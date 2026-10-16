#!/usr/bin/env python3
"""Finalize one verified batch; preserve unrelated queues and external supervisor."""
import copy, datetime, fcntl, gzip, hashlib, importlib.util, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('norway58',ROOT/'ops/continuous-norway-images-000058.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
h=b.h;i=b.i;E=b.E.parent;R=b.RUNTIME;load=h.load
lock=(R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def save(name,value):
    p=E/name
    if p.exists():return load(p)
    h.save(p,value);return value
def ref(p):
    p=Path(p);return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),sha256=h.sha(p.read_bytes()))

receipt=load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts']
assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=8,alternate_images=0,museum_links=0)
images,audit,review=i.accepted(b.B);assert len(images)==8 and len(review['decisions'])==8
ids=[x['artwork_id'] for x in images]

# Verify Princeton captures independently; no image was selected/downloaded.
pool=load(E/'bounded-gap-input.json')['rows'];state=load(E/'preparation-production-snapshot.json.gz')
checks=[]
for row in pool:
    oid=row['external_id'];rc=load(E/'source-captures'/(oid+'.receipt.json'))
    raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
    o=json.loads(raw);assert str(o['objectid'])==oid
    old=state['before'][row['id']]['artwork']
    comparisons={key:o[sk]==old[key] for sk,key in [('objectnumber','accession_number'),('displaytitle','title'),('datebegin','creation_year_start'),('dateend','creation_year_end'),('displaydate','date_display')]}
    restrictions=o.get('restrictions');primary=[v for v in o.get('media',[]) if v.get('isprimary')==1]
    cultures=[x['culture'] for x in o.get('cultureterms',[])];periods=[x['period'] for x in o.get('periodterms',[])]
    assert not any('Greek' in x or 'Byzantine' in x for x in cultures+periods)
    checks.append(dict(artwork_id=row['id'],native_id=oid,source_sha256=rc['sha256'],source_url=rc['url'],identity_comparisons=comparisons,cultures=cultures,periods=periods,actual_restrictions=restrictions,reproduction_credit=o.get('creditlinerepro'),primary_media_restrictions=[x.get('restrictions') for x in primary],outcome='explicit_source_restriction' if restrictions else 'image_rights_unspecified_outside_source_approval',images_downloaded=0,metadata_changed=False))
assert len(checks)==25 and sum(bool(x['actual_restrictions']) for x in checks)==6
save('independent-princeton-source-verification.json',dict(at=h.now(),records=checks,captures_verified=25,explicit_restriction_holds=6,unspecified_rights_holds=19,source_approval_not_generalized=True,image_requests=0,website_access_hold_preserved=True))

with b.connect() as db:
    current=h.snapshot(db,[r['id'] for r in pool]);assert current==state['before']
    live=h.snapshot(db,ids)
    media=[dict(x) for x in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
    assert len(media)==8 and {x['media_id'] for x in media}=={x['media_id'] for x in images}
    for x in media:
        ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
        assert ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256']
save('independent-princeton-preservation-verification.json',dict(at=h.now(),production_ids=[r['id'] for r in pool],live_snapshots_unchanged=True,images_added=0,metadata_updates=0))

# Normal saved-receipt replay must not open a database or request any network.
files=list((b.E/'batches').rglob('*.json'))+list((b.E/'batches').rglob('*.gz'))
hashes={str(p):h.sha(p.read_bytes()) for p in files}
calls=[]
def forbidden(*args,**kwargs):
    calls.append('unexpected production or network request');raise AssertionError(calls[-1])
original_connect=i.m.m.connect;original_session=i.session
i.m.m.connect=forbidden;i.session=forbidden
b.finish();i.apply(b.B)
i.m.m.connect=original_connect;i.session=original_session
assert not calls and hashes=={str(p):h.sha(Path(p).read_bytes()) for p in hashes}
with b.connect() as db:assert h.snapshot(db,ids)==live
reserve=load(E/'independent-reserve-evidence-verification.json')
for item in reserve['immutable_plans']:assert h.sha(Path(item['path']).read_bytes())==item['sha256']
save('independent-resume-verification.json',dict(at=h.now(),method='Re-ran prepare finish and transaction apply with database/network entry points disabled; saved applied receipt skipped writes. Then independently compared live production snapshots.',receipt_replay_production_connections=0,receipt_replay_network_calls=0,all_pinned_files_unchanged=True,live_after_equals_before=True,new_production_increments_on_replay=0,historical_french_plans_unchanged=True,limitation='Normal completed-receipt replay verified; does not claim a new supervisor or fault-injection test of every interruption point.'))

save('batch-verification-receipt.json',dict(receipt,component_receipt=ref(b.E/'batch-verification-receipt.json'),french_reserve_previous_campaign_excluded=188,princeton_new_images=0,new_artwork_inserts=0,viewed_images=8,accepted_images=8,held_norway_objects=4))

zero={k:0 for k in counts};now=h.now()
next_task='Rotate to SMK Denmark: resume existing native primary-image gaps after 02a1f9c0-64e2-4257-bdba-581286514593, inspect a bounded next page and require exact per-object open-image evidence. French reserve is exhausted; Princeton frozen queue is fully researched with holds preserved. Norway resumes after 0d63a351-f7d5-5fc3-91f4-4642f7b1d94b; Warsaw page 4 remains available.'
qp=E.parent.parent/'source-queue.json';touched={'yale_lux','princeton_art_museum','nasjonalmuseet_norway'}
with qp.with_suffix('.lock').open('a+') as qlock:
    fcntl.flock(qlock,fcntl.LOCK_EX)
    if (E/'source-queue-after.json').exists():
        before=load(E/'source-queue-immediately-before-update.json');after=load(E/'source-queue-after.json');assert load(qp)==after
    else:
        before=load(qp);after=copy.deepcopy(before);save('source-queue-immediately-before-update.json',before)
        assert len(after['sources'])==111
        for source in after['sources']:
            sid=source['source_id']
            if sid not in touched:continue
            cursor=source['resume_cursor'];source.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(cursor))
            source.update(last_checked_at=now,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),latest_batch_verified_counts=counts if sid=='nasjonalmuseet_norway' else zero)
            if sid=='yale_lux':
                assert cursor['unimported']==0
                source.update(status='french_reserve_exhausted_live_verified_188_already_delivered',access_status='Fresh batch-58 live production reconciliation plus archived source/visual checksum verification; no reserve supplement possible')
                evidence=['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json']
            elif sid=='princeton_art_museum':
                processed=[r['external_id'] for r in pool]
                assert cursor['unresearched_native_ids'][:25]==processed
                cursor['processed_native_ids']=list(dict.fromkeys(cursor['processed_native_ids']+processed))
                cursor['unresearched_native_ids']=cursor['unresearched_native_ids'][25:]
                cursor['held_rights_native_ids']=list(dict.fromkeys(cursor.get('held_rights_native_ids',[])+processed))
                cursor['rights_hold_ledger']=str((E/'independent-princeton-source-verification.json').relative_to(ROOT))
                cursor['next_step']='Frozen native queue fully researched; no further IDs. Resume only with new exact alternate image evidence or a documented rights/access change. Preserve all prior holds and website 403.'
                source.update(status='frozen_native_gap_queue_fully_researched_rights_holds_preserved',access_status='Native public metadata API HTTP 200; website 403 hold unchanged; no Princeton images requested')
                source.setdefault('remaining_gaps',[]).append('Batch 58: 25 frozen native objects researched; 6 explicit restrictions and 19 unspecified reproduction-rights labels outside Greek/Byzantine approval. No unresearched frozen IDs remain.')
                evidence=['independent-princeton-source-verification.json','independent-princeton-preservation-verification.json','gap-reconciliation.json']
            else:
                staged=load(b.E/'oslo-bounded-gap-input.json.gz');allids=[r['id'] for r in staged['rows']]
                assert cursor['after_artwork_id']=='0c03eace-07fc-5961-9b16-4ed3d9b4742f'
                cursor.update(previous_after_artwork_id=cursor['after_artwork_id'],after_artwork_id=allids[-1],latest_frozen_input=str((b.E/'oslo-bounded-gap-input.json.gz').relative_to(ROOT)),next_step='Rotate to SMK; return to Oslo keyset after 0d63a351-f7d5-5fc3-91f4-4642f7b1d94b. Preserve four new holds and earlier cases.')
                for key,more in [('inspected_ids',allids),('delivered_ids',ids),('held_ids',[x for x in allids if x not in ids])]:cursor[key]=list(dict.fromkeys(cursor.get(key,[])+more))
                holds=load(b.E/'research-holds.json')['records']
                cursor['latest_rights_hold_ids']=[r['artwork_id'] for r in holds if r['reason']=='Object-specific copyright restriction']
                cursor['latest_source_404_hold_ids']=[r['artwork_id'] for r in holds if r['reason']=='Native page HTTP 404']
                cursor['latest_identity_hold_ids']=[r['artwork_id'] for r in holds if 'reconciliation' in r['reason']]
                cursor['latest_hold_ledger']=str((b.E/'research-holds.json').relative_to(ROOT))
                cursor['latest_visual_hold_ids']=[r['artwork_id'] for r in review['decisions'] if r['decision']=='hold']
                cursor['visual_hold_ledger']=str((b.E/'actual-visual-review.json').relative_to(ROOT))
                cursor['selection_sha256']=receipt['selection_sha256']
                source.update(status='thirty_four_programme_primary_images_verified_eight_new_CC_BY_images',verified_counts=counts,access_status='Current official native object pages and selected IIIF JPEGs HTTP 200; object-specific CC BY rights and credits verified')
                source['programme_verified_counts']={k:source['programme_verified_counts'][k]+counts[k] for k in counts}
                source.setdefault('remaining_gaps',[]).append('Batch 58: 12 next-keyset objects researched, 8 primary images independently delivered; 2 copyright holds, 1 source-page 404 and 1 native-identifier/citation reconciliation hold. No new metadata, holdings or directory coverage.')
                evidence=['norway/batch-verification-receipt.json','norway/independent-production-verification.json','norway/independent-file-verification.json','norway/independent-source-verification.json','norway/independent-public-verification.json','norway/actual-visual-review.json','norway/research-holds.json','source-hold-clarification.json']
            source['evidence_paths']=list(dict.fromkeys(source.get('evidence_paths',[])+[str((E/f).relative_to(ROOT)) for f in evidence]))
        save('source-queue-after.json',after)
        assert load(qp)==before,'Concurrent queue change: do not overwrite'
        temp=qp.with_suffix('.batch58.tmp');temp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(temp,qp)
left={x['source_id']:x for x in before['sources']};right={x['source_id']:x for x in after['sources']}
assert {k:v for k,v in left.items() if k not in touched}=={k:v for k,v in right.items() if k not in touched}
assert len(right['princeton_art_museum']['resume_cursor']['unresearched_native_ids'])==0
save('independent-queue-verification.json',dict(at=h.now(),changed_source_ids=sorted(touched),unrelated_entries_preserved=108,source_count=111,before=ref(E/'source-queue-immediately-before-update.json'),after=ref(qp),warsaw_page4_cursor_preserved=True,princeton_frozen_queue_exhausted=True,french_unimported=0,norway_newly_illustrated=8,norway_programme_newly_illustrated=34))

master=load(E.parent.parent/'CHECKPOINT.json');assert master['inflight']['batch']==58
start=datetime.datetime.fromisoformat(master['inflight']['started_at']);end=datetime.datetime.now(datetime.timezone.utc)
cp=save('CHECKPOINT.json',dict(at=end.isoformat(),started_at=start.isoformat(),elapsed_seconds=(end-start).total_seconds(),batch=58,outcome='progress',stage='eight_primary_images_independently_verified_queue_and_replay_checked',verified_counts=counts,researched_existing_image_gaps=37,discovered_new_artwork_objects=0,selected_images=8,prepared_images=8,viewed_images=8,accepted_images=8,verified_images=8,unimported_french_reserve=0,holds=dict(princeton_rights=25,norway_rights=2,norway_source_404=1,norway_identity=1),next_task=next_task,resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-images-000058-verify.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-batch-000058-finalize.py'],production_helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0,supervisor_unmodified=True))
if not (R/'CHECKPOINT.json').exists():h.save(R/'CHECKPOINT.json',cp)
assert load(R/'CHECKPOINT.json')==cp
save('milestone-report.json',dict(at=end.isoformat(),measured_batch_runtime_seconds=(end-start).total_seconds(),measured_programme_runtime_hours=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600,previous_supervisor_counts=master['totals'],verified_batch_counts=counts,cumulative_receipt_counts={k:master['totals'][k]+counts[k] for k in counts},count_scope='Eight independently verified current increments plus saved supervisor totals; no whole-catalogue census or re-audit of all prior campaigns.',hourly_summary_owner='Existing external supervisor; unmodified',hundred_hours_is_not_stop=True,next_task=next_task,failures=ref(E/'failures.json')))
refs=['batch-verification-receipt.json','independent-resume-verification.json','independent-queue-verification.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','independent-princeton-source-verification.json','independent-princeton-preservation-verification.json','norway/independent-production-verification.json','norway/independent-source-verification.json','norway/independent-file-verification.json','norway/independent-audit-history-verification.json','norway/independent-storage-verification.json','norway/independent-public-verification.json','norway/independent-held-objects-verification.json','norway/actual-visual-review.json','CHECKPOINT.json','milestone-report.json','source-access-holds.json','source-archive-verification.json','source-hold-clarification.json','source-register.json']
save('final-checkpoint-verification.json',dict(at=h.now(),references=[ref(E/x) for x in refs],verified_counts=counts,runtime_checkpoint_matches=True,all_references_exist=True,historical_reserve_plans_unchanged=True,source_queue_111_entries=True,supervisor_unmodified=True))
print(json.dumps(dict(outcome='progress',verified_counts=counts,next_task=next_task)))
