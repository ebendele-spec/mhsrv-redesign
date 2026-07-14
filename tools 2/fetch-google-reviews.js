#!/usr/bin/env node
/**
 * Refresh google-reviews.json with the latest 5-star Google reviews.
 *
 * OPTION A (quick start) — Google Places API (New):
 *   1. Create an API key: console.cloud.google.com → enable "Places API (New)".
 *   2. Find the Place ID for each location: developers.google.com/maps/documentation/places/web-service/place-id
 *   3. Run:  GOOGLE_API_KEY=xxx PLACE_ID=ChIJ... node tools/fetch-google-reviews.js
 *   ⚠ Places API returns only the 5 "most relevant" reviews per place — great for a
 *   rotating fresh sample, not the full history.
 *
 * OPTION B (full history + true auto-sync) — Google Business Profile API:
 *   Owner-verified OAuth on the MHSRV account exposes EVERY review (all years),
 *   supports pagination, and can run on a nightly cron. Swap the fetch below for
 *   mybusiness.googleapis.com/v4/accounts/{acct}/locations/{loc}/reviews
 *   filtered to starRating === "FIVE".
 *
 * Schedule either with cron / GitHub Actions:  0 6 * * *  node tools/fetch-google-reviews.js
 */
const fs=require('fs');
const KEY=process.env.GOOGLE_API_KEY, PLACE=process.env.PLACE_ID;
if(!KEY||!PLACE){console.error('Set GOOGLE_API_KEY and PLACE_ID env vars.');process.exit(1)}
(async()=>{
  const r=await fetch(`https://places.googleapis.com/v1/places/${PLACE}?fields=reviews,googleMapsUri,rating,userRatingCount&key=${KEY}`);
  const j=await r.json();
  if(!j.reviews){console.error('No reviews returned',j);process.exit(1)}
  const cutoff=Date.now()-5*365*24*3600*1000; // last 5 years
  const out={
    updated:new Date().toISOString(),
    placeUrl:j.googleMapsUri||'',
    rating:j.rating,count:j.userRatingCount,
    reviews:j.reviews
      .filter(v=>v.rating===5&&new Date(v.publishTime).getTime()>=cutoff)
      .map(v=>({author:v.authorAttribution?.displayName||'Google user',rating:v.rating,
                date:new Date(v.publishTime).toLocaleDateString('en-US',{month:'short',year:'numeric'}),
                text:(v.text?.text||'').trim()}))
  };
  fs.writeFileSync(__dirname+'/../google-reviews.json',JSON.stringify(out,null,1));
  console.log('google-reviews.json updated:',out.reviews.length,'five-star reviews');
})();
