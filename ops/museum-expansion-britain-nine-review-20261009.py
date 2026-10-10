"""Review exact Box, York and Harris objects; physical and creation-scope holds persist."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-britain-nine-facts-v2-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
HOLDS={
20:'Fresh York object 20001095, YORAG2001.51 dates The Reflection to1991. Outside creation scope; preserve existing unknown metadata without linking in this pass.',
44:'Imported/source1808 conflicts with Sidney Starr1857–1925. Fresh York922 gives1857–1925, apparently lifespan bounds. Hold date/identity reconciliation; do not invent1908 or replace creation with lifespan.',
51:'Octavius Clark Landscape with Cows P1878.1 and P1878.2 share title,1870–1900 bounds and35.5x25.5cm format. Distinct numbers alone do not resolve physical-version duplication.',
65:'Beryl Cook Bowlers off the Hoe has unresolved exact creation scope; later-date discovery is not primary object confirmation. Accession1976.1 is not a creation date.',
67:'Contemporary Art Society exact object/accession2005.2.4 identifies Chronic Blue as1986. Outside creation scope; unknown catalogue date remains unchanged.',
122:'Two existing John Windass John Burton records share museum-qualified YORAG382. Fresh native object20000834 confirms113x88cm and one physical object. Preserve both IDs and queue reconciliation; no automatic merge or duplicate holding count.',
125:'Source filename qualifies Thomas Reynell as attributed to, but existing catalogue label does not. Hold qualification reconciliation before linking; do not silently affirm the unqualified maker.',
132:'Landscape with Cows P1878.2 remains unresolved against P1878.1: same maker,title,date bounds and dimensions. Both held until independent physical compositions are established.',
138:'Dr Morrison, Venereologist remains without a creation date; LO.74.3 also needs loan/holding-context clarification. Do not infer1974 creation or ownership from the inventory.',
147:'Beach at Looe has a secondary1975 discovery lead but no captured exact primary creation date. Preserve unknowns and hold scope review;1976.2 accession is not creation.',
164:'Foundation dates Project3 Mental Handicap exhibition to1976. Study of Child, Project3 has unresolved own creation date; do not turn project/exhibition date into exact object date. Hold scope.',
192:'South-West Prospect of York source filename says after William Lodge; existing primary creator is unqualified. Hold maker/version reconciliation.',
193:'Native YORAG1249 title says Layerthorpe, but description identifies Acaster Malbis. Canvas differs from1250 millboard, resolving a simple equal-format duplicate concern; title/location conflict still requires review. Native1787–1878 repeats maker lifespan and does not supply a creation date.',
199:'Fresh York object20001096,YORAG2001.52 dates Rose Wylie Doodle Bug to1998. Outside creation scope; retain existing unknown metadata.',
227:'Gbenga has a museum web-index discovery date2004, but direct article capture returned404. Hold creation-scope review; no successful fresh native object capture is claimed.',
233:'A View of Jamaica source filename says attributed to George Robertson. Existing maker is unqualified; hold qualification reconciliation, preserving1772.',
241:'Lenkiewicz PCF58P2 explicitly identifies a triptych centre panel. Whole-versus-panel identity and creation scope remain unresolved; do not count a component as an independently established whole artwork.'}
NOTES={
16:'Elford West African Madonna by a River PCF51 differs from his woman carrying a bowl PCF48 and woman with foliage PCF52. PCF51 also occurs in other museums for Tony Smith,John Codner and Wirgman: unqualified numeric collisions are not identity.',
19:'Jeremiah Meyer GeorgeIII portrait is pendant to Queen Charlotte,Q119025474; different sitter and object identity, not a second record of this portrait. Fresh York162 independently confirms maker and subject. Preserve circa1760–1789.',
22:'Elford woman carrying a bowl PCF48 differs in named action from Madonna and foliage works. Ray Walker Untitled Verso PCF48 belongs to another maker/museum namespace.',
27:'Wikidata one-sided before1920 qualification remains source evidence. Existing unknown creation is preserved, not replaced by1920 or artist lifespan.',
28:'Anthony Devis River Ure at Hackfall P1828 and Weeping Rock waterfall P1827 depict separately named landscape features. Similar formats do not make these different subjects interchangeable.',
37:'Samuel Cook Mrs Winsford and Nelson Cook Mrs James Merrill have different maker identities, sitters and dates.',
42:'Armfield Stag and Dogs1858,76.7x121.9cm differs from Dogs1870,26x30.7cm in date,format and named subject.',
46:'Swallow William Patterson portrait47.6x38.7cm differs from Mrs Patterson and her daughter63.5x48.9cm: different sitters and single/group compositions.',
48:'Fresh York1483 explicitly identifies Study for Nameless and Friendless1857,oil on wood20x27.5cm. It is a small landscape-format study, distinct from Tate full canvas103.8x82.5cm and1862 Skill engraving after Osborn. Native dimensions differ from retained22.5x29.2cm; preserve all source values. Existing published status and published_at are preserved; this is not a new publication.',
49:'Amy B.Atkinson The Lamp and Lawrence Atkinson Lake have different makers and compositions.',
58:'George Lucas landscape must not be conflated with Lucas van Uden,van Leyden,Cranach,Valckenborch or other Lucas name hits. Shared name tokens are discovery only.',
59:'Fresh York1251 is an oil-on-wood view with Castlegate Postern. York1443 is a separately accessioned1838 Clifford Tower view. Source size fields vary; preserve native versus retained dimensions and unknown date1251. Native1787–1878 matches maker lifespan, not an invented object date.',
64:'John Bell York from Scarborough Railway Bridge484 and York from Skeldergate Ferry487 name different viewpoints. Shared63.5x91.5cm size does not collapse opposite views. Robert Anning Bell Oxford/Hinksey is a different maker and place.',
73:'Fresh authority confirms object-level William Calcott Knell1830–1880. Preserve supplied label without creating or reconciling an artist link.',
92:'Fresh authority confirms Reginald Aspinwall; source1855 birth differs from older filename1858. The1876 object is plausible under either; no biography rewrite or artist link.',
107:'Bigg Girl Shelling Peas and Girl Gathering Filberts1782 have different depicted actions and inventories CO2/CO3; paired works are not duplicates.',
112:'Traies Landscape1824,63x93cm differs from1838 Landscape Composition91.5x72.4cm in date and orientation.',
124:'William Page Atkinson Wells differs from John Wells and Seth Wells Cheney; shared Wells token does not establish creator identity.',
136:'Bigg Girl Gathering Filberts and Girl Shelling Peas are independent named actions/compositions despite same year and similar size.',
137:'Swallow Mrs William Patterson and her daughter is a two-sitter composition, distinct from the smaller single portrait of William Patterson.',
142:'Fresh authority confirms William Hughes1842–1901 as the object-level label. David Gordon Hughes Flowers has another maker and square format. No new artist link.',
148:'Elford woman with foliage/river/boats PCF52 differs from his Madonna and bowl carriers. Other PCF52 works by Hinchliff,Hyde and Soden belong to other museum namespaces.',
150:'Gilman Artist Daughters1906–1907 and Artist Mother circa1913 depict different sitters and differ in date.',
161:'Wyn George Shaking Out the Nets is not a George Chambers,Carline,Catlin or Campion work. George name overlap is not identity.',
170:'James Burrell Smith1865 square landscape differs from George Smith of Chichester,Thomas Smith of Derby,James Smith Morland and Matthew Smith records; surname similarity does not reconcile makers.',
171:'Fresh Arthur William Devis1762–1822 authority confirms the supplied object-level maker label. Preserve1784–1795 range and leave artist reconciliation separate.',
172:'Mark Symons Molly in the Garden1930 differs from Molly in the Pantry preparatory study1932 in setting,date and status as a study.',
174:'After the Storm describes weather; it is not an after-another-artist attribution.',
190:'Keith Henderson The Word1931 and William Samuel P.Henderson A Hard Word1838 have different makers and subjects.',
201:'Ambrose Bowden Johns Mount Edgcumbe circa1821,66x88cm differs from St Nicholas Island from Mount Edgcumbe1829,44x61cm in date,format and viewpoint.',
204:'Thomas Percival Anderson Mrs Edith1907 is not a Robert Anderson,Nils Andersson or Lennart Anderson work.',
205:'Robert Noble River Tyne East Lothian1910 is a small portrait-format34x26cm painting, distinct from landscape122.5x218.5cm An East Lothian River1910. Dirleton Church has another subject.',
208:'Sebastian Pether Moonlight1840,21x26cm differs from Reading1836,65x77cm and Bath1819,61.7x88.3cm compositions; Abraham and Henry Pether are other makers.',
209:'Exact museum-qualified2021.2 and source object identify Marion Grace Hocken My Room. Fresh limited Hocken/My Room searches did not return this object and do not negate the retained exact source. Accession2021 is not creation; unknown date remains under review and excluded from eligible totals.',
212:'Anthony Devis Weeping Rock waterfall is a separately named Hackfall feature from River Ure; preserveP1827/P1828 as distinct source compositions.',
218:'Fresh York1250 confirms1829 oil on millboard28.3x36cm, while1249 is oil on canvas28.1x35.5cm. Different supports and accessioned objects distinguish them;1249 remains held for conflicting title/location description. No date or media rewrite.',
222:'Fresh York1443 confirms Clifford Tower1838 as a distinct native object from1251 with Castlegate Postern. Native image/frame size labels and retained dimensions differ; all source evidence retained without metadata substitution.',
236:'Fresh York object20001055,YORAG142 confirms Showery Weather,Charles Collins,1875 and40.6x66cm. This primary object evidence supports the holding while Q20018580 biography1867–1921 conflicts with filenameCharles CollinsII1851–1921. Preserve the unresolved object-level Charles Collins label; no accepted painter identity or new artist link is asserted.',
238:'York from Skeldergate Ferry487 and York from Scarborough Railway Bridge484 name different viewpoints despite equal formats. Different Robert Anning Bell Oxford view is not a duplicate.',
239:'Arthur Devis self portrait circa1737,P1349,70.5x58cm differs from Tate N03888 Portrait of a Man circa1750,47x29.8cm and N03317 Lady circa1750–1751,61x40.6cm; retained exact Tate API dimensions checked. Cleveland1763 portrait and NGA1756 Gentleman Netting Partridges have other dates and compositions.'}
ARTIFACTS=['initial-scope-001.json.gz','source-context-001.json.gz','candidate-facts-002.json.gz','identity-002.json.gz','identity-citations-002.json.gz','comparison-source-context-002.json.gz','editorial-comparisons-001.json.gz','native-probes-001.json','selected-authorities-001.json.gz','native-extra-001.json.gz','creation-scope-sources-001.json.gz','york-selected-native-001.json.gz','york-followup-native-001.json.gz']
def native_objects():
 return {v['index']['inventory']:v for name in ['york-selected-native-001.json.gz','york-followup-native-001.json.gz'] for v in m.load(RUN/name)['rows'] if v.get('capture')}
def raw_checked():
 cache={}
 def raw(dep,sha):
  key=(dep['path'],dep['sha256'])
  if key not in cache:
   p=checked(dep);b=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes();cache[key]=b
  assert hashlib.sha256(cache[key]).hexdigest()==sha;return cache[key]
 for name in ['source-context-001.json.gz','comparison-source-context-002.json.gz']:
  for row in m.load(RUN/name)['rows']:
   if row.get('body_reference'):
    b=raw(row['body_reference'],row['raw_sha256'])
    if name.startswith('source-'):assert json.loads(b)['entities'][row['source_id']]==row['entity']
 x=m.load(RUN/'selected-authorities-001.json.gz');c=x['capture'];assert json.loads(raw(ref(m.ROOT/c['body_path']),c['receipt']['sha256']))['entities']==x['entities']
 for name in ['native-probes-001.json','native-extra-001.json.gz','creation-scope-sources-001.json.gz','york-selected-native-001.json.gz','york-followup-native-001.json.gz']:
  x=m.load(RUN/name)
  for row in x.get('rows',[])+x.get('searches',[]):
   c=row.get('capture')
   if not c:continue
   b=raw(ref(m.ROOT/c['body_path']),c['receipt']['sha256']);assert c['receipt']['status']==200
   if row.get('parsed'):assert BeautifulSoup(b,'html.parser').get_text(' ',strip=True)==row['parsed']['text']
 return len(cache)
def build():
 initial=m.load(RUN/'initial-scope-001.json.gz');facts,errors=f.rows();assert not errors;identity=m.load(RUN/'identity-002.json.gz');assert identity['rows']==facts;comps={v['number']:v for v in identity['comparisons']};src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};artists={v['id']:v for v in initial['painters']};auth=m.load(RUN/'selected-authorities-001.json.gz')['entities'];native=native_objects();out=[]
 assert all(qid in auth for qid in s.QIDS.values())
 assert 'Production date start 1991' in native['YORAG : 2001.51']['parsed']['text'] and 'Production date start 1998' in native['YORAG : 2001.52']['parsed']['text']
 assert 'Oil on millboard' in native['YORAG : 1250']['parsed']['text'] and 'Oil on canvas' in native['YORAG : 1249']['parsed']['text']
 cas=next(v for v in m.load(RUN/'creation-scope-sources-001.json.gz')['rows'] if v['provider']=='cas')['parsed']['text'];assert all(t in cas for t in ['1986','2005.2.4','The Box'])
 for row in facts:
  n=row['number'];r=src[n];a=r['artwork'];fact=row['facts'];comp=comps[n];assert {v['entity_id'] for v in comp['source_hits']}=={a['id']};state='editorial_hold' if n in HOLDS else 'approved_existing_holding'
  for link in fact['artist_links']:
   ar=artists[link['artist_id']]
   if fact['first'] and state=='approved_existing_holding':assert not((ar['birth_year'] and fact['last']<ar['birth_year']) or(ar['death_year'] and fact['first']>ar['death_year']))
  if state=='approved_existing_holding':
   allowed=[]
   if n in [73,92,142,171,236]:
    assert auth[fact['creator_qid']]['labels']['en']['value']==fact['creator_label'] and not fact['artist_links'];allowed.append('creator_authority_requires_reconciliation')
   if n==236:assert all(v in native['YORAG : 142']['parsed']['text'] for v in ['Showery Weather','Collins, Charles','Production date start 1875'])
   if n==19:assert 'Q119025474' in json.dumps(fact['source_related_statements']);allowed.append('related_version_component_or_pendant_requires_review')
   if n==27:assert fact['date_precision']=='unknown' and 'P1326' in fact['source_creation_statements'][0]['qualifiers'];allowed.append('creation_qualifier_requires_review')
   if n in [48,174]:allowed.append('filename_or_title_qualification')
   if 'missing_exact_artuk_collection_reference' in row['issues']:assert any(fact['artuk_url'] in s.references(v,'P854') for v in fact['source_collection_statements']);allowed.append('missing_exact_artuk_collection_reference')
   assert not set(row['issues'])-set(allowed),(n,row['issues']);assert fact['last'] is None or fact['last']<=1970
  basis='Exact artwork QID,title,object-level creator label and museum-qualified inventory identify the retained object. Collection statements reference the same ArtUK object by identifier or URL. '+NOTES.get(n,'No unresolved same-maker physical-version conflict survives the bounded source,title,inventory and museum comparison.')
  limitation='Accept documented collection association only; no current display,custody or ownership claim. Wikidata/ArtUK statements are correlated secondary evidence,not fresh native object confirmation. Selected native object pages are explicitly attached where captured. ArtUK access hold respected. Preserve all dates,attributions,creator links,images,status and descriptive metadata. Confidence is editorial,not a calibrated probability.'
  if fact['date_precision']=='unknown':limitation+=' Unknown creation remains in editorial review and excluded from eligible pre1971 totals; acquisition,exhibition and maker lifespan dates are not substituted.'
  native_object=native.get(fact['inventory']);confidence=.95 if native_object and state=='approved_existing_holding' else .85
  out.append(dict(number=n,state=state,institution_id=r['institution_id'],source_institution_id=r['institution_id'],existing_artwork_id=a['id'],previous_institution_id=None,pending_assertion_id=r['pending_assertion']['id'],supersede_assertion_ids=[r['pending_assertion']['id']] if state=='approved_existing_holding' else [],facts=fact,comparison=comp,source_reference=r['body_reference'],source_raw_sha256=r['raw_sha256'],retrieved_at=r['pending_assertion']['checked_at'],confidence=confidence,basis=basis,limitation=limitation,hold_reason=HOLDS.get(n),metadata_review_note=NOTES.get(n),native_object_evidence=native_object))
 assert collections.Counter(v['state'] for v in out)=={'approved_existing_holding':229,'editorial_hold':17};assert sum(len(v['supersede_assertion_ids']) for v in out)==229;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();bodies=raw_checked();ds=build();approved=[v for v in ds if v['state']=='approved_existing_holding'];summary={iid:dict(approved=sum(v['institution_id']==iid for v in approved),eligible=sum(v['institution_id']==iid and v['facts']['date_precision']!='unknown' for v in approved)) for iid in s.IIDS};m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/name) for name in ARTIFACTS],verified_raw_bodies=bodies,summary=summary,policy='229 selected existing holdings,17 identity/attribution/scope holds. Existing publication retained for Osborn study; no new publication. No metadata,date,artist,media or display changes. Every unknown date remains excluded from eligible totals.'));print(json.dumps(dict(approved=len(approved),held=17,by_museum=summary,verified_raw_bodies=bodies)),flush=True)
if __name__=='__main__':main()
