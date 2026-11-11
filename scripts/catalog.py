"""Merge offers from all shops into products (one page per MODEL) and keep everything stable between runs.

1. Offers of the same item in different shops are joined by EAN/GTIN.
2. Items that are variants of one model (same shop wording without size/colour, same description start) become one
   product with a variant list: "Postel Ikaros" in 90×200 / 140×200 / 160×200, three colours -> one page, not nine
   near-duplicate pages. Each variant keeps its own price and shop link.
Slugs, price history and a short snapshot of products that went out of stock live in data/state/state.json.gz
(CI keeps it encrypted as a release asset).
"""
import gzip
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import taxonomy as X

APP = Path(__file__).resolve().parent.parent
RAW = APP / "data/raw"
WEEKLY = APP / "data/weekly"   # offers frozen by the last weekly (full) run: the product range changes only then
STATE = APP / "data/state"
TODAY = date.today()
DAY = TODAY.toordinal()
GONE_DAYS = 45            # an out-of-stock product keeps its page ("momentálně nedostupné") this long, then 404
HISTORY_DAYS = 120


def norm_ean(e):
    d = re.sub(r"\D", "", str(e or ""))
    if len(d) in (8, 12, 13, 14) and set(d) != {"0"}:
        d = d.lstrip("0").zfill(13) if len(d) > 8 else d
        return d if len(d) <= 13 else ""
    return ""


def https(u):
    return "https://" + u[7:] if (u or "").startswith("http://") else (u or "")


# Image sources ranked by weight for the product's main photo (measured 10. 11. 2026): hosts whose renditions we can request small go first,
# datadepo (fixed 688 px, 300-500 kB) last — a product sold by several shops should not get its heaviest photo.
SMALL_IMG = ("media.xxxlutz.com", "cdn.myshoptet.com")


def img_rank(u):
    if not u:
        return 3
    if any(h in u for h in SMALL_IMG):
        return 0
    return 1


def full_mode():
    """Full run = the range comes straight from the fresh feeds (new products appear, vanished ones go).
    Otherwise (daily/push runs) the range is the weekly snapshot and today's feeds only refresh price and link."""
    return os.environ.get("VIAN_FULL") == "1" or not WEEKLY.exists()


def todays_prices(path):
    over = {}
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if float(r.get("p") or 0) > 0 and r.get("go"):
                    over[r["id"]] = (r["p"], r.get("was"), r["go"], r.get("url"))
    return over


def load_offers(shops):
    out, dropped = [], Counter()
    full = full_mode()
    for s in shops:
        p = (RAW if full else WEEKLY) / f"{s['id']}.jsonl.gz"
        if not p.exists():
            continue
        over = {} if full else todays_prices(RAW / f"{s['id']}.jsonl.gz")
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                o = over.get(r["id"])
                if o:
                    r["p"], r["was"], r["go"] = o[0], o[1], o[2]
                    r["url"] = o[3] or r.get("url")
                cat = X.classify(r, kids=s.get("kids", False))
                if not cat:
                    dropped[s["id"]] += 1
                    continue
                price = float(r["p"] or 0)
                if price <= 0 or not r.get("go") or price < X.PRICE_FLOOR.get(cat, 0):
                    dropped[s["id"] + ":cheap"] += 1 if price > 0 else 0
                    continue
                name, params = X.split_variant(r["t"])
                desc = X.clean(re.sub(r"<[^>]+>", " ", r.get("d") or ""))
                colors, mats, styles, feats = X.attrs(r["t"], r.get("col"), desc)
                out.append({
                    "shop": s["id"], "oid": r["id"], "title": X.clean(r["t"]), "name": name, "params": params, "desc": desc,
                    "brand": X.brand_of(r) or s.get("brand", ""), "ean": norm_ean(r.get("ean")),
                    "img": "" if s.get("no_images") else https(r.get("img")),
                    "imgs": [] if s.get("no_images") else [https(u) for u in r.get("imgs") or [] if u][:4],
                    "price": round(price), "was": round(float(r.get("was") or 0)), "url": r.get("url") or "", "go": r["go"],
                    "cat": cat, "path": r.get("cat") or "", "dims": X.dims(r["t"], desc, cat),
                    "colors": colors, "mats": mats, "styles": styles, "feats": feats,
                })
    return out, dropped


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def mixed(s):
    """Prefer normally cased titles over SHOUTING ones."""
    letters = [c for c in s if c.isalpha()]
    return sum(1 for c in letters if c.islower()) / (len(letters) or 1)


def variant_label(o):
    """What tells this variant apart: shop parameters ("Rošt: Bez roštu"), else size and colour."""
    if o["params"]:
        return o["params"][:90]
    bits = []
    sl = X.size_label(o["dims"])
    if sl:
        bits.append(sl)
    if o["colors"]:
        bits.append(", ".join(X.COLOR_NAME[c] for c in o["colors"][:2]))
    return " · ".join(bits) or o["title"][len(o["name"]):].strip(" ,-–")[:60] or "základní provedení"


def cluster(offers, shop_rank):
    # 1) same item across shops (EAN)
    dsu = DSU()
    first = {}
    for i, o in enumerate(offers):
        dsu.find(i)
        if o["ean"]:
            k = "e:" + o["ean"]
            if k in first:
                dsu.union(first[k], i)
            else:
                first[k] = i
    items = defaultdict(list)
    for i in range(len(offers)):
        items[dsu.find(i)].append(offers[i])
    # 2) items -> models: same brand + same wording without size/colour + same description start (or a long, specific name)
    mdsu = DSU()
    mfirst = {}
    roots = list(items)
    for r in roots:
        mdsu.find(r)
        o = items[r][0]
        mk = X.model_key(o["name"])
        words = mk.split()
        d = re.sub(r"\W+", " ", o["desc"][:160].lower()).strip()
        if len(d) >= 60:
            key = (o["shop"], X.fold(o["brand"]), mk, d)
        elif len(words) >= 3 and re.search(r"[A-Z0-9]", o["name"][len(words[0]):]):
            key = (o["shop"], X.fold(o["brand"]), mk, "")
        else:
            continue
        if key in mfirst:
            mdsu.union(mfirst[key], r)
        else:
            mfirst[key] = r
    models = defaultdict(list)
    for r in roots:
        models[mdsu.find(r)].append(items[r])

    products = []
    for variants in models.values():
        allo = [o for v in variants for o in v]
        eans = sorted({o["ean"] for o in allo if o["ean"]})
        pid = ("e:" + eans[0]) if eans else f"o:{allo[0]['shop']}:{allo[0]['oid']}"
        var = []
        for v in variants:
            best = {}
            for o in sorted(v, key=lambda o: o["price"]):
                best.setdefault(o["shop"], o)
            offs = sorted(best.values(), key=lambda o: (o["price"], shop_rank.get(o["shop"], 99)))
            var.append({"label": variant_label(offs[0]), "title": offs[0]["title"], "price": offs[0]["price"], "img": offs[0]["img"], "dims": offs[0]["dims"],
                        "colors": offs[0]["colors"], "offers": [{"shop": o["shop"], "price": o["price"], "was": o["was"], "go": o["go"], "url": o["url"]} for o in offs]})
        if len(var) > 1:      # what really differs between the variants: words that are not shared by all of them
            toks = [re.findall(r"[^\s,;:()]+", v["title"]) for v in var]
            common = set.intersection(*[{t.lower() for t in tk} for tk in toks])
            for v, tk in zip(var, toks):
                parts = []
                for i, t in enumerate(tk):
                    if t.lower() not in common:
                        unit = tk[i + 1] if i + 1 < len(tk) and tk[i + 1].lower() in ("cm", "mm", "ks", "l") and re.search(r"\d$", t) else ""
                        parts.append(t + (" " + unit if unit else ""))
                diff = " · ".join(parts).strip(" -–/·")
                if diff and len(diff) <= 90:
                    v["label"] = diff
            base = [t for t in toks[0] if t.lower() in common]
        var.sort(key=lambda v: v["price"])
        # model-level offers: the cheapest variant per shop (listings, "od X Kč", shop filter)
        best = {}
        for v in var:
            for o in v["offers"]:
                if o["shop"] not in best or o["price"] < best[o["shop"]]["price"]:
                    best[o["shop"]] = o
        shop_offers = sorted(best.values(), key=lambda o: (o["price"], shop_rank.get(o["shop"], 99)))
        rep = sorted(allo, key=lambda o: (shop_rank.get(o["shop"], 99), -mixed(o["name"]), len(o["name"])))[0]
        if len(variants) > 1:     # model name = the words all variants share, in the representative's order ("Postel Ikaros")
            words = re.findall(r"\S+", rep["name"])
            commonw = set.intersection(*[{w.lower().strip(",;:") for w in re.findall(r"\S+", v[0]["name"])} for v in variants])
            keep = [w.lower().strip(",;:") in commonw for w in words]
            for i, w in enumerate(words):    # a unit whose number differs between variants goes too ("pro výšku jádra 18 cm" -> "pro výšku jádra")
                if keep[i] and w.lower().strip(",;:") in ("cm", "mm", "ks", "l", "x", "×", "/") and (i == 0 or not keep[i - 1]):
                    keep[i] = False
            kept = [w for w, k in zip(words, keep) if k]
            nm = re.sub(r"[\s,;:–-]+$", "", " ".join(kept))
            name = nice_name(nm if len(kept) >= 2 else rep["name"])
        else:
            name = nice_name(rep["title"] if not rep["params"] else rep["name"])
        brands = Counter(o["brand"] for o in allo if o["brand"])
        cats = Counter(o["cat"] for o in allo)
        desc = max((o["desc"] for o in allo), key=len)
        img = next((o["img"] for o in sorted(allo, key=lambda o: (img_rank(o["img"]), o["price"])) if o["img"]), "")
        imgs = []
        for o in allo:
            for u in [o["img"]] + o["imgs"]:
                if u and u != img and u not in imgs:
                    imgs.append(u)
        widths = sorted({o["dims"].get("w") for o in allo if o["dims"].get("w")})
        sizes = sorted({o["dims"]["size"] for o in allo if o["dims"].get("size")}, key=lambda s: [float(x) for x in s.split("x")])
        dm = dict(next((o["dims"] for o in sorted(allo, key=lambda o: o["price"]) if o["dims"]), {}))
        uniq = lambda key: [k for k, _ in Counter(x for o in allo for x in o[key]).most_common()]
        products.append({
            "id": pid, "name": name, "brand": brands.most_common(1)[0][0] if brands else "", "ean": eans[0] if eans else "",
            "cat": cats.most_common(1)[0][0], "desc": desc, "img": img, "imgs": imgs[:7],
            "dry": " ".join({o["name"] for o in allo}).lower()[:600],
            "paths": " ".join(sorted({o["path"] for o in allo if o["path"]}))[:500],
            "offers": shop_offers, "price": shop_offers[0]["price"], "variants": var if len(var) > 1 else [],
            "dims": dm, "wmin": widths[0] if widths else None, "wmax": widths[-1] if widths else None, "sizes": sizes,
            "colors": uniq("colors")[:4], "mats": uniq("mats")[:4], "styles": uniq("styles")[:2], "feats": uniq("feats"),
        })
    return products


VOCAB = None


def nice_name(n):
    """XXXLutz writes the noun in capitals ("Carryhome ROHOVÁ SEDACÍ SOUPRAVA, šedá"). Capitalised dictionary words
    (furniture nouns and adjectives) go lower case, other shouting words (model and brand names: IKAROS) become Ikaros."""
    global VOCAB
    if VOCAB is None:
        VOCAB = set()
        for v in list(X.TREE.values()):
            for w in re.findall(r"[^\W\d_]+", (v[0] + " " + v[2]).lower()):
                VOCAB.add(X.fold(w))
        VOCAB |= {X.fold(w) for w in ("postel postele čalouněná čalouněné dětská dětské manželská americká jednolůžková dvoulůžková boxspring rohová rohové "
                                      "sedací souprava soupravy sedačka pohovka křeslo židle stůl stolek skříň skříňka komoda regál police knihovna "
                                      "matrace rošt lampa svítidlo lustr koberec zrcadlo obraz plakát závěs záclona povlečení polštář deka přehoz "
                                      "jídelní konferenční noční psací kancelářská herní barová zahradní koupelnová šatní botník věšák taburet vitrína "
                                      "lavice stěna obývací vysoká nízká rozkládací relaxační houpací stojací stolní nástěnná závěsná stropní "
                                      "zářič fototapeta samolepka tapeta hodiny váza květináč svícen svíčka dekorace sada set kus ks a s se na do pro z").split()}
    def fix(m):
        w = m.group(0)
        if sum(1 for c in w if c.isalpha()) < 4 and X.fold(w.lower()) not in VOCAB:
            return w                                   # LED, TV, MDF, XL stay
        return w.lower() if X.fold(w.lower()) in VOCAB else w[:1] + w[1:].lower()
    n = re.sub(r"\b[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]+\b", fix, n)
    n = re.sub(r"\s+,", ",", n).strip(" ,-–")
    return n[:1].upper() + n[1:]


def sanity(products):
    """Price errors in feeds: an offer under 45 % of the same product's other offers is dropped."""
    dropped = 0
    for p in products:
        if len(p["offers"]) < 3:
            continue
        keep = []
        for o in p["offers"]:
            others = [x["price"] for x in p["offers"] if x is not o]
            if o["price"] < 0.45 * statistics.median(others):
                dropped += 1
            else:
                keep.append(o)
        p["offers"] = keep
        p["price"] = keep[0]["price"]
    return dropped


# ---------------------------------------------------------------- slugs, history, gone products

def product_slug(p):
    s = X.slugify(p["name"])
    if p["brand"] and not s.startswith(X.slugify(p["brand"])) and X.slugify(p["brand"]) not in s:
        s = X.slugify(p["brand"]) + "-" + s
    return s[:90].rsplit("-", 1)[0] if len(s) > 90 else s


def assign_slugs(products, state):
    slugs = state.setdefault("slugs", {})
    used = set(slugs.values())
    new = 0
    for p in products:
        if p["id"] in slugs:
            continue
        base = product_slug(p) or "produkt"
        s, i = base, 2
        while s in used:
            s, i = f"{base}-{i}", i + 1
        slugs[p["id"]] = s
        used.add(s)
        new += 1
    for p in products:
        p["slug"] = slugs[p["id"]]
    return new


def price_history(products, state):
    """Change points [day, price] per product; the 30-day low is what shoppers care about (and it is honest:
    only prices we saw ourselves)."""
    ph = state.setdefault("ph", {})
    for p in products:
        h = ph.setdefault(p["id"], [])
        if not h or h[-1][1] != p["price"] or DAY - h[-1][0] >= 7:
            if h and h[-1][0] == DAY:
                h[-1][1] = p["price"]
            else:
                h.append([DAY, p["price"]])
        while len(h) > 1 and h[1][0] <= DAY - HISTORY_DAYS:
            h.pop(0)
        p["hist"] = h
        prices = [x[1] for x in h if x[0] >= DAY - 30] + ([h[0][1]] if h and h[0][0] < DAY - 30 else [])
        p["low30"] = min(prices) if prices else p["price"]
        p["since"] = h[0][0]
    live = {p["id"] for p in products}
    for k in list(ph):
        if k not in live and (not ph[k] or ph[k][-1][0] < DAY - HISTORY_DAYS):
            ph.pop(k)


def gone_products(products, state, last_seen_snapshot):
    """Products that disappeared keep a "momentálně nedostupné" page for GONE_DAYS (search engines and links keep
    working; the page points to similar pieces), then they 404."""
    gone = state.setdefault("gone", {})
    live = {p["id"] for p in products}
    for pid, snap in last_seen_snapshot.items():
        if pid not in live and pid not in gone:
            gone[pid] = dict(snap, day=DAY)
    for pid in list(gone):
        if pid in live or gone[pid]["day"] < DAY - GONE_DAYS:
            gone.pop(pid)
    state["snap"] = {p["id"]: {"slug": p["slug"], "name": p["name"], "brand": p["brand"], "cat": p["cat"], "img": p["img"],
                               "price": p["price"]} for p in products if p.get("page")}
    return gone


def load_state():
    p = STATE / "state.json.gz"
    if p.exists():
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    STATE.mkdir(parents=True, exist_ok=True)
    with gzip.open(STATE / "state.json.gz", "wt", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, separators=(",", ":"))
