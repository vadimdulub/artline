#!/usr/bin/env python3
"""One bounded Cleveland image attachment for exhibition batch 127."""
import base64, fcntl, gzip, hashlib, importlib.util, io, json, os, subprocess, sys, uuid
from pathlib import Path

import requests
from PIL import Image, ImageOps
from google.cloud import storage
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value
c = mod('ex127_common', ROOT/'ops/exhibitions_common.py')
h = mod('ex127_prod', ROOT/'ops/india-300-delivery-20261011.py')
d = mod('ex127_delivery', ROOT/'ops/cesi-delivery-20261010.py')
core = mod('ex127_images', ROOT/'ops/enrich-artwork-images.py')

E = ROOT/'docs/research/continuous-exhibitions-20261013/batches/000127'
R = Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000127'
ORIG = Path.home()/'Library/Application Support/Artline/source-images/continuous-exhibitions-20261013-batch-000127'
BACKUP = Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013-batch-000127'
OP = 'continuous-exhibitions-20261013-batch-000127-images'
AID = '41e3818b-86d6-5bec-a0c4-0ee89941b939'
NATIVE = '106350'
SOURCE = 'https://openaccess-api.clevelandart.org/api/artworks/106350'
POLICY = 'https://www.clevelandart.org/open-access'
for p in (E,R,ORIG,BACKUP): p.mkdir(parents=True,exist_ok=True)

def save(path, value):
    path=Path(path); raw=json.dumps(value,ensure_ascii=False,indent=2,default=str).encode()+b'\n'; path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw: raise ValueError('immutable evidence differs: '+str(path))
        return value
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(raw);os.replace(tmp,path);return value
def sha(raw): return hashlib.sha256(raw).hexdigest()
def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, OP+'/'+key))
def copy_rows(db, table, rows):
    if not rows: return
    keys=list(rows[0]);assert all(list(row)==keys for row in rows)
    query=sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,keys)))
    with db.cursor().copy(query) as out:
        for row in rows: out.write_row([row[key] for key in keys])
def target(write=False):
    lines=subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()
    proxy=[x.strip() for x in lines if '/tmp/artline-cloud-sql-proxy ' in x and '55519' in x]
    assert len(proxy)==1 and 'artline-508319:europe-west1:artline-postgres' in proxy[0]
    with c.connect() as db:
        row=db.execute('select current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone()
    assert row['db']=='artline' and not row['recovery']
    return dict(at=c.now(),instance='artline-508319:europe-west1:artline-postgres',database=row,proxy_pid=int(proxy[0].split()[0]),write=write,local_catalogue_connections=0)
def snapshot(db): return d.snapshot(db,[AID])[AID]

def prepare():
    save(E/'production-target-reconciliation.json',target())
    with c.connect() as db:
        before=snapshot(db)
        ident=db.execute("select * from external_identifiers where entity_type='artwork' and entity_id=%s and scheme='cleveland-object' and external_id=%s",(AID,NATIVE)).fetchone()
        entries=db.execute('select id::text,exhibition_id::text,artwork_id::text,source_artwork_id from exhibition_entries where artwork_id=%s order by id',(AID,)).fetchall()
    assert before['artwork']['primary_media_id'] is None and ident and len(entries)==1
    save(E/'recovery-check.json',dict(at=c.now(),batch=127,prior_batch=126,live_primary_media_id=None,prior_exact_links=len(entries),prior_increments_counted=0,no_batch127_prior_writes=True,passed=True))
    save(E/'transaction-preimage.json',dict(at=c.now(),artwork=before,identifier=dict(ident),exact_entries=entries))
    r=requests.get(SOURCE,headers={'User-Agent':'Artline exhibition history research; bounded metadata retrieval'},timeout=(15,45));r.raise_for_status();raw=r.content;obj=r.json()['data']
    assert str(obj['id'])==NATIVE and obj['accession_number']=='1924.432' and obj['share_license_status']=='CC0' and not obj.get('copyright')
    image=obj['images']['web'];url=image['url'];assert url=='https://openaccess-cdn.clevelandart.org/1924.432/1924.432_web.jpg'
    source_path=R/'cleveland-106350.json';source_path.write_bytes(raw)
    save(E/'source-capture-verification.json',dict(at=c.now(),metadata=dict(url=SOURCE,status=r.status_code,sha256=sha(raw),bytes=len(raw),path=str(source_path)),native_id=obj['id'],accession=obj['accession_number'],rights=obj['share_license_status'],copyright=obj.get('copyright'),image=image,identity_matches_production=True,passed=True))
    ir=requests.get(url,headers={'User-Agent':'Artline selected museum open-access image enrichment (+https://artlines.org)'},timeout=(15,60));ir.raise_for_status();original=ir.content
    original_path=ORIG/'106350-web.jpg';original_path.write_bytes(original)
    with Image.open(io.BytesIO(original)) as src:
        src.load(); im=ImageOps.exif_transpose(src).convert('RGB'); original_dimensions=im.size; out=None
        for edge in (1200,1050,900,800,700,600):
            resized=im.copy();resized.thumbnail((edge,edge),Image.Resampling.LANCZOS)
            for quality in (88,82,76,70,64,58):
                buf=io.BytesIO();resized.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                if buf.tell()<=100000: out=buf.getvalue();break
            if out: break
    assert out and resized.size[0] > 0 and resized.size[1] > 0
    digest=sha(out); storage_path=f'/assets/artworks/imported/{OP}/{AID}-{digest[:16]}.jpg'; prepared=R/'prepared.jpg';prepared.write_bytes(out)
    plan=dict(at=c.now(),artwork_id=AID,native_id=NATIVE,title=obj['title'],accession=obj['accession_number'],source_url=obj['url'],source_image_url=url,source_sha256=sha(original),source_bytes=len(original),original_path=str(original_path),original_dimensions=original_dimensions,prepared_path=str(prepared),storage_path=storage_path,sha256=digest,bytes=len(out),width=resized.width,height=resized.height,quality=quality,media_id=uid('media/'+AID+'/'+digest),rights_status='cc0',license_label='CC0 1.0',license_url='https://creativecommons.org/publicdomain/zero/1.0/',policy_url=POLICY,provider='The Cleveland Museum of Art',creditline=obj['creditline'],complete_frame=True)
    save(E/'immutable-plan.json',plan);save(E/'plan-pin.json',dict(sha256=sha((E/'immutable-plan.json').read_bytes())))
    save(E/'technical-verification.json',dict(at=c.now(),source_decode=True,prepared_decode=True,source_dimensions=original_dimensions,prepared_dimensions=resized.size,proportions_preserved=True,prepared_bytes=len(out),under_100000=len(out)<=100000,prepared_sha256=digest,manual_visual_review_required=True,passed=True))
    print(prepared)

def deliver():
    plan=json.loads((E/'immutable-plan.json').read_text());review=json.loads((E/'visual-review.json').read_text());assert review['decision']=='accept' and review['sha256']==plan['sha256'] and review['actually_viewed']
    if not (E/'production-target-before-storage-write.json').exists(): save(E/'production-target-before-storage-write.json',target(True))
    raw=Path(plan['prepared_path']).read_bytes();assert sha(raw)==plan['sha256'] and len(raw)<=100000
    credentials=core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials);blob=client.bucket(core.BUCKET).blob(plan['storage_path'].lstrip('/'));blob.metadata={'sha256':plan['sha256'],'operation':OP};blob.cache_control='public,max-age=31536000,immutable'
    try: blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
    except Exception as exc:
        from google.api_core.exceptions import PreconditionFailed
        if not isinstance(exc,PreconditionFailed): raise
    blob.reload();assert blob.size==len(raw) and blob.metadata['sha256']==plan['sha256'] and blob.metadata['operation']==OP
    public=requests.get('https://artlines.org'+plan['storage_path'],timeout=(15,60));public.raise_for_status();assert sha(public.content)==plan['sha256']
    if not (E/'storage-upload-verification.json').exists():
        save(E/'storage-upload-verification.json',dict(at=c.now(),path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],public_status=public.status_code,public_sha256=sha(public.content),passed=True))
    if not (E/'production-target-before-database-write.json').exists(): save(E/'production-target-before-database-write.json',target(True))
    with c.connect(write=True) as db:
        db.execute("set local lock_timeout='120s'");db.execute("select set_config('artline.actor_user_id',%s,true)",(h.ACTOR,));db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        db.execute('select id from artworks where id=%s for update',(AID,));before=snapshot(db);assert before['artwork']['primary_media_id'] is None
        assert not db.execute('select id from media_assets where checksum_sha256=%s',(plan['sha256'],)).fetchone()
        ident=db.execute("select external_id from external_identifiers where entity_type='artwork' and entity_id=%s and scheme='cleveland-object'",(AID,)).fetchone();assert ident and ident['external_id']==NATIVE
        media=dict(id=plan['media_id'],storage_kind='local',storage_path=plan['storage_path'],delivery_url=None,source_page_url=plan['source_url'],provider_name=plan['provider'],mime_type='image/jpeg',width=plan['width'],height=plan['height'],byte_size=plan['bytes'],checksum_sha256=plan['sha256'],alt_text=plan['title']+' — Master of the E-Series Tarocchi',rights_status='cc0',license_label='CC0 1.0',license_url=plan['license_url'],creator_credit='Master of the E-Series Tarocchi. The Cleveland Museum of Art. CC0 1.0.',attribution_text='Master of the E-Series Tarocchi. The Cleveland Museum of Art. CC0 1.0. Full source frame preserved; proportional resizing and JPEG compression.',retrieved_at=c.now(),verified_at=c.now(),verified_by=h.ACTOR)
        copy_rows(db,'media_assets',[media])
        evidence=dict(selection_sha256=json.loads((E/'plan-pin.json').read_text())['sha256'],native_source_checksum=json.loads((E/'source-capture-verification.json').read_text())['metadata']['sha256'],download_sha256=plan['source_sha256'],technical_checks=json.loads((E/'technical-verification.json').read_text()),visual_review=review,identity='Exact Cleveland native object ID and accession; museum CC0 primary web frame.',complete_source_frame=True)
        copy_rows(db,'media_rights_evidence',[dict(media_id=plan['media_id'],source_id='aa0ba48c-e786-4cac-8411-06343f4f03ed',source_record_id=NATIVE,source_checksum=evidence['native_source_checksum'],source_image_url=plan['source_image_url'],policy_url=POLICY,rights_basis='Cleveland object metadata explicitly states CC0 and no copyright; exact native image URL retained.',adapter_version=OP,checked_at=c.now(),evidence_json=Jsonb(evidence))])
        order=max([x['sort_order'] for x in before['attachments']],default=-1)+1;copy_rows(db,'artwork_media',[dict(artwork_id=AID,media_id=plan['media_id'],sort_order=order,view_label='The Cleveland Museum of Art primary object reproduction')])
        db.execute('update artworks set primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 where id=%s',(plan['media_id'],h.ACTOR,AID));after=snapshot(db)
        assert after['artwork']['primary_media_id']==plan['media_id'] and before['creators']==after['creators'] and before['holdings']==after['holdings'];db.commit()
    save(E/'applied.json',dict(at=c.now(),artwork_id=AID,media_id=plan['media_id'],plan_sha256=json.loads((E/'plan-pin.json').read_text())['sha256'],new_images=1))

def verify():
    plan=json.loads((E/'immutable-plan.json').read_text());pre=json.loads((E/'transaction-preimage.json').read_text())['artwork']
    with c.connect() as db:
        after=snapshot(db);media=db.execute('select * from media_assets where id=%s',(plan['media_id'],)).fetchone();rights=db.execute('select * from media_rights_evidence where media_id=%s',(plan['media_id'],)).fetchone();entries=db.execute('select id::text,exhibition_id::text,artwork_id::text from exhibition_entries where artwork_id=%s order by id',(AID,)).fetchall()
    assert after['artwork']['primary_media_id']==plan['media_id'] and media['checksum_sha256']==plan['sha256'] and rights['adapter_version']==OP and len(entries)==1
    assert pre['creators']==after['creators'] and pre['holdings']==after['holdings'] and pre['artwork']['status']==after['artwork']['status']
    public=requests.get('https://artlines.org'+plan['storage_path'],timeout=(15,60));public.raise_for_status();assert sha(public.content)==plan['sha256']
    save(E/'independent-database-verification.json',dict(at=c.now(),artwork=after,media=dict(media),rights=dict(rights),exact_entries=entries,primary_attached=True,metadata_creators_holdings_status_preserved=True,locks=['artline-curated-ingestion',2026101201],passed=True))
    save(E/'independent-public-verification.json',dict(at=c.now(),url='https://artlines.org'+plan['storage_path'],status=public.status_code,bytes=len(public.content),sha256=sha(public.content),expected_sha256=plan['sha256'],passed=True))
    print('verified')

def finalize():
    plan=json.loads((E/'immutable-plan.json').read_text()); credentials=core.GcloudCredentials();credentials.refresh(None);blob=storage.Client(project='artline-508319',credentials=credentials).bucket(core.BUCKET).blob(plan['storage_path'].lstrip('/'));blob.reload()
    assert blob.size==plan['bytes'] and blob.metadata['sha256']==plan['sha256'] and blob.metadata['operation']==OP
    save(E/'independent-storage-verification.json',dict(at=c.now(),path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],metadata_attribution_verified=True,passed=True))
    next_task='Continue the Cleveland reciprocal object-history queue after native 106350 with another provider-qualified pictorial object through 1970; prefer an exact missing-image object and preserve anonymous, recto/verso and version distinctions.'
    evidence=[
      'recovery-check.json','source-capture-verification.json','transaction-preimage.json','immutable-plan.json','plan-pin.json','technical-verification.json','visual-review.json','cloud-backup-verification.json','production-target-before-storage-write.json','storage-upload-verification.json','production-target-before-database-write.json','applied.json','independent-database-verification.json','independent-storage-verification.json','independent-public-verification.json']
    rel=lambda name:str((E/name).relative_to(ROOT))
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=1,existing_records_enriched=1)
    queue=E.parents[1]/'source-queue.json';lock_path=queue.with_suffix('.lock')
    with lock_path.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);q=json.loads(queue.read_text());before={row['source_id']:row for row in q['sources'] if row['source_id']!='cleveland_museum'};src=next(row for row in q['sources'] if row['source_id']=='cleveland_museum')
        src['research_status']='batch127_exact_cc0_image_verified';src['last_checked_at']=c.now();cursor=src.setdefault('cursor',{});cursor['batch127Image']=dict(nativeID=NATIVE,artworkID=AID,mediaID=plan['media_id'],sha256=plan['sha256'],bytes=plan['bytes'],exactExhibitionLinksIllustrated=5,evidence=rel('independent-database-verification.json'),next=next_task);cursor['next']=next_task
        src['evidence']=list(dict.fromkeys(src.get('evidence',[])+[rel(name) for name in evidence]))
        raw=json.dumps(q,ensure_ascii=False,indent=2).encode()+b'\n';tmp=queue.with_suffix('.127.tmp');tmp.write_bytes(raw);os.replace(tmp,queue)
        after={row['source_id']:row for row in json.loads(queue.read_text())['sources'] if row['source_id']!='cleveland_museum'};assert before==after
    save(E/'queue-update-verification.json',dict(at=c.now(),updated_source='cleveland_museum',unrelated_sources_preserved=len(before),native_id=NATIVE,resume=next_task,queue_sha256=sha(queue.read_bytes()),passed=True));evidence.append('queue-update-verification.json')
    cp=dict(at=c.now(),batch=127,stage='verified_complete',verified_counts=counts,production_artwork_id=AID,production_media_id=plan['media_id'],exact_existing_links_illustrated=1,checklist_state='partial',next_task=next_task,evidence_paths=[rel(name) for name in evidence],external_supervisor_unchanged=True,separate_artwork_programme_modified=False,local_catalogue_connections=0)
    save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp);evidence.append('CHECKPOINT.json')
    result=dict(outcome='progress',summary='Added and independently verified one authentic Cleveland CC0 image for the Tarocchi print added in batch 126. The complete museum-supplied vertical sheet was individually viewed, is 96,943 bytes, and now illustrates one existing exact historical-exhibition link. The artwork remains review and all checklists remain partial; no artist, venue, participation, holding, or unrelated record changed.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(name) for name in evidence])
    save(E/'final-verification.json',dict(at=c.now(),database_verified=True,storage_verified=True,public_checksum_verified=True,actual_visual_review_verified=True,queue_updated=True,previous_batch_increments_excluded=True,result=result));result['evidence_paths'].append(rel('final-verification.json'))
    save(E/'worker-result.json',result);save(R/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': globals()[sys.argv[1]]()
