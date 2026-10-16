"""Batch 78: resolve Cleveland object 123355 and its documented 1989 entry."""
import fcntl, gzip, json, os, subprocess, sys, uuid
from pathlib import Path
import requests
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'ops'))
import exhibitions_common as c
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000078'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000078'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000078'
Q=E.parents[1]/'source-queue.json';OP='continuous-exhibitions-20261013-batch-000078';ACTOR='local-european-research'
ENTRY='00dc2fda-baa9-5f66-9981-391f243de9bd';EVENT='717615f4-9c2a-5999-a948-79b44711ed5e'
WORK=c.uid(OP+'/artwork/cleveland/123355');SOURCE=c.uid(OP+'/source/'+ENTRY)
IID='729385eb-92b0-4cc8-9229-1ac3a46aee1f';SOURCE_ID='aa0ba48c-e786-4cac-8411-06343f4f03ed'
ARTISTS=[('420753e2-43d2-4798-abc1-48f809a6d55d','Herman Naiwincx','22522')]
URL='https://openaccess-api.clevelandart.org/api/artworks/123355';API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'
serial=lambda x:json.loads(json.dumps(x,default=str))
def save(name,x):c.save(E/name,x)
def target(db):
 ps=subprocess.check_output(['ps','-axo','command'],text=True);assert any('cloud-sql-proxy' in x and 'artline-508319:europe-west1:artline-postgres' in x for x in ps.splitlines())
 assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline');return dict(instance='artline-508319:europe-west1:artline-postgres',host=db.info.host,port=db.info.port,database=db.info.dbname)
def state(db):
 return serial(dict(entry=db.execute('select * from exhibition_entries where id=%s',(ENTRY,)).fetchone(),event=db.execute('select * from exhibitions where id=%s',(EVENT,)).fetchone(),work=db.execute('select * from artworks where id=%s',(WORK,)).fetchone(),source=db.execute('select * from exhibition_source_records where id=%s',(SOURCE,)).fetchone(),participants=db.execute('select * from exhibition_participants where id=any(%s::uuid[]) order by id',([c.uid(OP+'/participant/'+x[0]) for x in ARTISTS],)).fetchall(),artists=db.execute('select * from artists where id=any(%s::uuid[]) order by id',([x[0] for x in ARTISTS],)).fetchall()))
def startup():
 E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True)
 if (E/'startup-recovery-verification.json').exists():
  old=c.load(E/'startup-recovery-verification.json');assert old['passed'] and old['no_prior_attributable_write'];return
 cp=c.load(E.parents[1]/'CHECKPOINT.json');assert cp['next_batch']==78
 with c.connect() as db:s=state(db);t=target(db);aud=serial(db.execute('select * from audit_log where request_id=%s',(OP,)).fetchall())
 save('startup-recovery-verification.json',dict(at=c.now(),target=t,prior_state=s,prior_audits=aud,no_prior_attributable_write=not s['work'] and not s['source'] and not s['participants'] and not aud,entry_still_unlinked=bool(s['entry'] and s['entry']['artwork_id'] is None),concurrent_smk_changes_attributed=0,inherited_descriptors_preserved=True,passed=True))
 assert not s['work'] and not s['source'] and not s['participants'] and not aud and s['entry']['artwork_id'] is None
 save('input-policy-verification.json',dict(at=c.now(),scope='exhibitions1600-1989; pictorial prints eligible; main artworks through1970',translation_calls=0,local_catalogue_writes=0,supervisor_changes=0))
def prepare():
 if (E/'plan.json').exists():
  assert c.sha((E/'plan.json').read_bytes())==c.load(E/'plan-pin.json')['sha256'];return
 r=requests.get(URL,headers={'User-Agent':'Artline exhibition history research; bounded metadata retrieval'},timeout=(15,45));r.raise_for_status();raw=r.content;d=r.json()['data'];body=R/'cleveland-123355.json';body.write_bytes(raw)
 rc=dict(url=URL,final_url=r.url,status=r.status_code,retrieved_at=c.now(),sha256=c.sha(raw),bytes=len(raw),content_type=r.headers.get('content-type'),body_path=str(body))
 assert d['id']==123355 and d['accession_number']=='1943.593' and d['title']=='Etchings by Herman Naiwincx' and d['type']=='Print' and d['creation_date_earliest']==1640 and d['creation_date_latest']==1651
 assert [(x['description'].split(' (')[0],x['role'],str(x['id'])) for x in d['creators']]==[('Herman Naiwincx','artist','22522'),('Clement de Jonghe','publisher','439179')]
 assert any(x['id']==310281 and x['title']=='Northern Landscape Traditions: 16th and 17th Century Prints and Drawings' for x in d['exhibitions']['current'])
 with c.connect() as db:
  pre=state(db);assert pre['entry']['source_artwork_id']=='123355' and pre['entry']['exhibition_id']==EVENT and pre['event']['start_year']==1989 and pre['event']['status']!='archived'
  assert [(x['id'],x['display_name']) for x in pre['artists']]==[(ARTISTS[0][0],ARTISTS[0][1])]
  collisions=serial(db.execute("select id::text,title,current_institution_id::text from artworks where accession_number='1943.593' or normalized_title=%s",(c.norm(d['title']),)).fetchall())
  assert len(collisions)==1 and collisions[0]['title']=='Garden on Debris' and collisions[0]['current_institution_id']!=IID
  native=serial(db.execute("select * from external_identifiers where entity_type='artwork' and scheme ilike '%%cleveland%%' and external_id='123355'").fetchall());assert not native
 p=dict(at=c.now(),operation=OP,target=dict(instance='artline-508319:europe-west1:artline-postgres'),entry_id=ENTRY,event_id=EVENT,work_id=WORK,source_id=SOURCE,source=rc,object=d,preimage=pre,collisions=collisions,participants=[dict(id=c.uid(OP+'/participant/'+aid),artist_id=aid,name=name,native_person=native) for aid,name,native in ARTISTS],basis='Official Cleveland native object 123355 and accession 1943.593 explicitly identify the exact accessioned print object in exhibition 282356. Same-number accession collision belongs to another institution and title. Naiwincx is the unqualified artist; Clement de Jonghe is preserved as publisher, not converted into artist participation. Checklist remains partial.')
 c.save(E/'plan.json',p);c.save(B/'plan.json',p);pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(sha256=pin,backup=str(B/'plan.json')))
 save('source-capture-verification.json',dict(at=c.now(),receipt=rc,native_object=123355,accession='1943.593',native_exhibition=282356,creators=d['creators'],checksum_verified=c.sha(body.read_bytes())==rc['sha256'],passed=True))
 save('research-review.json',dict(at=c.now(),selected_entries=1,prepared_main_works=1,prepared_exact_links=1,prepared_artist_participation_links=1,complete_checklists=0,holds=[dict(key='accession-collision',reason='Same accession string on unrelated artwork Garden on Debris is institution-scoped and not reused.'),dict(key='creator-lifespans',reason='Museum and existing authority life dates differ; authority dates are preserved unchanged.'),dict(key='publisher-role',reason='Clement de Jonghe is explicitly publisher, not converted into an artist participant.')],images=0))
def audit(db,kind,id,before,after,pin):db.execute('insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,%s,%s,%s,%s,%s,%s)',(ACTOR,'continuous_exhibition_batch78_enrichment',kind,id,OP,Jsonb(before),Jsonb(dict(record=after,plan_sha256=pin))))
def apply():
 if (E/'applied.json').exists():return
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert c.sha((E/'plan.json').read_bytes())==pin and p==c.load(B/'plan.json');assert c.sha(Path(p['source']['body_path']).read_bytes())==p['source']['sha256']
 with c.connect(write=True) as db:
  db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
  cur=state(db)
  if cur!=p['preimage']:assert cur['work'] and cur['entry']['artwork_id']==WORK;print('REPLAY');return
  assert not db.execute('select 1 from audit_log where request_id=%s',(OP,)).fetchone();pre=dict(at=c.now(),target=target(db),plan_sha256=pin,rows=cur,locks=['artline-curated-ingestion',2026101201]);c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre)
  d=p['object'];rc=p['source'];ev=dict(operation=OP,plan_sha256=pin,source_sha256=rc['sha256'],native_object='123355',accession='1943.593',checklist_complete=False,current_display_claim=False)
  db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(SOURCE,EVENT,'cleveland-official-object',OP+'/'+EVENT+'/123355',URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(d),Jsonb(ev)))
  db.execute("insert into artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,accession_number,status,research_candidate,current_institution_id,created_by,updated_by)values(%s,%s,%s,%s,%s,1640,1651,'range','print',%s,%s,'review',true,%s,%s,%s)",(WORK,'cleveland-print-123355-batch78',d['title'],c.norm(d['title']),d['creation_date'],d['technique'],d['accession_number'],IID,ACTOR,ACTOR))
  for aid,name,native in ARTISTS:db.execute("insert into artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)values(%s,%s,'primary',%s)",(WORK,aid,'Official Cleveland unqualified creator '+native+'; source wording retained'))
  db.execute("insert into external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)values('artwork',%s,'cleveland-object','123355',%s,%s,%s)",(WORK,d['url'],SOURCE_ID,rc['retrieved_at']))
  db.execute("insert into citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)values('artwork',%s,'continuous_exhibition_native_identity',%s,'123355',%s,%s,%s,%s)",(WORK,SOURCE_ID,URL,json.dumps(ev),rc['retrieved_at'],ACTOR))
  db.execute("insert into artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)values(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(WORK,IID,SOURCE_ID,URL,json.dumps(ev),p['at']))
  old=cur['entry'];db.execute('update exhibition_entries set artwork_id=%s,creator_label=%s,match_basis=%s,evidence=evidence||%s where id=%s and artwork_id is null',(WORK,'Herman Naiwincx',p['basis'],Jsonb(dict(batch78_review=ev,publisher_label='Clement de Jonghe')),ENTRY));audit(db,'exhibition_entry',ENTRY,old,serial(db.execute('select * from exhibition_entries where id=%s',(ENTRY,)).fetchone()),pin);audit(db,'artwork',WORK,None,serial(db.execute('select * from artworks where id=%s',(WORK,)).fetchone()),pin)
  for n in p['participants']:
   evidence=dict(operation=OP,plan_sha256=pin,source_sha256=rc['sha256'],supporting_entry=ENTRY,native_object='123355',native_person=n['native_person'],historical_participation_only=True,checklist_complete=False)
   assert not db.execute('select 1 from exhibition_participants where exhibition_id=%s and artist_id=%s',(EVENT,n['artist_id'])).fetchone()
   db.execute("insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence)values(%s,%s,%s,%s,%s,'artist',%s,%s)",(n['id'],EVENT,SOURCE,n['artist_id'],n['name'],n['native_person'],Jsonb(evidence)));audit(db,'exhibition_participant',n['id'],None,serial(db.execute('select * from exhibition_participants where id=%s',(n['id'],)).fetchone()),pin)
 c.save(E/'applied.json',dict(at=c.now(),plan_sha256=pin,committed=True))
def verify():
 p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=1,new_documentary_entries=0,new_artist_participation_links=1,new_exact_artwork_links=1,new_images=0,existing_records_enriched=1)
 with c.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');s=state(db);assert pre['rows']==p['preimage'] and s['entry']['artwork_id']==WORK and s['work']['status']=='review' and s['work']['creation_year_end']<=1970 and len(s['participants'])==1
  ids=serial(db.execute("select * from external_identifiers where entity_type='artwork' and entity_id=%s and scheme='cleveland-object'",(WORK,)).fetchall());assert len(ids)==1 and ids[0]['external_id']=='123355'
  audits=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall());assert len(audits)==3 and all(x['after_json']['plan_sha256']==pin for x in audits)
 if not (E/'independent-database-verification.json').exists():save('independent-database-verification.json',dict(at=c.now(),target=target_read(),plan_sha256=pin,preimage=pre,postimage=s,identifiers=ids,audits=audits,verified_counts=counts,attribution='Work, exact link and participants were absent in locked transaction preimage and are pinned to this programme source checksum/audits.',passed=True))
 res=requests.get(API+EVENT,timeout=(15,45));res.raise_for_status();detail=res.json();assert any(x['id']==n['id'] for n in p['participants'] for x in detail['participants'])
 res2=requests.get(API+EVENT+'/entries',params={'limit':100},timeout=(15,45));res2.raise_for_status();it=next(x for x in res2.json()['items'] if x['id']==ENTRY);assert it['artworkId']==WORK and it['creator']=='Herman Naiwincx'
 c.save(R/'public-event.json',detail);c.save(R/'public-entries.json',res2.json())
 if not (E/'public-verification.json').exists():save('public-verification.json',dict(at=c.now(),event_url=res.url,entries_url=res2.url,event_http=res.status_code,entries_http=res2.status_code,event_sha256=c.sha(res.content),entries_sha256=c.sha(res2.content),entry_id=ENTRY,work_id=WORK,participant_ids=[x['id'] for x in p['participants']],passed=True))
 finish(counts,pin)
def target_read():
 with c.connect() as db:return target(db)
def finish(counts,pin):
 nxt='Continue the saved Cleveland null-artwork queue after native 123355, selecting pictorial objects through 1970; exclude provider-ID and accession collisions unless institution, accession, title and version all agree. Preserve batch74 Gozzoli/Dore holds and Arthive HTTP429 hold.'
 paths=[f'docs/research/continuous-exhibitions-20261013/batches/000078/{x}' for x in ['independent-database-verification.json','public-verification.json','source-capture-verification.json','startup-recovery-verification.json','queue-update.json','CHECKPOINT.json']]
 with Q.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);before=c.load(Q);q=serial(before);route=next(x for x in q['sources'] if x['source_id']=='cleveland_museum');route['research_status']='batch78_native123355_exact_link_verified';route['cursor']['batch78']=dict(completed_native_object='123355',completed_entry=ENTRY,work_id=WORK,next=nxt);route['evidence'].extend(paths[:4]);save('source-queue-preimage.json',before);save('source-queue-postimage.json',q);tmp=Q.with_suffix('.batch78.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q);save('queue-update.json',dict(at=c.now(),updated_sources=['cleveland_museum'],unrelated_entries_preserved=True,next_task=nxt,passed=True))
 cp=dict(at=c.now(),batch=78,stage='verified_complete',plan_sha256=pin,verified_counts=counts,discovered=1,prepared=1,imported=1,verified=1,complete_checklists=0,next_task=nxt,external_supervisor_owns_continuation=True,evidence_paths=paths);save('CHECKPOINT.json',cp);c.save(R/'CHECKPOINT.json',cp)
 result=dict(outcome='progress',summary='Added and independently verified one review catalogue print and its exact participation link for Cleveland native object 123355, Etchings by Herman Naiwincx (1640–51), in Northern Landscape Traditions (1989), plus one supported artist participation link for Herman Naiwincx. Clement de Jonghe remains explicitly the publisher, not an artist participant. The checklist remains partial; a same-number accession collision at another institution was excluded.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=paths);save('result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 for f in (startup,prepare,apply,verify):f()
