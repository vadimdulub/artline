#!/usr/bin/env python3
"""One bounded Tate archive delivery. External supervisor owns continuation."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000160'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000160'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000160'
OP='continuous-exhibitions-20261013-batch-000160'
ACTOR='local-european-research'
INSTANCE='artline-508319:europe-west1:artline-postgres'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
EID=c.uid('tate-archive/TG92/518')
OID=c.uid('tate-archive/TG92/518/venue/london')
PID=c.uid('tate-archive/TG92/518/participant/558')
AID='d6e11ae7-c271-4b19-92d8-71c00c865288'
TATE='a1976c92-e516-4585-9c6e-c4e640f6a8e9'
TITLE='Young Turner: early work to 1800: watercolours and drawings from the Turner Bequest 1787-1800'
START='1988-01-11';END='1988-03-20';DISPLAY='11 January – 20 March 1988'
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
save=lambda n,x:c.save(E/n,x)

def target(db):
    cmd='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth '+INSTANCE
    assert cmd in [s.strip() for s in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    r=db.execute('select current_database() database,current_user role').fetchone()
    assert r==dict(database='artline',role='artline_app')
    return dict(instance=INSTANCE,host=db.info.host,port=db.info.port,**r,checked_at=c.now())

def preserved(db):
    return serial(dict(artist=db.execute('select * from artists where id=%s',(AID,)).fetchone(),
        aliases=db.execute('select * from artist_aliases where artist_id=%s order by id',(AID,)).fetchall(),
        authorities=db.execute("select * from external_identifiers where entity_type='artist' and entity_id=%s order by id",(AID,)).fetchall(),
        aggregate_institution=db.execute('select * from institutions where id=%s',(TATE,)).fetchone()))

def snapshot(db):
    rows={}
    for table in TABLES:
        col='id' if table=='exhibitions' else 'exhibition_id'
        rows[table]=serial(db.execute('select * from '+table+' where '+col+'=%s order by id',(EID,)).fetchall())
    rows['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return rows

def collisions(db):
    return serial(db.execute("""select e.id,e.title,e.alternate_titles,e.start_year,e.end_year,e.start_date,e.end_date,e.import_batch,
      (select jsonb_agg(to_jsonb(o) order by o.id) from exhibition_occurrences o where o.exhibition_id=e.id) venues,
      (select jsonb_agg(jsonb_build_object('key',s.source_key,'native',s.source_record_id,'url',s.source_url) order by s.id) from exhibition_source_records s where s.exhibition_id=e.id) sources
      from exhibitions e where e.id<>%s and (
       e.title ilike any(%s) or e.alternate_titles::text ilike any(%s)
       or e.id in(select exhibition_id from exhibition_source_records where source_record_id in('TG 92/518','TG 92/518/1') or source_url ilike '%%TG%%92%%518%%')
       or ((e.start_year is null or e.start_year<=1988) and (e.end_year is null or e.end_year>=1988)
        and e.id in(select exhibition_id from exhibition_occurrences where institution_id=%s or venue_label ilike '%%tate%%')))
      order by e.id""",(EID,['%turner%','%тёрнер%','%тернер%','%young%turn%'],['%turner%','%тёрнер%','%тернер%','%young%turn%'],TATE)).fetchall())

def capture_check(name):
    d=c.load(E/name);rc=d['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert rc['status']==200 and c.sha(raw)==rc['sha256']
    assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==d['text']
    return d

def prepare():
    captures={n:capture_check(n) for n in ['tate-518.json','tate-518-1.json','tate-514.json','tate-514-1.json','tate-106-274.json','tate-bibliography1980s.json']}
    assert TITLE+'. (11 Jan - 20 Mar 1988)' in captures['tate-518.json']['text']
    assert 'RefNo TG 92/518/1' in captures['tate-518-1.json']['text']
    txt=captures['tate-bibliography1980s.json']['text'];i=txt.index('Young Turner : early work to 1800')
    extract=txt[i:txt.index('Douglas Cooper and the masters of Cubism.',i)]
    assert all(s in extract for s in ['ISBN: 185437026X','Tate Gallery (London)','Exhibition held: 11 Jan. - 20 Mar. 1988'])
    with c.connect() as db:
        t=target(db);old=preserved(db);before=snapshot(db);matches=collisions(db)
        assert not any(before.values())
        assert (old['artist']['display_name'],old['artist']['birth_year'],old['artist']['death_year'])==('J. M. W. Turner',1775,1851)
        assert any(x['scheme']=='tate-person' and x['external_id']=='558' for x in old['authorities'])
    if not (E/'broader-duplicate-snapshot.json').exists():
        save('broader-duplicate-snapshot.json',dict(at=c.now(),target=t,matches=matches))
    else:
        assert c.load(E/'broader-duplicate-snapshot.json')['matches']==matches
    print('BROAD MATCHES',[(x['id'],x['title'],x['start_year'],x['end_year']) for x in matches],flush=True)
    # Identity review is a separate inspected receipt, not an automatic fuzzy-title match.
    review_path=E/'broader-duplicate-review.json'
    if not review_path.exists():
        print('Saved broader duplicate snapshot. Inspect it and save the review before preparing the plan.');return
    dr=c.load(review_path);assert dr['passed'] and dr['reviewed_ids']==[x['id'] for x in matches]
    review=dict(at=c.now(),selected_distinct_exhibitions=1,individually_reviewed_tate_events=2,
        eligibility='Tate exhibition series TG92/518 explicitly documents a watercolour and drawing exhibition with historical dates. Official Tate Library bibliography independently identifies held dates and the London host.',
        title_basis='Original English archive title; final punctuation and parenthesized event dates separated into date fields. Artwork date ranges in title are not event dates.',
        date_status_assessed_at=c.now(),event_state='held',status='review',checklist_state='unknown',
        creator_identity='Exhibition specifically identifies the Turner Bequest and early watercolours/drawings. Existing J.M.W.Turner1775–1851, Tate person558 and aliases reconciled; namesakes excluded. Posthumous representation, no attendance claim.',
        venue_identity='Historical Tate Gallery (London) from the official bibliography. Existing Tate row is explicitly an aggregate collection without a physical venue; retain venue label and city with null canonical institution rather than inventing a building match or duplicating a museum.',
        checklist_basis='Archive metadata describes a press-notice folder; its contents and the1988 catalogue have not been inspected. No individual objects established.',
        unknowns=['Full checklist and exact artworks.','Organizers, lenders and sponsors beyond the named host.','Exact room/building address and canonical physical venue.','Any other tour stops.'],
        held=[dict(native_id='TG92/514',reason='Turner and the Channel: TG92 series and library bibliography agree26October–27December1987. TG106/274 poster item Date is26October–27October1987 and does not explicitly label an exhibition closing date; keep item dates distinct. Event medium/checklist needs further evidence; not imported.'),
              dict(native_id='TG92/514/1',reason='Loan folder explicitly CLOSED until01/01/2088. Public metadata only inspected; no restricted contents requested.'),
              dict(native_id='SD_ILS:112443',reason='library.tate.org.uk catalogue detail returnedHTTP403. Provider held; no retry. Bibliography remains accessible independently.')],
        image_policy='Registry says no automated Tate image downloads; none selected or downloaded. Archive publications not mirrored publicly.',
        visual_review_claimed=False,passed=True)
    sources=[]
    for fn,native,key in [('tate-518.json','TG 92/518','tate-official-exhibition-archive'),('tate-518-1.json','TG 92/518/1','tate-official-exhibition-archive'),('tate-bibliography1980s.json','g723193-p5302025-ISBN185437026X','tate-official-exhibition-bibliography')]:
        d=captures[fn]
        sources.append(dict(id=c.uid('tate-archive/TG92/518/source/'+native),source_key=key,native_id=native,**d))
    p=dict(at=c.now(),operation=OP,target=t,exhibition=dict(id=EID,title=TITLE,start=START,end=END,year=1988,date_display=DISPLAY),sources=sources,
        occurrence=dict(id=OID,institution_id=None,venue_label='Tate Gallery',city='London',country='United Kingdom',country_code='GB',source_id=sources[2]['id']),
        participant=dict(id=PID,artist_id=AID,name='Turner',role='artist',source_person_id='558',source_id=sources[0]['id'],posthumous=True),
        bibliography_extract=extract,preserved_entities=old,duplicate_matches=matches,review=review,
        scope='Exhibitions1600–1989; photography/sculpture excluded. Main artworks through1970; no main catalogue changes.')
    save('plan.json',p);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);c.save(B/'plan.json',p)
    pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=[x['receipt'] for x in captures.values()],raw_capture_sha256_verified=True,original_bodies_outside_Documents=True,passed=True))
    print('Prepared one event, one venue, one posthumous artist connection, three source records.')

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
            assert len(before['exhibition_source_records'])==3 and all(s['interpretation']['plan_sha256']==pin for s in before['exhibition_source_records'])
            print('Own transaction exists; no replay. Verify independently.');return
        assert not any(before.values()) and preserved(db)==p['preserved_entities'] and collisions(db)==p['duplicate_matches']
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=preserved(db),locks=['artline-curated-ingestion',2026101201])
        save('transaction-preimage.json',pre);c.save(B/'transaction-preimage.json',pre)
        save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        base=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],exhibition_type='watercolour and drawing exhibition',checklist_complete=False,organizer_unknown=True,lenders_unknown=True,sponsors_unknown=True,no_current_display_claim=True)
        db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
          values(%s,%s,%s,%s,%s,%s,1988,1988,%s,'day','held',%s,'physical','unknown','review',%s)""",
          (EID,TITLE,c.norm(TITLE),Jsonb([]),START,END,DISPLAY,'Official Tate archive TG92/518 and Tate Library exhibition bibliography agree on held dates and London host. Date-status assessed '+p['at']+'. Checklist contents not inspected.',OP))
        audit(db,'exhibitions','exhibition',EID,pin)
        for s in p['sources']:
            rc=s['receipt']
            db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              (s['id'],EID,s['source_key'],s['native_id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(source_text=s['text'],receipt=rc,review=p['review'],bibliography_extract=p['bibliography_extract'])),Jsonb(base)))
            audit(db,'exhibition_source_records','exhibition_source_record',s['id'],pin)
        o=p['occurrence']
        db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
          values(%s,%s,%s,NULL,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (OID,EID,o['source_id'],o['venue_label'],o['city'],o['country'],o['country_code'],START,END,DISPLAY,Jsonb(base|dict(venue_basis=p['review']['venue_identity'],source_wording='Tate Gallery (London)',geography_basis='London, United Kingdom; Tate institution registry. Historical physical venue not equated with aggregate collection.'))))
        audit(db,'exhibition_occurrences','exhibition_occurrence',OID,pin)
        a=p['participant']
        db.execute("""insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence)
          values(%s,%s,%s,%s,%s,'artist',%s,%s)""",
          (PID,EID,a['source_id'],AID,a['name'],a['source_person_id'],Jsonb(base|dict(posthumous=True,personal_attendance=False,participation_basis=p['review']['creator_identity']))))
        audit(db,'exhibition_participants','exhibition_participant',PID,pin)
        assert preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independent verification pending.')

def verify():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
    assert c.sha((E/'plan.json').read_bytes())==pin==pre['plan_sha256'] and not any(pre['rows'].values())
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        assert preserved(db)==p['preserved_entities'] and collisions(db)==p['duplicate_matches']
        for table,n in dict(exhibitions=1,exhibition_source_records=3,exhibition_occurrences=1,exhibition_participants=1,exhibition_entries=0,exhibition_publications=0,audits=6).items():assert len(rows[table])==n,(table,len(rows[table]))
        for a in rows['audits']:
            assert a['before_json'] is None and a['after_json']['plan_sha256']==pin
            assert any(a['after_json']['record']==r for table in TABLES for r in rows[table])
        ex=rows['exhibitions'][0]
        assert (ex['id'],ex['title'],ex['start_date'],ex['end_date'],ex['start_year'],ex['end_year'],ex['date_precision'],ex['event_state'],ex['status'],ex['checklist_state'],ex['import_batch'])==(EID,TITLE,START,END,1988,1988,'day','held','review','unknown',OP)
        for s in p['sources']:
            sr=next(x for x in rows['exhibition_source_records'] if x['id']==s['id']);rc=s['receipt']
            assert (sr['exhibition_id'],sr['source_key'],sr['source_record_id'],sr['source_url'],sr['capture_sha256'])==(EID,s['source_key'],s['native_id'],rc['url'],rc['sha256'])
            assert sr['source_payload']['source_text']==s['text'] and sr['interpretation']['plan_sha256']==pin and sr['interpretation']['operation']==OP
        o=rows['exhibition_occurrences'][0];op=p['occurrence']
        assert (o['id'],o['exhibition_id'],o['institution_id'],o['source_record_id'],o['venue_label'],o['city_label'],o['country_label'],o['country_code'],o['start_date'],o['end_date'])==(OID,EID,None,op['source_id'],'Tate Gallery','London','United Kingdom','GB',START,END)
        assert o['evidence']['plan_sha256']==pin and o['evidence']['operation']==OP
        a=rows['exhibition_participants'][0]
        assert (a['id'],a['exhibition_id'],a['artist_id'],a['source_record_id'],a['name_label'],a['role'],a['source_person_id'])==(PID,EID,AID,p['participant']['source_id'],'Turner','artist','558')
        assert a['evidence']['plan_sha256']==pin and a['evidence']['posthumous'] and not a['evidence']['personal_attendance']
    counts=dict(new_exhibitions=1,new_venue_stops=1,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=1,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
    if not (E/'independent-database-verification.json').exists():
        save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,verified_counts=counts,attribution='All counted rows absent in locked preimage. Persisted source/venue/participant plan hashes and six null-before audits match this batch. Fresh read-only production transaction independently verifies relationships and unchanged existing artist/institution. Other campaigns excluded.',passed=True))
    else:assert c.load(E/'independent-database-verification.json')['rows']==rows
    u=API+'exhibitions/'+EID;r=requests.get(u,timeout=(15,45));r.raise_for_status();j=r.json();c.save(R/'public-exhibition.json',j)
    assert (j['id'],j['title'],j['startYear'],j['endYear'],j['entryCount'],j['checklistState'],j['state'],j['datePrecision'])==(EID,TITLE,1988,1988,0,'unknown','held','day')
    assert len(j['venues'])==len(j['participants'])==1
    v=j['venues'][0];assert (v['id'],v['institution_id'],v['name'],v['city'],v['country'],v['start_date'],v['end_date'])==(OID,None,'Tate Gallery','London','United Kingdom',START,END)
    assert j['participants'][0]['artist_id']==AID and j['participants'][0]['id']==PID
    if not (E/'independent-public-verification.json').exists():
        save('independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,url=u,status=r.status_code,body_sha256=c.sha(r.content),snapshot=str(R/'public-exhibition.json'),event_venue_artist_relationships_verified=True,unknown_checklist_and_zero_object_claims_verified=True,passed=True))
    assert c.sha((B/'plan.json').read_bytes())==pin and c.load(B/'transaction-postimage.json')['rows']==rows
    assert c.sha((B/'transaction-preimage.json').read_bytes())==c.sha((E/'transaction-preimage.json').read_bytes())
    if not (E/'backup-verification.json').exists():
        save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']],preimage_absent=True,postimage_matches_fresh_read=True,passed=True))
    print(json.dumps(counts))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify']
    globals()[sys.argv[1]]()
