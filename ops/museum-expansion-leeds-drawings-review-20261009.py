"""Selected physical-sheet review; native essay qualifications and exact versions retained."""
import collections,copy,gzip,hashlib,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-leeds-drawings-common-20261009.py');f=module('f','museum-expansion-leeds-drawings-facts-20261009.py');i=module('i','museum-expansion-leeds-drawings-identity-v2-20261009.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
HELD={16:'Two drawings on one mount: only upper drawing securely assigned1828; lower drawing date and whole-object authorship remain unresolved. Retain for editorial whole-object review.',62:'Recto church dated1811or1812 in the essay; verso boat explicitly may be later and remains undated. Whole-sheet creation scope not reduced to the recto date.'}
OVERRIDES={
8:'John Sell Cotman; possibly after James Stark',19:'John Sell Cotman; possibly after Nicolas Poussin',26:'John Sell Cotman, after William Havell',27:'Attributed to John Joseph Cotman; school of John Sell Cotman',29:'John Joseph Cotman; associated with John Sell Cotman',31:'Possibly Miles Edmund Cotman; formerly attributed to John Sell Cotman',33:'John Sell Cotman, after Samuel John Stump',41:'John Sell Cotman; possibly after Nicolas Poussin',51:'John Sell Cotman, after Joshua Cristall',68:'Possibly John Joseph Cotman; formerly attributed to John Sell Cotman',71:'John Sell Cotman; possibly after Peter La Cave',78:'John Sell Cotman or Miles Edmund Cotman (attribution uncertain)',82:'John Sell Cotman; associated with John Joseph Cotman',85:'Miles Edmund Cotman; associated with John Sell Cotman',86:'John Sell Cotman; possibly after Peter La Cave',91:'Attributed to John Sell Cotman (doubtful)',96:'Possibly Miles Edmund Cotman or a member of the Dawson Turner family; formerly attributed to John Sell Cotman',97:'John Sell Cotman, after Dirk Stoop',99:'Studio of John Sell Cotman; possibly John Joseph Cotman',102:'Possibly Miles Edmund Cotman; formerly attributed to John Sell Cotman'}
# All104 catalogue essays read; historic estimates, associated artists and models
# are kept apart from current object attribution, date and physical identity.
NOTE_TEXT='''1|Current curator retains Cotman1803 despite Kitson suggestion of a Rhodes copy; York tower versions at Whitworth/Ashmolean and Munn source sketch are distinct. Drop Gate oil is another composition.
2|Native Attributed to Miles Edmund retained; essay also considers Cooke or Stanfield. Hepworth gift to Leeds1928 establishes holding despite blank credit. Foreshortened open boat with worker and lifting gear differs from timber yawl3.
3|Attributed to Miles Edmund retained; possible John Sell participation remains uncertain. Bilborough bequest1925 establishes holding despite blank credit. Beached timber carrier differs from Yale French Fishing Boat off the Shears1846,14.2x16.2cm,B1977.14.11309.
4|Kirkstall chapter house, gallery purchase1995. Munn possibly depicted, not maker. Different architectural location from Turner undercroft and other west-front prints.
5|One diligence drawing with slight pole study on reverse; source1818 creation follows Normandy tour, not acquisition.
6|Tree-covered ridge composition differs from prior pupil trunks0593 and later watercolours; one sheet.
7|Dock-tailed pointer,c1820, differs from seated collared dog43,c1804; Saftleven Dog is another maker and century.
8|Possibly after James Stark Beach Scene1816; not a Stark original. Leger1920 Two Figures and Dog has different maker and medium.
9|Two boats drawingc1828 on reverse of part of an1812 Middleton etching: print publication is not drawing creation; count one sheet.
10|Man in punt with luggers on reverse; one sheet, not two independent works.
11|Lion-sur-Mer southeast view1820 differs from south view66 despite shared former Fontaine le Henri title.
12|Montivilliers wagonc1817; proposed27June date conjectural. Reverse horse studies historically recorded but hidden by current mount, not newly visually verified.
13|Two horses and cartc1818; separate accessioned paper.
14|Wading man studyc1810; reverse marks belong to same sheet.
15|Seated manc1820: Rembrandt influence does not establish a copy or Rembrandt authorship.
16|Two sheets, upper nautical studies and lower capstan; table repetitions do not establish joint authorship. Only upper assigned1828; held for group date and maker review.
17|Tracing horse and riderc1808 differs from British Museum watercolour1902,0514.41.a and from source print; watermark evidence undermines1806 exhibition equation.
18|Small lugsail ferryc1825 is a separately accessioned study.
19|Two classical women, possibly after Poussin. Kitson inscription reading1823 explicitly wants verification: date qualified rather than asserted exact; different from single standing male figure41.
20|Sawmill and trees. Possible pupil inscription on reverse does not establish pupil authorship of the drawing.
21|Three-masted lugger under repairc1815; verso part of Middleton etching1812 does not date the later drawing.
22|Normandy woman0109a: individually catalogued separated paper, one of eight pieces later mounted together. No parent or other seven drawings added.
23|Tall trees and bridge on oil-soaked tracing paperc1823, not an oil painting; transfer drawing distinct from1838 Liber Studiorum print.
24|River windmill, quay and cranesc1831:1828 paper watermark is a lower bound, not an exact creation date.
25|Trees by lakec1810 with ship on verso; one sheet, uncertain place retained.
26|Drawing after Havell, native1800-1842 range retained. Possible1815 exhibition memorandum does not silently narrow the creation range or become Havell original.
27|Wading manc1850 attributed to John Joseph, school of John Sell; not an unqualified father work.
28|Gaff ketch or Dutch galliotc1820; vessel study distinct from other riggings and views.
29|Man at workc1850 attributed John Joseph; associated John Sell is not a second joint author.
30|Study of a Tree0592c1803: single tree with buildings, different from prior0593 unidentified-pupil twisting trunks. Exact-title West lithographs, Savery, Blau, de Gheyn and Richmond have different makers/versions. Existing two West rows with inventory1947.7.127 remain a separate duplicate-research issue, not altered.
31|Yacht with flag and pennantc1830. Title and essay suggest Miles Edmund and reject secure John Sell authorship; retain uncertainty.
32|Single dipping-lug fishing boat in choppy waterc1820; separate sheet and rig.
33|Cotman copy after Samuel John Stump River Kennet1815, not Stump original. NGA1995.52.30 Wooded Landscape probably1841 is chalk and white,28.7x37.3cm, different subject/material/format.
34|Three-masted ship off Yarmouth inscribed2May1816; own dated drawing, not generic ship title match.
35|Four maritime sketches, including a beacon, on one sheetc1828; not four artwork records.
36|Calm harbourc1830, possibly after an unknown picture; Cuyp/Van de Velde influence not certain copy assignment. Exact Kitson1949 credit supports holding despite abbreviated provenance ending1926.
37|Horse and cart signed JJC and dated31March1870, John Joseph. Associated relatives do not establish joint authorship; creator death dates do not replace artwork date.
38|Horse,rider,cow tracingc1808 and separate inscribed scrap of uncertain significance form one catalogue item; no invented second artwork. Berchem/du Jardin model only possible.
39|Two gaff yawls with tan and black mizzen sailsc1820 differ from beached timber carrier3 and Yale1846 French Fishing Boat off the Shears.
40|Women and children at marketc1821; individual drawing, not the other market composition103.
41|Single classical man with staffc1810, possibly after Poussin; historic1807 estimate retained as evidence. Different from two women19, false shared alias Nicolas Poussin does not merge objects.
42|Two horses and donkeyc1808; physical sheet separate from related tracings and British Museum watercolour.
43|Seated collared dog on roughly cut paperc1804 differs from dock-tailed pointer7 and Saftleven seventeenth-century drawing.
44|Seated woman with straw hatc1804, possibly Brandsby; abbey/tower title collisions do not identify this figure sheet.
45|Goodrich solar arch inscribed4July1800, different from chapel or gateway views.
46|Single distant hatch-boatc1828 differs from Yale Miles Edmund Barge on Medway with Grampian and Dreadnaught,c1838,B1978.43.808,11.3x20.5cm,with named warships in background.
47|Single sprit barge with inset detailc1825, one paper rather than two artworks.
48|Rievaulx south transept from nave1803, graphite. Met2007.39 is watercolour and graphite,30.3x21cm; Cleveland1991.233 is1810 etching. Different medium,format and view/version, no merge. Met fresh metadata request429 retained as access hold; no successful fresh raw capture claimed.
49|Four figures on one paper stripc1817, related to Walsoken print; print use does not date every sketch exactly.
50|Cromer lighthousec1833 with reverse1812 South Gate etching/counterproof; print date and1867 landslip do not replace creation date.
51|Cotman after Joshua Cristall Fisher Boy1815. V&A model-version debate concerns source picture, not identity of this pencil copy.
52|Mother and child with jugc1810 used for1817 East Barsham etching; own drawing date retained.
53|Foliagec1810; reverse foliage recorded historically but currently hidden, not fresh visual confirmation.
54|Small beached rowing boat and windlassc1808, separate composition from later vessels.
55|Collier brig offloadingc1820; Master Gurney memorandum on reverse has uncertain hand/subject, not an extra artwork or definite maker.
56|Three boats on Yarmouth beachc1831; similar-sized pocketbook siblings0177/0196 have different IDs and compositions, not duplicates.
57|Wherry, warehouses and still riverc1828; one composition.
58|Three goats on one sheetc1808 with tobacco writing on verso; count one artwork.
59|Half-timbered three-storey house side viewc1803 differs from tall four-storey street house60.
60|Tall four-storey house in a streetc1803 differs from three-storey side view59 despite tentative shared town.
61|Wooded hollowc1824: current curator retains Cotman despite Kitson pupil theory based on1841 Blofield. NGA chalk landscape1995.52.30 differs in medium,format and subject.
62|Gillingham church recto1811or1812, boat reverse may be later. Whole-sheet date held. Cley Church2013.340 and Treport etching2010.591 depict other churches/medium, not matches.
63|Winter pollard willows by stream at sunsetc1830; other Sunset titles are different makers and physical objects.
64|Gaff cutterc1828: essay self-reference to same0071 number as contiguous sheet is an unresolved catalogue cross-reference, not authority to invent a duplicate or join pieces.
65|Aspen grove and cottagec1825; current curator prefers earlier date to1841 comparison, nativecirca retained.
66|Lion-sur-Mer south view1820 with horses on verso; different angle and sheet from southeast view11 despite same former title.
67|Ferry with two puntsc1830, man and boy on reverse; one sheet.
68|Pollarded treec1830: title and essay suggest John Joseph and reject father's hand; qualified attribution supersedes unqualified table.
69|Five studies of girls on one paperc1818, not five records.
70|Horse with covered baggage cartc1818, separate from wagon93 and cart37.
71|Five donkeys on one sheet and traced two on reversec1804, possibly after Peter La Cave; not La Cave original or seven artwork records.
72|Three-masted lugger in fresh breezec1825, separate rig/composition from other selected boat studies.
73|Man at table and womanc1818, one physical sheet.
74|Gaff fishing boat and three-masted traderc1818, possibly after unknown picture; no definite model maker assigned.
75|Small lugsail boat with passengers0203a,c1828; one of six separate thumbnail papers on shared mount. Not the three-masted lugger0203b80 despite shared former Sailing Boat title.
76|Triangular dinghy at sunset0203f,c1828; distinct paper and subject on shared mount, no extra aggregate record.
77|Gaff barge and rowing boat detail0203e,c1828; one paper with detail, not two works.
78|Two-masted lateener with George flag0203d,c1829, trapezoid paper added to original five-piece mount. John Sell or Miles Edmund uncertain, not joint. Related0705 different sheet; generic group provenance does not prove every intermediate transfer of this later addition.
79|Small gaff boat from port bow0203c,c1828; separate thumbnail paper from other five mounted drawings.
80|Three-masted lugger on calm water0203b,c1828, not lugsail passenger boat0203a75 despite shared alias. No aggregate0203 record exists in scoped database.
81|Possible Whitlingham Lane drawingc1865 by John Joseph differs from prior1873 watercolour and Norwich oil. Cleveland traveller1991.22,1806,graphite/wash30.3x21cm is another view/format; NGA1841 chalk landscape is distinct.
82|Stream and treec1834 by John Sell, associated John Joseph comparative style only; double-page spread one object. Different from Cleveland1806 portrait-format traveller and NGA1841 chalk landscape.
83|Smack in heavy seac1824 resembles Turner Mouth of Humber but essay explicitly says not a copy; no after-Turner attribution.
84|Girl carrying childc1810, used in1811/1813 prints; own study date retained.
85|Hay barge at Millwallc1831 by Miles Edmund; father associated, not joint maker.1825 watermark is not drawing creation; inscribed26June.
86|Donkeyc1804, possibly after Peter La Cave; derivative relationship qualified.
87|Figures in pony trap and horsec1830 on one paper.
88|Spindly fishing man, possibly Dr Syntax,1800s subject but native1810-1824 range retained; not automatically Rowlandson original.
89|Four headdress studiesc1817; historical mount1818 preserved as evidence,current curator prefers first Normandy tour.
90|Brig in rough seac1825, study for or after unknown picture; no definite Turner model.
91|Four-wheeled hay wagon with oxenc1816: essay doubts link to Cotman and suggests old-master/Rubens-like style, possibly imitation or copy. Retain doubtful Cotman, no definitive Rubens maker or model.
92|Willow in wind inscribedDecember1822; inscription supports creation independently of acquisition.
93|Two-wheeled wagon pulled by oxen and horsec1820,0108a. Exact0552 concordance page43916 depicts standing man, not this wagon: generic group recataloguing warning does not establish a duplicate. Later-style suggestions remain evidence, no silent date rewrite.
94|Whole Rochester Castle ensemble1825,0617, distinct from0618 keep detail and0619 right-hand pendant.
95|Normandy lady, possibly nun,c1820; uncertain subject retained.
96|Porch with womanc1830: essay rejects John Sell, suggests Miles Edmund or Dawson Turner family. Turner Gothic Church oil N05536,c1797,mahogany is different work and medium.
97|Horse at trough tracing after Dirk Stoopc1808; watermark1808 distinguishes own drawing from1651 engraving and possibly misidentified1806 exhibition watercolour.
98|Two post windmillsc1809: historical1802 mount date rejected by curator. Distinct from later Cotman watercolours and works by Cuyp,Jacque,Gabriel.
99|Studio tree groupc1832, possibly John Joseph, Miles also considered. Exact Kitson1938 credit supports collection despite absent provenance section; maker remains qualified.
100|Dover harbour with boat and castlec1799,0007, differs from prior Dover caulking0010,140x156mm. Monro school/Turner/Girtin possibilities discussed but current curator retains Cotman and distinct separated paper identity.
101|Masts above Yarmouth quay wallc1811; separate composition from other boats.
102|Shippingc1828: essay suggests Miles Edmund; repeated table John Sell/Miles is not joint authorship. Turner Shipping oil on mahogany67.9x91.8cm, Duveneck1883 etching and Frank Laing B.H.1971-70 have different makers/media.
103|Normandy women at marketc1820 on advertisement printed1811; print date and printer biography do not date drawing or identify its maker.
104|Two views of one Hoy on one paperc1828, no background warships, differs from Yale Miles Edmund Medway bargec1838,B1978.43.808; one record.'''
NOTES={int(line.split('|',1)[0]):line.split('|',1)[1] for line in NOTE_TEXT.splitlines()};assert set(NOTES)==set(range(1,105))
def source_rows():return m.load(RUN/'selected-objects-001.json.gz')['rows']
def verified_raw(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def validate_sources(rows):
 assert len(rows)==104 and len({r['source_id'] for r in rows})==104
 for r in rows:
  verified_raw(r['capture']);assert r['index']['url']=='https://cotmania.org/works-of-art/'+r['source_id'];fs=r['parsed']['fields'];assert fs['Reference'].startswith('LEEAG.');assert fs.get('Credit Line') or (r['number'] in [2,3] and 'Leeds' in r['parsed']['text']);assert 100<=r['date'][0]<=r['date'][1]<=1970
 probes=m.load(m.RUN/'native/leeds-additions-20261009/native-probes-001.json')
 for r in probes['rows']:verified_raw(r['capture'])
 assert 'Leeds Art Gallery' in probes['rows'][0]['parsed']['text'] and 'commission' in probes['rows'][0]['parsed']['text']
 extra=m.load(RUN/'comparison-native-extra-001.json.gz');assert len(extra['rows'])==1
 for r in extra['rows']:verified_raw(r['capture']);assert '0552' in r['parsed']['text'] and 'A man standing with hands in pockets' in r['parsed']['text']
def corrected(facts,number,text):
 v=copy.deepcopy(facts)
 if number in OVERRIDES:
  v['original_creator_label']=v['creator_label'];v['creator_label']=OVERRIDES[number];v['creator_editorial_basis']=NOTES[number]
  if 'qualified_creator' not in v['issues']:v['issues'].append('qualified_creator')
 if number==19:
  assert 'reading wants verification' in text;v['original_date_fields']={k:v[k] for k in ['date_display','first','last','date_precision']};v.update(date_display='1823? (inscription reading unverified)',date_precision='circa',date_editorial_basis=NOTES[19])
 assert v['work_type'] in ['watercolor','drawing'] and v['object_form'] is None
 return v
def build():
 rows=source_rows();validate_sources(rows);facts=m.load(RUN/'candidate-facts-001.json.gz');identity=m.load(RUN/'identity-002.json.gz');assert facts['rows']==f.rows()[0] and identity['rows']==i.rows();assert not facts['source_fact_holds'];comps=i.comparisons(identity['rows'],identity['state']);assert comps==identity['comparisons'];batch=i.within_batch(identity['rows']);assert batch==identity['within_batch'];assert len(batch)==7 and not any(v['kind']=='inventory' for v in batch);assert [v['numbers'] for v in batch if v['kind']=='mounted_group_inventory']==[[75,76,77,78,79,80]];out=[]
 ctx=m.load(RUN/'comparison-source-context-compact-001.json.gz');checked(ctx['full_context_reference'])
 for dep in ctx['body_references']:checked(dep)
 by={r['number']:r for r in rows}
 for r,c in zip(facts['rows'],comps):
  n=r['number'];src=by[n];v=corrected(r['facts'],n,src['parsed']['text']);assert not c['source_hits'];assert not any(set(h['hit_types'])&{'inventory','parent_or_sibling_inventory'} for h in c['hits'])
  for h in c['other_source_numeric_id_collisions']:assert not (h.get('source_url') or h.get('canonical_url') or '').startswith('https://cotmania.org/') and h.get('scheme')!='cotmania-object'
  assert not any(word in v['source_fields'].get('Credit Line','').lower() for word in ['missing','stolen','restituted']);held=n in HELD
  comparison_basis=NOTES[n]+(' All retained title/lexical candidates reviewed against creator,source inventory,medium,dimensions and composition; no same physical object supported. Generic title overlap with prior gallery sheets does not establish identity.' if c['hits'] else ' No identity candidate in bounded creator,title,inventory,source and full gallery scope.')
  out.append(dict(number=n,source_id=r['source_id'],institution_id=s.IID,state='editorial_hold' if held else 'approved_review_only_addition',facts=v,comparison=c,comparison_basis=comparison_basis,version_note=NOTES[n],hold_reason=HELD.get(n),confidence=None if held else .97,confidence_kind='editorial assessment, not calibrated probability',basis='Museum-commissioned Cotmania catalogue gives exact Leeds Art Gallery accession,object description and collection credit or explicit provenance. '+NOTES[n],limitation='Documented collection association only; no current display,current custody or legal ownership claim. Uncertain makers,subjects,dates and historical remounting retained. No image bytes or painter-authority links.',retrieved_at=src['capture']['receipt']['retrieved_at'],source_capture=src['capture'],source_record_reference=ref(RUN/'selected-objects-001'/('%03d.json'%n)),physical_object_count=0 if held else 1))
 assert collections.Counter(v['state'] for v in out)=={'approved_review_only_addition':102,'editorial_hold':2};assert len({v['facts']['inventory'] for v in out})==104
 return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()};ctx=m.load(RUN/'comparison-source-context-compact-001.json.gz');paths|={checked(d) for d in ctx['body_references']};m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),identity_artworks=len(m.load(RUN/'identity-002.json.gz')['state']['artworks']),identity_citations=len(m.load(RUN/'identity-citations-002.json.gz')['citations']),unrelated_duplicate_research=[dict(inventory='1947.7.127',maker='Benjamin West',policy='Two existing lithograph rows; separate deduplication research, no changes in this pass.')],policy='Selected102 physical objects,not archive pages,with two whole-object date holds. Six separately catalogued pieces on shared mount count individually; all multiple sketches or paired sides on a sheet count once. Existing data preserved; additions stay review.'))
 print(json.dumps(dict(reviewed=104,new_records=102,held=2,creator_refinements=len(OVERRIDES),comparison_raw_bodies=len(ctx['body_references']))),flush=True)
if __name__=='__main__':main()
