#!/usr/bin/env python3
"""One bounded National Gallery archive batch; external supervisor owns continuation."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000165'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000165'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000165'
OP='continuous-exhibitions-20261013-batch-000165'
INSTANCE='artline-508319:europe-west1:artline-postgres'
MID='2c909ffb-2614-4273-b76b-a0daa2a74833'
ACTOR='local-european-research'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']
EIDS=[c.uid('national-gallery-london-archive/'+x) for x in ['NG32/138']]
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

WID='6379204e-82b6-5bfe-ba21-4c4baa4ecbef'
AIDS=['4dd196e1-44f5-4ee5-9260-c57616d9c7b3','456383a0-b41a-4123-8ce0-07d61de5ddac']
KEYS=['NG32-138','NG24-1982-17','NG127','wikiart-NG127','Guardi-artist','Guardi-piazza','Guardi-piazza-1']

def preserved(db):
    return serial(dict(artworks=db.execute('select * from artworks where id=%s',(WID,)).fetchall(),
      creators=db.execute('select * from artwork_artists where artwork_id=%s order by artist_id',(WID,)).fetchall(),
      artists=db.execute('select * from artists where id=any(%s::uuid[]) order by id',(AIDS,)).fetchall(),
      aliases=db.execute('select * from artist_aliases where artist_id=any(%s::uuid[]) order by id',(AIDS,)).fetchall(),
      authorities=db.execute('select * from external_identifiers where entity_id=any(%s::uuid[]) order by id',([WID]+AIDS,)).fetchall(),
      institution=db.execute('select * from institutions where id=%s',(MID,)).fetchone()))

def collisions(db):
    return serial(db.execute("""select e.id,e.title,e.start_year,e.end_year,e.date_display,e.import_batch,
      (select jsonb_agg(to_jsonb(o) order by o.id) from exhibition_occurrences o where o.exhibition_id=e.id) venues,
      (select jsonb_agg(jsonb_build_object('native',s.source_record_id,'url',s.source_url) order by s.id) from exhibition_source_records s where s.exhibition_id=e.id) sources
      from exhibitions e where e.id<>all(%s::uuid[]) and (
      e.title ilike any(%s) or e.alternate_titles::text ilike any(%s)
      or e.id in(select exhibition_id from exhibition_source_records where source_record_id in('NG32/138','NG24/1982/17') or source_url like '%%/NG32/138' or source_url like '%%/NG24/1982/17')
      or ((e.start_year between 1980 and 1983 or e.end_year between 1980 and 1983) and e.title ilike any(%s))
      or ((e.start_year is null or e.start_year<=1982) and (e.end_year is null or e.end_year>=1982) and e.id in(select exhibition_id from exhibition_occurrences where institution_id=%s or (venue_label ilike '%%national gallery%%' and city_label ilike '%%london%%')))) order by e.id""",
      (EIDS,['%second%sight%','%canaletto%guardi%','%каналетто%гварди%'],['%second%sight%','%canaletto%guardi%'],['%canaletto%','%guardi%','%каналетто%','%гварди%'],MID)).fetchall())

def checked_sources():
    out={}
    for key in KEYS:
        v=c.load(E/(key+'.json'));rc=v['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes())
        assert rc['status']==200 and c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes']
        assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==v['text'];out[key]=v
    assert '[18 Feb-18 Apr 1982]' in out['NG32-138']['text'] and '72,375 visitors' in out['NG32-138']['text']
    assert "northern extension's Special Exhibition Room" in out['NG32-138']['text']
    assert "18 February 1982-18 April 1982" in out['NG24-1982-17']['text']
    assert "Canaletto 'The Stonemason's Yard' and Guardi 'Piazza San Marco'" in out['NG24-1982-17']['text']
    assert 'Paintings referenced in this record NG127' in out['NG24-1982-17']['text']
    assert 'Inventory number NG127' in out['NG127']['text'] and '123.8 × 162.9 cm' in out['NG127']['text']
    assert 'Location: National Gallery, London, UK' in out['wikiart-NG127']['text'] and 'Dimensions: 163 x 124 cm' in out['wikiart-NG127']['text']
    assert 'Inventory number NG210' in out['Guardi-piazza']['text'] and 'Inventory number NG2525' in out['Guardi-piazza-1']['text']
    assert all('Artist Francesco Guardi Artist dates 1712 - 1793' in out[k]['text'] for k in ['Guardi-piazza','Guardi-piazza-1'])
    return out

def prepare():
    src=checked_sources();live=c.load(E/'live-reconciliation.json');w=next(x for x in live['artworks']if x['id']==WID)
    with c.connect()as db:
        t=target(db);before=snapshot(db);old=preserved(db);matches=collisions(db)
        assert not any(before.values())
    save('duplicate-venue-snapshot.json',dict(at=c.now(),matches=matches))
    print('Duplicate matches',[(r['id'],r['title'],r['start_year'],r['end_year']) for r in matches],flush=True)
    assert {r['id']for r in matches}=={'28d70349-fca4-5387-b037-8cc1a8d3a685','77d4d1de-f702-5127-94b8-8dac551a1c1b'}
    assert old['artworks'][0]=={k:v for k,v in w.items()if k not in ['creators','identifiers']}
    assert old['institution']['id']==MID and w['creation_year_end']==1727 and w['work_type']=='painting'
    assert len(w['creators'])==1 and w['creators'][0]['artist_id']==AIDS[0] and w['creators'][0]['attribution_role']=='primary'
    dr=dict(at=c.now(),reviewed_ids=[r['id']for r in matches],decision='Only distinct Second sight events in 1980 (Titian/Rembrandt) and 1981 (Rubens/Gainsborough) match broad title, date, source and venue search. Different artists, dates and archive identities; no duplicate of NG32/138. Main artwork query returns one Canaletto Stonemason work; unrelated prints, portraits and labour scenes excluded.',passed=True)
    save('duplicate-venue-review.json',dr)
    ref='NG32/138';eid=EIDS[0];oid=c.uid('national-gallery-london-archive/'+ref+'/venue')
    sources=[dict(id=c.uid('national-gallery-london-archive/'+ref+'/source/'+native),native_id=native,key=key,**src[key])for native,key in [('NG32/138','NG32-138'),('NG24/1982/17','NG24-1982-17')]]
    sid=sources[1]['id']
    entries=[dict(id=c.uid('national-gallery-london-archive/'+ref+'/entry/NG127'),artwork_id=WID,source_id=sid,inventory='NG127',title="The Stonemason's Yard",creator='Canaletto',object_source=src['NG127'],date_label='About 1725',medium_label='Oil on canvas',dimensions_label='123.8 × 162.9 cm',artist_id=AIDS[0]),
      dict(id=c.uid('national-gallery-london-archive/'+ref+'/entry/Guardi-Piazza-documentary'),artwork_id=None,source_id=sid,inventory=None,title='Piazza San Marco',creator='Guardi',object_source=src['NG24-1982-17'],date_label=None,medium_label=None,dimensions_label=None,artist_id=AIDS[1])]
    participants=[dict(id=c.uid('national-gallery-london-archive/'+ref+'/artist/'+aid),artist_id=aid,name=name,source_id=sid,inventory=inv)for aid,name,inv in [(AIDS[0],'Canaletto','NG127'),(AIDS[1],'Guardi',None)]]
    basis='Official archive NG32/138 documents the held painting exhibition and 72,375 visitors. Independent archive NG24/1982/17 explicitly identifies the two exhibited paintings and agrees on 18 February–18 April 1982. Archive file date 25 November 1981 is not the exhibition opening.'
    ev=dict(id=eid,native_id=ref,title='Second sight: Canaletto/Guardi',alternate_titles=['Second Sight No 5: Canaletto and Guardi',"Canaletto: The Stonemason's Yard and Guardi: The Piazza San Marco"],year=1982,start='1982-02-18',end='1982-04-18',date_display='18 February – 18 April 1982',date_precision='day',date_qualified=False,room="northern extension's Special Exhibition Room",occurrence_id=oid,sources=sources,entries=entries,participants=participants,state_basis=basis)
    review=dict(at=c.now(),selected_distinct_exhibitions=1,exact_links=1,documentary_entries=1,distinct_existing_artworks=1,artist_links=2,duplicate_review=dr,
      object_identity='Canaletto: archive NG24/1982/17 references NG127 explicitly. Existing WikiArt native 57727911edc2cb3880d9f8b6 names this work, Canaletto, National Gallery London, oil/canvas and rounded 163 x 124 cm, matching official NG127 123.8 x 162.9 cm with reversed dimension order. Official About 1725 and existing 1727 are preserved as separate date assertions; no main metadata rewrite. Guardi: exhibition explicitly names Piazza San Marco, but NG210 and NG2525 are different same-title paintings with different dimensions and dates. No accession or version is inferred; documentary entry has null artwork_id, source_artwork_id, date, medium and dimensions.',
      source_roles='The event archive and exhibition press-cuttings description prove occurrence and participation. Museum and WikiArt object pages supply object/creator identity only. No installation-view visual interpretation.',
      scope='Painting exhibition 1982 falls within 1600–1989. Reuses one eighteenth-century catalogue painting; creates no main artwork.',
      date_review='Two official archive records agree on event dates. The separate Mantegna/Degas candidate NG32/137 versus NG30/1981/79 has conflicting 25 November1981–24January1982 and 7October–6December1981 ranges; held without import. Canaletto creation-year difference preserved.',
      venue_review='Reuse existing National Gallery London institution. Historical northern-extension Special Exhibition Room retained as subvenue. No new holding or present-display claims.',
      creators='Canaletto 1697–1768 matches existing artist and official object source. Guardi is resolved to existing Francesco Guardi 1712–1793 using official museum artist and both same-title museum painting records; object-version ambiguity does not change their shared creator. Gian Antonio/Antonio and Giacomo Guardi are distinct and excluded. Both artists posthumous; no personal attendance.',
      checklist_state='partial',checklist_basis='Two explicitly named paintings; full original exhibition catalogue/checklist not inspected.',unknowns=['Full original checklist, catalogue numbers, lenders, organizers and sponsors.','Exact Guardi object version/accession; no canonical work link.'],image_policy='No new images downloaded or prepared. Reuse existing Canaletto primary image unchanged. No visual-review claim.',passed=True)
    p=dict(at=c.now(),operation=OP,target=t,events=[ev],identity_sources=src,preserved_entities=old,duplicate_matches=matches,review=review)
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);save('plan.json',p);c.save(B/'plan.json',p);pin=c.sha((E/'plan.json').read_bytes())
    save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),receipts=[v['receipt']for v in src.values()],all_capture_checksums_and_extracted_text_verified=True,originals_outside_Documents=True,passed=True))
    print('Prepared 1 exhibition, 1 venue, 1 exact link, 1 documentary entry and 2 participants.',flush=True)

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
                  values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)""",(x['id'],e['id'],x['source_id'],e['occurrence_id'],x['artwork_id'],x['inventory'],x['title'],x['creator'],x['date_label'],x['medium_label'],x['dimensions_label'],Jsonb(base|dict(inventory=x['inventory'],object_identity_receipt=x['object_source']['receipt'],historical_title_preserved=True,object_fields_basis='Museum object identity fields for NG127; Guardi preserves exhibition wording with version-specific fields unknown.',catalogue_number_unknown=True,participation_basis=e['state_basis'])),p['review']['object_identity']))
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
