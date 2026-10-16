#!/usr/bin/env python3
"""Persist one verified batch; change only researched source routes."""
import copy,datetime,fcntl,importlib.util,json,os,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('b84',Path(__file__).with_name('continuous-greek-batch-000084.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
final=b.E/'final-checkpoint-verification.json'
if final.exists():
 for x in h.load(final)['files']:assert h.sha((b.ROOT/x['path']).read_bytes())==x['sha256']
 print('Immutable completed evidence verified; no queue mutation.');sys.exit(0)
receipt=h.load(b.E/'batch-verification-receipt.json');replay=h.load(b.E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
p,pin=h.pinned(b.PHASE);counts=receipt['verified_counts'];at=h.now();assert counts==dict(new_painters=0,new_artworks=4,newly_illustrated=3,alternate_images=0,museum_links=4)
checks=h.load(b.E/'parthenis-global-identity-reconciliation.json')['records'];assert len(checks)==24 and sum(bool(x['existing']) for x in checks)==5
review=h.load(b.E/'editorial-selection-review.json');initial=h.load(b.E/'source-queue-before.json');old=next(x for x in initial['sources'] if x['source_id']=='national_gallery_athens');cursor=copy.deepcopy(old['resume_cursor'])
cursor.update(processed_page=2,next_page=3,documented_next_request=dict(method='POST',url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php',form=dict(artist_id='91',lang='en',page=3,action='get_artist_artworks'),evidence=str((b.E/'parthenis-page2-capture.json').relative_to(b.ROOT)),executed=False),parthenis_notices_reviewed=old['resume_cursor']['parthenis_notices_reviewed']+24,processed_urls=list(dict.fromkeys(cursor['processed_urls']+[x['url'] for x in checks])),verified_source_ids=list(dict.fromkeys(cursor['verified_source_ids']+review['selected'])),verified_artwork_ids=list(dict.fromkeys(cursor['verified_artwork_ids']+receipt['production_ids'])))
cursor['held_versions'].update({k.removeprefix('athens/'):v for k,v in review['held_versions'].items()});cursor['held_date_source_ids']=list(dict.fromkeys(cursor['held_date_source_ids']+['angel']))
cursor['image_date_holds']=[dict(source_id='aphrodite',date_display='1950 - 1960',reason='Museum image approval requires creation through 1955; metadata through 1970 is eligible.',artwork_id=next(r['artwork_id'] for r in p['records'] if r['source_id']=='aphrodite'))]
cursor['do_not_repeat_unchanged_holds']=True;cursor['next_step']='Rotate institutions. Resume native artist 91 page 3 after rotation, skipping processed URLs; resolve saved existing/title/version/panel holds separately.'
next_task='Research the National Gallery London documented metadata API after reconciling source-access holds. Preserve Athens page 3, Scotland HTTP 403, and all Thyssen, SHUZO, Warsaw and French-reserve cursors.'
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 heldids=[h.uid('artwork/athens/'+x['record']['source_id']) for x in p['held']];assert not h.snapshot(db,heldids)
 notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s",(b.FIELD,))];assert len(notes)==4 and all(x['pin']==pin for x in notes)
 assert len([x for x in h.snapshot(db,receipt['production_ids']).values() if x['artwork']['primary_media_id']])==3
b.save('independent-held-and-attribution-verification.json',dict(at=at,held_proposed_artwork_ids_absent=heldids,own_plan_citations=notes,metadata_plan_sha256=pin,only_own_four_objects_counted=True,prior_campaigns_excluded=True))
registry=h.load(b.E/'registry-verification.json')
b.save('source-register-final.json',dict(at=at,registry_path=registry['path'],registry_sha256=registry['sha256'],registry_rows=111,researched=[dict(registry_entry=next(x for x in registry['selected'] if x['source_id']=='national_gallery_athens'),policy_reference='docs/ARTLINE_IMAGE_USE.md: Nationwide Greek museum delivery / Greek source extension; through-1955 images',access_status='One documented public index request, 24 exact object notices and three selected image requests HTTP 200',last_checked_at=at,discovered=24,selected=4,prepared_images=3,imported_artworks=4,verified_artworks=4,verified_primary_images=3,existing_objects_excluded=5,identity_and_unit_holds=14,open_date_holds=1,remaining_gaps='Pages 3–5 unreviewed; unresolved physical versions and translated titles remain; Aphrodite image not selected due 1950–1960 source date.',resume_cursor=cursor),dict(registry_entry=next(x for x in registry['selected'] if x['source_id']=='national_galleries_scotland'),policy_reference='Original registry; recorded provider holds',access_status='Historical HTTP 403 retained without retry; native image rights also require review',last_checked_at=at,check_kind='saved_ledger_reconciliation_only',new_native_requests=0,evidence='source-access-holds.json',remaining_gaps='No new exact object research; provider hold unchanged.')],directory_coverage_changes=0,whole_institution_coverage_complete=False,new_painters=0,creator_reconciliation='Existing global Konstantinos Parthenis identity reused; source birth-date ambiguity retained as source wording, no biography edits.'))
b.save('failures-and-resolutions.json',dict(at=at,production_failures=[],source_request_failures=[],research_interlocks=[dict(action='Global Aphrodite title reconciliation',finding='Two unlinked title candidates stopped plan preparation.',resolution='Verified one ancient terracotta and one 1929 Geraldine Owen print; distinct creators/materials/dates/inventories preserved. Plan then prepared.',evidence='aphrodite-global-collision-review.json'),dict(action='Image preparation immediately following held planning step',finding='No pinned plan existed; preparation stopped before image requests.',resolution='Completed identity review and pinned plan, then prepared only three selected images.')],unresolved=review))
changed={'national_gallery_athens','national_galleries_scotland'}
paths=[str((b.E/name).relative_to(b.ROOT)) for name in ['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-existing-preservation-verification.json','independent-resume-verification.json','independent-held-and-attribution-verification.json','actual-visual-review.json','actual-existing-composition-review.json','source-register-final.json','source-access-holds.json','prior-batch-live-reconciliation.json','local-recovery-verification.json','external-continuation-verification.json','failures-and-resolutions.json']]
queue_path=b.E.parent.parent/'source-queue.json'
with (b.R/'source-queue-update.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);before_bytes=queue_path.read_bytes();q=json.loads(before_bytes);before=copy.deepcopy(q);assert len(q['sources'])==111
 for row in q['sources']:
  if row['source_id']=='national_gallery_athens':
   row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']));row.setdefault('verified_count_history',[]).append(dict(checkpoint=row.get('checkpoint'),verified_counts=row.get('verified_counts'),scope='Prior batch counts retained, not re-counted'))
   row.update(status='page2_four_new_parthenis_works_four_holdings_three_primary_images_verified',last_batch=84,last_checked_at=at,access_status='24 page-2 notices and three selected images HTTP 200',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=cursor,verified_counts=counts,latest_batch_verified_counts=counts)
   row.setdefault('research_history',[]).append(dict(batch=84,at=at,evidence_path=str((b.E/'source-register-final.json').relative_to(b.ROOT)),discovered=24,verified_counts=counts,existing_excluded=5,identity_holds=14,date_holds=1))
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+paths+[str((b.E/'CHECKPOINT.json').relative_to(b.ROOT))]))
   row['remaining_gaps']=list(dict.fromkeys(row.get('remaining_gaps',[])+['Parthenis pages 3–5 unreviewed; this pass retains 14 title/version/panel holds, one open-date hold and Aphrodite image cutoff hold.']))
  elif row['source_id']=='national_galleries_scotland':
   if row.get('resume_cursor'):row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']))
   row.update(status='historical_native_http403_hold_reconciled_no_new_requests',last_batch=84,last_checked_at=at,access_status='Native HTTP 403 recorded earlier; no retry in batch 84',policy_reference='Original 111-source registry; source-access-holds.json',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)))
   row['resume_cursor']=dict(route='official_native_catalogue',retry_allowed=False,external_state_change_required='Documented provider access change before native requests',hold_evidence=str((b.E/'source-access-holds.json').relative_to(b.ROOT)),next_step='Rotate to another available registry source; independent approved image sources can be considered only with exact object evidence.')
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+[str((b.E/'source-access-holds.json').relative_to(b.ROOT)),str((b.E/'source-register-final.json').relative_to(b.ROOT))]));row['latest_batch_verified_counts']={k:0 for k in counts}
 unrelated_before={x['source_id']:x for x in before['sources'] if x['source_id'] not in changed};assert len(unrelated_before)==109
 assert {x['source_id']:x for x in q['sources'] if x['source_id'] not in changed}==unrelated_before
 assert {x['source_id']:x for x in initial['sources'] if x['source_id'] not in changed}==unrelated_before
 tmp=queue_path.with_name('source-queue.batch-000084.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');assert queue_path.read_bytes()==before_bytes;os.replace(tmp,queue_path)
 actual=h.load(queue_path);assert {x['source_id']:x for x in actual['sources'] if x['source_id'] not in changed}==unrelated_before
b.save('source-queue-update-verification.json',dict(at=at,before_sha256=h.sha(before_bytes),after_sha256=h.sha(queue_path.read_bytes()),entries=111,changed_source_ids=sorted(changed),unrelated_entries_preserved=109,unchanged_since_batch_start=True,prior_athens_cursor_retained=True,all_other_recovery_cursors_preserved=True))
paths.append(str((b.E/'source-queue-update-verification.json').relative_to(b.ROOT)))
parent=h.load(b.E.parent.parent/'CHECKPOINT.json');assert parent['inflight']['batch']==84
start=parent['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds();runtime=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(parent['started_at'])).total_seconds()
limitations=['Fourteen uncertain title/version/panel records and one open date remain held.','Aphrodite dated 1950–1960 has metadata and holding only; no image was requested.','Three new derivatives individually viewed, 44 existing images viewed in contact sheets; original files only technically decoded.','Recovery archive is full schema plus affected rows and preimages, not a full database dump.','Museum rights remain restricted; user source approval is separate from copyright-holder permission.']
cp=dict(at=at,batch=84,stage='independently_verified_complete',outcome='progress',started_at=start,elapsed_seconds=elapsed,verified_counts=counts,discovered_objects=24,selected_objects=4,prepared_images=3,imported_objects=4,verified_objects=4,existing_objects_excluded=5,identity_or_unit_holds=14,date_holds=1,production_ids=receipt['production_ids'],metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],resume_cursor=cursor,next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000084-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000084-verify.py',evidence_paths=paths,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,no_local_catalogue_connections=True,limitations=limitations)
b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
b.save('milestone-report.json',dict(at=at,batch=84,batch_elapsed_seconds=elapsed,programme_measured_elapsed_seconds=runtime,prior_supervisor_verified_totals=parent['totals'],batch_verified_increments=counts,reconciled_programme_totals_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts},totals_scope='Programme receipt totals; no prior-campaign additions included. External supervisor retains cumulative state and hourly/100-hour reporting ownership.',next_task=next_task,continue_after_100_hours=True,failures='No provider or production failure. One title-collision research guard resolved; dependent preparation stopped until plan existed.',limitations=limitations))
(b.E/'README.md').write_text('''# Batch 84: National Gallery of Athens

Verified four new Parthenis review paintings and four documented holdings:
Aphrodite (Π.6453), Portrait of Antonis Benakis (Π.6471), Belle Epoque Lady
[Portrait of Sophia Laskaridou] (Π.11532), and Odeon of Herodes Atticus (Π.6479).
Three authentic museum primary images were individually viewed and verified in
production storage and public delivery. Aphrodite retains an image gap because
its 1950–1960 date crosses the Greek museum image cutoff of 1955. No new painters
or alternate images. Existing creator metadata, holdings and historical statuses
were preserved; new objects remain review records. No current display claims.

The second native Parthenis page contains 24 records: four selected, five already
present, fourteen title/version/catalogue-unit holds and one open-date hold.
Forty-four existing images were viewed in four immutable prior contact sheets;
seventeen unillustrated creator works were checked through metadata only. Every
new derivative was fully decoded, hashed, checked under 100,000 bytes and served
with its complete supplied proportions. Original files are outside Documents.
Museum rights remain restricted, separate from the user's source approval.

Independent source, database, audit, storage and public API receipts establish
attribution from this batch's plan/source/rights checksums and locked preimages.
Replaying completed delivery changed no rows, audit counts or storage generations.
The existing external supervisor and 83-to-84 handoff were verified read-only.
No scheduler, subagent, commit, deployment or local catalogue mutation was made.

Athens resumes at page 3. Scotland's historical HTTP 403 was recorded without
retry. All other 109 source-queue entries remain identical, including Thyssen,
SHUZO, Warsaw and French reserve cursors. Next: National Gallery London metadata
API after hold reconciliation. Nationwide and institution coverage remain partial.

See batch-verification-receipt.json, independent-production-verification.json,
independent-public-verification.json, independent-resume-verification.json,
source-queue-update-verification.json and CHECKPOINT.json. Measured runtime and
programme totals are in milestone-report.json. The recovery export contains the
full schema and scoped affected-row/preimage data; it is not a full catalogue dump.
''')
manifest=[]
for name in [Path(x).name for x in paths]+['CHECKPOINT.json','milestone-report.json','README.md','required-input-verification.json','registry-verification.json','final-global-identity-reconciliation.json','editorial-selection-review.json']:
 f=b.E/name;assert f.exists();manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
for f in sorted((b.ROOT/'ops').glob('*000084*.py')):manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
b.save('final-checkpoint-verification.json',dict(at=h.now(),files=manifest,evidence_files_exist=True,runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==cp,verified_counts=counts,source_queue_other_109_unchanged=True,supervisor_configuration_unchanged=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_source_entries_preserved=109,next_page=3)))
