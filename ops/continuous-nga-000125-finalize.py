"""Finalize only batch125; external supervisor and unrelated queue entries unchanged."""
import importlib.util,json,copy,datetime,fcntl,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-nga-images-000125.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
receipt=b.load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts['newly_illustrated']==8
assert b.load(b.E/'independent-resume-verification.json')['unchanged_snapshot']
assert len(b.load(b.E/'independent-public-verification.json')['rows'])==len(b.load(b.E/'independent-storage-verification.json')['checks'])==8
ire=b.load(b.P/'ireland-index-verification.json');irv=b.load(b.P/'ireland-existing-catalogue-verification.json');cap=ire['capture'];assert h.sha(Path(cap['body_path']).read_bytes())==cap['sha256'] and cap['status']==200
recon=b.load(b.E/'nga-gap-reconciliation.json');stamp=h.now()
nxt='Prioritize National Gallery of Ireland page39 saved object leads: inspect native8936 Scene on the Ice (existing NGI.432) and8943 Trevor Self-Portrait (existing NGI.502), reconcile accessions globally, then research exact permitted WikiArt/Commons images. Reuse saved index; native image host remains HTTP403-held. Page40 index is next uncaptured; page39 objects are still unresolved. NGA fallback position1284 with deferred positions retained; prefer another eligible institution before further NGA portraits.'
queue=b.P.parents[1]/'source-queue.json'
with (queue.parent/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=b.load(queue);before=copy.deepcopy(q)
 nga=next(x for x in q['sources'] if x['source_id']=='nga_washington');assert nga['resume_cursor']['position'] in [1271,1284]
 nga.update(status='eight_further_NGA_primary_images_verified_batch125',last_checked_at=stamp,checkpoint=str((b.P/'CHECKPOINT.json').relative_to(b.ROOT)),latest_batch_verified_counts=counts)
 nga['resume_cursor'].update(position=recon['resume_position'],latest_reconciliation=str((b.E/'nga-gap-reconciliation.json').relative_to(b.ROOT)))
 nga['resume_cursor']['deferred_positions']=sorted(set(nga['resume_cursor'].get('deferred_positions',[]))|{r['position'] for r in recon['rows'] if r['reason']=='creator_variety_deferred'})
 for name in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','independent-resume-verification.json']:
  p=str((b.E/name).relative_to(b.ROOT));nga.setdefault('evidence_paths',[])
  if p not in nga['evidence_paths']:nga['evidence_paths'].append(p)
 ireland=next(x for x in q['sources'] if x['source_id']=='national_gallery_ireland');ireland.update(status='page39_twelve_index_leads_captured_object_reconciliation_pending_image_host_hold_preserved',last_checked_at=stamp,last_batch=125,checkpoint=str((b.P/'CHECKPOINT.json').relative_to(b.ROOT)),latest_batch_verified_counts={k:0 for k in counts})
 ireland.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(ireland['resume_cursor']))
 ireland['resume_cursor'].update(captured_page=39,next_page=40,next_url=ire['next_url'],pending_page39_object_ids=[r['source_id'] for r in ire['rows']],pending_page39_evidence=str((b.P/'ireland-index-verification.json').relative_to(b.ROOT)),next_step=nxt,retry_image_host=False)
 for name in ['ireland-index-capture.json','ireland-index-verification.json','ireland-existing-catalogue-verification.json']:
  p=str((b.P/name).relative_to(b.ROOT));ireland.setdefault('evidence_paths',[])
  if p not in ireland['evidence_paths']:ireland['evidence_paths'].append(p)
 ireland['remaining_gaps']=[s for s in ireland.get('remaining_gaps',[]) if s!='Page 39 onward unresearched in this programme.']+['Page39 index captured only: all12 object details and alternative-image research remain pending; page40 onward uncaptured.']
 others=lambda x:[r for r in x['sources'] if r['source_id'] not in ['nga_washington','national_gallery_ireland']]
 assert others(q)==others(before) and len(q['sources'])==111
 b.save(b.P/'source-queue-update-verification.json',dict(at=stamp,changed_source_ids=['nga_washington','national_gallery_ireland'],unrelated_entries_preserved=109,before=[x for x in before['sources'] if x['source_id'] in ['nga_washington','national_gallery_ireland']],after=[nga,ireland]))
 tmp=queue.with_suffix('.000125.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,queue)
start=b.load(b.P/'required-input-reconciliation.json')['at'];seconds=(datetime.datetime.fromisoformat(stamp)-datetime.datetime.fromisoformat(start)).total_seconds()
b.save(b.P/'batch-verification-receipt.json',dict(receipt,batch=125,batch107_reconciled=12,batch107_increment=0,ireland_index_leads=12,ireland_production_increment=0,measured_runtime_seconds=seconds))
evidence=[b.E/n for n in ['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','source-citation-pin-verification.json','local-recovery-verification.json']]+[b.P/n for n in ['batch107-live-reconciliation.json','actual-visual-review.json','ireland-index-verification.json','ireland-existing-catalogue-verification.json','source-queue-update-verification.json']]
files=[]
for p in evidence:
 h.load(p);files.append(dict(path=str(p.relative_to(b.ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
b.save(b.P/'independent-final-artifact-verification.json',dict(at=stamp,files=files,passed=True))
cp=dict(at=stamp,batch=125,stage='verified_complete',outcome='progress',verified_counts=counts,selected=8,prepared=8,imported=8,verified=8,contact_sheet_viewed=8,individually_viewed_derivatives=2,measured_runtime_seconds=seconds,next_task=nxt,resume_cursor=nga['resume_cursor'],local_catalogue_connections=0,external_supervisor_unchanged=True,limitations=['Eight Nanteuil/coauthored/after-model prints are not eight distinct printmakers.','All8 visually reviewed on contact sheet; both Colbert derivatives additionally viewed individually. No full-resolution originals viewed.','Scoped schema and affected-row recovery; no full database export.','Ireland index discovery does not establish exact object identity or image permission.'],failures=['System Python lacked psycopg; established venv reused without installing dependencies.'])
b.save(b.P/'CHECKPOINT.json',cp);b.save(b.RUNTIME/'batch-checkpoint.json',cp)
master=b.load(queue.parent/'CHECKPOINT.json');totals={k:master['totals'][k]+counts[k] for k in counts}
b.save(b.P/'milestone-report.json',dict(at=stamp,batch=125,measured_batch_seconds=seconds,prior_supervisor_totals=master['totals'],cumulative_including_batch125=totals,verified_counts=counts,next_task=nxt,failures=cp['failures'],limitations=cp['limitations'],reporting='External supervisor owns hourly and100-hour reporting and continuation; no edits to supervisor, schedule or master checkpoint.'))
print(json.dumps(dict(verified_counts=counts,next_task=nxt,seconds=seconds)))
