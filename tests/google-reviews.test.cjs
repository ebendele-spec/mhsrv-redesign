const test=require('node:test'),assert=require('node:assert/strict');
const {settingsFromEnv,fetchGoogleReviews,createHandler}=require('../tools/fetch-google-reviews.js');
const settings={apiKey:'FAKE_TEST_KEY',placeIds:['ChIJ_TEST_LOCATION'],allowedOrigins:['https://ebendele-spec.github.io']};
const place={id:'ChIJ_TEST_LOCATION',displayName:{text:'Test dealership'},googleMapsUri:'https://maps.google.com/?cid=1',rating:4.2,userRatingCount:20,reviews:[
  {authorAttribution:{displayName:'Alex',uri:'https://maps.google.com/author/alex',photoUri:'https://example.com/avatar.jpg'},rating:2,text:{text:'Translated text'},originalText:{text:'Original review'},relativePublishTimeDescription:'one month ago',googleMapsUri:'https://maps.google.com/review/one'},
  {authorAttribution:{displayName:'Sam'},rating:5,text:{text:'Helpful people'},googleMapsUri:'https://maps.google.com/review/two'}
]};
const success=async()=>({ok:true,json:async()=>place});
function response(){return {headers:{},statusCode:0,setHeader(k,v){this.headers[k]=v;},end(body){this.body=body;}};}
test('missing credentials and invalid origins fail without disclosing secrets',()=>{
  assert.throws(()=>settingsFromEnv({}),/MISSING_SERVER_API_KEY/);
  assert.throws(()=>settingsFromEnv({GOOGLE_API_KEY:'private',GOOGLE_PLACE_IDS:'bad'}),/INVALID_PLACE_IDS/);
  assert.throws(()=>settingsFromEnv({GOOGLE_API_KEY:'private',GOOGLE_PLACE_IDS:'ChIJ_TEST_LOCATION',GOOGLE_ALLOWED_ORIGINS:'*'}),/INVALID_ALLOWED_ORIGINS/);
});
test('current provider ratings, attribution, source links and original text survive',async()=>{
  let call;
  const result=await fetchGoogleReviews(settings,async(url,opts)=>{call={url,opts};return success();});
  assert.equal(result.source,'google-places-api');assert.equal(result.locations[0].rating,4.2);
  assert.deepEqual(result.locations[0].reviews.map(r=>r.rating),[2,5]);
  assert.equal(result.locations[0].reviews[0].text,'Original review');
  assert.equal(result.locations[0].reviews[0].authorUrl,'https://maps.google.com/author/alex');
  assert.ok(!call.url.includes(settings.apiKey));assert.equal(call.opts.cache,'no-store');
  assert.ok(!JSON.stringify(result).includes(settings.apiKey));
});
test('provider permission, quota, malformed JSON and mismatched location fail honestly',async()=>{
  for(const [status,code]of [[403,'PROVIDER_PERMISSION_DENIED'],[429,'PROVIDER_QUOTA_EXCEEDED']]){
    await assert.rejects(fetchGoogleReviews(settings,async()=>({ok:false,status})),new RegExp(code));
  }
  await assert.rejects(fetchGoogleReviews(settings,async()=>({ok:true,json:async()=>{throw new Error('raw provider secret');}})),/INVALID_PROVIDER_JSON/);
  await assert.rejects(fetchGoogleReviews(settings,async()=>({ok:true,json:async()=>({...place,id:'other'})})),/INVALID_PROVIDER_RESPONSE/);
});
test('API timeout is an error and is never replaced with seed data',async()=>{
  await assert.rejects(fetchGoogleReviews(settings,async()=>{throw Object.assign(new Error('private details'),{name:'TimeoutError'});}),/PROVIDER_TIMEOUT/);
});
test('endpoint has no-store, allowed-origin CORS and re-fetches each request',async()=>{
  let calls=0;const handler=createHandler(settings,async()=>{calls++;return success();});
  for(let i=0;i<2;i++){
    const res=response();await handler({method:'GET',url:'/google-reviews',headers:{origin:settings.allowedOrigins[0]}},res);
    assert.equal(res.statusCode,200);assert.equal(res.headers['Cache-Control'],'no-store, max-age=0');assert.equal(res.headers['Access-Control-Allow-Origin'],settings.allowedOrigins[0]);
  }
  assert.equal(calls,2);
});
test('endpoint rejects other origins, arbitrary place queries and mutation methods',async()=>{
  let calls=0;const handler=createHandler(settings,async()=>{calls++;return success();});
  for(const [origin,url,method,status]of [['https://unrelated.example','/google-reviews','GET',403],[settings.allowedOrigins[0],'/google-reviews?place=other','GET',404],[settings.allowedOrigins[0],'/google-reviews','POST',405]]){
    const res=response();await handler({method,url,headers:{origin}},res);assert.equal(res.statusCode,status);
  }
  assert.equal(calls,0);
});
test('provider errors expose a stable code without raw provider details',async()=>{
  const handler=createHandler(settings,async()=>{throw new Error('FAKE_TEST_KEY raw provider message');});const res=response();
  await handler({method:'GET',url:'/google-reviews',headers:{origin:settings.allowedOrigins[0]}},res);
  assert.equal(res.statusCode,502);assert.equal(JSON.parse(res.body).error,'PROVIDER_NETWORK_ERROR');assert.ok(!res.body.includes(settings.apiKey));
});
