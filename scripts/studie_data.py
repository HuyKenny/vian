"""derive functions of the data studies: state["agg"] (daily aggregates, scripts/catalog.py collect_study_data) -> numbers for scripts/studie.py."""
from datetime import date

import studie as ST
import taxonomy as X

MIN_ELIG = 500      # products with >= 7 days of our own price observations needed before "unseen original price" is quoted
MIN_MULTI = 1000    # products sold by 2+ shops needed before the shop spread is quoted
CAT_MIN = 150       # products in 2+ shops for a category row in the table


def cz(n, d=1):
    return f"{n:.{d}f}".replace(".", ",")


def num(n):
    return f"{n:,}".replace(",", " ")


def black_friday(agg):
    days = sorted(int(k) for k in agg if "multi" in agg[k])
    if len(days) < 2:
        return None
    last = agg[str(days[-1])]
    if last["multi"] < MIN_MULTI:
        return None
    day = lambda k: date.fromordinal(k)
    label = lambda k: f"{day(k).day}. {day(k).month}."
    first = day(days[0])
    share = lambda a: a["claim"] / a["n"] * 100 if a["n"] else 0
    sp10 = lambda a: a["sp10"] / a["multi"] * 100 if a["multi"] else 0
    ser = {"S uvedenou slevou": [(label(k), round(share(agg[str(k)]), 1)) for k in days],
           "Rozdíl obchodů ≥ 10 %": [(label(k), round(sp10(agg[str(k)]), 1)) for k in days]}
    have_unseen = last["elig"] >= MIN_ELIG
    unseen_share = last["unseen"] / last["elig"] * 100 if have_unseen else 0
    v = {"n": num(last["n"]), "claim": num(last["claim"]), "share": cz(share(last)), "med": last["med"], "p25": last["p25"], "p75": last["p75"],
         "first": f"{first.day}. {first.month}. {first.year}", "days": len(days), "last": f"{day(days[-1]).day}. {day(days[-1]).month}. {day(days[-1]).year}",
         "unseen": cz(unseen_share), "elig": num(last["elig"]),
         "multi": num(last["multi"]), "sp_med": last["sp_med"], "sp10": cz(sp10(last)), "sp20": cz(last["sp20"] / last["multi"] * 100),
         "kc_med": num(last["kc_med"]), "kc_p75": num(last["kc_p75"]),
         "unseen_sentence": (f"U {cz(unseen_share)} % těchto slev je uváděná původní cena vyšší než jakákoli nejnižší cena, kterou jsme u produktu za posledních 14 dní viděli."
                             if have_unseen else "Zatím nemáme dost dlouhou historii, abychom mohli říct, u kolika slev byla původní cena skutečně k vidění.")}
    cats = sorted(((X.TREE[c][0], r) for c, r in last["cat"].items() if c in X.TREE and r[3] >= CAT_MIN), key=lambda t: -t[1][5])
    rows = [[name, num(r[3]), f"{r[4]} %", f"{num(r[5])} Kč", f"{cz(r[1] / r[0] * 100)} %" if r[0] else "–"] for name, r in cats]
    rows_csv = [[day(k).isoformat(), agg[str(k)]["n"], agg[str(k)]["claim"], agg[str(k)]["med"], agg[str(k)]["elig"], agg[str(k)]["unseen"],
                 agg[str(k)]["multi"], agg[str(k)]["sp_med"], agg[str(k)]["sp10"], agg[str(k)]["kc_med"]] for k in days]
    return {"vars": v, "updated": v["last"], "updated_iso": day(days[-1]).isoformat(), "coverage": f"{first.isoformat()}/{day(days[-1]).isoformat()}",
            "chart_html": ST.line_chart(ser, aria="Vývoj podílu nábytku s uvedenou slevou a s rozdílem cen mezi obchody"),
            "table_head": ["Kategorie", "Kusů ve 2+ obchodech", "Medián rozdílu", "Medián rozdílu v Kč", "Podíl s uvedenou slevou"], "table_rows": rows,
            "csv_head": ["datum", "produktu", "s_uvedenou_slevou", "median_slevy_procent", "produktu_s_historii_7_dni", "pocet_s_nevidenou_puvodni_cenou",
                         "produktu_ve_2_a_vice_obchodech", "median_rozdilu_procent", "rozdil_aspon_10_procent", "median_rozdilu_kc"],
            "csv_rows": rows_csv}
