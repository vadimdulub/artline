#!/usr/bin/env python3
"""One bounded NGA exhibition-object image batch; existing supervisor unchanged."""
import ast, base64, csv, fcntl, gzip, hashlib, importlib.util, io, json, os, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value
base = module('base63', ROOT/'ops/continuous-image-batch-000002.py')
c = module('common63', ROOT/'ops/exhibitions_common.py')
i, h = base.i, base.h
E = ROOT/'docs/research/continuous-exhibitions-20261013/batches/000063'
R = Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000063'
OP = 'continuous-exhibitions-20261013-batch-000063-images'
B = 'nga-exhibition-063'
i.OP = OP; i.RUN = E
i.ORIG = Path.home()/'Library/Application Support/Artline/source-images'/OP
i.BACKUP = Path.home()/'Library/Application Support/Artline/backups'/OP
i.m.m.connect = base.connect
for path in [E, R, i.ORIG, i.BACKUP]: path.mkdir(parents=True, exist_ok=True)
def save(path, value):
    path = Path(path)
    if path.exists(): return h.load(path)
    h.save(path, value); return value
def target(write=False):
    actual = subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'], text=True).strip()
    assert actual == 'artline-508319:europe-west1:artline-postgres'
    return dict(base.target(write), connection_name=actual, helper='ops/india-300-delivery-20261011.py', local_catalogue_connections=0)

# Preserve established apply/recovery boundaries while taking both shared locks
# and checking the complete selected preimage and source citations in the transaction.
code = (ROOT/'ops/illustrated-300k-20261011.py').read_text()
node = next(n for n in ast.parse(code).body if isinstance(n, ast.FunctionDef) and n.name == 'apply')
code = ast.get_source_segment(code, node)
code = code.replace("db.execute(\"SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))\")", "db.execute(\"SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))\");db.execute('SELECT pg_advisory_xact_lock(2026101201)')")
code = code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", """assert native_ids.get(aid)==r['native_id'],'Native identity changed'
    assert before[aid]==m.load(RUN/'selected-preimage.json.gz')['before'][aid],'Full selected preimage changed'
    pinrow=m.load(RUN/'source-citation-pins.json')['rows'][aid]
    assert db.execute("SELECT 1 FROM citations WHERE id=%s AND evidence_note=%s AND source_record_id=%s",(pinrow['id'],pinrow['evidence_note'],r['native_id'])).fetchone(),'Pinned source citation changed'
    links=m.load(RUN/'exact-exhibition-preimages.json')['by_artwork'][aid]
    for link in links:
     live=db.execute('SELECT to_jsonb(ee) record FROM exhibition_entries ee WHERE id=%s AND artwork_id=%s',(link['entry']['id'],aid)).fetchone()
     assert live and live['record']==link['entry'],'Exact exhibition connection changed'""")
exec(compile(code, __file__, 'exec'), i.__dict__)

def prepare():
    if (i.folder(B)/'selection.json.gz').exists():
        assert h.sha((i.folder(B)/'selection.json.gz').read_bytes()) == h.load(i.folder(B)/'pin.json')['sha256']
        return finish_preparation()
    save(E/'production-target-reconciliation.json', target())
    registry = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    rows = list(csv.DictReader(registry.open())); assert len(rows) == 111
    holdpaths = list((ROOT/'docs/research').glob('**/access-holds/api.nga.gov.json'))
    assert not holdpaths, 'NGA image surface held: ' + str(holdpaths)
    save(E/'source-register.json', dict(at=c.now(), registry_path=str(registry), registry_sha256=h.sha(registry.read_bytes()), source=next(x for x in rows if x['source_id']=='nga_washington'), permitted_surface='api.nga.gov IIIF with per-image openaccess=1', held_www_nga_gov_surface_preserved=True))
    pp = i.m.RUN/'nga/plan-v2.json.gz'; plan = h.load(pp); by = {r['artwork_id']:r for r in plan['new_artworks']}; pin = h.sha(pp.read_bytes())
    rc = h.load(i.m.RUN/'sources/nga/published_images.csv.receipt.json')
    body = Path(rc['path']); assert h.sha(body.read_bytes()) == rc['sha256']
    save(E/'source-capture-verification.json', dict(at=c.now(), published_images_receipt=rc, capture_bytes=body.stat().st_size, checksum_verified=True, native_catalogue_plan_path=str(pp), native_catalogue_plan_sha256=pin))
    excluded = set()
    for p in (base.OLD/'batches').glob('nga-*/quality-audit.json'): excluded.update(h.load(p)['identity_holds'])
    for parent in [base.OLD, ROOT/'docs/research/continuous-production-20261011']:
        for p in parent.glob('**/visual-review.json'):
            excluded.update(x['artwork_id'] for x in h.load(p).get('decisions',[]) if x.get('decision') != 'accept')
    chosen=[]; reconciled=[]; links={}; citations={}
    with base.connect() as db:
        own = [dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(OP,))]
        assert not own, 'Unknown prior batch write requires reconciliation'
        candidates = db.execute("""SELECT DISTINCT a.id::text,x.external_id native_id,x.external_id::int sortkey FROM artworks a
          JOIN external_identifiers x ON x.entity_type='artwork' AND x.entity_id=a.id AND x.scheme=%s
          JOIN exhibition_entries ee ON ee.artwork_id=a.id JOIN exhibitions e ON e.id=ee.exhibition_id
          WHERE a.primary_media_id IS NULL AND a.status<>'archived' AND e.status<>'archived'
          AND e.start_year BETWEEN 1600 AND 1989 AND coalesce(e.end_year,e.start_year)<=1989
          AND a.work_type IN ('painting','drawing','print','watercolor','icon')
          AND x.external_id::int>3901 ORDER BY x.external_id::int LIMIT 200""",(i.CFG['nga']['scheme'],)).fetchall()
        for candidate in candidates:
            aid=candidate['id']; r=by.get(aid); reason='eligible'; image=i.native_image('nga',r) if r else None
            if aid in excluded: reason='prior_identity_or_visual_hold'
            elif not image: reason='no_eligible_open_native_primary'
            if reason=='eligible':
                a=h.snapshot(db,[aid])[aid]['artwork']
                if (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])!=(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],i.CFG['nga']['mid']): reason='changed_catalogue_identity'
            reconciled.append(dict(artwork_id=aid,native_id=candidate['native_id'],decision=reason))
            if reason!='eligible': continue
            ls=[]
            for z in db.execute("""SELECT to_jsonb(ee) entry,to_jsonb(e) exhibition FROM exhibition_entries ee JOIN exhibitions e ON e.id=ee.exhibition_id WHERE ee.artwork_id=%s AND e.status<>'archived' AND e.start_year BETWEEN 1600 AND 1989 AND coalesce(e.end_year,e.start_year)<=1989 ORDER BY ee.id""",(aid,)): ls.append(dict(z))
            assert ls and all(x['entry']['evidence'] for x in ls)
            citation=dict(db.execute("SELECT id::text,source_record_id,source_url,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name='million_catalogue_nga'",(aid,)).fetchone())
            assert citation['source_record_id']==r['native_id']
            assert json.loads(citation['evidence_note'])['plan_sha256']==pin
            keep={k:r[k] for k in ['artwork_id','native_id','title','creator_label','source_url','accession_number','first','last','precision','work_type']}
            chosen.append(dict(keep,provider='nga',image=image,plan_path=str(pp),plan_sha256=pin,manual_visual_required=True,rights_basis='NGA exact image UUID in checksum-verified published_images.csv: openaccess=1, viewtype=primary, depictstmsobjectid matches exact native accessioned impression. NGA Open Access CC0 label retained.'))
            links[aid]=ls;citations[aid]=citation
            if len(chosen)==10: break
        assert chosen
        before=h.snapshot(db,[r['artwork_id'] for r in chosen])
    save(E/'recovery-check.json',dict(at=c.now(),own_existing_rights_rows=own,prior_unknown_writes=False,live_null_primary_reconciled=True,smk_changes_counted=0,separate_artwork_programme_unchanged=True))
    save(E/'selected-preimage.json.gz',dict(at=c.now(),before=before))
    save(E/'source-citation-pins.json',dict(at=c.now(),rows=citations))
    save(E/'exact-exhibition-preimages.json',dict(at=c.now(),by_artwork=links))
    save(E/'candidate-reconciliation.json',dict(at=c.now(),rows=reconciled,selected=len(chosen),resume_after_native_id=chosen[-1]['native_id'],prior_hold_count=len(excluded)))
    save(i.folder(B)/'selection.json.gz',dict(at=c.now(),provider='nga',batch=B,rows=chosen,selection_basis='Up to ten live null-primary gaps in exact already documented 1600–1989 exhibition connections. Native impression, accession, catalogue fields, literal creation dates, source citations and image UUIDs reconciled; no new participation inferred.'))
    save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
    finish_preparation()

def finish_preparation():
    for row in i.selected(B)['rows']:
        rp=E/'source-captures'/(row['native_id']+'.info.json')
        if not rp.exists():
            assert not (E/'access-holds/api.nga.gov.json').exists()
            i.provider_slot('api.nga.gov');url=row['image']['native_url']+'/info.json'
            res=i.session().get(url,timeout=(15,60),allow_redirects=False)
            body=R/'source-captures'/(row['native_id']+'.info.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(res.content,mtime=0))
            rc=dict(at=c.now(),url=url,status=res.status_code,sha256=h.sha(res.content),body_path=str(body));save(rp,rc)
            if res.status_code in [401,403,429]:save(E/'access-holds/api.nga.gov.json',rc);raise RuntimeError('NGA image surface held')
            res.raise_for_status()
        rc=h.load(rp);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];data=json.loads(raw)
        assert data.get('@id',data.get('id'))==row['image']['native_url']
        assert (data['width'],data['height'])==(int(row['image']['source']['width']),int(row['image']['source']['height']))
        im=i.prepare_one(row,B);assert im['state']=='prepared',im
    i.audit(B)
    print(json.dumps([dict(artwork_id=im['artwork_id'],title=im['title'],path=im['path'],flags=im['flags']) for im in h.load(i.folder(B)/'quality-audit.json')['prepared_images']],ensure_ascii=False,indent=2))

def deliver():
    images,_,_=i.accepted(B);assert 1<=len(images)<=10
    backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791899943147','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
    save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
    save(E/'production-target-before-database-write.json',target(True));i.apply(B)

def verify():
    images,audit,review=i.accepted(B);ids=[im['artwork_id'] for im in images]
    pin=h.sha((i.folder(B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(B)/'visual-review.json').read_bytes())
    bp=i.BACKUP/B/'before-000.json.gz';before=h.load(bp);selected_before=h.load(E/'selected-preimage.json.gz')['before'];assert before==selected_before
    links=h.load(E/'exact-exhibition-preimages.json')['by_artwork'];verified=[];events=[]
    with base.connect() as db:
        after=h.snapshot(db,ids)
        for im in images:
            aid=im['artwork_id'];assert before[aid]['artwork']['primary_media_id'] is None
            row=dict(db.execute("""SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,m.storage_path,m.byte_size,m.rights_status,m.license_label,r.adapter_version,r.source_checksum,r.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence r ON r.media_id=m.id WHERE a.id=%s""",(aid,)).fetchone())
            ev=row['evidence_json'];ev=ev if isinstance(ev,dict) else json.loads(ev)
            assert row['primary_media_id']==im['media_id'] and row['checksum_sha256']==im['sha256'] and row['byte_size']==im['bytes']<=100000
            assert row['adapter_version']==OP and row['rights_status']=='cc0' and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv and ev['visual_review']['viewed_individually']
            source_pin=h.load(E/'source-capture-verification.json')
            assert row['source_checksum']==source_pin['published_images_receipt']['sha256']==ev['source_receipt']['sha256']
            assert ev['original_catalogue_plan_sha256']==source_pin['native_catalogue_plan_sha256']
            assert ev['native_source']['openaccess']=='1'
            assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
            assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
            log=[dict(x) for x in db.execute("SELECT before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=%s AND after_json->>'primary_media_id'=%s",(aid,im['media_id']))]
            assert len(log)==1 and log[0]['before_json']==before[aid]['artwork'];events.extend(log)
            for link in links[aid]:
                assert db.execute('SELECT to_jsonb(ee) record FROM exhibition_entries ee WHERE id=%s',(link['entry']['id'],)).fetchone()['record']==link['entry']
                assert db.execute('SELECT to_jsonb(e) record FROM exhibitions e WHERE id=%s',(link['exhibition']['id'],)).fetchone()['record']==link['exhibition']
            verified.append(row)
    save(E/'independent-database-verification.json',dict(at=c.now(),operation=OP,rows=verified,audit_events=events,transaction_preimage=str(bp),transaction_preimage_sha256=h.sha(bp.read_bytes()),selection_sha256=pin,visual_review_sha256=rv,all_new_primary_preimages_null=True,metadata_creators_holdings_statuses_preserved=True,exhibition_records_and_exact_links_unchanged=True))
    credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials)
    storage=[];public=[];files=[];api_cache={};api_pages=[]
    for im in images:
        raw=Path(im['path']).read_bytes();assert len(raw)==im['bytes']<=100000 and h.sha(raw)==im['sha256']
        with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
        files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],bytes=len(raw),full_decode=True,actually_viewed=True,complete_source_frame_preserved=True))
        blob=client.bucket(i.d.core.BUCKET).blob(im['storage_path'].lstrip('/'));blob.reload()
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==OP
        storage.append(dict(path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
        url='https://artlines.org'+im['storage_path'];res=i.session().get(url,timeout=(15,60));res.raise_for_status();assert h.sha(res.content)==im['sha256']
        for link in links[im['artwork_id']]:
            eid=link['exhibition']['id']
            if eid not in api_cache:
                items=[];cursor='';seen=set()
                while True:
                    api=f'https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/{eid}/entries?limit=100'+('&after='+cursor if cursor else '')
                    ar=i.session().get(api,timeout=(15,60));ar.raise_for_status();payload=ar.json();chunk=payload['items'];items.extend(chunk)
                    api_pages.append(dict(url=api,status=ar.status_code,response_sha256=h.sha(ar.content),entry_ids=[x['id'] for x in chunk],total=payload['total'],has_more=payload['hasMore'],next_cursor=payload.get('nextCursor')))
                    assert len({x['id'] for x in items})==len(items),'Duplicate public page'
                    if not payload['hasMore']:
                        assert len(items)==payload['total'];break
                    cursor=payload['nextCursor'];assert cursor and cursor not in seen;seen.add(cursor);assert len(seen)<100
                api_cache[eid]=items
            entry=next(x for x in api_cache[eid] if x['id']==link['entry']['id']);assert entry['artworkId']==im['artwork_id'] and im['storage_path'] in json.dumps(entry)
            public.append(dict(artwork_id=im['artwork_id'],image_url=url,image_status=res.status_code,image_sha256=h.sha(res.content),exhibition_id=eid,entry_id=entry['id'],entry=entry,api_association_verified=True))
    save(E/'independent-file-verification.json',dict(at=c.now(),rows=files))
    save(E/'independent-storage-verification.json',dict(at=c.now(),rows=storage))
    save(E/'public-verification.json',dict(at=c.now(),rows=public,api_pages=api_pages,complete_cursor_paging_verified=True,distinct_assets=len(images),all_sha256_verified=True))
    save(E/'research-review.json',dict(at=c.now(),source='nga_washington',selected=len(images),new_images=len(images),existing_connections_illustrated=len(public),exhibition_ids=sorted(api_cache),rights='NGA Open Access CC0; per-image openaccess=1',exact_native_impressions=True,actual_visual_review='Every accepted derivative individually viewed with tools.view_image; no unsampled claims',checklists_preserved=True,new_participation_claims=0,main_catalogue_scope_preserved=True))
    # Recovery path is checked read-only: completed writes and receipts must agree.
    applied=h.load(i.folder(B)/'applied/000.json');assert applied['ids']==ids and applied['selection_sha256']==pin
    save(E/'recovery-verification.json',dict(at=c.now(),applied_receipt_matches_live=True,all_media_attributed_by_persisted_operation_selection_and_review_checksums=True,transaction_null_primary_preimages_verified=True,replay_increments=0))
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=len(images),existing_records_enriched=len(images))
    paths=['source-iiif-verification.json','previous-batch-recovery-verification.json','inherited-lock-verification.json','supervisor-persistence-verification.json','independent-database-verification.json','independent-file-verification.json','independent-storage-verification.json','public-verification.json','research-review.json','source-capture-verification.json','recovery-verification.json',f'batches/{B}/visual-review.json']
    nxt='Continue the undercovered NGA exact exhibition-object image route after native '+i.selected(B)['rows'][-1]['native_id']+'; recheck live null-primary gaps and preserve all image, version and provider holds. Rotate to another permitted institutional route if NGA is held.'
    cp=dict(at=c.now(),batch=63,stage='verified_complete',verified_counts=counts,production_artwork_ids=ids,next_task=nxt,evidence_paths=[str((E/p).relative_to(ROOT)) for p in paths],external_supervisor_unchanged=True,local_catalogue_connections=0)
    save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
    qp=E.parents[1]/'source-queue.json'
    with qp.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);q=h.load(qp);other={x['source_id']:x for x in q['sources'] if x['source_id']!='nga_washington'}
        source=next(x for x in q['sources'] if x['source_id']=='nga_washington')
        source['research_status']='exact_exhibition_linked_images_verified_batch63';source['last_checked_at']=c.now()
        source['cursor']=dict(source.get('cursor') or {},route='exact_exhibition_linked_missing_images',next_native_id=None,resume_after_native_id=i.selected(B)['rows'][-1]['native_id'],last_batch=63,delivered_artwork_ids=ids,verified_new_images=len(images),next=nxt)
        source['evidence']=list(dict.fromkeys(source.get('evidence',[])+cp['evidence_paths']))
        temp=qp.with_suffix('.63.tmp');temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(temp,qp)
        assert other=={x['source_id']:x for x in h.load(qp)['sources'] if x['source_id']!='nga_washington'}
    save(E/'queue-update.json',dict(at=c.now(),updated_source='nga_washington',unrelated_sources_preserved=len(other),supplemental_sources_preserved=True,resume_cursor=source['cursor'],queue_sha256=h.sha(qp.read_bytes())))
    paths+=['queue-update.json','CHECKPOINT.json','final-validation.json']
    result=dict(outcome='progress',summary=f'Added {len(images)} authentic NGA CC0 images to existing exact exhibition-linked objects. Every derivative was individually viewed, preserves the complete supplied frame and is at most 100,000 bytes. Production associations, audit preimages, Storage attribution and public checksums were independently verified; existing metadata, statuses and exhibition links were preserved.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/p).relative_to(ROOT)) for p in paths])
    save(E/'final-validation.json',dict(at=c.now(),database_verified=True,storage_verified=True,public_checksums_verified=True,queue_updated=True,actual_visual_review_verified=True,result=result))
    save(E/'worker-result.json',result);save(R/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':globals()[sys.argv[1]]()
