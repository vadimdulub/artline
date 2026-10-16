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
E = ROOT / 'docs/research/continuous-production-20261011/batches/000274'
R = Path.home() / 'Library/Application Support/Artline/continuous-research/batches/000274'
DATA = Path.home() / 'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000274'
OP = 'continuous-smithsonian-20261014-b000274-images'
B = 'saam-044'
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
    assert q['resume_cursor']['next_shard'] in ('43','44')
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
    assert (E/'production-target-reconciliation.json').exists() and (E/'batch107-live-reconciliation.json').exists()
    url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/44.txt'; path=DATA/'saam-44.txt'; rp=E/'source-captures/saam-44.receipt.json'
    if rp.exists():
        rc=h.load(rp)
        raw=path.read_bytes() if path.exists() else gzip.decompress(Path(rc['body_path']).read_bytes())
        assert h.sha(raw)==rc['sha256']
    else:
        response=requests.get(url,timeout=(15,45));response.raise_for_status();raw=response.content;assert response.status_code==200 and len(raw)<12000000
        path.write_bytes(raw);body=E/'source-captures/saam-44.body.gz';body.write_bytes(gzip.compress(raw,mtime=0))
        rc=save('source-captures/saam-44.receipt.json',dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=rel(body),retry_after=response.headers.get('Retry-After')))
    all_objects=[json.loads(x) for x in raw.splitlines()];objects=all_objects[50:];classified=[];selected=[]
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
    save('saam-shard44-identity-reconciliation.json',dict(at=h.now(),captured_records=len(objects),total_shard_records=len(all_objects),starting_offset=50,candidate_count=len(selected),rows=classified,decisions=dict(collections.Counter(x['decision'] for x in classified)),source_sha256=rc['sha256'],production_writes=0))
    save('candidate-selection.json.gz',dict(provider='saam',batch=B,rows=selected))
    print('CLASSIFIED',len(objects),'CANDIDATES',len(selected),[(x['native_id'],x['title']) for x in selected],flush=True)

def prepare():
    candidates=h.load(E/'candidate-selection.json.gz')['rows']; reconciliation=h.load(E/'saam-shard44-identity-reconciliation.json'); selected=[]; decisions=[]
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
            assert [x['content'] for x in ft['objectType']] in [['Painting'],['Watercolor']]
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
    backups=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=20','--format=json'],text=True))
    backup=next(x for x in backups if x['status']=='SUCCESSFUL');assert backup['status']=='SUCCESSFUL'
    save('cloud-backup.json',backup)
    images,audit,review=i.accepted(B);assert len(images)==len(i.selected(B)['rows']) and all(x['viewed_individually'] for x in review['decisions'])
    i.upload(B)
    target('before-database-write')
    i.apply(B)

# A bounded second window follows the exhausted sixteen-record shard44 tail.
import inspect
more=inspect.getsource(discover).replace('def discover():','def discover45():').replace('saam-44','saam-45').replace('/44.txt','/45.txt').replace('shard44','shard45').replace('all_objects[50:]','all_objects[:50]').replace('starting_offset=50','starting_offset=0').replace('candidate-selection.json.gz','candidate-selection-shard45.json.gz')
exec(compile(more,__file__,'exec'),globals())

if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
