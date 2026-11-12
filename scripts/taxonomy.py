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
    "jidelna-a-kuchyne": ("Jídelna", "Nábytek do jídelny a kuchyně", "Jídelní stoly, židle a kuchyňské linky", "jidelna"),
    "kuchyne-a-stolovani": ("Kuchyně a stolování", "Kuchyňské potřeby a stolování", "Hrnce, pánve, nože, talíře, sklenice a dřezy", "jidelni-stul"),
    "pracovna": ("Pracovna", "Nábytek do pracovny a kanceláře", "Psací stoly, kancelářské a herní židle", "pracovna"),
    "detsky-pokoj": ("Dětský pokoj", "Dětský pokoj a miminka", "Dětské postele, stolky, textil a doplňky pro miminka", "detsky-pokoj"),
    "predsin": ("Předsíň a šatna", "Nábytek do předsíně a šatny", "Botníky, věšáky, předsíňové stěny a šatní systémy", "predsin"),
    "koupelna": ("Koupelna", "Koupelna: nábytek, sanita a doplňky", "Skříňky, umyvadla, sprchové kouty, baterie a doplňky", "koupelna"),
    "zahrada": ("Zahrada a balkon", "Zahradní nábytek a vybavení zahrady", "Sestavy, lehátka, grily, bazény a zahradní domky", "zahrada"),
    "svitidla": ("Svítidla", "Svítidla a lampy", "Lustry, lampy, bodovky, LED pásky a žárovky", "lustr"),
    "textil": ("Koberce a textil", "Koberce a bytový textil", "Koberce, záclony, rolety, povlečení a deky", "koberec"),
    "dekorace": ("Dekorace", "Bytové dekorace", "Obrazy, zrcadla, vázy, svíčky a pokojové rostliny", "vaza"),
    "vanoce-a-svatky": ("Vánoce a svátky", "Vánoční a sváteční dekorace", "Ozdoby, stromky, světelné řetězy a adventní výzdoba", "vaza"),
    "domacnost": ("Domácnost a úklid", "Potřeby pro domácnost", "Úložné boxy, regály, sušáky a úklidové pomůcky", "komoda"),
    "podlahy-a-kovani": ("Podlahy a kování", "Podlahy, lišty a kování", "Vinyl, laminát, koberce v metráži, kliky a úchytky", "koberec"),
    "spotrebice": ("Spotřebiče", "Kuchyňské a domácí spotřebiče", "Kávovary, mixéry, konvice, fritézy a vysavače", "jidelna"),
}

CATS = {
    # obývák
    "rohove-sedacky": ("Rohové sedačky", "obyvaci-pokoj", "Rohové sedačky", "kreslo"),
    "sedacky": ("Sedačky", "obyvaci-pokoj", "Sedačky a sedací soupravy", "sofa"),
    "pohovky": ("Pohovky a gauče", "obyvaci-pokoj", "Pohovky a gauče", "sofa"),
    "lenosky": ("Lenošky", "obyvaci-pokoj", "Lenošky a šezlongy", "sofa"),
    "kresla": ("Křesla", "obyvaci-pokoj", "Křesla", "kreslo"),
    "taburety-a-sedaci-vaky": ("Taburety a sedací vaky", "obyvaci-pokoj", "Taburety, pufy a sedací vaky", "kreslo"),
    "konferencni-stolky": ("Konferenční stolky", "obyvaci-pokoj", "Konferenční stolky", "komoda"),
    "tv-stolky": ("TV stolky", "obyvaci-pokoj", "TV stolky a televizní skříňky", "komoda"),
    "obyvaci-steny": ("Obývací stěny", "obyvaci-pokoj", "Obývací stěny a sestavy", "knihovna"),
    "knihovny-a-regaly": ("Knihovny a regály", "obyvaci-pokoj", "Knihovny a regály", "knihovna"),
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
    "stropni-svitidla": ("Stropní svítidla", "svitidla", "Stropní svítidla a plafony", "lustr"),
    "stojaci-lampy": ("Stojací lampy", "svitidla", "Stojací lampy", "lampa"),
    "stolni-lampy": ("Stolní lampy", "svitidla", "Stolní a noční lampy", "lampa"),
    "nastenna-svitidla": ("Nástěnná svítidla", "svitidla", "Nástěnná svítidla", "lampa"),
    "venkovni-svitidla": ("Venkovní svítidla", "svitidla", "Venkovní a zahradní svítidla", "lampa"),
    "dekoracni-osvetleni": ("Dekorativní osvětlení", "svitidla", "Světelné řetězy a dekorativní osvětlení", "lampa"),
    # textil
    "koberce": ("Koberce", "textil", "Koberce", "koberec"),
    "behouny-a-predlozky": ("Běhouny a předložky", "textil", "Běhouny, rohožky a předložky", "koberec"),
    "zaclony-a-zavesy": ("Záclony a závěsy", "textil", "Záclony a závěsy", "koberec"),
    "povleceni": ("Povlečení", "textil", "Povlečení", "postel"),
    "prikryvky-a-polstare": ("Přikrývky a polštáře na spaní", "textil", "Přikrývky a polštáře na spaní", "postel"),
    "dekorativni-polstare": ("Dekorativní polštáře", "textil", "Dekorativní polštáře a povlaky", "kreslo"),
    "deky-a-prehozy": ("Deky a přehozy", "textil", "Deky, pledy a přehozy", "kreslo"),
    "rucniky-a-osusky": ("Ručníky a osušky", "textil", "Ručníky, osušky a župany", "koupelna"),
    "potahy-na-nabytek": ("Potahy na nábytek", "textil", "Potahy na sedačky a židle", "sofa"),
    "ubrusy-a-prostirani": ("Ubrusy a prostírání", "textil", "Ubrusy, běhouny na stůl a prostírání", "jidelna"),
    # dekorace
    "vanocni-dekorace": ("Vánoční dekorace", "vanoce-a-svatky", "Vánoční dekorace", "vaza"),
    "zrcadla": ("Zrcadla", "dekorace", "Zrcadla", "koupelna"),
    "obrazy": ("Obrazy a plakáty", "dekorace", "Obrazy a plakáty", "vaza"),
    "nastenne-dekorace": ("Nástěnné dekorace", "dekorace", "Nástěnné dekorace", "vaza"),
    "ramy-na-fotky": ("Rámy na fotky", "dekorace", "Rámy na fotky a obrazy", "vaza"),
    "hodiny": ("Hodiny", "dekorace", "Nástěnné a stolní hodiny", "vaza"),
    "vazy": ("Vázy", "dekorace", "Vázy", "vaza"),
    "kvetinace": ("Květináče", "dekorace", "Květináče a obaly na květiny", "vaza"),
    "umele-kvetiny": ("Umělé květiny a rostliny", "dekorace", "Umělé květiny a rostliny", "vaza"),
    "svicky-a-svicny": ("Svíčky a svícny", "dekorace", "Svíčky a svícny", "vaza"),
    "ulozne-boxy-a-kose": ("Úložné boxy a koše", "domacnost", "Úložné boxy, koše a košíky", "komoda"),
    "sosky-a-doplnky": ("Sošky a bytové doplňky", "dekorace", "Sošky, figurky a bytové doplňky", "vaza"),
    # v2 (12. 11. 2026): the breadth of Favi/Biano, one block per department
    "police": ("Police a poličky", "obyvaci-pokoj", "Police a nástěnné poličky", "knihovna"),
    "odkladaci-stolky": ("Odkládací stolky", "obyvaci-pokoj", "Odkládací a příruční stolky", "konferencni-stolek"),
    "konzolove-stolky": ("Konzolové stolky", "obyvaci-pokoj", "Konzolové stolky", "konferencni-stolek"),
    "truhly": ("Truhly", "obyvaci-pokoj", "Truhly a dřevěné bedny", "komoda"),
    "paravany": ("Paravány", "obyvaci-pokoj", "Paravány a dělicí stěny", "zaclony"),
    "biokrby": ("Biokrby a krby", "obyvaci-pokoj", "Biokrby, elektrické krby a krbové doplňky", "sofa"),
    "priborniky": ("Příborníky a kredence", "jidelna-a-kuchyne", "Příborníky, kredence a bufety", "komoda"),
    "barove-stoly": ("Barové stoly", "jidelna-a-kuchyne", "Barové stoly a pulty", "jidelni-stul"),
    "stojany-na-vino": ("Stojany na víno", "jidelna-a-kuchyne", "Stojany na víno a barové skříňky", "jidelna"),
    "loznicove-sestavy": ("Ložnicové sestavy", "loznice", "Ložnicové sestavy a komplety", "postel"),
    "boxspringy": ("Boxspringové postele", "loznice", "Boxspringové postele", "postel"),
    "calounene-postele": ("Čalouněné postele", "loznice", "Čalouněné postele", "postel"),
    "toppery-a-chranice-matraci": ("Toppery a chrániče matrací", "loznice", "Toppery, vrchní matrace a chrániče matrací", "matrace"),
    "satni-systemy": ("Šatní systémy", "predsin", "Šatní systémy a otevřené šatny", "skrin"),
    "stojany-na-saty": ("Stojany na šaty a ramínka", "predsin", "Stojany na šaty, ramínka a obaly na oděvy", "predsin"),
    "stojany-na-destniky": ("Stojany na deštníky", "predsin", "Stojany na deštníky", "predsin"),
    "nastenky-a-tabule": ("Nástěnky a tabule", "pracovna", "Nástěnky, magnetické a křídové tabule", "pracovna"),
    "trezory": ("Trezory", "pracovna", "Trezory a pokladny", "skrin"),
    "umyvadla": ("Umyvadla", "koupelna", "Umyvadla a umývátka", "koupelna"),
    "vany": ("Vany", "koupelna", "Vany a vanové sety", "koupelna"),
    "sprchove-kouty": ("Sprchové kouty", "koupelna", "Sprchové kouty, dveře a zástěny", "koupelna"),
    "sprchove-vanicky": ("Sprchové vaničky", "koupelna", "Sprchové vaničky", "koupelna"),
    "wc-a-bidety": ("WC a bidety", "koupelna", "Záchody, bidety a WC sedátka", "koupelna"),
    "vodovodni-baterie": ("Vodovodní baterie", "koupelna", "Umyvadlové, vanové a sprchové baterie", "koupelna"),
    "sprchove-sety": ("Sprchové sety a hlavice", "koupelna", "Sprchové sety, sloupy a hlavice", "koupelna"),
    "topne-zebriky": ("Topné žebříky", "koupelna", "Koupelnové radiátory a topné žebříky", "koupelna"),
    "kose-na-pradlo": ("Koše na prádlo", "koupelna", "Koše na prádlo", "koupelna"),
    "hrnce": ("Hrnce a sady nádobí", "kuchyne-a-stolovani", "Hrnce, kastroly a sady nádobí", "jidelna"),
    "panve": ("Pánve", "kuchyne-a-stolovani", "Pánve a woky", "jidelna"),
    "pekace-a-formy": ("Pekáče a formy na pečení", "kuchyne-a-stolovani", "Pekáče, zapékací mísy a formy na pečení", "jidelna"),
    "kuchynske-noze": ("Kuchyňské nože", "kuchyne-a-stolovani", "Kuchyňské nože a bloky na nože", "jidelna"),
    "prkenka": ("Prkénka na krájení", "kuchyne-a-stolovani", "Prkénka na krájení a servírovací desky", "jidelna"),
    "kuchynske-nacini": ("Kuchyňské náčiní", "kuchyne-a-stolovani", "Kuchyňské náčiní a pomůcky", "jidelna"),
    "talire": ("Talíře a jídelní servisy", "kuchyne-a-stolovani", "Talíře, misky a jídelní servisy", "jidelni-stul"),
    "hrnky-a-salky": ("Hrnky a šálky", "kuchyne-a-stolovani", "Hrnky, šálky a čajové servisy", "jidelni-stul"),
    "sklenice": ("Sklenice a karafy", "kuchyne-a-stolovani", "Sklenice, karafy a džbány", "jidelni-stul"),
    "pribory": ("Příbory", "kuchyne-a-stolovani", "Příbory a sady příborů", "jidelni-stul"),
    "tacy-a-podnosy": ("Tácy a podnosy", "kuchyne-a-stolovani", "Tácy, podnosy a etažéry", "jidelni-stul"),
    "skladovani-potravin": ("Dózy a skladování potravin", "kuchyne-a-stolovani", "Dózy, boxy na potraviny a vakuové skladování", "komoda"),
    "termosky-a-lahve": ("Termosky a láhve", "kuchyne-a-stolovani", "Termosky, termohrnky a láhve na pití", "jidelna"),
    "kuchynsky-textil": ("Kuchyňský textil", "kuchyne-a-stolovani", "Utěrky, zástěry a chňapky", "jidelni-stul"),
    "drezy": ("Kuchyňské dřezy", "kuchyne-a-stolovani", "Kuchyňské dřezy", "jidelna"),
    "kuchynske-baterie": ("Kuchyňské baterie", "kuchyne-a-stolovani", "Dřezové a kuchyňské baterie", "jidelna"),
    "odpadkove-kose": ("Odpadkové koše", "kuchyne-a-stolovani", "Odpadkové koše a třídění odpadu", "komoda"),
    "kuchynske-doplnky": ("Kuchyňské doplňky", "kuchyne-a-stolovani", "Kuchyňské doplňky a organizéry", "jidelna"),
    "kavovary": ("Kávovary", "spotrebice", "Kávovary a mlýnky na kávu", "jidelna"),
    "rychlovarne-konvice": ("Rychlovarné konvice", "spotrebice", "Rychlovarné konvice", "jidelna"),
    "mixery-a-roboty": ("Mixéry a kuchyňské roboty", "spotrebice", "Mixéry, šlehače a kuchyňské roboty", "jidelna"),
    "odstavnovace": ("Odšťavňovače", "spotrebice", "Odšťavňovače a lisy na citrusy", "jidelna"),
    "toustovace-a-grily": ("Topinkovače a kontaktní grily", "spotrebice", "Topinkovače, sendvičovače a kontaktní grily", "jidelna"),
    "fritezy": ("Fritézy", "spotrebice", "Fritézy a horkovzdušné fritézy", "jidelna"),
    "drobne-kuchynske-spotrebice": ("Drobné kuchyňské spotřebiče", "spotrebice", "Pekárny, vakuovačky, rýžovary a další spotřebiče", "jidelna"),
    "digestore": ("Digestoře", "spotrebice", "Digestoře", "jidelna"),
    "vysavace": ("Vysavače", "spotrebice", "Vysavače a parní čističe", "komoda"),
    "uprava-vzduchu": ("Ventilátory a čističky vzduchu", "spotrebice", "Ventilátory, čističky, zvlhčovače a ohřívače", "komoda"),
    "bodova-svitidla": ("Bodová svítidla", "svitidla", "Bodová a vestavná svítidla", "lustr"),
    "led-pasky": ("LED pásky", "svitidla", "LED pásky a profily", "lampa"),
    "led-panely": ("LED panely", "svitidla", "LED panely", "lustr"),
    "zarovky": ("Žárovky", "svitidla", "Žárovky a LED zdroje", "lampa"),
    "koupelnova-svitidla": ("Koupelnová svítidla", "svitidla", "Koupelnová svítidla a světla nad zrcadlo", "lustr"),
    "stinidla": ("Stínidla", "svitidla", "Stínidla na lampy a lustry", "lampa"),
    "prosteradla": ("Prostěradla", "textil", "Prostěradla", "povleceni"),
    "rolety-a-zaluzie": ("Rolety a žaluzie", "textil", "Rolety, žaluzie a plisé", "zaclony"),
    "garnyze": ("Garnýže", "textil", "Garnýže a kolejnice na záclony", "zaclony"),
    "detsky-textil": ("Dětský textil", "detsky-pokoj", "Dětské povlečení, deky a textil", "detsky-pokoj"),
    "tapety": ("Tapety", "dekorace", "Tapety a fototapety", "obraz"),
    "samolepky-na-zed": ("Samolepky na zeď", "dekorace", "Samolepky a dekorace na zeď", "obraz"),
    "pokojove-rostliny": ("Pokojové rostliny", "dekorace", "Pokojové rostliny", "kvetinac"),
    "difuzery-a-vune": ("Difuzéry a vůně", "dekorace", "Difuzéry, vonné tyčinky a vůně do bytu", "vaza"),
    "lucerny": ("Lucerny", "dekorace", "Lucerny", "vaza"),
    "vanocni-ozdoby": ("Vánoční ozdoby", "vanoce-a-svatky", "Vánoční ozdoby a koule", "vaza"),
    "umele-stromky": ("Umělé vánoční stromky", "vanoce-a-svatky", "Umělé vánoční stromky", "kvetinac"),
    "vanocni-osvetleni": ("Vánoční osvětlení", "vanoce-a-svatky", "Vánoční osvětlení a světelné řetězy", "lampa"),
    "adventni-dekorace": ("Adventní dekorace", "vanoce-a-svatky", "Adventní věnce, svícny a kalendáře", "vaza"),
    "betlemy": ("Betlémy", "vanoce-a-svatky", "Betlémy", "vaza"),
    "velikonocni-dekorace": ("Velikonoční dekorace", "vanoce-a-svatky", "Velikonoční dekorace", "vaza"),
    "grily": ("Grily", "zahrada", "Zahradní grily a příslušenství", "zahrada"),
    "ohniste-a-ohrivace": ("Ohniště a terasové ohřívače", "zahrada", "Ohniště, zahradní krby a terasové ohřívače", "zahrada"),
    "bazeny-a-virivky": ("Bazény a vířivky", "zahrada", "Bazény, vířivky a bazénové příslušenství", "zahrada"),
    "sauny": ("Sauny", "zahrada", "Sauny a infrasauny", "zahrada"),
    "trampoliny": ("Trampolíny", "zahrada", "Zahradní trampolíny", "zahrada"),
    "zahradni-domky": ("Zahradní domky a altány", "zahrada", "Zahradní domky, altány, pergoly a přístřešky", "zahrada"),
    "zahradni-boxy": ("Zahradní boxy", "zahrada", "Zahradní úložné boxy a truhly", "zahrada"),
    "skleniky-a-pestovani": ("Skleníky a pěstování", "zahrada", "Skleníky, vyvýšené záhony a pěstební nádoby", "kvetinac"),
    "substraty-a-hnojiva": ("Substráty a hnojiva", "zahrada", "Substráty, hnojiva a péče o rostliny", "kvetinac"),
    "zavlazovani": ("Zavlažování", "zahrada", "Konve, hadice a zavlažování", "zahrada"),
    "zahradni-dekorace": ("Zahradní dekorace", "zahrada", "Zahradní dekorace, sochy a ptačí budky", "zahrada"),
    "vinylove-podlahy": ("Vinylové podlahy", "podlahy-a-kovani", "Vinylové podlahy", "koberec"),
    "laminatove-podlahy": ("Laminátové podlahy", "podlahy-a-kovani", "Laminátové podlahy", "koberec"),
    "drevene-podlahy": ("Dřevěné podlahy", "podlahy-a-kovani", "Dřevěné podlahy a parkety", "koberec"),
    "pvc-a-linoleum": ("PVC a linoleum", "podlahy-a-kovani", "PVC podlahy a linoleum", "koberec"),
    "koberce-metraz": ("Koberce v metráži", "podlahy-a-kovani", "Koberce v metráži a zátěžové koberce", "koberec"),
    "podlahove-listy": ("Podlahové lišty", "podlahy-a-kovani", "Podlahové lišty, profily a podložky", "koberec"),
    "kliky-a-kovani": ("Kliky a kování", "podlahy-a-kovani", "Kliky na dveře a okna, kování a rozety", "predsin"),
    "nabytkove-uchytky": ("Nábytkové úchytky", "podlahy-a-kovani", "Nábytkové úchytky a knopky", "komoda"),
    "zasuvky-a-vypinace": ("Vestavné zásuvky a vypínače", "podlahy-a-kovani", "Vestavné a nábytkové zásuvky, vypínače", "lampa"),
    "skladove-regaly": ("Kovové a skladové regály", "domacnost", "Kovové, plastové a skladové regály", "knihovna"),
    "susaky-na-pradlo": ("Sušáky na prádlo", "domacnost", "Sušáky na prádlo", "komoda"),
    "zehlici-prkna": ("Žehlicí prkna", "domacnost", "Žehlicí prkna a potahy", "komoda"),
    "uklidove-pomucky": ("Úklidové pomůcky", "domacnost", "Mopy, kbelíky a úklidové pomůcky", "komoda"),
    "pro-miminka": ("Pro miminka", "detsky-pokoj", "Přebalovací pulty, ohrádky a doplňky pro miminka", "detsky-pokoj"),
    "detska-svitidla": ("Dětská svítidla", "detsky-pokoj", "Dětské lampy a noční světla", "lampa"),
    "detske-koberce": ("Dětské koberce", "detsky-pokoj", "Dětské a hrací koberce", "koberec"),
    "domecky-a-teepee": ("Domečky a teepee", "detsky-pokoj", "Dětské domečky, stany a teepee", "detsky-pokoj"),
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
# sheets 3 and 4 (Canva, 12. 11. 2026): icons for the v2 departments and categories
ICON.update({"kuchyne-a-stolovani": "hrnec", "spotrebice": "kavovar", "podlahy-a-kovani": "podlaha", "domacnost": "uklid",
             "vanoce-a-svatky": "vanocni-stromek", "hrnce": "hrnec", "panve": "panev", "pekace-a-formy": "hrnec",
             "kuchynske-noze": "noze", "prkenka": "noze", "kuchynske-nacini": "hrnec", "talire": "stolovani",
             "hrnky-a-salky": "stolovani", "sklenice": "stolovani", "pribory": "stolovani", "tacy-a-podnosy": "stolovani",
             "skladovani-potravin": "hrnec", "termosky-a-lahve": "stolovani", "kuchynsky-textil": "stolovani", "drezy": "drez",
             "kuchynske-baterie": "drez", "odpadkove-kose": "uklid", "kuchynske-doplnky": "noze", "kavovary": "kavovar",
             "rychlovarne-konvice": "kavovar", "mixery-a-roboty": "mixer", "odstavnovace": "mixer", "toustovace-a-grily": "kavovar",
             "fritezy": "mixer", "drobne-kuchynske-spotrebice": "mixer", "digestore": "kavovar", "vysavace": "uklid",
             "uprava-vzduchu": "kavovar", "umyvadla": "umyvadlo", "vany": "vana", "sprchove-kouty": "sprchovy-kout",
             "sprchove-vanicky": "sprchovy-kout", "wc-a-bidety": "wc", "vodovodni-baterie": "umyvadlo", "sprchove-sety": "sprchovy-kout",
             "topne-zebriky": "vana", "kose-na-pradlo": "susak", "bodova-svitidla": "bodovky", "led-pasky": "led-pasek",
             "led-panely": "bodovky", "zarovky": "zarovka", "koupelnova-svitidla": "bodovky", "stinidla": "lampa",
             "prosteradla": "povleceni", "rolety-a-zaluzie": "roleta", "garnyze": "zaclony", "tapety": "tapeta",
             "samolepky-na-zed": "tapeta", "pokojove-rostliny": "kvetinac", "difuzery-a-vune": "difuzer", "lucerny": "difuzer",
             "vanocni-ozdoby": "ozdoba", "umele-stromky": "vanocni-stromek", "vanocni-osvetleni": "led-pasek", "adventni-dekorace": "ozdoba",
             "betlemy": "vanocni-stromek", "velikonocni-dekorace": "vaza", "vanocni-dekorace": "ozdoba", "grily": "gril",
             "ohniste-a-ohrivace": "gril", "bazeny-a-virivky": "bazen", "sauny": "zahradni-domek", "trampoliny": "trampolina",
             "zahradni-domky": "zahradni-domek", "zahradni-boxy": "zahradni-domek", "skleniky-a-pestovani": "kvetinac", "substraty-a-hnojiva": "kvetinac",
             "zavlazovani": "kvetinac", "zahradni-dekorace": "kvetinac", "vinylove-podlahy": "podlaha", "laminatove-podlahy": "podlaha",
             "drevene-podlahy": "podlaha", "pvc-a-linoleum": "podlaha", "koberce-metraz": "koberec", "podlahove-listy": "podlaha",
             "kliky-a-kovani": "klika", "nabytkove-uchytky": "klika", "zasuvky-a-vypinace": "zarovka", "skladove-regaly": "knihovna",
             "susaky-na-pradlo": "susak", "zehlici-prkna": "susak", "uklidove-pomucky": "uklid", "ulozne-boxy-a-kose": "komoda",
             "police": "police", "odkladaci-stolky": "konferencni-stolek", "konzolove-stolky": "konferencni-stolek", "truhly": "komoda",
             "paravany": "zaclony", "lenosky": "lenoska", "priborniky": "kredenc", "barove-stoly": "barova-zidle",
             "stojany-na-vino": "kredenc", "vitriny": "kredenc", "loznicove-sestavy": "boxspring", "boxspringy": "boxspring",
             "calounene-postele": "boxspring", "toppery-a-chranice-matraci": "matrace", "satni-systemy": "skrin", "stojany-na-saty": "predsin",
             "stojany-na-destniky": "predsin", "nastenky-a-tabule": "pracovna", "trezory": "skrin", "pro-miminka": "prebalovaci-pult",
             "detska-svitidla": "lampa", "detske-koberce": "koberec", "domecky-a-teepee": "zahradni-domek", "detsky-textil": "povleceni"})

# products cheaper than this in a category are almost always accessories in the wrong place (a "postel" for 190 Kč is a sheet)
PRICE_FLOOR = {"rohove-sedacky": 4000, "sedacky": 2500, "pohovky": 2000, "kresla": 700, "postele": 1500, "matrace": 800, "rosty": 400,
               "satni-skrine": 1200, "komody": 900, "jidelni-stoly": 900, "jidelni-sety": 2000, "jidelni-zidle": 300, "barove-zidle": 400,
               "psaci-stoly": 800, "kancelarske-zidle": 700, "herni-kresla": 1200, "detske-postele": 1000, "obyvaci-steny": 2500,
               "tv-stolky": 700, "konferencni-stolky": 400, "zahradni-sestavy": 2500, "kuchynske-linky": 1500, "predsinove-steny": 1500,
               "koupelnove-skrinky": 500, "lustry": 250, "stojaci-lampy": 300, "koberce": 150,
               "boxspringy": 4000, "calounene-postele": 2500, "loznicove-sestavy": 5000, "vany": 2000, "umyvadla": 300,
               "sprchove-kouty": 1500, "sprchove-vanicky": 700, "wc-a-bidety": 400, "vodovodni-baterie": 300, "drezy": 500,
               "kuchynske-baterie": 300, "priborniky": 1500, "lenosky": 2000, "sauny": 5000, "trampoliny": 1000,
               "zahradni-domky": 2000, "bazeny-a-virivky": 300, "kavovary": 500, "vysavace": 500, "topne-zebriky": 800,
               "biokrby": 400, "trezory": 500, "digestore": 1000}

# ------------------------------------------------------------------ veto: not furniture / décor
VETO_TITLE = re.compile(
    r"\b(vrtack|bruska|sroubovak|pilk|pila\b|kladiv|naradi|hmozdin|sroub[uy]?\b|hrebik|barva na|lak na|lazur|penetrac|tmel|silikon\b|stetec(?! na peceni)|malirsk|valecek(?! na testo)|"
    r"dlazb(?!ic\w* (koberc|kobercov))|obklad|^(posuvn\w* |interierov\w* |vchodov\w* |balkonov\w* )?dvere\b|zarubn|\bzamek|lepidl|deštník|destnik|pantofl|backor|boxerk|"
    r"sifon|odpad\b|ventil\b|"
    r"cerpadl|kotel|bojler|"
    r"herbicid|fungicid|insekticid|pesticid|\bjed na|\bchlor|algicid|\bph (plus|minus)|bazenov\w* chemi|"
    r"sekack|krovinorez|pletivo|plotov|"
    r"zehlick(?!\w* prkn)|pracka|lednic|trouba|varn\w* desk|mycka|"
    r"hrack|puzzle(?! podlozk)|kniha|plysa|panenk|stavebnic|kocar|autosedack|parfem(?! do bytu)|kosmetik|krem\b|sampon|"
    r"krmiv|pamlsk|obojek|voditk|pro psy|pro kocky|pelisek|pelech|skrabadl|"
    r"nahradn\w* dil|nahradn\w* (nuz|filtr|sacek|kartac)|kolecka (?!na nabytek)|koleck\w* (pro|k|na) zidl|plynov\w* pist|podruck|kluzak|\bbaterie (aa|aaa|cr|lr|\d|do|pro)|\bbaterk|\bakumulator\w* (aa|\d|clank)|\bpowerbank|nabijeck|kabel\b|prodluzov|"
    r"poukaz|oblecen|bunda|tricko|mikina|kalhoty|ponozk|"
    r"zebrik(?!\w* (radiator|na rucnik))|schudk|"
    r"autoz|autoprisl|reproduktor|televiz(?!n\w* (stol|skrin|dek|komod))|notebook|tiskarn)", I)
VETO_PATH = re.compile(r"((?<!kuchynske )(?<!krbove )(?<!grilovaci )naradi|(?<!zahrada a )stavebnin(?!y [>|/,]\s*kovani)|technika|barvy|dlazb|obklad|(?<!sprchove )(?<!sprchov )(?<!na )dvere(?!.*(klik|kovani|rozet))|zarubn|"
                       r"hracky|hracky pro deti|knihy|pro skolaky|nahradni dily|zahradni naradi|ochrana rostlin|bazenova chemie|auto\b|"
                       r"zabezpeceni|zelezarstvi|elektronika|darkove poukazy|(?<!na )(?<!pro )obleceni|moda a styl|kojeni|zebriky|chovatel|pro zvirata|pro psy|pro kocky|mazlic)", I)

R = lambda s: re.compile(s, I)
# (category, pattern on the folded title). First match wins.
TITLE_RULES = [
    # v2 categories (12. 11. 2026)
    ("police", R(r"\bpolic[eiy]?\b|nastenn\w* polic|\bpolick|\bpolicka")),
    ("odkladaci-stolky", R(r"(odkladac|prirucn|kavov|sofa|boc)\w* (stolek|stolk|stol|stul)")),
    # brackets are not console tables: shelf brackets -> hardware, washbasin/countertop supports -> bathroom accessories
    ("kliky-a-kovani", R(r"\bkonzol\w* (na|pro|pod) polic|\bpolicov\w* konzol|\bnastenn\w* konzol(?!ov\w* stol)")),
    ("koupelnove-doplnky", R(r"\b(podpern|nosn|skryt)\w* (podpern\w* )?konzol|\bkonzol\w* (pro|pod|k|na) (desk|umyvad)")),
    ("konzolove-stolky", R(r"konzolov\w* (stolek|stolk|stol)|\bkonzol[ae]\b")),
    ("truhly", R(r"\btruhl[ay]\b|\btruhlic|\bbedna\b|\bbedn[ey]\b")),
    ("paravany", R(r"\bparavan|delic\w* (sten|panel|prick)|\bparaván")),
    ("biokrby", R(r"\bbiokrb|\bbio krb|elektrick\w* krb|\bkrb\b|krbov\w* (vlozk|nara|sada|zasten|kos|kamn)|kos na drev|\bkamna\b")),
    ("priborniky", R(r"\bpribornik|\bkredenc|\bbufet\b|\bbufety\b|\bsideboard|\bhighboard")),
    ("barove-stoly", R(r"barov\w* (stul|stol\b|stolek|stoly|pult|desk)")),
    ("stojany-na-vino", R(r"stojan\w* na vin|vinny regal|regal na vin|barov\w* (skrin|skrink)")),
    ("loznicove-sestavy", R(r"loznic\w* (sestav|komplet|set\b|souprav|program)")),
    ("boxspringy", R(r"boxspring\w*\b(?! ?(prosteradl|chranic|topper|povlec|potah|polstar))|box spring|kontinentaln\w* postel")),
    ("calounene-postele", R(r"calounen\w* (postel|lozk|manzelsk)")),
    ("toppery-a-chranice-matraci", R(r"\btopper|vrchn\w* matrac|chranic\w* matrac|matracov\w* chranic|nepropustn\w* (chranic|podlozk|prosteradl)|ochrann\w* potah na matrac")),
    ("satni-systemy", R(r"satn\w* system|satnov\w* (sten|system)|\bsatna\b|otevren\w* satn|systemy? do satn")),
    ("stojany-na-saty", R(r"stojan\w* na (saty|obleceni|odev)|\bramink|obal\w* na (odev|saty|obleceni)|pojizdn\w* (vesak|stojan)")),
    ("stojany-na-destniky", R(r"stojan\w* na destnik")),
    ("nastenky-a-tabule", R(r"\bnastenk|magneticka tabule|kridov\w* tabul|\btabule\b|korkov\w* (tabul|nastenk)|flipchart")),
    ("trezory", R(r"\btrezor|\bsejf|pokladn\w* schran|schranka na klice")),
    ("umyvadla", R(r"umyvadl(o|a|el|u)?\b(?! ?(se|s) skrin)|umyvatk|keramick\w* umyvadl|umyvadlov\w* misa|\bmisa na desku|\bdrez do koupeln")),
    ("vany", R(r"\bvan[ay]\b|\bvanu\b|akrylatov\w* van|volne stojic\w* van|rohov\w* van|asymetrick\w* van|obdelnikov\w* van|hydromasazn\w* van")),
    ("sprchove-kouty", R(r"sprchov\w* (kout|zasten|dver|stena|sten|box|kabin)|walk.?in|vanov\w* zasten|zasten\w* (na|k) van")),
    ("sprchove-vanicky", R(r"sprchov\w* (vanick|zlab)|\bvanick|odtokov\w* zlab|podlahov\w* zlab|\bzlab\w* (do sprch|sprchov)")),
    ("wc-a-bidety", R(r"\bwc\b(?! ?(kartac|stetk|drzak|papir|dopln|souprav|kos|osvezov|cistic|blok|predlozk|kobere|sada))|zachod|zavesn\w* wc|kombi ?wc|\bbidet|pisoar|\bklozet|instalacn\w* (modul|system)|predstenov|splachov\w* (tlacitk|nadrz)|\bsedatk|wc prkenk")),
    ("vodovodni-baterie", R(r"(vodovodn|umyvadlov|sprchov|vanov|stojankov|nastenn|termostatick|pakov|podomitkov|bidetov|panelakov|kohoutkov)\w* (\w+ ){0,2}bateri|bateri\w* (umyvadl|sprch|van|stojank|nastenn|bidet)")),
    ("sprchove-sety", R(r"sprchov\w* (set|sestav|hlavic|souprav|sloup|panel|hadic|tyc|ruzic|system)|hlavov\w* sprch|ruc\w* sprch|dest\w* sprch|\bsprcha\b|\bsprchy\b")),
    ("topne-zebriky", R(r"topn\w* zebrik|koupelnov\w* (radiator|topn\w* teles)|zebrik\w* (radiator|na rucnik)|susak na rucnik")),
    ("kose-na-pradlo", R(r"kos\w* na pradlo|pradeln\w* kos|kose na pradlo")),
    ("hrnce", R(r"\bpoklic|\bhrnec\b|\bhrnce\b|\bhrncu\b|\bhrncek\b|kastrol|rendlik|tlakov\w* hrn|sad\w* (nadobi|hrncu)|\bnadobi\b(?! ?(pro deti|detsk))|smaltovan\w* hrn|litinov\w* hrn|\bdusic")),
    ("panve", R(r"\bpanev|\bpanve|\bpanvi|\bwok\b|grilovac\w* panev|palacinkov\w* panev|litinov\w* panev")),
    ("pekace-a-formy", R(r"\bpekac|zapekac\w* (mis|form)|form\w* na (peceni|dort|muffin|chleb|babovk|bab|kolac|tartu|pizz|cukrovi|led)|dortov\w* (form|kruh)|plech\w* na peceni|\bbabovk\w* form|silikonov\w* form|\bforma\b|vykrajovatk|cukrarsk")),
    ("kuchynske-noze", R(r"\bnuz\b|\bnoz(e|u)\b|sad\w* noz|blok\w* na noz|\bbrousek|ostric\w* noz|santoku|\bsekacek|\bnuzky na (drub|bylin)|magneticka lista na noz")),
    ("prkenka", R(r"prken\w* (na krajeni|krajec|na pecivo|na sy)|krajec\w* prken|\bprkenko\b(?!.*(wc|zehl))|servirovac\w* (desk|prken)")),
    ("kuchynske-nacini", R(r"stetec na peceni|\bnacini|vareck|obracec|naberac|\bmetla|struhad|\blis na (cesnek|brambor)|cednik|\bsitko|otvirac|\bloupac|kuchynsk\w* (pomuck|vah|teplomer|nuzky|sada)|\bsterk|valecek na testo|kuchynsk\w* vaha|\bkleste na|\bmlynek(?! na kavu)|odmerk|\bkrajec(?!.*prken)|spiralizer|\bmandolin|vykrajovac")),
    ("talire", R(r"\bcukrenk|\bmlekovk|\bmisa\b|\btalir|jideln\w* (servis|souprav)|servis (talir|jideln)|\bmisk[ay]\b(?!.*(pro (psy|pejsk|kock|zvir)|krmn))|\bmisek|\bmisky\b|salatov\w* mis|\bmis[ay] na|polevkov|dezertn\w* talir|\bpodtalir")),
    ("hrnky-a-salky", R(r"\bhrnek|\bhrnky|\bhrnecek|\bhrnk[uy]\b|\bsalek|\bsalky|\bsalk[uy]\b|kavov\w* (servis|souprav)|cajov\w* (servis|souprav|konvic)|\bkonvick|\bkonvice na caj|french press|\bmoka|\bdzezv|\bpresovac")),
    ("sklenice", R(r"barmansk|sklenic|\bkaraf|\bdzban|\bpohar|odlivk|\bsklenk|\bsklenky|\bflute\b|barov\w* sklo")),
    ("pribory", R(r"\bpribor|\blzic|\bvidlick|jideln\w* nuz|\bhulk[ay] na")),
    ("tacy-a-podnosy", R(r"\btac\b|\btacy\b|\btacek|\bpodnos|\betazer|servirovac\w* (tac|podnos|misa)")),
    ("skladovani-potravin", R(r"\bdoz[ayu]?\b|\bdozy\b|\bdozick|vakuov\w* (doz|nadob|vik|sack|pump)|\bchlebnik|box\w* na (potrav|svacin|chleb|jidlo|obed)|skladovan\w* potravin|zavarovac|krabick\w* na (jidlo|potrav)|svacinov\w* box|gastronadob|\bobedar|\bkoreni\w* (doz|sada)|\bslanka|\bpeprenk|\bkorenk")),
    ("termosky-a-lahve", R(r"termosk|termohrn|termo ?hrnek|\blahev|\blahve|\bbidon|termobox|termotask")),
    ("kuchynsky-textil", R(r"kuchynsk\w* (uterk|zaster|chnapk|textil|rukavic)|\buterk|\bzaster|\bchnapk|podlozk\w* pod hrn")),
    ("drezy", R(r"\bdrez(?!ov\w* bateri)|granitov\w* drez|nerezov\w* drez|\bdrezy")),
    ("kuchynske-baterie", R(r"(drezov|kuchynsk)\w* (\w+ ){0,2}bateri|bateri\w* (drez|kuchyn|na drez)")),
    ("odpadkove-kose", R(r"odpadkov\w* kos|kos\w* na (odpad|trideni|smeti|trideny)|trideni odpadu|pedalov\w* kos|vestavn\w* kos|\bkos\w* na trideny")),
    ("kuchynske-doplnky", R(r"stojan\w* na (koreni|papirov|ubrousk|noz|pokliček|poklic|vareck|kuchynsk)|drzak\w* na (papirov|kuchynsk|utěrk|uterk|ubrous)|\bodkapavac|susak\w* na nadobi|organizer\w* (do zasuv|na pribor)|\bpribornik do zasuv|vlozk\w* do zasuv|\bkorenk|\bubrousnik")),
    ("kavovary", R(r"kavovar|\bespresso\b(?! salek)|mlynek na kavu|kapslov|\bpakov\w* kavovar|automaticky kavovar|\bnapenovac")),
    ("rychlovarne-konvice", R(r"rychlovarn|varn\w* konvic|elektrick\w* konvic")),
    ("mixery-a-roboty", R(r"\bmixer|smoothie|kuchynsk\w* robot|ponorn\w* mix|\bslehac|food processor|elektrick\w* sekac|multifunkcn\w* hrnec|\bthermomix|\bmlynek na maso")),
    ("odstavnovace", R(r"odstavnov|\bjuicer|lis\w* na citrus|elektrick\w* lis")),
    ("toustovace-a-grily", R(r"topinkov|toustovac|kontaktn\w* gril|sendvicovac|vaflovac|elektrick\w* gril|stoln\w* gril|raclett")),
    ("fritezy", R(r"\bfritez|airfryer|air fryer|horkovzdusn\w* (fritez|hrn)")),
    ("drobne-kuchynske-spotrebice", R(r"pekarn\w* (na )?chleb|domaci pekarn|ryzovar|pomalovar|slow cooker|vakuovack|svarec\w* (folii|potrav)|elektrick\w* (hrnec|wok|panev)|indukcn\w* varic|\bvaric\b|mikrovln|parni hrnec|sous vide|zmrzlinovac|dehydrat|susick\w* (ovoce|potravin|hub)|jogurtovac|vyrobnik (sody|zmrzl|ledu|popcorn)|popcornovac|\bvaha\b|kuchynsk\w* vah")),
    ("digestore", R(r"digestor|odsavac\w* par")),
    ("vysavace", R(r"vysavac|robotick\w* vysav|tycov\w* vysav|parni cistic|parn\w* mop|myc\w* oken|cistic\w* oken|\bmyc\w* podlah")),
    ("uprava-vzduchu", R(r"ventilator|cistick\w* vzduch|zvlhcovac|odvlhcov|mobiln\w* klimatiz|\bklimatizac|\bohrivac(?! vody)|\btopidl|primotop|konvektor|olejov\w* radiator|teplovzdusn\w* ventil")),
    ("bodova-svitidla", R(r"bodov\w* (svitid|svetl)|\bspoty?\b(?!.*\b(polstr|sedak))|\bbodovk|vestavn\w* (svitid|bodov|led)|podhledov\w* (svitid|bod)|listov\w* system|\bspot\w* svitid")),
    ("led-pasky", R(r"led pas|svetel\w* pas|\bpasek led|led strip|led profil|hlinikov\w* profil|\bled pásk|profil pro led|napajec\w* (zdroj|pro led)|led zdroj")),
    ("led-panely", R(r"led panel")),
    ("zarovky", R(r"zarovk|zarivk|\bled zdroj|\bled trubic|\be27\b|\be14\b|\bgu10\b|\bmr16\b|\bg9\b|filament")),
    ("koupelnova-svitidla", R(r"koupelnov\w* (svitid|svetl|lamp|led)|svitidl\w* (do|nad) koupeln|svetl\w* (nad|k) zrcadl|osvetleni zrcadl")),
    ("stinidla", R(r"\bstinidl|\bpaplat")),
    ("prosteradla", R(r"prosteradl|napinac\w* prost|jersey prost|frote prost")),
    ("rolety-a-zaluzie", R(r"zaluzi|\brolet|\bplise|\bpliss|den.?noc rolet|textiln\w* rolet|okenn\w* (stineni|rolet)|\bmarkyzet")),
    ("garnyze", R(r"garnyz|kolejnic\w* (na zaclon|stropn|zaclon)|zaclonov\w* (kolejnic|tyc)|\btyc\w* na zaclon|\bkoncovk\w* garnyz")),
    ("detsky-textil", R(r"detsk\w* (povleceni|prikryvk|polstar|deck|dek[ay]|osusk|rucnik|textil|prosteradl|mantinel)|povleceni (do postylk|pro deti|detsk)|do postylky|\bmantinel|zavinovack|\bspacak pro deti|\bfusak")),
    ("tapety", R(r"\btapet|fototapet|vliesov\w* tapet")),
    ("samolepky-na-zed", R(r"samolepk\w* (na zed|na stenu|dekorac|na nabytek)|samolepic\w* (dekor|tapet)|\bsamolepk|nalepk\w* na zed|\bsablon\w* na zed")),
    ("pokojove-rostliny", R(r"pokojov\w* rostlin|\borchidej|\bmonster|\bfikus|\bsukulent|\bkaktus|\bdracen|zamiokulk|sansevier|\bpothos|filodendr|philodendr|kalanchoe|anthurium|spathiphyl|\bcalathe|\bsefler|\bbonsai|\balocasi|\bhoya\b|\bpilea|kapradin|\bbromeli")),
    ("difuzery-a-vune", R(r"\bdifuzer|vonn\w* (difuz|tycink|olej|vosk|sacek|kamen|svic)|aromalamp|aroma ?difuz|vune do (bytu|domu)|bytov\w* (parfem|vune)|\bvonne|esencialn\w* olej|\bkadidl|\bvonna")),
    ("lucerny", R(r"\blucern")),
    ("vanocni-ozdoby", R(r"ozdob\w* na (strom|stromecek|vanocn)|vanocn\w* (ozdob|koul|bank|spick|zvonk|zvonek|figurk)|spic\w* na strom|\bbanky\b|sklenen\w* ozdob")),
    ("umele-stromky", R(r"umel\w* (vanocn\w* )?(stromek|stromecek|jedl|smrk|smrcek|borovic|stromy)|vanocn\w* strom(ek|ecek|y)?\b|stojan\w* na (vanocn\w* )?strom")),
    ("vanocni-osvetleni", R(r"vanocn\w* (osvetl|svetel|retez|led|svetylk|svetl)|svetel\w* retez|led (svetel\w* )?retez|svetel\w* zaves|led (figur|zaves|sob|hvezd|vlock)|svitic\w* (sob|hvezd|vlock|dekorac)|venkovn\w* vanocn")),
    ("adventni-dekorace", R(r"advent|\bvenec\b|\bvence\b|vanocn\w* venec")),
    ("betlemy", R(r"\bbetlem")),
    ("velikonocni-dekorace", R(r"velikonoc|kraslic|\bpomlazk|velikonocn")),
    ("grily", R(r"\bgril\b|\bgrily\b|\bgrilu\b|\bgrilem\b|zahradn\w* gril|plynov\w* gril|kotlov\w* gril|elektrick\w* zahradn\w* gril|grilovac\w* (nara|sada|nastroj|kleste|desk|rost|kamen|plech)|\budirn|pizza pec|pec na pizz|\bkamado|\bbbq\b|\bplancha|dreven\w* uhli|grilovac|na grilov")),
    ("ohniste-a-ohrivace", R(r"ohnist|zahradn\w* krb|kos na ohen|venkovn\w* krb|terasov\w* (ohriv|topid|zaric)|plynov\w* (ohrivac|zaric)|\bpalenist|\bfire ?pit")),
    ("bazeny-a-virivky", R(r"\bbazen(?!\w* (chemi|filtr|cerpadl|vysavac|teplomer|plovak|chlor))|virivk|\bjacuzzi|nafukovac\w* (bazen|virivk)|bazenov\w* (folie|plachta|schod|zebrik|sprch|kryt|podlozk)|solarn\w* (sprch|ohrev)|zahradn\w* sprch|zastresen\w* bazen")),
    ("sauny", R(r"\bsaun|infrasaun|\bsaunov")),
    ("trampoliny", R(r"trampolin")),
    ("zahradni-domky", R(r"zahradn\w* (domek|domky|domku|chatk|altan|pristres|pavilon|stan)|\baltan|\bpergol|\bpristres|domek na naradi|\bcarport|\bpartystan|\bnuzkov\w* stan|\bgazebo")),
    ("zahradni-boxy", R(r"zahradn\w* (box|truhl|ulozn)|box na (podusky|polstr|sedak|naradi)|ulozn\w* (box|truhl)\w* (na zahrad|venkovn)|venkovn\w* (box|truhl)|obal\w* na zahradn|plachta na (nabytek|zahradn)")),
    ("skleniky-a-pestovani", R(r"\bsklenik|parenist|foliovn\w* (sklenik|tunel)|foliovnik|vyvysen\w* zahon|\bzahon|pestebn\w* (nadob|truhl|misk|sad|box|stol|regal)|\bkompost|\bsazenic")),
    ("substraty-a-hnojiva", R(r"substrat|\bhnojiv|\bzemina|\bmulc|\bkura\b|\brasel|\bkeramzit|\bperlit|\bbiohum|aktivator\w* (kompost|pud)|vyziv\w* rostlin|\bosiv|\bsemen(a|ka)\b")),
    ("zavlazovani", R(r"\bzalevac|\bkonev|konve\b|zavlazov|kapkov\w* (zavlaz|hadic)|postrikov|zahradn\w* hadic|rozstrikov|\bhadic\w* (na|zahrad|navijak)|navijak na hadic|sud na (vodu|destov)|nadrz na destov")),
    ("zahradni-dekorace", R(r"zahradn\w* (dekorac|soch|trpasl|zapich|fontan|zrcadl|hodin|teplomer|vetrnik)|\btrpaslik|\bfontan|ptac\w* (budk|krmitk|napajedl)|\bkrmitk|\bbudka|\bvetrnik|zvonkohr")),
    ("vinylove-podlahy", R(r"vinyl\w* (podlah|dilc|lamel|prkn|desk)|\bspc\b|\blvt\b|klikac\w* vinyl|lepen\w* vinyl|vinylov\w* (dlazb|dlaždic)|\bvinyl\b")),
    ("laminatove-podlahy", R(r"laminat\w* (podlah|plovouc|lamel)|plovouc\w* podlah|\blaminat\b(?! ?(pracovn|desk|kuchyn))")),
    ("drevene-podlahy", R(r"dreven\w* podlah|dubov\w* (podlah|parket|prkn)|\bparket|masivn\w* podlah|vicevrstv\w* podlah|korkov\w* podlah|drevoplast")),
    ("pvc-a-linoleum", R(r"\bpvc podlah|podlahov\w* pvc|\blino\b|linole|\bpvc\b(?=.*(\d+ ?cm|\bm2|metraz|sire|role|sirk))|\bmarmoleum|\bvinylova podlah\w* v roli")),
    ("koberce-metraz", R(r"koberc\w* (v metrazi|metraz|na metry|z role|zatezov)|metrazov\w* koberc|zatezov\w* koberc|\bkobercov\w* (ctverc|dlazdic)|umel\w* trav")),
    ("podlahove-listy", R(r"podlahov\w* (list|profil|soklov|podlozk)|soklov\w* list|prechodov\w* (list|profil)|podlozk\w* pod (podlah|vinyl|laminat|plovouc)|ukoncovac\w* (list|profil)|\blist[ay] (k|na) podlah|kotvic\w* list|schodov\w* (hran|profil)")),
    ("kliky-a-kovani", R(r"\bklik[ayu]\b|klik\w* (na dvere|na okn|dverni|okenni|s rozet|se stit)|dvern\w* (kovani|klik|stit|rozet|zarazk)|okenn\w* klik|\bkovani\b|\brozet[ay]?\b|\bzaslepk|\bstit (k|na) klik|\bdverni madl|madl\w* na dvere|zarazk\w* (dveri|na dvere)")),
    ("nabytkove-uchytky", R(r"uchytk|nabytkov\w* (knopk|uchyt|kovani|nozk|kolecka)|\bknopk|nozk\w* (na|k|pro) nabytek|nabytkov\w* nozk")),
    ("zasuvky-a-vypinace", R(r"vypinac|vestavn\w* zasuvk|nabytkov\w* zasuvk|zasuvk\w* (do (stolu|desky|desk|nabytk|pracovni)|vysuvn|vestav|vyklopn)|zasuvkov\w* (blok|veze|vez|panel)|\busb zasuvk")),
    ("skladove-regaly", R(r"(kovov|skladov|garazov|dilensk|plastov|policov|zinkovan|bezsroubov)\w* regal|regal\w* (do garaz|do sklep|do dilny|skladov|kovov|plastov|policov|bezsroub)|regalov\w* system")),
    ("susaky-na-pradlo", R(r"susak\w* (na pradlo|pradla|na balkon|na radiator|nastenn|stropn|vezov|stojanov|kridl|venkovn|zahradn)|susic\w* (na pradlo)|\bsusak\b(?!.*(nadob|rucnik|bot|vlas))|\bkolicky na pradlo|\bsnura na pradlo")),
    ("zehlici-prkna", R(r"zehlic\w* prkn|potah\w* na zehlic|\bzehlic\w* (desk|podlozk)")),
    ("uklidove-pomucky", R(r"\bmop\b|\bmopy\b|\bmopu\b|\bkbelik|\bsmetak|\blopatk|\bkoste\b|\bkostet|uklidov\w* (sad|voz|pomuck|souprav|hadr|uterk)|\bhadr(y|u|ik|iky)?\b(?! ?kobere)|\bprachovk|sterk\w* na okn|\bstěrk|mikrovlakn\w* (uterk|hadr)|\bhoub[ay] na nadobi|\bstetk\w* na (nadobi|lahv)")),
    ("pro-miminka", R(r"prebalovac\w* (pult|komod|podlozk|stul|nastavec|pultik|desk)|\bohradk|\bmiminko\b|pro miminka|pro novorozen|zabran\w* (na schod|ke schod|do dveri|na postel)|detsk\w* zabran|\bhrazdic|zabranka na postel|\bbaby box")),
    ("detska-svitidla", R(r"detsk\w* (lamp|svitid|svetl|lampick|nocn\w* svetl|stropn|lustr)|nocni svetylko|\bnocni svetlo|svitidl\w* (do|pro) detsk")),
    ("detske-koberce", R(r"detsk\w* (koberec|kobere|koberc|predlozk)|koberec (do detsk|pro deti|hraci)|hraci (koberec|podlozk)|penov\w* (puzzle )?podlozk")),
    ("domecky-a-teepee", R(r"\bteepee|\btipi\b|detsk\w* (domek|domecek|stan|stanek)|domek pro deti|domecek pro deti|hraci (domek|domecek|stan)|zahradn\w* domecek pro deti|\bpiskoviste")),
    # textiles that name a piece of furniture ("povlečení NA postel", "potah NA sedačku") — before furniture
    ("povleceni", R(r"povleceni|povlak\w* na (perin|prikryv)|potah\w* (na )?matrac(?!.*chranic)|povlak\w* na matrac")),
    ("potahy-na-nabytek", R(r"^(\w+ ){0,2}potah(?!\w* (na )?matrac)|potah\w* na (sedac|zidl|kresl|pohov|gauc|rohov|tabur)|napinac\w* potah|navlek\w* na (sedac|zidl|kresl|pohov)|prehoz\w* na (sedac|gauc|pohov)")),
    ("polstare-na-zahradni-nabytek", R(r"(polstar|polstr|podsedak|sedak)\w* (na|pro|k) (zahradn|zidl|lehatk|lavic|houpac|kresl|palet)|podsedak|sedak na zidl|polstr na lehatk")),
    ("prikryvky-a-polstare", R(r"prikryvk|\bperin|(zdravotn|anatomick|ortopedick|ergonomick)\w* polstar|polstar\b.{0,50}\b(40 ?x ?(60|70|80)|50 ?x ?(60|70)|70 ?x ?90)|\bpillow|polstar\w* (na spani|anatomick|ortoped|z pametov|pametov)|spaci polstar|polstar \d0 ?x ?\d0(?! ?cm.*dekor)|chranic\w* polstar")),
    ("dekorativni-polstare", R(r"dekorac\w* polstar|polstar\w* (dekorac|s vyplni|45 ?x ?45|40 ?x ?40|50 ?x ?50|30 ?x ?50)|povlak\w* (\w+ ){0,3}na (\w+ ){0,2}polstar|^(\w+ ){0,2}polstar(?!ov)|polstark|povlak\w* (krepov|bavln|satenov|dekorac)")),
    ("deky-a-prehozy", R(r"\bdek[ay]\b|\bdeku\b|\bdeck|\bpled|prehoz|beranek deka")),
    ("rucniky-a-osusky", R(r"rucnik|osusk|zupan|osuska")),
    ("ubrusy-a-prostirani", R(r"\bubrus|behoun na stul|stolni behoun|prostirani|ubrousk")),
    ("zaclony-a-zavesy", R(r"zaclon(?!ov\w* (kolejnic|tyc))|\bzaves(y|u|em|u)?\b|vitrazk|zatemnovac\w* zaves")),
    ("behouny-a-predlozky", R(r"\bbehoun|predlozk|rohozk|koupelnov\w* (koberec|koberecek)")),
    ("koberce", R(r"\bkoberec|\bkoberc|\bkobere")),
    # children (before generic furniture)
    ("detske-postele", R(r"detsk\w* (postel|postylk|lozk)|patrov\w* postel|postel pro deti|domeckov\w* postel|\bpostyl|kolebk|kolisk|junior postel|postel (s|se) skluzavk|vyvysen\w* postel")),
    ("detske-pokoje", R(r"(detsk|studentsk)\w* (pokoj|sestav)")),
    ("detske-stolky-a-zidle", R(r"(detsk|studentsk|rostouc)\w* (stolecek|stolek|stolick|stul|stol|zidlick|zidl|kreslick|kreslo|sedack)")),
    ("detske-skrine-a-ulozne-boxy", R(r"detsk\w* (skrin|komod|regal|knihovn|polic|satn)|(organizer|organizer|box|kos|truhla|regal) na hrack")),
    ("detske-dekorace", R(r"(do|pro) detsk\w* pokoj|detsk\w* (dekorac|obraz|samolepk|tapet|vesak|hodiny)")),
    # office & gaming
    ("herni-kresla", R(r"hern\w* (kresl|zidl|stul)|gaming")),
    ("kancelarske-zidle", R(r"kancelarsk\w* (zidl|kresl)|pracovn\w* zidl|zidl\w* (k pc|k pocitac|na kolecka)|otocn\w* (zidl|kresl)|konferencn\w* zidl|ergonomick\w* zidl|balancni zidl|klekack")),
    ("kancelarske-skrine", R(r"\bkontejner\b|kancelarsk\w* (skrin|kontejner|regal)|kontejner (pod stul|kancel|s zasuvk)|spisov\w* skrin")),
    ("psaci-stoly", R(r"(psac|pracovn|pc|kancelarsk|pocitacov)\w* (stul|stol\b|stolek)|vyskove (stavitel|nastavitel)\w* stul|stul (pod|na) (pc|pocitac|notebook)|\bpsaci\b")),
    # dining
    ("jidelni-sety", R(r"jideln\w* (set|sestav|souprav)|stul (a|\+|se|s) (\d+|dvema|ctyrmi|sesti) zidl|\d+ ?x ?zidl.*stul|stul.*\d+ ?x ?zidl")),
    ("barove-zidle", R(r"barov\w* (zidl|stolick|stolic|kresl)|barova\b|barove\b")),
    ("servirovaci-stolky", R(r"servirovac\w* (stol|vozik)|\bservirovak|barov\w* vozik")),
    ("kuchynske-linky", R(r"kuchyn\w* (link|sestav|skrin|blok|ostruvek|regal)|(horni|dolni|spodni)\w* (rohov\w* |policov\w* |drezov\w* )?skrink|skrink\w* (horni|dolni|spodni)|skrink\w* (na|pro) (vestavn|troub|mycku|lednic)|drezov\w* skrin|(horni|dolni|rohov\w*) kuchyn\w* skrin|kuchyne \d{3}|potravinov\w* skrin|\bspizirn")),
    # garden (before chairs/tables/sofas)
    ("houpacky-a-site", R(r"houpac\w* (sit|kresl|lehatk)|zahradn\w* houpac|zavesn\w* (kresl|houpac)|\bhoupacka")),
    ("lehatka", R(r"lehatk|zahradn\w* (lehatk|lehatko)|\bsezlong\w* zahrad")),
    ("zahradni-sestavy", R(r"zahradn\w* (sestav|souprav|\bset\b|lounge|sedack|sedaci|nabytek)|ratanov\w* (sestav|souprav|set|nabytek)|balkonov\w* (set|sestav|souprav)|lounge (set|sestav)|venkovn\w* (sedac|sestav)")),
    ("zahradni-stoly", R(r"(zahradn|balkonov|venkovn|kempinkov)\w* (stul|stol\b|stolek|stolk)")),
    ("zahradni-zidle", R(r"(zahradn|balkonov|venkovn|kempinkov|ratanov)\w* (zidl|kresl|lavic)|skladac\w* zahradn|adirondack")),
    ("slunecniky-a-zasteny", R(r"slunecnik|stinic\w* placht|plachta proti slunci|markyz|(balkonov|zahradn)\w* (zasten|paravan|clona)|zasten\w* na balkon|stojan na slunecnik")),
    # living room
    ("lenosky", R(r"\blenosk|\bsezlong(?!\w* zahrad)|\brecamier")),
    ("rohove-sedacky", R(r"rohov\w* (sedac|pohov|gauc|souprav)|sedac\w* (souprav\w* )?(do l|do u|ve tvaru)|\bu sedac|\bl sedac|\brohovka|rohova\b.*\bsouprav")),
    ("sedacky", R(r"sedac\w* souprav|\bsedack|\bsedacku|\bsedacky|sedaci (sestav|blok)|modulov\w* (sedac|sofa)|\bsofa\b.*\b(3|4|tri|ctyr)")),
    ("pohovky", R(r"pohovk|\bgauc|kanape|\bsofa\b|rozkladac\w* (sofa|pohov)|\bdivan|\bvalenda")),
    ("taburety-a-sedaci-vaky", R(r"taburet|\bpuf\b|\bpufy|\bpufik|sedac\w* vak|sedaci pytel|\bpodnozk|\bpodnoz\b")),
    ("kresla", R(r"kresl|\busak|relaxac\w* kresl|houpac\w* kresl")),
    ("tv-stolky", R(r"\btv box|\btv\b.*(stol|skrin|komod|lavic|regal|nabytek|sten)|televizn\w* (stol|skrin|komod)|(stolek|skrinka|komoda|lavice) (pod|na) (tv|televiz)")),
    ("obyvaci-steny", R(r"obyvac\w* (sten|sestav|nabytek|program)|nabytkov\w* (sestav|sten)|\bobyvak\b")),
    ("vitriny", R(r"vitrin")),
    ("konferencni-stolky", R(r"konferencn\w* (stolek|stolk|stol|stul)|stolek (do obyvak|ke gauc|k sedac)")),
    # bedroom
    ("toaletni-stolky", R(r"(toaletn|kosmetick)\w* (stolek|stol)|\btoaletk")),
    ("nocni-stolky", R(r"nocn\w* (stolek|stol|skrin)")),
    ("rosty", R(r"\brost(y|u|em)?\b(?!.*\bs rostem)|lamelov\w* rost|postelov\w* rost")),
    ("matrace", R(r"\bmatrac|\bpristylk")),
    ("postele", R(r"\bpostel|\blozk|jednoluzk|dvouluzk|manzelsk\w* (postel|lozk)|\bloznice\b")),
    ("satni-skrine", R(r"satn\w* skrin|skrin (s posuv|s otoc|s dverm|se zrcadl|s zrcadl)|vestavn\w* skrin|\bskrin\b|\bskrine\b|\bskrin\w* na saty|\bsatnik")),
    ("komody", R(r"komod|pradelnik|\bkomoda")),
    # hallway
    ("botniky", R(r"botnik|(skrin|skrink|regal|stojan|lavic|polic)\w* na (boty|obuv)")),
    ("vesaky", R(r"vesak|vesakov\w* (sten|panel)|stojan\w* na kabat|nemy sluha|\bhacky na")),
    ("predsinove-steny", R(r"predsin|predsinov")),
    # bathroom
    ("koupelnove-skrinky", R(r"desk\w* pod umyvadl|koupelnov\w* (skrin|skrink|sestav|nabytek|regal|polic|komod|galerk)|skrink\w* pod umyvadl|skrin\w* pod umyvadl|\bgalerk|umyvadl\w* se skrink|(skrinka|skrin) (do|v) koupeln")),
    ("koupelnove-doplnky", R(r"davkovac mydl|drzak (na kartack|na rucnik|toaletn|na wc|na papir)|mydelnic|stetka|koupelnov\w* (doplnk|sada|set)|kelimek na (zubni )?kartac|pohar\w* na (zubni )?kartac|drzak\w* na (zubni )?kartac|davkovac\w* (mydl|saponat)|wc (kartac|stetk|souprav|drzak)|drzak\w* na toaletn|\bpolick\w* do sprch|\bstetk\w* na wc")),
    # tables / chairs / shelves (generic, after the specific ones)
    ("jidelni-stoly", R(r"jideln\w* (stul|stol\b)|rozkladac\w* (stul|stol\b)|\bstul\b|\bstoly\b|\bstol\b")),
    ("jidelni-zidle", R(r"jideln\w* zidl|\bzidl|\bzidle|\bstolick")),
    ("lavice", R(r"\blavic")),
    ("knihovny-a-regaly", R(r"knihovn|regal")),
    # lighting
    ("venkovni-svitidla", R(r"(venkovn|zahradn|solarn)\w* (svitid|svetl|lamp|led|osvetl)")),
    ("dekoracni-osvetleni", R(r"svetel\w* (retez|zaves|dekorac)|led (retez|zaves|dekorac|figur|vlock)|svetylk|dekorac\w* (svetl|osvetl)")),
    ("stojaci-lampy", R(r"stojac\w* (lamp|svitid)|stojanov\w* lamp|oblouk\w* lamp")),
    ("stolni-lampy", R(r"stoln\w* (lamp|svitid)|nocn\w* lamp|lampick")),
    ("nastenna-svitidla", R(r"nastenn\w* (svitid|svetl|lamp)|\bapliky?\b")),
    ("lustry", R(r"\blustr|zavesn\w* (svitid|svetl|lamp|led)")),
    ("stropni-svitidla", R(r"stropn\w* (svitid|svetl|lamp|led)|plafon|\bzaric")),
    # décor
    ("vanocni-dekorace", R(r"vanocn|stromecek|\bsnehulak|\bmikulas|\bsob\b|\bandel")),
    ("zrcadla", R(r"zrcadl")),
    ("ramy-na-fotky", R(r"(ram|ramecek|ramecky) na (foto|obraz)|fotoram|\bramecek|\bramecky|fotoalb")),
    ("obrazy", R(r"\bobraz|plakat|\bprint\b|reprodukc|tisk na platn|fotoobraz|\bplatno\b|\bcanvas")),
    ("nastenne-dekorace", R(r"nastenn\w* dekorac|dekorac\w* na zed|makram|kovov\w* dekorac\w* na")),
    ("hodiny", R(r"\bhodiny|\bbudik")),
    ("kvetinace", R(r"kvetinac|obal na kvetin|\btruhlik|stojan na kvetin|zardinier")),
    ("vazy", R(r"\bvaz[ay]?\b|\bvazu\b|vazicka")),
    ("umele-kvetiny", R(r"umel\w* (kvet|rostlin|strom|kytk|orchid|travy|palm|vetev)|dekorac\w* (kvet|vetev)|susen\w* kvet|\bkytice")),
    ("svicky-a-svicny", R(r"\bsvick|svicn|svicen|cajov\w* svic")),
    ("ulozne-boxy-a-kose", R(r"ulozn\w* (box|kos|krabic|vak)|\bkosik|\bkos\b|\bkose\b|proutěn|organizer|\bbox na|vakuov\w* (vak|obal)|textiln\w* box|\bsperkovnic")),
    ("sosky-a-doplnky", R(r"\bsosk|figurk|\bsoch|dekorac\w* (predmet|misa|misk|socha)|\bdekorace\b|\bdekoracni misa")),
    # leftover lighting words
    ("stropni-svitidla", R(r"\bsvitidl|\bsvetlo\b")),
    ("stolni-lampy", R(r"\blampa\b|\blampy\b")),
    # bare "Stolek Ben" / "Brand stolek X" = coffee table; last, so "Noční stolek" ties go to the specific rule above
    ("konferencni-stolky", R(r"^(\w+ ){0,1}stolek\b")),
]

# shop category path -> category, when the title alone said nothing (paths are folded too)
PATH_RULES = [
    ("police", R(r"police a policky|\bpolice\b")),
    ("odkladaci-stolky", R(r"odkladaci stol|prirucni stol")),
    ("konzolove-stolky", R(r"konzolov")),
    ("paravany", R(r"paravan")),
    ("biokrby", R(r"krby|biokrb|krbov")),
    ("priborniky", R(r"pribornik|kredenc|sideboard")),
    ("barove-stoly", R(r"barove stoly")),
    ("stojany-na-vino", R(r"stojany na vino")),
    ("loznicove-sestavy", R(r"loznicove sestavy|loznicove komplety")),
    ("boxspringy", R(r"boxspring|kontinentalni postel")),
    ("calounene-postele", R(r"calounene postele")),
    ("toppery-a-chranice-matraci", R(r"topper|chranice matrac")),
    ("satni-systemy", R(r"satni system|satny")),
    ("stojany-na-saty", R(r"ramink|stojany na saty")),
    ("nastenky-a-tabule", R(r"nastenky|tabule")),
    ("trezory", R(r"trezor")),
    ("umyvadla", R(r"umyvadla|umyvatka")),
    ("vany", R(r"\bvany\b")),
    ("sprchove-kouty", R(r"sprchove kouty|sprchove dvere|sprchove zasteny|walk.?in|vanove zasteny")),
    ("sprchove-vanicky", R(r"sprchove vanicky|vanicky")),
    ("wc-a-bidety", R(r"zachody|wc a bidety|\bbidety|klozety|instalacni systemy|wc sedatka")),
    ("vodovodni-baterie", R(r"vodovodni baterie|baterie umyvadl|baterie sprch|baterie van|koupelnove baterie")),
    ("sprchove-sety", R(r"sprchove (sety|hlavice|sloupy|systemy|panely)|hlavove sprchy")),
    ("topne-zebriky", R(r"topne zebriky|koupelnove radiatory")),
    ("kose-na-pradlo", R(r"kose na pradlo")),
    ("hrnce", R(r"hrnce|nadobi|kastroly")),
    ("panve", R(r"panve|woky")),
    ("pekace-a-formy", R(r"peceni|formy na|pekace")),
    ("kuchynske-noze", R(r"kuchynske noze|noze\b")),
    ("prkenka", R(r"prkenka")),
    ("kuchynske-nacini", R(r"kuchynske naradi|kuchynske nacini|kuchynske pomucky|prislusenstvi do kuchyne")),
    ("talire", R(r"talire|jidelni servisy")),
    ("hrnky-a-salky", R(r"hrnky|salky|kava a caj|cajove")),
    ("sklenice", R(r"sklenice|karafy|dzbany|barove sklo")),
    ("pribory", R(r"pribory")),
    ("tacy-a-podnosy", R(r"tacy|podnosy|etazer")),
    ("skladovani-potravin", R(r"skladovani potravin|\bdozy|\bdozick|uskladneni potravin|vakuove skladovani")),
    ("termosky-a-lahve", R(r"termosky|lahve")),
    ("kuchynsky-textil", R(r"kuchynsky textil")),
    ("drezy", R(r"drezy|granitove sety|akcni sety")),
    ("kuchynske-baterie", R(r"kuchynske baterie|drezove baterie|baterie drez")),
    ("odpadkove-kose", R(r"odpadkove kose|trideni odpadu")),
    ("kuchynske-doplnky", R(r"kuchynske doplnky|organizace v kuchyni")),
    ("kavovary", R(r"kavovary|priprava kavy")),
    ("rychlovarne-konvice", R(r"rychlovarne konvice|varne konvice")),
    ("mixery-a-roboty", R(r"mixery|kuchynske roboty|slehace|priprava jidla")),
    ("odstavnovace", R(r"odstavnovace|priprava napoju")),
    ("toustovace-a-grily", R(r"topinkovace|kontaktni grily|sendvicovace")),
    ("fritezy", R(r"fritezy")),
    ("drobne-kuchynske-spotrebice", R(r"kuchynske spotrebice|male spotrebice")),
    ("digestore", R(r"digestore")),
    ("vysavace", R(r"vysavace|parni cistice|domov a uklid")),
    ("uprava-vzduchu", R(r"uprava vzduchu|ventilatory|topeni a chlazeni|chlazeni a topeni")),
    ("bodova-svitidla", R(r"bodova|vestavna|podhledova")),
    ("led-pasky", R(r"led pasky|led profily")),
    ("led-panely", R(r"led panely")),
    ("zarovky", R(r"zarovky|svetelne zdroje")),
    ("koupelnova-svitidla", R(r"koupelnova svitidla|koupelnove osvetleni")),
    ("stinidla", R(r"stinidla")),
    ("prosteradla", R(r"prosteradla")),
    ("rolety-a-zaluzie", R(r"rolety|zaluzie|plise")),
    ("garnyze", R(r"garnyze|kolejnice")),
    ("detsky-textil", R(r"detsky textil|detske povleceni")),
    ("tapety", R(r"tapety|fototapety")),
    ("samolepky-na-zed", R(r"samolepky")),
    ("pokojove-rostliny", R(r"pokojove rostliny|zive rostliny")),
    ("difuzery-a-vune", R(r"vune do bytu|difuzery|aromaterapie")),
    ("lucerny", R(r"lucerny")),
    ("vanocni-ozdoby", R(r"vanocni ozdoby|ozdoby na stromek")),
    ("umele-stromky", R(r"vanocni stromky|umele stromky")),
    ("vanocni-osvetleni", R(r"vanocni osvetleni|svetelne retezy")),
    ("adventni-dekorace", R(r"advent")),
    ("betlemy", R(r"betlem")),
    ("velikonocni-dekorace", R(r"velikonoc")),
    ("grily", R(r"grily|grilovani|udirny")),
    ("ohniste-a-ohrivace", R(r"ohniste|terasove ohrivace|zahradni krby")),
    ("bazeny-a-virivky", R(r"bazeny|virivky|zahradni sprchy")),
    ("sauny", R(r"sauny")),
    ("trampoliny", R(r"trampoliny")),
    ("zahradni-domky", R(r"zahradni domky|altany|pergoly|pristresky|party stany")),
    ("zahradni-boxy", R(r"zahradni boxy|ulozne boxy na zahradu")),
    ("skleniky-a-pestovani", R(r"skleniky|pestovani|vyvysene zahony|kompostery")),
    ("substraty-a-hnojiva", R(r"substraty|hnojiva|vyziva rostlin|substraty a mulcovani")),
    ("zavlazovani", R(r"zavlazovani|zahradni hadice|konve")),
    ("zahradni-dekorace", R(r"zahradni dekorace")),
    ("vinylove-podlahy", R(r"vinylove podlahy|vinyl")),
    ("laminatove-podlahy", R(r"laminatove podlahy|laminat")),
    ("drevene-podlahy", R(r"drevene podlahy|parkety|korkove podlahy")),
    ("pvc-a-linoleum", R(r"\bpvc\b|linoleum|lina")),
    ("koberce-metraz", R(r"metraz|zatezove koberce|kobercove ctverce|umele travy")),
    ("podlahove-listy", R(r"podlahove listy|soklove listy|prechodove listy|podlozky pod")),
    ("kliky-a-kovani", R(r"kliky|kovani|rozety")),
    ("nabytkove-uchytky", R(r"uchytky|nabytkove kovani|knopky")),
    ("zasuvky-a-vypinace", R(r"zasuvky|vypinace|elektroinstalace")),
    ("skladove-regaly", R(r"skladove regaly|kovove regaly|regaly do garaze")),
    ("susaky-na-pradlo", R(r"susaky|suseni pradla")),
    ("zehlici-prkna", R(r"zehlici prkna")),
    ("uklidove-pomucky", R(r"uklidove pomucky|uklid|uklidove")),
    ("pro-miminka", R(r"pro miminka|prebalovaci|ohradky|zabrany")),
    ("detska-svitidla", R(r"detska svitidla|detske osvetleni")),
    ("detske-koberce", R(r"detske koberce")),
    ("domecky-a-teepee", R(r"detske domecky|teepee|piskoviste")),
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
    ("dekorativni-polstare", R(r"dekoracni povlaky|povlaky na polstar")),
    ("povleceni", R(r"povleceni|povlak\w* na matrac|potah\w* (na )?matrac")), ("prikryvky-a-polstare", R(r"prikryvky|prikryvek|polstare a prikryvky|prikryvky a polstare")),
    ("rucniky-a-osusky", R(r"rucnik|koupelnovy textil")), ("deky-a-prehozy", R(r"deky|prehoz")), ("potahy-na-nabytek", R(r"potahy")),
    ("vanocni-dekorace", R(r"vanoc")), ("zrcadla", R(r"zrcadla")), ("obrazy", R(r"obrazy")), ("nastenne-dekorace", R(r"dekorace na zed|samolepky na zed")),
    ("ramy-na-fotky", R(r"ramy")), ("hodiny", R(r"hodiny")), ("vazy", R(r"vazy")), ("kvetinace", R(r"kvetinac")),
    ("umele-kvetiny", R(r"kvetiny")), ("svicky-a-svicny", R(r"svicky|svicny|vune do bytu")), ("ulozne-boxy-a-kose", R(r"ulozne|kosik|ukladani")),
    ("sosky-a-doplnky", R(r"figurky|sosky")),
    ("komody", R(r"skrine a skrinky|\bskrinky\b")),
]


def veto(title_f, path_f):
    return bool(VETO_TITLE.search(title_f)) or bool(VETO_PATH.search(path_f))


# Weak rules: generic words that only decide when nothing more concrete is in the title ("Vánoční polštář" = a cushion).
WEAK = {"vanocni-dekorace", "sosky-a-doplnky", "ulozne-boxy-a-kose", "detske-dekorace"}
RULE_ORDER = {i: i for i in range(len(TITLE_RULES))}


KIDS_MAP = {"koberce": "detske-koberce", "stolni-lampy": "detska-svitidla", "lustry": "detska-svitidla", "stropni-svitidla": "detska-svitidla",
            "povleceni": "detsky-textil", "deky-a-prehozy": "detsky-textil", "postele": "detske-postele", "satni-skrine": "detske-skrine-a-ulozne-boxy", "komody": "detske-skrine-a-ulozne-boxy",
            "knihovny-a-regaly": "detske-skrine-a-ulozne-boxy", "jidelni-zidle": "detske-stolky-a-zidle",
            "jidelni-stoly": "detske-stolky-a-zidle", "psaci-stoly": "detske-stolky-a-zidle"}


# nouns that name one category on their own, whatever words surround them: a single-word match of these is as good as a phrase
UNAMBIGUOUS = {"umyvadla", "vany", "drezy", "panve", "hrnce", "kavovary", "vysavace", "trampoliny", "sauny", "grily", "tapety",
               "zarovky", "garnyze", "prosteradla", "trezory", "lenosky", "biokrby", "paravany", "stinidla", "betlemy", "sklenice",
               "pribory", "talire", "fritezy", "digestore", "lucerny", "priborniky", "rolety-a-zaluzie", "boxspringy",
               "toppery-a-chranice-matraci", "wc-a-bidety", "skleniky-a-pestovani", "substraty-a-hnojiva", "vinylove-podlahy",
               "kliky-a-kovani", "nabytkove-uchytky", "vanocni-ozdoby", "adventni-dekorace", "velikonocni-dekorace",
               "pokojove-rostliny", "difuzery-a-vune", "termosky-a-lahve", "uklidove-pomucky", "hrnky-a-salky", "matrace", "botniky", "vitriny", "komody", "taburety-a-sedaci-vaky", "koberce", "zrcadla", "lustry", "vazy", "kvetinace",
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
SIZE_CATS = {"prosteradla", "toppery-a-chranice-matraci", "boxspringy", "calounene-postele", "detske-koberce", "detsky-textil",
             "rolety-a-zaluzie", "koberce-metraz", "postele", "matrace", "rosty", "detske-postele", "povleceni", "koberce", "behouny-a-predlozky", "prikryvky-a-polstare",
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


# ------------------------------------------------------------------ shape and number of seats (listing filters, 12. 11. 2026)
SHAPE_CATS = {"jidelni-stoly", "konferencni-stolky", "odkladaci-stolky", "zahradni-stoly", "barove-stoly", "koberce", "detske-koberce",
              "zrcadla", "sedacky", "rohove-sedacky", "zahradni-sestavy", "dekorativni-polstare", "bazeny-a-virivky"}
SHAPES = [("kulaty", "kulatý", r"\bkulat\w*|\bkruhov\w*|\bkruh\b|\bprumer|ø|⌀"), ("ovalny", "oválný", r"\boval\w*"),
          ("ctvercovy", "čtvercový", r"\bctverc\w*"), ("obdelnikovy", "obdélníkový", r"\bobdelnik\w*"),
          ("tvar-l", "rohový do L", r"\bdo l\b|tvar\w* (pismene )?l\b|\bl sedac|rohov"), ("tvar-u", "do U", r"\bdo u\b|tvar\w* (pismene )?u\b|\bu sedac")]
SHAPES_RX = [(s, l, re.compile(r)) for s, l, r in SHAPES]
SHAPE_NAME = {s: l for s, l, _ in SHAPES}
SEAT_CATS = {"sedacky", "rohove-sedacky", "pohovky", "jidelni-sety", "zahradni-sestavy", "lavice"}
RX_SEATS = re.compile(r"\b(\d{1,2})\s*-?\s*(mistn|mist\b|osob|sed\b|sedad)|\bpro (\d{1,2}) osob|\b(\d)\s*x\s*zidl|\b(\d)\s*zidl")
SEAT_WORDS = [(2, r"\bdvoj(sed|mist)|\bdvoumist|\bdvoused"), (3, r"\btroj(sed|mist)|\btrimist|\btrojka\b"), (4, r"\bctyr(mist|sed)")]


def shapes_of(text, cat):
    """Shapes a product has, from its titles (folded); only in categories where shape is something people choose by."""
    if cat not in SHAPE_CATS:
        return []
    t = fold(text)
    out = [s for s, _, rx in SHAPES_RX if rx.search(t)]
    if cat in ("sedacky", "rohove-sedacky", "zahradni-sestavy"):
        out = [s for s in out if s in ("tvar-l", "tvar-u")]
        if cat == "rohove-sedacky" and not out:
            out = ["tvar-l"]
    else:
        out = [s for s in out if s not in ("tvar-l", "tvar-u")]
    return out[:2]


def seats_of(text, cat):
    """Number of seats (2, 3, 4 = 4 and more) from the title: "3místná", "pro 6 osob", "stůl + 4 židle"."""
    if cat not in SEAT_CATS:
        return 0
    t = fold(text)
    m = RX_SEATS.search(t)
    n = 0
    if m:
        n = int(next(g for g in (m.group(1), m.group(3), m.group(4), m.group(5)) if g))
    else:
        n = next((k for k, rx in SEAT_WORDS if re.search(rx, t)), 0)
    return min(n, 4) if 2 <= n <= 12 else 0
