#!/usr/bin/env python3
"""Import a private NetSource CSV into a strictly allowlisted public catalog.

The input may contain dealer cost and must never be committed or uploaded to Pages.
Usage: python3 tools/import_inventory.py /private/path/feed.csv --date YYYY-MM-DD
"""
import argparse
import csv
import html
import json
import math
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlparse
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
TYPES = {'Class A':'classa','Class B':'classb','Class B+':'classc','Class C':'classc','Diesel Pusher':'diesel','Super C':'superc','Fifth Wheel':'fifth','Toy Hauler':'toy','Travel Trailer':'tt','Teardrop Trailer':'tt'}
LOCATIONS = {'2321':('Alvarado','TX','8003356054'),'29387':('Montgomery','AL','3342880331'),'42183':('Palm Desert','CA','8335191129')}
SPEC_FIELDS = {'Chassis':'Chassis','Engine':'Engine Model','Engine manufacturer':'Engine Manufacturer','Fuel':'Fuel Type','Transmission':'Transmission Spec','Mileage':'Mileage','Length (ft)':'Length','Sleeps':'Sleep Capacity','Slideouts':'# Slideouts','Fresh water (gal)':'Water Capacity - Fresh','Grey water (gal)':'Water Capacity - Grey','Black water (gal)':'Water Capacity - Black','GVWR (lb)':'Gross Vehicle Weight','Dry weight (lb)':'Dry Weight','Hitch weight (lb)':'Hitch Weight','A/C units':'# Air Conditioners','Interior':'Interior Color','Exterior':'Exterior Color','Width':'Width','Height':'Height','VIN':'VIN'}

def text(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()

class DescriptionParser(HTMLParser):
    """Preserve editorial paragraphs and equipment lists without publishing HTML."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks=[]; self.buffer=[]; self.kind='paragraph'; self.ignore=0; self.in_item=False
    def flush(self):
        value=re.sub(r'\s+',' ',' '.join(self.buffer)).strip()
        if value:self.blocks.append({'kind':self.kind,'text':value})
        self.buffer=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.ignore+=1;return
        if self.ignore:return
        if tag in ('p','div','li','br','h1','h2','h3','h4','ul','ol'):
            self.flush()
            if tag=='li':self.in_item=True
            self.kind='item' if self.in_item else 'heading' if tag.startswith('h') else 'paragraph'
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.ignore=max(0,self.ignore-1);return
        if not self.ignore and tag in ('p','div','li','h1','h2','h3','h4'):
            self.flush()
            if tag=='li':self.in_item=False
            self.kind='item' if self.in_item else 'paragraph'
    def handle_data(self,data):
        if not self.ignore:self.buffer.append(data)

def description_sections(value):
    parser=DescriptionParser();parser.feed(value or '');parser.flush()
    result=[]
    for block in parser.blocks:
        # Plain-text feeds may already delimit equipment with bullets/newlines.
        segments=re.split(r'\s*[•●]\s*',block['text'])
        for i,segment in enumerate(segments):
            if segment:result.append({'kind':'item' if i else block['kind'],'text':segment})
    return result

def horsepower(row):
    explicit=number(row.get('Horsepower'))
    if explicit:return explicit
    match=re.search(r'\b(\d{2,4})\s*(?:HP|horsepower)\b',text(row.get('Engine Model')),re.I)
    return int(match[1]) if match else None

def number(value):
    try:
        n = float(str(value or '').replace(',',''))
        if not math.isfinite(n):
            raise ValueError('Non-finite inventory number')
        return int(n) if n.is_integer() else n
    except ValueError:
        return None

def safe_url(url):
    u = urlparse((url or '').strip())
    return u.geturl() if u.scheme == 'https' and u.netloc and not u.username else ''

def read_map(name):
    return json.loads((ROOT/name).read_text())

def import_feed(path, imported):
    fp, videos, brochures = read_map('fpmap.json'), read_map('vidmap.json'), read_map('tools/brochures.json')
    blue_compass = read_map('bcmap.json')
    items, details, seen = [], {}, set()
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        required = {'Stock Number','Year','Brand','Model','Type','Images','Price'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Not a supported NetSource export: required columns are missing.')
        for row in reader:
            stock = text(row.get('Stock Number'))
            kind = TYPES.get(text(row.get('Type')))
            if not stock or not kind:
                continue
            if not re.fullmatch(r'[A-Za-z0-9_*-]+', stock) or stock in seen:
                raise ValueError('Invalid or duplicate stock identifier; nothing was published.')
            seen.add(stock)
            attrs = [text(x).lower() for x in (row.get('Attributes') or '').split('|')]
            status = 'pending' if 'sold - sale pending' in attrs else 'onorder' if 'on order' in attrs else 'coming' if 'coming soon' in attrs else 'listed'
            dealer, item = text(row.get('Dealer ID')), text(row.get('Item ID'))
            city, state, phone = LOCATIONS.get(dealer, (text(row.get('Dealer City')), text(row.get('Dealer State')), '8003356054'))
            photos = []
            floorplan = ''
            for raw in (row.get('Images') or '').split('|'):
                match = re.search(r'/(\d+)/i/(\d+)/o/([^/?;]+)', raw)
                if not match:
                    continue
                d, it, filename = match.groups()
                url = f'https://d17qgzvii7d4wm.cloudfront.net/s3/img.rv/{d}/i/{it}/o/{quote(filename)};width=1200;quality=75'
                if fp.get(stock) and ('_'+str(fp[stock])+'.') in filename:
                    floorplan = url
                else:
                    photos.append(url)
            if fp.get(stock) and not floorplan and dealer and item:
                floorplan = f'https://d17qgzvii7d4wm.cloudfront.net/s3/img.rv/{dealer}/i/{item}/o/1_{dealer}_{item}_{fp[stock]}.jpg;width=1200;quality=75'
            desc = text(row.get('Description'))
            # Do not match generic footer lists advertising other makes or equipment.
            boilerplate = r'\b(?:Shop (?:hundreds|a (?:huge|great|wide|large) selection)|Why buy from|ABOUT US|Visit us at|Choose from (?:Fleetwood|American Coach|Thor|Entegra|Newmar))\b'
            chunks = re.split(boilerplate, desc, maxsplit=1, flags=re.I)
            core = chunks[0].strip()
            if len(chunks)>1:
                actual = re.split(r'\bAbout This RV\b',chunks[1],maxsplit=1,flags=re.I)
                if len(actual)>1:
                    core += ' '+re.split(r'\b(?:About Us|Why buy from)\b',actual[1],maxsplit=1,flags=re.I)[0]
            features = list(dict.fromkeys(text(x) for x in (row.get('Features') or '').split('|') if text(x)))
            year, brand, model = number(row.get('Year')), text(row.get('Brand')), text(row.get('Model'))
            plan = text(row.get('Floorplan'))
            if plan and model.lower().endswith(' '+plan.lower()):
                model=model[:-len(plan)].strip()
            brochure = brochures['stocks'].get(stock)
            if not brochure:
                candidates = [(k,v) for k,v in brochures['catalog'].items() if k.split('|')[0] == brand.lower() and (model.lower() == k.split('|')[1] or model.lower().startswith(k.split('|')[1]+' '))]
                if candidates:
                    k, b = max(candidates, key=lambda x:len(x[0]))
                    by = number(b.get('broyear'))
                    if by and year and 0 <= year-by <= 2:
                        brochure = dict(b, label=f'{by} {b.get("family",model)} factory brochure')
            if brochure:
                label = text(brochure.get('label')) or 'Factory brochure'
                bm = re.search(r'\b(20\d{2})\b', label+' '+str(brochure.get('broyear') or ''))
                by = int(bm[1]) if bm else None
                brochure = {'url':'https://library.rvusa.com/brochure/'+quote(brochure['file']), 'label':label,'year':by,'sameYear':by==year}
            video = videos.get(stock,'')
            if not re.fullmatch(r'[A-Za-z0-9_-]{11}', str(video)):
                video = ''
            specs = {label:text(row.get(column)) for label,column in SPEC_FIELDS.items() if text(row.get(column)) not in ('','n/a','N/A','TBD')}
            for label in ['Width','Height','GVWR (lb)','Dry weight (lb)','Hitch weight (lb)','Length (ft)','Sleeps','Fresh water (gal)','Grey water (gal)','Black water (gal)']:
                if label in specs and number(specs[label])==0:
                    del specs[label]
            unit = {'stock':stock,'year':year,'brand':brand,'model':model,'floorplan':plan,'type':kind,'condition':text(row.get('Condition')).lower(),'price':number(row.get('Sale Price')) or number(row.get('Price')),'msrp':number(row.get('MSRP')),'length':number(row.get('Length')),'sleeps':number(row.get('Sleep Capacity')) or None,'slides':number(row.get('# Slideouts')),'city':city,'state':state,'phone':phone,'status':status,'image':photos[0].replace('width=1200;quality=75','width=640;quality=70') if photos else '', 'photoCount':len(photos),'fuel':text(row.get('Fuel Type')),'mileage':number(row.get('Mileage')),'features':features,'searchText':core[:2400],'hasFloorplan':bool(floorplan),'hasVideo':bool(video),'hasBrochure':bool(brochure),'gvwr':number(row.get('Gross Vehicle Weight')),'dryWeight':number(row.get('Dry Weight')),'updated':imported}
            regular=number(row.get('Price'));price=unit['price'];msrp=unit['msrp']
            unit.update(images=[p.replace('width=1200;quality=75','width=640;quality=70') for p in photos[:6]],
                newArrival='new arrival' in attrs,
                deal=bool(set(attrs)&{'super deals','blow out sale','on special','reduced'}) or bool(price and msrp and (msrp-price)/msrp>=.42),
                regularPrice=regular if regular and price and regular>price else None,
                horsepower=horsepower(row),engine=text(row.get('Engine Model')),chassis=text(row.get('Chassis')),
                exterior=text(row.get('Exterior Color')),interior=text(row.get('Interior Color')))
            bc_id=str(blue_compass.get(stock,''))
            dealer_url=f'https://www.bluecompassrv.com/product/rv-{bc_id}-5' if re.fullmatch(r'\d+',bc_id) else ''
            items.append(unit)
            details[stock] = dict(unit, description=desc,descriptionSections=description_sections(row.get('Description')), photos=photos, floorplanImage=floorplan, brochure=brochure, video=video, tour=safe_url(row.get('Tour 360 URL')), specs=specs,dealerListingUrl=dealer_url,youtubeSearchUrl='https://www.youtube.com/@motorhomespecialist/search?query='+quote(f'{year} {brand} {model} {plan}'))
    if not items:
        raise ValueError('Feed contains no valid inventory. Existing catalog was not changed.')
    return {'updated':imported,'source':'NetSource inventory export','items':items}, details

def write_inventory(catalog, details):
    out = ROOT/'inventory';out.mkdir(exist_ok=True)
    for stock,data in details.items():
        (out/(stock+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (ROOT/'inventory.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n')
    # Keep removed-stock pages as honest unavailable records, never stale active offers.
    for file in out.glob('*.json'):
        if file.stem not in details:
            old = json.loads(file.read_text());old['status']='unavailable'
            # The new feed establishes absence, not fresh prices or specifications.
            old.setdefault('unavailableSince', catalog['updated'])
            file.write_text(json.dumps(old,ensure_ascii=False,separators=(',',':'))+'\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feed',type=Path)
    parser.add_argument('--date',default=date.today().isoformat())
    args = parser.parse_args()
    date.fromisoformat(args.date)
    catalog, details = import_feed(args.feed,args.date)
    write_inventory(catalog, details)
    print(f'Imported {len(details):,} public inventory records, dated {args.date}. No private CSV columns exported.')

if __name__ == '__main__':
    main()
