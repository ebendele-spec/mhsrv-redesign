# MHSRV shopping redesign

Static HTML, CSS and JavaScript, published from `main` through GitHub Pages:
https://ebendele-spec.github.io/mhsrv-redesign/

## Work on the site

- `assets/site.css`: shared visual system and responsive layouts.
- `assets/app.js`: shopping, saved RVs, comparisons, dialogs and resource viewers.
- `assets/search.js`: inventory-grounded natural-language matching.
- `assets/core.js`: tested lead transport and payment calculations.
- `tools/site_templates.py`: shared page templates.
- `tools/build-site.py`: rebuilds all pages and sitemaps from public data.
- `site-config.json`: preview origin, publication mode and lead recipient.

Preview locally:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Rebuild after changing a template:

```sh
python3 tools/build-site.py
```

## Import a fresh daily feed

Keep the emailed CSV **outside the repository**. It contains confidential columns such as dealer Cost.

```sh
python3 tools/build-inventory.py /private/path/to/daily-feed.csv --date YYYY-MM-DD
```

The importer writes an allowlisted `inventory.json` and individual `inventory/*.json` records. It rebuilds existing stock URLs, retains missing stocks as unavailable, and does not publish the raw CSV. Use the actual feed date. Rebuilding alone does not update the inventory date.

For daily email automation, see `HANDOFF.md`. An email connection or private attachment runner still needs to be configured; this site does not poll your inbox.

## Check before publishing

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
python3 tools/validate-site.py
```

Publish reviewed changes to `main`; GitHub Pages rebuilds the live preview. Use the repository owner's GitHub credentials when the default signed-in account lacks push access.

## Important deployment details

- GitHub is a design preview and deliberately uses `noindex,follow` on every HTML page.
- Current inventory is the September 17, 2026 import (1,263 records). This is a supplied feed snapshot, not a live connection.
- Leads route to `elisha@mhsrv.com` through FormSubmit. Mailbox activation and a real delivery check are required before paid traffic.
- Saved and compared RVs are stored only in the current browser, without account sync.
- RV Match and listing answers are grounded local tools. A generative AI model and secure backend are not connected.
- `mhsrv_*` conversion events are ready for a tag manager, but no analytics account is connected.
- No changes have been made to the existing MHSRV.com production website.

Read `AGENTS.md`, `HANDOFF.md` and `SEO-STRATEGY.md` before continuing development or preparing a production launch.
