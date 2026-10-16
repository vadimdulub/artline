"""Persist batch156's verified cursor without modifying the external supervisor."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
sp=importlib.util.spec_from_file_location('batch156',Path(__file__).with_name('continuous-exhibitions-000156.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
names=['source-capture-verification.json','candidate-review-verification.json','broader-title-duplicate-verification.json','legacy-dutch-identity-verification.json','independent-database-verification.json','independent-public-verification.json','backup-verification.json','production-target-before-write.json']
for n in names:assert c.load(E/n)['passed']
v=c.load(E/'independent-database-verification.json');pin=c.load(E/'plan-pin.json')['sha256'];p=c.load(E/'plan.json')
assert v['plan_sha256']==pin==c.sha((E/'plan.json').read_bytes())
assert v['verified_counts']['new_exhibitions']==1 and len(v['rows']['exhibition_occurrences'])==1
proc=c.load(E/'continuation-process-verification.json');pids=[proc['supervisor_pid'],proc['worker_pid']]
for pid in pids:os.kill(pid,0)
for f in proc['protected_files']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
locks=subprocess.check_output(['lsof','-nP','-a','-p',','.join(map(str,pids)),'-d','3'],text=True)
assert locks.count('continuous-exhibition-research/supervisor.lock')==2
processes=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
workers=[line for line in processes if '/opt/homebrew/bin/codex exec ' in line and 'continuous-exhibition-research/schema.json' in line]
supervisors=[line for line in processes if '/ops/continuous-exhibition-research.py run' in line and 'Python' in line]
assert len(workers)==len(supervisors)==1
c.save(E/'continuation-final-verification.json',dict(at=c.now(),supervisor_pid=pids[0],worker_pid=pids[1],inherited_lock=locks,single_exhibition_supervisor_and_worker_running=True,protected_files_unchanged=proc['protected_files'],no_additional_supervisor_started=True,passed=True))
registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
next_task='Retrieve the original Modern Dutch Painting 1983 exhibition catalogue to establish named participants and exact works. For event expansion rotate to the unresearched Art Gallery of New South Wales historical archive; preserve Arthive and other provider holds. American 1982, Irish 1983 and Dutch landscape 1985–1986 require original dated sources before import.'
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    assert c.sha(registry.read_bytes())==before['registry_sha256']
    s=next(x for x in after['sources'] if x['source_id']=='national_gallery_athens')
    s['research_status']='batch156_dutch_painting1983_event_and_venue_verified'
    s['last_checked_at']=c.now();cursor=s.setdefault('cursor',{})
    en=c.load(E/'contemporary-dutch-painting.json');gr=c.load(E/'dutch-greek.json')
    cursor['completed']=list(dict.fromkeys(cursor.get('completed',[])+[en['receipt']['url']]))
    cursor['batch156']=dict(exhibition_id=m.EID,native_ids=[gr['native_id'],en['native_id']],source_urls=[gr['receipt']['url'],en['receipt']['url']],capture_sha256=[gr['receipt']['sha256'],en['receipt']['sha256']],opening='1983-09-16',closing='1983-10-23',new_exhibitions=1,new_venue_stops=1,source_records=2,participation_links=0,checklist_state='unknown',plan_sha256=pin,existing_spanish_event_excluded=m.SPANISH,reviewed_candidates=5,next=next_task,evidence=rel('independent-database-verification.json'))
    cursor['next']=next_task
    for h in p['review']['held']:
        captured=[c.load(E/f)['receipt'] for f in h['source_files']]
        s.setdefault('holds',[]).append(dict(key=h['key'],at=c.now(),reason=h['reason'],source_urls=[r['url'] for r in captured],capture_sha256=[r['sha256'] for r in captured],evidence=rel('candidate-review-verification.json')))
    s['holds'].append(dict(key='dutch1983-original-checklist',reason='Bilingual event pages identify no artists or individual works. Checklist unknown; no participation or full-checklist claim inferred.',evidence=rel('independent-public-verification.json')))
    s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n) for n in names]))
    assert [x for x in before['sources'] if x['source_id']!='national_gallery_athens']==[x for x in after['sources'] if x['source_id']!='national_gallery_athens']
    assert {k:v for k,v in before.items() if k!='sources'}=={k:v for k,v in after.items() if k!='sources'}
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch156.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
    assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=['national_gallery_athens'],all_unrelated_routes_and_existing_holds_preserved=True,original_registry_unchanged=True,resume=next_task,passed=True))
counts=v['verified_counts']
cp=dict(at=c.now(),batch=156,operation=m.OP,stage='independently_verified_complete',plan_sha256=pin,reviewed_candidates=5,newly_discovered_candidates=0,existing_archive_leads_reused=5,discovery_counting_note='The plan discovery count denotes the five selected archive leads reviewed in this invocation; all came from the existing batch004 inventory and are not claimed as new discoveries.',prepared_exhibitions=1,imported_exhibitions=1,verified_exhibitions=1,existing_events_excluded=1,date_conflict_candidates_held=3,verified_counts=counts,checklist_state='unknown',next_task=next_task,external_supervisor_owns_continuation=True,local_database_connections=0,separate_artwork_programme_modified=False)
c.save(E/'CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp)
names+=['startup-recovery-and-identity-query.json','continuation-process-verification.json','continuation-final-verification.json','queue-update-verification.json','CHECKPOINT.json']
c.save(E/'completion-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes())) for n in names],verified_counts=counts,prior_and_concurrent_campaign_increments_excluded=True,passed=True))
result=dict(outcome='progress',summary='Added and independently verified Modern Dutch Painting (Athens, 16 September–23 October 1983), one venue stop and two official source records. Review status and unknown checklist preserved. Three date-conflict candidates held; one existing Spanish exhibition excluded.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n) for n in names+['completion-verification.json']])
c.save(E/'result.json',result);c.save(R/'batch-result.json',result)
print(json.dumps(result,ensure_ascii=False))
