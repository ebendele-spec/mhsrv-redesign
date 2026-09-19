const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const search=require('../assets/search.js');
const items=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../inventory.json'))).items;
function query(q){return search.run(items,q);}
test('exact stock searches accept a stock prefix and ignore punctuation',()=>{
  const u=items[0];assert.equal(query(u.stock).items[0].stock,u.stock);assert.equal(query('stock #'+u.stock).items[0].stock,u.stock);
});
test('length is never interpreted as currency',()=>{
  for(const q of ['under 30 feet',"under 30'",'30 ft or shorter']){const {parsed,items:result}=query(q);assert.equal(parsed.maxLength,30);assert.equal(parsed.maxPrice,undefined);assert(result.every(u=>u.length<=30));}
});
test('money supports decimals, millions and explicit ranges',()=>{
  for(const [q,min,max]of [['under $25.5k',undefined,25500],['$1.2m',undefined,1200000],['50k-100k',50000,100000],['between $50k and $100k',50000,100000],['under 100 thousand',undefined,100000]]){const p=query(q).parsed;assert.equal(p.minPrice,min,q);assert.equal(p.maxPrice,max,q);}
});
test('years preserve ranges, newer and older operators',()=>{
  assert.equal(query('2022+').parsed.minYear,2022);assert.equal(query('2022+').parsed.maxYear,undefined);
  assert.equal(query('2018 or older').parsed.maxYear,2018);assert.equal(query('2018 or older').parsed.minYear,undefined);
  const p=query('2022 to 2025').parsed;assert.equal(p.minYear,2022);assert.equal(p.maxYear,2025);
});
test('sleeping capacity excludes missing specifications',()=>{
  const r=query('Class C sleeps six under $100k');assert.equal(r.parsed.minSleeps,6);assert(r.items.every(u=>u.type==='classc'&&u.sleeps>=6&&u.price<=100000));
});
test('typed fuel and RV category constraints remain separate',()=>{
  assert(query('Class A diesel').items.every(u=>u.type==='diesel'));
  assert.deepEqual(query('Class B+').parsed.types,['classc']);
  assert.deepEqual(query('class C, under $100k').parsed.types,['classc']);
  assert(query('Sprinter').items.some(u=>u.type==='classc'));
});
test('Sprinter matches both chassis and model without overriding explicit RV types or brands',()=>{
  const common={year:2026,condition:'new',price:100000,features:[],status:'listed',state:'TX',floorplan:''};
  const sample=[
    {...common,stock:'TEST-C',brand:'Example Coach',model:'Compact',type:'classc',fuel:'Diesel',searchText:'Mercedes Sprinter chassis'},
    {...common,stock:'TEST-F',brand:'Keystone',model:'Sprinter',type:'fifth',fuel:'n/a',searchText:'Fifth wheel'},
    {...common,stock:'TEST-Q',brand:'Thor Motor Coach',model:'Quantum Sprinter',type:'classc',fuel:'Diesel',searchText:'Mercedes Sprinter chassis'}
  ];
  const stocks=q=>search.run(sample,q).items.map(u=>u.stock).sort();
  assert.deepEqual(stocks('Sprinter'),['TEST-C','TEST-F','TEST-Q']);
  for(const q of ['class C Sprinter','Mercedes Sprinter','Sprinter diesel'])assert.deepEqual(stocks(q),['TEST-C','TEST-Q'],q);
  assert.deepEqual(stocks('Keystone Sprinter'),['TEST-F']);
  assert.deepEqual(stocks('Sprinter fifth wheel'),['TEST-F']);
  assert.deepEqual(stocks('Quantum Sprinter'),['TEST-Q']);
});
test('feature exclusions stop at the next positive clause',()=>{
  const p=query('no bunks with a king bed').parsed;assert.deepEqual(p.excluded,['bunks']);assert.deepEqual(p.features,['king bed']);
  const p2=query('bunkhouse without a loft but with solar').parsed;assert(p2.excluded.includes('loft'));assert(p2.features.includes('solar'));assert(p2.features.includes('bunks'));
  const p3=query('without solar and generator').parsed;assert(p3.excluded.includes('solar'));assert(p3.excluded.includes('generator'));
  assert.equal(query('no bunks in Texas').parsed.state,'TX');
});
test('negative fuel and condition constraints never apply the opposite intent',()=>{
  const r=query('not diesel');assert.equal(r.parsed.fuel,undefined);assert(r.items.every(u=>!u.fuel.toLowerCase().includes('diesel')));
  assert(query('not used').items.every(u=>u.condition!=='used'));
});
test('known model names and corrected brands do not match advertising boilerplate',()=>{
  for(const model of ['View','Phaeton','Unity','Discovery']){const r=query(model);assert(r.items.every(u=>search.norm(u.model)===model.toLowerCase()),model);}
  assert(query('Newmr').items.every(u=>u.brand==='Newmar'));
  assert(query('Grand Desgin').items.every(u=>u.brand==='Grand Design'));
  const p=query('used Newmar New Aire').parsed;assert.equal(p.condition,'used');assert(p.models.includes('new aire'));
});
test('video and lifestyle phrases leave no restrictive filler',()=>{
  const p=query('Class C with video tour').parsed;assert(p.video);assert.deepEqual(p.words,[]);
  const f=query('full time living').parsed;assert.equal(f.lifestyle,'fulltime');assert.deepEqual(f.words,[]);
});
test('a monthly amount and down payment are not purchase price filters',()=>{
  const p=query('$500 per month with $10k down').parsed;assert.equal(p.maxPrice,undefined);assert.equal(p.downPayment,10000);assert(p.notes.length);
});
test('no matching inventory never silently relaxes hard requirements',()=>{
  const r=query('diesel pusher sleeps 99 under $10k');assert.equal(r.items.length,0);assert.equal(r.parsed.minSleeps,99);assert.equal(r.parsed.maxPrice,10000);
});
test('pet searches cannot match competition or carpet substrings',()=>{
  assert(!search.featureRules['pet friendly'].test('carpet competition'));assert(query('pet friendly').items.every(u=>search.featureRules['pet friendly'].test(search.featureText(u))));
});
test('structured filters and search requirements are combined',()=>{
  const r=search.run(items,'under $150k',{condition:'used',state:'TX',maxLength:'35'});assert(r.items.every(u=>u.price&&u.price<=150000&&u.condition==='used'&&u.state==='TX'&&u.length<=35));
});

test('monthly budgets use explicit payment assumptions before interpreting model years',()=>{
  const common={year:2026,condition:'new',brand:'Example',model:'Road',type:'classc',fuel:'gas',features:[],status:'listed',floorplan:'',searchText:''};
  const finance={apr:9.99,months:240,downPercent:20};
  const ceiling=search.monthlyBudgetPrice(2000,finance);
  const sample=[{...common,stock:'BELOW',price:Math.floor(ceiling)},{...common,stock:'ABOVE',price:Math.ceil(ceiling)},{...common,stock:'UNKNOWN',price:null}];
  const r=search.run(sample,'under $2000/mo',{finance});
  assert.equal(r.parsed.minYear,undefined);assert.equal(r.parsed.maxYear,undefined);
  assert.equal(r.parsed.monthlyBudget,2000);assert.deepEqual(r.parsed.words,[]);
  assert.deepEqual(r.items.map(u=>u.stock),['BELOW']);
  assert(search.estimateMonthly(r.items[0].price,finance)<=2000);
  const explicit=search.parse('2024 diesel under $2,000 per month with $10k down',sample,finance);
  assert.equal(explicit.minYear,2024);assert.equal(explicit.maxYear,2024);assert.equal(explicit.downPayment,10000);
  assert.equal(explicit.finance.downPayment,10000);assert.deepEqual(explicit.words,[]);
  assert(Math.abs(search.estimateMonthly(explicit.monthlyMaxPrice,explicit.finance)-2000)<1e-6);
});

test('payment calculations honor editable APR, term, percent and fixed down payment',()=>{
  assert.equal(search.estimateMonthly(120000,{apr:0,months:120,downPercent:20}),800);
  assert.equal(search.estimateMonthly(120000,{apr:0,months:120,downPayment:24000}),800);
  assert.equal(search.estimateMonthly(null),null);assert.equal(search.estimateMonthly(0),null);
  assert.equal(search.estimateMonthly(10000,{apr:0,months:120,downPayment:20000}),0);
  for(const f of [{apr:7.5,months:180,downPercent:10},{apr:0,months:240,downPayment:10000}]){
    assert(Math.abs(search.monthlyBudgetPrice(search.estimateMonthly(85000,f),f)-85000)<1e-6);
  }
  assert.equal(search.financeOptions({apr:-1,months:'bad',downPercent:100}).apr,9.99);
});

test('horsepower and exterior colors use supplied fields rather than unrelated description text',()=>{
  const common={year:2026,condition:'new',brand:'Example',model:'Road',type:'diesel',fuel:'diesel',features:[],status:'listed',floorplan:'',price:150000};
  const sample=[
    {...common,stock:'MATCH',horsepower:450,exterior:'Pearl White / Grey',searchText:'Coach'},
    {...common,stock:'LOW',horsepower:400,exterior:'White',searchText:'Coach'},
    {...common,stock:'UNKNOWN',horsepower:null,exterior:'',interior:'White',searchText:'White cabinets and a black tank. Model range offers 450HP.'}
  ];
  assert.deepEqual(search.run(sample,'450hp+ white diesel').items.map(u=>u.stock),['MATCH']);
  assert.deepEqual(search.run(sample,'gray exterior').items.map(u=>u.stock),['MATCH']);
  const p=search.parse('450 horsepower or more',sample);assert.equal(p.minHp,450);assert.deepEqual(p.words,[]);
  const brandSample=[{...common,stock:'BRAND',brand:'Black Series',exterior:'Silver',horsepower:null}];
  assert.deepEqual(search.run(brandSample,'Black Series').items.map(u=>u.stock),['BRAND']);
});

test('people counts and washer AND dryer preserve every requested requirement',()=>{
  const common={year:2026,condition:'new',brand:'Example',model:'Road',type:'classc',fuel:'gas',status:'listed',floorplan:'',price:100000,searchText:''};
  const sample=[
    {...common,stock:'BOTH',sleeps:6,features:['Washer','Dryer']},
    {...common,stock:'WASHER',sleeps:8,features:['Washer']},
    {...common,stock:'DRYER',sleeps:7,features:['Dryer']},
    {...common,stock:'UNKNOWN',sleeps:null,features:['Washer','Dryer']}
  ];
  for(const query of ['6 people washer and dryer','six people washer & dryer','sleeps six washer/dryer']){
    const result=search.run(sample,query);assert.equal(result.parsed.minSleeps,6);assert.deepEqual(result.items.map(u=>u.stock),['BOTH'],query);
  }
  assert.deepEqual(search.run(sample,'washer without dryer').items.map(u=>u.stock),['WASHER']);
});

test('deals and arrivals are feed flags and savings sorting also covers regular price reductions',()=>{
  const common={year:2026,condition:'new',brand:'Example',model:'Road',type:'tt',fuel:'n/a',features:[],status:'listed',floorplan:'',searchText:'',price:50000};
  const sample=[
    {...common,stock:'MSRP',msrp:65000,deal:false,newArrival:false},
    {...common,stock:'DEAL',msrp:null,regularPrice:80000,deal:true,newArrival:true},
    {...common,stock:'NEITHER',msrp:null,regularPrice:50000,deal:false,newArrival:false}
  ];
  assert.deepEqual(search.run(sample,'deals of the week').items.map(u=>u.stock),['DEAL']);
  assert.deepEqual(search.run(sample,'',{condition:'deal'}).items.map(u=>u.stock),['DEAL']);
  assert.deepEqual(search.run(sample,'just arrived').items.map(u=>u.stock),['DEAL']);
  assert.deepEqual(search.run(sample,'',{sort:'savings'}).items.map(u=>u.stock),['DEAL','MSRP','NEITHER']);
});

test('lifestyle starting points preserve other facets and rank listed sleeping space',()=>{
  const common={year:2026,condition:'used',brand:'Example',model:'Road',features:[],status:'listed',floorplan:'',searchText:'',price:50000};
  const sample=[{...common,stock:'A',type:'tt'},{...common,stock:'B',type:'classc',sleeps:6},{...common,stock:'C',type:'classc',sleeps:2},{...common,stock:'D',type:'fifth',price:80000,sleeps:8}];
  assert.deepEqual(search.run(sample,'',{life:'family',maxPrice:60000}).items.map(u=>u.stock),['B','C']);
  assert.deepEqual(search.run(sample,'',{life:'weekend',type:'tt'}).items.map(u=>u.stock),['A']);
});

test('rich autocomplete provides partial brand/model completions and typo corrections',()=>{
  const common={year:2026,condition:'new',features:[],status:'listed',floorplan:'',searchText:'',price:200000};
  const sample=[{...common,stock:'TEST123',brand:'Newmar',model:'Dutch Star',type:'diesel'},{...common,stock:'TEST456',brand:'Grand Design',model:'Reflection',type:'fifth'}];
  const prefix=search.suggest(sample,'newm');assert(prefix.terms.includes('Newmar'));assert.equal(prefix.items[0].stock,'TEST123');
  assert.equal(search.suggest(sample,'TEST12').items[0].stock,'TEST123');
  assert(search.suggest(sample,'Newmr').corrections.some(c=>c.to==='newmar'));
  assert.deepEqual(search.run(sample,'Grand Desgin').items.map(u=>u.stock),['TEST456']);
});
