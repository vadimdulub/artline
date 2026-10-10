#!/usr/bin/env python3
"""Individual Detroit decisions against the completed native capture and identity scope."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-detroit-followup-v4-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN;IID=f.IID;ref=f.ref;checked=f.f.checked
CANDIDATES=RUN/'native-candidates-002.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CITATIONS=RUN/'identity-citations-002.json.gz'
HOLDINGS={14:'bad50959-c7b8-5173-9d6d-41eb1d9184b7',15:'18d41427-bdc0-596b-9e9d-5bb601f49747'}
HOLDS={
2:'Native provenance explicitly says location unknown since 1951; no accepted current holding.',
21:'Artwork date repeats the creator lifespan 1482–1525. Independent creation evidence is needed.',
24:'The former Samson/actor attribution and the Louvre red-coat portrait require a completed physical-version comparison.',
31:'Inventory 55.5.B is the reverse of The Nightmare, 55.5.A, already represented. Do not count the reverse as another physical work.',
33:'Artwork date repeats Ghirlandaio’s lifespan 1448–1494. Independent creation evidence is needed.',
36:'Date repeats the creator activity interval 1356–1399; no independently established creation date.',
37:'Date repeats the creator activity interval 1356–1399; no independently established creation date.',
50:'The native oil-on-canvas classification conflicts with plate/sheet dimension terminology; physical object type needs clarification.',
52:'Former Giaquinto attribution: Montefortino national-catalogue object 1100055447, inventory 27, remains an unresolved version lead.',
54:'The Turin Dolo version, national-catalogue 0100350774, inventory 418, remains insufficiently distinguished.',
57:'Several Henner Magdalene compositions remain unresolved; a generic title and broad century do not establish a distinct version.',
65:'Preserve After Frans Hals. The Finnish Laughing Boy 390125 remains an unresolved copy/version comparison.',
101:'Preserve Workshop of Georges de La Tour. Rouen and other Saint Sebastian versions require further complete comparison.',
109:'Preserve School of Leonardo da Vinci. Former Verrocchio attribution and close Madonna versions require further primary-object verification.',
114:'Close Matteo Madonna compositions in Italian collections and the Met remain unresolved.',
115:'Close Matteo Madonna-and-angels versions in Italian collections and the NGA remain unresolved.',
116:'Mariotto Madonna versions in Italian collections remain unresolved.',
117:'Creation range repeats the Master’s activity interval, and close Madonna versions remain unresolved.'}
NOTES={
8:'School of Fabriano is the detail attribution, not the unqualified index creator. DIA 29.243 is a 40.6 × 24.8 cm panel, acquired 1929. Yale’s 1425 Madonna is 91.8 × 62.8 cm; NGA 1939.1.255 is 95.7 × 56.5 cm; Met 30.95.262 is 85.7 × 50.8 cm. These are different physical panels. Keep the source circa 1400 and school label.',
9:'DIA 21.214 is the 1633 Pickenoy lady, 123.5 × 91.4 cm, Booth acquisition 1921. Compared Pickenoy women S100, 1628, 119.5 × 87 cm; 282CM, 1624, 105 × 80 cm; and the named Johanna le Maire portrait, 1622–29. Their dates, sitters or physical dimensions distinguish them.',
10:'DIA 43.33 is the 31.1 × 37.2 cm Engert interior, purchased 1943. Former Lawrie attribution and New York Interior title were included in discovery. The Engert lead depicting four Zlamal children, 1840, Gm96/4, is another subject. Preserve the literal nineteenth-century date.',
11:'DIA 89.61 is one small triptych, not three new artworks. Preserve the literal detail label School of School of Flanders, including the repeated wording, and former Patinier/Lombard evidence. NGA 1937.1.27 is a much larger 1482–85 triptych; the Cleveland 4.7 × 3.7 cm fragment and Barnes 65.7 × 42.2 cm painting are separate objects.',
12:'DIA 44.220 is the School of Florence Pilate panel, 1320, 17.2 × 15.1 cm. The 27 subject leads are principally later prints and differently attributed panels. Keep the school label and the source’s inconsistent acquisition/publication chronology as evidence without silently correcting it.',
13:'DIA 44.219 is the School of Florence Agony panel, 1320, 16.7 × 15.1 cm. The 117 subject leads are principally later named-artist works. The anonymous Cyprus 1197 lead, apsida 13614, is a fresco, not this panel. Preserve the source’s acquisition/publication chronology as recorded.',
14:'Exact existing Favanne object: title, creator, inventory 1984.36 and Wikidata Q64547337 agree with the native 82.6 × 45.7 cm painting. DIA records Neave, Corby Howard, Sotheby’s 1983 and Auslander Wittgenstein provenance before the 1984 purchase. Reconcile the existing pending holding; preserve its exact 1715, media and all metadata. Native circa 1715 remains citation evidence.',
15:'Exact existing Favanne object: title, creator, inventory 1984.37 and Wikidata Q64547342 agree with the native 83.2 × 47.6 cm painting. DIA records Neave, Corby Howard, Sotheby’s 1983 and Auslander Wittgenstein provenance before the 1984 purchase. Reconcile the existing pending holding; preserve its exact 1715, media and all metadata. Native circa 1715 remains citation evidence.',
16:'Fragonard’s Gardener, 71.393, is one of three separate large 1754–55 canvases. The 1971 sale lists separate lots for the Gardener, Grape Gatherer and Reaper. The 244-record creator scope contains no same-object garden/harvester match; count each separately accessioned canvas once.',
17:'Fragonard’s Grape Gatherer, 71.391, is a separately accessioned large 1754–55 canvas with its own 1971 auction lot, distinct from 71.392 and 71.393. The expanded creator scope contains no same-object match.',
18:'Fragonard’s Reaper, 71.392, is a separately accessioned large 1754–55 canvas with its own 1971 auction lot, distinct from 71.391 and 71.393. The expanded creator scope contains no same-object match.',
19:'DIA 22.10 is the Francesco dai Libri panel, 61.6 × 44.8 cm. Former Foppa and Maestro dei Garofani attributions were included in identity discovery. Met Foppa 30.95.293 is 43.8 × 32.1 cm; the Brera panel is 37 cm. Preserve the broad literal mid-fifteenth-to-early-sixteenth-century range without inventing narrower bounds.',
20:'DIA 30.90 is Franchoys the Younger’s Saint Michael, 1648–49, 25.4 × 19.7 cm on panel, formerly Rubens. Primary Thyssen object 348 is the Rubens-workshop Saint Michael, circa 1622, 149 × 126 cm on canvas, acquired through Haberstock in 1928. Different support, dimensions and acquisition establish separate objects; retain the former attribution.',
22:'DIA 68.294 is Foppa’s Child with Saint Benedict and Angels, circa 1478, 143.5 × 109.9 cm, Fisher gift 1968. National Gallery Adoration of the Kings and Madonna of the Book have different subjects/compositions. Keep the source bibliography’s workshop qualification as evidence alongside the current source heading.',
23:'DIA 38.15 is Van Geel’s carriage hold-up, circa 1615–25, 24.4 × 45.7 cm, Douwes acquisition 1938. Related Boslandschap circa 1633 and the SMK 1634 mountain landscape, 21 × 35 cm, are different physical works and subjects.',
25:'DIA 41.10 is Claude’s Sunrise, 1631, 76.2 × 117.2 cm, Ford gift 1941. Met 47.1 is 1646–47 and 102.9 × 134 cm. The similar sunrise title does not identify the same painting.',
26:'DIA 42.127 is Claude’s 1643 copper seaport, 40.6 × 53.3 cm, Whitcomb acquisition 1942. NG5 is a 1644 canvas, 103 × 131 cm. Keep historical 1638 dating and attribution questions in the retained bibliography; do not substitute the National Gallery version.',
27:'The DIA exhibition PDF identifies 52.253, circa 1623–25, 184.0 × 141.6 cm, Leslie H. Green gift. Actual visual comparison shows Judith with a raised palm shielding a candle and a crouching maid at lower right. The selected WikiArt image cited by existing 42c01256-f3ac-5718-9d51-bbbc5e3481b8 shows two upright women, a low sword and a head held at waist height, without that candle gesture. These are different complete compositions, not a crop or reverse. Preserve the mixed existing record unchanged; add this distinct native object in review.',
28:'DIA 68.47 is Orazio’s Young Woman with a Violin, circa 1612, 83.5 × 97.8 cm, Ford gift 1968, formerly Vermeer. The Artemisia Saint Cecilia in the Spada collection has a lute, another creator and distinct early Spada provenance. The primary Spada guide supports the distinct composition.',
29:'DIA 1986.40 is Gérard’s Daphnis and Chloe, circa 1824, 100 × 114 cm. Louvre INV4740 measures 204 × 228 cm and entered in 1825. Preserve both physical versions separately.',
30:'DIA 51.63 is the circa 1510 Flagellation. The Goertschacher/Görtschacher spelling variants were included in creator discovery; no same-object title, native URL or relevant inventory match was found. Preserve the native creator spelling.',
32:'DIA 31.53 is the fifteenth-century Ghirlandaio portrait, 51.8 × 38.7 cm, Carmichael–Grimthorpe–Ward–Aram provenance and 1931 acquisition. Primary NG2489 is 38.7 × 27.6 cm, circa 1480–90, Barberini–Salting provenance and 1910 acquisition. Preserve the native bibliography’s 1972 in-the-manner-of qualification.',
34:'DIA Giambono Saint Peter, 45.18, is 57.1 × 39.8 cm. NGA 1939.1.80 is 87.7 × 35.9 cm. Same saint and creator do not make these different-sized panels interchangeable.',
35:'DIA Giaquinto Rest, 77.73, is the 1764–65 Naples San Luigi canvas, 287 × 180.7 cm, acquired 1977. Louvre RF1983-60 is the 1740–42 Turin sketch, 98 × 63 cm, donated 1983. They are distinct versions.',
38:'DIA Giordano Entombment, 72.434, circa 1659–60, is 212.1 × 159.4 cm, Tannahill gift 1972. The expanded Giordano scope contains no corresponding entombment/lamentation object; native accession and provenance support one separate canvas.',
39:'DIA Giordano Shepherds, 44.3, circa 1690–91, is 70.5 × 52.9 cm, Haussmann–Schaeffer acquisition 1944. Louvre MI869 is circa 1688, 115 × 136 cm, La Caze acquisition 1869. The retained primary catalogue comparison distinguishes the versions.',
40:'DIA Lady Anna Horatia Waldegrave, 67.1, circa 1783, has a distinct named sitter, inventory and acquisition. The source 8.3 × 64.1 cm dimensions conflict with its 104.8 × 91.4 cm frame and appear erroneous; preserve the literal dimensions and uncertainty, without inventing a corrected height.',
41:'DIA Edward Swinburne, 49.508, 1785, 68.9 × 59.7 cm, Foy gift 1949, is separately identified from Sir John Edward Swinburne, 49.507. Other portrait leads depict Edward Richard Gardiner or Darnley, not this sitter.',
42:'DIA Sir John Edward Swinburne, 49.507, 1785, 67 × 58.4 cm, Foy gift 1949, is separately identified from Edward Swinburne, 49.508. Preserve both sitters and inventories.',
43:'DIA Market Cart, 74.267, circa 1787, 130.2 × 108 cm, Fisher gift 1974, is distinct from NG80, 1786, 184 × 153 cm, acquired 1830. Preserve the source bibliography’s 1982 description as a copy; no substitution or correction of the existing National Gallery record.',
44:'DIA Lady Anne Hamilton, 71.170, circa 1778, 236.9 × 154.6 cm, Dodge gift 1971, has Chichester provenance. Lady Alston, Gosset and Tatton portrait leads depict different named sitters.',
45:'DIA Gambard Oedipus, 76.73, 1843, 146.7 × 114 cm, Heim acquisition 1976, is distinct from the creator-scope Christ Crucified sketch of 1874. Native title, inventory and purchase establish the object.',
46:'DIA Gandolfi Venus at Vulcan’s Forge, 74.2, circa 1770–75, 191.5 × 142.5 cm, Castellane provenance and Shelden acquisition 1974. Creator leads depicting Cana, saints, Raphael or Bacchus are different subjects.',
47:'DIA Elizabeth Lewis, F79.49, circa 1776, 61 × 68.6 cm, Grigaut gift 1979, is one of two distinct Gardner pendants. Yorke, Gray and Charlotte Wynn leads depict other named sitters.',
48:'DIA Henry Greswolde Lewis, F79.48, circa 1776, 61 × 68.6 cm, Grigaut gift 1979, is a separate pendant from Elizabeth Lewis F79.49; same size and acquisition do not collapse the distinct sitters.',
49:'DIA Garofalo Holy Family with Saint Anne, 31.23, circa 1530, 38.7 × 54.6 cm, Northbrook–Ehrich acquisition 1931. Courtauld P.1966.GP.161 is circa 1520, 47.5 × 32.1 cm, Gambier Parry acquisition 1966. Primary catalogue evidence distinguishes the horizontal and vertical panels.',
51:'DIA Doña Amalia Bonells de Costa, 41.80, circa 1805, 87.3 × 65.4 cm, Booth gift 1941, depicts a woman. Met 61.259 is her son José, circa 1810, 105.1 × 84.5 cm; distinct named sitters.',
53:'DIA Greuze Boy with an Apple, 53.365, 40 × 32.4 cm, Whitcomb acquisition 1953. The National Gallery explicitly distinguishes its NG1020 version, 40.6 × 32.1 cm, Wynn Ellis acquisition 1876, from Detroit’s version. Near-identical dimensions alone do not collapse them.',
55:'DIA Hackaert Stag Hunt, 50.198, circa 1665–70, 86.4 × 63.8 cm, Clark gift 1950. NG829 is 99.7 × 120 cm, Peel acquisition 1871; Rijks SK-A-131 is 58.5 × 46 cm, Dupper bequest 1870. Primary catalogue comparisons distinguish all three objects.',
56:'DIA Van der Helst Young Man, 25.216, 1654, 91.4 × 73.7 cm, Young acquisition 1925. SMK KMSsp443 is 97 × 78 cm; KMSsp444 is 1651, 84.5 × 66.5 cm; Getty 70.PA.12 is 1650, 74.3 × 60.3 cm. The compared portraits are separate versions.',
58:'DIA Hesse Young Woman, 79.144, 1858, 136.8 × 98.1 cm, remained with the sitter’s descendants before the Versailles 1979 sale. The girl-with-fruit lead is a 1838 study, 92 × 70 cm, a separate composition.',
59:'DIA Heussen Fruit, 31.308, circa 1630, 76.2 × 109.2 cm, acquired 1931, is a still life. NG loan L1344 is the Hals/Heussen Woman with Fruit, 157 × 200 cm, a distinct large figure composition.',
60:'DIA Bull in a City Street, 38.31, circa 1670, 31.4 × 40.3 cm, credits both Adriaen van de Velde and Jan van der Heyden. The actual source maker fields are parsed separately and retained together as the object label. One canvas counts once; neither creator is silently dropped or promoted to a new authority.',
61:'DIA Miss Hamilton, 48.312, circa 1735–45, 127 × 101.6 cm, Ford gift 1948. Highmore’s Mrs Flower and Pamela narrative scenes are other sitters/subjects; no same-object native or relevant inventory collision.',
62:'DIA Henry Gladwin, 53.6, eighteenth century, 71.1 × 57.8 cm, descends through the sitter’s family to the Ferry-funded 1953 acquisition. The expanded Hall scope includes other homonymous artists and other sitters, with no Gladwin object.',
63:'DIA Hals Woman, 23.27, 1634, 73 × 56.2 cm on oak, acquired 1923, was formerly attributed to Verspronck. The reviewed women have different source inventories, sitters or dimensions. Preserve the former attribution in evidence.',
64:'DIA Hendrik Swalmius, 49.347, 1639, 27 × 20 cm on oak, acquired 1949, has no same-sitter match in the creator scope. Retain the 1972 bibliography’s copy qualification alongside the current Frans Hals heading.',
66:'DIA Jan Hals Man, 52.144, 1644, 87.6 × 71.1 cm, Briggs acquisition 1952. Frans Hals portrait leads are distinct attributed versions; the source specifically names Jan Hals.',
67:'DIA Gavin Hamilton Cleopatra, 80.44, 1767–69, 134.6 × 98.4 cm, acquired 1980. The 208-record identity scope contains no corresponding Cleopatra object; unrelated Hamilton creators and subjects do not establish a duplicate.',
68:'DIA Gros Murat at Aboukir, 49.337, circa 1805, 88.3 × 138.4 cm, is a small canvas backed by board. Versailles MV2276/INV5065/LP279 is the 1807 monumental 578 × 968 cm version. These are distinct physical works.',
69:'DIA Hobbema River Scene, 89.38, 1658, 52.7 × 68.3 cm on oak, Scripps gift 1889, was formerly Van Goyen. Expanded former-creator discovery found no same-object match; keep the current Hobbema label and former attribution evidence.',
70:'DIA Hobbema Cottage, 67.115, circa 1663, 62.2 × 86.4 cm, Fisher gift 1967. Cleveland 1942.641 is 84 × 111.4 cm. Related cottage subjects are different physical paintings.',
71:'DIA Hue Marie Joseph Chentier, 30.377, 1793, 67.9 × 59.7 cm, Floriat acquisition 1930, is a named portrait. Other Hue records principally depict landscapes; no corresponding sitter object.',
72:'DIA Fruit Vendor, 36.10, circa 1615–20, 130.2 × 97.8 cm, Ford gift 1936, uses the conventional Il Pensionante del Saraceni label and was formerly Caravaggio. Retain the current source designation without creating a biographical painter authority.',
73:'DIA Holbein the Younger Woman, 77.81, 1532–34, 23.2 × 19.1 cm on oak, Ford gift 1977. The same-title WikiArt Holbein the Elder lead is 1518–20; NGA 1991.182.18a is a 1508 oval, 14.4 × 10.3 cm. Creator generation, shape and dimensions distinguish them.',
74:'DIA Hondecoeter Poultry Yard, 45.16, circa 1668. Literal source dimensions 112.1 × 38.7 cm conflict with the 135.3 × 151.4 cm frame; preserve that uncertainty. Rijks SK-C-58 is 192.3 × 109.4 cm and the Baltimore version 93.3 × 114 cm. Separate inventories and provenance distinguish them without correcting the native dimension typo.',
75:'DIA Honthorst Sophia, 72.860, 1641, 74.6 × 59 cm on oak, Fisher gift 1972, was formerly identified as the Winter Queen. NG6362 depicts Elizabeth, 1642, 205.1 × 130.8 cm on canvas, Craven acquisition 1965. Different sitter and physical version.',
76:'DIA De Hooch Mother Nursing Her Child, 89.39, circa 1674/1676, 79.7 × 59.7 cm, Scripps gift 1889, formerly Dutch Interior. The related mother-delousing-child subject is a different composition; the nursing object retains its own accession and provenance.',
77:'DIA attributed Hoogstraten Perspective Box, 35.101, 1663, 41.9 × 30.2 × 28.3 cm, acquired 1935. NG3832 is 1655–60, 58 × 88 × 60.5 cm, Witt acquisition 1924. Count one physical box, not its painted faces, and preserve Attributed to.',
78:'DIA School of Rembrandt Annunciation, 09.13, 1650–55, 51.8 × 43.5 cm on oak, Scripps gift 1909. Former Dou, Hoogstraten, Flinck and De Bray labels were included in discovery. Met 1992.133 depicts the Annunciation of the Virgin’s death, circa 1670, 66 × 52.7 cm, a different subject and object.',
79:'DIA Hoppner John Granville, 77.8, 1790–95, 76.2 × 63.5 cm, Ford gift 1977. Former Beechey attribution is preserved and was included in discovery. Other portrait leads concern different sitters.',
80:'DIA Hoppner Little Gardener, 48.384, 1758–1800, 127 × 102.9 cm, Fisher gift 1948, formerly Reynolds and Young Lady in a Wood. The literal broad creation range ends in 1800, not Hoppner’s death in 1810; it is not an identical lifespan field. Retain the broad source range without narrowing it.',
81:'DIA Hoppner Mrs Dottin, 68.299, 1803–04, 222.9 × 147.6 cm, Fisher gift 1968. The named sitter, large format, inventory and acquisition distinguish this from other Hoppner female portraits.',
82:'DIA Hoppner Susannah Edith, Lady Rowley, 71.171, circa 1785, 76.2 × 63.5 cm, Dodge gift 1971. Other portrait leads depict different named sitters; no source or relevant inventory collision.',
83:'DIA Jacomart Three Virgin Martyrs, 41.83, fifteenth century, 37.5 × 146.7 cm, purchased 1941. Getty ULAN supports the Baco/Bacho alias search. Its seven alias-derived leads are Baccio Bandinelli sixteenth-century drawings, not this wide martyr panel.',
84:'DIA Isabey Wreck, 07.14, 1854, 96.5 × 76.2 cm, Walker gift 1907. French print leads measure 20.8 × 15 cm; Walters After the Storm is 1844, 76 × 115.5 cm. Different supports, dimensions and compositions.',
85:'DIA Isabey Grandfather’s Armor, 20.96, 1876, 44.5 × 62.2 cm on panel, Ferry acquisition 1920. Primary NG2714 Grandfather’s Birthday is 1866, 24.1 × 28.9 cm, Drucker gift 1910. The related domestic titles do not identify the same object.',
86:'DIA Knijff Hoorn North Port, 89.36, 1648, 42.9 × 64.1 cm on oak, Scripps gift 1889, formerly Van Goyen and River Scene. Expanded Van Goyen river leads include Met 07.285.2, a drawing; SMK KMS3714, 1646, 37 × 58.5 cm; MIA 83.84, 1648, 64.14 × 93.98 cm; and Rennes/Bordeaux differently sized dated scenes. None establishes this Hoorn object.',
87:'DIA Kessel Insects, 36.9, seventeenth century, 14 × 19.1 cm on panel, Boer gift. Missing provenance detail remains unknown. NGA 1983.19.3 is 11 × 14.8 cm; Rijks SK-A-793 is 10.9 × 14.6 cm on copper, acquired 1882. Primary Rijks evidence distinguishes that close version.',
88:'DIA Juan de Flandes Crowned with Thorns, 30.345, circa 1505, 21.6 × 16.2 cm on oak, Goudstikker acquisition 1930, has Isabella-panel provenance. Morros alias discovery and translated thorn/coronation subject searches produced no same-object lead.',
89:'DIA Kalraet River Landscape, 09.14, 1691, 40 × 54.3 cm on oak, Scripps gift 1909. The creator-scope SMK KMSst324 Ryttere is 51 × 67 cm and depicts riders, a separate object.',
90:'DIA Ludolf de Jongh Hunting Party, 58.169, circa 1665–70, 69.2 × 82.6 cm, Whitcomb acquisition 1958. The 49-record scope includes other Claude de Jongh and Palma records and different subjects; none matches this courtyard party.',
91:'DIA Jordaens Job, 43.418, circa 1620, 67 × 52.1 cm on oak, Gimbel–Hammer acquisition 1943. The 158-record creator pool contains no Job/Giob subject match; source inventory and provenance identify a separate panel.',
92:'DIA Keilhau Sleeping Girl, 39.592, circa 1655–60, 48.3 × 100.3 cm, Heimann acquisition 1939. Former Amorosi, Velazquez and Drost attributions and Keil/Bernardo aliases expanded discovery to 539 records. The sleep/repose hit is Fortuny’s nineteenth-century camels; Keil Girl Teasing Boy, inventory 825, 59 × 72 cm, is another subject.',
93:'DIA Lawrence Mrs Ayscoghe Boucherett, F74.46, circa 1795, 76.5 × 63.5 cm, Hanson gift 1974. Mrs Cuthbert, 1817, and Mrs Alice Wood, 1830, are different named sitters.',
94:'DIA Le Brun Presentation in the Temple, 73.1, 1645, 267 × 194.3 cm, acquired from a Lyon chapel in 1973. The 294-record pool contains no corresponding Presentation/purification/temple subject. Literal inventory 73.1 is retained.',
95:'DIA Antoine Le Nain Village Piper, 30.280, 1642, 22.5 × 30.5 cm on copper, acquired 1930. The 29-record Le Nain scope contains cart, cards, spinner and family compositions, not this separately identified piper.',
96:'DIA Master of the Games Peasant Family, 28.123, circa 1650, 87.9 × 109.2 cm on canvas, acquired 1928, was formerly Mathieu Le Nain. Primary Louvre family versions RF2081, MI1088 and RF1941-20 measure 113 × 159, 97 × 122 and 61 × 78 cm, with separate acquisition histories. Louvre RF1067 is 32 × 40 cm on copper, 1642, gifted 1897. NGA 1952.2.20 is 55.6 × 64.7 cm and Périgueux 10.1.2 is 60 × 73 cm. These comparisons distinguish the close versions.',
97:'DIA Le Prince Cowherd, 28.92, 1770–79, 24.8 × 32.4 cm, acquired 1928, formerly Fragonard. Met ford/stream, 1756, is 31.3 × 41 cm; MIA 70.25 shepherd, 1777, is a 28.26 × 39.05 cm print; the NGA mountain, circa 1765, is 21.5 × 32.8 cm. Different works and supports.',
98:'DIA La Hyre Finding of Moses, 71.30, 1647–50, 69.9 × 89.5 cm, Mopper acquisition 1971, was formerly Vien. The expanded 232-record scope contains no Moses/Moïse subject match.',
99:'DIA La Hyre Sacrifice of Isaac, 72.36, circa 1650, 64.8 × 79.1 cm, Mopper acquisition 1972. Preserve the 1989 bibliography’s description as a copy of the Reims original. PM2508, 23.4 × 33.5 cm, and D2646, 20.4 × 16.7 cm, are separate drawings/prints.',
100:'DIA La Tour Young Virgin Mary, 38.8, circa 1640, 57.8 × 44.5 cm, Friry–Waidmann–Minimes Nancy provenance and 1938 acquisition. The Frick-contributed primary AMICA record identifies Education of the Virgin, 48.1.155, as the complete 83.8 × 100.4 cm painting purchased 1948. Separate physical dimensions, full composition and acquisition distinguish that version from Detroit’s object.',
102:'DIA Lagrenée Pygmalion, 72.296, 1781, 59.4 × 48.9 cm, acquired 1972, formerly La Sculpture. The Finnish National Gallery primary 2018 research PDF identifies its Sinebrychoff/Antell painting as 1777, 104 × 86 cm. Different date, dimensions and provenance establish separate versions.',
103:'DIA Four Continents, 58.280, eighteenth century, 371.2 × 171.8 cm, Hearst acquisition 1958, is attributed to Lairesse. Count the single canvas once, not four continents. Science, 289 × 161 cm, and Riches, 288 × 153 cm, are different subjects and objects.',
104:'DIA Kyte Mrs E.B., 57.255, 1741, 76.2 × 66 cm, signed F. Kyte and inscribed E.B. aged 72, Colnaghi acquisition 1957. Former Mrs John Gainsborough identification was included in discovery. Gainsborough women are later dated and/or different named sitters; retain the current source identification.',
105:'DIA Lancret Repast, 28.95, circa 1725, 55.9 × 73.7 cm, Jonas acquisition 1928, has Mme Lancret 1782 lot 14, Beurnonville 1883 and Barre 1894 provenance. NGA 1952.2.22 Picnic is 61.5 × 74.8 cm and follows Frederick II–Hohenzollern–Wildenstein 1923–Kress 1946–NGA 1952. Primary NGA provenance distinguishes the close composition.',
106:'DIA Largillière Count Rutowski, 80.45, circa 1729, 74.3 × 58.1 cm, Polish private–Heim acquisition 1980. The creator scope has other named sitters and no Rutowski object.',
107:'DIA Lefèvre Odiot, 81.692, 1822, 157.5 × 125.1 cm, remained with the Odiot family until 1979, then Segoura/Heim. Keep the source’s 1982 acquisition narrative despite the 81 accession prefix. Other Lefèvre portraits depict different named sitters; no Odiot duplicate.',
108:'DIA Lely Letter, 53.80, 1650–60, 108 × 85.7 cm, Haass/McMath gift 1953, formerly Metsu, Love Letter and Billet Doux. Walters Note, 37.676, is 32.39 × 29.85 cm; NGA Intruder is 66.6 × 59.4 cm; other Metsu compositions differ. Expanded former-creator/title searches do not identify the same object.',
110:'DIA Leoni Susanna, 41.89, circa 1620, 45.9 × 36 cm on copper, Chanler–Mondschein acquisition 1941. Former Saraceni and follower-of-Elsheimer attributions expanded discovery to 81 records without a Susanna/Suzanne match. The frame dimensions are inconsistent with the object dimensions; preserve the source wording without correction.',
111:'DIA Leys Luther in Eisenach, 56.281, 1859, 29.2 × 41.9 cm on panel, Scripps acquisition 1956. The eight-record creator pool contains other interiors and Charles V, not this Eisenach subject.',
112:'DIA Workshop of Lorenzo Veneziano Baptist Preaching, 25.204, circa 1370, 29.2 × 29.7 cm, Sperling acquisition 1925, formerly Giovanni da Bologna or Marco di Paolo. Veronese’s same-title composition is circa 1562; Giovanni di Paolo panels are circa 1454. Preserve the workshop label and separate earlier physical panel.',
113:'DIA Matteis Danaë, 79.140, circa 1705–15, 97 × 125.2 cm, Gruber acquisition 1979. The 26-record creator pool has no Danaë match; native inventory and provenance support a separate work.',
118:'DIA Master of Frankfurt Virgin Enthroned, 89.59, fifteenth century, 72.4 × 58.7 cm, Scripps gift 1889, was formerly Hugo van der Goes or Jan de Vos. NGA 1976.67.1, circa 1511–15, 73.5 × 57.5 cm, depicts Saint Anne, Virgin and Child, a different three-generation subject. Van der Goes Trinity and Death of the Virgin are different compositions. Preserve the literal fifteenth-century source date.'}

def build():
 x=m.load(CANDIDATES);identity=m.load(IDENTITY);citations=m.load(CITATIONS)
 assert x['complete_capture_count']==117 and len(x['rows'])==112 and not x['capture_incomplete']
 for dep in x['dependencies']+identity['dependencies']:checked(dep)
 assert identity['candidate_reference']==ref(CANDIDATES) and citations['identity_reference']==ref(IDENTITY)
 assert citations['selected_ids']==identity['state']['artwork_ids']
 assert f.i.params_for(x['rows'])==identity['params'] and f.i.comparisons(x['rows'],identity['state'])==identity['comparisons']
 assert set(NOTES).isdisjoint(HOLDS) and set(NOTES)|set(HOLDS)=={r['number'] for r in x['rows']}
 comparisons={c['source_id']:c for c in identity['comparisons']};out=[]
 for row in x['rows']:
  assert f.parse(checked(row['source_reference']))==row
  n=row['number'];c=comparisons[row['source_id']];v=row['facts']
  if n in HOLDS:out.append(dict(row,state='editorial_hold',basis=HOLDS[n],comparison=c));continue
  assert v['date_issue'] is None and v['first']<=v['last']<=1970 and v['inventory'] and v['credit_line']
  assert set(row['review_flags'])<={'index_detail_creator_difference','version_or_qualified_creator_review','multiple_source_creators_review'}
  assert not any(c[k] for k in ['native_scheme_hits','native_url_hits','source_hits','untitled_creator_hits'])
  relevant=[r['id'] for r in c['inventory_hits'] if r['relevant']]
  assert relevant==([HOLDINGS[n]] if n in HOLDINGS else [])
  out.append(dict(row,state='approved_existing_holding' if n in HOLDINGS else 'approved_review_only_addition',confidence=.98 if n in HOLDINGS else .90,basis=NOTES[n],comparison=c,limitation='Editorial confidence in documented object identity and collection connection, not a calibrated probability. Original source qualifications, dates, dimension inconsistencies, provenance and unknown rights are retained. Holding is not a current-display, physical-custody or legal-title assertion. New records stay in review; no image or artist-authority changes.'))
 assert sum(r['state']=='approved_review_only_addition' for r in out)==92
 assert sum(r['state']=='approved_existing_holding' for r in out)==2
 assert sum(r['state']=='editorial_hold' for r in out)==18
 return out

def main():
 paths=[p for p in RUN.glob('*.json*') if p.name!='editorial-reviewed-002.json.gz']
 evidence=[ref(p) for p in sorted(paths)]
 m.save(RUN/'editorial-reviewed-002.json.gz',dict(at=m.now(),decisions=build(),reviewer_reference=ref(Path(__file__).resolve()),supplement_references=evidence,uncaptured=[dict(number=5,source_id='54995',reason='Transport timeout; no complete object capture; no retry or addition.')],policy='92 individually reviewed additions, two exact existing-object holding reconciliations,18 captured holds and one uncaptured hold. All additions remain review. The count target is not evidence. Actual primary Judith image was compared for identity only, not attached.'))
 print(json.dumps(dict(new=92,existing_holdings=2,held_captured=18,held_uncaptured=1)),flush=True)
if __name__=='__main__':main()
