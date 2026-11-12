"""Furniture & home category tree, classifier, colours, materials, styles and dimensions for vian.cz.

The tree is organised like a shopper thinks: by ROOM first (obývák, ložnice, jídelna…), then by piece of furniture.
Category URLs are flat (/sedacky/, /postele/), rooms are hub pages (/obyvaci-pokoj/).

classify(rec) reads the product title first (the most reliable signal across 18 shops with 18 different trees), then
the shop's own category path. Everything is matched on a FOLDED text (lower case, no diacritics), so the patterns
below are written without háčky/čárky. A veto list throws out what is not furniture or home décor (tools, paint,
sanitary ware, cookware, toys, spare parts…). Order matters: specific rules (rohová sedačka, dětská postel,
povlečení NA postel) come before generic ones (sedačka, postel).
"""
import re
import unicodedata

I = re.I


def fold(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"[®™©]", "", s or "")).strip()


def slugify(s):
    s = fold(clean(s).replace("&", " a "))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ------------------------------------------------------------------ tree
# slug: (name, parent room, h1 phrase, short blurb, icon)
ROOMS = {
    "obyvaci-pokoj": ("Obývací pokoj", "Nábytek do obývacího pokoje", "Sedačky, křesla, stolky a obývací stěny", "sofa"),
    "loznice": ("Ložnice", "Nábytek do ložnice", "Postele, matrace, skříně a komody", "postel"),
    "jidelna-a-kuchyne": ("Jídelna a kuchyně", "Nábytek do jídelny a kuchyně", "Jídelní stoly, židle a kuchyňské linky", "jidelna"),
    "pracovna": ("Pracovna", "Nábytek do pracovny a kanceláře", "Psací stoly, kancelářské a herní židle", "pracovna"),
    "detsky-pokoj": ("Dětský pokoj", "Nábytek do dětského pokoje", "Dětské postele, stolky a úložné boxy", "detsky-pokoj"),
    "predsin": ("Předsíň", "Nábytek do předsíně", "Botníky, věšáky a předsíňové stěny", "predsin"),
    "koupelna": ("Koupelna", "Koupelnový nábytek a doplňky", "Skříňky pod umyvadlo, sestavy a doplňky", "koupelna"),
    "zahrada": ("Zahrada a balkon", "Zahradní nábytek", "Sestavy, stoly, lehátka a slunečníky", "zahrada"),
    "svitidla": ("Svítidla", "Svítidla a lampy", "Lustry, stojací a stolní lampy", "lustr"),
    "textil": ("Koberce a textil", "Koberce a bytový textil", "Koberce, záclony, povlečení a deky", "koberec"),
    "dekorace": ("Dekorace", "Bytové dekorace", "Obrazy, zrcadla, vázy a svíčky", "vaza"),
}

CATS = {
    # obývák
    "rohove-sedacky": ("Rohové sedačky", "obyvaci-pokoj", "Rohové sedačky", "kreslo"),
    "sedacky": ("Sedačky", "obyvaci-pokoj", "Sedačky a sedací soupravy", "sofa"),
    "pohovky": ("Pohovky a gauče", "obyvaci-pokoj", "Pohovky a gauče", "sofa"),
    "kresla": ("Křesla", "obyvaci-pokoj", "Křesla", "kreslo"),
    "taburety-a-sedaci-vaky": ("Taburety a sedací vaky", "obyvaci-pokoj", "Taburety, pufy a sedací vaky", "kreslo"),
    "konferencni-stolky": ("Konferenční stolky", "obyvaci-pokoj", "Konferenční a odkládací stolky", "komoda"),
    "tv-stolky": ("TV stolky", "obyvaci-pokoj", "TV stolky a televizní skříňky", "komoda"),
    "obyvaci-steny": ("Obývací stěny", "obyvaci-pokoj", "Obývací stěny a sestavy", "knihovna"),
    "knihovny-a-regaly": ("Knihovny a regály", "obyvaci-pokoj", "Knihovny, regály a police", "knihovna"),
    "vitriny": ("Vitríny", "obyvaci-pokoj", "Vitríny", "knihovna"),
    # ložnice
    "postele": ("Postele", "loznice", "Postele", "postel"),
    "matrace": ("Matrace", "loznice", "Matrace", "postel"),
    "rosty": ("Rošty", "loznice", "Rošty do postele", "postel"),
    "satni-skrine": ("Šatní skříně", "loznice", "Šatní skříně", "skrin"),
    "komody": ("Komody", "loznice", "Komody a prádelníky", "komoda"),
    "nocni-stolky": ("Noční stolky", "loznice", "Noční stolky", "komoda"),
    "toaletni-stolky": ("Toaletní stolky", "loznice", "Toaletní a kosmetické stolky", "komoda"),
    # jídelna a kuchyně
    "jidelni-sety": ("Jídelní sety", "jidelna-a-kuchyne", "Jídelní sety (stůl a židle)", "jidelna"),
    "jidelni-stoly": ("Jídelní stoly", "jidelna-a-kuchyne", "Jídelní stoly", "jidelna"),
    "jidelni-zidle": ("Jídelní židle", "jidelna-a-kuchyne", "Jídelní židle", "jidelna"),
    "barove-zidle": ("Barové židle", "jidelna-a-kuchyne", "Barové židle a stoličky", "jidelna"),
    "lavice": ("Lavice", "jidelna-a-kuchyne", "Jídelní lavice", "jidelna"),
    "kuchynske-linky": ("Kuchyňské linky", "jidelna-a-kuchyne", "Kuchyňské linky a skříňky", "komoda"),
    "servirovaci-stolky": ("Servírovací stolky", "jidelna-a-kuchyne", "Servírovací stolky a vozíky", "jidelna"),
    # pracovna
    "psaci-stoly": ("Psací stoly", "pracovna", "Psací a pracovní stoly", "pracovna"),
    "kancelarske-zidle": ("Kancelářské židle", "pracovna", "Kancelářské židle", "pracovna"),
    "herni-kresla": ("Herní křesla", "pracovna", "Herní křesla a židle", "pracovna"),
    "kancelarske-skrine": ("Kancelářské skříně", "pracovna", "Kancelářské skříně a kontejnery", "skrin"),
    # dětský pokoj
    "detske-postele": ("Dětské postele", "detsky-pokoj", "Dětské postele a postýlky", "detsky-pokoj"),
    "detske-pokoje": ("Dětské pokoje", "detsky-pokoj", "Dětské a studentské pokoje", "detsky-pokoj"),
    "detske-stolky-a-zidle": ("Dětské stolky a židle", "detsky-pokoj", "Dětské stolky a židličky", "detsky-pokoj"),
    "detske-skrine-a-ulozne-boxy": ("Dětské skříně a úložné boxy", "detsky-pokoj", "Dětské skříně, regály a úložné boxy", "detsky-pokoj"),
    "detske-dekorace": ("Dekorace do dětského pokoje", "detsky-pokoj", "Dekorace do dětského pokoje", "detsky-pokoj"),
    # předsíň
    "botniky": ("Botníky", "predsin", "Botníky", "predsin"),
    "vesaky": ("Věšáky", "predsin", "Věšáky a věšákové stěny", "predsin"),
    "predsinove-steny": ("Předsíňové stěny", "predsin", "Předsíňové stěny a skříně do předsíně", "predsin"),
    # koupelna
    "koupelnove-skrinky": ("Koupelnový nábytek", "koupelna", "Koupelnový nábytek a skříňky", "koupelna"),
    "koupelnove-doplnky": ("Koupelnové doplňky", "koupelna", "Koupelnové doplňky", "koupelna"),
    # zahrada
    "zahradni-sestavy": ("Zahradní sestavy", "zahrada", "Zahradní sedací sestavy", "zahrada"),
    "zahradni-stoly": ("Zahradní stoly", "zahrada", "Zahradní stoly", "zahrada"),
    "zahradni-zidle": ("Zahradní židle a křesla", "zahrada", "Zahradní židle, křesla a lavice", "zahrada"),
    "lehatka": ("Lehátka", "zahrada", "Zahradní lehátka", "zahrada"),
    "houpacky-a-site": ("Houpačky a houpací sítě", "zahrada", "Zahradní houpačky, houpací sítě a závěsná křesla", "zahrada"),
    "slunecniky-a-zasteny": ("Slunečníky a zástěny", "zahrada", "Slunečníky, plachty a balkonové zástěny", "zahrada"),
    "polstare-na-zahradni-nabytek": ("Polstry na zahradní nábytek", "zahrada", "Polstry a sedáky na zahradní nábytek", "zahrada"),
    # svítidla
    "lustry": ("Lustry a závěsná svítidla", "svitidla", "Lustry a závěsná svítidla", "lustr"),
    "stropni-svitidla": ("Stropní svítidla", "svitidla", "Stropní a bodová svítidla", "lustr"),
    "stojaci-lampy": ("Stojací lampy", "svitidla", "Stojací lampy", "lampa"),
    "stolni-lampy": ("Stolní lampy", "svitidla", "Stolní a noční lampy", "lampa"),
    "nastenna-svitidla": ("Nástěnná svítidla", "svitidla", "Nástěnná svítidla", "lampa"),
    "venkovni-svitidla": ("Venkovní svítidla", "svitidla", "Venkovní a zahradní svítidla", "lampa"),
    "dekoracni-osvetleni": ("Dekorativní osvětlení", "svitidla", "Světelné řetězy a dekorativní osvětlení", "lampa"),
    # textil
    "koberce": ("Koberce", "textil", "Koberce", "koberec"),
    "behouny-a-predlozky": ("Běhouny a předložky", "textil", "Běhouny, rohožky a předložky", "koberec"),
    "zaclony-a-zavesy": ("Záclony a závěsy", "textil", "Záclony, závěsy a rolety", "koberec"),
    "povleceni": ("Povlečení a prostěradla", "textil", "Povlečení a prostěradla", "postel"),
    "prikryvky-a-polstare": ("Přikrývky a polštáře na spaní", "textil", "Přikrývky a polštáře na spaní", "postel"),
    "dekorativni-polstare": ("Dekorativní polštáře", "textil", "Dekorativní polštáře a povlaky", "kreslo"),
    "deky-a-prehozy": ("Deky a přehozy", "textil", "Deky, pledy a přehozy", "kreslo"),
    "rucniky-a-osusky": ("Ručníky a osušky", "textil", "Ručníky, osušky a župany", "koupelna"),
    "potahy-na-nabytek": ("Potahy na nábytek", "textil", "Potahy na sedačky a židle", "sofa"),
    "ubrusy-a-prostirani": ("Ubrusy a prostírání", "textil", "Ubrusy, běhouny na stůl a prostírání", "jidelna"),
    # dekorace
    "vanocni-dekorace": ("Vánoční dekorace", "dekorace", "Vánoční dekorace", "vaza"),
    "zrcadla": ("Zrcadla", "dekorace", "Zrcadla", "koupelna"),
    "obrazy": ("Obrazy a plakáty", "dekorace", "Obrazy a plakáty", "vaza"),
    "nastenne-dekorace": ("Nástěnné dekorace", "dekorace", "Nástěnné dekorace", "vaza"),
    "ramy-na-fotky": ("Rámy na fotky", "dekorace", "Rámy na fotky a obrazy", "vaza"),
    "hodiny": ("Hodiny", "dekorace", "Nástěnné a stolní hodiny", "vaza"),
    "vazy": ("Vázy", "dekorace", "Vázy", "vaza"),
    "kvetinace": ("Květináče", "dekorace", "Květináče a obaly na květiny", "vaza"),
    "umele-kvetiny": ("Umělé květiny a rostliny", "dekorace", "Umělé květiny a rostliny", "vaza"),
    "svicky-a-svicny": ("Svíčky, svícny a vůně", "dekorace", "Svíčky, svícny a vůně do bytu", "vaza"),
    "ulozne-boxy-a-kose": ("Úložné boxy a koše", "dekorace", "Úložné boxy, koše a košíky", "komoda"),
    "sosky-a-doplnky": ("Sošky a bytové doplňky", "dekorace", "Sošky, figurky a bytové doplňky", "vaza"),
}

TREE = {**{k: (v[0], None, v[1], v[2], v[3]) for k, v in ROOMS.items()},
        **{k: (v[0], v[1], v[2], "", v[3]) for k, v in CATS.items()}}
TOP = list(ROOMS)
ICON = {k: v[4] for k, v in TREE.items()}
# second Canva sheet (12. 11. 2026): a fitting icon for every big category, so tiles never repeat one picture
ICON.update({"rohove-sedacky": "rohova-sedacka", "taburety-a-sedaci-vaky": "taburet", "konferencni-stolky": "konferencni-stolek", "tv-stolky": "tv-stolek",
             "vitriny": "skrin", "matrace": "matrace", "rosty": "matrace", "nocni-stolky": "nocni-stolek", "toaletni-stolky": "zrcadlo",
             "jidelni-stoly": "jidelni-stul", "jidelni-zidle": "jidelni-zidle", "barove-zidle": "barova-zidle", "lavice": "predsin",
             "servirovaci-stolky": "jidelni-stul", "kancelarske-zidle": "kancelarska-zidle", "herni-kresla": "kancelarska-zidle",
             "kancelarske-skrine": "skrin", "botniky": "botnik", "zaclony-a-zavesy": "zaclony", "povleceni": "povleceni",
             "prikryvky-a-polstare": "povleceni", "dekorativni-polstare": "povleceni", "deky-a-prehozy": "povleceni", "ubrusy-a-prostirani": "jidelni-stul",
             "zrcadla": "zrcadlo", "obrazy": "obraz", "nastenne-dekorace": "obraz", "ramy-na-fotky": "obraz", "kvetinace": "kvetinac",
             "umele-kvetiny": "kvetinac", "ulozne-boxy-a-kose": "komoda", "stropni-svitidla": "lustr", "venkovni-svitidla": "zahrada",
             "rucniky-a-osusky": "koupelna", "potahy-na-nabytek": "sofa"})

# products cheaper than this in a category are almost always accessories in the wrong place (a "postel" for 190 Kč is a sheet)
PRICE_FLOOR = {"rohove-sedacky": 4000, "sedacky": 2500, "pohovky": 2000, "kresla": 700, "postele": 1500, "matrace": 800, "rosty": 400,
               "satni-skrine": 1200, "komody": 900, "jidelni-stoly": 900, "jidelni-sety": 2000, "jidelni-zidle": 300, "barove-zidle": 400,
               "psaci-stoly": 800, "kancelarske-zidle": 700, "herni-kresla": 1200, "detske-postele": 1000, "obyvaci-steny": 2500,
               "tv-stolky": 700, "konferencni-stolky": 400, "zahradni-sestavy": 2500, "kuchynske-linky": 1500, "predsinove-steny": 1500,
               "koupelnove-skrinky": 500, "lustry": 250, "stojaci-lampy": 300, "koberce": 150}

# ------------------------------------------------------------------ veto: not furniture / décor
VETO_TITLE = re.compile(
    r"\b(vrtack|bruska|sroubovak|pilk|pila\b|kladiv|naradi|hmozdin|sroub[uy]?\b|hrebik|barva na|lak na|lazur|penetrac|tmel|silikon\b|stetec|malirsk|valecek|"
    r"dlazb|obklad|laminat\w* podlah|vinylov\w* podlah|podlahov\w* (lista|krytin)|^(posuvn\w* |interierov\w* |vchodov\w* |balkonov\w* )?dvere\b|zarubn|\bklika|kovani\b|\bzamek|sokl\b|lepidl|sprchov\w* zasten|deštník|destnik|pantofl|backor|boxerk|"
    r"vodovodn\w* bateri|bateri\w* (umyvadl|sprch|drez|van)|umyvadl(o|a)?\b(?! skrin)|keramick\w* umyvadl|wc\b|zachod|zavesn\w* wc|splachov|sprchov|vanov|\bvana\b|bidet|pisoar|sifon|odpad\b|ventil\b|"
    r"cerpadl|kotel|radiator|bojler|klimatiz|odvlhcov|zvlhcov|topidl|primotop|"
    r"hnojiv|osiv|substrat|sekack|krovinorez|zahradn\w* hadic|postrikov|pletivo|plotov|pergol|bazen|gril\w*\b|udirn|"
    r"hrnec|hrnce|panev|kastrol|nuz\b|noze\b|pribor|talir|hrnek|hrnky|sklenic|konvic|mixer|kuchynsk\w* robot|kavovar|vysavac|zehlick|zehlic\w* prkn|pracka|lednic|"
    r"trouba|varn\w* desk|digestor|mikrovln|toustovac|rychlovarn|termoska|termohrn|lahev|svacinov|"
    r"hrack|puzzle|kniha|plysa|panenk|stavebnic|kocar|autosedack|parfem|kosmetik|krem\b|sampon|"
    r"krmiv|pamlsk|obojek|voditk|pro psy|pro kocky|pelisek|pelech|skrabadl|"
    r"nahradn\w* dil|kolecka|koleck\w* (pro|k|na) zidl|plynov\w* pist|podruck|kluzak|zarovk|baterie\b|nabijeck|kabel\b|prodluzov|"
    r"poukaz|oblecen|bunda|tricko|mikina|kalhoty|ponozk|"
    r"zebrik|schudk|mop\b|kbelik|susak na pradlo|susic\w* (na pradlo|pradla)|odpadkov\w* kos(?! kosmet)|"
    r"autoz|autoprisl|reproduktor|televiz(?!n\w* stol|n\w* skrin)|notebook|tiskarn)", I)
VETO_PATH = re.compile(r"(naradi|stavebnin|technika|barvy|dlazb|obklad|podlah|dvere|zarubn|sanitar|umyvadla|vodovodni bateri|sprchov|wc dopl|"
                       r"hracky|hracky pro deti|knihy|pro skolaky|pro nejmensi|nadobi|panve|hrnce|kuchynske noze|pribory|sklenice|pecen|"
                       r"kuchynske spotrebic|vse pro grilov|grilov|nahradni dily|zahradni naradi|pece o rostliny|auto\b|zabezpeceni|zelezarstvi|"
                       r"ohrev a chlazeni|elektro|darkove poukazy|obleceni|kojeni|prebalovani|uklid|zehleni|zebriky)", I)

R = lambda s: re.compile(s, I)
# (category, pattern on the folded title). First match wins.
TITLE_RULES = [
    # textiles that name a piece of furniture ("povlečení NA postel", "potah NA sedačku") — before furniture
    ("povleceni", R(r"povleceni|povlak\w* na matrac|potah\w* (na )?matrac|povlak\w* na (perin|prikryv)|prosteradl|chranic\w* matrac|matracov\w* chranic|napinac\w* prost")),
    ("potahy-na-nabytek", R(r"^(\w+ ){0,2}potah(?!\w* (na )?matrac)|potah\w* na (sedac|zidl|kresl|pohov|gauc|rohov|tabur)|napinac\w* potah|navlek\w* na (sedac|zidl|kresl|pohov)|prehoz\w* na (sedac|gauc|pohov)")),
    ("polstare-na-zahradni-nabytek", R(r"(polstar|polstr|podsedak|sedak)\w* (na|pro|k) (zahradn|zidl|lehatk|lavic|houpac|kresl|palet)|podsedak|sedak na zidl|polstr na lehatk")),
    ("prikryvky-a-polstare", R(r"prikryvk|\bperin|(zdravotn|anatomick|ortopedick|ergonomick)\w* polstar|polstar\b.{0,50}\b(40 ?x ?(60|70|80)|50 ?x ?(60|70)|70 ?x ?90)|\bpillow|polstar\w* (na spani|anatomick|ortoped|z pametov|pametov)|spaci polstar|polstar \d0 ?x ?\d0(?! ?cm.*dekor)|chranic\w* polstar")),
    ("dekorativni-polstare", R(r"dekorac\w* polstar|polstar\w* (dekorac|s vyplni|45 ?x ?45|40 ?x ?40|50 ?x ?50|30 ?x ?50)|povlak\w* na polstar|^(\w+ ){0,2}polstar(?!ov)|polstark")),
    ("deky-a-prehozy", R(r"\bdek[ay]\b|\bdeku\b|\bdeck|\bpled|prehoz|beranek deka")),
    ("rucniky-a-osusky", R(r"rucnik|osusk|zupan|osuska")),
    ("ubrusy-a-prostirani", R(r"\bubrus|behoun na stul|stolni behoun|prostirani|ubrousk")),
    ("zaclony-a-zavesy", R(r"zaclon|\bzaves(y|u|em|u)?\b|vitrazk|zaluzi|\brolet|garnyz|zatemnovac|kolejnic\w* na zaclon")),
    ("behouny-a-predlozky", R(r"\bbehoun|predlozk|rohozk|koupelnov\w* (koberec|koberecek)")),
    ("koberce", R(r"\bkoberec|\bkoberc|\bkobere")),
    # children (before generic furniture)
    ("detske-postele", R(r"detsk\w* (postel|postylk|lozk)|patrov\w* postel|postel pro deti|domeckov\w* postel|\bpostyl|kolebk|kolisk|junior postel|postel (s|se) skluzavk|vyvysen\w* postel")),
    ("detske-pokoje", R(r"(detsk|studentsk)\w* (pokoj|sestav)")),
    ("detske-stolky-a-zidle", R(r"(detsk|studentsk|rostouc)\w* (stul|stol|stolek|stolecek|zidl|zidlick|kreslo|kreslick|sedack|stolick)")),
    ("detske-skrine-a-ulozne-boxy", R(r"detsk\w* (skrin|komod|regal|knihovn|polic|satn)|(organizer|organizer|box|kos|truhla|regal) na hrack")),
    ("detske-dekorace", R(r"(do|pro) detsk\w* pokoj|detsk\w* (lamp|svitidl|koberec|polstar|dekorac|obraz|samolepk|nocni svetl|nocni lampick)")),
    # office & gaming
    ("herni-kresla", R(r"hern\w* (kresl|zidl|stul)|gaming")),
    ("kancelarske-zidle", R(r"kancelarsk\w* (zidl|kresl)|pracovn\w* zidl|zidl\w* (k pc|k pocitac|na kolecka)|otocn\w* (zidl|kresl)|konferencn\w* zidl|ergonomick\w* zidl|balancni zidl|klekack")),
    ("kancelarske-skrine", R(r"kancelarsk\w* (skrin|kontejner|regal)|kontejner (pod stul|kancel|s zasuvk)|spisov\w* skrin")),
    ("psaci-stoly", R(r"(psac|pracovn|pc|kancelarsk|pocitacov)\w* (stul|stol\b|stolek)|vyskove (stavitel|nastavitel)\w* stul|stul (pod|na) (pc|pocitac|notebook)|\bpsaci\b")),
    # dining
    ("jidelni-sety", R(r"jideln\w* (set|sestav|souprav)|stul (a|\+|se|s) (\d+|dvema|ctyrmi|sesti) zidl|\d+ ?x ?zidl.*stul|stul.*\d+ ?x ?zidl")),
    ("barove-zidle", R(r"barov\w* (zidl|stolick|stolic|kresl)|barova\b|barove\b")),
    ("servirovaci-stolky", R(r"servirovac\w* (stol|vozik)|\bservirovak|barov\w* vozik")),
    ("kuchynske-linky", R(r"kuchyn\w* (link|sestav|skrin|blok|ostruvek|regal)|(horni|dolni|rohov\w*) kuchyn\w* skrin|kuchyne \d{3}|potravinov\w* skrin|\bspizirn")),
    # garden (before chairs/tables/sofas)
    ("houpacky-a-site", R(r"houpac\w* (sit|kresl|lehatk)|zahradn\w* houpac|zavesn\w* (kresl|houpac)|\bhoupacka")),
    ("lehatka", R(r"lehatk|zahradn\w* (lehatk|lehatko)|\bsezlong\w* zahrad")),
    ("zahradni-sestavy", R(r"zahradn\w* (sestav|souprav|\bset\b|lounge|sedack|sedaci|nabytek)|ratanov\w* (sestav|souprav|set|nabytek)|balkonov\w* (set|sestav|souprav)|lounge (set|sestav)|venkovn\w* (sedac|sestav)")),
    ("zahradni-stoly", R(r"(zahradn|balkonov|venkovn|kempinkov)\w* (stul|stol\b|stolek|stolk)")),
    ("zahradni-zidle", R(r"(zahradn|balkonov|venkovn|kempinkov|ratanov)\w* (zidl|kresl|lavic)|skladac\w* zahradn|adirondack")),
    ("slunecniky-a-zasteny", R(r"slunecnik|stinic\w* placht|plachta proti slunci|markyz|(balkonov|zahradn)\w* (zasten|paravan|clona)|zasten\w* na balkon|stojan na slunecnik")),
    # living room
    ("rohove-sedacky", R(r"rohov\w* (sedac|pohov|gauc|souprav)|sedac\w* (souprav\w* )?(do l|do u|ve tvaru)|\bu sedac|\bl sedac|\brohovka|rohova\b.*\bsouprav")),
    ("sedacky", R(r"sedac\w* souprav|\bsedack|\bsedacku|\bsedacky|sedaci (sestav|blok)|modulov\w* (sedac|sofa)|\bsofa\b.*\b(3|4|tri|ctyr)")),
    ("pohovky", R(r"pohovk|\bgauc|kanape|\bsofa\b|rozkladac\w* (sofa|pohov)|\blenosk|\bdivan|\bsezlong|\bvalenda")),
    ("taburety-a-sedaci-vaky", R(r"taburet|\bpuf\b|\bpufy|\bpufik|sedac\w* vak|sedaci pytel|\bpodnozk|\bpodnoz\b")),
    ("kresla", R(r"kresl|\busak|relaxac\w* kresl|houpac\w* kresl")),
    ("tv-stolky", R(r"\btv\b.*(stol|skrin|komod|lavic|regal|nabytek|sten)|televizn\w* (stol|skrin|komod)|(stolek|skrinka|komoda|lavice) (pod|na) (tv|televiz)")),
    ("obyvaci-steny", R(r"obyvac\w* (sten|sestav|nabytek|program)|nabytkov\w* (sestav|sten)|\bobyvak\b")),
    ("vitriny", R(r"vitrin")),
    ("konferencni-stolky", R(r"(konferencn|odkladac|kavov|prirucn|konzolov|sofa)\w* (stol|stolek|stolk|stul)|^(\w+ ){0,1}stolek\b|\bkonzol[ae]\b|stolek (do obyvak|ke gauc|k sedac)")),
    # bedroom
    ("toaletni-stolky", R(r"(toaletn|kosmetick)\w* (stol|stolek)|\btoaletk")),
    ("nocni-stolky", R(r"nocn\w* (stol|stolek|skrin)")),
    ("rosty", R(r"\brost(y|u|em)?\b(?!.*\bs rostem)|lamelov\w* rost|postelov\w* rost")),
    ("matrace", R(r"\bmatrac|\btopper|\bpristylk")),
    ("postele", R(r"\bpostel|\blozk|manzelsk\w* (postel|lozk)|kontinental|boxspring|\bloznice\b")),
    ("satni-skrine", R(r"satn\w* skrin|skrin (s posuv|s otoc|s dverm|se zrcadl|s zrcadl)|vestavn\w* skrin|\bsatna\b|\bskrin\b|\bskrine\b|\bskrin\w* na saty|\bsatnik")),
    ("komody", R(r"komod|pradelnik|\bkomoda")),
    # hallway
    ("botniky", R(r"botnik|(skrin|skrink|regal|stojan|lavic|polic)\w* na (boty|obuv)")),
    ("vesaky", R(r"vesak|vesakov\w* (sten|panel)|stojan\w* na (kabat|obleceni)|nemy sluha|\bhacky na")),
    ("predsinove-steny", R(r"predsin|predsinov|satnov\w* (sten|system)")),
    # bathroom
    ("koupelnove-skrinky", R(r"koupelnov\w* (skrin|skrink|sestav|nabytek|regal|polic|komod|galerk)|skrink\w* pod umyvadl|skrin\w* pod umyvadl|\bgalerk|umyvadl\w* se skrink|(skrinka|skrin) (do|v) koupeln")),
    ("koupelnove-doplnky", R(r"davkovac mydl|drzak (na kartack|na rucnik|toaletn|na wc|na papir)|mydelnic|stetka|koupelnov\w* (doplnk|sada|set)|kos na pradlo|kelimek na kartack")),
    # tables / chairs / shelves (generic, after the specific ones)
    ("jidelni-stoly", R(r"jideln\w* (stul|stol\b)|rozkladac\w* stul|\bstul\b|\bstoly\b")),
    ("jidelni-zidle", R(r"jideln\w* zidl|\bzidl|\bzidle|\bstolick")),
    ("lavice", R(r"\blavic")),
    ("knihovny-a-regaly", R(r"knihovn|regal|\bpolic[ei]?\b|nastenn\w* polic|\bpolick")),
    # lighting
    ("venkovni-svitidla", R(r"(venkovn|zahradn|solarn)\w* (svitid|svetl|lamp|led|osvetl)")),
    ("dekoracni-osvetleni", R(r"svetel\w* (retez|zaves|dekorac)|led (retez|zaves|dekorac|figur|vlock)|svetylk|dekorac\w* (svetl|osvetl)")),
    ("stojaci-lampy", R(r"stojac\w* (lamp|svitid)|stojanov\w* lamp|oblouk\w* lamp")),
    ("stolni-lampy", R(r"stoln\w* (lamp|svitid)|nocn\w* lamp|lampick")),
    ("nastenna-svitidla", R(r"nastenn\w* (svitid|svetl|lamp)|\bapliky?\b")),
    ("lustry", R(r"\blustr|zavesn\w* (svitid|svetl|lamp|led)")),
    ("stropni-svitidla", R(r"stropn\w* (svitid|svetl|lamp|led)|plafon|bodov\w* (svitid|svetl)|led panel|\bspoty?\b(?!.*\b(polstr|sedak))|\bzaric")),
    # décor
    ("vanocni-dekorace", R(r"vanocn|advent|stromecek|ozdob\w* na strom|\bbetlem|\bsnehulak")),
    ("zrcadla", R(r"zrcadl")),
    ("ramy-na-fotky", R(r"(ram|ramecek|ramecky) na (foto|obraz)|fotoram|\bramecek|\bramecky|fotoalb")),
    ("obrazy", R(r"\bobraz|plakat|\bprint\b|reprodukc|tisk na platn|fotoobraz|\bplatno\b|\bcanvas")),
    ("nastenne-dekorace", R(r"nastenn\w* dekorac|dekorac\w* na zed|samolepk\w* na zed|tapet[ay]?\b|makram|nastenk|magneticka tabule")),
    ("hodiny", R(r"\bhodiny|\bbudik")),
    ("kvetinace", R(r"kvetinac|obal na kvetin|\btruhlik|stojan na kvetin|zardinier")),
    ("vazy", R(r"\bvaz[ay]?\b|\bvazu\b|vazicka")),
    ("umele-kvetiny", R(r"umel\w* (kvet|rostlin|strom|kytk|orchid|travy|palm|vetev)|dekorac\w* (kvet|vetev)|susen\w* kvet|\bkytice")),
    ("svicky-a-svicny", R(r"\bsvick|svicn|\blucern|vonn\w* (difuz|tycink|svick|olej|vosk)|\bdifuzer|aromalamp")),
    ("ulozne-boxy-a-kose", R(r"ulozn\w* (box|kos|krabic|vak)|\bkosik|\bkos\b|\bkose\b|proutěn|\btruhla|organizer|\bbox na")),
    ("sosky-a-doplnky", R(r"\bsosk|figurk|\bsoch|dekorac\w* (predmet|misa|socha)|\bdekorace\b|\bmisa\b")),
    # leftover lighting words
    ("stropni-svitidla", R(r"\bsvitidl|\bsvetlo\b")),
    ("stolni-lampy", R(r"\blampa\b|\blampy\b")),
]

# shop category path -> category, when the title alone said nothing (paths are folded too)
PATH_RULES = [
    ("rohove-sedacky", R(r"rohov\w* sedac")), ("sedacky", R(r"sedack|sedaci soupra")), ("pohovky", R(r"pohovk|gauc")),
    ("kresla", R(r"kresla|\bkreslo")), ("taburety-a-sedaci-vaky", R(r"taburet|sedaci vak")),
    ("konferencni-stolky", R(r"stolky do obyvak|konferencn")), ("tv-stolky", R(r"tv nabytek|tv sk|televizn")),
    ("obyvaci-steny", R(r"obyvaci sten")), ("knihovny-a-regaly", R(r"regal|knihovn|police")), ("vitriny", R(r"vitrin")),
    ("detske-postele", R(r"detsk\w* postel|postylk")), ("detske-pokoje", R(r"detske pokoje|pokoje pro miminka|variabilni sestavy detsk")),
    ("detske-skrine-a-ulozne-boxy", R(r"detsky nabytek|detske satni")), ("detske-dekorace", R(r"dekorace do detsk")),
    ("matrace", R(r"matrac")), ("rosty", R(r"rosty")), ("postele", R(r"postele")), ("satni-skrine", R(r"satni skrin|loznice > skrine|skrine$")),
    ("komody", R(r"komod")), ("nocni-stolky", R(r"nocni stol")), ("toaletni-stolky", R(r"toaletni stol")),
    ("jidelni-stoly", R(r"jidelny > stoly|jidelni stoly|kuchyne a jidelna > stoly")), ("jidelni-zidle", R(r"jidelny > zidle|jidelni zidle|kuchyne a jidelna > zidle")),
    ("barove-zidle", R(r"barov")), ("lavice", R(r"jidelny > lavice")), ("kuchynske-linky", R(r"kuchynsky nabytek|kuchynske link")),
    ("psaci-stoly", R(r"psaci stol|pracovni stol|pc a pracovni")), ("kancelarske-zidle", R(r"kancelarske zidle|kancelarska kresla|domu k pocitaci")),
    ("herni-kresla", R(r"herni")), ("kancelarske-skrine", R(r"kancelarske kontejnery|regaly a skrine")),
    ("botniky", R(r"skrine na boty|botnik")), ("vesaky", R(r"vesak")), ("predsinove-steny", R(r"predsin")),
    ("koupelnove-skrinky", R(r"koupelnove sestavy|koupelnove skrin|koupelnovy nabytek")), ("koupelnove-doplnky", R(r"koupelnove doplnky|vybaveni koupelny")),
    ("zahradni-sestavy", R(r"zahradni lounge|zahradni sestavy|zahradni nabytek")), ("zahradni-stoly", R(r"zahradni stoly")),
    ("zahradni-zidle", R(r"zahradni zidle")), ("slunecniky-a-zasteny", R(r"zastineni|zasteny na balkon")), ("houpacky-a-site", R(r"houpac")),
    ("polstare-na-zahradni-nabytek", R(r"polstry")),
    ("venkovni-svitidla", R(r"venkovni osvetleni")), ("dekoracni-osvetleni", R(r"dekorativni osvetleni|led svetla")),
    ("lustry", R(r"lustry|zavesn")), ("stojaci-lampy", R(r"stojaci")), ("stolni-lampy", R(r"stolni lamp|lampy")),
    ("nastenna-svitidla", R(r"nastenn\w* svitid")), ("stropni-svitidla", R(r"stropni|osvetleni interieru|svitidla|osvetleni")),
    ("koberce", R(r"koberce")), ("behouny-a-predlozky", R(r"behoun|rohoz")), ("zaclony-a-zavesy", R(r"zaclony|zavesy|okenni dekorace")),
    ("povleceni", R(r"povleceni|povlak\w* na matrac|potah\w* (na )?matrac|prosteradl")), ("prikryvky-a-polstare", R(r"prikryvky|polstare a prikryvky|prikryvky a polstare")),
    ("rucniky-a-osusky", R(r"rucnik|koupelnovy textil")), ("deky-a-prehozy", R(r"deky|prehoz")), ("potahy-na-nabytek", R(r"potahy")),
    ("vanocni-dekorace", R(r"vanoc")), ("zrcadla", R(r"zrcadla")), ("obrazy", R(r"obrazy")), ("nastenne-dekorace", R(r"dekorace na zed|samolepky na zed")),
    ("ramy-na-fotky", R(r"ramy")), ("hodiny", R(r"hodiny")), ("vazy", R(r"vazy")), ("kvetinace", R(r"kvetinac")),
    ("umele-kvetiny", R(r"kvetiny")), ("svicky-a-svicny", R(r"svicky|svicny|vune do bytu")), ("ulozne-boxy-a-kose", R(r"ulozne|kosik|ukladani")),
    ("sosky-a-doplnky", R(r"figurky|sosky")),
]


def veto(title_f, path_f):
    return bool(VETO_TITLE.search(title_f)) or bool(VETO_PATH.search(path_f))


# Weak rules: generic words that only decide when nothing more concrete is in the title ("Vánoční polštář" = a cushion).
WEAK = {"vanocni-dekorace", "sosky-a-doplnky", "ulozne-boxy-a-kose", "detske-dekorace"}
RULE_ORDER = {i: i for i in range(len(TITLE_RULES))}


KIDS_MAP = {"postele": "detske-postele", "satni-skrine": "detske-skrine-a-ulozne-boxy", "komody": "detske-skrine-a-ulozne-boxy",
            "knihovny-a-regaly": "detske-skrine-a-ulozne-boxy", "jidelni-zidle": "detske-stolky-a-zidle",
            "jidelni-stoly": "detske-stolky-a-zidle", "psaci-stoly": "detske-stolky-a-zidle"}


# nouns that name one category on their own, whatever words surround them: a single-word match of these is as good as a phrase
UNAMBIGUOUS = {"matrace", "botniky", "vitriny", "komody", "taburety-a-sedaci-vaky", "koberce", "zrcadla", "lustry", "vazy", "kvetinace",
               "hodiny", "zaclony-a-zavesy", "povleceni", "rucniky-a-osusky", "vesaky", "rosty", "lehatka", "slunecniky-a-zasteny",
               "vanocni-dekorace", "ramy-na-fotky", "svicky-a-svicny", "deky-a-prehozy", "prikryvky-a-polstare", "behouny-a-predlozky"}
VETOED = "__veto__"


def title_class(rec):
    """What the TITLE says: (category, strong) or (VETOED, True) or (None, False).

    Czech product titles name the thing first ("Šatní skříň Abi s posuvnými dveřmi", "Postel s roštem a žebříkem",
    "Povlečení na postel"): the rule whose match starts EARLIEST in the title wins; on a tie the longer match, then the
    order of TITLE_RULES. Weak rules count only when no other rule matched. The veto list works the same way: a veto word
    decides only when it comes before the furniture word (or the furniture word is a weak one).
    strong = the match is a phrase ("dětská postel", "noční stolek", "rohová sedací souprava") or an unambiguous noun
    (matrace, botník); a lone generic noun ("skříň", "pohovka", "polštář…", "obraz") is not strong."""
    t = fold(clean(rec.get("t"))).replace("-", " ")
    p = fold(rec.get("cat") or "")
    if VETO_PATH.search(p):
        return VETOED, True
    best = None
    for i, (slug, rx) in enumerate(TITLE_RULES):
        m = rx.search(t)
        if m:
            key = (slug in WEAK, m.start(), -(m.end() - m.start()), i)
            if best is None or key < best[0]:
                best = (key, slug, m.group(0))
    v = VETO_TITLE.search(t)
    if v and (best is None or best[0][0] or v.start() < best[0][1]):
        return VETOED, True
    if not best:
        return None, False
    slug, text = best[1], best[2].strip()
    strong = slug not in WEAK and (" " in text or slug in UNAMBIGUOUS)
    return slug, strong


def path_class(rec):
    p = fold(rec.get("cat") or "")
    for slug, rx in PATH_RULES:
        if rx.search(p):
            return slug
    return None


def kids_fix(slug, rec, kids=False):
    if slug and (kids or re.search(r"detsk|studentsk", fold(rec.get("cat") or ""))):   # a kids' shop / kids' section: its "postel" is a children's bed
        return KIDS_MAP.get(slug, slug)
    return slug


def classify(rec, kids=False):
    """Title only (with the shop path as the last resort). The catalogue uses decide() with per-shop path statistics."""
    slug, strong = title_class(rec)
    if slug == VETOED:
        return None
    return kids_fix(slug or path_class(rec), rec, kids)


def decide(rec, title, clean_path_cat, kids=False):
    """Final category from the title verdict and the shop's own category when that category is CLEAN (nearly all of its
    products are one kind of thing, measured on this run's data). A clean shop category beats a lone generic noun in the
    title ("POLŠTÁŘOVÁ postel" in Postele, "Skříň pod umyvadlo" in Koupelnové skříňky, a fototapeta in Dekorace na zeď)
    and classifies titles that say nothing; a specific phrase in the title beats the shop category ("dětská postel" in
    Postele, "noční stolek" in Odkládací stolky). Returns (category, source)."""
    slug, strong = title
    if slug == VETOED:
        return None, "veto"
    if clean_path_cat:
        if slug and strong and slug != clean_path_cat:
            return kids_fix(slug, rec, kids), "title>path"
        return kids_fix(clean_path_cat, rec, kids), "path"
    if slug:
        return kids_fix(slug, rec, kids), "title"
    fb = path_class(rec)
    return (kids_fix(fb, rec, kids), "path-rule") if fb else (None, "none")


# ------------------------------------------------------------------ attributes
COLORS = [  # slug, label (adjective for "bílé sedačky" style h1s is built per category), patterns
    ("bila", "bílá", r"\bbil[aáeéyý]\w*|\bwhite\b|\bsnehobil"),
    ("cerna", "černá", r"\bcern[aeyáéý]\w*|\bblack\b|\bantracit\w*"),
    ("seda", "šedá", r"\bsed[aeyáéý]\b|\bsedo\w*|\bsedi\w*|\bgrey\b|\bgray\b|\bgrafit\w*|\bplatinov"),
    ("bezova", "béžová", r"\bbezov\w*|\bkremov\w*|\bsmetanov\w*|\bbeige\b|\bcappuccino|\bkasmir|\bpiskov"),
    ("hneda", "hnědá", r"\bhned[aeyáéý]\w*|\bcokolad\w*|\bkavov\w*|\bkoniak|\bbrown\b|\bkaramel"),
    ("zelena", "zelená", r"\bzelen\w*|\bolivov\w*|\bsalvej|\bmatov[aá]\b|\bsmaragd\w*|\bgreen\b|\bmech\w*ov"),
    ("modra", "modrá", r"\bmodr\w*|\bpetrolej\w*|\btyrkys\w*|\bnavy\b|\bblue\b|\bazur"),
    ("ruzova", "růžová", r"\bruzov\w*|\bpudrov\w*|\bstarorůž|\bstaroruz|\bpink\b|\bmalinov"),
    ("cervena", "červená", r"\bcerven\w*|\bbordo\w*|\bvinov\w*|\bred\b"),
    ("zluta", "žlutá", r"\bzlut\w*|\bhorcicov\w*|\bokrov\w*|\byellow\b"),
    ("oranzova", "oranžová", r"\boranzov\w*|\bterakot\w*|\bcihlov\w*|\brezav"),
    ("zlata", "zlatá", r"\bzlat[aeyáéý]\w*|\bmosazn\w*|\bgold\b"),
    ("stribrna", "stříbrná", r"\bstribrn\w*|\bchrom\w*|\bsilver\b"),
]
COLORS_RX = [(s, l, re.compile(r)) for s, l, r in COLORS]
COLOR_NAME = {s: l for s, l, _ in COLORS}

MATERIALS = [
    ("masiv", "masiv", r"\bmasiv\w*"),
    ("dub", "dub", r"\bdub\b|\bdubov\w*|\boak\b"),
    ("buk", "buk", r"\bbuk\b|\bbukov\w*"),
    ("borovice", "borovice", r"\bborovic\w*|\bborov[aáeé]\b"),
    ("orech", "ořech", r"\borech\w*|\bwalnut"),
    ("akat", "akát", r"\bakat\w*|\bakacie|\bakaci"),
    ("mango", "mango", r"\bmango\w*"),
    ("teak", "teak", r"\bteak\w*"),
    ("kov", "kov", r"\bkov\b|\bkovov\w*|\bocel\w*|\bzelez\w*|\bhlinik\w*"),
    ("samet", "samet", r"\bsamet\w*|\bvelvet\b|\bmanchester|\bmansestr"),
    ("boucle", "bouclé", r"\bboucl\w*"),
    ("kuze", "kůže", r"(?<!eko)(?<!eko )\bkuz[ei]\b|\bkozen[aáeéyý]\b|\bprav\w* kuz"),
    ("ekokuze", "ekokůže", r"\beko ?kuz\w*|\bkozenk\w*|\bpu kuz|\bumel\w* kuz"),
    ("len", "len", r"\blnen\w*|\blen\b|\blinen\b"),
    ("ratan", "ratan", r"\bratan\w*|\bprouti\b|\bproutěn|\bprouten\w*|\bwicker"),
    ("bambus", "bambus", r"\bbambus\w*"),
    ("sklo", "sklo", r"\bsklo\b|\bsklenen\w*|\bskla\b"),
    ("mramor", "mramor", r"\bmramor\w*|\bmarble"),
    ("keramika", "keramika", r"\bkeramik\w*|\bkamenin\w*|\bporcelan\w*"),
    ("bavlna", "bavlna", r"\bbavln\w*|\bcotton"),
    ("vlna", "vlna", r"\bvln[aeěy]\b|\bvlnen\w*"),
]
MATERIALS_RX = [(s, l, re.compile(r)) for s, l, r in MATERIALS]
MATERIAL_NAME = {s: l for s, l, _ in MATERIALS}

STYLES = [
    ("skandinavsky", "skandinávský", r"skandinav\w*|\bscandi\w*|\bnordic|\bseversk"),
    ("industrialni", "industriální", r"industrial\w*|\bloft\w*"),
    ("retro", "retro", r"\bretro\b|\bvintage\b|\bmid.?century"),
    ("boho", "boho", r"\bboho\b|\betno\b|\bethno"),
    ("venkovsky", "venkovský", r"\bprovence|\bprovensal|\bvenkovsk\w*|\brustik\w*|\bcountry\b|\bshabby"),
    ("japandi", "japandi", r"\bjapandi\b"),
    ("glamour", "glamour", r"\bglamour|\bglamor|\bart deco\b"),
    ("moderni", "moderní", r"\bmoderni\w*|\bmodern\b|\bminimalist\w*"),
]
STYLES_RX = [(s, l, re.compile(r)) for s, l, r in STYLES]
STYLE_NAME = {s: l for s, l, _ in STYLES}

FEATURES = [
    ("rozkladaci", "rozkládací", r"rozkladac\w*|s funkci spani|na spani|\bs rozkladem|\brozklad\b"),
    ("s-uloznym-prostorem", "s úložným prostorem", r"ulozn\w* prostor|s ulozn\w*|uloznym|s uloznym|se zasuvk\w*|s uloz"),
    ("polohovaci", "polohovací", r"polohovac\w*|relax funkc|elektrick\w* polohov"),
    ("s-led", "s LED osvětlením", r"\bs led\b|s led osvetl|led osvetlen"),
    ("vyskove-nastavitelne", "výškově nastavitelné", r"vyskove (stavitel|nastavitel)\w*|elektricky stavitel"),
    ("kulate", "kulaté", r"\bkulat\w*|\bkruhov\w*|\boval\w*"),
]
FEATURES_RX = [(s, l, re.compile(r)) for s, l, r in FEATURES]
FEATURE_NAME = {s: l for s, l, _ in FEATURES}


def attrs(title, color_field, desc):
    """Colours, materials, styles and features from what the shop says. Title + the feed's colour field decide colour;
    materials/features also look at the first part of the description; style needs the word itself."""
    t = fold(clean(title))
    c = fold(color_field or "")
    d = fold((desc or "")[:500])
    colors = [s for s, _, rx in COLORS_RX if rx.search(c) or rx.search(t)]
    mats = [s for s, _, rx in MATERIALS_RX if rx.search(t) or rx.search(d)]
    if "ekokuze" in mats and "kuze" in mats:
        mats.remove("kuze")
    styles = [s for s, _, rx in STYLES_RX if rx.search(t) or rx.search(d[:300])]
    feats = [s for s, _, rx in FEATURES_RX if rx.search(t)]
    return colors[:3], mats[:4], styles[:2], feats


# ------------------------------------------------------------------ dimensions
NUM = r"(\d{2,3}(?:[,.]\d)?)"
RX_AXB = re.compile(NUM + r"\s*(?:x|×|\*)\s*" + NUM + r"(?:\s*(?:x|×|\*)\s*" + NUM + r")?\s*(cm)?", I)
RX_SLASH = re.compile(NUM + r"\s*/\s*" + NUM + r"\s*/\s*" + NUM + r"\s*cm", I)     # XXXLutz "101/95/22,5 cm" = š/v/h
RX_W = re.compile(r"\b(?:sirka|siroka|sire|s\.|rozmery|delka)\s*(?:\(cm\))?[:\s]*" + NUM + r"\s*cm", I)
RX_D = re.compile(r"\b(?:hloubka|hluboka|h\.)\s*(?:\(cm\))?[:\s]*" + NUM + r"\s*cm", I)
RX_H = re.compile(r"\b(?:vyska|vysoka|v\.)\s*(?:\(cm\))?[:\s]*" + NUM + r"\s*cm", I)
RX_DIAM = re.compile(r"(?:prumer|ø|⌀)\s*[:\s]*" + NUM + r"\s*cm", I)

# categories where "A x B" means a lying / floor size (postel 160x200, koberec 160x230), not width x depth
SIZE_CATS = {"postele", "matrace", "rosty", "detske-postele", "povleceni", "koberce", "behouny-a-predlozky", "prikryvky-a-polstare",
             "deky-a-prehozy", "dekorativni-polstare", "zaclony-a-zavesy", "rucniky-a-osusky", "ubrusy-a-prostirani", "obrazy"}


def num(s):
    return float(s.replace(",", "."))


RX_SIZE2 = re.compile(NUM + r"\s*(?:x|×|\*|/)\s*" + NUM + r"(?!\s*(?:x|×|\*|/)\s*\d)", I)


def dims(title, desc, cat):
    """{'w','d','h'} in cm when the shop LABELS them (Šířka/Hloubka/Výška), 'size' ("160x200") for lying/floor sizes,
    and 'raw' ("115,5 × 75 × 100") for unlabeled triples — shops order those differently (š×h×v, š×v×h), so only the
    first number (always the width) is used for filtering. Only plausible values are kept."""
    t = fold(title or "")
    d = fold((desc or "")[:1500])
    out = {}
    if cat in SIZE_CATS:
        m = RX_SIZE2.search(t)
        if m:
            a, b = num(m.group(1)), num(m.group(2))
            if 20 <= a <= 400 and 20 <= b <= 500:
                a, b = (a, b) if a <= b else (b, a)
                out["size"] = f"{a:g}x{b:g}"
                out["w"], out["l"] = a, b
    for key, rx in (("w", RX_W), ("d", RX_D), ("h", RX_H)):
        if key not in out:
            m = rx.search(t) or rx.search(d)
            if m:
                out[key] = num(m.group(1))
    if "w" not in out:
        m = RX_SLASH.search(t) or RX_AXB.search(t)
        if m and m.group(3):
            vals = [num(x) for x in m.groups()[:3]]
            out["w"] = vals[0]
            out["raw"] = " × ".join(f"{v:g}".replace(".", ",") for v in vals)
    if "w" not in out:
        m = RX_DIAM.search(t) or RX_DIAM.search(d)
        if m:
            out["w"] = num(m.group(1))
            out["round"] = True
    for k in ("w", "d", "h", "l"):
        if k in out and not (5 <= out[k] <= 600):
            out.pop(k)
    return out


def cz(v):
    return f"{v:g}".replace(".", ",")


def size_label(dm):
    if not dm:
        return ""
    if dm.get("size"):
        return dm["size"].replace("x", " × ").replace(".", ",") + " cm"
    if dm.get("raw"):
        return dm["raw"] + " cm"
    parts = [f"{k} {cz(dm[key])}" for k, key in (("š", "w"), ("h", "d"), ("v", "h")) if key in dm]
    if dm.get("round") and "w" in dm:
        parts[0] = f"⌀ {cz(dm['w'])}"
    return " × ".join(parts) + " cm" if parts else ""


# "Šatní skříň Abi V1 Barva korpusu: Dub Sonoma, Rozměry: 100 cm" -> name + variant parameters
RX_PARAMS = re.compile(r"\s+(?=(?:[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)(?: [a-záčďéěíňóřšťúůýž]+){0,2}: )")


def split_variant(title):
    title = clean(title)
    m = RX_PARAMS.search(title)
    if m and m.start() > 8:
        return title[:m.start()].rstrip(" ,-–"), title[m.end():]
    return title, ""


# ------------------------------------------------------------------ brands
BRAND_ALIAS = {"carryhome": "Carryhome", "ambia home": "Ambia Home", "ambiente": "Ambiente", "xora": "Xora", "novel": "Novel", "hom'in": "Hom'in",
               "homin": "Hom'in", "dieter knoll": "Dieter Knoll", "venda": "Venda", "my home": "MY HOME", "landscape": "Landscape",
               "bessagi home": "Bessagi Home", "cantus": "Cantus", "valnatura": "Valnatura", "luca bessoni": "Luca Bessoni", "mid.you": "Mid.you",
               "dorelan": "Dorelan", "ikea": "IKEA"}
BAD_BRANDS = {"", "none", "null", "neuvedeno", "ostatni", "nezarazeno", "bez znacky", "noname", "no name", "-", "n/a", "unknown", "generic",
              "vyrobce", "nezname", "nabytek", "decodoma", "xxxlutz", "baumax", "scandishop", "asko", "asko - nabytek", "ezidle", "rajnabytku",
              "vyprodejpovleceni", "nabytekpaul", "nabytek paul", "elis design", "elisdesign"}


def brand_of(rec):
    b = clean(rec.get("b"))
    k = fold(b)
    if k in BAD_BRANDS or len(k) < 2:
        return ""
    if k in BRAND_ALIAS:
        return BRAND_ALIAS[k]
    if b.isupper() and len(b) > 4:
        b = b.title()
    return b[:40]


# words that only tell variants of one model apart (size, colour, material names, "cm"); stripped to build the model key
VARIANT_WORDS = re.compile(
    r"\b(\d+([,.]\d+)?\s*(x|×|/)\s*\d+([,.]\d+)?(\s*(x|×|/)\s*\d+([,.]\d+)?)?\s*(cm|mm)?|\d+\s*(cm|mm|ks)|cm|"
    + "|".join(r[2].replace(r"\b", "") for r in COLORS) + r"|svetl\w*|tmav\w*|matn\w*|leskl\w*|prirodn\w*|antracit\w*|"
    r"levy|leva|leve|pravy|prava|prave|levou|pravou|l|p|varianta|barva|provedeni|potah|latka|odstin|rozmer|velikost)\b", I)


def model_key(name):
    t = fold(clean(name))
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    t = VARIANT_WORDS.sub(" ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return t
