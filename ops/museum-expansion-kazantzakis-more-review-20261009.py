"""Physical-object review of selected1940–1941 theatre designs, wave113."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-kazantzakis-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
NOTES={
1:'Leon costume: dark tailcoat, white shirt, large bow tie and pale narrow trousers, with a dark fabric sample.',
2:'Eftychia costume: patterned long dress, apron, blue shawl and bonnet; a small bonnet sketch belongs to the same sheet.',
3:'Charles costume: checked long coat with matching cape, boots and hat, with dark fabric samples.',
4:'Emma costume: long purple dress, bonnet and muff, with a purple fabric sample. The drawing has a different face, bonnet and skirt construction from the photocopy35037; that other record reports its own original at ELIA. No ELIA holding is inferred for this distinct study.',
5:'Madame Lefrancois costume: blue long dress and patterned apron, with a multicoloured fabric sample.',
6:'Emma costume: black long dress with a broad skirt, holding a blue hat.',
7:'Rodolphe costume: blue tailcoat, bow tie and pale trousers, with a blue-green fabric sample.',
8:'Leon costume: fitted coat, V-shaped waistcoat and narrow trousers; one mounted figure study.',
9:'Hippolyte costume: loose shirt and trousers with a straw hat; the rural-role interpretation remains tentative.',
10:'Homais costume: brown double-breasted coat, pale trousers and patterned cap.',
11:'Abbe costume: a long dark clerical robe, holding a broad-brimmed hat.',
12:'Rodolphe costume: yellow quilted fitted coat and pale blue trousers. The head, leg positions and coat drawing differ from the photocopy35036,whose own original is reported at ELIA. These different versions are not assigned the same physical identity.',
13:'Charles costume: blue tailcoat, patterned waistcoat, bow tie and boldly checked trousers.',
14:'Justin costume: brown tailcoat, checked short trousers and red-and-white striped stockings; distinct from the more finished white-ground35072 version.',
16:'Emma costume: blue fitted jacket and matching long skirt, with supplementary bodice sketches and a fabric sample. The photocopy mentioned inside the folder is not counted separately.',
17:'Emma costume: white dotted dress with a broad ruffled skirt and a blue fabric sample.',
18:'Leon costume: double-breasted blue tailcoat, pale trousers and scarf. The associated folder photocopy is not another artwork.',
19:'Charles costume: dark tailcoat and checked trousers, with fabric sample. A rough reverse sketch stays with this sheet.',
20:'Gerard costume: loose dark shirt and trousers, carrying a broad-brimmed hat.',
21:'Bonnet costume: green coat, pale shirt and dark trousers, with cap and a fabric sample.',
22:'Lheureux costume: coat draped over the shoulders, fitted inner jacket and narrow trousers. Distinct from the white-ground35071 study with a different coat silhouette and pose.',
23:'Black visiting dress with fitted diagonal bodice decoration and a broad-brimmed hat. Textile names in costume instructions do not establish the drawing medium.',
24:'Emma costume: layered yellow dress, floral decorations and long purple gloves.',
26:'Madame Caron costume: long blue dress with contrasting sleeves and bonnet. An attached coloured detail study stays with the principal sheet.',
27:'Maid costume: long dress, apron and bonnet, carrying a round box; a fabric sample is attached.',
29:'Emma costume: pale nightdress with abundant ruffles and ribbons, with fabric sample.',
30:'Emma costume: long purple layered dress with hat, gloves and bag, with a blue fabric sample.',
31:'Bonnet uniform: red tailcoat with gold epaulettes, helmet and white trousers; accessory sketches stay with the sheet.',
32:'Eftychia house dress: striped long skirt, short puffed sleeves and long white apron. The back-detail sketch is part of the same sheet.',
34:'Emma costume: finished green layered dress, with a supplementary bodice sketch. The source relates another coloured version toF032a/030. Existing34229 and34224 are separately drawn unfinished Popolaros1943 studies; their differing dates and play labels remain unchanged and are not reconciled by assuming one object.',
35:'Male costume: dark tailcoat, patterned waistcoat and striped trousers, holding a paper. Different head, hand and leg positions distinguish it from the photocopy35035.',
36:'Emma costume: long grey-blue dress with puffed shoulders, fitted cuffs and elaborate lace collar, with fabric sample.',
37:'One sheet of coloured scenery elevations and details with handwritten construction calculations; the several panels count once.',
38:'One sheet of red interior scenery studies and a lower architectural elevation, with a faint central pencil sketch.',
39:'One sheet containing several coloured scenery elevations and door or window details, with construction notes.',
40:'Station waiting-area scenery with ticket office and shop fronts, with a single figure; distinct from the fuller multi-figure version35553.',
41:'Scenery of an outdoor glazed atrium with plants and two figures beneath a theatrical curtain.',
42:'Interior scenery with striped walls, doors, staircase and period furniture, with two figures.',
43:'Ship-deck scenery with doorways, chairs and a table against a clouded sky; one mounted design.',
44:'Station waiting-area scenery with shop fronts and several travellers and staff; a separate painted composition from35548.',
45:'Sitting-room scenery with central depth, doors and period decoration, populated by three figures.',
46:'Monsieur Perrichon costume: fitted coat with broad purple stripes and patterned trousers.',
47:'Majoren costume: dark fitted long coat, narrow trousers and a tightly tied scarf.',
48:'Giannis costume: grey fitted jacket and narrow trousers, carrying a duster.',
49:'Henriella costume: blue checked long dress, broad white collar and straw hat. Its checked pattern and drawn details differ from the striped version35101.',
50:'Male costume: long black cape with blue lining, checked trousers and dark hat; one white-ground study.',
51:'Armand costume: blue coat, checked dark trousers, red neck scarf and tall hat.',
52:'Monsieur Perrichon second costume: checked coat and cape with brimmed hat, a separate study from35089 with a bonnet or head scarf and attached samples.',
53:'Monsieur Perrichon second costume: checked coat and cape with head covering, supplementary head profile and green fabric samples. Different drawn outlines distinguish it from35085.',
54:'Henriella costume: striped blue long dress, broad collar and straw hat, with a shoe detail. Distinct from the checked version35092.',
55:'Lheureux costume on a white ground: blue outer coat, dark inner jacket and narrow trousers, with performer and play notes. Distinct from35054.',
56:'Female travelling costume with fur-trimmed outer clothing, gloves and muff, drawn on a white ground beneath an attached transparent cover.',
57:'Daniel costume: dark brown tailcoat, bright waistcoat, pale striped trousers and tall hat, carrying a cane.',
58:'Madame Perrichon costume: layered long dress, broad pale collar and bonnet with ruffles.',
59:'Monsieur Perrichon costume: red-brown coat, yellow waistcoat and green checked trousers, holding a tall hat. Distinct drawing from35083: different leg and arm positions,face,coat contours and annotations.',
60:'Majoren costume: dark tailcoat and narrow trousers, holding a hat; supplementary garment detail on the sheet.',
61:'Bookseller costume: long green checked dress with a high pale collar.',
62:'Madame Perrichon costume: patterned skirt, fur-trimmed brown coat and hat, with a muff, on a white ground.',
63:'Daniel costume: brown coat, pale blue trousers and scarf, with construction notes. Different pose and headwear from35098.',
64:'Porter costume: dark loose shirt and trousers, beside luggage and trolley details. Reverse sketches stay with the same support.',
65:'Innkeeper costume: striped waistcoat and dark trousers, with a green fabric sample.',
66:'Monsieur Perrichon costume: red-brown coat, yellow waistcoat and green trousers; a separate drawing with different hand,leg and face contours from35079,plus additional written instructions.',
67:'Daniel costume: brown checked coat, pale blue trousers and a narrow-brimmed hat; a different pose from35094.',
68:'Justin costume: brown tailcoat and checked short trousers on a white ground. The more finished contours and leg positions differ from35053.',
69:'Female nightdress costume with ruffles and waist ribbon, with a pale fabric sample. Distinct silhouette and annotations from35066.',
70:'Armand costume: blue fitted coat and pale trousers, with extensive textile and construction instructions. Those textile names describe the costume rather than the artwork medium.',
71:'Sweet-seller costume: pink striped long dress with fitted lower sleeves.',
72:'Madame Perrichon visiting costume: long dress, lace shawl and decorated hat, with a sleeve-detail sketch. Source costume fabric terms remain separate from drawing medium.',
73:'Daniel costume: fitted tailcoat, waistcoat and striped trousers, with several fabric samples.',
74:'Joseph costume: dark fitted coat, narrow trousers and riding boots, with a dark fabric sample.',
75:'Henriella costume: long dress decorated with many blue bows, with a supplementary dress detail.',
76:'Major uniform design with double-breasted coat, epaulettes and cap; accessory diagrams and instructions belong to one sheet.',
77:'Madame Homais costume: long dress with fitted bodice and blue bonnet, with a skirt-detail sketch.',
78:'Mounted drawing of a grand interior stage set with doors, piano and period decoration. The type field says costume but the description and image show scenery; the broader drawing classification avoids repeating the type error.',
79:'Mother costume in a dark blue variant on a separately mounted support. The catalogue calls it a differently coloured version off013/017. Shawl decoration,skirt contours and placement differ from original35033 and its explicitly photographic copy35032; retain it as one separate study.',
81:'Hotel-corridor scenery with numbered doors, chairs and two figures. The cut-paper proscenium and mounted design are one composite object,not separate artworks.',
82:'Mother costume with fringed shawl, headscarf, long skirt and apron on blue-grey paper, with performer and play inscriptions. The separately catalogued photograph35032 is excluded.',
83:'Scenery-detail study with an orange area, pencil marks and applied three-dimensional elements. The source explicitly says mixed technique; physical type remains unknown rather than assuming a flat drawing.',
84:'Preliminary interior scenery with layered wall flats and a double door. Abstract reverse sketches remain part of the same sheet.',
85:'Preliminary pink-walled domestic interior scenery with doors, furniture and depth.',
86:'Small dark-ground scenery study of electrical pylons in perspective and an outlined cloud. No numerical dimensions are inferred.',
87:'Preliminary green interior scenery with tall door openings and furnishings; marginal sketches,calculations and reverse marks remain on one support.',
88:'Preliminary dining-room scenery with a long central table and receding wall flats. The reverse sketch is part of this object.',
89:'Preliminary blue interior scenery with central door, desk, bookcase and chairs,with colour trials and notes.',
90:'Preliminary bedroom scenery with central bed, blue spotted decoration, doors and small furniture.',
91:'Domestic interior scenery with doors, a central recess, furniture and two female figures. The separately cut proscenium belongs to the composite object.',
92:'Small blue-ground exterior scenery of tents beneath a large tree.',
93:'Bedroom scenery with curtained recess and side doors. Two overlaid painted pieces and their mounts are one documented composite design.',
94:'Finale curtain design bearing the word End and several figures; the separate cut-paper proscenium stays with the one mounted design.',
95:'Small blue-ground scenery of buildings amid trees and foliage.',
96:'Hotel-corridor scenery with doors numbered18–21,shoes outside two doors and a female figure; one composite mounted design.',
97:'Small blue-ground scenery with architectural fragments and a full moon.',
98:'Curtain design with a central caption naming the performers; one mounted composite design.',
99:'Small blue-ground scenery of a row of differently shaped houses.',
100:'Small dark-ground scenery with a tall decorative central opening and chairs.',
101:'Train-carriage scenery shown partly in section with berths,seating and two male figures; one mounted composite design.',
102:'Small dark-ground scenery with heraldic panels,steps,table and chairs. A pencil sketch on the reverse does not form another artwork.',
103:'Small dark-ground scenery with a Panorama sign and pale railings.',
104:'Dining-room scenery with tableware,decorated screens,birds and two female figures; one mounted composite design.',
105:'Curtain design with a map of the Vienna-to-Budapest journey; one mounted composite design.',
106:'Hat-shop interior scenery with desks,shelving and doorways, mounted on dark card.',
107:'Small blue-ground scenery with a building and a wooden cart under a striped awning.',
108:'One diptych sheet with two interior stage designs,fabric samples and colour instructions. Its upper and lower panels count as one artwork.',
109:'Interior scenery with two doors, a sitting area,flowers,telephone and two figures; one mounted composite design.',
110:'Small blue-ground scenery with a grocery or greengrocery storefront and striped awning.'}
HOLDS={15:'Explicit photocopy,not a securely dated original artwork. Related costume35044 is a different drawn version. Do not infer photocopy creation in1940 from the depicted production.',25:'Explicit photocopy whose source says the original is at ELIA. Related35057 is visually a different study; no original ELIA artwork is assigned to this museum. Copy date unknown.',33:'Explicit photocopy whose source says the original is at ELIA. Related35056 is visually a different study; no original ELIA artwork is assigned to this museum. Copy date unknown.',80:'Explicit photograph of original costume designf013/017,visually matching35033. Exclude duplicate reproduction;1941production date does not independently date the photograph.',28:'Thumbnail depicts a theatrical jester-like figure with breeches and plumed hat,while the description labels Emma17 for MadameBovary. Source object/image identity is unresolved; no artwork added until this mismatch is reconciled.'}
TITLE_FIXES={1:'Η Κυρία Μποβαρύ',91:'Το ταξίδι του γάμου'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows();out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];assert not c['source_hits'];assert d['metadata_state']=='eligible_metadata_candidate'
  if n in HOLDS:state='reproduction_review_hold'if n in {15,25,33,80}else 'source_identity_review_hold';note=HOLDS[n]
  else:
   assert n in NOTES,n;state='approved_review_only_addition';f['work_type']='unknown'if n==83 else 'drawing';context=' The original creator field says unknown; EKT semantic enrichment names Giorgos Anemoyannis. This attribution discrepancy remains unresolved.'
   if n in TITLE_FIXES:
    assert '\ufffd'in f['title'];f['source_title_literal']=f['title'];f['title']=TITLE_FIXES[n];f['titles'].append(f['title']);f['title_editorial_note']='Two replacement characters in the original title field corrected using the clean title explicitly repeated in the same object description. The unmodified title and raw HTML remain in source evidence.';context+=' '+f['title_editorial_note']
   if n==83:f['medium']='μικτή τεχνική (mixed technique; explicitly stated by the source)'
   f['description_md']=NOTES[n]+context;note=NOTES[n]+context+' One documented physical artwork. Separate drawings of the same costume are distinguished by painted contours,pose,support and source description. Reverse sketches,attached samples,cut-paper proscenia and multiple panels are not counted separately. No invented accessions,dimensions or materials.'
  d.update(state=state,institution_id=s.IID,basis=note,confidence=.95 if state=='approved_review_only_addition'else None,comparison_assessment='All128 bounded existing records and149citations reviewed.110 available thumbnails inspected onfive sheets; related versions enlarged individually. Exact source identifiers andURLs have no prior hits. See visual assessment and protected comparator snapshot.',limitation='Editorial confidence,not a calibrated probability. Museum collection holding only; no current display,venue,custody or ownership assertion. No artist-authority merge,publication or image attachment. Actual NC/ND image labels retained.');out.append(d)
 assert len([v for v in out if v['state']=='approved_review_only_addition'])==105
 return out
if __name__=='__main__':
 old=RUN.parent/'kazantzakis-20261009'/'institution-reconciliation-001.json';inst=m.load(old);inst.update(at=m.now(),inherited_reconciliation_reference=ref(old),decision=inst['decision']+' New110 object pages retain the same museum provider; no new institution is created.');m.save(RUN/'institution-reconciliation-001.json',inst)
 ds=build();visual=m.load(RUN/'visual-reference-captures-001.json');assert len(visual['rows'])==110 and all(v['receipt']['available']for v in visual['rows']);observations=[dict(number=v['number'],source_id=v['source_id'],image_available=True,observation=NOTES.get(v['number'],HOLDS.get(v['number'])),image_path=v['receipt']['path'],sha256=v['receipt']['sha256'])for v in visual['rows']]
 m.save(RUN/'visual-assessment-001.json',dict(at=m.now(),reference=ref(RUN/'visual-reference-captures-001.json'),contact_sheets_seen=visual['contact_sheets'],images_seen=110,unavailable=[],individual_enlargements_seen=[4,12,15,25,33,35,59,66,79,80,82,83],observations=observations,reviewer_reference=ref(Path(__file__).resolve()),policy='All110selected thumbnails inspected. No identical bytes; manual contour/version review distinguishes related originals fromcopies. Four reproduction records andone image-description mismatch remain held.105physical artworks selected. All images are internal identity references only,no production assets.'))
 deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-selection-001.json.gz','subject-comparators-001.json.gz','visual-assessment-001.json','visual-reference-captures-001.json','institution-reconciliation-001.json']]
 m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='105new review artworks:104drawings andone mixed-technique scenery detail with unknown physical type. Four reproductions andone image/description mismatch held. Source title corruption corrected in2records from clean text onthe same objectpage; literals preserved. Explicit1940–1941objectdates,unknown creators,and source/enrichment discrepancy retained. No inferred artist identities,materials,accessions or dates. Local catalogue read-only.'));print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)),types=dict(collections.Counter(v['facts']['work_type']for v in ds if v['state']=='approved_review_only_addition')))),flush=True)
