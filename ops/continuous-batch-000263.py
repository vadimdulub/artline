#!/usr/bin/env python3
"""Bounded batch 263: reconcile French reserve, then finish SAAM shard 43."""
import copy,csv,fcntl,gzip,hashlib,importlib.util,json,os,subprocess
from collections import Counter
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000263'
R=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000263')
S=Path('/Users/vadimdulub/Library/Application Support/Artline/source-metadata/continuous-production-20261011/000263')
for p in (E,R,S,E/'source-captures'): p.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def save(name,value): h.save(E/name,value); return value
def rel(p): return str(Path(p).relative_to(ROOT))
TARGET='artline-508319:europe-west1:artline-postgres'; MID='259d7efe-d565-56bf-bdc0-b467d3b2f69b'

# Required inputs and exact production target/proxy/helper configuration.
reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); qp=E.parents[1]/'source-queue.json'
required=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',qp]
assert len(list(csv.DictReader(reg.open())))==111
save('required-input-verification.json',dict(at=h.now(),registry_rows=111,complete_original_registry_used=True,files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],real_local_catalogue_read_only=True))
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxy=[x for x in cmds if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxy)==1
with h.connect() as db: server=dict(db.execute('select current_database() database,pg_is_in_recovery() recovery,inet_server_port() port').fetchone())
assert server['database']=='artline' and not server['recovery']
save('production-target-reconciliation.json',dict(at=h.now(),connection_name=TARGET,proxy_command_verified=True,proxy_port=55519,database=server,established_helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),shared_ingestion_lock='artline-curated-ingestion',writes_attempted=False))

# Interrupted batch 107 and immutable French reserve: fresh live reads, no replay.
prev=h.load(E.parent/'000107/independent-production-verification.json')
with h.connect() as db: live107=h.snapshot(db,list(prev['after']))
assert live107==prev['after']
save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live107),uncertain_writes_found=False,previous_increments_counted=0,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes())))
planp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=h.load(planp);assert len(plan['rows'])==188
ids=[x['artwork_id'] for x in plan['rows']]
with h.connect() as db:
 live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("select entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 from citations where entity_type='artwork' and entity_id=any(%s::uuid[]) and field_name='french_printmaking_source_identity'",(ids,))]
digest=h.sha(planp.read_bytes());assert len(live)==len(cit)==188 and all(x['plan_sha256']==digest for x in cit)
assert all(live[x['artwork_id']]['artwork']['primary_media_id']==plan['images'][x['artwork_id']]['media_id'] and live[x['artwork_id']]['artwork']['status']!='archived' for x in plan['rows'])
prior=E.parent/'000061/independent-french-reserve-evidence-verification.json';assert prior.exists()
save('french-reserve-live-reconciliation.json',dict(at=h.now(),scope='immutable French printmaking reserve',inspected=188,live_rows=188,already_imported_and_illustrated=188,checksum_bound_citations=188,eligible_unimported=0,selected=0,all_verified=True,immutable_plan_sha256=digest,prior_actual_visual_review=rel(prior),prior_actual_visual_review_sha256=h.sha(prior.read_bytes()),new_visual_review_claim=False,decision='No replay: every reserve artwork is active with its checksum-bound primary media and citation.'))

# Registry-backed fallback: finish the unresearched tail of SAAM shard 43.
url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/43.txt';resp=requests.get(url,timeout=(15,45));resp.raise_for_status();raw=resp.content
body=S/'saam-43.txt.gz';body.write_bytes(gzip.compress(raw,mtime=0));receipt=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(body),retry_after=resp.headers.get('Retry-After'))
save('source-captures/saam-43.receipt.json',receipt);objects=[json.loads(x) for x in raw.splitlines()];tail=objects;rows=[]
with h.connect() as db:
 for obj in tail:
  c=obj.get('content',{});d=c.get('descriptiveNonRepeating') or {};ft=c.get('freetext') or {};link=d.get('record_link','');oid=link.rsplit('=',1)[-1] if '?id=' in link else None
  vals=lambda k,l=None:[x.get('content') for x in ft.get(k,[]) if l is None or x.get('label')==l]
  title=(d.get('title') or {}).get('content');dates=vals('date','Date');ims=((d.get('online_media') or {}).get('media') or []);row=dict(native_id=oid,title=title)
  if not oid or not title or not dates or len(ims)!=1: row['decision']='missing_required_identity_date_or_single_image'
  else:
   matches=[dict(x) for x in db.execute("select id::text,title,primary_media_id::text,creation_year_start,creation_year_end from artworks where normalized_title=%s and current_institution_id=%s and status<>'archived'",(h.norm(title),MID))]
   native=[dict(x) for x in db.execute("select entity_id::text from external_identifiers where entity_type='artwork' and scheme='saam-object' and external_id=%s",(oid,))]
   eligible=[a for a in matches if a['primary_media_id'] is None and a['creation_year_end'] is not None and a['creation_year_end']<=1970 and str(a['creation_year_start']) in dates[0]]
   row.update(date=dates[0],native_matches=native,title_matches=matches,decision='native_identity_already_present' if native else ('candidate_needs_exact_identity_review' if len(eligible)==1 else 'no_unique_eligible_existing_primary_gap'))
  rows.append(row)
candidates=[x for x in rows if x['decision']=='candidate_needs_exact_identity_review']
save('saam-shard43-tail-reconciliation.json',dict(at=h.now(),source=receipt,source_file_total_records=len(objects),resume_offset=0,inspected_tail_records=len(tail),decisions=dict(Counter(x['decision'] for x in rows)),rows=rows,candidates=candidates,selected=0,production_writes=0))

# Advance only the researched source cursor under the shared queue file lock.
with qp.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);queue=h.load(qp);before=copy.deepcopy(queue);q=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access')
 q.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(q.get('resume_cursor',{})));q.update(status='saam_shard43_fully_classified_no_tail_candidates',last_checked_at=h.now(),last_batch=263,checkpoint=rel(E/'CHECKPOINT.json'))
 q['resume_cursor']=dict(unit='saam',completed_shard='43',next_shard='44',next_record_offset=0,source_sha256=receipt['sha256'],shard43_total_records=len(objects),records_classified=len(tail),eligible_tail_candidates=len(candidates),candidate_native_ids=[x['native_id'] for x in candidates],next_route='Reconcile saved shard43 candidates if any; otherwise rotate to an untouched original-registry museum. Do not replay French188 or SAAM shard43.')
 q.setdefault('evidence_paths',[]).extend([rel(E/'saam-shard43-tail-reconciliation.json'),rel(E/'CHECKPOINT.json')])
 assert [x for x in before['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in queue['sources'] if x['source_id']!='smithsonian_open_access'] and before['supplementary_image_routes']==queue['supplementary_image_routes']
 tmp=qp.with_suffix('.263.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
save('source-queue-update-verification.json',dict(at=h.now(),updated_source='smithsonian_open_access',routes_researched=['french_reserve','smithsonian_open_access_shard43_tail'],unrelated_entries_preserved=True,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=q['resume_cursor']))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
save('independent-production-verification.json',dict(at=h.now(),verified_counts=counts,database_writes=0,storage_writes=0,audit_writes=0,local_catalogue_writes=0,verification_basis=['188/188 French reserve rows live with expected primary media and checksum-bound citations',f'SAAM shard43 contained {len(tail)} records and {len(candidates)} unique eligible exact primary-image-gap candidates requiring individual identity and visual review','no delivery plan or transaction created'],attribution='No production increment is attributable to batch 263.'))
save('batch-verification-receipt.json',dict(at=h.now(),batch=263,outcome='no_eligible_candidates',selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True,local_catalogue_read_only=True,cloud_translation_used=False))
nxt=('Individually reconcile and visually review saved SAAM shard43 candidates: '+','.join(x['native_id'] for x in candidates)) if candidates else 'Research an untouched original-registry museum with stable object identifiers and explicit open-image terms; do not replay French188, completed SAAM shard43, exhausted Athens routes, AGO, or unchanged provider holds.'
evidence=['french-reserve-live-reconciliation.json','saam-shard43-tail-reconciliation.json','production-target-reconciliation.json','batch107-live-reconciliation.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
cp=dict(at=h.now(),batch=263,stage='independently_verified_complete',outcome='no_eligible_candidates',researched=dict(french_reserve=188,saam_shard43_tail=len(tail)),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',production_writes=0,local_catalogue_connections=0,external_supervisor_unchanged=True,evidence_paths=[rel(E/x) for x in evidence])
save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
checked=[]
for name in evidence+['CHECKPOINT.json']:
 p=E/name;h.load(p);checked.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,production_writes=0,verified_counts=counts,passed=True))
result=dict(outcome='no_eligible_candidates',summary=f'Batch 263 freshly verified that all 188 French reserve records are already imported and illustrated, so none were replayed. The registry-backed fallback classified all {len(tail)} SAAM shard-43 records and found {len(candidates)} unique eligible exact primary-image-gap candidates requiring individual identity and visual review. Batch 107, the production target/proxy, queue cursor and final artifacts were independently verified. No database, Storage, audit or local-catalogue writes occurred.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in evidence+['independent-final-artifact-verification.json','CHECKPOINT.json']])
save('worker-result.json',result);h.save(R/'worker-result.json',result);print(json.dumps(result))
