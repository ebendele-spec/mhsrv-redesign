# Google reviews: connection status and deployment

Historical customer stories are restored independently of Google. Their ratings are never inferred. The old `google-reviews.json` contains hand-entered seed data and is **not read** by the site or this integration.

**Status: prepared, not connected.** No Google credentials were found in task environment variables, local project settings, repository Actions secrets or the `github-pages` environment. The public MHSRV homepage did not contain an existing Google review widget/API integration. A successful authenticated Google response and deployed endpoint have not been verified.

## Implementation

Use an existing authorized **Places API (New)** project through a server-side, on-demand endpoint. GitHub Pages remains the static frontend. `fetch-google-reviews.js` exports the adapter and HTTP handler, fetches current data per request, and does not write review content to files, logs, browser storage or Git. Responses have `Cache-Control: no-store`; configure the hosting proxy/CDN to honor it. There is no nightly JSON commit job.

Places returns a relevance-ordered sample, normally up to five reviews per location, not full history. The UI displays all returned ratings, with original text, author name/profile/avatar when supplied, individual review links and Google Maps attribution. Historical testimonials are visually separate. Errors do not become fake reviews or fake zero ratings; the direct Maps link remains available.

## Finish connecting

1. Use an existing approved Google Cloud project with Places API (New) access and an authorized server-side API key. Configure it through the chosen host's secret settings, never in chat, source code, a URL or public assets. This work does not create billing accounts, enable paid services or authorize a service purchase.
2. Supply verified Google **Place IDs** for the desired dealership locations. A Maps CID is not a Place ID. Use the official Place ID finder or the authorized project's search API; do not substitute a guess.
3. Choose an approved existing server/serverless host and HTTPS endpoint. Set `GOOGLE_API_KEY`, `GOOGLE_PLACE_IDS` (comma-separated, maximum five) and `GOOGLE_ALLOWED_ORIGINS` (exact origins, e.g. `https://ebendele-spec.github.io,https://mhsrv.com`) in server environment settings. Restrict the key to Places API and the server where supported. Add host-level rate limits and project quota controls; CORS alone is not authentication or abuse protection.
4. Run `node tools/fetch-google-reviews.js --check` on that server. It logs connection status only. Use exported `createHandler(settingsFromEnv())` in the host adapter, or `--serve` behind an existing HTTPS reverse proxy. The local server binds loopback. It exposes only `GET /google-reviews` for configured origins and locations; callers cannot supply arbitrary place IDs.
5. Set the deployed HTTPS URL in `google-reviews.config.json` → `endpoint`. Verify a browser request from the preview origin, business names, ratings, source links, attribution, no-store headers, provider failure handling and repeat-request refresh. Only then describe the connection as active.
6. Update site privacy/terms before enabling: disclose Google Maps Platform usage and its applicable Terms of Service and Privacy Policy. Confirm current account terms and quota/billing settings with the project owner.

The endpoint fetches fresh content per page load, so no scheduled refresh is necessary. No Actions workflow was created: the available GitHub token lacks workflow scope, and permanent public Git storage is the wrong model for this content.

## Verification

`node --test tests/reviews.test.cjs tests/google-reviews.test.cjs` uses mocked provider responses without contacting Google. `python3 -m unittest discover -s tests -p 'test_reviews.py'` verifies the historical corpus. Passing mocks does not prove credentials or a hosted endpoint are connected.

## Official references checked September 19, 2026

- [Places policies and attribution](https://developers.google.com/maps/documentation/places/web-service/policies): storage restrictions, Google Maps attribution, author/source links and review-order disclosure.
- [Place Details (New)](https://developers.google.com/maps/documentation/places/web-service/place-details): authenticated requests and explicit field masks.
- [Place IDs](https://developers.google.com/maps/documentation/places/web-service/place-id): identifiers.
- [Business Profile review data](https://developers.google.com/my-business/content/review-data): separate owner-authorized OAuth option for full review history.
- [Business Profile policies](https://developers.google.com/my-business/content/policies): limited secure temporary storage, at most 30 days, not an indefinite public Git archive.

Full Google review history requires an approved Business Profile project with owner OAuth and an appropriate secure temporary service. The Places sample must never be presented as every Google review.

The unmodified `assets/google-maps-attribution.svg` is the official dark gray Google Maps attribution from [Google’s attribution asset download](https://developers.google.com/static/maps/documentation/images/Google_Maps_Attribution_Assets.zip). It is shown at 18px tall with the required clear space beside provider attributions returned by Google.
