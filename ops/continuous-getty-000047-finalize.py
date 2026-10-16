#!/usr/bin/env python3
"""Persist batch receipt/cursors and merge only the researched Getty queue entry."""
import copy, csv, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('w47',Path(__file__).with_name('continuous-getty-images-000047.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
i=w.i;h=w.h;E=w.E

with (w.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=w.load(E/'batch-verification-receipt.json');replay=w.load(E/'independent-resume-verification.json')
 assert replay['unchanged_snapshot'] and all(v==0 for v in replay['replay_increments'].values())
 counts=receipt['verified_counts'];ids=receipt['production_ids'];now=h.now()
 assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=18,alternate_images=0,museum_links=0)
 data=w.load(E/'bounded-gap-input.json.gz');holds=w.load(E/'specific-hold-verification.json')['records'];discovery=w.load(E/'byzantine-discovery-verification.json')
 assert len(data['rows'])==20 and len(holds)==2 and {r['id'] for r in data['rows']}==set(ids)|{r['artwork_id'] for r in holds}
 assert len(discovery['records'])==50 and all(not r['whole_object_candidate'] for r in discovery['records']) and not discovery['existing_image_gap_candidates']
 checks=[]
 for p in (E/'source-captures').glob('*.receipt.json'):
  rc=w.load(p);w.body(rc);checks.append(dict(receipt=str(p.relative_to(w.ROOT)),status=rc['status'],sha256=rc['sha256'],body_path=rc['body_path']))
 assert all(r['status']==200 for r in checks)
 w.save(E/'independent-route-completeness-verification.json',dict(at=now,source_captures=checks,byzantine_source_leads=50,byzantine_component_or_ensemble_records=50,byzantine_existing_image_gaps=0,painting_gaps_researched=20,primary_images_delivered=18,explicit_object_holds=2,all_selected_and_held_accounted_for=True,held_images_requested=0,new_directory_entries=0,nationwide_coverage_complete=False))
 beforeq=w.load(E/'source-queue-before.json');old=next(r for r in beforeq['sources'] if r['source_id']=='getty_museum');cursor=copy.deepcopy(old['resume_cursor'])
 cursor.update(next_offset=100,processed_slugs=list(dict.fromkeys(cursor['processed_slugs']+[r['slug'] for r in discovery['records']])),last_offset=50,last_page_evidence=str((E/'byzantine-discovery-verification.json').relative_to(w.ROOT)))
 cursor['painting_image_gaps']=dict(route='existing_Getty_painting_gaps_with_native_accession_creation_through_1955',after_artwork_id=data['rows'][-1]['id'],inspected_ids=[r['id'] for r in data['rows']],delivered_ids=ids,held_ids=[r['artwork_id'] for r in holds],selection_sha256=receipt['selection_sha256'],hold_evidence=str((E/'specific-hold-verification.json').relative_to(w.ROOT)),skip_unchanged_holds=True,metadata_refresh_due='2026-11-11')
 nxt='Rotate to the undercovered SKD Dresden registry route: audit a bounded page of existing image gaps and current official per-image rights, prioritizing whole Russian/Greek/Byzantine objects where present. If unavailable, use the saved NSW WikiArt pending queue with its official-site hold preserved. Getty later resumes Byzantine offset 100 or painting gaps after '+data['rows'][-1]['id']+'; skip recorded holds and exhausted French reserves.'
 w.save(E/'source-register-final.json',dict(at=now,source_id='getty_museum',provider='J. Paul Getty Museum',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Public native search, object and digital-image metadata HTTP 200; 18 selected native media downloads HTTP 200',last_checked_at=now,actual_rights='18 digital images individually assert CC0 and download clearance; conflicting territorial/zoom-only image remains held',resume_cursor=cursor,remaining_gaps=['Two image cases held with exact evidence; no repeated unchanged requests','Three prior complete-manuscript image/view holds remain unchanged','Byzantine component results require separate physical-object reconciliation; not counted as new works','Later painting UUID pages and broader museum coverage incomplete'],complete_original_registry_rows=111))
 w.save(E/'research-outcomes.json',dict(at=now,discovered_byzantine_leads=50,existing_painting_gaps_researched=20,selected=18,prepared=18,imported=18,independently_verified=18,actually_viewed_individually=18,held=2,verified_counts=counts,prior_campaign_increments_counted=0))
 manifest=E/'delivery-manifest.csv'
 if not manifest.exists():
  with manifest.open('w') as f:
   fields=['artwork_id','native_id','title','source_url','media_id','image_sha256','selection_sha256','rights_label','byte_size'];out=csv.DictWriter(f,fieldnames=fields);out.writeheader()
   images={im['artwork_id']:im for im in i.accepted(w.B)[0]}
   for r in i.selected(w.B)['rows']:
    im=images[r['artwork_id']];out.writerow(dict(artwork_id=r['artwork_id'],native_id=r['native_id'],title=r['title'],source_url=r['source_url'],media_id=im['media_id'],image_sha256=im['sha256'],selection_sha256=receipt['selection_sha256'],rights_label=i.CFG['getty']['license'],byte_size=im['bytes']))
 evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-file-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','independent-campaign-stop-verification.json','independent-prewrite-verification.json','independent-resume-verification.json','actual-visual-review.json','prior-write-reconciliation.json','global-identity-reconciliation-final.json','independent-route-completeness-verification.json','specific-hold-verification.json','byzantine-discovery-verification.json','source-register-final.json','research-outcomes.json','source-access-holds.json','required-input-reconciliation.json','preparation-refinement.json']
 cp=dict(at=now,batch=47,stage='verified_complete',verified_counts=counts,production_ids=ids,selected=18,prepared=18,imported=18,verified=18,holds=2,resume_cursor=cursor,next_task=nxt,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-getty-000047-verify.py replay',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-getty-000047-verify.py verify',evidence_paths=[str((E/name).relative_to(w.ROOT)) for name in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0)
 w.save(E/'CHECKPOINT.json',cp);w.save(w.RUNTIME/'CHECKPOINT.json',cp)
 qp=E.parents[1]/'source-queue.json'
 if not (E/'source-queue-update-verification.json').exists():
  with qp.with_suffix('.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);before=w.load(qp);q=copy.deepcopy(before)
   r=next(r for r in q['sources'] if r['source_id']=='getty_museum')
   checkpoint=str((E/'CHECKPOINT.json').relative_to(w.ROOT))
   if r.get('checkpoint')!=checkpoint:
    priorcounts=r.get('programme_verified_counts',r['verified_counts']);r.setdefault('prior_resume_cursors',[]).append(r.get('resume_cursor'))
    r.update(status='eighteen_existing_painting_gaps_newly_illustrated_verified_two_exact_image_holds',last_checked_at=now,checkpoint=checkpoint,resume_cursor=cursor,latest_batch_verified_counts=counts,verified_counts=counts,programme_verified_counts={k:priorcounts[k]+counts[k] for k in counts},policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Native object/search/digital-media metadata and 18 selected images HTTP 200',remaining_gaps=w.load(E/'source-register-final.json')['remaining_gaps'])
    r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str((E/name).relative_to(w.ROOT)) for name in evidence]+[checkpoint]))
    tmp=qp.with_suffix('.47.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
   live=w.load(qp);assert len(live['sources'])==111
   before_other={r['source_id']:r for r in before['sources'] if r['source_id']!='getty_museum'};after_other={r['source_id']:r for r in live['sources'] if r['source_id']!='getty_museum'};assert before_other==after_other
   assert all(before[k]==live[k] for k in before if k!='sources')
   w.save(E/'source-queue-update-verification.json',dict(at=h.now(),updated_sources=['getty_museum'],unrelated_entries_unchanged=110,registry_count=111,top_level_metadata_preserved=True,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor,replay_safe=True))
 master=w.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==47
 started=datetime.datetime.fromisoformat(master['inflight']['started_at']);ended=datetime.datetime.fromisoformat(now)
 cumulative={k:master['totals'][k]+counts[k] for k in counts}
 w.save(E/'milestone-report.json',dict(at=now,batch=47,batch_started_at=started.isoformat(),batch_verified_at=now,batch_elapsed_seconds=(ended-started).total_seconds(),programme_started_at=master['started_at'],programme_elapsed_hours=(ended-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600,prior_supervisor_verified_counts=master['totals'],verified_batch_increment=counts,programme_counts_after_this_batch=cumulative,continuous_execution_owner='Existing external supervisor; not created, edited or relaunched by this worker',new_spending_budget_created=False,failures=['Initial strict main-view wording and single citation-field selector corrected from captured evidence before production; initial staging preserved','Web-tool search fetch unavailable; documented official HTTP search route succeeded'],unresolved_cases=holds,next_task=nxt,one_hundred_hours_is_not_a_stop=True))
 allfiles=evidence+['CHECKPOINT.json','source-queue-update-verification.json','milestone-report.json','delivery-manifest.csv']
 checks=[dict(path=str((E/name).relative_to(w.ROOT)),sha256=h.sha((E/name).read_bytes()),bytes=(E/name).stat().st_size) for name in allfiles]
 assert w.load(E/'CHECKPOINT.json')==w.load(w.RUNTIME/'CHECKPOINT.json')
 w.save(E/'final-checkpoint-verification.json',dict(at=h.now(),verified_counts=counts,evidence_files=checks,runtime_checkpoint_equal=True,queue_source_count=111,unrelated_queue_entries_preserved=110,external_supervisor_unchanged=True,next_task=nxt))
 print(json.dumps(dict(verified_counts=counts,next_task=nxt),ensure_ascii=False))
