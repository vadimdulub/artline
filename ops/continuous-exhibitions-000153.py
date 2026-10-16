#!/usr/bin/env python3
"""Bounded historical Hockney tour delivery. External supervisor remains untouched."""
import fcntl, gzip, json, os, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000153'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000153'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000153'
Q=E.parents[1]/'source-queue.json'
OP='continuous-exhibitions-20261013-batch-000153'
ACTOR='local-european-research'
INSTANCE='artline-508319:europe-west1:artline-postgres'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
AID='e97b0a52-9f98-4808-8f20-d47cd7ac33dc'
EID=c.uid('ngv/exhibition/260305')
NGV='10f88aa8-da2e-58a1-99f1-dc7c360f55b7'
NSW='d3524dc2-2672-582f-be42-4bf3c8ace210'
SA='a8b66dee-f7b9-5059-8963-b4b72406fd62'
MIDS=[NGV,NSW,SA]

def serial(x): return json.loads(json.dumps(x,ensure_ascii=False,default=str))
def save(n,x): c.save(E/n,x)
def target(db):
    cmd='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth '+INSTANCE
    assert cmd in [x.strip() for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    r=db.execute('select current_database() database,current_user role').fetchone()
    assert r==dict(database='artline',role='artline_app')
    return dict(instance=INSTANCE,host=db.info.host,port=db.info.port,**r,checked_at=c.now())

def preserved(db):
    return serial(dict(artist=db.execute('select * from artists where id=%s',(AID,)).fetchone(),
        institutions=db.execute('select * from institutions where id=any(%s::uuid[]) order by id',(MIDS,)).fetchall()))

def snapshot(db):
    out={}
    for t in ['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']:
        col='id' if t=='exhibitions' else 'exhibition_id'
        out[t]=serial(db.execute('select * from '+t+' where '+col+'=%s order by id',(EID,)).fetchall())
    out['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return out

def collisions(db):
    return serial(db.execute("""select distinct e.id,e.title,e.start_year,e.end_year,e.import_batch
        from exhibitions e left join exhibition_source_records s on s.exhibition_id=e.id
        where e.id=%s or s.source_url like '%%/exhibition/david-hockney-prints/%%'
        or s.source_url='https://printsandprintmaking.gov.au/exhibitions/3296/'
        or ((e.title ilike '%%hockney%%' or e.alternate_titles::text ilike '%%hockney%%')
          and (e.start_year is null or e.start_year<=1978) and (e.end_year is null or e.end_year>=1976))""",(EID,)).fetchall())

def checked_capture(record):
    rc=record['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert rc['status']==200 and c.sha(raw)==rc['sha256']
    return BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)

def prepare():
    ngv=c.load(E.parents[1]/'batches/000152/hockney-tour-lead-verification.json')
    pp=c.load(E/'apj-tour-capture.json');nt=checked_capture(ngv);pt=checked_capture(pp)
    assert 'A collection of David Hockney prints on loan from the National Gallery of Australia.' in nt
    assert 'Single-artist travelling exhibition.' in pt and 'National Gallery of Australia is an Australian Government Agency' in pt
    ngv_sid=c.uid('ngv/exhibition/260305/source');pp_sid=c.uid('australian-prints-and-printmaking/exhibition/3296/source')
    sources=[dict(id=ngv_sid,key='ngv-official-exhibition-page',native='260305',receipt=ngv['receipt'],text=ngv['source_text']),
             dict(id=pp_sid,key='australian-prints-and-printmaking-exhibition',native='3296',receipt=pp['receipt'],text=pp['text'])]
    # Exact days only where explicitly supplied and not contradicted by another archive.
    # Other stop dates retain the literal month ranges, never manufactured day bounds.
    specs=[
      ('NGV International','22 Apr – 6 Jun 76','1976-04-22','1976-06-06',NGV,'Melbourne',None,None,'1976-04','1976-06'),
      ('Art Gallery of New South Wales','Jul – Aug 76','1976-07-31','1976-08-29',NSW,'Sydney','949','31 July 1976 – 29 August 1976','1976-07','1976-08'),
      ('Queensland Art Gallery','Sep 76',None,None,None,'Brisbane','700','8 September 1976 – 1 October 1976','1976-09',None),
      ('Rockhampton Art Gallery','Oct – Nov 76',None,None,None,None,None,None,'1976-10','1976-11'),
      ('University of Western Australia','Feb 77',None,None,None,None,None,None,'1977-02','1977-02'),
      ('Art Gallery of South Australia','Mar – Apr 77',None,None,SA,'Adelaide',None,None,'1977-03','1977-04'),
      ('Geelong Art Gallery','Jul 77',None,None,None,None,None,None,'1977-07','1977-07'),
      ('Tasmanian Museum and Art Gallery','Aug – Sep 77',None,None,None,'Hobart','591','14 September 1977 – 9 October 1977',None,None),
      ('Queen Victoria Museum and Art Gallery','Oct 77',None,None,None,None,None,None,'1977-10','1977-10'),
      ('Hamilton City Art Gallery','Nov 77',None,None,None,None,None,None,'1977-11','1977-11'),
      ('Benalla City Art Gallery','Dec 77','1977-12-05','1977-12-22',None,'Benalla','537','5 December 1977 – 22 December 1977','1977-12','1977-12'),
      ('Shepparton Art Gallery','Jan – Feb 78',None,None,None,None,None,None,'1978-01','1978-02'),
      ('Midura Arts Centre','Feb – Mar 78',None,None,None,None,None,None,'1978-02','1978-03'),
      ('Ararat Art Gallery','Mar – Apr 78','1978-03-22','1978-04-25',None,'Ararat','1218','22 March 1978 – 25 April 1978','1978-03','1978-04'),
      ('Bendigo Art Gallery',None,'1978-04-01','1978-04-30',None,'Bendigo','290','1 April 1978 – 30 April 1978','1978-04','1978-04'),
      ('Newcastle City Art Gallery','May – Jun 78',None,None,None,None,None,None,'1978-05','1978-06')]
    stops=[];identity_receipts=[]
    for index,(label,literal,start,end,mid,city,native,pp_date,sm,em) in enumerate(specs,1):
        if literal: assert literal in nt and label in nt
        if pp_date: assert pp_date in pt
        conflict=label in ['Queensland Art Gallery','Tasmanian Museum and Art Gallery']
        evidence=dict(source_venue_label=label,ngv_period=literal,prints_au_period=pp_date,date_conflict=conflict,
            source_start_month=sm,source_end_month=em,sequence=index,
            date_precision='conflicting' if conflict else ('day' if start else 'month'),
            exact_days_unknown=start is None,canonical_institution_unresolved=mid is None)
        if native:
            ident=c.load(E/('venue-'+native+'.json'));it=checked_capture(ident)
            assert city in it and 'Australia' in it
            evidence['venue_identity_receipt']=ident['receipt'];identity_receipts.append(ident['receipt'])
        if label=='Queensland Art Gallery':evidence['historical_identity_note']='Prints + Printmaking identifies historical Queensland Art Gallery [1], closed 1981. Modern QAG institution/location not forced; historical label and source venue ID retained.'
        if label=='Hamilton City Art Gallery':evidence['identity_hold']='Same historical name occurs in Australia and New Zealand. No city/country/canonical institution chosen without event-specific corroboration.'
        if label=='Midura Arts Centre':evidence['identity_hold']='NGV source spelling Midura retained; existing Mildura institution is a likely lead but not linked without corroboration.'
        if label=='Bendigo Art Gallery':evidence['itinerary_note']='Additional stop explicitly related to this tour by Prints + Printmaking; dates overlap Ararat. No separate exhibition or duplicated artwork set inferred.'
        if label=='NGV International':
            evidence['geography_basis']='Original 111-source institution registry; source exact institution label.'
        if label=='Art Gallery of South Australia':
            ident=c.load(E/'agsa-identity-capture.json');it=checked_capture(ident)
            assert 'Adelaide, South Australia' in it and 'Art Gallery of South Australia' in it
            evidence['geography_basis']='Official AGSA visitor page corroborates institutional identity in Adelaide; no exact historical building/room asserted.'
            evidence['venue_identity_receipt']=ident['receipt'];identity_receipts.append(ident['receipt'])
        display=(literal+' [NGV]; '+pp_date+' [Prints + Printmaking]; dates conflict') if conflict else (start+' – '+end if start else literal)
        stops.append(dict(id=c.uid('ngv/exhibition/260305/stop/'+c.norm(label)),source_id=pp_sid if label=='Bendigo Art Gallery' else ngv_sid,
            label=label,start=start,end=end,date_display=display,institution_id=mid,city=city,
            country='Australia' if city else None,country_code='AU' if city else None,
            source_venue_id='prints-au-gallery/'+native if native else None,evidence=evidence))
    with c.connect() as db:
        t=target(db);old=preserved(db);assert not collisions(db) and not any(snapshot(db).values())
        assert old['artist']['display_name']=='David Hockney' and len(old['institutions'])==3
    review=dict(at=c.now(),selected_distinct_exhibitions=1,ngv_stops=15,prints_au_additional_stops=1,total_stops=16,
        shared_identity='Same named print artist, Australian National Gallery collection/travelling exhibition and 1976–1978 period, five matching host institutions and compatible dates at Sydney, Benalla and Ararat. Two conflicting stop periods retained.',
        duplicate_review='Live title/alternate-title/source-URL/native-ID and overlapping venue/year reconciliation found no matching tour. Blue Guitar 1979 is separate. Prior batch152 and separate SMK campaign excluded.',
        unknowns=['Organizer role not explicitly identified; collection lender is not silently made organizer.','Exact final closing day unknown; June 1978 retained at month precision.','Hamilton historical institution and country unresolved.','Midura source spelling retained; Mildura institution match held.','Nine stops have only month precision; two have contradictory source periods.','Original contemporary checklist uninspected; no exact objects inferred.'],
        curator_label='Palmer, Tony. (Prints + Printmaking assertion)',lender_label='National Gallery of Australia (NGV explicit loan statement)',
        poster_role='NGV page includes a poster link; no image downloaded or linked, rights unreviewed.',
        checklist_state='unknown',images_selected=0,visual_review_claimed=False,passed=True)
    p=dict(at=c.now(),operation=OP,target=t,exhibition=dict(id=EID,title='David Hockney Prints: Selected from the Collection of the Australian National Gallery, Canberra',
        alternate_titles=['David Hockney: Prints [1976].','Australian National Gallery travelling exhibition.'],start='1976-04-22',end=None,start_year=1976,end_year=1978,date_display='22 April 1976 – June 1978',date_precision='mixed'),
        sources=sources,identity_receipts=identity_receipts,stops=stops,participant=dict(id=c.uid('ngv/exhibition/260305/artist'),artist_id=AID,name='David Hockney',source_id=ngv_sid),
        preserved_entities=old,review=review,scope='Exhibitions 1600–1989, pictorial media. No new main works; through-1970 rule unchanged.')
    assert len(stops)==16 and len({s['id'] for s in stops})==16
    save('plan-v2.json',p);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);c.save(B/'plan-v2.json',p)
    pin=c.sha((E/'plan-v2.json').read_bytes());save('plan-pin-v2.json',dict(operation=OP,sha256=pin));save('candidate-review-verification-v2.json',review)
    save('source-capture-verification-v2.json',dict(at=c.now(),plan_sha256=pin,receipts=[s['receipt'] for s in sources]+identity_receipts,
        original_bodies_outside_Documents=True,all_body_sha256_verified=True,prior_ngv_capture_reused=True,search_snippets_not_used_as_delivery_evidence=True,passed=True))
    print('Prepared one shared tour, sixteen stops and one existing artist link.',flush=True)

def audit(db,table,typ,ident,pin):
    row=serial(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
    db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)",
        (ACTOR,typ,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))

def apply():
    p=c.load(E/'plan-v2.json');pin=c.load(E/'plan-pin-v2.json')['sha256']
    assert p['operation']==OP and c.sha((E/'plan-v2.json').read_bytes())==c.sha((B/'plan-v2.json').read_bytes())==pin
    with c.connect(write=True) as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('select pg_advisory_xact_lock(2026101201)');before=snapshot(db)
        if before['exhibitions']:
            assert len(before['exhibitions'])==1 and before['exhibitions'][0]['import_batch']==OP
            assert (B/'transaction-preimage.json').exists() and len(before['exhibition_source_records'])==2
            assert all(x['interpretation']['plan_sha256']==pin for x in before['exhibition_source_records'])
            print('Own committed transaction exists. No replay; independent verification required.');return
        assert not any(before.values()) and not collisions(db) and preserved(db)==p['preserved_entities']
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=preserved(db),locks=['artline-curated-ingestion',2026101201])
        c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre)
        save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        ex=p['exhibition'];base=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],exhibition_type='single-artist travelling print exhibition',
            checklist_complete=False,organizer_unknown=True,lender_label=p['review']['lender_label'],curator_label=p['review']['curator_label'],
            source_assertions_distinguished=True,object_participation_unknown=True,no_current_display_claim=True)
        db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','unknown','review',%s)""",
            (EID,ex['title'],c.norm(ex['title']),Jsonb(ex['alternate_titles']),ex['start'],ex['end'],ex['start_year'],ex['end_year'],ex['date_display'],ex['date_precision'],
             'Two institutional retrospective archives document one historical travelling print exhibition. Date-status assessed '+p['at']+'. Two stop-date conflicts retained; exact final closing day and original checklist unknown.',OP))
        audit(db,'exhibitions','exhibition',EID,pin)
        for s in p['sources']:
            rc=s['receipt']
            db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(s['id'],EID,s['key'],s['native'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],
                Jsonb(dict(source_text=s['text'],receipt=rc,review=p['review'])),Jsonb(base)))
            audit(db,'exhibition_source_records','exhibition_source_record',s['id'],pin)
        for s in p['stops']:
            db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,source_venue_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(s['id'],EID,s['source_id'],s['institution_id'],s['source_venue_id'],s['label'],s['city'],s['country'],s['country_code'],s['start'],s['end'],s['date_display'],Jsonb(base|s['evidence'])))
            audit(db,'exhibition_occurrences','exhibition_occurrence',s['id'],pin)
        a=p['participant']
        db.execute("insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) values(%s,%s,%s,%s,%s,'artist',%s)",
            (a['id'],EID,a['source_id'],a['artist_id'],a['name'],Jsonb(base|dict(participation_basis='NGV explicitly describes a collection of David Hockney prints on loan. Works represented; personal attendance not asserted.'))))
        audit(db,'exhibition_participants','exhibition_participant',a['id'],pin)
        assert preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True))
    print('Transaction committed; independent verification pending.',flush=True)

def verify():
    p=c.load(E/'plan-v2.json');pin=c.load(E/'plan-pin-v2.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
    assert c.sha((E/'plan-v2.json').read_bytes())==pin==pre['plan_sha256'] and not any(pre['rows'].values())
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        assert preserved(db)==p['preserved_entities']
        for table,n in dict(exhibitions=1,exhibition_source_records=2,exhibition_occurrences=16,exhibition_participants=1,exhibition_entries=0,exhibition_publications=0).items(): assert len(rows[table])==n,(table,len(rows[table]))
        au=[a for a in rows['audits'] if a['action']=='continuous_exhibition_insert'];assert len(au)==20
        assert all(a['before_json'] is None and a['after_json']['plan_sha256']==pin for a in au)
        ex=rows['exhibitions'][0];ep=p['exhibition']
        assert (ex['id'],ex['title'],ex['start_date'],ex['end_date'],ex['start_year'],ex['end_year'],ex['date_display'],ex['date_precision'],ex['status'],ex['event_state'],ex['checklist_state'],ex['import_batch'])==(EID,ep['title'],ep['start'],None,1976,1978,ep['date_display'],'mixed','review','held','unknown',OP)
        assert ex['alternate_titles']==ep['alternate_titles']
        for s in p['sources']:
            sr=next(x for x in rows['exhibition_source_records'] if x['id']==s['id']);rc=s['receipt']
            assert (sr['exhibition_id'],sr['source_key'],sr['source_record_id'],sr['source_url'],sr['capture_sha256'])==(EID,s['key'],s['native'],rc['url'],rc['sha256'])
            assert sr['interpretation']['operation']==OP and sr['interpretation']['plan_sha256']==pin
            assert sr['source_payload']['source_text']==s['text']
        for s in p['stops']:
            row=next(x for x in rows['exhibition_occurrences'] if x['id']==s['id'])
            assert (row['exhibition_id'],row['source_record_id'],row['institution_id'],row['source_venue_id'],row['venue_label'],row['city_label'],row['country_label'],row['country_code'],row['start_date'],row['end_date'],row['date_display'])==(EID,s['source_id'],s['institution_id'],s['source_venue_id'],s['label'],s['city'],s['country'],s['country_code'],s['start'],s['end'],s['date_display'])
            assert row['evidence']['operation']==OP and row['evidence']['plan_sha256']==pin
            assert all(row['evidence'][k]==v for k,v in s['evidence'].items())
        a=rows['exhibition_participants'][0];assert (a['id'],a['exhibition_id'],a['artist_id'],a['name_label'],a['role'],a['source_record_id'])==(p['participant']['id'],EID,AID,'David Hockney','artist',p['participant']['source_id'])
        assert a['evidence']['operation']==OP and a['evidence']['plan_sha256']==pin
    counts=dict(new_exhibitions=1,new_venue_stops=16,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=1,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
    if (E/'independent-database-verification.json').exists():
        prior=c.load(E/'independent-database-verification.json')
        assert prior['passed'] and prior['rows']==rows and prior['plan_sha256']==pin and prior['verified_counts']==counts
    else:
        save('independent-database-verification.json',dict(at=c.now(),target=t,operation=OP,plan_sha256=pin,rows=rows,verified_counts=counts,
            attribution='All counted rows absent in locked preimage; persisted source/relationship checksums and 20 null-before audit records match this plan. Fresh read-only transaction verifies all rows and existing-entity preservation. Prior jobs excluded.',passed=True))
    u=API+'exhibitions/'+EID;r=requests.get(u,timeout=(15,45));r.raise_for_status();j=r.json();c.save(R/'public-exhibition.json',j)
    assert (j['id'],j['title'],j['startYear'],j['endYear'],j['entryCount'])==(EID,p['exhibition']['title'],1976,1978,0)
    assert len(j['venues'])==16 and len(j['participants'])==1 and j['participants'][0]['artist_id']==AID
    assert j['checklistState']=='unknown' and j['datePrecision']=='mixed' and j['state']=='held'
    for s in p['stops']:
        v=next(x for x in j['venues'] if x['id']==s['id'])
        assert v.get('institution_id')==s['institution_id'] and v['name']==s['label']
        for k,pkey in [('start_date','start'),('end_date','end'),('city','city'),('country','country')]:assert v.get(k)==s[pkey],(k,v.get(k),s[pkey])
    save('independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,url=u,status=r.status_code,body_sha256=c.sha(r.content),public_snapshot=str(R/'public-exhibition.json'),all_16_venue_relationships_and_exposed_day_fields_verified=True,artist_relationship_verified=True,
        public_schema_gap='Public venue objects omit date_display and evidence. Month-only ranges and conflicting periods are preserved and independently verified in production database rows, but are not exposed at venue level by this API. No migration or deployment performed.',passed=True))
    assert c.sha((B/'plan-v2.json').read_bytes())==pin and c.sha((B/'transaction-preimage.json').read_bytes())==c.sha((E/'transaction-preimage.json').read_bytes())
    assert c.load(B/'transaction-postimage.json')['rows']==rows
    save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['plan-v2.json','transaction-preimage.json','transaction-postimage.json']],preimage_absent=True,postimage_matches_fresh_read=True,passed=True))
    print(json.dumps(counts),flush=True)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify']
    globals()[sys.argv[1]]()
