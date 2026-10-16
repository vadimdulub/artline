"""Checkpoint batch160; do not modify the external supervisor or artwork programme."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path

sp=importlib.util.spec_from_file_location('batch160',Path(__file__).with_name('continuous-exhibitions-000160.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
names=['startup-recovery-verification.json','source-capture-verification.json','candidate-review-verification.json','broader-duplicate-review.json','held-candidate-verification.json','next-route-source-verification.json','production-target-before-write.json','independent-database-verification.json','independent-public-verification.json','backup-verification.json']
for n in names:assert c.load(E/n)['passed']
v=c.load(E/'independent-database-verification.json');p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256']
assert v['plan_sha256']==pin==c.sha((E/'plan.json').read_bytes())
counts=v['verified_counts'];assert counts['new_exhibitions']==counts['new_venue_stops']==counts['new_artist_participation_links']==1
proc=c.load(E/'continuation-process-verification.json');pids=[proc['supervisor_pid'],proc['worker_pid']]
for pid in pids:os.kill(pid,0)
for f in proc['protected_files']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
locks=subprocess.check_output(['lsof','-nP','-a','-p',','.join(map(str,pids)),'-d','3'],text=True)
assert locks.count('continuous-exhibition-research/supervisor.lock')==2
ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
workers=[x for x in ps if '/opt/homebrew/bin/codex exec ' in x and 'continuous-exhibition-research/schema.json' in x]
supervisors=[x for x in ps if '/ops/continuous-exhibition-research.py run' in x and 'Python' in x]
assert len(workers)==len(supervisors)==1
c.save(E/'continuation-final-verification.json',dict(at=c.now(),supervisor_pid=pids[0],worker_pid=pids[1],inherited_lock=locks,single_exhibition_supervisor_and_worker_running=True,protected_files_unchanged=proc['protected_files'],separate_artwork_programme_modified=False,no_new_supervisor_started=True,passed=True))

next_task='Reconcile the National Gallery, London archive leads NG32/63 (Rembrandt and Vermeer, [1965]) and NG30/1980/66 (Second Sight: Titian and Rembrandt, 8 October–7 December 1980). Check event duplicates, original exhibition records and exact NG672/NG2568/NG1944 objects before linking. Preserve the Tate library HTTP 403 and closed-folder holds; the Young Turner 1988 checklist remains unknown.'
registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    assert c.sha(registry.read_bytes())==before['registry_sha256']
    s=next(x for x in after['sources'] if x['source_id']=='tate')
    s['research_status']='batch160_young_turner1988_event_venue_posthumous_artist_verified'
    s['last_checked_at']=c.now();s['cursor']=s.get('cursor') or {};cursor=s['cursor']
    cursor['completed_archive_records']=list(dict.fromkeys(cursor.get('completed_archive_records',[])+['TG 92/518']))
    cursor['batch160']=dict(exhibition_id=m.EID,venue_id=m.OID,artist_id=m.AID,participant_id=m.PID,
        source_native_ids=[x['native_id'] for x in p['sources']],source_urls=[x['receipt']['url'] for x in p['sources']],
        source_sha256=[x['receipt']['sha256'] for x in p['sources']],plan_sha256=pin,opening=m.START,closing=m.END,
        canonical_physical_venue_id=None,posthumous_participation=True,checklist_state='unknown',
        reviewed_distinct_tate_candidates=2,verified_new_events=1,unimported_candidate='TG92/514',
        bibliography_count_not_counted_as_exhibitions=True,evidence=rel('independent-database-verification.json'))
    cursor['resume_after_archive_reference']='TG 92/518'
    cursor['next']='Research another individually documented pictorial Tate event after TG92/518, or obtain the Young Turner1988 original checklist through an available authorized source. Do not retry library.tate.org.uk while held. TG92/514 needs explicit medium evidence; TG106/274 dates belong to a poster item.'
    for h in p['review']['held']:
        s.setdefault('holds',[]).append(dict(key=h['native_id'],reason=h['reason'],batch=160,evidence=rel('held-candidate-verification.json')))
    s['holds'].append(dict(key='young-turner1988-checklist',reason='1988 catalogue and press-notice contents uninspected; no exact objects or complete checklist asserted.',batch=160,evidence=rel('independent-public-verification.json')))
    s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n) for n in names if n!='next-route-source-verification.json']))
    ng=next(x for x in after['sources'] if x['source_id']=='national_gallery_london')
    ng['research_status']='batch160_two_archive_event_leads_captured_pending_reconciliation'
    ng['last_checked_at']=c.now();ng['cursor']=ng.get('cursor') or {}
    leads=c.load(E/'next-route-source-verification.json')
    ng['cursor']['batch160']=dict(candidates=leads['candidates'],discovered=2,prepared=0,imported=0,verified_additions=0,evidence=rel('next-route-source-verification.json'))
    ng['cursor']['next']=next_task
    ng['evidence']=list(dict.fromkeys(ng.get('evidence',[])+[rel('next-route-source-verification.json')]))
    changed={'tate','national_gallery_london'}
    assert [x for x in before['sources'] if x['source_id'] not in changed]==[x for x in after['sources'] if x['source_id'] not in changed]
    assert {k:v for k,v in before.items() if k!='sources'}=={k:v for k,v in after.items() if k!='sources'}
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch160.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
    assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=sorted(changed),all_unrelated_entries_and_holds_preserved=True,original_registry_unchanged=True,next_task=next_task,backup_before=str(B/'source-queue-before.json'),backup_after=str(B/'source-queue-after.json'),passed=True))
cp=dict(at=c.now(),batch=160,operation=m.OP,stage='independently_verified_complete',plan_sha256=pin,
    newly_captured_event_candidates=4,individually_reviewed_tate_candidates=2,national_gallery_london_discovery_only=2,
    prepared_exhibitions=1,imported_exhibitions=1,verified_exhibitions=1,verified_counts=counts,
    checklist_state='unknown',next_task=next_task,external_supervisor_owns_continuation=True,
    local_database_connections=0,main_catalogue_mutations=0,separate_artwork_programme_modified=False,
    holds=['Tate library detailHTTP403','TG92/514/1 folder closed until2088','Young Turner checklist contents uninspected','Historical physical venue not canonically matched'],
    attribution='Locked null preimage, persisted plan checksums, six insert audits, independent database read and public API checks. Previous and concurrent programmes excluded.')
c.save(E/'CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp)
names+=['continuation-process-verification.json','continuation-final-verification.json','queue-update-verification.json','CHECKPOINT.json']
c.save(E/'final-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,verified_counts=counts,
    artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes())) for n in names],
    source_citations_and_transaction_preimages_establish_own_additions=True,passed=True))
result=dict(outcome='progress',summary='Added and independently verified [Young Turner at Tate, 11 January–20 March 1988](https://archive.tate.org.uk/Record.aspx?src=CalmView.Catalog&id=TG+92%2F518): one exhibition, one venue stop and one posthumous artist connection. Review status and unknown checklist preserved. Two London archive leads saved; Tate library HTTP 403 hold recorded. Queue/checkpoint saved; supervisor and worker verified running.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n) for n in names+['final-verification.json']])
c.save(E/'result.json',result);c.save(R/'batch-result.json',result)
print(json.dumps(result,ensure_ascii=False))
