#!/usr/bin/env python3
"""Validate generated pages, local links, metadata and public data before publishing."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlparse
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'site-config.json').read_text())
errors=[];count=0
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.assets=[];self.canon=[];self.robots=[];self.h1=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag in ('script','img') and a.get('src'):self.assets.append(a['src'])
        if tag=='link' and a.get('rel')=='canonical':self.canon.append(a.get('href'))
        if tag=='link' and a.get('rel')=='stylesheet':self.assets.append(a.get('href'))
        if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content'))

for path in ROOT.rglob('*.html'):
    if any(x.startswith('.') or x in ('node_modules','tools') for x in path.relative_to(ROOT).parts):continue
    count+=1;source=path.read_text();page=Page();page.feed(source)
    if page.h1!=1:errors.append(f'{path.name}: expected one H1')
    if len(page.canon)!=1:errors.append(f'{path.name}: expected one canonical')
    if len(page.ids)!=len(set(page.ids)):errors.append(f'{path.name}: duplicate IDs')
    if CONFIG['mode']=='preview' and 'noindex,follow' not in page.robots:errors.append(f'{path.name}: preview indexing is enabled')
    if 'ebendele@gmail.com' in source:errors.append(f'{path.name}: old lead recipient')
    for raw in page.links+page.assets:
        url=urlparse(raw)
        if url.scheme or url.netloc:continue
        if not url.path:
            if url.fragment and unquote(url.fragment) not in page.ids:errors.append(f'{path.name}: missing #{url.fragment}')
            continue
        target=(path.parent/unquote(url.path)).resolve()
        if target.is_dir():target=target/'index.html'
        if not target.exists():errors.append(f'{path.relative_to(ROOT)}: missing {raw}')
    for block in re.findall(r'<script[^>]+type="application/(?:ld\+json|json)"[^>]*>(.*?)</script>',source,re.S):
        try:json.loads(block)
        except ValueError:errors.append(f'{path.name}: invalid JSON')
    if '"ratingValue"' in source or '"aggregateRating"' in source:errors.append(f'{path.name}: unexpected inferred rating')
    if CONFIG['mode']=='preview' and '"@type": "Offer"' in source:errors.append(f'{path.name}: preview asserts a current offer')
for name in ['sitemap.xml','sitemap-main.xml','sitemap-reviews.xml']:
    tree=ET.parse(ROOT/name)
    for node in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        if not node.text.startswith(CONFIG['origin']+'/'):errors.append(f'{name}: wrong deployment origin')
        relative=unquote(node.text[len(CONFIG['origin'])+1:]);p=ROOT/relative
        if p.is_dir():p=p/'index.html'
        if not p.exists():errors.append(f'{name}: nonexistent {relative}')

if errors:
    print('\n'.join(errors[:30]));print(f'{len(errors)} validation issues.');sys.exit(1)
print(f'Validated {count:,} HTML pages: local links, assets, metadata, schema, anchors and preview indexing. No errors.')
