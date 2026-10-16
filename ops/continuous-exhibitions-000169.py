"""One bounded historical archive delivery; existing supervisors are untouched."""
import gzip,json,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

E=c.ROOT/'docs/research/continuous-exhibitions-20261013/batches/000169'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000169'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000169'
OP='continuous-exhibitions-20261013-batch-000169'
INSTANCE='artline-508319:europe-west1:artline-postgres'
ACTOR='local-european-research'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
AIDS=['6f657ee8-b5b6-4802-ac4e-2a80ce1c27c3','0ab19151-3f5b-52a9-bd34-29642af9fba7']
MID='b8975392-9315-4803-b8c9-4139b5dddf03'
KEYS=['wilhelm-hack-museum/1981-01-31/carl-buchheister','kunsthaus-zurich/1981-01-29/verena-loewensberg']
EIDS=[c.uid(k)for k in KEYS]
TABLES=['exhibitions','exhibition_source_records','exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
save=lambda n,x:c.save(E/n,x)

def target(db):
    expected='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth '+INSTANCE
    assert expected in [x.strip()for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    r=db.execute('select current_database() database,current_user role').fetchone()
    assert r==dict(database='artline',role='artline_app')
    return dict(at=c.now(),instance=INSTANCE,host=db.info.host,port=db.info.port,**r)

def snapshot(db):
    out={}
    for table in TABLES:
        col='id'if table=='exhibitions'else'exhibition_id'
        out[table]=serial(db.execute('select * from '+table+' where '+col+'=any(%s::uuid[])order by id',(EIDS,)).fetchall())
    out['audits']=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    return out

def preserved(db):
    return serial(dict(artists=db.execute('select * from artists where id=any(%s::uuid[])order by id',(AIDS,)).fetchall(),
      aliases=db.execute('select * from artist_aliases where artist_id=any(%s::uuid[])order by id',(AIDS,)).fetchall(),
      authorities=db.execute('select * from external_identifiers where entity_id=any(%s::uuid[])order by id',(AIDS+[MID],)).fetchall(),
      institutions=db.execute('select * from institutions where id=%s',(MID,)).fetchall()))

def collisions(db):
    tokens=['%buchheister%','%loewensberg%','%löwensberg%','%loewenberg%','%буххайстер%','%лёвенсберг%','%левенсберг%']
    return serial(db.execute("""select e.*,
      (select jsonb_agg(to_jsonb(o)order by o.id)from exhibition_occurrences o where o.exhibition_id=e.id)venues,
      (select jsonb_agg(jsonb_build_object('native',s.source_record_id,'url',s.source_url)order by s.id)from exhibition_source_records s where s.exhibition_id=e.id)sources
      from exhibitions e where not(e.id=any(%s::uuid[]))and(
      e.title ilike any(%s)or e.alternate_titles::text ilike any(%s)
      or e.id in(select exhibition_id from exhibition_source_records where source_url like '%%RSN=48292%%')
      or((e.start_year is null or e.start_year<=1981)and(e.end_year is null or e.end_year>=1981)and e.id in(
      select exhibition_id from exhibition_occurrences where institution_id=%s or venue_label ilike '%%wilhelm%%hack%%'or city_label ilike '%%ludwigshafen%%')))
      order by e.id""",(EIDS,tokens,tokens,MID)).fetchall())

def checked_sources():
    archive=c.load(E/'wilhelm-hack-archive-receipt.json');cat=c.load(E/'kunsthaus48292.json')
    for rc in [archive,cat['receipt']]:
        raw=gzip.decompress(Path(rc['body_path']).read_bytes())
        assert rc['status']==200 and c.sha(raw)==rc['sha256']and len(raw)==rc['bytes']
    assert c.sha((R/'wilhelm-hack-exhibitions.pdf').read_bytes())==archive['sha256']
    txt=subprocess.check_output(['pdftotext','-layout',str(R/'wilhelm-hack-exhibitions.pdf'),'-'],text=True)
    assert txt==(R/'wilhelm-hack-exhibitions.txt').read_text()
    assert '31/01/81 - 22/02/81' in txt and 'Carl Buchheister. Gemälde'in txt
    assert '28/03/81 - 03/05/81'in txt and 'Verena Loewensberg. Gemälde 1935–1980'in txt
    raw=gzip.decompress(Path(cat['receipt']['body_path']).read_bytes())
    assert BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==cat['text']
    assert '1981.01.29 - 1981.03.22'in cat['text'] and '1981.03.28 - 1981.05.03'in cat['text']
    assert '(1912-1986)'in cat['text']and '(OCoLC)637080335'in cat['text']
    return archive,cat

def prepare():
    archive,cat=checked_sources()
    with c.connect()as db:
        t=target(db);before=snapshot(db);old=preserved(db);dupes=collisions(db)
        identities=serial(db.execute("""select * from artists where normalized_name=any(%s)or id in(
          select artist_id from artist_aliases where normalized_alias=any(%s))order by id""",
          (['carl buchheister','karl buchheister','verena loewensberg','verena lowensberg'],)*2).fetchall())
        venues=serial(db.execute("select * from institutions where name ilike any(%s)order by id",(['%wilhelm%hack%','%ludwigshafen%','%kunsthaus%z%rich%'],)).fetchall())
    save('final-duplicate-snapshot.json',dict(at=c.now(),matches=dupes,artist_candidates=identities,venue_candidates=venues))
    print('Duplicate candidates',[(x['id'],x['title'],x['start_year'],x['end_year'])for x in dupes],flush=True)
    assert not any(before.values())
    assert not dupes
    assert {x['id']for x in identities}==set(AIDS)
    assert {(x['display_name'],x['birth_year'],x['death_year'])for x in identities}=={('Carl Buchheister',1890,1964),('Verena Loewensberg',1912,1986)}
    assert len(venues)==1 and venues[0]['id']==MID and venues[0]['website_url']=='https://www.kunsthaus.ch/'
    events=[]
    for key,eid,aid,title,name,start,end in zip(KEYS,EIDS,AIDS,['Carl Buchheister. Gemälde','Verena Loewensberg'],['Carl Buchheister','Verena Loewensberg'],['1981-01-31','1981-01-29'],['1981-02-22','1981-05-03']):
        is_tour=name=='Verena Loewensberg'
        excerpt='28/03/81 – 03/05/81 Verena Loewensberg. Gemälde 1935–1980'if is_tour else'31/01/81 – 22/02/81 Carl Buchheister. Gemälde'
        sid=c.uid(key+'/source/whm-archive-page1')
        sources=[dict(id=sid,native='whm190903_Ausstellungen_einzeln_LR-1_final.pdf#page=1;'+('1981-03-28'if is_tour else'1981-01-31'),provider='wilhelm-hack-museum-official-exhibition-archive',receipt=archive,excerpt=excerpt,page=1)]
        if is_tour:
            csid=c.uid(key+'/source/kunsthaus-48292');sources.append(dict(id=csid,native='48292',provider='kunsthaus-zurich-official-library-catalogue',receipt=cat['receipt'],excerpt=cat['text'],page=None))
        occurrences=[dict(id=c.uid(key+'/venue/ludwigshafen'),source_id=sid,institution_id=None,venue='Wilhelm-Hack-Museum',city='Ludwigshafen am Rhein',country='Federal Republic of Germany',country_code='DE',start='1981-03-28'if is_tour else start,end=end)]
        if is_tour:occurrences.insert(0,dict(id=c.uid(key+'/venue/zurich'),source_id=csid,institution_id=MID,venue='Kunsthaus Zürich',city='Zürich',country='Switzerland',country_code='CH',start=start,end='1981-03-22'))
        events.append(dict(id=eid,key=key,title=title,alternate_titles=['Verena Loewensberg. Gemälde 1935–1980']if is_tour else[],artist_id=aid,name=name,participant_id=c.uid(key+'/artist/'+aid),participant_source=csid if is_tour else sid,posthumous=not is_tour,start=start,end=end,date_display=start+' – '+end,sources=sources,occurrences=occurrences,publication=dict(id=c.uid(key+'/publication/48292'),source_id=csid,title='Verena Loewensberg: Kunsthaus Zürich, 29. Januar–22. März 1981, Wilhelm-Hack-Museum, Ludwigshafen, 28. März–03. Mai 1981',author='Verena Loewensberg',year='[1981]',publisher='Kunsthaus Zürich',pages='46 unnumbered pages',identifier='OCLC 637080335; Kunsthaus Zürich RSN 48292',url=cat['receipt']['url'])if is_tour else None))
    review=dict(at=c.now(),selected_distinct_events=2,venue_stops=3,existing_canonical_creators=2,checklist_state='unknown',
      scope='Two1981 physical painting exhibitions. The1935–1980 wording describes the range of paintings in the Loewensberg show, not event dates. No main artworks selected; through1970 artwork cutoff unchanged.',
      held_basis='Official museum retrospective archive explicitly records both historical dated exhibitions. Kunsthaus museum library identifies the corresponding published1981 two-venue exhibition catalogue; its Ludwigshafen dates agree with the host archive.',
      tour_identity='One Loewensberg exhibition with two dated occurrences. The official catalogue title explicitly joins Kunsthaus Zürich and Wilhelm-Hack-Museum and their successive dates. Catalogue editions, title variants and venue stops are not separate exhibitions.',
      duplicates='Full title/alias variants, native catalogue ID, overlapping1981 events at either venue and creator aliases queried; no existing event candidates. Broad preliminary Dorazio/Bernhard results concern other artists or1965Cleveland, not these events.',
      creator_identity='One canonical record per exact full name/alias query. Verena1912–1986 also agrees with the host-library creator authority. Carl1890–1964 is the unique canonical CarlBuchheister; no same-name candidate. Single-artist painting titles explicitly establish creator participation. Carl posthumous; no personal-attendance assertion for either artist.',
      venues='Kunsthaus Zürich reuses its existing official-site institution. No matching Wilhelm-Hack institution exists in the inspected canonical-name/location query; preserve named venue with null institution_id instead of conflating HackneyMuseum or creating an unverified institution. German country label is historical contextual normalization, not quoted source wording.',
      roles='Hosts are documented. Catalogue publisher KunsthausZürich is a bibliographic role; no organizer, sponsor, lender or holding assertion inferred.',
      objects='Original checklists not acquired. No exhibited object is securely identified; no exact artwork links, documentary object entries or collection holdings inferred.',
      images='No images selected or published. One museum archive PDF page and an enlarged1981detail viewed for factual date/title alignment; no claim to view the other PDF pages or the unavailable NGS PDF.',
      unknowns=['Original full checklists and catalogue numbers','Organizers, sponsors and lenders','Canonical Wilhelm-Hack-Museum institution identity','Whether additional tour stops exist beyond the two documented Loewensberg stops'],passed=True)
    p=dict(at=c.now(),operation=OP,target=t,events=events,preserved=old,duplicate_matches=dupes,identity_matches=identities,venue_matches=venues,review=review)
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);save('plan.json',p);c.save(B/'plan.json',p)
    pin=c.sha((E/'plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin));save('candidate-review-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),receipts=[archive,cat['receipt']],originals_outside_Documents=True,sha256_and_extractions_checked=True,whole_publications_not_uploaded=True,passed=True))
    print('Prepared two exhibitions, three stops, two artist links, one catalogue reference.',flush=True)

def audit(db,table,ident,pin):
    row=serial(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
    db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)",(ACTOR,table,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))

def apply():
    p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert p['operation']==OP
    assert pin==c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes());checked_sources()
    with c.connect(write=True)as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        before=snapshot(db)
        if before['exhibitions']:
            assert len(before['exhibitions'])==2 and all(x['import_batch']==OP for x in before['exhibitions'])
            assert(B/'transaction-preimage.json').exists()and all(x['interpretation']['plan_sha256']==pin for x in before['exhibition_source_records'])
            print('Own prior commit present; no replay. Verify independently.');return
        assert not any(before.values())and preserved(db)==p['preserved']and collisions(db)==p['duplicate_matches']
        t=target(db);pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=before,preserved=p['preserved'],locks=['artline-curated-ingestion',2026101201])
        save('transaction-preimage.json',pre);c.save(B/'transaction-preimage.json',pre);save('production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        base=dict(operation=OP,plan_sha256=pin,assessed_at=p['at'],checklist_complete=False,no_holding_claim=True,no_current_display_claim=True,organizers_unknown=True,sponsors_unknown=True,lenders_unknown=True,exhibition_type='temporary single-artist painting exhibition')
        inserted=[]
        for e in p['events']:
            db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
              values(%s,%s,%s,%s,%s,%s,1981,1981,%s,'day','held',%s,'physical','unknown','review',%s)""",(e['id'],e['title'],c.norm(e['title']),Jsonb(e['alternate_titles']),e['start'],e['end'],e['date_display'],p['review']['held_basis']+' Assessed '+p['at']+'.',OP));inserted.append(('exhibitions',e['id']))
            for s in e['sources']:
                rc=s['receipt'];db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
                  values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(s['id'],e['id'],s['provider'],s['native'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(source_excerpt=s['excerpt'],source_page=s['page'],receipt=rc,review=p['review'])),Jsonb(base|dict(shared_tour=len(e['occurrences'])>1))));inserted.append(('exhibition_source_records',s['id']))
            for o in e['occurrences']:
                db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
                  values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(o['id'],e['id'],o['source_id'],o['institution_id'],o['venue'],o['city'],o['country'],o['country_code'],o['start'],o['end'],o['start']+' – '+o['end'],Jsonb(base|dict(venue_role='host',canonical_institution_unresolved=o['institution_id']is None,venue_basis=p['review']['venues']))));inserted.append(('exhibition_occurrences',o['id']))
            db.execute("""insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)values(%s,%s,%s,%s,%s,'artist',%s)""",(e['participant_id'],e['id'],e['participant_source'],e['artist_id'],e['name'],Jsonb(base|dict(posthumous=e['posthumous'],personal_attendance_claimed=False,identity_basis=p['review']['creator_identity']))));inserted.append(('exhibition_participants',e['participant_id']))
            b=e['publication']
            if b:
                db.execute("""insert into exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence)values(%s,%s,%s,'catalogue',%s,%s,%s,%s,%s,%s,%s)""",(b['id'],e['id'],b['source_id'],b['title'],b['author'],b['year'],b['url'],b['identifier'],b['pages'],Jsonb(base|dict(publisher=b['publisher'],bibliography_only=True,full_catalogue_inspected=False))));inserted.append(('exhibition_publications',b['id']))
        for table,ident in inserted:audit(db,table,ident,pin)
        assert len(inserted)==11 and preserved(db)==p['preserved']
        c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db)))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independent verification required.')

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in['prepare','apply'];globals()[sys.argv[1]]()
