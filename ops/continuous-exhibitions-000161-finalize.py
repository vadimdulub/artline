"""Persist verified batch161 outcome; leave external supervisor/artwork programme untouched."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
sp=importlib.util.spec_from_file_location('b161',Path(__file__).with_name('continuous-exhibitions-000161.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;B=m.B;R=m.R;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
names=['startup-recovery-verification.json','startup-scope-and-holds-verification.json','registry-policy-verification.json','arthive-discovery-outcome.json','source-capture-verification.json','candidate-review-verification.json','duplicate-venue-review.json','broader-duplicate-verification.json','production-target-before-write.json','independent-database-verification.json','independent-public-verification.json','existing-image-delivery-verification.json','backup-verification.json','next-route-source-verification.json','next-event-lead-reviewed.json']
for n in names:assert c.load(E/n)['passed'],n
p=c.load(E/'plan.json');v=c.load(E/'independent-database-verification.json');pin=c.load(E/'plan-pin.json')['sha256'];counts=v['verified_counts']
assert pin==v['plan_sha256']==c.sha((E/'plan.json').read_bytes())
assert (counts['new_exhibitions'],counts['new_venue_stops'],counts['new_exact_artwork_links'],counts['new_artist_participation_links'])==(2,2,4,4)
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
next_task="Reconcile National Gallery archive NG30/1981/4 for Second Sight: Rubens and Gainsborough,18February–20April1981, against its original NG32 event record and live exhibition duplicates. Exact inventory leads are NG4815 (Rubens) and NG109 (Gainsborough); inspect canonical objects before linking. Continue Second Sight archive search page2 if needed. Preserve the bracketed1965 date and both partial checklists; do not replay batch161 or retry Arthive/Tate-library/Whistler access holds."
lead=c.load(E/'next-event-lead-reviewed.json');arth=c.load(E/'arthive-discovery-outcome.json')
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    assert c.sha(registry.read_bytes())==before['registry_sha256']==c.load(E/'registry-policy-verification.json')['sha256']
    s=next(x for x in after['sources'] if x['source_id']=='national_gallery_london')
    s['research_status']='batch161_two_historical_events_four_exact_links_verified';s['last_checked_at']=c.now();s['cursor']=s.get('cursor') or {}
    cursor=s['cursor'];cursor['completed_archive_records']=list(dict.fromkeys(cursor.get('completed_archive_records',[])+['NG32/63','NG32/130','NG30/1980/66']))
    cursor['batch161']=dict(exhibition_ids=m.EIDS,source_native_ids=['NG32/63','NG32/130','NG30/1980/66'],source_sha256=[x['receipt']['sha256'] for e in p['events'] for x in e['sources']],source_urls=[x['receipt']['url'] for e in p['events'] for x in e['sources']],plan_sha256=pin,delivered_previous_event_leads=2,prepared_exhibitions=2,imported_exhibitions=2,verified_counts=counts,distinct_existing_artworks=3,illustrated_exact_connections=4,existing_images=3,new_images=0,checklist_state='partial',date_qualification='NG32/63 year[1965] supplied in brackets by archive; day fields null; qualification preserved.',next_native_id='NG30/1981/4',next_inventory_leads=['NG4815','NG109'],next_lead_receipt=lead['receipt'],next_discovery_not_imported=True,evidence=rel('independent-database-verification.json'))
    cursor['next']=next_task
    s.setdefault('holds',[]).extend([
        dict(key='NG32/63-exact-dates',reason='Archive title supplies bracketed[1965], separate Date field empty. Exact dates and independent year corroboration remain open; held occurrence and date qualification are distinct.',evidence=rel('candidate-review-verification.json')),
        dict(key='NG32/63-NG32/130-complete-checklists',reason='Two explicitly documented paintings per event; original catalogue/archival contents uninspected. Preserve partial checklists and unknown catalogue numbers/lenders.',evidence=rel('independent-public-verification.json'))])
    s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n) for n in names if n!='arthive-discovery-outcome.json']))
    a=next(x for x in after['supplemental_sources'] if x['source_id']=='arthive_exhibitions')
    a['last_checked_at']=arth['at'];a['cursor']['batch161']=dict(at=arth['at'],historical_archive_access='held_http429',new_network_requests=0,new_discoveries=0,hold_reused_without_request=True,evidence=rel('arthive-discovery-outcome.json'),next='Await documented provider access-state change; no unchanged retry.')
    a['evidence']=list(dict.fromkeys(a.get('evidence',[])+[rel('arthive-discovery-outcome.json')]))
    assert [x for x in before['sources'] if x['source_id']!='national_gallery_london']==[x for x in after['sources'] if x['source_id']!='national_gallery_london']
    assert [x for x in before['supplemental_sources'] if x['source_id']!='arthive_exhibitions']==[x for x in after['supplemental_sources'] if x['source_id']!='arthive_exhibitions']
    assert {k:v for k,v in before.items() if k not in ['sources','supplemental_sources']}=={k:v for k,v in after.items() if k not in ['sources','supplemental_sources']}
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch161.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=['national_gallery_london','arthive_exhibitions'],all_unrelated_entries_and_holds_preserved=True,registry_unchanged=True,backup_before=str(B/'source-queue-before.json'),backup_after=str(B/'source-queue-after.json'),next_task=next_task,passed=True))
cp=dict(at=c.now(),batch=161,operation=m.OP,stage='independently_verified_complete',plan_sha256=pin,prepared_exhibitions=2,imported_exhibitions=2,verified_exhibitions=2,verified_counts=counts,distinct_existing_artworks=3,new_distinct_event_lead_not_imported=lead,checklist_state='partial',next_task=next_task,external_supervisor_owns_continuation=True,local_database_connections=0,main_catalogue_mutations=0,separate_artwork_programme_modified=False,attribution='Locked null preimage,3 persisted source plan checksums,15 null-before audits, fresh production verification and public delivery checks. Previous/concurrent campaigns excluded.')
c.save(E/'CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp)
names+=['continuation-process-verification.json','continuation-final-verification.json','queue-update-verification.json','CHECKPOINT.json']
c.save(E/'final-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,verified_counts=counts,artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes())) for n in names],source_citations_and_transaction_preimages_establish_own_additions=True,passed=True))
result=dict(outcome='progress',summary='Added and independently verified two National Gallery exhibitions: [Rembrandt and Vermeer, [1965]](https://www.nationalgallery.org.uk/research/research-centre/archive/record/NG32/63) and [Second sight: Titian/Rembrandt,1980](https://www.nationalgallery.org.uk/research/research-centre/archive/record/NG32/130). Two venue stops, four exact artwork links and four posthumous artist connections; three existing images verified. Review states, qualified1965 date and partial checklists preserved. Queue/checkpoint saved; existing supervisor verified running.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n) for n in names+['final-verification.json']])
c.save(E/'result.json',result);c.save(R/'batch-result.json',result)
(E/'README.md').write_text('# Batch161 — National Gallery archive\n\nTwo review exhibitions, two stops, four exact links and four posthumous artist connections independently verified. The three linked main works and their existing images are unchanged. No new artists, main artworks, documentary-only entries or images.\n\nThe archive-supplied [1965] date remains qualified; exact dates unknown. Second sight: Titian/Rembrandt was held8October–7December1980. Both checklists remain partial.\n\nSee final-verification.json for checksummed receipts. The queue retains the Arthive HTTP429 hold and all unrelated routes. Next: NG30/1981/4, Rubens NG4815 and Gainsborough NG109; discovery only.\n')
print(json.dumps(result,ensure_ascii=False))
