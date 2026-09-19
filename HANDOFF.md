# MHSRV redesign handoff

The September 2026 redesign keeps the existing GitHub Pages repository and every unit/review URL. The pre-redesign baseline was `66bf55a7`. The September 19 restoration builds on the September 17 feed update (`4eb09ed6`).

## September 19 functionality restoration

- Persistent Visual/Data shopping layouts; six-photo lazy card galleries with swipe, drag, arrows and dots; 24-item batches that become automatic after the first manual load, with pause/resume.
- Live typed results; model/brand prefix suggestions and thumbnails; typo recovery; recent searches and local browsing-based recommendations. Type tiles and quick condition/budget/lifestyle choices preserve other filters.
- Deals/New Arrival feed flags; legacy Deals/query links; biggest-dollar-savings sorting; savings percentages; monthly-budget matching and card estimates with editable assumptions. `$2000/mo` no longer becomes year 2000. Explicit horsepower, color and combined equipment requirements are supported without inventing missing specs.
- Complete inline unit photo rails and thumbnails, uncropped images, keyboard/touch/mouse navigation, retry/fallback messages, inline video, Blue Compass document links and model-specific MHSRV YouTube search.
- Detail price/payment/savings, itemized fees, percent or dollar down payment, five-year term, optional conservative term guidance, and exact calculator values carried into the financing inquiry. Available brochures and stock URLs remain intact.
- Structured descriptions, expandable floorplan/specs/description, verified buying benefits, and six similar available RVs ranked by condition/model/type/length/budget.
- Contextual SMS, mobile Call/Text, card calling; grouped detailed RV and auto trade-in workflows, sell/trade/consign choices, financing preferences, dealership/salesperson/date routing, conditional email confirmation, separate unchecked optional marketing permissions. Phone-only inquiries work. All inquiries target `elisha@mhsrv.com`.
- All 4,571 customer stories and 3,019 historical customer photos preserved. Brand/type/text/stock filtering, 36-story batches/counts, accurate metadata, previous/next and brand-shopping links restored.
- Expanded shopping menu, Service & Parts, verified locations/hours/call shortcuts, complete expandable pricing/deposit/promotional terms, external full-inventory link and old Budget/Featured/Reviews bookmarks.
- Existing saved RVs, three-unit comparisons, RV Match, deterministic listing assistant, preview noindex, canonicals, schema and production freshness gate retained.

## Google reviews — pending connection

The live endpoint adapter and attributed UI are implemented and mock-tested, but **Google is not connected**. No authorized Google key/project or server host was found. The existing seed JSON is not displayed. GitHub Pages cannot privately hold credentials; Google review content is not committed to public Git.

See `tools/README-google-reviews.md` for the concrete setup: an authorized existing Places API project/key, verified dealership Place IDs, an HTTPS runtime host, then an authenticated connection check and browser refresh verification. Set `google-reviews.config.json` → `endpoint` only after verification. The UI currently links directly to the MHSRV Google Maps profile. Places provides a sample of reviews; full history would require a separate approved Business Profile integration.

## Required before advertising or production cutover

1. Keep importing fresh feeds. The current snapshot was supplied and imported **September 17, 2026**; it is not a live connection. The CSV has no export-date field, so this date reflects the owner's latest-feed submission.
2. Activate the FormSubmit recipient and verify an actual inquiry arrives in `elisha@mhsrv.com`. No live test inquiry was sent during development. A service acceptance response is not mailbox delivery confirmation.
3. Connect the daily emailed feed to a private import process. Receiving an attachment in an email account does not automatically update this repository.
4. For generative AI, connect a secured server endpoint and an AI service account. GitHub Pages cannot keep an API secret. The current RV Match and listing assistant work without that service; they do not pretend to be one.
5. Connect the chosen analytics/CRM integrations and measure actual lead delivery and qualified conversion. `mhsrv_*` dataLayer events are emitted, but no external analytics service is installed.
6. Complete the production SEO migration in `SEO-STRATEGY.md`. No MHSRV.com DNS, hosting or production content has been changed.

## Daily feed options

The September 17 update added 234 stocks, removed 238 from search, and changed 531 prices compared with the July 18 snapshot. Removed-stock URLs remain available with a "No longer listed" status, their last known price/specification date, and the date they first disappeared from the feed. No raw source attachment was committed.

- **Manual now:** attach the CSV in the coding conversation or save it privately and run the documented importer.
- **Automatic later:** a mailbox rule/Power Automate/Zapier/Make workflow can fetch the attachment into private storage, then trigger a trusted import runner. Keep source credentials and the original attachment out of this public repository.
- A scheduler should validate expected feed columns, reject an empty/malformed feed, review unexpected inventory drops, build and check the public site, then publish. Failed imports must retain the last working catalog and alert the owner.

## Validation scope

Search, mocked lead/calculator/Google, inventory privacy, historical review and detail template regressions are included. Browser interaction checks were performed in Chrome at desktop and 390px mobile width: live payment search, persistent Data view, cards/galleries, calculator-to-finance handoff, RV/auto tabs, review filters/batches, Deals sorting, and overflow. All 6,215 generated HTML files are checked for local links, assets, anchors, metadata and preview indexing. No real leads were submitted; mailbox delivery and a real Google endpoint remain unverified.

## Maintenance

Claude or another developer can edit the same ordinary files. Rebuild generated pages after editing templates. Avoid simultaneous edits in the same working copy, and reread this file before resuming.

## Verified business content

Location addresses/hours, service URLs and purchase benefits were checked against the official [contact page](https://mhsrv.com/contact-us), [homepage](https://mhsrv.com/) and [service page](https://mhsrv.com/rv-service-rv-parts-and-rv-accessories) on September 19, 2026. The Texas $225 documentation amount and airport pickup were confirmed on [published MHSRV pricing](https://mhsrv.com/2007-fleetwood-flair33r-0-class-a-tx-i2681972). Other locations ask for confirmation rather than inheriting Texas’s document fee. Deposit language preserves the owner-provided prior site's terms; obsolete promotional rates were replaced by the actual displayed illustrative assumptions.
