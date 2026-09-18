(function(){
  'use strict';
  const $=(q,el=document)=>el.querySelector(q), $$=(q,el=document)=>[...el.querySelectorAll(q)];
  const config=JSON.parse($('#siteConfig').textContent),base=config.base||'';
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=n=>n?'$'+Math.round(n).toLocaleString('en-US'):'Request price';
  const title=u=>[u.year,u.brand,u.model,u.floorplan].filter(Boolean).join(' ');
  const unitHref=u=>base+'units/'+encodeURIComponent(u.stock)+'.html';
  const icon=name=>({heart:'<path d="M20.8 4.8a5.5 5.5 0 0 0-7.8 0L12 5.9l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.4a5.5 5.5 0 0 0 0-7.8Z"/>',arrow:'<path d="M5 12h14M13 6l6 6-6 6"/>',camera:'<path d="M3 7h4l2-3h6l2 3h4v14H3V7Z"/><circle cx="12" cy="13" r="4"/>',pin:'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',search:'<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/>'}[name]||'');
  const svg=name=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${icon(name)}</svg>`;
  let catalog=null,loading=null,unit=$('#unitData')?JSON.parse($('#unitData').textContent):null,toastTimer;
  const state={q:'',filters:{},limit:6,result:null};
  const memory={};
  function read(key){try{const a=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(a)?a.filter(s=>typeof s==='string'):[];}catch(_){return memory[key]||[];}}
  function write(key,value){memory[key]=value;try{localStorage.setItem(key,JSON.stringify(value));}catch(_){toast('Saved for this visit. Your browser is blocking persistent storage.');}}
  let saved=read('mhsrv-saved'),compared=read('mhsrv-compare').slice(0,3);
  function track(event,props={}){window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:'mhsrv_'+event,...props});document.dispatchEvent(new CustomEvent('mhsrv:analytics',{detail:{event,...props}}));}
  function toast(message){const el=$('#toast');el.textContent=message;el.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.hidden=true,3200);}
  function showDialog(id){const d=$(id);if(!d.open){d.showModal();document.body.style.overflow='hidden';}}
  function closeDialog(d){d.close();if(!document.querySelector('dialog[open]'))document.body.style.overflow='';if(d.id==='viewerDialog')$('#viewerContent').replaceChildren();}
  $$('dialog').forEach(d=>{d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeDialog(d);}});d.addEventListener('close',()=>{if(!document.querySelector('dialog[open]'))document.body.style.overflow='';if(d.id==='viewerDialog')$('#viewerContent').replaceChildren();});});
  async function getCatalog(){
    if(catalog)return catalog;if(loading)return loading;
    loading=fetch(base+'inventory.json').then(r=>{if(!r.ok)throw new Error('Inventory could not load.');return r.json();}).then(data=>{if(!Array.isArray(data.items))throw new Error('Inventory format is unavailable.');catalog=data;return data;}).catch(e=>{loading=null;throw e;});return loading;
  }
  function refreshSaved(){
    $$('[data-save-count]').forEach(e=>e.textContent=saved.length||'');
    $$('[data-save]').forEach(b=>{const active=saved.includes(b.dataset.save);b.setAttribute('aria-pressed',String(active));b.setAttribute('aria-label',(active?'Unsave ':'Save ')+b.dataset.save);});
    $$('[data-compare]').forEach(e=>e.checked=compared.includes(e.dataset.compare));
    const tray=$('#compareTray');tray.hidden=!compared.length||!!$('#comparison');$('#compareTrayTitle').textContent=compared.length+' RV'+(compared.length===1?'':'s')+' in your comparison';
  }
  function toggleSave(stock){saved=saved.includes(stock)?saved.filter(s=>s!==stock):[...saved,stock];write('mhsrv-saved',saved);refreshSaved();toast(saved.includes(stock)?'RV saved to your shortlist.':'RV removed from your shortlist.');track('save_rv',{stock,saved:saved.includes(stock)});if($('#savedGrid'))renderSaved();}
  function toggleCompare(stock,selected){
    if(selected&&!compared.includes(stock)){if(compared.length>=3){toast('Compare up to three RVs. Remove one to add another.');refreshSaved();return;}compared.push(stock);}else if(!selected){compared=compared.filter(s=>s!==stock);}
    write('mhsrv-compare',compared);refreshSaved();track('compare_change',{count:compared.length});if($('#comparison'))renderCompare();
  }
  function card(u,parsed){
    const name=title(u),url=unitHref(u),photo=u.image?`<img src="${esc(u.image)}" alt="${esc(name)}" width="640" height="420" loading="lazy" decoding="async">`:'<div class="photo-placeholder">Photos coming soon</div>';
    const badge=u.status==='listed'?(u.condition==='new'?'New':'Pre-owned'):RVSearch.statusLabel(u.status);
    const specs=[u.length?u.length+' ft':'Length unlisted',u.sleeps?'Sleeps '+u.sleeps:'Ask about sleeping',u.slides?u.slides+' slide'+(u.slides===1?'':'s'):''].filter(Boolean);
    const reasons=parsed?RVSearch.reasons(u,parsed):[];
    return `<article class="rv-card" data-stock="${esc(u.stock)}"><div class="card-photo"><a href="${url}" tabindex="-1" aria-hidden="true">${photo}</a><span class="status-tag ${u.status!=='listed'?'pending':''}">${esc(badge)}</span><button class="save-button" data-save="${esc(u.stock)}" aria-label="Save ${esc(name)}" aria-pressed="${saved.includes(u.stock)}">${svg('heart')}</button><span class="photo-count">${svg('camera')}${u.photoCount}</span></div><div class="card-body"><p class="card-kicker">${esc(RVSearch.labels[u.type])} · ${u.year}</p><h3 class="card-title"><a href="${url}">${esc([u.brand,u.model,u.floorplan].join(' '))}</a></h3><div class="card-specs">${specs.map(s=>'<span>'+esc(s)+'</span>').join('')}</div>${reasons.length?'<div class="match-reasons">'+reasons.map(esc).join(' · ')+'</div>':''}<div class="card-divider"></div><p class="price-label">Listed price</p><div class="card-price">${money(u.price)}</div><p class="card-msrp">${u.msrp&&u.price&&u.msrp>u.price?'MSRP <s>'+money(u.msrp)+'</s>':'Confirm current price &amp; availability'}</p><p class="card-location">${svg('pin')}${esc(u.city)}, ${esc(u.state)} · #${esc(u.stock)}</p><div class="card-actions"><label class="compare-check"><input type="checkbox" data-compare="${esc(u.stock)}" aria-label="Compare ${esc(name)}" ${compared.includes(u.stock)?'checked':''}>Compare</label><a class="text-link" href="${url}">Explore this RV ${svg('arrow')}</a></div></div></article>`;
  }
  function currentFilters(){const f=$('#filterForm');return f?Object.fromEntries([...new FormData(f).entries()]):{};}
  function updateUrl(){const url=new URL(location.href);['q','type','condition','cond','brand','state','maxPrice','minSleeps','maxLength','status','video','floorplan','sort'].forEach(k=>url.searchParams.delete(k));if(state.q)url.searchParams.set('q',state.q);Object.entries(state.filters).forEach(([k,v])=>{if(v&&!(k==='sort'&&v==='recommended'))url.searchParams.set(k,v);});history.replaceState(null,'',url);}
  function renderResults({scroll=false,preserveLimit=false}={}){
    if(!catalog)return;if(!preserveLimit)state.limit=6;
    state.filters={...currentFilters(),sort:$('#sortSelect')?.value||'recommended'};
    state.result=RVSearch.run(catalog.items,state.q,state.filters);
    const {items,parsed}=state.result;
    const preferred=['MHS44469','MHS43225','MHS43883','M130841','M128068','T147081'];
    if(!state.q&&!Object.entries(state.filters).some(([k,v])=>v&&(k!=='sort'||v!=='recommended')))items.sort((a,b)=>(preferred.includes(a.stock)?preferred.indexOf(a.stock):100)-(preferred.includes(b.stock)?preferred.indexOf(b.stock):100));
    $('#resultCount').textContent=items.length.toLocaleString()+' RV'+(items.length===1?'':'s')+(state.q?' match your search':' to explore');
    $('#results').innerHTML=items.length?items.slice(0,state.limit).map(u=>card(u,parsed)).join(''):`<div class="empty-state"><h3>No exact matches. Let's adjust your search.</h3><p>We kept all your requirements. Some RVs may have missing specifications, so they won't appear in a search that requires those details.</p><button class="button outline" data-clear-search>Clear search &amp; filters</button> <button class="button" data-lead="Help finding an RV">Ask a specialist</button></div>`;
    $('#resultProgress').textContent=items.length?'Showing '+Math.min(state.limit,items.length)+' of '+items.length.toLocaleString()+' RVs':'';
    $('#loadMore').hidden=state.limit>=items.length;
    const sum=$('#smartSummary');sum.hidden=!state.q;
    if(state.q)sum.innerHTML=`<strong>Here's how we understood your search</strong><div class="chips">${parsed.chips.map(c=>'<span class="query-chip">'+esc(c)+'</span>').join('')||'<span class="query-chip">All inventory</span>'}</div>${parsed.corrections.length?'<p class="smart-notes">Interpreting '+parsed.corrections.map(c=>'“'+esc(c.from)+'” as “'+esc(c.to)+'”').join(', ')+'.</p>':''}<div class="smart-notes">${parsed.notes.map(n=>'<p>'+esc(n)+'</p>').join('')}</div><button class="reset-button" data-clear-query>Clear search words</button>`;
    const filterNumber=Object.values(currentFilters()).filter(Boolean).length;$('#filterCount').textContent=filterNumber?'('+filterNumber+')':'';
    updateUrl();refreshSaved();
    if(scroll)$('#inventory').scrollIntoView({behavior:'smooth',block:'start'});
  }
  async function search(query,scroll=true){
    const target=$('[data-inventory]');
    if(!target){location.href=base+'index.html?q='+encodeURIComponent(query)+'#inventory';return;}
    state.q=String(query).trim().slice(0,250);if($('#rvSearch'))$('#rvSearch').value=state.q;hideSuggestions();
    try{await getCatalog();renderResults({scroll});track('inventory_search',{result_count:state.result.items.length,query_length:state.q.length});}
    catch(_){$('#smartSummary').hidden=false;$('#smartSummary').innerHTML='<p>Inventory search could not load. Your existing listings are still available below.</p><button class="button outline small" data-retry>Try again</button>';}
  }
  function hideSuggestions(){const s=$('#suggestions');if(s)s.hidden=true;$('#rvSearch')?.setAttribute('aria-expanded','false');$('#rvSearch')?.removeAttribute('aria-activedescendant');}
  let suggestTimer,suggestIndex=-1;
  async function suggest(){const input=$('#rvSearch'),q=input.value.trim();if(q.length<2){hideSuggestions();return;}try{await getCatalog();if(input.value.trim()!==q)return;const result=RVSearch.run(catalog.items,q);const first=result.items.slice(0,3);$('#suggestions').innerHTML=`<button class="suggestion" role="option" id="suggest-0" data-suggest-query="${esc(q)}"><span>${svg('search')} Search “${esc(q)}”</span><small>${result.items.length.toLocaleString()} matches</small></button>`+first.map((u,i)=>`<a class="suggestion" role="option" id="suggest-${i+1}" href="${unitHref(u)}"><span>${esc(title(u))}<small style="display:block">#${esc(u.stock)} · ${esc(u.city)}</small></span><small>${money(u.price)}</small></a>`).join('');$('#suggestions').hidden=false;input.setAttribute('aria-expanded','true');suggestIndex=-1;}catch(_){hideSuggestions();}}
  async function initInventory(){
    if(!$('[data-inventory]'))return;
    const url=new URL(location.href);state.q=url.searchParams.get('q')||$('[data-inventory]').dataset.initialQuery||'';
    if($('#rvSearch'))$('#rvSearch').value=state.q;
    try{await getCatalog();$('#filterBrand').innerHTML='<option value="">All brands</option>'+[...new Set(catalog.items.map(u=>u.brand))].sort().map(b=>`<option value="${esc(b)}">${esc(b)}</option>`).join('');
      for(const [key,value]of url.searchParams){const name=key==='cond'?'condition':key;const el=$('#filterForm').elements.namedItem(name);if(el){if(el.type==='checkbox')el.checked=value==='on'||value==='true';else el.value=value;}}
      if(url.searchParams.get('sort'))$('#sortSelect').value=url.searchParams.get('sort');
      renderResults();if(url.hash==='#inventory')$('#inventory').scrollIntoView();
    }catch(_){$('#smartSummary').hidden=false;$('#smartSummary').innerHTML='<p>Search is temporarily unavailable. Browse the listings below or call 800-335-6054.</p><button class="button outline small" data-retry>Retry inventory search</button>';}
  }
  function openLead(intent,stock=''){
    const form=$('#leadForm');form.elements.intent.value=intent;form.elements.stock.value=stock||unit?.stock||'';
    $('#leadTitle').textContent=intent==='Confirm price and availability'?'Is this your next RV?':intent;
    const current=unit?.stock===form.elements.stock.value?unit:catalog?.items.find(u=>u.stock===form.elements.stock.value);
    $('#leadContext').textContent=current?title(current)+' · #'+current.stock+' · Tell us how to reach you. We’ll help confirm the details.':'Tell us what you have in mind. An MHSRV specialist can help with your next step.';
    $('.form-message',form).hidden=true;const button=$('button[type=submit]',form);button.disabled=false;button.innerHTML='Send my request '+svg('arrow');
    if(intent.includes('finding')&&state.q)form.elements.message.value='I am looking for: '+state.q;
    if(intent.includes('trade')||intent.includes('sell'))form.elements.message.placeholder='Year, make, model, mileage, condition, and any RV you are interested in.';
    else form.elements.message.placeholder='Ask a question, request a walk-through, or tell us about your trade.';
    const phone=current?.phone||'8003356054';$('.contact-alternatives a[href^="tel:"]').href='tel:'+phone;
    showDialog('#leadDialog');track('lead_form_open',{intent,stock:form.elements.stock.value});
  }
  $('#leadForm').addEventListener('submit',async e=>{
    e.preventDefault();const form=e.currentTarget;if(!form.reportValidity())return;const button=$('button[type=submit]',form),message=$('.form-message',form);button.disabled=true;button.textContent='Sending your request…';message.hidden=true;
    const data=Object.fromEntries(new FormData(form));data._subject='MHSRV: '+data.intent+(data.stock?' · #'+data.stock:'');data._template='table';data.page=location.href;data.inventory_updated=unit?.updated||catalog?.updated||'';
    try{const attribution=JSON.parse(sessionStorage.getItem('mhsrv-attribution')||'{}');Object.assign(data,attribution);}catch(_){}
    try{await MHSCore.submitLead('https://formsubmit.co/ajax/'+encodeURIComponent(config.leadEmail),data);message.className='form-message success';message.textContent='Your request was accepted by our form service. For immediate help, call us below. Thank you for considering MHSRV.';message.hidden=false;button.textContent='Request sent';track('lead_request_accepted',{intent:data.intent,stock:data.stock});}
    catch(error){message.className='form-message error';message.innerHTML=esc(error.message||'Your request could not be confirmed.')+` <a href="mailto:${esc(config.leadEmail)}?subject=${encodeURIComponent(data._subject)}&body=${encodeURIComponent('Name: '+data.name+'\nEmail: '+data.email+'\nPhone: '+(data.phone||'')+'\nStock: '+(data.stock||'')+'\n'+(data.message||''))}">Email your request instead</a>.`;message.hidden=false;button.disabled=false;button.innerHTML='Try sending again '+svg('arrow');track('lead_request_error',{intent:data.intent});}
  });
  try{const q=new URLSearchParams(location.search),a={};['utm_source','utm_medium','utm_campaign','utm_content','utm_term','gclid','msclkid'].forEach(k=>{if(q.get(k))a[k]=q.get(k).slice(0,250);});if(Object.keys(a).length)sessionStorage.setItem('mhsrv-attribution',JSON.stringify(a));}catch(_){}
  $$('[data-privacy-link]').forEach(a=>a.href=base+'privacy.html');
  const matchSteps=[{title:'How do you want to travel?',options:[['motorhome','Drive my RV','Motorhomes & camper vans'],['towable','Tow my RV','Trailers & fifth wheels'],['','Keep my options open','Help me explore']]},{title:'What purchase budget feels right?',options:[['under $50k','Under $50,000','A focused starting point'],['under $100k','Under $100,000','More room to explore'],['under $150k','Under $150,000','A wider range of RVs'],['under $250k','Under $250,000','Explore premium choices'],['under $400k','Under $400,000','Space and comfort'],['','Show me all budgets','I’m still deciding']]},{title:'Who is coming along?',options:[['couple','One or two travelers','Prioritize compact options'],['family friendly','Family adventures','Prioritize listed bunks'],['full time','A longer chapter','Explore space for daily life'],['','Let me see everything','I’ll compare the layouts']]},{title:'Anything you want to prioritize?',options:[['bunkhouse','Bunk sleeping','Based on the listing'],['king bed','A king bed','Based on the listing'],['under 30 feet','A shorter RV','30 ft or shorter'],['with video','A video tour','Explore before you visit'],['','No must-have yet','Show my matches']]}];
  let matchStep=0,matchChoices=['','','',''];
  function renderMatch(){const s=matchSteps[matchStep];$('#matchBody').innerHTML=`<div class="step-count" aria-label="Step ${matchStep+1} of 4">${matchSteps.map((_,i)=>'<span class="'+(i<=matchStep?'active':'')+'"></span>').join('')}</div><h3>${s.title}</h3><div class="match-options">${s.options.map(([v,label,desc])=>`<button class="match-option ${matchChoices[matchStep]===v?'active':''}" data-match-choice="${esc(v)}"><span>${label}</span><small>${desc}</small></button>`).join('')}</div><p class="assistant-disclosure">Your preferences stay in this browser. Matching uses the imported listings, not guessed specifications.</p><div class="match-footer"><button class="text-link" data-match-back style="background:none;border:0;${matchStep?'':'visibility:hidden'}">← Back</button><span class="muted" style="font-size:.8rem">${matchStep+1} of 4</span></div>`;}
  function startMatch(){matchStep=0;renderMatch();showDialog('#matchDialog');track('rv_match_open');}
  async function chooseMatch(value){matchChoices[matchStep]=value;if(matchStep<3){matchStep++;renderMatch();return;}closeDialog($('#matchDialog'));const query=matchChoices.filter(Boolean).join(' ');if($('#filterForm'))$('#filterForm').reset();await search(query);track('rv_match_complete',{result_count:state.result?.items.length||0});}
  function assistantAnswer(question){
    if(!unit)return 'Open an RV listing to ask about that specific unit.';
    const q=question.toLowerCase(),s=unit.specs;
    let answer='';
    if(/sleep|people|person|bunk/.test(q)){answer=unit.sleeps?`The structured listing says this RV sleeps <b>${unit.sleeps}</b>. Confirm which beds and convertible spaces are included for your group.`:'Sleeping capacity is not provided in this unit’s structured specifications. I won’t estimate it from the photos or RV type. A specialist can confirm the exact sleeping layout.';}
    else if(/price|cost|available|availability|stock/.test(q)){answer=`The imported listing ${unit.price?'shows <b>'+money(unit.price)+'</b>':'does not include a public price'} and status <b>${esc(RVSearch.statusLabel(unit.status))}</b>, dated ${esc(unit.updated)}. A specialist must confirm the current price, fees and availability.`;}
    else if(/brochure|floorplan|floor plan|document/.test(q)){answer=(unit.floorplanImage?'<button class="text-link" data-floorplan style="border:0;background:none;padding:0">Open the floorplan</button>. ':'No floorplan image is attached. ')+(unit.brochure?`<button class="text-link" data-brochure style="border:0;background:none;padding:0">View ${esc(unit.brochure.label)}</button>. ${unit.brochure.sameYear?'The brochure matches the model year, but options can vary.':'This is a reference brochure from a different or unverified model year; it does not verify this unit’s equipment.'}`:'The factory brochure is not available in the imported library. We can request it.');}
    else if(/tow|truck|payload|weight|half ton/.test(q)){answer=`${s['GVWR (lb)']?'Listed GVWR: <b>'+esc(s['GVWR (lb)'])+' lb</b>. ':'GVWR is not listed. '}${s['Dry weight (lb)']?'Listed dry weight: <b>'+esc(s['Dry weight (lb)'])+' lb</b>. ':''}I cannot verify tow compatibility from this listing. Your specific vehicle’s ratings, hitch, payload and the loaded RV weights all matter. Ask a specialist to verify the combination.`;}
    else if(/spec|engine|chassis|length|water|fuel|mileage|slide/.test(q)){const selected=Object.entries(s).filter(([key])=>/chassis|engine|fuel|length|sleeps|slideouts|mileage|fresh water/i.test(key));answer=selected.length?'<ul>'+selected.map(([k,v])=>'<li><b>'+esc(k)+':</b> '+esc(v)+'</li>').join('')+'</ul>Source: this stock number’s structured dealer export. Missing values are not estimated.':'Detailed specifications are not supplied for this stock number. We can request them.';}
    else{
      const featureKeys=[['washer|dryer|laundry','washer / dryer'],['king','king bed'],['queen','queen bed'],['solar','solar'],['generator','generator'],['theater|theatre','theater seating'],['bath','bath and a half'],['office|desk','office'],['4x4|4wd','4x4'],['awd','AWD']];
      const found=featureKeys.find(([rx])=>new RegExp(rx).test(q));
      if(found){const label=found[1],has=RVSearch.featureRules[label].test(RVSearch.featureText(unit));const sentences=(unit.searchText||'').split(/(?<=[.!?])\s+/);const excerpt=sentences.find(x=>RVSearch.featureRules[label].test(x));answer=has?`The listing mentions <b>${esc(label)}</b>. ${excerpt?'<blockquote style="margin:12px 0;padding-left:12px;border-left:2px solid #9ab0c6">'+esc(excerpt.slice(0,650))+'</blockquote>':''}A listing mention may refer to prep, standard model equipment or an option. Confirm what is installed on stock #${esc(unit.stock)}.`:`I don’t see a confirmed ${esc(label)} detail in the available listing. That does not mean the RV lacks it. Ask your specialist to check this stock number.`;}
      else answer='I can help with this listing’s specs, sleeping capacity, pricing, documents and listed equipment. Your question needs a specialist to confirm details beyond that information.';
    }
    return answer+`<p style="margin-top:15px"><button class="text-link" style="background:none;border:0;padding:0" data-assistant-lead="${esc(question)}">Ask a specialist to verify this ${svg('arrow')}</button></p>`;
  }
  $('#assistantForm').addEventListener('submit',e=>{e.preventDefault();if(!e.currentTarget.reportValidity())return;$('#assistantAnswer').innerHTML=assistantAnswer($('#assistantInput').value);track('listing_question',{stock:unit?.stock});});
  let photoIndex=0, viewerMode='photos';
  function openPhoto(index){if(!unit?.photos?.length)return;viewerMode='photos';photoIndex=(index+unit.photos.length)%unit.photos.length;$('#viewerTitle').textContent=title(unit);$('#viewerContent').innerHTML=`<img src="${esc(unit.photos[photoIndex])}" alt="${esc(title(unit))} — photo ${photoIndex+1}">`;$('#viewerCount').textContent=(photoIndex+1)+' / '+unit.photos.length;$$('[data-photo-step]').forEach(b=>b.hidden=false);$('#viewerExternal').hidden=true;showDialog('#viewerDialog');}
  function showMedia(kind){
    if(!unit)return;viewerMode=kind;const viewer=$('#viewerContent');$$('[data-photo-step]').forEach(b=>b.hidden=true);$('#viewerCount').textContent='';const external=$('#viewerExternal');external.hidden=true;
    if(kind==='floorplan'&&unit.floorplanImage){$('#viewerTitle').textContent='Floorplan · '+unit.model+' '+unit.floorplan;viewer.innerHTML=`<img src="${esc(unit.floorplanImage)}" alt="${esc(title(unit))} floorplan">`;}
    else if(kind==='brochure'&&unit.brochure){$('#viewerTitle').textContent=unit.brochure.label;viewer.innerHTML=`<iframe src="${esc(unit.brochure.url)}" title="${esc(unit.brochure.label)}"></iframe>`;external.href=unit.brochure.url;external.textContent='Open or download PDF';external.hidden=false;$('#viewerCount').textContent=unit.brochure.sameYear?'Confirm stock-specific options':'Reference model year; equipment may differ';}
    else if(kind==='video'&&unit.video){$('#viewerTitle').textContent='Related model video';viewer.innerHTML=`<iframe src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(unit.video)}?autoplay=1&rel=0" title="Related model video" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>`;}
    else if(kind==='tour'&&unit.tour){$('#viewerTitle').textContent='Listed 360° tour';viewer.innerHTML=`<iframe src="${esc(unit.tour)}" title="Listed 360 degree RV tour" allowfullscreen sandbox="allow-scripts allow-same-origin allow-popups"></iframe>`;external.href=unit.tour;external.textContent='Open tour in a new tab';external.hidden=false;}
    else return;showDialog('#viewerDialog');track('resource_open',{stock:unit.stock,kind});
  }
  function calculate(){if(!unit?.price||!$('#calcDown'))return;const result=MHSCore.estimatePayment(unit.price,Number($('#calcDown').value),Number($('#calcApr').value),Number($('#calcTerm').value));$('#calcResult').textContent=result==null?'Check inputs':'$'+Math.round(result).toLocaleString()+'/mo';}
  async function renderSaved(){if(!$('#savedGrid'))return;try{await getCatalog();const list=saved.map(s=>catalog.items.find(u=>u.stock===s)).filter(Boolean);$('#savedCount').textContent=list.length+' saved RV'+(list.length===1?'':'s')+' · Stored on this device';$('#savedGrid').innerHTML=list.length?list.map(u=>card(u)).join(''):`<div class="empty-state"><h3>Your next adventure starts with a shortlist.</h3><p>Tap the heart on any RV to keep it here. Your saved RVs stay on this device.</p><a class="button" href="${base}index.html#inventory">Explore RVs ${svg('arrow')}</a></div>`;refreshSaved();}catch(_){$('#savedGrid').innerHTML='<p>Saved inventory could not load. Please refresh or try again later.</p>';}}
  let comparisonInitialized=false;
  async function renderCompare(){if(!$('#comparison'))return;try{await getCatalog();const q=new URLSearchParams(location.search).get('stocks');if(q&&!comparisonInitialized){compared=q.split(',').filter(s=>catalog.items.some(u=>u.stock===s)).slice(0,3);write('mhsrv-compare',compared);}
    comparisonInitialized=true;
    const list=compared.map(s=>catalog.items.find(u=>u.stock===s)).filter(Boolean);
    if(!list.length){const emptyUrl=new URL(location.href);emptyUrl.searchParams.delete('stocks');history.replaceState(null,'',emptyUrl);$('#comparison').innerHTML=`<div class="empty-state"><h3>Find your favorites. See the differences.</h3><p>Select Compare on up to three RVs to compare prices, dimensions, listed sleeping capacity and resources.</p><a class="button" href="${base}index.html#inventory">Start exploring</a></div>`;refreshSaved();return;}
    const rows=[['Listed price',u=>money(u.price)],['Condition',u=>u.condition==='new'?'New':'Pre-owned'],['RV type',u=>RVSearch.labels[u.type]],['Length',u=>u.length?u.length+' ft':'Not listed'],['Sleeping capacity',u=>u.sleeps?'Sleeps '+u.sleeps:'Not listed — ask us'],['Slideouts',u=>u.slides==null?'Not listed':u.slides],['Fuel',u=>u.fuel==='n/a'?'Towable':u.fuel||'Not listed'],['Mileage',u=>u.mileage==null?'Not listed':u.mileage.toLocaleString()+' mi'],['GVWR',u=>u.gvwr?u.gvwr.toLocaleString()+' lb':'Not listed'],['Location',u=>u.city+', '+u.state],['Listing status',u=>RVSearch.statusLabel(u.status)],['Floorplan',u=>u.hasFloorplan?'Available':'Request from specialist'],['Video',u=>u.hasVideo?'Related model video':'Request a walk-through'],['Brochure',u=>u.hasBrochure?'Available — check model year':'Request from specialist']];
    $('#comparison').innerHTML=`<div class="compare-scroll"><table class="comparison"><caption class="muted" style="text-align:left;padding:18px">Compare ${list.length} RVs. Missing values are not estimates.</caption><thead><tr><th scope="col">Your shortlist</th>${list.map(u=>`<th scope="col">${u.image?'<img src="'+esc(u.image)+'" alt="'+esc(title(u))+'" width="220" height="140">':''}<h3>${esc(title(u))}</h3><small>#${esc(u.stock)}</small><br><button class="reset-button" data-remove-compare="${esc(u.stock)}">Remove</button></th>`).join('')}</tr></thead><tbody>${rows.map(([label,get])=>`<tr><th scope="row">${label}</th>${list.map(u=>'<td>'+esc(get(u))+'</td>').join('')}</tr>`).join('')}<tr><th scope="row">Take a closer look</th>${list.map(u=>`<td><a class="button" href="${unitHref(u)}">Explore this RV</a><button class="button outline" data-lead="Compare my RV options" data-stock="${esc(u.stock)}">Ask a specialist</button></td>`).join('')}</tr></tbody></table></div><p class="data-note">Equipment and current availability must be confirmed for each stock number. Prices exclude applicable taxes, title, license and fees.</p>`;
    const url=new URL(location.href);url.searchParams.set('stocks',compared.join(','));history.replaceState(null,'',url);refreshSaved();
    }catch(_){$('#comparison').textContent='Comparison could not load. Please refresh or try again later.';}}
  let reviewData=null,reviewLimit=12;
  async function renderReviews(){if(!$('#reviewGrid'))return;try{if(!reviewData){const r=await fetch(base+'customer-stories.json');if(!r.ok)throw 0;reviewData=await r.json();}const q=RVSearch.norm($('#reviewSearch')?.value||new URLSearchParams(location.search).get('brand')||'');if($('#reviewSearch')&&!$('#reviewSearch').value&&q)$('#reviewSearch').value=q;const aliases={'thor motor coach':'thor','dynamax corp':'dynamax','fleetwood rv':'fleetwood'};const key=aliases[q]||q;const list=reviewData.filter(r=>!key||RVSearch.norm(r.title+' '+r.text).includes(key));$('#reviewCount').textContent=list.length.toLocaleString()+' customer stories';$('#reviewGrid').innerHTML=list.length?list.slice(0,reviewLimit).map(r=>`<article class="review-card"><h3><a href="${base}reviews/${encodeURIComponent(r.slug)}.html">${esc(r.title)}</a></h3><p>“${esc(r.text.slice(0,260))}${r.text.length>260?'…':''}”</p><small>${esc(r.date)}</small><a class="text-link" href="${base}reviews/${encodeURIComponent(r.slug)}.html">Read the story ${svg('arrow')}</a></article>`).join(''):'<div class="empty-state"><h3>No stories match those words.</h3><p>Try a brand name or a broader search.</p></div>';$('#moreReviews').hidden=reviewLimit>=list.length;}catch(_){$('#reviewCount').textContent='More customer stories could not load. Please try again later.';}}
  document.addEventListener('click',async e=>{
    const b=e.target.closest('button,a');if(!b)return;
    if(b.hasAttribute('data-close')){closeDialog(b.closest('dialog'));return;}
    if(b.hasAttribute('data-menu')){const open=$('#mobileNav').classList.toggle('open');b.setAttribute('aria-expanded',String(open));b.setAttribute('aria-label',open?'Close menu':'Open menu');return;}
    if(b.hasAttribute('data-save')){toggleSave(b.dataset.save);return;}
    if(b.hasAttribute('data-clear-compare')){compared=[];write('mhsrv-compare',[]);refreshSaved();renderCompare();return;}
    if(b.hasAttribute('data-remove-compare')){toggleCompare(b.dataset.removeCompare,false);return;}
    if(b.hasAttribute('data-lead')){openLead(b.dataset.lead,b.dataset.stock||'');return;}
    if(b.hasAttribute('data-query')){if($('#filterForm'))$('#filterForm').reset();search(b.dataset.query);return;}
    if(b.hasAttribute('data-suggest-query')){e.preventDefault();search(b.dataset.suggestQuery);return;}
    if(b.hasAttribute('data-match')){startMatch();return;}
    if(b.hasAttribute('data-match-choice')){chooseMatch(b.dataset.matchChoice);return;}
    if(b.hasAttribute('data-match-back')){matchStep=Math.max(0,matchStep-1);renderMatch();return;}
    if(b.hasAttribute('data-filter-open')){$('#filters').classList.add('open');document.body.style.overflow='hidden';$('.filter-close').focus();return;}
    if(b.hasAttribute('data-filter-close')){$('#filters').classList.remove('open');document.body.style.overflow='';$('[data-filter-open]').focus();return;}
    if(b.hasAttribute('data-reset-filters')){$('#filterForm').reset();renderResults();return;}
    if(b.hasAttribute('data-clear-search')){$('#filterForm').reset();state.q='';$('#sortSelect').value='recommended';search('');return;}
    if(b.hasAttribute('data-clear-query')){search('');return;}
    if(b.hasAttribute('data-retry')){search(state.q,false);return;}
    if(b.id==='loadMore'){state.limit+=12;renderResults({preserveLimit:true});return;}
    if(b.hasAttribute('data-assistant')){showDialog('#assistantDialog');return;}
    if(b.hasAttribute('data-ask')){$('#assistantInput').value=b.dataset.ask;$('#assistantAnswer').innerHTML=assistantAnswer(b.dataset.ask);return;}
    if(b.hasAttribute('data-assistant-lead')){closeDialog($('#assistantDialog'));openLead('Verify an RV detail',unit?.stock);$('#leadMessage').value=b.dataset.assistantLead;return;}
    if(b.hasAttribute('data-photo')){openPhoto(+b.dataset.photo);return;}
    if(b.hasAttribute('data-photo-step')){openPhoto(photoIndex+(+b.dataset.photoStep));return;}
    if(b.hasAttribute('data-floorplan')){showMedia('floorplan');return;}if(b.hasAttribute('data-brochure')){showMedia('brochure');return;}if(b.hasAttribute('data-video')){showMedia('video');return;}if(b.hasAttribute('data-tour')){showMedia('tour');return;}
    if(b.hasAttribute('data-share')){try{if(navigator.share)await navigator.share({title:document.title,url:location.href});else{await navigator.clipboard.writeText(location.href);toast('Link copied.');}}catch(error){if(error.name!=='AbortError')toast('Copy the page address to share this RV.');}return;}
    if(b.id==='moreReviews'){reviewLimit+=12;renderReviews();return;}
  });
  document.addEventListener('change',e=>{if(e.target.hasAttribute('data-compare'))toggleCompare(e.target.dataset.compare,e.target.checked);});
  document.addEventListener('click',e=>{if(!e.target.closest('.search-wrap'))hideSuggestions();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('#filters')?.classList.remove('open');if(!$('dialog[open]'))document.body.style.overflow='';hideSuggestions();}if($('#viewerDialog').open&&viewerMode!=='photos')return;if($('#viewerDialog').open&&['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();openPhoto(photoIndex+(e.key==='ArrowRight'?1:-1));}});
  $('#searchForm')?.addEventListener('submit',e=>{e.preventDefault();if(suggestIndex>=0&&!$('#suggestions').hidden){const options=$$('[role=option]',$('#suggestions'));options[suggestIndex]?.click();}else search($('#rvSearch').value);});
  $('#rvSearch')?.addEventListener('input',()=>{clearTimeout(suggestTimer);suggestTimer=setTimeout(suggest,170);});
  $('#rvSearch')?.addEventListener('keydown',e=>{if(!['ArrowDown','ArrowUp'].includes(e.key)||$('#suggestions').hidden)return;e.preventDefault();const opts=$$('[role=option]',$('#suggestions'));suggestIndex=(suggestIndex+(e.key==='ArrowDown'?1:-1)+opts.length)%opts.length;opts.forEach((o,i)=>o.setAttribute('aria-selected',String(i===suggestIndex)));e.target.setAttribute('aria-activedescendant',opts[suggestIndex].id);});
  $('#filterForm')?.addEventListener('change',()=>renderResults());$('#sortSelect')?.addEventListener('change',()=>renderResults());
  ['calcDown','calcApr','calcTerm'].forEach(id=>$('#'+id)?.addEventListener('input',calculate));calculate();
  $('#reviewSearchForm')?.addEventListener('submit',e=>{e.preventDefault();reviewLimit=12;renderReviews();});
  window.addEventListener('storage',()=>{saved=read('mhsrv-saved');compared=read('mhsrv-compare').slice(0,3);refreshSaved();renderSaved();renderCompare();});
  document.addEventListener('error',e=>{if(e.target.tagName==='IMG'&&e.target.closest('.card-photo')){e.target.replaceWith(Object.assign(document.createElement('div'),{className:'photo-placeholder',textContent:'Photo unavailable · ask for a walk-through'}));}},true);
  refreshSaved();initInventory();renderSaved();renderCompare();renderReviews();
})();
