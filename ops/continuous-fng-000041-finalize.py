#!/usr/bin/env python3
"""Verify replay, preserve route cursors and leave the external supervisor a durable result."""
import copy, datetime, fcntl, importlib.util, json, os, subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-fng-images-000041.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
E=b.E;h=b.h;i=b.i;ROOT=b.ROOT;load=b.load;save=b.save
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
receipt=load(E/'batch-verification-receipt.json');ids=receipt['production_ids'];counts=receipt['verified_counts']
assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=27,alternate_images=0,museum_links=0)
pin=receipt['selection_sha256'];assert pin==h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())
if not (E/'independent-resume-verification.json').exists():
 with b.connect() as db:
  before=h.snapshot(db,ids)
  owned=[dict(r) for r in db.execute('SELECT media_id::text,source_checksum,evidence_json FROM media_rights_evidence WHERE adapter_version=%s ORDER BY media_id',(i.OP,))]
  assert len(owned)==27
  for r in owned:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert ev['selection_sha256']==pin
 applied={str(p):h.sha(p.read_bytes()) for p in (i.folder(b.B)/'applied').glob('*.json')}
 uploads={str(p):h.sha(p.read_bytes()) for p in (i.folder(b.B)/'uploads').glob('*.json')}
 save(E/'resume-production-target.json',b.target())
 b.deliver()
 with b.connect() as db:
  after=h.snapshot(db,ids);assert before==after
  again=[dict(r) for r in db.execute('SELECT media_id::text,source_checksum,evidence_json FROM media_rights_evidence WHERE adapter_version=%s ORDER BY media_id',(i.OP,))];assert again==owned
  events=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[before[aid]['artwork']['primary_media_id'] for aid in ids])).fetchone()['n'];assert events==27
 assert applied=={str(p):h.sha(p.read_bytes()) for p in (i.folder(b.B)/'applied').glob('*.json')}
 assert uploads=={str(p):h.sha(p.read_bytes()) for p in (i.folder(b.B)/'uploads').glob('*.json')}
 save(E/'independent-resume-verification.json',dict(at=h.now(),method='Reinvoke completed bounded delivery, then independently compare fresh production snapshots, owned source/plan evidence and audit counts.',production_ids=ids,owned_rights_rows=27,owned_transition_audit_rows=events,selection_sha256=pin,before_after_identical=True,upload_receipts_unchanged=True,applied_receipts_unchanged=True,additional_primary_images=0,additional_artworks=0,additional_attachments=0))

oldcp=load(b.OLD/'CHECKPOINT.json');oldroute=oldcp['resume'];priorstates=load(b.OLD/'preparation-production-snapshot.json.gz')['before'];held=oldroute['held_ids']
with b.connect() as db:
 heldnow=h.snapshot(db,held)
 assert all(heldnow[aid]==priorstates[aid] for aid in held)
save(E/'prior-held-objects-preservation-verification.json',dict(at=h.now(),ids=held,held_count=33,live_state_unchanged=True,metadata_and_images_not_modified=True,prior_reconciliation='docs/research/continuous-production-20261011/batches/000038/research-holds.json'))

next_task='Research a bounded WikiArt image-matching pass for the 35 existing NSW gaps saved in batch 41, beginning with documented Charles Conder works. Use exact creator, date, inventory/version and composition evidence; reconcile global duplicates before attachment. Keep the official NSW museum route access/permission hold, 17 Warsaw pending icon leads, 33 Sinebrychoff holds and Ateneum cursor. Do not replay delivered French reserves or completed image campaigns.'
evidence_names=['batch-verification-receipt.json','independent-source-verification.json','independent-file-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','global-identity-reconciliation.json','pending-live-reconciliation.json','prior-batch-attribution-verification.json','prior-held-objects-preservation-verification.json','independent-campaign-stop-verification.json','nsw-route-verification.json','courtauld-discovery-verification.json','source-register.json','source-access-holds.json','metadata-and-mime-reuse-verification.json','preparation-failure-correction.json']
evidence=[str((E/n).relative_to(ROOT)) for n in evidence_names];assert all((ROOT/p).exists() for p in evidence)
route=copy.deepcopy(oldroute)
route['delivered_ids']=list(dict.fromkeys(route['delivered_ids']+ids))
route['pending_artwork_ids']=[aid for aid in route['pending_artwork_ids'] if aid not in ids]
delivered_native=[r['native_id'] for r in i.selected(b.B)['rows']]
route['pending_native_ids']=[oid for oid in route['pending_native_ids'] if oid not in delivered_native]
route['latest_delivered_native_ids']=delivered_native
route['latest_batch']=41;route['latest_verified_counts']=counts
route['programme_sinebrychoff_newly_illustrated']=47
route['retry_semantics']='All 27 pending candidates independently verified in batch 41; batch 38 delivered 20. Do not replay them as new. Preserve 33 unchanged source/date holds. Resume future distinct Sinebrychoff gaps strictly after after_artwork_id; keep metadata refresh date and FNG JPEG MIME validation.'
assert len(route['delivered_ids'])==47 and not route['pending_artwork_ids'] and not route['pending_native_ids']

qpath=E.parents[1]/'source-queue.json'
with (b.RUNTIME/'queue-update.lock').open('a+') as qlock:
 fcntl.flock(qlock,fcntl.LOCK_EX)
 current=load(qpath);beforeq=copy.deepcopy(current)
 oldmap={x['source_id']:copy.deepcopy(x) for x in current['sources']}
 for x in current['sources']:
  sid=x['source_id']
  if sid=='finnish_national_gallery':
   x['status']='forty_seven_sinebrychoff_primary_images_verified_pending_27_completed_33_holds_preserved'
   x['continuation_routes']['sinebrychoff']=route
   x['remaining_gaps']=[g for g in x['remaining_gaps'] if not g.startswith('Sinebrychoff:')]+['Sinebrychoff: all 47 eligible objects in the first 80-record slice now illustrated; 33 unchanged source/date/photo-path cases held. More gaps may follow 65ebef83-4813-4528-a282-d3a505a0a243; museum coverage incomplete.']
   x['verified_counts']=counts;x['latest_batch_verified_counts']=counts
   x['policy_reference']='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy'
   x['access_status']='Saved official anonymous source export checksum verified; 27 selected exact preferred CC0 photographs HTTP 200; source capture 2026-10-10 retained.'
   add=evidence
  elif sid=='art_gallery_nsw':
   x['status']='official_object_route_web_robots_hold_image_permission_unresolved_wikiart_crossmatch_pending'
   x['resume_cursor']=dict(route='wikiart_exact_matches_to_existing_nsw_gaps',input_path=str((E/'nsw-bounded-gap-input.json').relative_to(ROOT)),selected_production_gap_ids=[r['id'] for r in load(E/'nsw-bounded-gap-input.json')['rows']],position=0,official_object_pages_processed=0,official_museum_route_access_held=True,images_downloaded=0,do_not_repeat_unchanged_official_access_hold=True)
   x['policy_reference']='Registry art_gallery_nsw; docs/ARTLINE_IMAGE_USE.md general policy. Separate WikiArt provider uses explicit 6 October approval.'
   x['access_status']='Web tool reports non-retryable robots restriction on official museum domain; image-system terms require publication permission.'
   x['remaining_gaps']=['35 scoped existing image gaps saved, source identities not yet matched. No museum image rights generalized and no objects or holdings added.','Indigenous cultural notices must be preserved for any later eligible museum-source records.']
   add=[str((E/n).relative_to(ROOT)) for n in ['nsw-route-verification.json','nsw-bounded-gap-input.json','source-register.json']]
  elif sid=='courtauld_gallery':
   x['status']='terms_discovery_web_tool_unavailable_no_object_requests'
   x['access_status']='Only registry terms URL checked via web tool and returned inaccessible. Museum-wide access status unestablished; no object/image requests.'
   x['resume_cursor']=dict(route='terms_and_rights_reconciliation',url='https://gallerycollections.courtauld.ac.uk/terms',object_cursor=None,object_requests=0,image_downloads=0,scope='discovery_only')
   x['remaining_gaps']=['Resolve accessible current official reuse terms before image selection; IIIF availability alone is not permission.']
   add=[str((E/'courtauld-discovery-verification.json').relative_to(ROOT))]
  else:continue
  x['checkpoint']=str((E/'CHECKPOINT.json').relative_to(ROOT));x['last_checked_at']=h.now()
  x['evidence_paths']=list(dict.fromkeys(x['evidence_paths']+add))
 changed={'finnish_national_gallery','art_gallery_nsw','courtauld_gallery'}
 assert all(x==oldmap[x['source_id']] for x in current['sources'] if x['source_id'] not in changed)
 fng=next(x for x in current['sources'] if x['source_id']=='finnish_national_gallery')
 assert fng['resume_cursor']==oldmap['finnish_national_gallery']['resume_cursor'],'Ateneum cursor must remain untouched'
 assert len(current['sources'])==111
 payload=json.dumps(current,ensure_ascii=False,indent=2).encode()+b'\n'
 temporary=qpath.with_suffix('.batch41.tmp');temporary.write_bytes(payload);os.replace(temporary,qpath)
 save(E/'source-queue-update-verification.json',dict(at=h.now(),changed_routes=sorted(changed),unchanged_other_entries=108,before_sha256=h.sha(json.dumps(beforeq,sort_keys=True).encode()),after_sha256=h.sha(qpath.read_bytes()),ateneum_cursor_unchanged=True,warsaw_queue_unchanged=True,exact_delivered_ids=ids,pending_sinebrychoff_candidates=0,next_keyset_after=route['after_artwork_id']))

master=load(E.parents[1]/'CHECKPOINT.json');started=master['inflight']['started_at'];now=h.now()
elapsed=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(started)).total_seconds()
programme_elapsed=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()
totals={k:master['totals'][k]+counts[k] for k in counts}
save(E/'milestone-report.json',dict(at=now,started_at=started,measured_batch_elapsed_seconds=elapsed,measured_programme_elapsed_seconds=programme_elapsed,current_batch_verified=counts,previous_supervisor_totals=master['totals'],cumulative_through_this_batch=totals,cumulative_basis='External supervisor persisted totals plus independently verified current increment. Earlier complete programme not reaudited in this batch; batch 40 six images and batch 38 twenty images freshly reconciled and excluded from increment.',failures=[dict(type='local_dependency',detail='System Python missing psycopg; established /tmp/artline-cesi-venv reused without installing packages'),dict(type='read_only_query',detail='Incorrect FNG citation host produced zero candidates; assertion stopped work, failed receipt preserved, exact persisted host corrected once')],holds='NSW official route access and permission unresolved; Courtauld terms web tool unavailable; 33 prior Sinebrychoff source/date holds retained.',next_task=next_task,paid_services_or_budget_changes=0,stop_at_100_hours=False,external_supervisor_unchanged=True))
checkpoint=dict(at=now,batch=41,stage='independently_verified_complete',campaign=i.OP,started_at=started,measured_batch_elapsed_seconds=elapsed,verified_counts=counts,production_ids=ids,discovered_existing_gaps=dict(nsw_inventory_only=35,sinebrychoff_pending_reconciled=27),selected=27,prepared=27,individually_viewed=27,imported=27,verified=27,alternate_images=0,prior_delivered_excluded=dict(previous_batch=6,sinebrychoff_batch38=20),source_resume=route,next_task=next_task,selection_sha256=pin,visual_review_sha256=receipt['visual_review_sha256'],evidence_paths=evidence+ [str((E/n).relative_to(ROOT)) for n in ['source-queue-update-verification.json','milestone-report.json']],resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-fng-images-000041.py deliver',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-fng-images-000041-verify.py',resume_effect='Verified no changes on replay.',local_catalogue_connections=0,external_supervisor_unchanged=True)
save(E/'CHECKPOINT.json',checkpoint);save(b.RUNTIME/'CHECKPOINT.json',checkpoint)
save(b.RUNTIME/'verified-batch-result.json',dict(outcome='progress',summary='27 existing Sinebrychoff artworks gained individually viewed, independently verified CC0 primary images. Replay added nothing. NSW route hold and all unrelated queues preserved; local catalogue untouched.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((E/n).relative_to(ROOT)) for n in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','source-queue-update-verification.json','CHECKPOINT.json']]))
verification=[]
for p in evidence+[str((E/n).relative_to(ROOT)) for n in ['CHECKPOINT.json','source-queue-update-verification.json','milestone-report.json']]:
 path=ROOT/p;assert path.exists();verification.append(dict(path=p,sha256=h.sha(path.read_bytes()),bytes=path.stat().st_size))
assert load(E/'CHECKPOINT.json')==load(b.RUNTIME/'CHECKPOINT.json')
save(E/'final-checkpoint-verification.json',dict(at=h.now(),evidence_files=verification,runtime_checkpoint=str(b.RUNTIME/'CHECKPOINT.json'),runtime_checkpoint_matches=True,verified_counts=counts,source_queue_has_111_sources=True,external_supervisor_state_not_edited=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,cumulative=totals)))
