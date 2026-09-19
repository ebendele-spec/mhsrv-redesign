#!/usr/bin/env python3
"""Rebuild the static website from the public, sanitized inventory and story data.

No third-party packages, API keys, or private feed are required for a rebuild.
The GitHub preview remains noindex. Production indexing requires an explicit
configuration change after the migration and inventory-freshness checks.
"""
import json
import re
from pathlib import Path
from urllib.parse import quote
from datetime import date
import site_templates as t
import lead_templates as leads
import review_templates as reviews
import dealership_templates as dealership

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'site-config.json').read_text())
CATALOG=json.loads((ROOT/'inventory.json').read_text())
UNITS=CATALOG['items']
CONFIG['inventoryDate']=CATALOG['updated']
if CONFIG['mode']=='production' and (date.today()-date.fromisoformat(CATALOG['updated'])).days>2:
    raise SystemExit('Production build stopped: import a fresh inventory feed before enabling indexing.')
PAGES=[]

def write(path,content,indexable=True):
    f=ROOT/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content)
    if indexable:PAGES.append(path)

def page(path,title,description,body,prefix='',schema=None,body_class=''):
    return t.document(body,title+' | MHSRV',description,path,CONFIG,prefix,body_class=body_class,schema=schema)

def article(path,title,description,content):
    body=f'<main id="main" class="container narrow content-page"><div class="page-heading"><p class="eyebrow">The MHSRV buying guide</p><h1>{title}</h1><p>{description}</p></div><article class="article-body">{content}</article><div class="inline-concierge"><div><h3>Make the next step a little easier.</h3><p>Tell us what matters to you. We can help you narrow the choices.</p></div><button class="button" data-match>Find my RV match {t.icon("arrow")}</button></div></main>'
    return page(path,title,description,body)

GUIDES={
 'rv-buying-guide.html':('The right RV starts with your life.','Compare RV types, think through your travel plans, and make a shortlist that fits the way you want to go.', '''<h2>Start with how you’ll travel.</h2><p>Think about who travels with you, how long you stay, where you want to camp, and whether you want to drive or tow your RV. Those decisions make a better starting point than a brand or a floorplan number alone.</p><h2>Motorhomes: drive your home on the road.</h2><p><b>Class A motorhomes</b> offer a bus-style layout, often with substantial living and storage space. Gas Class A and diesel pushers differ in chassis, drivetrain, ride, maintenance and price. Compare the actual coach specifications, not just the category.</p><p><b>Class B camper vans</b> bring living features into a van platform. Look closely at bathroom design, bed setup, storage, standing room and the gear you want to bring.</p><p><b>Class C and B+ motorhomes</b> offer a wide range of sizes and layouts on a cab-and-chassis platform. Some have an over-cab sleeping area; others prioritize a lower-profile design. <b>Super C</b> models use heavier-duty platforms, but capacities still vary by unit.</p><h2>Towables: choose the trailer and tow vehicle together.</h2><p><b>Travel trailers</b> and <b>fifth wheels</b> give you a living space that stays at camp while you use your tow vehicle. Fifth wheels require an appropriate truck and bed-mounted hitch. <b>Toy haulers</b> add a garage-style area for gear; the garage dimensions and weight limits matter.</p><div class="article-callout"><p><b>Type does not establish towing compatibility.</b> Check the exact tow vehicle, hitch, payload and loaded trailer weights. Ask a qualified specialist to verify the combination before committing to an RV.</p></div><h2>Compare the things you’ll use every day.</h2><ul><li>Usable beds, not just a headline sleeping number.</li><li>Bathroom access and living space with slides retracted.</li><li>Kitchen work space, seating, storage and power needs.</li><li>Real measurements for your driveway, storage space and preferred campsites.</li><li>Service requirements, warranty terms and a complete written price.</li></ul><h2>New or pre-owned?</h2><p>New RVs let you compare current designs and manufacturer warranty coverage. Pre-owned RVs may offer a different price point or a discontinued layout. For either, review the unit’s condition, installed options, inspection, service history where available, and delivery process.</p><h2>Build a shortlist you can explain.</h2><p>Save a few promising RVs and compare them side by side. Use the floorplan, photos, specifications and related resources to identify what you know and what you still need to ask. The best shortlist is one that fits your needs, not simply the one with the most features.</p>'''),
 'floorplan-guide.html':('The floorplan is where the decision gets real.','Look past the exterior and picture an ordinary day inside your next RV.', '''<h2>Walk through a normal day.</h2><p>Where does everyone sleep? Who gets up first? Can one person make breakfast while another uses the bathroom? Is there a comfortable place to work, read, eat and relax? A floorplan is most useful when you connect it to these small, everyday moments.</p><h2>Understand every sleeping space.</h2><p>A published sleeping capacity can include a fixed bed, bunks, a dinette or a convertible sofa. Check dimensions, access, setup effort and whether converting a bed changes the usable living space. If sleeping capacity is missing from a listing, ask instead of guessing.</p><h2>Check the layout with the slides in.</h2><p>Ask which areas you can reach when slideouts are retracted. Access to the bathroom, kitchen, refrigerator and bed may change. A walk-through video with the slides in can answer a question that a brochure cannot.</p><h2>Look for the storage you actually need.</h2><p>Consider clothing, groceries, cookware, outdoor chairs, tools and any special equipment. Ask for compartment measurements and cargo capacity. Available space and allowable weight are different questions.</p><h2>Match the document to the unit.</h2><p>Brochures may cover multiple floorplans and show optional equipment. A prior model-year brochure is a reference, not confirmation of the current unit’s layout. Compare the exact stock number, model year and installed options with your specialist.</p><div class="article-callout"><p><b>A useful request:</b> “Please send a video of stock #___ with the slides in, the beds set up, and the storage compartments open.” Specific requests produce more useful answers.</p></div><h2>Bring your measurements.</h2><p>If a bed, doorway, storage bay or aisle must fit something specific, get an actual measurement. Manufacturer drawings are useful references; the unit itself settles the question.</p>'''),
 'rv-shopping-checklist.html':('A better checklist for your next RV.','Keep the questions that matter in one place—from your first shortlist to your visit.', '''<h2>Before you shortlist</h2><ul><li>Set a purchase budget and consider taxes, fees, insurance, storage and maintenance separately.</li><li>Choose a practical length for your storage and intended campsites.</li><li>List your must-haves and the features you can be flexible about.</li><li>If towing, collect the exact vehicle and hitch specifications for a compatibility review.</li></ul><h2>For every RV you compare</h2><ul><li>Confirm the stock number, model year, location and current availability.</li><li>Ask which photos and videos show the actual unit.</li><li>Check whether the brochure matches the model year and floorplan.</li><li>Confirm sleeping spaces and installed equipment, including items described as “prep” or “optional.”</li><li>Request any missing specification or document before your visit.</li></ul><h2>When you’re ready to talk numbers</h2><ul><li>Request a written total with the selling price and all applicable charges.</li><li>Discuss trade-in value separately from the purchase price.</li><li>If financing, review the actual APR, term, amount financed and payment with the lender or finance specialist.</li><li>Ask about deposits, refund terms and any conditions in writing.</li></ul><h2>Before you take delivery</h2><ul><li>Review the inspection, condition and any agreed repairs.</li><li>Get a demonstration of the RV’s systems and safety equipment.</li><li>Confirm the manuals, keys, documents, warranty details and service contacts you’ll receive.</li><li>Ask what to do if a question comes up after you leave.</li></ul><div class="article-callout"><p><b>Make your request specific.</b> Share the stock numbers you’re considering and your top three questions. That lets a specialist prepare useful answers for your visit or video call.</p></div>''')}

def category(path,name,query,items,copy):
    content=f'<main id="main"><div class="container page-heading"><p class="eyebrow">Find your next chapter</p><h1>{name}</h1><p>{copy}</p><div class="search-wrap" style="max-width:760px;margin-top:22px"><form class="search-form" id="searchForm" role="search">{t.icon("search")}<input id="rvSearch" name="q" type="search" aria-label="Search RV inventory" placeholder="Tell us what you’re looking for" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="suggestions" aria-expanded="false"><button class="button">Search</button></form><div class="suggestions" id="suggestions" role="listbox" hidden></div></div></div>{t.inventory_surface(items,"../",heading=name,initial=query,total=len(items))}<section class="container learn-section"><div class="section-heading"><h2>Make an informed shortlist.</h2></div>{t.guide_cards("../")}</section></main>'
    return page(path,name+' for Sale',copy,content,'../')

write('index.html',t.home(UNITS,CONFIG))
for file in sorted((ROOT/'inventory').glob('*.json')):
    u=json.loads(file.read_text());write('units/'+u['stock']+'.html',t.detail(u,UNITS,CONFIG),u['status']!='unavailable')

TYPE_COPY={
 'diesel':'Explore diesel pusher motorhomes with listing photos, floorplans and model resources. Compare lengths, layouts and listed equipment, then confirm the exact coach with a specialist.',
 'classa':'Explore gas Class A motorhomes and compare the layouts, dimensions and features that make each coach different. Save your favorites and see them side by side.',
 'classc':'Explore Class C and B+ motorhomes across a range of sizes and layouts. Compare available sleeping specifications, floorplans and related model videos.',
 'superc':'Explore Super C listings and learn about the chassis, engine and layout of each coach. Capacities and installed equipment vary; confirm the details for your stock number.',
 'classb':'Explore Class B motorhomes and camper vans. Compare compact layouts, bathrooms, bed setups and listed features for your next road trip.',
 'fifth':'Explore fifth wheel layouts, living spaces and published specifications. Ask a specialist to verify compatibility with your exact tow vehicle and hitch.',
 'tt':'Explore travel trailers and compare floorplans, dimensions and available specifications. Choose the trailer and tow vehicle together with a verified compatibility review.',
 'toy':'Explore toy hauler listings and compare living space, garage layout and available specifications. Confirm actual garage dimensions, weights and carrying limits.'}
for key,name in t.TYPE_NAMES.items():
    items=[u for u in UNITS if u['type']==key];query={'diesel':'diesel pusher','classa':'class A gas','classc':'class C','superc':'super C','classb':'camper van','fifth':'fifth wheel','tt':'travel trailer','toy':'toy hauler'}[key]
    write(t.TYPE_PATHS[key]+'/index.html',category(t.TYPE_PATHS[key]+'/',name.title(),query,items,TYPE_COPY[key]))
for condition,name,path in [('new','New RVs','new-rvs-for-sale'),('used','Pre-Owned RVs','used-rvs-for-sale')]:
    write(path+'/index.html',category(path+'/',name,condition,[u for u in UNITS if u['condition']==condition],f'Explore {name.lower()} at Motor Home Specialist. Search by the way you travel, compare real listing details, and get answers from an RV specialist.'))
for name,path in [('Entegra Coach','entegra-rv'),('Tiffin','tiffin-rv'),('Thor Motor Coach','thor-motor-coach'),('Forest River','forest-river-rv'),('Newmar','newmar-rv')]:
    write(path+'/index.html',category(path+'/',name+' RVs',name,[u for u in UNITS if u['brand']==name],f'Shop {name} RV listings with photos, floorplan resources and detailed specifications. Compare individual stock numbers and confirm model-year options with MHSRV.'))
for path,(title,description,content) in GUIDES.items():write(path,article(path,title,description,content))

saved=f'<main id="main" class="container content-page"><div class="page-heading"><p class="eyebrow">Your shortlist</p><h1>The ones worth coming back to.</h1><p id="savedCount">Your saved RVs stay on this device. No account required.</p></div><div class="result-grid" id="savedGrid"><div class="search-loading">Loading your saved RVs…</div></div><div class="inline-concierge"><div><h3>Need help narrowing it down?</h3><p>Compare your favorites or talk through the differences with a specialist.</p></div><a href="compare.html" class="button outline">Compare my RVs {t.icon("arrow")}</a></div></main>'
write('saved.html',page('saved.html','Your Saved RVs','Keep a shortlist of RVs on this device and compare your favorite listings.',saved),False)
compare='<main id="main" class="container compare-page"><div class="page-heading"><p class="eyebrow">A clearer choice</p><h1>Find your differences.</h1><p>Compare up to three RVs side by side. See the price, dimensions, specifications and resources that matter to your decision.</p></div><div id="comparison"><div class="search-loading">Loading your comparison…</div></div></main>'
write('compare.html',page('compare.html','Compare RVs','Compare up to three RVs side by side using actual inventory specifications, photos and resources.',compare),False)

for path,title,desc,body in [
 ('sell-your-rv.html','Sell, Trade or Consign Your RV','Tell MHSRV about your RV and explore selling, trading or consignment.',leads.sell_page(CONFIG)),
 ('trade-in.html','RV and Auto Trade Appraisal','Provide your RV or vehicle details for a specialist appraisal.',leads.trade_page(CONFIG)),
 ('get-prequalified.html','Explore RV Financing','Share your budget, preferred RV and down payment with an MHSRV finance specialist.',leads.finance_page(CONFIG))]:
    write(path,page(path,title,desc,body))
write('about.html',page('about.html','Visit Motor Home Specialist','Dealership hours, directions and buying support in Texas, California and Alabama.',dealership.about(CONFIG)))

stories=reviews.load_stories()
for index,story in enumerate(stories):
    previous=stories[index-1] if index else None
    following=stories[index+1] if index+1<len(stories) else None
    path='reviews/'+story['slug']+'.html'
    write(path,page(path,story['title'],story['text'][:155],reviews.review_detail(story,previous,following,CONFIG),'../'))
write('customer-stories.json',json.dumps(stories,ensure_ascii=False,separators=(',',':'))+'\n',False)
write('reviews.html',page('reviews.html','Customer Stories','Explore historical MHSRV customer stories by brand, RV type, stock number and location.',reviews.review_hub(stories,CONFIG)))

# Ordinary HTML pagination exposes every record even when JavaScript is unavailable.
for kind,records,size in [('inventory',UNITS,36),('review',stories,60)]:
    total=(len(records)+size-1)//size
    for number in range(1,total+1):
        subset=records[(number-1)*size:number*size]
        heading='Browse all RV listings' if kind=='inventory' else 'Browse all customer stories'
        if kind=='inventory':
            entries=''.join(f'<li><a href="../units/{quote(u["stock"],safe="")}.html">{t.E(t.title(u))}</a> — {t.money(u["price"])} · {t.E(u["city"])} · #{t.E(u["stock"])}</li>' for u in subset)
        else:
            entries=''.join(f'<li><a href="../reviews/{r["slug"]}.html">{t.E(r["title"])}</a> · {t.E(r["date"])}</li>' for r in subset)
        pagination=(f'<a class="button outline small" href="{number-1}.html">Previous page</a>' if number>1 else '')+f'<span class="muted">Page {number} of {total}</span>'+(f'<a class="button outline small" href="{number+1}.html">Next page {t.icon("arrow")}</a>' if number<total else '')
        content=f'<main id="main" class="container narrow content-page"><div class="page-heading"><p class="eyebrow">MHSRV directory</p><h1>{heading}</h1><p>Page {number} of {total}. Follow a listing to explore the complete details.</p></div><div class="article-body"><ul>{entries}</ul></div><nav aria-label="Pagination" style="display:flex;gap:18px;align-items:center;margin-top:25px;flex-wrap:wrap">{pagination}</nav></main>'
        path=f'{kind}-pages/{number}.html'
        write(path,page(path,heading+f' · Page {number}',f'{heading}, page {number} of {total}.',content,'../'))

privacy='''<h2>Your inquiries</h2><p>When you submit a contact request, the information you enter is sent through FormSubmit to MHSRV at elisha@mhsrv.com. The request includes the page and stock number you are asking about and available campaign attribution. Do not submit Social Security numbers, financial account details or other sensitive documents.</p><h2>Shopping preferences</h2><p>Your preferred inventory view, recent searches and browsing preferences are stored on this device to personalize suggestions. You can reset recommendations from the homepage. They do not create an account. Calculator assumptions may also be saved locally.</p><h2>Your saved RVs</h2><p>Saved RVs and comparison choices are stored in your browser on this device. They are not an account and do not automatically sync to another device. Clearing your browser storage removes them.</p><h2>Photos, documents and video</h2><p>Photos and fonts may load from external providers. Opening a video, brochure or 360-degree tour loads content from the provider identified by that resource. Those providers may receive normal connection information such as your IP address.</p><h2>Company privacy information</h2><p>This page describes how this preview works. Existing company notices are available in the <a href="ccpa-notice.html">CCPA notice</a> and <a href="your-california-privacy-rights.html">California privacy rights</a> pages. For questions about a shopping inquiry, contact <a href="mailto:elisha@mhsrv.com">elisha@mhsrv.com</a>. The company notices include the contacts for privacy rights requests.</p>'''
write('privacy.html',article('privacy.html','Privacy and your shopping experience.','How contact requests, saved RVs and external resources work on this preview.',privacy))
legal_dir=ROOT/'tools/legal-content';legal_dir.mkdir(exist_ok=True)
for path,title in [('ccpa-notice.html','CCPA Notice for California Consumers'),('your-california-privacy-rights.html','Your California Privacy Rights')]:
    source=legal_dir/(path+'.fragment')
    if not source.exists():
        original=(ROOT/path).read_text();m=re.search(r'<main[^>]*>(.*?)</main>',original,re.S)
        if not m:raise ValueError('Could not preserve existing legal content')
        source.write_text(m[1])
    body='<main id="main" class="container narrow content-page"><article class="article-body" style="padding-top:35px">'+source.read_text()+'</article></main>'
    write(path,page(path,title,'Motor Home Specialist and Blue Compass RV privacy notice.',body))

missing='<main id="main" class="container narrow content-page"><div class="page-heading"><p class="eyebrow">Let’s get you back on the road</p><h1>That page isn’t here.</h1><p>The listing may have moved. Explore the inventory or tell us the stock number you’re looking for.</p></div><a href="index.html#inventory" class="button">Explore inventory</a> <button class="button outline" data-lead="Find a missing listing">Ask a specialist</button></main>'
write('404.html',page('404.html','Page Not Found','Find your way back to the MHSRV inventory.',missing),False)

# Preview is crawlable so search engines can read every static noindex directive.
robots='User-agent: *\nAllow: /\n'
if CONFIG['mode']=='production':robots+='\nSitemap: '+CONFIG['origin'].rstrip('/')+'/sitemap.xml\n'
else:robots+='\n# Design preview: every HTML page has a static noindex,follow directive.\n'
write('robots.txt',robots,False)
main=[p for p in PAGES if not p.startswith('reviews/')];reviews=[p for p in PAGES if p.startswith('reviews/')]
def sitemap(paths):
    urls=[]
    for p in paths:
        canonical=p[:-10] if p.endswith('index.html') else p
        urls.append('<url><loc>'+t.E(CONFIG['origin'].rstrip('/')+'/'+quote(canonical,safe='/'))+'</loc></url>')
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(urls)+'</urlset>\n'
write('sitemap-main.xml',sitemap(main),False);write('sitemap-reviews.xml',sitemap(reviews),False)
write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<sitemap><loc>'+CONFIG['origin'].rstrip('/')+'/'+n+'</loc></sitemap>' for n in ['sitemap-main.xml','sitemap-reviews.xml'])+'</sitemapindex>\n',False)
write('.nojekyll','',False)
print(f'Built {len(PAGES):,} crawlable content pages. Mode: {CONFIG["mode"]}. Lead destination: {CONFIG["leadEmail"]}.')
