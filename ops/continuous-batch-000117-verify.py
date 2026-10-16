"""One bounded icon research verification; production read-only, no scheduler."""
import importlib.util,json,gzip,fcntl,os,csv,datetime,subprocess,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('b117',Path(__file__).with_name('continuous-batch-000117-research.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E;R=b.R;save=b.save
zero=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
with (R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 rows=[];captures=[]
 q=h.load(E.parents[1]/'source-queue.json');mds=next(r for r in q['sources'] if r['source_id']=='museum_data_service_uk');prior=set(mds['icon_resume_cursor']['processed_source_ids'])
 for page in [3,4,5]:
  rp=(E.parent/'000114' if page==3 else E)/f'mds-icon-page{page}.receipt.json';rc=h.load(rp);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
  captures.append(dict(page=page,receipt=str(rp.relative_to(b.ROOT)),sha256=rc['sha256'],bytes=len(raw),status=200,cached_from_prior_batch=page==3))
  cards=b.BeautifulSoup(raw,'html.parser').select('details.object-overview');assert len(cards)==20
  for offset,d in enumerate(cards):
   if page==3 and offset<10:continue
   fields=[(x.dt.get_text(' ',strip=True).rstrip(':'),x.dd.get_text(' ',strip=True)) for x in d.select('dl div') if x.dt and x.dd]
   tx=d.get_text(' ',strip=True);lic=tx.split('Use licence for this record: ')[1].split(' Attribution for this record:')[0];url=next(a['href'] for a in d.select('a[href]') if a['href'].startswith('https://museumdata.uk/objects/'));pid=url.rsplit('/',1)[-1]
   def vals(k):return [v for key,v in fields if key==k]
   reasons=[]
   if lic=='CC BY-NC':reasons.append('Contributor metadata is CC BY-NC; commercial production reuse unresolved. No image licence inferred.')
   if (page,offset) in [(4,4),(5,0),(5,1)]:
    assert 'Cast icon' in tx or 'cast icons' in tx
    reasons.append('Cast brass relief, not a painted icon; no explicit creation date. Group 1976.504 and components 1976.504.1/.2 must not become three artwork additions. C1249/C1250 are external numbers, not inferred medieval years.')
   if (page,offset)==(3,18):
    assert 'stone' in vals('Material');reasons.append('Stone religious object; painted surface and creation date unsupported.')
   if (page,offset)==(4,12):reasons.append('Set of six commemorative medallions, not an eligible pictorial artwork. Manufacturing creator label is not a painter.')
   if (page,offset)==(5,3):reasons.append('2016 reference book, not an eligible original pictorial object; editor is not an artwork creator.')
   if (page,offset) in [(3,15),(4,14),(4,17),(5,5),(5,17),(5,19)]:reasons.append('Explicit modern/non-pictorial object or publication; no catalogue-work selection.')
   if (page,offset) in [(5,11),(5,18)]:reasons.append('Source literal eighteenth or possibly early twentieth century conflicts with structured latest2000; preserve uncertainty and historic authenticity debate; no forced date.')
   if (page,offset)==(3,16):reasons.append('Two physical icons share one record/display box; do not fabricate independent identifiers.')
   assert reasons and pid not in prior,pid
   rows.append(dict(source_id=pid,url=url,page=page,offset=offset,title=vals('Title'),collection=vals('Collection'),accession=vals('Object number'),creator_labels=vals('Object production person'),metadata_license=lic,fields=fields,decision='held',reasons=reasons,capture_sha256=rc['sha256'],images_requested=0))
 assert len(rows)==len({r['source_id'] for r in rows})==50
 save('object-research-and-holds.json',dict(at=h.now(),records=rows,distinct_records=50,selected=0,scope='Object-search expanded detail cards, not individually fetched native object pages. Some are grouped records or books; not counted as50 eligible artworks.'))
 save('independent-source-verification.json',dict(at=h.now(),passed=True,captures=captures,new_distinct_object_records=50,overlap_with_prior_processed_ids=0,license_counts=dict(collections.Counter(r['metadata_license'] for r in rows)),selected=0,images_downloaded=0,actual_visual_reviews=0))
 save('production-target-verification.json',b.base.target())
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 save('proxy-configuration-verification.json',dict(at=h.now(),connection_name=actual,helper='ops/india-300-delivery-20261011.py',read_only=True))
 ids=[r['source_id'] for r in rows];urls=[r['url'] for r in rows];accs=list({a for r in rows for a in r['accession']})
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  prev=h.load(E.parent/'000114/batch107-live-reconciliation.json');states=next(v for v in prev.values() if isinstance(v,dict) and v and all(isinstance(x,dict) and 'artwork' in x for x in v.values()));assert h.snapshot(db,list(states))==states
  save('batch107-live-reconciliation.json',dict(at=h.now(),verified_ids=list(states),unchanged=True,new_increments=0,prior_receipt_sha256=h.sha((E.parent/'000114/batch107-live-reconciliation.json').read_bytes())))
  p109=h.load(E.parent/'000109/independent-production-verification.json');a109=h.snapshot(db,list(p109['after']));assert a109==p109['after']
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name='continuous_mds_object_evidence_b000109'",(list(a109),))];assert len(notes)==2 and all(x['plan_sha256']==p109['plan_sha256'] for x in notes)
  save('batch109-live-reconciliation.json',dict(at=h.now(),verified_ids=list(a109),unchanged=True,persisted_plan_sha256=p109['plan_sha256'],citations=notes,new_increments=0))
  native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))",(ids,urls))]
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
  accessions=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',(accs,))]
  save('independent-production-verification.json',dict(at=h.now(),read_only=True,native_matches=native,citation_matches=citations,accession_leads=accessions,production_writes=0,new_programme_increments=zero,attribution='No selected plan, storage upload or write connection. Existing exact/native/accession matches and reconciled107/109 deliveries excluded from increments.'))
 reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')));assert len(reg)==111
 save('source-register.json',dict(at=h.now(),registry_source=next(x for x in reg if x['source_id']=='museum_data_service_uk'),policy='docs/ARTLINE_IMAGE_USE.md; contributor metadata licensing separate from images',access_status='Public HTML search200; cached page3 reused and pages4/5 captured once; no individual native/object/API/image requests.',remaining_gaps='No complete institution coverage.44 noncommercial records and6 out-of-scope/unresolved physical objects. Icon cursor page6; painting cursor unchanged.'))
 save('source-access-holds.json',dict(at=h.now(),inherited=['docs/research/continuous-production-20261011/batches/000114/source-access-holds.json','docs/research/continuous-production-20261011/batches/000109/source-access-holds.json','docs/research/source-index-delivery-20261010/inherited-source-access-holds.json'],held_provider_requests=0,new_access_failures=0,retries=0,images_requested=0))
 next_task='Rotate to the remaining10 unresearched Basel image-gap IDs using permitted independent sources; preserve native multimedia and Commons API holds. Skip every researched_artwork_id. MDS icon cursor is page6; painting cursor remains page2. Do not repeat the100 researched icon records or count prior107/109 deliveries.'
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);old=h.load(qp);q=json.loads(json.dumps(old));r=next(x for x in q['sources'] if x['source_id']=='museum_data_service_uk');assert r['icon_resume_cursor']['page']==3 and r['icon_resume_cursor']['offset']==10
  save('source-queue-before.json',old)
  r['icon_resume_cursor']=dict(query='icon',page=6,offset=0,next_url='https://museumdata.uk/object-search/?q=icon&i=6',processed_source_ids=sorted(prior|set(ids)),next_step='Rotate to another source first; if resuming icon search start page6 and skip these100 researched IDs.')
  r.update(last_batch=117,last_checked_at=h.now(),status='one_hundred_icon_query_records_researched_no_eligible_new_selection',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),latest_batch_verified_counts=zero,access_status='Public MDS HTML200; no held native provider or image requests.')
  r.setdefault('research_history',[]).append(dict(batch=117,at=h.now(),researched_new_records=50,selected=0,verified_counts=zero,evidence=str((E/'independent-source-verification.json').relative_to(b.ROOT))))
  r.setdefault('remaining_gaps',[]).append('Batch117:50 additional object cards reviewed;44 CC BY-NC and6 cast/stone/medallion/book records held. Group/component identities preserved; no eligible image or metadata selection.')
  for n in ['independent-source-verification.json','independent-production-verification.json','object-research-and-holds.json','batch109-live-reconciliation.json']:
   r.setdefault('evidence_paths',[]).append(str((E/n).relative_to(b.ROOT)))
  assert all(x==y for x,y in zip(old['sources'],q['sources']) if x['source_id']!='museum_data_service_uk')
  oldr=next(x for x in old['sources'] if x['source_id']=='museum_data_service_uk');assert oldr['resume_cursor']==r['resume_cursor'] and oldr['verified_counts']==r['verified_counts']
  tmp=qp.with_name('source-queue.b117.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp);assert h.load(qp)==q
  save('independent-queue-verification.json',dict(at=h.now(),passed=True,modified_source_ids=['museum_data_service_uk'],unrelated_entries_preserved=True,painting_cursor_preserved=True,cumulative_delivery_counts_preserved=True,icon_cursor=dict(page=6,offset=0,processed_ids=100),queue_sha256=h.sha(qp.read_bytes())))
 start=h.load(E/'required-input-verification.json')['at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 receipt=dict(at=end,batch=117,outcome='no_eligible_candidates',verified_counts=zero,researched_distinct_object_records=50,selected=0,prepared=0,imported=0,production_writes=0,storage_writes=0,local_catalogue_connections=0,actual_visual_reviews=0,measured_runtime_seconds=elapsed,prior107_reconciled=True,prior109_reconciled=True,next_task=next_task)
 save('batch-verification-receipt.json',receipt)
 refs=[str((E/n).relative_to(b.ROOT)) for n in ['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-queue-verification.json','batch107-live-reconciliation.json','batch109-live-reconciliation.json','object-research-and-holds.json']]
 cp=dict(receipt,status='complete',supervisor_unmodified=True,evidence_paths=refs,limitations='Only50 newly reviewed object search cards; no eligible artwork or image selected. Entire programme not exhausted. No images visually accepted.')
 save('CHECKPOINT.json',cp);h.save(R/'worker-checkpoint.json',cp);print(json.dumps(receipt,indent=2))
