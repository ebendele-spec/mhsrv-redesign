# MHSRV redesign handoff

The September 2026 redesign keeps the existing GitHub Pages repository and every unit/review URL. The previous published commit was `66bf55a7`.

## What works

- Responsive shopping page, natural-language inventory matching, keyboard suggestions, explicit filter interpretation, conventional filters and sort.
- Stock and model matching, common brand typos, dollar/length/year/capacity constraints, feature exclusions and transparent missing-data handling.
- Saved RVs on this device; three-unit comparisons; a guided RV Match questionnaire.
- 1,267 imported RVs, individual static detail pages, full photo galleries, available floorplans, on-page brochure and related-video viewers, and 360-tour links where supplied.
- Listing-based answers from the exact unit data. These are deterministic and explicitly labeled; they are not a connected generative AI model.
- Lead requests to `elisha@mhsrv.com` through FormSubmit, with validation, stock/intent context, campaign attribution, timeout handling and honest failures.
- Payment illustrations with editable assumptions, not offered rates or approval claims.
- 4,571 historical customer stories without fabricated ratings; static category/brand pages, buying guides and crawlable directories.
- Static preview noindex, consistent canonicals, breadcrumb/product data, and a production freshness gate.

## Required before advertising or production cutover

1. Import a fresh feed. The current snapshot is **July 18, 2026**, not live inventory.
2. Activate the FormSubmit recipient and verify an actual inquiry arrives in `elisha@mhsrv.com`. No live test inquiry was sent during development. A service acceptance response is not mailbox delivery confirmation.
3. Connect the daily emailed feed to a private import process. Receiving an attachment in an email account does not automatically update this repository.
4. For generative AI, connect a secured server endpoint and an AI service account. GitHub Pages cannot keep an API secret. The current RV Match and listing assistant work without that service; they do not pretend to be one.
5. Connect the chosen analytics/CRM integrations and measure actual lead delivery and qualified conversion. `mhsrv_*` dataLayer events are emitted, but no external analytics service is installed.
6. Complete the production SEO migration in `SEO-STRATEGY.md`. No MHSRV.com DNS, hosting or production content has been changed.

## Daily feed options

- **Manual now:** attach the CSV in the coding conversation or save it privately and run the documented importer.
- **Automatic later:** a mailbox rule/Power Automate/Zapier/Make workflow can fetch the attachment into private storage, then trigger a trusted import runner. Keep source credentials and the original attachment out of this public repository.
- A scheduler should validate expected feed columns, reject an empty/malformed feed, review unexpected inventory drops, build and check the public site, then publish. Failed imports must retain the last working catalog and alert the owner.

## Validation scope

Search regression and mocked lead/calculator tests, importer privacy tests, and generated-page/link/schema checks are included. The first local preview was opened. Automated browser/device interaction testing and real email delivery were not performed in this pass.

## Maintenance

Claude or another developer can edit the same ordinary files. Rebuild generated pages after editing templates. Avoid simultaneous edits in the same working copy, and reread this file before resuming.
