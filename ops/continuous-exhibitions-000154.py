"""One bounded exact-object reconciliation; continuation belongs to external supervisor."""
import fcntl, gzip, json, os, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000154'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000154'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000154'
OP='continuous-exhibitions-20261013-batch-000154'
ACTOR='local-european-research'
EVENT='5c64ef50-18f0-5cf3-8a19-e86adf45c299'
ENTRY='fda2b161-6d43-5484-881f-03c217ae49fe'
ARTIST='de003eac-51c4-4057-bec5-4870d243b1b2'
INST='f94d0f6b-d6a7-5da2-afdf-e35a294b4e31'
SOURCE='193572a2-65c0-5ca7-8158-b4979bfdf648'
WORK=c.uid('harvard/artwork/298817')
ESOURCE=c.uid(OP+'/harvard/298817')
URL='https://harvardartmuseums.org/collections/object/298817'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
NEW_IDS={k:c.uid(OP+'/'+k) for k in ['identifier','citation','holding']}
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
def save(n,x):c.save(E/n,x)

def target(db):
    expected='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth artline-508319:europe-west1:artline-postgres'
    assert expected in [x.strip() for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    row=db.execute('select current_database() database,current_user role,pg_is_in_recovery() recovery').fetchone()
    assert row==dict(database='artline',role='artline_app',recovery=False)
    return dict(instance='artline-508319:europe-west1:artline-postgres',host=db.info.host,port=db.info.port,checked_at=c.now(),**row)

def receipt(rc):
    raw=Path(rc['body_path']).read_bytes()
    if str(rc['body_path']).endswith('.gz'):raw=gzip.decompress(raw)
    assert c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes'] and rc['status']==200
    return raw

def snapshot(db):
    out={}
    for t in ['exhibitions','exhibition_entries','exhibition_occurrences','exhibition_participants','exhibition_publications','exhibition_source_records']:
        col='id' if t=='exhibitions' else 'exhibition_id'
        out[t]=db.execute('select * from '+t+' where '+col+'=%s order by id',(EVENT,)).fetchall()
    for t,col in [('artworks','id'),('artwork_artists','artwork_id'),('artwork_location_assertions','artwork_id')]:
        order='artwork_id,artist_id' if t=='artwork_artists' else 'id'
        out[t]=db.execute('select * from '+t+' where '+col+'=%s order by '+order,(WORK,)).fetchall()
    for t in ['citations','external_identifiers']:
        out[t]=db.execute('select * from '+t+" where entity_type='artwork' and entity_id=%s order by id",(WORK,)).fetchall()
    out['artists']=db.execute('select * from artists where id=%s',(ARTIST,)).fetchall()
    out['institutions']=db.execute('select * from institutions where id=%s',(INST,)).fetchall()
    out['sources']=db.execute('select * from sources where id=%s',(SOURCE,)).fetchall()
    return serial(out)

def duplicate_query(db):
    exact=db.execute("select * from external_identifiers where entity_type='artwork' and (external_id in ('298817','1915.8') or canonical_url like '%%/298817%%') order by id").fetchall()
    works=db.execute("select * from artworks where accession_number='1915.8' or normalized_title like '%binding%satan%' or normalized_title like '%michael%satan%' or normalized_title like '%satan%bound%' or normalized_title like '%bottomless%' order by id").fetchall()
    ids=[str(x['id']) for x in works]
    creators=db.execute('select aa.artwork_id,aa.artist_id,aa.attribution_role,a.display_name from artwork_artists aa join artists a on a.id=aa.artist_id where aa.artwork_id=any(%s::uuid[]) order by aa.artwork_id,aa.artist_id',(ids,)).fetchall()
    assert not exact and WORK not in ids
    assert not any(str(x['artist_id'])==ARTIST for x in creators)
    assert all(x['accession_number']!='1915.8' for x in works)
    return serial(dict(exact_identifiers=exact,other_title_candidates=works,candidate_creators=creators))

def prepare():
    E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    src=c.load(E.parent/'000062/harvard-research-capture.json');rc=src['receipt']
    text=BeautifulSoup(receipt(rc),'html.parser').get_text(' ',strip=True)
    for s in ['1915.8','c. 1805','35.9 x 32.5 cm','to Fogg Art Museum, 1915','Watercolor, black ink, and graphite on off-white wove paper']:assert s in text
    pdf=c.load(E.parent/'000070/plan.json')['pdf_receipt'];receipt(pdf)
    assert c.sha((R/'blake1939.pdf').read_bytes())==pdf['sha256']
    with c.connect() as db:
        t=target(db);pre=snapshot(db);dup=duplicate_query(db)
        entry=next(x for x in pre['exhibition_entries'] if x['id']==ENTRY)
        assert entry['artwork_id'] is None and entry['catalogue_number']=='171' and entry['lender_label']=='The Fogg Art Museum, Harvard University'
        assert entry['title_label']=='Michael Binding Satan' and entry['participation']=='catalogued'
        original=next(x for x in pre['exhibition_source_records'] if x['id']==entry['source_record_id'])
        _,original_receipt=c.capture(original['source_url']);receipt(original_receipt);assert original_receipt['sha256']==original['capture_sha256']
        assert pre['exhibitions'][0]['start_year']==1939 and pre['exhibitions'][0]['checklist_state']=='partial'
        assert pre['artists'][0]['display_name']=='William Blake' and pre['institutions'][0]['name']=='Harvard Art Museums'
        assert any(x['artist_id']==ARTIST for x in pre['exhibition_participants'])
        assert not pre['artworks'] and not pre['citations'] and not pre['external_identifiers']
    basis='Original Philadelphia 1939 catalogue no. 171, printed page 119 (PDF page 145), explicitly identifies Michael Binding Satan, a watercolor lent by the Fogg Art Museum, Harvard University. Official Harvard object 298817/accession 1915.8 identifies the same William Blake watercolor, c. 1805, 35.9 x 32.5 cm, and documents W. A. White acquisition in 1908 and gift to Fogg in 1915. Historical title, artist, medium, unique institutional object identity and pre-exhibition lender continuity agree. Catalogue participation remains catalogued, not promoted to a stronger assertion; no current display inferred.'
    visual=dict(at=c.now(),actual_viewed_pdf_pages=[145],printed_pages=[119],page_path=str(R/'catalogue-page145.png'),page_sha256=c.sha((R/'catalogue-page145.png').read_bytes()),pdf_sha256=pdf['sha256'],observation='Visually read entry171 and its explicit Fogg Art Museum, Harvard University lender credit. Page also distinguishes Met entry168 from Philip Hofer entry169; these were not relinked. No artwork reproductions or unsampled pages claimed as viewed.',new_images_prepared=0)
    obj=dict(native_id='298817',accession='1915.8',title='The Angel Michael Binding Satan ("He Cast him into the Bottomless Pit, and Shut him up")',date_display='c. 1805',creation_year=1805,medium='Watercolor, black ink, and graphite on off-white wove paper',dimensions='35.9 x 32.5 cm (14 1/8 x 12 13/16 in.)',credit_line='Harvard Art Museums/Fogg Museum, Gift of W. A. White',creator='William Blake',work_type='drawing')
    plan=dict(at=c.now(),operation=OP,target=t,work_id=WORK,entry_id=ENTRY,event_id=EVENT,source=rc,source_text=text,object=obj,original_catalogue_record=original,original_catalogue_receipt=original_receipt,pdf_receipt=pdf,basis=basis,visual=visual,preimage=pre,duplicate_review=dup,
        scope=dict(exhibition_years=[1600,1989],main_work_cutoff=1970),image_rights=dict(source_label='personal, noncommercial use including educational and scholarly purposes; higher resolution by request',images_selected=0,production_rights_not_inferred=True))
    c.save(E/'immutable-plan.json',plan);c.save(B/'immutable-plan.json',plan)
    pin=c.sha((E/'immutable-plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin))
    save('visual-review-verification.json',visual|dict(passed=True))
    save('source-capture-verification.json',dict(at=c.now(),museum_receipt=rc,original_catalogue_receipt=original_receipt,original_pdf_receipt=pdf,all_checksums_verified=True,source_bodies_outside_Documents=True,prior_capture_reused=True,passed=True))
    save('candidate-reconciliation-verification.json',dict(at=c.now(),selected_existing_entries=1,new_main_artworks_prepared=1,exact_links_prepared=1,creator_catalogue_rows_reviewed=len(c.load(E/'blake-full-creator-catalogue.json')),additional_title_candidates=len(dup['other_title_candidates']),duplicate_review=dup,basis=basis,checklist_complete=False,image_rights_held=True,passed=True))
    print('Prepared one new review drawing and one existing-entry exact link.',flush=True)

def audit(db,typ,ident,before,record,pin):
    db.execute('insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,%s,%s,%s,%s,%s,%s)',(ACTOR,'continuous_exhibition_exact_object_reconciliation',typ,ident,OP,Jsonb(before),Jsonb(dict(record=record,plan_sha256=pin))))

def apply():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert c.sha((E/'immutable-plan.json').read_bytes())==c.sha((B/'immutable-plan.json').read_bytes())==pin
    receipt(p['source']);receipt(p['pdf_receipt']);receipt(p['original_catalogue_receipt'])
    with c.connect(write=True) as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        db.execute('select id from exhibition_entries where id=%s for update',(ENTRY,));cur=snapshot(db)
        if cur['artworks']:
            assert (B/'transaction-preimage.json').exists()
            assert any(x['interpretation'].get('plan_sha256')==pin and x['id']==ESOURCE for x in cur['exhibition_source_records'])
            assert next(x for x in cur['exhibition_entries'] if x['id']==ENTRY)['artwork_id']==WORK
            print('Own pinned transaction already present; verify without replay.');return
        assert cur==p['preimage']
        dup=duplicate_query(db);assert dup==p['duplicate_review']
        pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=target(db),rows=cur,locks=['artline-curated-ingestion',2026101201])
        c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre);save('production-target-before-write.json',pre['target']|dict(plan_sha256=pin,passed=True))
        rc=p['source'];o=p['object'];ev=dict(operation=OP,plan_sha256=pin,source_sha256=rc['sha256'],source_capture=rc['body_path'],original_catalogue_sha256=p['original_catalogue_record']['capture_sha256'],original_pdf_sha256=p['pdf_receipt']['sha256'],native_id='298817',accession='1915.8',catalogue_number='171',printed_page=119,pdf_page=145,basis=p['basis'],checklist_complete=False,current_display_claim=False,holding_basis='Explicit official Harvard/Fogg credit and acquisition record; not inferred from historical exhibition loan.',image_rights=p['image_rights'])
        db.execute("insert into artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by)values(%s,%s,%s,%s,%s,1805,1805,'circa','drawing',%s,%s,'1915.8','review',true,%s,%s)",(WORK,'harvard-object-298817',o['title'],c.norm(o['title']),o['date_display'],o['medium'],o['dimensions'],ACTOR,ACTOR))
        db.execute("insert into artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)values(%s,%s,'primary',%s)",(WORK,ARTIST,'Unqualified official Harvard creator attribution; exact object298817, accession1915.8.'))
        db.execute("insert into external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)values(%s,'artwork',%s,'harvard-art-museums-object','298817',%s,%s,%s)",(NEW_IDS['identifier'],WORK,URL,SOURCE,rc['retrieved_at']))
        db.execute("insert into citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by)values(%s,'artwork',%s,'native_object_metadata_and_historical_exhibition_match',%s,'298817',%s,%s,%s,%s,%s)",(NEW_IDS['citation'],WORK,SOURCE,URL,'Official object298817/accession1915.8; Philadelphia1939 no.171, p.119',json.dumps(ev,ensure_ascii=False),rc['retrieved_at'],ACTOR))
        db.execute("insert into artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)values(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(NEW_IDS['holding'],WORK,INST,SOURCE,URL,json.dumps(ev,ensure_ascii=False),rc['retrieved_at']))
        db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(ESOURCE,EVENT,OP,'harvard/298817',URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(object=o,source_text=p['source_text'],receipt=rc)),Jsonb(ev)))
        old=next(x for x in cur['exhibition_entries'] if x['id']==ENTRY)
        evidence=old['evidence']|dict(canonicalObjectMatchPending=False,canonicalObjectMatch=ev,canonicalMatchSourceRecordID=ESOURCE)
        result=db.execute('update exhibition_entries set artwork_id=%s,match_basis=%s,evidence=%s where id=%s and artwork_id is null',(WORK,p['basis'],Jsonb(evidence),ENTRY));assert result.rowcount==1
        after=snapshot(db)
        audit(db,'artwork',WORK,None,after['artworks'][0],pin)
        audit(db,'exhibition_entry',ENTRY,old,next(x for x in after['exhibition_entries'] if x['id']==ENTRY),pin)
        audit(db,'exhibition_source_record',ESOURCE,None,next(x for x in after['exhibition_source_records'] if x['id']==ESOURCE),pin)
        c.save(B/'transaction-postimage.json',dict(at=c.now(),operation=OP,plan_sha256=pin,rows=after))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Transaction committed; verification pending.',flush=True)

def verify():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
    assert c.sha((E/'immutable-plan.json').read_bytes())==pin==pre['plan_sha256']==post['plan_sha256'] and pre['rows']==p['preimage']
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        assert rows==post['rows']
        au=serial(db.execute('select * from audit_log where entity_id=any(%s::uuid[]) and request_id=%s order by entity_id',([WORK,ENTRY,ESOURCE],OP)).fetchall())
        assert len(au)==3 and all(a['after_json']['plan_sha256']==pin for a in au)
    old=pre['rows'];entry=next(x for x in rows['exhibition_entries'] if x['id']==ENTRY);before=next(x for x in old['exhibition_entries'] if x['id']==ENTRY)
    assert before['artwork_id'] is None and entry['artwork_id']==WORK
    for key in before:
        if key not in ['artwork_id','evidence','match_basis']:assert before[key]==entry[key],key
    for key in ['exhibitions','exhibition_occurrences','exhibition_participants','exhibition_publications','artists','institutions','sources']:assert old[key]==rows[key],key
    assert [x for x in rows['exhibition_entries'] if x['id']!=ENTRY]==[x for x in old['exhibition_entries'] if x['id']!=ENTRY]
    assert [x for x in rows['exhibition_source_records'] if x['id']!=ESOURCE]==old['exhibition_source_records']
    work=rows['artworks'][0];o=p['object'];assert work['id']==WORK and work['title']==o['title'] and work['status']=='review' and work['date_precision']=='circa' and work['creation_year_start']==work['creation_year_end']==1805 and work['primary_media_id'] is None and work['current_institution_id']==INST and work['accession_number']=='1915.8'
    assert len(rows['artwork_artists'])==len(rows['external_identifiers'])==len(rows['citations'])==len(rows['artwork_location_assertions'])==1
    assert rows['artwork_artists'][0]['artist_id']==ARTIST
    assert json.loads(rows['citations'][0]['evidence_note'])['plan_sha256']==pin
    assert json.loads(rows['artwork_location_assertions'][0]['evidence_note'])['plan_sha256']==pin
    sr=next(x for x in rows['exhibition_source_records'] if x['id']==ESOURCE);assert sr['capture_sha256']==p['source']['sha256'] and sr['interpretation']['plan_sha256']==pin
    for a in au:
        assert a['before_json']==(before if a['entity_id']==ENTRY else None)
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=1,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=1,new_images=0,existing_records_enriched=1)
    if not (E/'independent-database-verification.json').exists():save('independent-database-verification.json',dict(at=c.now(),target=t,operation=OP,plan_sha256=pin,rows=rows,audits=au,verified_counts=counts,attribution='Work absent and existing entry artwork_id null in locked preimage; source, citation, holding evidence and audits carry this plan checksum. No concurrent/previous programme changes counted.',passed=True))
    receipts=[]
    for key,url in [('entries',API+'exhibitions/'+EVENT+'/entries?limit=100'),('work',API+'artists/'+p['preimage']['artists'][0]['slug']+'/works/'+WORK)]:
        res=requests.get(url,timeout=(15,45));res.raise_for_status();data=res.json();c.save(R/('public-'+key+'.json'),data)
        if key=='entries':
            assert len(data['items'])==28 and not data.get('nextCursor');x=next(x for x in data['items'] if x['id']==ENTRY);assert x['artworkId']==WORK and not x.get('image')
        else:
            assert data.get('id')==WORK and data.get('title')==o['title'],data
            assert data['status']=='review' and data['accession_number']=='1915.8' and data['date_precision']=='circa' and data['creation_year_start']==1805
            assert data['holding']['id']==INST and data['display'] is None and data['medium_text']==o['medium'] and data['dimensions_text']==o['dimensions']
            assert any(x['source_url']==URL for x in data['citations'])
        receipts.append(dict(url=res.url,status=res.status_code,sha256=c.sha(res.content),path=str(R/('public-'+key+'.json'))))
    save('independent-public-verification.json',dict(at=c.now(),receipts=receipts,entry_id=ENTRY,artwork_id=WORK,new_exact_links=1,new_review_artworks=1,checklist_entry_count=28,checklist_still_partial=True,no_image_selected=True,passed=True))
    save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['immutable-plan.json','transaction-preimage.json','transaction-postimage.json']],postimage_matches_independent_read=True,passed=True))
    print(json.dumps(counts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
