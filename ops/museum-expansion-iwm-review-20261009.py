"""Review103 exact IWM objects;99 supported network holdings and4 version holds."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-iwm-facts-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
HOLDS={13:'Gledstanes Greenwich naval drill LD6087 versus courtyard LD6088: same venue and closely similar59.7x76.3cm/60.8x77.1cm formats. Resolve composition and physical versions before counting both.',52:'Gledstanes Greenwich courtyard LD6088 versus naval drill LD6087: different titles alone do not settle the near-identical format and shared scene.',44:'Flint Walcheren LD5465 versus LD5464: both1945 and49.5cm high,60cm versus65cm wide. Resolve composition and measurement/version discrepancy before accepting both.',85:'Flint attacking rocket ship LD5464 versus ships in firing position LD5465: closely related titles and5cm width difference require composition verification.'}
NOTES={
 5:'Explicit preparatory study ART16669,29.1x34.9cm,versus finished ART4205,182.8x220cm. Separate physical scale and accession; preserve the study title.',
 6:'Loading Tanks for Russia LD1922 is1941,48.2x41.2cm; explicitly numbered sequel II LD1969 is1942,52.7x39.3cm. Separate dated,inventoried source objects.',
 7:'Marshall ART2000 and Pierse ART3056 name different sitters and have separate dates and inventories.',
 12:'FreshQ20011765 confirms William Thomas Wood1877–1958 and exact existing unlinked maker label. No new artist link.',
 16:'Training School is part of the literal subject,not a school-attribution qualifier.',
 17:'IWM Evacuees Growing Cabbages LD428,1940,24.7x29.5cm,is separate from Evacuees AC64,1941,30.2x40.3cm in sourceQ119790236. Preserve that comparison object and its unresolved holding.',
 21:'Hailstone’s Dempsey LD5856 and Mountbatten LD5840 identify different named sitters; shared honours are not identity.',
 26:'Bapaume ART6347,Nieuport ART6345 and Mine Craters at Albert ART6346 are separately inventoried aerial views of different named places. The latter has retained native page4315 and stays unchanged.',
 30:'Mainframe has no creation statement. Preserve unknown date; no conclusion of pre1971 eligibility from maker birth,accession or subject.',
 32:'Pierse and Marshall are different named sitters,not alternate honorific versions of one portrait.',
 34:'Ben Ledi ART2295 and Ben Lomond ART3982 are different named vessels; retain both source identities.',
 36:'Wood’s White Tower view ART1489 is60.9x76.2cm,while Last Phase ART877 is76.2x71.1cm. Distinct format and named composition support separate views of the same fire. Exact existing Wood label retained.',
 39:'Commons metadata for exact ART2249 describes a half-length skipper with flat cap and dark polo-neck jumper. ART2254 is a head-and-shoulders able seaman in a neckerchief looking left. Different compositions despite equal41.2x31.1cm formats; no image bytes or independent visual comparison claimed.',
 41:'Exact Commons ART2254 description differs from ART2249 in crop,dress and pose. Separate physical portraits,not one renamed naval subject.',
 46:'The Bandstand by Morland Lewis is another maker and source identity; Connard ART1290 stays distinct.',
 51:'Nieuport ART6345 differs from Bapaume ART6347 and the separately catalogued Albert mine craters ART6346.',
 56:'Exact fresh Wood authority supports the existing object-level maker label. Named Doiran-front view and source inventory retained.',
 60:'Loading Tanks II LD1969 explicitly names the sequel and has a1942 date,versus1941 LD1922. Dimensions and inventories are preserved separately.',
 62:'P195 is Wikipedia-derived,not an ArtUK-referenced collection statement. Exact Commons file suppliesQ21575028,1915,maker Kennington and IWM native15145; filename carriesART15661. This museum-derived secondary evidence supports broader IWM membership,not newly fetched native confirmation or London location.',
 63:'Ben Lomond ART3982 and Ben Ledi ART2295 name separate ships; no title-similarity merge.',
 74:'Finished ART4205 is182.8x220cm; preparatory study ART16669 is29.1x34.9cm. Both are separately catalogued physical works.',
 79:'Last Phase ART877 is76.2x71.1cm versus White Tower view ART1489,60.9x76.2cm. Different formats/compositions,with exact Wood maker label retained.',
 89:'Native page has a First World War production period but no exact production-date field. Existing1914–1918 range remains unchanged; holding identity rests on title,maker andART631.',
 90:'FreshQ16856083 lists Sydney William Carline as the existing Sydney Carline’s alias. After the Italian Advance is a subject phrase,not after-another-artist. Native1918-11-01 retains greater precision than existing1918 without rewriting it.',
 91:'Native1916-04-01 and existing1916 agree in creation year. Preserve literal native precision as evidence.',
 92:'Native production-period wording does not replace existing1918–1919 range. ExactART3787,title and Haydn Reynolds Mackey identify the object.',
 93:'Native1915-10-01 and existing1915 agree in year; no date rewrite.',
 94:'FreshQ19393256 identifies Cecil Constant Philip Lawson1880–1967,not landscape painter Cecil Gordon Lawson. Generic Untitled hits have different makers and no matching source/inventory. Preserve exactART5879 and native dimensions.',
 95:'FreshCecil Lawson authority includes Cecil Constant Philip Lawson; nativeART5892 and literal title agree. Production period does not substitute a new exact date.',
 96:'Native Bomb Disposal has Second World War content only,no production date. Preserve unknown date; historical subject does not date creation.',
 97:'NativeART3197,maker Stuart Reid and title identify The Bott Incident. Existing circa1918–1920 remains alongside First World War production-period wording.',
 98:'Cecil Constant Philip Lawson is the verified existing maker identity. NativeART5897 and portrait-format228x146mm distinguish Kemilly Hill; existingcirca1916–1918 unchanged.',
 99:'Native Epéhy title andART3653 match. Title’s1918 event date and broad production period do not overwrite existing1918–1919.',
 100:'Retained native page explicitly calls this a copy by John Leigh-Pemberton of an Oswald Birley portrait whose original was at White’s Club. IWMARTLD5916 is the distinct99x76.2cm copy by the existing maker,not the Birley original. Copy qualification is retained in evidence; no attribution or ownership rewrite.',
 101:'Native eye-irritation work has Second World War content only. Existing creation remains unknown; historical content does not establish date.',
 102:'Native1945 lies within existing1944–1945; preserve existing range and exact source wording. William Little’s separate Mountbatten INF3/8 is another maker/object.',
 103:'NativeART1927,title and Victor MacClure identify the Gallipoli headquarters work. Broad war production period does not rewrite existingcirca1915–1918.'}
def raw_checked():
 cache={}
 def raw(dep,sha):
  path=checked(dep);key=str(path)
  if key not in cache:cache[key]=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
  assert hashlib.sha256(cache[key]).hexdigest()==sha;return cache[key]
 for name in ['source-context-002.json.gz','comparison-source-context-001.json.gz']:
  for row in m.load(RUN/name)['rows']:
   if not row.get('body_reference'):continue
   body=raw(row['body_reference'],row['raw_sha256'])
   if name.startswith('source-'):
    assert json.loads(body)['entities'][row['source_id']]==row['entity']
    if row.get('native_reference'):raw(row['native_reference'],row['native_raw_sha256'])
 c=m.load(RUN/'retained-institution-context-001.json.gz');body=raw(c['body_reference'],c['raw_sha256']);assert BeautifulSoup(body,'html.parser').get_text(' ',strip=True)==c['text'];assert 'Our Five Museums' in c['text']
 for name in ['institution-authorities-001.json.gz','selected-authorities-001.json.gz','selected-commons-descriptions-001.json.gz']:
  x=m.load(RUN/name);c=x['capture'];body=raw(ref(m.ROOT/c['body_path']),c['receipt']['sha256']);data=json.loads(body)
  if 'entities' in x:assert data['entities']==x['entities']
  else:assert data==x['data']
 for name in ['selected-commons-discovery-001.json.gz','selected-commons-discovery-002.json.gz']:
  for x in m.load(RUN/name)['rows']:
   c=x['capture'];body=raw(ref(m.ROOT/c['body_path']),c['receipt']['sha256']);assert json.loads(body)==x['data']
 return len(cache)
def build():
 initial=m.load(RUN/'initial-scope-001.json.gz');facts,errors=f.rows();assert not errors;identity=m.load(RUN/'identity-001.json.gz');assert identity['rows']==facts;comps={v['number']:v for v in identity['comparisons']};src={v['number']:v for v in m.load(RUN/'source-context-002.json.gz')['rows']};artists={v['id']:v for v in initial['painters']};auth=m.load(RUN/'selected-authorities-001.json.gz')['entities'];institutions=m.load(RUN/'institution-authorities-001.json.gz')['entities'];assert s.val(institutions[s.QID],'P361')['id']==s.QIDS[s.NETWORK]
 commons=m.load(RUN/'selected-commons-descriptions-001.json.gz')['data']['query']['pages'];texts=[v['revisions'][0]['slots']['main']['*'] for v in commons.values()];assert any('2249' in t and 'flat cap' in t for t in texts);assert any('2254' in t and 'neckerchief' in t for t in texts);ken=m.load(RUN/'selected-commons-discovery-002.json.gz')['rows'][-1]['data']['query']['pages'];kt=next(iter(ken.values()))['revisions'][0]['slots']['main']['*'];assert 'Q21575028' in kt and '/object/15145' in kt and '1915' in kt
 out=[]
 for row in facts:
  n=row['number'];r=src[n];a=r['artwork'];fact=row['facts'];comp=comps[n];assert {v['entity_id'] for v in comp['source_hits']}=={a['id']};state='editorial_hold' if n in HOLDS else 'approved_existing_holding'
  for link in fact['artist_links']:
   ar=artists[link['artist_id']]
   if fact['first']:assert not ((ar['birth_year'] and fact['last']<ar['birth_year']) or(ar['death_year'] and fact['first']>ar['death_year']))
  if state=='approved_existing_holding':
   allowed=[]
   if n in [12,36,56,79]:assert auth[fact['creator_qid']]['labels']['en']['value']==fact['creator_label'];assert not fact['artist_links'];allowed.append('creator_authority_requires_reconciliation')
   if n in [5,16,90,100]:allowed.append('filename_or_title_qualification')
   if n==62:allowed.append('missing_exact_artuk_collection_reference')
   if n>=89:allowed.append('native_date_wording_difference');assert r['native_object']['fields']['Catalogue number']
   if n in [90,94,95,98]:
    e=auth[fact['creator_qid']];names=[v['value'] for v in e['labels'].values()]+[v['value'] for vs in e.get('aliases',{}).values() for v in vs];assert f.namekey(fact['native_object']['fields']['Creator'][0]) in [f.namekey(v) for v in names];allowed.append('native_creator_name_difference')
   assert not set(row['issues'])-set(allowed),(n,row['issues']);assert fact['last'] is None or fact['last']<=1970
  basis='Exact artwork QID,creator and IWM-qualified inventory identify this physical object. '
  basis+=('Retained official object page independently corroborates title,maker and normalized inventory. ' if r.get('native_object') else 'Saved secondary collection statement and exact object reference support membership of the wider IWM collection. ')
  basis+=NOTES.get(n,'No unresolved same-maker physical-version conflict survives the bounded source,title,inventory and collection comparison.')
  limitation='Accept only Imperial War Museums network membership. Keep every unaccepted London-specific assertion unresolved; no new London location,custody,ownership or current display claim. Saved Wikidata/ArtUK statements are correlated secondary evidence; ArtUK and IWM were not newly fetched after access holds. Retained native pages date from5October2026. Existing dates,attributions,creator links,images,status and descriptive metadata remain unchanged. Confidence is editorial,not a calibrated probability.'
  if fact['date_precision']=='unknown':limitation+=' Unknown creation excluded from eligible pre1971 totals; neither accession nor historical subject dates substituted.'
  out.append(dict(number=n,state=state,institution_id=s.NETWORK,source_institution_id=r['institution_id'],existing_artwork_id=a['id'],previous_institution_id=None,pending_assertion_id=r['pending_assertion']['id'],supersede_assertion_ids=[r['pending_assertion']['id']] if state=='approved_existing_holding' and r['institution_id']==s.NETWORK else [],facts=fact,comparison=comp,source_reference=r['body_reference'],source_raw_sha256=r['raw_sha256'],native_reference=r.get('native_reference'),native_raw_sha256=r.get('native_raw_sha256'),retrieved_at=r['pending_assertion']['checked_at'],confidence=.9 if r.get('native_object') else .85,basis=basis,limitation=limitation,hold_reason=HOLDS.get(n),metadata_review_note=NOTES.get(n)))
 assert collections.Counter(v['state'] for v in out)=={'approved_existing_holding':99,'editorial_hold':4};assert sum(len(v['supersede_assertion_ids']) for v in out)==15;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();bodies=raw_checked();decisions=build();paths=[RUN/n for n in ['initial-scope-001.json.gz','source-context-002.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','native-probes-001.json','institution-authorities-001.json.gz','retained-institution-context-001.json.gz','selected-authorities-001.json.gz','selected-commons-discovery-001.json.gz','selected-commons-discovery-002.json.gz','selected-commons-descriptions-001.json.gz']];m.save(dest,dict(at=m.now(),decisions=decisions,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(p) for p in paths],verified_raw_bodies=bodies,policy='99 selected existing-object network holdings,including15 with retained primary pages. Four physical-version holds. Three dates remain unknown. Preserve13 existing London and34 existing network holdings,all88 unresolved London claims,and every legacy field.'))
 print(json.dumps(dict(approved=99,held=4,unknown=3,native=15,london_claims_preserved=88,verified_raw_bodies=bodies)),flush=True)
if __name__=='__main__':main()
