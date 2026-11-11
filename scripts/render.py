"""HTML templates for vian.cz (plain f-strings, no dependencies). Design "Showroom" — see static/assets/site.css.

A furniture catalogue that measures things: linen paper (#F6F3EE), ink (#1E2321), fir green (#2F5D50) for the brand and
links, terracotta (#B4532D) only for sales and the call to action. Shapes borrowed from print: 1.5px ink rules, hard
offset shadows on buttons, price labels cut like a shop's hang tag, and a tape-measure strip wherever a size is shown.
Illustrations from Canva (one icon sheet cut into 16 pieces, so they share one hand).
"""
import html
import json
import re

import taxonomy as X

E = html.escape
PER_PAGE = 36
SUFFIX = " | Vian"
SPECULATION = ('<script type="speculationrules">{"prerender":[{"where":{"and":[{"href_matches":"/*"},{"not":{"href_matches":"/data/*"}},'
               '{"not":{"selector_matches":"[rel~=nofollow],[target=_blank]"}}]},"eagerness":"moderate"}]}</script>')
SEARCH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>'
RULER_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2" y="8" width="20" height="8" rx="1.5"/>'
              '<path d="M6 8v3M10 8v4M14 8v3M18 8v4"/></svg>')
SWATCH = {"bila": "#FFFFFF", "cerna": "#1E1E1E", "seda": "#9A9C9A", "bezova": "#E3D3B8", "hneda": "#7A5236", "zelena": "#4F7A5A", "modra": "#3F6E9E",
          "ruzova": "#E7B3B8", "cervena": "#B3322C", "zluta": "#E9C24A", "oranzova": "#D8743C", "zlata": "#C7A043", "stribrna": "#C9CCCF"}
OPERATOR = {"name": "Ha Duy Huy", "address": "Bartáková 36, 140 00 Praha", "ico": "07876823", "ds": "dxmsrdt",
            "vat": "není plátce DPH", "email": "info@vian.cz"}   # public business-register data (ARES), the site operator on legal pages
LOGO = '<img src="/img/ui/mark-96.webp" alt="" width="40" height="35"><span class="wm">vian</span>'
NAV = ["obyvaci-pokoj", "loznice", "jidelna-a-kuchyne", "pracovna", "detsky-pokoj", "predsin", "koupelna", "zahrada", "svitidla", "textil", "dekorace"]


def kc(n):
    return f"{int(round(n)):,}".replace(",", " ") + " Kč"


def plural(n, one, few, many):
    return one if n == 1 else few if 1 < n < 5 else many


def shops_in(n):
    return f"v {n} obchodě" if n == 1 else f"ve {n} obchodech" if n in (2, 3, 4) else f"v {n} obchodech"


def shorten(text, limit, keep_tail=""):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    tail = keep_tail if keep_tail and text.endswith(keep_tail) else ""
    room = limit - len(tail) - 1
    head = text[:len(text) - len(tail)][:room].rsplit(" ", 1)[0].rstrip(" ,;:-–—(")
    return head + "…" + tail


def img_url(u, size="card"):
    """Smaller renditions straight from the shops' image CDNs — we never resize anything ourselves (0 CPU on Cloudflare).
    XXXLutz (Amplience) measured 11. 11. 2026: feed preset 44 kB -> ?fmt=webp&w=400 5 kB."""
    if not u:
        return u
    card = size == "card"
    if "media.xxxlutz.com/" in u:
        return u.split("?")[0] + ("?fmt=auto&w=400" if card else "?fmt=auto&w=900")
    if "cdn.myshoptet.com" in u and "/user/shop/orig/" in u:
        return u.replace("/user/shop/orig/", "/user/shop/detail/" if card else "/user/shop/big/")
    return u


def pager_html(path, cur, pages):
    if pages <= 1:
        return ""
    url = lambda k: path if k == 1 else f"{path}strana-{k}/"
    show = sorted({1, pages, cur - 2, cur - 1, cur, cur + 1, cur + 2} & set(range(1, pages + 1)))
    out, last = [], 0
    for k in show:
        if k - last > 1:
            out.append('<span class="gap">…</span>')
        out.append(f'<a aria-current="page" class="on">{k}</a>' if k == cur else f'<a href="{url(k)}">{k}</a>')
        last = k
    prev = f'<a class="pp" href="{url(cur - 1)}" rel="prev" aria-label="Předchozí strana">‹</a>' if cur > 1 else ""
    nxt = f'<a class="pp" href="{url(cur + 1)}" rel="next" aria-label="Další strana">›</a>' if cur < pages else ""
    return f'<nav class="pager" aria-label="Stránkování">{prev}{"".join(out)}{nxt}</nav>'


def ld(x):
    return f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>'


def swatches(colors, n=4):
    if not colors:
        return ""
    return '<span class="sw">' + "".join(f'<i style="--c:{SWATCH[c]}" title="{X.COLOR_NAME[c]}"></i>' for c in colors[:n]) + "</span>"


def dims_svg(dm):
    """Measured drawing of the piece: a box in front view with width and height arrows, depth as a label.
    Only labelled dimensions (Šířka/Hloubka/Výška) or a lying size (160 × 200) are drawn."""
    w, d, h = dm.get("w"), dm.get("d"), dm.get("h")
    if dm.get("size"):
        a, b = dm["size"].split("x")
        return (f'<figure class="dimfig"><svg viewBox="0 0 260 170" role="img" aria-label="Rozměr {a} × {b} cm">'
                f'<rect x="60" y="20" width="140" height="120" rx="6" class="dbox"/><path d="M60 155h140M60 150v10M200 150v10" class="dline"/>'
                f'<path d="M222 20v120M217 20h10M217 140h10" class="dline"/><text x="130" y="166" text-anchor="middle">{X.cz(float(a))} cm</text>'
                f'<text x="238" y="84" text-anchor="start" transform="rotate(90 238 84)">{X.cz(float(b))} cm</text></svg>'
                f'<figcaption>Rozměr ložné / podlahové plochy</figcaption></figure>')
    if not (w and (d or h)) or dm.get("raw"):
        return ""
    lab = lambda v: X.cz(v) + " cm"
    parts = [f'<rect x="40" y="30" width="170" height="100" rx="4" class="dbox"/>',
             '<path d="M40 148h170M40 143v10M210 143v10" class="dline"/>', f'<text x="125" y="166" text-anchor="middle">šířka {lab(w)}</text>']
    if h:
        parts += ['<path d="M228 30v100M223 30h10M223 130h10" class="dline"/>', f'<text x="236" y="80" transform="rotate(90 236 80)" text-anchor="middle">výška {lab(h)}</text>']
    if d:
        parts += ['<path d="M40 30l20-18h170l-20 18M210 130l20-18V12" class="dbox dback"/>', f'<text x="135" y="9" text-anchor="middle">hloubka {lab(d)}</text>']
    return f'<figure class="dimfig"><svg viewBox="0 0 260 172" role="img" aria-label="Rozměry {E(X.size_label(dm))}">{"".join(parts)}</svg></figure>'


class Site:
    def __init__(self, base, env, ga, css, js, shops, stats):
        self.base, self.env, self.ga, self.css, self.js = base, env, ga, css, js
        self.shops = shops
        self.stats = stats
        self.pg = None
        self.pg_noindex = False
        self.pending_ld = None
        self.nav_ok = None
        self.footer_links = []
        self.has_guides = False

    def url(self, path):
        return self.base + path

    def layout(self, path, title, desc, body, crumbs=None, noindex=False, jsonld=None, preload_img=None, og_img=None, full=False):
        title, desc = shorten(title, 68, SUFFIX), shorten(desc, 160)      # BEFORE the " – strana N" suffix, so paginated titles stay distinct
        robots = "noindex,follow" if (noindex or self.pg_noindex or self.env != "production") else "index,follow,max-image-preview:large"
        if self.pg and self.pg[1] > 1:
            n = self.pg[1]
            path = f"{self.pg[0]}strana-{n}/"
            title = title.replace(SUFFIX, f" – strana {n}{SUFFIX}") if title.endswith(SUFFIX) else f"{title} – strana {n}"
            desc = f"Strana {n}: {desc}"
            jsonld = [x for x in (jsonld or []) if x and x.get("@type") != "FAQPage"]
            body = re.sub(r'<section class="faq">.*?</section>', "", body, flags=re.S)
            body = re.sub(r'<div class="prose">.*?</div><!--/prose-->', "", body, flags=re.S)
            body = re.sub(r"</h1>", f' <small class="pgn">strana {n}</small></h1>', body, count=1)
        lds = list(jsonld or [])
        if self.pending_ld:
            lds.append(self.pending_ld)
            self.pending_ld = None
        head_ld = "".join(ld(x) for x in lds if x)
        cr = ""
        if crumbs:
            head_ld += ld({"@context": "https://schema.org", "@type": "BreadcrumbList",
                           "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": self.url(u)} for i, (n, u) in enumerate(crumbs)]})
            cr = '<nav class="crumbs" aria-label="Drobečková navigace">' + "<i>/</i>".join(
                f'<a href="{u}">{E(n)}</a>' if i < len(crumbs) - 1 else f"<span>{E(n)}</span>" for i, (n, u) in enumerate(crumbs)) + "</nav>"
        pre = f'<link rel="preload" as="image" href="{E(preload_img)}" fetchpriority="high">' if preload_img else ""
        ga = ""
        if self.ga and self.env == "production":
            boot = ('window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}'
                    'var g="denied";try{if(localStorage.getItem("vian-consent")==="yes")g="granted"}catch(e){}'
                    'gtag("consent","default",{analytics_storage:g,ad_storage:"denied",ad_user_data:"denied",ad_personalization:"denied",wait_for_update:500});'
                    'gtag("set","ads_data_redaction",true);')
            if self.ga.startswith("GTM-"):
                lib = f'dataLayer.push({{"gtm.start":Date.now(),event:"gtm.js"}});</script><script async src="https://www.googletagmanager.com/gtm.js?id={self.ga}"></script>'
            else:
                lib = f'gtag("js",new Date());gtag("config","{self.ga}");</script><script async src="https://www.googletagmanager.com/gtag/js?id={self.ga}"></script>'
            ga = f'<meta name="ga4" content="{self.ga}"><script>{boot}{lib}'
        content = body if full else f'<div class="wrap page">{cr}{body}</div>'
        if full and crumbs:
            content = content.replace("<!--crumbs-->", cr, 1)
        ok = self.nav_ok
        nav = "".join(f'<li><a href="/{k}/"><img src="/img/ic/{X.ICON[k]}.webp" alt="" width="36" height="36" loading="lazy">{E(X.ROOMS[k][0])}</a></li>'
                      for k in NAV if ok is None or k in ok)
        og = og_img or f"{self.base}/img/ui/og.png"
        n_shops = self.stats["shops"]
        return f"""<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{self.url(path)}"><meta name="robots" content="{robots}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{self.url(path)}"><meta property="og:type" content="website"><meta property="og:locale" content="cs_CZ"><meta property="og:site_name" content="Vian"><meta property="og:image" content="{E(og)}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#2F5D50"><link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/favicon-192.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/favicon-180.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/fonts/fraunces-cs.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="/fonts/onest-cs.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="/assets/{self.css}">{pre}{SPECULATION}{ga}{head_ld}</head><body>
<a class="skip" href="#main">Přeskočit na obsah</a>
<header class="top"><div class="wrap"><a class="logo" href="/" aria-label="Vian – úvod">{LOGO}</a>
<form class="search" role="search" action="/hledat/" method="get"><label class="sr" for="q">Hledat nábytek, značku nebo obchod</label>{SEARCH_ICON}<input id="q" name="q" type="search" placeholder="Rohová sedačka, postel 160×200, dubový stůl…" autocomplete="off"><button type="submit">Hledat</button><div class="sugg" id="sugg" role="listbox"></div></form>
<nav class="hl" aria-label="Rychlé odkazy"><a href="/slevy/">Slevy</a>{'<a href="/poradna/">Poradna</a>' if self.has_guides else ""}</nav></div>
<nav class="rooms" aria-label="Místnosti"><div class="wrap"><ul>{nav}</ul></div></nav></header>
<main id="main">{content}</main>
<footer><div class="wrap cols"><div class="fabout"><a class="logo" href="/">{LOGO}</a><p>Vian srovnává ceny nábytku a bytových doplňků z {n_shops} českých e‑shopů. Nic neprodáváme: nakoupíte přímo v obchodě za stejnou cenu. Když nakoupíte přes náš odkaz, obchod nám může zaplatit provizi. Z ní web žije a pořadí nabídek neovlivňuje.</p></div>
<div><h3>Nábytek</h3><ul><li><a href="/sedacky/">Sedačky</a></li><li><a href="/rohove-sedacky/">Rohové sedačky</a></li><li><a href="/postele/">Postele</a></li><li><a href="/matrace/">Matrace</a></li><li><a href="/satni-skrine/">Šatní skříně</a></li><li><a href="/jidelni-stoly/">Jídelní stoly</a></li><li><a href="/kancelarske-zidle/">Kancelářské židle</a></li><li><a href="/kategorie/">Všechny kategorie</a></li></ul></div>
<div><h3>Bydlení</h3><ul><li><a href="/koberce/">Koberce</a></li><li><a href="/lustry/">Lustry</a></li><li><a href="/zaclony-a-zavesy/">Záclony a závěsy</a></li><li><a href="/povleceni/">Povlečení</a></li><li><a href="/zrcadla/">Zrcadla</a></li><li><a href="/slevy/">Slevy na nábytek</a></li>{"".join(f'<li><a href="{u}">{E(t)}</a></li>' for u, t in self.footer_links)}</ul></div>
<div><h3>Vian</h3><ul><li><a href="/jak-srovnavame/">Jak srovnáváme</a></li>{'<li><a href="/poradna/">Poradna</a></li>' if self.has_guides else ""}<li><a href="/obchody/">Obchody</a></li><li><a href="/znacky/">Značky</a></li><li><a href="/kontakt/">Kontakt</a></li><li><a href="/ochrana-osobnich-udaju/">Ochrana osobních údajů</a></li><li><a href="#" id="consent-open">Nastavení cookies</a></li></ul></div></div>
<div class="wrap fine"><p>Ceny, rozměry a dostupnost přebíráme od obchodů a mohou se změnit; platí údaj v e‑shopu v okamžiku nákupu. Poslední aktualizace {self.stats["updated"]}.</p>
<p>Provozovatel: {OPERATOR["name"]}, {OPERATOR["address"]}, IČO {OPERATOR["ico"]}, {OPERATOR["vat"]}. <a href="/kontakt/">Kontakt</a> · <a href="mailto:{OPERATOR["email"]}">{OPERATOR["email"]}</a></p></div></footer>
<div class="consent" id="consent" role="dialog" aria-label="Cookies" hidden><p>Smíme měřit návštěvnost (Google Analytics)? Bez souhlasu nic neměříme.</p>
<div class="row"><button class="btn" data-consent="yes">Souhlasím</button><button class="btn btn--g" data-consent="no">Nesouhlasím</button><a href="/ochrana-osobnich-udaju/" class="lnk">Více</a></div></div>
<script src="/assets/{self.js}" defer></script></body></html>"""

    # ------------------------------------------------------------ pieces

    def shop(self, sid):
        return self.shops.get(sid, {"name": sid, "color": "#888"})

    def go_attrs(self, shop):
        return f'rel="sponsored nofollow noopener" target="_blank" data-go="{E(shop)}"'

    @staticmethod
    def discount(p):
        o = p["offers"][0]
        if o.get("was") and o["was"] > o["price"]:
            d = round((o["was"] - o["price"]) / o["was"] * 100)
            return d if d <= 80 else 0      # "−95 %" is a broken "was" price in the feed, not a real sale
        return 0

    def tag(self, price, prefix="", big=False, was=0):
        pre = f"<small>{prefix}</small>" if prefix else ""
        old = f"<s>{kc(was)}</s>" if was and was > price else ""
        return f'<span class="ptag{" ptag--xl" if big else ""}">{pre}{old}<b>{kc(price)}</b></span>'

    @staticmethod
    def tape(p):
        dm = p.get("dims") or {}
        if p.get("sizes") and len(p["sizes"]) > 1:
            return f'{len(p["sizes"])} rozměry' if len(p["sizes"]) < 5 else f'{len(p["sizes"])} rozměrů'
        return X.size_label(dm)

    def card(self, p, lazy=True):
        n = len(p["offers"])
        href = f'/produkt/{p["slug"]}/'
        img = E(img_url(p["img"]) or "/img/ui/placeholder.svg")
        load = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
        d = self.discount(p)
        sale = f'<span class="flag">−{d} %</span>' if d >= 10 else ""
        tp = self.tape(p)
        tape = f'<span class="tape">{E(tp)}</span>' if tp else ""
        nv = len(p.get("variants") or [])
        meta = shops_in(n) + (f" · {nv} {plural(nv, 'varianta', 'varianty', 'variant')}" if nv > 1 else "")
        alt_u = next((img_url(u) for u in p.get("imgs") or [] if u and u != p["img"]), "")
        alt = f' data-alt="{E(alt_u)}"' if alt_u and p["img"] else ""
        return (f'<li class="pc"><a class="pc__img" href="{href}" tabindex="-1" aria-hidden="true"><img src="{img}" alt=""{load}{alt} referrerpolicy="no-referrer" width="320" height="320">{sale}{tape}</a>'
                f'<div class="pc__b">{f"<span class=pc__brand>{E(p["brand"])}</span>" if p["brand"] else ""}<h3><a href="{href}">{E(p["name"])}</a></h3>'
                f'{swatches(p.get("colors"))}<div class="pc__f">{self.tag(p["price"], "od" if (n > 1 or nv > 1) else "")}<span class="pc__n">{meta}</span></div></div></li>')

    def item_json(self, p, bidx):
        """Compact row for client-side filtering:
        [name, slug, img, price, shops, brand#, colors, mats, styles, wmin, wmax, discount, shopids, variants, tape, feats]"""
        return [p["name"], p["slug"], img_url(p["img"]), p["price"], len(p["offers"]), bidx.get(p["brand"], -1), p["colors"], p["mats"], p["styles"],
                p["wmin"] or 0, p["wmax"] or 0, self.discount(p), [o["shop"] for o in p["offers"]], len(p.get("variants") or []), self.tape(p), p["feats"]]

    def grid(self, items, first_lazy=True, cls="grid"):
        return f'<ul class="{cls}">' + "".join(self.card(p, lazy=first_lazy or i > 3) for i, p in enumerate(items)) + "</ul>"

    def faq(self, qa):
        if not qa:
            return "", None
        h = '<section class="faq"><h2>Časté otázky</h2>' + "".join(f"<details><summary>{E(q)}</summary><div>{a}</div></details>" for q, a in qa) + "</section>"
        data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in qa]}
        return h, data

    def chips(self, links, cls="chips"):
        return f'<ul class="{cls}">' + "".join(f'<li><a href="{u}">{E(t)}{f"<small>{n}</small>" if n else ""}</a></li>' for u, t, n in links) + "</ul>" if links else ""

    def listing(self, items, json_url, order="pop", facets=None):
        path, cur, pages = self.pg or ("", 1, 1)
        chunk = items[(cur - 1) * PER_PAGE:cur * PER_PAGE]
        self.pending_ld = {"@context": "https://schema.org", "@type": "ItemList", "numberOfItems": len(items),
                           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": self.url(f'/produkt/{p["slug"]}/'), "name": p["name"]}
                                               for i, p in enumerate(chunk[:24], (cur - 1) * PER_PAGE)]} if chunk else None
        filt = self.filters(items, facets or {})
        n = len(items)
        return (f'<div class="layout">{filt}<div class="results"><div class="listhead"><p><b id="count">{n}</b> {plural(n, "kus", "kusy", "kusů")}</p>'
                f'<button class="btn btn--g ftoggle" type="button" aria-controls="filters">Filtry</button>'
                f'<label class="sort">Řadit <select id="sort"><option value="pop">nejvíc obchodů</option><option value="price"{" selected" if order == "price" else ""}>nejlevnější</option>'
                f'<option value="pricedesc">nejdražší</option><option value="sale">největší sleva</option></select></label></div>'
                f'<div class="qf" role="group" aria-label="Rychlé filtry"><button type="button" data-q="sale">Ve slevě</button><button type="button" data-q="multi">Ve více obchodech</button>'
                + "".join(f'<button type="button" data-q="pmax" data-v="{c}">do {kc(c)}</button>' for c in self.quick_caps(items)) +
                f'</div><ul class="grid" id="plist" data-json="{json_url}" data-page="{cur}" data-order="{order}">{"".join(self.card(p, lazy=i > 3) for i, p in enumerate(chunk))}</ul>'
                f'{pager_html(path, cur, pages) if path else ""}</div></div>')

    @staticmethod
    def quick_caps(items):
        ps = sorted(p["price"] for p in items)
        if not ps:
            return []
        steps = [500, 1000, 2000, 3000, 5000, 10000, 15000, 20000, 30000]
        med = ps[len(ps) // 2]
        lo = next((s for s in steps if s >= ps[len(ps) // 5]), steps[0])
        hi = next((s for s in steps if s >= med), steps[-1])
        return sorted({lo, hi})

    def filters(self, items, facets):
        h = '<form class="card filters" id="filters" aria-label="Filtry">'
        cats = facets.get("cats")
        if cats:
            srch = '<input class="fsearch" type="search" placeholder="Hledat" aria-label="Hledat v odkazech">' if len(cats) > 10 else ""
            h += (f'<fieldset class="fcats"><legend>{E(facets.get("cats_label", "Upřesnit"))}</legend>{srch}<div class="flinks">' + "".join(
                f'<a href="{u}">{E(t)}{f"<span class=count>{n}</span>" if n else ""}</a>' for u, t, n in cats) + "</div></fieldset>")
        if facets.get("width"):
            h += ('<fieldset class="fit"><legend>Vejde se to?</legend><p class="muted">Změřte místo a zadejte šířku v cm.</p>'
                  '<div class="fprice"><input type="number" name="wmin" min="0" step="5" placeholder="od" aria-label="Šířka od (cm)">'
                  '<span>–</span><input type="number" name="wmax" min="0" step="5" placeholder="do" aria-label="Šířka do (cm)"><span>cm</span></div></fieldset>')
        h += ('<fieldset><legend>Cena</legend><div class="fprice"><input type="number" name="pmin" min="0" step="100" placeholder="od" aria-label="Cena od (Kč)">'
              '<span>–</span><input type="number" name="pmax" min="0" step="100" placeholder="do" aria-label="Cena do (Kč)"><span>Kč</span></div></fieldset>')
        cols = facets.get("colors")
        if cols:
            h += '<fieldset><legend>Barva</legend><div class="fsw">' + "".join(
                f'<label title="{X.COLOR_NAME[c]}"><input type="checkbox" name="colors" value="{c}"><i style="--c:{SWATCH[c]}"></i><span>{X.COLOR_NAME[c]}</span><span class="count">{n}</span></label>'
                for c, n in cols) + "</div></fieldset>"
        for key, legend, names in (("mats", "Materiál", X.MATERIAL_NAME), ("styles", "Styl", X.STYLE_NAME), ("feats", "Provedení", X.FEATURE_NAME)):
            vals = facets.get(key)
            if vals:
                h += f'<fieldset><legend>{legend}</legend><div class="flinks">' + "".join(
                    f'<label><input type="checkbox" name="{key}" value="{v}"> {E(names[v])}<span class="count">{n}</span></label>' for v, n in vals) + "</div></fieldset>"
        brands = facets.get("brand")
        if brands:
            srch = '<input class="fsearch" type="search" placeholder="Hledat značku" aria-label="Hledat značku">' if len(brands) > 10 else ""
            h += (f'<fieldset><legend>Značka</legend>{srch}<div class="flinks">' + "".join(
                f'<label><input type="checkbox" name="brand" value="{i}"> {E(b)}<span class="count">{n}</span></label>' for i, b, n in brands) + "</div></fieldset>")
        shops = facets.get("shop")
        if shops and len(shops) > 1:
            h += '<fieldset><legend>Obchod</legend><div class="flinks">' + "".join(
                f'<label><input type="checkbox" name="shop" value="{E(s)}"> {E(self.shop(s)["name"])}<span class="count">{n}</span></label>' for s, n in shops) + "</div></fieldset>"
        h += ('<fieldset><legend>Jen</legend><label><input type="checkbox" name="multi" value="1"> ve více obchodech</label>'
              '<label><input type="checkbox" name="sale" value="1"> ve slevě</label></fieldset>')
        return h + '<button class="btn btn--g freset" type="button" hidden>Zrušit filtry</button><div class="fbar"><button class="btn fclose" type="button">Zobrazit</button></div></form>'

    def band(self, h1, lead, icon=None, extra=""):
        art = f'<img class="band__ic" src="/img/ic/{icon}.webp" alt="" width="120" height="120">' if icon else ""
        return f'<section class="band"><div class="wrap"><div class="band__t"><!--crumbs--><h1>{h1}</h1><p class="lead">{lead}</p>{extra}</div>{art}</div></section>'


def svg_history(hist, today):
    """Step chart of our own price observations (no JS)."""
    if not hist or len(hist) < 2:
        return ""
    pts = hist + [[today, hist[-1][1]]]
    x0, x1 = pts[0][0], max(pts[-1][0], pts[0][0] + 1)
    ys = [p[1] for p in pts]
    lo, hi = min(ys), max(ys)
    if hi == lo:
        hi = lo + 1
    W, H = 320, 90
    Xf = lambda d: round((d - x0) / (x1 - x0) * (W - 10) + 5, 1)
    Y = lambda v: round(H - 12 - (v - lo) / (hi - lo) * (H - 30), 1)
    d = f"M{Xf(pts[0][0])},{Y(pts[0][1])}"
    for a, b in zip(pts, pts[1:]):
        d += f" H{Xf(b[0])} V{Y(b[1])}"
    return (f'<svg class="hist" viewBox="0 0 {W} {H}" role="img" aria-label="Vývoj nejnižší ceny: od {kc(lo)} do {kc(hi)}">'
            f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<text x="5" y="{H - 1}" font-size="11">{kc(lo)}</text><text x="{W - 5}" y="12" font-size="11" text-anchor="end">{kc(hi)}</text></svg>')
