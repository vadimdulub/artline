"""Individual Brighton and Ulster decisions, retaining date and identity uncertainty."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-britain-four-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);f=i.f;s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
NETWORK=s.NETWORK
HOLDS={
29:'Native Robert Home maker is explicitly attributed to. Existing creator link is unqualified; retain the association pending attribution reconciliation.',
62:'Native exact object is dated 1978. The existing unknown creation date remains unchanged; do not strengthen this post-1970 museum association in the selected eligible expansion.',
67:'Dickey San Vito Romano1923 has a same-maker comparison Monte Scalambra from San Vito Romano1923,82.1x101.9 versus76.7x102.5cm. Similar dimensions and overlapping subject do not resolve physical identity; retain accepted network holding.',
73:'Native department is PORTRAITS : PAINTINGS, outside the specific Fine Art branch inference used here. Preserve accepted network association pending object-level branch evidence.',
75:'Native primary maker is Norman French McLachlan, but another artist line names W.J.McLachan. Preserve the conflicting maker labels and defer reconciliation.',
76:'Native maker Comhghall Casey is born1976 and has no creation date. This is incompatible with creation by1970; retain existing unknown date and network association without inventing a year.',
78:'John Simpson William IV1830 has another same-maker/same-title/year record with no inventory or dimensions. Native exact FA000797 gives no creator. Physical version unresolved; do not create a second accepted museum representation.',
84:'Native department is VIEWS : PAINTINGS, outside the specific Fine Art branch inference used here. Preserve accepted network association pending object-level branch evidence.',
98:'Morris Old Town Hall1934 has another same-maker/same-building/year record1966/127,63.2x76.5cm versus native FA000287,61x70.8cm. Modest size differences alone do not resolve version or transfer history.',
100:'Native/filename attribution to John Greenhill is qualified; existing unqualified maker needs separate reconciliation.',
113:'Native exact inventory is explicitly in the Royal Pavilion department,while the pending claim names Brighton Museum and Art Gallery. Preserve this branch conflict for reconciliation; do not treat institutions as interchangeable.',
156:'Gilbert Untitled1950 has a same-maker Untitled1948 comparison without dimensions or inventory. Date difference alone cannot establish a different object; preserve accepted network holding.',
194:'Source filename qualifies attribution to Alexander Carse. Preserve original label and defer association pending creator reconciliation.',
235:'Native Castle Hill on the Sussex Downs has date1982, conflicting with pre-1971 scope and the source artist identity. Existing unknown date remains unknown pending resolution; no inferred correction.'}
for number in [8,18,19,41,72,170,228]:HOLDS[number]='FAPM inventory series requires Preston Manor branch reconciliation. The official Preston Manor history places the Pickle portrait in that house; other selected FAPM inventories are leads,not independently proven branch assignments. Preserve the pending Brighton association and seek object-level branch evidence before acceptance or reassignment.'
NOTES={
30:'Ernest Borough Johnson differs from Cornelius Johnson,Eastman Johnson and Joshua Johnson. Generic portrait titles and surname overlap do not identify the same maker.',
35:'Clement Lambert differs from George Lambert and James Lambert I/II. Preserve exact selected inventory.',
36:'Native Boulogne date fields contain both1925-1926 and1925-1929. Preserve both source values separately and the original catalogue date unchanged; no new chronology is inferred.',
37:'Native Frederick Footet is a spelling variant on this exact inventory/title; existing Frederick Footett label remains unchanged.',
44:'Charles Keith Miller differs from William Edwards Miller,Philip Homan Miller and Alfred Jacob Miller. The selected ship is not those portraits or war party.',
46:'Paul Henry differs from Paul Gauguin and Henri Fantin-Latour; the blacksmith is not the similarly tokenized bathers or rocks.',
50:'Native Jonzen Still Life1944,79x65.5cm,on paper,depicts purple flowers on a wicker chair and the Spectator. The comparison1936 is explicitly Dead Birds and Lemons. Subject,medium and date support distinct works despite modest size difference.',
54:'Native Benjamin Barker II1807 landscape116.5x172.5cm differs from his1803 Welsh Landscape78x65cm in date and physical format. Benjamin Barker I,Joseph,David Walker and Thomas Barker comparisons are different makers.',
55:'Procter Early Morning1927,51.4x101.6cm differs in format from Early Morning,Newlyn1926,49.7x60.2cm and Tate Morning1926,76.2x152.4cm. Distinct inventories and sizes support separate versions.',
58:'Native Waterloo Bridge No.1 is the same exact inventory as existing Waterloo Bridge,London; retain the more specific native title as evidence without changing catalogue text.',
69:'William Gibbes Mackenzie differs from Alexander Mackenzie.',
83:'Existing title explicitly preserves after Joshua Reynolds. Native identifies Alma Gogin after Reynolds; retain the copy maker and qualified title,not a Reynolds original. Native title1779 refers to the portrait prototype,while native creation says Early-Mid20thCentury; no1779 creation is inferred.',
85:'Robinson1798 portrait76.8x63.1cm differs from the attributed circa1805 Linen Hall portrait91.5x70.5cm. Other Robinson comparisons are different makers. Preserve possibly a United Irishman sitter uncertainty.',
89:'Native Large version has a separate inventory and physical dimensions from the smaller Disturbed at Dinner229. Both source size labels and dimensions remain distinct.',
94:'Harry R.Douglas differs from John Douglas; Robert Barklie sitter is not Robertson Place.',
101:'Meninsky Boy with a Cat1925,123.5x55.5cm differs from Tate Portrait of a Boy1923,91.4x71.1cm,with distinct subject and format.',
102:'Walter Taylor differs from Donald Taylor; source inventory and interior setting retained.',
117:'Rex Vicat Cole differs from George Vicat Cole; their mill scenes are not treated as the same object.',
119:'Native kitchen object retains conflicting circa1934 and1936 date lines. Exact title,maker and inventory agree; preserve the existing date and all native date evidence without rewriting.',
121:'Robin Wallace differs from William and Harry Wallace. Native exact inventory expands Landscape to Landscape with Church and Estuary and dates1926-1929; preserve original1929 without rewriting metadata.',
144:'David Gordon Hughes differs from William Hughes. Generic flowers subject does not equate makers.',
164:'John Poad Drake William IV is a different attributed maker from John Simpson number78; keep their exact inventories distinct.',
166:'Alfred Robert Hayward differs from Arthur Hayward; source shortened Alfred Hayward retained separately.',
169:'Native Yeats Riverside has1923 and1922 date lines. Existing1922 remains unchanged; the exact inventory,title and maker identify the work independently of this one-year discrepancy.',
176:'Maidment Farm Scene1932,56x76cm horizontal canvas differs from Old Houses76.2x60.9cm vertical format. Exact inventories and subjects retained.',
177:'Native Geums retains circa1930-1931 and1930-1936 lines. Preserve the source discrepancy and existing date without inferring a correction.',
186:'Marjorie Brooks,Lady Holford differs from Mildred Bryant Brooks; painting and print are distinct.',
195:'Mackenzie William Gray1912 differs from William Fee McKinney1905; these are distinct named sitters and inventory objects.',
204:'Native Portrait of a Man Wearing a Garter Star has the same exact inventory and Solomon Alexander Hart creator; keep the more specific imported sitter identification separate from less specific native title.',
226:'John Luke differs from Sir Luke Fildes; Tipster and Widower are different makers and objects.',
229:'Native smaller Disturbed at Dinner has distinct dimensions and inventory from number89 Large. Do not collapse or duplicate these separate source versions.',
230:'John Luke differs from Sir Luke Fildes. Self-portrait is a generic title across these distinct makers.',
234:'Chisholm Cole differs from Timothy Cole and Thomas Cole; their reader/departure/return objects are not this estuary.',
236:'School is part of the train journey subject,not a school-of attribution. Norman Alexander Clark differs from Joseph Clark.'}
LIMIT='Editorial confidence is not a calibrated probability. Saved Wikidata collection/location statements are correlated secondary evidence,not independent confirmation. Native evidence supports its explicit facts only. Art UK access hold remains. Holdings do not assert legal ownership,physical custody or current display. Preserve catalogue metadata,dates,creator links,images and review status.'
def native_rows():
 out={}
 for provider,count in [('brighton',120),('ulster',119)]:
  x=m.load(RUN/(provider+'-native-001.json.gz'));assert not x['requests_stopped'] and not x['unprocessed_numbers'] and len(x['rows'])==count
  for v in x['rows']:
   row=m.load(checked(v['reference']));assert row['number']==v['number'];out[row['number']]=row
 return out
def build():
 src=m.load(RUN/'source-context-001.json.gz');srcby={v['number']:v for v in src['rows']};rs=f.rows();comps={v['number']:v for v in m.load(RUN/'identity-001.json.gz')['comparisons']};own={v['existing_artwork_id'] for v in rs};verified={v['number']:v for v in m.load(RUN/'unlinked-creator-authorities-001.json.gz')['rows']};native=native_rows();network=m.load(RUN/'ulster-network-context-001.json.gz');neth={v['artwork_id']:v for v in network['rows']};assert len(neth)==53;out=[];invs=set()
 for row in rs:
  number=row['number'];v=row['facts'];source=srcby[number];art=source['artwork'];c=comps[number];aid=art['id'];key=(row['institution_id'],i.i.q.compact(v['inventory']));assert key not in invs;invs.add(key);assert c['source_hits'] and {h['entity_id'] for h in c['source_hits']}=={aid}
  hold=HOLDS.get(number);external=[h for h in c['hits'] if h['id'] not in own and(h['same_creator'] or 'inventory' in h['hit_types'])];assert not external or number in NOTES or hold
  issues=list(v['issues']);note=NOTES.get(number,'No unresolved same-maker/version comparison. Generic within-batch titles do not merge different creator identities.');confidence=.8;nr=native[number];native_ref=ref(RUN/('brighton-selected' if row['institution_id']==s.IIDS[0] else 'ulster-selected')/('%03d.json'%number));in_network=art['current_institution_id']==NETWORK
  if 'creator_authority_requires_reconciliation' in issues:
   author=verified[number];assert author['label_match'] and author['qid']==v['creator_qid'] and author['existing_label']==v['creator_label'];issues.remove('creator_authority_requires_reconciliation');note+=' Existing unlinked label matches its exact creator authority; no painter link added.'
  if number in [83,236]:issues.remove('filename_or_title_qualification')
  if nr['state']=='captured_exact_inventory':
   p=nr['parsed'];confidence=.9
   if row['institution_id']==s.IIDS[0]:
    assert p['accessionId']==v['inventory'];assert p['department']=='Fine Art' or number==113 and hold;maker=p['creator'];date=p['dateCreated']
   else:
    assert p['fields']['Catalogue Number']==[v['inventory']];maker='; '.join(p['fields'].get('Maker',[]));date='; '.join(p['fields'].get('Date Made',[]))
   if re.search(r'\b(?:attributed|circle|workshop|school|manner|follower)\b',maker,re.I):assert hold,'Unreviewed native maker qualification'
   if any(int(y)>1970 for y in re.findall(r'\b(?:19|20)\d{2}\b',date)):assert hold,'Native creation date beyond1970 requires review'
   note+=' Native exact inventory,title,maker and date labels reviewed. Source abbreviations and title variants are retained separately; no metadata is replaced.'
  else:assert nr['state']=='no_unique_exact_inventory_result';note+=' Public native inventory search returned no exact object; approval relies on referenced saved exact object evidence,not native confirmation.'
  net_assertion=None
  if in_network:
   assert aid in neth;net_assertion=neth[aid]['assertion_id']
   if not hold:
    assert nr['state']=='captured_exact_inventory' and nr['parsed']['headings']==['FINE ART : PAINTINGS'];issues.remove('existing_institution_requires_review');confidence=.85;note+=' Branch refinement is an editorial inference from this exact BELUM inventory and Fine Art:Paintings department,the official policy placing Fine Art under Ulster Museum,and exact referenced Wikidata collection/location claims naming Ulster. Existing NMNI network evidence is compatible broader context; preserve it in superseded assertion history. This does not merge network and branch authorities.'
  if v['date_precision']=='unknown':note+=' Unknown or broad dates stay unknown and do not enter eligible-date counts; no lifespan or acquisition year is substituted.'
  if not hold:assert not issues and art['current_institution_id'] in [None,NETWORK] and art['status']=='review'
  out.append(dict(number=number,institution_id=row['institution_id'],existing_artwork_id=aid,facts=v,state='editorial_hold' if hold else 'approved_existing_holding',confidence=None if hold else confidence,basis=hold or 'Exact existing object ID,title/alias,creator identity,referenced museum-scoped inventory and creation evidence checked. '+note,limitation=LIMIT,derived_fields=[],retrieved_at=source['pending_assertion']['checked_at'],source_reference=source['body_reference'],source_raw_sha256=source['raw_sha256'],native_evidence_reference=native_ref,pending_assertion_id=source['pending_assertion']['id'],previous_network_assertion_id=net_assertion,previous_institution_id=art['current_institution_id'],comparison=c,source_issues=v['issues'],resolved_issues=[j for j in v['issues'] if j not in issues],existing_status=art['status']))
 assert len(out)==239;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build();names=['source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','unlinked-creator-authorities-001.json.gz','brighton-native-001.json.gz','ulster-native-001.json.gz','ulster-network-context-001.json.gz'];m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='Individual selected existing holding links and explicit network-to-branch refinements only. Preserve unknown dates,qualification conflicts,versions and existing review status. No new artworks,images or display claims.'))
 print(json.dumps(dict(approved=sum(v['state']=='approved_existing_holding' for v in ds),held=[v['number'] for v in ds if v['state']=='editorial_hold'],by_museum=dict(collections.Counter(v['institution_id'] for v in ds if v['state']=='approved_existing_holding')),branch_refinements=sum(v['state']=='approved_existing_holding' and bool(v['previous_network_assertion_id']) for v in ds))),flush=True)
if __name__=='__main__':main()
