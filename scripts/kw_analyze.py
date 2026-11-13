#!/usr/bin/env python3
"""Keyword universe from the Marketing Miner cache -> content/keywords/universe.tsv + backlog.tsv + a short stats report.

    python3 scripts/kw_analyze.py [sitemap_paths.txt]

sitemap_paths.txt = one live path per line (from sitemap-listings/-landings, saved by the caller); without it every phrase counts as "no page".
Steps: merge phrase variants (diacritics / no diacritics = one intent, volumes summed), drop noise (food, football players, games for PC ...),
classify the intent (question, brand, licence, age/gender, occasion, price, material/feature, comparison, product type), map to an existing
page by stems of the significant words, score the opportunity (volume x ease x season). Nothing here touches the site."""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
CACHE = APP / "content/keywords/cache"
OUT = APP / "content/keywords"


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


STOP = set("pro na do od a s se z ze v ve u k o po za je to jak co ktery kde kdy kolik jaky jake jaka cena cenik levne levny akce sleva".split())
NOISE = re.compile(r"\b(recept|film|filmy|online zdarma|zdarma ke|ke stazeni|stahnout|pdf|hra|hry|steam|ps4|ps5|xbox|minecraft|sex|erotick|pro psy|pro kocky|pro kocku|pro psa|pro zvirata|"
                   r"navod|plan domu|projekt domu|dum na klic|byt na prodej|pronajem|prodej bytu|reality|hypoteka|3d model|blender|sketchup|autocad|dwg|program|aplikace|"
                   r"alza|mall|rohlik|kasa|aukro|bazos|sbazar|pepco|tesco|lidl|kaufland|albert|billa|dm drogerie|hornbach|obi|bauhaus|makro|datart|okay|electroworld|"
                   r"kosmetick|kuchar|jidlo|svatba|pohrb|rakev|nahrobek|truhla pro|zbrane|nabyt|kryptomen)\b")
BRAND_NAV = re.compile(r"\b(favi|biano|ikea|jysk|sconto|mobelix|bonami|asko|kondela|halmar|vox|jena nabytek|nabytek bohemia|baumax|dekoria|westwing|homeroom|kika|leiner|moebelix|conforama|xxxlutz|xxl lutz|maxi nabytek|nabytek pohoda|nabytek tempo|bazar nabytek|sedaci nabytek)\b")
Q = re.compile(r"^(jak|kdy|proc|co|kolik|kde|jaky|jaka|jake|na co|je |jsou |muze|mohu|lze|ma smysl|vyplati)\b|\b(jak vybrat|jak vybirat|jak zaridit|jak poskladat|jak umyt|jak cistit|jak vyrobit|jak vybrat)\b")
ROOM = re.compile(r"\b(obyvak|obyvaci|loznice|loznicov|kuchyn|jidelna|jidelni|koupelna|koupelnov|predsin|pracovna|detsky pokoj|detsk|zahrada|zahradni|balkon|teras|garsonka|maly byt)")
SIZE = re.compile(r"\b(\d{2,3}\s?x\s?\d{2,3}|\d{2,3}\s?cm|\d{2,3}x\d{2,3}|rozmer|sirka|vyska|delka|maly|velky|uzky|siroky)")
COLOR = re.compile(r"\b(bil[aeyý]|cern[aeyý]|sed[aeyý]|bezov|hned|zelen|modr|ruzov|cerven|zlut|oranzov|zlat|stribrn|antracit|dub|ořech|orech|sonoma|wenge)")
MAT = re.compile(r"\b(masiv|dreven|kovov|sklenen|ratan|kozen|ekokuz|latkov|sametov|lnen|bavlnen|vlnen|mramor|bambus|plast|nerez|proutene|pletene)")
STYLE = re.compile(r"\b(skandinav|industrial|loft|retro|vintage|boho|provence|venkovsk|moderni|minimalist|japandi|glamour|rustik)")
FEAT = re.compile(r"\b(rozkladac|uloz|polohovac|led|kulat|kruhov|vyskove stavitel|elektricky|s uloznym|zasuvk|na kolecka|skladac|sklopn|rozkladaci)")
OCC = re.compile(r"\b(vanoc|vanocni|advent|black friday|cerny patek|akce|vyprodej|sleva)")
PRICE = re.compile(r"\b(do \d{3,5}|pod \d{3,5}|levn|nejlevnejsi|za \d{3,5}|za nejlepsi cenu)")
CMP = re.compile(r"\b(nejlepsi|top \d|srovnani|porovnani|recenze|test|vs |versus|rozdil|alternativ|tipy|napady|inspirace|vyber)")
SEASON = {"vanoc": (10, 12), "advent": (9, 11), "black": (10, 11), "zahrad": (3, 7), "bazen": (4, 8), "gril": (4, 8), "slunecnik": (4, 8), "lehatko": (4, 8)}


def stems(text):
    out = []
    for w in re.findall(r"[a-z0-9]+", fold(text)):
        if w in STOP or len(w) < 2:
            continue
        out.append(w[: max(4, len(w) - 2)] if len(w) > 4 else w)
    return out


def load_cache():
    rows = defaultdict(lambda: {"vol": 0, "kd": None, "serp": set(), "seeds": set(), "yoy": None, "msv": None, "variants": {}})
    for f in sorted(CACHE.glob("*.json")):
        d = json.loads(f.read_text())
        kws = (((d.get("data") or {}).get("data") or {}).get("keywords")) or []
        for k in kws:
            key = " ".join(re.findall(r"[a-z0-9]+", fold(k["keyword"])))
            if not key:
                continue
            r = rows[key]
            r["variants"][k["keyword"]] = max(r["variants"].get(k["keyword"], 0), k["search_volume"] or 0)
            r["seeds"].add(d["seed"])
            if k.get("difficulty") is not None and (r["kd"] is None or k["difficulty"] < r["kd"]):
                r["kd"] = k["difficulty"]
            r["serp"] |= set(k.get("serp_features") or [])
            if r["msv"] is None and k.get("monthly_sv"):
                r["msv"], r["yoy"] = k["monthly_sv"], k.get("yoy_change")
    for key, r in rows.items():
        # variants differ only by diacritics: same intent, volume = sum of the variants (the shown phrase is the biggest one with diacritics)
        r["vol"] = sum(r["variants"].values())
        r["phrase"] = max(r["variants"].items(), key=lambda kv: (kv[1], any(ord(c) > 127 for c in kv[0])))[0]
    return rows


def intent(key, phrase):
    if BRAND_NAV.search(key):
        return "brand-nav"
    if Q.search(key):
        return "question"
    tags = []
    for name, rx in (("room", ROOM), ("size", SIZE), ("color", COLOR), ("material", MAT), ("style", STYLE), ("feature", FEAT), ("occasion", OCC), ("price", PRICE), ("compare", CMP)):
        if rx.search(key):
            tags.append(name)
    return "+".join(tags) if tags else "type"


def season_factor(key, msv):
    """Seasonality: share of the yearly volume that falls into the next 8 weeks (Nov-Dec) -> publish now."""
    if not msv:
        return 1.0
    tot = sum(msv.values()) or 1
    near = msv.get("11", 0) + msv.get("12", 0)
    return 1.0 + 1.5 * (near / tot) if near / tot > 0.35 else 1.0


def main():
    rows = load_cache()
    paths = [p.strip("/") for p in Path(sys.argv[1]).read_text().split()] if len(sys.argv) > 1 else []
    page_stems = [(p, set(stems(p.replace("/", " ").replace("-", " ")))) for p in paths if p]
    out, noise = [], 0
    for key, r in rows.items():
        if NOISE.search(key):
            noise += 1
            continue
        st = set(stems(key))
        if not st:
            continue
        best = ""
        for p, ps in page_stems:
            if st <= ps and (not best or len(ps) < len(dict(page_stems)[best])):
                best = p
        it = intent(key, r["phrase"])
        kd = r["kd"]
        ease = 1.0 if kd is None else max(0.2, 1 - kd / 100)
        unknown = kd is None
        score = r["vol"] * (0.6 if unknown else ease) * season_factor(key, r["msv"]) * (0.1 if it == "brand-nav" else 1)
        out.append((key, r, it, best, score))
    out.sort(key=lambda x: -x[4])
    with (OUT / "universe.tsv").open("w") as f:
        f.write("phrase\tvolume\tkd\tintent\tpage\tscore\tserp\tyoy\tseeds\n")
        for key, r, it, best, score in out:
            f.write(f"{r['phrase']}\t{r['vol']}\t{'' if r['kd'] is None else r['kd']}\t{it}\t{best}\t{round(score)}\t{','.join(sorted(r['serp']))}\t{'' if r['yoy'] is None else r['yoy']}\t{len(r['seeds'])}\n")
    gap = [x for x in out if not x[3] and x[2] != "brand-nav" and x[1]["vol"] >= 30]
    with (OUT / "backlog.tsv").open("w") as f:
        f.write("phrase\tvolume\tkd\tintent\tscore\n")
        for key, r, it, best, score in gap[:3000]:
            f.write(f"{r['phrase']}\t{r['vol']}\t{'' if r['kd'] is None else r['kd']}\t{it}\t{round(score)}\n")
    by = defaultdict(lambda: [0, 0, 0, 0])
    for key, r, it, best, score in out:
        b = by[it]
        b[0] += 1
        b[1] += r["vol"]
        if best:
            b[2] += 1
            b[3] += r["vol"]
    print(f"phrases {len(rows)} (noise dropped {noise}); kept {len(out)}; with a page {sum(1 for x in out if x[3])}; gap (vol>=30, no page) {len(gap)}")
    print(f"{'intent':28} {'phrases':>8} {'volume':>9} {'covered':>8} {'cov.vol':>9}")
    for it, b in sorted(by.items(), key=lambda kv: -kv[1][1]):
        print(f"{it:28} {b[0]:8d} {b[1]:9d} {b[2]:8d} {b[3]:9d}")


if __name__ == "__main__":
    main()
