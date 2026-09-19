"""Historical customer stories. Metadata is parsed from source titles, never ratings."""
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
E = lambda value: html.escape(str(value or ''), quote=True)
BRANDS = ['Thor Motor Coach', 'Thor Motor', 'Forest River', 'Holiday Rambler',
          'American Coach', 'American Eagle', 'Grand Design', 'Leisure Travel',
          'Gulf Stream', 'Fleetwood RV', 'Country Coach', 'Georgie Boy',
          'Travel Supreme', 'Entegra Coach', 'Heartland RV', 'Midwest Automotive Designs',
          'National RV', 'Coachmen', 'Fleetwood', 'Entegra', 'Tiffin', 'Newmar',
          'Winnebago', 'Dynamax', 'Nexus', 'Heartland', 'Jayco', 'Keystone', 'Midwest',
          'Foretravel', 'Monaco', 'Renegade', 'Gulfstream', 'Airstream', 'Itasca',
          'Damon', 'Pleasure-Way', 'Roadtrek', 'Crossroads', 'Dutchmen', 'Palomino',
          'Cruiser', 'Venture', 'KZ', 'Alliance', 'DRV', 'Brinkley', 'Axiom', 'OGV',
          'Beaver', 'Nu-Wa', 'Sportscoach', 'Safari', 'National', 'Thor',
          'American', 'Phoenix', 'Regency', 'K-Z', 'Open Range', 'Four Winds',
          'MVP', 'Coleman', 'Sunnybrook', 'Carriage', 'Skyline', 'Prevost',
          'Coach House', 'EnduraMax', 'Alfa', 'Born Free', 'Mandalay',
          'Western RV', 'Blue Bird', 'Chinook', 'Forestravel', 'Coahmen',
          'Heatland', 'Dynmax', 'Curiser', 'Dynamx', 'Amerian Coach', 'Monoco',
          'Sportcoach', 'Hearltand', 'Dymamx', 'Hoiday Rambler', 'Foret River']
ALIASES = {'thor':'Thor Motor Coach', 'thor motor':'Thor Motor Coach',
           'entegra':'Entegra Coach', 'fleetwood rv':'Fleetwood', 'heartland rv':'Heartland',
           'gulfstream':'Gulf Stream', 'dynamax corp':'Dynamax', 'national':'National RV',
           'midwest':'Midwest Automotive Designs', 'american':'American Coach',
           'american eagle':'American Coach', 'k-z':'KZ',
           'forestravel':'Foretravel', 'coahmen':'Coachmen', 'heatland':'Heartland',
           'hearltand':'Heartland', 'dynmax':'Dynamax', 'dynamx':'Dynamax',
           'dymamx':'Dynamax', 'curiser':'Cruiser', 'amerian coach':'American Coach',
           'monoco':'Monaco', 'sportcoach':'Sportscoach',
           'hoiday rambler':'Holiday Rambler', 'foret river':'Forest River'}
TYPES = {'class a':'Class A', 'class b':'Class B', 'class c':'Class C',
         'super c':'Super C', 'diesel pusher':'Diesel Pusher', 'diesel engine':'Diesel Engine',
         'fifth wheel':'Fifth Wheel', '5th wheel':'Fifth Wheel', 'toy hauler':'Toy Hauler',
         'travel trailer':'Travel Trailer', 'travel tailer':'Travel Trailer',
         'truck camper':'Truck Camper', 'bus conversion':'Bus Conversion'}


def load_stories(path=None):
    records = json.loads(Path(path or ROOT / 'mhsrv-reviews-all.json').read_text())
    stories = []
    seen = set()
    for slug, title, stock, text, image, flag, ym in records:
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', slug) or slug in seen:
            raise ValueError('Invalid or duplicate customer-story URL')
        seen.add(slug)
        # Preserve original title/text verbatim. Normalize only independent filter metadata.
        parts = re.split(r'\s+(?:sold\s+(?:to\s+)?|to\s+the\s+)', title, maxsplit=1, flags=re.I)
        prefix = parts[0]
        buyer = location = ''
        if len(parts) == 2:
            recipient = re.sub(r'^the\s+', '', parts[1], flags=re.I)
            chunks = recipient.rsplit(' of ', 1)
            buyer = chunks[0].strip()
            if len(chunks) == 2:
                location = chunks[1].strip()
        clean = re.sub(r'\b(?:review|reivew)\b', '', prefix, flags=re.I).strip(' ,')
        typ = ''
        if ',' in clean:
            unit, candidate = clean.rsplit(',', 1)
            typ = TYPES.get(candidate.strip().lower(), '')
            if typ:
                clean = unit.strip()
        elif clean.lower() in TYPES:
            typ, clean = TYPES[clean.lower()], ''
        year_match = re.match(r'^(\d{4})(?:\s+|$)', clean)
        year = int(year_match[1]) if year_match else None
        unit = clean[year_match.end():] if year_match else clean
        brand = ''
        for known in sorted(BRANDS, key=len, reverse=True):
            if unit.lower() == known.lower() or unit.lower().startswith(known.lower() + ' '):
                brand = known
                break
        model = unit[len(brand):].strip() if brand else unit
        brand = ALIASES.get(brand.lower(), brand)
        date_label = ''
        if re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', ym or ''):
            date_label = datetime.strptime(ym, '%Y-%m').strftime('%B %Y')
        stories.append(dict(slug=slug, title=title, text=text.strip(), stock=stock,
                            image=image if image.startswith('https://') else '',
                            year=year, brand=brand, model=model, type=typ, buyer=buyer,
                            location=location, date=ym if date_label else '', dateLabel=date_label))
    return stories


def story_card(story, prefix=''):
    href = prefix + 'reviews/' + story['slug'] + '.html'
    meta = [story['type'], 'Stock #' + story['stock'] if story['stock'] else '',
            story['location'], story['dateLabel']]
    excerpt = story['text'][:260] + ('…' if len(story['text']) > 260 else '')
    return f'<article class="review-card"><h3><a href="{href}">{E(story["title"])}</a></h3><p>“{E(excerpt)}”</p><small>{E(" · ".join(x for x in meta if x))}</small><a class="text-link" href="{href}">Read the story →</a></article>'


def review_hub(stories, config):
    options = lambda key: ''.join(f'<option value="{E(v)}">{E(v)}</option>' for v in sorted({r[key] for r in stories if r[key]}))
    count = len(stories)
    return f'''<link rel="stylesheet" href="assets/reviews.css"><main id="main" class="container content-page">
<div class="page-heading"><p class="eyebrow">The MHSRV community</p><h1>Real adventures.<br>In our customers’ words.</h1><p>Explore {count:,} customer stories. Find an RV brand, model, stock number or hometown.</p></div>
<form id="reviewSearchForm" class="review-filters" role="search"><div class="field review-query"><label for="reviewSearch">Search customer stories</label><input id="reviewSearch" name="q" type="search" placeholder="Brand, model, city or stock number" maxlength="180" autocomplete="off"></div><div class="field"><label for="reviewBrand">Brand</label><select id="reviewBrand" name="brand"><option value="">All brands</option>{options('brand')}</select></div><div class="field"><label for="reviewType">RV type</label><select id="reviewType" name="type"><option value="">All types</option>{options('type')}</select></div><button type="reset" class="button outline small">Clear filters</button><button type="submit" class="button small review-submit">Search stories</button></form>
<p id="reviewCount" class="data-note" role="status" aria-live="polite">Showing {min(36,count)} of {count:,} customer stories</p>
<div class="review-grid" id="reviewGrid" data-reviews-v2>{''.join(story_card(s) for s in stories[:36])}</div>
<div class="load-more-row"><button class="button outline" id="moreReviews" type="button">Load 36 more · {max(0,count-36):,} remaining</button></div><p class="review-directory"><a href="review-pages/1.html">Browse every customer story by page →</a></p>
<section class="google-reviews-section" id="googleReviews" aria-labelledby="googleReviewsTitle"><div class="section-heading"><div><p class="eyebrow">A second perspective</p><h2 id="googleReviewsTitle">Find us on Google Maps.</h2></div></div><p id="googleReviewsStatus">Read customer reviews on our Google Maps business profile.</p><div id="googleReviewsGrid" class="review-grid"></div><a id="googleReviewsLink" class="text-link" href="https://maps.google.com/?cid=6032804850552315364" target="_blank" rel="noopener">Read reviews on Google Maps ↗</a></section>
<p class="data-note">The customer stories above describe historical dealership experiences and may discuss previously sold RVs. A star rating is shown only when provided by its review source.</p>
</main><script src="assets/reviews.js" defer></script>'''


def review_detail(story, previous, following, config):
    s = story
    meta = [f'Stock #{s["stock"]}' if s['stock'] else '', s['type'],
            f'Buyer location: {s["location"]}' if s['location'] else '', s['dateLabel']]
    photo = f'<img class="review-photo" src="{E(s["image"])}" alt="Customer photo from this MHSRV story" loading="lazy" width="400" height="295">' if s['image'] else ''
    signature = ' · '.join(v for v in [s['buyer'], s['location'], s['dateLabel']] if v)
    signature_html = f'<p class="review-signature">— {E(signature)}</p>' if signature else ''
    brand = s['brand']
    shop = '../index.html?' + 'brand=' + quote(brand) + '#inventory' if brand else '../index.html#inventory'
    more = '../reviews.html?brand=' + quote(brand) if brand else '../reviews.html'
    previous_link = f'<a href="{previous["slug"]}.html" rel="prev"><small>← Previous story</small><span>{E(previous["title"])}</span></a>' if previous else '<span></span>'
    next_link = f'<a href="{following["slug"]}.html" rel="next"><small>Next story →</small><span>{E(following["title"])}</span></a>' if following else '<span></span>'
    return f'''<link rel="stylesheet" href="../assets/reviews.css"><main id="main" class="container narrow content-page"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a><span>/</span><a href="../reviews.html">Customer stories</a></nav><div class="page-heading"><p class="eyebrow">An MHSRV customer story</p><h1>{E(s['title'])}</h1><p>{E(' · '.join(v for v in meta if v))}</p></div>{photo}<blockquote class="review-content">{E(s['text']).replace(chr(10),'<br>')}</blockquote>{signature_html}<div class="review-actions"><a class="button" href="{shop}">Shop {E(brand) + ' ' if brand else ''}RVs →</a><a class="button outline" href="{more}">More {E(brand) + ' ' if brand else ''}customer stories</a></div><nav class="story-pagination" aria-label="Customer stories">{previous_link}{next_link}</nav><p class="data-note">This historical testimonial describes a customer’s experience and may refer to a previously sold RV. Confirm the equipment and availability of current listings with your specialist.</p></main><script src="../assets/reviews.js" defer></script>'''
