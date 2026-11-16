"""Third level of the tree: subcategories inside a category (Favi-style depth, content gap round 2, 15. 11. 2026).

A product keeps its category (p["cat"], used by rooms, landings, facets, similar products); a subcategory only refines it
(p["sub"]). The category page lists its own products plus those of its subcategories; a subcategory has its own page and
its own product cap, so big categories (shower enclosures, taps, wardrobes) show more of the feed.

Rules run on the folded product name and only inside the parent category, so a subcategory can never pull a product
out of another category. Within a parent, the FIRST rule that matches wins (put the specific ones first).

A slug equal to an existing phrase landing (content/landings/kw2.json) takes over that URL: the landing is skipped as
"path exists" once the subcategory is public (>= MIN_CAT = 5 products), so an indexed URL keeps working with more products.
Search volume (Marketing Miner, CZ, 15. 11. 2026) is in the comment column; reports/vian/category-gap-2026-11.md has the table."""
import re

from taxonomy import CATS, fold, clean

# slug, menu name, parent category, h1, rule on the folded product name
SUBS = [
    # ------------------------------------------------------------ koupelna
    ("sprchove-dvere", "Sprchové dveře", "sprchove-kouty", "Sprchové dveře", r"sprchov\w* dver|\bdver\w* (do|ke|k) (sprch|nik)|\bdver\w* do niky"),
    ("vanove-zasteny", "Vanové zástěny", "sprchove-kouty", "Vanové zástěny", r"vanov\w* (zasten|stena|stenka)|(zasten|stena|stenka)\w* (na|nad|k|ke) van"),
    ("walk-in-sprchy", "Walk-in sprchové zástěny", "sprchove-kouty", "Walk-in sprchové zástěny", r"walk ?-?in"),
    ("sprchove-zasteny", "Sprchové zástěny", "sprchove-kouty", "Sprchové zástěny", r"sprchov\w* (zasten|stena|stenka|plenta)|\bzasten\w* (do|ke|k) sprch|pevn\w* (sprchov\w* )?(stena|stenka|zasten)"),
    ("sprchove-boxy", "Sprchové boxy", "sprchove-kouty", "Sprchové boxy", r"sprchov\w* box|hydromasazn\w* box|parni box"),
    ("umyvadlove-baterie", "Umyvadlové baterie", "vodovodni-baterie", "Umyvadlové baterie", r"umyvadl\w* (bater|stojank)|bater\w* (na|k|ke|pro) umyvad|stojankov\w* umyvadl"),
    ("vanove-baterie", "Vanové baterie", "vodovodni-baterie", "Vanové baterie", r"vanov\w* bater|bater\w* (na|k|ke|pro) van|bater\w* (na )?okraj vany"),
    ("sprchove-baterie", "Sprchové baterie", "vodovodni-baterie", "Sprchové baterie", r"sprchov\w* bater|bater\w* (do|na|pro|ke|k) sprch"),
    ("bidetove-baterie", "Bidetové baterie", "vodovodni-baterie", "Bidetové baterie", r"bidet"),
    ("podomitkove-baterie", "Podomítkové baterie", "vodovodni-baterie", "Podomítkové baterie", r"podomitk"),
    ("termostaticke-baterie", "Termostatické baterie", "vodovodni-baterie", "Termostatické baterie", r"termostat"),
    ("skrinka-pod-umyvadlo", "Skříňky pod umyvadlo", "koupelnove-skrinky", "Skříňky pod umyvadlo", r"pod ?umyvad|umyvadl\w* (se|s) skrin|skrin\w* s umyvad|umyvadlov\w* skrin"),
    ("galerky", "Galerky", "koupelnove-skrinky", "Galerky a zrcadlové skříňky", r"galerk|zrcadlov\w* skrin|skrin\w* se zrcadl"),
    ("vysoke-koupelnove-skrinky", "Vysoké koupelnové skříňky", "koupelnove-skrinky", "Vysoké koupelnové skříňky", r"vysok\w* (koupelnov\w* )?skrin|\bvysoka\b|\bvysoka skrin"),
    ("skrinky-nad-pracku", "Skříňky nad pračku", "koupelnove-skrinky", "Skříňky nad pračku", r"(nad|pod|na) prack|nad wc"),
    ("umyvadlo-na-desku", "Umyvadla na desku", "umyvadla", "Umyvadla na desku", r"na desk|nastavn\w* umyvad|umyvad\w* nastavn|na skrinku|polozen"),
    ("zapustna-umyvadla", "Zápustná umyvadla", "umyvadla", "Zápustná a vestavná umyvadla", r"zapustn|vestavn|podomyvadl|pod desku|polozapust"),
    ("rohova-umyvadla", "Rohová umyvadla", "umyvadla", "Rohová umyvadla", r"rohov\w* umyvad|umyvad\w* rohov"),
    ("umyvatka", "Umývátka", "umyvadla", "Umývátka", r"umyvatk"),
    ("zavesna-wc", "Závěsná WC", "wc-a-bidety", "Závěsná WC", r"zavesn\w* (wc|zachod|klozet|misa)|(wc|klozet|misa)\w* zavesn"),
    ("kombi-wc", "Kombi WC", "wc-a-bidety", "Kombi WC a stojící záchody", r"kombi|stojic\w* (wc|zachod|klozet)|(wc|klozet) stojic"),
    ("wc-prkenka", "WC prkénka", "wc-a-bidety", "WC prkénka a sedátka", r"prken|sedatk|sedadl"),
    ("splachovaci-tlacitka", "Splachovací tlačítka", "wc-a-bidety", "Splachovací tlačítka", r"tlacit|ovladac\w* (desk|splach)"),
    ("bidety", "Bidety", "wc-a-bidety", "Bidety", r"\bbidet"),
    ("pisoary", "Pisoáry", "wc-a-bidety", "Pisoáry", r"pisoar"),
    ("volne-stojici-vany", "Volně stojící vany", "vany", "Volně stojící vany", r"volne ?stoj|samostatn\w* stoj"),
    ("rohove-vany", "Rohové vany", "vany", "Rohové a asymetrické vany", r"rohov|asymetr"),
    ("hydromasazni-vany", "Hydromasážní vany", "vany", "Hydromasážní a vířivé vany", r"hydromasaz|virivk|virivou|whirlpool"),
    ("sprchove-zlaby", "Sprchové žlaby", "sprchove-vanicky", "Sprchové a odtokové žlaby", r"zlab|liniov\w* (odtok|vpust)|podlahov\w* vpust"),
    ("sprchove-sloupy", "Sprchové sloupy", "sprchove-sety", "Sprchové sloupy a systémy", r"sprchov\w* (sloup|system|souprav)|sloup|sprchov\w* set s|s termostat"),
    ("sprchove-panely", "Sprchové panely", "sprchove-sety", "Sprchové panely", r"sprchov\w* panel|panel\w* sprch|masazn\w* panel"),
    ("hlavove-sprchy", "Hlavové sprchy", "sprchove-sety", "Hlavové sprchy", r"hlavov\w* sprch|sprchov\w* hlavic|\bhlavic|dest\w* sprch|rain"),
    ("rucni-sprchy", "Ruční sprchy", "sprchove-sety", "Ruční sprchy", r"rucn\w* sprch|sprchov\w* (ruc|rukojet)"),
    ("sprchove-hadice", "Sprchové hadice", "sprchove-sety", "Sprchové hadice", r"hadic"),
    ("madla-do-koupelny", "Madla do koupelny", "koupelnove-doplnky", "Madla do koupelny", r"madl|bezpecnost\w* drzad|oporn"),
    ("drzaky-na-toaletni-papir", "Držáky na toaletní papír", "koupelnove-doplnky", "Držáky na toaletní papír", r"toaletn\w* papir|wc papir|zasobnik\w* na (toaletn|papir)"),
    ("davkovace-mydla", "Dávkovače mýdla", "koupelnove-doplnky", "Dávkovače mýdla", r"davkovac|zasobnik\w* (na |tekut\w* )?mydl"),
    ("wc-stetky", "WC štětky", "koupelnove-doplnky", "WC štětky", r"stetk|\bwc kartac|kartac\w* (na|do) wc"),
    ("mydlenky", "Mýdlenky", "koupelnove-doplnky", "Mýdlenky", r"mydlenk|misk\w* na mydl"),
    ("drzaky-na-kartacky", "Držáky na zubní kartáčky", "koupelnove-doplnky", "Držáky na zubní kartáčky a kelímky", r"kartack|kelimek|kelimk|\bpohar\w* (na|do) koupel"),
    ("elektricke-topne-zebriky", "Elektrické topné žebříky", "topne-zebriky", "Elektrické topné žebříky", r"elektr|topn\w* tyc|s topnou"),
    # ------------------------------------------------------------ kuchyně a spotřebiče
    ("kuchynske-skrinky", "Kuchyňské skříňky", "kuchynske-linky", "Kuchyňské skříňky", r"(horn|doln|zavesn|spodn|vysok|rohov|potravinov)\w* (kuchyn\w* )?skrin|kuchyn\w* (horn\w* |doln\w* |zavesn\w* |spodn\w* |vysok\w* )?skrin|skrin\w* (pod drez|na vestav|na troub|pro vestav|pod varnou)"),
    ("rohove-kuchyne", "Rohové kuchyně", "kuchynske-linky", "Rohové kuchyňské linky", r"rohov\w* (kuchyn|linka|linky)|kuchyn\w* (linka )?rohov|\bl kuchyn|ve tvaru l"),
    ("kuchynske-pracovni-desky", "Pracovní desky", "kuchynske-linky", "Kuchyňské pracovní desky", r"^(\w+ ){0,2}pracovn\w* desk|kuchyn\w* pracovn\w* desk"),
    ("indukcni-desky", "Indukční desky", "trouby-a-varne-desky", "Indukční varné desky", r"indukc"),
    ("plynove-desky", "Plynové varné desky", "trouby-a-varne-desky", "Plynové varné desky", r"plynov\w* (varn\w* )?desk|desk\w* plyn"),
    ("sklokeramicke-desky", "Sklokeramické desky", "trouby-a-varne-desky", "Sklokeramické varné desky", r"sklokeram|keramick\w* (varn\w* )?desk"),
    ("sporaky", "Sporáky", "trouby-a-varne-desky", "Sporáky", r"sporak"),
    ("vestavne-trouby", "Vestavné trouby", "trouby-a-varne-desky", "Vestavné trouby", r"\btroub|parn\w* troub|horkovzdusn\w* troub"),
    ("mrazaky", "Mrazáky", "lednice", "Mrazáky a mrazničky", r"mrazak|mraznick|mrazic\w* box|truhlic"),
    ("americke-lednice", "Americké lednice", "lednice", "Americké lednice", r"americk|side ?by ?side|vicedver|multidoor|french door"),
    ("vestavne-lednice", "Vestavné lednice", "lednice", "Vestavné lednice", r"vestav"),
    ("minibary", "Minibary a malé lednice", "lednice", "Minibary a malé lednice", r"minibar|mini lednic|autochlad|\bmal\w* lednic|podpultov"),
    ("kombinovane-lednice", "Kombinované lednice", "lednice", "Kombinované lednice s mrazákem", r"kombinovan|s mrazak|s mrazicim|mraznic\w* dole|dvoudver"),
    ("pracky-se-susickou", "Pračky se sušičkou", "pracky-a-susicky", "Pračky se sušičkou", r"pracka se susick|prack\w* se susic|s susen"),
    ("susicky", "Sušičky prádla", "pracky-a-susicky", "Sušičky prádla", r"susick|kondenzacn|tepeln\w* cerpad"),
    ("pracky", "Pračky", "pracky-a-susicky", "Pračky", r"prack"),
    ("vestavne-mycky", "Vestavné myčky", "mycky", "Vestavné myčky nádobí", r"vestav|integrov"),
    ("automaticke-kavovary", "Automatické kávovary", "kavovary", "Automatické kávovary", r"automat|plnoautomat"),
    ("pakove-kavovary", "Pákové kávovary", "kavovary", "Pákové kávovary", r"pakov|espresso kavovar|kavovar\w* espresso|espresovac"),
    ("kapslove-kavovary", "Kapslové kávovary", "kavovary", "Kapslové kávovary", r"kapsl|nespresso|dolce gusto|tassimo"),
    ("prekapavace", "Překapávače", "kavovary", "Překapávače kávy", r"prekapav|filtr\w* (kav|kavovar)|french press|moka|dzezv|dripper"),
    ("klimatizace", "Klimatizace", "uprava-vzduchu", "Klimatizace", r"klimatiz|split"),
    ("cisticky-vzduchu", "Čističky vzduchu", "uprava-vzduchu", "Čističky vzduchu", r"cistick|cistic\w* vzduch"),
    ("odvlhcovace", "Odvlhčovače", "uprava-vzduchu", "Odvlhčovače vzduchu", r"odvlhc"),
    ("zvlhcovace", "Zvlhčovače", "uprava-vzduchu", "Zvlhčovače vzduchu", r"zvlhc|difuz"),
    ("ventilatory", "Ventilátory", "uprava-vzduchu", "Ventilátory", r"ventilator"),
    ("roboticke-vysavace", "Robotické vysavače", "vysavace", "Robotické vysavače", r"robot"),
    ("tycove-vysavace", "Tyčové vysavače", "vysavace", "Tyčové a bezdrátové vysavače", r"tycov|bezdrat|aku\b|akumulator|bezsnur"),
    ("rucni-vysavace", "Ruční vysavače", "vysavace", "Ruční vysavače a autovysavače", r"rucn|autovysav|do auta"),
    ("tlakove-hrnce", "Tlakové hrnce", "hrnce", "Tlakové hrnce", r"tlakov"),
    ("sady-hrncu", "Sady nádobí", "hrnce", "Sady hrnců a nádobí", r"\bsad[ay]\b|\bset\b|souprav"),
    ("granitove-drezy", "Granitové dřezy", "drezy", "Granitové dřezy", r"granit|silgranit|kompozit|fragranit|tectonite"),
    ("nerezove-drezy", "Nerezové dřezy", "drezy", "Nerezové dřezy", r"nerez"),
    # ------------------------------------------------------------ obývák, ložnice, předsíň, pracovna
    ("kreslo-usak", "Křesla ušák", "kresla", "Křesla ušák", r"\busak|usakov"),
    ("masazni-kreslo", "Masážní křesla", "kresla", "Masážní křesla", r"masazn|masaz"),
    ("relaxacni-kreslo", "Relaxační křesla", "kresla", "Relaxační a polohovací křesla", r"relax|polohov|elektricky polohov|\btv kresl|s podnozk"),
    ("rozkladaci-kreslo-na-spani", "Rozkládací křesla", "kresla", "Rozkládací křesla na spaní", r"rozklad|na spani|s funkci spani|kreslo ?postel"),
    ("otocna-kresla", "Otočná křesla", "kresla", "Otočná křesla", r"otocn"),
    ("rozkladaci-pohovky", "Rozkládací pohovky", "pohovky", "Rozkládací pohovky na spaní", r"rozklad|na spani|s funkci spani|s uloz|pohovk\w* postel|gauc\w* postel"),
    ("rozkladaci-rohove-sedacky", "Rozkládací rohové sedačky", "rohove-sedacky", "Rozkládací rohové sedačky", r"rozklad|na spani|s funkci spani|s uloz"),
    ("sedacky-ve-tvaru-u", "Sedačky ve tvaru U", "rohove-sedacky", "Rohové sedačky ve tvaru U", r"tvar\w* u\b|\bu sedac|\bu-sedac|\bpanorama|\bdo u\b"),
    ("satni-skrine-s-posuvnymi-dvermi", "Skříně s posuvnými dveřmi", "satni-skrine", "Šatní skříně s posuvnými dveřmi", r"posuvn|kuprov|s posuv"),
    ("rohove-satni-skrine", "Rohové šatní skříně", "satni-skrine", "Rohové šatní skříně", r"rohov"),
    ("satni-skrine-se-zrcadlem", "Skříně se zrcadlem", "satni-skrine", "Šatní skříně se zrcadlem", r"zrcadl"),
    ("polohovaci-postele", "Polohovací postele", "postele", "Polohovací postele", r"polohov|elektricky nastav|motorov"),
    ("postele-s-uloznym-prostorem", "Postele s úložným prostorem", "postele", "Postele s úložným prostorem", r"uloz|s uloz|uloznym|s uloznym|vyklopn\w* rost|zvedac\w* rost|se supliky|se zasuvk|s zasuvk"),
    ("jednoluzkove-postele", "Jednolůžkové postele", "postele", "Jednolůžkové postele", r"jednoluz|jednoloz|\b(80|90|100) ?x ?(190|200)\b"),
    ("manzelske-postele", "Manželské postele", "postele", "Manželské a dvoulůžkové postele", r"manzelsk|dvouluz|dvouloz|\b(140|160|180|200) ?x ?200\b"),
    ("domeckove-postele", "Domečkové postele", "detske-postele", "Domečkové a Montessori postele", r"domeck|tvar\w* domu|montessori|\bdomek"),
    ("kolebky", "Kolébky", "detske-postylky", "Kolébky a košíky pro miminka", r"kolebk|kolisk|kosik|proutn"),
    ("cestovni-postylky", "Cestovní postýlky", "detske-postylky", "Cestovní postýlky", r"cestovn|skladac|ohradk"),
    ("postylka-k-posteli", "Postýlky k posteli", "detske-postylky", "Přistýlky a postýlky k posteli", r"k posteli|pristylk|co ?sleep|side ?bed|bedside"),
    ("polohovaci-rosty", "Polohovací rošty", "rosty", "Polohovací rošty", r"polohov|elektr|motor"),
    ("detske-matrace", "Dětské matrace", "matrace", "Dětské matrace", r"detsk|do postyl|pro deti|\b(60|70) ?x ?(120|140|160)\b"),
    ("pradelniky", "Prádelníky", "komody", "Prádelníky", r"pradelnik|chiffon|sifonier|vysok\w* komod"),
    ("komoda-se-supliky", "Komody se šuplíky", "komody", "Komody se šuplíky", r"suplik|zasuvk"),
    ("knihovny", "Knihovny", "knihovny-a-regaly", "Knihovny", r"knihovn"),
    ("regaly", "Regály", "knihovny-a-regaly", "Regály", r"\bregal"),
    ("nastenne-police", "Nástěnné police", "police", "Nástěnné police a poličky", r"nastenn|na zed|zavesn|plovouc"),
    ("rohove-police", "Rohové police", "police", "Rohové police", r"rohov"),
    ("botnik-s-lavici", "Botníky se sedákem", "botniky", "Botníky se sedákem a lavicí", r"lavic|sedak|sedadl|sedac|s polstrem"),
    ("uzke-botniky", "Úzké botníky", "botniky", "Úzké botníky", r"uzk|\bslim\b|vyklopn"),
    ("vesak-na-obleceni", "Stojanové věšáky", "vesaky", "Stojanové věšáky na oblečení", r"stojan|stojac|na kolecka|\bvesak\w* (na )?(obleceni|saty|kabat)|garnyz"),
    ("nastenny-vesak", "Nástěnné věšáky", "vesaky", "Nástěnné věšáky", r"nastenn|na zed|vesakov\w* (panel|lista|stena)|na dvere"),
    ("zavesne-tv-stolky", "Závěsné TV stolky", "tv-stolky", "Závěsné TV stolky", r"zavesn|na zed|plovouc"),
    ("rohove-psaci-stoly", "Rohové psací stoly", "psaci-stoly", "Rohové psací stoly", r"rohov|tvaru l\b|\bl stul"),
    ("kancelarske-kreslo", "Kancelářská křesla", "kancelarske-zidle", "Kancelářská a manažerská křesla", r"kresl|manazer|reditel|director|executive|boss"),
    ("ergonomicke-zidle", "Ergonomické židle", "kancelarske-zidle", "Ergonomické a balanční židle", r"ergonom|balanc|klekac|sedlov|aktivn\w* sed|zdravotn"),
    ("jidelni-lavice", "Jídelní lavice", "lavice", "Jídelní a rohové lavice", r"jideln|rohov|kuchyn|lavic\w* (ke|k|do) (stol|kuchyn|jideln)"),
    ("lavice-do-predsine", "Lavice do předsíně", "lavice", "Lavice do předsíně", r"predsin|chodb|s botnik|na boty|s vesak"),
    ("sedaci-vaky", "Sedací vaky", "taburety-a-sedaci-vaky", "Sedací vaky a pytle", r"sedac\w* (vak|pytel|pytl)|beanbag|sakko|\bvak\b"),
    ("puffy", "Pufy a podnožky", "taburety-a-sedaci-vaky", "Pufy a podnožky", r"\bpuf|podnoz|otoman"),
    ("toaletni-stolky-se-zrcadlem", "Toaletní stolky se zrcadlem", "toaletni-stolky", "Toaletní stolky se zrcadlem", r"zrcad|s led|s osvetl"),
    ("rozkladaci-jidelni-stoly", "Rozkládací jídelní stoly", "jidelni-stoly", "Rozkládací jídelní stoly", r"rozklad|roztah|prodlouz|vysuv"),
    ("kulate-jidelni-stoly", "Kulaté jídelní stoly", "jidelni-stoly", "Kulaté a oválné jídelní stoly", r"kulat|ovaln|\bround\b"),
    # ------------------------------------------------------------ osvětlení
    ("zavesna-svitidla", "Závěsná svítidla", "lustry", "Závěsná svítidla", r"zavesn|zavesov|pendant"),
    ("kristalove-lustry", "Křišťálové lustry", "lustry", "Křišťálové lustry", r"kristal|crystal|sklenen\w* oves|ovesk"),
    ("stropni-ventilatory", "Stropní ventilátory", "stropni-svitidla", "Stropní ventilátory se světlem", r"ventilator"),
    ("stmivatelna-svitidla", "Stmívatelná svítidla", "stropni-svitidla", "Stmívatelná stropní svítidla s ovladačem", r"stmiv|dalkov\w* ovlad|s ovladac|ovladacem|smart|wifi|wi-fi|chytr"),
    ("lampicky-na-psaci-stul", "Lampy na psací stůl", "stolni-lampy", "Lampy na psací stůl", r"psac|kancelar|pracovn|architekt|studij|s klipem|na stul s"),
    ("lampicka-k-posteli", "Noční lampičky", "stolni-lampy", "Noční lampičky k posteli", r"nocn|k posteli|lozni|ke posteli"),
    ("obloukove-lampy", "Obloukové lampy", "stojaci-lampy", "Obloukové stojací lampy", r"oblouk"),
    ("solarni-svitidla", "Solární svítidla", "venkovni-svitidla", "Solární svítidla", r"solar"),
    ("svitidla-s-cidlem", "Svítidla s čidlem", "venkovni-svitidla", "Venkovní svítidla s pohybovým čidlem", r"cidl|senzor|pohyb"),
    # ------------------------------------------------------------ bytový textil a dekorace
    ("obrazy-na-platne", "Obrazy na plátně", "obrazy", "Obrazy na plátně", r"platn|canvas"),
    ("vicedilne-obrazy", "Vícedílné obrazy", "obrazy", "Vícedílné obrazy", r"vicediln|dvoudiln|trojdiln|ctyrdiln|petidiln|\b[2-9] ?-?dil"),
    ("plakaty", "Plakáty", "obrazy", "Plakáty", r"plakat|poster"),
    ("fototapety", "Fototapety", "tapety", "Fototapety", r"fototapet|foto tapet|obrazov\w* tapet"),
    ("vliesove-tapety", "Vliesové tapety", "tapety", "Vliesové tapety", r"vlies|flis"),
    ("stojaci-zrcadlo", "Stojací zrcadla", "zrcadla", "Stojací zrcadla", r"stojac|stoj\w* zrcad|na stojan|psych|\bdo podlah"),
    ("kulata-zrcadla", "Kulatá zrcadla", "zrcadla", "Kulatá a oválná zrcadla", r"kulat|ovaln|kruh"),
    ("kusove-koberce", "Kusové koberce", "koberce", "Kusové koberce", r"kusov"),
    ("venkovni-koberce", "Venkovní koberce", "koberce", "Venkovní koberce", r"venkovn|na terasu|na balkon|outdoor"),
    ("kulate-koberce", "Kulaté koberce", "koberce", "Kulaté koberce", r"kulat|kruh"),
    ("zaclony", "Záclony", "zaclony-a-zavesy", "Záclony", r"zaclon"),
    ("zatemnovaci-zavesy", "Zatemňovací závěsy", "zaclony-a-zavesy", "Zatemňovací závěsy", r"zatemn|blackout|dim ?out"),
    ("zavesy", "Závěsy", "zaclony-a-zavesy", "Závěsy", r"\bzaves(y|u)?\b|\bzavesov"),
    ("rolety-den-noc", "Rolety den a noc", "rolety-a-zaluzie", "Rolety den a noc", r"den ?(a|/|-)? ?noc"),
    ("zaluzie", "Žaluzie", "rolety-a-zaluzie", "Žaluzie", r"zaluzi"),
    ("rolety", "Rolety", "rolety-a-zaluzie", "Rolety", r"rolet"),
    ("prehozy-na-postel", "Přehozy na postel", "deky-a-prehozy", "Přehozy na postel", r"prehoz"),
    ("elektricke-deky", "Vyhřívací deky", "deky-a-prehozy", "Elektrické vyhřívací deky", r"elektr|vyhrivac|vyhriv"),
    ("prikryvky", "Přikrývky a peřiny", "prikryvky-a-polstare", "Přikrývky a peřiny", r"prikryvk|perin|duvet"),
    ("polstare-na-spani", "Polštáře na spaní", "prikryvky-a-polstare", "Polštáře na spaní", r"polstar|podhlavnik|polstark"),
    ("osusky", "Osušky", "rucniky-a-osusky", "Osušky", r"^(?!.*drzak).*osusk"),
    ("zupany", "Župany", "rucniky-a-osusky", "Župany", r"zupan"),
    ("vonne-svicky", "Vonné svíčky", "svicky-a-svicny", "Vonné svíčky", r"vonn|aromat|parfem|yankee"),
    ("led-svicky", "LED svíčky", "svicky-a-svicny", "LED svíčky", r"\bled\b|elektr|na baterie"),
    ("svicny", "Svícny", "svicky-a-svicny", "Svícny", r"svicn|svicen|lucern"),
    ("hodiny-na-zed", "Nástěnné hodiny", "hodiny", "Nástěnné hodiny", r"nastenn|na zed|\bzavesn"),
    ("budiky", "Budíky", "hodiny", "Budíky", r"budik|budici"),
    ("kose-na-trideny-odpad", "Koše na tříděný odpad", "odpadkove-kose", "Koše na tříděný odpad", r"trid|recykl|na separ|separac|\b[2-4] ?(komor|nadob|oddil)|vicekomor"),
    ("vestavne-kose", "Vestavné koše", "odpadkove-kose", "Vestavné koše do kuchyně", r"vestav|vysuvn|do skrinky|do linky|pod drez"),
    ("ulozne-boxy-pod-postel", "Úložné boxy pod postel", "ulozne-boxy-a-kose", "Úložné boxy pod postel", r"pod postel"),
    ("vakuove-pytle", "Vakuové pytle", "ulozne-boxy-a-kose", "Vakuové pytle na oblečení", r"vakuov"),
    ("svetelne-retezy", "Světelné řetězy", "vanocni-osvetleni", "Vánoční světelné řetězy", r"retez|girland|\bled svetl|svetel\w* (had|kabel)"),
    ("svetelne-zavesy", "Světelné závěsy", "vanocni-osvetleni", "Světelné závěsy a krápníky", r"zaves|krapnik|zaclon|rampouch|\bdest\b|vodopad"),
    ("vanocni-koule", "Vánoční koule", "vanocni-ozdoby", "Vánoční koule a baňky", r"koul|bank|\bban[ky]"),
    ("spice-na-stromek", "Špice na stromek", "vanocni-ozdoby", "Špice na vánoční stromek", r"spic"),
    ("samozavlazovaci-kvetinace", "Samozavlažovací květináče", "kvetinace", "Samozavlažovací květináče", r"samozavlaz|lechuza"),
    ("zavesne-kvetinace", "Závěsné květináče", "kvetinace", "Závěsné květináče", r"zavesn|na zabradl|na zed"),
    ("truhliky", "Truhlíky", "kvetinace", "Truhlíky na balkon", r"truhlik"),
    # ------------------------------------------------------------ zahrada
    ("udirny", "Udírny", "grily", "Udírny", r"udirn|udic|smoker"),
    ("plynove-grily", "Plynové grily", "grily", "Plynové grily", r"plynov|na plyn|\bplyn\b"),
    ("elektricke-grily", "Elektrické grily", "grily", "Elektrické grily", r"elektr"),
    ("grily-na-uhli", "Grily na dřevěné uhlí", "grily", "Grily na dřevěné uhlí", r"gril\w* (na )?(drev\w* )?uhl|kotlov\w* gril|gril\w* kotlov|kulov\w* gril|gril\w* na drev"),
    ("keramicke-grily", "Keramické grily", "grily", "Keramické grily kamado", r"kamado|keramick|big green egg"),
    ("zahradni-sedaci-soupravy", "Zahradní sedací soupravy", "zahradni-sestavy", "Zahradní sedací a lounge soupravy", r"sedac\w* (soupr|sestav)|lounge|rohov|ratanov\w* sedac"),
    ("balkonove-sety", "Balkonové sety", "zahradni-sestavy", "Balkonové sety", r"balkon|bistro|\b2 ?\+ ?1\b|pro dva|pro 2"),
    ("zahradni-kresla", "Zahradní křesla", "zahradni-zidle", "Zahradní křesla", r"kresl"),
    ("skladaci-zahradni-zidle", "Skládací zahradní židle", "zahradni-zidle", "Skládací zahradní židle", r"skladac|kempink|campingov|rezisersk"),
    ("lehatko-na-zahradu", "Zahradní lehátka", "lehatka", "Zahradní lehátka", r"zahradn|na zahrad|polohovac|ratanov|lehatk\w* s kolecky|sezlong|na terasu"),
    ("plazove-lehatko", "Plážová lehátka", "lehatka", "Plážová a skládací lehátka", r"plazov|skladac|k bazenu|plaz"),
    ("zahradni-houpacky", "Zahradní houpačky", "houpacky-a-site", "Zahradní houpačky", r"houpack|houpaci lavic"),
    ("houpaci-site", "Houpací sítě", "houpacky-a-site", "Houpací sítě", r"\bsit"),
    ("stojany-na-slunecniky", "Stojany na slunečníky", "slunecniky-a-zasteny", "Stojany a podstavce na slunečníky", r"stojan|podstav|zatez|drzak"),
    ("balkonove-zasteny", "Balkonové zástěny", "slunecniky-a-zasteny", "Balkonové zástěny a stínění", r"zasten|zastin|stinic|plachta|rakos|bambus"),
    ("slunecniky", "Slunečníky", "slunecniky-a-zasteny", "Slunečníky", r"slunecnik"),
    ("virivky", "Vířivky", "bazeny-a-virivky", "Vířivky", r"virivk|\bspa\b|jacuzz|hot ?tub"),
    ("nadzemni-bazeny", "Bazény", "bazeny-a-virivky", "Nadzemní bazény", r"bazen"),
    ("zahradni-sprchy", "Zahradní sprchy", "bazeny-a-virivky", "Zahradní a solární sprchy", r"sprch"),
    ("pristresky", "Přístřešky", "zahradni-domky", "Přístřešky na auto a popelnice", r"pristres|carport|na popelnic|na auto"),
    ("pareniste", "Pařeniště", "skleniky-a-pestovani", "Pařeniště a fóliovníky", r"parenist|foliovnik|tunel"),
    ("kompostery", "Kompostéry", "skleniky-a-pestovani", "Kompostéry", r"kompost"),
    ("vyvysene-zahony", "Vyvýšené záhony", "skleniky-a-pestovani", "Vyvýšené záhony", r"vyvysen\w* zahon|zahon"),
    ("plynove-ohrivace", "Terasové ohřívače", "ohniste-a-ohrivace", "Terasové ohřívače a zářiče", r"ohrivac|zaric|infra|heater"),
    ("ohniste", "Ohniště", "ohniste-a-ohrivace", "Zahradní ohniště", r"ohnist|kos\w* na ohen|fire ?pit|na ohen"),
    ("zahradni-hadice", "Zahradní hadice", "zavlazovani", "Zahradní hadice", r"hadic"),
    ("zavlazovaci-system", "Zavlažovací systémy", "zavlazovani", "Zavlažovací systémy a postřikovače", r"postrikov|\bzavlazovac|kapkov|rozstrikov"),
    # ------------------------------------------------------------ content gap round 3 (16. 11. 2026, MM search volume in the comment)
    ("adventni-kalendare", "Adventní kalendáře", "adventni-dekorace", "Adventní kalendáře", r"adventn\w* kalendar|kalendar\w* advent"),   # 34 000
    ("termohrnky", "Termohrnky", "termosky-a-lahve", "Termohrnky a cestovní hrnky", r"termohrn|termo hrn|cestovn\w* hrn|hrnek do auta|termo kelim"),   # 11 000
    ("termosky", "Termosky", "termosky-a-lahve", "Termosky", r"termosk|termolahev|termo lahev|jidelni termos|\btermos\b"),   # 6 600
    ("lahve-na-piti", "Láhve na pití", "termosky-a-lahve", "Láhve na pití", r"lahev|lahve|lahv|bidon"),
    ("mlynky-na-kavu", "Mlýnky na kávu", "kavovary", "Mlýnky na kávu", r"mlyn\w*"),   # 8 200
    ("vyrobniky-ledu", "Výrobníky ledu", "drobne-kuchynske-spotrebice", "Výrobníky ledu", r"vyrobnik\w* ledu|ledovac|ice maker"),   # 8 000
    ("zmrzlinovace", "Zmrzlinovače", "drobne-kuchynske-spotrebice", "Zmrzlinovače", r"zmrzlinovac|vyrobnik\w* zmrzlin"),   # 5 700
    ("vyrobniky-sody", "Výrobníky sody", "drobne-kuchynske-spotrebice", "Výrobníky sody", r"vyrobnik\w* sody|sodastream|sifon\w* na sodu"),
    ("vaflovace", "Vaflovače", "toustovace-a-grily", "Vaflovače", r"vaflov|na vafle"),   # 4 800
    ("sendvicovace", "Sendvičovače", "toustovace-a-grily", "Sendvičovače", r"sendvic"),
    ("mlynky-na-maso", "Mlýnky na maso", "mixery-a-roboty", "Mlýnky na maso", r"mlyn\w* na maso|masomlyn"),   # 4 700
    ("pece-na-pizzu", "Pece na pizzu", "grily", "Pece na pizzu", r"pec\w* na pizz|pizza ?pec|pizz\w* (pec|kamen)|kamen\w* na pizz"),   # 4 200
    ("sklenice-na-vino", "Sklenice na víno", "sklenice", "Sklenice na víno", r"na vin|vinov\w* sklen|sklenic\w* na (cerven|bil)|\bnapa\b|bordeaux|burgund"),   # 4 400
    ("karafy", "Karafy", "sklenice", "Karafy a dekantéry", r"karaf|dekant"),   # 1 400
    ("sklenice-na-pivo", "Sklenice na pivo", "sklenice", "Sklenice a půllitry na pivo", r"na pivo|pivn\w* sklen|\bkrigl|pullitr|tupl"),
    ("sklenice-na-whisky", "Sklenice na whisky", "sklenice", "Sklenice na whisky a destiláty", r"whisk|na rum|na lihovin|panak|stamprl|na destilat"),
    ("stojany-na-kvetiny", "Stojany na květiny", "kvetinace", "Stojany na květiny", r"stojan|etazer|na nozk\w* kvetin|podstav"),   # 7 200
    ("sudy-na-destovou-vodu", "Sudy na dešťovou vodu", "zavlazovani", "Sudy a nádrže na dešťovou vodu", r"\bsud\b|\bsudy\b|nadrz|destov\w* vod"),   # 3 800
    ("chlebniky", "Chlebníky", "skladovani-potravin", "Chlebníky", r"chlebnik|box\w* na (chleb|pecivo)"),   # 3 500
    ("svacinove-boxy", "Svačinové boxy", "skladovani-potravin", "Svačinové boxy a obědáře", r"svacin|obedar|lunch ?box|bento|jidlonos"),   # 2 600
    ("kuchynske-vahy", "Kuchyňské váhy", "kuchynske-nacini", "Kuchyňské váhy", r"\bvah[ay]\b|\bvaha|odmerk\w* digit"),   # 3 500
    ("lisy-na-cesnek", "Lisy na česnek", "kuchynske-nacini", "Lisy na česnek", r"lis\w* na cesnek|cesnekov"),   # 2 100
    ("vyvrtky", "Vývrtky", "kuchynske-nacini", "Vývrtky a otvíráky na víno", r"vyvrtk|otvirak\w* (na )?vin"),
    ("kolotoce-nad-postylku", "Kolotoče nad postýlku", "detske-postylky", "Kolotoče nad postýlku", r"kolotoc|\bmobil\w* nad|nad postyl"),   # 3 400
    ("krmitka-pro-ptaky", "Krmítka a budky pro ptáky", "zahradni-dekorace", "Krmítka a budky pro ptáky", r"krmitk|budk\w* (pro|na) ptak|ptac\w* budk|pitk\w* pro ptak|hmyz\w* hotel"),   # 3 200
    ("ohradky-pro-deti", "Ohrádky a zábrany", "pro-miminka", "Dětské ohrádky a zábrany", r"ohradk|zabran"),   # 2 100
    ("plastove-boxy", "Plastové boxy", "ulozne-boxy-a-kose", "Plastové úložné boxy", r"plastov\w* (box|krabic|bedn|ulozn|kontejner)|box\w* plastov|\bpp box"),   # 2 200
    ("sperkovnice", "Šperkovnice", "ulozne-boxy-a-kose", "Šperkovnice a stojany na šperky", r"sperk"),   # 5 700 + 560
    ("kosmeticke-zrcadlo", "Kosmetická zrcátka", "zrcadla", "Kosmetická zrcátka", r"kosmetick|zrcatk|make ?up|zvetsovac|lic\w* zrcad"),   # 2 400 + 1 600
    ("lekarnicky", "Lékárničky", "koupelnove-skrinky", "Lékárničky", r"lekarnic"),   # 1 400
    ("vylevky", "Výlevky", "umyvadla", "Výlevky", r"vylevk"),   # 980
    ("podtacky", "Podtácky", "ubrusy-a-prostirani", "Podtácky", r"podtack|podlozk\w* pod (sklenic|hrnk|napoj)"),   # 850
    ("svetelne-girlandy", "Světelné girlandy", "dekoracni-osvetleni", "Světelné girlandy a řetězy", r"girland|retez|svetel\w* (had|kabel)|\bled svetyl"),   # 4 100
    ("rozkladaci-postele", "Rozkládací postele", "postele", "Rozkládací a skládací postele", r"rozklad|skladac\w* (postel|lozk)|pristylk|hostovsk|pro hosty"),   # 7 000
    ("servirovaci-voziky", "Servírovací vozíky", "servirovaci-stolky", "Servírovací a kuchyňské vozíky", r"vozik|na kolecka|pojizdn"),   # 540 + 390
    ("kartoteky", "Kartotéky", "kancelarske-skrine", "Kartotéky a kontejnery pod stůl", r"kartotek|kontejner|pojizdn\w* (skrin|box)|zasuvkov\w* (box|skrink)"),   # 630 + 390
    # ------------------------------------------------------------ round 4 (16. 11. 2026, reports/vian/content-gap-kolo4-2026-11.md)
    ("vanicky-pro-miminka", "Vaničky pro miminka", "pro-miminka", "Vaničky pro miminka", r"vanick"),   # 4 300 + 3 700 + 720
    ("lehatka-a-houpatka", "Lehátka a houpátka", "pro-miminka", "Lehátka a houpátka pro miminka", r"lehatk|houpatk|houpack|houpac\w* (sitk|kresilk)"),   # 3 400 + 3 300 + 1 600
    ("hnizdecka", "Hnízdečka", "pro-miminka", "Hnízdečka pro miminka", r"hnizdeck|kokon"),   # 2 600
    ("spaci-pytle", "Spací pytle", "pro-miminka", "Spací pytle pro miminka", r"spaci (pytel|pytl|vak)"),   # 2 400
    ("koupelnove-police", "Poličky do koupelny", "police", "Poličky do koupelny", r"(do|pro|na) koupeln|koupelnov|do sprch|sprchov|bez vrtan"),   # 3 300 + 2 500 + 2 200 + 1 600
    ("lavice-s-uloznym-prostorem", "Lavice s úložným prostorem", "lavice", "Lavice s úložným prostorem", r"uloz|s truhl|s box|s kosem|s kosi|s vik"),   # 2 800
    ("presypaci-hodiny", "Přesýpací hodiny", "hodiny", "Přesýpací hodiny", r"presypac"),   # 2 300 + 1 500
    ("obaly-na-kvetinace", "Obaly na květináče", "kvetinace", "Obaly na květináče", r"\bobal\w* na kvetinac|kvetinac\w* obal|\bcachepot"),   # 1 200
    ("led-zrcadla", "Zrcadla s osvětlením", "koupelnova-zrcadla", "Zrcadla s LED osvětlením", r"\bled\b|osvetl|podsvic|se svetl|s svetl"),   # 1 300 + 1 900
    ("protiskluzove-podlozky", "Protiskluzové podložky", "koupelnove-doplnky", "Protiskluzové podložky do vany a sprchy", r"protiskluz|podlozk\w* (do|na) (van|sprch)"),   # 2 000 + 1 070
    ("stolky-do-postele", "Stolky do postele", "odkladaci-stolky", "Stolky do postele a na notebook", r"postel|snidan|notebook|laptop"),   # 1 200 + 1 100
    ("struhadla", "Struhadla a kráječe", "kuchynske-nacini", "Struhadla, kráječe a mandolíny", r"struhadl|krajec|mandolin|spiraliz"),   # 24 600
    ("valecky-na-testo", "Válečky na těsto", "kuchynske-nacini", "Válečky na těsto", r"valec\w* (na|k) test|\bvalecek\b"),   # 3 100
    ("stojany-na-noze", "Stojany na nože", "kuchynske-doplnky", "Stojany a bloky na nože", r"(stojan|blok|drzak)\w* (na|pro) noz|magnetick\w* (list|drzak|tyc)|nozov\w* blok|\bblok na noz"),   # 6 400
    ("zastery", "Zástěry", "kuchynsky-textil", "Kuchyňské zástěry", r"zaster"),   # 19 300
    ("chnapky", "Chňapky", "kuchynsky-textil", "Chňapky a kuchyňské rukavice", r"chnapk|rukavic|podlozk\w* pod (hrnec|horke)"),
    ("zavinovacky", "Zavinovačky", "detsky-textil", "Zavinovačky pro miminka", r"zavinov"),   # 18 700
    ("prebalovaci-podlozky", "Přebalovací podložky", "pro-miminka", "Přebalovací podložky", r"prebalov\w* podlozk|podlozk\w* (na|k) prebal"),   # 14 100
    ("party-stany", "Party stany", "pergoly-a-altany", "Party stany a zahradní pavilony", r"party|nuzkov\w* stan|skladac\w* stan|pavilon|\bstan\b|\bstany\b"),   # 21 900
    ("zahradni-fontany", "Zahradní fontány", "zahradni-dekorace", "Zahradní a pokojové fontány", r"fontan|kaskad|vodn\w* prvek"),   # 7 300
    ("zahradni-trpaslici", "Zahradní trpaslíci", "zahradni-dekorace", "Zahradní trpaslíci", r"trpasl"),   # 1 400
    ("etazery", "Etažéry", "tacy-a-podnosy", "Etažéry", r"etazer|patrov\w* (podnos|tac|misa)"),   # 3 100
    ("zapekaci-misy", "Zapékací mísy", "pekace-a-formy", "Zapékací mísy", r"zapekac|na zapekani"),   # 3 300
    ("magneticke-tabule", "Magnetické tabule", "nastenky-a-tabule", "Magnetické tabule", r"magnetick|bil\w* tabul|whiteboard"),   # 12 800
    ("cajove-konvice", "Konvice na čaj", "hrnky-a-salky", "Konvice na čaj a čajníky", r"konvic\w* (na|pro) caj|cajov\w* konvic|cajnik|\bkonvick\w* na caj"),   # 14 600
    ("french-press", "French press a moka konvičky", "hrnky-a-salky", "French press a moka konvičky", r"french ?press|moka (konvic|kavovar|pot)|bialetti (moka|venus|brikka|musa|kitty|express)|presov\w* konvic|konvic\w* na kav|kavov\w* konvic"),   # 14 900
    ("vonne-tycinky", "Vonné tyčinky", "difuzery-a-vune", "Vonné tyčinky", r"tycink|\bvonn\w* (tyc|kuzel)|\bkadidl"),   # 6 000
    ("solne-lampy", "Solné lampy", "dekoracni-osvetleni", "Solné lampy", r"soln\w* lamp|\bsolna\b|himalaj"),   # 4 000
    ("led-neony", "LED neony", "dekoracni-osvetleni", "LED neony a světelné cedule", r"neon|svetel\w* cedul"),   # 800 + 400
    ("susene-kvetiny", "Sušené květiny", "umele-kvetiny", "Sušené květiny a pampová tráva", r"susen|pampov"),   # 3 000 + 2 400
    ("krbove-prislusenstvi", "Krbové příslušenství", "biokrby", "Krbové nářadí, koše a stojany na dřevo", r"stojan\w* na drev|kos\w* na drev|krbov\w* (narad|sada|kos|zasten|mriz|rukavic|kleste|lopat)|\bdrevnik|\bnarad\w* ke krbu"),   # 3 400 + koš na dřevo
    ("lapace-snu", "Lapače snů", "nastenne-dekorace", "Lapače snů", r"lapac\w* snu"),   # 4 400
    ("remosky", "Remosky", "drobne-kuchynske-spotrebice", "Remosky", r"remosk|elektrick\w* pekac"),   # 16 000
    ("fondue-a-raclette", "Fondue a raclette", "drobne-kuchynske-spotrebice", "Fondue a raclette", r"fondue|raclett"),   # 3 400
    ("maslenky", "Máslenky", "skladovani-potravin", "Máslenky", r"maslenk|doz\w* na maslo"),   # 4 800
    ("solnicky-a-mlynky", "Solničky a mlýnky na koření", "skladovani-potravin", "Solničky, pepřenky a mlýnky na koření", r"solnick|peprenk|mlyn\w* na (pepr|sul|koreni)|korenk|korenick|stojan\w* na koren"),   # 2 200 + mlýnky
    # ------------------------------------------------------------ round 5 (16. 11. 2026, reports/vian/content-gap-kolo5-2026-11.md):
    # searched phrases without a page of their own, checked against the kw2 phrase landings and the live catalogue (>= 5 products)
    ("vence-na-dvere", "Věnce na dveře", "adventni-dekorace", "Věnce na dveře", r"^(?!.*drzak).*(\bven(ec|ce)\w* na dver|\bna dvere\b.*\bven(ec|ce))"),   # 960 + 640
    ("adventni-vence", "Adventní věnce", "adventni-dekorace", "Adventní věnce", r"^(?!.*\b(drzak|hacek|haky)\b).*\bven(ec|ce|cu|cem|ci)\b"),   # 14 700 + na stůl 3 200
    ("wok-panve", "Wok pánve", "panve", "Wok pánve", r"^(?!.*(lopat|limec|poklic|kartac|obracec|stojan\w* na)).*\bwok"),   # 12 000
    ("elektricke-krby", "Elektrické krby", "biokrby", "Elektrické krby", r"elektrick\w* krb"),   # 5 500 + do bytu, na zeď
    ("cukrenky", "Cukřenky", "talire", "Cukřenky", r"\bcukrenk"),   # 2 400
    ("misy-a-misky", "Mísy a misky", "talire", "Mísy, misky a salátové mísy", r"^(?!.*(\bwc\b|drez|sedatk|mydl|odkapav|na postaveni)).*(\bmis(a|y|u|ek)\b|\bmisk(a|y|u|ami)?\b|salatov\w* mis)"),   # 5 900 + 5 200 + salátová
    ("rucni-slehace", "Ruční šlehače a tyčové mixéry", "mixery-a-roboty", "Ruční šlehače a tyčové mixéry", r"rucn\w* (slehac|mixer)|tycov\w* mixer|\bslehac\b|penic\w* mlek"),   # 6 100 + 4 200
    ("aromalampy", "Aromalampy", "difuzery-a-vune", "Aromalampy", r"aromalamp"),   # 2 100
    ("organizery-do-supliku", "Organizéry do šuplíku", "kuchynske-doplnky", "Organizéry do šuplíku a zásuvky", r"organizer\w* (do|na) (supl|zasuv)|\bdo (supliku|zasuvky)\b"),   # 2 400 + 800
    ("detske-knihovny", "Dětské knihovny", "detske-skrine-a-ulozne-boxy", "Dětské knihovny a regály na knížky", r"knihovn|regal\w* na kni"),   # 5 700
    ("teplomery-na-maso", "Teploměry na maso", "kuchynske-nacini", "Teploměry na maso a do trouby", r"teplomer"),   # 3 000 + trouby 580 + vpichový 490
    ("cedniky", "Cedníky", "kuchynske-nacini", "Cedníky a síta", r"\bcednik|\bsito\b|\bsita\b"),   # 1 600
    ("sitka-na-caj", "Sítka na čaj", "kuchynske-nacini", "Sítka a louhovátka na čaj", r"sitk\w* (na|pro) caj|caj\w* sitk|louhovat"),   # 1 400
    ("rohozky", "Rohožky", "behouny-a-predlozky", "Rohožky ke dveřím", r"^(?!.*(sorpc|schod)).*\brohoz"),   # 3 500 + ke dveřím 3 100 + venkovní
    ("hacky-na-zed", "Háčky na zeď", "vesaky", "Háčky na zeď a na obrazy", r"^(?!.*vesak)(\w+ ){0,2}hac(ek|ky|ku|iky)\b|\bhac\w* na obraz"),   # háčky na obrazy 1 700 + háčky 600
    ("plechy-na-peceni", "Plechy na pečení", "pekace-a-formy", "Plechy na pečení a pizzu", r"\bplech"),   # 2 300 + pečení
    ("servirovaci-tacy", "Servírovací tácy", "tacy-a-podnosy", "Servírovací tácy", r"servirovac\w* tac|\btac\w* (na|k) servir"),   # 710 + 440
    ("stolni-hodiny", "Stolní hodiny", "hodiny", "Stolní hodiny", r"\bstoln\w* hodin"),   # 1 300
    ("dzbany", "Džbány", "sklenice", "Džbány na vodu", r"\bdzban"),   # na vodu 920 + 690
    ("podsedaky", "Podsedáky", "polstare-na-zahradni-nabytek", "Podsedáky na židle a lavice", r"podsedak|sedak\w* na (zidl|lavic)"),   # 4 200 + na židle 3 300 + na lavici 2 400
]

# older family landings (scripts/landings.py) that the subcategory replaces: once the subcategory is public, the landing is
# not built (its path is reserved) and its URL redirects (301) to the subcategory, which has the bigger selection
SUPERSEDES = {
    "satni-skrine-s-posuvnymi-dvermi": "/satni-skrine/s-posuvnymi-dvermi/",
    "satni-skrine-se-zrcadlem": "/satni-skrine/se-zrcadlem/",
    "rohove-satni-skrine": "/satni-skrine/rohove/",
    "ergonomicke-zidle": "/kancelarske-zidle/ergonomicke/",
    "manzelske-postele": "/postele/manzelske/",
    "jednoluzkove-postele": "/postele/jednolozkove/",
    "postele-s-uloznym-prostorem": "/postele/s-uloznym-prostorem/",
    "rozkladaci-jidelni-stoly": "/jidelni-stoly/rozkladaci/",
    "kulate-jidelni-stoly": "/jidelni-stoly/kulate/",
    "keramicke-grily": "/grily/keramicke/",
}

SUBCATS = {s: (name, parent, h1, re.compile(rx, re.I)) for s, name, parent, h1, rx in SUBS}
SUB_PARENT = {s: v[1] for s, v in SUBCATS.items()}
BY_PARENT = {}
for _s, (_n, _p, _h, _rx) in SUBCATS.items():
    BY_PARENT.setdefault(_p, []).append((_s, _rx))

_bad = [(s, p) for s, p in SUB_PARENT.items() if p not in CATS or s in CATS]
assert not _bad, f"subcategory with an unknown parent or clashing with a category: {_bad}"
assert len(SUBCATS) == len(SUBS), "duplicate subcategory slug"
assert set(SUPERSEDES) <= set(SUBCATS)


# a name that starts with an accessory or spare part is not the thing itself ("Ochranný obal na kotlové grily",
# "Šuplík k domečkové posteli", "Dřevěné uhlí", "Kroužek na záclony"): such products stay in the category only
ACCESSORY = re.compile(r"^(\w+ ){0,2}?(ochrann\w* )?(obal|kryt|plachta|nahradn\w*|suplik|krouz\w*|udrzb\w*|zesilen\w*|lupink\w*|"
                       r"brikety|vune|naplne?|filtr\w*|kolecka|nozicky|nozky|podsalek|sada naradi|prislusenstvi|"
                       r"cistic\w*|odvapnovac\w*|kapsle|sacky?|hadice k vysav)\b")

ACCESSORY_OK = re.compile(r"^(\w+ ){0,2}?obal\w* na kvetinac")   # a pot cover is a product of its own (subcategory obaly-na-kvetinace)


def sub_of(p):
    """The subcategory of a product, or None. Only rules of its own category are tried; the first that matches wins."""
    rules = BY_PARENT.get(p.get("cat"))
    if not rules:
        return None
    name = fold(clean(p.get("name"))).replace("-", " ")
    if ACCESSORY.search(name) and not ACCESSORY_OK.search(name):
        return None
    for slug, rx in rules:
        if rx.search(name):
            return slug
    return None


def _register():
    """Subcategories join the tree (name, parent CATEGORY, h1, "", icon of the parent): crumbs walk up through the
    parent to the room, tiles get the parent's icon."""
    import taxonomy as T
    for s, (name, parent, h1, _) in SUBCATS.items():
        T.TREE[s] = (name, parent, h1, "", T.ICON.get(parent, "kreslo"))
        T.ICON[s] = T.ICON.get(parent, "kreslo")


_register()
