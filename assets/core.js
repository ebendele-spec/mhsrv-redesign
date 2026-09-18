(function(root){
  'use strict';
  function estimatePayment(price,down,apr,months){
    if(![price,down,apr,months].every(Number.isFinite)||price<0||down<0||down>price||apr<0||months<=0)return null;
    const principal=price-down,r=apr/1200;
    return r===0?principal/months:principal*r/(1-Math.pow(1+r,-months));
  }
  async function submitLead(endpoint,data,transport=fetch){
    if(!data.name||!data.email||!/^\S+@\S+\.\S+$/.test(data.email))throw new Error('Please enter your name and a valid email address.');
    if(data.website)throw new Error('The form could not be sent. Please contact us directly.');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
    try{
      const response=await transport(endpoint,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(data),signal:controller.signal});
      if(!response.ok)throw new Error('Your request was not sent. Please try again or email us directly.');
      const result=await response.json();
      if(![true,'true'].includes(result.success)||/activat|confirm.*email/i.test(result.message||''))throw new Error('We could not confirm this form is ready to receive requests. Please email or call us directly.');
      return {accepted:true};
    }catch(error){
      if(error.name==='AbortError')throw new Error('The request timed out. Delivery is unconfirmed. Please email or call us directly.');
      throw error;
    }finally{clearTimeout(timer);}
  }
  root.MHSCore={estimatePayment,submitLead};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.MHSCore;
})(typeof window!=='undefined'?window:globalThis);
