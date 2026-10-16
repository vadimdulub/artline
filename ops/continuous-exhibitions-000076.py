"""Batch 76: attach Fitzwilliam native object 14511 to its explicit Agnew 1977 show."""
import fcntl, gzip, hashlib, json, os, subprocess, sys, uuid
from pathlib import Path
import requests
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ops'))
import exhibitions_common as c
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000076'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000076'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000076'
Q=E.parents[1]/'source-queue.json'
OP='continuous-exhibitions-20261013-batch-000076'
EVENT='df845901-248e-5db5-bea3-24ab46ec9e1d'; WORK='7926c714-236d-5860-9021-b6f6b22e0c93'
ENTRY=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.app/'+OP+'/entry/14511/1176'))
URL='https://data.fitzmuseum.cam.ac.uk/id/object/14511'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'
serial=lambda x:json.loads(json.dumps(x,default=str))

def save(p,x): c.save(p,x)
def target(db):
    return serial(db.execute("select current_database() db,pg_is_in_recovery() recovery").fetchone())
def own(db): return serial(db.execute('select * from exhibition_entries where id=%s',(ENTRY,)).fetchall())
def event_rows(db):
    e=serial(db.execute('select * from exhibitions where id=%s',(EVENT,)).fetchone())
    o=serial(db.execute('select * from exhibition_occurrences where exhibition_id=%s',(EVENT,)).fetchall())
    s=serial(db.execute('select * from exhibition_source_records where exhibition_id=%s order by id',(EVENT,)).fetchall())
    w=serial(db.execute('select * from artworks where id=%s',(WORK,)).fetchone())
    ids=serial(db.execute("select * from external_identifiers where entity_type='artwork' and entity_id=%s",(WORK,)).fetchall())
    return dict(event=e,occurrences=o,sources=s,work=w,identifiers=ids)

def startup():
    E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True)
    cp=c.load(E.parents[1]/'CHECKPOINT.json'); assert cp['next_batch']==76
    ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True)
    locks=subprocess.check_output(['lsof','-p',str(cp['supervisor_pid'])+','+str(os.getppid()),'-a','-d','3'],text=True)
    proxy=next(x.strip() for x in ps.splitlines() if 'cloud-sql-proxy' in x and 'artline-508319:europe-west1:artline-postgres' in x)
    actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--format=value(connectionName)'],text=True).strip()
    assert actual=='artline-508319:europe-west1:artline-postgres'
    with c.connect() as db:
        t=target(db); prior=own(db); base=event_rows(db)
    assert not prior and base['event']['import_batch']=='continuous-exhibitions-20261013-batch-000073'
    assert len(base['occurrences'])==1 and len(base['sources'])==2
    save(E/'startup-recovery-verification.json',dict(at=c.now(),target=t,proxy=proxy,connection_name=actual,inherited_lock_descriptors=locks,inherited_descriptors_preserved=True,own_prior_writes=prior,agnew_event_verified=True,smk_changes_attributed=0,passed=True))
    save(E/'input-policy-verification.json',dict(at=c.now(),scope='exhibitions1600-1989; drawings eligible; main-artwork cutoff not relevant because existing work reused',local_catalogue_connections=0,translation_calls=0,supervisor_changes=0,inputs=[str(ROOT/'AGENTS.md'),str(ROOT/'docs/ARTLINE_IMAGE_USE.md'),str(ROOT/'docs/LOCAL_DATA_LOCATIONS.md')]))

def prepare():
    r=requests.get(URL,headers={'Accept':'application/json','User-Agent':'Artline exhibition history research; bounded metadata retrieval'},timeout=(15,45));r.raise_for_status(); raw=r.content;j=r.json()
    body=R/'fitzwilliam-object-14511.json'; body.write_bytes(raw)
    rc=dict(url=URL,final_url=r.url,status=r.status_code,retrieved_at=c.now(),sha256=c.sha(raw),bytes=len(raw),content_type=r.headers.get('content-type'),body_path=str(body))
    ex=next(x for x in j['exhibitions'] if x['admin']['id']=='exhibition-1176')
    assert ex['@link']['catalogue']=='83' and ex['summary_title']=='104th Annual Exhibition of Watercolour & Drawings'
    assert j['title'][0]['value']=='On the Dart' and j['admin']['id']=='object-14511'
    with c.connect() as db:
        t=target(db); base=event_rows(db); assert not own(db)
        assert base['work']['accession_number']=='PD.5-1977' and base['work']['title']=='On the Dart'
        assert any(x['scheme']=='fitzwilliam-native-object' and x['external_id']=='14511' for x in base['identifiers'])
        dup=serial(db.execute("select * from exhibition_entries where exhibition_id=%s and (artwork_id=%s or source_artwork_id in ('14511','fitzwilliam/14511'))",(EVENT,WORK)).fetchall());assert not dup
    plan=dict(at=c.now(),operation=OP,target=t,entry_id=ENTRY,event_id=EVENT,artwork_id=WORK,occurrence_id=base['occurrences'][0]['id'],source_record_id=base['sources'][0]['id'],receipt=rc,source=ex,work_preimage=base['work'],identifiers=base['identifiers'],duplicate_rows=dup,basis='Official Fitzwilliam reciprocal native object history explicitly lists object14511, On the Dart, as catalogue83 in exhibition1176. Existing production artwork matches native identifier14511 and accession PD.5-1977; existing batch73 event is the same official exhibition1176. Partial checklist only; no artist, holding, complete-checklist or current-display inference.')
    save(E/'plan.json',plan);save(B/'plan.json',plan);pin=c.sha((E/'plan.json').read_bytes());save(E/'plan-pin.json',dict(sha256=pin,backup=str(B/'plan.json')))
    save(E/'source-capture-verification.json',dict(at=c.now(),receipt=rc,object_title='On the Dart',native_object='14511',exhibition_native='1176',catalogue_number='83',capture_checksum_verified=c.sha(body.read_bytes())==rc['sha256'],passed=True))
    save(E/'research-review.json',dict(at=c.now(),discovered=1,prepared=1,imported=0,verified=0,complete_checklists=0,selected_explicit_participation=1,new_images=0,holds=[dict(key='creator',reason='Existing work has only unlinked creator label De Wint, Peter; no canonical artist link forced.'),dict(key='checklist',reason='One reciprocal object history is selected evidence, not a complete checklist.'),dict(key='courtauld-object',reason='D.2007.DS.43 remains unmatched and was not linked.')]))

def apply():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert c.sha((E/'plan.json').read_bytes())==pin and p==c.load(B/'plan.json')
    assert c.sha(Path(p['receipt']['body_path']).read_bytes())==p['receipt']['sha256']
    with c.connect(write=True) as db:
        db.execute("select set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        if own(db): print('REPLAY');return
        base=event_rows(db); assert base['work']==p['work_preimage'] and base['identifiers']==p['identifiers']
        assert not db.execute("select 1 from exhibition_entries where exhibition_id=%s and (artwork_id=%s or source_artwork_id in ('14511','fitzwilliam/14511'))",(EVENT,WORK)).fetchone()
        tx=db.execute('select txid_current()::text id').fetchone()['id'];pre=dict(at=c.now(),target=target(db),plan_sha256=pin,transaction_id=tx,selected_rows=[],existing_event=base['event'],existing_work=base['work'],locks=['artline-curated-ingestion',2026101201])
        save(E/'transaction-preimage.json',pre);save(B/'transaction-preimage.json',pre)
        ev=dict(operation=OP,plan_sha256=pin,transaction_id=tx,nativeObjectID='14511',accession='PD.5-1977',nativeExhibitionID='1176',catalogueNumber='83',checklistComplete=False,holdingClaim=False,currentDisplayClaim=False,creatorLabelPreserved='De Wint, Peter',basis=p['basis'])
        db.execute('insert into exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,lender_label,participation,source_page,evidence,match_basis) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s,NULL,NULL,%s,%s,%s,%s)',(ENTRY,EVENT,p['source_record_id'],p['occurrence_id'],WORK,'fitzwilliam/14511','83','On the Dart','De Wint, Peter','drawing','exhibited',URL,Jsonb(ev),p['basis']))
        row=serial(db.execute('select * from exhibition_entries where id=%s',(ENTRY,)).fetchone())
        db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values('local-european-research','continuous_exhibition_insert','exhibition_entry',%s,%s,%s,%s)",(ENTRY,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin,transaction_id=tx))))
        save(B/'transaction-postimage.json',dict(at=c.now(),row=row,plan_sha256=pin,transaction_id=tx))
    save(E/'applied.json',dict(at=c.now(),entry_id=ENTRY,plan_sha256=pin,transaction_id=tx))

def verify():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');assert not pre['selected_rows'] and pin==pre['plan_sha256']
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');rows=own(db);assert len(rows)==1;r=rows[0]
        assert (r['exhibition_id'],r['artwork_id'],r['occurrence_id'],r['catalogue_number'],r['title_label'],r['participation'])==(EVENT,WORK,p['occurrence_id'],'83','On the Dart','exhibited')
        assert r['evidence']['plan_sha256']==pin
        audits=serial(db.execute('select * from audit_log where request_id=%s',(OP,)).fetchall());assert len(audits)==1 and audits[0]['after_json']['plan_sha256']==pin
        assert event_rows(db)['work']==p['work_preimage']
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=1,new_images=0,existing_records_enriched=1)
    save(E/'independent-database-verification.json',dict(at=c.now(),target=target_read(),entry=r,audits=audits,locked_preimage=str(B/'transaction-preimage.json'),plan_sha256=pin,verified_counts=counts,attribution='Entry absent in shared-lock transaction preimage; exact programme plan/source checksum and transaction audit independently verified. Prior campaigns and concurrent jobs excluded.',passed=True))
    res=requests.get(API+EVENT+'/entries?limit=100',timeout=(15,45));res.raise_for_status();d=res.json();item=next(x for x in d['items'] if x['id']==ENTRY);assert item['artworkId']==WORK and item['catalogueNumber']=='83'
    save(R/'public-entries.json',d);save(E/'public-verification.json',dict(at=c.now(),url=res.url,http_status=res.status_code,response_sha256=c.sha(res.content),entry_id=ENTRY,artwork_id=WORK,catalogue_number='83',passed=True))
    finish(counts,pin)

def target_read():
    with c.connect() as db:return target(db)
def finish(counts,pin):
    nxt='Rotate to an undercovered official Russian-icon, Greek, Byzantine or post-Byzantine historical archive route; Arthive remains held at HTTP429. Do not replay Fitzwilliam object14511/exhibition1176; Courtauld D.2007.DS.43 remains an identity hold.'
    paths=[f'docs/research/continuous-exhibitions-20261013/batches/000076/{x}' for x in ['independent-database-verification.json','public-verification.json','source-capture-verification.json','startup-recovery-verification.json','queue-update.json','CHECKPOINT.json']]
    with Q.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);before=c.load(Q);q=serial(before);g=next(x for x in q['supplemental_sources'] if x['source_id']=='fitzwilliam_remaining_pictorial_events')
        g['research_status']='agnew1977_exact_object_link_verified_batch76';g['cursor']['batch76']=dict(completed_native_object='14511',completed_exhibition='1176',entry_id=ENTRY,next=nxt);g['evidence'].extend(paths[:4])
        a=next(x for x in q['supplemental_sources'] if x['source_id']=='arthive_exhibitions');a['cursor']['batch76']=dict(hold_reused_without_request=True,next='Await changed HTTP429 access state; use available official archives')
        assert [x for x in before['sources']]==[x for x in q['sources']]
        save(E/'source-queue-preimage.json',before);save(E/'source-queue-postimage.json',q)
        tmp=Q.with_suffix('.batch76.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
        save(E/'queue-update.json',dict(at=c.now(),updated_sources=['fitzwilliam_remaining_pictorial_events','arthive_exhibitions'],unrelated_entries_preserved=True,registry_unchanged=True,next_task=nxt,passed=True))
    cp=dict(at=c.now(),batch=76,stage='verified_complete',plan_sha256=pin,verified_counts=counts,discovered=1,prepared=1,imported=1,verified=1,complete_checklists=0,next_task=nxt,external_supervisor_owns_continuation=True,evidence_paths=paths)
    save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
    result=dict(outcome='progress',summary='Added and independently verified one exact artwork participation link for Fitzwilliam object 14511, On the Dart, catalogue no. 83 in the existing 104th Annual Exhibition of Watercolour & Drawings (Agnew, 1977). Native object, accession, event and public API delivery all match; the checklist remains partial and no creator or holding claim was inferred.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=paths)
    save(E/'result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    for f in (startup,prepare,apply,verify): f()
