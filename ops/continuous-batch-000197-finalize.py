#!/usr/bin/env python3
"""Batch 197: reconcile the sole registry Greek route's saved image-gap cursor."""
import copy,csv,fcntl,gzip,hashlib,importlib.util,json,os,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000197'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000197'
BASE=E.parents[1]; TARGET='artline-508319:europe-west1:artline-postgres'
INPUT=E.parent/'000166/athens-all-gap-input.json.gz'
HELPER=ROOT/'ops/india-300-delivery-20261011.py'
s=importlib.util.spec_from_file_location('prod197',HELPER);h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(n,v):h.save(E/n,v);return v
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(ROOT))

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
with (R/'worker.lock').open('a+') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);at=load(E/'required-input-verification.json')['at'] if (E/'required-input-verification.json').exists() else h.now();zero=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')));assert len(registry)==111
 greek=[x for x in registry if x['country_code'] in ('GR','CY') or 'byzant' in ' '.join(x.values()).lower()];assert [x['source_id'] for x in greek]==['national_gallery_athens']
 proxy=[x for x in subprocess.check_output(['ps','-axo','command='],text=True).splitlines() if 'cloud-sql-proxy' in x and '--port 55519' in x];assert len(proxy)==1 and TARGET in proxy[0]
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 frozen=load(INPUT);ids=[x['id'] for x in frozen['rows']];assert len(ids)==20 and len(set(ids))==20
 with h.connect() as db:
  target=dict(db.execute("SELECT current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery").fetchone());assert target['db']=='artline' and not target['recovery']
  live=h.snapshot(db,ids)
  current=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,status,primary_media_id::text FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id",(ids,))]
  prior=load(E.parent/'000107/independent-production-verification.json');live107=h.snapshot(db,list(prior['after']));assert live107==prior['after']
 assert len(current)==20 and all(x['status']!='archived' for x in current)
 gaps=[x for x in current if not x['primary_media_id']];illustrated=[x for x in current if x['primary_media_id']]
 eligible=[x for x in gaps if x['creation_year_start'] is not None and x['creation_year_end'] is not None and x['creation_year_end']<=1955]
 unknown=[x for x in gaps if x['creation_year_start'] is None or x['creation_year_end'] is None]
 save('required-input-verification.json',dict(at=at,registry_rows=len(registry),registry_greek_or_byzantine_routes=[x['source_id'] for x in greek],required_docs_read=True,latest_checkpoint='000196',latest_hold_ledgers=['000166/failures-and-holds.json','000185/aivazovsky-eligibility-reconciliation-v2.json'],translation_calls=0))
 save('production-target-reconciliation.json',dict(at=at,connection_name=actual,proxy_command_inspected=True,proxy_port=55519,database=target,helper=rel(HELPER),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 save('batch107-live-reconciliation.json',dict(at=at,rows=len(live107),snapshot_fields_equal=True,previous_increments_counted=0,evidence=rel(E.parent/'000107/independent-production-verification.json')))
 save('athens-gap-live-reconciliation.json',dict(at=at,route='national_gallery_athens/saved_existing_primary_image_gaps',frozen_input_sha256=sha(INPUT),frozen_rows=20,live_active_rows=len(current),still_primary_gaps=len(gaps),now_illustrated_by_other_jobs=len(illustrated),eligible_with_supported_creation_date_through_1955=len(eligible),held_unknown_creation_date=len(unknown),rows=current,production_writes=0,previous_deliveries_counted=0,conclusion='No eligible image candidate remains on the saved registry-route cursor; unknown dates are not invented.'))
 prior_reviews=[E.parent/'000164/batches/athens-native-000/visual-review.json',E.parent/'000166/batches/athens-native-000/visual-review.json',E.parent/'000168/batches/athens-native-000/visual-review.json']
 assert all(p.exists() for p in prior_reviews)
 save('actual-visual-review.json',dict(at=at,new_images_prepared=0,new_images_viewed=0,claim='No new visual review claimed because live reconciliation selected zero eligible images.',immutable_prior_review_files=[dict(path=rel(p),sha256=sha(p)) for p in prior_reviews],prior_review_reused_for_new_delivery=False))
 save('batch-verification-receipt.json',dict(at=at,verified_counts=zero,production_ids=[],production_writes=0,production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Fresh live reads show zero eligible selected images and no writes. Prior Athens and other campaign deliveries are excluded.',transaction_preimages='No transaction preimages: no eligible candidate and no write transaction.'))
 qpath=BASE/'source-queue.json'
 with (BASE/'source-queue.lock').open('a+') as qlk:
  fcntl.flock(qlk,fcntl.LOCK_EX);q=load(qpath);assert len(q['sources'])==111;before=copy.deepcopy(q)
  row=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');row['last_checked_at']=at;row['last_batch']=197;row['status']='saved_primary_gap_cursor_live_reconciled_zero_eligible_batch197';row['checkpoint']=rel(E/'CHECKPOINT.json')
  row.setdefault('resume_cursor',{})['batch197_existing_gap_reconciliation']=dict(frozen_rows=20,still_gaps=len(gaps),illustrated_elsewhere=len(illustrated),eligible=0,unknown_date_holds=len(unknown),retry_allowed=False,evidence=rel(E/'athens-gap-live-reconciliation.json'),next_step='Do not replay unchanged Athens gap cursor; rotate to an undercovered permitted WikiArt creator route with exact existing primary gaps.')
  tmp=qpath.with_suffix('.197.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
  assert [x for x in before['sources'] if x['source_id']!='national_gallery_athens']==[x for x in q['sources'] if x['source_id']!='national_gallery_athens']
 save('source-queue-update-verification.json',dict(at=at,modified_source_ids=['national_gallery_athens'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,queue_sha256=sha(qpath),resume_cursor=row['resume_cursor']['batch197_existing_gap_reconciliation']))
 nxt='Select a bounded permitted WikiArt cohort of exact existing primary-image gaps from an undercovered Greek, Byzantine, post-Byzantine or Russian-icon creator; require >=90% identity confidence and actual visual review. Do not replay the exhausted Athens cursor, Aivazovsky notices, French188 reserve, or SAAM shards 0–27.'
 evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','athens-gap-live-reconciliation.json','actual-visual-review.json','batch-verification-receipt.json','source-queue-update-verification.json']
 cp=dict(at=at,batch=197,stage='verified_no_eligible_candidates',researched=dict(registry_routes=1,frozen_gap_rows=20,live_gap_rows=len(gaps)),selected=0,prepared=0,imported=0,verified=0,verified_counts=zero,next_task=nxt,blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
 (E/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n');(R/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n')
 save('independent-final-artifact-verification.json',dict(at=at,checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),all_evidence_exists=all((E/x).exists() for x in evidence),counts_match=True,evidence=[dict(path=rel(E/x),sha256=sha(E/x)) for x in evidence],source_queue_sha256=sha(qpath),passed=True))
 print(json.dumps(dict(outcome='no_eligible_candidates',still_gaps=len(gaps),unknown_date_holds=len(unknown),illustrated_elsewhere=len(illustrated),verified_counts=zero,next_task=nxt)))
