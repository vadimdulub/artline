#!/usr/bin/env python3
"""One bounded official Greek archive delivery; external supervisor owns continuation."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000156'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000156'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000156'
OP='continuous-exhibitions-20261013-batch-000156'
ACTOR='local-european-research'
INSTANCE='artline-508319:europe-west1:artline-postgres'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b'
EID=c.uid('national-gallery-athens/contemporary-dutch-painting')
OID=c.uid('national-gallery-athens/contemporary-dutch-painting/venue/athens')
SID_GR=c.uid('national-gallery-athens/contemporary-dutch-painting/source/el')
SID_EN=c.uid('national-gallery-athens/contemporary-dutch-painting/source/en')
SPANISH='1564d759-76c1-5284-8b13-2a91aef14ee2'
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']

def serial(x): return json.loads(json.dumps(x,ensure_ascii=False,default=str))
def save(n,x): c.save(E/n,x)
def target(db):
    cmd='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth '+INSTANCE
    assert cmd in [s.strip() for s in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    r=db.execute('select current_database() database,current_user role').fetchone()
    assert r==dict(database='artline',role='artline_app')
    return dict(instance=INSTANCE,host=db.info.host,port=db.info.port,**r,checked_at=c.now())
def preserved(db):
    return serial(dict(institution=db.execute('select * from institutions where id=%s',(MID,)).fetchone(),
        prior_spanish_event=db.execute('select * from exhibitions where id=%s',(SPANISH,)).fetchone()))
def snapshot(db):
    rows={}
    for table in TABLES:
        col='id' if table=='exhibitions' else 'exhibition_id'
        rows[table]=serial(db.execute('select * from '+table+' where '+col+'=%s order by id',(EID,)).fetchall())
    rows['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return rows
def collisions(db):
    return serial(db.execute("""select distinct e.id,e.title,e.start_year,e.end_year,e.import_batch
        from exhibitions e left join exhibition_source_records s on s.exhibition_id=e.id
        where e.id=%s or s.source_url like any(%s)
        or ((e.title ilike any(%s) or e.alternate_titles::text ilike any(%s))
        and (e.start_year is null or e.start_year<=1983) and (e.end_year is null or e.end_year>=1983))""",
        (EID,['%/contemporary-dutch-painting/%','%/sughroni-ollandikh-zographikh/%'],
        ['%dutch%','%ολλανδ%','%holland%','%niederländ%'],['%dutch%','%ολλανδ%','%holland%','%niederländ%'])).fetchall())
def check_capture(record):
    rc=record['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert rc['status']==200 and c.sha(raw)==rc['sha256']
    text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert text==record['text']
    return text
def check_collisions(matches):
    review=c.load(E/'broader-title-duplicate-verification.json')
    assert review['passed'] and review['different_events_verified']
    old=c.load(E/'broader-title-duplicate-snapshot.json')['matches']
    expected=[{k:v for k,v in r.items() if k not in ['sources','venues']} for r in old]
    assert sorted(matches,key=lambda x:x['id'])==sorted(expected,key=lambda x:x['id']),matches
def prepare():
    en=c.load(E/'contemporary-dutch-painting.json');gr=c.load(E/'dutch-greek.json')
    for rec in [en,gr]:
        txt=check_capture(rec)
        assert '16.09.1983' in txt and '23.10.1983' in txt
    assert en['title']=='Modern Dutch Painting' and gr['title']=='Σύγχρονη Ολλανδική Ζωγραφική'
    all_files=['american-paintings-1900-1982.json','american-greek.json','six-artists-from-ireland-an-aspect-of-irish-painting.json','contemporary-dutch-painting.json','dutch-greek.json','contemporary-spanish-painting.json','dutch-landscape-painting-of-the-17th-century.json']
    for fn in all_files:check_capture(c.load(E/fn))
    with c.connect() as db:
        t=target(db);before=snapshot(db);old=preserved(db);matches=collisions(db)
        # Broad wildcard results were individually distinguished using source dates, media and venues.
        check_collisions(matches)
        assert not any(before.values())
        assert old['institution']['name']=='National Gallery – Alexandros Soutsos Museum'
    review=dict(at=c.now(),discovered_candidates=5,selected_distinct_exhibitions=1,
        eligible_basis='Both official language pages explicitly identify painting, the central gallery venue and matching historical dates.',
        original_title=gr['title'],translated_title=en['title'],translation_basis='Institution-supplied English title, not machine translation.',
        date_status_assessed_at=c.now(),state='held',checklist_state='unknown',
        unknowns=['No named artists or exact objects supplied by these event pages.','Full contemporary checklist not inspected.','Organizer, lenders and sponsors unestablished.','Greek website venue taxonomy says permanent collections; temporary-versus-collection-display subtype not inferred.','No additional venue stops documented.'],
        duplicate_excluded=dict(source='contemporary-spanish-painting',id=SPANISH,prior_batch=140,counted_new=False),
        held=[dict(key='american-painting-1982-date-conflict',source_files=['american-paintings-1900-1982.json','american-greek.json'],reason='English opening20.09.1982 versus Greek20.09.2981; both close01.11.1982. Obvious invalid chronology preserved, original catalogue required before choosing dates.'),
              dict(key='irish-six-1983-date-conflict',source_files=['six-artists-from-ireland-an-aspect-of-irish-painting.json'],reason='Page opens21.11.1983 but closes09.01.1983. No corrected year inferred.'),
              dict(key='dutch-landscape-1985-1986-date-conflict',source_files=['dutch-landscape-painting-of-the-17th-century.json'],reason='Widget opens18.12.1986 but closes28.02.1986; narrative says18December1985–28February1986. Original catalogue and tour reconciliation required.')],
        images_selected=0,visual_review_claimed=False,passed=True)
    sources=[]
    for rec,sid,lang in [(gr,SID_GR,'el'),(en,SID_EN,'en')]:
        sources.append(dict(id=sid,source_key='national-gallery-athens-official-exhibition-'+lang,language=lang,**rec))
    p=dict(at=c.now(),operation=OP,target=t,exhibition=dict(id=EID,title=gr['title'],alternate_titles=[en['title']],start='1983-09-16',end='1983-10-23',year=1983,date_display='16 September – 23 October 1983'),
        sources=sources,occurrence=dict(id=OID,institution_id=MID,venue_label='National Gallery - Central Building',city='Athens',country='Greece',country_code='GR',source_id=SID_EN),
        preserved_entities=old,review=review,scope='Historical exhibitions1600–1989; main artwork scope unchanged. No main-catalogue, artist or image additions.',
        duplicate_review_files=['startup-recovery-and-identity-query.json','venue-period-duplicate-review.json','legacy-dutch-identity-verification.json','broader-title-duplicate-verification.json'])
    assert c.load(E/'legacy-dutch-identity-verification.json')['different_event_verified']
    save('plan.json',p);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);c.save(B/'plan.json',p)
    pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=[c.load(E/f)['receipt'] for f in all_files],all_raw_capture_sha256_verified=True,original_bodies_outside_Documents=True,passed=True))
    print('Prepared one event, two source records, one existing-institution venue; no asserted participation.')
def audit(db,table,typ,ident,pin):
    row=serial(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
    db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)",
        (ACTOR,typ,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))
def apply():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256']
    assert p['operation']==OP and c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())==pin
    with c.connect(write=True) as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('select pg_advisory_xact_lock(2026101201)');before=snapshot(db)
        if before['exhibitions']:
            assert before['exhibitions'][0]['import_batch']==OP and (B/'transaction-preimage.json').exists()
            assert len(before['exhibition_source_records'])==2 and all(x['interpretation']['plan_sha256']==pin for x in before['exhibition_source_records'])
            print('Own transaction exists; no replay. Verify independently.');return
        assert not any(before.values()) and preserved(db)==p['preserved_entities']
        check_collisions(collisions(db))
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=preserved(db),locks=['artline-curated-ingestion',2026101201])
        save('transaction-preimage.json',pre);c.save(B/'transaction-preimage.json',pre)
        save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        ex=p['exhibition'];base=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],exhibition_type='painting exhibition',exact_subtype_unknown=True,
            checklist_complete=False,organizer_unknown=True,lenders_unknown=True,sponsors_unknown=True,no_current_display_claim=True,
            source_venue_taxonomy='Greek page: central building – permanent collections. English page: central building.',no_participation_inferred=True)
        db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
          values(%s,%s,%s,%s,%s,%s,1983,1983,%s,'day','held',%s,'physical','unknown','review',%s)""",
          (EID,ex['title'],c.norm(ex['title']),Jsonb(ex['alternate_titles']),ex['start'],ex['end'],ex['date_display'],'Official institutional retrospective archive in Greek and English documents matching dates and host. Date-status assessed '+p['at']+'. Original checklist unknown.',OP))
        audit(db,'exhibitions','exhibition',EID,pin)
        for s in p['sources']:
            rc=s['receipt']
            db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(s['id'],EID,s['source_key'],s['native_id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(source_text=s['text'],receipt=rc,language=s['language'],review=p['review'])),Jsonb(base)))
            audit(db,'exhibition_source_records','exhibition_source_record',s['id'],pin)
        o=p['occurrence']
        db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(OID,EID,o['source_id'],MID,o['venue_label'],o['city'],o['country'],o['country_code'],ex['start'],ex['end'],ex['date_display'],Jsonb(base|dict(geography_basis='Existing canonical institution and original111-source registry; source explicitly names central building. Current street address not projected into history.'))))
        audit(db,'exhibition_occurrences','exhibition_occurrence',OID,pin)
        assert preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; verification pending.')
def verify():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
    assert c.sha((E/'plan.json').read_bytes())==pin==pre['plan_sha256'] and not any(pre['rows'].values())
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        assert preserved(db)==p['preserved_entities']
        for table,n in dict(exhibitions=1,exhibition_source_records=2,exhibition_occurrences=1,exhibition_participants=0,exhibition_entries=0,exhibition_publications=0,audits=4).items():assert len(rows[table])==n
        assert all(a['before_json'] is None and a['after_json']['plan_sha256']==pin for a in rows['audits'])
        ex=rows['exhibitions'][0];ep=p['exhibition']
        assert (ex['id'],ex['title'],ex['alternate_titles'],ex['start_date'],ex['end_date'],ex['start_year'],ex['end_year'],ex['date_precision'],ex['event_state'],ex['status'],ex['checklist_state'],ex['import_batch'])==(EID,ep['title'],ep['alternate_titles'],ep['start'],ep['end'],1983,1983,'day','held','review','unknown',OP)
        for s in p['sources']:
            sr=next(x for x in rows['exhibition_source_records'] if x['id']==s['id']);rc=s['receipt']
            assert (sr['exhibition_id'],sr['source_key'],sr['source_record_id'],sr['source_url'],sr['capture_sha256'])==(EID,s['source_key'],s['native_id'],rc['url'],rc['sha256'])
            assert sr['source_payload']['source_text']==s['text'] and sr['interpretation']['plan_sha256']==pin and sr['interpretation']['operation']==OP
        o=rows['exhibition_occurrences'][0];op=p['occurrence']
        assert (o['id'],o['exhibition_id'],o['institution_id'],o['source_record_id'],o['venue_label'],o['city_label'],o['country_label'],o['country_code'],o['start_date'],o['end_date'])==(OID,EID,MID,SID_EN,op['venue_label'],'Athens','Greece','GR',ep['start'],ep['end'])
        assert o['evidence']['plan_sha256']==pin and o['evidence']['operation']==OP
    counts=dict(new_exhibitions=1,new_venue_stops=1,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
    if (E/'independent-database-verification.json').exists():
        prior=c.load(E/'independent-database-verification.json')
        assert prior['passed'] and prior['rows']==rows and prior['plan_sha256']==pin and prior['verified_counts']==counts
    else:
        save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,verified_counts=counts,attribution='All counted rows absent in locked preimage; persisted source and venue plan hashes and four null-before audits match. Fresh read-only production transaction verifies relations and preserved entities. Prior Spanish event and other programmes excluded.',passed=True))
    u=API+'exhibitions/'+EID;r=requests.get(u,timeout=(15,45));r.raise_for_status();j=r.json();c.save(R/'public-exhibition.json',j)
    assert (j['id'],j['title'],j['startYear'],j['endYear'],j['entryCount'],j['checklistState'],j['state'],j['datePrecision'])==(EID,ep['title'],1983,1983,0,'unknown','held','day')
    assert len(j['venues'])==1 and len(j['participants'])==0
    v=j['venues'][0];assert (v['id'],v['institution_id'],v['name'],v['city'],v['country'],v['start_date'],v['end_date'])==(OID,MID,op['venue_label'],'Athens','Greece',ep['start'],ep['end'])
    if (E/'independent-public-verification.json').exists():
        prior=c.load(E/'independent-public-verification.json');assert prior['passed'] and prior['plan_sha256']==pin and c.load(R/'public-exhibition.json')==j
    else:
        save('independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,url=u,status=r.status_code,body_sha256=c.sha(r.content),snapshot=str(R/'public-exhibition.json'),event_and_venue_independently_verified=True,zero_asserted_participants_and_entries_verified=True,passed=True))
    assert c.sha((B/'plan.json').read_bytes())==pin and c.load(B/'transaction-postimage.json')['rows']==rows
    assert c.sha((B/'transaction-preimage.json').read_bytes())==c.sha((E/'transaction-preimage.json').read_bytes())
    files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']]
    if (E/'backup-verification.json').exists():
        prior=c.load(E/'backup-verification.json');assert prior['passed'] and prior['plan_sha256']==pin and prior['files']==files
    else:
        save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=files,preimage_absent=True,postimage_matches_fresh_read=True,passed=True))
    print(json.dumps(counts))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify']
    globals()[sys.argv[1]]()
