"""Long-tail landing pages: category x colour / material / style / feature / size / price, plus hand-written records.

People search "šedá rohová sedačka", "postel 160x200 s úložným prostorem", "sametové křeslo", "jídelní stůl dub",
"koberec 200x300". Each family below turns the catalogue into such pages; a page exists only with enough products
(MIN, else nothing), and is indexable only from INDEX_MIN products (fewer = noindex,follow and out of the sitemap).
Hand-written records (content/landings/*.json) say WHAT a page is and the engine finds the products:
  {"slug": "...", "h1": "...", "rules": {"cat": ["sedacky"], "any": ["\\bchesterfield\\b"], "colors": ["seda"], "price": [null, 15000]}}
Rule keys: any / all / none (regex on the folded product titles; "scope": "text" adds description + shop paths), cat, brand,
colors, mats, styles, feats (any of), price [lo, hi], wmax / wmin (width in cm), size ("160x200"), offers (min shops).
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import taxonomy as X

APP = Path(__file__).resolve().parent.parent
MIN_DEFAULT, INDEX_MIN_DEFAULT = 6, 12
fold = X.fold

# plural adjective forms: most categories are feminine/masculine-inanimate plural ("šedé sedačky", "šedé koberce"),
# a few are neuter plural ("šedá křesla", "zrcadla", "svítidla") or neuter singular ("povlečení", "osvětlení")
NEUTER_PL = {"kresla", "zrcadla", "stropni-svitidla", "nastenna-svitidla", "venkovni-svitidla", "lustry-xx"}
NEUTER_SG = {"povleceni", "dekoracni-osvetleni"}

COLOR_ADJ = {"bila": "bíl", "cerna": "čern", "seda": "šed", "bezova": "béžov", "hneda": "hněd", "zelena": "zelen", "modra": "modr",
             "ruzova": "růžov", "cervena": "červen", "zluta": "žlut", "oranzova": "oranžov", "zlata": "zlat", "stribrna": "stříbrn"}
MAT_ADJ = {"masiv": "masivní*", "dub": "dubov", "buk": "bukov", "borovice": "borovicov", "orech": "ořechov", "akat": "akátov", "mango": "z mangového dřeva#",
           "teak": "teakov", "kov": "kovov", "samet": "sametov", "boucle": "bouclé*", "kuze": "kožen", "ekokuze": "z ekokůže#", "len": "lněn",
           "ratan": "ratanov", "bambus": "bambusov", "sklo": "skleněn", "mramor": "mramorov", "keramika": "keramick", "bavlna": "bavlněn", "vlna": "vlněn"}
STYLE_ADJ = {"skandinavsky": "skandinávsk", "industrialni": "industriální*", "retro": "retro*", "boho": "boho*", "venkovsky": "venkovsk",
             "japandi": "japandi*", "glamour": "glamour*", "moderni": "moderní*"}
FEAT_ADJ = {"rozkladaci": "rozkládací*", "s-uloznym-prostorem": "s úložným prostorem#", "polohovaci": "polohovací*", "s-led": "s LED osvětlením#",
            "vyskove-nastavitelne": "výškově nastaviteln", "kulate": "kulat"}
COLOR_SLUG = {"bila": "bile", "cerna": "cerne", "seda": "sede", "bezova": "bezove", "hneda": "hnede", "zelena": "zelene", "modra": "modre",
              "ruzova": "ruzove", "cervena": "cervene", "zluta": "zlute", "oranzova": "oranzove", "zlata": "zlate", "stribrna": "stribrne"}
MAT_SLUG = {"masiv": "z-masivu", "dub": "dubove", "buk": "bukove", "borovice": "z-borovice", "orech": "orechove", "akat": "akatove", "mango": "z-manga",
            "teak": "teakove", "kov": "kovove", "samet": "sametove", "boucle": "boucle", "kuze": "kozene", "ekokuze": "z-ekokuze", "len": "lnene",
            "ratan": "ratanove", "bambus": "bambusove", "sklo": "sklenene", "mramor": "mramorove", "keramika": "keramicke", "bavlna": "bavlnene", "vlna": "vlnene"}
STYLE_SLUG = {"skandinavsky": "skandinavsky-styl", "industrialni": "industrialni-styl", "retro": "retro", "boho": "boho", "venkovsky": "venkovsky-styl",
              "japandi": "japandi", "glamour": "glamour", "moderni": "moderni"}


def adj(stem, cat):
    """'šed' -> 'šedé' / 'šedá' / 'šedé' by the category's grammar; '*' = indeclinable before the noun, '#' = after the noun."""
    if stem.endswith("#"):
        return None, stem[:-1]
    if stem.endswith("*"):
        return stem[:-1], None
    if cat in NEUTER_SG:
        end = "é"
    elif cat in NEUTER_PL:
        end = "á"
    else:
        end = "é"
    return stem + ("í" if stem.endswith("í") else end), None


def phrase(stem, cat, noun):
    pre, post = adj(stem, cat)
    noun_l = noun[:1].lower() + noun[1:] if not noun[:2].isupper() else noun
    if pre:
        return f"{pre[:1].upper() + pre[1:]} {noun_l}"
    return f"{noun} {post}"


def hay(p):
    h = p.get("_h")
    if h is None:
        h = fold(" ".join([p["name"], p["dry"], p["desc"][:600], p.get("paths", "")]))
        p["_h"] = h
    return h


def title_hay(p):
    h = p.get("_t")
    if h is None:
        h = fold(p["name"] + " " + p["dry"])
        p["_t"] = h
    return h


def compile_rules(r):
    rx = lambda lst: [re.compile(x) for x in lst]
    any_, all_, none_ = rx(r.get("any", [])), rx(r.get("all", [])), rx(r.get("none", []))
    cats, brands = tuple(r.get("cat", [])), {fold(b) for b in r.get("brand", [])}
    price, offers = r.get("price"), r.get("offers", 0)
    sets = {k: set(r[k]) for k in ("colors", "mats", "styles", "feats") if r.get(k)}
    wmax, wmin, size = r.get("wmax"), r.get("wmin"), r.get("size")
    haystack = hay if r.get("scope") == "text" else title_hay

    def pred(p):
        if cats and p["cat"] not in cats and X.TREE[p["cat"]][1] not in cats:
            return False
        if offers and len(p["offers"]) < offers:
            return False
        if price and ((price[0] is not None and p["price"] < price[0]) or (price[1] is not None and p["price"] > price[1])):
            return False
        if brands and fold(p["brand"]) not in brands:
            return False
        for k, want in sets.items():
            if not want & set(p[k]):
                return False
        if wmax is not None and not (p["wmin"] and p["wmin"] <= wmax):
            return False
        if wmin is not None and not (p["wmax"] and p["wmax"] >= wmin):
            return False
        if size and size not in p["sizes"]:
            return False
        if any_ or all_ or none_:
            h = haystack(p)
            if any_ and not any(x.search(h) for x in any_):
                return False
            if all_ and not all(x.search(h) for x in all_):
                return False
            if none_ and any(x.search(h) for x in none_):
                return False
        return True
    return pred


def load_records():
    recs = []
    for f in sorted((APP / "content/landings").glob("*.json")):
        data = json.loads(f.read_text())
        recs += data if isinstance(data, list) else data.get("pages", [])
    return recs


def nice_cap(n):
    return f"{n:,}".replace(",", " ")


def price_caps(items):
    """2-3 round price caps that split the category sensibly (do 5 000 Kč, do 10 000 Kč…)."""
    ps = sorted(p["price"] for p in items)
    steps = [300, 500, 1000, 2000, 3000, 5000, 7000, 10000, 15000, 20000, 30000, 50000]
    out = []
    for q in (0.25, 0.5):
        v = ps[int(len(ps) * q)]
        cap = next((s for s in steps if s >= v), None)
        if cap and cap not in out:
            out.append(cap)
    return out


def generated_records(products, by_cat):
    recs = []
    for cat, items in by_cat.items():
        if cat not in X.CATS or len(items) < MIN_DEFAULT:
            continue
        name = X.CATS[cat][0]
        noun = name.split(" a ")[0] if cat not in ("taburety-a-sedaci-vaky",) else "Taburety"
        base = {"parent": f"/{cat}/", "cat": cat}
        cnt = lambda key: Counter(x for p in items for x in p[key])
        for c, n in cnt("colors").most_common():
            if n >= MIN_DEFAULT:
                recs.append({**base, "slug": f"{cat}/{COLOR_SLUG[c]}", "h1": phrase(COLOR_ADJ[c], cat, noun), "group": f"{cat}-color",
                             "_pred": (lambda c: lambda p: c in p["colors"])(c), "facet": ("colors", c)})
        for m, n in cnt("mats").most_common():
            if n >= MIN_DEFAULT:
                recs.append({**base, "slug": f"{cat}/{MAT_SLUG[m]}", "h1": phrase(MAT_ADJ[m], cat, noun), "group": f"{cat}-mat",
                             "_pred": (lambda m: lambda p: m in p["mats"])(m), "facet": ("mats", m)})
        for s, n in cnt("styles").most_common():
            if n >= MIN_DEFAULT:
                recs.append({**base, "slug": f"{cat}/{STYLE_SLUG[s]}", "h1": phrase(STYLE_ADJ[s], cat, noun),
                             "group": f"{cat}-style", "_pred": (lambda s: lambda p: s in p["styles"])(s), "facet": ("styles", s)})
        for f_, n in cnt("feats").most_common():
            if n >= MIN_DEFAULT and not (f_ == "kulate" and cat not in ("jidelni-stoly", "konferencni-stolky", "koberce", "zrcadla", "zahradni-stoly")):
                recs.append({**base, "slug": f"{cat}/{f_}", "h1": phrase(FEAT_ADJ[f_], cat, noun), "group": f"{cat}-feat",
                             "_pred": (lambda f_: lambda p: f_ in p["feats"])(f_), "facet": ("feats", f_)})
        for sz, n in cnt("sizes").most_common(14):
            if n >= MIN_DEFAULT and cat in ("postele", "matrace", "rosty", "koberce", "povleceni", "detske-postele", "prikryvky-a-polstare", "behouny-a-predlozky"):
                recs.append({**base, "slug": f"{cat}/{sz.replace('.', '-')}", "h1": f"{name} {sz.replace('x', '×').replace('.', ',')} cm", "group": f"{cat}-size",
                             "_pred": (lambda sz: lambda p: sz in p["sizes"])(sz), "facet": ("sizes", sz),
                             "title": f"{name} {sz.replace('x', '×').replace('.', ',')} – srovnání cen"})
        for cap in price_caps(items):
            recs.append({**base, "slug": f"{cat}/do-{cap}-kc", "h1": f"{name} do {nice_cap(cap)} Kč", "group": f"{cat}-cap",
                         "_pred": (lambda cap: lambda p: p["price"] <= cap)(cap), "facet": ("price", cap)})
        # width caps for big furniture: "sedačka do 200 cm", "skříň 100 cm"
        if cat in ("sedacky", "rohove-sedacky", "pohovky", "satni-skrine", "komody", "jidelni-stoly", "psaci-stoly", "tv-stolky", "botniky", "koupelnove-skrinky"):
            widths = [p["wmin"] for p in items if p["wmin"]]
            if len(widths) >= len(items) * 0.3:
                for wcap in (60, 80, 100, 120, 150, 180, 200, 250):
                    sel = sum(1 for w in widths if w <= wcap)
                    if 12 <= sel <= len(widths) * 0.8:
                        recs.append({**base, "slug": f"{cat}/do-{wcap}-cm", "h1": f"{name} do šířky {wcap} cm", "group": f"{cat}-width",
                                     "_pred": (lambda wcap: lambda p: p["wmin"] is not None and p["wmin"] <= wcap)(wcap), "facet": ("wmax", wcap),
                                     "title": f"{name} do {wcap} cm šířky – srovnání cen"})
    # whole-site hubs people search as one phrase: "skandinávský nábytek", "nábytek z masivu", "ratanový nábytek"
    furniture = [p for c, ps in by_cat.items() if X.TREE[c][1] not in ("svitidla", "textil", "dekorace") for p in ps]
    hubs = [("skandinavsky-nabytek", "Skandinávský nábytek", "styles", "skandinavsky"), ("industrialni-nabytek", "Industriální nábytek", "styles", "industrialni"),
            ("retro-nabytek", "Retro nábytek", "styles", "retro"), ("boho-nabytek", "Boho nábytek", "styles", "boho"),
            ("venkovsky-nabytek", "Venkovský nábytek", "styles", "venkovsky"), ("nabytek-z-masivu", "Nábytek z masivu", "mats", "masiv"),
            ("dubovy-nabytek", "Dubový nábytek", "mats", "dub"), ("ratanovy-nabytek", "Ratanový nábytek", "mats", "ratan"),
            ("sametovy-nabytek", "Sametový nábytek", "mats", "samet"), ("kovovy-nabytek", "Kovový nábytek", "mats", "kov")]
    for slug, h1, key, val in hubs:
        recs.append({"slug": slug, "h1": h1, "group": "hub-" + key, "parent": None, "home": True,
                     "_items": [p for p in furniture if val in p[key]], "facet": (key, val)})
    # combinations people type: colour x material for the biggest categories ("šedá sametová sedačka")
    for cat in ("sedacky", "rohove-sedacky", "pohovky", "kresla", "postele", "jidelni-zidle"):
        items = by_cat.get(cat, [])
        combos = Counter((c, m) for p in items for c in p["colors"][:1] for m in p["mats"] if m in ("samet", "boucle", "kuze", "ekokuze", "len"))
        for (c, m), n in combos.most_common(10):
            if n >= INDEX_MIN_DEFAULT:
                noun = X.CATS[cat][0]
                pre_c, _ = adj(COLOR_ADJ[c], cat)
                h1 = phrase(MAT_ADJ[m], cat, noun)
                h1 = pre_c[:1].upper() + pre_c[1:] + " " + h1[:1].lower() + h1[1:]
                recs.append({"parent": f"/{cat}/{MAT_SLUG[m]}/", "cat": cat, "slug": f"{cat}/{MAT_SLUG[m]}/{COLOR_SLUG[c]}", "h1": h1, "group": f"{cat}-combo",
                             "_pred": (lambda c, m: lambda p: c in p["colors"] and m in p["mats"])(c, m)})
    return recs


def jaccard(a, b):
    return len(a & b) / max(1, len(a | b))


def plan(products, reserved=()):
    """Evaluate all records. Returns landing dicts (path, h1, items, ...) in priority order; skips tiny, duplicate and reserved ones."""
    by_cat = defaultdict(list)
    for p in products:
        by_cat[p["cat"]].append(p)
    recs = load_records() + generated_records(products, by_cat)
    seen_paths, groups, out, dropped = set(reserved), defaultdict(list), [], defaultdict(int)
    for r in recs:
        path = "/" + r["slug"].strip("/") + "/"
        if path in seen_paths:
            dropped["path exists"] += 1
            continue
        if "_items" in r:
            items = r["_items"]
        elif r.get("_pred"):
            pool = by_cat.get(r["cat"], products) if r.get("cat") else products
            items = [p for p in pool if r["_pred"](p)]
        else:
            pred = compile_rules(r.get("rules", {}))
            cats = (r.get("rules") or {}).get("cat", [])
            pool = [p for c in cats for p in by_cat.get(c, [])] + [p for c in cats if c in X.ROOMS for k in X.CATS if X.CATS[k][1] == c for p in by_cat.get(k, [])] if cats else products
            items = [p for p in pool if pred(p)]
        items = [p for p in items if p.get("page", True)]
        if len(items) < r.get("min", MIN_DEFAULT):
            dropped["too few"] += 1
            continue
        if r.get("cat") and len(items) >= 0.95 * len(by_cat.get(r["cat"], [])):
            dropped["same as the category"] += 1
            continue
        ids = {p["id"] for p in items}
        g = r.get("group") or r["slug"].split("/")[0]
        if any(jaccard(ids, o) > 0.9 for o in groups[g]):
            dropped["duplicate of a sibling"] += 1
            continue
        groups[g].append(ids)
        seen_paths.add(path)
        prices = sorted(p["price"] for p in items)
        out.append({"path": path, "slug": r["slug"].strip("/"), "h1": r["h1"], "title": r.get("title"), "lead": r.get("lead"), "desc": r.get("desc"), "items": items,
                    "parent": r.get("parent"), "hubs": r.get("hubs", []), "group": g, "cat": r.get("cat") or ((r.get("rules") or {}).get("cat") or [None])[0],
                    "home": r.get("home", False), "facet": r.get("facet"),
                    "index": len(items) >= r.get("index_min", INDEX_MIN_DEFAULT), "lo": prices[0], "n": len(items)})
    return out, dict(dropped)


def kids_map(landings):
    """path of a hub page -> [(path, h1, n)] of landing pages that belong under it (parent) or want a link from it (hubs)."""
    kids = defaultdict(list)
    for L in landings:
        for hub in set(([L["parent"]] if L["parent"] else []) + list(L["hubs"])):
            kids[hub].append((L["path"], L["h1"], L["n"]))
    return kids


# ---------------------------------------------------------------- guides (content/guides): _index.json = metadata + product-pick rules, <slug>.json = text
def load_guides():
    gd = APP / "content/guides"
    if not (gd / "_index.json").exists():
        return []
    meta = {g["slug"]: g for g in json.loads((gd / "_index.json").read_text())}
    out = []
    for slug, g in meta.items():
        f = gd / f"{slug}.json"
        if f.exists():
            t = json.loads(f.read_text())
            out.append({**g, "intro": t.get("intro", ""), "body": t.get("body", ""), "faq": t.get("faq", []), "description": t.get("description")})
    return out


def guide_picks(products, g, limit=8):
    rules = dict(g.get("rules") or {})
    if g.get("cat"):
        rules["cat"] = g["cat"]
    pred = compile_rules(rules)
    cats = set(rules.get("cat", []))
    pool = [p for p in products if p["cat"] in cats or X.TREE[p["cat"]][1] in cats] if cats else products
    items = [p for p in pool if pred(p) and p["img"] and p.get("page", True)]
    items.sort(key=lambda p: (-len(p["offers"]), p["price"]))
    return items[:limit]
