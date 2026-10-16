"""Verify receipt replay and persist bounded batch 92 without touching the supervisor."""
import copy,csv,datetime,fcntl,importlib.util,json,os,gzip
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000092.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h;E=b.E.parent;load=b.load

def save(name,v):return b.save(E/name,v)
def rel(p):return str(Path(p).relative_to(b.ROOT))
def ref(p):
 p=Path(p);return dict(path=rel(p) if p.is_relative_to(b.ROOT) else str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size)

def main():
 receipt=load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts'];images,audit,review=i.accepted(b.B)
 assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=8,alternate_images=0,museum_links=0)
 ids=receipt['production_ids'];staged=load(b.E/'oslo-bounded-gap-input.json.gz');allids=[r['id'] for r in staged['rows']];holds=load(b.E/'research-holds.json')['records']
 assert len(allids)==12 and len(images)==len(review['decisions'])==8 and len(holds)==4
 assert all(r['reason']=='Object-specific copyright restriction' for r in holds)
 def state():
  with b.connect() as db:
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
   snaps=h.snapshot(db,allids)
   events=[dict(r) for r in db.execute('SELECT entity_type,entity_id::text,action,count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[]) GROUP BY entity_type,entity_id,action ORDER BY entity_type,entity_id,action',(ids,))]
   rights=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s ORDER BY media_id',(i.OP,))]
   assert {r['media_id'] for r in rights}=={im['media_id'] for im in images}
   for r in rights:
    ev=json.loads(r['evidence_json']) if isinstance(r['evidence_json'],str) else r['evidence_json'];assert ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256']
   verified=load(b.E/'independent-production-verification.json')['after'];assert all(snaps[aid]==verified[aid] for aid in ids)
   assert all(snaps[aid]==staged['states'][aid] for aid in set(allids)-set(ids))
   return snaps,events,rights
 before=state();hashes={str(p):h.sha(p.read_bytes()) for p in (b.E/'batches').rglob('*') if p.is_file()};calls=[]
 def forbidden(*a,**kw):calls.append('unexpected call');raise AssertionError('Unexpected network or database call during completed-receipt replay')
 old_connect,old_session=i.m.m.connect,i.session
 try:
  i.m.m.connect=forbidden;i.session=forbidden;b.finish();i.apply(b.B)
 finally:i.m.m.connect=old_connect;i.session=old_session
 after=state();assert before==after and not calls;assert hashes=={p:h.sha(Path(p).read_bytes()) for p in hashes}
 stop=load(E/'completed-campaign-stop-preservation.json');assert h.sha((b.ROOT/stop['path']).read_bytes())==stop['sha256']
 save('independent-resume-verification.json',dict(at=h.now(),steps=['prepare finish','transaction apply'],unchanged_snapshot=True,unchanged_audit_counts=True,unchanged_rights_evidence=True,pinned_files_unchanged=True,unexpected_requests=0,replay_increments={k:0 for k in counts},completed_campaign_stops_unchanged=True,separate_campaign=i.OP,external_supervisor_unmodified=True))
 save('batch-verification-receipt.json',dict(receipt,detailed_receipt=ref(b.E/'batch-verification-receipt.json')))
 qd=load(E/'qagoma-discovery.json');qids=[]
 for r in qd['rows']:
  raw=gzip.decompress(Path(r['body_path']).read_bytes());assert h.sha(raw)==r['sha256'] and r['status']==404 and not r['links'];qids.append(r['artwork_id'])
 save('independent-qagoma-verification.json',dict(at=h.now(),checked_artwork_ids=qids,capture_checksums_verified=True,profile_statuses=[r['status'] for r in qd['rows']],new_primary_images=0,no_exact_reproduction_selected=True,native_held_requests=0,image_requests=0,limitation='Only these three profile routes and the saved search queries checked; 404 is not proof that the artist or image is absent elsewhere.'))
 next_task='Resume Athens Parthenis page 4 under the saved Greek source policy. Norway can later resume after UUID '+allids[-1]+', preserving four new copyright holds. QAGOMA has nine untouched gaps; seven investigated candidates need new profile or exact-version evidence. French reserve is exhausted.'
 qp=E.parents[1]/'source-queue.json';modified={'nasjonalmuseet_norway','qagoma'}
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if (E/'source-queue-after.json').exists():
   old=load(E/'source-queue-immediately-before-update.json');new=load(E/'source-queue-after.json');live=load(qp)
   assert all(next(r for r in live['sources'] if r['source_id']==sid)==next(r for r in new['sources'] if r['source_id']==sid) for sid in modified)
  else:
   old=load(qp);new=copy.deepcopy(old);save('source-queue-immediately-before-update.json',old)
   frozen=load(E/'source-queue-before.json')
   for sid in modified:assert next(r for r in old['sources'] if r['source_id']==sid)==next(r for r in frozen['sources'] if r['source_id']==sid),'Source queue changed concurrently'
   route=next(r for r in new['sources'] if r['source_id']=='nasjonalmuseet_norway');c=route['resume_cursor'];assert c['after_artwork_id']==staged['after_artwork_id']
   route.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(c))
   c.update(previous_after_artwork_id=c['after_artwork_id'],after_artwork_id=allids[-1],latest_frozen_input=rel(b.E/'oslo-bounded-gap-input.json.gz'),selection_sha256=receipt['selection_sha256'],latest_verified_batch=92,latest_hold_ledger=rel(b.E/'research-holds.json'),visual_hold_ledger=rel(b.E/'actual-visual-review.json'),latest_visual_hold_ids=[],latest_rights_hold_ids=[r['artwork_id'] for r in holds],latest_source_404_hold_ids=[],latest_identity_hold_ids=[],no_repeat_of_unchanged_holds=True,next_step=next_task)
   for key,more in [('inspected_ids',allids),('delivered_ids',ids),('held_ids',[r['artwork_id'] for r in holds])]:c[key]=list(dict.fromkeys(c.get(key,[])+more))
   route['programme_verified_counts']={k:route['programme_verified_counts'][k]+counts[k] for k in counts}
   route.update(status='58_programme_primary_images_verified_eight_further_CC_BY_images',last_checked_at=h.now(),checkpoint=rel(E/'CHECKPOINT.json'),verified_counts=counts,latest_batch_verified_counts=counts,policy_reference='Original 111-source registry nasjonalmuseet_norway; docs/ARTLINE_IMAGE_USE.md general policy; current official object-specific CC BY 4.0 photo policy',access_status='12 native object pages HTTP200; eight selected source images, production images and APIs verified; four explicit artwork copyright holds.')
   route.setdefault('remaining_gaps',[]).append('Batch 92: four explicit artwork copyright restrictions retained. Museum coverage incomplete; only 12 further primary-image gaps checked.')
   route.setdefault('research_history',[]).append(dict(batch=92,at=h.now(),researched=12,selected=8,prepared=8,individually_viewed=8,verified_counts=counts,evidence=rel(E/'batch-verification-receipt.json')))
   route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+[rel(b.E/f) for f in ['independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','research-holds.json']]+[rel(E/'independent-resume-verification.json')]))
   route=next(r for r in new['sources'] if r['source_id']=='qagoma');c=route['resume_cursor'];route.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(c));assert set(qids)<=set(c['pending_artwork_ids'])
   c['pending_artwork_ids']=[aid for aid in c['pending_artwork_ids'] if aid not in qids]
   c['researched_artwork_ids']=list(dict.fromkeys(c['researched_artwork_ids']+qids));c['held_artwork_ids']=list(dict.fromkeys(c['held_artwork_ids']+qids));c['profile_404_no_unchanged_retry']=[r['url'] for r in qd['rows']]
   c.update(latest_discovery_ledger=rel(E/'qagoma-discovery.json'),latest_checked_batch=92,skip_unchanged_searches=True)
   assert len(c['pending_artwork_ids'])==9
   route.update(status='seven_gap_candidates_unresolved_nine_untouched_native_access_hold_preserved',last_checked_at=h.now(),checkpoint=rel(E/'CHECKPOINT.json'),access_status='Native QAGOMA HTTP403 hold preserved with zero requests; three further WikiArt profile routes HTTP404, no retries or downloads.')
   route['remaining_gaps']=['Nine untouched existing primary-image gaps.','Four earlier candidates need exact-version evidence; three further profile routes returned 404 and require a new supported profile URL or source.','No new museum coverage, artworks or holdings from image research.']
   route.setdefault('research_history',[]).append(dict(batch=92,at=h.now(),researched=3,selected=0,profile_404=3,verified_counts={k:0 for k in counts},evidence=rel(E/'independent-qagoma-verification.json')))
   route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+[rel(E/f) for f in ['qagoma-discovery.json','independent-qagoma-verification.json','source-access-holds.json']]))
   save('source-queue-after.json',new);assert load(qp)==old
   tmp=qp.with_suffix('.batch92.tmp');tmp.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 left={r['source_id']:r for r in old['sources']};right={r['source_id']:r for r in new['sources']};assert len(left)==len(right)==111
 assert {k:v for k,v in left.items() if k not in modified}=={k:v for k,v in right.items() if k not in modified}
 save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(modified),unrelated_entries_preserved=109,all_111_registry_routes_preserved=True,prior_holds_preserved=True,before=ref(E/'source-queue-immediately-before-update.json'),after=ref(E/'source-queue-after.json'),norway_after_artwork_id=allids[-1],qagoma_untouched=9))
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(reg.open()))
 save('source-register-final.json',dict(at=h.now(),registry=ref(reg),registry_records=111,sources=[dict(registry=next(r for r in registry if r['source_id']==sid),programme=right[sid]) for sid in sorted(modified)],directory_additions=0,directory_coverage_complete=False,artwork_coverage_complete=False))
 save('failures.json',dict(at=h.now(),provider_access_denials=0,profile_404=3,object_copyright_holds=4,production_failures=0,local_dependency_probe='System python lacks psycopg; reused established /tmp/artline-cyprus-venv/bin/python successfully.',unchanged_failed_requests_retried=0))
 master=load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==92
 start=datetime.datetime.fromisoformat(master['inflight']['started_at']);end=datetime.datetime.now(datetime.timezone.utc)
 cp=save('CHECKPOINT.json',dict(at=end.isoformat(),started_at=start.isoformat(),elapsed_seconds=(end-start).total_seconds(),batch=92,stage='independently_verified_complete',outcome='progress',verified_counts=counts,norway=dict(researched=12,selected=8,prepared=8,actually_viewed=8,imported=8,verified=8,copyright_holds=4,after_artwork_id=allids[-1]),qagoma=dict(researched=3,selected=0,profile_404=3,untouched_gaps=9),production_ids=ids,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],next_task=next_task,blocker='',resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-images-000092-verify.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-batch-000092-finalize.py'],local_catalogue_connections=0,external_supervisor_unmodified=True,reporting='External supervisor owns continuation and hourly reports; this worker completed one bounded batch.',limitations=['Scoped recovery: complete schema and affected rows, not a full database backup.','Eight derivatives viewed individually; originals decoded and hashed, not separately viewed.','No museum-wide or whole-catalogue census claimed.']))
 b.save(b.RUNTIME/'CHECKPOINT.json',cp)
 save('milestone-report.json',dict(at=cp['at'],measured_batch_runtime_seconds=cp['elapsed_seconds'],measured_programme_runtime_hours=(datetime.datetime.fromisoformat(cp['at'])-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600,previous_supervisor_counts=master['totals'],verified_batch_counts=counts,cumulative_receipt_counts={k:master['totals'][k]+counts[k] for k in counts},hundred_hours_is_not_stop=True,failures=ref(E/'failures.json'),next_task=next_task))
 refs=['batch-verification-receipt.json','independent-resume-verification.json','independent-queue-verification.json','independent-qagoma-verification.json','norway/independent-production-verification.json','norway/independent-source-verification.json','norway/independent-file-verification.json','norway/independent-storage-verification.json','norway/independent-public-verification.json','norway/independent-audit-history-verification.json','norway/independent-held-objects-verification.json','norway/actual-visual-review.json','norway/local-recovery-verification.json','source-register-final.json','source-access-holds.json','CHECKPOINT.json','milestone-report.json']
 save('independent-final-handoff-verification.json',dict(at=h.now(),verified_counts=counts,references=[ref(E/f) for f in refs],all_references_exist=True,runtime_checkpoint_matches=load(b.RUNTIME/'CHECKPOINT.json')==cp,unrelated_routes_preserved=109,completed_campaign_stop_unchanged=True,external_supervisor_unmodified=True,local_catalogue_connections=0))
 print(json.dumps(dict(outcome='progress',verified_counts=counts,next_task=next_task)))
if __name__=='__main__':
 with (b.RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
