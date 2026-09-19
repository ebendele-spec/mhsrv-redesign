#!/usr/bin/env node
'use strict';
/** Live server-side Google Places adapter. No review content is written to disk/Git.
 * --check verifies configured access without logging keys or reviews.
 * --serve exposes GET /google-reviews for explicitly allowed website origins.
 */
const FIELD_MASK='id,displayName,googleMapsUri,rating,userRatingCount,reviews,attributions';
class GooglePlacesError extends Error{
  constructor(code,status=502){super('Google reviews are unavailable ('+code+').');this.name='GooglePlacesError';this.code=code;this.status=status;}
}
const httpsUrl=value=>{try{const u=new URL(value);return u.protocol==='https:'?u.href:'';}catch(_){return '';}};
function settingsFromEnv(env=process.env){
  const apiKey=env.GOOGLE_API_KEY||'';
  const placeIds=[...new Set(String(env.GOOGLE_PLACE_IDS||env.PLACE_ID||'').split(',').map(x=>x.trim()).filter(Boolean))];
  if(!apiKey)throw new GooglePlacesError('MISSING_SERVER_API_KEY',503);
  if(!placeIds.length||placeIds.length>5||placeIds.some(x=>!/^[-_A-Za-z0-9]{10,255}$/.test(x)))throw new GooglePlacesError('INVALID_PLACE_IDS',503);
  const allowedOrigins=String(env.GOOGLE_ALLOWED_ORIGINS||'').split(',').map(x=>x.trim()).filter(Boolean);
  if(allowedOrigins.some(x=>{try{const u=new URL(x);return u.protocol!=='https:'||u.origin!==x;}catch(_){return true;}}))throw new GooglePlacesError('INVALID_ALLOWED_ORIGINS',503);
  return {apiKey,placeIds,allowedOrigins};
}
function normalizePlace(place,expectedId){
  if(place.id!==expectedId||typeof place.displayName?.text!=='string'||!httpsUrl(place.googleMapsUri))throw new GooglePlacesError('INVALID_PROVIDER_RESPONSE');
  const reviews=(Array.isArray(place.reviews)?place.reviews:[]).filter(r=>Number.isInteger(r.rating)&&r.rating>=1&&r.rating<=5&&typeof r.authorAttribution?.displayName==='string'&&httpsUrl(r.googleMapsUri)).map(r=>({
    author:r.authorAttribution.displayName,authorUrl:httpsUrl(r.authorAttribution.uri),authorPhoto:httpsUrl(r.authorAttribution.photoUri),
    rating:r.rating,text:r.originalText?.text||r.text?.text||'',date:r.relativePublishTimeDescription||r.publishTime||'',url:httpsUrl(r.googleMapsUri)
  }));
  return {id:place.id,name:place.displayName.text,url:httpsUrl(place.googleMapsUri),
    rating:Number.isFinite(place.rating)&&place.rating>=1&&place.rating<=5?place.rating:null,
    count:Number.isInteger(place.userRatingCount)&&place.userRatingCount>=0?place.userRatingCount:null,
    attributions:(Array.isArray(place.attributions)?place.attributions:[]).map(a=>({provider:String(a.provider||''),url:httpsUrl(a.providerUri)})),reviews};
}
async function fetchGoogleReviews(settings,transport=fetch){
  const locations=await Promise.all(settings.placeIds.map(async id=>{
    let response;
    try{response=await transport('https://places.googleapis.com/v1/places/'+encodeURIComponent(id),{
      headers:{'X-Goog-Api-Key':settings.apiKey,'X-Goog-FieldMask':FIELD_MASK},signal:AbortSignal.timeout(10000),cache:'no-store'});
    }catch(error){throw new GooglePlacesError(error.name==='TimeoutError'||error.name==='AbortError'?'PROVIDER_TIMEOUT':'PROVIDER_NETWORK_ERROR');}
    if(!response.ok){
      const code={400:'INVALID_PROVIDER_REQUEST',401:'INVALID_API_KEY',403:'PROVIDER_PERMISSION_DENIED',404:'PLACE_NOT_FOUND',429:'PROVIDER_QUOTA_EXCEEDED'}[response.status]||'PROVIDER_HTTP_ERROR';
      throw new GooglePlacesError(code);
    }
    let data;try{data=await response.json();}catch(_){throw new GooglePlacesError('INVALID_PROVIDER_JSON');}
    if(data.error)throw new GooglePlacesError('PROVIDER_ERROR');
    return normalizePlace(data,id);
  }));
  return {source:'google-places-api',fetchedAt:new Date().toISOString(),locations};
}
function createHandler(settings,transport=fetch){
  if(!settings.allowedOrigins?.length)throw new GooglePlacesError('MISSING_ALLOWED_ORIGINS',503);
  return async(req,res)=>{
    res.setHeader('Cache-Control','no-store, max-age=0');res.setHeader('Pragma','no-cache');
    res.setHeader('Vary','Origin');res.setHeader('Content-Type','application/json; charset=utf-8');res.setHeader('X-Content-Type-Options','nosniff');
    const origin=req.headers.origin;
    if(!settings.allowedOrigins.includes(origin)){res.statusCode=403;res.end(JSON.stringify({error:'ORIGIN_NOT_ALLOWED'}));return;}
    res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Access-Control-Allow-Methods','GET, OPTIONS');
    if(req.url!=='/google-reviews'){res.statusCode=404;res.end(JSON.stringify({error:'NOT_FOUND'}));return;}
    if(req.method==='OPTIONS'){res.statusCode=204;res.end();return;}
    if(req.method!=='GET'){res.statusCode=405;res.end(JSON.stringify({error:'METHOD_NOT_ALLOWED'}));return;}
    try{res.statusCode=200;res.end(JSON.stringify(await fetchGoogleReviews(settings,transport)));}
    catch(error){res.statusCode=error instanceof GooglePlacesError?error.status:502;res.end(JSON.stringify({error:error instanceof GooglePlacesError?error.code:'PROVIDER_UNAVAILABLE'}));}
  };
}
async function main(){
  const settings=settingsFromEnv();
  if(process.argv.includes('--check')){
    const result=await fetchGoogleReviews(settings);
    console.log('Google Places API connection verified for '+result.locations.length+' configured location(s). Review content was not saved.');
  }else if(process.argv.includes('--serve')){
    const http=require('node:http'),port=Number(process.env.PORT||8787);
    http.createServer(createHandler(settings)).listen(port,'127.0.0.1',()=>console.log('No-store Google review endpoint listening locally on port '+port+'. Use an approved HTTPS reverse proxy for deployment.'));
  }else throw new GooglePlacesError('CHOOSE_CHECK_OR_SERVE',503);
}
module.exports={GooglePlacesError,FIELD_MASK,settingsFromEnv,normalizePlace,fetchGoogleReviews,createHandler};
if(require.main===module)main().catch(error=>{console.error(error instanceof GooglePlacesError?error.message:'Google review setup failed. No provider data was written.');process.exitCode=1;});
