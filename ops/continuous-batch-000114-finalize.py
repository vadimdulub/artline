"""Verify researched records and persist one bounded no-write checkpoint."""
import importlib.util,json,gzip,fcntl,os,collections,datetime
from pathlib import Path
s=importlib.util.spec_from_file_location('r114',Path(__file__).with_name('continuous-batch-000114-research.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E;R=b.R;save=b.save
rows=[];captures=[]
for page in [1,2,3]:
 rc=h.load(E/f'mds-icon-page{page}.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'];captures.append(dict(page=page,sha256=rc['sha256'],bytes=len(raw),status=200))
 cards=b.BeautifulSoup(raw,'html.parser').select('details.object-overview');assert len(cards)==20
 for offset,d in enumerate(cards[:10] if page==3 else cards):
  fields=[(x.dt.get_text(' ',strip=True).rstrip(':'),x.dd.get_text(' ',strip=True)) for x in d.select('dl div') if x.dt and x.dd]
  text=d.get_text(' ',strip=True);url=next(a['href'] for a in d.select('a[href]') if a['href'].startswith('https://museumdata.uk/objects/'));pid=url.rstrip('/').split('/')[-1]
  def vals(key):return [v for k,v in fields if k==key]
  license=text.split('Use licence for this record: ')[1].split(' Attribution for this record:')[0]
  if license=='CC BY-NC':reason='Contributor metadata licence CC BY-NC: commercial production reuse unresolved; retain research only.'
  elif pid in ['bb958ca9-5d53-3a86-b6b2-d573e7e1aa46','11a17ff6-d9c0-3816-a2ac-428995a3dc22']:reason='Non-pictorial manufactured object; keyword icon is not artwork identity.'
  elif pid=='23aeb86f-b6d0-3bb5-8ef1-a92ac6d3432f':reason='Modern reproduction explicitly made 1983-08, after1970; medieval subject is not creation date.'
  elif pid=='27c4404e-c960-3a30-8850-096c5cee90e5':reason='Twentieth Century crosses1970; three contemporary icons versus one object unit unresolved; acquisition/person association is not secure authorship.'
  else:
   assert not vals('Object production date'),pid
   reason='No creation date; no through1970 eligibility inferred from acquisition or icon subject. Curatorial Care does not establish ownership.'
  rows.append(dict(source_id=pid,url=url,page=page,offset=offset,title=vals('Title'),accession=vals('Object number'),collection=vals('Collection'),creator_labels=vals('Object production person'),metadata_license=license,fields=fields,decision='held',reason=reason,capture_sha256=rc['sha256'],image_requests=0))
assert len(rows)==len({x['source_id'] for x in rows})==50
save('object-research-and-holds.json',dict(at=h.now(),reviewed=50,selected=0,records=rows,unreviewed_captured_page3_offsets=list(range(10,20)),scope='50 object search result detail cards; not 50 individually fetched object pages; no directory entries counted.'))
save('independent-source-verification.json',dict(at=h.now(),passed=True,checked_captures=captures,unique_researched_objects=50,selection_count=0,decision_counts=dict(collections.Counter(r['reason'] for r in rows)),license_counts=dict(collections.Counter(r['metadata_license'] for r in rows)),downloaded_images=0,viewed_images=0))
# Bounded live reconciliation of exact native identities. No broad count or mutation.
ids=[r['source_id'] for r in rows];urls=[r['url'] for r in rows];accs=list({a for r in rows for a in r['accession']})
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
 native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))",(ids,urls))]
 citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
 accessions=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',(accs,))]
 save('independent-production-verification.json',dict(at=h.now(),read_only=True,native_matches=native,citation_matches=citations,accession_leads=accessions,production_writes=0,new_programme_increments=0,attribution='No import plan, storage upload or write transaction executed; any matching prior records are excluded from additions. Batch107 matched saved live snapshot.'))
next_task='Research Basel\u2019s 23 pending image gaps using permitted WikiArt/Commons routes. Preserve native provider holds. MDS icon research can resume from cached page3 offset10; painting query remains at page2.'
zero=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
queue=E.parents[1]/'source-queue.json';touched={'museum_data_service_uk','mnaa_portugal','royal_collection_trust'}
with (E.parents[1]/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 before=h.load(queue);save('source-queue-immediately-before-update.json',before);after=json.loads(json.dumps(before))
 for r in after['sources']:
  if r['source_id'] not in touched:continue
  r['last_checked_at']=h.now();r['checkpoint']=str((E/'CHECKPOINT.json').relative_to(b.ROOT));r.setdefault('evidence_paths',[])
  for name in ['independent-source-verification.json','source-access-holds.json','independent-production-verification.json','object-research-and-holds.json']:
   ref=str((E/name).relative_to(b.ROOT))
   if ref not in r['evidence_paths']:r['evidence_paths'].append(ref)
  if r['source_id']=='museum_data_service_uk':
   r['status']='fifty_icon_query_objects_researched_no_eligible_metadata_selection';r['icon_resume_cursor']=dict(query='icon',page=3,offset=10,captured_page3_receipt=str((E/'mds-icon-page3.receipt.json').relative_to(b.ROOT)),processed_source_ids=ids,next_step='Resume cached page3 offset10, retaining per-object metadata/date/medium holds; painting cursor unchanged.');r['latest_batch_verified_counts']=zero
   r.setdefault('remaining_gaps',[]).append('Batch114:50 icon-query detail cards researched, none selected. CC BY-NC data reuse holds, undated/open twentieth-century and non-pictorial/modern records explicit. Images unrequested.')
  else:
   r['status']='official_collection_TLS_hostname_mismatch_hold' if r['source_id']=='mnaa_portugal' else 'historical_native_http403_hold_reconciled_navigation_only_search_lead'
   r['resume_cursor']=dict(retry_allowed=False,next_step='Rotate sources; require documented access change before provider requests.',url='https://museudearteantiga.pt/collections' if r['source_id']=='mnaa_portugal' else 'https://www.rct.uk/collection/403476/christ-pantocrator-with-the-virgin-and-st-john-the-baptist-the-deisis')
   r['policy_reference']='Original111-source registry and docs/ARTLINE_IMAGE_USE.md; preserve source-specific access and image permission holds.'
 temp=queue.with_name('source-queue.b114.tmp');temp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(temp,queue)
 live=h.load(queue);assert live==after
 for old,new in zip(before['sources'],live['sources']):
  if old['source_id'] not in touched:assert old==new
 m0=next(r for r in before['sources'] if r['source_id']=='museum_data_service_uk');m1=next(r for r in live['sources'] if r['source_id']=='museum_data_service_uk');assert m0['resume_cursor']==m1['resume_cursor']
 save('source-queue-after.json',live)
 save('independent-queue-verification.json',dict(at=h.now(),passed=True,modified_source_ids=sorted(touched),unrelated_entries_preserved=True,original_painting_cursor_preserved=True,icon_cursor=dict(page=3,offset=10),queue_sha256=h.sha(queue.read_bytes())))
start=h.load(E/'required-input-verification.json')['at'];runtime=(datetime.datetime.fromisoformat(h.now())-datetime.datetime.fromisoformat(start)).total_seconds()
receipt=dict(at=h.now(),batch=114,outcome='no_eligible_candidates',verified_counts=zero,discovered_object_cards=60,researched_distinct_objects=50,selected=0,prepared=0,imported=0,verified_production_additions=0,production_writes=0,image_requests=0,visually_viewed_images=0,measured_runtime_seconds=runtime,prior107_reconciled=True,next_task=next_task,limitations='50 search-result object detail cards reviewed; ten additional captured cards remain unreviewed. No complete institutional coverage or autonomous-supervisor changes claimed.')
save('batch-verification-receipt.json',receipt)
cp=dict(at=h.now(),batch=114,stage='complete_no_eligible_candidates',verified_counts=zero,next_task=next_task,prior107_reconciled=True,supervisor_unchanged=True,receipt=str((E/'batch-verification-receipt.json').relative_to(b.ROOT)))
save('CHECKPOINT.json',cp);h.save(R/'worker-checkpoint.json',cp)
print(json.dumps(receipt,indent=2))
