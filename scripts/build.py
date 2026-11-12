#!/usr/bin/env python3
"""Build the static vian.cz site into dist/ from data/raw/*.jsonl.gz.

    VIAN_ENV=production python3 scripts/build.py      # indexable build (default: staging = noindex everywhere)
    VIAN_MAX_PRODUCTS=20000 python3 scripts/build.py  # cap product pages (staging on workers.dev has no shards)

Output is plain files: Workers static assets serve them for free. When the site has more files than one Worker version
may hold (100 000), scripts/deploy.py moves /produkt/<x>… into shard Workers (routes per first letter).
State (stable slugs, price history, gone products, content hashes) lives in data/state/state.json.gz.
"""
import base64
import hashlib
import json
import os
import re
import shutil
import statistics
import sys
import time
from collections import Counter, defaultdict
from urllib.parse import quote
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog as C  # noqa: E402
import render as R  # noqa: E402
import taxonomy as X  # noqa: E402
import landings as LD  # noqa: E402
import texts as TX  # noqa: E402

APP = Path(__file__).resolve().parent.parent
DIST = APP / "dist"
BASE = os.environ.get("VIAN_BASE", "https://vian.cz")
ENV = os.environ.get("VIAN_ENV", "staging")
GA4 = os.environ.get("GA4_ID", "")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")
MAX_PRODUCTS = int(os.environ.get("VIAN_MAX_PRODUCTS", "0"))
MAX_PAGES = 30
JSON_ITEMS = 3000
E = R.E
TODAY = date.today()
TODAY_CZ = f"{TODAY.day}. {TODAY.month}. {TODAY.year}"
DAY = TODAY.toordinal()
SUFFIX = R.SUFFIX
HOME = ("Vian", "/")


def log(m):
    print(m, file=sys.stderr, flush=True)


INLINE_SCRIPT = re.compile(rb'<script(?: type="speculationrules")?>(.*?)</script>', re.S)


class Out:
    def __init__(self, state):
        self.hashes = state.setdefault("hash", {})
        self.lastmod = state.setdefault("lastmod", {})
        self.changed, self.files, self.sitemap = [], 0, defaultdict(list)
        self.seen = set()
        self.script_hashes = set()      # CSP: inline scripts are allowed by hash, never 'unsafe-inline'

    def write(self, rel, content):
        p = DIST / rel.lstrip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode() if isinstance(content, str) else content
        p.write_bytes(data)
        self.files += 1
        if rel.endswith(".html") and b"<script" in data:
            for m in INLINE_SCRIPT.finditer(data):
                self.script_hashes.add(base64.b64encode(hashlib.sha256(m.group(1)).digest()).decode())
        return data

    def page(self, path, html, group=None, index=True):
        if path in self.seen:
            raise SystemExit(f"duplicate page {path}")
        self.seen.add(path)
        data = self.write(path + "index.html", html)
        h = hashlib.md5(re.sub("Poslední aktualizace [^<]+".encode(), b"", data)).hexdigest()[:12]
        if self.hashes.get(path) != h:
            self.hashes[path] = h
            self.lastmod[path] = TODAY.isoformat()
            if index:
                self.changed.append(path)
        if group and index:
            self.sitemap[group].append(path)


CAT_CAP = int(os.environ.get("VIAN_CAT_CAP", "1500"))   # Kenny 12. 11. 2026: enough to choose from, not everything
MIN_CAT = 8                                              # a category is public (nav, tiles, sitemap) from this many products


def quality(p):
    """How useful a product is to a shopper comparing prices: more shops first, then a photo, a brand, a known width,
    a real discount, variants and a description."""
    return (100 * (len(p["offers"]) - 1) + (20 if p["img"] else 0) + (10 if p["brand"] else 0) + (10 if p.get("wmin") else 0)
            + (5 if R.Site.discount(p) >= 10 else 0) + 2 * min(len(p.get("variants") or []), 5) + (5 if len(p.get("desc") or "") >= 120 else 0))


def cap_categories(products, cap):
    """At most `cap` products per category. Products in 2+ shops always stay; the rest is taken round-robin over the
    shops (each shop's best first), so one big shop cannot fill a category on its own. Deterministic (ties by id), so
    the same feed gives the same selection every night and pages do not flicker."""
    if not cap:
        return products, {}
    by_cat = defaultdict(list)
    for p in products:
        by_cat[p["cat"]].append(p)
    keep, capped = [], {}
    for k, ps in by_cat.items():
        if len(ps) <= cap:
            keep += ps
            continue
        ps = sorted(ps, key=lambda p: (-quality(p), p["id"]))
        multi = [p for p in ps if len(p["offers"]) > 1][:cap]
        queues = defaultdict(list)
        for p in ps:
            if len(p["offers"]) == 1:
                queues[p["offers"][0]["shop"]].append(p)
        order = sorted(queues, key=lambda sid: (-quality(queues[sid][0]), sid))
        picked, i = list(multi), 0
        while len(picked) < cap and any(queues.values()):
            for sid in order:
                if queues[sid] and len(picked) < cap:
                    picked.append(queues[sid].pop(0))
        keep += picked
        capped[k] = len(ps) - len(picked)
    return keep, capped


def pop_key(p):
    return (-len(p["offers"]), -(1 if p["img"] else 0), -(1 if R.Site.discount(p) >= 10 else 0), -len(p.get("variants") or []), p["price"])


def facets(items, extra_cats=None, label="Upřesnit"):
    cnt = lambda key: [(k, n) for k, n in Counter(x for p in items for x in p[key]).most_common() if n >= 2]
    bc = Counter(p["brand"] for p in items if p["brand"])
    brands = [(i, b, n) for i, (b, n) in enumerate(bc.most_common(60))]
    sc = Counter(o["shop"] for p in items for o in p["offers"])
    widths = sum(1 for p in items if p["wmin"])
    has = lambda key: sum(1 for p in items if (p.get("dims") or {}).get(key))
    enough = lambda k: k >= max(6, len(items) * 0.15)
    sizes = [(z, n) for z, n in Counter(z for p in items for z in p.get("sizes") or []).most_common(14) if n >= 2]
    seats = sorted(((v, n) for v, n in Counter(p.get("seats") for p in items if p.get("seats")).items() if n >= 2))
    f = {"brand": brands if len(brands) > 1 else [], "shop": sc.most_common(), "colors": cnt("colors"), "mats": cnt("mats")[:14],
         "styles": cnt("styles"), "feats": cnt("feats"), "width": widths >= max(6, len(items) * 0.3),
         "height": enough(has("h")), "depth": enough(has("d")), "sizes": sizes if len(sizes) > 1 else [],
         "shape": cnt("shape"), "seats": seats if len(seats) > 1 else []}
    if extra_cats:
        f["cats"], f["cats_label"] = extra_cats, label
    return f


def write_json(out, S, key, items):
    items = items[:JSON_ITEMS]
    bc = [b for b, _ in Counter(p["brand"] for p in items if p["brand"]).most_common(60)]
    bidx = {b: i for i, b in enumerate(bc)}
    shops = {o["shop"] for p in items for o in p["offers"][:1]}
    out.write(f"data/l/{key}.json", json.dumps({"b": bc, "s": {sid: S.shop(sid)["name"] for sid in sorted(shops)}, "i": [S.item_json(p, bidx) for p in items]},
                                               ensure_ascii=False, separators=(",", ":")))
    return f"/data/l/{key}.json"


def paged(out, S, path, items, render, group="listings", index=True, per=None):
    pages = max(1, min(-(-len(items) // (per or R.PER_PAGE)), MAX_PAGES))
    for k in range(1, pages + 1):
        S.pg = (path, k, pages)
        S.pg_noindex = k == 1 and not index          # thin listing: noindex AND out of the sitemap (they must agree)
        out.page(path if k == 1 else f"{path}strana-{k}/", render(), group if k == 1 else None, index=index if k == 1 else False)
    S.pg = None
    S.pg_noindex = False


def price_stats(items):
    ps = sorted(p["price"] for p in items)
    if not ps:
        return 0, 0, 0
    return ps[0], int(statistics.median(ps)), ps[-1]


def cat_name(k):
    return X.TREE[k][0]


def crumbs_for(k):
    out = [HOME]
    parent = X.TREE[k][1]
    if parent:
        out.append((cat_name(parent), f"/{parent}/"))
    out.append((cat_name(k), f"/{k}/"))
    return out


# ======================================================================= main

GO_JS = r"""(function(){var b=document.body.dataset,q=new URLSearchParams(location.search),u=q.get("u")||"",g=q.get("g")||"",to="",d=[];
try{d=JSON.parse(b.d)}catch(e){}
function ok(x){try{var h=new URL(x).hostname;return d.some(function(n){return h===n||h.slice(-n.length-1)==="."+n})}catch(e){return false}}
if(g){if(ok(g))to=g}else if(u){var t=/^https?:\/\//.test(u)?u:b.h+u;if(ok(t))to=b.p+(b.m==="e"?encodeURIComponent(t):t)+b.s}
var a=document.getElementById("go");if(to){a.href=to;location.replace(to)}})();
"""


def local_go(products):
    """Shop links as /go/<shop>/?u=/product-path instead of the raw affiliate deeplink (Kenny 12. 11. 2026: the network
    links are long and ugly). Each shop has one template, prefix + product URL (+ suffix), read off its own links;
    /go/<shop>/ is a tiny static page whose script rebuilds the deeplink and redirects (no Worker code, 0 $). An offer
    whose link does not follow the shop's template keeps its exact link as ?g=. The page redirects only to hosts that
    the shop's own links use, so /go/ is no open redirect. Returns {shop: template} for the pages."""
    offers = [o for p in products for o in p["offers"]] + [o for p in products for v in p.get("variants") or [] for o in v.get("offers") or []]

    def split(o):
        go, url = o.get("go") or "", o.get("url") or ""
        if not go.startswith("http") or not url.startswith("http"):
            return None
        for mode, needle in (("e", quote(url, safe="")), ("r", url)):
            i = go.find(needle)
            if i >= 0:
                suf = go[i + len(needle):]
                if re.fullmatch(r"&cjsku=[^&]*", suf):      # CJ's optional SKU (reporting only): one template for the shop
                    suf = ""
                # CJ rotates five equivalent click hosts; one of them serves every shop's links
                return re.sub(r"^https://www\.(kqzyfj|tkqlhce|jdoqocy|dpbolvw|anrdoezrs)\.(com|net)/", "https://www.anrdoezrs.net/", go[:i]), suf, mode
        return None
    keys, hosts, doms = defaultdict(Counter), defaultdict(Counter), defaultdict(set)
    for o in offers:
        k = split(o)
        if k:
            keys[o["shop"]][k] += 1
        if o.get("url", "").startswith("http"):
            hosts[o["shop"]][re.match(r"https?://[^/?#]+", o["url"]).group(0)] += 1
        for u in (o.get("go"), o.get("url")):
            m = re.match(r"https?://([^/?#:]+)", u or "")
            if m:
                doms[o["shop"]].add(m.group(1).lower())
    tpl = {}
    for sid in set(keys) | set(hosts) | set(doms):
        k = keys[sid].most_common(1)[0][0] if keys[sid] else ("", "", "r")
        tpl[sid] = {"p": k[0], "s": k[1], "m": k[2], "h": hosts[sid].most_common(1)[0][0] if hosts[sid] else "", "d": sorted(doms[sid])}
    for o in offers:
        t, sid = tpl.get(o["shop"]), o["shop"]
        k = split(o)
        if t and k == (t["p"], t["s"], t["m"]):
            u = o["url"][len(t["h"]):] if t["h"] and o["url"].startswith(t["h"] + "/") else o["url"]
            o["go"] = f"/go/{sid}/?u=" + quote(u, safe="/-_.~")
        elif o.get("go", "").startswith("http"):
            o["go"] = f"/go/{sid}/?g=" + quote(o["go"], safe="")
    return tpl


def go_page(sid, t, name, js_name):
    dom = t["d"]
    home = t["h"] or (f"https://{dom[0]}" if dom else "/")
    return ('<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>Přesměrování do obchodu ' + E(name) + '</title>'
            '<style>body{font:16px/1.5 system-ui,sans-serif;margin:0;display:grid;place-items:center;min-height:90vh;background:#f4efe6;color:#1e2420}'
            'a{color:#2f5d4c;font-weight:700}</style></head>'
            f'<body data-p="{E(t["p"])}" data-s="{E(t["s"])}" data-m="{t["m"]}" data-h="{E(t["h"])}" data-d="{E(json.dumps(dom))}">'
            f'<p>Přesměrováváme vás do obchodu <b>{E(name)}</b>… <a id="go" href="{E(home)}" rel="sponsored nofollow">Pokračovat</a></p>'
            f'<script src="/assets/{js_name}"></script></body></html>')


def main():
    import faulthandler
    faulthandler.dump_traceback_later(int(os.environ.get("VIAN_BUILD_WATCHDOG", "8100")), exit=True)
    t0 = time.time()
    shops = [s for s in json.load(open(APP / "data/shops.json"))["shops"] if s.get("enabled", True)]
    rank = {s["id"]: i for i, s in enumerate(shops)}
    state = C.load_state()
    log("full run: range from fresh feeds" if C.full_mode() else "price run: range frozen at the last weekly run, only prices refreshed")
    offers, dropped = C.load_offers(shops)
    if not offers:
        sys.exit("no offers — refusing to build an empty site")
    log(f"{len(offers)} offers; dropped (not furniture / too cheap for the category): {dict(dropped)}")
    products = C.cluster(offers, rank)
    bad = C.sanity(products)
    products = [p for p in products if p["offers"]]
    products, capped = cap_categories(products, CAT_CAP)
    log(f"category cap {CAT_CAP}: {sum(capped.values())} products left out in {len(capped)} categories")
    new_slugs = C.assign_slugs(products, state)
    C.price_history(products, state)
    present = sorted({o["shop"] for p in products for o in p["offers"]})
    multi = sum(1 for p in products if len(p["offers"]) > 1)
    log(f"{len(products)} products ({multi} in 2+ shops, {sum(1 for p in products if p['variants'])} with variants), {bad} price errors dropped, {new_slugs} new slugs")

    products.sort(key=pop_key)
    for i, p in enumerate(products):
        p["nkey"] = X.slugify(p["name"])
        p["shape"] = X.shapes_of(p["name"] + " " + p.get("dry", ""), p["cat"])
        p["seats"] = X.seats_of(p["name"] + " " + p.get("dry", ""), p["cat"])
        p["page"] = not MAX_PRODUCTS or i < MAX_PRODUCTS
        p["index"] = len(p["offers"]) > 1 or len(p["desc"]) >= 120 or bool(p["variants"])
    name_count = Counter(p["nkey"] for p in products)
    for p in products:
        p["dup"] = name_count[p["nkey"]] > 1
    gone = C.gone_products(products, state, state.get("snap", {}))
    products = [p for p in products if p["page"]]      # staging cap: listings must not link pages that are not built
    go_tpl = local_go(products)

    shop_meta = {s["id"]: {"name": s["name"], "color": s.get("color", "#888"), "domain": s["domain"],
                           **({"logo": s["logo"], "lw": s["lw"], "lh": s["lh"]} if s.get("logo") else {})} for s in shops}
    stats = {"products": len(products), "shops": len(present), "offers": sum(len(p["offers"]) for p in products), "updated": TODAY_CZ}

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    out = Out(state)
    for f in (APP / "static").rglob("*"):
        if f.is_file():
            rel = f.relative_to(APP / "static").as_posix()
            if rel not in ("assets/site.css", "assets/app.js"):
                out.write(rel, f.read_bytes())
    css = (APP / "static/assets/site.css").read_bytes()
    js = (APP / "static/assets/app.js").read_bytes()
    css_name = f"site.{hashlib.md5(css).hexdigest()[:8]}.css"
    js_name = f"app.{hashlib.md5(js).hexdigest()[:8]}.js"
    out.write("assets/" + css_name, css)
    out.write("assets/" + js_name, js)
    S = R.Site(BASE, ENV, GA4, css_name, js_name, shop_meta, stats)
    go_js = f"go.{hashlib.md5(GO_JS.encode()).hexdigest()[:8]}.js"
    out.write("assets/" + go_js, GO_JS)
    for sid, t in go_tpl.items():
        out.write(f"go/{sid}/index.html", go_page(sid, t, shop_meta.get(sid, {}).get("name", sid), go_js))

    # ---------------- groupings
    by_cat, by_room, by_brand = defaultdict(list), defaultdict(list), defaultdict(list)
    for p in products:
        by_cat[p["cat"]].append(p)
        by_room[X.TREE[p["cat"]][1]].append(p)
        if p["brand"]:
            by_brand[X.slugify(p["brand"])].append(p)
    S.cat_ok = {k for k in by_cat if len(by_cat[k]) >= MIN_CAT}
    S.nav_ok = {X.CATS[k][1] for k in S.cat_ok}
    brand_name = {b: Counter(p["brand"] for p in ps).most_common(1)[0][0] for b, ps in by_brand.items()}
    brand_pages = {b: ps for b, ps in by_brand.items() if len(ps) >= 6 and b and b not in X.TREE}
    S.ctx = {"by_cat": by_cat, "brands": brand_pages, "brand_name": brand_name}

    reserved = ({f"/{k}/" for k in X.TREE} | {f"/znacky/{b}/" for b in brand_pages}
                | {f"/obchody/{s['id']}/" for s in shops}
                | {"/", "/kategorie/", "/znacky/", "/slevy/", "/obchody/", "/jak-srovnavame/", "/hledat/", "/poradna/", "/kontakt/", "/ochrana-osobnich-udaju/"})
    landings, ldropped = LD.plan(products, reserved)
    S.landings = {L["path"]: L for L in landings}
    S.kids = LD.kids_map(landings)
    S.footer_links = [(L["path"], L["h1"]) for L in landings if L["slug"] in ("skandinavsky-nabytek", "nabytek-z-masivu")]
    guides = LD.load_guides()
    S.guides = {f"/poradna/{g['slug']}/": g for g in guides}
    S.has_guides = bool(guides)
    S.guide_links = defaultdict(list)
    for g in guides:
        for rel in g.get("related", []):
            S.guide_links[rel].append((f"/poradna/{g['slug']}/", g["h1"], 0))
    (APP / "data/state").mkdir(parents=True, exist_ok=True)
    (APP / "data/state/landings.tsv").write_text("\n".join(f"{L['path']}\t{L['n']}\t{'index' if L['index'] else 'noindex'}\t{L['group']}\t{L['lo']}" for L in landings))
    log(f"landings: {len(landings)} pages ({sum(1 for L in landings if L['index'])} indexable), dropped {ldropped}")

    # ---------------- product pages
    for p in products:
        if p["page"]:
            out.page(f"/produkt/{p['slug']}/", product_page(S, p), "products", index=p["index"])
    for pid, g in gone.items():
        path = f"/produkt/{g['slug']}/"
        if path not in out.seen:
            out.page(path, gone_page(S, g), None, index=False)
    log(f"product pages done ({time.time() - t0:.0f}s)")

    # ---------------- rooms and categories
    for room in X.TOP:
        items = sorted(by_room.get(room, []), key=pop_key)
        if not items or room not in S.nav_ok:
            continue
        subs = [(k, by_cat[k]) for k in X.CATS if X.CATS[k][1] == room and k in S.cat_ok]
        j = write_json(out, S, room, items)
        paged(out, S, f"/{room}/", items, lambda: room_page(S, room, items, subs, j), "listings")
    for k in X.CATS:
        ps = sorted(by_cat.get(k, []), key=pop_key)
        if not ps:
            continue
        j = write_json(out, S, k, ps)
        paged(out, S, f"/{k}/", ps, lambda: category_page(S, k, ps, j), "listings", index=k in S.cat_ok)

    # ---------------- landings (facets, hubs, hand-written)
    for L in landings:
        ps = sorted(L["items"], key=pop_key)
        j = write_json(out, S, "x-" + L["slug"].replace("/", "-"), ps)
        paged(out, S, L["path"], ps, lambda: landing_page(S, L, ps, j), "landings", index=L["index"])

    # ---------------- brands, sale
    for b, ps in brand_pages.items():
        ps = sorted(ps, key=pop_key)
        j = write_json(out, S, f"z-{b}", ps)
        paged(out, S, f"/znacky/{b}/", ps, lambda: brand_page(S, b, ps, j), "listings", index=len(ps) >= 12)
    out.page("/znacky/", brands_index(S, brand_pages, brand_name), "pages")
    sale = sorted([p for p in products if R.Site.discount(p) >= 10], key=lambda p: -R.Site.discount(p))
    if sale:
        j = write_json(out, S, "slevy", sale)
        paged(out, S, "/slevy/", sale, lambda: sale_page(S, sale, j), "pages")

    # ---------------- guides
    for path, g in S.guides.items():
        out.page(path, guide_page(S, g, LD.guide_picks(products, g)), "guides")
    if S.guides:
        paged(out, S, "/poradna/", list(S.guides.items()), lambda: guides_index(S, S.guides), "pages", per=BLOG_PER_PAGE)

    # ---------------- static pages, search, home, 404
    out.page("/kategorie/", categories_index(S, by_room, by_cat), "pages")
    by_shop = defaultdict(list)
    for p in products:
        for sid in {o["shop"] for o in p["offers"]}:
            by_shop[sid].append(p)
    S.shop_pages = {sid for sid, ps in by_shop.items() if ps}
    for s in shops:
        ps = sorted(by_shop.get(s["id"], []), key=pop_key)
        if not ps:
            continue
        j = write_json(out, S, f"o-{s['id']}", ps)
        paged(out, S, f"/obchody/{s['id']}/", ps, lambda: shop_page(S, s, ps, j), "listings", index=len(ps) >= 12)
    out.page("/obchody/", shops_page(S, shops, present, products), "pages")
    out.page("/jak-srovnavame/", about_page(S, present), "pages")
    out.page("/kontakt/", contact_page(S), "pages")
    out.page("/ochrana-osobnich-udaju/", privacy_page(S), "pages")
    out.page("/hledat/", search_page(S), None, index=False)
    out.page("/", home_page(S, products, by_room, by_cat, sale), "pages")
    out.write("404.html", S.layout("/404/", "Stránka nenalezena" + SUFFIX, "Tahle stránka neexistuje.",
                                   '<div class="e404"><div><p class="eyebrow">404</p><h1>Tady nic nestojí. Ani v rohu.</h1><p class="lead">Kus mohl zmizet z nabídky obchodů, nebo vedla stará adresa. '
                                   'Zkuste ho vyhledat nahoře, nebo začněte <a class="lnk" href="/">na úvodní stránce</a>.</p>'
                                   '<p><a class="btn" href="/kategorie/">Všechny kategorie</a></p></div><img src="/img/ic/kreslo.webp" alt="" width="192" height="192"></div>', noindex=True))
    write_search(out, products, by_room, by_cat, brand_pages, brand_name, landings)

    # ---------------- sitemaps, robots, headers
    sm = []
    for group, paths in out.sitemap.items():
        for i in range(0, len(paths), 40000):
            name = f"sitemap-{group}-{i // 40000 + 1}.xml"
            body = "".join(f"<url><loc>{BASE}{p}</loc><lastmod>{state['lastmod'].get(p, TODAY.isoformat())}</lastmod></url>" for p in paths[i:i + 40000])
            out.write(name, f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
            sm.append(name)
    out.write("sitemap_index.xml", '<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              + "".join(f"<sitemap><loc>{BASE}/{n}</loc><lastmod>{TODAY.isoformat()}</lastmod></sitemap>" for n in sm) + "</sitemapindex>")
    if ENV == "production":
        out.write("robots.txt", f"User-agent: *\nDisallow: /data/\nDisallow: /hledat/\nDisallow: /go/\n\nSitemap: {BASE}/sitemap_index.xml\n")
        out.write("llms.txt", llms_txt(stats, by_room))
    else:
        out.write("robots.txt", "User-agent: *\nDisallow: /\n")
    out.write(".well-known/security.txt", f"Contact: mailto:{R.OPERATOR['email']}\nExpires: {TODAY.year + 1}-12-31T00:00:00.000Z\nPreferred-Languages: cs, en\nCanonical: {BASE}/.well-known/security.txt\n")
    noidx = "" if ENV == "production" else "  X-Robots-Tag: noindex\n"
    sec = ("  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
           "  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload\n  X-Frame-Options: DENY\n"
           "  Cross-Origin-Opener-Policy: same-origin\n  Cross-Origin-Resource-Policy: same-site\n  X-Permitted-Cross-Domain-Policies: none\n"
           "  Permissions-Policy: accelerometer=(), autoplay=(), camera=(), display-capture=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), "
           "midi=(), payment=(), usb=(), xr-spatial-tracking=(), interest-cohort=()\n")
    csp = ("  Content-Security-Policy: default-src 'none'; img-src 'self' https: data:; "
           "script-src 'self' 'inline-speculation-rules' https://www.googletagmanager.com " + " ".join(f"'sha256-{h}'" for h in sorted(out.script_hashes)) + "; "
           "connect-src 'self' https://*.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com; style-src 'self' 'unsafe-inline'; "
           "font-src 'self'; manifest-src 'self'; object-src 'none'; frame-src 'none'; worker-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; "
           "upgrade-insecure-requests\n")
    preload = f"  Link: </assets/{css_name}>; rel=preload; as=style, </fonts/fraunces-cs.woff2>; rel=preload; as=font; type=font/woff2; crossorigin, </fonts/onest-cs.woff2>; rel=preload; as=font; type=font/woff2; crossorigin\n"
    html_cache = "  Cache-Control: public, max-age=300, stale-while-revalidate=86400\n"
    out.write("_headers", "/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n"
              "/data/*\n  Cache-Control: public, max-age=3600\n  X-Robots-Tag: noindex\n"
              "/img/*\n  Cache-Control: public, max-age=604800, stale-while-revalidate=2592000\n"
              "/favicon*\n  Cache-Control: public, max-age=604800\n"
              "/*.xml\n  Cache-Control: public, max-age=3600\n"
              "/go/*\n  X-Robots-Tag: noindex, nofollow\n"
              "/\n" + html_cache + preload + "/*/\n" + html_cache + preload +
              "/*\n" + sec + csp + noidx)
    if INDEXNOW_KEY:
        out.write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)

    unlink_missing(out.seen)
    for k in list(out.hashes):
        if k not in out.seen:
            out.hashes.pop(k, None)
            out.lastmod.pop(k, None)
    C.save_state(state)
    (APP / "data/state/changed.txt").write_text("\n".join(out.changed))
    report = {"at": time.strftime("%Y-%m-%d %H:%M"), "env": ENV, "files": out.files, "offers": len(offers), "products": len(products), "multi_shop": multi,
              "with_variants": sum(1 for p in products if p["variants"]), "product_pages": sum(1 for p in products if p["page"]),
              "indexable_products": sum(1 for p in products if p["page"] and p["index"]), "gone_pages": len(gone), "categories": len(by_cat),
              "landings": len(landings), "brands": len(brand_pages), "changed": len(out.changed), "shops": present,
              "per_shop": dict(Counter(o["shop"] for p in products for o in p["offers"])), "per_cat": dict(Counter(p["cat"] for p in products).most_common()),
              "with_width": sum(1 for p in products if p["wmin"]), "dropped": dict(dropped), "categorisation": dict(C.STATS),
              "public_categories": len(S.cat_ok), "departments": len(S.nav_ok), "capped": capped, "shop_pages": len(S.shop_pages)}
    json.dump(report, open(APP / "data/state/build-report.json", "w"), indent=1, ensure_ascii=False)
    log(json.dumps({k: v for k, v in report.items() if k not in ("per_cat",)}, ensure_ascii=False))
    log(f"built {out.files} files in {time.time() - t0:.0f}s")


def unlink_missing(seen):
    """Hand-written texts may link a page that this build does not have (too few products today): keep the words, drop the link."""
    rx = re.compile(r'<a href="(/[^"#?]*)">(.*?)</a>')
    fixed = 0
    for f in DIST.rglob("index.html"):
        if f.parts[len(DIST.parts)] == "produkt":
            continue
        html = f.read_text()
        if 'class="prose"' not in html and 'class="faq"' not in html:
            continue
        fix = lambda part: rx.sub(lambda m: m.group(0) if (m.group(1) in seen or not m.group(1).endswith("/") or m.group(1) == "/") else m.group(2), part.group(0))
        new = re.sub(r'<div class="prose">.*?</div><!--/prose-->|<div class="prose"[^>]*>.*?</div>|<section class="faq">.*?</section>', fix, html, flags=re.S)
        if new != html:
            f.write_text(new)
            fixed += 1
    log(f"texts: removed dead internal links on {fixed} pages")


# ======================================================================= page builders

def offer_rows(S, offers, best_price, label=None):
    rows = []
    n = len(offers)
    for i, o in enumerate(offers):
        m = S.shop(o["shop"])
        was = f'<s>{R.kc(o["was"])}</s>' if o.get("was") and o["was"] > o["price"] else ""
        diff = f'<small>o {R.kc(o["price"] - best_price)} dráž</small>' if o["price"] > best_price else '<small>nejlepší cena</small>' if n > 1 else ""
        rows.append(f'<li class="ticket{" best1" if i == 0 and n > 1 else ""}"><span class="stripe" style="background:{m["color"]}"></span>'
                    f'<span class="sname">{R.shop_logo(m)}<span class="stxt"><b>{E(m["name"])}</b>{diff}</span></span>'
                    f'<span class="tprice">{was}{R.kc(o["price"])}</span><a class="btn{" btn--g" if i else ""}" href="{E(o["go"])}" {S.go_attrs(o["shop"])}>Do obchodu</a></li>')
    return "".join(rows)


def product_page(S, p):
    k = p["cat"]
    n = len(p["offers"])
    var = p.get("variants") or []
    best = p["offers"][0]
    bs = S.shop(best["shop"])
    code = re.sub(r"\D", "", p["ean"])[-4:] or p["slug"][-4:]
    uniq = f" (kód {code})" if p.get("dup") else ""
    core = f"{p['name']} – srovnání cen" if n > 1 else f"{p['name']} – cena a rozměry"
    title = R.shorten(core, 68 - len(SUFFIX) - len(uniq)) + uniq + SUFFIX
    sl = X.size_label(p["dims"])
    desc = (f"{p['name']}: {'od ' + R.kc(p['price']) + ' v ' + str(n) + ' obchodech' if n > 1 else 'cena ' + R.kc(p['price']) + ' v obchodě ' + bs['name']}"
            f"{', rozměry ' + sl if sl else ''}{', ' + str(len(var)) + ' variant' if len(var) > 1 else ''}. Porovnejte nabídky a kupte přímo v e‑shopu.")
    imgs = [p["img"]] + p["imgs"] if p["img"] else p["imgs"]
    imgs = [u for u in imgs if u][:7]
    thumb_srcs = [R.img_url(u, "card") for u in imgs]
    imgs = [R.img_url(u, "main") for u in imgs]
    main_img = E(imgs[0]) if imgs else "/img/ui/placeholder.svg"
    thumbs = "".join(f'<button type="button" data-src="{E(u)}"{" class=on" if i == 0 else ""} aria-label="Obrázek {i + 1}"><img src="{E(thumb_srcs[i])}" alt="" loading="lazy" referrerpolicy="no-referrer" width="64" height="64"></button>'
                     for i, u in enumerate(imgs)) if len(imgs) > 1 else ""
    gal = f'<div class="gal"><div class="gal__main"><img id="gmain" src="{main_img}" alt="{E(p["name"])}" referrerpolicy="no-referrer" width="640" height="640" fetchpriority="high"></div><div class="thumbs">{thumbs}</div></div>'

    meta = []
    if p["brand"] and X.slugify(p["brand"]) in S.ctx["brands"]:
        meta.append(f'<a href="/znacky/{X.slugify(p["brand"])}/">{E(p["brand"])}</a>')
    elif p["brand"]:
        meta.append(f"<span>{E(p['brand'])}</span>")
    meta.append(f'<a href="/{k}/">{E(cat_name(k))}</a>')
    for key, names, slugs in (("styles", X.STYLE_NAME, LD.STYLE_SLUG), ("mats", X.MATERIAL_NAME, LD.MAT_SLUG), ("colors", X.COLOR_NAME, LD.COLOR_SLUG)):
        for v in p[key][:2]:
            path = f"/{k}/{slugs[v]}/"
            meta.append(f'<a href="{path}">{E(names[v])}</a>' if path in S.landings else f"<span>{E(names[v])}</span>")

    low = ""
    if p["since"] <= DAY - 7:
        low = (f'<p class="low">Nejnižší cena, jakou jsme za posledních 30 dní viděli.</p>' if p["price"] <= p["low30"]
               else f'<p>Nejnižší cena za posledních 30 dní u nás: <b>{R.kc(p["low30"])}</b>.</p>')
    else:
        sd = date.fromordinal(p["since"])
        low = f'<p class="muted">Cenu sledujeme od {sd.day}. {sd.month}. {sd.year}.</p>'
    who = f"Nejlevněji v obchodě {E(bs['name'])}" if n > 1 else f"V obchodě {E(bs['name'])}"
    if len(var) > 1:
        who += f" · {len(var)} {R.plural(len(var), 'varianta', 'varianty', 'variant')}"
    bestbox = (f'<div class="best"><div class="best__top">{S.tag(p["price"], "od" if (n > 1 or len(var) > 1) else "", big=True, was=best.get("was") or 0)}<div class="best__who">{who}</div>'
               f'<a class="btn btn--lg btn--cta" href="{E(best["go"])}" {S.go_attrs(best["shop"])}>Do obchodu</a></div>{low}</div>')

    fit = ""
    if p["wmin"]:
        fit = (f'<div class="fitbox" data-w="{p["wmin"]:g}"><label for="fitw">{R.RULER_ICON}<b>Vejde se?</b> Máte místo široké</label>'
               f'<input id="fitw" type="number" min="10" max="900" inputmode="numeric" placeholder="např. {int(p["wmin"] + 20)}"><span>cm</span><output id="fitout" aria-live="polite"></output></div>')
    dimfig = R.dims_svg(p["dims"])

    if len(var) > 1:
        vrows = []
        for v in var[:80]:
            o = v["offers"][0]
            m = S.shop(o["shop"])
            vrows.append(f'<li class="ticket"><span class="stripe" style="background:{m["color"]}"></span><span class="sname"><b>{E(v["label"])}</b><small>{E(m["name"])}'
                         f'{" a další " + str(len(v["offers"]) - 1) if len(v["offers"]) > 1 else ""}</small></span><span class="tprice">{R.kc(v["price"])}</span>'
                         f'<a class="btn btn--g" href="{E(o["go"])}" {S.go_attrs(o["shop"])}>Do obchodu</a></li>')
        more = f'<button class="more" type="button" data-more="vlist">Všech {len(var)} variant</button>' if len(var) > 8 else ""
        offers_html = f'<h2 id="nabidky">Varianty a ceny</h2><ul class="offers clampl" id="vlist">{"".join(vrows)}</ul>{more}'
        if n > 1:
            offers_html += f'<h2>Nejlevněji podle obchodu</h2><ul class="offers">{offer_rows(S, p["offers"], p["price"])}</ul>'
    else:
        offers_html = f'<h2 id="nabidky">{"Ceny v obchodech" if n > 1 else "Kde koupit"}</h2><ul class="offers">{offer_rows(S, p["offers"], p["price"])}</ul>'

    spec = [("Značka", E(p["brand"]) if p["brand"] else "neuvedena"), ("Kategorie", f'<a href="/{k}/">{E(cat_name(k))}</a>')]
    if sl:
        spec.append(("Rozměry", E(sl)))
    if p["sizes"] and len(p["sizes"]) > 1:
        spec.append(("Dostupné rozměry", ", ".join(s.replace("x", " × ") for s in p["sizes"][:12]) + " cm"))
    if p["mats"]:
        spec.append(("Materiál", ", ".join(X.MATERIAL_NAME[m] for m in p["mats"])))
    if p["colors"]:
        spec.append(("Barva", ", ".join(X.COLOR_NAME[c] for c in p["colors"])))
    if p["styles"]:
        spec.append(("Styl", ", ".join(X.STYLE_NAME[s] for s in p["styles"])))
    if p["feats"]:
        spec.append(("Provedení", ", ".join(X.FEATURE_NAME[f] for f in p["feats"])))
    if p["ean"]:
        spec.append(("EAN", p["ean"]))
    spec.append(("Počet obchodů", str(n)))
    spec_html = '<h2>Parametry</h2><table class="spec">' + "".join(f"<tr><th>{a}</th><td>{b}</td></tr>" for a, b in spec) + "</table>"
    desc_html = ""
    if len(p["desc"]) > 40:
        desc_html = f'<h2>Popis</h2><div class="desc clamp" id="desc">{E(p["desc"])}</div><button class="more" type="button" data-more="desc">Celý popis</button><p class="disc">Popis převzatý od obchodu.</p>'
    hist = R.svg_history(p["hist"], DAY)
    hist_html = f"<h2>Vývoj ceny</h2>{hist}<p class=\"disc\">Nejnižší cena napříč obchody, jak jsme ji zaznamenali my.</p>" if hist else ""

    sim = [q for q in S.ctx["by_cat"].get(k, []) if q is not p and q["page"] and q["nkey"] != p["nkey"]][:600]
    st = set(p["styles"]) | set(p["mats"][:1])
    sim = sorted(sim, key=lambda q: (abs(q["price"] - p["price"]) / max(p["price"], 1) - 0.25 * len(st & (set(q["styles"]) | set(q["mats"][:1]))) - 0.1 * len(q["offers"])))[:8]
    sim_html = f'<section class="sec"><div class="sec__h"><h2>Podobné kusy</h2><a href="/{k}/">Celá kategorie →</a></div>{S.grid(sim)}</section>' if sim else ""

    ld = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "image": imgs[:3] or None, "url": S.url(f"/produkt/{p['slug']}/"),
          "description": (p["desc"][:300] or p["name"]), "category": cat_name(k),
          "offers": {"@type": "AggregateOffer", "priceCurrency": "CZK", "lowPrice": p["price"], "highPrice": max(o["price"] for o in p["offers"]),
                     "offerCount": max(n, len(var)), "availability": "https://schema.org/InStock"}}
    if p["brand"]:
        ld["brand"] = {"@type": "Brand", "name": p["brand"]}
    if p["ean"] and len(p["ean"]) == 13:
        ld["gtin13"] = p["ean"]
    if p["colors"]:
        ld["color"] = X.COLOR_NAME[p["colors"][0]]
    if p["mats"]:
        ld["material"] = X.MATERIAL_NAME[p["mats"][0]]
    if p["dims"].get("w") and not p["dims"].get("raw") and not p["dims"].get("size"):
        ld["width"] = {"@type": "QuantitativeValue", "value": p["dims"]["w"], "unitCode": "CMT"}
        if p["dims"].get("h"):
            ld["height"] = {"@type": "QuantitativeValue", "value": p["dims"]["h"], "unitCode": "CMT"}
        if p["dims"].get("d"):
            ld["depth"] = {"@type": "QuantitativeValue", "value": p["dims"]["d"], "unitCode": "CMT"}
    ld = {k2: v for k2, v in ld.items() if v}

    sizes_html = f'<p class="dimline">{R.RULER_ICON}<span>{E(sl)}</span></p>' if sl else ""
    body = (f'<div class="prod">{gal}<div class="prod__info"><h1>{E(p["name"])}</h1><div class="meta">{"".join(meta)}</div>{sizes_html}{bestbox}{fit}{offers_html}</div></div>'
            f'<div class="prod__more"><div>{dimfig}{spec_html}</div><div>{desc_html}{hist_html}</div></div>{sim_html}')
    cr = crumbs_for(k) + [(R.shorten(p["name"], 60), f"/produkt/{p['slug']}/")]
    return S.layout(f"/produkt/{p['slug']}/", title, desc, body, crumbs=cr, jsonld=[ld], preload_img=imgs[0] if imgs else None,
                    og_img=imgs[0] if imgs else None, noindex=not p["index"])


def gone_page(S, g):
    k = g["cat"] if g["cat"] in X.TREE else "sedacky"
    sim = sorted([q for q in S.ctx["by_cat"].get(k, []) if q["page"]], key=lambda q: abs(q["price"] - g["price"]))[:8]
    body = (f'<div class="prod"><div class="gal"><div class="gal__main"><img src="{E(R.img_url(g["img"], "main") or "/img/ui/placeholder.svg")}" alt="{E(g["name"])}" width="640" height="640"></div></div>'
            f'<div class="prod__info"><h1>{E(g["name"])}</h1><div class="gone"><b>Momentálně nedostupné.</b> Žádný ze sledovaných obchodů teď tenhle kus nemá v nabídce. '
            f'Naposledy stál {R.kc(g["price"])}. Podívejte se na podobné níže, nebo se vraťte později.</div>'
            f'<p><a class="btn" href="/{k}/">{E(cat_name(k))}</a></p></div></div>'
            f'<section class="sec"><h2>Podobné kusy skladem</h2>{S.grid(sim)}</section>')
    return S.layout(f"/produkt/{g['slug']}/", f"{g['name']} – momentálně nedostupné" + SUFFIX, f"{g['name']} teď není v nabídce. Podobné kusy a jejich ceny.",
                    body, crumbs=crumbs_for(k) + [(R.shorten(g["name"], 60), f"/produkt/{g['slug']}/")], noindex=True)


def listing_body(S, path, h1, lead, items, jsn, icon, texts_key=None, extra_ld=None, links=None, links_label="Upřesnit", extra=""):
    t = TX.get(texts_key) if texts_key else None
    intro = t["intro"] if t and t.get("intro") else ""
    kids = [k for k in getattr(S, "kids", {}).get(path, []) if k[0] != path]
    cats = list(links or [])
    if kids:
        seen = {u for u, _, _ in cats}
        cats += [k for k in sorted(kids, key=lambda k: -k[2])[:40] if k[0] not in seen]
    gl = S.guide_links.get(path, [])
    if gl:
        extra += '<p class="muted guidel">Z poradny: ' + " · ".join(f'<a class="lnk" href="{u}">{E(t_)}</a>' for u, t_, _ in gl[:3]) + "</p>"
    band = S.band(h1, intro or lead, icon, extra)
    prose, qa = TX.generated(texts_key, items, h1, S)
    if t and t.get("body"):
        prose = t["body"]
    if t and t.get("faq"):
        qa = t["faq"]
    faq_html, faq_ld = S.faq(qa)
    body = band + f'<div class="wrap">{S.listing(items, jsn, facets=facets(items, cats, links_label))}' + \
        (f'<div class="prose">{prose}</div><!--/prose-->' if prose else "") + faq_html + "</div>"
    return body, [faq_ld] + (extra_ld or [])


def room_page(S, room, items, subs, jsn):
    name, h1, blurb = X.ROOMS[room][0], X.ROOMS[room][1], X.ROOMS[room][2]
    lo, med, hi = price_stats(items)
    n = len(items)
    title = f"{h1} – srovnání cen z {S.stats['shops']} obchodů" + SUFFIX
    desc = f"{h1}: {blurb.lower()}. {n} kusů z českých e‑shopů, ceny od {R.kc(lo)}. Porovnejte rozměry a ceny na jednom místě."
    tiles = S.tiles([(k, cat_name(k), len(ps)) for k, ps in sorted(subs, key=lambda x: -len(x[1]))])
    lead = f"{blurb}. {n} {R.plural(n, 'kus', 'kusy', 'kusů')} z {len({o['shop'] for p in items for o in p['offers']})} obchodů, ceny od {R.kc(lo)}."
    body, lds = listing_body(S, f"/{room}/", E(h1), lead, items, jsn, X.ICON[room], texts_key=f"room:{room}", extra=tiles)
    return S.layout(f"/{room}/", title, desc, body, crumbs=[HOME, (name, f"/{room}/")], jsonld=lds, full=True)


def category_page(S, k, items, jsn):
    name, room, h1 = X.CATS[k][0], X.CATS[k][1], X.CATS[k][2]
    lo, med, hi = price_stats(items)
    n = len(items)
    title = f"{h1} – srovnání cen od {R.kc(lo)}" + SUFFIX
    desc = f"{h1}: {n} {R.plural(n, 'kus', 'kusy', 'kusů')} z {len({o['shop'] for p in items for o in p['offers']})} českých e‑shopů, ceny od {R.kc(lo)}. Filtr podle rozměrů, barvy a materiálu."
    sibs = [(c, cat_name(c), len(S.ctx["by_cat"][c])) for c in X.CATS if X.CATS[c][1] == room and c != k and c in S.cat_ok]
    lead = f"{n} {R.plural(n, 'kus', 'kusy', 'kusů')} skladem, ceny od {R.kc(lo)} do {R.kc(hi)}. Polovina stojí méně než {R.kc(med)}."
    body, lds = listing_body(S, f"/{k}/", E(h1), lead, items, jsn, X.ICON[k], texts_key=f"cat:{k}", links=[], links_label="Upřesnit",
                             extra=S.tiles(sibs))
    return S.layout(f"/{k}/", title, desc, body, crumbs=crumbs_for(k), jsonld=lds, full=True)


def landing_page(S, L, items, jsn):
    h1, path = L["h1"], L["path"]
    lo, med, hi = price_stats(items)
    n = len(items)
    shops = len({o["shop"] for p in items for o in p["offers"]})
    title = (L.get("title") or f"{h1} – srovnání cen od {R.kc(lo)}") + (SUFFIX if "Vian" not in (L.get("title") or "") else "")
    if len(title) > 72 and not L.get("title"):
        title = f"{h1} – ceny od {R.kc(lo)}" + SUFFIX
    desc = L.get("desc") or f"{h1}: {n} {R.plural(n, 'kus', 'kusy', 'kusů')} z {shops} českých e‑shopů, ceny od {R.kc(lo)}. Porovnejte rozměry, varianty a ceny."
    lead = L.get("lead") or f"{n} {R.plural(n, 'kus', 'kusy', 'kusů')} z {shops} {R.plural(shops, 'obchodu', 'obchodů', 'obchodů')}, ceny od {R.kc(lo)} do {R.kc(hi)}."
    par = L["parent"]
    sibs = [x for x in S.kids.get(par, []) if x[0] != path] if par else []
    chips = sorted(sibs, key=lambda x: -x[2])[:40]
    icon = X.ICON.get(L.get("cat") or "", "kreslo")
    body, lds = listing_body(S, path, E(h1), lead, items, jsn, icon, texts_key="landing:" + L["slug"], links=chips, links_label="Podobné výběry")
    cr = [HOME]
    if L.get("cat"):
        room = X.TREE[L["cat"]][1]
        if room:
            cr.append((cat_name(room), f"/{room}/"))
        cr.append((cat_name(L["cat"]), f"/{L['cat']}/"))
        if par and par != f"/{L['cat']}/" and par in S.landings:
            cr.append((S.landings[par]["h1"], par))
    cr.append((h1, path))
    return S.layout(path, title, desc, body, crumbs=cr, jsonld=lds, full=True)


def brand_page(S, b, items, jsn):
    name = S.ctx["brand_name"][b]
    lo, med, hi = price_stats(items)
    cats = Counter(p["cat"] for p in items).most_common(8)
    title = f"{name} – nábytek a doplňky, srovnání cen" + SUFFIX
    desc = f"{name}: {len(items)} {R.plural(len(items), 'kus', 'kusy', 'kusů')} v českých e‑shopech, ceny od {R.kc(lo)}. Porovnejte ceny a rozměry."
    lead = f"{len(items)} {R.plural(len(items), 'kus', 'kusy', 'kusů')} značky {E(name)}, nejčastěji " + ", ".join(cat_name(c).lower() for c, _ in cats[:3]) + "."
    links = [(f"/{c}/", cat_name(c), n) for c, n in cats]
    body, lds = listing_body(S, f"/znacky/{b}/", E(name), lead, items, jsn, None, texts_key=f"brand:{b}", links=links, links_label="Kategorie")
    return S.layout(f"/znacky/{b}/", title, desc, body, crumbs=[HOME, ("Značky", "/znacky/"), (name, f"/znacky/{b}/")], jsonld=lds, full=True)


def sale_page(S, items, jsn):
    lo, med, hi = price_stats(items)
    cats = Counter(p["cat"] for p in items).most_common(16)
    links = [(f"/{c}/", cat_name(c), n) for c, n in cats]
    lead = f"{len(items)} {R.plural(len(items), 'kus', 'kusy', 'kusů')}, které mají v obchodě teď nižší cenu než původní. Řazeno od největší slevy."
    body, lds = listing_body(S, "/slevy/", "Slevy na nábytek a bytové doplňky", lead, items, jsn, "kreslo", texts_key="slevy", links=links, links_label="Kategorie")
    body = body.replace('data-order="pop"', 'data-order="sale"').replace('<option value="sale">', '<option value="sale" selected>')
    return S.layout("/slevy/", "Slevy na nábytek – aktuální akce e‑shopů" + SUFFIX, f"Nábytek a bytové doplňky ve slevě: {len(items)} kusů z českých e‑shopů. Seřazeno od největší slevy, ceny denně aktualizované.",
                    body, crumbs=[HOME, ("Slevy", "/slevy/")], jsonld=lds, full=True)


BLOG_PER_PAGE = 12
BLOG_PHOTOS = json.loads((APP / "content/guides/photos.json").read_text()) if (APP / "content/guides/photos.json").exists() else {}


def blog_photo(g, size):
    ph = BLOG_PHOTOS.get(g["slug"])
    return (ph, f"/img/blog/{g['slug']}-{size}.jpg") if ph and (APP / f"static/img/blog/{g['slug']}-{size}.jpg").exists() else (None, None)


def reading_min(g):
    words = len(re.sub(r"<[^>]+>", " ", g["intro"] + " " + g["body"]).split())
    return max(2, round(words / 190))


def guide_page(S, g, picks):
    path = f"/poradna/{g['slug']}/"
    title = (g.get("title") or g["h1"]) + SUFFIX
    desc = g.get("description") or (re.sub(r"<[^>]+>", "", g["intro"]) or g["h1"])[:155]
    faq_html, faq_ld = S.faq(g.get("faq", []))
    rel = [(u, S.landings[u]["h1"]) for u in g.get("related", []) if u in S.landings]
    rel += [(u, cat_name(u.strip("/"))) for u in g.get("related", []) if u.strip("/") in X.TREE]
    rel_html = ("<h2>Související stránky</h2>" + S.chips([(u, t, 0) for u, t in rel[:8]])) if rel else ""
    picks_html = f'<section class="sec"><div class="sec__h"><h2>Výběr z nabídky</h2></div>{S.grid(picks)}</section>' if len(picks) >= 4 else ""
    ph, img = blog_photo(g, "1200")
    fig = ""
    if ph:
        fig = (f'<figure class="post__img"><img src="{img}" srcset="{blog_photo(g, "640")[1]} 640w, {img} 1200w" sizes="(max-width:800px) 92vw, 760px" width="1200" height="750" alt="{E(ph["alt"])}" fetchpriority="high">'
               f'<figcaption>Foto: <a href="{E(ph["page"])}" rel="noopener" target="_blank">{E(ph["by"])} / Pexels</a></figcaption></figure>')
    body = (f'<article class="post"><header class="post__h"><p class="post__meta"><a href="/poradna/">Poradna</a> · {reading_min(g)} min čtení</p><h1>{E(g["h1"])}</h1>'
            f'<p class="lead">{g["intro"]}</p></header>{fig}<div class="prose">{g["body"]}</div>'
            f'{picks_html}<div class="post__rel">{rel_html}</div>{faq_html}</article>')
    art = {"@context": "https://schema.org", "@type": "Article", "headline": g["h1"], "description": desc, "mainEntityOfPage": S.url(path),
           "datePublished": g.get("date", TODAY.isoformat()), "dateModified": TODAY.isoformat(),
           "author": {"@type": "Organization", "name": "Vian", "url": BASE + "/"}, "publisher": {"@type": "Organization", "name": "Vian", "url": BASE + "/", "logo": {"@type": "ImageObject", "url": BASE + "/favicon-512.png"}}}
    if ph:
        art["image"] = [S.url(img)]
    return S.layout(path, title, desc, body, crumbs=[HOME, ("Poradna", "/poradna/"), (g["h1"], path)], jsonld=[art, faq_ld], preload_img=img if ph else None, og_img=S.url(img) if ph else None)


def guides_index(S, guides):
    path, cur, pages = S.pg or ("/poradna/", 1, 1)
    chunk = list(guides.items())[(cur - 1) * BLOG_PER_PAGE:cur * BLOG_PER_PAGE]
    cards = []
    for i, (p, g) in enumerate(chunk):
        ph, img = blog_photo(g, "640")
        pic = f'<img src="{img}" width="640" height="400" alt="{E(ph["alt"])}"{"" if i < 3 else " loading=lazy"}>' if ph else ""
        ex = re.sub(r"<[^>]+>", "", g["intro"])
        ex = ex if len(ex) <= 140 else ex[:140].rsplit(" ", 1)[0] + "…"
        cards.append(f'<li class="bc"><a class="bc__img" href="{p}" tabindex="-1" aria-hidden="true">{pic}</a><div class="bc__b"><p class="post__meta">{reading_min(g)} min čtení</p>'
                     f'<h2><a href="{p}">{E(g["h1"])}</a></h2><p>{E(ex)}</p></div></li>')
    body = ('<div class="blogh"><h1>Poradna</h1><p class="lead">Jak změřit místo, vybrat rozměr postele, tvrdost matrace nebo velikost koberce. Praktické rady bez reklamních řečí.</p></div>'
            f'<ul class="blog">{"".join(cards)}</ul>{R.pager_html(path, cur, pages)}')
    return S.layout("/poradna/", "Poradna – jak vybrat nábytek, rozměry a materiály" + SUFFIX, "Rady k výběru nábytku: rozměry postelí a matrací, jak velkou sedačku do obýváku, jaký koberec, materiály a údržba.", body,
                    crumbs=[HOME, ("Poradna", "/poradna/")])


def brands_index(S, pages, names):
    groups = defaultdict(list)
    for b, ps in sorted(pages.items(), key=lambda x: names[x[0]].lower()):
        ch = X.slugify(names[b])[:1].upper() or "#"
        groups[ch if ch.isalpha() else "#"].append((b, ps))
    top = sorted(pages.items(), key=lambda x: -len(x[1]))[:24]
    body = '<h1>Značky nábytku</h1><p class="lead">Značky, které teď mají zboží ve sledovaných obchodech.</p>' + \
        S.chips([(f"/znacky/{b}/", names[b], len(ps)) for b, ps in top]) + "".join(
            f'<p class="letter">{ch}</p><div class="cols3">' + "".join(f'<a href="/znacky/{b}/">{E(names[b])} <small>{len(ps)}</small></a>' for b, ps in lst) + "</div>"
            for ch, lst in sorted(groups.items()))
    return S.layout("/znacky/", "Značky nábytku A–Z" + SUFFIX, f"{len(pages)} značek nábytku a bytových doplňků se srovnáním cen.",
                    body, crumbs=[HOME, ("Značky", "/znacky/")])


def categories_index(S, by_room, by_cat):
    parts = []
    for room in X.TOP:
        if room not in S.nav_ok:
            continue
        subs = [(k, cat_name(k), len(by_cat[k])) for k in X.CATS if X.CATS[k][1] == room and k in S.cat_ok]
        parts.append(f'<section class="catgrp"><h2><a href="/{room}/"><img src="/img/ic/{X.ICON[room]}.webp" alt="" width="56" height="56" loading="lazy">{E(X.ROOMS[room][0])}</a></h2>{S.tiles(subs)}</section>')
    hubs = sorted([L for L in S.landings.values() if L["parent"] is None], key=lambda L: -L["n"])
    extra = ('<h2 style="margin-top:34px">Podle stylu a materiálu</h2>' + S.chips([(L["path"], L["h1"], L["n"]) for L in hubs])) if hubs else ""
    n_cats = len(S.cat_ok)
    body = f'<h1>Všechny kategorie</h1><p class="lead">{n_cats} kategorií nábytku a bytových doplňků v {len(parts)} odděleních.</p><div class="catgrid">{"".join(parts)}</div>{extra}'
    return S.layout("/kategorie/", "Kategorie nábytku a bytových doplňků" + SUFFIX, f"Přehled {n_cats} kategorií: nábytek podle místností, svítidla, koberce, textil, dekorace, kuchyně, koupelna, zahrada a podlahy.",
                    body, crumbs=[HOME, ("Kategorie", "/kategorie/")])


def shop_page(S, s, items, jsn):
    """One shop: what it sells here (its categories), its products sorted like everywhere else, and where it is the
    cheapest of several shops."""
    sid, name = s["id"], s["name"]
    lo, med, hi = price_stats(items)
    n = len(items)
    cats = Counter(p["cat"] for p in items)
    tiles = S.tiles([(k, cat_name(k), c) for k, c in cats.most_common(14) if k in S.cat_ok])
    multi = [p for p in items if len(p["offers"]) > 1]
    best = sum(1 for p in multi if p["offers"][0]["shop"] == sid)
    cmp_txt = (f" {len(multi)} {R.plural(len(multi), 'kus nabízí', 'kusy nabízejí', 'kusů nabízí')} i jiné obchody, u {best} z nich je {E(name)} nejlevnější."
               if multi else "")
    lead = (f"{n} {R.plural(n, 'kus', 'kusy', 'kusů')} z e‑shopu {E(s['domain'])} v {len(cats)} {R.plural(len(cats), 'kategorii', 'kategoriích', 'kategoriích')}, "
            f"ceny od {R.kc(lo)}.{cmp_txt}")
    title = f"{name} – nabídka a srovnání cen" + SUFFIX
    desc = f"{name}: {n} {R.plural(n, 'kus', 'kusy', 'kusů')} nábytku a doplňků, ceny od {R.kc(lo)}. Porovnejte s dalšími českými e‑shopy na jednom místě."
    head = f'<div class="shophead" style="--c:{s.get("color", "#888")}">{R.shop_logo(S.shop(sid), big=True)}</div>' if s.get("logo") else ""
    body, lds = listing_body(S, f"/obchody/{sid}/", E(name), lead, items, jsn, None, texts_key=f"shop:{sid}", extra=head + tiles)
    return S.layout(f"/obchody/{sid}/", title, desc, body, crumbs=[HOME, ("Obchody", "/obchody/"), (name, f"/obchody/{sid}/")], jsonld=lds, full=True)


def shops_page(S, shops, present, products):
    cnt = Counter(o["shop"] for p in products for o in p["offers"])
    dept = {}
    for p in products:
        for o in p["offers"]:
            dept.setdefault(o["shop"], Counter())[X.TREE[p["cat"]][1]] += 1
    def li(s):
        top = ", ".join(X.ROOMS[r][0].lower() for r, _ in dept.get(s["id"], Counter()).most_common(3))
        return (f'<li style="--c:{s.get("color", "#888")}" data-name="{E(X.fold(s["name"]))}">{R.shop_logo(S.shop(s["id"]), big=True)}'
                f'<h3><a href="/obchody/{s["id"]}/">{E(s["name"])}</a></h3><p class="muted">{cnt.get(s["id"], 0)} kusů · {E(top)}</p></li>')
    lis = "".join(li(s) for s in sorted(shops, key=lambda s: X.fold(s["name"])) if s["id"] in present)
    body = (f'<h1>Obchody, které srovnáváme</h1><p class="lead">{len(present)} českých e‑shopů s nábytkem a vybavením domácnosti. Ceny a dostupnost bereme z jejich produktových feedů. Ceny obnovujeme každý den, nabídku produktů jednou týdně.</p>'
            '<p><label class="sr" for="shopq">Najít obchod</label><input id="shopq" class="shopq" type="search" placeholder="Najít obchod…" autocomplete="off"></p>'
            f'<ul class="shoplist" id="shoplist">{lis}</ul><p class="muted" style="margin-top:18px;font-size:.88rem">Loga a názvy obchodů patří jejich majitelům a uvádíme je jen k označení obchodu, jehož nabídku porovnáváme. Nejde o oficiální doporučení ani partnerství. Odstranění loga na žádost: <a class="lnk" href="/kontakt/">kontakt</a>.</p>')
    return S.layout("/obchody/", "Obchody s nábytkem, které srovnáváme" + SUFFIX, "Seznam českých e‑shopů s nábytkem a bytovými doplňky, jejichž ceny Vian srovnává.", body,
                    crumbs=[HOME, ("Obchody", "/obchody/")])


def about_page(S, present):
    body = (f'<div class="prose" style="margin-top:0"><h1>Jak srovnáváme</h1>'
            f'<p>Vian je srovnávač cen nábytku a bytových doplňků. Nic neprodáváme a nesbíráme objednávky. Každý den obnovíme ceny a jednou týdně nabídku produktů z {len(present)} českých e‑shopů, roztřídíme je podle místností a kategorií a stejné kusy z různých obchodů dáme k sobě.</p>'
            '<h2>Jak poznáme, že jde o stejný kus</h2><p>Mezi obchody párujeme podle čárového kódu (EAN) a podle značky s kódem výrobce. Varianty jednoho modelu v rámci obchodu, třeba stejnou postel ve třech šířkách a dvou barvách, spojíme na jednu stránku a ke každé variantě ukážeme její cenu. Když si nejsme jistí, necháme kusy zvlášť.</p>'
            '<h2>Rozměry</h2><p>Rozměry přebíráme z názvu a popisu, které obchod uvádí. Kde obchod napíše šířku, hloubku a výšku, nakreslíme je. Kde jen tři čísla bez popisu, ukážeme je tak, jak jsou: obchody je řadí různě. Před nákupem velkého kusu si rozměry vždy ověřte v e‑shopu a změřte dveře a schodiště, kudy se bude nosit.</p>'
            '<h2>Odkud jsou ceny</h2><p>Ceny, dostupnost, obrázky a popisy posílají obchody v produktových feedech. Cena se v obchodě může mezi naší aktualizací a vaším nákupem změnit; platí vždy cena v e‑shopu. Vývoj ceny a „nejnižší cenu za 30 dní“ počítáme jen z hodnot, které jsme sami zaznamenali.</p>'
            '<h2>Jak web vydělává</h2><p>Když přes náš odkaz nakoupíte, obchod nám může zaplatit provizi z partnerského programu (sítě CJ, eHub, Dognet a AffiliatePort). Cenu pro vás to nemění a pořadí nabídek neovlivňuje: řadíme vždy od nejlevnější.</p>'
            f'<h2>Kontakt</h2><p>Chybu v ceně, rozměru nebo zařazení nám napište na <a class="lnk" href="mailto:{R.OPERATOR["email"]}">{R.OPERATOR["email"]}</a>. Provozovatel a další údaje jsou na stránce <a class="lnk" href="/kontakt/">Kontakt</a>.</p></div>')
    return S.layout("/jak-srovnavame/", "Jak srovnáváme ceny nábytku" + SUFFIX, "Jak Vian získává ceny nábytku, páruje stejné kusy mezi obchody, slučuje varianty a z čeho žije.", body,
                    crumbs=[HOME, ("Jak srovnáváme", "/jak-srovnavame/")])


def contact_page(S):
    o = R.OPERATOR
    body = (f'<div class="prose" style="margin-top:0"><h1>Kontakt</h1><p>Vian je srovnávač cen nábytku. Nic neprodáváme, objednávky vyřizují e‑shopy, na které odkazujeme. '
            f'S dotazem k objednávce nebo dopravě se proto obracejte přímo na obchod.</p>'
            f'<h2>Provozovatel webu</h2><table class="spec"><tr><th>Jméno</th><td>{o["name"]}</td></tr><tr><th>Sídlo</th><td>{o["address"]}</td></tr>'
            f'<tr><th>IČO</th><td>{o["ico"]}</td></tr><tr><th>DPH</th><td>{o["vat"][0].upper() + o["vat"][1:]}</td></tr>'
            f'<tr><th>Datová schránka</th><td>{o["ds"]}</td></tr><tr><th>E‑mail</th><td><a class="lnk" href="mailto:{o["email"]}">{o["email"]}</a></td></tr></table>'
            '<h2>Co nám napsat</h2><p>Chybná cena, rozměr nebo zařazení, nefunkční odkaz, nebo obchod, který bychom měli srovnávat. U chyby prosím pošlete odkaz na stránku.</p></div>')
    return S.layout("/kontakt/", "Kontakt a provozovatel" + SUFFIX, "Kontakt na provozovatele srovnávače cen nábytku Vian.", body, crumbs=[HOME, ("Kontakt", "/kontakt/")])


def privacy_page(S):
    o = R.OPERATOR
    body = ('<div class="prose" style="margin-top:0"><h1>Ochrana osobních údajů a cookies</h1>'
            f'<h2>Správce údajů</h2><p>{o["name"]}, {o["address"]}, IČO {o["ico"]}, {o["vat"]}. Kontakt: <a class="lnk" href="mailto:{o["email"]}">{o["email"]}</a>. Dozorovým úřadem je Úřad pro ochranu osobních údajů (uoou.cz), u kterého můžete podat stížnost.</p>'
            '<p>Vian nemá registraci, účty ani formuláře. Neukládáme o vás žádné osobní údaje.</p>'
            '<h2>Měření návštěvnosti</h2><p>Google Analytics 4 (Google Ireland Ltd.) je na stránce ve výchozím režimu „bez souhlasu“ (Google Consent Mode): dokud nedáte souhlas v liště, nenastavuje cookies, neukládá identifikátory a o návštěvě se do Googlu posílá jen anonymní signál bez cookies. Po souhlasu měříme, které stránky lidé čtou a na které obchody klikají. Souhlas můžete kdykoli změnit odkazem „Nastavení cookies“ v patičce.</p>'
            '<h2>Odkazy do obchodů</h2><p>Odkazy do e‑shopů vedou přes partnerské sítě (CJ, eHub, Dognet, AffiliatePort), které si mohou uložit cookie, aby obchod poznal, že jste přišli od nás. Řídí se zásadami té sítě a obchodu.</p>'
            '<h2>Kalkulačka „Vejde se?“</h2><p>Rozměry, které zadáte do kalkulačky u produktu, se počítají jen ve vašem prohlížeči a nikam se neodesílají.</p></div>')
    return S.layout("/ochrana-osobnich-udaju/", "Ochrana osobních údajů" + SUFFIX, "Jak Vian zachází s osobními údaji a cookies.", body,
                    crumbs=[HOME, ("Ochrana osobních údajů", "/ochrana-osobnich-udaju/")])


def search_page(S):
    body = '<h1>Hledání</h1><p class="lead" id="sq">Napište, co hledáte, do pole nahoře.</p><ul class="grid" id="sres"></ul>'
    return S.layout("/hledat/", "Hledání" + SUFFIX, "Hledání v nábytku na Vian.cz", body, noindex=True)


# the 14 most searched categories (Marketing Miner, 11. 11. 2026), in order of demand
HOME_CATS = ["konferencni-stolky", "satni-skrine", "kancelarske-zidle", "matrace", "jidelni-zidle", "postele", "jidelni-stoly", "sedacky",
             "rohove-sedacky", "koberce", "komody", "kresla", "lustry", "tv-stolky"]


# home rows show furniture only: rooms with real furniture, minus the small stuff that lives in them (hooks, shelves, LED strips)
SHOWCASE_ROOMS = {"obyvaci-pokoj", "loznice", "jidelna-a-kuchyne", "pracovna", "detsky-pokoj", "predsin", "zahrada"}
NOT_SHOWCASE_CATS = {"vesaky", "police", "kuchynske-linky", "konzolove-stolky", "paravany", "biokrby", "stojany-na-destniky", "toppery-a-chranice-matraci",
                     "nastenky-a-tabule", "trezory", "stojany-na-vino", "detske-dekorace", "detsky-textil", "pro-miminka", "detska-svitidla",
                     "detske-koberce", "slunecniky-a-zasteny", "polstare-na-zahradni-nabytek", "grily", "ohniste-a-ohrivace", "bazeny-a-virivky",
                     "sauny", "trampoliny", "zahradni-domky", "zahradni-boxy", "skleniky-a-pestovani", "substraty-a-hnojiva", "zavlazovani",
                     "zahradni-dekorace"}
SHOWCASE_MIN_PRICE = 1500


def home_page(S, products, by_room, by_cat, sale):
    st = S.stats
    def showcase(pool, n=10, per_cat=2):
        """Home rows show furniture (not soap dispensers), at most two pieces of one category, for variety."""
        out, seen = [], Counter()
        for p in pool:
            if (p["img"] and p["price"] >= SHOWCASE_MIN_PRICE and X.TREE[p["cat"]][1] in SHOWCASE_ROOMS
                    and p["cat"] not in NOT_SHOWCASE_CATS and seen[p["cat"]] < per_cat):
                out.append(p)
                seen[p["cat"]] += 1
                if len(out) == n:
                    break
        return out
    hot = showcase([p for p in products if len(p["offers"]) > 1]) or showcase(products)
    sale = showcase(sale)
    tiles = S.tiles([(k, cat_name(k), len(by_cat[k])) for k in HOME_CATS if by_cat.get(k)], "cattiles", 96)
    rooms = S.chips([(f"/{r}/", X.ROOMS[r][0], 0) for r in X.TOP if r in S.nav_ok])
    hubs = [L for L in S.landings.values() if L["parent"] is None and L["index"]]
    styles = S.chips([(L["path"], L["h1"], L["n"]) for L in sorted(hubs, key=lambda L: -L["n"])[:10]])
    guides_sec = (f'<section class="sec"><div class="sec__h"><h2>Z poradny</h2><a href="/poradna/">Všechny články →</a></div>' + S.chips([(p, g["h1"], 0) for p, g in list(S.guides.items())[:8]]) + "</section>") if S.guides else ""
    cnt = Counter(o["shop"] for p in products for o in p["offers"])
    top_shops = [sid for sid, _ in cnt.most_common() if S.shop(sid).get("logo")][:21]
    shop_strip = (f'<section class="sec"><div class="sec__h"><h2>Obchody, které srovnáváme</h2><a href="/obchody/">Všech {len(cnt)} obchodů →</a></div><ul class="shoptiles">'
                  + "".join(f'<li><a href="/obchody/{sid}/" title="{E(S.shop(sid)["name"])}">{R.shop_logo(S.shop(sid))}</a></li>' for sid in top_shops)
                  + "</ul></section>") if len(top_shops) >= 6 else ""
    row = lambda ps: '<ul class="grid grid--5">' + "".join(S.card(p) for p in ps) + "</ul>"
    n_txt = f"{st['products']:,}".replace(",", " ")
    hero_btns = "".join(f'<a class="btn btn--lg {cls}" href="/{k}/">{t}</a>' for k, t, cls in (("rohove-sedacky", "Sedačky", "btn--cta"), ("postele", "Postele", "btn--g"))
                        if by_cat.get(k))
    body = f"""<section class="hero"><div class="wrap"><div class="hero__t"><p class="eyebrow">Srovnávač nábytku</p><h1>Nábytek, který se vám <em>vejde</em>. Za nejnižší cenu.</h1>
<p class="lead">{n_txt} kusů nábytku a doplňků z {st['shops']} českých e‑shopů na jednom místě. Filtrujte podle rozměrů v centimetrech, barvy a materiálu a kupte tam, kde je to nejlevnější.</p>
<div class="row">{hero_btns}<a class="btn btn--g btn--lg" href="/kategorie/">Vše</a></div>
<dl class="hero__stats"><div><dt>{n_txt}</dt><dd>kusů v nabídce</dd></div><div><dt>{st['shops']}</dt><dd>obchodů</dd></div><div><dt>denně</dt><dd>nové ceny</dd></div></dl></div>
<div class="hero__art"><img src="/img/ui/hero-1200.webp" srcset="/img/ui/hero-640.webp 640w, /img/ui/hero-1200.webp 1200w" sizes="(max-width:980px) 92vw, 620px" alt="Obývací pokoj se zelenou sedačkou a svinovacím metrem na podlaze" width="1200" height="583" fetchpriority="high"></div></div></section>
<div class="wrap"><section class="sec"><div class="sec__h"><h2>Nejhledanější kategorie</h2><a href="/kategorie/">Všechny kategorie →</a></div>{tiles}</section>
<section class="sec"><div class="sec__h"><h2>Podle místnosti a oddělení</h2><a href="/kategorie/">{len(S.cat_ok)} kategorií →</a></div>{rooms}</section>
<section class="sec"><div class="sec__h"><h2>Ve více obchodech najednou</h2><a href="/kategorie/">Procházet →</a></div>{row(hot)}</section>
{f'<section class="sec"><div class="sec__h"><h2>Teď ve slevě</h2><a href="/slevy/">Všechny slevy →</a></div>{row(sale)}</section>' if sale else ''}
{shop_strip}
{f'<section class="sec"><div class="sec__h"><h2>Podle stylu a materiálu</h2></div>{styles}</section>' if hubs else ''}
{guides_sec}
<section class="sec how"><h2>Jak Vian funguje</h2><ol class="steps"><li><h3>Změřte místo</h3><p>Šířku stěny, výklenku nebo prostor mezi dveřmi. U každé kategorie pak vyfiltrujete jen kusy, které se tam vejdou.</p></li>
<li><h3>Porovnejte obchody</h3><p>Stejný kus z různých e‑shopů dáme vedle sebe od nejlevnějšího. Varianty jednoho modelu najdete na jedné stránce.</p></li>
<li><h3>Kupte v e‑shopu</h3><p>Odkaz vás pošle rovnou do obchodu. Platíte tam a za stejnou cenu jako bez nás.</p></li></ol></section></div>"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Vian", "url": BASE + "/",
           "potentialAction": {"@type": "SearchAction", "target": BASE + "/hledat/?q={q}", "query-input": "required name=q"}},
          {"@context": "https://schema.org", "@type": "Organization", "name": "Vian", "url": BASE + "/", "logo": BASE + "/favicon-512.png"}]
    return S.layout("/", "Vian – srovnání cen nábytku z českých e‑shopů", f"Srovnání cen nábytku z {st['shops']} českých e‑shopů: sedačky, postele, matrace, skříně, stoly, svítidla a koberce. Filtr podle rozměrů v cm.",
                    body, jsonld=ld, preload_img="/img/ui/hero-1200.webp", full=True)


def write_search(out, products, by_room, by_cat, brands, brand_name, landings=()):
    """Header suggestions (rooms, categories, hubs, brands: small, loaded on focus) + a product index split by the first two
    letters of each word, so one query loads one small file."""
    sug = [[X.ROOMS[r][0], f"/{r}/", "místnost"] for r in X.TOP if by_room.get(r)]
    sug += [[cat_name(k), f"/{k}/", "kategorie"] for k in X.CATS if by_cat.get(k)]
    sug += [[L["h1"], L["path"], "výběr"] for L in landings if L["index"] and L["n"] >= 15][:1500]
    sug += [[brand_name[b], f"/znacky/{b}/", "značka"] for b in sorted(brands, key=lambda b: -len(brands[b]))]
    out.write("data/sug.json", json.dumps(sug, ensure_ascii=False, separators=(",", ":")))
    buckets = defaultdict(list)
    for p in products:
        if not p["page"]:
            continue
        row = [p["name"], p["slug"], p["price"], len(p["offers"]), R.img_url(p["img"])]
        keys = {w[:2] for w in re.findall(r"[a-z0-9]+", X.slugify(p["name"]).replace("-", " ")) if len(w) >= 2}
        for k in keys:
            buckets[k].append(row)
    for k, rows in buckets.items():
        out.write(f"data/s/{k}.json", json.dumps(rows[:4000], ensure_ascii=False, separators=(",", ":")))


def llms_txt(stats, by_room):
    lines = ["# Vian (vian.cz)", "", f"> Srovnávač cen nábytku a bytových doplňků z {stats['shops']} českých e-shopů ({stats['products']} kusů, ceny aktualizujeme denně).", "",
             "## Místnosti"] + [f"- [{X.ROOMS[r][0]}]({BASE}/{r}/)" for r in X.TOP if by_room.get(r)] + \
            ["", "## O webu", f"- [Jak srovnáváme]({BASE}/jak-srovnavame/)", f"- [Obchody]({BASE}/obchody/)"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
