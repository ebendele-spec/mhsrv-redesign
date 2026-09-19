/* Unit-specific interaction: full galleries, inline media and transparent estimates. */
(function(){
  'use strict';
  const main=document.querySelector('[data-detail-v2]');if(!main)return;
  const unit=JSON.parse(document.getElementById('unitData').textContent),$=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
  const photos=unit.photos||[],track=$('#inlinePhotoTrack');let inlineIndex=0,viewerIndex=0,viewerPhoto=false,dragged=false;
  const currency=n=>'$'+Math.round(n).toLocaleString('en-US');
  function imageFailure(img){
    if(img.dataset.retried!=='true'&&img.src.includes(';width=')){
      img.dataset.retried='true';img.src=img.src.split(';width=')[0];return;
    }
    const note=document.createElement('span');note.className='media-unavailable';note.textContent='This photo is unavailable. Try another photo or request a walk-through.';
    img.replaceWith(note);
  }
  document.addEventListener('error',e=>{if(e.target instanceof HTMLImageElement&&(e.target.closest('.inline-gallery')||e.target.closest('#viewerContent')||e.target.hasAttribute('data-document-image')))imageFailure(e.target);},true);
  $$('img[data-document-image],.inline-gallery img').forEach(img=>{if(img.complete&&img.naturalWidth===0)imageFailure(img);});
  function go(index){
    if(!track||!photos.length)return;
    inlineIndex=(index+photos.length)%photos.length;
    track.scrollTo({left:inlineIndex*track.clientWidth,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  function updateInline(){
    if(!track||!track.clientWidth)return;inlineIndex=Math.min(photos.length-1,Math.round(track.scrollLeft/track.clientWidth));
    $('#inlinePhotoCount').textContent=(inlineIndex+1)+' / '+photos.length;
    $('.inline-gallery-toolbar [data-photo]').dataset.photo=String(inlineIndex);
    $$('.inline-thumb').forEach((b,i)=>b.setAttribute('aria-current',String(i===inlineIndex)));
    const thumb=$(`.inline-thumb[data-inline-photo="${inlineIndex}"]`),rail=$('.inline-thumbnails');
    if(thumb&&rail&&(thumb.offsetLeft<rail.scrollLeft||thumb.offsetLeft+thumb.offsetWidth>rail.scrollLeft+rail.clientWidth))rail.scrollTo({left:thumb.offsetLeft-rail.clientWidth/2+thumb.clientWidth/2,behavior:'smooth'});
  }
  function openPhoto(index){
    if(!photos.length)return;viewerPhoto=true;viewerIndex=(index+photos.length)%photos.length;
    $('#viewerTitle').textContent=[unit.year,unit.brand,unit.model,unit.floorplan].join(' ');
    const img=document.createElement('img');img.src=photos[viewerIndex];img.alt=`${unit.brand} ${unit.model} — listing photo ${viewerIndex+1}`;img.draggable=false;
    $('#viewerContent').replaceChildren(img);$('#viewerCount').textContent=(viewerIndex+1)+' / '+photos.length;
    $$('[data-photo-step]').forEach(b=>b.hidden=false);$('#viewerExternal').hidden=true;
    if(!$('#viewerDialog').open)window.MHSApp.showDialog('#viewerDialog');
  }
  function step(delta){if(viewerPhoto)openPhoto(viewerIndex+delta);}
  $('#viewerDialog').addEventListener('close',()=>viewerPhoto=false);
  document.addEventListener('click',e=>{if(e.target.closest('[data-floorplan],[data-brochure],[data-tour],[data-video]'))viewerPhoto=false;});
  function gestures(el,advance,isInline){
    if(!el)return;let start=null,lastWheel=0;
    el.addEventListener('pointerdown',e=>{if(e.button!==0)return;start={x:e.clientX,y:e.clientY,left:el.scrollLeft,id:e.pointerId,touch:e.pointerType==='touch'};dragged=false;});
    el.addEventListener('pointermove',e=>{
      if(!start||start.touch)return;const dx=e.clientX-start.x,dy=e.clientY-start.y;
      if(Math.abs(dx)>10&&Math.abs(dx)>Math.abs(dy)){dragged=true;el.setPointerCapture(e.pointerId);if(isInline){el.style.scrollSnapType='none';el.scrollLeft=start.left-dx;}e.preventDefault();}
    });
    const finish=e=>{if(!start)return;const dx=e.clientX-start.x,dy=e.clientY-start.y;
      if(isInline){el.style.scrollSnapType='';if(dragged)go(Math.round(el.scrollLeft/el.clientWidth));}
      else if(Math.abs(dx)>45&&Math.abs(dx)>Math.abs(dy)&&viewerPhoto){dragged=true;advance(dx<0?1:-1);}
      start=null;setTimeout(()=>dragged=false,150);
    };
    el.addEventListener('pointerup',finish);el.addEventListener('pointercancel',()=>{start=null;el.style.scrollSnapType='';});
    el.addEventListener('click',e=>{if(dragged){e.preventDefault();e.stopImmediatePropagation();}},true);
    // Native horizontal scrolling remains available in the inline gallery.
    if(!isInline)el.addEventListener('wheel',e=>{if(!viewerPhoto||Math.abs(e.deltaX)<Math.abs(e.deltaY)||Math.abs(e.deltaX)<8)return;e.preventDefault();if(Date.now()-lastWheel>350){lastWheel=Date.now();advance(e.deltaX>0?1:-1);}},{passive:false});
  }
  if(track){track.addEventListener('scroll',updateInline,{passive:true});track.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();go(inlineIndex+(e.key==='ArrowRight'?1:-1));}});gestures(track,delta=>go(inlineIndex+delta),true);new ResizeObserver(()=>{track.scrollLeft=inlineIndex*track.clientWidth;}).observe(track);}
  gestures($('#viewerContent'),step,false);
  document.addEventListener('click',e=>{
    const b=e.target.closest('[data-inline-photo],[data-inline-step],[data-inline-video]');if(!b)return;
    if(b.hasAttribute('data-inline-photo'))go(Number(b.dataset.inlinePhoto));
    if(b.hasAttribute('data-inline-step'))go(inlineIndex+Number(b.dataset.inlineStep));
    if(b.hasAttribute('data-inline-video')){
      const frame=document.createElement('iframe');frame.src='https://www.youtube-nocookie.com/embed/'+encodeURIComponent(b.dataset.inlineVideo)+'?autoplay=1&rel=0';frame.title='Related RV model video';frame.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen';frame.allowFullscreen=true;$('#inlineVideo').replaceChildren(frame);
    }
  });
  function calculate(source){
    if(!unit.price||!$('#calcDown'))return;
    const down=$('#calcDown'),range=$('#calcDownPercent'),term=$('#calcTerm'),apr=$('#calcApr'),guide=$('#calcTermGuide');
    if(source===range)down.value=Math.round(unit.price*Number(range.value)/100);
    const downValue=Number(down.value),aprValue=Number(apr.value),principal=unit.price-downValue;
    if(source!==range&&Number.isFinite(downValue))range.value=Math.max(0,Math.min(100,downValue/unit.price*100));
    $('#downPercentLabel').textContent=(downValue/unit.price*100).toFixed(1).replace(/\.0$/,'')+'%';
    const maxTerm=guide.checked?(principal<=20000?120:principal<=50000?180:240):240;
    Array.from(term.options).forEach(o=>o.disabled=Number(o.value)>maxTerm);
    if(Number(term.value)>maxTerm)term.value=String(maxTerm);
    const months=Number(term.value),result=down.value===''||apr.value===''||aprValue>36?null:MHSCore.estimatePayment(unit.price,downValue,aprValue,months);
    $('#calcResult').textContent=result==null?'Check your inputs':currency(result)+'/mo';
    if(result==null){$('#calcTotals').textContent='Enter a down payment from $0 to the listed price and an APR from 0% to 36%.';$('#pricePayment').textContent='Check calculator';$('#priceAssumptions').textContent='Correct the payment inputs below to see an estimate.';$('#detailFinanceLink').hidden=true;return;}
    $('#detailFinanceLink').hidden=false;
    $('#pricePayment').textContent=currency(result)+'/mo';
    $('#priceAssumptions').textContent=`${(downValue/unit.price*100).toFixed(1).replace(/\.0$/,'')}% down · ${aprValue}% illustrative APR · ${months} months. Taxes and fees excluded.`;
    $('#calcTotals').textContent=`Amount financed: ${currency(principal)} · Estimated total interest: ${currency(result*months-principal)} · ${months} payments. Figures exclude taxes and fees.`;
    $('#detailFinanceLink').href='../get-prequalified.html?'+new URLSearchParams({stock:unit.stock,monthly_payment:Math.round(result),down_payment:downValue,term:months,apr:aprValue});
  }
  [$('#calcDownPercent'),$('#calcDown'),$('#calcApr'),$('#calcTerm'),$('#calcTermGuide')].filter(Boolean).forEach(el=>el.addEventListener(el.tagName==='SELECT'||el.type==='checkbox'?'change':'input',()=>calculate(el)));
  window.MHSDetail={openPhoto,step,calculate};calculate();
})();
