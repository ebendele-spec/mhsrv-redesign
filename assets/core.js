(function(root){
  'use strict';
  function estimatePayment(price,down,apr,months){
    if(![price,down,apr,months].every(Number.isFinite)||price<0||down<0||down>price||apr<0||months<=0)return null;
    const principal=price-down,r=apr/1200;
    return r===0?principal/months:principal*r/(1-Math.pow(1+r,-months));
  }
  function validateContact(data){
    const name=String(data.name||'').trim(),email=String(data.email||'').trim(),phone=String(data.phone||data.preferred_phone||'').trim();
    if(!name)throw new Error('Please enter your name.');
    if(email&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))throw new Error('Please enter a valid email address, or leave email blank and provide a phone number.');
    const mainPhone=phone.replace(/\s*(?:ext\.?|x|#)\s*\d{1,6}\s*$/i,'');
    const digits=mainPhone.replace(/\D/g,'');
    if(phone&&(!/^\+?[\d\s().-]+$/.test(mainPhone)||digits.length<10||digits.length>15))throw new Error('Please enter a valid phone number, including the area or country code.');
    if(!email&&!phone)throw new Error('Please enter an email address or phone number so we can reply.');
    const preferred=String(data.preferred_contact||'').toLowerCase();
    if(preferred==='email'&&!email)throw new Error('Please add an email address for your preferred reply method.');
    if(['call','text','sms'].includes(preferred)&&!phone)throw new Error('Please add a phone number for your preferred reply method.');
    if(data.marketing_email_consent==='Yes'&&!email)throw new Error('Please add an email address or uncheck optional email offers.');
    if(data.marketing_sms_consent==='Yes'&&!phone)throw new Error('Please add a phone number or uncheck optional text offers.');
    return {name,email,phone};
  }
  async function submitLead(endpoint,data,transport=fetch){
    const contact=validateContact(data);
    if(data.website)throw new Error('The form could not be sent. Please contact us directly.');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
    try{
      const response=await transport(endpoint,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({...data,...contact,marketing_email_consent:data.marketing_email_consent==='Yes'?'Yes':'No',marketing_sms_consent:data.marketing_sms_consent==='Yes'?'Yes':'No'}),signal:controller.signal});
      if(!response.ok)throw new Error('Your request was not sent. Please try again or email us directly.');
      const result=await response.json();
      if(![true,'true'].includes(result.success)||/activat|confirm.*email/i.test(result.message||''))throw new Error('We could not confirm this form is ready to receive requests. Please email or call us directly.');
      return {accepted:true};
    }catch(error){
      if(error.name==='AbortError')throw new Error('The request timed out. Delivery is unconfirmed. Please email or call us directly.');
      throw error;
    }finally{clearTimeout(timer);}
  }
  root.MHSCore={estimatePayment,submitLead,validateContact};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.MHSCore;
})(typeof window!=='undefined'?window:globalThis);
