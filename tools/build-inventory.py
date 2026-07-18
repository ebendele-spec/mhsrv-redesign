#!/usr/bin/env python3
"""Rebuild the site's inventory-derived files from the daily NetSource Media export.

Usage:
    python3 tools/build-inventory.py [path/to/export.csv]

Reads (defaults):
    netsourcemedia_export.csv   — daily inventory export (all dealer locations)
    fpmap.json                  — stock -> floorplan photo id   (persistent enrichment)
    vidmap.json                 — stock -> YouTube video id     (persistent enrichment)
    bcmap.json                  — stock -> brochure id          (persistent enrichment)
    stickermap.json             — stock -> window sticker id    (persistent enrichment)

Regenerates:
    data.js, units/*.html, search-index.js, specs.js, sitemap-main.xml

Prints a summary of adds/removals/price changes against the previous data.js.
"""
import csv
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CF_HOST = "https://d17qgzvii7d4wm.cloudfront.net/s3/img.rv"

TYPE_MAP = {
    "Class A": "classa",
    "Class B": "classb",
    "Class B+": "classc",
    "Class C": "classc",
    "Diesel Pusher": "diesel",
    "Super C": "superc",
    "Fifth Wheel": "fifth",
    "Toy Hauler": "toy",
    "Travel Trailer": "tt",
    "Teardrop Trailer": "tt",
}

TYPE_NAMES = [
    ("classa", "Class A Gas"),
    ("classc", "Class C & B+"),
    ("classb", "Class B / Van"),
    ("diesel", "Diesel Pusher"),
    ("superc", "Super C"),
    ("fifth", "5th Wheel"),
    ("toy", "Toy Hauler"),
    ("tt", "Travel Trailer"),
]

DEALER_LOC = {
    "2321": "MHS Texas — Alvarado",
    "29387": "MHS Alabama",
    "42183": "MHS California",
}


def num(x):
    x = (x or "").replace(",", "").strip()
    if not x:
        return 0
    try:
        return round(float(x))
    except ValueError:
        return 0


def intval(x):
    x = (x or "").strip()
    if not x:
        return 0
    try:
        return int(round(float(x)))
    except ValueError:
        return 0


def ftlen(x):
    """CSV Length '41' / '28.92' -> '41ft' / '28.92ft' (matching original trim rules)."""
    x = (x or "").strip()
    if not x:
        return ""
    if "." in x:
        x = x.rstrip("0").rstrip(".")
    return x + "ft"


def attr_tokens(s):
    return {t.strip() for t in (s or "").split("|") if t.strip()}


def parse_images(s):
    """Images column -> list of (dealer_id, item_id, filename)."""
    out = []
    for u in (s or "").split("|"):
        u = u.strip()
        if not u:
            continue
        m = re.search(r"/(\d+)/i/(\d+)/o/([^|;]+)$", u)
        if m:
            out.append((m.group(1), m.group(2), m.group(3)))
    return out


def load_units(csv_path):
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))
    units = []
    skipped = []
    for r in rows:
        stk = (r.get("Stock Number") or "").strip()
        typ = TYPE_MAP.get((r.get("Type") or "").strip())
        if not stk or not typ:
            skipped.append(stk or "<no-stock>")
            continue
        attrs = attr_tokens(r.get("Attributes"))
        msrp = num(r.get("MSRP"))
        price = num(r.get("Sale Price")) or num(r.get("Price"))
        was = num(r.get("Price")) if num(r.get("Sale Price")) else 0
        imgs = parse_images(r.get("Images"))
        pct = (1 - price / msrp) if (msrp and price) else 0
        u = {
            "stk": stk,
            "year": intval(r.get("Year")),
            "brand": (r.get("Brand") or "").strip(),
            "model": ((r.get("Model") or "").strip() + " " + (r.get("Floorplan") or "").strip()).strip(),
            "type": typ,
            "type_label": (r.get("Type") or "").strip(),
            "cond": (r.get("Condition") or "").strip().lower(),
            "msrp": msrp,
            "price": price,
            "was": was,  # regular price when a lower sale price is active
            "deal": 1 if ("Super Deals" in attrs or "Blow Out Sale" in attrs or "On Special" in attrs
                          or "Reduced" in attrs or pct >= 0.42) else 0,
            "len": ftlen(r.get("Length")),
            "sleeps": intval(r.get("Sleep Capacity")),
            "slides": intval(r.get("# Slideouts")),
            "item": (r.get("Item ID") or "").strip(),
            "dealer": (r.get("Dealer ID") or "").strip(),
            "imgs": imgs,
            "pend": 1 if "Sold - Sale Pending" in attrs else 0,
            "onord": 1 if "On Order" in attrs else (2 if "Coming Soon" in attrs else 0),
            "arrv": 1 if "New Arrival" in attrs else 0,
            "attrs": attrs,
            "row": r,  # full CSV row for VDP/specs generation
        }
        units.append(u)
    return units, skipped


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def build_data_js(units):
    raw_rows = []
    for u in units:
        files = [f for (_d, _i, f) in u["imgs"][:4]]
        raw_rows.append(json.dumps([
            u["stk"], u["year"], u["brand"], u["model"], u["type"], u["cond"],
            u["msrp"], u["price"], u["deal"], u["len"], u["sleeps"], u["slides"],
            len(u["imgs"]), u["item"], files, u["pend"], u["onord"], u["arrv"],
        ], ensure_ascii=False, separators=(",", ":")))
    counts = {}
    for u in units:
        counts[u["type"]] = counts.get(u["type"], 0) + 1
    types_data = [{"id": tid, "name": name, "n": f"{counts.get(tid, 0)} in stock"}
                  for tid, name in TYPE_NAMES]
    # mki derives the dealer id from the image filename (1_<dealer>_<item>_<photo>.jpg)
    # so Alabama/California units get working photos too.
    out = (
        "/* Full MHSRV inventory — generated from the NetSource Media export */\n"
        f'const CF="{CF_HOST}/";\n'
        'const mki=(it,f,w)=>CF+(f.split("_")[1]||"2321")+"/i/"+it+"/o/"+f+";width="+w+";quality=55";\n'
        "function vw24(stk){const d=new Date().toISOString().slice(0,10);const s=stk+d;let h=5381;"
        "for(let i=0;i<s.length;i++)h=((h<<5)+h+s.charCodeAt(i))|0;return 15+Math.abs(h)%96}\n"
        'const SCN=["lake","desert","mountain","family"];\n'
        "const RAW=[" + ",".join(raw_rows) + "];\n"
        "const RVS=RAW.map((a,ri)=>{const pct=a[6]&&a[7]?1-a[7]/a[6]:0;const arrv=!!a[17];"
        "const vw=Math.min(128,vw24(a[0])+(a[8]?18:0)+(arrv?10:0)+Math.round(Math.min(20,pct*40)));"
        "const fs0=(arrv?30:0)+(a[1]>=2027?16:a[1]===2026?8:0)+pct*70+vw*.35+(a[12]>40?6:0)+"
        '(a[5]==="new"?6:0)-(a[15]?60:0)-(a[14][0]?0:50);'
        "return {stk:a[0],y:a[1],brand:a[2],model:a[3],type:a[4],cond:a[5],msrp:a[6],price:a[7],"
        "deal:!!a[8],len:a[9],sleeps:a[10],slides:a[11],photos:a[12],it:a[13],pend:!!a[15],"
        "onord:a[16]===1,coming:a[16]===2,arrv,vw,fs:fs0,scene:SCN[ri%4],"
        'img:a[14][0]?mki(a[13],a[14][0],480):"",imgs:a[14].length>1?a[14].map(p=>mki(a[13],p,480)):null,url:""}});\n'
        "const TYPES_DATA=" + json.dumps(types_data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )
    return out


SPECS_FIELDS = [
    # (SPECS key, CSV column)
    ("Chassis", "Chassis"),
    ("Engine", "Engine Model"),
    ("Fuel", "Fuel Type"),
    ("Interior", "Interior Color"),
    ("Exterior", "Exterior Color"),
    ("A/C units", "# Air Conditioners"),
    ("Mileage", "Mileage"),
    ("Fresh water", "Water Capacity - Fresh"),
    ("GVWR", "Gross Vehicle Weight"),
]


def build_specs_js(units):
    specs = {}
    for u in units:
        r = u["row"]
        d = {}
        for key, col in SPECS_FIELDS:
            v = (r.get(col) or "").strip()
            if key == "Engine" and not v:
                v = (r.get("Engine Manufacturer") or "").strip()
            if v:
                d[key] = v
        if d:
            specs[u["stk"]] = d
    return (
        "/* Per-unit specs extracted from VDP pages — swap for live feed fields in production */\n"
        "const SPECS=" + json.dumps(specs, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )


def build_sitemap(units):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "<url><loc>https://www.mhsrv.com/</loc><priority>1.0</priority></url>",
    ]
    for page in ("about.html", "reviews.html", "sell-your-rv.html", "get-prequalified.html", "saved.html"):
        lines.append(f"<url><loc>https://www.mhsrv.com/{page}</loc><priority>0.8</priority></url>")
    for u in units:
        lines.append(f"<url><loc>https://www.mhsrv.com/units/{u['stk']}.html</loc><priority>0.9</priority></url>")
    lines.append("<url><loc>https://www.mhsrv.com/trade-in.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>")
    for page in ("your-california-privacy-rights.html", "ccpa-notice.html"):
        lines.append(f"<url><loc>https://www.mhsrv.com/{page}</loc><changefreq>yearly</changefreq><priority>0.2</priority></url>")
    lines.append("</urlset>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# VDP (unit page) generation
# ---------------------------------------------------------------------------
import urllib.parse

TOOLS = os.path.dirname(os.path.abspath(__file__))

CHIP_TYPE = {"classa": "Class A Gas", "classb": "Class B / Van", "classc": "Class C & B+",
             "diesel": "Diesel Pusher", "superc": "Super C", "fifth": "5th Wheel",
             "toy": "Toy Hauler", "tt": "Travel Trailer"}
CAT_NAME = {"classa": "Class A Gas", "classb": "Class B Van", "classc": "Class C",
            "diesel": "Diesel Pusher", "superc": "Super C", "fifth": "Fifth Wheel",
            "toy": "Toy Hauler", "tt": "Travel Trailer"}

HIGHLIGHTS = {
    "diesel": ["Rear diesel power", "Air-ride suspension", "Tag axle stability", "Full-body paint",
               "Residential fridge", "Aqua-Hot ready", "Huge basement bays", "Whisper-quiet drive"],
    "classc": ["Cab-over bunk", "Power awning", "Back-up camera", "Generator ready",
               "Sleeps the family", "Easy to drive", "Ducted A/C", "Apple CarPlay"],
    "classa": ["One-piece windshield", "Power awning w/ LED", "Auto leveling jacks", "Onan generator",
               "Back-up monitor", "Basement storage", "Ducted A/C", "King or queen bed"],
    "classb": ["Fits anywhere a truck fits", "High roof", "Solar ready", "Galley kitchen",
               "Wet bath", "Swivel cab seats", "Roof fan", "Off-grid capable"],
    "superc": ["Freightliner chassis", "Massive towing capacity", "Cab-over bunk", "Diesel power",
               "Air-ride seats", "Big-rig braking", "Huge storage", "Sleeps the crew"],
    "fifth": ["Towable luxury", "Raised gooseneck bedroom", "Auto-leveling", "Residential kitchen",
              "Huge slide-outs", "5th-wheel stability", "Basement storage", "Rear living options"],
    "toy": ["Rear ramp door garage", "Fuel station", "Loft sleeping", "Party deck ready",
            "Heavy-duty tie-downs", "Generator", "Outdoor entertainment", "Sleeps the whole crew"],
    "tt": ["A-frame tongue tow", "Power awning", "Outdoor kitchen ready", "Bunk options",
           "Stabilizer jacks", "Pass-through storage", "Ducted A/C", "Easy weekend setup"],
}

FPIMGX = ('<style id="fpimgx">.fp-img{width:100%;border:1px solid var(--line);border-radius:10px;'
          'margin-bottom:10px;background:#fff;display:block}</style>')

DESC_HEADINGS = ["Optional Features", "More About This RV", "About This RV", "Features", "About Us"]


def money(v):
    return f"${v:,}"


def monthly_payment(price):
    L = price * 0.8
    years = 20 if price > 50000 else 15 if price > 20000 else 10
    r = 0.0999 / 12
    n = years * 12
    return round(L * r / (1 - (1 + r) ** -n))


def q(s, safe="/"):
    return urllib.parse.quote(s, safe=safe)


def djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h + ord(c)) & 0xFFFFFFFF
    return h


def cdn(dealer, item, fn, params):
    return f"{CF_HOST}/{dealer}/i/{item}/o/{fn};{params}"


def title_of(u):
    return f"{u['year']} {u['brand']} {u['model']}"


def location_of(u):
    if "MHS Alabama" in u["attrs"]:
        return "MHS Alabama — Montgomery"
    if "MHS California" in u["attrs"]:
        return "MHS California — Palm Desert"
    return "MHS Texas — Alvarado"


def vw_boost(u):
    base = (20 if u["deal"] else 0) + (22 if u["arrv"] else 0) + (10 if u["onord"] else 0)
    return base + djb2(u["stk"]) % 5 if base else 0


def family_of(model):
    toks = model.split()
    while len(toks) > 1 and any(ch.isdigit() for ch in toks[-1]):
        toks.pop()
    return " ".join(toks)


class Assets:
    """Persistent enrichment maps + template chunks."""

    def __init__(self):
        self.fpmap = json.load(open(os.path.join(ROOT, "fpmap.json")))
        self.vidmap = json.load(open(os.path.join(ROOT, "vidmap.json")))
        self.bcmap = json.load(open(os.path.join(ROOT, "bcmap.json")))
        bro = json.load(open(os.path.join(TOOLS, "brochures.json")))
        self.bro_stocks = bro["stocks"]
        self.bro_catalog = bro["catalog"]
        self.type_svgs = json.load(open(os.path.join(TOOLS, "type-svgs.json")))
        self._slice_template(open(os.path.join(TOOLS, "vdp-template.html")).read())

    def _slice_template(self, T):
        def upto(hay, anchor):
            return hay[:hay.index(anchor)]

        def after(hay, anchor):
            return hay[hay.index(anchor) + len(anchor):]

        def between_incl(start, end):
            i = T.index(start)
            return T[i:T.index(end, i)]

        self.c_head = upto(T, "<title>")
        r = after(T, "</script>")  # after ld+json (first </script> follows it)
        self.c_css = upto(r, FPIMGX)
        r = after(r, FPIMGX)
        self.c_body = upto(r, '<div class="hero-photo">')
        self.c_fees = between_incl('    <button class="fee-toggle"', '  <section><h2>Highlights</h2>')
        self.c_calc = between_incl('  <section><h2>Payment estimator</h2>', '  <section><div class="perks">')
        self.c_perks = between_incl('  <section><div class="perks">', '  <section><h2>Owner reviews</h2>')
        self.c_dock = between_incl("</main>", '<div class="modal" id="docmodal"')
        self.js_head = between_incl("<script>\n\nasync function sendLead", "function openLB")
        self.js_gallery = between_incl("function openLB",
                                       "hookStrip(document.getElementById('vstrip'));hookStrip(document.getElementById('lbs'));\n")
        self.js_gallery += "hookStrip(document.getElementById('vstrip'));hookStrip(document.getElementById('lbs'));\n"
        self.js_mid = between_incl("function openModal(){",
                                   "function submitLead(){document.getElementById('formview').style.display='none';"
                                   "document.getElementById('successview').style.display='block'}\n")
        self.js_mid += ("function submitLead(){document.getElementById('formview').style.display='none';"
                        "document.getElementById('successview').style.display='block'}\n")
        self.js_calc = between_incl("const PRICE=", "document.getElementById('term').addEventListener('input',calc);calc();\n")
        self.js_calc += "document.getElementById('term').addEventListener('input',calc);calc();\n"
        # template's own values, patched per unit
        self.tpl_price = re.search(r"^const PRICE=(\d+);", self.js_calc).group(1)
        self.tpl_photo_count = re.search(r" / (\d+)'", self.js_gallery).group(1)

    def brochure_for(self, u):
        e = self.bro_stocks.get(u["stk"])
        if e:
            m = re.match(r"^(\d{4}) (.+) factory brochure$", e["label"])
            return {"file": e["file"], "label": e["label"], "exact": e["exact"],
                    "broyear": m.group(1) if m else None, "family": m.group(2) if m else None}
        best = None
        model_l = u["model"].lower()
        for key, c in self.bro_catalog.items():
            b, fam = key.split("|", 1)
            if b != u["brand"].lower():
                continue
            if model_l == fam or model_l.startswith(fam + " "):
                if not best or len(fam) > len(best[0]):
                    best = (fam, c)
        if not best:
            return None
        fam, c = best
        # a family brochure only applies to nearby model years (year, -1 or -2)
        try:
            if not (0 <= u["year"] - int(c["broyear"]) <= 2):
                return None
        except (TypeError, ValueError):
            return None
        label = f"{c['broyear']} {c['family']} factory brochure" if c["exact"] else "Factory brochure"
        return {"file": c["file"], "label": label, "exact": c["exact"],
                "broyear": c["broyear"], "family": c["family"]}


def build_description_body(desc):
    desc = (desc or "").replace("&", "&amp;")
    # split on runs of ≥3 whitespace chars (incl. NBSP); inside segments collapse only
    # spaces/newlines — single NBSPs and tabs in the feed text are preserved
    segs = [re.sub(r"[ \r\n]+", " ", s).strip() for s in re.split(r"\s{3,}", desc)]
    segs = [s for s in segs if s]
    out = []
    in_features = False
    ul = []

    def flush_ul():
        nonlocal ul
        if ul:
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in ul) + "</ul>")
            ul = []

    def find_heading(seg):
        best = None
        for h in DESC_HEADINGS:
            m = re.search(r"(?:^| )" + re.escape(h) + r"(?: |$)", seg)
            if m:
                pos = seg.index(h, m.start())
                if best is None or pos < best[0] or (pos == best[0] and len(h) > len(best[1])):
                    best = (pos, h)
        return best

    def is_item(seg):
        return len(seg) <= 66 and not re.search(r"[.!?]$", seg) and len(seg.split()) <= 9

    for seg in segs:
        while seg:
            hit = find_heading(seg)
            if hit:
                pos, h = hit
                pre = seg[:pos].strip()
                if pre:
                    flush_ul()
                    if in_features and is_item(pre):
                        out.append(f"<p>{pre}</p>")
                    else:
                        out.append(f"<p>{pre}</p>")
                flush_ul()
                out.append(f'<p class="d-h">{h}</p>')
                in_features = h in ("Features", "Optional Features")
                seg = seg[pos + len(h):].strip()
                if seg:  # remainder attached to a heading renders as a paragraph
                    out.append(f"<p>{seg}</p>")
                    seg = ""
                continue
            if in_features and is_item(seg):
                ul.append(seg)
            else:
                in_features = False
                flush_ul()
                out.append(f"<p>{seg}</p>")
            seg = ""
    flush_ul()
    return "".join(out)


def build_vdp(u, assets, all_units):
    stk = u["stk"]
    TITLE = title_of(u)
    imgs = u["imgs"]
    n = len(imgs)
    price = u["price"]
    msrp = u["msrp"]
    cond_word = "New" if u["cond"] == "new" else "Used"
    cat = CAT_NAME[u["type"]]
    fp_id = assets.fpmap.get(stk)
    bc_id = assets.bcmap.get(stk)
    yt_id = assets.vidmap.get(stk)
    bro = assets.brochure_for(u)

    # --- head ---
    title_tag = f"{TITLE} · {stk} | MHSRV"
    TITLE_ATTR = TITLE.replace("&", "&amp;")  # for attribute contexts (meta content)
    if price:
        save_clause = f", save {money(msrp - price)} off M.S.R.P." if msrp > price else ""
        meta = (f"{cond_word} {TITLE_ATTR} for sale at Motor Home Specialist — {money(price)}{save_clause}. "
                f"{u['len']} {cat}, stock #{stk}. #1 RV dealer in the world, Alvarado TX.")
    else:
        meta = (f"{cond_word} {TITLE_ATTR} for sale at Motor Home Specialist — {u['len']} {cat}, "
                f"stock #{stk}. #1 RV dealer in the world, Alvarado TX.")
    ld = {"@context": "https://schema.org", "@type": "Product", "name": TITLE, "sku": stk,
          "brand": {"@type": "Brand", "name": u["brand"]}, "category": cat,
          "offers": {"@type": "Offer", "price": price, "priceCurrency": "USD",
                     "availability": "https://schema.org/" + ("PreOrder" if u["onord"] else "InStock"),
                     "itemCondition": "https://schema.org/" + ("NewCondition" if u["cond"] == "new" else "UsedCondition"),
                     "seller": {"@type": "AutoDealer", "name": "Motor Home Specialist",
                                "telephone": "+1-800-335-6054"}}}
    if imgs:
        d0, i0, f0 = imgs[0]
        ld["image"] = cdn(d0, i0, f0, "width=860;quality=60")
    ld_json = json.dumps(ld, ensure_ascii=False)

    # --- badge ---
    if u["pend"]:
        badge = '<span class="badge" style="position:static;background:#B4530A;color:#fff">Sale pending</span>'
    elif u["onord"] == 2:
        badge = ('<span class="badge" style="position:static;background:linear-gradient(135deg,#E8873F,#C24E31);'
                 'color:#fff">Coming soon</span>')
    elif u["onord"] == 1:
        badge = ('<span class="badge" style="position:static;background:linear-gradient(135deg,#E8873F,#C24E31);'
                 'color:#fff">On order</span>')
    elif u["arrv"]:
        badge = '<span class="badge" style="position:static;background:#2F7D4C;color:#fff">Just arrived</span>'
    else:
        badge = ""

    # --- gallery ---
    PHOTO_CAP = 80
    shown = min(n, PHOTO_CAP)
    if imgs:
        vs, lb = [], []
        for k, (d, it, fn) in enumerate(imgs[:PHOTO_CAP]):
            lazy = "" if k == 0 else 'loading="lazy" '
            vs.append(f'<img {lazy}src="{cdn(d, it, fn, "width=860;quality=60")}" alt="{TITLE} photo {k+1}" '
                      f'onclick="openLB({k})" onerror="this.remove()">')
            lb.append(f'<img {lazy}src="{cdn(d, it, fn, "width=1200;quality=70")}" alt="{TITLE} photo {k+1}">')
        lb_note = f"{shown} of {n} photos · full resolution" if n > shown else f"{n} photos · full resolution"
        gallery = f'''<div class="hero-photo">
  <div class="vstrip" id="vstrip">{"".join(vs)}</div><div class="g-count" id="gc">1 / {shown}</div>
  <div class="g-badge" style="flex-direction:column;align-items:flex-start">{badge}</div>
  <button class="vnav pv" onclick="stepV(-1)" aria-label="Previous photo">‹</button><button class="vnav nx" onclick="stepV(1)" aria-label="Next photo">›</button>
  <button class="g-save" aria-label="Save" onclick="toggleSave('{stk}',this)">♡</button>
</div>
<button class="morephotos" onclick="openLB(0)">📷 See all <b>{n} photos</b></button>
<div class="views" id="vwbar" hidden>🔥 <b id="vwn"></b> people viewed this unit in the last 24 hours</div>
<div class="lb" id="lb">
  <button class="lb-x" onclick="closeLB()" aria-label="Close">✕</button>
  <div class="lb-strip" id="lbs">{"".join(lb)}</div>
  <button class="vnav pv" style="display:flex" onclick="document.getElementById('lbs').scrollBy({{left:-innerWidth,behavior:'smooth'}})" aria-label="Previous">‹</button>
  <button class="vnav nx" style="display:flex" onclick="document.getElementById('lbs').scrollBy({{left:innerWidth,behavior:'smooth'}})" aria-label="Next">›</button>
  <div class="lb-foot"><span id="lbc">1 / {shown}</span><span class="lb-note">{lb_note}</span></div>
</div>
'''
    else:
        svg = assets.type_svgs[u["type"]]
        gallery = f'''<div class="hero-photo">
  <div style="height:300px;max-width:860px;margin:0 auto;background:linear-gradient(150deg,#1D4079,#0E2347);display:flex;align-items:center;justify-content:center;color:#8FA6C9"><span style="width:260px">{svg}</span></div>
  <div class="g-badge" style="flex-direction:column;align-items:flex-start">{badge}</div>

  <button class="g-save" aria-label="Save" onclick="toggleSave('{stk}',this)">♡</button>
</div>
<div class="morephotos">📷 <b>0 photos</b> &amp; floorplan available — call or text for the full gallery</div>
<div class="views" id="vwbar" hidden>🔥 <b id="vwn"></b> people viewed this unit in the last 24 hours</div>

'''

    # --- titleblock ---
    sleeps_chip = f'<div class="spec-chip"><b>Sleeps</b>{u["sleeps"]}</div>' if u["sleeps"] else ""
    slides_chip = f'<div class="spec-chip"><b>Slides</b>{u["slides"]}</div>' if u["slides"] else ""
    fuel = (u["row"].get("Fuel Type") or "").strip() or "n/a"
    titleblock = f'''  <div class="titleblock">
    <div class="stock">Stock #{stk} · {location_of(u)}</div>
    <h1>{TITLE}</h1>
    <div class="chipsrow">
      <div class="spec-chip"><b>Length</b>{u["len"]}</div>
      <div class="spec-chip"><b>Type</b>{CHIP_TYPE[u["type"]]}</div>
      {sleeps_chip}
      {slides_chip}
      <div class="spec-chip"><b>Condition</b>{"New" if u["cond"] == "new" else "Pre-owned"}</div>
      <div class="spec-chip"><b>Fuel</b>{fuel}</div>
    </div>
  </div>
'''

    # --- price block ---
    if price == 0:
        pc = f'''    <div class="pc-top">
      <div><div class="msrp">M.S.R.P. <s>$0</s></div>
      <div class="special" style="font-size:26px">In transit — arriving soon</div></div>
      <div class="save-pill">Unlock<b>intro price</b>before arrival</div></div>
    <div class="pc-mo">Call <b>800-335-6054</b> to reserve this unit before it hits the lot</div>
'''
    elif u["cond"] == "used":
        pc = f'''    <div class="pc-top">
      <div><div class="msrp">Pre-owned · priced to move</div>
      <div class="special">{money(price)} <small>Our Price</small></div></div></div>
    <div class="pc-mo">Est. <b>{money(monthly_payment(price))}/mo</b> w.a.c.* · 9.99% APR, 20% down</div>
'''
    elif msrp > price:
        sale = f" · Sale <s>{money(u['was'])}</s>" if u["was"] and u["was"] > price else ""
        pct = round((msrp - price) / msrp * 100)
        pc = f'''    <div class="pc-top">
      <div><div class="msrp">M.S.R.P. <s>{money(msrp)}</s>{sale}</div>
      <div class="special">{money(price)} <small>PrecisionPrice</small></div></div>
      <div class="save-pill">You save<b>{money(msrp - price)}</b>{pct}% off</div></div>
    <div class="pc-mo">Est. <b>{money(monthly_payment(price))}/mo</b> w.a.c.* · 9.99% APR, 20% down</div>
'''
    else:
        pc = f'''    <div class="pc-top">
      <div><div class="msrp">M.S.R.P. {money(msrp) if msrp else money(price)}</div>
      <div class="special">{money(price)} <small>PrecisionPrice</small></div></div></div>
    <div class="pc-mo">Est. <b>{money(monthly_payment(price))}/mo</b> w.a.c.* · 9.99% APR, 20% down</div>
'''

    highlights = ('  <section><h2>Highlights</h2><div class="hl">'
                  + "".join(f"<span>{h}</span>" for h in HIGHLIGHTS[u["type"]]) + "</div></section>\n")

    # --- floorplan & documents ---
    sub_parts = [u["len"]]
    if u["slides"]:
        sub_parts.append(f"{u['slides']} slide" + ("s" if u["slides"] != 1 else ""))
    if u["sleeps"]:
        sub_parts.append(f"sleeps {u['sleeps']}")
    fp_sub = " · ".join(sub_parts) + " — tap for layout details"
    # raw (unstripped) Model/Floorplan join — reproduces the original's spacing quirks
    fp_title = (f"{u['row'].get('Model') or ''} {u['row'].get('Floorplan') or ''} floorplan").replace("&", "&amp;")

    if bro and bro["exact"]:
        fp_lead = (f"The official {bro['broyear']} {bro['family']} floorplan drawing with full dimensions is in the "
                   f"factory brochure. Want the exact layout of this coach with options? Text us the stock number "
                   f"<b>#{stk}</b> and we&#39;ll send it right over.")
    else:
        fp_lead = (f"Want the exact floorplan of this coach with dimensions and options? Want the exact layout of "
                   f"this coach with options? Text us the stock number <b>#{stk}</b> and we&#39;ll send it right over.")

    if fp_id and u["item"]:
        fn = f"1_{u['dealer']}_{u['item']}_{fp_id}.jpg"
        fp_img = (f'<img class="fp-img" src="{cdn(u["dealer"], u["item"], fn, "maxwidth=900;quality=70")}" '
                  f'alt="{TITLE} floorplan" loading="lazy" onerror="this.style.display=\'none\'">\n        ')
    else:
        fp_img = "\n        "

    ctas = []
    if bc_id:
        ctas.append(f'<a class="fp-cta" href="https://www.bluecompassrv.com/product/rv-{bc_id}-5'
                    f'#section-detail-floorplan-anchor" target="_blank" rel="noopener">📐 View floorplan drawing</a>')
    if bro and bro["exact"]:
        icon = "📘" if bc_id else "📐"
        ctas.append(f'<a class="fp-cta" href="https://library.rvusa.com/brochure/{bro["file"]}" target="_blank" '
                    f'rel="noopener">{icon} Open factory brochure</a>')
    if not bc_id and not (bro and bro["exact"]):
        ctas.append('<button class="fp-cta" style="border:none;cursor:pointer" '
                    'onclick="openDocReq(\'brochure\')">📐 Request the floorplan</button>')
    sms_fp = q(f"Hi! I'm interested in the {TITLE} (stock #{stk}). Can you send me the floorplan image with "
               f"dimensions and options? Thanks!", safe="/")
    ctas.append(f'<a class="fp-cta" style="background:#fff;color:var(--hwy-green);border:1.5px solid '
                f'var(--hwy-green);margin-left:8px" href="sms:8177907771?&body={sms_fp}">💬 Text us</a>')
    ctas_html = "\n        ".join(ctas)

    docs = []
    if u["cond"] == "new":
        docs.append('<button class="doc" onclick="openDocReq(\'sticker\')"><div class="ic">📄</div>'
                    '<span>Window sticker &amp; M.S.R.P.<span class="sub">We&#39;ll send it to you in minutes — '
                    'full transparency</span></span></button>')
    else:
        docs.append("")  # used units keep an empty slot line where the sticker button would be
    if bro:
        docs.append(f'<a class="doc" href="https://library.rvusa.com/brochure/{bro["file"]}" target="_blank" '
                    f'rel="noopener"><div class="ic">📘</div><span>{bro["label"]}<span class="sub">Full specs '
                    f'&amp; floorplans (PDF)</span></span></a>')
    elif bc_id:
        docs.append(f'<a class="doc" href="https://www.bluecompassrv.com/product/rv-{bc_id}-5" target="_blank" '
                    f'rel="noopener"><div class="ic">📘</div><span>Factory brochure &amp; floorplan'
                    f'<span class="sub">View on BlueCompassRV.com</span></span></a>')
    else:
        docs.append('<button class="doc" onclick="openDocReq(\'brochure\')"><div class="ic">📘</div>'
                    '<span>Factory brochure<span class="sub">We&#39;ll track one down and send it to you'
                    '</span></span></button>')
    if yt_id:
        docs.append(f'<button class="doc vdoc" data-yt="{yt_id}" onclick="playTour(this)">'
                    f'<img class="vd-thumb" loading="lazy" src="https://i.ytimg.com/vi/{yt_id}/hqdefault.jpg" '
                    f'alt=""><span class="vd-shade"></span><span class="vd-play">▶</span><span class="vd-txt">'
                    f'Watch the video tour<span class="sub">Plays right here — no leaving the page</span></span></button>')
    else:
        docs.append(f'<a class="doc" href="https://www.youtube.com/@motorhomespecialist/search?query={q(TITLE, safe="/")}" '
                    f'target="_blank" rel="noopener"><div class="ic">🎬</div><span>Video tour<span class="sub">'
                    f'Watch on MHSRV&#39;s YouTube channel</span></span></a>')
    docs_html = "\n      ".join(docs)

    fpdocs = f'''  <section><h2>Floorplan &amp; documents</h2>
  <div class="fpdocs">
    <div class="fpcard{" open" if fp_id else ""}">
      <button class="fp-toggle" onclick="this.parentElement.classList.toggle('open')" aria-expanded="false">
        <span class="fp-art"><svg viewBox="0 0 120 60" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="4" y="6" width="112" height="48" rx="8"/><path d="M40 6 v20 h-14 M40 26 h-36 M78 54 v-22 h20 M78 32 h38 M56 6 v14 M56 54 v-16"/><rect x="88" y="12" width="20" height="12" rx="2"/><rect x="12" y="38" width="22" height="10" rx="2"/></svg></span>
        <span class="fpt"><b>{fp_title}</b><span class="sub">{fp_sub}</span></span>
        <span class="fp-chev">⌄</span>
      </button>
      <div class="fp-body">{fp_img}<p>{fp_lead}</p>
        {ctas_html}
        <p class="fine">Manufacturer changes and/or options may alter the floorplan of the unit for sale.</p>
      </div>
    </div>
    <div class="docs">
      {docs_html}
    </div>
  </div></section>
'''

    desc_body = build_description_body(u["row"].get("Description"))
    description = (f'  <section><h2>About this coach</h2>\n  <details open><summary>Full description</summary>'
                   f'<div class="d-body">{desc_body}</div></details></section>\n')

    lis = []
    for key, col in SPECS_FIELDS:
        v = (u["row"].get(col) or "").strip()
        if key == "Engine" and not v:
            v = (u["row"].get("Engine Manufacturer") or "").strip()
        if v:
            lis.append(f"<li><b>{key}:</b> {v}</li>")
    specs_sec = ('  <section><h2>Specifications</h2>\n  <details><summary>Chassis, power &amp; capacities</summary>'
                 '<div class="d-body"><ul style="grid-template-columns:1fr">' + "".join(lis)
                 + "</ul></div></details></section>\n")

    reviews = f'''  <section><h2>Owner reviews</h2>
    <a class="review" style="display:block;text-decoration:none;color:inherit" href="../reviews.html?brand={q(u["brand"], safe="")}">
      <div class="stars">★★★★★</div>
      <p><b>4,571 five-star reviews</b> from real MHSRV buyers — including {u["brand"]} owners. Every coach we deliver gets its own review, with photos.</p>
      <footer style="color:var(--hwy-green);font-weight:700">Read {u["brand"]} owner reviews →</footer>
    </a>
  </section>
'''

    # --- similar units ---
    fam = family_of(u["model"])
    pool = [v for v in all_units
            if v["stk"] != stk and v["type"] == u["type"] and v["cond"] == u["cond"] and not v["pend"]]

    def ft(x):
        m = re.match(r"([\d.]+)", x["len"] or "0")
        return float(m.group(1)) if m else 0.0

    def score(v):
        s = 0 if family_of(v["model"]) == fam else 1000
        s += 2 * abs(ft(v) - ft(u))
        s += round(abs(v["price"] - price) / 10000)
        if not v["imgs"]:
            s += 5000
        return (s, -len(v["imgs"]), abs(v["price"] - price), v["stk"])

    sims = sorted(pool, key=score)[:6]
    sim_html = []
    for v in sims:
        if v["imgs"]:
            d, it, fn = v["imgs"][0]
            src = cdn(d, it, fn, "width=480;quality=55")
        else:
            src = ""
        sim_html.append(f'<a class="sim" href="./{v["stk"]}.html"><img loading="lazy" src="{src}" alt="" '
                        f'onerror="this.style.opacity=.2"><div class="s-body"><b>{title_of(v)}</b>'
                        f'<small>#{v["stk"]} · {v["len"]}</small><div class="s-price">{money(v["price"])}</div></div></a>')
    sims_sec = ('  <section><h2>Similar on the lot</h2><div class="sim-rail">\n    '
                + "".join(sim_html) + "\n  </div></section>\n")

    # --- modals ---
    doc_sms = q(f"Hi! Can you text me the factory documents (window sticker / brochure) for the {TITLE} — "
                f"stock #{stk}? Thanks!", safe="/")
    docmodal = f'''<div class="modal" id="docmodal" onclick="if(event.target===this)closeDocReq()"><div class="sheet docsheet">
  <button class="x" onclick="closeDocReq()" aria-label="Close">✕</button>
  <div id="docformview"><span class="ds-tag">FACTORY DOCUMENT</span>
    <h3 id="dochead">Window sticker &amp; M.S.R.P.</h3>
    <p id="docsub"></p>
    <div class="ds-strip" aria-hidden="true"></div>
    <form id="docform" onsubmit="return false">
      <input placeholder="First name" name="first_name" required><input placeholder="Last name" name="last_name">
      <input placeholder="Phone" type="tel" name="phone" required><input placeholder="Email" type="email" name="email">
      <button class="go" id="docbtn" onclick="sendLead(document.getElementById('docform'),(docKind==='brochure'?'Brochure':'Window Sticker')+' Request — {TITLE} #{stk}',this).then(ok=>{{if(ok){{document.getElementById('docformview').style.display='none';document.getElementById('docsuccess').style.display='block';}}}})">📄 Send me the Document</button><a class="go" style="display:block;text-align:center;text-decoration:none;background:#fff;color:var(--hwy-green);border:1.5px solid var(--hwy-green);margin-top:8px" href="sms:8177907771?&body={doc_sms}">💬 Text Us For The Brochure Immediately</a>
    </form>
    <p style="font-size:11px;margin-top:10px;color:var(--muted)">Msg &amp; data rates may apply. Easily unsubscribe at any time.</p>
  </div>
  <div class="success" id="docsuccess"><div class="big">📄</div><h4>It&#39;s on the way!</h4>
    <p>A specialist is pulling the document for stock #{stk} right now — expect a text shortly.</p></div>
</div></div>
'''
    modal = f'''<div class="modal" id="modal" onclick="if(event.target===this)closeModal()"><div class="sheet">
  <button class="x" onclick="closeModal()" aria-label="Close">✕</button>
  <div id="formview"><h3>Unlock your price</h3>
    <p>{TITLE} · #{stk} — or call <a href="tel:8003356054" style="color:var(--hwy-green);font-weight:700">800-335-6054</a></p>
    <form id="leadform" onsubmit="return false">
      <input placeholder="First name" name="first_name" required><input placeholder="Last name" name="last_name">
      <input placeholder="Phone" type="tel" name="phone" required><input placeholder="Email" type="email" name="email" required>
      <button class="go" id="gobtn" onclick="sendLead(document.getElementById('leadform'),'MHSRV Lead — {TITLE} #{stk}',this).then(ok=>{{if(ok)submitLead()}})">Submit</button>
    </form>
    <p style="font-size:11px;margin-top:10px">Msg &amp; data rates may apply. Easily unsubscribe at any time.</p>
  </div>
  <div class="success" id="successview"><div class="big">🤠</div><h4>You're on the board!</h4>
    <p>A specialist will reach out shortly. Skip the line: call 800-335-6054 and mention stock #{stk}.</p></div>
</div></div>
'''

    # --- scripts ---
    js_gallery = assets.js_gallery.replace(f" / {assets.tpl_photo_count}'", f" / {shown}'") if imgs else "\n\n"
    views = (f"(function(){{const stk='{stk}';const d=new Date().toISOString().slice(0,10);const s=stk+d;"
             f"let h=5381;for(let i=0;i<s.length;i++)h=((h<<5)+h+s.charCodeAt(i))|0;\n"
             f"const vw=Math.min(128,15+Math.abs(h)%96+{vw_boost(u)});\n"
             f"if(vw>=35){{document.getElementById('vwn').textContent=vw;"
             f"document.getElementById('vwbar').hidden=false;}}}})();\n")
    save_init = (f"document.addEventListener('DOMContentLoaded',()=>{{const b=document.querySelector('.g-save');"
                 f"if(b&&isSaved('{stk}'))b.textContent='❤️';}});\n")
    js_calc = assets.js_calc.replace(f"const PRICE={assets.tpl_price};", f"const PRICE={price};") if price else "\n"
    profile = (f"</script><script>try{{var _k='mhsrv-profile',_p=JSON.parse(localStorage.getItem(_k))||"
               f"{{t:{{}},b:{{}},p:[],q:[],n:0}};_p.n++;_p.t['{u['type']}']=(_p.t['{u['type']}']||0)+3;"
               f"_p.b['{u['brand']}']=(_p.b['{u['brand']}']||0)+2;{price}&&_p.p.push({price});"
               f"_p.p=_p.p.slice(-20);localStorage.setItem(_k,JSON.stringify(_p))}}catch(e){{}}</script>"
               f'<script src="../footer.js" defer></script>\n</body></html>')

    # --- assemble ---
    return (assets.c_head
            + f"<title>{title_tag}</title>\n"
            + f'<meta name="description" content="{meta}">\n'
            + f'<script type="application/ld+json">{ld_json}</script>'
            + assets.c_css
            + (FPIMGX if fp_id else "")
            + assets.c_body
            + gallery
            + '<main class="wrap">\n'
            + titleblock
            + '  <div class="pricecard">\n'
            + pc
            + assets.c_fees
            + highlights
            + fpdocs
            + description
            + specs_sec
            + (assets.c_calc if price else "")
            + assets.c_perks
            + reviews
            + sims_sec
            + assets.c_dock
            + docmodal
            + modal
            + assets.js_head
            + js_gallery
            + views
            + assets.js_mid
            + save_init
            + js_calc
            + profile)


def read_previous_raw():
    path = os.path.join(ROOT, "data.js")
    if not os.path.exists(path):
        return {}
    src = open(path).read()
    i = src.find("const RAW=")
    if i < 0:
        return {}
    i += len("const RAW=")
    j = src.find("];", i) + 1
    try:
        return {a[0]: a for a in json.loads(src[i:j])}
    except Exception:
        return {}


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "netsourcemedia_export.csv")
    units, skipped = load_units(csv_path)
    prev = read_previous_raw()

    new_stks = {u["stk"] for u in units}
    added = sorted(new_stks - set(prev))
    removed = sorted(set(prev) - new_stks)
    price_changes = []
    for u in units:
        p = prev.get(u["stk"])
        if p and p[7] and u["price"] and u["price"] != p[7]:
            price_changes.append((u["stk"], p[7], u["price"]))

    open(os.path.join(ROOT, "data.js"), "w").write(build_data_js(units))
    open(os.path.join(ROOT, "specs.js"), "w").write(build_specs_js(units))
    open(os.path.join(ROOT, "sitemap-main.xml"), "w").write(build_sitemap(units))

    assets = Assets()
    units_dir = os.path.join(ROOT, "units")
    for u in units:
        open(os.path.join(units_dir, u["stk"] + ".html"), "w").write(build_vdp(u, assets, units))

    # remove VDP pages for units no longer in the feed
    stale = 0
    for fn in os.listdir(units_dir):
        if fn.endswith(".html") and fn[:-5] not in new_stks:
            os.remove(os.path.join(units_dir, fn))
            stale += 1

    # search index is derived from data.js + specs.js + units/*.html
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "build-search-index.py")], cwd=ROOT,
                       capture_output=True, text=True)
    print(r.stdout.strip() or "search-index.js rebuilt")
    if r.returncode != 0:
        print("WARNING: build-search-index.py failed:\n" + r.stderr)

    print(f"data.js/specs.js/sitemap-main.xml + {len(units)} unit pages written"
          + (f" ({len(skipped)} rows skipped: {skipped})" if skipped else ""))
    print(f"added: {len(added)}  removed: {len(removed)}  price changes: {len(price_changes)}  stale pages deleted: {stale}")
    return units, added, removed, price_changes


if __name__ == "__main__":
    main()
