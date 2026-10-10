"""Review selected existing holdings; do not rewrite artwork metadata."""
import collections,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
i=module('i','museum-expansion-britain-seven-identity-20261009.py');f=i.f;s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
g=module('g','museum-expansion-britain-seven-gac-selected-20261009.py');editor=module('ed','museum-expansion-britain-seven-decisions-20261009.py');HOLDS=editor.HOLDS;NOTES=editor.NOTES
LIMIT='Confidence is an editorial assessment,not a calibrated probability. Saved Wikidata collection/location statements and their ArtUK references are correlated secondary evidence,not independently fetched primary confirmation. Exact Guildhall publisher corroboration is separately identified. Holdings do not establish ownership,current custody or current display. Preserve metadata,dates,qualified/unlinked creator labels,images and review status. Unknown dates do not establish pre1971 eligibility.'
RESOLVED={2:['missing_exact_artuk_reference'],7:['filename_or_title_qualification'],54:['filename_or_title_qualification'],72:['missing_exact_artuk_reference'],144:['filename_or_title_qualification']}
def native_rows():
 x=m.load(RUN/'guildhall-gac-selected-001.json.gz');assert not x['requests_stopped'] and not x['unprocessed'];out=collections.defaultdict(list)
 for v in x['rows']:
  row=m.load(checked(v['reference']));assert row['state']=='captured_metadata';row['evidence_reference']=v['reference']
  for h in row['candidate_leads']:out[h['number']].append(row)
 assert set(out)=={60,72,95,113} and sum(len(v) for v in out.values())==5;return out
def native_guard(number,rows):
 expected={60:('Richard Paton and Francis Wheatley','1789-1792'),72:('Briton Rivière','1898'),95:('Byam Shaw','1895'),113:('George Percy Jacomb-Hood','1885')};maker,date=expected[number];matches=[]
 for row in rows:
  p=row['parsed'];fields={v['label']:v['value'] for v in p['fields']};assert '/partner/guildhall-art-gallery' in p['partner_links'] and p['publisher_heading'].startswith('Guildhall Art Gallery')
  if fields.get('Creator')==maker and fields.get('Date Created')==date:
   assert fields['Location']=='Guildhall Art Gallery' and fields['Rights']=='City of London Corporation';matches.append(row)
 assert len(matches)==1;return matches[0]
def referenced_object_guard(source):
 # Specific artwork51017 reference has a browsing suffix; no request to ArtUK.
 url='https://artuk.org/discover/artworks/old-drury-lane-theatre-on-fire-london-24-february-1809-51017/search/keyword:old-drury-lane-theatre-on-fire'
 for prop in ['P170','P571','P195','P217']:
  claims=source['entity']['claims'][prop];assert any(url==v.get('datavalue',{}).get('value') for c in claims for r in c.get('references',[]) for v in r.get('snaks',{}).get('P854',[]))
def build():
 src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};rs=f.rows();cs={v['number']:v for v in m.load(RUN/'identity-001.json.gz')['comparisons']};own={v['existing_artwork_id'] for v in rs};verified={v['number']:v for v in m.load(RUN/'unlinked-creator-authorities-001.json.gz')['rows']};native=native_rows();out=[];invs=collections.defaultdict(list)
 for row in rs:invs[(row['institution_id'],i.i.q.compact(row['facts']['inventory']))].append(row['number'])
 for numbers in invs.values():
  if len(numbers)>1:assert all(n in HOLDS for n in numbers)
 for row in rs:
  number=row['number'];v=row['facts'];source=src[number];art=source['artwork'];aid=art['id'];c=cs[number];assert c['source_hits'] and {h['entity_id'] for h in c['source_hits']}=={aid};hold=HOLDS.get(number)
  external=[h for h in c['hits'] if h['id'] not in own and h['same_creator']];assert not external or number in NOTES or hold,('Unreviewed comparison',number)
  issues=list(v['issues']);note=NOTES.get(number,'Exact source object,creator and museum-scoped inventory reviewed. Generic title matches do not identify different creator identities.');confidence=.8;native_url=None;native_ref=None
  if 'creator_authority_requires_reconciliation' in issues:
   author=verified[number];assert author['label_match'] and author['qid']==v['creator_qid'] and author['existing_label']==v['creator_label'];issues.remove('creator_authority_requires_reconciliation');note+=' Exact source authority verifies existing unlinked creator text only; no artist record or painter link is added.'
  if number==2:referenced_object_guard(source)
  for issue in RESOLVED.get(number,[]):assert issue in issues;issues.remove(issue)
  if number in native:
   nr=native_guard(number,native[number]);native_url=nr['card']['url'];native_ref=nr['evidence_reference'];confidence=.9
  else:note+=' No exact native object corroboration is claimed. Official general collection pages are context only; the holding basis remains the referenced museum-scoped secondary object.'
  if any(h['id'] not in own and not h['same_creator'] and 'inventory' in h['hit_types'] for h in c['hits']):note+=' Bare accession collisions in other creator/collection scopes are not object identity.'
  if v['date_precision']=='unknown':note+=' Creation remains unknown and excluded from eligible-date totals. Acquisition,subject,career and artist life dates are not substituted.'
  if v['inventory'].startswith('KH'):assert hold,'Unreviewed Keats institution mapping'
  if source.get('additional_pending_assertions'):assert hold,'Unreviewed multiple pending claims'
  if not hold:assert not issues and art['current_institution_id'] is None and art['status']=='review',('Unresolved issue',number,issues)
  out.append(dict(number=number,institution_id=row['institution_id'],existing_artwork_id=aid,facts=v,state='editorial_hold' if hold else 'approved_existing_holding',confidence=None if hold else confidence,basis=hold or 'Exact existing object ID,title/alias,creator,referenced museum-scoped inventory and chronology checked. '+note,limitation=LIMIT,derived_fields=[],retrieved_at=source['pending_assertion']['checked_at'],source_reference=source['body_reference'],source_raw_sha256=source['raw_sha256'],native_evidence_reference=native_ref,selected_native_object_url=native_url,pending_assertion_id=source['pending_assertion']['id'],additional_pending_assertion_ids=[h['id'] for h in source.get('additional_pending_assertions',[])],previous_network_assertion_id=None,previous_institution_id=art['current_institution_id'],comparison=c,source_issues=v['issues'],resolved_issues=[j for j in v['issues'] if j not in issues],existing_status=art['status']))
 assert len(out)==201;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build();names=['source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','retained-primary-comparisons-001.json.gz','unlinked-creator-authorities-001.json.gz','guildhall-gac-selected-001.json.gz','native-probes-001.json','keats-institution-context-001.json','new-source-access-holds-001.json','salford-catalogue-probe-001.json'];m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),editorial_notes_reference=ref(Path(editor.__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='Selected existing holdings only. No new artworks,metadata,images,painter links,publication or display changes. Duplicate pending assertions stay with one held object. Keats House branch mappings,paired sides,attribution conflicts and ambiguous versions remain held.'))
 print(json.dumps(dict(approved=sum(v['state']=='approved_existing_holding' for v in ds),held=[v['number'] for v in ds if v['state']=='editorial_hold'],by_museum=dict(collections.Counter(v['institution_id'] for v in ds if v['state']=='approved_existing_holding')),unknown_dates_preserved=sum(v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown' for v in ds))),flush=True)
if __name__=='__main__':main()
