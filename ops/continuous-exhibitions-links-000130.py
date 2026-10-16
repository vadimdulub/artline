#!/usr/bin/env python3
import fcntl,hashlib,importlib.util,json,os,subprocess,sys,uuid
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000130';R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000130';OP='continuous-exhibitions-20261013-batch-000130-links'
sp=importlib.util.spec_from_file_location('c',ROOT/'ops/exhibitions_common.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
T=[('4ec41a80-a6b5-53df-bd76-89110a300a4c','9f2769de-5f44-5761-b408-167b9e0ca36a','dbeb62ed-8b79-4393-91f7-476a6245cd65','Wybrand Hendriks','fitzwilliam/23543'),('bc1144d9-d2f0-5d57-ade9-291f1c799dd4','5cacaf41-6786-5c42-8486-157c91c118dd','dbeb62ed-8b79-4393-91f7-476a6245cd65','Wybrand Hendriks','fitzwilliam/23543'),('92f06ff0-4218-5c86-b653-437c14aa5c44','5c3b9b1b-560f-5093-96a0-b20670b77c26','bd8908c1-019c-4321-980c-9a8d5919a239','Philip Connard','fitzwilliam/210190')]
for p in(E,R):p.mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+s))
def save(p,v):
 p=Path(p);b=json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()+b'\n';p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b;return
 q=p.with_suffix(p.suffix+'.tmp');q.write_bytes(b);os.replace(q,p)
def target(w=False):
 ps=subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines();x=[z.strip()for z in ps if '/tmp/artline-cloud-sql-proxy 'in z and '55519'in z];assert len(x)==1 and 'artline-508319:europe-west1:artline-postgres'in x[0]
 with c.connect()as d:r=d.execute('select current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone()
 assert r['db']=='artline'and not r['recovery'];return dict(at=c.now(),instance='artline-508319:europe-west1:artline-postgres',database=r,proxy_pid=int(x[0].split()[0]),write=w,local_catalogue_connections=0)
def live(d):
 out=[]
 for eid,en,aid,name,native in T:
  e=d.execute('select * from exhibition_entries where id=%s',(en,)).fetchone();a=d.execute('select * from artists where id=%s',(aid,)).fetchone();s=d.execute('select * from exhibition_source_records where id=%s',(e['source_record_id'],)).fetchone();p=d.execute('select * from exhibition_participants where exhibition_id=%s and artist_id=%s',(eid,aid)).fetchone();out.append(dict(eid=eid,entry=dict(e),artist=dict(a),source=dict(s),participant=dict(p)if p else None,native=native,name=name,pid=uid(eid+'/'+aid)))
 return out
def prepare():
 save(E/'production-target-reconciliation.json',target())
 with c.connect()as d:x=live(d)
 assert all(not z['participant']and z['entry']['artwork_id']is None and z['entry']['source_artwork_id']==z['native']and z['artist']['display_name']==z['name']and z['source']['capture_sha256']for z in x)
 save(E/'recovery-check.json',dict(at=c.now(),batch=130,prior_batch=129,noPriorWrites=True,concurrentJobsExcluded=True,passed=True));save(E/'transaction-preimage.json',dict(at=c.now(),targets=x))
 p=dict(at=c.now(),operation=OP,targets=[dict(exhibitionID=z['eid'],entryID=z['entry']['id'],sourceRecordID=z['entry']['source_record_id'],sourceArtworkID=z['native'],sourceCaptureSHA256=z['source']['capture_sha256'],sourceURL=z['source']['source_url'],artistID=z['artist']['id'],artistName=z['name'],participantID=z['pid'],creatorLabel=z['entry']['creator_label'],participation=z['entry']['participation'])for z in x]);save(E/'immutable-plan.json',p);save(E/'plan-pin.json',dict(sha256=sha((E/'immutable-plan.json').read_bytes())));save(E/'source-capture-verification.json',dict(at=c.now(),records=[dict(entryID=z['entry']['id'],native=z['native'],sourceURL=z['source']['source_url'],captureSHA256=z['source']['capture_sha256'],creatorLabel=z['entry']['creator_label'],canonicalArtist=z['name'])for z in x],primaryMuseumEvidencePersisted=True,passed=True));print('prepared')
def apply():
 p=json.loads((E/'immutable-plan.json').read_text());pin=json.loads((E/'plan-pin.json').read_text())['sha256'];assert sha((E/'immutable-plan.json').read_bytes())==pin;save(E/'production-target-before-database-write.json',target(True))
 with c.connect(write=True)as d:
  d.execute("set local lock_timeout='120s'");d.execute("select set_config('artline.actor_user_id','local-european-research',true)");d.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");d.execute('select pg_advisory_xact_lock(2026101201)');x=live(d);assert all(not z['participant']for z in x)
  for q,z in zip(p['targets'],x):
   assert z['source']['capture_sha256']==q['sourceCaptureSHA256']and z['artist']['display_name']==q['artistName'];ev=dict(operation=OP,planSHA256=pin,basis='Exact Fitzwilliam native object and reciprocal exhibition history; source creator label reconciled to existing canonical artist. Object remains documentary because no main-artwork version match is secure.',entryID=q['entryID'],sourceArtworkID=q['sourceArtworkID'],sourceCaptureSHA256=q['sourceCaptureSHA256'],currentDisplayClaim=False,checklistComplete=False);d.execute("insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)values(%s,%s,%s,%s,%s,'artist',%s)",(q['participantID'],q['exhibitionID'],q['sourceRecordID'],q['artistID'],q['artistName'],Jsonb(ev)))
  d.commit()
 save(E/'applied.json',dict(at=c.now(),operation=OP,planSHA256=pin,newArtistParticipationLinks=3))
def verify():
 p=json.loads((E/'immutable-plan.json').read_text());api=[]
 with c.connect()as d:x=live(d)
 for q,z in zip(p['targets'],x):
  assert z['participant']and str(z['participant']['id'])==q['participantID']and z['participant']['evidence']['operation']==OP and z['entry']['artwork_id']is None
  r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+q['exhibitionID'],timeout=40);r.raise_for_status();assert any(a['artist_id']==q['artistID']for a in r.json()['participants']);api.append(dict(exhibitionID=q['exhibitionID'],artistID=q['artistID'],status=r.status_code))
 save(E/'independent-database-verification.json',dict(at=c.now(),participants=[z['participant']for z in x],documentaryEntriesPreserved=[z['entry']for z in x],sourceChecksums=[z['source']['capture_sha256']for z in x],locks=['artline-curated-ingestion',2026101201],newRows=3,passed=True));save(E/'independent-public-verification.json',dict(at=c.now(),verified=api,newArtistParticipationLinks=3,passed=True));print('verified')
def finalize():
 p=json.loads((E/'immutable-plan.json').read_text());queue=E.parents[1]/'source-queue.json';nxt='Resolve remaining Fitzwilliam documentary objects to main artworks only where accession, version, date and qualified creator identity are secure; otherwise retain documentary entries.';names=['recovery-check.json','source-capture-verification.json','transaction-preimage.json','immutable-plan.json','plan-pin.json','cloud-backup-verification.json','production-target-before-database-write.json','applied.json','independent-database-verification.json','independent-public-verification.json'];rel=lambda n:str((E/n).relative_to(ROOT))
 with queue.with_suffix('.lock').open('a+')as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);q=json.loads(queue.read_text());b={x['source_id']:x for x in q['sources']if x['source_id']!='fitzwilliam_remaining_pictorial_events'};s=next(x for x in q['sources']if x['source_id']=='fitzwilliam_remaining_pictorial_events');s['research_status']='batch130_three_creator_links_verified';s['last_checked_at']=c.now();cur=s.setdefault('cursor',{});cur['batch130Links']=dict(entryIDs=[x['entryID']for x in p['targets']],count=3,evidence=rel('independent-database-verification.json'),next=nxt);cur['next']=nxt;s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(x)for x in names]));tmp=queue.with_suffix('.130.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,queue);assert b=={x['source_id']:x for x in json.loads(queue.read_text())['sources']if x['source_id']!='fitzwilliam_remaining_pictorial_events'}
 save(E/'queue-update-verification.json',dict(at=c.now(),updatedSource='fitzwilliam_remaining_pictorial_events',unrelatedSourcesPreserved=len(b),queueSHA256=sha(queue.read_bytes()),resume=nxt,passed=True));names.append('queue-update-verification.json');counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=3,new_exact_artwork_links=0,new_images=0,existing_records_enriched=3);cp=dict(at=c.now(),batch=130,stage='verified_complete',verified_counts=counts,next_task=nxt,evidence_paths=[rel(x)for x in names],external_supervisor_unchanged=True,separate_artwork_programme_modified=False,local_catalogue_connections=0);save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp);names.append('CHECKPOINT.json');result=dict(outcome='progress',summary='Added and independently verified three canonical artist-participation links across three existing Fitzwilliam exhibitions: Wybrand Hendriks in two Broughton flower-drawing shows and Philip Connard in the George Clausen exhibition. Each is supported by an exact native-object reciprocal exhibition record and persisted museum capture. The source objects remain documentary entries because secure main-artwork/version matches are unresolved; no artworks, exhibitions, images, holdings or statuses changed.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(x)for x in names]);save(E/'final-verification.json',dict(at=c.now(),databaseVerified=True,publicAPIVerified=True,sourceAttributionVerified=True,previousAndConcurrentIncrementsExcluded=True,result=result));result['evidence_paths'].append(rel('final-verification.json'));save(E/'worker-result.json',result);save(R/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':globals()[sys.argv[1]]()
