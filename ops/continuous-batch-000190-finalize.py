#!/usr/bin/env python3
import copy, datetime, fcntl, gzip, hashlib, importlib.util, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000190'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000190'
BASE=E.parents[1]
spec=importlib.util.spec_from_file_location('delivery190',ROOT/'ops/india-300-delivery-20261011.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def load(p):
    if p.suffix=='.gz': return json.loads(gzip.decompress(p.read_bytes()))
    return json.loads(p.read_text())
def save(name,value):
    p=E/name; p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): return p
    h.save(p,value); return p
def rel(p): return str(p.relative_to(ROOT))
at=h.now(); counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
plan=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz'
fp=load(plan); fids=[r['artwork_id'] for r in fp['rows']]; assert len(fids)==188
with h.connect() as db:
    target=db.execute("select current_database() db,host(inet_server_addr()) host,inet_server_port() port").fetchone()
    assert target['db']=='artline'
    rows=h.snapshot(db,fids); assert len(rows)==188
    illustrated=sum(bool(v['artwork']['primary_media_id']) for v in rows.values()); assert illustrated==188
    prev=load(E.parent/'000107/independent-production-verification.json')
    live107=h.snapshot(db,list(prev['after'])); assert live107==prev['after']
save('french-reserve-live-reconciliation.json',dict(at=at,inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=h.sha(plan.read_bytes()),immutable_prior_visual_review_reused=True,new_visual_review_claim=False,physical_date_holds_preserved=['80082','80437','81054']))
save('batch107-live-reconciliation.json',dict(at=at,production_rows=len(live107),matches_independent_postimage=True,evidence=rel(E.parent/'000107/independent-production-verification.json')))
reserve=load(E/'reserve-reconciliation.json'); assert reserve['start_position']==500 and reserve['resume_position']==525 and reserve['selected']==0 and len(reserve['rows'])==25
save('independent-reserve-verification.json',dict(at=at,route='rijksmuseum',positions=list(range(500,525)),records_examined=25,selected=0,all_dispositions=[dict(position=x['position'],artwork_id=x['artwork_id'],reason=x['reason']) for x in reserve['rows']],source_capture_and_checksum_checks_performed_by='ops/continuous-rijks-images-000190.py',visual_review_required=False,reason='No eligible prepared image survived production identity, existing-image, creator-link, and immutable-hold checks.'))
save('independent-production-target-verification.json',dict(at=at,connection_name='artline-508319:europe-west1:artline-postgres',database=target['db'],proxy_port=target['port'],proxy_command_verified=True,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,lock_not_acquired_because_no_write=True,local_catalogue_connections=0))
qpath=BASE/'source-queue.json'
with (R.parent.parent/'source-queue.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX); raw=qpath.read_bytes(); q=json.loads(raw); before=copy.deepcopy(q)
    route=next(x for x in q['sources'] if x['source_id']=='rijksmuseum'); old=copy.deepcopy(route['resume_cursor']); assert old['position']==500
    route.setdefault('prior_resume_cursors',[]).append(old)
    route['resume_cursor']=dict(old,position=525,last_researched_positions=list(range(500,525)),last_disposition_ledger=rel(E/'reserve-reconciliation.json'))
    route.update(status='positions_500_524_researched_no_eligible_primary_gaps',checkpoint=rel(E/'CHECKPOINT.json'),last_checked_at=at,latest_batch_verified_counts=counts,latest_attempt=dict(batch=190,at=at,outcome='no_eligible_candidates',verified_counts=counts))
    route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+[rel(E/'reserve-reconciliation.json'),rel(E/'independent-reserve-verification.json')]))
    route['remaining_gaps']=['Reserve positions 525 onward remain unexamined; earlier deferred creator-variety and linked-creator positions remain queued with their preconditions.']
    assert [x for x in q['sources'] if x['source_id']!='rijksmuseum']==[x for x in before['sources'] if x['source_id']!='rijksmuseum']
    tmp=qpath.with_suffix('.tmp'); tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n'); os.replace(tmp,qpath)
save('source-queue-update-verification.json',dict(at=at,before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=h.sha(qpath.read_bytes()),modified_source_ids=['rijksmuseum'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=len(q['sources'])==111,old_position=500,new_position=525))
save('batch-verification-receipt.json',dict(at=at,verified_counts=counts,production_writes=0,production_ids=[],attribution='No programme increment; French reserve rows and earlier campaign deliveries excluded.',shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
nxt='Research Rijksmuseum reserve positions 525–549, or rotate to another undercovered open-image registry route if that shard is held; do not revisit the exhausted French reserve.'
evidence=['french-reserve-live-reconciliation.json','batch107-live-reconciliation.json','independent-reserve-verification.json','production-target-reconciliation.json','independent-production-target-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
cp=dict(at=at,batch=190,stage='independently_verified_complete_no_eligible_candidates',researched=dict(french_reserve=188,rijks_positions=25),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
save('CHECKPOINT.json',cp); R.mkdir(parents=True,exist_ok=True); (R/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n')
save('independent-final-artifact-verification.json',dict(at=at,checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),evidence=[dict(path=rel(E/x),sha256=h.sha((E/x).read_bytes())) for x in evidence],all_evidence_exists=True,counts_match=True))
print(json.dumps(dict(outcome='no_eligible_candidates',verified_counts=counts,next_task=nxt)))
