"""Selected York physical-object decisions, explicit version and source-fact holds."""
import collections,copy,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-york-additions-facts-20261009.py');i=module('i','museum-expansion-york-additions-identity-20261009.py');s=f.s;m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
HELD={
25:'Bellini/follower Virgin and Child versions need complete object comparison. NGA496 near-size panel has different background in cached discovery, but fresh NGA request403 is stopped; other Bellini versions remain to check.',
28:'Native Parmigianino canvas differs from Louvre panel, but alternative Catena Portrait of a Man with a Book record lacks sufficient retained physical comparison. Hold possible cross-attribution duplicate.',
32:'Style-of-Patenier square panel needs further comparison with Cima da Conegliano Saint Jerome in a Landscape and source-attributed variants.',
34:'Unidentified/imitator-of-Bouts Christ in the House of Simon needs physical comparison with existing Sigmund Holbein version, c1500.',
39:'Anonymous Holy Family has Virgin and Child alias; several legacy versions with incomplete dates/formats remain unresolved. Existing prints are distinct, but that does not resolve every painting candidate.',
42:'Anonymous1556 male portrait needs further comparison with Corneille de Lyon, Hemessen and Mor versions. Generic title and different attribution do not resolve same-object identity.',
48:'Cavallino St Agatha1635-1645 needs physical comparison with existing Furini St Agatha carrying the same date range; possible attribution/version ambiguity.',
50:'Likely existing WikiArt Roman Charity654a18b7-ffcd-566a-8443-7c5d1ee4c678. York inventory788 is documented, but WikiArt version is not yet securely distinguished from known replicas. Neither a duplicate addition nor an unsupported holding link.',
54:'York Fetti Mote and Beam panel67x51.7cm differs from Met1991.153 panel61.3x44.1cm, but same-composition version comparison remains incomplete; no held-provider request.',
67:'Unresolved Miranda/Loth attribution. RijksSK-A-1425 is76x64cm versus York89x69cm; PradoP000649 and versions need further comparison. Do not resolve on size/date alone.',
78:'Dughet Campagna landscape38x49cm differs from Rijks larger canvases, but two retained ArCo comparisons lack fully reconstructed physical dimensions. No ArCo retry.',
83:'Mercier oval gentleman73x61cm differs from V&A scroll-and-curtain composition; NG4036 overall81.3x65.4cm needs composition comparison before ruling out framing/measurement difference.',
103:'Anonymous lady1785-1795 needs further physical comparison with incomplete legacy female-portrait records. Identified miniatures and drawings are distinct but do not resolve remaining canvases.',
118:'Jackson Mr Hopper1812 needs physical comparison with legacy Portrait of a Man c1820-1825, inventory1960.244. Sitter/date distinction alone is insufficient for uncertain legacy title.',
124:'Anonymous Shipwreck1815-1825 on millboard differs from Altamouras charcoal; William James Durant Ready legacy Shipwreck remains incompletely documented.',
162:'Native Blanche page has two incompatible production-date starts1903 and1913. Do not invent a range or select one date.',
190:'Likely existing WikiArt Digging for Roots4638873e-77b9-5c0d-aec6-5676842f9ae6 with exact creator/title/1949. Native978 is secure, but WikiArt lacks inventory/physical fields; complete same-version review before linking.'}
NOTE_TEXT='''3|Home/Canterbury Meadows source Cooper1858 differs from Shalders1855 and Fitton1942; no creator equivalence supported.
6|Henry Moore landscape1857, not Schwanfelder125 or Etty128; common landscape title does not identify physical work.
13|Danby and John Martin labels remain unresolved, not joint authors. York66x86.4cm differs from Tate Danby70.7x109.9cm study and284.5x452.1cm canvas; WikiArt Martin1834 explicitly Yale, different source version.
15|Near-square Danby23.9x24.9cm sunset differs from NGA coast panorama13.9x34.1cm and James Francis Danby work.
16|Herring and Faed native labels retained as unresolved attribution, not an invented collaboration.
17|779a, one24cm roundel: Peter has keys/book. Separate from Paul779b and unknown Aragonese/Valencian187x87cm panel.
18|779b, one24cm roundel: Paul has sword/book. Separate from Peter779a. No aggregate779 record added.
19|Three native maker labels remain unresolved. Small29x32cm Baptism differs from other named-makers' prints, frescoes and large panels; do not choose one source attribution.
22|Native dimensions repeat width27.5 and18cm; retain literal labels without inventing which is height. Painting differs from Schongauer engraving.
23|898b is one accessioned altarpiece wing, painted on two sides with several saints. Count once, not both wings or each figure.
24|Follower-of-Weyden retained. Yorkwood30.5x20cm differs from WikiArt KHM Madonna12.1x18.8cm and its standing-in-niche composition.
26|Unidentified creator remains explicit; no invented named painter.
29|Bacchiacca/Foschi labels unresolved; no joint-author inference.
31|854 triptych is one native object with centre and wings. No separate record for each scene or panel.
33|Anonymous painted wood57.7x40cm differs from Duvet engraved paper15.1x22.2cm.
36|Unidentified/studio-of-Lorenzo-di-Credi attribution retained; no unqualified master link.
37|Painted panel57.7x75cm differs from Durer charcoal17.1x23.5cm.
38|885 consists of ten joined panels with five scenes; native object count1. Add one accessioned ensemble.
41|Unidentified/style-of-Gheeraerts remains qualified; named sitter does not resolve painter.
49|Monsignor Agucchi1603-1604 differs from Agostino Carracci engraving Pope InnocentIX1591; sitter,creator,medium differ.
51|Soutman1642 painting not Samson and Delilah prints or pictures by other named makers.
53|Yorkcanvas64x82cm differs from NGA2000.159.1 oilpanel48x82.5cm; retain distinct material/format.
55|Louvre Joconde00000104589 explicitly distinguishes its later altarpiece from smaller York devotional version. Louvre canvas versus York62.8x49.5cm wood panel; Camillo versions/drawing are another creator and format.
56|York1631panel46.9x64.4cm has cat on left. Rijks1632SK-A-2544 is74.3x114cm with cat at right;1660SK-A-1481 is47.5x75.5cm fish/lobster/oysters. Different signed dates,formats and compositions.
57|York99x250cm stall differs from WikiArt Hermitage1618,341x207cm; no merge from title alone.
58|Unknown/Gheeraerts-style/Peake-style labels remain unresolved.
60|York1627panel19.8x31.9cm river scene differs from Met drawing16x27.3cm and later named river compositions.
61|Unidentified/Salomon van Ruisdael retained unresolved. Separate from Goyen1627 river scene60.
63|Unknown/Kneller retained unresolved; no automatic painter-authority link.
66|Duquesnoy relief described in background is a depicted object, not attribution of whole painting to Duquesnoy.
68|Giordano canvas46.9x59.9cm differs from Apsida12196 Saint Neophytos mural in Cyprus; generic Last Supper title is insufficient identity.
69|Crown of Life convert/angel/devotional books differs from Valdes Leal In Ictu Oculi Death1672.
72|Vois/Mieris unresolved lady29x23cm at column differs from male/boy subjects and another maker Jan Mieris.
73|Barent Fabritius Roman Charity is not Baburen50; distinct maker,source inventory and date scope.
79|Anonymous studio interior retained as actual work; no invented master.
81|Vanderbank1737canvas138x97cm differs from NGA1734standing-lady drawing29.7x18.5cm.
82|Elizabeth Betts1741 is female sitter76x63.5cm, not Bishop Benjamin Hoadly127.3x101.5cm.
88|Unidentified/John Fayram maker relationship unresolved.
89|Wine-skins episode differs from Tate Don Quixote and Goatherds despite similar format.
90|Troost lady1741canvas69x57cm differs from Rijks1723 male and Met male drawing.
96|Cotes1765double portrait240x152.5cm differs from Tate1768single Lady126.7x101.6cm. Frame ornaments remain parts, not extra artwork records.
99|Marlow Tivoli/Italian Landscape104.1x127cm differs from retained YaleB1975.4.1336,27.3x38.4cm.
100|Marlow old Ouse Bridge1758-1768 differs from Hamilton1925-1931bridge176.
101|Hoppner male77.5x64cm differs from named women and Belgrave Hoppner's different-maker records.
104|Prospero fragment is one extant catalogue object; do not reconstruct or count the missing whole composition.
107|Captain John Foote in Indian clothes/turban differs from Captain Robert Orme, another sitter.
109|Francesco Guardi canvas36x41cm differs from Bergamo panel19x15cm and Giacomo pen/wash12x20cm.
110|Batoni John Smyth1773 differs from John Scott1774, another sitter.
112|Etty after Lawrence: source aliases disagree Lady Templeton versus her daughter. Use neutral study title with sitter uncertain; retain all source labels. Not Lawrence original.
113|Etty after Lawrence: source aliases disagree Charles Baring Wall versus Jacob Pattisson. Use neutral study title with sitter uncertain; retain all source labels. Not Lawrence original.
114|Etty copy after Reynolds Iphigenia, not Reynolds original.
115|Etty raised-arm/knee nude on millboard59x41cm differs from Fitzwilliam standing56.3x47cm and seated/reclining or chalk/graphite versions.
116|Reclining nude with spear42x54cm differs from Fitzwilliam raised-knee portrait-format66x49.5cm.
117|Standing staff nude oil47x29cm differs from NGA seated staff graphite30.7x18.6cm and Shirlaw1872.
123|1808 inscription on historical photograph records painting. Source woodworm disposal concerns photograph, not documented deaccession/destruction of painting.
125|Schwanfelder1825 landscape is not Moore6 or Etty128; named makers and inventories retained.
128|Etty landscape with reverse studies counts once. Whole catalogue production range retained without independently dating each reverse mark.
129|Plantation at Acomb with reverse studies counts once; no extra verso artwork or invented separate date.
130|Named Etty portrait of unidentified woman; sitter unknown does not mean anonymous maker.
134|Mary Ann Purdon crochet-worker study1844-1849 differs from Mary Arabella Jay1819.
135|Yorkmillboard61.5x45.6cm Bacchante differs from LouvreRF1970-49 canvas98.5x74.5cm, retained Joconde000PE021190.
136|Mlle Rachel with reverse studies counts once; native range applies to catalogue object.
137|Use current native Study of a Black Boy primary title; historical alias retained in source evidence only.
140|Haddon Hall scene depicts sixteenth century but painting creation1866; subject period does not replace creation.
141|Hogarth studio subject1739; actual source creation1863 retained.
146|Sickert Twilight/Butcher Shop1881-1887wood36x48.5cm differs from Antique Shop1906cardboard24.1x19.1cm.
149|Garstin Canadian landscape1891 differs from Tangierc1885location/version.
152|Cooper1875panel50x69cm differs from Tate1854panel29.2x40.6cm, Troyon version and other Cooper makers.
153|Fantin white roses1875,42x38cm differs from Tate1864,56.5x46.4cm and Minneapolis1884,38.4x32.9cm.
154|Pink roses1881,49x54cm differs from same-year Chicago bowl26.2x31.4cm and other dates/formats.
156|OConor1898seascape differs from Glade1892forest and other named-makers' wave compositions.
158|Steer Southwold boatswood20x26.5cm differs from Tatecanvas50.5x61cm.
161|Follower-of-Maitland uncertainty retained. Yorkverticalcanvas25.5x20.5cm differs from HunterianGLAHA43756 horizontaloilpanel16.5x25.6cm, retained primaryIIIF metadata.
167|Bomberg Bath1922canvas50.8x61cm differs from Mud Bath1914canvas152.4x224.2cm.
170|Wolmark male45x37cm millboard differs from Fisher Girl76.2x64.8cm canvas.
171|Gwen John red-shawl woman with clasped hands45.1x34.9cm differs from Black Cat46x29.8cm and violin composition; John surname hits include other makers.
172|Richard Jack1920Wagner funeral scene differs from Jack Levine Passing Scene1941; surname is not identity.
174|Sickert Rue de la Boucherie1903wood19x24.5cm differs from Notre Dame1899canvas55x46cm,1909etching and other streets.
175|Nash Winter Seacanvas71x96.5cm differs from Winter Scene/Holidaylinocut12.5x9.5cm and Thubron1951.
176|Hamilton Ouse Bridge1925-1931 differs from Marlow old bridge100 and John Hamilton Mortimer different maker.
180|Source1943-08 is valid August1943, not year range1943to8; month string retained with1943 classification.
181|Source1933-08 is valid August1933, not year range1933to8; month string retained with1933 classification.
187|Nicholson Birdie1934,45x60cm differs from Tate1934-1936Still Life40.7x51cm. Existing WikiArt/Tate duplicate pairs remain separate research, not altered.
189|Pasmore1946cafe differs from Evelyn Gibbs1940; no creator equivalence supported.'''
NOTES={int(x.split('|',1)[0]):x.split('|',1)[1] for x in NOTE_TEXT.splitlines()}
def verified_raw(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def corrected(v,n):
 v=copy.deepcopy(v)
 if n==50:v['original_creator_label']=v['creator_label'];v['creator_label']='Source attribution unresolved: Dirck van Baburen; Thoedore van Baburen';v['creator_editorial_basis']='Remove empty role parentheses only; source spelling/identity uncertainty retained.'
 if n in [112,113]:
  v['original_title']=v['title'];v['title']="Study of a girl's head, after Thomas Lawrence (sitter uncertain)" if n==112 else "Study of a boy's head, after Thomas Lawrence (sitter uncertain)";v['title_editorial_basis']=NOTES[n]
 return v
def build():
 source=m.load(RUN/'selected-objects-001.json.gz')['rows'];assert len(source)==177;by={x['number']:x for x in source};facts=m.load(RUN/'candidate-facts-001.json.gz');fresh,errors=f.rows();assert fresh==facts['rows'] and errors==facts['source_fact_holds'];assert [x['number'] for x in errors]==[162];identity=m.load(RUN/'identity-001.json.gz');assert identity['rows']==fresh;comps=i.comparisons(fresh,identity['state']);assert comps==identity['comparisons'];assert i.within_batch(fresh)==identity['within_batch'];ctx=m.load(RUN/'comparison-source-context-001.json.gz')
 for dep in ctx['body_references']:checked(dep)
 out=[]
 for row,c in zip(fresh,comps):
  n=row['number'];src=by[n];v=corrected(row['facts'],n);verified_raw(src['capture']);assert v['physical_object_count']=='1';assert not c['source_hits'];assert not any('parent_or_sibling_inventory' in h['hit_types'] for h in c['hits']);held=n in HELD
  note=NOTES.get(n,'Native accession identifies one painting. Primary title,all source maker labels,production-date fields,materials and labeled support/frame measurements retained. No separate record for figures,frame parts or catalogued aliases.')
  basis='York Museums Trust native Fine Art painting record gives exact YORAG accession,one object and supported production dates. '+note
  comparison_basis=HELD[n] if held else note+' Creator/title/source/inventory candidates compared; numeric alternative-inventory collisions across museum namespaces are not identity. Generic titles and lexical overlap alone do not establish a match. Full comparison ledger and available source bodies retained.'
  out.append(dict(number=n,source_id=row['source_id'],institution_id=s.IID,state='editorial_hold' if held else 'approved_review_only_addition',facts=v,comparison=c,comparison_basis=comparison_basis,version_note=note,hold_reason=HELD.get(n),confidence=None if held else .97,confidence_kind='editorial assessment, not calibrated probability',basis=basis,limitation='Documented collection association only; no current display,current custody or legal ownership claim. Source maker/date/subject uncertainty retained. No image bytes or artist-authority links.',retrieved_at=src['capture']['receipt']['retrieved_at'],source_capture=src['capture'],source_record_reference=ref(RUN/'selected-objects-001'/('%03d.json'%n)),physical_object_count=0 if held else 1))
 src=by[162];verified_raw(src['capture']);out.append(dict(number=162,source_id=src['source_id'],institution_id=s.IID,state='source_fact_hold',hold_reason=HELD[162],source_record_reference=ref(RUN/'selected-objects-001/162.json'),source_capture=src['capture'],physical_object_count=0));out.sort(key=lambda x:x['number']);assert len(out)==177;assert collections.Counter(x['state'] for x in out)=={'approved_review_only_addition':160,'editorial_hold':16,'source_fact_hold':1};assert len({x['facts']['inventory'] for x in out if 'facts' in x})==176
 return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()};ctx=m.load(RUN/'comparison-source-context-001.json.gz');paths|={checked(d) for d in ctx['body_references']};m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),identity_artworks=26380,identity_citations=54896,unrelated_duplicate_research=[dict(maker='Ben Nicholson',policy='Existing WikiArt/Tate pairs remain separate research; no mutation.')],policy='160 selected physical paintings added in review,17 holds.13 already-linked index objects excluded before selection. Whole triptych/joined panels and two-sided items count once; two separately catalogued saint roundels count individually. Attribution relationships remain explicitly unresolved. Two conflicting sitter labels qualified. No catalogue metadata overwrite,publication,image or display claim.'))
 print(json.dumps(dict(reviewed=177,new_records=160,held=17,comparison_raw_bodies=len(ctx['body_references']))),flush=True)
if __name__=='__main__':main()
