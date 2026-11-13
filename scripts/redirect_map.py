#!/usr/bin/env python3
"""data/redirects.txt (old vian.cz URLs -> live pages) from data/old-urls.txt (Wayback CDX, see scripts/vian/old-urls.py in ai-workspace).

    python3 scripts/redirect_map.py [report]

The old WordPress site had product slugs at the top level (/bellatex-polstar-ekonomy-50-x-60-cm/), /obchod/<slug>/, old category slugs and
/brand/<name>/. The slug words are classified with the same taxonomy as the live catalogue (taxonomy.classify) -> the live category with
enough products (data/state/build-report.json per_cat >= 8), else its room, else nothing. Numeric ids (/162149/), images and anything that
does not classify get NO rule (404 + the client-side nearest-page redirect + suggestions); spam-like paths never get a rule, so no inherited
bad authority flows into good categories. build.py (redirects_file) additionally skips sources that are live pages and falls back to a
parent for targets that do not exist; the file is capped at 2 000 static rules (Cloudflare limit), ordered by how specific the match is."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taxonomy as X  # noqa: E402

APP = Path(__file__).resolve().parent.parent
LIMIT = 2000
per_cat = json.loads((APP / "data/state/build-report.json").read_text()).get("per_cat", {})
live = {c for c, n in per_cat.items() if n >= 8 and c in X.CATS}
SKIP = re.compile(r"^/(wp-|feed|xmlrpc|sitemap|robots|admin|cart|kosik|login|my-account|tag/|author/|page/|comments|search|\?)|\.(jpe?g|png|gif|webp|svg|pdf|css|js|xml)$", re.I)
SPAM = re.compile(r"casino|kasino|poker|slot|sazk|viagra|cialis|pharma|porn|xxx|sex|erotic|escort|loan|pujck|kratom|cbd|hazard|bonus|crypto|gift.?card|amazon|discount|instant", re.I)
FIRST = {"doplnky", "kuchyne", "obchod", "produkt", "kategorie", "shop", "product", "product-category", "nabytek", "svitidla", "koupelna", "zahrada", "textil"}


def target(slugtext):
    cat = X.classify({"t": slugtext})
    if cat and cat in live:
        return f"/{cat}/", 3
    room = X.CATS[cat][1] if cat in X.CATS else None
    return (f"/{room}/", 2) if room in X.ROOMS else (None, 0)


def main():
    rules, stats = {}, Counter()
    for path in (APP / "data/old-urls.txt").read_text().split("\n"):
        path = path.strip()
        if not path or path == "/":
            continue
        if SKIP.search(path) or SPAM.search(path):
            stats["skipped"] += 1
            continue
        clean = path.split("?")[0].rstrip("/") or "/"
        segs = [s for s in clean.split("/") if s]
        if not segs or re.fullmatch(r"\d+", segs[-1]):
            stats["numeric-or-empty"] += 1
            continue
        if segs[0] == "brand" and len(segs) >= 2:
            rules[path.split("?")[0]] = (f"/znacky/{segs[1]}/", 4)
            stats["brand"] += 1
            continue
        if segs[0] in FIRST and len(segs) > 1:
            segs = segs[1:]
        slugtext = " ".join(segs[-1].split("-"))
        to, score = target(slugtext)
        if not to:
            stats["unclassified"] += 1
            continue
        src = clean + "/"
        rules[src] = (to, score)
        stats["product" if len(segs[-1]) > 22 else "category-ish"] += 1
    # old short category-like slugs first (they carried the links), then brands, then product slugs; cap
    order = sorted(rules.items(), key=lambda kv: (-(kv[1][1] == 4), len(kv[0].strip("/")) > 22, kv[0]))
    out = [f"{s} {t} 301" for s, (t, _) in order[:LIMIT]]
    (APP / "data/redirects.txt").write_text("# Old vian.cz URLs -> live categories (scripts/redirect_map.py; rules above 2 000 are not emitted).\n" + "\n".join(out) + "\n")
    print(dict(stats), "rules:", len(rules), "written:", len(out))
    if "report" in sys.argv:
        for s, (t, sc) in order[:40]:
            print(s, "->", t)
        tops = Counter(t for _, (t, _) in rules.items()).most_common(12)
        print(tops)


main()
