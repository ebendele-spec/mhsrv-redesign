/* ============ SHARED SITE FOOTER ============
   Single source of truth for the footer on every page (SRP, VDPs, reviews,
   info pages). Include with:  <script src="footer.js" defer></script>
   (use ../footer.js from /units and /reviews — the base path is derived
   from the script tag automatically).
   On pages with a fixed bottom .dock, the dark footer extends beneath the
   dock (body padding-bottom is zeroed) so no page-background gap shows. */
(function(){
  var script=document.currentScript;
  function init(){
    if(document.querySelector('.sitefoot'))return;
    var src=(script&&script.getAttribute('src'))||'footer.js';
    var base=src.slice(0,src.lastIndexOf('footer.js'));
    var css=''+
/* dark canvas below the document so short pages never show a light gap
   between the footer and the fixed dock (body bg stops propagating) */
'html{background:#1C1F23}'+
'.sitefoot{background:#1C1F23;color:#fff;margin-top:30px;padding:24px 0 28px;font-family:\'Barlow\',system-ui,sans-serif}'+
'.sitefoot.sf-dock{padding-bottom:calc(84px + env(safe-area-inset-bottom))}'+
'.sf-wrap{max-width:520px;margin:0 auto;padding:0 16px;display:grid;gap:18px}'+
'@media(min-width:760px){.sf-wrap{max-width:960px;grid-template-columns:repeat(3,1fr)}}'+
'.sf-loc b{font-family:\'Barlow Condensed\',sans-serif;font-weight:700;font-size:17px;text-transform:uppercase;letter-spacing:.03em;color:#FFC91F}'+
'.sf-loc p{font-size:13px;line-height:1.5;opacity:.8;margin:4px 0 0}'+
'.sf-loc a{color:#fff;font-weight:600;text-decoration:none;font-size:13.5px}'+
'.sf-legal{max-width:520px;margin:0 auto;padding:0 16px}'+
'@media(min-width:760px){.sf-legal{max-width:960px}}'+
'.sf-fine{text-align:center;margin:18px auto 0;font-size:11.5px;line-height:1.5;color:#9AA3AD;max-width:640px}'+
'.sf-discwrap{text-align:center;margin-top:14px}'+
'.sf-discbtn{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.06);color:#9AA3AD;font-weight:600;font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;padding:9px 18px;border-radius:99px;border:1px solid rgba(255,255,255,.16);cursor:pointer;font-family:\'Barlow Condensed\',sans-serif;transition:.2s}'+
'.sf-discbtn:hover{color:#fff;border-color:rgba(255,201,31,.5)}'+
'.sf-discbtn .sf-dch{color:#FFC91F;font-size:13px;transition:transform .25s;display:inline-block}'+
'.sf-discbtn.open .sf-dch{transform:rotate(45deg)}'+
'.sf-discbody[hidden]{display:none}'+
'.sf-discbody{text-align:left;margin-top:16px;font-size:11.5px;line-height:1.6;color:#9AA3AD}'+
'.sf-discbody p{margin-top:10px}'+
'.sf-discbody b{color:#C4CCD4}'+
'.sf-discbody a{color:#FFC91F}';
    var st=document.createElement('style');
    st.textContent=css;
    document.head.appendChild(st);
    var foot=document.createElement('div');
    foot.className='sitefoot';
    foot.innerHTML=''+
'<div class="sf-wrap">'+
  '<div class="sf-loc"><b>Texas — Alvarado</b><p>5411 South I-35W, Alvarado, TX 76009<br>Mon–Sat 8:30–5:30 · Sun closed</p><a href="tel:8003356054">800-335-6054</a></div>'+
  '<div class="sf-loc"><b>Alabama — Montgomery</b><p>4504 Troy Hwy, Montgomery, AL 36116<br>Mon–Sat 8:30–5:30 · Sun closed</p><a href="tel:3342880331">334-288-0331</a></div>'+
  '<div class="sf-loc"><b>California — Coming Soon</b><p>77840 Varner Rd, Palm Desert, CA 92211</p><a href="tel:8006103934">800-610-3934</a></div>'+
'</div>'+
'<div class="sf-legal">'+
  '<p class="sf-fine">*#1 in the world per Stats Surveys Inc. for American-built motorhomes sold at a single location. Prices &amp; payments estimated; see dealer for details.</p>'+
  '<div class="sf-discwrap">'+
    '<button type="button" class="sf-discbtn" aria-expanded="false">Legal &amp; pricing disclaimer <span class="sf-dch">+</span></button>'+
    '<div class="sf-discbody" hidden>'+
      '<p>All material copyright © Motor Home Specialist ( MHSRV.com ). All rights are reserved. No part of any material on this web site may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of Motor Home Specialist. *Information deemed reliable, but not guaranteed. Features &amp; options subject to change without notice. Weights &amp; measurements are estimates only. Verify before purchase.</p>'+
      '<p><b>DISCLAIMER:</b> +Due to industry shortages, product changes, and continual price increases the M.S.R.P. on “coming soon” and “on order” units must be estimated and based on the manufacturer’s information provided to MHS at the time of order. M.S.R.P.s may be slightly higher or lower when they ultimately arrive at MHS. *#1 in the world or #1 in Texas references are per the official Stats Surveys Inc. for American-built Motorhomes sold at a single location. *MINIMUM 25% OFF MSRP ON MOST RVs DISCOUNT DOES NOT APPLY TO ALL NEW RVs including, but not restricted to, CLASS B, CLASS C &amp; B+, CLASS A, TRAVEL TRAILER RVs, AND MERCEDES. CONTACT SALES FOR UP-TO-DATE SALE PRICING AND PERCENTAGE DISCOUNTS ON ALL PRODUCTS. The % discount shown on a unit is rounded to the nearest "whole number" percentage. The sale price is fractionally higher or lower than the percentage shown. All sale prices include all other incentives, offers, and rebates offered by MHSRV or any other manufacturer unless specified in writing. Motor Home Specialist’s prices, sales, and offers are subject to change without notice and Motor Home Specialist reserves the right to price any unit, including those spotlighted or specially marked, before, during or after a sale or promotion of any kind or type of advertisement including that of an email blast, TV spot, written ad or any other type of advertisement at any price they wish after any sale or promotion ends to ultimately sell every unit. *(w.a.c.) Estimated payment figured at 7.99% on 20 yrs with 10% down on units above $49,001. Units below $49,000, estimated payment figured at 7.99% on 15yrs with 20% down. Price and payment do NOT include TT&amp;L or any other fees that may apply. Used units and RVs under $50K are subject to shorter terms, higher rates, and restrictions. Call MHSRV’s finance department for complete details. Some videos and photos may not represent the actual vehicle for sale. Manufacturer’s standards and features subject to change without notice. ALL weights, measurements, sizes, etc. including, but not limited to, TVs, bed sizes, tank capacities, lengths, GVWRs, etc., are all either estimated or information provided by the manufacturer and not guaranteed to be 100% accurate by MHSRV or the manufacturer due to continual product changes and enhancements. All deposits are NON-REFUNDABLE unless otherwise specified in writing. Upon receipt of deposit seller (MHSRV) agrees to hold the selected unit and prepare it for delivery and orientation to the buyer. Buyer understands and agrees that by leaving said NON-REFUNDABLE deposit they are asking MHS to prepare their purchase for delivery and orientation and should they fail to pay for their purchase by the specified delivery date they will forfeit the NON-REFUNDABLE deposit. MHS retains the right to apply partial or all said NON-REFUNDABLE deposit to a future purchase. Online info deemed reliable, but not guaranteed. All materials are copyrighted by Motor Home Specialist (MHSRV.com). All rights are reserved. No part of any material on this website may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of Motor Home Specialist. Thank you so much for shopping with us at Motor Home Specialist. If you have any further questions about sale prices, promotions, finance, etc. please call 800-335-6054 or local 817-790-7771. 100 OBanion Way Alvarado, TX. 76009.</p>'+
      '<p>View your <a href="'+base+'your-california-privacy-rights.html">California Privacy Rights</a>. View the <a href="'+base+'ccpa-notice.html">California Consumer Privacy Act Notice for California Consumers</a>.</p>'+
    '</div>'+
  '</div>'+
'</div>';
    var dock=document.querySelector('.dock');
    if(dock&&getComputedStyle(dock).position==='fixed'){
      foot.classList.add('sf-dock');
      document.body.style.paddingBottom='0';
      document.body.insertBefore(foot,dock);
    }else{
      document.body.appendChild(foot);
    }
    var btn=foot.querySelector('.sf-discbtn'),body=foot.querySelector('.sf-discbody');
    btn.addEventListener('click',function(){
      var open=body.hidden;
      body.hidden=!open;
      btn.classList.toggle('open',open);
      btn.setAttribute('aria-expanded',open?'true':'false');
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();
