#!/usr/bin/env python3
"""Search demand for the candidate subcategories (scripts/subcats.py) from Marketing Miner.

    python3 scripts/subcat_gap.py            # fetch missing seeds (1 MM query each), print the table
    python3 scripts/subcat_gap.py --report   # table only, from the cache

One keyword_suggestions call per subcategory (seed = its menu name). The demand of a subcategory = the sum of the
suggested phrases that its own product rule matches (singular, plural, without diacritics, "zástěna do sprchy"...).
Raw MM data stay local (content/keywords/ is gitignored: the repo is public). Runs on the workspace machine, not in CI
(the MM credentials live in ~/ai/credentials)."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/kenny/ai/bin")
import subcats as S  # noqa: E402
from taxonomy import fold  # noqa: E402

APP = Path(__file__).resolve().parent.parent
CACHE = APP / "content/keywords/subcats-mm.json"


def fetch(seed):
    import mm
    for attempt in range(3):
        try:
            d = mm.call("keyword_suggestions", {"lang": "cs", "keyword": seed, "limit": 50})
            return [(k["keyword"], k.get("search_volume") or 0) for k in d["data"]["keywords"]]
        except Exception as e:  # noqa: BLE001
            err = e
    print(f"  ! {seed}: {err}", file=sys.stderr)
    return None


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [s for s in S.SUBCATS if s not in cache]
    if todo and "--report" not in sys.argv:
        print(f"MM: {len(todo)} queries", file=sys.stderr)
        with ThreadPoolExecutor(4) as pool:
            for s, rows in zip(todo, pool.map(lambda s: fetch(S.SUBCATS[s][0].lower()), todo)):
                if rows is not None:
                    cache[s] = rows
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    out = []
    for s, (name, parent, h1, rx) in S.SUBCATS.items():
        rows = [(k, v) for k, v in cache.get(s, []) if rx.search(fold(k).replace("-", " "))]
        rows.sort(key=lambda r: -r[1])
        out.append((sum(v for _, v in rows), s, parent, rows[:3]))
    out.sort(key=lambda r: -r[0])
    print("demand\tsubcategory\tparent\ttop phrases")
    for v, s, parent, top in out:
        print(f"{v}\t{s}\t{parent}\t" + ", ".join(f"{k} {n}" for k, n in top))


if __name__ == "__main__":
    main()
