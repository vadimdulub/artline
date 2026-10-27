"""Create-only delivery of 611 actually reviewed exact Rouen object views."""
import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import requests
from PIL import Image
from psycopg.types.json import Jsonb
from google.cloud import storage
import exhibitions_common as c

spec=importlib.util.spec_from_file_location('dedup_resume',Path(__file__).with_name('catalogue-deduplication-resume-20261027.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OP='rouen-reviewed-image-delivery-20261027'
E=m.E/'images'
B=Path.home()/'Library/Application Support/Artline/backups'/OP
D=m.D
PREP=D/'rouen-image-delivery-preparation.json.gz'
ROUEN='f92766ec-41cf-42d1-9bb1-f333fe5d2980'
EDITOR=m.EDITOR
WEB='https://artline-web-lpuqqlugnq-ew.a.run.app'
API='https://artline-api-lpuqqlugnq-ew.a.run.app'


def snapshot(db,ids):
    return {t:m.rows(db,t,col,ids) for t,col in {'artworks':'id','artwork_artists':'artwork_id','artwork_media':'artwork_id','artwork_location_assertions':'artwork_id'}.items()}


def checked_image(r):
    raw=Path(r['path']).read_bytes()
    assert c.sha(raw)==r['sha256'] and len(raw)==r['bytes']<=100000
    assert c.sha(Path(r['original_path']).read_bytes())==r['source_receipt']['sha256']
    assert r['visual_review']['decision']=='primary_view_approved' and r['visual_review']['image_sha256']==c.sha(raw)
    assert c.sha(Path(r['visual_review']['contact_sheet']).read_bytes())==r['visual_review']['contact_sheet_sha256']
    assert c.sha(gzip.decompress(Path(r['source_page_receipt']['body_path']).read_bytes()))==r['source_page_receipt']['sha256']
    with Image.open(r['path']) as im:
        im.load();assert im.size==(r['width'],r['height'])
    return raw


def plan():
    prep=c.load(PREP);images=prep['images'];assert len(images)==611
    selected=c.load(D/'rouen-image-selection-649.json.gz')['selected']
    identities={r['artwork_id']:r for r in selected}
    assert len({r['artwork_id'] for r in images})==len(images)
    for r in images:
        checked_image(r)
        a=identities[r['artwork_id']]
        assert a['native_id']==r['native_id'] and c.norm(r['title'])==c.norm(r['source_fields']['Titre'])
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        before=snapshot(db,[r['artwork_id'] for r in images])
        works={r['id']:r for r in before['artworks']}
        assert len(works)==611
        source=db.execute("SELECT to_jsonb(s)v FROM sources s WHERE slug='joconde-m0729'").fetchone()['v']
        # The existing source is already linked to this museum; do not duplicate it.
        native=db.execute("SELECT l.artwork_id::text,l.object_key FROM research_artwork_links l WHERE l.artwork_id=ANY(%s::uuid[])", (list(works),)).fetchall()
        native_pairs={(r['artwork_id'],r['object_key']) for r in native}
        ex=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(works),)).fetchall()
        external_pairs={(r['entity_id'],r['external_id']) for r in ex}
        citation_rows=db.execute("SELECT id::text,entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(works),)).fetchall()
        citation_pairs={(r['entity_id'],r['source_record_id'],r['source_url']) for r in citation_rows}
        for im in images:
            w=works[im['artwork_id']]
            assert w['status']!='archived' and w['primary_media_id'] is None and w['current_institution_id']==ROUEN
            assert c.norm(w['title'])==c.norm(im['title'])
            if w['accession_number']:assert c.norm(w['accession_number'])==c.norm(im['source_fields']["Numéro d'inventaire"])
            assert (w['id'],'joconde:'+im['native_id']) in native_pairs or (w['id'],im['native_id']) in external_pairs or (w['id'],im['native_id'],im['source_page']) in citation_pairs,('Missing current exact native identity',im['native_id'])
        matches=db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s) OR source_page_url=ANY(%s) OR storage_path=ANY(%s)',([r['sha256'] for r in images],[r['source_page'] for r in images],[r['provisional_storage_path'] for r in images])).fetchall()
        assert not matches,'Existing media requires individual reuse reconciliation'
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    assert shutil.disk_usage(B).free>15*1024**3
    p=dict(at=c.now(),operation=OP,preparation_sha256=c.sha(PREP.read_bytes()),images=images,source=source,before=before,native_identity_verified=True,citations=citation_rows)
    c.save(B/'plan.json.gz',p)
    c.save(E/'plan-pin.json',dict(at=c.now(),path=str(B/'plan.json.gz'),sha256=c.sha((B/'plan.json.gz').read_bytes()),images=611,state='pinned_not_delivered',preparation_sha256=p['preparation_sha256']))
    print('Pinned611 exact existing-object images, source facts, files and fresh production preimages.',flush=True)


def pinned():
    p=B/'plan.json.gz'
    assert c.sha(p.read_bytes())==c.load(E/'plan-pin.json')['sha256']
    return c.load(p)


def bucket():
    spec=importlib.util.spec_from_file_location('image_core',c.ROOT/'ops/enrich-artwork-images.py')
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cred=core.GcloudCredentials();cred.refresh(None)
    return storage.Client(project='artline-508319',credentials=cred).bucket(core.BUCKET)


def upload():
    p=pinned();target=bucket();s=requests.Session()
    for n,r in enumerate(p['images'],1):
        out=E/'uploads'/(r['native_id']+'.json')
        if out.exists():continue
        raw=checked_image(r);blob=target.blob(r['provisional_storage_path'].lstrip('/'))
        exists=blob.exists(timeout=30)
        if not exists:
            blob.metadata={'sha256':r['sha256'],'operation':OP}
            blob.cache_control='public,max-age=31536000,immutable'
            blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=45)
        blob.reload(timeout=30)
        stored=blob.download_as_bytes(timeout=30)
        assert c.sha(stored)==r['sha256'] and blob.size==len(raw)
        assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=s.get(WEB+r['provisional_storage_path'],timeout=(10,35),allow_redirects=False)
        assert response.status_code==200 and c.sha(response.content)==r['sha256'],('Origin image verification',response.status_code,r['native_id'])
        c.save(out,dict(at=c.now(),native_id=r['native_id'],artwork_id=r['artwork_id'],storage_path=blob.name,generation=blob.generation,existed_before=exists,sha256=r['sha256'],bytes=len(raw),storage_bytes_verified=True,service_origin_bytes_verified=True,normal_edge_verification_claimed=False))
        if n%20==0 or n==len(p['images']):print('Uploaded and Storage/origin byte-verified',n,'/',len(p['images']),flush=True)


def apply():
    p=pinned();images=p['images']
    for start in range(0,len(images),50):
        batch=images[start:start+50];number=start//50+1;operation=OP+'-b%03d'%number
        receipt=E/('batch-%03d-verification.json'%number)
        if receipt.exists():assert c.load(receipt)['passed'];continue
        for r in batch:
            rc=c.load(E/'uploads'/(r['native_id']+'.json'));assert rc['storage_bytes_verified'] and rc['sha256']==r['sha256']
            checked_image(r)
        ids=[r['artwork_id'] for r in batch];changes=[]
        with c.connect(write=True) as db:
            db.execute("SET LOCAL lock_timeout='5s'")
            db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
            db.execute('SELECT pg_advisory_xact_lock(202610053)')
            db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
            before=snapshot(db,ids);old={r['id']:r for r in before['artworks']}
            initial={r['id']:r for r in p['before']['artworks'] if r['id'] in ids}
            assert old==initial,'Artwork metadata/primary changed since pinned plan; review without overwrite'
            assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s) OR id=ANY(%s::uuid[]) OR storage_path=ANY(%s)',([r['sha256'] for r in batch],[r['provisional_media_id'] for r in batch],[r['provisional_storage_path'] for r in batch])).fetchall()
            c.save(B/('locked-before-%03d.json.gz'%number),dict(at=c.now(),operation=operation,tables=before,plan_sha256=c.load(E/'plan-pin.json')['sha256']))
            for r in batch:
                aid,mid=r['artwork_id'],r['provisional_media_id']
                credit='Musée des Beaux-Arts de Rouen. Photographic credit: '+(r['credit'] or 'Not specified by source')
                asset=db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)VALUES(%s,'local',%s,%s,'Musée des Beaux-Arts de Rouen via Ministry of Culture POP/Joconde','image/jpeg',%s,%s,%s,%s,%s,'unknown','Image licence not specified; metadata licence is separate',%s,%s,%s,now(),%s) RETURNING to_jsonb(media_assets)v",(mid,r['provisional_storage_path'],r['source_page'],r['width'],r['height'],r['bytes'],r['sha256'],r['title'],credit,credit+'. '+r['transformation']+' '+r['rights_basis'],r['source_receipt']['at'],EDITOR)).fetchone()['v']
                ev=dict(preparation_sha256=p['preparation_sha256'],source_notice=r['source_page_receipt'],source_fields=r['source_fields'],source_image_receipt=r['source_receipt'],visual_review=r['visual_review'],derivative_sha256=r['sha256'],transformation=r['transformation'],metadata_licence_does_not_license_photograph=True,source_photographic_credit=r['credit'])
                rights=db.execute('INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s) RETURNING to_jsonb(media_rights_evidence)v',(mid,p['source']['id'],r['native_id'],r['source_page_receipt']['sha256'],r['image_url'],r['source_page'],r['rights_basis'],OP,Jsonb(ev))).fetchone()['v']
                attachment=db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,'Reviewed complete primary view from the exact POP/Joconde notice') RETURNING to_jsonb(artwork_media)v",(aid,mid)).fetchone()['v']
                work=db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s AND primary_media_id IS NULL RETURNING to_jsonb(artworks)v',(mid,EDITOR,aid)).fetchone()['v']
                assert all(work[k]==v for k,v in old[aid].items() if k not in {'primary_media_id','revision','updated_by','updated_at'})
                assert work['revision']==old[aid]['revision']+1
                for t,key,b,a,eid in [('media_assets',mid,None,asset,mid),('media_rights_evidence',mid,None,rights,mid),('artwork_media',aid+'/'+mid,None,attachment,aid),('artworks',aid,old[aid],work,aid)]:changes.append(dict(table=t,key=key,entity_id=eid,before=b,after=a))
            after=snapshot(db,ids)
            for t in ['artwork_artists','artwork_location_assertions']:assert m.ordered(before[t])==m.ordered(after[t]),('Protected references changed',t)
            assert len(after['artwork_media'])==len(before['artwork_media'])+len(batch)
            m.audit(db,changes,operation)
            c.save(B/('transaction-after-%03d.json.gz'%number),dict(at=c.now(),operation=operation,changes=changes,protected_before=before))
        verify_batch(number)


def verify_batch(number):
    tx=c.load(B/('transaction-after-%03d.json.gz'%number));changes=tx['changes'];ids=[r['key'] for r in changes if r['table']=='artworks']
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for t,col in [('artworks','id'),('media_assets','id'),('media_rights_evidence','media_id')]:
            expected={r['key']:r['after'] for r in changes if r['table']==t}
            assert {r[col]:r for r in m.rows(db,t,col,list(expected))}==expected,('Independent row mismatch',t)
        expected=[r['after'] for r in changes if r['table']=='artwork_media']
        actual=m.rows(db,'artwork_media','media_id',[r['media_id'] for r in expected]);assert m.ordered(actual)==m.ordered(expected)
        aa=db.execute('SELECT id,entity_type,entity_id,before_json,after_json,request_id FROM audit_log WHERE id=ANY(%s::uuid[])',([m.uid(tx['operation']+'/'+r['table']+'/'+r['key']) for r in changes],)).fetchall()
        audits={str(r['id']):r for r in aa};assert len(audits)==len(changes)
        for r in changes:
            a=audits[m.uid(tx['operation']+'/'+r['table']+'/'+r['key'])]
            assert a['request_id']==tx['operation'] and a['before_json']==r['before'] and a['after_json']==r['after']
        current=snapshot(db,ids)
        for t in ['artwork_artists','artwork_location_assertions']:assert m.ordered(current[t])==m.ordered(tx['protected_before'][t])
        n=db.execute('SELECT count(*)n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id',(ids,)).fetchone()['n'];assert n==len(ids)
    c.save(E/('batch-%03d-verification.json'%number),dict(at=c.now(),passed=True,operation=tx['operation'],new_primary_images=len(ids),atomic_audits=len(audits),independent_rows=len(changes),search_documents=n,metadata_creators_holdings_preserved=True))
    print('Committed and independently verified image batch',number,':',len(ids),'primary images,',len(audits),'atomic audits',flush=True)


def verify():
    p=pinned();s=requests.Session();out=[]
    for number in range(1,14):
        assert c.load(E/('batch-%03d-verification.json'%number))['passed']
    for n,r in enumerate(p['images'],1):
        rc=E/'public-artworks'/(r['native_id']+'.json')
        if rc.exists():out.append(c.load(rc));continue
        response=s.get(API+'/api/v1/atlas/artworks/'+r['artwork_id'],timeout=(10,35),allow_redirects=False)
        assert response.status_code==200,('Artwork API',response.status_code,r['artwork_id'])
        detail=response.json()
        assert r['provisional_storage_path'] in json.dumps(detail),('Image missing from public artwork',r['native_id'])
        img=s.get(WEB+r['provisional_storage_path'],timeout=(10,35),allow_redirects=False)
        assert img.status_code==200 and c.sha(img.content)==r['sha256']
        row=dict(at=c.now(),artwork_id=r['artwork_id'],native_id=r['native_id'],api_status=response.status_code,image_status=img.status_code,sha256=c.sha(img.content),bytes=len(img.content),service_origin=True)
        c.save(rc,row);out.append(row)
        if n%30==0:print('Public artwork/image pairs verified',n,'/',len(p['images']),flush=True)
    with c.connect() as db:
        count=db.execute("SELECT count(*)n,count(*)FILTER(WHERE primary_media_id IS NOT NULL) illustrated FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(ROUEN,)).fetchone()
    c.save(E/'final-verification.json',dict(at=c.now(),passed=True,new_primary_images=len(out),atomic_audits=4*len(out),public_service_origin_pairs=len(out),museum_counts=count,existing_images_preserved=True,normal_edge_client_verification_claimed=False,source_rights_unknown_and_credits_preserved=True))
    print('Finished611 production attachments and611 public artwork/image-byte pairs.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','upload','apply','verify','verify_batch']);p.add_argument('--batch',type=int)
    args=p.parse_args()
    if args.phase=='verify_batch':verify_batch(args.batch)
    else:globals()[args.phase]()
