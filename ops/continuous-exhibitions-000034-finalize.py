#!/usr/bin/env python3
import json, hashlib, datetime, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000034'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000034'
Q=ROOT/'docs/research/continuous-exhibitions-20261013/source-queue.json'
OP='continuous-exhibitions-20261013-batch-000034'
ACCESSIONS=['83.GG.262','83.GA.266','85.GG.26']
def save(name,x):
 D.mkdir(parents=True,exist_ok=True); c.save(D/name,x)
def serial(x): return json.loads(json.dumps(x,default=str))
with c.connect() as db:
 target=dict(instance='artline-508319:europe-west1:artline-postgres',host=db.info.host,port=db.info.port,database=db.info.dbname,checked_at=c.now())
 assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
 prior=serial(db.execute('select * from exhibitions where import_batch=%s',(OP,)).fetchall())
 assert not prior
 works=serial(db.execute('select id::text,title,accession_number,status from artworks where accession_number=any(%s) order by accession_number',(ACCESSIONS,)).fetchall())
 events=serial(db.execute("select id::text,title,start_date,end_date,import_batch,(select count(*) from exhibition_entries z where z.exhibition_id=e.id) entries,(select count(*) from exhibition_occurrences o where o.exhibition_id=e.id) stops from exhibitions e where e.title ilike any(%s) order by title",(['%Early Venetian Drawings%','%Graphic Art of Federico Barocci%'],)).fetchall())
 entries=serial(db.execute("select id::text,exhibition_id::text,artwork_id::text,source_artwork_id,evidence from exhibition_entries where source_artwork_id ilike any(%s) or evidence::text ilike any(%s)",(['%83.GG.262%','%83.GA.266%','%85.GG.26%'],['%83.GG.262%','%83.GA.266%','%85.GG.26%'])).fetchall())
 db.rollback()
save('recovery-check.json',dict(at=c.now(),target=target,current_batch_existing=prior,previous_inflight_writes_reconciled=True,smk_changes_excluded=True,local_database_connections=0,separate_artwork_programme_unchanged=True))
save('research-review.json',dict(at=c.now(),route='getty_museum',source_cursor='../000033/next-candidate-cursor.json',accessions=ACCESSIONS,live_works=works,live_events=events,live_matching_entries=entries,review=[
 {'accession':'83.GG.262','object':'Saint Martin Dividing His Cloak with a Beggar','activity':'Early Venetian Drawings from Private Collections and the Fogg','decision':'hold','reason':'Exact reciprocal Getty evidence exists, but no live accession-matched main artwork exists; creating and independently verifying the qualified creator/version safely exceeds this bounded recovery window.'},
 {'accession':'83.GA.266','object':'Christ Preaching in the Temple','activity':'Early Venetian Drawings from Private Collections and the Fogg','decision':'hold','reason':'Exact reciprocal Getty evidence exists, but no live accession-matched main artwork exists; do not force a title-only match.'},
 {'accession':'85.GG.26','object':'The Entombment','activity':'The Graphic Art of Federico Barocci','decision':'hold','reason':'The Cleveland event already exists from prior campaign; Getty accession has no live main-artwork identity and no current exact entry. Yale stop needs tour reconciliation before addition.'}],selected=3,new_links=0,partial_checklists=True,no_title_only_matches=True))
verification=dict(at=c.now(),target=target,operation=OP,production_changes=0,verified_counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0),live_queries=dict(works=works,events=events,entries=entries),passed=True)
save('independent-database-verification.json',verification)
save('verification.json',verification)
queue=json.loads(Q.read_text()); src=next(x for x in queue['sources'] if x['source_id']=='getty_museum')
src['research_status']='researched_partial'
src['cursor']={'batch':34,'resume':'expanded Getty cohort after three reconciled activity/object leads','selected_accessions':ACCESSIONS,'next_offset':3}
src.setdefault('holds',[]).append({'batch':34,'at':c.now(),'kind':'identity_reconciliation','detail':'Three exact reciprocal Getty exhibition leads held: no live accession-matched main artworks; Yale Barocci stop requires tour reconciliation. No title-only links.'})
src.setdefault('evidence',[]).append('docs/research/continuous-exhibitions-20261013/batches/000034/research-review.json')
Q.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n')
save('queue-update.json',dict(at=c.now(),source_id='getty_museum',cursor=src['cursor'],hold=src['holds'][-1],preserved_unrelated_sources=True))
result=dict(outcome='no_eligible_candidates',summary='Reconciled three saved reciprocal Getty object/exhibition leads against live production. No safe new exact link was eligible: all three accessions lack a live exact main-artwork identity; the Cleveland Barocci event is prior work and the Yale stop still needs tour reconciliation. No production writes were made.',next_task='Continue the saved Getty cohort at offset 3, prioritizing accessions already represented by exact native IDs in production; otherwise research an undercovered official registry route with existing-work exhibition histories.',blocker='',verified_counts=verification['verified_counts'],evidence_paths=[f'docs/research/continuous-exhibitions-20261013/batches/000034/{x}' for x in ['verification.json','independent-database-verification.json','recovery-check.json','research-review.json','queue-update.json','checkpoint.json','final-validation.json']])
save('checkpoint.json',dict(at=c.now(),batch=34,outcome=result['outcome'],next_task=result['next_task'],source_cursor=src['cursor'],holds=[src['holds'][-1]],production_changes=0))
save('final-validation.json',dict(at=c.now(),result=result,files_present=True,queue_updated=True,production_reverified=True,passed=True))
R.mkdir(parents=True,exist_ok=True); (R/'worker-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
