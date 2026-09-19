(function(root){
  'use strict';
  const norm=value=>String(value||'').normalize('NFKD').replace(/[’']/g,'').toLowerCase().replace(/[^a-z0-9.]+/g,' ').trim();
  const aliases={'thor':'thor motor coach','thor motor':'thor motor coach','entegra':'entegra coach','fleetwood rv':'fleetwood','dynamax corp':'dynamax','gulfstream':'gulf stream','midwest':'midwest automotive designs','heartland rv':'heartland','national':'national rv','american':'american coach','american eagle':'american coach','k z':'kz'};
  const brandKey=value=>aliases[norm(value)]||norm(value);
  const esc=value=>String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeUrl=value=>{try{const u=new URL(value);return u.protocol==='https:'?u.href:'';}catch(_){return '';}};
  function filterStories(stories,filters={}){
    const query=norm(filters.q),tokens=query.split(' ').filter(Boolean),brand=brandKey(filters.brand),type=norm(filters.type);
    return stories.filter(s=>{
      if(brand&&brandKey(s.brand)!==brand)return false;
      if(type&&norm(s.type)!==type)return false;
      if(!query)return true;
      if(brandKey(s.brand)===brandKey(query))return true;
      const haystack=norm([s.title,s.text,s.stock,s.year,s.brand,s.model,s.type,s.buyer,s.location].join(' '));
      return tokens.every(t=>haystack.includes(t));
    });
  }
  function initialFilters(search,stories){
    const params=new URLSearchParams(search),requested=params.get('brand')||'';
    const match=stories.find(s=>s.brand&&brandKey(s.brand)===brandKey(requested));
    return {q:params.get('q')||(!match&&requested?requested:''),brand:match?match.brand:'',type:params.get('type')||''};
  }
  function filterUrl(href,filters){
    const url=new URL(href);['q','brand','type'].forEach(k=>{if(filters[k])url.searchParams.set(k,filters[k]);else url.searchParams.delete(k);});return url;
  }
  function storyCard(s,base=''){
    const href=base+'reviews/'+encodeURIComponent(s.slug)+'.html';
    const meta=[s.type,s.stock?'Stock #'+s.stock:'',s.location,s.dateLabel].filter(Boolean).join(' · ');
    return `<article class="review-card"><h3><a href="${href}">${esc(s.title)}</a></h3><p>“${esc(s.text.slice(0,260))}${s.text.length>260?'…':''}”</p><small>${esc(meta)}</small><a class="text-link" href="${href}">Read the story →</a></article>`;
  }
  function googlePlace(place,base=''){
    const attributions=(Array.isArray(place.attributions)?place.attributions:[]).filter(a=>a.provider).map(a=>safeUrl(a.url)?'<a href="'+esc(safeUrl(a.url))+'" target="_blank" rel="noopener">'+esc(a.provider)+'</a>':'<span>'+esc(a.provider)+'</span>').join(' · ');
    const cards=[];
        for(const review of place.reviews||[]){
          if(!Number.isInteger(review.rating)||review.rating<1||review.rating>5||!review.author||!safeUrl(review.url))continue;
          const profile=safeUrl(review.authorUrl),avatar=safeUrl(review.authorPhoto);
          cards.push(`<article class="review-card"><div class="google-review-author">${avatar?'<img src="'+esc(avatar)+'" alt="" width="40" height="40" loading="lazy">':''}${profile?'<a href="'+esc(profile)+'" target="_blank" rel="noopener">'+esc(review.author)+'</a>':'<strong>'+esc(review.author)+'</strong>'}</div><p class="google-review-rating" aria-label="${review.rating} out of 5 stars">${'★'.repeat(review.rating)}${'☆'.repeat(5-review.rating)}</p>${review.date?'<small>'+esc(review.date)+'</small>':''}<p class="google-review-text">${esc(review.text||'')}</p><a class="google-review-source" href="${esc(safeUrl(review.url))}" target="_blank" rel="noopener">Read this review on Google Maps ↗</a></article>`);
        }
        const rating=Number.isFinite(place.rating)&&place.rating>=1&&place.rating<=5?place.rating.toFixed(1)+' / 5':'';
        const total=Number.isInteger(place.count)&&place.count>=0?place.count.toLocaleString()+' ratings':'';
        return (`<div class="google-place"><h3>${esc(place.name)}</h3><p>${esc([rating,total].filter(Boolean).join(' · '))}</p><div class="review-grid">${cards.join('')||'<p>No review excerpts were returned. View the business profile on Google Maps.</p>'}</div>${safeUrl(place.url)?'<a class="google-review-source" href="'+esc(safeUrl(place.url))+'" target="_blank" rel="noopener">View this location on Google Maps ↗</a>':''}<div class="google-provider-attribution"><img class="google-maps-logo" src="${esc(base)}assets/google-maps-attribution.svg" alt="Google Maps" height="18">${attributions}</div></div>`);
  }
  const api={norm,brandKey,filterStories,initialFilters,filterUrl,storyCard,googlePlace};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(!root.document)return;
  const doc=root.document,$=selector=>doc.querySelector(selector);
  doc.addEventListener('error',event=>{if(event.target.matches?.('.review-photo'))event.target.hidden=true;},true);
  const grid=$('#reviewGrid[data-reviews-v2]');if(!grid)return;
  const base=JSON.parse($('#siteConfig')?.textContent||'{}').base||'';
  const form=$('#reviewSearchForm'),input=$('#reviewSearch'),brand=$('#reviewBrand'),type=$('#reviewType'),more=$('#moreReviews'),count=$('#reviewCount');
  let stories=null,limit=36,initial=true,pending=null;
  async function load(){
    if(stories)return stories;
    if(!pending)pending=fetch(base+'customer-stories.json').then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{if(!Array.isArray(data))throw new Error();stories=data;return data;}).catch(error=>{pending=null;throw error;});
    return pending;
  }
  function readFilters(){return {q:input.value.trim(),brand:brand.value,type:type.value};}
  function render(){
    const filters=readFilters(),results=filterStories(stories,filters),shown=Math.min(limit,results.length),remaining=results.length-shown;
    grid.innerHTML=results.length?results.slice(0,limit).map(s=>storyCard(s,base)).join(''):'<div class="empty-state"><h3>No stories match those filters.</h3><p>Try a broader search, or clear your brand and RV type.</p><button class="button outline" type="button" data-review-clear>Clear filters</button></div>';
    count.textContent='Showing '+shown.toLocaleString()+' of '+results.length.toLocaleString()+' matching stories · '+stories.length.toLocaleString()+' total';
    more.hidden=!remaining;more.textContent='Load '+Math.min(36,remaining)+' more · '+remaining.toLocaleString()+' remaining';
    history.replaceState(null,'',filterUrl(location.href,filters));
  }
  async function update(reset=true){
    if(reset)limit=36;
    try{
      await load();
      if(initial){const f=initialFilters(location.search,stories);input.value=f.q;brand.value=f.brand;type.value=f.type;initial=false;}
      render();
    }catch(_){count.textContent='Search could not load. The stories below and our page directory are still available.';}
  }
  function clear(){initial=false;input.value='';brand.value='';type.value='';history.replaceState(null,'',filterUrl(location.href,{}));update();}
  input.addEventListener('input',()=>{initial=false;update();});
  brand.addEventListener('change',()=>{initial=false;update();});type.addEventListener('change',()=>{initial=false;update();});
  form.addEventListener('submit',event=>{event.preventDefault();initial=false;update();});
  form.addEventListener('reset',event=>{event.preventDefault();clear();});
  grid.addEventListener('click',event=>{if(event.target.closest('[data-review-clear]'))clear();});
  more.addEventListener('click',()=>{limit+=36;update(false);});
  update();

  async function loadGoogle(){
    const status=$('#googleReviewsStatus'),target=$('#googleReviewsGrid'),link=$('#googleReviewsLink');
    try{
      const configResponse=await fetch(base+'google-reviews.config.json',{cache:'no-store'});
      if(!configResponse.ok)return;
      const settings=await configResponse.json();
      if(safeUrl(settings.googleMapsUrl))link.href=safeUrl(settings.googleMapsUrl);
      if(!settings.endpoint)return;
      const endpoint=safeUrl(settings.endpoint);if(!endpoint)throw new Error();
      const response=await fetch(endpoint,{cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(12000)});
      if(!response.ok)throw new Error();
      const data=await response.json();
      const age=Date.now()-Date.parse(data.fetchedAt);
      if(data.source!=='google-places-api'||!Number.isFinite(age)||age< -60000||age>300000||!Array.isArray(data.locations))throw new Error();
      const sections=[];
      for(const place of data.locations)sections.push(googlePlace(place,base));
      if(!sections.length)throw new Error();
      $('#googleReviewsTitle').textContent='What customers say on Google Maps.';
      target.classList.remove('review-grid');target.innerHTML=sections.join('');
      status.textContent='Reviews supplied by Google Maps, ordered by relevance. All returned ratings are included; up to five reviews per location.';
    }catch(_){status.textContent='Google review excerpts are unavailable right now. You can read customer reviews directly on Google Maps.';target.replaceChildren();}
  }
  loadGoogle();
})(typeof window!=='undefined'?window:globalThis);
