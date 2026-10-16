"""Save verified batch158 receipts and only the source routes actually researched."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
sp=importlib.util.spec_from_file_location('batch158',Path(__file__).with_name('continuous-exhibitions-000158.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
v=c.load(E/'independent-database-verification.json');pub=c.load(E/'independent-public-verification.json');backup=c.load(E/'backup-verification.json');p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256']
assert v['passed'] and pub['passed'] and backup['passed'] and v['plan_sha256']==backup['plan_sha256']==pin
assert len(v['rows']['exhibition_entries'])==28 and pub['exact_linked_entries']==14
for s in p['sources'].values():m.body(s)
hold=c.load(E/'risd-baptism.json')['receipt'];m.body(hold);assert hold['status']==403
assert all(s['retrieved_at']<hold['retrieved_at']for s in p['sources'].values())
c.save(E/'source-access-hold-verification.json',dict(at=c.now(),provider='risdmuseum.org',direct_request=hold,successful_web_pages_returned_at=p['sources']['baptism']['retrieved_at'],successful_extracts_precede_hold=True,requests_after_hold=0,decision='Preserve prior successful primary-source web extracts; no origin HTML claimed. Stop further RISD page/image retrieval until documented access-state change. No images downloaded or added.',passed=True))
proc=c.load(E/'startup-recovery-verification.json')
for f in proc['protected_files']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
for pid in [proc['supervisor_pid'],proc['worker_pid']]:os.kill(pid,0)
locks=subprocess.check_output(['lsof','-nP','-a','-p',str(proc['supervisor_pid'])+','+str(proc['worker_pid']),'-d','3'],text=True)
assert locks.count('continuous-exhibition-research/supervisor.lock')==2
c.save(E/'continuation-final-verification.json',dict(at=c.now(),supervisor_pid=proc['supervisor_pid'],worker_pid=proc['worker_pid'],inherited_lock_lines=locks.splitlines(),protected_files_unchanged=proc['protected_files'],external_supervisor_owns_continuation=True,no_additional_supervisor_or_worker_launched=True,separate_artwork_programme_untouched=True,passed=True))
next_task='Reconcile the six Boston-lent Blake Philadelphia1939 entries158,159,162,163,164 and170 with official MFA object IDs, accessions and original lender/provenance evidence. RISD154/176 are complete; keep RISD HTTP403, NGA161 provenance and same-title version holds. For image batches resume Cleveland after native106615.'
names=['independent-database-verification.json','independent-public-verification.json','source-capture-verification.json','visual-review-verification.json','candidate-reconciliation-verification.json','backup-verification.json','source-access-hold-verification.json','startup-recovery-verification.json','registry-and-scope-verification.json','continuation-final-verification.json']
with Q.with_suffix('.lock').open('a+')as lk:
    fcntl.flock(lk,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    s=next(x for x in after['sources']if x['source_id']=='philadelphia_museum_art')
    s['research_status']='batch158_blake1939_risd154_176_two_review_works_two_exact_links_verified';s['last_checked_at']=c.now()
    s.setdefault('cursor',{})['batch158']=dict(exhibition_id=m.EVENT,entries=[dict(catalogue_number=o['number'],entry_id=o['entry'],accession=o['accession'],artwork_id=o['id'])for o in m.OBJECTS],plan_sha256=pin,new_review_artworks=2,new_exact_links=2,total_entries=28,exact_linked_entries=14,remaining_unlinked_entries=14,checklist_state='partial',next=next_task,evidence=rel('independent-database-verification.json'))
    s['cursor']['next']=next_task;s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n)for n in names]))
    s.setdefault('holds',[]).append(dict(key='partial-checklist-batch158',reason='Original1939 checklist remains partially transcribed:28 entries,14 exactly linked,14 still unlinked. RISD154/176 now resolved; two new works remain unillustrated. Preserve the original source labels and separate same-title versions.',evidence=rel('independent-public-verification.json')))
    sid='risd_museum_official_collection'
    assert not any(x['source_id']==sid for x in after['supplemental_sources'])
    after['supplemental_sources'].append(dict(source_id=sid,source_kind='official_museum_collection',institution_or_network='Rhode Island School of Design Museum',official_website='https://risdmuseum.org/',research_status='batch158_two_exact_links_verified_provider_direct_http403_held',last_checked_at=c.now(),cursor=dict(batch158=dict(accessions=['32.219','31.280'],catalogue_numbers=['154','176'],exhibition_id=m.EVENT,plan_sha256=pin,new_review_artworks=2,new_exact_links=2,source_urls=[p['sources'][o['key']]['url']for o in m.OBJECTS],source_capture_sha256=[p['sources'][o['key']]['sha256']for o in m.OBJECTS],origin_html_not_captured=True),next='Wait for a documented RISD access-state change before further object/image retrieval. Preserve existing successful extracted source captures. Rotate to accessible MFA Boston source for the next exact-object batch.'),holds=[dict(key='provider-access-http403',url=hold['url'],at=hold['retrieved_at'],status=403,evidence=rel('source-access-hold-verification.json'),reason='Direct museum request returned Cloudflare403. No retry or bypass after hold. Successful web page extracts predate this hold.')],image_rights_rule='The two captured official object records label Public Domain/CC0. No images downloaded; no blanket RISD image licence inferred.',counting_note='These are the same two changes recorded under Philadelphia; count once, not once per source.',evidence=[rel(n)for n in names]))
    assert [x for x in before['sources']if x['source_id']!='philadelphia_museum_art']==[x for x in after['sources']if x['source_id']!='philadelphia_museum_art']
    assert before['supplemental_sources']==after['supplemental_sources'][:-1]
    assert {k:v for k,v in before.items()if k not in ['sources','supplemental_sources']}=={k:v for k,v in after.items()if k not in ['sources','supplemental_sources']}
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch158.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=['philadelphia_museum_art','risd_museum_official_collection'],unrelated_routes_and_holds_preserved=True,original_registry_unchanged=True,resume=next_task,passed=True));names.append('queue-update-verification.json')
counts=v['verified_counts']
cp=dict(at=c.now(),batch=158,operation=m.OP,stage='independently_verified_complete',plan_sha256=pin,selected_existing_entries=2,prepared_main_artworks=2,imported_main_artworks=2,verified_main_artworks=2,prepared_exact_links=2,imported_exact_links=2,verified_exact_links=2,verified_counts=counts,checklist_state='partial',total_entries=28,exact_linked_entries=14,remaining_unlinked_entries=14,next_task=next_task,local_catalogue_connections=0,separate_artwork_programme_modified=False,external_supervisor_owns_continuation=True)
c.save(E/'CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp);names.append('CHECKPOINT.json')
c.save(E/'completion-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,verified_counts=counts,artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes()))for n in names],prior_and_concurrent_campaign_changes_excluded=True,no_user_approval_pending=True,passed=True));names.append('completion-verification.json')
result=dict(outcome='progress',summary='Added two review artworks and verified two exact links to Philadelphia1939 catalogue entries154/176: [Baptism of Christ](https://risdmuseum.org/art-design/collection/baptism-christ-32219) and [St. Paul Preaching at Athens](https://risdmuseum.org/art-design/collection/st-paul-preaching-athens-31280). Checklist remains partial; no images added. Queue and checkpoint saved; existing supervisor verified running.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n)for n in names])
c.save(E/'worker-result.json',result);c.save(R/'worker-result.json',result)
print(json.dumps(result,ensure_ascii=False),flush=True)
