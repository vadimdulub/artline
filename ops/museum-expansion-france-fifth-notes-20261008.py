#!/usr/bin/env python3
"""Individual review decisions for current official source records; no quota overrides."""
HOLDS={
5:'Existing 583116fe-5cb5-4e0d-8c08-8e77e99d65b9 has the same maker and Dante et Virgile title but no physical details. Reconcile the copy identity before creating another record; conflicting creator birth dates remain source evidence.',
28:'Soft is dated 1961 in the headline but inscription is transcribed markbrusse 81. Resolve the creation/inscription discrepancy, including possible post-cutoff execution, before addition.',
29:'Degottex untitled drawing: existing same-maker Sans titre lacks physical metadata. Different unverified year alone does not settle identity.',
32:'Laubies untitled drawing: existing same-maker Sans titre lacks physical metadata; hold pending physical comparison.',
34:'Michaux untitled ink: existing 51c44f4b-de23-43ae-887d-79dc3e15041e and candidates 42/46 have overlapping dates and near-identical physical descriptions. Resolve versions.',
36:'Viseux Stimuli-signe du crabe: candidate 44 has the same title, month, medium and transposed dimensions. Different inventories alone do not settle two sheets versus duplicate notices.',
39:'Kijno Composition: two existing generic compositions lack physical metadata; unverified 1950/1957 dates alone do not clear candidate 1955.',
40:'Laubies untitled print: existing same-maker Sans titre has unknown physical form; reconcile before adding an impression.',
42:'Michaux untitled ink: see 34/46; same existing generic work and almost identical sheets require physical mapping.',
44:'Viseux Stimuli-signe du crabe: see 36, transposed dimensions and near-identical inscription leave duplicate notice possibility unresolved.',
45:'Bellegarde untitled lithograph: existing Italian generic Sans titre has no physical metadata. Edition and object mapping remain unresolved.',
46:'Michaux untitled ink: see 34/42; near-identical dimensions and generic existing title require reconciliation.',
49:'Viseux Multitude: existing Foule and Facies have similar dimensions and incompletely described media. Resolve composition/translated-title identity before addition.',
56:'Beaudin Le Calligraphe describes a book with lithographs, no dimensions or individual sheet identity. Do not turn an unclear bibliographic unit into an individual print.',
63:'Cazier no.4 empreintes and candidate 117 share exact inscription and near-identical dimensions. Two sheets versus duplicate cataloguing unresolved.',
66:'Deriennic generic sheet: existing Sans titre/Bouquet and other drawing lack physical details; source signature also spells Derriennic. Reconcile full identity.',
72:'Madge Gill generic ink sheet: existing 027df71d-e177-5d28-96f9-18a597eef263 has unknown creation date/physical details. Reconcile with candidates 72/122.',
74:'Hernandez generic oil-on-paper: two existing untitled works lack physical details and overlap broad creation period. Reconcile before adding.',
77:'Georgine Hu generic sheet shares dimensions, year and transcribed inscription with candidate 126. Distinct physical identity needs confirmation.',
84:'Le Bedeau crucifixion is signed Rene Coadou. Preserve both source names pending identity resolution; do not silently treat them as aliases.',
85:'Lesage generic drawing: existing same-maker untitled works lack physical metadata. Earlier headline date is insufficient to resolve identities.',
86:'Lonne generic drawing: existing same-maker untitled works lack physical metadata. Compare physical sheets before addition.',
92:'Modigliani sculpture-head study requires fuller version comparison against generic existing head studies; no automatic new-object assignment.',
93:'Pascin group of women requires fuller comparison with generic women sheets, including Deux femmes; no title-only clearance.',
101:'Tal Coat Sur le pas is described as a book with engravings and no physical dimensions. Book versus individual print unit unresolved.',
104:'Van Hecke Lanskoy portrait overlaps existing f56289b3-2ef4-444c-b3b9-bc25f9a9debc without physical details. Different unverified date does not settle identity.',
112:'Beaudin Bucoliques describes book illustration(s) without dimensions or sheet identity. Hold the physical unit.',
117:'Cazier generic sheet repeats candidate 63 inscription no.4 empreintes with nearly identical size. Resolve duplicate versus second object.',
122:'Madge Gill second generic ink sheet: same unresolved existing work as 72, no physical metadata to settle mapping.',
123:'Hernandez generic plywood painting: existing untitled works overlap before-1957 range and lack support/dimensions. Resolve mapping.',
126:'Georgine Hu banknote-face sheet: see 77; exact year, dimensions and inscription overlap generic companion notice.'
}
_TEXT='''
1|One Mongin etching after Bastien-Lepage, with paper dimensions and creator roles. The Melbourne painted prototype is not this physical print.
2|Small plaster study, 80 cm without base, is explicitly distinguished from the existing 190 cm full-size plaster and Paris marble. Before-1905 boundary retains unknown lower year.
3|One painted plaster Marianne bust, with Clesinger and Marnyhac marks. Existing same-title Hurtubise is another creator; no bronze medium inferred from the foundry inscription.
4|One Donzel watercolor forest sheet, signature at lower left with 17 Avril; candidate 13 uses ink and a lower-right signature. Same format does not erase those physical distinctions.
6|One lithograph on paper, 92 by 80 framed, after the Rouen Bastille oil. Existing 514 by 650 oil is the prototype, not this print.
7|One Galimard Sand portrait sheet with lower paper extension, not two artworks; other named sitter and nude studies differ.
8|One 1877 Jannin Republic bronze bust, 40 high, signed on base. Same-title paintings by other creators differ in physical form and maker.
9|One Lere painted copy after Pils, 75 by 93 unframed, with explicit copy inscription. Preserve copyist and model roles.
10|Anonymous seventeenth-century Catherine canvas, 63.5 by 78. Existing named-creator versions have different supports, sizes or periods; no attribution invented.
11|One Sainte Anne canvas, 62 by 79; retain uncertain Toussaint Charton suggestion. Existing Lefebvre square nineteenth-century canvas is different.
12|One signed 1907 Beguine shepherdess plaster, 66 high; existing same-title paintings/etching and other Beguine figures differ.
13|One Donzel forest watercolor with Chinese ink and lower-right signature; candidate 4 has lower-left dated signature and no ink in medium. Count one sheet per documented physical version.
14|One Galimard angel-round drawing with squaring for a mural, 36 by 16.5; mural design, not executed wall decoration.
15|One anonymous fifteenth-century stone Catherine statue, 50 high; distinct from candidate 10 canvas and existing same-title paintings.
16|One Beguine spinner plaster, 63 high; source Dalou comparison does not change authorship. Existing same-title works have different makers and physical media.
17|One Donzel river watercolor/ink, 23 by 14.5, with 27 Juillet inscription; existing generic 1888 river work needs no matching claim and documented period here is 1851–1875.
18|One signed 1864 Galimard cat drawing, 24 by 31. Source distinguishes an anonymous photograph at Orsay from the original sheet.
19|One fourteenth-century stone female statue, 53 high. Possible saint remains a qualified subject; no invented name.
20|One fourteenth-century stone bishop, 52.5 high; exact-title painted panels have other supports and periods.
21|One anonymous Magdalene canvas with reversed composition after Titian inspiration. Preserve anonymous status and distinguish existing Domenichino-related narrow canvas.
22|One anonymous moving male academy canvas, 47.5 by 72.5; existing Moreau drawings and Molin 76.8 by 63.8 canvas differ physically.
23|One anonymous flower canvas, 64.5 by 50, marked 130/20. Known-maker same-title records are not reassigned to this anonymous work.
24|One anonymous farmyard canvas, 73 by 54 unframed, with P.B and transport/framer stamps; source initials do not establish a creator authority.
25|One anonymous nineteenth-century Iphigenia canvas, 140 by 104.5. Existing same-title named works differ in period, dimensions or support; no prototype attribution invented.
26|One anonymous nineteenth-century Assumption canvas. Literal source centimetre values are retained despite apparent unit anomaly; no guessed conversion.
27|One 1966 Cabine chromatique four-colour lithograph, numbered 27/30, 70.6 by 50.5. Source description retains technique while missing structured medium remains unknown.
30|One 1958 Erro Radioactivity paper drawing, 35 by 25.3; Gudmundsson checked, existing American Interior is a different composition.
31|One signed 1954 crumpled-paper violinist study, 28.5 by 30.5; not Saint Jean/Assy study or generic later compositions.
33|One signed 1956 Magnelli felt-tip/graphite drawing mounted on canvas, 80 by 107.5; separate from smaller 1962 sheet 41.
35|One 1968 Rancillac screenprint, 73 by 53; existing Mickey, Israel and scarf compositions differ.
37|One white-on-white 1954 Bellegarde paper embossing, numbered 53/60, 44.5 by 62; not the later untitled coloured lithograph.
38|One Erro 1958 Only Auto Lite sheet with printed collage, 35 by 25.3; different composition and collage technique from Radioactivity 30.
41|One signed 1962 Magnelli felt-tip/graphite paper drawing, 65 by 50, mounted on paper; physically distinct from 1956 canvas-mounted 33.
43|One 1968 Rancillac Cuba screenprint on plexiglass/painted wood, numbered 3/3, 160.5 by 120.8; physical edition example counted once.
47|One Viseux Pagure 1955 graphite/copal-varnish drawing, 65.5 by 50; dated earlier and different technique from Foule/Facies.
48|One 1963 Bellegarde Stature lithograph, artist proof on BFK Rives, 69.3 by 56.6.
50|One 1964 Bellegarde Effigie seven-colour lithograph, 28/40, 50.2 by 65.9; not Bird I oil/collage or other named compositions.
51|One 1970 Bellegarde Couple six-colour lithograph, 51/60, 28.2 by 38.4; same-title Picasso prints have different makers, dates and techniques.
52|One 1959 Aloise/Corbaz oil-pastel Guisan sheet, 29.7 by 21, with transcribed title.
53|One signed 1953 Jacqueline B/Bartes sheet on watermarked Moirans paper, 24.1 by 31.4. Different support/year from companions 54/110; alternative surname spelling is preserved.
54|One signed 1955 Jacqueline B/Barthes cream-paper drawing, 25.4 by 30, including reverse sketch; both faces counted once.
55|One Johann B graphite Himalaya sheet, 14.9 by 10.4, title inscription. Creator remains the incomplete literal name without invented biography.
57|One circa-1947 Baya woman in orange and blue horse gouache sheet mounted on card, 74.7 by 91.6; existing 1966 bird/vase sheets are different compositions and sizes.
58|One 1963 Boix-Vives mountain-curate gouache, 65 by 49.7, signed/titled; not Dahu companion.
59|One Bonnelalbay August-1970 felt-tip drawing, 24 by 31.7; distinct date/orientation from March-1969 candidate 115.
60|One signed 8-January-1951 Burnat-Provins Varskhodel-chel drawing, 32.6 by 25; existing Ma Ville works depict other named beings and dates.
61|One signed Crepin heart cut from cardboard, 7.5 by 7.9, dated 1946; not Louis-Philippe Crepin marine paintings.
62|One 1925 Cueto Mikioito coloured-pencil study on squared paper, 31.5 by 22.5; paper design, not the sculpture.
64|One signed 12-April-1968 Genevieve Clement cow/two-calves sheet, 25.2 by 32.7; one sheet, not a record per animal.
65|One 1943 Darger Catherine Isles drawing, 34.5 by 42.5; existing storm work has a different named composition.
67|One circa-1928 Ducret dead-lake drawing with straw and spiderweb on paper, 37 by 52; not the larger village sheet 119.
68|One Gaston Dufour gouache with literal invented-word title, 27.6 by 35.5; before-1953 upper boundary, no invented lower year.
69|One Paul Engrand Camargue/La Vie coloured-pencil wrapping-paper sheet, 44 by 70; no link to Pierre Engrand ship painting.
70|One signed 1961 Godi first drawing, 32.5 by 25.3; paper mounted on grey card is one physical work.
71|One Ted Gordon signed 1969 ballpoint sheet, 12.7 by 7.7; different date, size and support from lined-paper 1970 sheet 121.
73|One 1948 Jeu policier wrapping-paper drawing, 84 by 97.3; preserve Henri de Beaumarchai label without resolving broad Henri-name matches into an authority.
75|One Hodinos/Menetrier Apprets ink miniature with eight medallion inscriptions, 6.9 by 5.9; count one sheet and retain before-1897 boundary.
76|One Margarethe Held Italy-elf pastel, 42 by 28, reverse number 278; source 1977 book gives title but does not replace 1950–1954 creation. Ireland companion 125 numbered 256.
78|One signed 1970 Iselstroger Ecce Homo drypoint with coloured pencil, 25 by 12.7; literal spelling preserved.
79|One signed 1929 Max Jacob lions/elephants charcoal sheet, 36.8 by 25.9, with Christmas dedication.
80|One large Jayet Bar vin lits coeurs drawing with extensive recto/verso inscriptions, 100 by 90.7; depicted/narrated historical dates do not narrow before-1949 source creation.
81|One Kopac 1948 ink-on-paper greeting to Andre Breton, 27 by 21; official print classification retained and greeting counted once.
82|One Lassiter front-facing-man gouache woodcut, 46 by 65, signed 1964 with 1-3 notation retained.
83|One 1928 Laurens polychrome terracotta relief, 93 by 131 by 4.5; source former instrument titles retained, existing 1916 musical-instrument paper collage is different.
87|One Justin MacCarthy Swaps gouache/ink sheet, 28 by 34.3, signed Jus McCarthy 1957; surname spelling preserved pending expanded comparison.
88|One Jean Marchand copper engraving reworked with gouache/graphite, 49.8 by 30; not other Marchand oil compositions.
89|One Max/Limberger graphite sheet dated 8-March-1961, 14.9 by 10.5; literal Rufolf spelling retained without biography repair.
90|One Albert Moindre six-point-star-in-circle gouache, 48.8 by 47; before-1957 boundary with unknown lower year.
91|One Monsiel graphite drawing on beige paper, 9.5 by 21; before-1962 boundary retained, no exact year invented.
94|One Perdrizet machine-design sheet, 50 by 65.1, dated 16-February-1970; drawing is not an executed machine record.
95|One signed 1970 Pous ballpoint/gouache drawing on printed corrugated card, 33 by 16.5; existing 39-square figures and 55-by-38 composition differ physically.
96|One 12-August-1938 Pujolle Star/Female-head mixed-media sheet, 31.7 by 24; uncertain pharmaceutical materials retained, existing Astronome/Sourie titles differ.
97|One signed 1970 Rundgrem people/animals painted sheet, 31.8 by 42; no replacement with another Nils artist or corrected surname.
98|One signed 1970 Rebeyrolle lithograph, 90 by 60.8; existing named paintings differ in physical type and subjects.
99|One Schopke Madame Miezi crayon sheet, 40 by 30, signed/detailed 12-December-1958; crossed-out age retained as inscription, not creation.
100|One 1921 Survage urban-landscape canvas, 73 by 92.2; former Houses title preserved; existing Nice/Lemon Tree works have other compositions and periods.
102|One signed 17-February-1967 Taveaux house/utensils sheet, 23.5 by 32.5; no creator birth dates invented.
103|One signed 1970 Ubac lithograph, 96 by 54; existing named oils and compositions require no identity conflation.
105|One Scottie Wilson/Freeman Face and headdress drawing, 36.5 by 25.5, before 1945; literal signature supports named physical sheet.
106|One signed 5-May-1967 Wittlich marching-soldiers gouache, 109.4 by 51.4; former and translated titles retained.
107|One signed/titled 18-March-1964 Yoakum Wrangell landscape, 30.6 by 45.7; literal geographical title retained without correcting the artist's geography.
108|One anonymous inventor's technical-art drawing dated 8-June-1915, 26.8 by 17.8; torn signature does not establish a named creator.
109|One 1958–1960 Aloise large drawing, 102.2 by 72.3. Grand-Hornu deposit is explicitly historical, ending 12-April-2010; no current-display or legal-title claim.
110|One signed 1957 Jacqueline B/Barthes sheet, 24 by 31.3, with reverse year. Different documented year from 1953 watermarked and 1955 reverse-sketch sheets.
111|One 1959 Johann B female-nude graphite sheet, 14.8 by 10.5; incomplete maker label preserved, distinct subject from Himalaya 55.
113|One circa-1947 Baya pink-dress woman gouache/graphite on card, 48 by 63; distinct subject/support/format from orange-dress/blue-horse candidate 57.
114|One signed Boix-Vives 1964 Dahu drawing, 80.5 by 27.4; tall card support and titled subject distinguish mountain curate 58.
115|One Bonnelalbay March-1969 person/vegetation felt-tip sheet, 31.6 by 24.3; signed TB, separate from August-1970 landscape-format companion 59.
116|One signed Cueto 1941 graphite drawing on brown paper, 33.2 by 23.7; separate from 1925 squared-paper sculpture study.
118|One signed 17-April-1968 Clement carnations sheet, 25.7 by 32.5; different subject and date from cow/two-calves sheet 64.
119|One signed Ducret village drawing with straw/paint/spiderweb, 46.4 by 59; distinct composition, size and coloured-pencil technique from lake sheet 67.
120|One Paul Engrand Authie valley sheet, 47.8 by 79.4, circa 1948; explicit title and different size distinguish Camargue wrapping-paper sheet.
121|One Ted Gordon signed 1970 ballpoint drawing on lined paper, 13.3 by 10.2; separate support/date from 1969 small sheet 71.
124|One Hodinos/Menetrier Chaux medallion ink sheet on wrapping paper, 5.6 by 7.9; different inscription/layout/support from Apprets 75, before-1897 boundary retained.
125|One Margarethe Held Ireland-elf pastel, 42 by 28, reverse number 256; counterpart Italy-elf sheet numbered 278 remains distinct. Book publication date is title provenance only.
'''
NOTES={int(line.split('|',1)[0]):line.split('|',1)[1] for line in _TEXT.strip().splitlines()}
QUALIFIED={}
INVENTORY_EXCEPTIONS={
166:{'4cee4428-f849-4c37-ae6b-8091d6dbd621'},
173:{'99b00824-f9ae-4189-a17d-4fbfb8f6f976'},
181:{'4cee4428-f849-4c37-ae6b-8091d6dbd621'}
}
HOLDS.update({
17:'Donzel river watercolor overlaps existing generic PAYSAGE, BORD DE RIVIERE without physical data. Different unverified year is insufficient to resolve the sheet.',
33:'Full Magnelli pool includes generic 1956 Composizione and Tentation mesuree without physical metadata. Reconcile drawing identity first.',
41:'Magnelli generic drawing has the same paper format as existing Composition and other generic abstract works have unknown media. Further physical comparison needed.',
100:'Survage urban landscape: full pool includes Composition cubiste circa 1919/1920 without physical metadata. Resolve possible alternate title before addition.',
127:'Headline creator is empty but author notes contain unattributed biographical dates. Do not infer an artist from those dates; fuller object/creator reconciliation required.',
139:'Di Maria/Reni-school Magdalene: existing Reni penitential Magdalene lacks physical metadata. Resolve school/original versions before addition.',
140:'Dughet Italian landscape: full maker pool contains generic landscapes and shepherd scenes without physical details. Qualified attribution and inventory alone do not settle physical mapping.',
145:'Le Nain card players overlap existing Petits joueurs de cartes without physical metadata. Preserve Mathieu attribution uncertainty and resolve versions.',
147:'Millet/old Grimaldi landscape has unresolved generic counterparts; headline/notes also disagree on creator death year. No authority or physical identity inferred.',
148:'Neeffs/Francken church interior: full pool contains unsized generic church interiors. Existing Granet and small panels differ, but remaining versions still need reconciliation.',
153:'Recco fish still life: expanded full pool contains generic fish works with unknown dimensions/support; no title/date-only new-object assignment.',
155:'Attributed Rosa Allegory of Laughter/mask composition may overlap existing allegoria della Menzogna without physical metadata. Resolve iconography and versions.',
156:'Rubens-school Nature adorned by Graces needs comparison with generic Three Graces object lacking physical details. Unrelated Samson inventory 351 is not a match.',
157:'Sahut headline 1947 accompanies transcribed signature SAHUT 17; resolve whether transcription/date discrepancy before selecting exact year.',
159:'Former Ribera Paul Hermit overlaps existing e736843c-593d-494e-a235-2ef785e1eb90 without physical detail. Reconcile the former and current attributed identities.',
160:'Stern flower vase and candidate 176 have near-identical sizes and generic composition. Distinct catalogue numbers alone do not establish two physical canvases.',
161:'Salome headline attributes Strozzi, former attribution also lists Strozzi, while author notes introduce Stroiffi. Preserve conflicting authority evidence pending clarification.',
164:'Vanvitelli Rome/San Giovanni view overlaps existing de9477a0 with the same site and unknown physical metadata. Signature year does not settle version mapping.',
170:'Anonymous Rosa-manner mountain landscape: several generic rocky landscapes lack physical data. Need fuller copy/version comparison.',
171:'Snyders follower bear panel headline says seventeenth century while reverse label says fin XVIII. Do not silently choose a creation century.',
176:'Second Stern flower vase notice: see 160, near-identical physical data leaves duplicate-versus-pendant identity unresolved.',
189:'Anonymous evangelist head bears old Guercino/Barbieri labels; generic head/saint version comparison remains incomplete. No creator promotion.',
191:'Anonymous Trinity ceiling work has conflicting design versus former ceiling-element descriptions and old Preti discussion. Resolve physical unit/version before addition.',
193:'Anonymous woman portrait bears Beham/BB labels. Generic sitter and former attribution need fuller identity comparison before addition.'
})
for n in HOLDS: NOTES.pop(n,None)
_MORE='''
128|One seventeenth-century Baugin temple-presentation canvas, 148.5 by 188.3; full maker pool contains other Marian scenes and different physical formats.
129|One attributed van Beest pipe-smoker oil panel, 23.1 by 19.7. Old Cuyp label retained and compared; same-title Barbey/Picasso works differ in period/support/size.
130|One attributed Bonito female portrait canvas, 44.2 by 34.6; existing same-maker female portraits are 69 by 55, other named scenes differ.
131|One attributed Busti/Bambaia marble woman-and-child statuette, 66 high; Virgin versus Andromache subject remains explicitly unresolved.
132|One attributed Cellony unknown-woman canvas, 72.2 by 69.5; sitter remains unknown and no artist authority is created.
133|One attributed Cerquozzi bird-nesters canvas, 153.5 by 153.3, with fruit, marsh and children. Full pool smaller still lifes and battles are distinct compositions.
134|One signed 1819 Louis Mathurin Clerian Pont de l'Arc drawing, 15.5 by 23.2; no confusion with Noel Clerian Roi Rene oil.
135|One 1820 Noel Clerian harp-knight watercolor with dedication to Leontine de Parade, 12.4 by 9.8 mounted; not the larger 1826 Roi Rene oil.
136|One attributed Compagno bishop-baptism oil on copper, 25 by 33. Former Napoletano label preserved in inscriptions and added to comparison, not promoted to current maker.
137|One attributed Cozza Baptist canvas, 72 by 61; full maker pool contains other saints and narratives, not this single Baptist.
138|One before-1731 Dandre-Bardon battle sketch, 66.5 by 43.7, for one of nine town-hall paintings; count the sketch, not all nine paintings.
141|One attributed Fauchier copper portrait, 25.5 by 21.3; sitter remains presumed Forbin Rascas, crossed-out Grignan label retained. Other Fauchier works are different subjects/supports.
142|One 1957 Fraggi paper study, 27.8 by 40.5, for the existing 89-by-116 canvas panorama. Historical Alain Fraggi ownership label retained alongside current museum acquisition evidence.
143|One attributed Johannes Hermans game/fruit/vegetable canvas, 49 by 65. Charles Hermans works are another maker; qualified attribution retained.
144|One 1935 Gabriel Laurin reading-young-man charcoal/pastel sheet, 32.2 by 25.2; existing draughts/dice canvases have different compositions and supports.
146|One attributed Le Sueur Martha/Mary canvas, 76.7 by 57.5; existing same-title 225-by-121 canvas is physically different, qualification retained.
149|One attributed Nunez del Valle Cecilia-martyrdom canvas, 141 by 101; preserve cancelled old inventory and distinguish other Nunez creators.
150|One attributed Pace/Campidoglio fruit canvas, 71.2 by 95.5; full matching-maker pool contains a 64-by-55.5 fruit canvas, a different format.
151|One attributed Preti 1660 oval Magdalene canvas, 128.3 by 96. Full maker pool checked; no corresponding Magdalene composition found.
152|One attributed Puget Marcus Aurelius terracotta bust, 18 high, with separate base measurements. Base is not a second artwork.
154|One attributed Rimpatta Virgin/Child panel, 76.5 by 50.4, with two attendant women. Uncertain artist lifespan remains source evidence, not a rewritten creation date.
158|One attributed Simonelli/Giordano-workshop Helen-abduction canvas, 128.7 by 156; existing Giordano 139-by-249 oil and small ink drawing differ physically. Both source qualifications retained.
162|One 1946 Tal Coat left-facing rooster ink sheet, 74 by 58, signed lower right; counterpart 177 faces right and has white highlights/lower-left signature.
163|One attributed Traversi monk-portrait study, 38.5 by 28; existing 135-by-101 Berti portrait is a separate full-size work.
165|One attributed Veyrier Sabine-abduction unbaked-clay group, 38 high; all figures and horse constitute one statuette.
166|One anonymous mule-miracle canvas, 134.5 by 96; Scarsella same-title work is smaller on different support. Shared old number 335 belongs to a different inventory series than Hackaert landscape, whose subject/format differ.
167|One anonymous Le Brun-after Good Samaritan canvas, 49.5 by 65; kneeling healer and wounded man describe the copy. Expanded Le Brun/Lebrun comparison found no corresponding physical object.
168|One anonymous workshop copy after Lione, 130.8 by 160.6, Tobias burying the dead. Source explicitly distinguishes Met prototype; former Bourdon/Poussin labels checked. Existing Bourdon burial prints differ physically.
169|One anonymous Manfredi-after card-player canvas, 96 by 115.5; old Valentin label retained and compared. Existing Valentin Soldiers Playing Cards and Dice is 121 by 152; no autograph assignment.
172|One attributed Bonito child-with-rattle canvas, 82.3 by 68, with red cushion/white embroidered dress. Other full-pool child/narrative subjects differ; sitter remains unnamed.
173|One before-1731 Dandre-Bardon Provence/Aix allegorical sketch, 66 by 43.2, distinct subject from 138 battle. Shared old 30 is from Gibert 1862, not Martellange Gibert 1867 Virgin panel.
174|One attributed Puget King David terracotta bust with marble base, 28.5 high overall; base included in one object. Full pool has no corresponding David bust.
175|One signed 1947 Sahut Milles plain/Pilon du roi ink drawing, 44.5 by 56, source number 1055; companion landscapes have different documented sites/inscriptions.
177|One 1946 Tal Coat right-facing rooster sheet with white highlights, 74 by 58, signed lower left. Distinct posture and technique from left-facing 162 despite same format.
178|One attributed Traversi mandolin player canvas, 72.6 by 60.7, with dancing man behind; existing concert is 95.5 by 131 and other scenes differ.
179|One anonymous 1630 Salome canvas, 101.7 by 157.5, with turbaned witness behind bars. Former Caravaggio attribution retained as historical; existing 91.5-by-106.7 Caravaggio composition and portrait-format Strozzi candidate 161 differ.
180|One Sahut 1947 Cabanon ink drawing, 45.3 by 56.3, with roof sketch verso; count both faces once.
181|One anonymous apotheosis sketch canvas, 48.5 by 38.3. Old white-label 277 is distinct from Hackaert landscape's Pontier number; subject and dimensions differ.
182|One signed/titled 1947 Sahut Lentaume dovecote drawing, 45.2 by 56, with reverse date and number 1002.
183|One anonymous sixteenth-century gallant-meal painting, 91 by 133.8; transferred canvas on later support is one work, support alterations retained.
184|One Sahut Campagne d'Aix 1947 sheet mounted on card, 45.2 by 56.3, source number 1000; not a second object for the mount.
185|One anonymous late-sixteenth-century Venus/Graces oil panel, 130.7 by 100.5; different period, subject wording and physical format from Rubens-school Nature panel 156.
186|One Sahut 1947 Galice-plateau almond-trees sheet, 45.5 by 56.4, number 1050, explicitly titled on both faces.
187|One anonymous late-seventeenth-century fortune-teller copper painting, 30.8 by 20.7, marked G411; known-maker same-title canvases do not establish this copper's authorship.
188|One Sahut 1947 Milles tomato-plants sheet, 45.4 by 56.2, number 1044 and reverse title/date.
190|One Sahut 1947 Grande Bastide ink sheet, 45.5 by 56.2, including roof/chimney sketch verso; one two-sided object.
192|One Sahut 1947 Placette des Milles drawing, 45.2 by 56.3, number 1041; distinct explicitly named view.
194|One Sahut 1947 Campagne d'Aix/Val Chantant view, 45.5 by 56.3, number 1036; distinguish generic companion 184 by specific reverse site and documented number.
195|One anonymous sixteenth-century alabaster Virgin/Child, 49.5 high, with iron mounting pin; not attributed Busti marble candidate 131.
196|One Sahut 1947 Galice plateau/Eguilles view, 45.5 by 56.3, number 1035; different named view from almond-trees 186.
197|One anonymous seventeenth-century Henri IV bust assembled from two measured components. One overall bust, 66 high; uncertain terracotta and wax/straw materials retained, not two new objects.
198|One Sahut 1947 Lentaume-house/Arc-valley sheet, 45.2 by 56.2, with brown-charcoal trees verso; both faces one physical object.
199|One Sahut 1947 village from Val Chantant view, 45.2 by 56.2, number 1033; not the house or mill companion sheets.
200|One Sahut 1947 Galice mill opposite Val Chantant, 45.4 by 56.3, number 1032 and reverse title; one paper work.
201|One Sahut 1947 Grand Pin brown-wash drawing, 45.1 by 56.1. Secondary source number 1021 conflicts with inscription 1027; primary museum inventory 2021.2.16 and distinctive titled medium retained, neither secondary value corrected.
202|One signed 1925 Baschet Foch pastel on paper, 57 by 42, with London-1927 exhibition label. Full Baschet pool has no Foch counterpart. Literal old Depot 4368 identifier retained; exact current museum code/name and source Paris support collection link while empty database city stays unknown.
'''
NOTES.update({int(line.split('|',1)[0]):line.split('|',1)[1] for line in _MORE.strip().splitlines()})
