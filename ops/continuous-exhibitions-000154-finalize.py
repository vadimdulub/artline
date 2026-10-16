"""Verify saved receipts and update only researched source cursors."""
import fcntl, json, os, subprocess
from pathlib import Path
import importlib.util
sp=importlib.util.spec_from_file_location('batch154',Path(__file__).with_name('continuous-exhibitions-000154.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B;Q=E.parents[1]/'source-queue.json'
rel=lambda n:str((E/n).relative_to(m.ROOT))
v=c.load(E/'independent-database-verification.json');pub=c.load(E/'independent-public-verification.json');backup=c.load(E/'backup-verification.json')
assert v['passed'] and pub['passed'] and backup['passed']
assert len(v['rows']['exhibition_entries'])==28 and sum(bool(e['artwork_id']) for e in v['rows']['exhibition_entries'])==12
pin=c.load(E/'plan-pin.json')['sha256'];assert pin==v['plan_sha256']==backup['plan_sha256']
for name in ['hockney-reference-capture.json','hockney-catalogue-reference.json']:
    rc=c.load(E/name)['receipt'];m.receipt(rc)
ref=c.load(E/'hockney-catalogue-reference.json')
assert '064292600X' in ref['text'] and 'pages: 32' in ref['text']
hockney_next='Acquire and inspect the actual 32-page 1976 catalogue, ISBN064292600X, before identifying exhibited impressions. Official reference9467 supplies bibliography only, no checklist or scan link; do not repeat the same reference pages as new coverage. Preserve NGV tour/venue date conflicts and main NGA access hold.'
hockney_review=dict(at=c.now(),exhibition_native_id='3296',reference_native_id='9467',sources=[c.load(E/n)['receipt'] for n in ['hockney-reference-capture.json','hockney-catalogue-reference.json']],bibliography=dict(title='David Hockney prints : selected from the collection of the Australian National Gallery, Canberra.',author='Australian National Gallery',publisher='Australian Govt. Pub. Service',place='Canberra',year=1976,pages=32,isbn='064292600X'),full_checklist_obtained=False,explicit_object_ids_found=0,new_production_changes=0,decision=hockney_next,passed=True)
c.save(E/'hockney-reference-outcome-verification.json',hockney_review)
process=c.load(E/'continuation-process-verification.json')
for p in process['protected_files_unchanged']:assert c.sha(Path(p['path']).read_bytes())==p['sha256']
for pid in [process['supervisor_pid'],process['worker_pid']]:os.kill(pid,0)
lock_lines=subprocess.check_output(['lsof','-nP','-a','-p',str(process['supervisor_pid'])+','+str(process['worker_pid']),'-d','3'],text=True).splitlines()
assert len([s for s in lock_lines if 'continuous-exhibition-research/supervisor.lock' in s])==2
c.save(E/'continuation-final-verification.json',dict(at=c.now(),supervisor_pid=process['supervisor_pid'],worker_pid=process['worker_pid'],inherited_lock_lines=lock_lines,protected_files_still_unchanged=True,additional_processes_launched=0,passed=True))
source_names=['independent-database-verification.json','independent-public-verification.json','source-capture-verification.json','visual-review-verification.json','candidate-reconciliation-verification.json','backup-verification.json']
blake_next='Resolve original Blake Philadelphia1939 documentary entries154 and176 using official RISD native IDs/accessions and historical lender continuity. No171/Harvard298817 is complete; do not replay. Retain distinct versions168/169 and173/174 and existing NGA161 provenance hold.'
next_task='Resume the missing-image queue at Cleveland native106596, selecting up to10 exact exhibition-linked objects after delivered native106595, with per-object rights and visual review. For later linking batches, reconcile Blake1939 nos154/176 with RISD accessions; no171 is delivered.'
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    before=c.load(Q);after=m.serial(before);before_sha=c.sha(Q.read_bytes())
    for source_id in ['harvard_art_museums','philadelphia_museum_art']:
        s=next(x for x in after['sources'] if x['source_id']==source_id)
        s['research_status']='batch154_blake1939_no171_exact_object_link_and_review_work_verified'
        s['last_checked_at']=c.now()
        s.setdefault('cursor',{})['batch154']=dict(exhibition_id=m.EVENT,catalogue_number='171',entry_id=m.ENTRY,native_object_id='298817',accession='1915.8',artwork_id=m.WORK,plan_sha256=pin,new_review_artworks=1,new_exact_links=1,remaining_unlinked_entries=16,next=blake_next,evidence=rel('independent-database-verification.json'))
        s['cursor']['next']=blake_next
        for h in s.get('holds',[]):
            if h.get('key')=='blake-1939-no171':h.update(resolved_at=c.now(),resolved_by_batch=154,resolution_evidence=rel('candidate-reconciliation-verification.json'),status='resolved')
        s.setdefault('holds',[]).append(dict(key='partial-checklist-batch154',reason='Original1939 checklist remains partial:28 entries,12 now exactly linked,16 unlinked. No171 is unillustrated; Harvard noncommercial-only image language does not authorize a new production image.',evidence=rel('independent-public-verification.json')))
        s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n) for n in source_names]))
    pp=next(x for x in after['supplemental_sources'] if x['source_id']=='australian_prints_and_printmaking')
    pp['research_status']='batch154_reference9467_bibliography_captured_original_checklist_pending'
    pp['last_checked_at']=c.now()
    pp.setdefault('cursor',{})['batch154']=dict(exhibition_native_id='3296',reference_native_id='9467',source_url=ref['receipt']['url'],capture_sha256=ref['receipt']['sha256'],catalogue_isbn='064292600X',new_exhibitions=0,new_exact_links=0,next=hockney_next,evidence=rel('hockney-reference-outcome-verification.json'))
    pp['cursor']['next']=hockney_next
    pp.setdefault('holds',[]).append(dict(key='3296-original-checklist',reason=hockney_next,evidence=rel('hockney-reference-outcome-verification.json')))
    pp['evidence']=list(dict.fromkeys(pp.get('evidence',[])+[rel('hockney-reference-outcome-verification.json')]))
    changed={'harvard_art_museums','philadelphia_museum_art'}
    assert [s for s in before['sources'] if s['source_id'] not in changed]==[s for s in after['sources'] if s['source_id'] not in changed]
    assert [s for s in before['supplemental_sources'] if s['source_id']!='australian_prints_and_printmaking']==[s for s in after['supplemental_sources'] if s['source_id']!='australian_prints_and_printmaking']
    assert {k:v for k,v in before.items() if k not in ['sources','supplemental_sources']}=={k:v for k,v in after.items() if k not in ['sources','supplemental_sources']}
    c.save(B/'source-queue-before.json',before);c.save(B/'source-queue-after.json',after)
    tmp=Q.with_suffix('.batch154.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
    assert c.load(Q)==after
c.save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=sorted(changed|{'australian_prints_and_printmaking'}),all_unrelated_routes_and_holds_preserved=True,original_registry_unchanged=True,resume=next_task,passed=True))
counts=v['verified_counts']
cp=dict(at=c.now(),batch=154,stage='independently_verified_complete',operation=m.OP,plan_sha256=pin,selected_existing_documentary_entries=1,prepared_main_artworks=1,imported_main_artworks=1,verified_main_artworks=1,prepared_exact_links=1,imported_exact_links=1,verified_exact_links=1,verified_counts=counts,checklist_state='partial',total_entries_in_existing_event=28,exact_linked_entries=12,remaining_unlinked_entries=16,images_added=0,source_reference_only_routes=['australian_prints_and_printmaking/exhibitions/3296/references/9467'],next_task=next_task,external_supervisor_owns_continuation=True,local_catalogue_connections=0,separate_artwork_programme_modified=False)
c.save(E/'CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp)
names=source_names+['startup-recovery-verification.json','hockney-reference-outcome-verification.json','continuation-process-verification.json','continuation-final-verification.json','queue-update-verification.json','CHECKPOINT.json']
artifacts=[dict(path=rel(n),sha256=c.sha((E/n).read_bytes())) for n in names]
c.save(E/'completion-verification.json',dict(at=c.now(),operation=m.OP,plan_sha256=pin,artifacts=artifacts,verified_counts=counts,prior_and_concurrent_campaign_increments_excluded=True,no_user_approval_pending=True,passed=True))
result=dict(outcome='progress',summary='Added one review artwork, [Blake’s Michael Binding Satan](https://harvardartmuseums.org/collections/object/298817) (Harvard1915.8, c.1805), and verified its exact link to Philadelphia1939 catalogue no.171. Historical labels and partial checklist preserved; no images added. Hockney catalogue reference captured; checklist still unavailable.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(n) for n in names+['completion-verification.json']])
c.save(E/'result.json',result);c.save(R/'batch-result.json',result)
print(json.dumps(result,ensure_ascii=False),flush=True)
