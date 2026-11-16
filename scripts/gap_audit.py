#!/usr/bin/env python3
"""Content gap audit: which searched phrases have no category / subcategory page on vian, or land on the wrong one.

    python3 scripts/gap_audit.py --fetch     # MM: keyword_suggestions for content/keywords/seeds4.txt + content gaps
    python3 scripts/gap_audit.py             # report from the cache

Phrases come from content/keywords/universe.tsv (round 1), the seeds4 suggestions and the competitor content gaps. Each
phrase goes through the same rules as product titles (taxonomy.title_class, subcats.sub_of):
  * no category        -> candidate for a new category (clustered by the first word)
  * category, no sub   -> candidate for a new subcategory (clustered by category)
Raw MM data stay local (content/keywords/ is gitignored: the repo is public). Runs on the workspace machine (MM creds)."""
import collections
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/kenny/ai/bin")
import subcats as S  # noqa: E402
import taxonomy as T  # noqa: E402
from taxonomy import fold  # noqa: E402

APP = Path(__file__).resolve().parent.parent
KW = APP / "content/keywords"
CACHE = KW / "gap4-mm.json"
GAPS = KW / "gap4-competitors.json"
COMPETITORS = ["bonami.cz", "4home.cz", "homein.cz", "decodoma.cz", "mydepot.cz", "butlers.cz", "westwing.cz",
               "tescoma.cz", "dumdekorace.cz", "kika.cz", "ikea.com", "jysk.cz", "sconto.cz", "mobelix.cz", "xxxlutz.cz",
               "favi.cz", "biano.cz", "asko-nabytek.cz", "nabytek-forliving.cz", "bauhaus.cz"]
SKIP_INTENT = {"brand-nav", "question", "size", "color", "price"}
NOISE = re.compile(r"\b(recept|navod|jak |co je|bazar|inspirac|praha|brno|ostrava|olomouc|jidelna|kolik|zdarma|"
                   r"vyprodej|akce|levn|ikea|jysk|sconto|xxxlutz|mobelix|bonami|4home|favi|biano|hornbach|obi|bauhaus|"
                   r"lidl|kaufland|tesco|albert|pepco|action|mall|alza|heureka|diy|vyroba|hackovan|pletene|omalovank)")


def mm_retry(tool, args):
    import mm
    err = None
    for _ in range(3):
        try:
            return mm.call(tool, args)
        except Exception as e:  # noqa: BLE001
            err = e
    print(f"  ! {tool} {args}: {err}", file=sys.stderr)
    return None


def fetch():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    seeds = [s.strip() for s in (KW / "seeds4.txt").read_text().splitlines() if s.strip() and s.strip() not in cache]
    print(f"MM: {len(seeds)} seeds", file=sys.stderr)
    with ThreadPoolExecutor(4) as pool:
        for s, d in zip(seeds, pool.map(lambda s: mm_retry("keyword_suggestions", {"lang": "cs", "keyword": s, "limit": 100,
                                                                                    "with_keyword_data": True}), seeds)):
            if d:
                cache[s] = [(k["keyword"], k.get("search_volume") or 0) for k in d["data"]["keywords"]]
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    gaps = json.loads(GAPS.read_text()) if GAPS.exists() else {}
    todo = [c for c in COMPETITORS if c not in gaps]
    with ThreadPoolExecutor(4) as pool:
        for c, d in zip(todo, pool.map(lambda c: mm_retry("website_content_gap", {"lang": "cs", "type": "domain", "target": "vian.cz",
                                                                                   "other_domain_1": c, "limit": 100}), todo)):
            if d:
                gaps[c] = [(r["keyword"], r.get("search_volume") or 0) for r in d["data"]["websites"]]
    GAPS.write_text(json.dumps(gaps, ensure_ascii=False, indent=0))


def phrases():
    out = {}
    for line in (KW / "universe.tsv").read_text().splitlines()[1:]:
        f = line.split("\t")
        if f[3] not in SKIP_INTENT:
            out[f[0]] = int(f[1] or 0)
    for src in (CACHE, GAPS):
        if src.exists():
            for rows in json.loads(src.read_text()).values():
                for k, v in rows:
                    out[k] = max(out.get(k, 0), v)
    return {k: v for k, v in out.items() if not NOISE.search(fold(k))}


def main():
    if "--fetch" in sys.argv:
        fetch()
    new, sub = collections.defaultdict(list), collections.defaultdict(list)
    for k, v in phrases().items():
        if v < 100:
            continue
        cat, _ = T.title_class({"t": k})
        if cat == T.VETOED:
            continue
        if not cat:
            new[fold(k).split()[0]].append((v, k))
        elif not S.sub_of({"name": k, "cat": cat}):
            sub[cat].append((v, k))
    print("## Without a category (first word, total volume, top phrases)")
    for w, rows in sorted(new.items(), key=lambda kv: -sum(v for v, _ in kv[1]))[:120]:
        rows.sort(reverse=True)
        print(f"{sum(v for v, _ in rows)}\t{w}\t" + ", ".join(f"{k} {v}" for v, k in rows[:6]))
    print("\n## Category without a subcategory")
    for c, rows in sorted(sub.items(), key=lambda kv: -sum(v for v, _ in kv[1]))[:70]:
        rows.sort(reverse=True)
        print(f"{sum(v for v, _ in rows)}\t{c}\t" + ", ".join(f"{k} {v}" for v, k in rows[:10]))


if __name__ == "__main__":
    main()
