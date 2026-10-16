"""One bounded RISD/Philadelphia 1939 exact-object batch; no supervisor changes."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000158'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000158'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000158'
OP='continuous-exhibitions-20261013-batch-000158'
ACTOR='local-european-research'
EVENT='5c64ef50-18f0-5cf3-8a19-e86adf45c299'
ARTIST='de003eac-51c4-4057-bec5-4870d243b1b2'
INST='12d29a09-486c-5a1a-abe3-9bcf009174f2'
SOURCE=c.uid('risd-museum-official-collection')
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
OBJECTS=[
 dict(key='baptism',entry='2cc2d6a4-a00c-5c80-af8c-344b7d8c0b56',number='154',accession='32.219',title='Baptism of Christ',year=1799,date='ca. 1799',precision='circa',work_type='painting',medium='Tempera over pen and ink on canvas',dimensions='32.4 x 49.2 cm (12 3/4 x 19 3/8 inches)',credit='Museum Appropriation Fund',pdf_page=132,printed_page=106,
      basis='Original Philadelphia 1939 catalogue no.154, printed p.106, explicitly identifies The Baptism of Christ, tempera on canvas, painted for Thomas Butts and lent by The Rhode Island School of Design. Official RISD accession32.219 identifies the same William Blake tempera, ca.1799, and documents Thomas Butts provenance and purchase from Gordon Kennedy in1932. Title, creator, specific medium, provenance and historical institutional lender agree. Current RISD holding follows the official object record, not an inference from the exhibition loan.',
      qualifications=['RISD medium says canvas while its Supports fields say paper, mounted on canvas; retain both assertions in source evidence without silently resolving support construction.']),
 dict(key='paul',entry='e4f16c55-c0ba-581e-8d94-95dfa341af2b',number='176',accession='31.280',title='St. Paul Preaching at Athens',year=1803,date='1803',precision='exact',work_type='drawing',medium='Pen and ink, watercolor, black chalk with wet brush, and scraping on wove paper',dimensions='45.7 x 31.1 cm (18 x 12 1/4 inches)',credit='Gift of the Estate of Mrs. Gustav Radeke',pdf_page=153,printed_page=127,
      basis='Original Philadelphia 1939 catalogue no.176, printed p.127, identifies St. Paul Preaching at Athens, watercolor, signed1803, formerly Thomas Butts and lent by The Rhode Island School of Design. Official RISD accession31.280 identifies the same William Blake watercolor, dates it1803, records an1803 inscription and the Butts commission. Exact title, author, medium, date and institutional lender agree. It is distinct from Raphael-derived prints with similar titles. Current holding follows the museum object record, not the loan alone.',
      qualifications=['1939 catalogue transcribes the signature as W B inv1803; current RISD text transcribes Wm. B.1803. Preserve both transcriptions; no signature correction or invented acquisition date.'])]
for o in OBJECTS:
    o['id']=c.uid('risd/artwork/'+o['accession'])
    o['source_record']=c.uid(OP+'/source/'+o['accession'])
    o['ids']={k:c.uid(OP+'/'+o['accession']+'/'+k) for k in ['identifier','citation','holding']}
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
save=lambda n,x:c.save(E/n,x)

def target(db):
    expected='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth artline-508319:europe-west1:artline-postgres'
    assert expected in [x.strip() for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    row=db.execute('select current_database() database,current_user role,pg_is_in_recovery() recovery').fetchone()
    assert row==dict(database='artline',role='artline_app',recovery=False)
    return dict(instance='artline-508319:europe-west1:artline-postgres',host=db.info.host,port=db.info.port,checked_at=c.now(),**row)

def body(rc):
    raw=Path(rc['body_path']).read_bytes()
    if rc['body_path'].endswith('.gz'):raw=gzip.decompress(raw)
    assert c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes']
    return raw

def snapshot(db):
    out={}
    for t in ['exhibitions','exhibition_entries','exhibition_occurrences','exhibition_participants','exhibition_publications','exhibition_source_records']:
        col='id' if t=='exhibitions' else 'exhibition_id'
        out[t]=db.execute('select * from '+t+' where '+col+'=%s order by id',(EVENT,)).fetchall()
    ids=[o['id']for o in OBJECTS]
    for t,col in [('artworks','id'),('artwork_artists','artwork_id'),('artwork_location_assertions','artwork_id')]:
        order='artwork_id,artist_id' if t=='artwork_artists' else 'id'
        out[t]=db.execute('select * from '+t+' where '+col+'=any(%s::uuid[]) order by '+order,(ids,)).fetchall()
    for t in ['citations','external_identifiers']:
        out[t]=db.execute('select * from '+t+" where entity_type='artwork' and entity_id=any(%s::uuid[]) order by id",(ids,)).fetchall()
    out['artists']=db.execute('select * from artists where id=%s',(ARTIST,)).fetchall()
    out['institutions']=db.execute('select * from institutions where id=%s',(INST,)).fetchall()
    out['sources']=db.execute('select * from sources where id=%s',(SOURCE,)).fetchall()
    return serial(out)

def duplicate_query(db):
    # Native accession checks are provider-scoped: other museums reuse digit strings.
    exact=db.execute("select * from external_identifiers where entity_type='artwork' and (external_id in ('31.280','32.219','31280','32219') or canonical_url like '%%risdmuseum%%') order by id").fetchall()
    works=db.execute("select * from artworks where accession_number in ('31.280','32.219') or normalized_title like '%%paul%%preach%%athens%%' or normalized_title like '%%baptism%%christ%%' order by id").fetchall()
    ids=[str(w['id'])for w in works]
    creators=db.execute('select aa.*,a.display_name from artwork_artists aa join artists a on a.id=aa.artist_id where artwork_id=any(%s::uuid[]) order by artwork_id,artist_id',(ids,)).fetchall()
    sources=db.execute("select * from sources where base_url ilike '%%risd%%'").fetchall()
    assert not any('risdmuseum' in (x['canonical_url'] or '') or x['external_id'] in ['31.280','32.219'] for x in exact)
    assert not any(w['accession_number'] in ['31.280','32.219'] or 'blake' in (w['unlinked_creator_label'] or '').lower() for w in works)
    assert not any(str(a['artist_id'])==ARTIST for a in creators)
    assert not sources
    return serial(dict(identifiers=exact,artworks=works,creators=creators,sources=sources))

def prepare():
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    prior=c.load(E.parent/'000154/immutable-plan.json');pdf=prior['pdf_receipt'];body(pdf)
    assert c.sha((R/'blake1939.pdf').read_bytes())==pdf['sha256']
    sources={o['key']:c.load(E/('risd-'+o['key']+'-web-extract.json'))for o in OBJECTS}
    for o in OBJECTS:
        rc=sources[o['key']];txt=body(rc).decode();assert txt==rc['source_text']
        assert all(x in txt for x in [o['accession'],o['title'],o['date'],o['dimensions'],'William Blake','CC0 1.0'])
    assert '1932, Purchased from Gordon Kennedy by RISD Museum' in sources['baptism']['source_text']
    assert 'Commissioned by Thomas Butts in 1803' in sources['paul']['source_text']
    with c.connect() as db:
        t=target(db);pre=snapshot(db);dup=duplicate_query(db)
        assert not pre['artworks'] and not pre['sources']
        assert pre['exhibitions'][0]['start_year']==1939 and pre['exhibitions'][0]['checklist_state']=='partial'
        assert pre['artists'][0]['display_name']=='William Blake' and pre['institutions'][0]['name']=='Rhode Island School of Design Museum'
        assert any(p['artist_id']==ARTIST for p in pre['exhibition_participants'])
        assert not db.execute('select id from audit_log where request_id=%s',(OP,)).fetchall()
    originals=[]
    for o in OBJECTS:
        entry=next(x for x in pre['exhibition_entries']if x['id']==o['entry'])
        assert entry['artwork_id'] is None and entry['catalogue_number']==o['number'] and entry['participation']=='catalogued'
        assert entry['lender_label']=='The Rhode Island School of Design'
        sr=next(x for x in pre['exhibition_source_records']if x['id']==entry['source_record_id'])
        raw=gzip.decompress(Path(sr['capture_url']).read_bytes());assert c.sha(raw)==sr['capture_sha256']
        originals.append(sr)
    visual=dict(at=c.now(),method='Rendered original catalogue PDF pages and individually viewed using view_image.',pages=[dict(pdf_page=o['pdf_page'],printed_page=o['printed_page'],catalogue_number=o['number'],path=str(R/('catalogue-page'+str(o['pdf_page'])+'.png')),sha256=c.sha((R/('catalogue-page'+str(o['pdf_page'])+'.png')).read_bytes()))for o in OBJECTS],observation='Both original entries explicitly credit The Rhode Island School of Design as lender. No154 names tempera on canvas and Butts provenance; no176 names watercolor and signed1803. All other pages and artwork reproductions are outside this visual-review claim.',artwork_images_viewed=0,new_images=0,passed=True)
    p=dict(at=c.now(),operation=OP,target=t,objects=OBJECTS,event_id=EVENT,artist_id=ARTIST,institution_id=INST,source_id=SOURCE,sources=sources,original_catalogue_records=originals,pdf_receipt=pdf,visual=visual,preimage=pre,duplicate_review=dup,scope=dict(exhibition_years=[1600,1989],main_work_cutoff=1970),rights=dict(actual_per_object_statement='Public Domain; CC0 1.0 Universal Public Domain Dedication',image_downloads=0,image_licence_not_generalized=True),source_access=dict(direct_request_403_hold=True,web_pages_successfully_returned_before_hold=True,origin_html_not_captured=True,web_extracted_pages_captured_with_sha256=True,no_requests_after_hold=True))
    save('immutable-plan.json',p);c.save(B/'immutable-plan.json',p);pin=c.sha((E/'immutable-plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin))
    save('visual-review-verification.json',visual)
    save('source-capture-verification.json',dict(at=c.now(),plan_sha256=pin,museum_captures=[{k:v for k,v in s.items()if k!='source_text'}for s in sources.values()],original_catalogue_records=[dict(id=s['id'],source_url=s['source_url'],sha256=s['capture_sha256'],body_path=s['capture_url'])for s in originals],original_pdf=pdf,all_capture_checksums_verified=True,capture_method_limitations=p['source_access'],passed=True))
    save('candidate-reconciliation-verification.json',dict(at=c.now(),selected_existing_entries=2,prepared_review_artworks=2,prepared_exact_links=2,objects=OBJECTS,creator_catalogue_rows_reviewed=len(c.load(E/'startup-production-reconciliation.json')['creator_works']),title_candidates_reviewed=len(dup['artworks']),provider_id_collisions_rejected=dup['identifiers'],decision='No existing native RISD accession or Blake-title match. All149 broad title candidates differ by documented creator, date, medium or native holding identity. Three numeric matches belong to NGA or MALI, not RISD. Reuse existing Blake and RISD institution.',checklist_remains_partial=True,passed=True))
    print('Prepared two review artworks and two existing-entry exact links.',flush=True)

def audit(db,typ,ident,before,record,pin):
    db.execute('insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,%s,%s,%s,%s,%s,%s)',(ACTOR,'continuous_exhibition_exact_object_reconciliation',typ,ident,OP,Jsonb(before),Jsonb(dict(record=record,plan_sha256=pin))))

def apply():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert c.sha((E/'immutable-plan.json').read_bytes())==c.sha((B/'immutable-plan.json').read_bytes())==pin
    for s in p['sources'].values():body(s)
    body(p['pdf_receipt'])
    with c.connect(write=True) as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        db.execute('select id from exhibition_entries where id=any(%s::uuid[]) order by id for update',([o['entry']for o in OBJECTS],));cur=snapshot(db)
        if cur['artworks']:
            assert (B/'transaction-preimage.json').exists() and len(cur['artworks'])==2
            assert all(any(s['id']==o['source_record'] and s['interpretation'].get('plan_sha256')==pin for s in cur['exhibition_source_records'])for o in OBJECTS)
            print('Own pinned transaction already exists; verify without replay.');return
        assert cur==p['preimage'] and duplicate_query(db)==p['duplicate_review']
        pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=target(db),rows=cur,locks=['artline-curated-ingestion',2026101201])
        c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre);save('production-target-before-write.json',pre['target']|dict(plan_sha256=pin,passed=True))
        db.execute("insert into sources(id,slug,name,source_type,base_url) values(%s,'risd-museum-official-collection','RISD Museum official collection','collection_page','https://risdmuseum.org/')",(SOURCE,))
        for o in OBJECTS:
            rc=p['sources'][o['key']];orig=next(s for s in p['original_catalogue_records']if s['id']==next(e['source_record_id']for e in cur['exhibition_entries']if e['id']==o['entry']))
            ev=dict(operation=OP,plan_sha256=pin,source_sha256=rc['sha256'],source_capture=rc['body_path'],capture_kind=rc['capture_kind'],original_catalogue_sha256=orig['capture_sha256'],original_pdf_sha256=p['pdf_receipt']['sha256'],accession=o['accession'],catalogue_number=o['number'],printed_page=o['printed_page'],pdf_page=o['pdf_page'],basis=o['basis'],qualifications=o['qualifications'],checklist_complete=False,current_display_claim=False,rights=p['rights'])
            db.execute("insert into artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)",(o['id'],'risd-object-'+o['accession'].replace('.','-'),o['title'],c.norm(o['title']),o['date'],o['year'],o['year'],o['precision'],o['work_type'],o['medium'],o['dimensions'],o['accession'],ACTOR,ACTOR))
            db.execute("insert into artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)values(%s,%s,'primary',%s)",(o['id'],ARTIST,'Unqualified official RISD creator attribution. Exact museum object number '+o['accession']+'. Historical exhibition creator label remains separate.'))
            db.execute("insert into external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)values(%s,'artwork',%s,'risd-object-number',%s,%s,%s,%s)",(o['ids']['identifier'],o['id'],o['accession'],rc['url'],SOURCE,rc['retrieved_at']))
            db.execute("insert into citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by)values(%s,'artwork',%s,'native_object_metadata_and_historical_exhibition_match',%s,%s,%s,%s,%s,%s,%s)",(o['ids']['citation'],o['id'],SOURCE,o['accession'],rc['url'],'RISD '+o['accession']+'; Philadelphia1939 no.'+o['number']+', p.'+str(o['printed_page']),json.dumps(ev,ensure_ascii=False),rc['retrieved_at'],ACTOR))
            db.execute("insert into artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)values(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(o['ids']['holding'],o['id'],INST,SOURCE,rc['url'],json.dumps(ev|dict(holding_basis='Official RISD object credit: '+o['credit']+'. Historical loan alone does not establish current ownership.'),ensure_ascii=False),rc['retrieved_at']))
            db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(o['source_record'],EVENT,OP,'risd/'+o['accession'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(object=o,source_text=rc['source_text'],capture_kind=rc['capture_kind'])),Jsonb(ev)))
            old=next(e for e in cur['exhibition_entries']if e['id']==o['entry']);evidence=old['evidence']|dict(canonicalObjectMatchPending=False,canonicalObjectMatch=ev,canonicalMatchSourceRecordID=o['source_record'])
            result=db.execute('update exhibition_entries set artwork_id=%s,match_basis=%s,evidence=%s where id=%s and artwork_id is null',(o['id'],o['basis'],Jsonb(evidence),o['entry']));assert result.rowcount==1
        after=snapshot(db)
        audit(db,'source',SOURCE,None,after['sources'][0],pin)
        for o in OBJECTS:
            for table,typ,ident,key in [('artworks','artwork',o['id'],'id'),('exhibition_entries','exhibition_entry',o['entry'],'id'),('exhibition_source_records','exhibition_source_record',o['source_record'],'id'),('citations','citation',o['ids']['citation'],'id'),('external_identifiers','external_identifier',o['ids']['identifier'],'id'),('artwork_location_assertions','artwork_location_assertion',o['ids']['holding'],'id'),('artwork_artists','artwork_artist',o['id'],'artwork_id')]:
                before=next((x for x in cur[table]if x[key]==ident),None);row=next(x for x in after[table]if x[key]==ident);audit(db,typ,ident,before,row,pin)
        c.save(B/'transaction-postimage.json',dict(at=c.now(),operation=OP,plan_sha256=pin,rows=after))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Transaction committed; independent verification pending.',flush=True)

def verify():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
    assert c.sha((E/'immutable-plan.json').read_bytes())==pin==pre['plan_sha256']==post['plan_sha256'] and pre['rows']==p['preimage']
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        au=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
        assert rows==post['rows'] and len(au)==15 and all(a['after_json']['plan_sha256']==pin for a in au)
    old=pre['rows'];selected={o['entry']for o in OBJECTS}
    for k in ['exhibitions','exhibition_occurrences','exhibition_participants','exhibition_publications','artists','institutions']:assert old[k]==rows[k],k
    assert [x for x in rows['exhibition_entries']if x['id']not in selected]==[x for x in old['exhibition_entries']if x['id']not in selected]
    assert [x for x in rows['exhibition_source_records']if x['id']not in {o['source_record']for o in OBJECTS}]==old['exhibition_source_records']
    assert not old['artworks'] and len(rows['artworks'])==2
    for k in ['artwork_artists','artwork_location_assertions','external_identifiers','citations']:assert not old[k] and len(rows[k])==2
    for o in OBJECTS:
        before=next(x for x in old['exhibition_entries']if x['id']==o['entry']);entry=next(x for x in rows['exhibition_entries']if x['id']==o['entry']);assert before['artwork_id'] is None and entry['artwork_id']==o['id']
        assert all(entry[k]==v for k,v in before.items()if k not in ['artwork_id','evidence','match_basis'])
        w=next(x for x in rows['artworks']if x['id']==o['id']);assert w['status']=='review' and w['primary_media_id'] is None and w['creation_year_start']==w['creation_year_end']==o['year'] and w['date_precision']==o['precision'] and w['accession_number']==o['accession'] and w['current_institution_id']==INST
        s=next(x for x in rows['exhibition_source_records']if x['id']==o['source_record']);assert s['capture_sha256']==p['sources'][o['key']]['sha256'] and s['interpretation']['plan_sha256']==pin
        assert any(a['entity_id']==o['entry'] and a['before_json']==before for a in au)
        assert any(a['entity_id']==o['id'] and a['entity_type']=='artwork' and a['before_json'] is None for a in au)
        assert any(x['artwork_id']==o['id'] and x['artist_id']==ARTIST for x in rows['artwork_artists'])
        for table in ['citations','artwork_location_assertions']:
            x=next(x for x in rows[table]if x.get('entity_id',x.get('artwork_id'))==o['id']);assert json.loads(x['evidence_note'])['plan_sha256']==pin
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=2,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=2,new_images=0,existing_records_enriched=2)
    if not (E/'independent-database-verification.json').exists():save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,audits=au,verified_counts=counts,attribution='Both new works absent and both selected existing-entry artwork IDs null in locked preimage. Persisted museum captures, citation/holding evidence, entry matches and all15 audits carry this plan checksum. Previous and concurrent jobs excluded.',passed=True))
    receipts=[];urls=[('entries',API+'exhibitions/'+EVENT+'/entries?limit=100')]+[(o['key'],API+'artists/'+rows['artists'][0]['slug']+'/works/'+o['id'])for o in OBJECTS]
    for key,url in urls:
        res=requests.get(url,timeout=(15,45));res.raise_for_status();data=res.json();path=R/('public-'+key+'.json');c.save(path,data)
        if key=='entries':
            assert len(data['items'])==28 and not data.get('nextCursor')
            for o in OBJECTS:
                e=next(x for x in data['items']if x['id']==o['entry']);assert e['artworkId']==o['id'] and not e.get('image')
        else:
            o=next(x for x in OBJECTS if x['key']==key);assert data['id']==o['id'] and data['title']==o['title'] and data['status']=='review' and data['accession_number']==o['accession'] and data['creation_year_start']==o['year'] and data['date_precision']==o['precision']
            assert data['holding']['id']==INST and data['display'] is None and data['medium_text']==o['medium'] and data['dimensions_text']==o['dimensions']
            assert any(x['source_url']==p['sources'][key]['url']for x in data['citations'])
        receipts.append(dict(url=res.url,status=res.status_code,raw_response_sha256=c.sha(res.content),saved_json_sha256=c.sha(path.read_bytes()),path=str(path)))
    save('independent-public-verification.json',dict(at=c.now(),receipts=receipts,new_review_artworks=2,new_exact_links=2,checklist_entry_count=28,exact_linked_entries=sum(bool(x['artwork_id'])for x in rows['exhibition_entries']),checklist_still_partial=True,images_added=0,passed=True))
    save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes()))for n in ['immutable-plan.json','transaction-preimage.json','transaction-postimage.json']],postimage_matches_independent_read=True,backups_outside_Documents=True,passed=True))
    print(json.dumps(counts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
