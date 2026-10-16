#!/usr/bin/env python3
"""One bounded National Gallery archive batch; external supervisor owns continuation."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000161'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000161'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000161'
OP='continuous-exhibitions-20261013-batch-000161'
INSTANCE='artline-508319:europe-west1:artline-postgres'
MID='2c909ffb-2614-4273-b76b-a0daa2a74833'
ACTOR='local-european-research'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']
EIDS=[c.uid('national-gallery-london-archive/'+x) for x in ['NG32/63','NG32/130']]
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
save=lambda n,x:c.save(E/n,x)

def target(db):
    cmd='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth '+INSTANCE
    assert cmd in [x.strip() for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    r=db.execute('select current_database() database,current_user role').fetchone()
    assert r==dict(database='artline',role='artline_app')
    return dict(at=c.now(),instance=INSTANCE,host=db.info.host,port=db.info.port,**r)

def snapshot(db):
    out={}
    for table in TABLES:
        col='id' if table=='exhibitions' else 'exhibition_id'
        out[table]=serial(db.execute('select * from '+table+' where '+col+'=any(%s::uuid[]) order by id',(EIDS,)).fetchall())
    out['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return out

def preserved(db):
    ids=[x['id'] for x in c.load(E/'live-reconciliation.json')['artworks']]
    aid=[x['creators'][0]['artist_id'] for x in c.load(E/'live-reconciliation.json')['artworks']]
    return serial(dict(
        artworks=db.execute('select * from artworks where id=any(%s::uuid[]) order by id',(ids,)).fetchall(),
        creators=db.execute('select * from artwork_artists where artwork_id=any(%s::uuid[]) order by artwork_id,artist_id',(ids,)).fetchall(),
        artists=db.execute('select * from artists where id=any(%s::uuid[]) order by id',(aid,)).fetchall(),
        aliases=db.execute('select * from artist_aliases where artist_id=any(%s::uuid[]) order by id',(aid,)).fetchall(),
        authorities=db.execute('select * from external_identifiers where entity_id=any(%s::uuid[]) order by id',(ids+aid,)).fetchall(),
        institution=db.execute('select * from institutions where id=%s',(MID,)).fetchone()))

def collisions(db):
    return serial(db.execute("""select e.id,e.title,e.start_year,e.end_year,e.date_display,e.import_batch,
      (select jsonb_agg(to_jsonb(o) order by o.id) from exhibition_occurrences o where o.exhibition_id=e.id) venues,
      (select jsonb_agg(jsonb_build_object('native',s.source_record_id,'url',s.source_url) order by s.id) from exhibition_source_records s where s.exhibition_id=e.id) sources
      from exhibitions e where e.id<>all(%s::uuid[]) and (
        e.title ilike any(%s) or e.alternate_titles::text ilike any(%s)
        or e.id in(select exhibition_id from exhibition_source_records where source_record_id in('NG32/63','NG32/130','NG30/1980/66') or source_url like '%%/NG32/63' or source_url like '%%/NG32/130' or source_url like '%%/NG30/1980/66')
        or ((e.start_year in(1965,1980) or e.end_year in(1965,1980)) and e.title ilike any(%s))
        or ((e.start_year is null or e.start_year<=1980) and (e.end_year is null or e.end_year>=1965) and e.id in(select exhibition_id from exhibition_occurrences where institution_id=%s or (venue_label ilike '%%national gallery%%' and city_label ilike '%%london%%'))))
        order by e.id""",(EIDS,['%second%sight%','%rembrandt%vermeer%','%titian%rembrandt%','%tizian%rembrandt%','%рембранд%вермеер%'],['%second%sight%','%rembrandt%vermeer%','%titian%rembrandt%'],['%rembrand%','%vermeer%','%titian%','%tizian%','%рембранд%','%тициан%','%вермеер%'],MID)).fetchall())

def checked_sources():
    d={}
    for key in ['NG32-63','NG32-130','NG30-1980-66','NG672','NG2568','NG1944','NG672-catalogue1991']:
        v=c.load(E/(key+'.json'));rc=v['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
        assert rc['status']==200 and c.sha(raw)==rc['sha256']
        assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==v['text']
        d[key]=v
    assert "Exhibition of Rembrandt's 'Self-portrait at the age of 34' and Vermeer's 'A young woman seated at a virginal'." in d['NG32-63']['text']
    assert "Held in the Board Room." in d['NG32-63']['text'] and '[1965]' in d['NG32-63']['text']
    assert "[8 Oct-7 Dec 1980]" in d['NG32-130']['text'] and "northern extension's Special Exhibition Room" in d['NG32-130']['text']
    assert "Hang includes Titian's 'A Man with a Quilted Sleeve' (NG1944) and Rembrandt's 'Self Portrait at the Age of 34' (NG672)." in d['NG30-1980-66']['text']
    return d

def prepare():
    src=checked_sources();live=c.load(E/'live-reconciliation.json');works={x['accession_number']:x for x in live['artworks']}
    assert len(works)==3 and len(live['institutions'])==1 and live['institutions'][0]['id']==MID and not live['exhibitions']
    for inv,w in works.items():
        txt=src[inv]['text']
        assert 'Inventory number '+inv in txt and w['dimensions_text'] in txt and w['title'] in txt
        assert 'Oil on canvas' in txt and w['work_type']=='painting' and w['current_institution_id']==MID
        assert w['creation_year_end']<1965 and w['creation_year_end']<=1970 and w['status']!='archived'
        assert len(w['creators'])==1 and w['creators'][0]['attribution_role']=='primary'
        assert any(x['scheme']=='european-ng-object' and x['external_id']==inv for x in w['identifiers'])
    with c.connect() as db:
        t=target(db);before=snapshot(db);old=preserved(db);matches=collisions(db)
        assert not any(before.values())
    if not (E/'duplicate-venue-snapshot.json').exists():
        save('duplicate-venue-snapshot.json',dict(at=c.now(),matches=matches))
    else:assert c.load(E/'duplicate-venue-snapshot.json')['matches']==matches
    if not (E/'duplicate-venue-review.json').exists():
        print('Review duplicate-venue-snapshot.json before preparing.');return
    dr=c.load(E/'duplicate-venue-review.json');assert dr['passed'] and dr['reviewed_ids']==[x['id'] for x in matches]
    for w in old['artworks']:
        expected={k:v for k,v in works[w['accession_number']].items() if k not in ['identifiers','creators']}
        assert w==expected
    events=[]
    for ix,(ref,title,year,start,end,display,precision,room,natives,source_keys) in enumerate([
        ('NG32/63','Rembrandt and Vermeer',1965,None,None,'[1965] (archive-supplied year; exact dates unknown)','year','Board Room',['NG672','NG2568'],['NG32-63']),
        ('NG32/130','Second sight: Titian/Rembrandt',1980,'1980-10-08','1980-12-07','8 October – 7 December 1980','day',"northern extension's Special Exhibition Room",['NG1944','NG672'],['NG32-130','NG30-1980-66'])]):
        eid=EIDS[ix];oid=c.uid('national-gallery-london-archive/'+ref+'/venue');sources=[]
        for sk in source_keys:
            native={'NG32-63':'NG32/63','NG32-130':'NG32/130','NG30-1980-66':'NG30/1980/66'}[sk]
            sources.append(dict(id=c.uid('national-gallery-london-archive/'+ref+'/source/'+native),native_id=native,key=sk,**src[sk]))
        entries=[];participants=[]
        for inv in natives:
            w=works[inv];person=w['creators'][0];sid=sources[-1]['id']
            historical_title={'NG672':'Self-portrait at the age of 34' if ix==0 else 'Self Portrait at the Age of 34','NG2568':'A young woman seated at a virginal','NG1944':'A Man with a Quilted Sleeve'}[inv]
            label={'NG672':'Rembrandt','NG2568':'Vermeer','NG1944':'Titian'}[inv]
            entries.append(dict(id=c.uid('national-gallery-london-archive/'+ref+'/entry/'+inv),artwork_id=w['id'],source_id=sid,inventory=inv,title=historical_title,creator=label,object_source=src[inv],date_label=w['date_display'],medium_label='Oil on canvas',dimensions_label=w['dimensions_text'],artist_id=person['artist_id']))
            participants.append(dict(id=c.uid('national-gallery-london-archive/'+ref+'/artist/'+person['artist_id']),artist_id=person['artist_id'],name=label,source_id=sid,inventory=inv))
        basis=('Official exhibition archive explicitly describes a held Board Room display; [1965] is supplied in brackets in the archive title and the separate Date field is empty. Preserve qualification; exact dates unknown.' if ix==0 else 'Official exhibition archive NG32/130 supplies held dates, Special Exhibition Room and attendance; separate photographic archive metadata NG30/1980/66 explicitly identifies two paintings in the hang and agrees on exhibition dates. The photograph item date is not substituted for exhibition dates.')
        events.append(dict(id=eid,native_id=ref,title=title,alternate_titles=['Exhibition: Rembrandt and Vermeer [1965]'] if ix==0 else ['Second Sight: Titian and Rembrandt','Exhibition: Second sight: Titian/Rembrandt [8 Oct-7 Dec 1980]'],year=year,start=start,end=end,date_display=display,date_precision=precision,date_qualified=ix==0,room=room,occurrence_id=oid,sources=sources,entries=entries,participants=participants,state_basis=basis))
    review=dict(at=c.now(),selected_distinct_exhibitions=2,exact_links=4,distinct_existing_artworks=3,artist_links=4,
        duplicate_review=dr,object_identity='National Gallery accession plus existing european-ng-object authority, current institution, exact dimensions, title, creation date and unqualified artist. NG1944 historical title and modern qualified sitter title are explicitly the same native painting. No copies or title-only matches.',
        source_roles='Exhibition archive and explicit archive hang description prove participation; collection pages prove only exact object identity. No installation photograph downloaded or visually interpreted. The1991 NG672 catalogue independently corroborates the1980 participation.',
        scope='Historical painting exhibitions1600–1989; no main artwork additions or exceptions needed.',
        date_review='NG32/63 bracketed year retained in display/evidence with null exact dates. NG32/130 exact dates supported by NG30/1980/66. Held status concerns occurrence; it does not remove date qualification.',
        venue_review='Existing National Gallery London institution with official domain and London GB place reused; Board Room and northern-extension Special Exhibition Room preserved separately in venue labels.',
        creators='Reuse existing unqualified primary creator links, reconciled against source names and lifetimes. All representation is posthumous; no personal attendance asserted.',
        checklist_state='partial',checklist_basis='Only two explicitly documented paintings per event; original catalogues/archival contents not inspected. Never claim completeness.',
        unknowns=['Exact1965 dates and independent year corroboration.','Complete checklists and catalogue numbers.','Organizers, lenders and sponsors.'],
        image_policy='No images downloaded; existing primary media untouched. National Gallery metadata access is not image licensing. No visual review claimed.',passed=True)
    p=dict(at=c.now(),operation=OP,target=t,events=events,identity_sources=src,preserved_entities=old,duplicate_matches=matches,review=review)
    save('plan.json',p);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);c.save(B/'plan.json',p)
    pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),receipts=[x['receipt'] for x in src.values()],all_raw_sha256_and_text_extractions_verified=True,originals_outside_Documents=True,reused_batch160_captures=2,new_captures=5,passed=True))
    print('Prepared2 exhibitions,2 stops,4 exact links,4 artist connections. Plan:',pin)

def audit(db,table,ident,pin):
    row=serial(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
    db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)",(ACTOR,table,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))

def apply():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256']
    assert p['operation']==OP and c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())==pin
    checked_sources()
    with c.connect(write=True) as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        before=snapshot(db)
        if before['exhibitions']:
            assert len(before['exhibitions'])==2 and all(x['import_batch']==OP for x in before['exhibitions'])
            assert (B/'transaction-preimage.json').exists() and all(x['interpretation']['plan_sha256']==pin for x in before['exhibition_source_records'])
            print('Own transaction already exists; no replay. Verify independently.');return
        assert not any(before.values()) and preserved(db)==p['preserved_entities'] and collisions(db)==p['duplicate_matches']
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=p['preserved_entities'],locks=['artline-curated-ingestion',2026101201])
        save('transaction-preimage.json',pre);c.save(B/'transaction-preimage.json',pre)
        save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        base=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],checklist_complete=False,no_current_display_claim=True,no_holding_claim=True,organizer_unknown=True,lenders_unknown=True,sponsors_unknown=True)
        inserted=[]
        for e in p['events']:
            db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)""",(e['id'],e['title'],c.norm(e['title']),Jsonb(e['alternate_titles']),e['start'],e['end'],e['year'],e['year'],e['date_display'],e['date_precision'],e['state_basis']+' Assessed '+p['at']+'.',OP))
            inserted.append(('exhibitions',e['id']))
            for s in e['sources']:
                rc=s['receipt']
                db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
                  values(%s,%s,'national-gallery-london-official-archive',%s,%s,%s,%s,%s,%s,%s)""",(s['id'],e['id'],s['native_id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(source_text=s['text'],receipt=rc,review=p['review'],object_identity_sources=[x['object_source'] for x in e['entries']],corroborating_catalogue=p['identity_sources']['NG672-catalogue1991'] if e['year']==1980 else None)),Jsonb(base|dict(original_native_id=s['native_id'],date_qualified=e['date_qualified']))))
                inserted.append(('exhibition_source_records',s['id']))
            db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
              values(%s,%s,%s,%s,%s,'London','United Kingdom','GB',%s,%s,%s,%s)""",(e['occurrence_id'],e['id'],e['sources'][0]['id'],MID,'National Gallery — '+e['room'],e['start'],e['end'],e['date_display'],Jsonb(base|dict(room_source_wording=e['room'],date_qualified=e['date_qualified'],venue_basis=p['review']['venue_review']))))
            inserted.append(('exhibition_occurrences',e['occurrence_id']))
            for x in e['entries']:
                db.execute("""insert into exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis)
                  values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)""",(x['id'],e['id'],x['source_id'],e['occurrence_id'],x['artwork_id'],x['inventory'],x['title'],x['creator'],x['date_label'],x['medium_label'],x['dimensions_label'],Jsonb(base|dict(inventory=x['inventory'],object_identity_receipt=x['object_source']['receipt'],historical_title_preserved=True,object_fields_basis='Current museum object identity record; not a transcription of the original exhibition catalogue.',catalogue_number_unknown=True,participation_basis=e['state_basis'])),p['review']['object_identity']))
                inserted.append(('exhibition_entries',x['id']))
            for x in e['participants']:
                db.execute("""insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)
                  values(%s,%s,%s,%s,%s,'artist',%s)""",(x['id'],e['id'],x['source_id'],x['artist_id'],x['name'],Jsonb(base|dict(posthumous=True,personal_attendance=False,documented_work=x['inventory'],identity_basis=p['review']['creators']))))
                inserted.append(('exhibition_participants',x['id']))
        for table,ident in inserted:audit(db,table,ident,pin)
        assert len(inserted)==15 and preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independent verification pending.')

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply']
    globals()[sys.argv[1]]()
