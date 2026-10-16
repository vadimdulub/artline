"""One bounded original-catalogue exact-version reconciliation; no supervisor changes."""
import fcntl, gzip, json, os, subprocess, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT = c.ROOT
E = ROOT / 'docs/research/continuous-exhibitions-20261013/batches/000166'
R = Path.home() / 'Library/Application Support/Artline/continuous-exhibition-research/batches/000166'
B = Path.home() / 'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000166'
OP = 'continuous-exhibitions-20261013-batch-000166'
EVENT = '5c64ef50-18f0-5cf3-8a19-e86adf45c299'
ENTRY = 'e7b27964-fa7b-56f3-bae7-9027ab768cee'
WORK = 'aa11f76b-81f1-5a82-922c-439302e6866c'
OTHER = 'af3de883-69a9-4996-8209-d9cc31b6a159'
ARTIST = 'de003eac-51c4-4057-bec5-4870d243b1b2'
MEDIA = '2fdfe77f-764b-5676-9cc1-8ffcace52e82'
SID = c.uid(OP + '/original-catalogue-174-visual-reconciliation')
ACTOR = 'local-european-research'
API = 'https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
serial = lambda x: json.loads(json.dumps(x, ensure_ascii=False, default=str))
save = lambda n, x: c.save(E / n, x)

def target(db):
    expected = '/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth artline-508319:europe-west1:artline-postgres'
    assert expected in [x.strip() for x in subprocess.check_output(['ps', '-axo', 'command'], text=True).splitlines()]
    assert (db.info.host, db.info.port, db.info.dbname) == ('127.0.0.1', 55519, 'artline')
    row = db.execute('select current_database() database,current_user role,pg_is_in_recovery() recovery').fetchone()
    assert row == dict(database='artline', role='artline_app', recovery=False)
    return dict(at=c.now(), instance='artline-508319:europe-west1:artline-postgres', host=db.info.host, port=db.info.port, **row)

def snapshot(db):
    out = {}
    for table in ['exhibitions', 'exhibition_entries', 'exhibition_occurrences', 'exhibition_participants', 'exhibition_publications', 'exhibition_source_records']:
        col = 'id' if table == 'exhibitions' else 'exhibition_id'
        out[table] = db.execute('select * from ' + table + ' where ' + col + '=%s order by id', (EVENT,)).fetchall()
    for table, col, order in [('artworks', 'id', 'id'), ('artwork_artists', 'artwork_id', 'artwork_id,artist_id'), ('artwork_location_assertions', 'artwork_id', 'id')]:
        out[table] = db.execute('select * from ' + table + ' where ' + col + '=any(%s::uuid[]) order by ' + order, ([WORK, OTHER],)).fetchall()
    for table in ['citations', 'external_identifiers']:
        out[table] = db.execute('select * from ' + table + " where entity_type='artwork' and entity_id=any(%s::uuid[]) order by id", ([WORK, OTHER],)).fetchall()
    out['media_assets'] = db.execute('select * from media_assets where id=%s', (MEDIA,)).fetchall()
    return serial(out)

def check_receipt(rc):
    p = Path(rc['body_path']); raw = gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes()
    assert c.sha(raw) == rc['sha256'] and len(raw) == rc['bytes'] and rc['status'] == 200
    return raw

def prepare():
    B.mkdir(parents=True, exist_ok=True); B.chmod(0o700)
    with c.connect() as db:
        t = target(db); pre = snapshot(db)
        candidates = db.execute("select a.id,a.title,a.accession_number,a.current_institution_id from artworks a join artwork_artists aa on aa.artwork_id=a.id where aa.artist_id=%s and (a.normalized_title like '%%dragon%%' or a.normalized_title like '%%woman%%sun%%') order by a.id", (ARTIST,)).fetchall()
    entry = next(x for x in pre['exhibition_entries'] if x['id'] == ENTRY)
    assert entry['artwork_id'] is None and entry['catalogue_number'] == '174' and entry['lender_label'] == 'The Brooklyn Museum' and entry['participation'] == 'catalogued'
    assert next(x for x in pre['exhibition_entries'] if x['catalogue_number'] == '173')['artwork_id'] == OTHER
    assert not any(x['artwork_id'] == WORK for x in pre['exhibition_entries'])
    source = next(x for x in pre['exhibition_source_records'] if x['id'] == entry['source_record_id'])
    raw, ocr = c.capture(source['source_url']); assert c.sha(raw) == source['capture_sha256']; check_receipt(ocr)
    pdf = c.load(E.parent / '000070/plan.json')['pdf_receipt']; check_receipt(pdf)
    assert c.sha((R / 'blake1939.pdf').read_bytes()) == pdf['sha256']
    work = next(x for x in pre['artworks'] if x['id'] == WORK)
    assert work['creation_year_start'] == 1803 and work['creation_year_end'] == 1805 and work['status'] == 'review'
    assert work['current_institution_id'] == '5c8ba9fd-8765-57dc-b653-39ba8d9964e6'
    assert any(x['artist_id'] == ARTIST for x in pre['exhibition_participants'])
    cite = next(x for x in pre['citations'] if x['entity_id'] == WORK and x['field_name'] == 'museum_location_lead_review')
    wiki = json.loads(cite['evidence_note'])['source_receipt']
    wp = ROOT / wiki['body_path']; wr = gzip.decompress(wp.read_bytes()); assert c.sha(wr) == wiki['sha256']
    archived = R / 'wikiart-existing-capture.body.gz'; archived.write_bytes(wp.read_bytes())
    wiki = wiki | dict(original_body_path=wiki['body_path'], body_path=str(archived)); check_receipt(wiki)
    text = BeautifulSoup(wr, 'html.parser').get_text(' ', strip=True)
    assert 'Brooklyn Museum' in text and 'William Blake' in text
    media = pre['media_assets'][0]; image_path = ROOT / 'apps/web/public' / media['storage_path'].lstrip('/')
    assert c.sha(image_path.read_bytes()) == media['checksum_sha256'] and image_path.stat().st_size == media['byte_size'] <= 100000
    with Image.open(image_path) as im: assert im.size == (media['width'], media['height']); im.verify()
    visual = dict(at=c.now(),method='Actual assistant image-tool visual review of three rendered original PDF pages and the existing catalogue reproduction.',
        pages=[dict(pdf_page=n,path=str(R/f'catalogue-{n}.png'),sha256=c.sha((R/f'catalogue-{n}.png').read_bytes())) for n in [146,147,150]],
        printed_text_page=124,existing_image=dict(path=str(image_path),sha256=media['checksum_sha256']),
        observations='PDF147 reproduces the standing dragon viewed from behind, legs spread, large outstretched bat wings, central curving tail, and a reclining woman at lower right. The existing WikiArt reproduction shows the same composition and details. PDF146 depicts the different flying dragon and seated winged woman described as no173. PDF150/printed124 explicitly identifies no174 as another watercolor version, lent by The Brooklyn Museum, and no173 as lent by A. Edward Newton.',
        individually_viewed_images=4,new_images_prepared=0,no_unsampled_visual_review_claim=True,passed=True)
    basis='Original Philadelphia 1939 catalogue no174, printed p124 (PDF150), explicitly lists the watercolor and The Brooklyn Museum as lender. Its reproduction at PDF147 visually matches the existing Artline/WikiArt object57726f1fedc2cb3880b962c5 in the distinctive back-facing standing dragon, spread wings and legs, curving tail, and reclining woman. The retained WikiArt record confirms William Blake, Brooklyn location and 1803–1805 date range. PDF146 and the adjacent no173 description show the distinct flying-dragon NGA version; no173 remains unchanged. Primary catalogue number, lender, medium, creator and exact illustrated composition support this object-level link. Modern Brooklyn native ID/accession remain unverified after HTTP429 and are not inserted. This does not create a holding or current-display assertion.'
    hold = c.load(c.RUN / 'access-holds/www.brooklynmuseum.org.json')
    assert hold['status'] == 429 and hold['url'].endswith('/4368')
    save('brooklyn-access-hold-verification.json', dict(at=c.now(),receipt=hold,requests=1,retries=0,alternate_host_requests=0,decision='No retry or bypass. Modern object4368/accession15.368 remain unverified discovery leads. Link relies on already retained primary exhibition catalogue and exact existing reproduction.',passed=True))
    plan = dict(at=c.now(),operation=OP,event_id=EVENT,entry_id=ENTRY,artwork_id=WORK,new_source_id=SID,target=t,preimage=pre,
        source=source,ocr_receipt=ocr,pdf_receipt=pdf,wikiart_receipt=wiki,visual_review=visual,basis=basis,candidates=serial(candidates),
        verified_source_identity=dict(primary_catalogue_id='williamblakedesc00phil/174',wikiart_native_id='57726f1fedc2cb3880b962c5',modern_museum_accession=None,modern_museum_native_id=None),
        scope=dict(exhibition_years=[1600,1989],main_artwork_cutoff=1970,new_main_artworks=0),images_added=0)
    c.save(E/'immutable-plan.json',plan); c.save(B/'immutable-plan.json',plan)
    pin = c.sha((E/'immutable-plan.json').read_bytes()); save('plan-pin.json',dict(operation=OP,sha256=pin))
    save('visual-review-verification.json',visual)
    save('source-capture-verification.json',dict(at=c.now(),receipts=[ocr,pdf,wiki],all_checksums_verified=True,source_bodies_used_outside_Documents=True,primary_catalogue_proves_participation=True,new_museum_source_facts_inferred=False,passed=True))
    save('candidate-reconciliation-verification.json',dict(at=c.now(),selected_entries=1,prepared_exact_links=1,other_versions=candidates,full_creator_catalogue='blake-existing-artwork-reconciliation.json',basis=basis,no_duplicate_work_created=True,no173_preserved=True,passed=True))
    print('Prepared one exact link to an existing illustrated work.')

def apply():
    p=c.load(E/'immutable-plan.json'); pin=c.load(E/'plan-pin.json')['sha256']
    assert c.sha((E/'immutable-plan.json').read_bytes())==c.sha((B/'immutable-plan.json').read_bytes())==pin
    for rc in [p['ocr_receipt'],p['pdf_receipt'],p['wikiart_receipt']]:check_receipt(rc)
    with c.connect(write=True) as db:
        t=target(db)
        db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('select pg_advisory_xact_lock(2026101201)')
        db.execute('select id from exhibition_entries where id=%s for update',(ENTRY,))
        cur=snapshot(db)
        old=next(x for x in cur['exhibition_entries'] if x['id']==ENTRY)
        if old['artwork_id'] is not None:
            assert old['artwork_id']==WORK and old['evidence']['canonicalObjectMatch']['plan_sha256']==pin and (B/'transaction-preimage.json').exists()
            print('Own checksum-pinned link already present; verify without replay.');return
        assert cur==p['preimage'], 'Concurrent changes require a new review; no overwrite.'
        pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,rows=cur,locks=['artline-curated-ingestion',2026101201])
        c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre);save('production-target-before-write.json',t|dict(plan_sha256=pin,passed=True))
        ev=dict(operation=OP,plan_sha256=pin,basis=p['basis'],original_catalogue_sha256=p['ocr_receipt']['sha256'],original_pdf_sha256=p['pdf_receipt']['sha256'],wikiart_capture_sha256=p['wikiart_receipt']['sha256'],source_identity=p['verified_source_identity'],visual_evidence='visual-review-verification.json',catalogue_number='174',printed_page=124,pdf_text_page=150,pdf_plate_page=147,checklist_complete=False,current_display_claim=False,new_holding_claim=False)
        rc=p['pdf_receipt']
        db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(SID,EVENT,OP,'williamblakedesc00phil/174/visual-object-match',rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(original_entry=p['source']['source_payload'],wikiart_receipt=p['wikiart_receipt'],visual=p['visual_review'])),Jsonb(ev)))
        evidence=old['evidence']|dict(canonicalObjectMatchPending=False,canonicalObjectMatch=ev,canonicalMatchSourceRecordID=SID)
        res=db.execute('update exhibition_entries set artwork_id=%s,match_basis=%s,evidence=%s where id=%s and artwork_id is null',(WORK,p['basis'],Jsonb(evidence),ENTRY));assert res.rowcount==1
        after=snapshot(db)
        for typ,ident,before,record in [('exhibition_entry',ENTRY,old,next(x for x in after['exhibition_entries'] if x['id']==ENTRY)),('exhibition_source_record',SID,None,next(x for x in after['exhibition_source_records'] if x['id']==SID))]:
            db.execute('insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,%s,%s,%s,%s,%s,%s)',(ACTOR,'continuous_exhibition_exact_object_reconciliation',typ,ident,OP,Jsonb(before),Jsonb(dict(record=record,plan_sha256=pin))))
        c.save(B/'transaction-postimage.json',dict(at=c.now(),operation=OP,plan_sha256=pin,rows=after))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True))
    print('Committed; independent verification pending.')

def verify():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
    assert c.sha((E/'immutable-plan.json').read_bytes())==pre['plan_sha256']==post['plan_sha256']==pin and pre['rows']==p['preimage']
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db)
        audits=serial(db.execute('select * from audit_log where entity_id=any(%s::uuid[]) and request_id=%s order by entity_id',([ENTRY,SID],OP)).fetchall())
    assert rows==post['rows'] and len(audits)==2
    before=next(x for x in pre['rows']['exhibition_entries'] if x['id']==ENTRY);entry=next(x for x in rows['exhibition_entries'] if x['id']==ENTRY)
    assert before['artwork_id'] is None and entry['artwork_id']==WORK and entry['evidence']['canonicalObjectMatch']['plan_sha256']==pin
    for k in before:
        if k not in ['artwork_id','evidence','match_basis']:assert before[k]==entry[k],k
    for k in rows:
        if k not in ['exhibition_entries','exhibition_source_records']:assert rows[k]==pre['rows'][k],k
    assert [x for x in rows['exhibition_entries'] if x['id']!=ENTRY]==[x for x in pre['rows']['exhibition_entries'] if x['id']!=ENTRY]
    assert [x for x in rows['exhibition_source_records'] if x['id']!=SID]==pre['rows']['exhibition_source_records']
    new=next(x for x in rows['exhibition_source_records'] if x['id']==SID);assert new['interpretation']['plan_sha256']==pin and new['capture_sha256']==p['pdf_receipt']['sha256']
    for a in audits:assert a['after_json']['plan_sha256']==pin and a['before_json']==(before if a['entity_id']==ENTRY else None)
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=1,new_images=0,existing_records_enriched=1)
    if not (E/'independent-database-verification.json').exists():
        save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,audits=audits,verified_counts=counts,attribution='Existing entry was null in locked preimage; exact after-image and new persisted primary-source record carry this operation and plan checksum. Previous/concurrent changes excluded.',passed=True))
    else:
        prior=c.load(E/'independent-database-verification.json');assert prior['rows']==rows and prior['audits']==audits and prior['plan_sha256']==pin
    receipts=[]
    for name,url in [('entries',API+'exhibitions/'+EVENT+'/entries?limit=100'),('event',API+'exhibitions/'+EVENT)]:
        res=requests.get(url,timeout=(15,45));res.raise_for_status();data=res.json();c.save(R/('public-'+name+'.json'),data)
        if name=='entries':
            assert len(data['items'])==28 and not data.get('nextCursor');item=next(x for x in data['items'] if x['id']==ENTRY)
            assert item['artworkId']==WORK and item['image'];assert next(x for x in data['items'] if x.get('catalogueNumber')=='173')['artworkId']==OTHER
        else:assert data['checklistState']=='partial'
        receipts.append(dict(url=res.url,status=res.status_code,sha256=c.sha(res.content),capture=str(R/('public-'+name+'.json'))))
    save('public-api-verification.json',dict(at=c.now(),receipts=receipts,entry=ENTRY,artwork=WORK,checklist_entries=28,exact_links=15,remaining_documentary_entries=13,passed=True))
    print(json.dumps(dict(counts=counts,image=item['image']),ensure_ascii=False))

def finalize():
    dbv=c.load(E/'independent-database-verification.json');pub=c.load(E/'public-api-verification.json');p=c.load(E/'immutable-plan.json');pin=dbv['plan_sha256']
    assert dbv['passed'] and pub['passed'] and c.sha((E/'immutable-plan.json').read_bytes())==pin
    media=p['preimage']['media_assets'][0];url='https://artlines.org'+media['storage_path']
    res=requests.get(url,timeout=(15,45));res.raise_for_status();assert c.sha(res.content)==media['checksum_sha256'] and len(res.content)==media['byte_size']
    (R/'verified-existing-image.jpg').write_bytes(res.content)
    with Image.open(R/'verified-existing-image.jpg') as im:assert im.size==(464,600);im.verify()
    save('independent-public-verification.json',dict(at=c.now(),api_verification=pub,existing_asset=dict(url=url,status=res.status_code,sha256=c.sha(res.content),bytes=len(res.content),path=str(R/'verified-existing-image.jpg')),new_exact_links=1,new_images=0,existing_image_reused=True,passed=True))
    pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
    assert pre['rows']==p['preimage'] and post['rows']==dbv['rows']
    save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes()))for n in ['immutable-plan.json','transaction-preimage.json','transaction-postimage.json']],postimage_matches_independent_read=True,passed=True))
    nxt='Resume the Cleveland missing-image queue after native106969, with source rights and individual visual review. For the next exact-object batch, research Blake1939 no165 (Infant Jesus Praying, Philip Hofer lender) through accessible Harvard records and original catalogue evidence. Preserve Brooklyn429, MFA/RISD access and NGA161 provenance holds; no174 is complete.'
    names=['startup-recovery-verification.json','registry-and-scope-verification.json','brooklyn-access-hold-verification.json','source-capture-verification.json','visual-review-verification.json','candidate-reconciliation-verification.json','production-target-before-write.json','transaction-preimage.json','independent-database-verification.json','independent-public-verification.json','backup-verification.json']
    rel=lambda n:str((E/n).relative_to(ROOT))
    qpath=E.parents[1]/'source-queue.json';changed={'philadelphia_museum_art','brooklyn_museum'}
    with qpath.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        q=c.load(qpath);before=serial(q);c.save(B/'source-queue-preimage.json',before)
        for s in q['sources']:
            if s['source_id'] not in changed:continue
            cur=s.setdefault('cursor',{});cur['batch166']=dict(exhibition_id=EVENT,catalogue_number='174',entry_id=ENTRY,artwork_id=WORK,plan_sha256=pin,new_exact_links=1,new_images=0,existing_image_reused=True,primary_source_identity=p['verified_source_identity'],primary_catalogue_url=p['pdf_receipt']['url'],pdf_page=150,plate_page=147,exact_linked_entries=15,remaining_documentary_entries=13,next=nxt,evidence=rel('independent-database-verification.json'))
            cur['next']=nxt;s['last_checked_at']=c.now()
            if s['source_id']=='philadelphia_museum_art':
                s['research_status']='batch166_blake1939_no174_exact_existing_work_link_verified'
            else:
                s['research_status']='batch166_existing_catalogue_plate_match_verified_direct_provider429_held'
                hold=c.load(E/'brooklyn-access-hold-verification.json')['receipt']
                s.setdefault('holds',[]).append(dict(key='direct-provider-http429-batch166',url=hold['url'],at=hold['retrieved_at'],status=429,reason='Provider returned HTTP429. No repeat or alternate-host request. Modern object4368/accession15.368 remain unverified and were not inserted; exact participation is established independently from the retained1939 original catalogue.',evidence=rel('brooklyn-access-hold-verification.json')))
                s['counting_note']='Batch166 is the same single exact link recorded under Philadelphia, counted once. No new main artwork or image; existing catalogue records unchanged.'
            s['evidence']=list(dict.fromkeys(s.get('evidence',[])+[rel(n)for n in names]))
        assert {s['source_id']:s for s in q['sources'] if s['source_id'] not in changed}=={s['source_id']:s for s in before['sources'] if s['source_id'] not in changed}
        assert all(q[k]==before[k] for k in q if k!='sources')
        tmp=qpath.with_suffix('.batch166.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
        check=c.load(qpath);assert check==q
    save('queue-update-verification.json',dict(at=c.now(),updated_sources=sorted(changed),unrelated_sources_and_supplemental_sources_unchanged=True,registry_sha256=q['registry_sha256'],queue_sha256=c.sha(qpath.read_bytes()),resume=nxt,passed=True));names.append('queue-update-verification.json')
    startup=c.load(E/'startup-recovery-verification.json');cp=c.load(E.parents[1]/'CHECKPOINT.json');sup=cp['supervisor_pid'];worker=cp['worker_pid'];assert cp['inflight']['batch']==166
    lines=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
    assert len([x for x in lines if x.strip().startswith(str(sup)+' ') and 'continuous-exhibition-research.py run' in x])==1
    assert len([x for x in lines if x.strip().startswith(str(worker)+' ') and str(sup) in x])==1
    locks=subprocess.check_output(['lsof','-nP',str(R.parents[1]/'supervisor.lock')],text=True);assert str(sup)in locks and str(worker)in locks
    for x in startup['protected_files']:assert c.sha(Path(x['path']).read_bytes())==x['sha256']
    save('continuation-final-verification.json',dict(at=c.now(),supervisor_pid=sup,worker_pid=worker,inherited_lock=locks,single_existing_exhibition_supervisor_and_worker_running=True,protected_files_unchanged=startup['protected_files'],separate_artwork_programme_modified=False,no_new_supervisor_started=True,passed=True));names.append('continuation-final-verification.json')
    counts=dbv['verified_counts'];checkpoint=dict(at=c.now(),batch=166,stage='verified_complete',operation=OP,plan_sha256=pin,verified_counts=counts,next_task=nxt,checklist_state='partial',remaining_documentary_entries=13,evidence_paths=[rel(n)for n in names],external_supervisor_unchanged=True,real_local_connections=0)
    c.save(E/'CHECKPOINT.json',checkpoint);c.save(R/'CHECKPOINT.json',checkpoint);names.append('CHECKPOINT.json')
    result=dict(outcome='progress',summary='Verified one new exact link for Blake1939 catalogue no174 to the existing illustrated Brooklyn-version artwork. Original catalogue text and plates distinguish it from no173. Review states and partial checklist preserved; no new artwork or image. Queue and batch checkpoint saved; existing supervisor verified running.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(n)for n in names])
    save('final-verification.json',dict(at=c.now(),database_verified=True,public_api_and_existing_image_verified=True,locked_preimage_and_persisted_source_checksum_attribution_verified=True,previous_and_concurrent_changes_excluded=True,result=result));result['evidence_paths'].append(rel('final-verification.json'))
    c.save(E/'worker-result.json',result);c.save(R/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':globals()[sys.argv[1]]()
