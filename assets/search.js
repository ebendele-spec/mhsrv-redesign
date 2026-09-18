/* Inventory-grounded search. No remote service, hidden criteria, or invented specs. */
(function (root) {
  'use strict';
  const labels = {classa:'Class A gas',diesel:'Diesel pusher',classb:'Class B / camper van',classc:'Class C & B+',superc:'Super C',fifth:'Fifth wheel',tt:'Travel trailer',toy:'Toy hauler'};
  const norm = s => String(s || '').normalize('NFKD').replace(/[’']/g,'').toLowerCase().replace(/[^a-z0-9.]+/g,' ').trim();
  const cash = n => '$' + Number(n).toLocaleString('en-US');
  const numeric = s => {const value=s.replace(/[$,\s]/g,'');return parseFloat(value)*(/k$/i.test(value)?1000:/m$/i.test(value)?1000000:1);};
  const featureRules = {
    bunks: /\bbunk(?:house|s| beds?)?\b/i,
    'king bed': /\bking(?:[ -](?:size|sized))?[ -]bed\b/i,
    'queen bed': /\bqueen(?:[ -](?:size|sized))?[ -]bed\b/i,
    'theater seating': /\btheat(?:er|re)\s+(?:seats?|seating)\b/i,
    'outdoor kitchen': /\b(?:outdoor|outside|exterior)\s+kitchen\b/i,
    'bath and a half': /\b(?:bath and a half|1[ .]5\s*bath|one and a half bath|bath & a half)\b/i,
    'two bathrooms': /\b(?:2|two)\s+(?:full\s+)?bath(?:room)?s\b/i,
    'washer / dryer': /\b(?:washer|dryer|laundry)\b/i,
    'solar': /\bsolar\b/i,
    '4x4': /\b(?:4x4|4wd|four wheel drive)\b/i,
    'AWD': /\b(?:awd|all[ -]wheel drive)\b/i,
    'pet friendly': /\b(?:pet[ -]friendly|dog[ -]friendly|pet station|pet bed|dog bed)\b/i,
    'loft': /\bloft\b/i,
    'office': /\b(?:office|desk|workstation|work station)\b/i,
    'residential refrigerator': /\bresidential\s+(?:refrigerator|fridge)\b/i,
    'generator': /\bgenerator\b/i,
    'diesel': /\bdiesel\b/i
  };
  const featureQueries = [
    ['bunks',/\b(?:bunkhouse|bunk beds?|bunks?)\b/g],['king bed',/\bking(?: size| sized)?(?: bed)?\b/g],['queen bed',/\bqueen(?: size| sized)?(?: bed)?\b/g],
    ['theater seating',/\btheat(?:er|re)(?: seats?| seating)?\b/g],['outdoor kitchen',/\b(?:outdoor|outside|exterior) kitchen\b/g],
    ['bath and a half',/\b(?:bath and a half|1\.5 baths?|one and a half baths?|bath & a half)\b/g],['two bathrooms',/\b(?:2|two) (?:full )?bath(?:room)?s\b/g],
    ['washer / dryer',/\b(?:washer(?: and|\s*\/)?(?: dryer)?|dryer|laundry)\b/g],['solar',/\bsolar(?: panels?)?\b/g],
    ['4x4',/\b(?:4x4|4wd|four wheel drive)\b/g],['AWD',/\b(?:awd|all wheel drive)\b/g],['pet friendly',/\b(?:pet friendly|dog friendly|pets?|dogs?)\b/g],
    ['loft',/\bloft\b/g],['office',/\b(?:office|desk|workstation|work station)\b/g],['residential refrigerator',/\bresidential (?:refrigerator|fridge)\b/g],['generator',/\bgenerator\b/g]
  ];
  const stop = new Set(('i we my our am are is a an the to for me us want wants need needs looking find show with that has have and or in on at of please rv rvs recreational vehicle vehicles camper campers sale buy shopping budget cost price priced than less more below above under over max maximum minimum between up around about people person family suitable can good best great travel trips trip road driving drive motor coach coach ft feet foot length long inch inches dollars dollar thousand available models model equipped featuring included includes new used gas fuel diesel').split(' '));
  const statusLabel = s => ({listed:'Listed inventory',pending:'Sale pending',onorder:'On order',coming:'Coming soon',unavailable:'No longer listed'}[s] || 'Confirm availability');
  const searchText = u => norm([u.brand,u.model,u.floorplan,u.stock,u.fuel,u.city,u.state,...(u.features||[]),u.searchText].join(' '));
  const featureText = u => (u.features||[]).join(' ')+' '+(u.searchText||'');
  function near(a,b) {
    if (Math.abs(a.length-b.length)>1 || a===b) return a===b;
    if(a.length===b.length){const diff=[...a].map((c,i)=>c!==b[i]?i:-1).filter(i=>i>=0);if(diff.length===2&&diff[1]===diff[0]+1&&a[diff[0]]===b[diff[1]]&&a[diff[1]]===b[diff[0]])return true;}
    let i=0,j=0,d=0;
    while(i<a.length && j<b.length){if(a[i]===b[j]){i++;j++;continue;}if(++d>1)return false;if(a.length>b.length)i++;else if(a.length<b.length)j++;else{i++;j++;}}
    return d+(i<a.length||j<b.length?1:0)<=1;
  }
  function parse(query, items=[]) {
    const p={query:String(query||'').trim(), types:[], brands:[], models:[], features:[], excluded:[], words:[], chips:[], notes:[], corrections:[]};
    let q = p.query.toLowerCase().replace(/(\d)\s*[’']/g,'$1 feet ').replace(/[’']/g,'').replace(/pre[- ]?owned/g,'used').replace(/\b(\d+(?:\.\d+)?)\s+thousand\b/g,'$1k').replace(/\b(\d+(?:\.\d+)?)\s+million\b/g,'$1m').replace(/\$/g,' $').replace(/\s+/g,' ').trim();
    const digits={one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10};
    q=q.replace(/\b(sleeps?|family of) (one|two|three|four|five|six|seven|eight|nine|ten)\b/g,(_,prefix,n)=>prefix+' '+digits[n]);
    const take = (rx, fn) => {q=q.replace(rx,(...a)=>{fn(...a);return ' ';});};
    const stockKey = p.query.replace(/^(?:stock(?: number| no\.?)?|unit)\s*#?\s*/i,'').replace(/[^a-z0-9]/gi,'').toUpperCase();
    const exact = items.find(u=>u.stock.replace(/[^a-z0-9]/gi,'').toUpperCase()===stockKey);
    if(exact){p.stock=exact.stock;p.chips.push('#'+exact.stock);return p;}
    // Protect model names such as New Aire before interpreting "new" as condition.
    const modelNames=[...new Set(items.map(u=>norm(u.model)))].filter(m=>m.length>=3&&!['new','used','gas','diesel','solar','bunkhouse'].includes(m)).sort((a,b)=>b.length-a.length);
    for(const model of modelNames){const rx=new RegExp('\\b'+model.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','g');if(rx.test(q)){p.models.push(model);q=q.replace(rx,' ');}}
    take(/\b(?:between\s+)?(20\d{2})\s*(?:-|to|and)\s*(20\d{2})\b/g,(_,a,b)=>{p.minYear=+a;p.maxYear=+b;});
    take(/\b(20\d{2})\s*(?:or newer|and newer|and up|\+)(?=\s|$)/g,(_,a)=>p.minYear=+a);
    take(/\b(20\d{2})\s*(?:or older|and older|and earlier)(?=\s|$)/g,(_,a)=>p.maxYear=+a);
    take(/\b(?:since|after|newer than)\s+(20\d{2})\b/g,(_,a)=>p.minYear=+a);
    take(/\b(20\d{2})\b/g,(_,a)=>{p.minYear=+a;p.maxYear=+a;});
    take(/\b(?:under|below|less than|up to|max(?:imum)?|shorter than)\s*(\d+(?:\.\d+)?)\s*(?:feet|foot|ft)\b/g,(_,a)=>p.maxLength=+a);
    take(/\b(\d+(?:\.\d+)?)\s*(?:feet|foot|ft)\s*(?:or less|or shorter|and under|max(?:imum)?)\b/g,(_,a)=>p.maxLength=+a);
    take(/\b(?:over|above|longer than|at least)\s*(\d+(?:\.\d+)?)\s*(?:feet|foot|ft)\b/g,(_,a)=>p.minLength=+a);
    take(/\b(?:sleeps?|sleeping|sleep|seats?|family of|room for)\s*(\d{1,2})\b/g,(_,a)=>p.minSleeps=+a);
    take(/\b(?:under|below|less than|max(?:imum)?|up to)\s*([\d,.]+\s*k?)\s*miles\b/g,(_,a)=>p.maxMileage=numeric(a));
    take(/\$?\s*([\d,.]+)\s*(?:\/\s*(?:mo(?:nth)?|month)|per month|a month)\b/g,()=>{p.monthly=true;p.notes.push('Monthly payments depend on down payment, APR, term and credit approval. Use the payment estimator on an RV page.');});
    take(/\$?\s*([\d,.]+\s*[km]?)\s*down(?: payment)?\b/g,(_,a)=>{p.downPayment=numeric(a);p.notes.push('Your down payment is not treated as the RV purchase budget.');});
    take(/(?:\bbetween\s*)?\$?([\d,.]+\s*[km]?)\s*(?:and|to|-)\s*\$?([\d,.]+\s*[km]?)\b/g,(_,a,b)=>{p.minPrice=numeric(a);p.maxPrice=numeric(b);});
    take(/\b(?:under|below|less than|up to|max(?:imum)?|budget(?: of)?)\s*\$?([\d,.]+\s*[km]?)\b/g,(_,a)=>p.maxPrice=numeric(a));
    take(/\b(?:over|above|at least|min(?:imum)?)\s*\$?([\d,.]+\s*[km]?)\b/g,(_,a)=>p.minPrice=numeric(a));
    take(/\$\s*([\d,.]+\s*[km]?)\b/g,(_,a)=>p.maxPrice=numeric(a));
    take(/\b([\d,.]+\s*[km])\b/g,(_,a)=>p.maxPrice=numeric(a));
    take(/\b(?:no|not|without)\s+(?:a\s+)?(diesel|gas|gasoline)\b/g,(_,v)=>p.excludedFuel=v==='gasoline'?'gas':v);
    take(/\b(?:no|not|without)\s+(new|used)\b/g,(_,v)=>p.excludedCondition=v);
    take(/\bused\b/g,()=>p.condition='used');take(/\bnew\b/g,()=>{if(!p.condition)p.condition='new';});
    take(/\b(?:diesel pushers?|class a diesel)\b/g,()=>{p.types=['diesel'];p.fuel='diesel';});
    take(/\b(?:class ?a)(?: gas)?\b/g,(_,offset,whole)=>{p.types=/\bgas\b/.test(whole)?['classa']:['classa','diesel'];});
    take(/\b(?:super ?c)\b/g,()=>p.types=['superc']);
    take(/\b(?:class ?c|class b\+|b plus)(?=\s|[,;]|$)/g,()=>p.types=['classc']);
    take(/\b(?:class ?b|camper ?vans?|van life|vans?)\b/g,()=>p.types=['classb']);
    take(/\b(?:fifth wheels?|5th wheels?)\b/g,()=>p.types=['fifth']);
    take(/\b(?:travel trailers?|teardrops?)\b/g,()=>p.types=['tt']);
    take(/\btoy haulers?\b/g,()=>p.types=['toy']);
    take(/\b(?:motor ?homes?|motorized)\b/g,()=>{if(!p.types.length)p.types=['classa','diesel','classb','classc','superc'];});
    take(/\b(?:towables?|trailers?)\b/g,()=>{if(!p.types.length)p.types=['tt','fifth','toy'];});
    take(/\bdiesel\b/g,()=>p.fuel='diesel');take(/\bgas(?:oline)?\b/g,()=>p.fuel='gas');
    take(/\b(?:half[ -]ton(?: towable)?|f[ -]?150|1500 truck|tow with my truck)\b/g,()=>{p.towQuestion=true;p.notes.push('Truck compatibility cannot be verified from RV type. Confirm your truck’s payload, tow rating and the loaded RV and hitch weights with a specialist.');});
    take(/\b(?:national parks?|state parks?)\b/g,()=>{p.maxLength=p.maxLength||30;p.notes.push('Using 30 ft or shorter as a starting point. Individual parks and campsites have different length limits.');});
    take(/\b(?:full[ -]time(?: living)?|full timing|live in|living in)\b/g,()=>{p.lifestyle='fulltime';p.notes.push('For full-time living, verify storage, climate systems, floorplan and warranty use with a specialist.');});
    take(/\b(?:couples?|two people|weekend getaways?)\b/g,()=>{p.lifestyle='couple';});
    take(/\b(?:family friendly|families|kids|children)\b/g,()=>{p.lifestyle='family';p.notes.push('Family suggestions prioritize listed bunks or sleeping capacity. Verify the sleeping layout for your group.');});
    const featureQuery=q;
    for (const [key,rx] of featureQueries) {
      for(const found of featureQuery.matchAll(new RegExp(rx.source,'g'))){
        const prefix=featureQuery.slice(0,found.index).split(/[,.;]/).pop();
        const negative=[...prefix.matchAll(/\b(?:without|no|not)\b/g)].pop();
        const positive=[...prefix.matchAll(/\b(?:with|including|but|however|plus)\b/g)].pop();
        const target=negative&&(!positive||negative.index>positive.index)?p.excluded:p.features;
        if(!target.includes(key))target.push(key);
      }
      q=q.replace(rx,' ');
    }
    if(p.excluded.length)p.notes.push('Excluded equipment is not mentioned in these listings; absence must be confirmed before purchase.');
    if(p.features.includes('washer / dryer')||p.features.includes('solar'))p.notes.push('Listings may describe prep or optional equipment. Check the exact equipment installed on your stock number.');
    take(/\b(?:has|with)?\s*(?:a\s+)?(?:video tour|walkthrough|walk-through|video)\b/g,()=>p.video=true);
    take(/\b(?:has|with)?\s*(?:a\s+)?brochure\b/g,()=>p.brochure=true);
    take(/\b(?:has|with)\s*(?:a\s+)?floorplan\b/g,()=>p.floorplan=true);
    take(/\b(?:texas|alvarado|fort worth|dallas)\b/g,()=>p.state='TX');take(/\b(?:california|palm desert)\b/g,()=>p.state='CA');take(/\b(?:alabama|montgomery)\b/g,()=>p.state='AL');
    take(/\b(?:without|not|no)\b/g,()=>{});
    const brands=[...new Set(items.map(u=>u.brand))].sort((a,b)=>b.length-a.length);
    for(const brand of brands){const b=norm(brand);if(norm(q).includes(b)){p.brands.push(brand);q=q.replace(new RegExp(b.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'gi'),' ');}}
    const aliases={thor:'Thor Motor Coach',entegra:'Entegra Coach',dynamax:'Dynamax Corp',fleetwood:'Fleetwood RV',midwest:'Midwest Automotive Designs'};
    for(const [alias,brand]of Object.entries(aliases)){const rx=new RegExp('\\b'+alias+'\\b','g');if(rx.test(q)&&brands.includes(brand)){if(!p.brands.includes(brand))p.brands.push(brand);q=q.replace(rx,' ');}}
    let words=norm(q).split(' ').filter(w=>w&&!stop.has(w)&&!['but','however','plus','including'].includes(w));
    const vocabulary=[...new Set(items.flatMap(u=>norm(u.brand+' '+u.model).split(' ')))].filter(w=>w.length>3&&!/\d/.test(w));
    p.words=words.map(w=>{
      if(w.length<4||/\d/.test(w)||items.some(u=>searchText(u).split(' ').includes(w)))return w;
      const match=vocabulary.find(v=>near(v,w));if(match){p.corrections.push({from:w,to:match});return match;}return w;
    });
    for(const brand of brands){const tokens=norm(brand).split(' ');if(tokens.every(token=>p.words.includes(token))){if(!p.brands.includes(brand))p.brands.push(brand);p.words=p.words.filter(w=>!tokens.includes(w));}}
    if(p.types.length)p.chips.push(p.types.length===2&&p.types.includes('diesel')?'Class A':p.types.length>3?'Motorhomes':p.types.map(t=>labels[t]).join(' / '));
    if(p.condition)p.chips.push(p.condition==='new'?'New':'Pre-owned');
    if(p.fuel)p.chips.push(p.fuel==='diesel'?'Diesel fuel':'Gas fuel');
    if(p.excludedFuel)p.chips.push('Exclude '+p.excludedFuel+' fuel');if(p.excludedCondition)p.chips.push('Exclude '+p.excludedCondition);
    if(p.minPrice)p.chips.push('From '+cash(p.minPrice));if(p.maxPrice)p.chips.push('Up to '+cash(p.maxPrice));
    if(p.maxLength)p.chips.push(p.maxLength+' ft or shorter');if(p.minLength)p.chips.push(p.minLength+' ft or longer');
    if(p.minSleeps)p.chips.push('Sleeps '+p.minSleeps+'+');if(p.maxMileage)p.chips.push('Under '+p.maxMileage.toLocaleString()+' miles');
    if(p.minYear)p.chips.push(p.minYear===p.maxYear?String(p.minYear):p.minYear+(p.maxYear?'–'+p.maxYear:'+'));else if(p.maxYear)p.chips.push(p.maxYear+' or older');
    p.chips.push(...p.brands,...p.models,...p.features,...p.excluded.map(f=>'No listed '+f),...p.words.map(w=>'“'+w+'”'));
    if(p.state)p.chips.push(p.state);if(p.video)p.chips.push('Video available');if(p.brochure)p.chips.push('Brochure available');if(p.floorplan)p.chips.push('Floorplan available');
    return p;
  }
  function matches(u,p) {
    if(p.stock)return u.stock===p.stock;
    if(p.types.length&&!p.types.includes(u.type)&&!(p.types.includes('superc')&&/\bsuper c\b/i.test((u.searchText||'').slice(0,300))))return false;
    if(p.condition&&u.condition!==p.condition)return false;
    if(p.excludedCondition&&u.condition===p.excludedCondition)return false;
    if(p.fuel&&!norm(u.fuel).includes(p.fuel))return false;
    if(p.excludedFuel&&norm(u.fuel).includes(p.excludedFuel))return false;
    if(p.brands.length&&!p.brands.includes(u.brand))return false;
    if(p.models.length&&!p.models.some(m=>norm(u.model)===m))return false;
    if(p.minPrice&&(!u.price||u.price<p.minPrice))return false;if(p.maxPrice&&(!u.price||u.price>p.maxPrice))return false;
    if(p.minYear&&u.year<p.minYear)return false;if(p.maxYear&&u.year>p.maxYear)return false;
    if(p.maxLength&&(!u.length||u.length>p.maxLength))return false;if(p.minLength&&(!u.length||u.length<p.minLength))return false;
    if(p.minSleeps&&(!u.sleeps||u.sleeps<p.minSleeps))return false;
    if(p.maxMileage&&(u.mileage==null||u.mileage>p.maxMileage))return false;
    if(p.state&&u.state!==p.state)return false;
    if(p.video&&!u.hasVideo||p.brochure&&!u.hasBrochure||p.floorplan&&!u.hasFloorplan)return false;
    const ft=featureText(u);
    if(p.features.some(f=>!featureRules[f].test(ft)))return false;
    if(p.excluded.some(f=>featureRules[f].test(ft)))return false;
    const txt=searchText(u);
    if(p.words.some(w=>!new RegExp('(?:^| )'+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'(?: |$)').test(txt)&&!norm(u.stock+' '+u.floorplan).split(' ').some(token=>token.startsWith(w))))return false;
    return true;
  }
  function reasons(u,p) {
    const r=[];
    if(p.stock)r.push('Exact stock match');
    if(p.maxPrice&&u.price)r.push(cash(p.maxPrice-u.price)+' below your budget');
    if(p.minSleeps)r.push('Listed to sleep '+u.sleeps);
    if(p.maxLength)r.push(u.length+' ft · within your length');
    r.push(...p.features.slice(0,2).map(f=>'Listing mentions '+f));
    if(p.words.length)r.push('Matches '+p.words.join(' + '));
    if(!r.length&&p.brands.length)r.push('Your selected brand');
    return r.slice(0,3);
  }
  function run(items,query,filters={}) {
    const parsed=parse(query,items);
    const found=items.filter(u=>matches(u,parsed)).filter(u=>{
      if(filters.type&&u.type!==filters.type)return false;if(filters.condition&&u.condition!==filters.condition)return false;
      if(filters.brand&&u.brand!==filters.brand)return false;if(filters.state&&u.state!==filters.state)return false;
      if(filters.maxPrice&&(!u.price||u.price>+filters.maxPrice))return false;
      if(filters.minSleeps&&(!u.sleeps||u.sleeps<+filters.minSleeps))return false;
      if(filters.maxLength&&(!u.length||u.length>+filters.maxLength))return false;
      if(filters.status&&u.status!==filters.status)return false;
      if(filters.video&&!u.hasVideo)return false;if(filters.floorplan&&!u.hasFloorplan)return false;
      return true;
    });
    const rank=u=>{
      let score=({listed:60,coming:10,onorder:0,pending:-100,unavailable:-200}[u.status]||0)+(u.image?12:0)+(u.hasFloorplan?4:0)+(u.hasVideo?2:0);
      if(parsed.lifestyle==='family')score+=(featureRules.bunks.test(featureText(u))?40:0)+(u.sleeps>=6?20:0);
      if(parsed.lifestyle==='couple')score+=(u.type==='classb'?30:0)+(u.length&&u.length<30?15:0);
      if(parsed.lifestyle==='fulltime')score+=(['diesel','fifth'].includes(u.type)?30:0);
      for(const w of parsed.words){if(norm(u.model+' '+u.floorplan+' '+u.brand).includes(w))score+=20;}
      return score;
    };
    found.sort((a,b)=>filters.sort==='price-low'?(a.price||Infinity)-(b.price||Infinity):filters.sort==='price-high'?(b.price||0)-(a.price||0):filters.sort==='year'?(b.year||0)-(a.year||0):filters.sort==='length'?(a.length||Infinity)-(b.length||Infinity):rank(b)-rank(a)||a.stock.localeCompare(b.stock));
    return {items:found,parsed};
  }
  root.RVSearch={parse,run,matches,reasons,norm,labels,statusLabel,featureRules,featureText};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.RVSearch;
})(typeof window!=='undefined'?window:globalThis);
