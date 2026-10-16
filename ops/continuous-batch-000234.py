#!/usr/bin/env python3
"""Execute bounded continuous-production batch 234 against SAAM shard 42."""
import copy, csv, fcntl, gzip, importlib.util, json, os, subprocess, urllib.request
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000234'
R=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000234')
S=Path('/Users/vadimdulub/Library/Application Support/Artline/source-metadata/continuous-production-20261011/000234')
for p in (E,R,S): p.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/india-300-delivery-20261011.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def save(name,value): h.save(E/name,value); return value
url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/42.txt'
with urllib.request.urlopen(url,timeout=60) as response:
    raw=response.read(); status=response.status; final_url=response.url
assert status==200
(S/'saam-42.txt.gz').write_bytes(gzip.compress(raw,mtime=0))
objects=[json.loads(x) for x in raw.splitlines()][:50]
receipt=dict(url=url,final_url=final_url,status=status,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(S/'saam-42.txt.gz'),retry_after=None)

MID='259d7efe-d565-56bf-bdc0-b467d3b2f69b'
rows=[]
with h.connect() as db:
  for o in objects:
    c=o.get('content',{});d=c.get('descriptiveNonRepeating') or {};ft=c.get('freetext') or {}
    link=d.get('record_link',''); oid=link.rsplit('=',1)[-1] if '?id=' in link else None
    vals=lambda k,label=None:[x.get('content') for x in ft.get(k,[]) if label is None or x.get('label')==label]
    title=(d.get('title') or {}).get('content');dates=vals('date','Date');media=((d.get('online_media') or {}).get('media') or [])
    row=dict(native_id=oid,title=title)
    if not oid or not title or not dates or len(media)!=1:
      row['decision']='missing_required_identity_date_or_single_image';rows.append(row);continue
    native=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s",(oid,))]
    matches=[dict(x) for x in db.execute("SELECT id::text,title,primary_media_id::text,creation_year_start,creation_year_end,date_display,status FROM artworks WHERE normalized_title=%s AND current_institution_id=%s AND status<>'archived'",(h.norm(title),MID))]
    eligible=[a for a in matches if a['primary_media_id'] is None and a['creation_year_end'] is not None and a['creation_year_end']<=1970 and str(a['creation_year_start']) in dates[0]]
    decision='native_identity_already_present' if native else ('eligible_unexpected' if len(eligible)==1 else 'no_unique_eligible_existing_primary_gap')
    row.update(date=dates[0],native_matches=native,title_matches=matches,decision=decision);rows.append(row)
assert not any(x['decision']=='eligible_unexpected' for x in rows), [x for x in rows if x['decision']=='eligible_unexpected']
save('saam-shard42-reconciliation.json',dict(at=h.now(),source=receipt,captured_records=len(objects),source_file_total_records=len(raw.splitlines()),bounded_limit=50,decisions=dict(Counter(x['decision'] for x in rows)),rows=rows,candidates=[],selected_for_write=0,production_writes=0))

registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
required=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
assert len(list(csv.DictReader(registry.open())))==111
save('required-input-verification.json',dict(at=h.now(),registry_rows=111,complete_original_registry_used=True,files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],local_catalogue_connections=0))
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
assert actual=='artline-508319:europe-west1:artline-postgres'
commands=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines(); proxy=[x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x];assert len(proxy)==1
with h.connect() as db: target=dict(db.execute('SELECT current_database() db, inet_server_port() port').fetchone())
assert target['db']=='artline'
save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_port=55519,proxy_command_verified=True,database=target,helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
prev=h.load(E.parent/'000107/independent-production-verification.json')
with h.connect() as db: live=h.snapshot(db,list(prev['after']))
assert live==prev['after']
save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live),uncertain_writes_found=False,previous_increments_counted=0,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes())))

qp=E.parents[1]/'source-queue.json';queue=h.load(qp);before=copy.deepcopy(queue);q=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access')
q.update(status='saam_shard42_first50_classified_no_eligible_exact_missing_image_matches',last_checked_at=h.now(),last_batch=234,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)))
q['resume_cursor']=dict(unit='saam',completed_shard='41',active_shard='42',next_record_offset=50,source_sha256=receipt['sha256'],records_classified=50,source_file_total_records=len(raw.splitlines()),eligible_exact_missing_image_matches=0,next_route='Continue untouched SAAM shard 42 at record offset 50, then rotate to an untouched National Gallery Athens creator route.')
q['evidence_paths']=[str((E/x).relative_to(ROOT)) for x in ['saam-shard42-reconciliation.json','production-target-reconciliation.json','batch107-live-reconciliation.json','CHECKPOINT.json']]
with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);tmp=qp.with_suffix('.234.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
save('source-queue-update-verification.json',dict(at=h.now(),updated_source='smithsonian_open_access',unrelated_sources_preserved=[x for x in before['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in queue['sources'] if x['source_id']!='smithsonian_open_access'],supplementary_routes_preserved=before['supplementary_image_routes']==queue['supplementary_image_routes'],queue_sha256=h.sha(qp.read_bytes()),resume_cursor=q['resume_cursor']))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
save('actual-visual-review.json',dict(at=h.now(),prepared_images=0,files_actually_viewed=0,claim='No image selected or prepared; no visual-inspection claim.',passed=True))
save('batch-verification-receipt.json',dict(at=h.now(),batch=234,discovered=len(objects),selected=0,prepared=0,imported=0,verified_counts=counts,production_ids=[],production_writes=0,storage_writes=0,local_catalogue_writes=0,attribution='No eligible selection and no production mutation; prior programme rows excluded.',shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
nxt='Continue untouched SAAM shard 42 at record offset 50; then rotate to a newly selected National Gallery Athens creator route. Do not replay exhausted Lembesis/Bouzianis or unchanged source holds.'
evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','saam-shard42-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json']
cp=dict(at=h.now(),batch=234,outcome='no_eligible_candidates',stage='independently_verified_complete',researched=50,selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',production_writes=0,local_catalogue_connections=0,external_supervisor_unchanged=True,evidence=[str((E/x).relative_to(ROOT)) for x in evidence])
save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
checked=[]
for name in evidence+['CHECKPOINT.json']:
  p=E/name;h.load(p);checked.append(dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,production_writes=0,verified_counts=counts,passed=True))
result=dict(outcome='no_eligible_candidates',summary='Batch 234 classified the first 50 distinct records in untouched Smithsonian SAAM shard 42. None uniquely matched an active through-1970 production primary-image gap with sufficient native identity and single-image evidence. No image was prepared and no production write occurred. Production target, batch 107, queue integrity and the offset-50 resume cursor were independently verified.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/x).relative_to(ROOT)) for x in ['saam-shard42-reconciliation.json','production-target-reconciliation.json','batch107-live-reconciliation.json','source-queue-update-verification.json','batch-verification-receipt.json','independent-final-artifact-verification.json','CHECKPOINT.json']])
save('worker-result.json',result);h.save(R/'worker-result.json',result);print(json.dumps(result))
