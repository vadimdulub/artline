#!/usr/bin/env python3
"""Reconcile the completed UK batch with production without overwriting records."""
import base64,concurrent.futures,hashlib,importlib.util,json,time,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('uk',Path(__file__).with_name('uk-painters-20260920.py'))
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
m,RUN=u.m,u.RUN
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'

def read(path):return json.loads(path.read_bytes())
def records(path):return [read(p) for p in sorted(path.glob('*.json'))]

def repair_memberships(dsn,collection,ids,selections):
    entries=[selections[aid] for aid in sorted(ids)]
    key=m.core.sha(m.core.encode(entries))[:20]
    backup=m.BACKUP/'production-sync/collection-memberships'/(key+'.json')
    with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
        with db.transaction():
            db.execute("SET LOCAL lock_timeout='15s'")
            before=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection,)).fetchone()['record']
            assert before['curator_kind']=='owner' and before['institution_id'] is None and before['status']!='archived'
            old=db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection,ids)).fetchall()
            artworks=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
            assert len(artworks)==len(ids) and all(v['record']['status']!='archived' and v['record']['creation_year_start'] is not None and v['record']['creation_year_end']<=1955 for v in artworks)
            if not backup.exists():u.save(backup,{'collection':before,'memberships':old,'artworks':artworks,'selected':entries,'reason':'Complete the owner-requested UK production delivery; these existing artworks already received selected images.'})
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(u.SOURCE,)).fetchone()['id']
            db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) x(artwork_id uuid,source_url text,checked_at timestamptz)),
                positions AS(SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s),
                selected AS(SELECT x.*,row_number() OVER(ORDER BY artwork_id)::int ord FROM input x)
                INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                SELECT %s,s.artwork_id,p.n+s.ord,'Owner UK collection selection; production synchronization of already delivered historical artwork and image. No museum designation or holding claim.',%s,s.source_url,s.checked_at
                FROM selected s CROSS JOIN positions p ON CONFLICT(collection_id,artwork_id) DO NOTHING""",(m.Jsonb(entries),collection,collection,sid))
            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection,))
            after=db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection,ids)).fetchall()
            assert {r['artwork_id'] for r in after}==set(ids)
    u.save(RUN/('production-memberships-'+key+'.json'),{'added_artworks':ids,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now()})
    return len(ids)

def main():
    previous=read(sorted(RUN.glob('final-verification-*.json'))[-1]);assert not previous['errors']
    images={r['path']:{k:r[k] for k in ('path','sha256','bytes')} for r in records(RUN/'museum-uploads')}
    works={r['artwork_id']:r['after'] for r in records(RUN/'museum-applied/cloud')}
    artists={r['artist_id']:r['after'] for r in records(RUN/'authorities-applied/cloud')+records(RUN/'directory-final-applied/cloud')}
    attached=[];selections={}
    for receipt in records(RUN/'museum-applied/cloud'):
        if receipt['image_attached']:attached.append({'id':receipt['artwork_id'],'media_id':receipt['media_id'],'provider':'Commons'})
    for folder in [RUN,RUN/'wikiart-supplement']:
        wiki_images={r['artwork_id']:r for r in records(folder/'images')}
        for im in wiki_images.values():images[im['path']]={k:im[k] for k in ('path','sha256','bytes')}
        for receipt in records(folder/'delivery'):
            target=receipt['targets']['cloud']
            if target.get('after'):
                after=target['after'];works[after['id']]=after
                attached.append({'id':after['id'],'media_id':after['primary_media_id'],'provider':'WikiArt'})
                im=wiki_images[receipt['artwork_id']];selections[after['id']]={'artwork_id':after['id'],'source_url':im['page'],'checked_at':im['checked_at']}
    assert len(images)==previous['public_uploaded_files']
    collection=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    errors=[];dsn=m.core.cloud_dsn()
    with m.read_only(dsn) as db:
        current_artists={v['record']['id']:v['record'] for v in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(list(artists),)).fetchall()}
        current_works={v['record']['id']:v['record'] for v in db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(list(works),)).fetchall()}
        members={v['artwork_id'] for v in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection,list(works))).fetchall()}
        media={v['record']['id']:v['record'] for v in db.execute('SELECT to_jsonb(ma) record FROM media_assets ma WHERE id=ANY(%s::uuid[])',([r['media_id'] for r in attached],)).fetchall()}
        for kind,expected,current in [('artist',artists,current_artists),('artwork',works,current_works)]:
            for key,before in expected.items():
                after=current.get(key)
                # A later schema may add columns. Existing supplied fields must
                # still match, except ordinary revision/audit timestamps.
                differences=[field for field,value in before.items() if field not in ('revision','updated_at','updated_by') and (not after or after.get(field)!=value)]
                if differences:errors.append({'entity_type':kind,'id':key,'fields':differences,'missing':after is None})
        missing_memberships=sorted(set(works)-members)
        if set(missing_memberships)-set(selections):errors.append({'error':'Unexpected owner collection gaps','ids':missing_memberships})
        for row in attached:
            asset=media.get(row['media_id'])
            image=images.get(asset['storage_path']) if asset else None
            if not image or asset['checksum_sha256']!=image['sha256'] or asset['byte_size']!=image['bytes']:errors.append({'error':'Image attachment metadata differs','artwork_id':row['id']})
    print('Production database checked',len(artists),'artist records,',len(works),'artworks,',len(attached),'attachments; discrepancies',len(errors),flush=True)
    if errors:
        u.save(RUN/('production-reconciliation-errors-'+str(int(time.time()))+'.json'),errors)
        raise RuntimeError('Production record differences need scoped reconciliation; no existing record overwritten')
    memberships_added=repair_memberships(dsn,collection,missing_memberships,selections) if missing_memberships else 0
    print('Personal collection links added in production',memberships_added,flush=True)
    bucket=m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    object_names={path.lstrip('/') for path in images};remote={}
    for prefix in sorted({name.rsplit('/',1)[0]+'/' for name in object_names}):
        for blob in bucket.list_blobs(prefix=prefix,page_size=1000,fields='items(name,size,md5Hash,generation),nextPageToken'):
            if blob.name in object_names:remote[blob.name]=blob
        print('Production storage inventory',prefix,len(remote),'matched objects',flush=True)
    uploaded=[];file_checks=[]
    def check_image(im):
        path=im['path'];raw=(u.ROOT/'apps/web/public'/path.lstrip('/')).read_bytes()
        assert len(raw)==im['bytes']<=100000 and m.core.sha(raw)==im['sha256'],('Local source differs',path)
        checksum=base64.b64encode(hashlib.md5(raw).digest()).decode();blob=remote.get(path.lstrip('/'));created=False
        if blob is None:
            blob=bucket.blob(path.lstrip('/'));blob.cache_control='public,max-age=31536000,immutable';blob.metadata={'sha256':im['sha256']}
            try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60);created=True
            except m.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==checksum,('Production object differs; preserved for review',path)
        return dict(im,md5_base64=checksum,generation=blob.generation,uploaded=created)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(check_image,images.values()):
            file_checks.append(result)
            if result['uploaded']:uploaded.append(result['path'])
    # Fresh unauthenticated requests confirm both public serving and API access.
    samples=[]
    for provider in ('Commons','WikiArt'):
        rows=[v for v in attached if v['provider']==provider]
        samples.extend(rows[::max(1,len(rows)//20)][:20])
    def public_check(row):
        response=m.requests.get(BASE+'/api/backend/v1/atlas/artworks/'+row['id'],timeout=(15,45));response.raise_for_status();body=response.json()
        expected=images[media[row['media_id']]['storage_path']];assert body['media_url']==expected['path']
        response=m.requests.get(BASE+expected['path'],timeout=(15,45));response.raise_for_status()
        assert len(response.content)==expected['bytes'] and m.core.sha(response.content)==expected['sha256']
        return {'artwork_id':row['id'],'image':expected['path'],'http_status':200,'checksum_verified':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:public_checks=list(pool.map(public_check,samples))
    result={'at':m.core.now(),'scope':'Completed UK batch only','prior_verification':previous['at'],'production_artists_checked':len(artists),'production_artworks_checked':len(works),'image_attachments_checked':len(attached),'production_image_files_checked':len(file_checks),'missing_images_uploaded':uploaded,'personal_collection_links_added':memberships_added,'max_bytes':max(r['bytes'] for r in file_checks),'file_checks':file_checks,'public_checks':public_checks,'errors':[],'new_batch_totals':previous['databases']['cloud']}
    path=RUN/('production-sync-'+str(int(time.time()))+'.json');u.save(path,result)
    digest=m.core.sha(Path(__file__).read_bytes());u.save(m.BACKUP/'operation-scripts'/(Path(__file__).name+'.'+digest[:16]),Path(__file__).read_bytes())
    print(json.dumps({'receipt':str(path),'production_artists':len(artists),'production_artworks':len(works),'public_images':len(file_checks),'new_uploads':len(uploaded),'personal_collection_links_added':memberships_added,'public_spot_checks':len(public_checks),'errors':0}),flush=True)

if __name__=='__main__':main()
