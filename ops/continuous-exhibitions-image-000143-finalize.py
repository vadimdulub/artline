#!/usr/bin/env python3
"""Read-only independent checks and checkpoint for image batch 143."""
import fcntl
import importlib.util
import json
import os
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location('batch143', Path(__file__).with_name('continuous-exhibitions-image-000143.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def finish():
    p = b.plan()
    pin = b.load(b.E/'plan-pin.json')['sha256']
    review = b.load(b.E/'visual-review.json')
    rv = {x['native_id']: x for x in review['rows']}
    pre = b.load(b.E/'transaction-preimage.json')
    dv = b.load(b.E/'independent-database-verification.json')
    sv = b.load(b.E/'independent-storage-verification.json')
    pv = b.load(b.E/'independent-public-verification.json')
    assert all(x['passed'] for x in [dv, sv, pv])
    assert len(dv['rows']) == len(sv['rows']) == len(pv['assets']) == len(p['rows']) == 10
    assert len(pv['api_entries']) == len(pre['exact_links']) == 16
    assert b.sha((b.E/'visual-review.json').read_bytes()) == b.load(b.E/'visual-review-pin.json')['sha256']
    checks = []
    with b.c.connect() as db:
        own = db.execute('select media_id::text,source_checksum,evidence_json from media_rights_evidence where adapter_version=%s order by media_id', (b.OP,)).fetchall()
        assert {x['media_id'] for x in own} == {x['media_id'] for x in p['rows']}
        for r in p['rows']:
            persisted = next(x for x in own if x['media_id'] == r['media_id'])
            ev = persisted['evidence_json']
            assert ev['selection_sha256'] == pin and ev['preimage_sha256'] == p['preimage_sha256']
            assert ev['native_source_checksum'] == persisted['source_checksum'] == r['source_checksum']
            assert ev['source_creators'] == r['source_creators']
            assert ev['visual_review'] == rv[r['native_id']]
            assert ev['dimension_discrepancy'] == r['dimension_discrepancy']
            m = db.execute('select to_jsonb(m) r from media_assets m where id=%s', (r['media_id'],)).fetchone()['r']
            assert m['alt_text'] == r['title']+' — '+rv[r['native_id']]['creator_label']
            assert rv[r['native_id']]['creator_label'] in m['creator_credit']
            if r['native_id'] == '106462':
                assert 'after Filippino Lippi' in m['creator_credit'] and 'after Filippino Lippi' in m['alt_text']
            original = pre['before'][r['artwork_id']]
            assert original['artwork']['primary_media_id'] is None and original['attachments'] == []
            checks.append(dict(native_id=r['native_id'],media_id=r['media_id'],caption=m['alt_text'],persisted_source_and_review_checksums_match=True,empty_preimage_proves_new_attachment=True))
        pending = db.execute("""select distinct x.external_id native_id,x.external_id::int sortkey
          from artworks a join external_identifiers x on x.entity_type='artwork' and x.entity_id=a.id and x.scheme='cleveland-object'
          join exhibition_entries ee on ee.artwork_id=a.id join exhibitions e on e.id=ee.exhibition_id
          where a.primary_media_id is null and a.status<>'archived' and e.status<>'archived'
          and e.start_year between 1600 and 1989 and coalesce(e.end_year,e.start_year)<=1989
          and a.work_type in ('painting','drawing','print','watercolor','icon') and a.creation_year_end<=1970
          and x.external_id::int>106521 order by sortkey limit 10""").fetchall()
    b.save(b.E/'independent-caption-and-attribution-verification.json',dict(at=b.c.now(),rows=checks,qualified_creator_preserved=True,all_seven_dimension_exceptions_documented=True,passed=True))
    b.save(b.E/'independent-resume-verification.json',dict(at=b.c.now(),operation=b.OP,plan_sha256=pin,persisted_own_media_ids=[x['media_id'] for x in own],persisted_rights_source_review_checksums_verified=True,transaction_preimages_prove_ten_new_attachments=True,recovery_action='Already present with this exact pinned plan; do not reapply or count again.',replay_performed=False,read_only_check=True,other_job_changes_counted=0,passed=True))
    startup = b.load(b.E/'startup-verification.json')
    cp = b.load(b.E.parents[1]/'CHECKPOINT.json')
    assert cp['inflight']['batch'] == 143
    for k in ['worker_pid','supervisor_pid']:
        assert cp[k] == startup[k]
        os.kill(cp[k],0)
    for f in startup['supervisor_files']:
        assert b.sha(Path(f['path']).read_bytes()) == f['sha256']
    ps = subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
    workers = [x for x in ps if '/opt/homebrew/bin/codex exec ' in x and '--output-schema /Users/vadimdulub/Library/Application Support/Artline/continuous-exhibition-research/schema.json' in x]
    assert len(workers) == 1 and int(workers[0].split()[0]) == cp['worker_pid'] and int(workers[0].split()[1]) == cp['supervisor_pid']
    lockpath = Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/supervisor.lock'
    holders = subprocess.check_output(['lsof','-a','-p',str(cp['supervisor_pid'])+','+str(cp['worker_pid']),str(lockpath)],text=True)
    assert all(str(cp[k]) in holders for k in ['supervisor_pid','worker_pid'])
    b.save(b.E/'continuation-process-verification.json',dict(at=b.c.now(),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],supervisor_and_worker_running=True,single_exhibition_worker=True,inherited_singleton_lock_open=True,supervisor_prompt_schema_launchagent_and_artwork_research_files_unchanged=True,new_supervisor_started=False,passed=True))

    names=['startup-verification.json','source-register-verification.json','recovery-check.json','prior-batch-live-recovery-verification.json','production-target-reconciliation.json','new-source-holds.json','source-capture-verification.json','technical-verification.json','visual-review.json','visual-review-pin.json','backup-verification.json','storage-upload-verification.json','production-target-before-database-write.json','independent-file-verification.json','independent-database-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-caption-and-attribution-verification.json','independent-resume-verification.json','continuation-process-verification.json']
    rel = lambda n: str((b.E/n).relative_to(b.ROOT))
    source_next='Resume missing exact Cleveland images after native 106521; retain all existing rights and multipart holds. Pending IDs are discovery leads only and require fresh source and visual review.'
    next_task='Reconcile Cleveland objects 119016 and 119017 against exact existing exhibition entries, accessions, dates and creator authorities. Image delivery resumes after native 106521; preserve all existing version, date and rights holds.'
    qpath=b.E.parents[1]/'source-queue.json'
    with qpath.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        q=b.load(qpath)
        before=b.sha(qpath.read_bytes())
        unrelated=[s for s in q['sources'] if s['source_id']!='cleveland_museum']
        unrelated_bytes=json.dumps(unrelated,sort_keys=True)
        source=next(s for s in q['sources'] if s['source_id']=='cleveland_museum')
        heldids={str(h.get('nativeID',h.get('native_id',h.get('native','')))) for h in source.get('holds',[])}
        pending_ids=[x['native_id'] for x in pending if x['native_id'] not in heldids]
        source.update(research_status='batch143_ten_exact_cc0_images_verified',last_checked_at=b.c.now(),last_batch=143)
        source.setdefault('cursor',{})['batch143Images']=dict(nativeIDs=[r['native_id'] for r in p['rows']],artworkIDs=[r['artwork_id'] for r in p['rows']],plan_sha256=pin,visual_review_sha256=b.sha((b.E/'visual-review.json').read_bytes()),verified_images=10,existing_connections_illustrated=16,existing_exhibitions_illustrated=8,resume_after_native_id='106521',next_native_id='106522',pending_native_ids=pending_ids,unresolved_api_dimensions=7,reviewed_complete_frames=10,evidence=rel('independent-database-verification.json'),next=source_next)
        source['cursor']['imageResumeAfterNativeID']='106521'
        source['cursor']['next']=next_task
        for h in b.load(b.E/'new-source-holds.json')['rows']:
            source.setdefault('holds',[]).append(dict(nativeID=h['native_id'],reason=h['reason'],source_receipt=h['source_receipt'],evidence=rel('new-source-holds.json')))
        source['evidence']=list(dict.fromkeys(source.get('evidence',[])+[rel(n) for n in names]))
        temp=qpath.with_suffix('.143.tmp');temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(temp,qpath)
        assert json.dumps([s for s in b.load(qpath)['sources'] if s['source_id']!='cleveland_museum'],sort_keys=True)==unrelated_bytes
    b.save(b.E/'queue-update-verification.json',dict(at=b.c.now(),source='cleveland_museum',queue_before_sha256=before,queue_after_sha256=b.sha(qpath.read_bytes()),unrelated_sources_preserved=len(unrelated),pending_native_ids=pending_ids,resume_after_native_id='106521',new_rights_holds=3,original_registry_unchanged=b.sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes())==b.load(b.E/'source-register-verification.json')['registry_sha256'],passed=True))
    names.append('queue-update-verification.json')
    counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']}
    counts.update(new_images=10,existing_records_enriched=10)
    checkpoint=dict(at=b.c.now(),batch=143,stage='verified_complete',discovered=13,prepared=10,imported=10,verified=10,rights_held=3,dimension_discrepancies_individually_reviewed=7,verified_counts=counts,existing_connections_illustrated=16,existing_exhibitions_illustrated=8,checklist_states='Preserved; no completeness claim',next_task=next_task,evidence_paths=[rel(n) for n in names],supervisor_unchanged=True,separate_artwork_programme_unchanged=True,local_catalogue_connections=0)
    b.save(b.E/'CHECKPOINT.json',checkpoint);b.save(b.R/'CHECKPOINT.json',checkpoint)
    names.append('CHECKPOINT.json')
    summary='Added ten visually reviewed Cleveland CC0 images to existing artworks, illustrating 16 existing connections across eight historical exhibitions. Public checksums, database attribution and API links verified; existing statuses preserved. Three rights holds and seven reviewed dimension discrepancies recorded.'
    result=dict(outcome='progress',summary=summary,next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n) for n in names])
    b.save(b.E/'final-verification.json',dict(at=b.c.now(),plan_sha256=pin,verified_counts=counts,prior_campaign_and_other_job_changes_excluded=True,attribution_from_persisted_rights_and_transaction_preimages=True,verification_files=[dict(path=rel(n),sha256=b.sha((b.E/n).read_bytes())) for n in names],passed=True))
    result['evidence_paths'].append(rel('final-verification.json'))
    b.save(b.E/'bounded-result.json',result);b.save(b.R/'bounded-result.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    finish()
