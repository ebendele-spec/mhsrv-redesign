#!/usr/bin/env python3
"""Build search-index.js: per-unit hp / exterior color words / feature flags
mined from the VDP pages, plus the fuzzy-search vocabulary."""
import re,glob,json,os,html
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw=json.loads(re.search(r'const RAW=(\[.*?\]);\n',open(os.path.join(ROOT,'data.js')).read(),re.S).group(1))
specs=json.loads(re.search(r'const SPECS=(\{.*\});',open(os.path.join(ROOT,'specs.js')).read(),re.S).group(1))

FEATS=['bunk','loft','king bed','queen bed','theater seat','washer','dryer','solar','generator',
 '4x4','awd','all-wheel','outdoor kitchen','bath & 1/2','half bath','two full bath','fireplace',
 'dishwasher','starlink','off-grid','off road','lithium','inverter','satellite','residential fridge',
 'power awning','full wall slide','tankless','heat pump','diesel generator','murphy bed','pet','garage']
COLORS=['white','black','silver','gray','grey','blue','red','green','gold','bronze','brown','champagne','pearl','tan','beige','copper','sand','graphite','charcoal','maroon','burgundy']

IDX={}
for a in raw:
    stk=a[0]
    f=os.path.join(ROOT,'units',stk+'.html')
    d={}
    sp=specs.get(stk,{})
    eng=sp.get('Engine','')+' '+sp.get('Chassis','')
    m=re.search(r'(\d{3,4})\s*\.?\s*hp|(\d{3,4})HP',eng,re.I)
    if m: d['hp']=int(m.group(1) or m.group(2))
    ext=(sp.get('Exterior','') or '').lower()
    cols=[c for c in COLORS if re.search(r'\b'+c+r'\b',ext)]
    if cols: d['col']=cols
    txt=''
    if os.path.exists(f):
        s=open(f,encoding='utf-8').read()
        hl=re.search(r'<h2>Highlights</h2><div class="hl">(.*?)</div>',s)
        desc=re.search(r'<summary>Full description</summary><div class="d-body">([\s\S]*?)</div></details>',s)
        body=desc.group(1) if desc else ''
        body=re.split(r'<p class="d-h">About Us</p>',body)[0]           # drop boilerplate tail
        paras=re.findall(r'<(?:p|li)>(.*?)</(?:p|li)>',body)
        keep=[p for p in paras if 'mhsrv' not in p.lower() and 'shop ' not in p.lower()[:60]]
        txt=((hl.group(1) if hl else '')+' '+' '.join(keep)).lower()
        txt=html.unescape(re.sub(r'<[^>]+>',' ',txt))
        txt=re.sub(r'cab[- ]?over bunk','',txt)   # every Class C has one; not a bunkhouse
    flags=[i for i,t in enumerate(FEATS) if t in txt or ('bunk' in t and 'bunkhouse' in txt)]
    if flags: d['f']=flags
    if d: IDX[stk]=d

# vocabulary for fuzzy/autocomplete
def family(m):
    t=m.split()
    return ' '.join(t[:-1]) if len(t)>1 and re.search(r'\d',t[-1]) else m
vocab=set()
for a in raw:
    vocab.add(a[2])                 # brand
    vocab.add(family(a[3]))        # model family
    vocab.add(a[2]+' '+family(a[3]))
TYPES=['diesel pusher','class a gas','class a','class b','class c','super c','fifth wheel','5th wheel','toy hauler','travel trailer','van','sprinter','bunkhouse','bunk model']
out={'FEATS':FEATS,'COLORS':COLORS,'IDX':IDX,'VOCAB':sorted(vocab)+TYPES}
open(os.path.join(ROOT,'search-index.js'),'w',encoding='utf-8').write(
 '/* Search index mined from VDP specs + descriptions — regenerate with tools/build-search-index.py */\nconst SIDX='+json.dumps(out,separators=(',',':'),ensure_ascii=False)+';\n')
hp=sum(1 for v in IDX.values() if 'hp' in v);co=sum(1 for v in IDX.values() if 'col' in v);fe=sum(1 for v in IDX.values() if 'f' in v)
print(f'index: {len(IDX)} units | hp:{hp} colors:{co} features:{fe} | vocab:{len(out["VOCAB"])} | KB:{os.path.getsize(os.path.join(ROOT,"search-index.js"))//1024}')
