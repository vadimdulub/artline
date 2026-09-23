#!/usr/bin/env python3
"""Compress audited oversize media without deleting originals or changing rights."""
import argparse
import base64
import concurrent.futures
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image, ImageOps
import psycopg
from psycopg.rows import dict_row
import requests
from google.api_core.exceptions import PreconditionFailed

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/deep-image-review-20260920/size-limit')
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'
NOTICE='Full-frame proportional resize and JPEG compression to at most 100,000 bytes; no crop or generated content.'


def normalized(value):return json.loads(core.encode(value))


def preimages(db,ids):
    return normalized({
        'media':db.execute('SELECT to_jsonb(m) record FROM media_assets m WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall(),
        'rights':db.execute('SELECT to_jsonb(r) record FROM media_rights_evidence r WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id',(ids,)).fetchall(),
        'artworks':db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE primary_media_id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall(),
        'portraits':db.execute('SELECT to_jsonb(p) record FROM artists p WHERE portrait_media_id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall(),
        'artwork_media':db.execute('SELECT to_jsonb(am) record FROM artwork_media am WHERE media_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',(ids,)).fetchall()})


def prepare(a):
    snapshots={t:json.loads((a.audit/(t+'-media-snapshot.json')).read_text()) for t in ('local','cloud')}
    targets={t:{r['id']:r for r in s['images'] if r['byte_size'] and r['byte_size']>100000} for t,s in snapshots.items()}
    if not targets['local'] or set(targets['local'])!=set(targets['cloud']):raise ValueError('Oversize selections differ; review target-specific differences')
    ids=sorted(targets['local']);manifests={};before={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            before[target]=preimages(db,ids)
        path=BACKUP/(target+'-before.json');core.save_new(path,before[target]);manifests[target]={'path':str(path),'sha256':core.sha(path.read_bytes())}
    records=[]
    for n,mid in enumerate(ids,1):
        old={t:next(r['record'] for r in before[t]['media'] if r['record']['id']==mid) for t in before}
        local=old['local']
        keys=('storage_path','byte_size','checksum_sha256','mime_type','rights_status','license_url','license_label','creator_credit','source_page_url')
        if any(old['cloud'][k]!=local[k] for k in keys):raise ValueError('Target media identities differ: '+mid)
        if local['storage_kind']!='local' or local.get('delivery_url'):raise ValueError('Remote delivery requires separate migration')
        source=ROOT/'apps/web/public'/local['storage_path'].lstrip('/')
        data=source.read_bytes()
        if core.sha(data)!=local['checksum_sha256'] or len(data)!=local['byte_size']:raise ValueError('Audited original changed')
        core.save_new(BACKUP/'originals'/(mid+source.suffix),data)
        encoded,w,h,quality=core.compress(data)
        with Image.open(io.BytesIO(data)) as im:
            oriented=ImageOps.exif_transpose(im)
            ow,oh=oriented.size
        if abs(w/h-ow/oh)>max(2/h,2/oh):raise ValueError('Aspect ratio changed')
        with Image.open(io.BytesIO(encoded)) as im:im.verify()
        path='/assets/artworks/size-limit-20260920/'+mid+'-'+core.sha(encoded)[:16]+'.jpg'
        core.save_new(ROOT/'apps/web/public'/path.lstrip('/'),encoded)
        records.append({'media_id':mid,'old':old,'path':path,'sha256':core.sha(encoded),
            'bytes':len(encoded),'width':w,'height':h,'quality':quality,
            'md5':base64.b64encode(hashlib.md5(encoded).digest()).decode()})
        if n%25==0:print('Prepared size-limited copies',n,'of',len(ids),flush=True)
    plan={'at':core.now(),'records':records,'backups':manifests,'scope':'Compression only; original files, original rights evidence, artwork metadata and all references preserved.'}
    core.save_new(a.run/'plan.json',plan)
    core.save_new(a.run/'manifest.json',{'sha256':core.sha((a.run/'plan.json').read_bytes()),'count':len(records)})
    print(json.dumps({'prepared':len(records),'before_bytes':sum(r['old']['local']['byte_size'] for r in records),
        'after_bytes':sum(r['bytes'] for r in records),'maximum_bytes':max(r['bytes'] for r in records)},indent=2),flush=True)


def pinned(run):
    raw=(run/'plan.json').read_bytes()
    if core.sha(raw)!=json.loads((run/'manifest.json').read_text())['sha256']:raise ValueError('Pinned plan changed')
    plan=json.loads(raw)
    for item in plan['backups'].values():
        if core.sha(Path(item['path']).read_bytes())!=item['sha256']:raise ValueError('Recovery preimage changed')
    return plan


def expected(r,target):
    old=r['old'][target]
    return dict(old,storage_path=r['path'],byte_size=r['bytes'],checksum_sha256=r['sha256'],
                width=r['width'],height=r['height'],mime_type='image/jpeg',
                attribution_text=((old.get('attribution_text') or '').rstrip()+' '+NOTICE).strip())


def stable(row):return {k:v for k,v in row.items() if k!='updated_at'}


def apply(a):
    plan=pinned(a.run);rows=plan['records'];dsns={'local':'postgres://localhost/artline'}
    if not a.local_only:dsns['cloud']=core.cloud_dsn()
    # Check both sides before uploads or any database mutation.
    for target,dsn in dsns.items():
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            current={r['record']['id']:r['record'] for r in db.execute('SELECT to_jsonb(m) record FROM media_assets m WHERE id=ANY(%s::uuid[])',([r['media_id'] for r in rows],)).fetchall()}
            for r in rows:
                if stable(current[r['media_id']]) not in (stable(r['old'][target]),stable(expected(r,target))):raise ValueError('Media changed since planning')
    bucket=None if a.local_only else core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def upload(r):
        data=(ROOT/'apps/web/public'/r['path'].lstrip('/')).read_bytes()
        if core.sha(data)!=r['sha256'] or len(data)!=r['bytes'] or len(data)>100000:raise ValueError('Prepared derivative differs')
        if a.local_only:return
        blob=bucket.blob(r['path'].lstrip('/'))
        blob.metadata={'media-id':r['media_id'],'sha256':r['sha256'],'original-sha256':r['old']['local']['checksum_sha256'],'license':r['old']['local']['license_label'] or ''}
        blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except PreconditionFailed:pass
        blob.reload()
        if blob.size!=r['bytes'] or blob.md5_hash!=r['md5']:raise ValueError('Stored derivative differs')
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(upload,rows))
    print('All new '+('local files' if a.local_only else 'storage objects')+' hash-verified before database updates',len(rows),flush=True)
    for target,dsn in dsns.items():
        with psycopg.connect(dsn,row_factory=dict_row) as db:
            db.execute("SET LOCAL lock_timeout='3s'")
            for r in rows:
                current=db.execute('SELECT to_jsonb(m) record FROM media_assets m WHERE id=%s FOR UPDATE',(r['media_id'],)).fetchone()['record']
                want=expected(r,target)
                if stable(current)==stable(want):continue
                if current!=r['old'][target]:raise ValueError('Concurrent media edit; transaction rolled back')
                db.execute('''UPDATE media_assets SET storage_path=%s,byte_size=%s,checksum_sha256=%s,
                    width=%s,height=%s,mime_type='image/jpeg',attribution_text=%s,updated_at=now() WHERE id=%s''',
                    (r['path'],r['bytes'],r['sha256'],r['width'],r['height'],want['attribution_text'],r['media_id']))
        if not (a.run/(target+'-applied.json')).exists():core.save_new(a.run/(target+'-applied.json'),{'at':core.now(),'updated_media':len(rows)})
        print(target,'size-limited media updated',len(rows),flush=True)


def verify(a):
    plan=pinned(a.run);rows=plan['records'];ids=[r['media_id'] for r in rows];results={};issues=[]
    targets=[('local','postgres://localhost/artline')]
    if not a.local_only:targets.append(('cloud',core.cloud_dsn()))
    for target,dsn in targets:
        before=json.loads(Path(plan['backups'][target]['path']).read_text())
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            after=preimages(db,ids)
            all_counts=db.execute("""SELECT count(*) images,max(byte_size) maximum_bytes,
                count(*) FILTER(WHERE byte_size>100000) oversize,
                count(*) FILTER(WHERE byte_size IS NULL) unknown_size
                FROM media_assets WHERE mime_type LIKE 'image/%%' OR mime_type IS NULL""").fetchone()
        byid={r['record']['id']:r['record'] for r in after['media']}
        matches=sum(stable(byid[r['media_id']])==stable(expected(r,target)) for r in rows)
        preserved={k:before[k]==after[k] for k in ('rights','artworks','portraits','artwork_media')}
        if matches!=len(rows) or not all(preserved.values()) or all_counts['oversize']:issues.append({'target':target,'error':'Preservation, metadata or size check failed'})
        results[target]={'updated_media_matched':matches,'unchanged':preserved,'whole_database_sizes':all_counts}
    def check(r):
        res=requests.get(BASE+r['path'],timeout=30)
        return {'media_id':r['media_id'],'http_status':res.status_code,'verified':res.status_code==200 and core.sha(res.content)==r['sha256'] and len(res.content)==r['bytes']<=100000}
    public=[]
    if not a.local_only:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:public=list(pool.map(check,rows))
    if not all(c['verified'] for c in public):issues.append({'error':'Public delivery mismatch'})
    result={'at':core.now(),'compressed':len(rows),'before_bytes':sum(r['old']['local']['byte_size'] for r in rows),
        'after_bytes':sum(r['bytes'] for r in rows),'databases':results,'public':public,'issues':issues,
        'originals_deleted':False,'rights_relicensed':False,'local_only':a.local_only}
    core.save_new(a.run/('verification-local.json' if a.local_only else 'verification.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k!='public'},indent=2),flush=True)
    if issues:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','apply','verify']);p.add_argument('--run',type=Path,required=True);p.add_argument('--audit',type=Path)
    p.add_argument('--local-only',action='store_true');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);globals()[a.phase](a)
