#!/usr/bin/env python3
"""Read-only independent verification and durable batch-25 handoff."""
import collections,datetime,fcntl,gzip,importlib.util,json,sys
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('b25',Path(__file__).with_name('continuous-chicago-batch-000025.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
def save(name,v):return b.save(E/name,v)
def source():
 p,pin=h.pinned(b.PHASE);checks=[]
 assert 1<=len(p['records'])<=12 and not p['new_institutions'] and not p['artists']
 for r in p['records']:
  rc=r['original_api_receipt'];body=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(body)==rc['sha256'];o=json.loads(body)['data']
  assert o==r['raw']==h.load(b.ROOT/r['evidence_file']) and h.sha((b.ROOT/r['evidence_file']).read_bytes())==r['evidence']['sha256']
  assert str(o['id'])==r['source_id'] and rc['url'].startswith('https://api.artic.edu/api/v1/artworks/'+r['source_id']+'?')
  assert (r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['dimensions'],r['medium'],r['creator_label'])==(o['title'],o['main_reference_number'],o['date_display'],o['date_start'],o['date_end'],o['dimensions'],o['medium_display'],o['artist_display'])
  assert r['first']<=r['last']<=1970 and r['artist_id'] is None and r['creator_link_hold'] and o['artist_display'].startswith('Byzantine')
  assert not r['before'] and r['add_holding'] and r['holding_confidence']>=.8
  checks.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],accession=r['accession_number'],source_url=r['source_url'],api_url=rc['url'],api_sha256=rc['sha256'],selected_source_sha256=r['evidence']['sha256'],date_display=r['date_display'],bounds=[r['first'],r['last']],credit=o['credit_line'],provenance=o['provenance_text'],original_cultural_attribution=r['creator_label'],source_type=o['artwork_type_title'],no_current_display_claim=True))
 save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,images_selected=0,images_downloaded=0,images_visually_viewed=0,source_image_access_hold_preserved=True))
 print('Independent source verification',len(checks),flush=True)
def production():
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];locked=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert locked['artworks']=={} and locked['plan_sha256']==pin
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==len(ids)
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))]
  assert len(notes)==len(ids) and all(x['note']['plan_sha256']==pin for x in notes)
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert {x['entity_id'] for x in events}==set(ids)
  for r in p['records']:
   aid=r['artwork_id'];state=after[aid];a=state['artwork'];note=next(x for x in notes if x['entity_id']==aid)
   assert note['source_record_id']==r['source_id'] and note['note']['evidence']['sha256']==r['evidence']['sha256']
   assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None and a['research_candidate']
   assert (a['title'],a['accession_number'],a['date_display'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['dimensions_text'],a['medium_text'],a['unlinked_creator_label'],a['cultural_context'])==(r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'],r['creator_label'],'Byzantine')
   assert a['current_institution_id']==b.MID and not state['creators'] and not state['attachments']
   assert len(state['holdings'])==1;hold=state['holdings'][0];assert hold['claim_type']=='holding' and hold['review_state']=='accepted' and hold['institution_id']==b.MID
   ev=json.loads(hold['evidence_note']);assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
   native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(r['scheme'],r['source_id'])).fetchall();assert native==[dict(entity_id=aid)]
   assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,r['accession_number'])).fetchone()['n']==1
  scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))];assert all(x['scope']=='eligible' for x in scope)
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n'];assert search==len(ids)
 save('independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),empty_transaction_preimages_verified=True,rows=after,citations=notes,creation_scope=scope,search_documents=search,new_review_artworks=len(ids),accepted_holdings=len(ids),local_database_connections=0))
 save('independent-audit-history-verification.json',dict(at=h.now(),events=events,attribution='New IDs absent from locked transaction preimages, own persisted source/plan checksums and insertion audit events; previous campaigns excluded.'))
 public=[]
 for aid in ids:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;rr=requests.get(url,timeout=(15,45));rr.raise_for_status();obj=rr.json();assert obj['id']==aid and obj['title']==after[aid]['artwork']['title'];public.append(dict(artwork_id=aid,url=url,status=rr.status_code,response_sha256=h.sha(rr.content)))
 save('independent-public-verification.json',dict(at=h.now(),rows=public,unified_catalogue_visibility_verified=True))
 counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=0,alternate_images=0,museum_links=len(ids))
 save('independent-no-image-changes-verification.json',dict(at=h.now(),selected_images=0,prepared_images=0,new_media_assets=0,actual_images_visually_viewed=0,production_artworks_with_media=0,evidence='All selected current rows have primary_media_id null and empty media associations; Chicago image access hold preserved; SMK selection empty.'))
 save('actual-visual-review.json',dict(at=h.now(),viewed_files=[],selected_images=0,reason='French reserve already illustrated; no reserve selected. SMK selected zero. Chicago metadata-only under recorded image HTTP 403 hold. No unsampled images claimed viewed.',prior_reserve_visual_evidence='docs/research/printmaking-continuation-20261011/french-reserve/; immutable historical visual approvals retained without replay.'))
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,production_target=b.base.target(),attribution='Independently verified source captures, empty locked preimages, own persisted plan/source checksums, audit insertion events, holdings and public detail responses. All prior French/Walters additions excluded.'))
 print(json.dumps(counts),flush=True)
def finish():
 receipt=h.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];g=h.load(E/'gap-reconciliation.json');c=h.load(E/'chicago-global-identity-reconciliation.json')
 nxt='Rotate to a new registry-backed route such as Princeton public-domain object/image evidence or an unheld Greek object route. SMK image gaps resume after UUID '+g['resume_after_artwork_id']+'; do not repeat these 80 unchanged holds. Chicago metadata resumes with saved unselected IDs, then Byzantine search page 2; preserve image HTTP 403 hold. French reserve exhausted (188 already delivered).'
 evidence=['independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-no-image-changes-verification.json','batch-verification-receipt.json','french-reserve-live-reconciliation.json','prior-batch-live-reconciliation.json','gap-reconciliation.json','chicago-global-identity-reconciliation.json','final-editorial-review.json','source-queue-update-verification.json','milestone-report.json','CHECKPOINT.json']
 cp=dict(at=h.now(),batch=25,stage='independently_verified_complete',verified_counts=counts,production_ids=receipt['production_ids'],next_task=nxt,evidence_paths=[str((E/x).relative_to(b.ROOT)) for x in evidence],remaining_gaps=['Chicago new objects have no images; native IIIF hold preserved','Chicago object 35355 held: 5th-century display versus 301–500 source bounds; original plan retained unapplied','SMK 80 checked gaps selected zero; exact rights/date/attribution reasons saved','No national or museum-wide coverage completion implied'],resumes=dict(smk_after_artwork_id=g['resume_after_artwork_id'],chicago=dict(c['resume'],editorial_held_ids=['35355']),french_reserve_remaining=0),external_supervisor='Unchanged; one bounded worker batch only')
 save('CHECKPOINT.json',cp);b.save(b.R/'CHECKPOINT.json',cp)
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);queue=h.load(qp);before=json.loads(json.dumps(queue));routes={x['source_id']:x for x in queue['sources']}
  yale=routes['yale_lux'];yale.update(last_checked_at=h.now(),status='french_reserve_exhausted_live_verified_188_already_delivered')
  yale['evidence_paths']=list(dict.fromkeys(yale.get('evidence_paths',[])+[str((E/'french-reserve-live-reconciliation.json').relative_to(b.ROOT))]))
  smk=routes['smk_denmark'];smk.update(last_checked_at=h.now(),status='bounded_80_image_gaps_no_eligible_exact_pdm_matches',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=dict(route='existing_native_primary_image_gaps',after_artwork_id=g['resume_after_artwork_id'],checked=80,selected=0),remaining_gaps=dict(collections.Counter(x['reason'] for x in g['rows'])))
  smk['evidence_paths']=list(dict.fromkeys(smk.get('evidence_paths',[])+[str((E/x).relative_to(b.ROOT)) for x in ['source-register.json','bounded-gap-input.json','gap-reconciliation.json','source-access-holds.json']]))
  chicago=routes['artic'];chicago.update(last_checked_at=h.now(),status='new_byzantine_metadata_verified_iiif_http_403_access_hold',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),metadata_resume_cursor=cp['resumes']['chicago'],verified_counts=counts)
  # Keep the prior image route cursor and explicit retry_allowed=false unchanged.
  chicago['evidence_paths']=list(dict.fromkeys(chicago.get('evidence_paths',[])+[str((E/x).relative_to(b.ROOT)) for x in evidence if x not in ['source-queue-update-verification.json']]))
  unrelated={x['source_id']:x for x in before['sources'] if x['source_id'] not in ['yale_lux','smk_denmark','artic']};assert unrelated=={x['source_id']:x for x in queue['sources'] if x['source_id'] in unrelated}
  old_hash=h.sha(qp.read_bytes());tmp=qp.with_suffix('.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2));tmp.replace(qp)
  save('source-queue-update-verification.json',dict(at=h.now(),before_sha256=old_hash,after_sha256=h.sha(qp.read_bytes()),changed_routes=['yale_lux','smk_denmark','artic'],unrelated_entries_preserved=len(unrelated),chicago_image_resume_cursor_preserved=chicago['resume_cursor'],resumes=cp['resumes']))
 root=h.load(E.parents[1]/'CHECKPOINT.json');start=datetime.datetime.fromisoformat(root['inflight']['started_at']);end=datetime.datetime.now(datetime.timezone.utc);assert root['inflight']['batch']==25
 save('milestone-report.json',dict(at=h.now(),measured_batch_interval=dict(start=start.isoformat(),end=end.isoformat(),seconds=(end-start).total_seconds()),reserve_reconciled=188,reserve_new=0,smk_checked=g['checked'],smk_selected=0,chicago_checked=c['checked'],initial_selection=c['selected'],final_selected=counts['new_artworks'],final_editorial_holds=1,imported=counts['new_artworks'],verified_counts=counts,programme_prior_verified_totals=root['totals'],programme_totals_including_this_batch={k:root['totals'][k]+counts[k] for k in counts},failures=['System Python lacked psycopg; established venv reused','One SMK metadata HTTP 500 retained; no retry','Chicago optional is_deaccessioned field absent; handled with get, explicit provenance/credit review preserved; capture reused'],unresolved=cp['remaining_gaps'],next_task=nxt,supervisor='External supervisor owns hourly schedule and root checkpoint; no edits, launches or additional sessions'))
 result=dict(outcome='progress',summary='Verified '+str(counts['new_artworks'])+' new Chicago Byzantine review artworks and documented holdings. French reserve: all 188 already delivered, counted zero. Saved 80 SMK gap outcomes; provider image holds preserved.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence_paths'])
 save('worker-result.json',result);b.save(b.R/'worker-result.json',result)
 assert all((b.ROOT/x).exists() for x in result['evidence_paths']);print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(source=source,production=production,finish=finish)[sys.argv[1]]()
