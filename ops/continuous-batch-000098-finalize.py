"""Persist batch 98 evidence and only actually researched source cursors."""
import copy,datetime,fcntl,gzip,importlib.util,json,os
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-khm-images-000098.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;W=b.E;E=W.parent;Q=E.parents[1]/'source-queue.json';R=b.R.parent

def save(name,v):
 p=E/name
 if not p.exists():h.save(p,v)
 return h.load(p)
def rel(p):return str(p.relative_to(b.ROOT))
with (R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'CHECKPOINT.json').exists():print('Completed checkpoint retained; verify saved production before replay.');raise SystemExit(0)
 receipt=h.load(W/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=2,alternate_images=0,museum_links=0)
 resume=h.load(W/'independent-resume-verification.json');assert all(v==0 for v in resume['replay_increments'].values())
 ids=receipt['production_ids'];initial=h.load(W/'gap-input.json.gz');auckland=h.load(E/'independent-auckland-discovery-verification.json');assert len(auckland['rows'])==25
 with b.connect() as db:
  assert h.snapshot(db,ids)==h.load(W/'independent-production-verification.json')['after']
  ainput=h.load(E/'gap-input.json.gz');assert h.snapshot(db,list(ainput['before']))==ainput['before']
  recovery=h.load(i.BACKUP/'affected-row-recovery-before.json.gz');museum=db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,)).fetchone()['v'];assert museum==recovery['institutions'][0]
 save('independent-existing-preservation-verification.json',dict(at=h.now(),auckland_gap_records_unchanged=25,khm_non_delivered_records_unchanged=9,khm_institution_unchanged=True,metadata_holdings_creators_and_status_preserved=True,local_database_connections=0))
 reasons={
 '0b8b6cc0-60d4-5e3e-9236-5c035d2a661e':'Exact sitter and accession match, but prepared source proportions differ from museum physical dimensions by about 5.8 percent; held after actual visual review for full-frame comparison. Catalogue 1628, WikiArt 1630 and official around 1632 retained.',
 '0e0e6d9a-9372-5f94-8566-a7a7f11f8684':'No Jan Wildens match in captured Van Dyck index; title explicitly identifies a lost work. No substitute.',
 '14e4c2d0-0ee1-56a8-9888-c9d79cf8dd72':'Already illustrated candidate 6157c704-e485-5b60-8846-e18c61ee63fb, Young Woman in a Blue Dress, with Fan, requires duplicate reconciliation; no attachment or record deletion.',
 '20e8ab18-12ec-56bc-acbe-00d6cfc11d79':'No exact Jan van Montfort match in captured Van Dyck index.',
 '29141c41-42f4-56d2-b021-32f8008e28f6':'WikiArt St Sebastian 1558 is a 270 x 130 cm fresco, not this Vienna 1565 painting; different version already illustrated under b1cdd9c0-e2ec-5767-8f02-732bbc8b76f6.',
 '29efded2-28b0-557b-8ff5-18fc32d6f276':'No exact Francesco Filetto title in captured Titian index; translated/generic portrait aliases require further evidence.',
 '2a39702d-bc7c-50d6-8092-820f0c5aa2af':'Isabella Brant and Isabella van Assche in the index are different sitters; no exact widow Isabella Clara Eugenia match.',
 '3409b833-c362-58eb-8b8d-44ae156cda3d':'Already illustrated candidate ae09e00a-8c22-5798-9f07-5afd30ca28a7, Portrait of a Young Woman (Laura), requires duplicate reconciliation; no extra image or record deletion.',
 '40822a83-a772-5ead-a1e2-95e43b1a0dd4':'No exact named three-saints composition in captured Titian index; no generic Madonna substituted.'}
 profiles={'Anthony van Dyck':'anthony-van-dyck','Lucas Cranach the Elder':'lucas-cranach-the-elder','Palma Vecchio':'palma-vecchio','Paolo Veronese':'paolo-veronese','Titian':'titian','Giorgione':'giorgione'}
 dispositions=[]
 for a in initial['rows']:
  index=h.load(W/'indexes'/(profiles[a['creator']]+'.json'));rc=index['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
  dispositions.append(dict(artwork_id=a['id'],title=a['title'],creator=a['creator'],source_index_receipt=rc,index_entries=len(index['entries']),outcome='verified_new_primary_image' if a['id'] in ids else 'held_unresolved',reason='Exact physical object, reviewed full supplied composition and current rights evidence; production/storage/public delivery independently verified.' if a['id'] in ids else reasons[a['id']]))
 save('independent-khm-discovery-verification.json',dict(at=h.now(),rows=dispositions,researched=11,selected=3,prepared=3,actually_viewed=3,accepted=2,imported=2,verified=2,source_capture_hashes_verified=True,unresearched_previous_pending=24,no_whole_catalogue_coverage_claim=True))
 save('research-holds.json',dict(at=h.now(),auckland=auckland['rows'],khm=[r for r in dispositions if r['artwork_id'] not in ids],native_auckland_route_status='Historical HTTP404; no source-wide permission/authentication claim.',prior_holds_preserved=True))
 native_failures=[h.load(p) for p in (W/'source-captures').glob('*.json') if h.load(p)['status']!=200]
 save('failure-ledger.json',dict(at=h.now(),auckland_profile_http404=auckland['profile_404s'],khm_metadata_failures=native_failures,khm_resolution='Old indexed /st-jerome-526-1 returned 404; current /st-jerome-526 returned 200. No repeated request to failed URL. No provider authentication restriction encountered.',metadata_missing_not_provider_wide_holds=True,production_write_failures=0,storage_failures=0,local_recovered_errors=[dict(error='System Python lacked bs4 during one read-only summary attempt',resolution='Used established artline-cyprus virtualenv; no production effects')],spending_budget_changes=0,cloud_backups_created=0))
 programme=h.load(E.parents[1]/'CHECKPOINT.json');assert programme['inflight']['batch']==98;start=programme['inflight']['started_at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 save('batch-verification-receipt.json',dict(receipt,batch=98,started_at=start,finished_at=end,measured_runtime_seconds=elapsed,source_verification_receipt=rel(W/'batch-verification-receipt.json'),auckland_verified=0,prior_campaign_additions_excluded=True))
 next_task='Research a bounded existing-primary-image-gap cohort at undercovered MNAC Barcelona using object-level open rights or approved WikiArt. Preserve Auckland unresolved matches and failed-profile URLs, Lanier full-frame hold, 24 untouched KHM IDs and Warsaw page 12. Do not restart completed campaigns or rescan the exhausted French reserve.'
 with (Q.parent/'source-queue.worker.lock').open('a+') as l1,(Q.parent/'source-queue.lock').open('a+') as l2:
  fcntl.flock(l1,fcntl.LOCK_EX);fcntl.flock(l2,fcntl.LOCK_EX)
  before=h.load(Q);save('source-queue-immediately-before-update.json',before);after=copy.deepcopy(before);touched={'auckland_art_gallery','khm_vienna'}
  for row in after['sources']:
   sid=row['source_id']
   if sid not in touched:continue
   cur=row['resume_cursor'];oldcur=copy.deepcopy(cur);row.setdefault('prior_resume_cursors',[]).append(oldcur)
   ds=auckland['rows'] if sid=='auckland_art_gallery' else dispositions;checked=[x['artwork_id'] for x in ds];verified=[] if sid=='auckland_art_gallery' else ids;vc={k:0 for k in counts} if sid=='auckland_art_gallery' else counts
   refs=[rel(E/('independent-auckland-discovery-verification.json' if sid=='auckland_art_gallery' else 'independent-khm-discovery-verification.json'))]
   if sid=='khm_vienna':refs += [rel(W/p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json']]
   row.update(last_checked_at=end,last_batch=98,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts=vc)
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs));row.setdefault('research_history',[]).append(dict(batch=98,at=end,evidence=refs,verified_counts=vc))
   cur['researched_artwork_ids']=list(dict.fromkeys(cur.get('researched_artwork_ids',[])+checked));cur['pending_artwork_ids']=[aid for aid in cur['pending_artwork_ids'] if aid not in checked];cur['verified_artwork_ids']=list(dict.fromkeys(cur.get('verified_artwork_ids',[])+verified));cur['discovery_evidence']=refs[0]
   cur['held_artwork_ids']=list(dict.fromkeys(cur.get('held_artwork_ids',[])+[aid for aid in checked if aid not in verified]));cur['hold_ledger']=rel(E/'research-holds.json')
   if sid=='auckland_art_gallery':
    assert not cur['pending_artwork_ids'] and len(cur['researched_artwork_ids'])==40
    cur['after_artwork_id']=cur['next_keyset_after_frozen_input'];cur['profile_404_no_unchanged_retry']=list(dict.fromkeys(cur['profile_404_no_unchanged_retry']+[r['receipt']['url'] for r in auckland['rows'] if r['receipt']['status']==404]));cur['next_step']='Frozen 40-record input researched with limited profile/title coverage; do not repeat unchanged 404s or ambiguous images. Rotate source, then keyset after saved UUID using new evidence.'
    row['status']='frozen_40_gaps_researched_no_secure_wikiart_matches';row['access_status']='Three new artist indexes HTTP200, 22 profile HTTP404; two ambiguous object pages HTTP200. No Auckland native/image requests; historical route HTTP404 is not a provider-wide authentication hold.'
    row['remaining_gaps']=['All 40 frozen records remain unresolved; failed guessed profiles do not establish absence elsewhere.','Current batch Amigoni version and Bratby sitter/date mismatches explicitly held.','Further institutional keyset pages and broad collection coverage remain incomplete.']
   else:
    assert len(cur['pending_artwork_ids'])==24
    cur['next_step']='24 untouched frozen UUIDs remain. Reuse six captured creator indexes for later rows; do not retry prior failed profiles or unresolved duplicate/Lanier holds without new evidence.';cur['selection_sha256']=receipt['selection_sha256'];cur['verified_evidence']=rel(W/'independent-production-verification.json')
    row['status']='two_existing_primary_gaps_verified_wikiart_24_frozen_ids_untouched';row['programme_verified_counts']=counts;row['programme_count_evidence']=rel(W/'batch-verification-receipt.json')
    row['access_status']='Six WikiArt creator indexes and five object pages HTTP200; three exact official KHM metadata pages HTTP200. One old object URL HTTP404 corrected to current route. Three WikiArt images prepared/viewed; two verified primary attachments, one full-frame hold. Native museum image permissions not generalized.'
    row['remaining_gaps']=['24 untouched frozen image gaps; nine researched current-batch holds plus five earlier unresolved records.','Lanier requires full-frame comparison; Palma and Giorgione duplicate candidates remain unmerged.','Museum image terms require separate permission; this delivery uses WikiArt approval only.']
  assert len(after['sources'])==111 and [r for r in before['sources'] if r['source_id'] not in touched]==[r for r in after['sources'] if r['source_id'] not in touched]
  tmp=Q.with_suffix('.batch98.tmp')
  with tmp.open('wb') as f:f.write(json.dumps(after,ensure_ascii=False,indent=2).encode());f.flush();os.fsync(f.fileno())
  os.replace(tmp,Q);assert h.load(Q)==after
  save('source-queue-after.json',after);save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(touched),unrelated_routes_preserved=109,original_registry_routes=111,exact_unrelated_structures_equal=True,atomic_replace=True,queue_sha256=h.sha(Q.read_bytes())))
 save('source-register-final.json',dict(at=end,original_registry_rows=111,registry_sha256=h.load(E/'required-input-reconciliation.json')['registry_sha256'],researched_routes=[r for r in after['sources'] if r['source_id'] in touched],policy_reference='Original 111-source registry plus current docs/ARTLINE_IMAGE_USE.md WikiArt approval',directory_coverage_changed=False,object_coverage_complete=False))
 evidence=[rel(E/p) for p in ['batch-verification-receipt.json','independent-auckland-discovery-verification.json','independent-khm-discovery-verification.json','independent-existing-preservation-verification.json','research-holds.json','failure-ledger.json','external-continuation-verification.json','independent-queue-verification.json','source-register-final.json']]+[rel(W/p) for p in ['independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json']]
 assert all((b.ROOT/p).is_file() for p in evidence)
 checkpoint=dict(batch=98,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=ids,image_selection_sha256=receipt['selection_sha256'],stage_counts=dict(auckland_researched=25,khm_researched=11,selected=3,prepared=3,actually_viewed=3,accepted=2,imported=2,verified=2),next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-khm-000098-verify.py',evidence_paths=evidence,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,local_catalogue_connections=0,limitations=receipt['limitations'])
 save('CHECKPOINT.json',checkpoint);h.save(R/'CHECKPOINT.json',checkpoint)
 save('batch-summary.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,prior_programme_totals=programme['totals'],recorded_cumulative_after_batch={k:programme['totals'][k]+counts[k] for k in counts},prior_totals_source='Supervisor checkpoint inherited; not independently re-audited as whole-catalogue totals.',next_task=next_task,reporting_owner='External supervisor owns hourly and 100-hour reports; no schedule edited.'))
 final=dict(outcome='progress',summary='Verified two authentic primary images on existing Vienna paintings. All three prepared images visually reviewed; Lanier held for possible crop. Auckland’s 25 pending gaps researched with no secure matches. Public delivery and duplicate-free replay verified; 109 unrelated source routes preserved.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/'batch-verification-receipt.json'),rel(E/'independent-auckland-discovery-verification.json'),rel(W/'independent-production-verification.json'),rel(W/'independent-public-verification.json'),rel(W/'actual-visual-review.json'),rel(W/'independent-resume-verification.json'),rel(E/'independent-queue-verification.json'),rel(E/'CHECKPOINT.json')])
 save('worker-result.json',final);print(json.dumps(final))
