"""Shared, crawlable HTML for the MHSRV shopping experience."""
import html
import json
import re
from urllib.parse import quote

J = lambda value: json.dumps(value,ensure_ascii=False).replace('</','<\\/')
E = lambda value: html.escape(str(value if value is not None else ''), quote=True)
TYPE_NAMES = {'diesel':'Diesel pushers','classa':'Class A gas','classc':'Class C & B+','superc':'Super C','classb':'Class B vans','fifth':'Fifth wheels','tt':'Travel trailers','toy':'Toy haulers'}
TYPE_PATHS = {'diesel':'diesel-pusher-rvs','classa':'class-a-rvs','classc':'class-c-rvs','superc':'super-c-rvs','classb':'class-b-rvs','fifth':'fifth-wheels','tt':'travel-trailers','toy':'toy-haulers'}
TYPE_IMAGES = {'diesel':'diesel_pusher','classa':'class_a','classc':'class_c','superc':'super_c','classb':'class_b','fifth':'fifth_wheel','tt':'travel_trailer','toy':'toy_hauler'}
STATUS = {'listed':'Listed inventory','pending':'Sale pending','onorder':'On order','coming':'Coming soon','unavailable':'No longer listed'}
ICONS = {
 'search':'<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/>',
 'heart':'<path d="M20.8 4.8a5.5 5.5 0 0 0-7.8 0L12 5.9l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.4a5.5 5.5 0 0 0 0-7.8Z"/>',
 'arrow':'<path d="M5 12h14M13 6l6 6-6 6"/>',
 'chevron':'<path d="m9 5 7 7-7 7"/>',
 'close':'<path d="m6 6 12 12M6 18 18 6"/>',
 'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
 'phone':'<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2Z"/>',
 'pin':'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
 'check':'<path d="m5 12 4 4L19 6"/>',
 'shield':'<path d="M12 3 3 7v6c0 5 9 9 9 9s9-4 9-9V7l-9-4Z"/><path d="m8 12 3 3 5-6"/>',
 'spark':'<path d="m12 3 2.7 6.3L21 12l-6.3 2.7L12 21l-2.7-6.3L3 12l6.3-2.7L12 3Z"/>',
 'camera':'<path d="M3 7h4l2-3h6l2 3h4v14H3V7Z"/><circle cx="12" cy="13" r="4"/>',
 'filter':'<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="2" fill="white"/><circle cx="15" cy="17" r="2" fill="white"/>',
 'compare':'<path d="M8 3v18M16 3v18M3 8h10M11 16h10"/><path d="m5 6-2 2 2 2m14 4 2 2-2 2"/>',
 'book':'<path d="M12 5v16M12 5C9 3 5 3 2 4v15c3-1 7-1 10 2 3-3 7-3 10-2V4c-3-1-7-1-10 1Z"/>',
 'message':'<path d="M21 11a9 9 0 0 1-9 9H3l2-5a9 9 0 1 1 16-4Z"/><path d="M8 9h8M8 13h5"/>',
 'file':'<path d="M14 2H5v20h14V7l-5-5Z"/><path d="M14 2v6h5M8 12h8M8 16h6"/>',
 'play':'<path d="m8 5 11 7-11 7V5Z"/>',
 'share':'<path d="M12 16V2M7 7l5-5 5 5M5 12H3v10h18V12h-2"/>',
 'home':'<path d="m3 10 9-8 9 8v12h-7v-8h-4v8H3V10Z"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'
}
def icon(name):
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(name,ICONS["arrow"])}</svg>'
def money(n):
    return f'${n:,.0f}' if n else 'Request price'
def title(u):
    return f'{u["year"]} {u["brand"]} {u["model"]} {u["floorplan"]}'.strip()
def link(u,prefix=''):
    return prefix+'units/'+quote(u['stock'],safe='')+'.html'
def brand(prefix=''):
    return f'<a class="wordmark" href="{prefix}index.html" aria-label="Motor Home Specialist home"><strong>MHSRV<em>®</em></strong><small>Motor Home Specialist</small></a>'

def dialogs(prefix='',config=None):
    email=E((config or {}).get('leadEmail','elisha@mhsrv.com'))
    from lead_templates import contact_dialog
    return contact_dialog(prefix,config)+f'''<dialog id="matchDialog" aria-labelledby="matchTitle"><div class="dialog-head"><div><div class="eyebrow">MHSRV · RV Match</div><h2 id="matchTitle">A little about you.<br>A much better shortlist.</h2></div><button class="icon-button" data-close aria-label="Close RV Match">{icon('close')}</button></div><div class="dialog-body" id="matchBody"></div></dialog>
<dialog id="assistantDialog" aria-labelledby="assistantTitle"><div class="dialog-head"><div><div class="eyebrow">MHSRV · Inventory assistant</div><h2 id="assistantTitle">Get to know this RV.</h2></div><button class="icon-button" data-close aria-label="Close inventory assistant">{icon('close')}</button></div><div class="dialog-body"><p>Ask about the information in this listing. Missing details can go straight to your specialist.</p><div class="assistant-questions"><button data-ask="What are the key specs?">Key specs</button><button data-ask="How many people can it sleep?">Sleeping capacity</button><button data-ask="Show me the brochure and floorplan">Brochure &amp; floorplan</button><button data-ask="Does it have a washer?">Washer / dryer</button></div><form id="assistantForm"><div class="field"><label for="assistantInput">Your question</label><input id="assistantInput" placeholder="Does it have a king bed?" maxlength="300" required></div><button class="button small" type="submit" style="margin-top:12px">Find an answer {icon('arrow')}</button></form><div class="assistant-answers" id="assistantAnswer" aria-live="polite">Answers use this unit's imported specifications and listing text.</div><p class="assistant-disclosure">Listing-based guidance, not a live generative AI service. Optional equipment and missing specifications need confirmation.</p></div></dialog>
<dialog id="viewerDialog" class="viewer-dialog" aria-labelledby="viewerTitle"><div class="dialog-head"><h2 id="viewerTitle">RV photos</h2><button class="icon-button" data-close aria-label="Close viewer">{icon('close')}</button></div><div class="viewer-content" id="viewerContent"></div><div class="viewer-controls"><button class="button outline small" data-photo-step="-1">Previous</button><span class="viewer-count" id="viewerCount"></span><button class="button outline small" data-photo-step="1">Next</button><a id="viewerExternal" class="text-link" target="_blank" rel="noopener" hidden>Open document {icon('arrow')}</a></div></dialog>'''

def document(content, title_text, description, path, config, prefix='', current='shop', body_class='', scripts=True, schema=None):
    canonical=config['origin'].rstrip('/')+'/'+('' if path=='index.html' else path)
    noindex=config['mode']=='preview' or path in ('saved.html','compare.html')
    robots='noindex,follow' if noindex else 'index,follow,max-image-preview:large'
    boot=dict(base=prefix,leadEmail=config['leadEmail'],mode=config['mode'],assistantEndpoint=config.get('assistantEndpoint',''),googleReviewsEndpoint=config.get('googleReviewsEndpoint',''))
    ld=f'<script type="application/ld+json">{J(schema)}</script>' if schema else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title_text)}</title>{('<base href="'+E(config['origin'].rstrip('/')+'/')+'">' if path=='404.html' else '')}<meta name="description" content="{E(description)}"><meta name="robots" content="{robots}"><meta name="theme-color" content="#112c4d"><link rel="canonical" href="{E(canonical)}"><meta property="og:title" content="{E(title_text)}"><meta property="og:description" content="{E(description)}"><meta property="og:type" content="website"><meta property="og:url" content="{E(canonical)}"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="preconnect" href="https://d17qgzvii7d4wm.cloudfront.net"><link rel="stylesheet" href="{prefix}assets/site.css"><link rel="stylesheet" href="{prefix}assets/shopping.css"><link rel="stylesheet" href="{prefix}assets/leads.css"><link rel="stylesheet" href="{prefix}assets/detail.css"><link rel="stylesheet" href="{prefix}assets/restoration.css">{ld}</head><body class="{body_class}">{header(prefix,current,config)}{content}{footer(prefix,config)}{dialogs(prefix,config)}<script id="siteConfig" type="application/json">{json.dumps(boot)}</script><script src="{prefix}assets/core.js" defer></script><script src="{prefix}assets/search.js" defer></script><script src="{prefix}assets/app.js" defer></script><script src="{prefix}assets/leads.js" defer></script><script src="{prefix}assets/detail.js" defer></script></body></html>'''

def home(units, config):
    counts={k:sum(u['type']==k for u in units) for k in TYPE_NAMES}
    types=''.join(f'<a class="type-tile" data-type="{k}" href="{TYPE_PATHS[k]}/"><img src="img/types/{TYPE_IMAGES[k]}.webp" alt="" width="120" height="60"><span>{label}</span><small>{counts[k]} listed</small></a>' for k,label in TYPE_NAMES.items())
    preferred=['MHS44469','MHS43225','MHS43883','M130841','M128068','T147081']
    start=sorted(units,key=lambda u:preferred.index(u['stock']) if u['stock'] in preferred else 100)
    content=f'''<main id="main"><section class="hero"><div class="container hero-layout"><div class="hero-copy"><p class="eyebrow">Where your next chapter begins</p><h1>Big plans.<br><span>The right RV.</span></h1><p class="hero-description">Find the RV that fits your life, your people, and wherever the road takes you.</p><div class="search-wrap"><form class="search-form" id="searchForm" role="search">{icon('search')}<label for="rvSearch" hidden>Search RV inventory in your own words</label><input id="rvSearch" name="q" type="search" aria-label="Search RV inventory in your own words" placeholder="Try “diesel under $150k”" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="suggestions" aria-expanded="false" maxlength="250"><button type="submit" class="button">Search</button></form><div class="suggestions" id="suggestions" role="listbox" hidden></div></div><div class="query-examples"><span>Try:</span><button data-query="used diesel under $150k">Diesel under $150k</button><button data-query="bunkhouse">Room for the family</button><button data-query="camper van">Camper vans</button></div><p class="search-help">{icon('spark')}Not sure where to start? <button data-match>Find my RV match</button></p></div><a class="hero-photo" href="about.html"><img src="assets/showroom.jpg" alt="Motor Home Specialist dealership and motorhome display in Alvarado, Texas" width="1200" height="675" fetchpriority="high"><span class="hero-photo-caption"><span><small>More possibilities. One place.</small><b>Your adventure starts here.</b></span><span class="round-arrow">{icon('arrow')}</span></span></a></div></section><div class="trust-strip"><div class="container trust-inner"><div>{icon('shield')}<span><b>13 years at #1*</b> · Motor Home Specialist</span></div><div>{icon('pin')}<span>Texas · California · Alabama</span></div><div>{icon('message')}<span>Real people. RV expertise.</span></div><div>{icon('book')}<a href="reviews.html">4,571 customer stories {icon('arrow')}</a></div></div></div>{home_extras(units)}<section class="container shop-types"><div class="section-heading"><h2>What kind of adventure?</h2><a class="text-link" href="rv-buying-guide.html">Find your RV type {icon('arrow')}</a></div><div class="type-list">{types}</div></section>{inventory_surface(start,total=len(units))}<section class="container learn-section"><div class="section-heading"><h2>A little know-how goes a long way.</h2><a class="text-link" href="rv-buying-guide.html">Explore the buying guide {icon('arrow')}</a></div>{guide_cards()}</section><section class="owner-section" id="reviews"><div class="container owner-layout"><div class="owner-copy"><p class="eyebrow">The people behind the adventures</p><h2>More than an RV.<br>A story of your own.</h2><p>Browse thousands of customer stories from the people who've started their next chapter with MHSRV.</p><a href="reviews.html" class="text-link">Meet our customers {icon('arrow')}</a></div><figure class="testimonial"><span class="quote-mark" aria-hidden="true">“</span><blockquote>Reasonable prices, a good selection of quality coaches, and great service at Motor Home Specialist!</blockquote><figcaption>The Hawkins family · League City, Texas<br><a href="reviews/2014-forest-river-georgetown-review-class-a-sold-to-the-hawkins-of-league-city-texas.html" class="text-link" style="margin-top:10px;font-size:.8rem">Read their story {icon('arrow')}</a></figcaption></figure></div></section></main>'''
    schema={'@context':'https://schema.org','@type':'AutoDealer','name':'Motor Home Specialist','url':config['origin'],'telephone':'+1-800-335-6054','address':{'@type':'PostalAddress','streetAddress':'5411 South I-35W','addressLocality':'Alvarado','addressRegion':'TX','postalCode':'76009','addressCountry':'US'}}
    return document(content,'New & Used RVs | Find Your Next Adventure | MHSRV','Shop new and used motorhomes, camper vans, fifth wheels and travel trailers. Search in your own words, compare RVs and explore photos, floorplans and specifications.','index.html',config,schema=schema)

def guide_cards(prefix=''):
    cards=[('01 / KNOW YOUR RV','Which RV fits your life?','Understand the differences between motorhomes, camper vans and towable RVs.','rv-buying-guide.html'),('02 / LOOK BEYOND THE PHOTO','The floorplan makes the difference.','Sleeping spaces, bathrooms, storage and how you move through your RV.','floorplan-guide.html'),('03 / ARRIVE PREPARED','Your RV shopping checklist.','The questions to ask before you decide, from equipment to the final price.','rv-shopping-checklist.html')]
    return '<div class="learn-grid">'+''.join(f'<a class="guide-card" href="{prefix}{url}"><span class="guide-number">{n}</span><h3>{h}</h3><p>{p}</p><span class="text-link">Read the guide {icon("arrow")}</span></a>' for n,h,p,url in cards)+'</div>'


from shopping_templates import card, filters, inventory_surface, home_extras
from dealership_templates import header, footer
from detail_templates import detail
