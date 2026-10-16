#!/usr/bin/env python3
"""Batch 77: two bilingual National Gallery of Greece historical pictorial events."""
import fcntl,gzip,json,os,re,subprocess,sys,uuid
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'ops'))
import exhibitions_common as c
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000077'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000077'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000077'
Q=E.parents[1]/'source-queue.json';OP='continuous-exhibitions-20261013-batch-000077'
MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'
URLS={
'gate':[('en','https://www.nationalgallery.gr/en/exhibitions/gate-to-heaven/'),('el','https://www.nationalgallery.gr/ektheseis/mia-porta-ston-ourano/')],
'hermitage':[('en','https://www.nationalgallery.gr/en/exhibitions/hermitage-monuments-of-ancient-greek-art-from-the-black-sea-rembrandt-and-russian-painters-of-the-18th-and-19th-centuries/'),('el','https://www.nationalgallery.gr/ektheseis/mouseio-ermitaz-mnimeia-arhaias-ellinikhs-tehnis-apo-ton-euxeino-ponto-remprant-rosoi-zographoi-tou-18ou-kai-tou-19ou-aiona/')],}
META={
'gate':dict(title='Μια πόρτα στον ουρανό',alt='Gate to Heaven',start='1983-12-12',end=None,sy=1983,ey=None,precision='day',display='From 12 December 1983; closing date and year unknown',type='silkscreen/print exhibition'),
'hermitage':dict(title='Μουσείο Ερμιτάζ: Μνημεία αρχαίας ελληνικής τέχνης από τον Εύξεινο Πόντο, Ρέμπραντ, Ρώσοι ζωγράφοι του 18ου και του 19ου αιώνα',alt='Hermitage: Monuments of ancient Greek art from the Black Sea. Rembrandt and Russian painters of the 18th and 19th centuries',start='1989-04-20',end='1989-05-20',sy=1989,ey=1989,precision='day',display='20 April – 20 May 1989',type='painting and antiquities exhibition; only pictorial event-level scope retained')}
uid=lambda s:str(uuid.uuid5(uuid.UUID('facf6d82-e2ca-4a30-a7d8-035bf7f05954'),s))
ser=lambda x:json.loads(json.dumps(x,default=str))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);c.save(p,x)
def target(db):
 r=ser(db.execute('select current_database() db,inet_server_port() port,current_user usr').fetchone());assert r['db']=='artline';return r
def cap():
 out=[];S=requests.Session();S.headers['User-Agent']='ArtlineResearch/1.0'
 for key,pairs in URLS.items():
  for lang,url in pairs:
   r=S.get(url,timeout=(15,45));r.raise_for_status();raw=r.content;sp=BeautifulSoup(raw,'html.parser');main=sp.select_one('main');assert main
   text=' '.join(main.get_text(' ',strip=True).split());h=sp.find('h1').get_text(' ',strip=True)
   if key=='gate':assert '12.12.1983' in text and ('Silkscreens' in text if lang=='en' else 'Μεταξοτυπίες' in text)
   else:assert '20.04.1989' in text and '20.05.1989' in text
   p=R/'captures'/f'{key}-{lang}.html.gz';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(gzip.compress(raw))
   out.append(dict(key=key,lang=lang,url=url,status=r.status_code,retrieved_at=c.now(),sha256=c.sha(raw),bytes=len(raw),body_path=str(p),h1=h,text=text))
 return out
def startup():
 E.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True)
 cp=c.load(E.parents[1]/'CHECKPOINT.json');assert cp['inflight']['batch']==77
 ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True);assert str(cp['supervisor_pid']) in ps
 with c.connect() as db:
  t=target(db);own=ser(db.execute('select id::text,title from exhibitions where import_batch=%s',(OP,)).fetchall())
 save(E/'startup-recovery-verification.json',dict(at=c.now(),target=t,prior_attributable_rows=own,previous_batch=76,previous_increment_recounted=0,external_supervisor_pid=cp['supervisor_pid'],separate_artwork_programme_untouched=True,danish_changes_attributed=0,passed=True))
 inputs=[ROOT/'AGENTS.md',ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')]
 save(E/'input-policy-verification.json',dict(at=c.now(),inputs=[dict(path=str(p),sha256=c.sha(p.read_bytes())) for p in inputs],scope='1600-1989; photography/sculpture excluded; main artworks through1970; metadata-only event delivery',arthive_hold_reused_without_request=True))
def prepare():
 receipts=cap();events=[]
 with c.connect() as db:
  t=target(db);inst=ser(db.execute('select * from institutions where id=%s',(MID,)).fetchone());assert inst['slug']=='national-gallery-greece'
  for key,m in META.items():
   src=[x for x in receipts if x['key']==key];eid=uid(OP+'/'+key);oid=uid(OP+'/occ/'+key)
   dups=ser(db.execute("select distinct e.id::text,e.title,e.start_year,e.import_batch from exhibitions e left join exhibition_source_records s on s.exhibition_id=e.id where e.normalized_title=any(%s) or e.title=any(%s) or e.alternate_titles ?| %s or s.source_url=any(%s)",([c.norm(m['title']),c.norm(m['alt'])],[m['title'],m['alt']],[m['title'],m['alt']],[x['url'] for x in src])).fetchall())
   assert not [x for x in dups if x['start_year'] in (None,m['sy'])],(key,dups)
   events.append(dict(key=key,id=eid,oid=oid,sources=src,duplicates=dups,**m))
 plan=dict(at=c.now(),operation=OP,target=t,institution=inst,events=events,basis='Official bilingual National Gallery of Greece historical records explicitly support titles, pictorial media and dates at retained precision. Host taxonomy says central-building permanent collections; temporary/display subtype remains unresolved. No object checklist, lender, organizer, additional stop, holding or current-display inference.',holds=['Gate to Heaven closing date/year unknown','No object-level checklist inspected; checklist state unknown','Hermitage antiquities and pictorial components are not split into invented events','Arthive existing HTTP429 hold reused without request'])
 save(E/'plan.json',plan);save(B/'plan.json',plan);pin=c.sha((E/'plan.json').read_bytes());save(E/'plan-pin.json',dict(sha256=pin))
 save(E/'source-capture-verification.json',dict(at=c.now(),receipts=[dict(url=x['url'],sha256=x['sha256'],bytes=x['bytes'],retrieved_at=x['retrieved_at'],h1=x['h1'],passed=True) for x in receipts],plan_sha256=pin,passed=True))
 save(E/'research-review.json',dict(at=c.now(),discovered=2,prepared=2,imported=0,verified=0,complete_checklists=0,images_downloaded=0,holds=plan['holds']))
def rows(db,ids):
 return dict(events=ser(db.execute('select * from exhibitions where id=any(%s)',(ids,)).fetchall()),occurrences=ser(db.execute('select * from exhibition_occurrences where exhibition_id=any(%s)',(ids,)).fetchall()),sources=ser(db.execute('select * from exhibition_source_records where exhibition_id=any(%s)',(ids,)).fetchall()),entries=ser(db.execute('select * from exhibition_entries where exhibition_id=any(%s)',(ids,)).fetchall()),participants=ser(db.execute('select * from exhibition_participants where exhibition_id=any(%s)',(ids,)).fetchall()))
def apply():
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert c.sha((E/'plan.json').read_bytes())==pin and p==c.load(B/'plan.json');ids=[e['id'] for e in p['events']]
 with c.connect(write=True) as db:
  t=target(db);db.execute("select set_config('artline.actor_user_id','local-european-research',true)");db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
  before=rows(db,ids)
  if before['events']:assert len(before['events'])==2 and all(x['import_batch']==OP for x in before['events']);return
  assert not any(before.values());pre=dict(at=c.now(),target=t,plan_sha256=pin,rows=before,locks=['artline-curated-ingestion',2026101201]);save(E/'transaction-preimage.json',pre);save(B/'transaction-preimage.json',pre)
  for e in p['events']:
   ev=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],basis=p['basis'],type_label=e['type'],checklistComplete=False,individualObjectsUnknown=True)
   db.execute("insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','unknown','review',%s)",(e['id'],e['title'],c.norm(e['title']),Jsonb([e['alt']]),e['start'],e['end'],e['sy'],e['ey'],e['display'],e['precision'],p['basis']+' Assessed '+p['at'],OP))
   sids=[]
   for x in e['sources']:
    sid=uid(OP+'/source/'+e['key']+'/'+x['lang']);sids.append(sid);db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,e['id'],'national-gallery-greece-official',e['key']+'-'+x['lang'],x['url'],x['retrieved_at'],x['body_path'],x['sha256'],Jsonb(x),Jsonb(ev)))
   db.execute('insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],sids[1],MID,'National Gallery - Central Building','Athens','Greece','GR',e['start'],e['end'],e['display'],Jsonb(ev)))
   for kind,eid,table in [('exhibition',e['id'],'exhibitions'),('exhibition_occurrence',e['oid'],'exhibition_occurrences')]:
    rec=ser(db.execute('select * from '+table+' where id=%s',(eid,)).fetchone());db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values('local-european-research','continuous_exhibition_insert',%s,%s,%s,%s,%s)",(kind,eid,OP,Jsonb(None),Jsonb(dict(record=rec,plan_sha256=pin))))
  save(B/'transaction-postimage.json',dict(at=c.now(),rows=rows(db,ids),plan_sha256=pin))
 save(E/'applied.json',dict(at=c.now(),ids=ids,plan_sha256=pin))
def verify():
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');assert not any(pre['rows'].values());ids=[e['id'] for e in p['events']]
 with c.connect() as db:
  db.execute('set transaction isolation level repeatable read, read only');t=target(db);r=rows(db,ids);aud=ser(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall());assert len(r['events'])==len(r['occurrences'])==2 and len(r['sources'])==4 and not r['entries'] and not r['participants'] and len(aud)==4
  for e in p['events']:
   a=next(x for x in r['events'] if x['id']==e['id']);o=next(x for x in r['occurrences'] if x['exhibition_id']==e['id']);assert (a['start_date'],a['end_date'],a['status'],a['event_state'],a['checklist_state'],a['import_batch'])==(e['start'],e['end'],'review','held','unknown',OP);assert o['institution_id']==MID
 counts=dict(new_exhibitions=2,new_venue_stops=2,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
 save(E/'independent-database-verification.json',dict(at=c.now(),target=t,plan_sha256=pin,rows=r,audits=aud,verified_counts=counts,attribution='Rows absent in locked preimage and identified by this operation/plan; concurrent programmes excluded.',passed=True))
 pubs=[]
 for e in p['events']:
  z=requests.get(API+e['id'],timeout=(15,45));z.raise_for_status();d=z.json();assert d['title']==e['title'] and d['startYear']==e['sy'] and d['endYear']==e['ey'] and d['entryCount']==0 and not d['participants'] and len(d['venues'])==1;save(R/('public-'+e['id']+'.json'),d);pubs.append(dict(url=API+e['id'],status=z.status_code,sha256=c.sha(z.content),event_id=e['id'],passed=True))
 save(E/'public-verification.json',dict(at=c.now(),receipts=pubs,passed=True));finish(p,pin,counts)
def finish(p,pin,counts):
 nxt='Continue the official National Gallery of Greece archive with the next unreconciled pre-1990 pictorial record, or rotate to a Russian-icon/post-Byzantine primary archive. Preserve Gate to Heaven unknown closing year and do not replay these two event IDs. Arthive remains held at HTTP429.'
 paths=[str((E/x).relative_to(ROOT)) for x in ['independent-database-verification.json','public-verification.json','source-capture-verification.json','startup-recovery-verification.json','queue-update.json','CHECKPOINT.json']]
 with Q.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);before=c.load(Q);q=ser(before);g=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');a=next(x for x in q['supplemental_sources'] if x['source_id']=='arthive_exhibitions')
  for e in p['events']:
   u=e['sources'][0]['url']
   if u not in g['cursor']['completed']:g['cursor']['completed'].append(u)
  g.update(last_checked_at=c.now(),research_status='two_bilingual_historical_pictorial_events_verified_batch77');g['cursor']['batch77']=dict(completed_keys=[e['key'] for e in p['events']],event_ids=[e['id'] for e in p['events']],plan_sha256=pin,next=nxt);g['cursor']['next']=nxt;g.setdefault('evidence',[]).extend(paths[:4]);a['cursor']['batch77']=dict(hold_reused_without_request=True,next='Await changed HTTP429 state; use official archives');a['last_checked_at']=c.now()
  save(E/'source-queue-preimage.json',before);save(E/'source-queue-postimage.json',q);tmp=Q.with_suffix('.batch77.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);save(E/'queue-update.json',dict(at=c.now(),updated_sources=['national_gallery_athens','arthive_exhibitions'],unrelated_entries_preserved=True,before_sha256=c.sha((E/'source-queue-preimage.json').read_bytes()),after_sha256=c.sha(Q.read_bytes()),passed=True))
 cp=dict(at=c.now(),batch=77,stage='verified_complete',plan_sha256=pin,verified_counts=counts,discovered=2,prepared=2,imported=2,verified=2,complete_checklists=0,production_exhibition_ids=[e['id'] for e in p['events']],next_task=nxt,external_supervisor_owns_continuation=True,evidence_paths=paths);save(E/'CHECKPOINT.json',cp);save(R/'batch-checkpoint.json',cp)
 result=dict(outcome='progress',summary='Added and independently verified two bilingual historical National Gallery of Greece exhibitions and their Athens venue stops: Gate to Heaven (silkscreens, opening 12 December 1983; closing date unknown) and the Hermitage exhibition including Rembrandt and Russian painters (20 April–20 May 1989). Both remain review records with unknown/partial checklists; no object participation, organizer, lender or current-display claims were inferred.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=paths);save(E/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ['startup','prepare','apply','verify'];globals()[sys.argv[1]]()
