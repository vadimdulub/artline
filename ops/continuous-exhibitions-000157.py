#!/usr/bin/env python3
"""Bounded NSW historical print exhibition delivery; no supervisor changes."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000157'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000157'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000157'
OP='continuous-exhibitions-20261013-batch-000157'
ACTOR='local-european-research'
INSTANCE='artline-508319:europe-west1:artline-postgres'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
MID='d3524dc2-2672-582f-be42-4bf3c8ace210'
EID=c.uid('australian-prints-printmaking/exhibition/14')
SID=c.uid('australian-prints-printmaking/exhibition/14/source')
OID=c.uid('australian-prints-printmaking/exhibition/14/venue/949')
TITLE='Australian Woodcuts and Linocuts.'
START='1984-06-30';END='1984-08-19'
DISPLAY='30 June – 19 August 1984'
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
    return serial(dict(institution=db.execute('select * from institutions where id=%s',(MID,)).fetchone(),
        other_events=db.execute('select * from exhibitions where id=any(%s) order by id',(['ed68e4cd-9af8-564c-968f-8968637ee3e0','397470b3-b582-5fef-9c82-4b0d96e91ff1'],)).fetchall()))

def snapshot(db):
    rows={}
    for table in TABLES:
        col='id' if table=='exhibitions' else 'exhibition_id'
        rows[table]=serial(db.execute('select * from '+table+' where '+col+'=%s order by id',(EID,)).fetchall())
    rows['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return rows

def collisions(db):
    return serial(db.execute("""select e.id,e.title,e.alternate_titles,e.start_year,e.end_year,e.start_date,e.end_date,e.import_batch,
      (select jsonb_agg(jsonb_build_object('id',o.id,'label',o.venue_label,'city',o.city_label,'institution',o.institution_id,'start',o.start_date,'end',o.end_date)) from exhibition_occurrences o where o.exhibition_id=e.id) venues,
      (select jsonb_agg(jsonb_build_object('source_key',s.source_key,'native',s.source_record_id,'url',s.source_url)) from exhibition_source_records s where s.exhibition_id=e.id) sources
      from exhibitions e where e.id<>%s and (
      e.id in(select exhibition_id from exhibition_source_records where source_url ~ 'printsandprintmaking[.]gov[.]au/exhibitions/14(/|$)')
      or ((e.start_year is null or e.start_year<=1984) and (e.end_year is null or e.end_year>=1984) and (
      e.title ilike any(%s) or e.alternate_titles::text ilike any(%s)
      or e.id in(select exhibition_id from exhibition_occurrences where institution_id=%s or city_label ilike '%%Sydney%%' or venue_label ilike '%%new south wales%%')))
      or e.title ilike '%%australian%%woodcut%%' or e.title ilike '%%australian%%linocut%%') order by e.id""",
      (EID,['%woodcut%','%linocut%','%relief%','%australian%print%'],['%woodcut%','%linocut%','%relief%','%australian%print%'],MID)).fetchall())

def capture_check(name):
    d=c.load(E/name);rc=d['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert rc['status']==200 and c.sha(raw)==rc['sha256']
    assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==d['text']
    return d

def prepare():
    names=['pp-14.json','pp-11419.json','pp-8159.json','pp-gallery949.json','pp-gallery949-history6.json','nsw-exhibition-archive.json']
    captures={n:capture_check(n) for n in names};src=captures['pp-14.json'];txt=src['text']
    assert all(t in txt for t in [TITLE,'30 June 1984 – 19 August 1984','Multi-artist exhibition.','Prints.','Documentation Checklist'])
    assert '/galleries/949' in [x['href'].rstrip('/') for x in src['links']]
    assert 'The Domain, Sydney, New South Wales, Australia' in captures['pp-gallery949.json']['text']
    with c.connect() as db:
        t=target(db);before=snapshot(db);old=preserved(db);matches=collisions(db)
        assert not any(before.values())
        assert old['institution']['name']=='Art Gallery of New South Wales'
        assert matches==c.load(E/'broader-duplicate-query.json')['matches']
        assert len(matches)==1 and matches[0]['id']=='ed68e4cd-9af8-564c-968f-8968637ee3e0'
    review=dict(at=c.now(),selected_distinct_exhibitions=1,individual_candidate_pages_reviewed=3,
      eligibility='Explicit official institutional exhibition record: multi-artist print exhibition held 30 June–19 August 1984 at Art Gallery of New South Wales.',
      venue_identity='Native gallery949 names AGNSW, Sydney, and official website; matched to existing registry/canonical institution. Source1958 establishment label is not imported as institutional founding date.',
      date_status_assessed_at=c.now(),event_state='held',status='review',checklist_state='unknown',
      checklist_basis='Documentation Checklist is a bibliography/category label. No checklist contents or named exhibited objects supplied; completeness remains unknown.',
      unknowns=['Organizer, lenders and sponsors unestablished.','No named participating creators, exact objects or additional venue stops established.','No authentic images selected; no visual-review claim.'],
      held=[dict(native_id='11419',reason='Fruit and flowers venue dates8August–11September1981 conflict with abstract saying it coincided with botanical congress21–28March1981. Single-artist category and Australian prints section require original catalogue review.'),
            dict(native_id='8159',reason='Sali Herman retrospective dates captured; medium not explicitly specified on the inspected event page. Retrieve original catalogue/explicit painting evidence before selecting.')],
      duplicate_review=dict(matches=matches,decision='Existing Picasso1984 tour has a different title and October–December Sydney stop; not the June–August multi-artist Australian print exhibition. Fruit and Flower Paintings1933 is also a different year/title, excluded from selection.'),
      nsw_archive_outcome='Direct museum archive index covers2000–2010, outside historical scope. National Gallery of Australia Prints + Printmaking supplies independent official historical event record.',
      rights='No image download or image licence inferred from accepted metadata.',passed=True)
    p=dict(at=c.now(),operation=OP,target=t,exhibition=dict(id=EID,title=TITLE,start=START,end=END,year=1984,date_display=DISPLAY),
      source=dict(id=SID,source_key='australian-prints-printmaking-official-exhibition',**src),
      venue_source=captures['pp-gallery949.json'],occurrence=dict(id=OID,institution_id=MID,venue_label='Art Gallery Of New South Wales.',city='Sydney',country='Australia',country_code='AU',source_id=SID),
      preserved_entities=old,review=review,scope='Exhibitions1600–1989; photography/sculpture excluded. Main artwork scope unchanged; no main catalogue changes.',duplicate_matches=matches)
    save('plan.json',p);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);c.save(B/'plan.json',p)
    pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin))
    save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=[x['receipt'] for x in captures.values()],all_raw_capture_sha256_verified=True,original_bodies_outside_Documents=True,passed=True))
    print('Prepared one new historical print exhibition and existing-institution venue.')

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
            assert len(before['exhibition_source_records'])==1 and before['exhibition_source_records'][0]['interpretation']['plan_sha256']==pin
            print('Own transaction exists; no replay. Verify independently.');return
        assert not any(before.values()) and preserved(db)==p['preserved_entities'] and collisions(db)==p['duplicate_matches']
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=preserved(db),locks=['artline-curated-ingestion',2026101201])
        save('transaction-preimage.json',pre);c.save(B/'transaction-preimage.json',pre)
        save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        base=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],exhibition_type='multi-artist print exhibition',checklist_complete=False,organizer_unknown=True,lenders_unknown=True,sponsors_unknown=True,no_current_display_claim=True,no_participation_inferred=True)
        db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
          values(%s,%s,%s,%s,%s,%s,1984,1984,%s,'day','held',%s,'physical','unknown','review',%s)""",
          (EID,TITLE,c.norm(TITLE),Jsonb([]),START,END,DISPLAY,'Official NGA Prints + Printmaking retrospective exhibition record explicitly documents dates, print medium and AGNSW venue. Date-status assessed '+p['at']+'. Checklist contents not inspected.',OP))
        audit(db,'exhibitions','exhibition',EID,pin)
        s=p['source'];rc=s['receipt']
        db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
          values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (SID,EID,s['source_key'],s['native_id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(source_text=s['text'],receipt=rc,venue_source=p['venue_source'],review=p['review'])),Jsonb(base)))
        audit(db,'exhibition_source_records','exhibition_source_record',SID,pin)
        o=p['occurrence']
        db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
          values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (OID,EID,SID,MID,o['venue_label'],o['city'],o['country'],o['country_code'],START,END,DISPLAY,Jsonb(base|dict(venue_native_id='949',geography_source=p['venue_source']['receipt'],no_new_institution=True))))
        audit(db,'exhibition_occurrences','exhibition_occurrence',OID,pin)
        assert preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independent verification pending.')

def verify():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
    assert c.sha((E/'plan.json').read_bytes())==pin==pre['plan_sha256'] and not any(pre['rows'].values())
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        assert preserved(db)==p['preserved_entities'] and collisions(db)==p['duplicate_matches']
        for table,n in dict(exhibitions=1,exhibition_source_records=1,exhibition_occurrences=1,exhibition_participants=0,exhibition_entries=0,exhibition_publications=0,audits=3).items():assert len(rows[table])==n
        for a in rows['audits']:
            assert a['before_json'] is None and a['after_json']['plan_sha256']==pin
            assert any(a['after_json']['record']==r for table in TABLES for r in rows[table])
        ex=rows['exhibitions'][0]
        assert (ex['id'],ex['title'],ex['start_date'],ex['end_date'],ex['start_year'],ex['end_year'],ex['date_precision'],ex['event_state'],ex['status'],ex['checklist_state'],ex['import_batch'])==(EID,TITLE,START,END,1984,1984,'day','held','review','unknown',OP)
        sr=rows['exhibition_source_records'][0];s=p['source'];rc=s['receipt']
        assert (sr['id'],sr['exhibition_id'],sr['source_key'],sr['source_record_id'],sr['source_url'],sr['capture_sha256'])==(SID,EID,s['source_key'],'14',rc['url'],rc['sha256'])
        assert sr['source_payload']['source_text']==s['text'] and sr['source_payload']['venue_source']==p['venue_source']
        assert sr['interpretation']['plan_sha256']==pin and sr['interpretation']['operation']==OP
        o=rows['exhibition_occurrences'][0];op=p['occurrence']
        assert (o['id'],o['exhibition_id'],o['institution_id'],o['source_record_id'],o['venue_label'],o['city_label'],o['country_label'],o['country_code'],o['start_date'],o['end_date'])==(OID,EID,MID,SID,op['venue_label'],'Sydney','Australia','AU',START,END)
        assert o['evidence']['plan_sha256']==pin and o['evidence']['operation']==OP
    counts=dict(new_exhibitions=1,new_venue_stops=1,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
    if not (E/'independent-database-verification.json').exists():
        save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,verified_counts=counts,attribution='All counted rows absent in locked preimage. Persisted source/venue hashes and three null-before audits match own plan. Fresh read-only production transaction verifies relationships; prior and concurrent jobs excluded.',passed=True))
    else:assert c.load(E/'independent-database-verification.json')['rows']==rows
    u=API+'exhibitions/'+EID;r=requests.get(u,timeout=(15,45));r.raise_for_status();j=r.json();c.save(R/'public-exhibition.json',j)
    assert (j['id'],j['title'],j['startYear'],j['endYear'],j['entryCount'],j['checklistState'],j['state'],j['datePrecision'])==(EID,TITLE,1984,1984,0,'unknown','held','day')
    assert len(j['venues'])==1 and not j['participants']
    v=j['venues'][0];assert (v['id'],v['institution_id'],v['name'],v['city'],v['country'],v['start_date'],v['end_date'])==(OID,MID,op['venue_label'],'Sydney','Australia',START,END)
    if not (E/'independent-public-verification.json').exists():
        save('independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,url=u,status=r.status_code,body_sha256=c.sha(r.content),snapshot=str(R/'public-exhibition.json'),event_and_venue_independently_verified=True,zero_asserted_participants_and_entries_verified=True,passed=True))
    assert c.sha((B/'plan.json').read_bytes())==pin and c.load(B/'transaction-postimage.json')['rows']==rows
    assert c.sha((B/'transaction-preimage.json').read_bytes())==c.sha((E/'transaction-preimage.json').read_bytes())
    if not (E/'backup-verification.json').exists():
        save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']],preimage_absent=True,postimage_matches_fresh_read=True,passed=True))
    print(json.dumps(counts))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify']
    globals()[sys.argv[1]]()
