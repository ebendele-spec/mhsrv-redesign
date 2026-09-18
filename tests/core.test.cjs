const test=require('node:test');
const assert=require('node:assert/strict');
const {estimatePayment,submitLead}=require('../assets/core.js');
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
