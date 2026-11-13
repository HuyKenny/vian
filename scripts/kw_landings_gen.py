#!/usr/bin/env python3
"""content/landings/kw2.json from the keyword backlog (scripts/kw_analyze.py).

    python3 scripts/kw_landings_gen.py [--min-volume 60] [--limit 900]

Each phrase is mapped with the SAME taxonomy as the catalogue: category = taxonomy.classify({"t": phrase}); colour / material / style / feature
= the taxonomy patterns; size NNxNNN; price cap "do N kč"; a known brand; what is left over becomes `all` stems. The record carries `evidence`
(monthly searches). The build (scripts/landings.py) decides what exists: fewer than `min` products = no page, the same product set as an
existing page (dedupe_all) = no page, below `index_min` = noindex, a phrase that is just the category = no record. Over-generating is safe."""
import csv
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taxonomy as X  # noqa: E402

APP = Path(__file__).resolve().parent.parent
MIN_VOL = int(sys.argv[sys.argv.index("--min-volume") + 1]) if "--min-volume" in sys.argv else 60
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 900
fold = X.fold
STOPW = set("pro na do od a s se z ze v ve u k o po za je to nejlepsi levne levny levna cena cenik akce sleva eshop obchod koupit online cz skladem srovnani cm mm kc kus kusy sada nabytek".split())
NOISE = re.compile(r"\b(kreslen\w*|kresleny|recept\w*|kur\w*|hoved\w*|vepr\w*|maso|boty|bota|pes|psa|kocka|kocky|kocici|zaba|kavarn\w*|rozmery|servis|co je|vyznam|historie|navod|plan|projekt|3d|program|aplikace|vyroba|vyrobit|diy|bazar|pujcovna|pronajem|montaz|kuchynske pracovni desky na miru)\b")
SKIP_SLUGS = {"nabytek", "bytove-doplnky", "dekorace", "svitidla", "lampy"}


def stem(w):
    return w[: max(5, len(w) - 2)] if len(w) > 5 else w


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", fold(s)).strip("-")[:64].rstrip("-")


def brands():
    c = Counter()
    for f in (APP / "data/raw").glob("*.jsonl.gz"):
        for line in gzip.open(f, "rt", encoding="utf-8"):
            b = (json.loads(line).get("b") or "").strip()
            if b:
                c[b] += 1
    out = {}
    for b, n in c.most_common(500):
        k = fold(re.sub(r"[^\w ]", " ", b)).strip()
        if len(k) >= 4 and k not in ("top", "duo", "cwf", "bpm", "astro"):
            out.setdefault(k, b)
    return out


def main():
    rows = list(csv.DictReader(open(APP / "content/keywords/backlog.tsv"), delimiter="\t"))
    br = brands()
    seen, recs, skipped = {}, [], Counter()
    for r in rows:
        vol = int(r["volume"])
        if vol < MIN_VOL or r["intent"] in ("brand-nav", "question"):
            continue
        key = " ".join(re.findall(r"[a-z0-9]+", fold(r["phrase"])))
        if NOISE.search(key):
            skipped["noise"] += 1
            continue
        cat = X.classify({"t": key})
        if not cat or cat not in X.CATS:
            skipped["no category"] += 1
            continue
        rules, used = {"cat": [cat]}, set()
        for lst, name, rxs in (("colors", "colors", X.COLORS_RX), ("mats", "mats", X.MATERIALS_RX), ("styles", "styles", X.STYLES_RX), ("feats", "feats", X.FEATURES_RX)):
            hit = [s for s, _, rx in rxs if rx.search(key)]
            if hit:
                rules[name] = hit[:2]
                for s, _, rx in rxs:
                    if s in hit:
                        m = rx.search(key)
                        used |= set(re.findall(r"[a-z0-9]+", m.group(0)))
        m = re.search(r"\b(\d{2,3})\s?x\s?(\d{2,3})\b", key)
        if m:
            rules["size"] = f"{m.group(1)}x{m.group(2)}"
            used |= {m.group(1), m.group(2), "x", m.group(1) + "x" + m.group(2)}
        m = re.search(r"\b(?:do|pod)\s(\d{3,6})\b(?:\s?kc)?", key)
        if m:
            rules["price"] = [None, int(m.group(1))]
            used |= {m.group(1), "do", "pod"}
        bm = next((b for k, b in br.items() if re.search(r"\b" + re.escape(k) + r"\b", key)), None)
        if bm:
            rules["brand"] = [bm]
            used |= set(re.findall(r"[a-z0-9]+", fold(bm)))
        catwords = {stem(w) for w in re.findall(r"[a-z0-9]+", fold(X.CATS[cat][0] + " " + X.CATS[cat][2]))}
        rest = [w for w in re.findall(r"[a-z0-9]+", key) if w not in STOPW and w not in used and stem(w) not in catwords and not re.fullmatch(r"\d+", w) and len(w) > 2]
        if rest:
            rules["all"] = [r"\b" + stem(w) + r"\w*" for w in rest[:3]]
        if len(rules) == 1:                           # only the category: the category page itself covers it
            skipped["is the category"] += 1
            continue
        sig = json.dumps(rules, sort_keys=True)
        if sig in seen:
            seen[sig]["evidence"] += vol
            continue
        h1 = r["phrase"][:1].upper() + r["phrase"][1:]
        slug = slugify(r["phrase"])
        if not slug or slug in SKIP_SLUGS or slug in X.TREE:
            continue
        rec = {"slug": slug, "h1": h1, "parent": f"/{cat}/", "cat": cat, "hubs": [f"/{cat}/"], "group": "kw2", "dedupe_all": True, "rules": rules, "min": 8, "index_min": 14,
               "evidence": vol, "intent": r["intent"], "title": f"{h1} – srovnání cen"}
        seen[sig] = rec
        recs.append(rec)
        if len(recs) >= LIMIT:
            break
    (APP / "content/landings/kw2.json").write_text(json.dumps(recs, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(recs)} phrase pages -> content/landings/kw2.json; skipped {dict(skipped)}")


if __name__ == "__main__":
    main()
