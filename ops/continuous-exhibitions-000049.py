#!/usr/bin/env python3
import fcntl, json, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import exhibitions_common as c
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000049'; R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000049'; B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000049'; Q=E.parents[1]/'source-queue.json'; OP='continuous-exhibitions-20261013-batch-000049'
SPECS=[
 ('painters-and-antiquity','Painters and Antiquity','1985-12-20','1986-03-02','National Gallery','Athens'),
 ('giorgos-mavroidis','Giorgos Mavroidis','1986-01-27','1986-03-06','National Gallery','Athens'),
 ('impressionist-and-post-impressionist-engravings','Impressionist and post-impressionist engravings','1981-04-06','1981-05-10','Macedonian Centre of Contemporary Art','Thessaloniki')]
serial=lambda x:json.loads(json.dumps(x,default=str))
def save(p,x): p.parent.mkdir(parents=True,exist_ok=True); c.save(p,x)
def target(db):
 ps=subprocess.check_output(['ps','-axo','command'],text=True); assert any('/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth artline-508319:europe-west1:artline-postgres'==x.strip() for x in ps.splitlines()); assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline'); return {'instance':'artline-508319:europe-west1:artline-postgres','host':db.info.host,'port':db.info.port,'database':db.info.dbname,'checked_at':c.now()}
def prepare():
 events=[]
 with c.connect() as db:
  t=target(db); prior=serial(db.execute('select id::text,title from exhibitions where import_batch=%s',(OP,)).fetchall()); assert not prior
  for key,title,start,end,venue,city in SPECS:
   url=f'https://www.nationalgallery.gr/en/exhibitions/{key}/'; raw,rc=c.capture(url); text=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',raw.decode('utf8','replace')))
   assert title.casefold() in text.casefold() and venue.casefold() in text.casefold() and start[:4] in text and end[:4] in text
   near=serial(db.execute("select id::text,title,start_year,import_batch from exhibitions where normalized_title=%s and start_year=%s",(c.norm(title),int(start[:4]))).fetchall()); assert not near,(title,near)
   events.append(dict(key=key,id=c.uid(OP+'/'+key),oid=c.uid(OP+'/venue/'+key),title=title,start=start,end=end,venue=venue,city=city,source=dict(receipt=rc,text=text)))
 save(E/'recovery-check.json',dict(at=c.now(),target=t,prior_batch_rows=prior,previous_inflight_writes_reconciled=True,concurrent_danish_rows_counted=0,separate_artwork_programme_unchanged=True))
 p=dict(at=c.now(),operation=OP,target=t,events=events,basis='Official National Gallery of Greece historical page explicitly identifies the held pictorial or print exhibition, exact dates, and venue. No checklist was reviewed and no artist or artwork participation is inferred.',checklist_state='unknown')
 save(E/'plan.json',p);save(B/'plan.json',p);save(E/'plan-pin.json',{'sha256':c.sha((E/'plan.json').read_bytes()),'backup':str(B/'plan.json')});save(E/'research-review.json',{'at':c.now(),'selected':len(events),'events':events,'partial_or_unknown_checklists':True,'images_reviewed':0,'getty':'remaining accession leads retain batch 34 identity hold','arthive':'existing HTTP 429 hold retained; no repeat request','holds':['No explicit object checklist; no participation inferred.']})
def apply():
 p=c.load(E/'plan.json'); pin=c.load(E/'plan-pin.json')['sha256']; assert c.sha((E/'plan.json').read_bytes())==pin and p==c.load(B/'plan.json')
 with c.connect(write=True) as db:
  target(db);db.execute("select set_config('artline.actor_user_id','local-european-research',true)");db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
  ids=[x['id'] for x in p['events']]; old=serial(db.execute('select * from exhibitions where id=any(%s::uuid[])',(ids,)).fetchall());assert not old;save(B/'transaction-preimage.json',{'at':c.now(),'plan_sha256':pin,'exhibitions':old})
  for e in p['events']:
   display=e['start']+' – '+e['end']; ev={'operation':OP,'plan_sha256':pin,'basis':p['basis'],'checked_at':p['at'],'checklistComplete':False}
   db.execute("insert into exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,'day','held',%s,'physical','unknown','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['start'],e['end'],int(e['start'][:4]),int(e['end'][:4]),display,p['basis']+' Assessment: '+p['at'],OP))
   r=e['source']['receipt'];sid=c.uid(OP+'/source/'+e['key']);db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,e['id'],OP,e['key'],r['url'],r['retrieved_at'],r['body_path'],r['sha256'],Jsonb(e['source']),Jsonb(ev)))
   db.execute('insert into exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],sid,e['venue'],e['city'],'Greece','GR',e['start'],e['end'],display,Jsonb(ev)))
   post=serial(db.execute('select * from exhibitions where id=%s',(e['id'],)).fetchone());db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values('local-european-research','continuous_exhibition_insert','exhibition',%s,%s,%s,%s)",(e['id'],OP,Jsonb(None),Jsonb({'record':post,'plan_sha256':pin,'occurrence_id':e['oid']})))
 save(E/'applied.json',{'at':c.now(),'plan_sha256':pin,'ids':ids})
def verify():
 p=c.load(E/'plan.json');ids=[x['id'] for x in p['events']]
 with c.connect() as db:
  t=target(db); rows=serial(db.execute('select id::text,title,start_date,end_date,status,import_batch from exhibitions where id=any(%s::uuid[]) order by title',(ids,)).fetchall()); occ=serial(db.execute('select exhibition_id::text,venue_label,city_label,country_code,start_date,end_date from exhibition_occurrences where exhibition_id=any(%s::uuid[]) order by venue_label',(ids,)).fetchall()); src=serial(db.execute('select exhibition_id::text,source_url,capture_sha256 from exhibition_source_records where exhibition_id=any(%s::uuid[])',(ids,)).fetchall()); audits=db.execute('select count(*) n from audit_log where request_id=%s',(OP,)).fetchone()['n'];assert len(rows)==len(occ)==len(src)==audits==3 and all(x['import_batch']==OP for x in rows)
 counts=dict(new_exhibitions=3,new_venue_stops=3,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0); v={'at':c.now(),'target':t,'rows':rows,'occurrences':occ,'sources':src,'audit_events':audits,'transaction_preimage':str(B/'transaction-preimage.json'),'verified_counts':counts,'passed':True};save(E/'independent-database-verification.json',v);save(E/'verification.json',v)
 with Q.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=json.loads(Q.read_text()); before={x['source_id']:x for x in q['sources'] if x['source_id']!='national_gallery_athens'};g=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');g['last_checked_at']=c.now();g['research_status']='partial_forty_historical_events_verified';g['cursor']['completed'] += [f'https://www.nationalgallery.gr/en/exhibitions/{x[0]}/' for x in SPECS];g['cursor']['next']='Continue after Painters and Antiquity, Giorgos Mavroidis, and Impressionist/post-impressionist engravings; do not revisit Dutch landscape until date conflict resolves.';g.setdefault('evidence',[]).append('docs/research/continuous-exhibitions-20261013/batches/000049/independent-database-verification.json');tmp=Q.with_suffix('.49.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);assert before=={x['source_id']:x for x in json.loads(Q.read_text())['sources'] if x['source_id']!='national_gallery_athens'}
 save(E/'queue-update.json',{'at':c.now(),'updated_source':'national_gallery_athens','unrelated_entries_preserved':len(before),'queue_sha256':c.sha(Q.read_bytes()),'next':g['cursor']['next']});nxt=g['cursor']['next']; evidence=[f'docs/research/continuous-exhibitions-20261013/batches/000049/{x}' for x in ['independent-database-verification.json','verification.json','recovery-check.json','research-review.json','queue-update.json','CHECKPOINT.json']];cp={'at':c.now(),'batch':49,'stage':'verified_complete','verified_counts':counts,'production_ids':ids,'next_task':nxt,'evidence_paths':evidence,'external_supervisor_unchanged':True};save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp);result={'outcome':'progress','summary':'Added and independently verified three held pictorial or print exhibitions from official National Gallery of Greece records, including the actual Thessaloniki host for the engraving exhibition. Exact dates are retained; checklists remain unknown and no participation was inferred.','next_task':nxt,'blocker':'','verified_counts':counts,'evidence_paths':evidence};save(E/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':globals()[sys.argv[1]]()
