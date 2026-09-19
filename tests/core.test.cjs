const test=require('node:test');
const assert=require('node:assert/strict');
const {estimatePayment,submitLead,validateContact}=require('../assets/core.js');
const {serializeEntries,preparePayload,validateIntake,financePrefill}=require('../assets/leads.js');
const valid={name:'Test Customer',email:'customer@example.com',intent:'Availability',stock:'TEST123'};
test('payment estimator handles zero APR and invalid inputs',()=>{
  assert.equal(estimatePayment(120000,0,0,120),1000);assert.equal(estimatePayment(100,100,9,120),0);
  assert.equal(estimatePayment(100,101,9,120),null);assert.equal(estimatePayment(100,0,-1,120),null);assert.equal(estimatePayment(100,0,9,0),null);
  assert(Math.abs(estimatePayment(100000,20000,9.99,240)-771.49)<1);
});
test('lead submission requires affirmative success and retains stock context',async()=>{
  let sent;const r=await submitLead('https://formsubmit.co/ajax/elisha%40mhsrv.com',valid,async(url,options)=>{sent={url,body:JSON.parse(options.body)};return{ok:true,json:async()=>({success:'true'})};});
  assert.equal(r.accepted,true);assert.equal(sent.body.stock,'TEST123');assert(sent.url.includes('elisha%40mhsrv.com'));
});
test('lead transport failures cannot become success',async()=>{
  await assert.rejects(submitLead('test',valid,async()=>({ok:false})),/not sent/);
  await assert.rejects(submitLead('test',valid,async()=>{throw new Error('offline');}),/offline/);
});
test('activation and ambiguous service responses remain errors',async()=>{
  for(const response of [{success:false},{message:'ok'},{success:'false'},{success:true,message:'Please activate your form'}])await assert.rejects(submitLead('test',valid,async()=>({ok:true,json:async()=>response})));
});
test('invalid or spam input does not call the delivery service',async()=>{
  let calls=0;const transport=async()=>{calls++;throw Error('should not send');};
  await assert.rejects(submitLead('test',{...valid,email:'invalid'},transport));await assert.rejects(submitLead('test',{...valid,website:'spam'},transport));assert.equal(calls,0);
});
test('email-only and phone-only inquiries are valid and normalize contact fields',async()=>{
  assert.deepEqual(validateContact({name:' Customer ',preferred_phone:'(817) 790-7771 ext. 42'}),{name:'Customer',email:'',phone:'(817) 790-7771 ext. 42'});
  assert.equal(validateContact({...valid,phone:''}).email,valid.email);
  let sent;await submitLead('mock',{name:'Phone Customer',phone:'+1 (817) 790-7771',email:''},async(_url,options)=>{sent=JSON.parse(options.body);return{ok:true,json:async()=>({success:true})};});
  assert.equal(sent.email,'');assert.equal(sent.phone,'+1 (817) 790-7771');
  assert.equal(sent.marketing_email_consent,'No');assert.equal(sent.marketing_sms_consent,'No');
});
test('invalid supplied contact information and incompatible reply choices are rejected before delivery',async()=>{
  let calls=0;const transport=async()=>{calls++;return{ok:true,json:async()=>({success:true})};};
  const inputs=[{name:'Customer'},{...valid,phone:'123'},{...valid,phone:'not a phone 8177907771'},{...valid,phone:'8177907771',email:'bad@'},{name:'',phone:'8177907771'},{name:'Customer',phone:'8177907771',preferred_contact:'email'},{...valid,preferred_contact:'text'},{...valid,marketing_sms_consent:'Yes'},{name:'Customer',phone:'8177907771',marketing_email_consent:'Yes'}];
  for(const data of inputs)await assert.rejects(submitLead('mock',data,transport));
  assert.equal(calls,0);
});
test('email confirmation is conditional and must match on detailed intake',()=>{
  assert.equal(validateIntake({name:'Customer',phone:'8177907771'}),true);
  assert.equal(validateIntake({...valid,confirm_email:' CUSTOMER@EXAMPLE.COM '}),true);
  assert.throws(()=>validateIntake({...valid,confirm_email:''}),/confirm/);
  assert.throws(()=>validateIntake({...valid,confirm_email:'other@example.com'}),/match/);
  assert.throws(()=>validateIntake({name:'Customer',phone:'8177907771',confirm_email:'customer@example.com'}),/clear the confirmation/);
});
test('intake serialization retains all checked values, exact context and separate consents',async()=>{
  const entries=[['name',' Customer '],['email','customer@example.com'],['confirm_email','customer@example.com'],['beds','Queen'],['beds','Bunks'],['awnings','Patio'],['awnings','Window'],['stock','OLD123'],['unit_of_interest','NEW456'],['marketing_sms_consent','Yes'],['phone','8177907771']];
  assert.deepEqual(serializeEntries(entries).beds,['Queen','Bunks']);
  const data=preparePayload(entries,{subject:'MHSRV RV Trade-In Inquiry',page:'https://example.test/trade-in.html',attribution:{utm_campaign:'fall',gclid:'click123',name:'overwritten'}});
  assert.equal(data.beds,'Queen; Bunks');assert.equal(data.awnings,'Patio; Window');assert.equal(data.stock,'NEW456');
  assert.equal(data._subject,'MHSRV RV Trade-In Inquiry · NEW456');assert.equal(data.utm_campaign,'fall');assert.equal(data.gclid,'click123');assert.equal(data.name,'Customer');
  assert.equal(data.marketing_sms_consent,'Yes');assert.equal(data.marketing_email_consent,'No');
  let sent;await submitLead('https://formsubmit.co/ajax/elisha%40mhsrv.com',data,async(url,options)=>{sent={url,body:JSON.parse(options.body)};return{ok:true,json:async()=>({success:true})};});
  assert.equal(sent.body.awnings,'Patio; Window');assert.equal(sent.body.stock,'NEW456');assert.equal(sent.body.marketing_sms_consent,'Yes');assert.equal(sent.url,'https://formsubmit.co/ajax/elisha%40mhsrv.com');
});
test('selling intent appears in subjects and malformed service responses stay unconfirmed',async()=>{
  const data=preparePayload([['selling_goal','Consignment'],['stock','TEST\r\n123']],{subject:'MHSRV Sell / Trade / Consign Inquiry'});
  assert.equal(data._subject,'MHSRV Sell / Trade / Consign Inquiry — Consignment · TEST  123');
  await assert.rejects(submitLead('mock',valid,async()=>({ok:true,json:async()=>{throw new SyntaxError('invalid response');}})),/invalid response/);
  await assert.rejects(submitLead('mock',valid,async()=>{const e=new Error('aborted');e.name='AbortError';throw e;}),/Delivery is unconfirmed/);
});
test('detail calculator URL carries its unit and all estimate assumptions into the submitted finance inquiry',async()=>{
  const query=new URLSearchParams({stock:'MHS123',monthly_payment:'771',down_payment:'20000',term:'240',apr:'9.99'});
  const fields=financePrefill(query);
  assert.deepEqual(fields,{stock:'MHS123',unit_of_interest:'MHS123',monthly_budget:'771',down_payment_amount:'20000',term_months:'240',illustrative_apr:'9.99'});
  const data=preparePayload(Object.entries({...fields,name:valid.name,email:valid.email,confirm_email:valid.email,intent:'Discuss RV financing'}),{subject:'MHSRV Financing Inquiry'});
  let sent;await submitLead('mock',data,async(_url,options)=>{sent=JSON.parse(options.body);return{ok:true,json:async()=>({success:true})};});
  assert.equal(sent._subject,'MHSRV Financing Inquiry · MHS123');
  for(const [name,value] of Object.entries(fields))assert.equal(sent[name],value);
});
test('calculator prefilling accepts zero values and field aliases but ignores invalid assumptions',()=>{
  assert.deepEqual(financePrefill('?stock=ZERO&monthly_payment=0&down_payment=0&term=120&apr=0'),{stock:'ZERO',unit_of_interest:'ZERO',monthly_budget:'0',down_payment_amount:'0',term_months:'120',illustrative_apr:'0'});
  assert.deepEqual(financePrefill('?monthly_budget=123.45&down_payment_amount=5000&term_months=180&illustrative_apr=6.25'),{monthly_budget:'123.45',down_payment_amount:'5000',term_months:'180',illustrative_apr:'6.25'});
  for(const query of ['?monthly_payment=NaN&down_payment=-1&term=0&apr=Infinity','?monthly_payment=%3Cscript%3E&down_payment=1e9&term=12.5&apr=36.1'])assert.deepEqual(financePrefill(query),{});
  assert.deepEqual(financePrefill(null),{});
});
