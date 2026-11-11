"""Listing texts: hand-written ones from content/texts/*.json win; otherwise a short, honest text built from the data
(price range, widths, materials, colours, brands, shops) — nothing invented, every number comes from the current catalogue."""
import json
import statistics
from collections import Counter
from pathlib import Path

import render as R
import taxonomy as X

APP = Path(__file__).resolve().parent.parent
_T = None


def _load():
    global _T
    if _T is None:
        _T = {}
        for f in sorted((APP / "content/texts").glob("*.json")):   # one file per page: {"key", "intro", "body", "faq": [[q, a]]}
            d = json.loads(f.read_text())
            _T[d["key"]] = d
    return _T


def get(key):
    return _load().get(key)


def low(h1):
    return h1[:1].lower() + h1[1:] if not h1[:2].isupper() else h1


def generated(key, items, h1, S):
    if not items:
        return "", []
    E = R.E
    ps = sorted(p["price"] for p in items)
    lo, med, hi = ps[0], int(statistics.median(ps)), ps[-1]
    n = len(items)
    noun = low(h1)
    brands = [b for b, _ in Counter(p["brand"] for p in items if p["brand"]).most_common(6)]
    shops = Counter(o["shop"] for p in items for o in p["offers"])
    multi = [p for p in items if len(p["offers"]) > 1]
    widths = sorted(p["wmin"] for p in items if p["wmin"])
    mats = Counter(m for p in items for m in p["mats"]).most_common(4)
    cols = Counter(c for p in items for c in p["colors"]).most_common(4)
    q = [(f"Kolik stojí {noun}?",
          f"Teď je v nabídce {n} {R.plural(n, 'kus', 'kusy', 'kusů')} od {R.kc(lo)} do {R.kc(hi)}. Polovina stojí méně než {R.kc(med)}.")]
    if len(widths) >= max(6, n * 0.3):
        w_lo, w_med, w_hi = widths[0], widths[len(widths) // 2], widths[-1]
        q.append(("Jaké rozměry mají?",
                  f"U {len(widths)} {R.plural(len(widths), 'kusu', 'kusů', 'kusů')} obchod uvádí šířku: od {X.cz(w_lo)} do {X.cz(w_hi)} cm, nejčastěji kolem {X.cz(w_med)} cm. "
                  "V levém panelu zadejte šířku místa a ukážeme jen to, co se vejde."))
    if len(mats) >= 2:
        q.append(("Z jakých materiálů vybírat?", "Nejčastěji " + ", ".join(f"{X.MATERIAL_NAME[m]} ({c})" for m, c in mats) + ". Materiál filtrujete vlevo."))
    if len(brands) >= 2:
        q.append(("Které značky jsou nejčastější?", "Nejvíc nabídek mají " + ", ".join(E(b) for b in brands[:5]) + "."))
    if shops:
        top = shops.most_common(3)
        q.append(("Ve kterých obchodech je nejvíc nabídek?",
                  ", ".join(f"{E(S.shop(s)['name'])} ({c})" for s, c in top) + f". Celkem srovnáváme {len(shops)} {R.plural(len(shops), 'obchod', 'obchody', 'obchodů')}."))
    if multi:
        save = [p["offers"][-1]["price"] - p["price"] for p in multi]
        q.append(("Vyplatí se ceny porovnávat?",
                  f"U {len(multi)} {R.plural(len(multi), 'kusu', 'kusů', 'kusů')} z této stránky máme víc obchodů najednou. Rozdíl mezi nejlevnějším a nejdražším obchodem je u nich v průměru "
                  f"{R.kc(sum(save) / len(save))}, nejvíc {R.kc(max(save))}."))
    colours = (" Nejčastější barvy: " + ", ".join(X.COLOR_NAME[c] for c, _ in cols) + ".") if len(cols) >= 2 else ""
    prose = (f"<h2>{E(h1)}: přehled nabídky</h2><p>Na této stránce je {n} {R.plural(n, 'kus', 'kusy', 'kusů')} z českých e‑shopů, "
             f"ceny od {R.kc(lo)} do {R.kc(hi)}.{colours} Nahoře jsou kusy, které najdete ve více obchodech, u nich má srovnání největší smysl. "
             "Filtry vlevo zúží výběr podle rozměru, ceny, barvy, materiálu, značky nebo obchodu.</p>")
    return prose, q
