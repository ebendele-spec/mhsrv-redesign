# Google Reviews — live sync

The reviews hub (`reviews.html`) renders a "Fresh from Google" section from
`google-reviews.json` whenever that file contains 5-star reviews. Nothing else
to wire up — populate the JSON and the section appears.

## Making it live
A static site can't hold API credentials, so the refresh runs OUTSIDE the site:

1. **Quick start — Places API (New).** `tools/fetch-google-reviews.js` pulls the
   current "most relevant" reviews (max 5 per location per Google's limit),
   filters to 5-star within the last 5 years, and rewrites `google-reviews.json`.
   Schedule it nightly (cron, GitHub Actions, or your host's scheduler) and each
   deploy/publish picks up fresh reviews automatically.

2. **Full history — Google Business Profile API.** With owner OAuth on the MHSRV
   Google account you get EVERY review (all years, paginated) — that's the path
   for "pull every 5-star review, ongoing." Same JSON output; swap the endpoint
   noted in the script.

Run for both locations (Alvarado + Montgomery) by invoking the script once per
PLACE_ID and merging, or extend the script's PLACE list.

## Why Claude couldn't finish this hookup
Creating API keys / OAuth on your Google account requires credentials only you
should handle. Everything else — the widget, the JSON contract, the fetcher, the
5-star/5-year filter — is done and tested with seed data.
