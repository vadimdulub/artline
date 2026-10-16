#!/usr/bin/env python3
"""Bounded, checksum-pinned National Gallery archive delivery; no supervisor changes."""
import gzip,json,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c
ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000168'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000168'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000168'
OP='continuous-exhibitions-20261013-batch-000168'
INSTANCE='artline-508319:europe-west1:artline-postgres'
MID='2c909ffb-2614-4273-b76b-a0daa2a74833'
ACTOR='local-european-research'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
REF='NG32/127';EID=c.uid('national-gallery-london-archive/'+REF)
AIDS=['22910ad1-23c3-42b1-94d0-c0ba32681f3b','d6e11ae7-c271-4b19-92d8-71c00c865288']
WIDS=['95f02174-f902-4f3f-ab9f-3b7260032d38','055e8d15-d5e0-4cbd-a316-909983bf505b']
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']
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
        out[table]=serial(db.execute('select * from '+table+' where '+col+'=%s order by id',(EID,)).fetchall())
    out['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return out

def preserved(db):
    return serial(dict(artworks=db.execute('select * from artworks where id=any(%s::uuid[]) order by id',(WIDS,)).fetchall(),
      creators=db.execute('select * from artwork_artists where artwork_id=any(%s::uuid[]) order by artwork_id,artist_id',(WIDS,)).fetchall(),
      artists=db.execute('select * from artists where id=any(%s::uuid[]) order by id',(AIDS,)).fetchall(),
      aliases=db.execute('select * from artist_aliases where artist_id=any(%s::uuid[]) order by id',(AIDS,)).fetchall(),
      authorities=db.execute('select * from external_identifiers where entity_id=any(%s::uuid[]) order by id',(WIDS+AIDS,)).fetchall(),
      media=db.execute('select * from media_assets where id in(select primary_media_id from artworks where id=any(%s::uuid[]))order by id',(WIDS,)).fetchall(),
      institution=db.execute('select * from institutions where id=%s',(MID,)).fetchone()))

def collisions(db):
    return serial(db.execute("""select e.id,e.title,e.start_year,e.end_year,e.date_display,e.import_batch,
      (select jsonb_agg(to_jsonb(o) order by o.id) from exhibition_occurrences o where o.exhibition_id=e.id) venues,
      (select jsonb_agg(jsonb_build_object('native',s.source_record_id,'url',s.source_url) order by s.id) from exhibition_source_records s where s.exhibition_id=e.id) sources
      from exhibitions e where e.id<>%s and (
      e.title ilike any(%s) or e.alternate_titles::text ilike any(%s)
      or e.id in(select exhibition_id from exhibition_source_records where source_record_id in('NG32/127','NG60/48') or source_url like '%%/NG32/127' or source_url like '%%/NG60/48')
      or ((e.start_year between 1979 and 1981 or e.end_year between 1979 and 1981) and e.title ilike any(%s))
      or ((e.start_year is null or e.start_year<=1980) and (e.end_year is null or e.end_year>=1980) and e.id in(select exhibition_id from exhibition_occurrences where institution_id=%s or (venue_label ilike '%%national gallery%%' and city_label ilike '%%london%%')))) order by e.id""",
      (EID,['%second%sight%','%claude%turner%','%turner%claude%','%dido%carthage%','%клод%тернер%'],['%second%sight%','%claude%turner%','%dido%carthage%'],['%claude%','%turner%','%клод%','%тёрнер%','%тернер%'],MID)).fetchall())

def checked_sources():
    out={}
    for key in ['NG32-127','NG24-1980-10','NG60-48','NG14','NG498']:
        v=c.load(E/(key+'.json'));rc=v['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
        assert rc['status']==200 and c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes']
        assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==v['text'];out[key]=v
    assert '[14 Feb-13 Apr 1980]' in out['NG32-127']['text'] and '119,044 visitors' in out['NG32-127']['text']
    assert "northern extension's Special Exhibition Room" in out['NG32-127']['text']
    assert 'Paintings referenced in this record NG14 , NG498' in out['NG32-127']['text']
    assert '14 February-13 April 1980' in out['NG24-1980-10']['text']
    assert '"The Embarkation of the Queen of Sheba" by Claude and "Dido building Carthage or the Rise of the Carthaginian Empire" by Turner' in out['NG24-1980-10']['text']
    assert 'Date 14 Feb-13 Apr 1980' in out['NG60-48']['text']
    for key,dim in [('NG14','149.1 × 196.7 cm'),('NG498','155.5 × 230 cm')]:
        assert 'Inventory number '+key in out[key]['text'] and dim in out[key]['text']
        assert 'M. Wilson, Claude: Embarkation of the Queen of Sheba and Turner: Dido building Carthage (exh. cat. The National Gallery, London, 14 February - 13 April 1980), London 1980' in out[key]['text']
    return out

def prepare():
    src=checked_sources()
    with c.connect() as db:
        t=target(db);before=snapshot(db);old=preserved(db);matches=collisions(db)
        exact_native=serial(db.execute('select id,title,accession_number from artworks where current_institution_id=%s and accession_number=any(%s) order by id',(MID,['NG14','NG498'])).fetchall())
    if (E/'duplicate-venue-snapshot.json').exists():
        assert c.load(E/'duplicate-venue-snapshot.json')['matches']==matches
    else:
        save('duplicate-venue-snapshot.json',dict(at=c.now(),matches=matches))
    print('Duplicate matches',[(r['id'],r['title'],r['start_year'],r['end_year'])for r in matches],flush=True)
    assert not any(before.values())
    assert {r['id']for r in matches}=={'28d70349-fca4-5387-b037-8cc1a8d3a685','77d4d1de-f702-5127-94b8-8dac551a1c1b','dda9eac7-d406-54f2-a17e-aa516b816039','10f02f2b-e314-5e66-8eab-439344e833e4','8121a7e2-07ba-51cb-80ce-48f55c5ffa75'}
    assert {r['id']for r in exact_native}==set(WIDS)
    for wid,aid,inv,year,dim in zip(WIDS,AIDS,['NG14','NG498'],[1648,1815],['149.1 × 196.7 cm','155.5 × 230 cm']):
        w=next(x for x in old['artworks']if x['id']==wid)
        assert w['accession_number']==inv and w['current_institution_id']==MID and w['creation_year_start']==w['creation_year_end']==year and w['dimensions_text']==dim and w['work_type']=='painting'
        creators=[x for x in old['creators']if x['artwork_id']==wid];assert len(creators)==1 and creators[0]['artist_id']==aid and creators[0]['attribution_role']=='primary'
    assert {(x['display_name'],x['death_year'])for x in old['artists']}=={('Claude Lorrain',1682),('J. M. W. Turner',1851)}
    dr=dict(at=c.now(),reviewed_ids=[r['id']for r in matches],exact_native_matches=exact_native,decision='Broad title/alias/year/venue/native searches find five candidates. Turner1981 is the separate Athens retrospective, not London1980. Hommage a Claude Monet1980 is a different artist and Louvre venue. The remaining three are distinct Second sight events: Titian/Rembrandt1980, Rubens/Gainsborough1981 and Canaletto/Guardi1982. Different artists, dates and source identities. NG24/1980/10 is a compound archive file and explicitly distinguishes the Claude/Turner and Titian/Rembrandt events; the file is not itself an exhibition. Each selected accession has exactly one main record at the National Gallery. Different Dido subjects, works after Claude/Turner and Didot publisher-title false matches excluded.',passed=True)
    save('duplicate-venue-review.json',dr)
    sources=[dict(id=c.uid('national-gallery-london-archive/'+REF+'/source/'+native),native_id=native,**src[key])for native,key in [('NG32/127','NG32-127'),('NG24/1980/10','NG24-1980-10'),('NG60/48','NG60-48')]]
    sid=sources[1]['id'];oid=c.uid('national-gallery-london-archive/'+REF+'/venue')
    entries=[]
    for wid,aid,inv,title,creator,year,dim in zip(WIDS,AIDS,['NG14','NG498'],['The Embarkation of the Queen of Sheba','Dido building Carthage or the Rise of the Carthaginian Empire'],['Claude','Turner'],[1648,1815],['149.1 × 196.7 cm','155.5 × 230 cm']):
        entries.append(dict(id=c.uid('national-gallery-london-archive/'+REF+'/entry/'+inv),artwork_id=wid,source_id=sid,inventory=inv,title=title,creator=creator,object_source=src[inv],date_label=str(year),medium_label='Oil on canvas',dimensions_label=dim,artist_id=aid))
    participants=[dict(id=c.uid('national-gallery-london-archive/'+REF+'/artist/'+x['artist_id']),artist_id=x['artist_id'],name=x['creator'],source_id=sid,inventory=x['inventory'])for x in entries]
    basis='Official archive NG32/127 states the exhibition was held and records 119,044 visitors. NG24/1980/10 explicitly names both exhibited paintings, agreeing with the exhibition title on 14 February–13 April1980; poster archive NG60/48 and the catalogue citation in both object records corroborate the dates. Archive file creation dates16November1978–13February1980 are not exhibition dates.'
    ev=dict(id=EID,native_id=REF,title='Second sight: Claude/Turner',alternate_titles=['Second Sight 1: Claude and Turner','Claude: The Embarkation of the Queen of Sheba, Turner: Dido building Carthage'],year=1980,start='1980-02-14',end='1980-04-13',date_display='14 February – 13 April 1980',date_precision='day',date_qualified=False,room="northern extension's Special Exhibition Room",occurrence_id=oid,sources=sources,entries=entries,participants=participants,state_basis=basis)
    review=dict(at=c.now(),selected_distinct_exhibitions=1,exact_links=2,documentary_entries=0,distinct_existing_artworks=2,artist_links=2,duplicate_review=dr,
      object_identity='Exhibition-level NG24/1980/10 explicitly names both works. NG32/127 supplies native identities NG14 and NG498. Each existing main artwork matches the official museum accession, institution, direct creator, painting title, creation year, oil/canvas medium and precise dimensions. NG14 is the1648 original, not another Queen of Sheba or a reproduction; NG498 is the1815 Dido building Carthage, not Dido and Aeneas or the Decline painting. Both object pages cite the corresponding1980 exhibition catalogue. Main artwork facts and media are unchanged.',
      source_roles='Archive event and press-cuttings descriptions establish held event and named participation. Poster metadata corroborates dates but is not an artwork image. Object records independently establish exact identities and catalogue bibliography. No depicted-object claim from an unseen photograph or poster.',
      scope='1980 painting exhibition within1600–1989. Two reused main paintings1648/1815 are in scope. No sculpture/photography exhibition imported.',
      date_review='Event title, press-cuttings description, poster record and bibliographic citation agree. Archival file creation dates preserved separately, not substituted for opening/closing dates.',
      venue_review='Reuse National Gallery London institution; exact historical northern-extension Special Exhibition Room wording retained. No newly asserted ownership or current display.',
      creators='Existing Claude Lorrain and J.M.W.Turner are linked by their accessioned main works and matching museum creator labels. Claude birth1604/5? on the museum page differs from existing1600; source uncertainty retained without rewriting his biography. Turner1775–1851 matches. Both participations posthumous, not personal attendance. Same-surname artists excluded.',
      checklist_state='partial',checklist_basis='Two explicitly named paintings; original full catalogue contents not inspected. Selected documentation is not asserted complete.',
      unknowns=['Full original catalogue/checklist, catalogue numbers, organizers, sponsors and lender labels.'],
      image_policy='No new images selected, downloaded from museum or created. Existing catalogue images preserved; verification is technical/public delivery only, no new visual review claimed.',passed=True)
    p=dict(at=c.now(),operation=OP,target=t,event=ev,identity_sources=src,preserved_entities=old,duplicate_matches=matches,review=review)
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);save('plan.json',p);c.save(B/'plan.json',p);pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),receipts=[v['receipt']for v in src.values()],all_capture_checksums_and_extracted_text_verified=True,originals_outside_Documents=True,passed=True))
    print('Prepared 1 exhibition, 1 venue, 2 exact links, 2 participants; 9 insert rows.',flush=True)

def audit(db,table,ident,pin):
    row=serial(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
    db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)",(ACTOR,table,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))

def apply():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];e=p['event']
    assert p['operation']==OP and c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())==pin
    checked_sources()
    with c.connect(write=True)as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        before=snapshot(db)
        if before['exhibitions']:
            assert len(before['exhibitions'])==1 and before['exhibitions'][0]['import_batch']==OP
            assert (B/'transaction-preimage.json').exists() and all(x['interpretation']['plan_sha256']==pin for x in before['exhibition_source_records'])
            print('Own transaction exists; no replay. Independently verify.');return
        assert not any(before.values()) and preserved(db)==p['preserved_entities'] and collisions(db)==p['duplicate_matches']
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved_entities=p['preserved_entities'],locks=['artline-curated-ingestion',2026101201])
        save('transaction-preimage.json',pre);c.save(B/'transaction-preimage.json',pre);save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        base=dict(operation=OP,plan_sha256=pin,checked_at=p['at'],checklist_complete=False,no_current_display_claim=True,no_holding_claim=True,organizer_unknown=True,lenders_unknown=True,sponsors_unknown=True)
        inserted=[]
        db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
          values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)""",(EID,e['title'],c.norm(e['title']),Jsonb(e['alternate_titles']),e['start'],e['end'],1980,1980,e['date_display'],'day',e['state_basis']+' Assessed '+p['at']+'.',OP));inserted.append(('exhibitions',EID))
        for s in e['sources']:
            rc=s['receipt']
            db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
              values(%s,%s,'national-gallery-london-official-archive',%s,%s,%s,%s,%s,%s,%s)""",(s['id'],EID,s['native_id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(source_text=s['text'],receipt=rc,review=p['review'],object_identity_sources=[x['object_source']for x in e['entries']])),Jsonb(base|dict(original_native_id=s['native_id'],date_qualified=False))));inserted.append(('exhibition_source_records',s['id']))
        db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
          values(%s,%s,%s,%s,%s,'London','United Kingdom','GB',%s,%s,%s,%s)""",(e['occurrence_id'],EID,e['sources'][0]['id'],MID,'National Gallery — '+e['room'],e['start'],e['end'],e['date_display'],Jsonb(base|dict(room_source_wording=e['room'],venue_basis=p['review']['venue_review']))));inserted.append(('exhibition_occurrences',e['occurrence_id']))
        for x in e['entries']:
            db.execute("""insert into exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis)
              values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)""",(x['id'],EID,x['source_id'],e['occurrence_id'],x['artwork_id'],x['inventory'],x['title'],x['creator'],x['date_label'],x['medium_label'],x['dimensions_label'],Jsonb(base|dict(inventory=x['inventory'],object_identity_receipt=x['object_source']['receipt'],historical_title_preserved=True,object_fields_basis='Official accession-level collection record, corroborated against existing canonical object.',catalogue_number_unknown=True,participation_basis=e['state_basis'])),p['review']['object_identity']));inserted.append(('exhibition_entries',x['id']))
        for x in e['participants']:
            db.execute("""insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) values(%s,%s,%s,%s,%s,'artist',%s)""",(x['id'],EID,x['source_id'],x['artist_id'],x['name'],Jsonb(base|dict(posthumous=True,personal_attendance=False,documented_work=x['inventory'],identity_basis=p['review']['creators']))));inserted.append(('exhibition_participants',x['id']))
        for table,ident in inserted:audit(db,table,ident,pin)
        assert len(inserted)==9 and preserved(db)==p['preserved_entities']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independently verify.')

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in['prepare','apply'];globals()[sys.argv[1]]()
