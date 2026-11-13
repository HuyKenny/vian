#!/usr/bin/env python3
"""content/keywords/seeds.txt for scripts/kw_collect.py (one seed per line, optional TAB + questions|new|trending).
Seeds come from what the site knows (rooms, categories sorted by product count, live brands) crossed with the modifiers people type
(colour, material, style, size, "levně", "nejlepší", "jak vybrat"). Order = priority, so a quota-limited run collects the best seeds first."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taxonomy as X  # noqa: E402

APP = Path(__file__).resolve().parent.parent
seeds = []


def add(s, typ=""):
    s = s.strip().lower()
    if s and (s, typ) not in seeds:
        seeds.append((s, typ))


rep = json.loads((APP / "data/state/build-report.json").read_text())
per_cat = rep.get("per_cat", {})
cats = sorted(X.CATS, key=lambda k: -per_cat.get(k, 0))
BIG = [c for c in cats if per_cat.get(c, 0) >= 30][:60]

for r, v in X.ROOMS.items():
    add(v[0]); add(v[1])
for c in cats:
    add(X.CATS[c][0]); add(X.CATS[c][2])
for c in cats[:90]:
    n = X.CATS[c][0]
    add(f"{n} levně"); add(f"nejlepší {n}"); add(f"{n} akce")
    add(f"{n} skladem")
for c in cats[:45]:
    n = X.CATS[c][0]
    add(f"jak vybrat {n}", "questions"); add(f"{n} rozměry")
    add(f"{n} do 3000 kč"); add(f"{n} do 10000 kč")
for _, label, _ in X.COLORS[:10]:
    for c in BIG[:22]:
        add(f"{label} {X.CATS[c][0]}".lower())
for _, label, _ in X.MATERIALS:
    for c in BIG[:14]:
        add(f"{label} {X.CATS[c][0]}")
for _, label, _ in X.STYLES:
    for c in BIG[:18]:
        add(f"{label} {X.CATS[c][0]}")
for _, label, _ in X.FEATURES:
    for c in BIG[:16]:
        add(f"{label} {X.CATS[c][0]}")
for c in ("postele", "matrace", "sedacky", "rohove-sedacky", "jidelni-stoly", "psaci-stoly", "skrine", "komody", "koberce", "kresla"):
    for sz in ("90x200", "140x200", "160x200", "180x200", "200x200", "120x170", "160x230"):
        if c in ("postele", "matrace") or sz in ("120x170", "160x230"):
            add(f"{X.CATS[c][0] if c in X.CATS else c} {sz}")
BRANDS = ["ikea", "sconto", "kondela", "halmar", "asko", "vox", "beliani", "vicco", "sapho", "polysan", "aqualine", "marimex", "springos", "curver", "kitchenaid", "smeg", "weber", "villeroy boch", "tarkett",
          "quick step", "gerflor", "fatra", "artemide", "paulmann", "slv", "philippi", "tulup", "strakoš", "dreamy", "delife", "textilomanie", "elis design", "bpm", "cwf"]
for b in BRANDS:
    add(f"{b} nábytek" if b in ("ikea", "sconto", "kondela", "halmar", "asko", "vox", "beliani", "vicco") else b)
for q in ("jak vybrat sedačku", "jak vybrat matraci", "jak vybrat koberec", "jak vybrat jídelní stůl", "jak vybrat kancelářskou židli", "jak vybrat postel", "jak zařídit malý byt", "jak zařídit obývací pokoj",
          "jak vybrat vinylovou podlahu", "jak vybrat gril", "jak vybrat lustr", "jak vybrat zahradní nábytek", "jak vybrat botník", "jak vybrat šatní skříň", "jak vybrat televizní stolek"):
    add(q, "questions")
for t in ("new", "trending"):
    for s in ("nábytek", "bytové doplňky", "zahradní nábytek", "svítidla", "koberce", "podlahy", "kuchyňské potřeby", "vánoční dekorace"):
        add(s, t)
out = APP / "content/keywords/seeds.txt"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(f"{s}\t{t}\n" if t else f"{s}\n" for s, t in seeds))
print(len(seeds), "seeds ->", out)
