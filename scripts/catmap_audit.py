#!/usr/bin/env python3
"""Report on the shop category paths that the classifier could not settle (data/state/catmap-report.tsv from the last build).

    python3 scripts/catmap_audit.py [min_products=25]

Prints (and writes reports to stdout only) the shop categories with many products and NO clean category of ours: either one of our categories is
missing (the titles all say the same thing, top share high, but no category matches) or the shop category is mixed. Suggests a data/catmap.json line
when the titles agree (top share >= 0.7) and a taxonomy.CATS candidate name when 'top by titles' is empty (our taxonomy has nothing for it)."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 25
rows = list(csv.DictReader(open(APP / "data/state/catmap-report.tsv"), delimiter="\t"))
unclean = [r for r in rows if r["clean -> our category"] == "-" and int(r["titled products"]) >= MIN]
unclean.sort(key=lambda r: -int(r["titled products"]))
missing, mixed = [], []
for r in unclean:
    (missing if not r["top by titles"] else mixed).append(r)
print(f"{len(rows)} shop categories, {len(unclean)} with >= {MIN} products and no clean category of ours")
print("\n== nothing in our taxonomy matches the titles (candidates for NEW categories)")
for r in missing[:60]:
    print(f"{r['titled products']:>5}  {r['shop']:18} {r['shop category'][:70]:70}  e.g. {r['examples'][:90]}")
print("\n== mixed shop categories (titles decide per product; suggestion = catmap line when one category dominates)")
by = defaultdict(int)
for r in mixed[:80]:
    share = float(r["top share"] or 0)
    sug = f'  -> catmap "{r["top by titles"]}"' if share >= 0.7 else ""
    print(f"{r['titled products']:>5}  {r['shop']:18} {r['shop category'][:60]:60} top={r['top by titles']} {share}{sug}")
