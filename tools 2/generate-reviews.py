#!/usr/bin/env python3
"""Generate all review pages + hub data from mhsrv-reviews-all.json (scraped corpus).
Run from the site root: python3 tools/generate-reviews.py"""
import json,re,os,html,sys

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'mhsrv-reviews-all.json')
if not os.path.exists(SRC):
    sys.exit('mhsrv-reviews-all.json not found in site root')
raw=json.load(open(SRC,encoding='utf-8'))
print('records:',len(raw))

BRANDS2={'forest river','holiday rambler','american coach','grand design','leisure travel','gulf stream','fleetwood rv','thor motor'}
KNOWN={'thor','entegra','tiffin','newmar','winnebago','coachmen','fleetwood','dynamax','nexus','heartland','jayco','keystone','midwest','foretravel','monaco','renegade','gulfstream','airstream','itasca','damon','pleasure-way','roadtrek','crossroads','dutchmen','palomino','cruiser','venture','kz','alliance','drv','brinkley','axiom','ogv','beaver','nu-wa','sportscoach','georgie','safari','country','holiday','american','forest','grand','leisure','gulf'}
MON={'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}

def parse(rec):
    slug,title,stock,text,img,flag,ym=rec
    m=re.match(r'^(\d{4})\s+(.+?)\s+Review,?\s*(.*?)\s+sold to\s+(?:the\s+)?(.+?)\s+of\s+(.+?)\s*$',title,re.I)
    y,unit,typ,buyer,loc=(m.groups() if m else ('', title.replace(' Review',''),'','',''))
    words=unit.split()
    brand=unit
    if len(words)>1:
        two=(words[0]+' '+words[1]).lower()
        brand=words[0]+' '+words[1] if two in BRANDS2 else words[0]
    model=unit[len(brand):].strip() or unit
    date=(MON.get(ym[5:7],'')+' '+ym[:4]).strip() if ym else ''
    return dict(slug=slug,y=int(y) if y.isdigit() else None,unit=unit,brand=brand,model=model,
                typ=typ.strip(' ,'),buyer=buyer,loc=loc,stk=stock,txt=text.strip(),img=img,flag=flag,date=date)

R=[parse(r) for r in raw]
R=[r for r in R if r['slug']]
print('parsed:',len(R))

E=lambda s:html.escape(str(s or ''),quote=True)
def jld(r):
    d={"@context":"https://schema.org","@type":"Review",
       "itemReviewed":{"@type":"Product","name":f"{r['y'] or ''} {r['unit']}".strip()},
       "reviewRating":{"@type":"Rating","ratingValue":"5","bestRating":"5"},
       "author":{"@type":"Person","name":(r['buyer'] or 'Verified MHSRV buyer').title()},
       "publisher":{"@type":"Organization","name":"Motor Home Specialist"},
       "reviewBody":r['txt'][:1200]}
    return json.dumps(d,ensure_ascii=False)

CSS=""":root{--g:#17376A;--gd:#0E2347;--y:#FFC91F;--line:#E4E7E4;--paper:#F7F8F6;--ink:#22262A;--mut:#66706B}
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Barlow',system-ui,sans-serif;background:var(--paper);color:var(--ink);padding-bottom:70px}
.wrap{max-width:720px;margin:0 auto;padding:0 16px}
header{background:var(--g);color:#fff;padding:11px 0}
header .wrap{display:flex;justify-content:space-between;align-items:center}
header a{color:#fff;text-decoration:none;font-weight:700}
.call{background:var(--y);color:var(--gd);padding:8px 13px;border-radius:99px;font-size:13.5px;font-weight:700 !important}
.hero{background:linear-gradient(140deg,#1D4079,var(--gd));color:#fff;padding:22px 0}
.crumb{font-size:12px;opacity:.8}.crumb a{color:#fff}
h1{font-family:'Barlow Condensed',sans-serif;font-size:24px;line-height:1.15;text-transform:uppercase;margin-top:8px}
.stars{color:var(--y);font-size:17px;letter-spacing:2.5px;margin-top:6px}
.meta{font-size:12.5px;opacity:.85;margin-top:6px}
.photo{width:100%;border-radius:12px;margin:16px 0 0;display:block}
blockquote{background:#fff;border:1px solid var(--line);border-left:5px solid var(--y);border-radius:12px;padding:18px;font-size:15.5px;line-height:1.65;margin:16px 0}
.sig{font-size:13px;color:var(--mut);font-weight:600;margin-top:-6px;padding:0 4px 14px}
.ctas{display:grid;gap:8px;grid-template-columns:1fr 1fr;margin:6px 0 18px}
.ctas a{text-align:center;font-size:13.5px;font-weight:700;padding:12px;border-radius:10px;text-decoration:none}
.c1{background:var(--g);color:#fff}.c2{border:1.5px solid var(--g);color:var(--g)}
.pn{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;margin-bottom:20px}
.pn a{color:var(--g);text-decoration:none;font-weight:600;max-width:48%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dock{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid var(--line);display:flex;gap:8px;padding:10px 14px}
.dock a{flex:1;text-align:center;font-size:13.5px;font-weight:700;padding:11px 0;border-radius:10px;text-decoration:none}
.d1{background:var(--g);color:#fff}.d2{border:1.5px solid var(--g);color:var(--g)}.d3{background:var(--y);color:var(--gd)}"""

TPL="""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | MHSRV Reviews</title>
<meta name="description" content="Five-star Motor Home Specialist review: {unit} delivered to {loc}. One of 4,571 verified MHSRV owner reviews.">
<script type="application/ld+json">{jld}</script>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&family=Barlow:wght@400;600;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
<header><div class="wrap"><a href="../index.html">🚌 MHSRV</a><a class="call" href="tel:8003356054">📞 800-335-6054</a></div></header>
<div class="hero"><div class="wrap">
<div class="crumb"><a href="../index.html">Home</a> › <a href="../reviews.html">Reviews</a> › {y}</div>
<h1>{title}</h1>
<div class="stars">★★★★★</div>
<div class="meta">{metaline}</div>
</div></div>
<main class="wrap">
{photo}
<blockquote>{txt}</blockquote>
<p class="sig">— {buyer}, {loc}{datesig}</p>
<div class="ctas">
<a class="c1" href="../index.html?brand={brandq}#inventory">Shop {brand} inventory →</a>
<a class="c2" href="../reviews.html?brand={brandq}">More {brand} reviews</a>
</div>
<div class="pn">{prev}{next}</div>
</main>
<nav class="dock"><a class="d1" href="tel:8003356054">📞 Call</a><a class="d2" href="sms:8177907771">💬 Text</a><a class="d3" href="../index.html#inventory">Shop RVs</a></nav>
</body></html>"""

os.makedirs(os.path.join(ROOT,'reviews'),exist_ok=True)
# clear old sample pages
for f in os.listdir(os.path.join(ROOT,'reviews')):
    if f.endswith('.html'): os.remove(os.path.join(ROOT,'reviews',f))

from urllib.parse import quote
hub=[];redirects=[]
for i,r in enumerate(R):
    title=f"{r['y'] or ''} {r['unit']} Review".strip()
    meta=[]
    if r['stk']:meta.append('Stock #'+r['stk'])
    if r['typ']:meta.append(r['typ'])
    if r['loc']:meta.append('Delivered to '+r['loc'])
    if r['date']:meta.append(r['date'])
    photo=f'<img class="photo" loading="lazy" src="{E(r["img"])}" alt="{E(title)} — customer delivery photo" onerror="this.remove()">' if r['img'] else ''
    prev_=R[i-1] if i>0 else None
    next_=R[i+1] if i<len(R)-1 else None
    prevh=f'<a href="./{prev_["slug"]}.html">← {E((str(prev_["y"] or "")+" "+prev_["unit"]).strip())}</a>' if prev_ else '<span></span>'
    nexth=f'<a href="./{next_["slug"]}.html">{E((str(next_["y"] or "")+" "+next_["unit"]).strip())} →</a>' if next_ else '<span></span>'
    page=TPL.format(title=E(title+(', '+r['typ']+' sold to '+r['buyer']+' of '+r['loc'] if r['loc'] else '')),
        unit=E(f"{r['y'] or ''} {r['unit']}".strip()),loc=E(r['loc'] or 'a happy MHSRV customer'),
        jld=jld(r),css=CSS,y=r['y'] or '',metaline=E(' · '.join(meta)),
        photo=photo,txt=E(r['txt'] or 'Five stars for Motor Home Specialist!'),
        buyer=E((r['buyer'] or 'Verified buyer').title()),datesig=(' · '+r['date'] if r['date'] else ''),
        brand=E(r['brand']),brandq=quote(r['brand']),prev=prevh,next=nexth)
    open(os.path.join(ROOT,'reviews',r['slug']+'.html'),'w',encoding='utf-8').write(page)
    hub.append(dict(slug=r['slug'],y=r['y'],brand=r['brand'],model=r['model'][:40],typ=r['typ'],
                    buyer=(r['buyer'] or '').title()[:40],loc=r['loc'],date=r['date'],stk=r['stk'],
                    txt=(r['txt'][:178]+'…') if len(r['txt'])>180 else r['txt']))
    redirects.append(f"https://www.motorhomespecialistreviews.com/review/{r['slug']}/,/reviews/{r['slug']}.html")

open(os.path.join(ROOT,'reviews-data.js'),'w',encoding='utf-8').write(
 '/* Full corpus: %d reviews scraped from motorhomespecialistreviews.com */\nconst REVIEWS=%s;\n'%(
 len(hub),json.dumps([{ 'slug':h['slug'],'y':h['y'],'brand':h['brand'],'model':h['model'],'type':h['typ'],
 'buyer':h['buyer'],'loc':h['loc'],'date':h['date'],'stk':h['stk'],'txt':h['txt']} for h in hub],ensure_ascii=False,separators=(',',':'))))
open(os.path.join(ROOT,'redirects-301.csv'),'w',encoding='utf-8').write('old_url,new_path\n'+'\n'.join(redirects))
print('pages:',len(R),'| reviews-data.js KB:',os.path.getsize(os.path.join(ROOT,'reviews-data.js'))//1024)
