"""Save verified batch157 progress and narrowly update researched source cursors."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
sp=importlib.util.spec_from_file_location('batch157',Path(__file__).with_name('continuous-exhibitions-000157.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
names=['registry-and-policy-verification.json','startup-scope-and-holds-verification.json','arthive-discovery-outcome.json','source-capture-verification.json','candidate-review-verification.json','independent-database-verification.json','independent-public-verification.json','backup-verification.json','production-target-before-write.json']
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
next_task="Inspect the original Australian Woodcuts and Linocuts 1984 checklist if available. For another historical event, reconcile NGA Prints + Printmaking Women's Imprint records 4069/6611 as a possible duplicate pair before import; both are listed at AGNSW 1–31 October 1982. Continue gallery 949 history page 6 then page 7. Retain Fruit and flowers 11419 date conflict, Sali Herman 8159 medium gap and all Arthive/Getty/Fitzwilliam/Whistler holds."
hist=c.load(E/'pp-gallery949-history6.json')
leads=[x for x in hist['links'] if x['href'].startswith('/exhibitions/')]
assert len(leads)==20
discovery=dict(at=c.now(),source=hist['receipt'],directory_leads=leads,directory_count=20,individual_candidate_pages_reviewed=['14','11419','8159'],selected=['14'],confirmed_new_production_exhibitions=1,
  holds=p['review']['held'],other_directory_warnings=[dict(native_ids=['4069','6611'],reason='Same venue/dates and similar titles; reconcile possible duplicate before selecting.'),dict(native_id='2821',reason='1982 Sydney date but1992–1993 later stops in directory; chronology/tour identity unresolved.'),dict(native_id='2482',reason='Directory Perc Tucker stop6December1983–6January1983 has reversed dates; retain conflict.')],
  excluded_directory_mediums=[dict(native_id='2460',reason='Explicit photography title'),dict(native_id='8154',reason='Explicit photography title')],
  direct_nsw_archive=dict(receipt=c.load(E/'nsw-exhibition-archive.json')['receipt'],outcome='2000–2010 index outside historical scope; no modern events imported.'),
  next_task=next_task,all_directory_leads_are_discovery_not_verified_exhibitions=True,passed=True)
c.save(E/'discovery-outcome-verification.json',discovery);names.append('discovery-outcome-verification.json')
registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
changed={'art_gallery_nsw','australian_prints_and_printmaking','arthive_exhibitions','getty_museum','fitzwilliam_remaining_pictorial_events'}
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    assert c.sha(registry.read_bytes())==before['registry_sha256']
    touched=[]
    for group in ['sources','supplemental_sources']:
        for s in after[group]:
            key=s['source_id']
            if key not in changed:continue
            touched.append(dict(group=group,source_id=key))
            cursor=s.get('cursor') or {};s['cursor']=cursor
            if key in ['getty_museum','fitzwilliam_remaining_pictorial_events']:
                cursor['batch157_hold_review']=dict(at=c.now(),new_network_requests=0,decision='Existing deliveries not replayed; unresolved identity/date holds unchanged. Rotate to available Australian institutional archive.',evidence=rel('startup-scope-and-holds-verification.json'))
                s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel('startup-scope-and-holds-verification.json')]))
            elif key=='arthive_exhibitions':
                cursor['batch157']=dict(at=c.now(),historical_archive_access='held_http429',new_network_requests=0,new_discoveries=0,evidence=rel('arthive-discovery-outcome.json'),next='Await documented provider access-state change; no unchanged retry.')
                s['last_hold_reviewed_at']=c.now();s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel('arthive-discovery-outcome.json')]))
            else:
                s['research_status']='batch157_australian_woodcuts_linocuts1984_event_and_venue_verified'
                s['last_checked_at']=c.now()
                s['counting_note']='Batch 157 has one shared production exhibition, also referenced by the NSW institution route and NGA Prints + Printmaking route; never count twice.'
                cursor['batch157']=dict(exhibition_id=m.EID,native_exhibition_id='14',native_gallery_id='949',source_url=p['source']['receipt']['url'],capture_sha256=p['source']['receipt']['sha256'],plan_sha256=pin,new_exhibitions=1,new_venue_stops=1,exact_participation_links=0,checklist_state='unknown',directory_leads=20,individual_candidates_reviewed=3,source_history_page=6,next_candidate_native_ids=['4069','6611'],next_history_url='https://printsandprintmaking.gov.au/galleries/949/history/?num_results=20&page=7',next=next_task,evidence=rel('independent-database-verification.json'))
                cursor['next']=next_task
                cursor['completed']=list(dict.fromkeys(cursor.get('completed',[])+[p['source']['receipt']['url']]))
                for h in p['review']['held']:
                    receipt=c.load(E/('pp-'+h['native_id']+'.json'))['receipt']
                    s.setdefault('holds',[]).append(dict(key='pp-exhibition-'+h['native_id'],reason=h['reason'],url=receipt['url'],capture_sha256=receipt['sha256'],evidence=rel('candidate-review-verification.json')))
                s['holds'].append(dict(key='pp14-original-checklist',reason='Documentation Checklist is mentioned but checklist contents are absent from the inspected page. No participants/objects inferred.',evidence=rel('independent-public-verification.json')))
                s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n) for n in names]))
    assert {x['source_id'] for x in touched}==changed
    for group in ['sources','supplemental_sources']:
        assert [x for x in before[group] if x['source_id'] not in changed]==[x for x in after[group] if x['source_id'] not in changed]
    assert {k:v for k,v in before.items() if k not in ['sources','supplemental_sources']}=={k:v for k,v in after.items() if k not in ['sources','supplemental_sources']}
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch157.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
    assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_routes=touched,all_unrelated_routes_and_existing_holds_preserved=True,original_registry_unchanged=True,resume=next_task,passed=True))
counts=v['verified_counts']
cp=dict(at=c.now(),batch=157,operation=m.OP,stage='independently_verified_complete',plan_sha256=pin,directory_leads=20,individual_candidate_pages_reviewed=3,prepared_exhibitions=1,imported_exhibitions=1,verified_exhibitions=1,held_individual_candidates=2,verified_counts=counts,checklist_state='unknown',next_task=next_task,external_supervisor_owns_continuation=True,local_database_connections=0,separate_artwork_programme_modified=False)
c.save(E/'CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp)
names+=['startup-recovery-and-identity-query.json','continuation-process-verification.json','continuation-final-verification.json','queue-update-verification.json','CHECKPOINT.json']
c.save(E/'completion-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes())) for n in names],verified_counts=counts,prior_and_concurrent_campaign_increments_excluded=True,passed=True))
result=dict(outcome='progress',summary='Verified one new exhibition—Australian Woodcuts and Linocuts, Sydney, 30 June–19 August 1984—and one venue stop in production. Checklist remains unknown; two other candidates held. Existing supervisor/worker and inherited lock verified.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n) for n in names+['completion-verification.json']])
c.save(E/'result.json',result);c.save(R/'batch-result.json',result)
print(json.dumps(result,ensure_ascii=False))
