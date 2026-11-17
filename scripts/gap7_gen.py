#!/usr/bin/env python3
"""Content gap round 7 (Favi/Biano top pages by traffic, Ahrefs 17. 11. 2026) -> content/landings/gap7.json

    python3 scripts/gap7_gen.py

Favi earns much of its traffic on "category x property" pages our generated families do not have:
wooden / Christmas / on wheels / corner / wall-mounted / folding / kids' / concrete / fabric (dřevěný regál, vánoční
talíře, stolek na kolečkách, rohový regál, dětský toaletní stolek…). This writes one record per category x facet plus
hand-picked phrase pages from the gap. The build keeps a record only with enough products (min / index_min) and,
because group "gap7" is evaluated after kw2 with dedupe_all, only when no existing page already shows the same products.
Raw Ahrefs data stay in the private workspace (reports/vian/kw-2026-11/gap7/)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import landings as L  # noqa: E402
import subcats as S  # noqa: E402
import taxonomy as X  # noqa: E402

APP = Path(__file__).resolve().parent.parent
KIDS = {c for c in X.CATS if c.startswith(("detsk", "detsky"))} | {"pro-miminka", "ucici-veze", "domecky-a-teepee", "detska-hriste", "trampoliny",
                                                                    "patrove-postele", "prebalovaci-pulty", "detska-svitidla", "detske-dekorace"}
XMAS = {"vanocni-dekorace", "vanocni-osvetleni", "vanocni-ozdoby", "adventni-dekorace", "betlemy", "umele-stromky"}

FULL_NAME = {"knihovny-a-regaly", "ulozne-boxy-a-kose", "taburety-a-sedaci-vaky"}     # "Rohové knihovny a regály", not just "knihovny"
NOUN = {"akusticke-panely": "Akustické panely", "houpaci-kresla": "Houpací křesla", "skladove-regaly": "Skladové regály", "koupelnove-skrinky": "Koupelnové skříňky"}
NO_FACETS = {"wc-a-bidety", "pvc-a-linoleum", "pro-miminka", "zavlazovani", "substraty-a-hnojiva", "uprava-vzduchu"}
WALL = {"venkovni-svitidla", "koupelnova-svitidla", "detska-svitidla", "vodovodni-baterie", "kuchynske-baterie"}    # "nástěnná svítidla", not "závěsná"


def h1_for(stem, cat, noun):
    """Adjective + noun with the right plural ending: šedé sedačky, šedá křesla, šedý textil, šedé náčiní."""
    if stem.endswith(("#", "*")):
        return L.phrase(stem, cat, noun)
    words = noun.split()
    head = next((w.lower() for w in words if not w.lower().endswith(("í", "é", "ý", "á"))), None)
    if head in ("nábytek", "textil"):
        end = "ý"
    elif head and head.endswith("a"):
        end = "á"
    else:
        end = "é"
    pre = stem + ("" if stem.endswith("í") else end)
    return pre[:1].upper() + pre[1:] + " " + (noun if noun[:2].isupper() else noun[:1].lower() + noun[1:])

# slug, adjective stem for landings.phrase ('*' indeclinable, '#' after the noun), title regex, categories to skip
# (the category itself is that thing, or a subcategory / kw2 page already covers it)
FACETS = [
    ("drevene", "dřevěn", r"\bdreven\w*|\bz dreva\b", {"drevene-podlahy", "potahy-na-nabytek", "uklidove-pomucky", "led-panely", "kliky-a-kovani", "biokrby", "laminatove-podlahy", "vinylove-podlahy", "pvc-a-linoleum", "podlahove-listy",
                                                              "sauny", "krbova-kamna", "grily", "substraty-a-hnojiva"}),
    ("vanocni", "vánoční*", r"\bvanoc\w*|\bchristmas\b|\bxmas\b|\bsnehulak\w*|\bsob(i|ik\w*)?\b|\bjezisk\w*|\bmikulas\w*", XMAS | {"povleceni", "tapety"}),
    ("na-koleckach", "na kolečkách#", r"\bna kolec\w*|\bs kolec\w*|\bkolecka\b|\bpojizdn\w*", {"kancelarske-zidle", "herni-kresla", "servirovaci-stolky",
                                                                                       "vysavace", "popelnice", "zehlici-prkna"}),
    ("rohove", "rohov", r"\brohov\w*|\bdo rohu\b", {"rohove-sedacky", "kuchynske-linky", "umyvadla", "vany", "satni-skrine", "police", "psaci-stoly",
                                                    "sprchove-kouty", "sprchove-vanicky", "lavice", "komody", "podlahove-listy", "sedacky",
                                                    "potahy-na-nabytek", "led-pasky", "sprchove-sety", "topne-zebriky"}),
    ("zavesne", "závěsn", r"\bzavesn\w*|\bnasten\w*|\bna zed\b|\bna stenu\b", {"lustry", "kvetinace", "police", "tv-stolky", "hodiny", "wc-a-bidety",
                                                                               "nastenne-dekorace", "nastenna-svitidla", "obrazy", "vesaky", "samolepky-na-zed",
                                                                               "tapety", "nastenky-a-tabule", "houpacky-a-site", "nocni-stolky", "topne-zebriky",
                                                                               "vesaky-na-klice", "vesaky-na-rucniky", "ramy-na-fotky", "kryty-na-radiatory",
                                                                               "postovni-schranky", "led-panely", "bodova-svitidla", "zrcadla", "koupelnova-zrcadla",
               "stropni-svitidla", "sprchove-sety", "garnyze", "sosky-a-doplnky", "vanocni-osvetleni", "stolni-lampy", "stinidla", "led-pasky", "kliky-a-kovani",
               "nabytkove-uchytky", "rosty", "rolety-a-zaluzie", "vany", "kuchynske-linky", "akusticke-panely", "sprchove-kouty", "termosky-a-lahve", "hrnce",
               "rucniky-a-osusky", "lavice", "vanocni-ozdoby", "zahradni-zidle", "kuchynske-nacini", "konferencni-stolky", "svicky-a-svicny", "stojany-na-saty"}),
    ("skladaci", "skládací*", r"\bskladac\w*|\bskladatel\w*", {"zahradni-zidle", "sklapeci-postele", "matrace", "lehatka", "kresla", "paravany"}),
    ("detske", "dětsk", r"\bdetsk\w*|\bpro deti\b|\bpro holcic\w*|\bpro kluk\w*", KIDS | XMAS | {"taburety-a-sedaci-vaky", "tapety", "matrace", "koberce",
                                                                                                 "samolepky-na-zed", "pribory", "detske-pokoje", "postele", "psaci-stoly", "povleceni", "jidelni-zidle", "stolni-lampy",
                                                                                                 "stropni-svitidla", "lustry", "satni-skrine", "komody", "knihovny-a-regaly"}),
    ("betonove", "betonov", r"\bbeton\w*", {"biokrby"}),
    ("latkove", "látkov", r"\blatkov\w*|\btextiln\w*|\bz latky\b", {"kuchynsky-textil", "ubrusy-a-prostirani", "behouny-a-predlozky", "rucniky-a-osusky",
                                                                      "prosteradla", "deky-a-prehozy", "dekorativni-polstare", "zaclony-a-zavesy", "detsky-textil",
                                                                      "koberce", "rosty", "koberce-metraz", "detske-povleceni"}),
]

# hand-picked phrase pages from the gap: slug, h1, categories (or rooms), all-regexes, monthly traffic of the competitor page (evidence)
PHRASES = [
    ("regaly-do-koupelny", "Regály do koupelny", ["knihovny-a-regaly", "koupelnove-skrinky", "skladove-regaly"], [r"\bregal\w*", r"\bkoupel\w*"], 1935),
    ("regaly-na-hracky", "Regály a organizéry na hračky", ["knihovny-a-regaly", "detske-skrine-a-ulozne-boxy", "ulozne-boxy-a-kose"], [r"\bhrac(ky|ek|kam)\b|\bna hracky\b"], 1407),
    ("adventni-svicny", "Adventní svícny", ["svicky-a-svicny", "adventni-dekorace", "vanocni-dekorace"], [r"\bsvic(en|n)\w*", r"\badvent\w*"], 1467),
    ("vanocni-vence", "Vánoční věnce", ["adventni-dekorace", "vanocni-dekorace"], [r"\bven(ec|ce|cek|ecek|cky)\b"], 1388),
    ("sady-taliru", "Sady talířů a jídelní servisy", ["talire"], [r"\bsad[auy]\b|\bsouprav\w*|\bservis\w*|\bset\b"], 1128),
    ("vanocni-svicny-do-okna", "Vánoční svícny do okna", ["svicky-a-svicny", "vanocni-osvetleni", "vanocni-dekorace"], [r"\bsvic(en|n)\w*", r"\bokn\w*|\boken\b|\boblouk\w*"], 1126),
    ("zabrany-na-postel", "Zábrany na postel", None, [r"\bzabran\w* (na|k|pro) (postel|postyl|luzk)\w*|\bzabran\w* postele\b"], 976),
    ("vanocni-flanelove-povleceni", "Vánoční flanelové povlečení", ["povleceni", "detske-povleceni"], [r"\bvanoc\w*", r"\bflanel\w*"], 972),
    ("sperkovnice-se-zrcadlem", "Šperkovnice se zrcadlem", ["ulozne-boxy-a-kose", "toaletni-stolky", "zrcadla"], [r"\bsperkovnic\w*", r"\bzrcad\w*"], 913),
    ("valendy", "Válendy", ["postele", "detske-postele", "sklapeci-postele"], [r"\bvalend\w*|\bvaland\w*"], 847),
    ("pitka-pro-ptaky", "Pítka a koupátka pro ptáky", ["zahradni-dekorace"], [r"\bpitk\w*|\bkoupatk\w*|\bnapajed\w*"], 782),
    ("detske-koberce-silnice", "Dětské koberce se silnicí", ["detske-koberce", "koberce"], [r"\bsilnic\w*|\bulic\w*|\bmesto\b|\bautodrah\w*|\bcest[ay]\b"], 788),
    ("truhly-na-hracky", "Truhly a boxy na hračky", ["truhly", "detske-skrine-a-ulozne-boxy", "ulozne-boxy-a-kose"], [r"\bhrac(ky|ek|kam)\b"], 762),
    ("koupelnove-sestavy", "Koupelnové sestavy", ["koupelnove-skrinky", "umyvadla"], [r"\bsestav\w*|\bset\b|\bkomplet\w*"], 708),
    ("pokladnicky", "Pokladničky", None, [r"\bpokladnic\w*|\bpokladnick\w*"], 655),
    ("police-do-kuchyne", "Police a poličky do kuchyně", ["police", "kuchynske-doplnky", "skladovani-potravin"], [r"\bpolic\w*", r"\bkuchyn\w*|\bkoren\w*"], 616),
    ("detske-sedaci-vaky", "Dětské sedací vaky", ["taburety-a-sedaci-vaky", "detske-stolky-a-zidle"], [r"\bvak\w*|\bpytel\b|\bpuf\w*", r"\bdetsk\w*|\bpro deti\b"], 596),
    ("postel-140x200-s-matraci-a-rostem", "Postele 140×200 s matrací a roštem", ["postele", "calounene-postele", "boxspringy"], [r"\b140 ?x ?200\b", r"\bmatrac\w*", r"\brost\w*"], 584),
    ("postel-180x200-s-matraci-a-rostem", "Postele 180×200 s matrací a roštem", ["postele", "calounene-postele", "boxspringy"], [r"\b180 ?x ?200\b", r"\bmatrac\w*", r"\brost\w*"], 565),
    ("postel-90x200-s-matraci-a-rostem", "Postele 90×200 s matrací a roštem", ["postele", "calounene-postele", "detske-postele"], [r"\b90 ?x ?200\b", r"\bmatrac\w*", r"\brost\w*"], 192),
    ("barove-pulty", "Barové pulty", ["barove-stoly", "kuchynske-ostruvky"], [r"\bpult\w*"], 405),
    ("misy-na-ovoce", "Mísy na ovoce", ["talire", "tacy-a-podnosy", "kuchynske-doplnky"], [r"\bovoc\w*"], 558),
    ("policky-do-koupelny-bez-vrtani", "Poličky do koupelny bez vrtání", ["police", "koupelnove-doplnky"], [r"\bbez vrtan\w*|\bprisav\w*|\bsamolepic\w*|\bsamodrzic\w*"], 553),
    ("drevene-bedny", "Dřevěné bedny a bedýnky", ["truhly", "ulozne-boxy-a-kose", "sosky-a-doplnky"], [r"\bbedn\w*|\bbedyn\w*|\bbedynk\w*"], 538),
    ("skrinky-na-wc", "Skříňky na WC", ["koupelnove-skrinky"], [r"\bwc\b|\btoalet\w*|\bnad (wc|zachod)\w*"], 536),
    ("stojany-na-rucniky", "Stojany na ručníky", ["vesaky-na-rucniky", "koupelnove-doplnky", "topne-zebriky"], [r"\bstojan\w*"], 530),
    ("stojany-na-vanocni-stromek", "Stojany na vánoční stromek", None, [r"\bstojan\w* (na|pro|pod) (vanocni )?strom\w*"], 529),
    ("stojany-na-drevo", "Stojany a koše na dřevo ke krbu", None, [r"\b(stojan|kos|kose|regal|nosic|drzak|box)\w* na (palivov\w* )?drev\w*|\bdrevnik\w*"], 660),
    ("zrcadla-s-polickou", "Zrcadla s poličkou", ["zrcadla", "koupelnova-zrcadla"], [r"\bs polic\w*|\bpolick\w*"], 577),
    ("vanocni-girlandy", "Vánoční girlandy", ["vanocni-dekorace", "vanocni-ozdoby", "vanocni-osvetleni", "adventni-dekorace"], [r"\bgirland\w*"], 506),
    ("kancelarske-kontejnery", "Kancelářské kontejnery", ["kancelarske-skrine", "psaci-stoly"], [r"\bkontejner\w*"], 467),
    ("koupelnove-skrinky-s-kosem-na-pradlo", "Koupelnové skříňky s košem na prádlo", ["koupelnove-skrinky", "kose-na-pradlo"], [r"\bskrin\w*|\bkomod\w*|\bregal\w*", r"\bkos\w* na pradlo\b|\bpradl\w*"], 467),
    ("beranky-deky", "Beránkové deky", ["deky-a-prehozy"], [r"\beran\w*|\bsherpa\b"], 453),
    ("nastenne-kvetinace", "Nástěnné květináče", ["kvetinace"], [r"\bnasten\w*|\bna zed\b|\bna stenu\b"], 448),
    ("korenky", "Kořenky a stojany na koření", ["skladovani-potravin", "kuchynske-doplnky", "kuchynske-nacini", "solnicky-a-mlynky"], [r"\bkoren\w*"], 439),
    ("boxy-na-kapesniky", "Boxy na kapesníky", None, [r"\b(box|krabick|zasobnik|obal|dozn?)\w* na (papirov\w* )?kapesnik\w*|\bkapesnikov\w*"], 428),
    ("koberce-300x400", "Koberce 300×400 cm", ["koberce", "kusove-koberce"], [r"\b300 ?x ?400\b|\b400 ?x ?300\b"], 458),
    ("koberce-300x300", "Koberce 300×300 cm", ["koberce"], [r"\b300 ?x ?300\b"], 40),
    ("podlahove-vazy", "Podlahové vázy", ["vazy"], [r"\bpodlahov\w*|\bna zem\b|\bvysok\w*|\bvelk\w*"], 460),
    ("zahradni-kuchyne", "Zahradní kuchyně", None, [r"\b(zahradn|venkovn|outdoor)\w* kuchyn\w*|\bkuchyn\w* (na|do) zahrad\w*"], 406),
    ("stojany-na-noviny", "Stojany na noviny a časopisy", None, [r"\b(stojan|kos|regal|drzak|box)\w* na (noviny|casopis\w*)"], 406),
    ("vanocni-balici-papiry", "Vánoční balicí papíry", None, [r"\bbalic\w* papir\w*", r"\bvanoc\w*"], 392),
    ("organizery-do-skrine", "Organizéry do skříně", ["ulozne-boxy-a-kose", "satni-systemy", "satni-skrine"], [r"\borganizer\w*|\borganizac\w*"], 390),
    ("retro-rychlovarne-konvice", "Retro rychlovarné konvice", ["rychlovarne-konvice"], [r"\bretro\b|\bvintage\b|\bnostalg\w*"], 287),
    ("kulate-podsedaky", "Kulaté podsedáky", ["polstare-na-zahradni-nabytek", "dekorativni-polstare", "jidelni-zidle"], [r"\bpodsedak\w*|\bsedak\w*", r"\bkulat\w*|\bkruh\w*"], 123),
    ("vanocni-projektory", "Vánoční projektory", ["vanocni-osvetleni", "dekoracni-osvetleni", "venkovni-svitidla"], [r"\bprojektor\w*|\bprojekc\w*"], 85),
    ("teflonove-ubrusy", "Teflonové ubrusy", ["ubrusy-a-prostirani"], [r"\bteflon\w*|\bnesmacivy\w*|\bnesmaciv\w*|\bomyvatel\w*"], 82),
    ("smaltovane-konvice", "Smaltované konvice", ["hrnky-a-salky", "rychlovarne-konvice", "hrnce", "kuchynske-nacini"], [r"\bsmalt\w*", r"\bkonvic\w*"], 81),
    ("markyzy-bez-vrtani", "Markýzy na balkon bez vrtání", ["markyzy", "slunecniky-a-zasteny"], [r"\bbez vrtan\w*|\bupinac\w*|\bvzpern\w*|\bstojan\w*"], 69),
    ("povleceni-se-srdicky", "Povlečení se srdíčky", ["povleceni", "detske-povleceni"], [r"\bsrdic\w*|\bsrdc\w*|\bheart\w*"], 69),
    ("bodovky-do-koupelny", "Bodová světla do koupelny", ["bodova-svitidla", "koupelnova-svitidla", "stropni-svitidla"], [r"\bkoupel\w*|\bip ?44\b|\bip ?65\b"], 62),
    ("hodiny-do-kuchyne", "Hodiny do kuchyně", ["hodiny"], [r"\bkuchyn\w*|\bkuchar\w*|\bkav[ay]\b|\bpribor\w*"], 54),
    ("detske-zupany", "Dětské župany", ["rucniky-a-osusky", "detsky-textil"], [r"\bzupan\w*", r"\bdetsk\w*|\bpro deti\b|\bholcic\w*|\bchlapec\w*"], 49),
    ("rolety-do-pergoly", "Rolety a stínění do pergoly", ["rolety-a-zaluzie", "pergoly-a-altany", "markyzy", "slunecniky-a-zasteny"], [r"\bpergol\w*"], 47),
    ("boxy-na-kosmetiku", "Boxy a organizéry na kosmetiku", ["ulozne-boxy-a-kose", "koupelnove-doplnky", "toaletni-stolky"], [r"\bkosmetik\w*|\blicid\w*|\bmake ?up\b"], 44),
    ("sklenice-na-kavu", "Skleničky na kávu", ["sklenice", "hrnky-a-salky"], [r"\bkav\w*|\blatte\b|\bcappuccin\w*|\bespress\w*"], 41),
    ("povleceni-s-dinosaury", "Povlečení s dinosaury", ["detske-povleceni", "povleceni"], [r"\bdinosaur\w*|\bdino\b"], 45),
]


def main():
    recs = []
    for cat, meta in sorted(X.CATS.items()):
        if cat in NO_FACETS:
            continue
        noun = NOUN.get(cat) or (meta[0] if cat in FULL_NAME else meta[0].split(" a ")[0])
        for slug, stem, rx, skip in FACETS:
            if cat in skip:
                continue
            if slug == "zavesne" and cat in WALL:
                stem = "nástěnn"
            h1 = h1_for(stem, cat, noun)
            recs.append({"slug": f"{cat}/{slug}", "h1": h1, "parent": f"/{cat}/", "cat": cat, "hubs": [f"/{cat}/"], "group": "gap7", "dedupe_all": True,
                         "rules": {"cat": [cat], "any": [rx]}, "min": 8, "index_min": 12, "title": f"{h1} – srovnání cen"})
    for slug, h1, cats, alls, ev in PHRASES:
        rules = {"all": alls}
        if cats:
            rules["cat"] = cats
        r = {"slug": slug, "h1": h1, "group": "gap7", "dedupe_all": True, "rules": rules, "min": 6, "index_min": 10, "evidence": ev,
             "title": f"{h1} – srovnání cen"}
        if cats:
            r.update({"parent": f"/{cats[0]}/", "cat": cats[0], "hubs": [f"/{c}/" for c in cats if c in X.CATS][:3]})
        recs.append(r)
    subs = set(S.SUB_PARENT)
    clash = [r["slug"] for r in recs if r["slug"] in subs or r["slug"] in X.CATS]
    assert not clash, clash
    out = APP / "content/landings/gap7.json"
    out.write_text(json.dumps(recs, ensure_ascii=False, indent=0) + "\n")
    print(f"{len(recs)} records -> {out.relative_to(APP)}")


if __name__ == "__main__":
    main()
