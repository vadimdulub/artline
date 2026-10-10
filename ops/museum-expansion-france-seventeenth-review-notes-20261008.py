"""Cognacq-Jay object decisions; unresolved identities remain in the research queue."""
DEFERRED = {
387: 'Sparse Boucher Marriage 1744 comparator still needs primary physical identity.',
394: 'Grenoble Faure La Source primary-page lead found (178 x 94.5 cm painting); preserve and capture inventory MG704 before closing the sparse comparator.',
395: 'Complete the broad generic oil-portrait pool, including near-size and sparse records.',
398: 'Compare J42 composition and sparse Louvre Greuze girl identity against the white-bonnet copy J40; captured Louvre pages do not identify the sparse CSV entry by themselves.',
409: 'Resolve sparse same-era male portraits, including Jagger J780, Asper 5646 and Antolinez 876.3.2.',
417: 'Resolve the remaining sparse male-portrait physical identities; measured large oils are already distinguished from this 6 cm portrait.',
433: 'Resolve Jagger J780 and other sparse male-portrait identities against Isabey J744 ivory.',
435: 'Finish sparse Natoire INV6849 and Souverbie comparator context; native Julien attribution remains disputed.',
451: 'Unknown painting medium remains unknown; finish sparse Fontaine/Benner physical comparison.',
458: 'Fresh 27 manual pairs read, but sparse Heinsius, Millington, Dagoty and other female-portrait identities still need physical evidence.',
461: 'Resolve sparse Mallet Premiers pas comparator against Morland circular watercolor.',
464: 'Resolve remaining sparse male-portrait identities against Perronneau pastel; no date-only duplicate dismissal.',
470: 'V&A Hamilton DYCE.76 specifically resolved in wave71; complete broad remaining portrait pool before approving J75.',
477: 'Fresh generic pool reviewed; obtain composition evidence for near-size oil portraits, especially Lefevre P0920, before final release.',
489: 'Fresh generic pool reviewed; confirm closest former-Fragonard paper-portrait versions and composition before final release.',
490: 'Compare J42 composition and sparse Louvre Greuze girl identity against J49 Malice copy.',
510: 'Met 43.163.23 fan-study composition remains unresolved under the existing Met429 access hold; do not retry or bypass.',
}
ORIGINAL_HOLDS = {362,392,399,406,467,498}
SELECTED = sorted(set(range(361,511))-ORIGINAL_HOLDS-set(DEFERRED)-{439,488})
assert len(SELECTED)==125
GENERAL = ('National Joconde facts and matching native Paris Musees inventory/detail were reviewed together. '
 'Fresh source-ID, native URL, historical inventory, title, creator and related-work comparisons are preserved. '
 'Each physical miniature, sheet, painting or sculpture counts once; a frame, depicted work, model, obsolete title or companion is not another artwork. '
 'Native executing maker, model author, workshop, alternative and former attribution roles override the national export only in the derived object label; literal source fields remain intact. '
 'Date-only triage is not sufficient identity evidence: physical form, support, dimensions, composition, signatures and independently documented acquisition distinguish the selected objects. '
 'Unresolved sparse and close-version cases are explicitly deferred. Holdings do not establish current display. All additions remain in review with no artist-authority links or images.')
FOLLOWUP = {}
def note(nums, value):
 for n in nums: FOLLOWUP[n]=FOLLOWUP.get(n,'')+value+' '
note(SELECTED, 'The earlier source assessment and supplemental comparison notes remain evidence, with provisional language superseded only by the present explicit selection. Fresh comparison coverage and native physical units were reviewed. No identical source object was returned.')
note([366,370,371,393,425,426,427,441,457,469], 'The nine captured native miniature comparators retain separate shapes, signatures, frames and acquisitions: Kanz J791 signed enamel/copper 5.8 cm circle; Ledoux-attributed J749 7.2 cm circle signed LeDoux; Schrader J754 signed rectangle 8.1 x 6.8 cm; Engleheart-attributed J726 oval 5.7 x 4.5 cm with hair frame; Sicard J755 signed 1781 oval 4.6 x 3.6 cm; Villers-attributed J759 6.7 cm circle; Le Guay 1996.2 signed 7.3 cm circle purchased at Christies in 1996. Native candidate descriptions and current inventories independently establish distinct objects, not merely different spellings of a sitter.')
note([366], 'J704 bears Boquet 1789 and D66, 7.5 cm circular ivory with 8 cm frame. Preserve attributed Boquet and former Filleul.')
note([367,485], 'Before-date lower bound stays unknown; upper-bound evidence is pre-1971. Do not manufacture a first year from the maker lifespan or the historical model.')
note([368], 'D2929 is a woman lying on a bed, 25 x 35.3 cm blue-paper chalk, not the 26.2 x 37 cm mermaid drawing; Louvre 24752 remains related design, not this Mayor-marked sheet.')
note([369], 'Champaigne D17 is a male portrait, not the presumed female singer on 17 x 13 cm ivory. A museum-local D17 collision does not identify these objects.')
note([372], 'Capet J178 is mother-and-child gouache 45 x 34 cm. Gerard DE26 canvas 64 x 53, Martin canvas 46 x 38.3 and Fragonard wood oil 16.4 x 12 differ in physical support and composition.')
note([376,487], 'Leveque J794 is a 7.8 cm circular enamel/copper library portrait; Daniel J772 is oval ivory 5.5 x 4.2 with memorial hair reverse, while J785 is 4.2 x 3.7 enamel with blue coat, gold vest and feathered hat. They are distinct described compositions.')
note([377,454], 'Debucourt J166 landscape-format 23.5 x 30 cm gouache and Mallet J176 portrait-format 29 x 21.8 cm gouache are separately catalogued fashion-shop compositions. The related Freudeberg ribbon seller is not asserted as their identity; fresh expanded searches return no existing exact source object.')
note([378,410], 'Shared former F21 is not a global identity: J209 is the signed December1761 old-woman bust, 25 x 18 x 11.5 cm; J258 is Hercules and Alceste, 33.5 x 17 x 19 cm. Ward F21 depicts a temple tank. Different sculpture subjects and physical sizes resolve the historical number overlap.')
note([379], 'Other 2006.1 objects depict Barret Stornoway and Gumery Yport cliff oil 815 x 605 mm; neither is the 1787 Deseine 32 cm plaster Love/Fidelity group.')
note([388], 'Millet MTH2006.0.208 is oil on wood 39 x 25.5 cm; Topham F36 depicts Goldsmith. Neither is the 28 cm Cupid terracotta.')
note([389], 'The source explicitly calls J21 a nineteenth-century pastiche, 57.5 x 45.5 cm, after Colson CA252 93 x 73 cm dated1759. Boucher J10 is a large multi-figure Diana hunting scene; Bilcoq J4 is oil on wood19.2 x16. Other Repos oils have different measured formats, and the Dufresne and Picasso objects are prints. Preserve the copy date, not1759.')
note([396], 'Eisen DE1004 is graphite10.7 x7 cm; J165 is watercolor/ink19.5 x13 cm after a Fragonard design. The model and copy are not merged.')
note([397], 'J731 is a 7.3 cm circular ivory. Hillner1993.4 is a 4.7 x5.9 cm rectangular portrait; Bourgeois J717 is6.8 x5.6 cm ivory, and Greuze/Letellier82.2087 is a26.3 x17.4 cm print. Native rejection of the Fragonard sitter identification is retained.')
note([401], '1988.7 also denotes an ancient4 x2.3 cm ivory cosmetic spoon and Macomber1902 Night and Sleep canvas76.2 x63.2 cm, not the40.8 x32.5 cm Pierrot copy purchased in1988.')
note([404], 'J88 is the54.5 x46.5 cm oval Flavacourt Silence copy. Nattier J86 Boudrey/Sainte-Croix and2933 Dreux-Breze have separately identified sitters and measured canvases40 x32.5 and73 x59.5 cm.')
note([407], 'Granet1990.3 is a cardinal in a cloister,19.5 x26 cm pen/wash; Henner JJHD432 four hands measure21.2 x26.6 cm. Candidate is12.5 x15.2 cm four-hand black/white chalk study. No guessed restoration or cropped identity.')
note([408], 'Molin M678 oil91.5 x73.5 cm and Eisen10.7 x7 cm graphite are not the46.5 x56 cm Pater-derived canvas. The1733 engraving is model evidence, not this copy manufacture year.')
note([411], 'Bernay Vasse-attributed866.1.333 is a20 cm bust plus11 cm socle; J259 is a56 cm full Bacchus child. Different formats/scale resolve the apparent name/title match.')
note([413], 'J757 is22.5 x18 cm ivory after Vigee-Lebrun, not the76 x63 cm Marseille107 oil model or large Versailles oil portraits. Other captured miniatures are much smaller and have distinct subjects/signatures.')
note([414], 'Native circa1900 manufacture takes precedence over the forged Voiart1787 signature; source dates are retained, not silently rewritten to an eighteenth-century model.')
note([418,491], 'J255 Apollo and J256 Venus/Cupid are distinct33 cm marble groups with gilded bronze mounts and different compositions. All additional same-title comparators are oils, graphite/paper studies or prints; their domain, support and measurements differ physically. Former German/French/Coustou labels are retained as former, not collaborators.')
note([420,493], 'Shared oldD73 belongs to different museum objects: J728 presumed Rosalie girl7.2 x6 cm and J729 boy6.9 x5.2 cm. Different sex/composition, physical dimensions and current native inventories establish separate miniatures. Chicago1965.454 is a33.1 x40.4 cm mother-reading group wash, not either ivory.')
note([421], 'J222 is a32 cm marble girl with doves. Raucourt J697 is8 x7 cm ivory; all generic Summer matches are paintings, paper drawings or prints. Their literal domains, materials and sizes provide physical distinction independent of date.')
note([423,424,476], 'J56 workshop oil canvas16.5 x25 differs from Giacomo brass13 x18. J60 oil on paper12.4 x22.5, J51 Venetian copy on wood19.5 x33, J54 canvas34 x29 and Robert J99 canvas60.5 x73 have separately described ruin compositions and supports. Met1972.118.255 is an ink wash24.9 x46.9. Preserve workshop/model/former roles.')
note([428], 'Houdon signed1774 marble50.7 x21.5 x29 cm is distinct from the documented Gotha1769 plaster and Hermitage1775 marble versions. Generic Head of Woman candidates are drawings, prints or paintings; the only additional sculpture under date-only triage is Ecouen CL11635A, a36 x16 cm carved wooden relief. No date difference alone is used to separate sculptures.')
note([429], '1989.2 also names a42.1 cm medieval stoneware ewer. Hue-attributed19.5 x27.5 cm watercolor purchased27November1989 is materially and compositionally different.')
note([431], 'Use native Unknown executor/signature illegible, after Boilly; narrative possibility of Boilly himself is unconfirmed. Circa1840 copy after reversed1826 lithograph is not the1822 model canvas.')
note([434,495], 'J117 Toilette and J116 Bain are distinct Jollain compositions on25.5 x20.5 cm copper. The native signed counterpart and different subjects support separate objects. Other Bath/Toilette records are prints/drawings, larger canvases, wood/cardboard oils or Beau/Porquier faience, with literal physical distinctions. Preserve national malformed dates of comparators without repairing them.')
note([436], '1995.2 Pether/Wright Alchemist is a64.6 x50.7 cm mezzotint sheet, not the21.1 x16.3 cm original twelve-putti ink wash.')
note([438], '1991.4 medieval silk/gold brocade109.8 x38.5 cm is unrelated to the14 x20.3 cm ink-wash lovers drawing.')
note([441], 'J774 is8.8 x7 cm oval ivory with copper-ribbon frame and D110 mark; Raffort D110 is14.3 x21 cm bridge watercolor. Do not equate G.-E.Lami with Eugene Lami.')
note([443], 'J232 is39 x29 x21 cm marble, not Lemoyne painted oval58.2 x47.5, Lassus J7456.4 cm ivory, Bruegel/Baudouin oils or Greuze J42 canvas. Earlier LeLorrain stylistic bust comparisons remain different documented versions.')
note([445,473], 'Favier1988.5 is117 x89 cm oil Ernest Cognacq; selected1928.215 is58.3 cm marble bust and1983.1 is1934 wood engraving after Besnard. Renoir1983.1 oil studies45.8 x39 cm are a separate museum-number collision. Sculpture acquisition mode remains unknown.')
note([447], 'Picasso MPA1946.2.4 is a65.6 x50.5 cm drawing; Lemire J226 is signed1785 terracotta29 x17 x12 on stone.')
note([448], 'Saxe J227 is39 x38 x27 cm terracotta; LaTour D89.48 is pastel65.5 x54.2. Former F16 also matches Raja Chandu Lal and Hardy Sunday Afternoon compositions. They are not the named French marshal sculpture.')
note([450], 'Oligny presumed sitter J233 is30 cm terracotta. Generic female busts are drawings, paintings, prints, Drivier bronze44.5 cm, or Ecouen wax medallions6/9 cm and wooden relief38 x20 cm. The source formats/materials resolve the date-triage cases without changing their dates.')
note([452,453], 'Mallet Bouquet gouache28.8 x21.5 and Nurse Visit ink/watercolor24.8 x31.7 retain distinct source compositions. Segonzac/Daumier exact-title hits are prints. Related Bouquetiere/Convalescente titles supply no identical existing native object in expanded search.')
note([455,456], 'Michel seesaw terracotta20.2 x28.4 x4 and shepherdess13 x19.2 x8.6 differ from Lignier Bascule canvases, Watteau prints/DPG156 oil, Stapleaux dog canvas and Beguine plaster66 cm. Sources distinguish Pierre-Joseph and Sigisbert-Francois Michel, not a shared surname authority.')
note([459,460], 'Louis-Gabriel Moreau the elder is distinct from Gustave Moreau. The latter city/river studies and Chimeres have different compositions, media and nineteenth-century museum records. J180 is21.5 x32.5 cm gouache; J199bis signed bathers watercolor38.4 x50.4 differs from Lancret oil66 x55, Huet etching and later Grésy context. No surname-only merge.')
note([466], 'Pigalle versus Attiret are alternative disputed attributions. The Getty sister busts are marble comparators, not this47 cm terracotta; no collaboration or secure autograph is invented.')
note([468], 'Gautier-Dagoty MV7853 is86 x68 cm oil; J110 is60 x49 with a presumed sitter and former Roslin attribution. The depicted sketch is not separately counted.')
note([469], 'J734 ivory4.7 x3.7 has its own native D7/Hall reverse history and Romany attribution; Sicard J755 is signed Sicardi1781 and separately framed4.6 x3.6. Distinction relies on native inscriptions/framing and object records, not the1 mm difference. D7 Saint Ursula is95 cm wood relief.')
note([471], 'Russell J127 is signed1789 pastel60 x45; Bonnard1914 and Heilbuth objects are oils. John Russell remains distinct from John Peter Russell.')
note([472,475,482,484], 'Native source narratives identify these as separate measured physical marble copies/versions. Antique models, different dated/signed versions and larger plaster casts are not merged or counted as additional holdings. Preserve manufacture uncertainty and former maker roles. No access-hold source was retried.')
note([479,501,509], 'Three independently inventoried Watteau de Lille sheets bought11March1988 depict parasols, spectators and an old woman in profile. Shared acquisition is not a single drawing. Cole oil, Shunman silk and Trumbull oil inventory coincidences differ in subject/support/scale. Antoine Watteau D2605 is sanguine15.7 x21.7, not the14.4 x18.8 black-chalk spectators. Francois/Louis-Joseph former role is explicit.')
note([480], 'J189 two women viewed from behind is one13.2 x12 cm sheet. Native1967 theft concerns related J185 single woman, not this object; no display/theft status inferred.')
note([481,486,487,503,504,505], 'Native enamel descriptions distinguish the6.9 cm seated blue-jacket man with paper/lake,4.6 x4 black/red magistrate,4.2 x3.7 bluecoat/feathered hat,5.9 cm peasant profile with basket,4.7 x4 browncoat/beige-vest man, and3.9 x4 historic-costume woman. Leveque7.8 cm library circle, Kanz5.8 cm signed female circle, Hillner ivory, large oils and Beeh paper drawings are different physical works.')
note([483], 'Candidate is expressly nineteenth-century black chalk35.8 x24.5 cm; correct earlier supplemental shorthand saying eighteenth-century. Other1993.1 objects are an ancient bird vessel and Quadri Carpet of Contemplation, unrelated subjects/physical objects; sparse comparator date stays unknown.')
note([492], 'NGA1960.6.12 is oil on canvas oval53.9 x65.1 cm, not candidate33.5 x41.5 cm gouache/wash. Met1996.328.2 is a Satyr Family etching. Related inventory match documents a model, not duplicate sheet.')
note([496], 'Poussin DE222 is20 x19.5 cm pen/wash, not Delarue signed1760 frieze28.5 x80.7. Nancy Carline1986.1 VE Night1946 is an unrelated composition.')
note([497], 'Hervier J160 is a19th-century37 x24 cm Caen market wood panel. Lavreince25 x20.5 cm gouache Petit Conseil differs in composition/decor from the Stockholm watercolor prototype and companion J159.')
note([502], 'Candidate22.2 x21.1 cm single seated-man chalk sheet differs from Watteau reclining-man/seated-woman24.1 x35.9 and female24 x13.8 drawings. Other Seated Man records have different modern makers, subjects and physical media; sparse Hopper/Lipchitz chronology stays unverified.')
note([506], 'Bilcoq J4 is19.2 x16 cm oil on wood; J39 is46.5 x36 cm canvas after Greuze. Other generic readers are separately documented nineteenth/twentieth-century compositions by Renoir, Henner, Fantin-Latour, Blanchard, Espagnat and others with different formats/supports. No title-only match to the Greuze-derived copy.')
note([508], 'Native J17231 x40 cm gouache is a replica with decorative-frieze differences from Marmottan1790inv42 and Cassel versions. It is not the depicted Cupid/Psyche sculpture. Expanded title/source searches yielded no identical physical object.')
