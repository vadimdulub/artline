#!/usr/bin/env python3
"""One bounded NGV historical exhibition batch; no supervisor changes."""
import fcntl
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000152'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000152'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000152'
Q=E.parents[1]/'source-queue.json'
OP='continuous-exhibitions-20261013-batch-000152'
ACTOR='local-european-research'
MID='10f88aa8-da2e-58a1-99f1-dc7c360f55b7'
INSTANCE='artline-508319:europe-west1:artline-postgres'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
SPECS=[
 ('Albrect Dürer: Engraving and Woodcuts','27 Oct – 12 Dec 76','1976-10-27','1976-12-12','Albrecht Dürer','1e6dc7e2-7c1d-4ec6-b3a6-25c05bfe4a93','Albrect Dürer','prints'),
 ('Rembrandt Etchings','9 Feb – 9 Apr 78','1978-02-09','1978-04-09','Rembrandt van Rijn','a08fbe07-1cb4-4423-b9e5-a17529eb64d9','Rembrandt','prints'),
 ('William Blake (1757-1827): Watercolours and Prints from the Permanent Collection','15 Dec 83 – 19 Feb 84','1983-12-15','1984-02-19','William Blake','de003eac-51c4-4057-bec5-4870d243b1b2','William Blake','watercolours and prints'),
 ('Albrect Durer (1471 – 1528): Engravings from the Permanent Collection','9 Mar – 13 May 84','1984-03-09','1984-05-13','Albrecht Dürer','1e6dc7e2-7c1d-4ec6-b3a6-25c05bfe4a93','Albrect Durer','prints'),
 ('George Baldessin Etchings','20 Aug – 18 Dec 88','1988-08-20','1988-12-18','George Baldessin','037e33f8-74fd-5145-9ae8-e7fe65aa76d8','George Baldessin','prints'),
]

def serial(x):return json.loads(json.dumps(x,ensure_ascii=False,default=str))
def save(n,x):c.save(E/n,x)
def target(db):
 cmd='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth '+INSTANCE
 assert cmd in [x.strip() for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
 assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
 r=db.execute('select current_database() database,current_user role').fetchone()
 assert r==dict(database='artline',role='artline_app')
 return dict(instance=INSTANCE,host=db.info.host,port=db.info.port,**r,checked_at=c.now())

def preserved(db):
 ids=sorted({x[5] for x in SPECS})
 return serial(dict(artists=db.execute('select * from artists where id=any(%s::uuid[]) order by id',(ids,)).fetchall(),
  institution=db.execute('select * from institutions where id=%s',(MID,)).fetchone()))

def collisions(db,e):
 return serial(db.execute("""select distinct e.id,e.title,e.start_year,e.end_year,e.import_batch
 from exhibitions e left join exhibition_source_records s on s.exhibition_id=e.id
 where e.id=%s or (s.source_key='ngv-official-exhibition-archive' and s.source_record_id=%s)
 or ((e.normalized_title=%s or e.alternate_titles ? %s) and (e.start_year is null or e.start_year=%s))""",
 (e['id'],e['row_locator'],c.norm(e['title']),e['title'],int(e['start'][:4]))).fetchall())

def snapshot(db,p):
 ids=[x['id'] for x in p['events']];out={}
 for t in ['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries']:
  col='id' if t=='exhibitions' else 'exhibition_id'
  out[t]=serial(db.execute('select * from '+t+' where '+col+'=any(%s::uuid[]) order by id',(ids,)).fetchall())
 out['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
 return out

def prepare():
 a=c.load(E/'ngv-archive-capture.json');rc=a['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
 assert c.sha(raw)==rc['sha256'] and rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');assert 'page-id-266303' in sp.body['class']
 events=[]
 for title,dates,start,end,name,aid,label,medium in SPECS:
  nodes=sp.find_all(string=title);assert len(nodes)==1,(title,len(nodes))
  node=nodes[0].parent.parent;date_text=''
  for sib in node.next_siblings:
   if getattr(sib,'name',None)=='br':break
   date_text+=str(sib)
  assert date_text.strip().lstrip(',').strip()==dates,(title,date_text)
  locator='266303/row-sha256/'+c.sha((title+'|'+dates).encode())
  key='ngv/exhibition-archive/'+start+'/'+c.norm(title)
  events.append(dict(id=c.uid(key),sid=c.uid(key+'/source'),oid=c.uid(key+'/venue'),pid=c.uid(key+'/artist'),
   title=title,source_date_text=dates,start=start,end=end,artist_id=aid,artist_name=name,name_label=label,medium=medium,
   row_locator=locator,source_page_native_id='266303',source_event_native_id=None,
   row_locator_is_local_not_provider_native=True,source_row=title+', '+dates))
 with c.connect() as db:
  t=target(db);old=preserved(db)
  assert len(old['artists'])==4 and old['institution']['name']=='National Gallery of Victoria'
  for e in events:
   ar=next(x for x in old['artists'] if x['id']==e['artist_id']);assert ar['display_name']==e['artist_name']
   assert ar['death_year']<int(e['start'][:4])
   assert not collisions(db,e),'Concurrent or existing event requires replan'
  assert not any(snapshot(db,dict(events=events)).values())
 review=dict(at=c.now(),selected_events=5,source_registry_id='ngv',source_type='official museum retrospective exhibition archive',
  source_archive_warning='NGV states this evolving archive may be refined and recommends verifying key information against primary documents. Dates retained as archive assertions in review; original catalogues/checklists remain uninspected.',
  title_typography='Original Albrect spellings and punctuation retained; established Albrecht Dürer creator identity reused with the two source labels explicit.',
  duplicate_decisions='Broad title/date/source/venue/tour search found no selected events. Existing Modern Masters 1975, Poetical Circle 1979 and Picasso 1984 NGV tour stops remain untouched. Dürer 1976 and 1984 are distinct dated exhibitions.',
  participation_basis='Each selected exhibition title explicitly identifies its exhibited artist and pictorial medium. All four creators died before the events; links mean exhibited works, not personal attendance.',
  venue_basis='Official NGV exhibition archive and existing NGV institutional identity; Melbourne, Australia confirmed by registry. Generic NGV venue retained; no exact historical room asserted.',
  checklist_state='unknown',original_checklists_viewed=0,objects_selected=0,images_selected=0,visual_review_claimed=False,
  holds=[dict(key='ngv-icons-1976-mixed-media',title='European Cribs, Icons and Paintings: Voluntary Guides Christmas Exhibition',source_period='14 Dec 76 – 7 Jan 77',reason='Cribs indicate possible excluded three-dimensional material; no event imported before a pictorial-scope/checklist review.'),
   dict(key='ngv-hockney1976-tour',url='https://www.ngv.vic.gov.au/exhibition/david-hockney-prints/',reason='Official linked event page identifies a 1976–1978 tour with fourteen additional stops. Retained as one shared-tour lead, not fifteen counted exhibitions; full venue/date-precision reconciliation is next.'),
   dict(key='selected-checklists',reason='No original checklists or exact exhibited versions reviewed. Named artists do not justify individual object or image links.'),
   dict(key='archive-date-verification',reason='Exact days are explicit official archive assertions; original contemporary documents remain a corroboration gap.')],passed=True)
 p=dict(at=c.now(),operation=OP,target=t,receipt=rc,events=events,preserved_entities=old,review=review,
  scope='Historical exhibitions 1600–1989; paintings/drawings/prints/icons. No main catalogue works created; through-1970 main-work rule remains unchanged.')
 save('plan.json',p);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);c.save(B/'plan.json',p)
 pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(sha256=pin,operation=OP))
 save('candidate-review-verification.json',review)
 save('source-capture-verification.json',dict(at=c.now(),plan_sha256=pin,receipt=rc,source_page_native_id='266303',
  source_events=[dict(title=e['title'],row=e['source_row'],local_locator=e['row_locator']) for e in events],
  original_capture_outside_Documents=True,sha256_verified=True,passed=True))
 print('Prepared',len(events),'events; plan',pin)

def audit(db,table,typ,ident,pin):
 row=serial(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
 db.execute("""insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)
 values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)""",(ACTOR,typ,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))

def apply():
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert p['operation']==OP
 assert c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())==pin
 with c.connect(write=True) as db:
  t=target(db)
  db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
  db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('select pg_advisory_xact_lock(2026101201)')
  before=snapshot(db,p)
  if before['exhibitions']:
   assert len(before['exhibitions'])==5 and (B/'transaction-preimage.json').exists()
   assert all(x['import_batch']==OP for x in before['exhibitions'])
   assert all(x['interpretation']['plan_sha256']==pin for x in before['exhibition_source_records'])
   print('Prior own transaction found; no replay. Run independent verification.');return
  assert not any(before.values())
  assert preserved(db)==p['preserved_entities']
  for e in p['events']:assert not collisions(db,e)
  pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=preserved(db),locks=['artline-curated-ingestion',2026101201])
  c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre)
  save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
  for e in p['events']:
   rc=p['receipt'];display=e['start']+' – '+e['end']
   ev=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],source_url=rc['url'],capture_sha256=rc['sha256'],
    source_row=e['source_row'],source_page_native_id='266303',source_event_native_id=None,local_row_locator=e['row_locator'],
    source_date_precision='day',source_authority='NGV official retrospective archive; original contemporary documents not inspected',
    checklist_complete=False,exact_objects_unknown=True,organizer_unknown=True,exact_historical_room_unknown=True,
    no_ownership_or_current_display_claim=True,medium=e['medium'],exhibition_type_label='temporary exhibition',
    collection_display_explicit='Permanent Collection' in e['title'],posthumous=True,
    participation_basis='Explicit artist and pictorial medium in the dated exhibition title; exhibited works rather than personal attendance.')
   db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,
    date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,'day','held',%s,'physical','unknown','review',%s)""",
    (e['id'],e['title'],c.norm(e['title']),Jsonb([]),e['start'],e['end'],int(e['start'][:4]),int(e['end'][:4]),display,
     'Retrospective official NGV exhibition archive explicitly lists this dated past exhibition. Assessed '+p['at']+'. Original contemporary checklist remains uninspected.',OP))
   db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,
    capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,'ngv-official-exhibition-archive',%s,%s,%s,%s,%s,%s,%s)""",
    (e['sid'],e['id'],e['row_locator'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],
     Jsonb(dict(event=e,receipt=rc,archive_warning=p['review']['source_archive_warning'])),Jsonb(ev)))
   db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,
    country_label,country_code,start_date,end_date,date_display,evidence) values(%s,%s,%s,%s,'National Gallery of Victoria','Melbourne','Australia','AU',%s,%s,%s,%s)""",
    (e['oid'],e['id'],e['sid'],MID,e['start'],e['end'],display,Jsonb(ev)))
   db.execute("""insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)
    values(%s,%s,%s,%s,%s,'artist',%s)""",(e['pid'],e['id'],e['sid'],e['artist_id'],e['name_label'],Jsonb(ev)))
   for table,typ,key in [('exhibitions','exhibition','id'),('exhibition_source_records','exhibition_source_record','sid'),('exhibition_occurrences','exhibition_occurrence','oid'),('exhibition_participants','exhibition_participant','pid')]:audit(db,table,typ,e[key],pin)
  assert preserved(db)==p['preserved_entities']
  c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db,p)))
 save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,verification_pending=True))
 print('Transaction completed; independently verify before reporting counts.')

def verify():
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
 assert c.sha((E/'plan.json').read_bytes())==pin==pre['plan_sha256'] and not any(pre['rows'].values())
 with c.connect() as db:
  db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db,p)
  assert preserved(db)==p['preserved_entities']
  for table,n in dict(exhibitions=5,exhibition_source_records=5,exhibition_occurrences=5,exhibition_participants=5,exhibition_entries=0).items():assert len(rows[table])==n
  audits=[x for x in rows['audits'] if x['action']=='continuous_exhibition_insert'];assert len(audits)==20
  assert all(x['before_json'] is None and x['after_json']['plan_sha256']==pin for x in audits)
  for e in p['events']:
   ex=next(x for x in rows['exhibitions'] if x['id']==e['id'])
   assert (ex['title'],ex['start_date'],ex['end_date'],ex['status'],ex['event_state'],ex['checklist_state'],ex['import_batch'])==(e['title'],e['start'],e['end'],'review','held','unknown',OP)
   sr=next(x for x in rows['exhibition_source_records'] if x['id']==e['sid'])
   assert (sr['exhibition_id'],sr['source_record_id'],sr['source_url'],sr['capture_sha256'])==(e['id'],e['row_locator'],p['receipt']['url'],p['receipt']['sha256'])
   assert sr['interpretation']['operation']==OP and sr['interpretation']['plan_sha256']==pin
   oc=next(x for x in rows['exhibition_occurrences'] if x['id']==e['oid'])
   assert (oc['exhibition_id'],oc['source_record_id'],oc['institution_id'],oc['start_date'],oc['end_date'])==(e['id'],e['sid'],MID,e['start'],e['end'])
   pa=next(x for x in rows['exhibition_participants'] if x['id']==e['pid'])
   assert (pa['exhibition_id'],pa['source_record_id'],pa['artist_id'],pa['name_label'],pa['role'])==(e['id'],e['sid'],e['artist_id'],e['name_label'],'artist')
   for row in [oc,pa]:assert row['evidence']['operation']==OP and row['evidence']['plan_sha256']==pin and row['evidence']['posthumous'] is True
 counts=dict(new_exhibitions=5,new_venue_stops=5,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=5,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
 save('independent-database-verification.json',dict(at=c.now(),target=t,operation=OP,plan_sha256=pin,rows=rows,verified_counts=counts,
  attribution='All counted rows absent in the shared-lock preimage. Source and relationship checksums match this immutable plan. New read-only transaction verifies each relationship and preserves existing creators/institution. Other jobs and prior campaigns excluded.',passed=True))
 public=[]
 for e in p['events']:
  u=API+'exhibitions/'+e['id'];r=requests.get(u,timeout=(15,45));r.raise_for_status();j=r.json()
  assert (j['id'],j['title'],j['startYear'],j['endYear'],j['entryCount'])==(e['id'],e['title'],int(e['start'][:4]),int(e['end'][:4]),0)
  assert len(j['venues'])==1 and len(j['participants'])==1
  assert j['participants'][0]['artist_id']==e['artist_id']
  assert j['venues'][0]['institution_id']==MID
  c.save(R/('public-'+e['id']+'.json'),j)
  public.append(dict(url=u,status=r.status_code,sha256=c.sha(r.content),exhibition_id=e['id'],venues=j['venues'],participants=j['participants'],passed=True))
 save('independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=public,passed=True))
 assert c.sha((B/'plan.json').read_bytes())==pin and c.sha((B/'transaction-preimage.json').read_bytes())==c.sha((E/'transaction-preimage.json').read_bytes())
 assert c.load(B/'transaction-postimage.json')['rows']==rows
 save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']],preimage_absent_rows=True,postimage_matches_fresh_read=True,passed=True))
 print(json.dumps(counts))

def finalize():
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];v=c.load(E/'independent-database-verification.json')
 assert v['passed'] and c.load(E/'independent-public-verification.json')['passed'] and c.load(E/'backup-verification.json')['passed']
 cp=c.load(E.parents[1]/'CHECKPOINT.json');startup=c.load(E/'startup-verification.json');assert cp['inflight']['batch']==152
 for k in ['supervisor_pid','worker_pid']:
  assert cp[k]==startup[k];os.kill(cp[k],0)
 for f in startup['protected_files']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
 commands=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
 workers=[x for x in commands if '/opt/homebrew/bin/codex exec ' in x and '--output-schema /Users/vadimdulub/Library/Application Support/Artline/continuous-exhibition-research/schema.json' in x]
 assert len(workers)==1 and int(workers[0].split()[0])==cp['worker_pid'] and int(workers[0].split()[1])==cp['supervisor_pid']
 lockpath=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/supervisor.lock'
 holders=subprocess.check_output(['lsof','-a','-p',str(cp['supervisor_pid'])+','+str(cp['worker_pid']),str(lockpath)],text=True)
 assert all(str(cp[k]) in holders for k in ['supervisor_pid','worker_pid'])
 if not (E/'continuation-process-verification.json').exists():
  save('continuation-process-verification.json',dict(at=c.now(),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],
   supervisor_and_worker_running=True,single_exhibition_worker=True,inherited_singleton_lock_open=True,
   supervisor_script_schema_and_registry_unchanged=True,other_programme_mutations_performed=0,new_supervisor_started=False,passed=True))
 else:
  prior=c.load(E/'continuation-process-verification.json')
  assert prior['passed'] and prior['supervisor_pid']==cp['supervisor_pid'] and prior['worker_pid']==cp['worker_pid']
 nxt='Reconcile the captured NGV David Hockney Prints 1976–1978 tour as one event with fifteen venue stops; preserve month precision, source venue spellings and lender/host distinctions. Resolve institutions and tour duplicates before import. Moralis and Cleveland image cursors remain unchanged.'
 rel=lambda n:str((E/n).relative_to(ROOT))
 with Q.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);before=c.load(Q);q=serial(before);before_sha=c.sha(Q.read_bytes())
  g=next(x for x in q['sources'] if x['source_id']=='ngv')
  g['last_checked_at']=c.now();g['research_status']='batch152_five_historical_pictorial_events_verified'
  if g.get('cursor') is None:g['cursor']={}
  g['cursor']['batch152']=dict(archive_url=p['receipt']['url'],source_page_native_id='266303',capture_sha256=p['receipt']['sha256'],
   completed_rows=[dict(title=e['title'],source_period=e['source_date_text'],local_row_locator=e['row_locator'],exhibition_id=e['id']) for e in p['events']],
   delivered_events=5,delivered_venue_stops=5,delivered_artist_links=5,complete_checklists=0,
   next_url='https://www.ngv.vic.gov.au/exhibition/david-hockney-prints/',next=nxt)
  g.setdefault('holds',[]).extend([dict(**x,evidence=rel('candidate-review-verification.json')) for x in p['review']['holds']])
  g.setdefault('evidence',[]).extend([rel(n) for n in ['source-capture-verification.json','candidate-review-verification.json','hockney-tour-lead-verification.json','independent-database-verification.json','independent-public-verification.json']])
  assert before['supplemental_sources']==q['supplemental_sources']
  assert [x for x in before['sources'] if x['source_id']!='ngv']==[x for x in q['sources'] if x['source_id']!='ngv']
  c.save(B/'source-queue-before.json',before)
  tmp=Q.with_suffix('.batch152.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);assert c.load(Q)==q
 save('queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),updated_sources=['ngv'],
  all_unrelated_sources_supplemental_sources_and_registry_preserved=True,moralis_and_cleveland_cursors_preserved=True,next_task=nxt,passed=True))
 checkpoint=dict(at=c.now(),batch=152,stage='verified_complete',plan_sha256=pin,discovered_selected_events=5,prepared_events=5,
  imported_events=5,independently_verified_events=5,verified_counts=v['verified_counts'],production_ids=[e['id'] for e in p['events']],
  research_only_leads=['European Cribs, Icons and Paintings 1976–1977','David Hockney Prints shared tour 1976–1978'],
  next_task=nxt,external_supervisor_owns_continuation=True)
 save('CHECKPOINT.json',checkpoint);c.save(R/'batch-checkpoint.json',checkpoint)
 names=['source-capture-verification.json','candidate-review-verification.json','independent-database-verification.json',
  'independent-public-verification.json','backup-verification.json','hockney-tour-lead-verification.json','continuation-process-verification.json',
  'queue-update-verification.json','CHECKPOINT.json','final-verification.json']
 result=dict(outcome='progress',summary='Verified five historical NGV exhibitions, five venue stops and five artist participation links, reusing four artists. All remain in review with unknown checklists. No artworks or images added.',next_task=nxt,blocker='',verified_counts=v['verified_counts'],evidence_paths=[rel(n) for n in names])
 save('final-verification.json',dict(**result,at=c.now(),plan_sha256=pin,passed=True));save('worker-result.json',result)
 report='''# Batch 152 — NGV historical exhibition archive\n\nFive distinct dated historical exhibitions, five NGV venue stops and five artist participation links were added and independently verified in production and the public API. Four existing artists and the existing NGV institution were reused. No main-catalogue works, documentary entries, exact artwork links or images were added; no existing catalogue rows were rewritten.\n\n| Source title | Exhibition dates | Existing artist |\n|---|---|---|\n'''
 for e in p['events']:report+='| '+e['title']+' | '+e['start']+' – '+e['end']+' | '+e['artist_name']+' |\n'
 report+='\nEvidence: [NGV official archive]('+p['receipt']['url']+'). The original archive spelling “Albrect” is retained. These are posthumous presentations of artists’ works, not personal attendance. Original checklists are uninspected and completeness is unknown. The archive warns its dates may be refined; all additions remain in review. No individual object participation, ownership or current display is inferred.\n\nThe mixed cribs/icons/paintings show is held for medium review. The captured Hockney itinerary is a single 1976–1978 touring-exhibition lead with fifteen stops, awaiting venue reconciliation; it was not imported. Existing NGV stops in prior tours were excluded from new counts.\n\nThe immutable plan, shared-lock absent-row preimage, per-row audit entries, persisted plan checksums, fresh read-only database verification and public relationship checks establish attribution to this batch. Recovery files are outside Documents under Application Support/Artline/backups/continuous-exhibitions-20261013/000152. Only the NGV queue route changed. The existing external supervisor and inherited singleton lock were verified; no additional worker or supervisor was launched.\n'
 path=E/'README.md';assert not path.exists();path.write_text(report)
 print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify','finalize']
 globals()[sys.argv[1]]()
