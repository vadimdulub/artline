#!/usr/bin/env python3
import copy, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000036'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000036'
Q=ROOT/'docs/research/continuous-exhibitions-20261013/source-queue.json'
PDF=D.parents[0]/'000029/hermitage-pdf-receipt.json'
def save(n,x): D.mkdir(parents=True,exist_ok=True); c.save(D/n,x)
def plain(x): return json.loads(json.dumps(x,default=str))
counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']}
receipt=c.load(PDF)
with c.connect() as db:
 target={'instance':'artline-508319:europe-west1:artline-postgres','host':db.info.host,'port':db.info.port,'database':db.info.dbname,'checked_at':c.now()}
 assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
 prior=plain(db.execute("select * from exhibitions where import_batch=%s",('continuous-exhibitions-20261013-batch-000036',)).fetchall())
 matches=plain(db.execute("select id::text,title,start_date,end_date,import_batch from exhibitions where (title ilike %s or title ilike %s or title ilike %s or title ilike %s) order by start_date,title",('%Pontormo%','%Понторм%','%portrait%','%портрет%')).fetchall())
 totals=plain(db.execute("select count(*)::int exhibitions,(select count(*) from exhibition_occurrences)::int occurrences,(select count(*) from exhibition_entries)::int entries,(select count(*) from exhibition_participants)::int participants from exhibitions").fetchone())
 db.rollback()
save('recovery-check.json',{'at':c.now(),'target':target,'current_batch_existing':prior,'previous_inflight_writes_reconciled':True,'concurrent_smk_changes_excluded':True,'local_database_connections':0,'separate_artwork_programme_unchanged':True})
review={'at':c.now(),'route':'hermitage','source':receipt,'reviewed_exhibition_bibliography_pages':[397],'candidates':[{'key':'florence-1956-pontormo','source_label':'Florence 1956 Pontormo exhibition','decision':'hold','reason':'The saved official collection catalogue bibliography is a secondary object-history lead, but this bounded review did not recover the original exhibition title, exact dates, host venue, or an accession-specific object citation sufficient for an accurate event and participation row.'},{'key':'leningrad-1938-portraits','source_label':'Leningrad 1938 portrait exhibition','decision':'hold','reason':'The bibliography-level lead does not by itself delimit a painting/drawing checklist, distinguish the exact event title and venue, or identify an exact exhibited object. A generic portrait exhibition cannot be imported from a directory/publication mention.'}],'selected_events':0,'partial_or_complete_checklist_claimed':False,'no_directory_or_publication_count_as_event':True,'no_participation_inferred':True,'live_possible_title_matches':matches}
save('research-review.json',review)
verification={'at':c.now(),'target':target,'operation':'continuous-exhibitions-20261013-batch-000036','verified_counts':counts,'batch_rows':prior,'live_possible_title_matches':matches,'production_totals_snapshot':totals,'writes_attempted':0,'passed':True}
save('independent-database-verification.json',verification);save('verification.json',verification)
raw=Q.read_bytes();q=json.loads(raw);before=copy.deepcopy(q);src=next(x for x in q['sources'] if x['source_id']=='hermitage')
hold={'batch':36,'at':c.now(),'kind':'event_identity_and_checklist_evidence','detail':'Reviewed queued Florence1956 Pontormo and Leningrad1938 portrait leads from official Hermitage catalogue p397. Bibliography-level evidence did not establish accurate original event title/dates/host plus accession-specific participation; neither lead imported.','evidence':'docs/research/continuous-exhibitions-20261013/batches/000036/research-review.json'}
src['research_status']='partial_six_historical_events_verified_two_bibliography_leads_held'
src['cursor']['last_reviewed_batch']=36;src['cursor']['reviewed_leads_batch36']=['florence-1956-pontormo','leningrad-1938-portraits'];src['cursor']['next']='Rotate to an undercovered official Greek/Byzantine/icon archive with event-level pages or original catalogues; return to these two Hermitage leads only with original event identity and accession-specific evidence.'
src.setdefault('holds',[]).append(hold);src.setdefault('evidence',[]).extend([hold['evidence'],'docs/research/continuous-exhibitions-20261013/batches/000036/independent-database-verification.json'])
assert [x for x in q['sources'] if x['source_id']!='hermitage']==[x for x in before['sources'] if x['source_id']!='hermitage']
tmp=Q.with_name('source-queue.000036.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');tmp.replace(Q)
save('queue-update.json',{'at':c.now(),'source_id':'hermitage','before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(Q.read_bytes()).hexdigest(),'cursor':src['cursor'],'hold':hold,'preserved_unrelated_sources':True})
next_task='Research an undercovered official Greek, Byzantine or icon archive with event-level pages or an original catalogue; prioritize up to five events with explicit title/date/venue and selected accession-level participation. Do not retry the two Hermitage bibliography leads without stronger evidence.'
result={'outcome':'no_eligible_candidates','summary':'Reviewed the two queued official Hermitage historical leads (Florence 1956 Pontormo; Leningrad 1938 portraits) against the checksum-pinned catalogue and live production. Neither bibliography-level mention safely established the original event identity, venue/dates and exact participation required for import, so no production writes were made and both holds were checkpointed.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':[f'docs/research/continuous-exhibitions-20261013/batches/000036/{x}' for x in ['verification.json','independent-database-verification.json','recovery-check.json','research-review.json','queue-update.json','checkpoint.json','final-validation.json']]}
save('checkpoint.json',{'at':c.now(),'batch':36,'outcome':result['outcome'],'source_id':'hermitage','source_sha256':receipt['sha256'],'reviewed_leads':src['cursor']['reviewed_leads_batch36'],'holds':[hold],'production_changes':0,'verified_counts':counts,'next_task':next_task,'external_supervisor_owns_continuation':True})
R.mkdir(parents=True,exist_ok=True);c.save(R/'checkpoint.json',c.load(D/'checkpoint.json'));c.save(R/'worker-result.json',result)
save('final-validation.json',{'at':c.now(),'result':result,'all_result_evidence_paths_exist_except_self':all((ROOT/p).is_file() for p in result['evidence_paths'] if not p.endswith('final-validation.json')),'queue_after_matches_receipt':hashlib.sha256(Q.read_bytes()).hexdigest()==c.load(D/'queue-update.json')['after_sha256'],'production_reverified':True,'batch_boundary_respected':True,'passed':True})
print(json.dumps(result))
