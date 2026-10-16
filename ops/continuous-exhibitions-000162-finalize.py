"""Finalize verified batch162 without changing the external supervisor."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path

sp=importlib.util.spec_from_file_location('batch162',Path(__file__).with_name('continuous-exhibitions-000162.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
p,pin=m.pinned();v=c.load(E/'independent-database-verification.json');pub=c.load(E/'independent-public-verification.json');backup=c.load(E/'backup-verification.json')
assert v['passed'] and pub['passed'] and backup['passed'] and v['plan_sha256']==pub['plan_sha256']==backup['plan_sha256']==pin
counts=v['verified_counts'];startup=c.load(E/'startup-recovery-verification.json')
for f in startup['protected_files']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
for pid in [startup['supervisor_pid'],startup['worker_pid']]:os.kill(pid,0)
locks=subprocess.check_output(['lsof','-nP','-a','-p',str(startup['supervisor_pid'])+','+str(startup['worker_pid']),'-d','3'],text=True)
assert locks.count('continuous-exhibition-research/supervisor.lock')==2
previous=c.load(E.parent/'000161/continuation-final-verification.json')
for f in previous['protected_files_unchanged']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
c.save(E/'continuation-final-verification.json',dict(at=c.now(),supervisor_pid=startup['supervisor_pid'],worker_pid=startup['worker_pid'],inherited_lock=locks,protected_files_unchanged=startup['protected_files'],prior_launchagent_and_schema_fingerprints_unchanged=True,external_supervisor_owns_continuation=True,no_additional_supervisor_or_worker_launched=True,separate_artwork_programme_modified=False,passed=True))

wood=c.load(E/'cma-105741.json');m.body(wood['receipt']);assert wood['data']['type']=='Woodblock'
hold=c.load(E/'mfa-access-hold-verification.json');assert c.sha(Path(hold['body_path']).read_bytes())==hold['sha256']
c.save(E/'research-outcome-verification.json',dict(at=c.now(),selected_existing_entries=10,prepared_and_imported_main_artworks=1,verified_main_artworks=1,prepared_and_imported_exact_links=3,verified_exact_links=3,verified_artist_links=3,held_entries=7,
    held_boston=dict(catalogue_numbers=['158','159','162','163','164','170'],reason=hold['reason'],evidence=rel('mfa-access-hold-verification.json')),
    held_cleveland=dict(native_object='105741',accession='1923.83',title=wood['data']['title'],reason='The exact museum object is a Woodblock, not an identified paper impression. Preserve documentary entry; do not force it into painting/drawing/print scope. Timothy Cole is the maker; Rubens is qualified after, not its primary maker.',rights_label=wood['data']['share_license_status'],receipt=wood['receipt']),
    inventory_only='Broad native-number collisions and four remaining Fitzwilliam held rows were inspected as live inventory, not new source coverage. No automatic ID-only links. Existing holds remain.',
    exact_source=m.pinned()[0]['object_source']['receipt'],new_images=0,images_downloaded=0,images_visually_reviewed=0,local_catalogue_connections=0,checklists='All three existing partial states preserved.',passed=True))

next_task='For exact-object reconciliation, inspect Cleveland component106833/accession1924.848.3 (View of Amsterdam with Ships in Foreground) and its existing unlinked exhibition entries. Require reciprocal native event membership, accession and print-state identity; preserve portfolio parent distinctions. National Gallery NG30/1981/4 remains queued for an event-addition batch. Do not retry MFA robot verification, RISD, Arthive or other held providers without an access-state change.'
names=['independent-database-verification.json','independent-public-verification.json','source-capture-verification.json','candidate-reconciliation-verification.json','backup-verification.json','production-target-before-write.json','transaction-preimage.json','research-outcome-verification.json','mfa-access-hold-verification.json','startup-recovery-verification.json','scope-and-registry-verification.json','continuation-final-verification.json']
registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry_sha=c.load(E/'scope-and-registry-verification.json')['registry_sha256'];assert c.sha(registry.read_bytes())==registry_sha
with Q.with_suffix('.lock').open('a+')as lk:
    fcntl.flock(lk,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    touched={'mfa_boston','philadelphia_museum_art','cleveland_museum'}
    for s in after['sources']:
        if s['source_id']not in touched:continue
        s['last_checked_at']=c.now();s['cursor']=s.get('cursor')or{}
        if s['source_id']=='mfa_boston':
            s['research_status']='batch162_access_held_robot_verification_no_imports'
            s['cursor']['batch162']=dict(url=hold['url'],capture_sha256=hold['sha256'],selected_catalogue_numbers=hold['selected_catalogue_numbers'],new_links=0,next='Wait for a documented access-state change. Do not retry or bypass robot verification.')
            s['cursor']['next']=s['cursor']['batch162']['next']
            s.setdefault('holds',[]).append(dict(key='robot-verification-batch162',reason=hold['reason'],url=hold['url'],evidence=rel('mfa-access-hold-verification.json')))
            s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel('mfa-access-hold-verification.json'),rel('research-outcome-verification.json')]))
        elif s['source_id']=='philadelphia_museum_art':
            s['research_status']='batch162_blake_boston_six_entries_held_for_mfa_access'
            s['cursor']['batch162']=dict(exhibition_id='5c64ef50-18f0-5cf3-8a19-e86adf45c299',selected_catalogue_numbers=hold['selected_catalogue_numbers'],new_links=0,all_existing_entries_preserved=True,next='Boston entries158/159/162/163/164/170 remain documentary until official exact object records become available; do not retry held MFA/RISD providers. Retain the earlier NGA161 provenance hold.')
            s['cursor']['next']=s['cursor']['batch162']['next']
            s.setdefault('holds',[]).append(dict(key='blake-boston-six-mfa-access-batch162',reason=hold['reason'],evidence=rel('mfa-access-hold-verification.json')))
            s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel('mfa-access-hold-verification.json'),rel('research-outcome-verification.json')]))
        else:
            s['research_status']='batch162_one_exact_impression_three_existing_entry_links_three_artist_links_verified'
            s['cursor']['batch162ExactObjects']=dict(native_object='106831',accession='1924.848.10',artwork_id=m.WORK,source_url=p['object_source']['receipt']['url'],source_capture_sha256=p['object_source']['receipt']['sha256'],plan_sha256=pin,entries=p['entries'],verified_counts=counts,checklist_state='partial',next_native_object='106833',next=next_task,evidence=rel('independent-database-verification.json'))
            # Keep the independently queued image cursor and its next task intact.
            s['cursor']['next_exact_object_task']=next_task
            s.setdefault('holds',[]).append(dict(key='cma105741-woodblock-batch162',reason='Exact native object is a Woodblock; do not equate with a paper impression. Documentary entry remains unchanged.',source_url=wood['receipt']['url'],source_capture_sha256=wood['receipt']['sha256'],evidence=rel('research-outcome-verification.json')))
            s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n)for n in names]))
    assert [s for s in before['sources']if s['source_id']not in touched]==[s for s in after['sources']if s['source_id']not in touched]
    assert {k:v for k,v in before.items()if k!='sources'}=={k:v for k,v in after.items()if k!='sources'}
    orig=next(s for s in before['sources']if s['source_id']=='cleveland_museum');changed=next(s for s in after['sources']if s['source_id']=='cleveland_museum')
    assert all(changed['cursor'][k]==v for k,v in orig['cursor'].items())
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch162.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=sorted(touched),unrelated_entries_and_holds_preserved=True,cleveland_image_cursor_unchanged=True,supplemental_sources_unchanged=True,original_registry_sha256=registry_sha,original_registry_unchanged=True,resume=next_task,passed=True));names.append('queue-update-verification.json')
checkpoint=dict(at=c.now(),batch=162,operation=m.OP,stage='independently_verified_complete',plan_sha256=pin,selected_existing_entries=10,prepared_main_artworks=1,imported_main_artworks=1,verified_main_artworks=1,prepared_exact_links=3,imported_exact_links=3,verified_exact_links=3,verified_counts=counts,held_entries=7,next_task=next_task,local_catalogue_connections=0,separate_artwork_programme_modified=False,external_supervisor_owns_continuation=True)
c.save(E/'CHECKPOINT.json',checkpoint);c.save(R/'batch-checkpoint.json',checkpoint);names.append('CHECKPOINT.json')
c.save(E/'completion-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,verified_counts=counts,artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes()))for n in names],prior_and_concurrent_campaign_changes_excluded=True,passed=True));names.append('completion-verification.json')
result=dict(outcome='progress',summary='Added one review artwork for Cleveland’s [Storm at Sea, accession1924.848.10](https://clevelandart.org/art/1924.848.10), with three verified exact exhibition links and three artist connections. Preserved the specific impression, partial checklists and existing statuses. Seven entries remain held; no images added. Queue and checkpoint saved; existing supervisor verified running.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n)for n in names])
c.save(E/'final-result.json',result);c.save(R/'verified-batch-result.json',result)
print(json.dumps(result,ensure_ascii=False),flush=True)
