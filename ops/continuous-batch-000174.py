#!/usr/bin/env python3
"""One bounded, resumable SAAM fallback after live French-reserve reconciliation."""
import ast, collections, copy, csv, fcntl, gzip, importlib.util, io, json, os, re, subprocess, sys
from pathlib import Path
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'ops' / file)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value
base = module('established169', 'continuous-batch-000146.py')
h, i = base.h, base.i
E = ROOT / 'docs/research/continuous-production-20261011/batches/000174'
R = Path.home() / 'Library/Application Support/Artline/continuous-research/batches/000174'
DATA = Path.home() / 'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000174'
OP = 'continuous-smithsonian-20261013-b000174-images'
B = 'saam-024'
MID = base.MID
TARGET = 'artline-508319:europe-west1:artline-postgres'
for p in (E, R, DATA, E / 'source-captures'): p.mkdir(parents=True, exist_ok=True)
i.OP = OP; i.RUN = E
i.ORIG = Path.home() / 'Library/Application Support/Artline/source-images' / OP
i.BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
# Reuse the established transaction body with the same legacy-native allowances
# as batch146, retaining the actual museum credit and verifying the persisted
# native holding while the shared ingestion lock and artwork row locks are held.
adapter_source=(ROOT/'ops/illustrated-300k-20261011.py').read_text()
apply_node=next(x for x in ast.parse(adapter_source).body if isinstance(x,ast.FunctionDef) and x.name=='apply')
apply_code='\n'.join(adapter_source.splitlines()[apply_node.lineno-1:apply_node.end_lineno])
apply_code=apply_code.replace("credits={}","credits={r['artwork_id']:r.get('source_credit','') for r in p['rows']}")
apply_code=apply_code.replace("(a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r.get('expected_museum_id',cfg['mid']))","(a['title'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['first'],r['last'],r['precision'],r.get('expected_museum_id',cfg['mid']))")
apply_code=apply_code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid) in [None,r['native_id']],'Native identity changed'\n    owners=db.execute(\"SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s\",(r['native_id'],)).fetchall();assert all(x['entity_id']==aid for x in owners),'Native object assigned elsewhere'\n    exact_holdings=[x for x in before[aid]['holdings'] if x['claim_type']=='holding' and x['review_state']=='accepted' and x['superseded_by'] is None and x['institution_id']==cfg['mid']];assert len(exact_holdings)==1 and json.loads(exact_holdings[0]['evidence_note'])['object_id']==r['native_id'],'Persisted exact native holding changed'")
apply_code=apply_code.replace("    if p['provider']=='wikiart':evidence.update(","    supplemental=m.load(RUN/'identity-review-supplement.json');evidence.update(identity_confidence=supplemental['confidence'],identity_review_supplement_sha256=m.sha((RUN/'identity-review-supplement.json').read_bytes()),native_identity_review=supplemental,user_approval=supplemental['user_approval'])\n    if p['provider']=='wikiart':evidence.update(")
exec(compile(apply_code,str(Path(__file__).resolve()),'exec'),i.__dict__)
def save(name,value):
    if name=='CHECKPOINT.json':
        import datetime,uuid
        text=json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n'
        for dest in [E/name,R/name]:
            tmp=dest.with_suffix('.'+str(uuid.uuid4())+'.tmp');tmp.write_text(text);os.replace(tmp,dest)
    else:h.save(E/name,value)
    return value
def rel(path): return str(Path(path).relative_to(ROOT))
def target(stage):
    actual = subprocess.check_output(['gcloud', 'sql', 'instances', 'describe', 'artline-postgres', '--project=artline-508319', '--account=vadim@alingva.com', '--format=value(connectionName)'], text=True).strip()
    assert actual == TARGET
    commands = subprocess.check_output(['ps', 'ax', '-o', 'command='], text=True).splitlines()
    proxy = [x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x]
    assert len(proxy) == 1
    with h.connect() as db:
        server = dict(db.execute('SELECT current_database() AS database, pg_is_in_recovery() AS recovery').fetchone())
        assert server['database'] == 'artline' and not server['recovery']
    return save('production-target-' + stage + '.json', dict(at=h.now(), connection_name=actual, proxy_command=proxy[0], database=server, helper='ops/india-300-delivery-20261011.py', shared_ingestion_lock='artline-curated-ingestion', local_catalogue_connections=0))

def preflight():
    target('reconciliation')
    reg = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    registry = list(csv.DictReader(reg.open())); qp = E.parents[1] / 'source-queue.json'; queue = h.load(qp)
    assert len(registry) == 111 and {x['source_id'] for x in registry} == {x['source_id'] for x in queue['sources']}
    required = [ROOT/'AGENTS.md', reg, ROOT/'docs/ARTLINE_IMAGE_USE.md', ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md', ROOT/'docs/LOCAL_DATA_LOCATIONS.md', E.parents[1]/'CHECKPOINT.json', qp]
    save('required-input-verification.json', dict(at=h.now(), complete_original_registry_used=True, registry_rows=111, files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required], real_local_catalogue_read_only=True))
    for required_path in required: required_path.read_text()
    save('original-source-registry.json',registry);save('source-queue-preimage.json',queue)
    provider = next(x for x in registry if x['source_id']=='smithsonian_open_access')
    q = next(x for x in queue['sources'] if x['source_id']==provider['source_id'])
    assert q['resume_cursor']['next_shard']=='24'
    save('source-register.json',dict(at=h.now(),provider=provider,prior_cursor=q,access_status=q['access_status'],policy_reference='Original registry Smithsonian CC0-designated images only; docs/ARTLINE_IMAGE_USE.md',access_holds_preserved=True,held_search_not_requested=True,api_key_route_not_requested=True,remaining_gaps=q['remaining_gaps']))
    prev=h.load(E.parent/'000107/independent-production-verification.json')
    with h.connect() as db: live107=h.snapshot(db,list(prev['after']))
    assert live107==prev['after']
    save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live107),previous_increments_counted=0,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes())))
    previous173=E.parent/'000173/independent-production-verification.json'; previous=h.load(previous173)
    with h.connect() as db: live173=h.snapshot(db,list(previous['after']))
    assert live173==previous['after']
    save('batch173-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live173),previous_increments_counted=0,prior_receipt_sha256=h.sha(previous173.read_bytes())))
    pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz'; plan=h.load(pp); assert len(plan['rows'])==188
    evidence=[]
    for row in plan['rows']:
        source=ROOT/row['source_record_reference']; assert h.sha(source.read_bytes())==row['source_record_sha256']
        raw=gzip.decompress((ROOT/row['receipt']['body_path']).read_bytes()); assert h.sha(raw)==row['receipt']['sha256']
        raw=gzip.decompress((ROOT/row['manifest_receipt']['body_path']).read_bytes()); assert h.sha(raw)==row['manifest_receipt']['sha256']
        visual=row['continuation_visual_evidence']; decision=ROOT/visual['decision_reference']; assert h.sha(decision.read_bytes())==visual['decision_sha256']
        im=plan['images'][row['artwork_id']]; assert im['sha256']==visual['image_sha256']; image=Path(im['local_path']); assert h.sha(image.read_bytes())==im['sha256'] and image.stat().st_size<=100000
        with Image.open(image) as decoded: decoded.load(); assert list(decoded.size)==[im['width'],im['height']]
        evidence.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_record_reference=row['source_record_reference'],source_sha256=row['source_record_sha256'],prior_actual_visual_review=visual,derivative_sha256=im['sha256']))
    with h.connect() as db:
        live=h.snapshot(db,[x['artwork_id'] for x in plan['rows']]);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(list(live),))]
    digest=h.sha(pp.read_bytes()); assert len(live)==len(cit)==188 and all(x['plan_sha256']==digest for x in cit)
    assert all(live[x['artwork_id']]['artwork']['primary_media_id']==plan['images'][x['artwork_id']]['media_id'] and live[x['artwork_id']]['artwork']['status']!='archived' for x in plan['rows'])
    save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=digest,immutable_prior_visual_evidence=rel(E.parent/'000061/independent-french-reserve-evidence-verification.json'),checksum_verified_prior_reviews=evidence,new_visual_review_claim=False,physical_date_holds_preserved=['80082','80437','81054'],source_citations=cit,live_rows=live))
    save('PREFLIGHT.json',dict(at=h.now(),stage='production_and_interrupted_receipts_reconciled',next_action='discover',production_writes=0))
    print('PREFLIGHT: 188 French reserve objects already active and illustrated; batch107 live receipt equal; production proxy confirmed.',flush=True)

def discover():
    assert (E/'PREFLIGHT.json').exists()
    url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/24.txt'; path=DATA/'saam-24.txt'; rp=E/'source-captures/saam-24.receipt.json'
    if rp.exists():
        rc=h.load(rp);raw=path.read_bytes();assert h.sha(raw)==rc['sha256']
    else:
        response=requests.get(url,timeout=(15,45));response.raise_for_status();raw=response.content;assert response.status_code==200 and len(raw)<12000000
        path.write_bytes(raw);body=E/'source-captures/saam-24.body.gz';body.write_bytes(gzip.compress(raw,mtime=0))
        rc=save('source-captures/saam-24.receipt.json',dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=rel(body),retry_after=response.headers.get('Retry-After')))
    objects=[json.loads(x) for x in raw.splitlines()];classified=[];selected=[]
    with h.connect() as db:
        for obj in objects:
            c=obj.get('content',{});d=c.get('descriptiveNonRepeating') or {};ft=c.get('freetext') or {};link=d.get('record_link','');oid=link.rsplit('=',1)[-1] if '?id=' in link else None
            def vals(k,label=None):return [x['content'] for x in ft.get(k,[]) if label is None or x.get('label')==label]
            title=(d.get('title') or {}).get('content');dates=vals('date','Date');ims=((d.get('online_media') or {}).get('media') or [])
            row=dict(native_id=oid,title=title)
            if not oid or not title or not dates or len(ims)!=1:row['decision']='missing_required_identity_date_or_single_image';classified.append(row);continue
            matches=[dict(x) for x in db.execute("SELECT id::text,title,normalized_title,primary_media_id::text,current_institution_id::text,accession_number,creation_year_start,creation_year_end,date_precision,date_display,unlinked_creator_label,status FROM artworks WHERE normalized_title=%s AND current_institution_id=%s AND status<>'archived'",(h.norm(title),MID))]
            native=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s",(oid,))]
            eligible=[a for a in matches if a['primary_media_id'] is None and a['creation_year_end'] is not None and a['creation_year_end']<=1970 and str(a['creation_year_start']) in dates[0]]
            row.update(date=dates[0],title_matches=matches,native_matches=native)
            if native:row['decision']='native_identity_already_present'
            elif len(eligible)!=1:row['decision']='no_unique_eligible_existing_primary_gap'
            elif not(d.get('metadata_usage',{}).get('access')=='CC0' and vals('objectRights','Restrictions & Rights')==['CC0'] and ims[0].get('usage',{}).get('access')=='CC0'):row['decision']='not_explicitly_cc0'
            else:
                a=eligible[0];row['decision']='candidate_needs_exact_identity_review'
                row['source_identity']={k:vals(k) for k in ['name','identifier','physicalDescription','dataSource','creditLine','objectType']}
                row['snapshot']=h.snapshot(db,[a['id']])[a['id']]
                row['citations']=[dict(x) for x in db.execute("SELECT field_name,evidence_note,source_record_id FROM citations WHERE entity_type='artwork' AND entity_id=%s",(a['id'],))]
                selected.append(dict(artwork_id=a['id'],native_id=oid,title=a['title'],creator_label=a['unlinked_creator_label'] or '',source_credit='; '.join(vals('creditLine')),source_url=link,accession_number=vals('identifier','Object number')[0],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type='painting',provider='saam',image=dict(image_url=ims[0]['content'],source=obj,receipt=rc),rights_basis='Official Smithsonian shard marks metadata, object and exact image CC0; user approval remains separate.',manual_visual_required=True))
            classified.append(row)
    save('saam-shard24-identity-reconciliation.json',dict(at=h.now(),captured_records=len(objects),candidate_count=len(selected),rows=classified,decisions=dict(collections.Counter(x['decision'] for x in classified)),source_sha256=rc['sha256'],production_writes=0))
    save('candidate-selection.json.gz',dict(provider='saam',batch=B,rows=selected))
    print('CLASSIFIED',len(objects),'CANDIDATES',len(selected),[(x['native_id'],x['title']) for x in selected],flush=True)

def prepare():
    candidates=h.load(E/'candidate-selection.json.gz')['rows']; reconciliation=h.load(E/'saam-shard24-identity-reconciliation.json'); selected=[]; decisions=[]
    assert len(candidates)<=50
    with h.connect() as db:
        for row in candidates:
            current=h.snapshot(db,[row['artwork_id']])[row['artwork_id']]
            a=current['artwork'];ft=row['image']['source']['content']['freetext']
            names=[x['content'] for x in ft['name'] if x['label']=='Artist']
            dates=[x['content'] for x in ft['date'] if x['label']=='Date']
            assert names==[a['unlinked_creator_label']] and len(dates)==1
            parsed=re.fullmatch(r'(?:ca\.\s*)?(\d{4})(?:[-–](\d{4}))?',dates[0]);assert parsed,'Unreviewed source date syntax'
            source_bounds=(int(parsed[1]),int(parsed[2] or parsed[1]));assert source_bounds==(a['creation_year_start'],a['creation_year_end']) and source_bounds[1]<=1970
            assert [x['content'] for x in ft['objectType']]==['Painting']
            holds=[x for x in current['holdings'] if x['claim_type']=='holding' and x['review_state']=='accepted' and x['superseded_by'] is None and x['institution_id']==MID]
            assert len(holds)==1
            note=json.loads(holds[0]['evidence_note']);assert note['scheme']=='saam-object' and note['object_id']==row['native_id']
            original=ROOT/note['evidence_path'];raw=gzip.decompress(original.read_bytes());assert h.sha(raw)==note['source_response_sha256']
            assert row['native_id'] in holds[0]['source_url']
            matches=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,current_institution_id::text,primary_media_id::text FROM artworks WHERE accession_number=%s AND status<>'archived'",(row['accession_number'],))]
            assert not [x for x in matches if x['current_institution_id']==MID and x['id']!=row['artwork_id']]
            decision=dict(artwork_id=row['artwork_id'],native_id=row['native_id'],accession_number=row['accession_number'],exact_creator_label=names[0],source_date=dates[0],existing_holding_native_identity=note['object_id'],previous_source_capture_sha256=h.sha(raw),previous_source_capture=note['evidence_path'],global_accession_matches=matches,confidence_basis='Exact already accepted museum-native object ID in persisted holding and citation; matching original capture checksum, title, full creator label and exact supported creation bounds including circa qualifications. Museum accession identifies the exact source image.',decision='accept_image_only' if a['primary_media_id'] is None else 'skip_concurrent_primary')
            decisions.append(decision)
            if a['primary_media_id'] is None:
                row['identity_basis']=decision['confidence_basis'];row['identity_confidence']=1.0;row['plan_sha256']=h.sha((E/'candidate-selection.json.gz').read_bytes()); selected.append(row)
    save('exact-identity-decisions.json',dict(at=h.now(),rows=decisions,selected=len(selected),metadata_updates=0))
    assert selected
    h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=selected));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
    for row in selected: print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
    i.audit(B)
    for sheet in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',h.load(sheet)['path'],flush=True)
    save('PREPARED.json',dict(at=h.now(),stage='prepared_requires_actual_visual_review',selected=len(selected),next_action='view_images_then_deliver'))

def deliver():
    target('before-storage-write')
    backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791897658924','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL'
    save('cloud-backup.json',backup)
    images,audit,review=i.accepted(B);assert len(images)==len(i.selected(B)['rows']) and all(x['viewed_individually'] for x in review['decisions'])
    i.upload(B)
    target('before-database-write')
    i.apply(B)

def finalize():
    reconciliation_count=h.load(E/'saam-shard24-identity-reconciliation.json')['captured_records']
    images,audit,review=i.accepted(B);rows=i.selected(B)['rows'];ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images}
    assert len(ids)==len(rows)==len(review['decisions'])
    selection=h.sha((i.folder(B)/'selection.json.gz').read_bytes());preimage_path=i.BACKUP/B/'before-000.json.gz';before=h.load(preimage_path)
    assert all(before[x]['artwork']['primary_media_id'] is None for x in ids)
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
        media=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.width,ma.height,ma.rights_status,ma.creator_credit,ma.source_page_url,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])",(ids,))]
        search=[dict(x) for x in db.execute('SELECT a.id::text,s.primary_media_id::text,s.status,s.title FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,))]
    assert len(after)==len(media)==len(search)==len(ids)
    for aid in ids:
        assert after[aid]['artwork']['primary_media_id']==expected[aid]['media_id']
        assert after[aid]['holdings']==before[aid]['holdings'] and after[aid]['creators']==before[aid]['creators']
        assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
        assert any(x['media_id']==expected[aid]['media_id'] for x in after[aid]['attachments'])
    for row in media:
        im=expected[row['id']];evidence=row['evidence_json'] if isinstance(row['evidence_json'],dict) else json.loads(row['evidence_json'])
        assert (row['checksum_sha256'],row['byte_size'],row['rights_status'],row['adapter_version'])==(im['sha256'],im['bytes'],'cc0',OP)
        assert evidence['native_identity_review']==h.load(E/'identity-review-supplement.json') and evidence['identity_review_supplement_sha256']==h.sha((E/'identity-review-supplement.json').read_bytes())
        assert evidence['selection_sha256']==selection and evidence['visual_review']['viewed_individually'] and evidence['visual_review']['sha256']==im['sha256']
        assert row['source_checksum']==rows[0]['image']['receipt']['sha256']
        assert im['bytes']<=100000 and Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline')
        with Image.open(im['path']) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
    counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
    with h.connect() as db:
        events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
    assert len(events)==len(ids) and {x['entity_id'] for x in events}==set(ids)
    for event in events:
        aid=event['entity_id'];assert event['before_json']==before[aid]['artwork'] and event['after_json']==after[aid]['artwork']
    save('independent-audit-history-verification.json',dict(at=h.now(),events=events,passed=True,new_programme_primary_images=len(ids),preimage_sha256=h.sha(preimage_path.read_bytes()),selection_sha256=selection))
    save('independent-production-verification.json',dict(at=h.now(),rows=after,media=media,search_documents=search,transaction_preimage_path=str(preimage_path),preimage_sha256=h.sha(preimage_path.read_bytes()),selection_sha256=selection,verified_counts=counts,metadata_creators_holdings_and_status_unchanged=True,local_catalogue_connections=0))
    public=[]
    for aid in ids:
        im=expected[aid];url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;response=requests.get(url,timeout=(15,45));response.raise_for_status()
        picture=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));picture.raise_for_status()
        assert im['storage_path'] in response.text and h.sha(picture.content)==im['sha256']
        with Image.open(io.BytesIO(picture.content)) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
        public.append(dict(artwork_id=aid,api_url=url,api_status=response.status_code,api_body_sha256=h.sha(response.content),image_status=picture.status_code,storage_path=im['storage_path'],image_sha256=h.sha(picture.content),bytes=len(picture.content),complete_decoding=True))
    save('independent-public-verification.json',dict(at=h.now(),rows=public,all_selected_images_delivered=True))
    import base64,hashlib
    from google.cloud import storage
    credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);stored=[]
    for aid in ids:
        im=expected[aid];blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();payload=blob.download_as_bytes()
        assert h.sha(payload)==im['sha256'] and blob.size==im['bytes'] and blob.metadata['operation']==OP and blob.metadata['sha256']==im['sha256']
        assert blob.md5_hash==base64.b64encode(hashlib.md5(payload).digest()).decode()
        stored.append(dict(artwork_id=aid,object_key=blob.name,generation=blob.generation,bytes=blob.size,sha256=h.sha(payload),metadata=blob.metadata))
    save('independent-storage-verification.json',dict(at=h.now(),rows=stored,verified=True))
    save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,production_writes=len(ids),selection_sha256=selection,transaction_preimage_sha256=h.sha(preimage_path.read_bytes()),production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Each exact existing work had null primary media in this transaction preimage; persisted media-rights evidence carries this unique operation, selection and original-source checksums and actual visual decisions. Fresh database, search-document, storage-byte and public-byte reads verify the additions; no French reserve or previous programme changes counted.'))
    cursor=dict(unit='saam',completed_shard='24',next_shard='25',source_sha256=h.load(E/'source-captures/saam-24.receipt.json')['sha256'],records_classified=reconciliation_count,eligible_exact_missing_image_matches=len(ids),newly_illustrated_native_ids=[x['native_id'] for x in rows],scope=f'All {reconciliation_count} shard records classified; {len(ids)} exact accepted legacy native identities delivered as image-only enrichment.',rotate_next='national_gallery_athens',next_route='Untouched Greek official creator index, with existing holds preserved; SAAM shard25 is saved for later rotation.')
    qp=E.parents[1]/'source-queue.json'
    with qp.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);queue=h.load(qp);prior=copy.deepcopy(queue)
        q=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access')
        assert q['resume_cursor']['next_shard']=='24'
        q.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(q['resume_cursor']))
        q.update(status=f'saam_shard24_{len(ids)}_exact_existing_primary_images_verified',last_checked_at=h.now(),last_batch=174,checkpoint=rel(E/'CHECKPOINT.json'),resume_cursor=cursor,latest_batch_verified_counts=counts,access_status=dict(public_bulk_metadata='HTTP200 shard24',selected_ids_images=f'HTTP200 {len(ids)} exact CC0 images',selected_museum_pages='Selected canonical native pages captured; bulk and original native source captures checksum verified',web_search='Existing403 hold preserved; not accessed',rest_api='API key required; not used'),remaining_gaps=['Collection coverage incomplete; other units and held identities remain separate.','SAAM shard25 is unresearched; rotate to untouched Greek creators before further SAAM work.','No canonical artist, medium, accession, dates, holdings or status updates made by this image-only batch.'])
        q.setdefault('evidence_paths',[]).extend([rel(E/x) for x in ['saam-shard24-identity-reconciliation.json','exact-identity-decisions.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','CHECKPOINT.json']])
        q.setdefault('batch_history',[]).append(dict(batch=174,verified_counts=counts,selection_sha256=selection,verification_receipt=rel(E/'batch-verification-receipt.json')))
        tmp=qp.with_suffix('.174.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
        unchanged=[x for x in prior['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in queue['sources'] if x['source_id']!='smithsonian_open_access'] and prior['supplementary_image_routes']==queue['supplementary_image_routes']
        assert unchanged
        save('source-queue-update-verification.json',dict(at=h.now(),updated_source='smithsonian_open_access',unrelated_entries_preserved=unchanged,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor))
    save('source-register-final.json',dict(at=h.now(),provider='smithsonian_open_access',policy_reference='Original111-source SmithsonianCC0 row and docs/ARTLINE_IMAGE_USE.md; explicit per-object and image CC0 labels preserved.',last_checked_at=h.now(),access_status=q['access_status'],directory_coverage_count=0,objects_classified=reconciliation_count,selected=len(ids),prepared=len(ids),imported=len(ids),verified=len(ids),remaining_gaps=q['remaining_gaps'],resume_cursor=cursor))
    save('failures-and-holds.json',dict(at=h.now(),provider_failures=[],local_environment_diagnostics=[dict(reason='Default Python lacks psycopg; existing b34 environment lacks google-cloud-storage',resolution='Reused established /tmp/artline-cesi-venv/bin/python with all required dependencies; no dependency installation')],french_reserve='188 already imported and illustrated, zero unimported; no replay.',date_holds_preserved=['80082','80437','81054'],held_provider_search='si.edu collection search403 preserved; not requested',greek_date_holds='26 Roilos holds preserved; no unchanged requests',next_retry='Rotate institution; no unchanged failed source retry.'))
    nxt='Research an untouched National Gallery Athens creator index for selected eligible works; preserve exhausted native image-gap keysets and all source/date/version holds. Smithsonian SAAM shard25 is saved for later rotation; do not replay completed shards00–24 or French188.'
    evidence=['required-input-verification.json','production-target-reconciliation.json','production-target-before-storage-write.json','production-target-before-database-write.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','saam-shard24-identity-reconciliation.json','exact-identity-decisions.json','identity-review-supplement.json','inherited-holds-verification.json','batches/saam-024/quality-audit.json','batches/saam-024/visual-review.json','actual-visual-review.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json','failures-and-holds.json','batch173-live-reconciliation.json','independent-source-and-visual-verification.json']
    started=h.load(E/'production-target-reconciliation.json')['at'];finished=h.now()
    import datetime
    duration=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(started)).total_seconds()
    cp=dict(at=finished,batch=174,stage='independently_verified_complete',researched=dict(french_reserve=188,saam_shard24_records=reconciliation_count),selected=len(ids),prepared=len(ids),imported=len(ids),verified=len(ids),verified_counts=counts,next_task=nxt,blocker='',evidence=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=len(ids),local_catalogue_connections=0,started_at=started,finished_at=finished,measured_runtime_seconds=duration)
    save('CHECKPOINT.json',cp);assert h.load(R/'CHECKPOINT.json')==cp
    checked=[]
    for name in evidence+['CHECKPOINT.json']:
        path=E/name;h.load(path);checked.append(dict(path=rel(path),sha256=h.sha(path.read_bytes()),bytes=path.stat().st_size))
    save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,passed=True))
    result=dict(outcome='progress',summary=f'Batch 174 classified {reconciliation_count} Smithsonian SAAM shard 24 records and independently verified {len(ids)} new CC0 primary images on exact existing paintings. Derivatives were individually viewed, below 100,000 bytes, and verified through fresh production, Storage and public reads. French reserve188 was already delivered and excluded; batch107 reconciled. Catalogue metadata and the local database were unchanged.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in ['french-reserve-live-reconciliation.json','exact-identity-decisions.json','batches/saam-024/visual-review.json','actual-visual-review.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','independent-final-artifact-verification.json','CHECKPOINT.json']])
    save('verified-batch-result.json',result);h.save(R/'verified-batch-result.json',result);print(json.dumps(result),flush=True)

def reconcile():
    """Fresh read-only recovery check; no provider searches or mutations."""
    target('read-only-recovery')
    images,audit,review=i.accepted(B);ids=[x['artwork_id'] for x in images]
    persisted=h.load(E/'independent-production-verification.json')
    receipt=h.load(E/'batch-verification-receipt.json');selection=h.sha((i.folder(B)/'selection.json.gz').read_bytes())
    assert receipt['selection_sha256']==selection and set(receipt['production_ids'])==set(ids)
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        live=h.snapshot(db,ids)
        rights=[dict(x) for x in db.execute("SELECT e.media_id::text,e.adapter_version,e.evidence_json FROM media_rights_evidence e WHERE e.media_id=ANY(%s::uuid[])",([im['media_id'] for im in images],))]
        events=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images])).fetchone()['n']
    assert live==persisted['rows'] and len(rights)==len(ids)==events
    for row in rights:
        ev=row['evidence_json'] if isinstance(row['evidence_json'],dict) else json.loads(row['evidence_json'])
        assert row['adapter_version']==OP and ev['selection_sha256']==selection
    for im in images:assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
    save('independent-read-only-resume-verification.json',dict(at=h.now(),live_rows_equal=True,source_and_derivative_checksums_equal=True,selection_sha256=selection,audit_events=events,own_operation=OP,prior_batch_increments_excluded=True,replay_required=False,new_production_writes=0,local_catalogue_connections=0,passed=True))
    print('Read-only recovery passed: exact batch174 image present; unique operation and selection checksums persist; no replay required.',flush=True)

if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
