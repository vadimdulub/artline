#!/usr/bin/env python3
"""One bounded National Gallery archive batch; external supervisor owns continuation."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000164'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000164'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000164'
OP='continuous-exhibitions-20261013-batch-000164'
INSTANCE='artline-508319:europe-west1:artline-postgres'
MID='2c909ffb-2614-4273-b76b-a0daa2a74833'
ACTOR='local-european-research'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']
EIDS=[c.uid('national-gallery-london-archive/'+x) for x in ['NG32/133']]
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
    ids=['4de918df-83c6-4f9c-9892-741b133c56b6','68a587fd-a9b2-5ea4-9c98-54e910944161']
    aid=['e23c26f2-d022-4b0c-8319-138ee7ffb169','56aa94b3-4f41-4760-a5f8-34027e7bb7e1']
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
        or e.id in(select exhibition_id from exhibition_source_records where source_record_id in('NG32/133','NG30/1981/4') or source_url like '%%/NG32/133' or source_url like '%%/NG30/1981/4')
        or ((e.start_year between 1979 and 1983 or e.end_year between 1979 and 1983) and e.title ilike any(%s))
        or ((e.start_year is null or e.start_year<=1981) and (e.end_year is null or e.end_year>=1981) and e.id in(select exhibition_id from exhibition_occurrences where institution_id=%s or (venue_label ilike '%%national gallery%%' and city_label ilike '%%london%%')))) order by e.id""",(EIDS,['%second%sight%','%rubens%gainsborough%','%рубенс%гейнсборо%'],['%second%sight%','%rubens%gainsborough%'],['%rubens%','%gainsborough%','%рубенс%','%гейнсборо%'],MID)).fetchall())

def checked_sources():
    out={}
    for key in ['NG32-133','NG30-1981-4','NG109','NG4815','wikiart-NG109']:
        v=c.load(E/(key+'.json'));rc=v['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
        assert rc['status']==200 and c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes']
        assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==v['text'];out[key]=v
    assert '[18 Feb-20 Apr 1981]' in out['NG32-133']['text']
    assert "northern extension's Special Exhibition Room" in out['NG32-133']['text']
    assert "Hang includes Rubens's 'The Watering Place' (NG4815) and Gainsborough's 'The Watering Place' (NG109)." in out['NG30-1981-4']['text']
    assert '18 Feb-20 Apr 1981' in out['NG30-1981-4']['text']
    assert 'Inventory number NG109' in out['NG109']['text'] and '147.3 × 180.3 cm' in out['NG109']['text']
    assert 'Before 1777' in out['NG109']['text'] and 'Thomas Gainsborough' in out['NG109']['text']
    assert 'Location: National Gallery, London, UK' in out['wikiart-NG109']['text'] and 'Dimensions: 147 x 180 cm' in out['wikiart-NG109']['text']
    assert 'Inventory number NG4815' in out['NG4815']['text'] and '99.4 × 135 cm' in out['NG4815']['text']
    return out

def prepare():
    src=checked_sources();live=c.load(E/'live-reconciliation.json');broad=c.load(E/'broad-reconciliation.json')
    works={x['accession_number']:x for x in live['artworks']};works['NG109']=next(x for x in broad['artworks']if x['id']=='68a587fd-a9b2-5ea4-9c98-54e910944161')
    assert len(works)==2 and live['institution']['id']==MID
    with c.connect()as db:
        t=target(db);before=snapshot(db);old=preserved(db);matches=collisions(db)
        assert not any(before.values())
    save('duplicate-venue-snapshot.json',dict(at=c.now(),matches=matches))
    assert len(matches)==1 and matches[0]['id']=='77d4d1de-f702-5127-94b8-8dac551a1c1b' and matches[0]['start_year']==1980
    dr=dict(at=c.now(),reviewed_ids=[r['id']for r in matches],decision='Only Second sight: Titian/Rembrandt1980 overlaps title/venue query. Distinct artists, exact dates and archiveNG32/130 establish separate event. Broad1979–1983 artist-title query additionally returned two unrelated titles in France and video; none matchesNG32/133.',passed=True)
    save('duplicate-venue-review.json',dr)
    for inv,w in works.items():
        assert next(x for x in old['artworks']if x['id']==w['id'])=={k:v for k,v in w.items()if k not in ['identifiers','creators']}
        assert len(w['creators'])==1 and w['creators'][0]['attribution_role']=='primary'
        assert w['creation_year_end']<1981 and w['work_type']=='painting'
    ref='NG32/133';eid=EIDS[0];oid=c.uid('national-gallery-london-archive/'+ref+'/venue')
    sources=[dict(id=c.uid('national-gallery-london-archive/'+ref+'/source/'+native),native_id=native,key=key,**src[key])for native,key in [('NG32/133','NG32-133'),('NG30/1981/4','NG30-1981-4')]]
    entries=[];participants=[]
    for inv in ['NG4815','NG109']:
        w=works[inv];person=w['creators'][0];label='Rubens' if inv=='NG4815' else 'Gainsborough';sid=sources[-1]['id']
        entries.append(dict(id=c.uid('national-gallery-london-archive/'+ref+'/entry/'+inv),artwork_id=w['id'],source_id=sid,inventory=inv,title='The Watering Place',creator=label,object_source=src[inv],date_label='About 1615-22' if inv=='NG4815' else 'Before 1777',medium_label='Oil on wood (probably oak)' if inv=='NG4815' else 'Oil on canvas',dimensions_label='99.4 × 135 cm' if inv=='NG4815' else '147.3 × 180.3 cm',artist_id=person['artist_id']))
        participants.append(dict(id=c.uid('national-gallery-london-archive/'+ref+'/artist/'+person['artist_id']),artist_id=person['artist_id'],name=label,source_id=sid,inventory=inv))
    basis='Official event archiveNG32/133 documents the held exhibition and107,772 visitors. Independent archiveNG30/1981/4 explicitly identifies both paintings in the hang and confirms18February–20April1981. March1981 dates the contact sheet only.'
    ev=dict(id=eid,native_id=ref,title='Second sight: Rubens/Gainsborough',alternate_titles=['Second Sight: Rubens and Gainsborough','Exhibition: Second sight: Rubens/Gainsborough [18 Feb-20 Apr 1981]'],year=1981,start='1981-02-18',end='1981-04-20',date_display='18 February – 20 April 1981',date_precision='day',date_qualified=False,room="northern extension's Special Exhibition Room",occurrence_id=oid,sources=sources,entries=entries,participants=participants,state_basis=basis)
    review=dict(at=c.now(),selected_distinct_exhibitions=1,exact_links=2,distinct_existing_artworks=2,artist_links=2,duplicate_review=dr,
        object_identity='Rubens: exactNG4815 accession and european-ng-object identity, maker, panel, dimensions99.4x135cm, circa1615–1622 and existing institution. Gainsborough: existing WikiArt native5772765cedc2cb3880d14877 explicitly names same painting, creator, National Gallery London, oil/canvas and rounded147x180cm matching officialNG109147.3x180.3cm. Its1777 date differs from official Before1777: retain both assertions, do not rewrite main record. Museum describes its related etching as compositionally different; MIA8847 is a separate aquatint, excluded. No title-only match.',
        source_roles='Exhibition archive and explicit archival hang description prove participation. Museum object pages and WikiArt prove exact object identity only. No installation view visually interpreted.',
        scope='Painting exhibition1981 within1600–1989. Existing17th/18th-century paintings reused; no creation exception.',
        date_review='Two official archival records agree on event dates. Photography archive item dateMarch1981 is not the exhibition date. Gainsborough creation-date conflict retained in entry and source evidence; existing main artwork unchanged.',
        venue_review='Reuse existing National Gallery London institution; northern-extension Special Exhibition Room retained as historical subvenue. No museum holding or current-display assertions created.',
        creators='Existing Peter Paul Rubens1577–1640 and Thomas Gainsborough1727–1788 match official unqualified artist names and lifetimes. Gainsborough Dupont is distinct and excluded. Both participants posthumous; no personal attendance.',
        checklist_state='partial',checklist_basis='Only two explicitly documented exhibited paintings. No complete original checklist inspected.',
        unknowns=['Original full checklist, catalogue numbers, lenders, organizers and sponsors.'],
        image_policy='No new images downloaded or prepared. Existing Gainsborough primary media unchanged; Rubens image gap retained. No visual review claimed.',passed=True)
    p=dict(at=c.now(),operation=OP,target=t,events=[ev],identity_sources=src,preserved_entities=old,duplicate_matches=matches,review=review)
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);save('plan.json',p);c.save(B/'plan.json',p);pin=c.sha((E/'plan.json').read_bytes())
    save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),receipts=[v['receipt']for v in src.values()],all_capture_checksums_and_extracted_text_verified=True,reused_batch161_captures=1,originals_outside_Documents=True,passed=True))
    print('Prepared one event, one venue stop, two exact links and two artist connections.',flush=True)

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
            assert len(before['exhibitions'])==1 and all(x['import_batch']==OP for x in before['exhibitions'])
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
        assert len(inserted)==8 and preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independent verification pending.')

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply']
    globals()[sys.argv[1]]()
