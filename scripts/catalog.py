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


def new_shops():
    """Shops with a fresh feed but no frozen weekly range yet (just added to data/shops.json): their first night is a full run."""
    if not WEEKLY.exists():
        return []
    return sorted(p.name.split(".")[0] for p in RAW.glob("*.jsonl.gz") if not (WEEKLY / p.name).exists())


def full_mode():
    """Full run = the range comes straight from the fresh feeds (new products appear, vanished ones go).
    Otherwise (daily/push runs) the range is the weekly snapshot and today's feeds only refresh price and link.
    A new shop (fresh feed, nothing frozen) makes the run full too, so it shows up the next night, not next Wednesday."""
    return os.environ.get("VIAN_FULL") == "1" or not WEEKLY.exists() or bool(new_shops())


def todays_prices(path):
    over = {}
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if float(r.get("p") or 0) > 0 and r.get("go"):
                    over[r["id"]] = (r["p"], r.get("was"), r["go"], r.get("url"))
    return over


CLEAN_SHARE, CLEAN_MIN = 0.85, 5      # a shop category is "clean" when >= 85 % of its titled products are one kind of thing
STATS = {}                            # filled by load_offers: how categories were decided (for the build report)


def load_catmap():
    """Manual exceptions only (data/catmap.json): {"shops": {"<shop>": {"<path prefix>": "<category>" | "skip"}}}.
    Everything else is decided from the data on every run, so a new product in a known shop category needs no work."""
    p = APP / "data/catmap.json"
    return json.loads(p.read_text()).get("shops", {}) if p.exists() else {}


def override(rules, path):
    best = None
    for prefix, cat in rules.items():
        if path.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, cat)
    return best[1] if best else None


def read_shop(s, full):
    p = (RAW if full else WEEKLY) / f"{s['id']}.jsonl.gz"
    if not p.exists():
        return []
    over = {} if full else todays_prices(RAW / f"{s['id']}.jsonl.gz")
    recs = []
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            o = over.get(r["id"])
            if o:
                r["p"], r["was"], r["go"] = o[0], o[1], o[2]
                r["url"] = o[3] or r.get("url")
            recs.append(r)
    return recs


def load_offers(shops):
    """Two passes per shop: 1) what every title says, and per shop category how uniform the titles are; 2) the final
    category from title + clean shop category (taxonomy.decide), with manual exceptions from data/catmap.json."""
    out, dropped = [], Counter()
    full = full_mode()
    catmap = load_catmap()
    source = Counter()
    report = []
    for s in shops:
        recs = read_shop(s, full)
        if not recs:
            continue
        verdicts = [X.title_class(r) for r in recs]
        per_path = defaultdict(Counter)
        for r, (slug, strong) in zip(recs, verdicts):
            if slug and slug != X.VETOED:
                per_path[r.get("cat") or ""][slug] += 1
        clean = {}
        for path, c in per_path.items():
            n = sum(c.values())
            top, tv = c.most_common(1)[0]
            if path and n >= CLEAN_MIN and tv / n >= CLEAN_SHARE:
                clean[path] = top
        rules = catmap.get(s["id"], {})
        conflicts = defaultdict(Counter)
        examples = {}
        for r, verdict in zip(recs, verdicts):
            path = r.get("cat") or ""
            man = override(rules, path) if rules else None
            if man == "skip":
                dropped[s["id"] + ":skip"] += 1
                continue
            if man:
                cat, src = (None, "veto") if verdict[0] == X.VETOED else (man, "manual")
            else:
                cat, src = X.decide(r, verdict, clean.get(path), kids=s.get("kids", False))
            if src == "title>path":
                conflicts[path][verdict[0]] += 1
                examples.setdefault((path, verdict[0]), r["t"][:80])
            source[src] += 1
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
                "brand": X.brand_of(r) or s.get("brand", ""), "ean": norm_ean(r.get("ean")), "mpn": X.clean(r.get("mpn") or "")[:40],
                "img": "" if s.get("no_images") else https(r.get("img")),
                "imgs": [] if s.get("no_images") else [https(u) for u in r.get("imgs") or [] if u][:4],
                "price": round(price), "was": round(float(r.get("was") or 0)), "url": r.get("url") or "", "go": r["go"],
                "cat": cat, "cw": 2 if verdict[1] and verdict[0] == cat else 1,   # the title itself names the category: its vote counts double
                "path": r.get("cat") or "", "dims": X.dims(r["t"], desc, cat),
                "colors": colors, "mats": mats, "styles": styles, "feats": feats,
            })
        for path, c in per_path.items():
            n = sum(c.values())
            top, tv = c.most_common(1)[0]
            k = conflicts.get(path, Counter())
            ex = "; ".join(f"{t}: {examples[(path, t)]}" for t, _ in k.most_common(2))
            report.append((s["id"], path, n, clean.get(path, "-"), round(tv / n, 2), top, sum(k.values()), ex))
    report.sort(key=lambda x: -x[2])
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "catmap-report.tsv").write_text("shop\tshop category\ttitled products\tclean -> our category\ttop share\ttop by titles\ttitle beat the shop\texamples\n"
                                             + "\n".join("\t".join(str(x) for x in row) for row in report))
    STATS.clear()
    STATS.update({"decided_by": dict(source), "clean_shop_categories": sum(1 for r in report if r[3] != "-"), "shop_categories": len(report)})
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


MAX_CODE_GROUP = 12
RX_CODE_TOKEN = re.compile(r"[a-z0-9][a-z0-9.\-/]{2,}[a-z0-9]")
RX_NOT_CODE = re.compile(r"^(\d+([.,]\d+)?(x\d+([.,]\d+)?){1,2}|\d{1,3}(cm|mm|ks|kg|l|w|lm)?|\d+(cm|mm|kg|ks|w|lm|k)|(19|20)\d\d|h\d(h\d)?|e\d\d|gu\d\d|ip\d\d|\d+v\d+)$")


def product_codes(text):
    """Manufacturer product codes in a title or MPN: tokens with at least one digit, 4-14 characters, that are not sizes,
    years, units, firmness grades or bulb sockets ("K292", "XR703", "3197853", "41784000")."""
    out = set()
    for tok in RX_CODE_TOKEN.findall(X.fold(text)):
        tok = re.sub(r"[.\-/]", "", tok)
        if 4 <= len(tok) <= 14 and re.search(r"\d", tok) and not RX_NOT_CODE.match(tok):
            out.add(tok)
    return out


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
        # merge only when the name carries a real model name ("Postel Ikaros", "Skříň Abi V1"), not just dictionary words and
        # the brand ("Sit & More rohová sedačka, textil" is the generic name of hundreds of different sofas)
        if not specific_name(o["name"], o["brand"]):
            continue
        key = (o["shop"], X.fold(o["brand"]), mk, d if len(d) >= 60 else "")
        if key in mfirst:
            mdsu.union(mfirst[key], r)
        else:
            mfirst[key] = r
    # 3) the same model in DIFFERENT shops without a shared EAN: brand + the manufacturer's product code in the title or
    # MPN ("Halmar K292" at eŽidle = "HALMAR Jídelní židle K292" at Kancelářské židle). A code shared by many products
    # (firmness "H3/H4", "2v1", socket "E27") is not a model code: only codes of <= MAX_CODE_GROUP items count, and the
    # prices of one code must not differ more than 2x (a 299 Kč cushion and a 12 000 Kč sofa never share a model).
    by_code = defaultdict(list)
    for r in roots:
        o = items[r][0]
        bt = X.fold(o["brand"]).split()
        if not bt:
            continue
        for c in product_codes(o["title"] + " " + o.get("mpn", "")):
            by_code[(bt[0], c)].append(r)
    linked = 0
    for (brand, code), rs in by_code.items():
        if not 1 < len(rs) <= MAX_CODE_GROUP:
            continue
        if len({items[r][0]["shop"] for r in rs}) < 2:
            continue                   # inside one shop the name rule above decides (codes there are often colour codes)
        ps = [items[r][0]["price"] for r in rs]
        if max(ps) > 2 * min(ps):
            continue
        for r in rs[1:]:
            if mdsu.find(r) != mdsu.find(rs[0]):
                mdsu.union(rs[0], r)
                linked += 1
    STATS["code_links"] = linked
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
        cats = Counter()     # one shop's title says "TV stolek", the other files it under its own category: the title wins
        for o in allo:
            cats[o["cat"]] += o.get("cw", 1)
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


GENERIC = {"textil", "kuze", "latka", "ekokuze", "samet", "velvet", "boucle", "dub", "buk", "kov", "masiv", "sonoma", "set", "sada", "typ", "model",
           "levy", "pravy", "levá", "pravá", "rohova", "rohovy", "s", "se", "a", "na", "do", "pro", "z", "ze", "v", "cm", "mm", "ks", "x", "led", "usb"}


def specific_name(name, brand):
    nice_name("")                     # builds VOCAB
    bt = set(X.fold(brand).split())
    for t in re.findall(r"[^\W_]+", X.fold(name)):
        if t in bt or t in VOCAB or t in GENERIC or len(t) < 2:
            continue
        if any(rx.search(t) for _, _, rx in X.COLORS_RX) or any(rx.search(t) for _, _, rx in X.MATERIALS_RX):
            continue
        if re.fullmatch(r"\d{1,4}(x\d{1,4}){0,2}", t):  # a bare size ("160x200", "90") is not a model name
            continue
        return True
    return False


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
