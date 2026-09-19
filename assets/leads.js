(function(root){
  'use strict';
  const ATTRIBUTION=['utm_source','utm_medium','utm_campaign','utm_content','utm_term','gclid','msclkid'];
  function serializeEntries(entries){
    const fields=new Map();
    for(const [key,value] of entries){
      const text=typeof value==='string'?value.trim():String(value);
      if(fields.has(key)){const previous=fields.get(key);fields.set(key,Array.isArray(previous)?[...previous,text]:[previous,text]);}
      else fields.set(key,text);
    }
    return Object.fromEntries(fields);
  }
  function validateIntake(data,core=root.MHSCore){
    core.validateContact(data);
    const email=String(data.email||'').trim(),confirmation=String(data.confirm_email||'').trim();
    if(email&&email.toLowerCase()!==confirmation.toLowerCase())throw new Error('Please confirm your email address; the two email entries must match.');
    if(!email&&confirmation)throw new Error('Please add your email address, or clear the confirmation to use phone only.');
    return true;
  }
  function preparePayload(entries,context={}){
    const data=serializeEntries(entries);
    for(const [key,value] of Object.entries(data)){if(Array.isArray(value))data[key]=value.join('; ');}
    data.phone=data.phone||data.preferred_phone||'';
    data.marketing_email_consent=data.marketing_email_consent==='Yes'?'Yes':'No';
    data.marketing_sms_consent=data.marketing_sms_consent==='Yes'?'Yes':'No';
    data.stock=data.unit_of_interest||data.description_or_stock_of_rv_that_you_are_interest||data.stock||'';
    const goal=data.selling_goal?' — '+data.selling_goal:'';
    data._subject=((context.subject||'MHSRV Inquiry')+goal+(data.stock?' · '+data.stock:'')).replace(/[\r\n]/g,' ').slice(0,250);
    data._template='table';data.page=context.page||'';
    for(const key of ATTRIBUTION){if(context.attribution?.[key])data[key]=String(context.attribution[key]).slice(0,250);}
    return data;
  }
  function financePrefill(query){
    const params=typeof query==='string'?new URLSearchParams(query):query,fields={};
    if(!params||typeof params.get!=='function')return fields;
    const stock=(params.get('stock')||'').trim().slice(0,300);
    if(stock){fields.stock=stock;fields.unit_of_interest=stock;}
    const aliases=[['monthly_payment','monthly_budget',0,100000000],['down_payment','down_payment_amount',0,1000000000],['term','term_months',1,600],['apr','illustrative_apr',0,36]];
    for(const [source,target,min,max] of aliases){
      const raw=(params.get(source)||params.get(target)||'').trim();
      if(!/^\d+(?:\.\d+)?$/.test(raw))continue;
      const value=Number(raw);
      if(!Number.isFinite(value)||value<min||value>max||(target==='term_months'&&!Number.isInteger(value)))continue;
      fields[target]=String(value);
    }
    return fields;
  }
  const api={serializeEntries,validateIntake,preparePayload,financePrefill};
  root.MHSLeads=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof document==='undefined')return;

  function init(){
    const forms=[...document.querySelectorAll('[data-intake-form]')];
    if(!forms.length)return;
    let config={};try{config=JSON.parse(document.querySelector('#siteConfig')?.textContent||'{}');}catch(_){}
    const email=config.leadEmail||'elisha@mhsrv.com';
    const app=()=>root.MHSApp||{};
    const track=(name,props)=>app().track?.(name,props);
    const snapshots=new WeakMap();
    function showError(form,error,target){
      const alert=form.querySelector('[data-intake-alert]');alert.textContent=error.message||String(error);alert.hidden=false;
      if(target){target.closest('details')?.setAttribute('open','');target.focus();target.scrollIntoView({behavior:'smooth',block:'center'});}
      else{alert.focus();alert.scrollIntoView({behavior:'smooth',block:'center'});}
    }
    function syncConfirmation(form){
      const confirmation=form.querySelector('[name="confirm_email"]'),field=form.querySelector('[name="email"]');
      if(confirmation)confirmation.required=!!field?.value.trim();
    }
    function formData(form){return serializeEntries(new FormData(form));}
    function contactTarget(form,error){
      const message=error.message||'';
      const name=/confirm|two email/.test(message)?'confirm_email':/email address/i.test(message)?'email':/phone number/i.test(message)?(form.querySelector('[name="phone"]')?'phone':'preferred_phone'):'name';
      return form.querySelector('[name="'+name+'"]');
    }
    function validate(form,section=form){
      syncConfirmation(form);
      const invalid=[...section.querySelectorAll('input,select,textarea')].find(input=>input.willValidate&&!input.checkValidity());
      if(invalid){showError(form,new Error('Please check “'+(invalid.dataset.fieldLabel||invalid.name)+'”.'),invalid);invalid.reportValidity();return false;}
      if(section===form||section.querySelector('[name="email"]')){
        try{validateIntake(formData(form));}
        catch(error){showError(form,error,contactTarget(form,error));return false;}
      }
      form.querySelector('[data-intake-alert]').hidden=true;return true;
    }
    function refresh(form){
      syncConfirmation(form);
      for(const step of form.querySelectorAll('[data-intake-step]')){
        const counter=step.querySelector('[data-step-count]');if(!counter)continue;
        const grouped=new Map();for(const el of step.querySelectorAll('input:not([type=hidden]),select,textarea')){
          const answered=['checkbox','radio'].includes(el.type)?el.checked:!!el.value.trim();
          grouped.set(el.name,(grouped.get(el.name)||false)||answered);
        }
        counter.textContent=[...grouped.values()].filter(Boolean).length+' of '+grouped.size+' answered';
      }
      const data=formData(form),summary=form.querySelector('[data-intake-review-summary]');
      const who=data.name||'Your name',contact=[data.email,data.phone||data.preferred_phone].filter(Boolean).join(' · ')||'Add an email or phone number';
      const vehicle=[data.year,data.make,data.make_and_model,data.model,data.floor_plan_model||data.floorplan].filter(Boolean).join(' ');
      summary.replaceChildren();
      for(const line of [who,contact,data.location,vehicle,data.selling_goal,data.unit_of_interest||data.description_or_stock_of_rv_that_you_are_interest].filter(Boolean)){
        const p=document.createElement('p');p.textContent=line;summary.append(p);
      }
    }
    function inquiryText(data){return Object.entries(data).filter(([key,value])=>!key.startsWith('_')&&key!=='website'&&value!==''&&value!=null).map(([key,value])=>key.replace(/_/g,' ')+': '+(Array.isArray(value)?value.join('; '):value)).join('\n');}
    function failure(form,error,data){
      const message=form.querySelector('.form-message');message.className='form-message error';message.hidden=false;message.replaceChildren(document.createTextNode(error.message||'Your request could not be confirmed.'));
      const links=document.createElement('span');links.className='intake-error-actions';
      const mail=document.createElement('a');mail.textContent='Email this inquiry';mail.href='mailto:'+email+'?subject='+encodeURIComponent(data._subject)+'&body='+encodeURIComponent(inquiryText(data));
      const copy=document.createElement('button');copy.type='button';copy.className='text-link';copy.dataset.copyIntake='';copy.textContent='Copy inquiry details';
      links.append(mail,copy);message.append(links);snapshots.set(form,data);message.focus();
    }
    const now=new Date(),today=now.getFullYear()+'-'+String(now.getMonth()+1).padStart(2,'0')+'-'+String(now.getDate()).padStart(2,'0');
    let url;try{url=new URL(location.href);}catch(_){}
    for(const form of forms){
      const alert=document.createElement('div');alert.className='intake-alert';alert.dataset.intakeAlert='';alert.hidden=true;alert.tabIndex=-1;alert.setAttribute('role','alert');form.prepend(alert);
      form.querySelectorAll('[data-request-date]').forEach(el=>{if(!el.value)el.value=today;});
      const stock=url?.searchParams.get('stock')||'';
      if(stock){form.querySelector('[name="stock"]').value=stock;const field=form.querySelector('[name="unit_of_interest"],[name="description_or_stock_of_rv_that_you_are_interest"]');if(field)field.value=stock;}
      if(form.id==='finance-intake'){
        const estimate=financePrefill(url?.searchParams);
        for(const [name,value] of Object.entries(estimate)){const field=form.elements.namedItem(name);if(field&&!field.value)field.value=value;}
        if(Object.keys(estimate).some(name=>!['stock','unit_of_interest'].includes(name))){
          const note=document.createElement('p');note.className='intake-notice';note.textContent='Your calculator estimates have been added to the budget section. Review or change them before sending. These figures are illustrative, not a financing offer.';form.prepend(note);
        }
      }
      form.addEventListener('input',()=>{refresh(form);if(form.dataset.sent){delete form.dataset.sent;const button=form.querySelector('[type="submit"]');button.disabled=false;button.textContent='Send updated inquiry →';}});
      form.addEventListener('change',()=>refresh(form));
      form.addEventListener('click',async event=>{
        const next=event.target.closest('[data-intake-next]');
        if(next){const step=next.closest('[data-intake-step]');if(!validate(form,step))return;const steps=[...form.querySelectorAll('[data-intake-step]')],following=steps[steps.indexOf(step)+1];if(following){step.open=false;following.open=true;following.querySelector('summary').focus();following.scrollIntoView({behavior:'smooth',block:'start'});}refresh(form);}
        if(event.target.closest('[data-copy-intake]')){
          try{await navigator.clipboard.writeText(inquiryText(snapshots.get(form)||formData(form)));event.target.closest('[data-copy-intake]').textContent='Copied';}
          catch(_){const message=form.querySelector('.form-message'),copy=document.createElement('textarea');copy.readOnly=true;copy.value=inquiryText(snapshots.get(form)||formData(form));copy.setAttribute('aria-label','Your inquiry details, ready to copy');message.append(copy);copy.focus();copy.select();}
        }
      });
      form.addEventListener('submit',async event=>{
        event.preventDefault();if(form.dataset.sending==='true'||!validate(form))return;
        const review=form.querySelector('.intake-review');review.open=true;
        const button=form.querySelector('[type="submit"]'),message=form.querySelector('.form-message');button.disabled=true;button.textContent='Sending your inquiry…';message.hidden=true;form.dataset.sending='true';
        let attribution={};try{attribution=JSON.parse(sessionStorage.getItem('mhsrv-attribution')||'{}');}catch(_){}
        const data=preparePayload(new FormData(form),{subject:form.dataset.subject,page:location.href,attribution});
        try{
          await root.MHSCore.submitLead('https://formsubmit.co/ajax/'+encodeURIComponent(email),data);
          message.className='form-message success';message.textContent='Your inquiry was accepted by our form service. An MHSRV specialist can review your information and help with the next step. For immediate help, call 800-335-6054.';message.hidden=false;button.textContent='Inquiry sent';form.dataset.sent='true';message.focus();track('lead_request_accepted',{intent:data.intent,stock:data.stock,intake_type:data.intake_type});
        }catch(error){failure(form,error,data);button.disabled=false;button.textContent='Try sending again →';track('lead_request_error',{intent:data.intent,intake_type:data.intake_type});}
        finally{delete form.dataset.sending;}
      });
      refresh(form);
    }
    function selectTab(kind,focus=false){
      for(const tab of document.querySelectorAll('[data-intake-tab]')){const active=tab.dataset.intakeTab===kind;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;if(active&&focus)tab.focus();}
      document.querySelectorAll('[data-intake-panel]').forEach(panel=>panel.hidden=panel.dataset.intakePanel!==kind);
    }
    for(const tab of document.querySelectorAll('[data-intake-tab]')){
      tab.addEventListener('click',()=>selectTab(tab.dataset.intakeTab));
      tab.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();selectTab(event.key==='Home'?'rv':event.key==='End'?'auto':tab.dataset.intakeTab==='rv'?'auto':'rv',true);}});
    }
    if(url?.searchParams.get('vehicle')==='auto')selectTab('auto');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})(typeof window!=='undefined'?window:globalThis);
