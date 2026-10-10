#!/usr/bin/env python3
"""Individual source/object review; uncertainty is retained, never filled to reach a quota."""
HOLDS={
3:'Barye lion bronze: existing 7d3a0f83-eac2-4624-a77d-0bc06b6bfab1 has the same title but no physical metadata; casting/version identity unresolved.',
8:'Cabirol maquette: history qualifies both attribution and 1784 with a question mark, unlike the headline date. Former Deschamp attribution checked; retain evidence pending qualified date reconciliation.',
13:'Debucourt third-state print: existing NGA and AIC impressions have closely matching plate/sheet dimensions. An accession alone does not distinguish this impression; provenance/version reconciliation needed.',
15:'Rivoli cup: existing Sevres L608 has a closely matching form and dimensions; painter/decorative composition and physical cup identity require confirmation.',
18:'Delorme nude drawing: same-maker Untitled fb760e8f-6c02-52a3-a96d-61f210978a01 lacks physical details. Title similarity alone cannot clear that version.',
19:'Dupas studies: existing Femme en buste 3b1a2b92-e687-4515-b439-e302efbd5727 lacks medium/dimensions. Confirm whether this sheet or a related study.',
23:'Bastille-taking plate: event in title is 1789 but creation period is third quarter eighteenth century (1751–1775). Do not invent a corrected creation date.',
27:'Expanded Fischetti/Gioffredo search found two generic dipinto entries without physical details; identify their works before creating the panel/ceiling drawing.',
30:'Kinsburger jewellery sheet: author field says Sylvain, but history explicitly suggests a relative instead. Maker identity remains unresolved.',
47:'Existing 649eee53-5326-47c4-8c80-3448489c3bd2 already has the same Niel print and Bx E 954 inventory. Reconcile collection context rather than create another object.',
61:'Headline 1791 and inscription read as 1791 or 1781 conflict. Preserve the source but hold pending qualified creation-date reconciliation.',
57:'Giordano workshop Seneca: same-title existing 3b87864f-b6db-4750-bb4c-19d063d4f88a lacks physical details. Workshop/original version unresolved.',
108:'Bernier: existing d4f3b54d-c197-405a-b699-f704f52508ef has this title but no physical detail; candidate 122 has the same headline and a different size/subject. Reconcile the two native canvases to that existing identity.',
122:'Bernier: same existing identity as candidate 108; this 78 by 110 canvas describes cows despite horse in title. Preserve contradiction pending reconciliation.',
154:'Darcy plan: headline creation 1869 conflicts with signed 18 March 1870. Both eligible, but no silent exact-year choice.',
162:'Hardouin Vilaine study: existing 8243086a-e036-40c1-a3fd-c7bd21604f51 and candidate 184 share title/date; two physical labels P.47/P.48 need reconciliation to existing record.',
170:'Simon drawing: author is Ernest Simon but transcribed signature says Ernest Landais. Expanded Landais check does not resolve the literal source contradiction.',
172:'Tancrede Abraham landscape: candidate 190 is another similarly sized watercolor with generic title; confirm two physical sheets rather than rely on SN versus accession.',
179:'Dehuz elevation record names two inventories 1910/1911 and two dimensions. Physical assembly versus two independent sheets unresolved; do not count as one new object.',
184:'Hardouin Vilaine study P.48: see candidate 162 and existing 8243086a-e036-40c1-a3fd-c7bd21604f51; unresolved duplicate mapping.',
190:'Tancrede Abraham landscape: compare candidate 172 before adding either near-sized generic watercolor; existing 1879 large oil is separately distinguishable.',
192:'Babey flower canvas: existing c6ba2ec2-f2c8-48cf-a605-101410b5cc5b has same title/1858; another generic nineteenth-century version exists and candidate 220 is a second native canvas. Resolve identities first.',
199:'Attributed David warrior-head study needs comparison with generic David heads and studies in the large creator pool; no automatic autograph or new object assignment.',
203:'Attributed Girodet Greek warrior needs fuller comparison with existing wounded/hero studies and versions; qualified attribution preserved in research.',
206:'Joberti male pendant: creation says circa 1851 but partly hidden signature transcribed 189(...). Retain conflict; do not substitute date from its pendant.',
212:'Roth Moneteau: existing 7b587afc-6ca5-4581-bd01-c15adb73a8f7 lacks physical metadata; candidates 212/226 have nearly identical dimensions and same scene. Reconcile before new records.',
216:'Anonymous Holy Family after Correggio: uncertain prototype and broad title leave copy/version comparisons unresolved; keep all source qualifications.',
217:'Anonymous copy after Rembrandt: existing same-title 2424bbcf-065a-4d2e-81f2-328785141052 lacks physical metadata; verify its original/copy identity first.',
220:'Second Babey 1858 flower canvas: same unresolved existing candidates as 192. Inventory and small dimension differences alone are insufficient.',
224:'Repeated Le Reve service plate, nearly identical to candidate 202; inspect individual physical examples before counting additional same-design objects.',
226:'Second Roth Moneteau canvas: unresolved mapping to same existing record as candidate 212.',
228:'Repeated Renee deep plate with identical dimensions/description to 219; physical duplicate/individual-service-piece check outstanding.',
230:'Bonvalot plaster: candidate 240 duplicates title, date, dimensions and inscription including incorrect old inventory note. Two casts versus duplicate notices unresolved.',
231:'Repeated Le Reve service plate: distinguish physical object from candidates 202/224/236 before addition.',
232:'Anonymous generic male portrait: maker unknown and no distinctive sitter identification; broader portrait identity research needed.',
233:'Repeated Renee deep plate: same dimensions/description as 219/228/238; physical identity not established independently.',
236:'Repeated Le Reve service plate: near-identical object description to 202/224/231, hold pending individual-object confirmation.',
238:'Repeated Renee deep plate: same dimensions/description as 219/228/233; hold pending physical identity check.',
240:'Second Bonvalot plaster notice: black tint alone does not settle duplicate versus second cast with otherwise identical record 230.'
}
# Notes below were written after reading the full current source fields and identity comparisons.
_TEXT='''
1|One signed 1778 Boyer terracotta bust, including base dimensions; Masse dit Martin signature evidence retained while the empty headline creator remains unknown. Expanded maker names find no matching Boyer object.
2|One Rouargue/Bordes print of the former Chartrons mill, 17 by 21; no matching scene in the scoped comparison.
4|Four kiosk designs occupy one 47 by 34 sheet; count the physical sheet once.
5|Two pavilion elevations on one sheet. Preserve source alternative attribution to Julien Belloir or the Belloir & Vazelle house.
6|Paper design for vase 82.3.7, not the ceramic itself; 31.5 by 22.5 drawing and independent inventory distinguish the physical work.
7|Saige pastel on cardboard, 66 by 53. Source author notes explicitly say attributed; that qualification is added to the display label with literal evidence retained.
9|One red-and-gold ceramic plate, diameter 23.5, attributed Caranza design and Vieillard workshop context. General workshop dates are not substituted for source creation 1878.
10|Octagonal plate design is a 23.7 by 23.9 paper drawing. Old Sevres deposit number is explicitly a historical error; current communal purchase label retained. Caranza attribution qualified.
11|One 1900 vault-study drawing, separate from other numbered companion sheets.
12|One 1942 Buthaud portrait on paper, 52 by 45; existing Charazac girl/boat paintings are different compositions.
14|One signed 1789 Saige marble bust, 71 by 54 by 30, not the pastel portrait in candidate 7.
16|Klipsch pastel on cardboard, signed 1843; existing generic male Dagoty portrait is dated 1815 and named miniature sitters differ. Full 33-record maker pool inspected.
17|Ducos pastel, 1839, 27.8 by 24.3; adult named sitter differs from children, women, 1815 male portrait and other named miniatures in full Dagoty pool.
20|One small bowl from a four-piece service; count bowl only, not the whole service. ROBJ manufacturer comparison added; no maker authority created.
21|One 1773 Rohan facade drawing, 26.5 by 114 with attached annotations; architectural project is distinct from broad Etienne given-name matches.
22|One Choisy plate depicting the Duc de Bordeaux and Louise in Scottish dress, diameter 22.2; manufacturer identity remains an object label.
24|One Moustiers grotesque-decor plate, diameter 25.4, OL/Icard marks. Expanded Olerys/Laugier/Icard names find no ceramic counterpart.
25|One Quinsac plate, diameter 24.8, among separately inventoried service pieces; count only this scene and vessel.
26|One Roman military-camp scenography sheet, not all six companion designs. Source presents Galliari or Basoli as alternative attributions, retained explicitly.
28|One 1864 museum/villa architecture watercolor, 51 by 60.3; J. Grimaldi remains a source label without invented architect biography.
29|One round floral Guillibaud workshop dish, diameter 48. Same-surname painted female portrait is a different maker/object type.
31|One caricature sheet with the Foire du Trone composition; depicted 1873 political events do not replace the source's broader creation period.
32|One third-state Comparison aquatint, 45.7 by 34.3. Full Janinet/Lavreince/Lafrensen pool contains other compositions; roles and state remain in citation.
33|One trompe-l'oeil almond plate, 25.8 diameter. Veuve Perrin attribution is uncertain and the catalogue proposes Honore Savy; both retained as alternatives, not confirmed makers.
34|One purple Turc plate with horse and two men, 23.2 diameter; after Pierre Lacour's drawing, manufactured by Johnston. Not candidate 42 fisher dish.
35|One Simone Larrieu geometric ball vase, 13.7 high and 14 diameter; single vessel.
36|One 33 cm dish from Tapisserie no.3, not the whole service; maker search separates the Johnston factory from unrelated individual artists.
37|One seventeenth-century Ming porcelain vase, 45 high; companion 4848 is a separate inventory and is not included.
38|One yellow vine-leaf dessert plate by Lahens/Rateau, 20.5 diameter; factory comparison added, no person authority inferred.
39|One large 1738 Bordeaux-port drawing with a lower Place Royale vignette. Source explicitly distinguishes the smaller 1737 drawing sold in 2014; count the one sheet.
40|One Marseille Chinese-garden plate, diameter 22.5. Place/workshop label retained without linking to the person Marseille Pierre.
41|One Bonie-armory dome design, 1892, 53 by 38.8; Leon Millet/Augier identity is distinct from the many unrelated Millet creators.
42|One 37 cm Turc dish depicting fishermen; distinct subject and format from candidate 34 horse plate. Lacour model is evidence, not a new artist assignment.
43|One Chinese-inspired turquoise Vieillard vase with its composite presentoir, 43 high; no equivalent vessel in expanded maker pool.
44|One paper design for the Fox Gourmand dessert plate, 16.7 by 16.8; other animal-design inventories not included and drawing is not a ceramic plate.
45|One Eventails service plate, diameter 23.5 with JVB marks; current object distinct from other designs and the source service name is not counted as a set.
46|One Nevers bottle, 18 by 10; related bottle 3314 is a separate work and excluded here.
48|One ornamental-vase drawing, not a silver vessel. Pierre Paraud or Francois Joseph Paraud are alternatives in source notes, retained as such.
49|One La Charte figure panel drawing, 38.5 by 21; source Charles Percier and circle qualification retained. Existing Metereau-after-Percier oil frieze differs in medium, format and composition.
50|One 1898 rue Duffour-Dubergier watercolor; Artus/Lauriol surnames added to comparison. Existing Gustave Artus garden oil is different. Literal duplicate Largeur dimension labels retained.
51|One 60 cm marble Spring, supported by 1881 purchase/exhibition detail; same-title Rodin objects and paintings have different makers/formats.
52|One circa-1770 Bacchus drawing; existing Boichot Saint Martin oil is a different medium and subject.
53|One paper poultry composition, watercolor and oil, 32.8 by 49.5; existing small poultry oils differ in support and dimensions.
54|One 1806 Return from Austerlitz etching, 8.2 by 10.7. Full Denon pool inspected; no corresponding print or impression found.
55|One 1786 Emmaus etching after Guercino, 19.7 by 26. Guercino/Barbieri aliases included; model maker explicitly marked after, not joint autograph authorship.
56|One two-lions-and-lioness etching after Quadal, 30.5 by 41.4. Preserve before-1803 creation with unknown lower bound; dealer's 1787 annotation not promoted to exact year.
58|One 1824 Chalon watercolor, 28.3 by 37.7. Existing 1837 large oil and 1843 oil view differ physically and chronologically.
59|One Cupid/VD monogram sheet, 14.8 by 15.7. Main creator stays anonymous despite Denon biographical note; Denon identity pool checked without promoting attribution.
60|One framed Lycurgus drawing circa 1785, 59.5 by 82.5. Compound acquisition numbering is retained; no count per depicted figure.
62|One St Paul window design on paper, 30.3 by 20.8; not the executed stained glass.
63|One 1794 Bonnet Rouge committee drawing, 22.5 by 33.5, with nine men on one sheet. Other Denon revolutionary figure studies have distinct subjects and dimensions.
64|One St Stephen window design, 30.3 by 20, distinct from the St Paul sheet 62.
65|One 1817 Theodore St Claire drawing for Monk Lewis, 11.1 by 17; older generic singer/guitarist title retained in source. No corresponding subject in full Denon pool.
66|One mountain footbridge watercolor, 13.6 by 21.5; G. Carpenter annotation retained without creating another author. Separate from signed 1849 candidate 68.
67|One print with Brunet and Lasteyrie, 17.1 by 19.3; two sitters on one object. Drawn-1816 annotation does not narrow broad source creation automatically.
68|One signed 1849 Raffort mountain bridge watercolor, 14.3 by 21; Carpenter annotation retained. Distinct physical sheet from 66 by support evidence, inscription and dimensions.
69|One 1784 Misses Merry etching, 13.6 by 15.2 sheet; named sitters and circular image differ from other Denon portraits.
70|One Gergy Christ-on-Olives choir design on paper, 61 by 47, dated 1866; not the executed church mural.
71|One presumed Emma Hart praying drawing, circa 1791, 10.8 by 6.5; subject identification stays presumed. Different from Emma holding a cup in candidate 75.
72|One 1777 St Laurent bridge drawing, 28.4 by 35.6; documented architectural scene differs from Denon's generic Italian rural landscapes.
73|Tanucci front-view black-chalk portrait, 12.8 by 11.8; different pose and sheet from profile candidate 74.
74|Tanucci profile black-chalk portrait, 12.6 by 11.7; paired subject does not merge it with front-view candidate 73.
75|Emma Hart holding a cup, pen/wash sheet 14.3 by 11; separate pose/format from praying Emma candidate 71.
76|Young girl in left profile, black chalk 16.8 by 11.9; not the Denon frontal head/shoulders drawing or large lithographic bust.
77|Helmeted ghost holding a candle, one 18.3 by 13.2 sheet; no matching composition in Denon pool.
78|Galvani frog experiment, one pen/wash sheet 21.1 by 16.6; different from small human-headed frog 79.
79|Human-headed frog, one pen/wash sheet 9.7 by 11.1, not the full Galvani experiment 78.
80|Three female bust studies on one sheet, 11.4 by 14.9; count physical sheet once.
81|Flying Cupid seen from behind on a small 5.9 by 5.1 sheet; not anonymous VD-monogram composition 59.
82|Pulpit and elephants recto, people/child head verso, on one 21.7 by 17 sheet; one physical object across both faces.
83|Fortune drawing on tracing paper, 19.3 by 13.6; same-title Merson work is a different maker and date.
84|Burlesque man and flute recto, snake/rat verso, one 17.2 by 12.3 sheet; both faces counted once.
85|Sarcophagus and two birds share one 18.5 by 17.3 sheet; not three separate objects.
86|Two chameleons share one 23.7 by 19.7 blue-paper sheet; one record.
87|Seated dog, black chalk on wove paper, 8.3 by 10.7; distinct posture and dimensions from adjacent dog studies.
88|Lying dog in black chalk on wove paper, 7.2 by 10; different medium/size from pen-and-ink lying dog 93.
89|Two panthers on one laid-paper chalk sheet, 6.9 by 9.5.
90|Dog on rocks, pen/chalk on laid paper, 5.7 by 9.6; distinctive support/scene separates adjacent studies.
91|Two playing dogs on orange paper, 6.2 by 11.4; one sheet, different support and action from other dogs.
92|Human body with dog's head/tail, pen/chalk 8.5 by 5.5; not a naturalistic dog study.
93|Lying dog, pen/brown ink/chalk, 5.9 by 7.3; smaller and different technique from 88, with separate inventory.
94|Three lying-cat studies on one 9.8 by 14 sheet, counted once.
95|One lying cat in black chalk, 8.5 by 12.5; separate sheet from three-study composition 94.
96|Antique profile, 8.9 by 10.6 chalk sheet; same-title Cocteau ink is later and another maker.
97|Ornamental vase study, 10.7 by 8.3, qualification in title retained; paper drawing, not a vase object.
98|Architectural tower section on one 23.2 by 14.3 sheet; not an architectural structure record.
99|Curule-seat drawing, 8.4 by 8.1; paper object, not furniture.
100|Antique toiletries drawing, 17.9 by 11; depicted objects remain one sheet.
101|Modern vase/bacchanalia drawing in sanguine, 20.2 by 15.2; distinct from smaller ornamental-vase chalk sheet 97.
102|One Marie Elisabeth Bourbon-Parma etching, 12.6 by 10.4; before-1803 boundary retained without fabricated lower year.
103|One Vigee-Lebrun etched portrait, 24.5 by 17.5, remounted proof; before-1793 boundary retained, mount not counted separately.
104|One Breton pipesmoker faience dish; source dimensions absent and remain unknown, no invented maker.
105|One Alfred Beau Neptune plate dated 1880, diameter 23. Bequest 1947 is provenance, not creation; Pajou marble is a different object.
106|One 1893 Le Bain ceramic dish, 53 by 40 by 5; exact-title paintings by other makers differ in medium and creation.
107|One Beau/Porquier boat-and-sails dish, 33 by 19; source 29-piece bequest does not turn this object into 29 additions.
109|One Creston-model/Henriot pigkeeper dish, 1925–1930, diameter 30.7; existing Creston oils are separate works.
110|One attributed Caussy Locmaria rector basin dated 1773, diameter 26.5; absent ewer is not added. Existing pagoda-decor dish differs in subject/size.
111|One Brittany-arms/three-angels dish, diameter 43, after Dargent's model. Unmarked Porquier-Beau origin is explicitly qualified as an attribution; related drawing 990.81.5 remains a different object.
112|One 1906 blind-beggar plate, 23.5 diameter. Decorator signature is read uncertainly as G. Fely(?) / Felix(?); derived label retains that uncertainty and named factory role.
113|One Henriot Flower Seller plate, 1904–1922; absent dimensions remain unknown, exact-title Ziem oils differ in maker/medium.
114|One Houel/HB Voice of Brooms dish, 1925–1930, diameter 29.3. Different maker identity from older Houel landscape oils.
115|One Houel/HB tavern dish with two men and servant, diameter 29.7; series context not counted as multiple works.
116|One Meheut-model/Henriot geometric cachepot, circa 1920, 16 by 15.7; ceramic distinct from Meheut oils.
117|One 1860–1870 dragon/saint dish, diameter 38; Saint George or Michael identification remains uncertain as supplied.
118|One 1896 Bigouden woman-and-girl porcelain plate, diameter 23; question-mark factory attribution retained. Lalaisse motif does not establish autograph creator.
119|One Recouvrance Brest plate, circa 1890, diameter 23.3; PB mark and two-women/chicken-market scene identify this vessel.
120|One Vieillard Ploudaniel costume plate, circa 1860, diameter 20.3; Lalaisse engraving is prototype evidence, not the same physical object.
121|One eighteenth-century dragon plate, diameter 25; unknown maker remains unknown and no source detail invented.
123|One Union Regionaliste Bretonne plate, 1910–1920, diameter 23.5 with heraldic decoration.
124|One Bigouden-au-lard plate, diameter 23, glazed terracotta; separate inscribed scene from Yancoz 128.
125|One Breton wedding dish, diameter 48; historical staged museum display is model provenance, not a claim this object is currently on view.
126|One grid-decor plate with central blue circle and grid half-circles, 22.2 by 2.8; different from red-flower deep plate 130.
127|One 1917 Honour/Patrie plate, diameter 25; fifteen decorative medallions are on one vessel.
128|One Yancoz glazed-terracotta plate, diameter 23; inscription/composition distinguish candidate 124 of similar form.
129|One Aria plate, 1875–1898, diameter 24.7, musical score/flower cartouches; no matching object in manufacturer pool.
130|One deep grid-decor plate, diameter 22 and height 3.5, red central flower/blue heart; distinct vessel and decoration from 126.
131|One 1917 Jeu de l'Or plate with shells and coin-headed figures, 24.8 diameter; Gassler inscription retained.
132|One Douarnenez plate circa 1890, diameter 25.8, fisherman/child after Lalaisse; existing Bouchor town oil differs in physical type and composition.
133|One 1791 Mirabeau commemorative dish, 25 diameter and 7.7 high; date explicitly inscribed, consistent with subject.
134|One 1917 Nous marchons plate, 24.9 diameter, women bearing allied flags; distinct patriotic design.
135|One Bannalec plate circa 1890, diameter 23.3, woman feeding pigs; source Lalaisse model reference is preserved.
136|One eighteenth-century fantastic-bird/fence plate, diameter 23, R mark; old inventories remain aliases of one physical vessel.
137|One 1917 Donnez votre or plate with purses and inscription, diameter 23.7; not the shell/coin game plate 131.
138|One Quimerc'h tavern dish, diameter 30, three men and serving woman; distinct from Houel tavern candidate 115 in maker, scene and period.
139|One Breton couple plate, diameter 25.5 and height 2.3; existing Belay 1928 wooden oil is a different work.
140|One 1917 Verdun plate with soldier, cock and floral/medal motifs, diameter 24; one object in patriotic group.
141|One Tancrede Abraham Montreuil-Bellay watercolor, 24.5 by 35. Existing same-maker landscapes are oils or other sites, no matching castle sheet.
142|One Alanic January-1828 Madeleine plan, 71.5 by 77.5 with watercolor; distinct dimensions/technique from 173 grey/blue wash plan.
143|One Allain 1926 rue de Paris watercolor, signed and dated, 26 by 34.5; no maker/title counterpart.
144|One Aubree 1853 Notre Dame drawing on beige paper, 34.5 by 22, signed/titled; not later castle drawing 174.
145|One Audroing 1890 college door/window architectural drawing, 49 by 60; depicted multiple details remain one sheet.
146|One Georges Aumont 1867 park plan on tracing paper mounted on canvas, 60 by 55; Louis Aumont portraits are another maker and subject.
147|One signed Bayard 1801 terracotta Virgin/Child statue, 135 high; existing Bayard illustrations and other-maker Virgins differ. No link to Emile Bayard inferred.
148|One Bazire 1894 Rennes-forest watercolor, 50 by 35; no matching identity.
149|One Bazire 1905 copy of Huguet's 1742 Grapinian drawing. The original deposit was retrieved; source explicitly distinguishes the museum's replacement copy and its creation year.
150|One Belay 1942 Saint Just gouache on paper, 37 by 52; same-place oils differ in support, size and composition.
151|One Busnel 1876 rue Poterie ink drawing, 20.5 by 14.5; separate from horizontal market-place drawing 177.
152|One signed Cardini 1877 marine oil on wood, 19 by 40. Same-name eighteenth-century allegorical prints and exact-title marines by other makers are different works.
153|One Choleau Plaguer chapel ink drawing, 15.8 by 18; before-1905 boundary remains exclusive with unknown lower bound.
155|One Raoul David Roche aux Fees pencil drawing on grey paper, 27 by 43. Existing same-maker local views are oils of other sites; before-1932 bound retained.
156|One Dehuz east elevation of Vitre castle on mounted paper, 55 by 41.4. Before-1738 boundary preserved; distinct from held two-inventory southern-elevation record 179.
157|One Jean Louis Treton portrait, 15 by 10.5 image; G. Dupuis question mark retained and no authority assignment.
158|One signed Fielding 1866 shipwreck oil, 70.5 by 130. Exact-title works have other makers, supports/sizes or dates; unspecified Fielding not expanded to a named artist.
159|One Leon Gaucherel 1843 castle/town gate wash drawing, 25.5 by 37.5; lithographic reproduction is another work and not imported here.
160|One Gautier 1772 sanguine counterproof, inventory 1883; source explicitly distinguishes original drawing 1882. Existing Lalanne etchings and Lottier oil are different media/periods.
161|One E. Gontier drawing of Guy III/Louise tomb, 46 by 28.4; 1553 is an inscription on depicted tomb, not creation. SN retained without inventing accession.
163|One Florent Antoine Heller 1894 Basque drinker watercolor; frame dimensions retained literally, Helen West Heller prints are a different maker.
164|One detached Helmut Kolle Turfiste leaf no.37, blue ink 21 by 13.4, workshop stamp; separate physical leaf from 185 no.91.
165|One Raoul Lesage de la Haye 1969 Hotel de la Meriais drawing, 23 by 16.5; no confusion with Augustin or Pierre Alexis Lesage.
166|One signed Moizard 1843 west-view castle pencil drawing, 30.3 by 54; no corresponding maker/title identity.
167|One signed Paillard 1831 Vitre pencil view, 23.5 by 29; exact-title Lalanne prints and Lottier oil are distinct media/periods.
168|One Rupin Gatesel tower/gate wash drawing dated 18 June 1855; existing Puits Pese oil and candidate 187 different site/composition.
169|One Sagnier Pere 1738 Oratory-tower watercolor/wash on mounted paper, 50 by 38; date inscription identifies this sheet.
171|One anonymous eighteenth-century Saint Joseph/Child oil on copper, 15.5 by 12.5; existing Murillo canvas is seventeenth century and 27 by 17.
173|One Alanic Madeleine plan, 65.5 by 76 in blue/grey wash, signed 1828; different sheet dimensions and medium from watercolor plan 142.
174|One Aubree 1854 castle/ditch drawing, 22 by 33.5; distinct from Notre Dame 1853 upright sheet 144.
175|One Audroing 1886 gendarmerie ground-floor plan, 48 by 61.5; one paper sheet, not a building or entire architectural project.
176|One Belay 1942 Pipriac farmyard gouache, 37 by 52; existing Pipriac oils and nude landscapes differ physically and compositionally.
177|One Busnel 1876 market-place ink drawing, 14 by 20.5; title inscription Marchix retained, different scene from Poterie street 151.
178|One Darcy signed 1870 restoration-plan drawing, 68 by 103; independent inventory and layout from held 154 date-conflicted plan.
180|One Jean Cottereau portrait, 15 by 11 image; Dupuis question-mark signature reading retained, separate sitter from Treton 157.
181|One Gaucherel 1844 Porte d'en Bas wash drawing, image 27.5 by 36.5; distinct year/site/format from castle gate sheet 159.
182|One Gautier 1772 castle-view sanguine counterproof, inventory 1884, image 25 by 43.3; separate from city-view counterproof 160.
183|One E. Gontier drawing of Claude d'Espinay's tomb, 45.5 by 28; distinct tomb from her parents' monument 161, unknown inventory retained as SN.
185|One detached Kolle portrait leaf no.91, black ink 20.7 by 13.1; different leaf, ink and composition from blue-ink Turfiste 164.
186|One 1969 Lesage de la Haye Saint Martin tower drawing, 23.5 by 16.5; same creator/period as 165, separate site and sheet.
187|One Rupin Tour d'en Bas pencil/wash sheet, 20 by 29.7; separate from Gatesel gate 168 and existing Puits Pese oil.
188|One signed Ernest Simon July-1890 Petit Rachapt watercolor, 48 by 34; existing Bahieu oil is 177 by 234 dated 1882. Do not inherit signature conflict of held companion 170.
189|One anonymous seventeenth-century Judas kiss oil on copper, 17 by 21; existing Gue nineteenth-century oil is a different format/period.
191|One Renee dessert plate, diameter 22.2 and height 2; distinct from deep Renee plate 219 (25.8 by 3.3). Unknown maker retained.
193|One 1885 Claudet Lazare Hoche decorative dish, diameter 35.8; child in revolutionary uniform, separate from Claudet busts/reliefs.
194|One signed 1876 grandmother/child plaster relief, 34.5 by 22 with mounting holes; not a ceramic dish or grouped relief.
195|One Max and Julie Claudet 1882 crayfish-fisher dish, diameter 59; both signatures retained; Besson maiden-name comparison adds no matching ceramic.
196|One Max/Julie Claudet 1880 hellebore vase, 35.5 high, J. Max signature; different from bust of Georges-Max and other vessels.
197|One 1881 Claudet Saint Nicolas dish, diameter 58; exact-title panel paintings and later Cournault work are distinct.
198|One signed Marie-Anne Collot 1765 Claude Marmet terracotta bust, 44.5 by 30 by 26; existing Collot/Falconet Dutch sitters are 1782 marble. Jacques Callot print aliases are not this maker.
200|One Fouleux 1871 Combat de Salins charcoal drawing, 113 by 83, signed/date-supported; depiction and creation year explicitly agree.
201|One signed Framin 1875 Marianne plaster bust, 90 by 53 by 47; Halou's small 1848 terracotta differs in maker, size and material.
202|One Le Reve flat plate, 24.8 by 2, Charbonnier/Salins mark; other near-identical service notices held for physical review, count only this selected vessel.
204|One signed Theodore Guillot male oil portrait, 55.5 by 46; existing self-portrait on wood and port views are different physical works.
205|One Victor Huguenin 1832 Bachelu plaster bust, 65 by 50 by 26, signed/date-inscribed; historical sitter biography not used as creation metadata.
207|One Khotz Claude Joseph Marmet pastel/crayon drawing, 30.5 by 21.5. Gift label 1898 is provenance, not exact creation; broad nineteenth-century date retained.
208|One river-fisher watercolor attributed to Masquelier, 13.5 by 19; Mosquelier spelling from inscriptions included in identity check and source, attribution not promoted.
209|One seventeenth-century Salins panorama print after Van der Meulen by Boudewyns/Baudouin, 50 by 131 image. Existing Salins oil is 264 by 166; retain separate model/engraver roles.
210|One Mazerand 1830 Bonzon printed portrait, 39.5 by 30.5; mount/frame not counted separately. Existing Mazerand town oils have different subjects/supports.
211|One 1888 Carnot heliogravure after Petit/Dujardin, 61 by 43.5; photograph date 1887 retained as prototype evidence. Exact-title Pageot-Faure entry is a different maker.
213|One Virtue-triumph allegory, 100 by 136; source prefers Claude-Marie over Claude-Adrien Richard and this uncertainty is explicit. Existing Time-leading-vices canvas is a different subject, not inferred pendant identity.
214|One eighteenth-century Delaunay print after Weenix's 1667 painting, 50.7 by 62.5. Existing La Partie de plaisir is labelled Weenix/1667, consistent with model rather than this later engraving; after/engraver roles preserved.
215|One anonymous seventeenth-century St Jerome-in-cave canvas, 242 by 176; no matching exact source/title identity and unknown maker remains explicit.
218|One seventeenth-century full-length Ecce Homo copy after Solario, 149 by 83. Existing small 1500–1505 panel is 39.3 by 31.5; source distinguishes full-length composition from prototypes.
219|One Renee deep plate, diameter 25.8 and height 3.3; larger/deeper than dessert plate 191. Other indistinguishable deep-plate notices held, no quota-driven multiplication.
221|One signed 1881 Claudet dish depicting an old woman returning from market, diameter 35 and height 4.4; distinct from portrait/profile Mother Lantimeche dish 223.
222|One signed 1874 Max Claudet plaster self-portrait bust, 44 by 22.5 by 24; none of the full Claudet pool or other-maker self-portraits is this bust.
223|One signed 1881 Mother Lantimeche profile dish, 34.5 diameter; source profile format distinguishes it from old woman returning from market in 221.
225|One Madame Godin pastel pendant, 1851, 24 by 18.5; own signature/date supplied. Male pendant's conflicting date does not change this record.
227|One anonymous nineteenth-century Narcissus oil, 53.3 by 64.9; existing Gaudar composition is 164.7 by 198.4, a different physical canvas.
229|One signed November-1891 Claudet Algerian mother/child dish, diameter 35. Inventory 2017.1.1 collides with a Perronneau 1767 pastel portrait in a different collection; different medium, maker, subject and date rule out identity.
234|One signed 1882 Jura peasants/cheese-soup dish, 55 by 52 by 8. Verso family dedication from 1939 is provenance, not creation.
235|One small Claudet Notre Dame Liberatrice plaster relief, 29 by 14.5 by 0.7; single relief, distinct from the grouped Judas/Wandering Jew terracottas.
237|One anonymous eighteenth-century Christ-on-cross canvas from justice hall, 155.5 by 96; exact-title scoped records name other makers, no unknown equivalent surfaced.
239|One 1887 Lendemain de combat decorative dish, diameter 64, dying soldier/family and Athena/arms/owl border; medallions belong to one vessel.
'''
NOTES={int(line.split('|',1)[0]):line.split('|',1)[1] for line in _TEXT.strip().splitlines()}
QUALIFIED={
5:('Belloir Julien (attribué à) ou Belloir & Vazelle','Precisions_sur_l_auteur'),
7:('CHAPERON paul-romain (attribué à)','Precisions_sur_l_auteur'),
10:('Caranza de Amédée (1843-1914) (attribué à);Vieillard Jules & Cie','Precisions_sur_l_auteur'),
26:('Galliari Gaspare (1761-1823) (attribué à) ou Basoli Antonio (1774-1848) (attribué à)','Precisions_sur_l_auteur'),
33:('La Veuve Perrin (attribution incertaine) ou Honoré Savy','Historique'),
34:('Lacour Pierre (1778-1859) (d’après);Manufacture David Johnston','Precisions_sur_l_auteur'),
48:('Paraud Pierre (1759-1812) ou Paraud François Joseph','Precisions_sur_l_auteur'),
49:('Percier Charles (1764-1838) et son cercle','Precisions_sur_l_auteur'),
55:('Denon Dominique Vivant (1747-1825);Guerchin Le (1591-1666) (d’après)','Precisions_sur_l_auteur'),
111:('DARGENT Jean Edouard (auteur du modèle);PORQUIER-BEAU (faïencerie, attribué à)','Precisions_sur_l_auteur'),
112:('G. Fély (?) / Félix (?) (auteur du décor);Saint-Amand & Hamage (faïencerie)','Precisions_inscriptions'),
213:('Richard Claude-Adrien (1662-1748) ou Richard Claude Marie (peintre, attribution proposée)','Precisions_sujets_representes')
}
INVENTORY_EXCEPTIONS={229:{'d43afd98-1fe6-494a-8ff1-b773f66a8afa'}}
assert set(NOTES).isdisjoint(HOLDS) and set(NOTES)|set(HOLDS)==set(range(1,241))
assert set(QUALIFIED)<=set(NOTES)
