"""Receipt reconciliation and locked source-queue checkpoint for one batch."""
import copy,datetime,fcntl,importlib.util,json,os,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('b171',Path(__file__).with_name('continuous-greek-batch-000171.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);rc=h.load(b.E/'batch-verification-receipt.json');counts=rc['verified_counts'];assert counts==dict(new_painters=0,new_artworks=2,newly_illustrated=2,alternate_images=0,museum_links=2)
ids=rc['production_ids'];prod=h.load(b.E/'independent-production-verification.json');images,audit,review=i.accepted(b.B);ims={x['artwork_id']:x for x in images};selection=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert after==prod['after']
 notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' checksum FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(notes)==2 and all(x['checksum']==pin for x in notes)
 media=[dict(x) for x in db.execute('SELECT a.id::text,ma.creator_credit,ma.license_label,ma.rights_status,mre.adapter_version,mre.source_record_id,mre.source_checksum,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))]
 for x in media:
  row=next(r for r in p['records'] if r['artwork_id']==x['id']);ev=x['evidence_json'] if isinstance(x['evidence_json'],dict) else json.loads(x['evidence_json']);assert ev['selection_sha256']==selection and ev['original_catalogue_plan_sha256']==pin
  assert x['adapter_version']==b.OP and x['source_checksum']==row['evidence']['sha256'] and x['source_record_id']==row['source_id'];assert row['credit'] in x['creator_credit'] and x['rights_status']=='restricted' and '© 2026' in x['license_label']
 pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['artworks']=={} and pre['plan_sha256']==pin
 ipre=h.load(i.BACKUP/b.B/'before-000.json.gz');assert all(x['artwork']['primary_media_id'] is None for x in ipre.values())
b.save('independent-read-only-resume-verification.json',dict(at=h.now(),live_rows_equal=True,metadata_citation_plan_checksums=notes,image_operation_and_selection_checksums_match=True,metadata_locked_preimages_empty=True,image_locked_preimages_null=True,source_foundation_credit_preserved=True,rights_restricted_preserved=True,rows=len(ids),new_write_attempts=0,replay_required=False,previous_campaigns_excluded=True,passed=True))
checks=h.load(b.E/'roilos-global-identity-reconciliation.json')['records'];assert len(checks)==28
holds=h.load(b.E/'research-holds.json');assert len(holds['records'])==26
next_task='Process Smithsonian SAAM shard23 for exact existing image gaps, reconciling live primaries before selection. Roilos28/28 reviewed: two delivered,24 undated and two open-boundary objects held. Preserve French reserve exhaustion and Greek/provider holds; then rotate to another untouched registry institution.'
at=h.now();parent=h.load(b.E.parents[1]/'CHECKPOINT.json');start=parent['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds();runtime=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(parent['started_at'])).total_seconds()
paths=[str((b.E/n).relative_to(b.ROOT)) for n in ['independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-existing-preservation-verification.json','independent-public-verification.json','independent-storage-verification.json','independent-read-only-resume-verification.json','actual-visual-review.json','batch-verification-receipt.json','batch107-live-reconciliation.json','batch169-live-reconciliation.json','batch170-live-reconciliation.json','research-holds.json']]
cursor=dict(route='official_roilos_artist_index_and_inventory_reconciliation',artist_index='https://www.nationalgallery.gr/en/artist/roilos-georgios/',artist_native_id='133',processed_page=2,next_page=None,index_complete=True,source_reported_total=28,notices_reviewed=28,processed_urls=h.load(b.E/'roilos-all-object-urls.json'),verified_native_ids=[r['source_id'] for r in p['records']],verified_artwork_ids=ids,held_source_ids=[r['source_id'] for r in holds['records']],metadata_plan_sha256=pin,image_selection_sha256=selection,evidence=str((b.E/'source-register-final.json').relative_to(b.ROOT)),do_not_repeat_unchanged_holds=True,next_task=next_task)
b.save('source-register-final.json',dict(at=at,source_id='national_gallery_athens',provider=b.MUSEUM,registry_reference='/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv',policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',access_status='Official creator index, documented page2 AJAX,28 selected object notices and two selected source images HTTP200',last_checked_at=at,metadata_creation_scope='through1970',image_creation_scope='through1955 Greek museum-source extension',rights_status='restricted',licence_basis='Actual museum copyright notice; no per-image open licence. User source approval retained separately.',discovered_object_notices=28,selected_objects=2,prepared_images=2,imported_artworks=2,independently_verified_counts=counts,artist_reused='e17bd3cc-0953-5aa6-9e0e-00a16419379d',legal_owner_not_asserted=True,source_collection_credit='Ε. Koutlidis Foundation Collection',holdings_not_display=True,directory_coverage='One existing institution route and one previously unprocessed creator index; no claim of nationwide or whole-museum artwork coverage.',resume_cursor=cursor,remaining_gaps=['24 undated and two open-boundary notices held for separate editorial review; no guessed dates.','Existing War Museum broad chronology and unillustrated records remain unchanged.','Other Greek creators and all source-wide collection coverage incomplete.']))
qp=b.E.parents[1]/'source-queue.json'
with (b.E.parents[1]/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);raw=qp.read_bytes();queue=json.loads(raw);before=copy.deepcopy(queue);assert len(queue['sources'])==111
 row=next(x for x in queue['sources'] if x['source_id']=='national_gallery_athens');history=row.setdefault('research_history',[]);assert not any(x.get('batch')==171 for x in history),'Finalization already recorded; reconcile checkpoint instead of updating queue again'
 row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']));row.setdefault('verified_count_history',[]).append(dict(checkpoint=row.get('checkpoint'),verified_counts=row.get('latest_batch_verified_counts'),scope='Prior independent increments retained, not recounted'))
 row['resume_cursor']['roilos_georgios']=cursor;row['resume_cursor']['next_undercovered_creator_route']='Rotate institution to Smithsonian SAAM shard23; Roilos index28/28 reviewed and holds preserved.'
 history.append(dict(batch=171,at=at,route='roilos-georgios',discovered_objects=28,selected=2,date_holds=26,verified_counts=counts,evidence_path=str((b.E/'source-register-final.json').relative_to(b.ROOT))))
 row.update(status='roilos28_notices_reviewed_two_new_illustrated_review_paintings_and_holdings_verified',last_checked_at=at,last_batch=171,checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),latest_batch_verified_counts=counts,verified_counts=counts,access_status='Roilos creator index and28 native object pages plus2 source images HTTP200; all prior holds retained')
 row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+paths+[str((b.E/'source-register-final.json').relative_to(b.ROOT)),str((b.E/'CHECKPOINT.json').relative_to(b.ROOT))]))
 row.setdefault('remaining_gaps',[]).append('Roilos28/28 native notices reviewed in batch171;24 undated and2 open-boundary date holds remain; no source-wide exhaustion claim.')
 assert {x['source_id']:x for x in queue['sources'] if x['source_id']!='national_gallery_athens'}=={x['source_id']:x for x in before['sources'] if x['source_id']!='national_gallery_athens'}
 assert all(queue[k]==before[k] for k in before if k!='sources')
 temp=qp.with_name('source-queue.batch-000171.tmp');temp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');assert qp.read_bytes()==raw;os.replace(temp,qp)
 after_queue=h.load(qp);assert after_queue==queue
b.save('source-queue-update-verification.json',dict(at=at,before_sha256=h.sha(raw),after_sha256=h.sha(qp.read_bytes()),registry_rows=111,changed_source_ids=['national_gallery_athens'],unrelated_entries_preserved=110,other_top_level_fields_preserved=True,prior_athens_cursors_and_holds_preserved=True,exact_new_cursor=cursor,passed=True));paths.append(str((b.E/'source-queue-update-verification.json').relative_to(b.ROOT)))
cp=dict(at=at,batch=171,stage='independently_verified_complete',outcome='progress',started_at=start,elapsed_seconds=elapsed,verified_counts=counts,discovered=28,selected=2,prepared=2,imported=2,verified=2,date_holds=26,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=selection,resume_cursor=cursor,next_task=next_task,evidence_paths=paths,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,local_catalogue_connections=0,verification_command='/tmp/artline-cesi-venv/bin/python ops/continuous-greek-000171-verify.py',limitations=['New source metadata and creator reconciliation verified; no new painter record needed.','Four new image files viewed: two originals and two derivatives. Existing creator records metadata-reviewed only.','Source copyright remains restricted, with Foundation credit; museum holdings do not assert legal ownership or current display.','Recovery uses full schema and scoped exact preimages, not a new full database backup.','Million-artwork and300000 illustrated-work global counts not recalculated. External supervisor owns master checkpoint and hourly reports.'])
b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
b.save('milestone-report.json',dict(at=at,batch=171,batch_measured_elapsed_seconds=elapsed,programme_measured_elapsed_seconds=runtime,prior_supervisor_totals=parent['totals'],verified_batch_increments=counts,programme_totals_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts},scope='This programme receipts only; all previous campaigns and other jobs excluded. Pending external supervisor acceptance; master totals unchanged by this worker.',source_failures=0,production_failures=0,held_objects=26,next_task=next_task,continue_after100hours=True,external_supervisor_owns_hourly_reports=True))
(b.E/'README.md').write_text('''# Batch171: Georgios Roilos at the National Gallery Athens

Verified two new review paintings, two primary images and two accepted holdings:
Self-portrait (ca.1890–1893), Κ.191, and The Battle of Farsala (1897–1903), Κ.433.
The existing globally reconciled Georgios Roilos artist was reused. E.Koutlidis
Foundation collection credit is preserved; holdings do not assert legal ownership
or current display. Actual image rights remain restricted, with user approval
recorded separately.

All28 native notices were captured: two delivered,24 undated and two open-boundary
date holds. Both originals and derivatives were individually viewed; derivatives
fully decoded, hashed, under100000 bytes and independently checked against
production, image storage bytes and public HTTP delivery. Existing creator works
were metadata-reviewed. No claim of whole-institution or nationwide coverage.

Own empty metadata transaction preimages, null image transaction preimages,
persisted citation/rights checksums and insert/update audit records establish this
batch's increments. Batches107,169 and170 reconciled live; no earlier increments
recounted. Scoped recovery and original sources are outside Documents. Only the
Athens registry entry changed;110 other entries and supplementary routes remain
unchanged. No local catalogue connections, new supervisor, schedule change,
Translation, infrastructure change, commit, push or deployment.

Next: Smithsonian SAAM shard23 exact existing primary-image gaps, then rotate
institutions. Roilos holds must not be re-requested without new date evidence.
''')
manifest=[]
for path in paths+[str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),str((b.E/'milestone-report.json').relative_to(b.ROOT)),str((b.E/'README.md').relative_to(b.ROOT)),str((b.E/'source-register-final.json').relative_to(b.ROOT))]:
 f=b.ROOT/path;assert f.exists();h.load(f) if f.suffix=='.json' else f.read_bytes();manifest.append(dict(path=path,sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
b.save('independent-final-artifact-verification.json',dict(at=h.now(),files=manifest,evidence_paths_exist=True,runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==cp,source_queue_other110_preserved=True,counts=counts,passed=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,checkpoint=str(b.E/'CHECKPOINT.json'),next_task=next_task)))
