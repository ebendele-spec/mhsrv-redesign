# Working on MHSRV

This is a plain HTML/CSS/JavaScript site hosted by GitHub Pages. Keep that architecture unless the owner explicitly requests a migration.

- Edit `tools/site_templates.py` and `tools/build-site.py` for generated HTML. Rebuild with `python3 tools/build-site.py`; do not hand-edit thousands of generated pages.
- Shared UI is in `assets/site.css` and `assets/app.js`. Inventory search is in `assets/search.js`; lead delivery and calculator logic are in `assets/core.js`.
- Lead destination is `site-config.json`: `elisha@mhsrv.com`. The FormSubmit mailbox must be activated and actual delivery confirmed before a paid campaign.
- The GitHub site is a design preview. Preserve static `noindex,follow` and the preview origin until a deliberate production migration.
- Never publish the raw inventory CSV, dealer `Cost`, credentials, financial account details or API keys. The importer emits an explicit public-field allowlist. Raw CSVs are ignored.
- Missing specifications stay unknown. Do not infer sleeping capacity, towing compatibility, installed options, ratings, popularity, price drops or availability.
- Keep customer testimonial text and existing URL paths. Do not invent star ratings or label dealership testimonials as unit reviews.
- Run `python3 -m unittest discover -s tests -p 'test_*.py'`, `node --test tests/*.test.cjs`, and `python3 tools/validate-site.py` after relevant changes.
- Do not submit test leads to real recipients during automated checks. Tests use a mocked transport.

Read `README.md`, `HANDOFF.md` and `SEO-STRATEGY.md` for the current implementation and remaining integration work.
