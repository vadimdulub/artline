#!/usr/bin/env python3
"""Individual Princeton decisions, preserving source ambiguity and physical units."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('identity',Path(__file__).with_name('museum-expansion-princeton-identity-20261007.py'));identity=importlib.util.module_from_spec(s);s.loader.exec_module(identity)
s=importlib.util.spec_from_file_location('aliases',Path(__file__).with_name('museum-expansion-princeton-aliases-20261007.py'));aliases=importlib.util.module_from_spec(s);s.loader.exec_module(aliases)
f=identity.f;m=f.m;RUN=f.RUN;IID=f.IID;ref=f.ref;checked=f.checked
CANDIDATES=RUN/'native-candidates-002.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CITATIONS=RUN/'identity-citations-002.json.gz'
NOTES={
1:'One bronze censer with five represented biblical episodes, not five works. Native seventh-century object dates are distinct from the Early Byzantine period label; purchased from Castano in1943.',
2:'One late-antique/Byzantine glass jug. The four exact-title records are an Escher print, Cleveland fritware, gold and earthenware objects, with different dates, sizes and inventories. Preserve Glass as source classification and unknown mapped type.',
3:'One Byzantine ring with a Saint Paul head, not a separate portrait and ring; Behrenberg gift and native inventory identify the physical metal object.',
4:'The fifth-century pendant cross is native suffix f of the1930 purchase, separately accessioned from b and g and with its own dimensions. One pendant, not an inferred altarpiece pendant painting.',
5:'One bound1296 manuscript of297 folios. Keep its eighteenth-century binding in the literal medium; do not count individual folios or use the binding date as creation of the Gospel manuscript.',
6:'One inscribed three-ounce Byzantine weight; the title states the historical weight denomination, not an invented metric measurement.',
7:'This pendant cross has suffix b and source fifth–eighth-century bounds, distinct from suffix f and g objects. Count one separately documented pendant.',
9:'The dotted-circle cross is suffix g, distinct native object and dimensions from b and f. Count one pendant and retain the broad fifth–seventh-century date.',
10:'One fifth-century buckle, Behrenberg gift. Its inventory and physical measurements distinguish it from the other separately accessioned buckle in this selection.',
11:'Second separately accessioned fifth-century buckle, Behrenberg gift. It has a different native ID, accession and dimensions; no duplicate created from alternate views.',
13:'One tenth-century ivory relief plaque attributed to the Nikephoros Group. Preserve that qualified attribution; maker activity dates970–1029 are not substituted for the object date. Drill holes describe attachment history, not a surviving complete assembly.',
14:'One fragmentary Greek royal portrait sculpture, third century BCE. Native negative creation bounds preserved; neither an identified ruler nor a complete lost statue is invented.',
15:'One Davies etching/aquatint sheet in the Mather Collection, plate30.2×20.2cm and sheet38.6×24.7cm. Cleveland1963.600 is separately credited to Mrs.Malcolm L.McBride and dated1920; its current official API documents a separate collection impression. Preserve Princeton1918–1919 and Ernest Haskell as printer, not co-artist.',
16:'One1664 Greek litany manuscript given by Mather. A title language/tradition label remains an object label; no named scribe is invented.',
18:'One East Greek turtle-shaped ceramic aryballos, sixth century BCE. Preserve the actual memorial gift and object dimensions, not a modern depiction of a turtle.',
19:'One late-eighteenth–nineteenth-century marble Hermes. Its former fourth-century-BCE attribution is retained only as former attribution; the1984 purchase provenance and modern creation bounds remain distinct.',
20:'One kneeling-figure aryballos of faience, sixth century BCE. Preserve faience literally and leave the broad mapped type unknown; do not force it into pottery.',
21:'One faience baboon-and-young aryballos. The represented animals do not create multiple objects; native sixth-century-BCE date and dimensions identify the vessel.',
22:'One third–second-century-BCE metal Eros. Exact-title Hayter record is a1970 print with a different creator, inventory and medium.',
23:'One East Greek lydion, native circa550–525BCE. It is separately inventoried and measured from the later lydion in this selection.',
30:'One East Greek lydion with the literal circa540–500BCE label and native numeric range545–500BCE. Preserve the source approximation and Caroline G.Mather Fund purchase; it is distinct from the circa550–525BCE vessel.',
31:'One glass amphoriskos, late-sixth–fifth-centuryBCE, Mayer gift. Retain the source period-label alternatives and unmatched glass type; no personal maker inferred.',
34:'One sixth-century-BCE faience hedgehog aryballos, museum purchase. The named animal is the vessel form; retain faience and unknown broad type.',
35:'One surviving handscroll fragment dated1321, not eighteen separately counted icons or the lost complete ten-scroll compilation. Keep Ryōshō and the source account of the copied iconographic text; no creator dates substituted.',
36:'One seventeenth-century carved wood Dormition icon, Friend bequest. Specific icon/carving classification supports sculpture and icon form; literal Byzantine label preserved despite its post-Byzantine date.',
37:'One surviving fourteenth-century triptych wing, not three panels. Native blue-steatite relief and measured fragment support sculpture; preserve the broad Ceramic source classification as a discrepancy. Purchased from Margret Burg in1952.',
39:'One surviving twelfth-century military-saint steatite relief fragment, purchased from Komor in1957. Count only the surviving accession, preserve the missing identity and original extent, and keep the contradictory broad Ceramic source label as evidence.',
40:'One Ethiopian diptych with two panels under one a-b accession, Mather gift1946. The native late-fifteenth–early-sixteenth-century date and unidentified maker remain qualified; no two-record split.',
41:'One seventeenth-century painted Saint George panel, Haring bequest. Exact-title Altdorfer and Dürer woodcuts have different dates, creators, media and inventories. Do not assign either printmaker to this unidentified panel.',
42:'One fifteenth-century tempera panel,46.5×37.7×2.4cm, Museum Collection. Exact-title prints/drawing and1544 Chourri painting are different works; preserve the Late Byzantine cultural label and no invented personal creator.',
43:'One early-fourteenth-century Twelve Apostles icon with explicitly later gilding/frame. Count the extant panel once and retain the later modifications in its title; do not pretend the frame shares the painting date.',
44:'One surviving Gabriel panel from a kings-door Annunciation,76×38.8×2.7cm, purchased from the Hill estate. No complete iconostasis or missing companion panel is reconstructed or counted.',
45:'One surviving Chairete steatite icon-relief fragment, Heyer gift1961 after purchase from Lubin. Its dimensions and accession differ from the military-saint fragment and triptych wing; retain fragment status.',
46:'One Virgin-head fragment from a larger icon, Angleton Hyde gift2010. Preserve the provisional fifteenth–sixteenth-century date, Greek label and probable Crete discussion without making Crete a structured certainty.',
47:'One porcelain Dog of Fu,13.2×5.4×6.8cm, accession162. Distinct physical dimensions and accession from161; native provenance specifies Prime gift1890 while the bracketed credit remains uncertain and is preserved.',
48:'One porcelain Dog of Fu,13.0×5.3×7.6cm, accession161. Distinct physical dimensions and accession from162. Preserve the qualified Trumbull-Prime credit and explicit1890 museum gift provenance.',
51:'One eighteenth-century sculpture attributed to Jan Claudius de Cock, Thorne gift for the Boudinot Collection. Exact-title Delaune engraving and Daglish record have different creators and physical identities.',
52:'One1924 Larionov drawing15.6×10.6cm, anonymous gift. No corresponding Bathers object in the38-record creator scope; exact-title other-creator paintings/prints are separate. Source rights labels retained, with no image use.',
53:'One folding brass polyptych with twenty represented scenes, Friend bequest1956. Open and closed dimensions identify the same object; no split into twenty artworks. Generic Polyptych hits are fourteenth-century Italian paintings.',
54:'One1922 Kandinsky plate4 lithograph, Rothman bequest by exchange. Met31.10.20 is the same composition in a separately inventoried Dick Fund1931 sheet; near-equal dimensions are expected for impressions, not evidence of transfer. Other Small Worlds numbers are different plates. Preserve publisher role and no invented print state.',
56:'One1933 Sasha Stone photograph from Femme, museum purchase with anonymous gift. Keep the individual native accession and dimensions; the series is not imported as additional works.',
57:'One1930 Rodchenko photograph, Fowler McCormick Fund purchase. Preserve source date and reproduction restrictions; no image downloaded or attached.',
58:'One porcelain gravy boat by the explicitly named Imperial Porcelain Manufactory, not an invented individual painter. Source late-eighteenth–early-nineteenth-century bounds and Prime1890 gift provenance are distinct from the manufactory foundation date.',
61:'One seventeenth-century Four Russian Patriarchs painted icon, Bancroft memorial gift. Four represented figures count as one panel; retain Russian as the object-level cultural label.',
62:'One knife-and-sheath set under the single a-b accession, Elliott bequest. Antler/leather/metal remain literal; unknown broad type is preferable to treating the whole object as ivory sculpture.',
64:'One tenth–twelfth-century ivory griffin plaque, Mather gift. Preserve the question mark in Russian (?) and the unknown broad type; no certain geographic origin or named maker invented.',
65:'One1906 Duveneck Antique Shop painting, Cleveland donors gift. Exact-title Horter etching and Bacon lithograph are different objects. Preserve source-use restrictions; no reproduction attached.',
67:'One seventeenth-century Virgin/Child/Catherine panel with literal Greek,Cretan label, Norman Muller gift. No unqualified named painter assigned.',
68:'One Dou Penitent Magdalene panel, Fowler McCormick Fund purchase. Exact-title El Greco, Pittoni and Reni works are different creators/versions. Preserve both the circa1660–65 display and source1655–1665 numeric bounds.',
69:'One1797 Benjamin West Beast painting, Bates/Notaras memorial gift. No same composition in the336-record broad creator scope; the highest token-similarity result is a Helen West Heller woodcut.',
72:'One1905 Ranger Hillside Trees painting, Cleveland gift. Distinct title and inventory from the same-year Woodland Scene and existing Lone Sentinel; retain source-use labels.',
73:'One1905 Ranger Woodland Scene painting, Cleveland gift. Existing Lone Sentinel is1895 and separately inventoried; Hillside Trees is another documented object.',
75:'One1889 Jones Autumn canvas38.1×81.3cm, Cleveland gift. The current Met API for11278 identifies a25.4×35.6cm canvas, Salter gift1907, accession07.119.8. These are distinct physical paintings, not a holding transfer.',
76:'One1885 John Francis Murphy Summertime painting35.6×48.3cm, Cleveland gift. Exact-title works by Cassatt,Kienbusch,Homer and other creators are separate; no matching Murphy composition in the104-record creator scope.',
77:'One circa1591 Cornelis van Haarlem Apollo panel. Native medium Oil on wood panel and specific oil-paintings term support painting despite the broad Metal classification; preserve the contradiction in evidence.',
78:'One1960 Toledo Cubista canvas, Meginnity bequest. Creation date is before1971 despite the artist living until2019; source-use labels remain evidence only.',
81:'One1520s van Scorel portrait of a possible pilgrim, Caroline G.Mather Fund purchase. Preserve possibly in the title and unidentified sitter; no source-identity or same-object creator-scope counterpart.',
83:'One1540–1549 Beccafumi Holy Family panel57.8×46cm. NGA1943.4.28 Holy Family with Angels is a different81.3×61.6cm panel; exact-title Mignon/Carracci prints and other-creator paintings are separate.',
84:'One circa1550 panel of a lady as Poppaea Sabina, Galt gift. Fontainebleau School remains a school label; a role-played identity is not an asserted portrait of the ancient empress.',
87:'One circa1860–65 Rousseau Plain of Chailly panel, Eugene Geddes gift. No same composition in the255-record broad creator scope; preserve source wood support and dimensions.',
90:'One1580s? Saint John panel by a Follower of Tintoretto, Cannon gift. Exact-title Baldung painting and Schongauer/Dumoûtier graphics have different creators, dates and inventories. Preserve the question mark and follower attribution.',
97:'One Boudin Le Havre wood panel27.1×21cm, Remington bequest. NGA2015.19.58 is canvas52.39×72.87cm; Louvre1888 port panel is32×41cm; the other close port record is a drawing. Distinct support/size/version, not merely another holding for the NGA canvas.',
98:'One1869 La Farge Snow Weather panel, Mather gift. No same title/native/inventory counterpart in the41-record creator scope.',
24:'One bronze warrior11.4×5.1×4.3cm, Shear gift1947. The native inscription is a dedication by Pythodoros to the River Pamisos, not an artist signature. Preserve Greek,Messenia or Arcadia as alternatives and circa550–525BCE.',
101:'One1963 Siqueiros painting48×39cm, Meginnity bequest. No corresponding Tropics Today work in the41-record creator scope; source rights retained without image use.',
102:'One1648 van der Poel canal farmhouse panel36.2×44cm, museum purchase. No same physical/title work in the26-record creator scope.',
105:'One surviving Saint Peter altarpiece gable,47.4×22.5cm, Meiss bequest. Preserve Circle of Nardo di Cione; NGA1939.1.261.a is a different left panel49×16.9cm. Retain the native mid-fourteenth-century label and wider1350–1399 numeric range as source evidence.',
106:'One1952 Seitz Mirror painting96×60.7cm, gift of the artist. No same object in the five-record creator scope; exact-title works by other creators are separate.',
108:'One1956 Alan Wood-Thomas Crustacean painting50.8×65.8cm, Fox gift. The4546-record broad Wood/Thomas scope has no same composition. Its blank-title Rowlandson lead is an1822 hand-coloured etching, not this1956 painting; unrelated Whymper similarity is not identity.',
111:'One1956 Crustacean Snared, separately accessioned from Crustacean despite equal dimensions and donor. Retain each native title and count one canvas for each. The blank-title Rowlandson lead in the broad Thomas scope is an1822 etching, a different creator/date/medium.',
112:'One individually catalogued Gradual leaf46.2×32cm, letter R/Resurrection, Morgan gift1929 after the Gelis-Didot sale. Count this surviving illuminated leaf once, not the original Gradual or each depicted element.',
114:'One1490 Descent into Hell panel61.5×59.5cm, Kienbusch memorial purchase. School of Simon von Taisten remains qualified; no named-author attribution substituted.',
120:'One small surviving Madonna fragment from a Crucifix,15.1×10.8×1.3cm, source mid-thirteenth-century bounds. Count the surviving accession only, not an invented complete Crucifix.',
126:'One fourteenth-century Mezzana Master panel121.5×55×9cm, Mather gift1927. Literal object century independently supports the date despite matching broad maker activity. Jacopo del Casentino remains former attribution. Other exact-title records are different named creators/physical versions.',
129:'One late-fifteenth-century Artés Master Annunciation panel41.3×53cm, Kienbusch memorial collection. Joos van Cleve exact-title painting and other broad Master-scope entries have different makers/physical identities; no same native or inventory match.',
130:'One circa1520 Visitation tempera panel, sight19.4×15cm. Keep Circle of Wolf Huber and Anonymous,South German together; Hans Dürer remains former attribution. Native provenance documents Nazi seizure, return to Mrs.Bondy and later Martin gift1954; this is not a present restitution or loan statement. Dürer title matches are woodcuts.',
133:'One1462 Foppa panel with two angels and donor, Platt bequest, panel76.7×57.2cm. Met30.95.293 is a circa1480 Madonna43.8×32.1cm with different composition/size.',
134:'One1944 Federico Cantú Horse painting50×65cm, Meginnity bequest. Native date governs scope, not the later bequest; no same-object creator lead.',
135:'One Indian illuminated sheet with Crow pecking Horse, nineteenth–early-twentieth-century source bounds1800–1929. One measured image/sheet, not separately counted animals; cultural label remains object level.',
136:'One1959 Tobey Untitled painting45.7×25.4cm, Cohen memorial gift. Existing same-title Tobey works are1964 oil/collage212.1×157cm and1957 ink drawing33.7×24.4cm; distinct physical works.',
137:'One Master of Perea Entry into Jerusalem panel59.8×66.2cm, Hughes gift. Exact-title prints and later icons have different dates/media; the anonymous Fitzwilliam panel is38.8×27.6cm. Retain native late-fifteenth-century date and notname label.',
138:'One fourteenth-century Luca di Tommè Pope Urban V panel66.8×50.1cm, museum purchase1951. Angelo Puccinelli remains former attribution and is not appended to the active creator label.',
139:'One late-fourteenth–early-fifteenth-century Italian Saint Jerome panel30×36cm, Kienbusch gift. Exact-title Crespi painting is1710–20 and Baldung work is1511 woodcut; no conflation.',
145:'One a-b accession consisting of a Madonna/Child panel and predella, museum purchase1953. Count the documented composite once; preserve separate panel/predella measurements. Jacopo di Cione and Niccolo Gerini are former attributions, so retain current Italian object label.',
147:'One fourteenth-century Crucifixion panel100×62.5cm, documented1930 museum purchase. Robert Oderisi remains former attribution; the current source personal creator is unknown, retained as Italian label.',
149:'One mid-seventeenth-century Indian illuminated illustration21.5×17cm, Davis gift. No named poet/artist inferred from the subject; no same-title/native/inventory lead.',
150:'One1870 Richards Sailboat painting36.8×67.3cm, Feld gift. Specific New Jersey subject and native physical measurements have no same-object creator-scope counterpart.',
151:'One1964 Morales Marina canvas127×102cm, Hooker gift. No same composition in the18-record creator scope; retain actual source-use labels.',
153:'One1959 Schneider30D canvas195×129.5cm, Kootz gift. Title number is not an edition count; one separately accessioned painting.',
154:'One1958 Serpan Dluddaa canvas130×162cm, Lescaze gift. No corresponding object in the two-record creator scope.',
155:'One1950 Nay Figural Alpha painting40.3×75.2cm, Hume gift. No matching title or physical identity in the ten-record creator scope.',
157:'One1777 Guiol casta canvas numbered12,62.3×55.2cm, purchased2022. Native provenance explicitly identifies five separate canvases from an original sixteen-painting series, distributed then reassembled; count only this physical canvas. Retain historical title and critical museum interpretation without endorsing its racial hierarchy.',
158:'One1957 Kienbusch To the Ocean canvas83×126.5cm, Beal gift. No matching object in the four-record creator scope.',
160:'One1777 Guiol casta canvas numbered10, separately accessioned from numbers2,12,16. Source provenance explicitly treats these as separate paintings, not details of a single canvas; retain historical title as catalogue evidence.',
161:'One1954 Mathieu Robert II Laying Siege painting96.5×195cm, Kootz gift. The historical event named in the title does not supply creation date.',
162:'One1954 Birolli Song to a Happy Land canvas195×148.5cm, Kelleher gift. No same composition in the24-record creator scope.',
163:'One1965 Sawada Tetsurō Untitled canvas169.5×126.4cm, Reik Fund purchase. Additional Latin-component Sawada/Tetsuro authority, alias and unlinked-label queries found no existing creator/work. Separate from the76.2×101.6cm Cioffi gift of the same year.',
166:'One1777 Guiol casta canvas numbered16, its own2022-49 accession. The explicitly separate-canvas group provenance supports one record for this canvas; no count of represented family members.',
167:'One1777 Guiol casta canvas numbered2, accession2022-45. Separate physical canvas in the documented reassembled five-painting group, not the entire original series.',
168:'One1952 Corpora Composition145×113.5cm, Seeger gift. None of the309 generic title hits is a corresponding Corpora object; the three-record creator scope has no same composition.',
169:'One1965 Sawada Tetsurō Untitled canvas76.2×101.6cm, Cioffi gift. Literal Latin-component alias query found no existing artist/work; dimensions, credit and accession distinguish it from the much larger Reik Fund painting.',
170:'One1952 Morlotti Bulls canvas160×212cm, Seeger gift. No corresponding object in the ten-record creator scope.',
171:'One1950 Beckmann Bowery painting60.5×30cm, Seeger gift. Existing exact titles are Reisman etching, Marsh tempera and Gropper lithograph, different artists and physical works.',
172:'Existing Maitland record has exact2016-58 accession and native125768 reference, title and compatible circa1890 date. Reconcile the Hall-bequest museum holding only; preserve its existing date, image and artist authority. Cheyne Walk in Sunshine and generic Chelsea view are distinct leads.',
175:'One1956 Hosiasson Commencement painting162×113.5cm, Lescaze gift. No same physical object in the three-record creator scope.',
177:'One1960 Jack Smith Light and Dark Machine canvas137.5cm square, Seeger gift. Broad572-record Smith scope has no corresponding title/version.',
178:'One circa1850 Searle Two Plums canvas9.5×13cm, Feld gift. Exact-title George Brookshaw record has a different creator; no Searle counterpart.',
180:'One1964 Picasso Head of a Man and Seated Nude canvas65×81cm, Callimanopulos gift. The3650-record creator scope has no exact title/native/inventory counterpart; preserve the two represented figures as one painting.',
181:'Existing Richardson self-portrait matches native131632 and2017-155,1733 and Surdna purchase. Keep this record distinct from Richardson the younger self-portraits and the1736 Yale portrait; update only its pending Princeton holding.',
182:'One seventeenth-century Young Prince canvas76.8×63.3cm, Moffett gift. Preserve attributed to Gerard Soest and unidentified sitter; no same-object creator-scope counterpart.',
183:'One1960 Kokoschka Joshua Logan canvas100×81.2cm, Logan bequest. Closest creator-scope portrait titles are other named sitters or earlier drawings; no same Logan portrait.',
185:'One seventeenth-century portrait titled Antonio Caracci, Kienbusch memorial gift. Italian remains the creator label; the sitter title is not converted into an artist attribution.',
186:'One1807 Granet Tivoli/San Silvestro canvas, McCormick Fund purchase. Specific church/view title and native identity have no corresponding creator-scope work.',
188:'One Hunt Dressing for the Play canvas59.2×88.9cm, Koller gift. Native literal probably1860s is retained; numeric1862 is independently supported by the source signature transcription Ch.Hunt1862, not invented from the decade.',
189:'One1950 George L.K.Morris Solid and Void painting, Miller/Vivante gift. No same title/native/inventory counterpart in the broad207-record creator scope.',
191:'Existing Ramsay record matches native32596, y1982-79, John Second Baron Desart and1751. Official Quarles gift confirms museum connection; preserve existing catalogue values and image.',
194:'One nineteenth-century German portrait of Friedrich Gottlieb Kretzschmar von Kienbusch, Kienbusch bequest. The sitter is not promoted into a creator; no exact-title/native/inventory counterpart.',
195:'One Bonnard Tugboat on the Seine canvas40×58.7cm, Bienstock gift. Closest Seine works are a20.3×30.4cm1916 canvas, Met34.9×48.3cm House on the Seine and24.5×29.5cm balcony view. Preserve circa1912–26 and distinguish these different supports/extents/subjects.',
196:'Existing Wright of Derby Old John portrait has exact2018-158 and135184 source identity, compatible circa1780 and Surdna purchase. Reconcile its holding without narrowing the catalogue date or changing image/artist.',
197:'One early-twentieth-century À La Mort canvas66×54.5cm, Keating gift. Retain attributed to Henri Pierre Lejeune and native1900–1923 bounds; the Lejeune signature does not justify removing the qualification.',
198:'One1957 Alan Davie Dog and Moon Adventure I canvas122×182cm, Seeger gift. Roman numeral identifies the titled work, not a count of additional unselected paintings.',
199:'One1928 Lurcat Standing Woman canvas41.3×27.2cm, Kelleher memorial gift. Closest Lurçat work is a1925 Reclining Woman drypoint with different pose, date, medium and dimensions.',
200:'One circa1788–89 Raeburn Lady Anne Miller portrait77.3×64.9cm, Lidow gift. Preserve the native1783–1793 numeric approximation; no same named sitter/native identity in the53-record scope.',
201:'One1920 Nolde Twilight canvas40.5×55cm, Bargmann bequest. Exact-title works belong to other creators; no matching Nolde version in the116-record scope.',
203:'One1857 Díaz landscape canvas41×69.2cm, Taplin memorial gift. Same-creator exact-title2008.389 is a circa1860 watercolor/gouache drawing15×22.8cm; other autumn landscape is1876. Distinct physical painting.',
204:'One1912 Burlin Figure of a Woman canvas101.6×76.2cm, Harris estate gift. No corresponding Burlin object in the six-record creator scope; generic exact titles belong to other creators.',
205:'One circa1830? Rousseau Auvergne? landscape canvas27×34cm, Mather gift. AIC1975.668 is a33.2×43.4cm canvas; AIC1894.1065 is a21.7×27cm panel dated circa1850. Other landscape leads are circa1860–65. Preserve both source uncertainties and native1825–1835 range; no duplicate from the generic subject.',
206:'One1953 Porter Katie canvas60.9×55.6cm, Herring gift. Exact-title Bernard Sickert record is a different creator; no Porter counterpart.',
208:'One1920 van Rysselberghe Nude with Agave canvas91.8×73cm, Prickett memorial gift. No same composition/native identity in the28-record creator scope.',
209:'One1895 Boudin Giudecca seascape canvas37.1×50cm, Wilder bequest. The two existing Douane/Notre-Dame-de-la-Salute leads include documented Marseille907.19.39, a19.7×39.7cm wood panel; Cleveland open-sky lead is1860 pastel. Different physical versions; retain the unresolved duplicate French leads without merging them.',
212:'One1882–87 Toulouse-Lautrec Marble Polisher canvas65.5×81.3cm, Forbes gift. The983-record creator scope has no corresponding work; similarly worded Marco Brothers are later photomechanical prints.',
214:'One1965 Lam Untitled canvas44×39cm, Meginnity bequest. Existing same-creator Untitled entries are1942–53 ink, watercolor or graphite sheets with different dimensions; no corresponding1965 canvas.',
216:'One1951 Afro Basaldella Nuovo Testamento II canvas110cm square, Seeger gift. No matching object in the seven-record creator scope; series numeral does not create another record.',
220:'One1911 Randall Davey drawing of Henri painting, Feld gift. The title identifies the represented artist activity, not an attribution to Robert Henri.',
221:'One1965 Yutaka Ohashi Water Painting sculptural object172.1×114.9×25.4cm, Forbes gift. Preserve native sculpture classification and material description; the word Painting in the title does not override physical type.',
223:'One1958 Ruth Bernhard House Painting photograph29×16cm, artist bequest. No same physical/title entry in the106-record broad creator scope; source reproduction restriction preserved without image use.',
224:'One1880s–1890s photograph19.7×25.8cm with separate mount dimensions, Bagley Fund purchase. Preserve Photographer unidentified and count the photographic object once, not the paintings represented within it.',
226:'One Soulages Painting:June10,1965 canvas92×73cm, Wolf-funded museum purchase. Tate Painting23May1953 is a different dated canvas194.9×130.2cm; no conflation from generic title.',
227:'One late1880s George Woodall cameo-glass vessel23cm high, McCormick Fund purchase. Exact-title Burney entry is a1790–1800 ink/wash drawing. Preserve glass as literal medium and broad type unknown.',
230:'One circa1900 German watercolor87.3×85cm of a Pompeian wall-painting, Dodge gift. This is a modern watercolor reproduction, not an ancient fresco fragment; preserve source type/date and unidentified maker.',
233:'Existing Peploe Paris-Plage record matches125769,2016-59,title and compatible circa1907. Hall bequest supports the accepted holding; preserve existing circa date and image.',
234:'Existing Cole record matches21730 and y1941-51. Museum text explicitly identifies the16×26cm oil-on-paper sketch for The Savage State, distinct from the large finished Course of Empire cycle. Reconcile this sketch record only and preserve its existing circa1834 date/image.',
235:'Existing Carrick Landscape has exact27935,y1957-25 and1861. Mather gift confirms museum connection; preserve its unresolved object-level creator label and existing image rather than creating a painter authority.',
236:'Existing Leighton After Vespers matches28649,y1961-17 and1871, museum purchase. Preserve the existing image/date/creator link and reconcile only the holding.',
237:'Existing Boyle Schiehallion matches28778,y1963-12 and1896. Its specific title and inventory distinguish it from the other Boyle Scottish landscape; update holding only.',
238:'Existing Boyle Bridge at Fortingall matches28923,y1963-13 and1896. Keep it separate from Schiehallion,y1963-12; update only the pending museum assertion.',
239:'Existing Vaughan Nude in Landscape matches29079,y1962-2 and1948. Confirm collection credit without attaching an image or changing its existing artist/date metadata.',
240:'Existing Etty Phaedria and Cymochles matches30445,y1967-24 and compatible circa1830. Native62.5×76cm canvas and object reference identify the version; preserve the existing catalogue date and image.',
241:'Existing Marshall Cotter Returning Home matches31667,y1971-12 and compatible circa1860. Accession1971 is acquisition context, not creation; retain existing date/image and reconcile holding.',
242:'Existing Severn Mother and Child with a Bird matches31798,y1978-34 and1845. Native sight width935cm conflicts with its103.5cm frame width; retain the apparent source error as evidence and do not write dimensions or correct it silently. Identity is secured by exact object URL/accession, title and creator.',
243:'Existing Moore Flower Walk matches33094,y1986-4 and1874–75. Native1874–75 is compatible with existing1874–1875; preserve catalogue metadata and image.',
244:'Existing Herbert Monastery record matches33196,y1988-24 and compatible circa1840. The fourteenth century in the title is the represented setting, not artwork creation. Retain literal source donor spelling and existing metadata.',
245:'Existing Varo Mujer matches39923,2001-140,creator and compatible circa1960. Legacy source response independently preserved the native URL. Confirm Meginnity-bequest holding without attaching an image or changing date.',
246:'Existing Lewis Gondolier matches46877,1996-265 and compatible circa1835. Native Forbes gift confirms collection connection; preserve existing catalogue values and image.',
247:'One Ndebele Itjogolo apron66×56cm, Mary Trumbull Adams Fund purchase. Literal mid-twentieth-century date is bounded by native1930–1969 fields, so it is eligible without inferring an arbitrary mid-century year. Artists unrecorded remains literal.',
248:'One circa480–470BCE Panathenaic amphora with two depicted sides, Marquand bequest. Retain in the manner of the Berlin Painter; do not count Athena and the chariot race as separate objects.',
249:'One circa1250 wooden Guanyin sculpture110cm high, Kienbusch memorial purchase. Preserve traces of pigments/clay relief and source1200–1300 range; no named sculptor invented.',
250:'One Maya drinking cup670–750, Widenmann-funded purchase. The Princeton Painter(name vase) remains the source attribution/notname, not a new personal authority. Red/cream/black slip and painted-stucco remnants belong to one vessel.',
251:'One sixth-century Japanese haniwa tomb figure50cm high, Wilder-funded purchase. Anonymous remains the creator label; Kofun-period dates are not substituted for the object century.',
252:'One Maya ceramic Ballplayer,600–900, McCormick Fund purchase honoring Griffin. Preserve traces of Maya blue and the individual physical-object dimensions.',
253:'One surviving coffin-lid fragment of Wadj-shemsi-su, circa1500–1425BCE. Native61×39.5×20.5cm fragment and composite materials are preserved; do not create a complete coffin or portrait of a separate living sitter. Broad type remains unknown.',
254:'One kneeling Maya noblewoman-and-lidded-jar assemblage under one a-b accession,600–800. Count the documented object once, preserving separate movable components and polychrome ceramic.',
255:'One museum-catalogued pair of tomb guardians under the combined .1-.2 accession, circa mid-eighth century. Two figures and their bases count as one pair record, not four artworks; full component dimensions retained.',
256:'One Igbo ikenga wood-and-paint figure, native first-half-twentieth-century1900–1949 bounds, McCormick Fund purchase. Artist unrecorded stays literal; mounted and unmounted dimensions are distinct.'
}
HOLDS={
66:'The literal After1608(?) statement supplies only a lower bound. Native1611 upper bound coincides with the maker death year; retain for date review rather than counting an after date as eligible.',
71:'Near-translated same-creator Paysage à la tour lead has32×26cm extent versus Princeton33.7×28.9cm and incomplete physical metadata. The small dimensional discrepancy is insufficient to rule out a catalogue variant or changed measurement; identity remains unresolved.',
25:'Component of1999-257 assemblage. Relationship of the separately catalogued bronze plaques/fragments to a single original object remains unresolved; do not inflate the count by components.',
26:'Component of1999-257 assemblage; original physical counting unit unresolved.',
28:'Fragment within1999-257 assemblage; original physical counting unit unresolved.',
29:'Component of1999-257 assemblage; original physical counting unit unresolved.',
33:'Component of1999-257 assemblage; original physical counting unit unresolved.',
59:'Full object has no credit line; physical print and collection connection need further review, despite a documented publication date.',
86:'Honfleur port composition has unresolved same-creator Joconde leads with incomplete physical metadata; do not create a duplicate from title similarity.',
89:'Anonymous Dutch Portrait of a Man has a large exact-title scope and former attribution. Physical identity reconciliation remains open.',
91:'Generic sixteenth-century French Portrait of a Woman requires fuller comparison against anonymous/qualified existing portrait records.',
92:'Literal seventeenth-century? date conflicts with native1612–1966 bounds, whose upper bound matches the gift year. Do not treat the acquisition date as supported creation.',
96:'Generic circa1550 Italian Portrait of a Man requires fuller physical-identity review across anonymous and qualified portrait records.',
99:'Literal seventeenth-century date conflicts with native1587–1641 bounds; generic portrait identity also needs further review.',
104:'Existing same-creator View of Dordrecht1660 may be the same painting; missing inventory/support dimensions require further object-version verification before adding or linking.',
107:'Native1560s catalogue date conflicts with the transcribed ANNO1538 inscription. Keep the discrepancy and qualified physical-version comparison open.',
109:'Native1560s catalogue date conflicts with the transcribed ANNO1538 inscription. Former Holbein attribution and paired-portrait identity require further review.',
118:'Generic late-fifteenth-century Italian Portrait of a Woman needs fuller anonymous/qualified physical-object reconciliation.',
119:'The native sixteenth-century after-Roger-van-der-Weyden panel and existing1440 Rogier Madonna need an explicit copy/original physical-version comparison; title and attribution distinction alone are not final approval.',
143:'Generic anonymous fifteenth-century Madonna and Child has97 exact-title leads. Further physical identity review required; no named creator inferred.',
148:'Literal after1400 is unbounded. Native upper1937 matches the gift year; retain the earlier1924 loan and subsequent1937 gift as provenance, not as a creation endpoint.',
152:'Qualified Highmore portrait has a close1738 lady lead with missing dimensions and only frame dimensions in the native record. Physical identity remains unresolved.',
156:'Existing Haystacks on the Newburyport Marshes has an unverified1862 date but no physical metadata. The date discrepancy cannot by itself rule out the same Heade painting; source-version check remains open.',
173:'Dutch Divine has an incompletely described same-creator Walters young-man lead. The Met portraits are different sizes, but this remaining portrait identity needs review.',
184:'Workshop of Canaletto? and mixed after/circa date are retained. Resolve the physical workshop version among Grand Canal compositions and the bounded-date interpretation before adding.',
187:'Two existing Jacob de Wit Autumn leads have unverified1740/1746 dates and missing physical metadata; native1751 alone does not rule out duplicates.',
202:'After-van-Dyck Duchess of Orleans portrait needs fuller sitter/copy comparison against the Margaret of Lorraine duchess lead; do not treat a sitter-label discrepancy as proof of a different physical painting.',
228:'Existing Saint Paraskeve lead lacks physical metadata. Native early-fifteenth-century date and Stroganoff School of Novgorod label also need chronological/attribution review; preserve both without inventing a correction.',
232:'Existing Chardin Attributes of the Sciences1731 and native Attributes of the Architect need a same-composition/version check. A date/title difference alone does not clear duplication.'
}
def build():
 x=m.load(CANDIDATES);ix=m.load(IDENTITY);cx=m.load(CITATIONS)
 for dep in x['dependencies']+[ix['query_reference'],ix['base_query_reference']]:checked(dep)
 ax=m.load(RUN/'latin-creator-aliases-001.json.gz');checked(ax['query_reference']);assert ax['patterns']==aliases.PATTERNS and ax['state']==dict(artists=[],aliases=[],artworks=[])
 for dep in ax['source_references']:checked(dep)
 assert ix['candidate_reference']==ref(CANDIDATES) and cx['identity_reference']==ref(IDENTITY)
 validation=m.load(RUN/'identity-recomputed-001.json');checked(validation['validator_reference'])
 assert validation['candidate_reference']==ref(CANDIDATES) and validation['identity_reference']==ref(IDENTITY) and validation['comparisons_recomputed_equal'] and validation['rows']==256
 assert validation['query_references']==[ix['query_reference'],ix['base_query_reference']] and ix['params']==identity.params_for(x['rows'])
 assert not x['partial'] and x['capture_count']==x['expected_capture_count']==256
 assert set(NOTES).isdisjoint(HOLDS);out=[]
 for row,cmp in zip(x['rows'],ix['comparisons']):
  assert row==f.parse(checked(row['source_reference']));n=row['number'];v=copy.deepcopy(row['facts'])
  if n in HOLDS or v['date_issue']:
   out.append(dict(row,state='editorial_hold',basis=HOLDS.get(n) or v['date_issue']+'. Preserve literal source values; no date inferred from maker lifespan, period or accession.',comparison=cmp));continue
  assert n in NOTES,('Missing individual decision',n)
  assert v['first']<=v['last']<=1970 and v['inventory'] and v['credit_line'] and v['creator_label']
  assert not any(flag in row['review_flags'] for flag in ['campus_collection_requires_review','university_portrait_inventory','inventory_or_credit_requires_review'])
  if cmp['untitled_creator_hits']:
   assert n in [108,111] and len(cmp['untitled_creator_hits'])==1
   hit=cmp['untitled_creator_hits'][0];assert hit['id']=='f74d27cb-6fe6-5885-8c14-522389f9060f' and hit['creators']==['Thomas Rowlandson'] and hit['date_display']=='1822' and hit['medium_text']=='Hand-colored etching'
  old=row['index'].get('existing_pending');state='approved_existing_holding' if old else 'approved_review_only_addition'
  if old:assert old['artwork_id'] in {a['id'] for a in cmp['inventory_hits'] if a['relevant']}
  else:assert not any(cmp[k] for k in ['native_scheme_hits','native_url_hits','source_hits']) and not any(a['relevant'] for a in cmp['inventory_hits'])
  icon=any(a.get('classification')=='icons' for a in v['source_fields'].get('classifications',[])) or n==40
  if icon:v['object_form']='icon'
  basis='Native object '+v['source_id']+', inventory '+v['inventory']+': '+NOTES[n]
  out.append(dict(row,facts=v,state=state,existing_artwork_id=old['artwork_id'] if old else None,confidence=.90,basis=basis,comparison=cmp,derived_fields=dict(object_form='icon' if icon else None,basis='Explicit native icon classification or Diptych Icon title; existing records unchanged'),limitation='Editorial confidence in same physical object and documented museum collection connection, not a calibrated probability. Full source metadata, qualifications, later modifications, rights and unknowns retained. No current-display, image-use, physical-custody or legal-title claim. No new painter authority; new records remain review and existing metadata/images/publication remain unchanged.'))
 return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();rows=build()
 paths=[CANDIDATES,IDENTITY,CITATIONS,RUN/'campus-collection-context-001.json',RUN/'latin-creator-aliases-001.json.gz',RUN/'identity-recomputed-001.json']+list(RUN.glob('comparison-*-001.json.gz'))+list(RUN.glob('version-web-*.json'))
 m.save(dest,dict(at=m.now(),reviewer_reference=ref(Path(__file__).resolve()),decisions=rows,supplement_references=[ref(p) for p in sorted(paths)],policy='Individual metadata and identity decisions. Index holds remain outside delivery; date-unknown and unresolved physical versions are preserved as research evidence. No source access bypass, images or production writes.'))
 print(json.dumps({k:sum(v['state']==k for v in rows) for k in ['approved_review_only_addition','approved_existing_holding','editorial_hold']}),flush=True)
if __name__=='__main__':main()
