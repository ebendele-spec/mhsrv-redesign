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
