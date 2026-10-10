#!/usr/bin/env python3
"""Deliver the exact regional review batch to production; never publish it."""
import argparse
import base64
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from urllib.parse import quote

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/research/africa-asia-cyprus-20261005'
RUN=BASE/'production'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/africa-asia-cyprus-20261005/production'
PROJECT='artline-508319'
INSTANCE='artline-postgres'
ACCOUNT='vadim@alingva.com'
BUCKET='artline-508319-images'
SITE='https://artline-web-lpuqqlugnq-ew.a.run.app'
DESCRIPTION='Before regional review import: Africa Asia Cyprus 20261005'
ORDER=['countries','sources','artists','artist_countries','media_assets','media_rights_evidence',
       'artworks','artwork_artists','artwork_media','external_identifiers','citations','curated_collection_items']
KEYS={'countries':['code'],'sources':['id'],'artists':['id'],'artist_countries':['artist_id','country_code','relationship_type'],
      'media_assets':['id'],'media_rights_evidence':['media_id'],'artworks':['id'],
      'artwork_artists':['artwork_id','artist_id'],'artwork_media':['artwork_id','media_id'],
      'external_identifiers':['id'],'citations':['id'],'curated_collection_items':['id']}
spec=importlib.util.spec_from_file_location('publication_helpers',ROOT/'ops/publish-japan-20260925.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
save=h.save
sha=h.sha
now=h.now
getrows=h.getrows
insert=h.insert


def gcloud(*args):
    return subprocess.check_output(['gcloud',*args,'--project='+PROJECT,'--account='+ACCOUNT],text=True)


def connect(target,readonly=True):
    dsn='postgres://localhost/artline'
    if target=='production':
        secret=gcloud('secrets','versions','access','latest','--secret=artline-database-url').strip()
        params=psycopg.conninfo.conninfo_to_dict(secret)
        params.update(host='127.0.0.1',port='55446',sslmode='disable',connect_timeout='15')
        dsn=psycopg.conninfo.make_conninfo(**params)
    return psycopg.connect(dsn,row_factory=dict_row,autocommit=True,
        options='-c timezone=UTC -c statement_timeout=180000 -c lock_timeout=10000'+(' -c default_transaction_read_only=on' if readonly else ''))


def load(name):return json.loads((RUN/name).read_text())
def key(table,row):return tuple(row[k] for k in KEYS[table])


def selected_rows(db,table,rows):
    if not rows:return []
    if len(KEYS[table])==1:
        field=KEYS[table][0]
        cast='text[]' if field=='code' else 'uuid[]'
        return getrows(db,table,field+'=ANY(%s::'+cast+')',([x[field] for x in rows],))
    column=KEYS[table][0]
    all_rows=getrows(db,table,column+'=ANY(%s::uuid[])',([x[column] for x in rows],))
    keys={key(table,x) for x in rows}
    return [x for x in all_rows if key(table,x) in keys]


def plan():
    assert not (RUN/'plan.json').exists(),'Plan already pinned'
    local_plan=json.loads((BASE/'application-plan.json').read_text())
    receipt=json.loads((BASE/'applied.json').read_text())
    verification=json.loads((BASE/'verification.json').read_text())
    assert not verification['errors'] and receipt['artworks']==177 and receipt['images']==43
    assert sha((BASE/'application-plan.json').read_bytes())==receipt['plan_sha256']
    ids=receipt['artwork_ids'];sid=receipt['source_id']
    with connect('local') as local,connect('production') as prod:
        batch={}
        batch['sources']=getrows(local,'sources','id=%s',(sid,));assert len(batch['sources'])==1
        batch['artworks']=getrows(local,'artworks','id=ANY(%s::uuid[])',(ids,));assert len(batch['artworks'])==177
        batch['artwork_artists']=getrows(local,'artwork_artists','artwork_id=ANY(%s::uuid[])',(ids,))
        artist_ids=sorted({x['artist_id'] for x in batch['artwork_artists']})
        batch['artists']=getrows(local,'artists','id=ANY(%s::uuid[])',(artist_ids,))
        all_countries=getrows(local,'artist_countries','artist_id=ANY(%s::uuid[])',(artist_ids,))
        geography={(x['artist_id'],x['country'][0],'cultural_affiliation') for x in local_plan['geography']}
        batch['artist_countries']=[x for x in all_countries if key('artist_countries',x) in geography]
        assert len(batch['artist_countries'])==37
        codes=sorted({x['country_code'] for x in batch['artist_countries']})
        batch['countries']=getrows(local,'countries','code=ANY(%s::text[])',(codes,))
        media=[x['primary_media_id'] for x in batch['artworks'] if x['primary_media_id']]
        for table,column,values in [('media_assets','id',media),('media_rights_evidence','media_id',media),
                                   ('artwork_media','artwork_id',ids),('curated_collection_items','artwork_id',ids)]:
            batch[table]=getrows(local,table,column+'=ANY(%s::uuid[])',(values,))
        for table in ['citations','external_identifiers']:
            batch[table]=getrows(local,table,'source_id=%s AND entity_id=ANY(%s::uuid[])',(sid,ids+artist_ids))
        owner=getrows(prod,'curated_collections',"curator_kind='owner' AND institution_id IS NULL",())
        assert len(owner)==1 and owner[0]['status']!='archived'
        assert all(x['collection_id']==local_plan['owner_collection_id'] for x in batch['curated_collection_items'])
        assert prod.execute("SELECT 1 FROM editor_accounts WHERE user_id='local-european-research'").fetchone()
        for w in batch['artworks']:
            assert w['status']=='review' and w['research_candidate'] and w['published_at'] is None
            assert w['creation_year_end']<=1970 and not w['current_institution_id'] and not w['location_checked_at']
        assert not getrows(local,'artwork_location_assertions','artwork_id=ANY(%s::uuid[])',(ids,))
        source_snapshot=copy.deepcopy(batch)
        remap={local_plan['owner_collection_id']:owner[0]['id']}
        before={'curated_collections':owner};conflicts=[];existing_artist_ids=[];new_artists=[]
        for a in batch['artists']:
            matches=getrows(prod,'artists','id=%s OR slug=%s OR normalized_name=%s',(a['id'],a['slug'],a['normalized_name']))
            if not matches:
                aliases=prod.execute('SELECT artist_id::text FROM artist_aliases WHERE normalized_alias=%s',(a['normalized_name'],)).fetchall()
                if aliases:matches=getrows(prod,'artists','id=ANY(%s::uuid[])',([x['artist_id'] for x in aliases],))
            if len(matches)>1:
                conflicts.append({'artist':a['display_name'],'reason':'ambiguous_identity','matches':matches});continue
            if matches:
                target=matches[0]
                if target['status']=='archived' or any(a[x]!=target[x] for x in ['display_name','birth_year','death_year']):
                    conflicts.append({'artist':a['display_name'],'reason':'identity_fields_differ','local':a,'production':target});continue
                remap[a['id']]=target['id'];existing_artist_ids.append(target['id'])
            else:
                assert a['status']=='review' and a['published_at'] is None and a['portrait_media_id'] is None,'Missing existing authority needs dependency review'
                new_artists.append(a)
        if conflicts:
            save(RUN/'identity-conflicts.json',conflicts)
            raise ValueError('Resolve production artist identities first; see identity-conflicts.json')
        before['existing_artists']=getrows(prod,'artists','id=ANY(%s::uuid[])',(existing_artist_ids,))
        batch['artists']=new_artists
        for rows in batch.values():
            for row in rows:
                for field in ['artist_id','entity_id','collection_id']:
                    if row.get(field) in remap:row[field]=remap[row[field]]
        urls=[x['source_url'] for x in batch['citations'] if x['entity_type']=='artwork']
        assert not getrows(prod,'artworks','id=ANY(%s::uuid[]) OR slug=ANY(%s)',(ids,[x['slug'] for x in batch['artworks']])), 'Batch artwork already exists'
        assert not getrows(prod,'citations',"entity_type='artwork' AND source_url=ANY(%s)",(urls,)), 'Source already attached to production artwork'
        assert not getrows(prod,'external_identifiers',"entity_type='artwork' AND canonical_url=ANY(%s)",(urls,)), 'Source already has production identity'
        # Check creator/title collisions only within the selected artists.
        title_index=collections_title_index(batch['artworks'],batch['artwork_artists'])
        existing_works=prod.execute("""SELECT a.id::text,a.title,a.alternate_title,aa.artist_id::text FROM artwork_artists aa
          JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])""",(existing_artist_ids,)).fetchall()
        spec2=importlib.util.spec_from_file_location('regional_names',ROOT/'ops/research-africa-asia-cyprus-20261005.py')
        names=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(names)
        collisions=[x for x in existing_works if any(names.norm(v) in title_index.get(x['artist_id'],set()) for v in [x['title'],x['alternate_title']] if v)]
        assert not collisions,'Production creator/title collision: '+str(collisions)
        for table in ORDER:
            old=selected_rows(prod,table,batch[table]);before[table]=old
            if table=='countries':
                old_by_key={key(table,x):x for x in old}
                for x in batch[table]:
                    if key(table,x) in old_by_key:assert x==old_by_key[key(table,x)],'Country metadata differs'
            elif table=='artist_countries':
                pass  # Existing documented relationship stays untouched.
            else:
                assert not old,'Selected row already exists: '+table
            existing={key(table,x) for x in old}
            batch[table]=[x for x in batch[table] if key(table,x) not in existing]
        for m in batch['media_assets']:
            path=ROOT/'apps/web/public'/m['storage_path'].lstrip('/')
            assert sha(path.read_bytes())==m['checksum_sha256'] and path.stat().st_size==m['byte_size']<=100000
            assert m['rights_status']=='public_domain'
        export=dict(at=now(),ids=ids,source_id=sid,rows=batch,source_snapshot=source_snapshot,before=before,remap=remap,
                    owner_id=owner[0]['id'],source_plan_sha256=receipt['plan_sha256'],
                    policy='Production delivery only; preserve review state, unknown fields and all existing artist records.')
    save(RUN/'plan.json',export);save(BACKUP/'plan.json',export)
    save(RUN/'plan-pin.json',{'sha256':sha((RUN/'plan.json').read_bytes())})
    print(json.dumps({'insert_counts':{k:len(v) for k,v in batch.items()},'existing_artists':len(existing_artist_ids),
                      'sha256':sha((RUN/'plan.json').read_bytes())}),flush=True)


def collections_title_index(works,links):
    import unicodedata,re
    def norm(v):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',v.casefold()) if not unicodedata.combining(c))))
    titles={x['id']:norm(x['title']) for x in works};result={}
    for x in links:result.setdefault(x['artist_id'],set()).add(titles[x['artwork_id']])
    return result


def pinned():
    assert sha((RUN/'plan.json').read_bytes())==load('plan-pin.json')['sha256']
    return load('plan.json')


def backup():
    pinned()
    rows=json.loads(gcloud('sql','backups','list','--instance='+INSTANCE,'--limit=40','--format=json'))
    matching=[x for x in rows if x.get('description')==DESCRIPTION]
    if not matching:
        result=gcloud('sql','backups','create','--instance='+INSTANCE,'--description='+DESCRIPTION,'--async','--format=json')
        save(BACKUP/'backup-operation.json',json.loads(result))
        print('Production backup requested',flush=True);return
    current=max(matching,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':
        print('Production backup status:',current['status'],flush=True);return
    save(BACKUP/'cloud-backup.json',current)
    save(RUN/'backup.json',dict(at=now(),backup=current))
    print('Production backup verified:',current['id'],flush=True)


def upload():
    p=pinned();assert load('backup.json')['backup']['status']=='SUCCESSFUL'
    token=subprocess.check_output(['gcloud','auth','print-access-token','--account='+ACCOUNT],text=True).strip()
    session=requests.Session();session.headers['Authorization']='Bearer '+token
    checks=[]
    for m in p['rows']['media_assets']:
        data=(ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes()
        assert sha(data)==m['checksum_sha256'] and len(data)==m['byte_size']<=100000
        name=m['storage_path'].lstrip('/');url=f'https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/'+quote(name,safe='')
        response=session.get(url,timeout=(10,40));created=False
        if response.status_code==404:
            response=session.post(f'https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o',
                params={'uploadType':'media','name':name,'ifGenerationMatch':0},data=data,headers={'Content-Type':'image/jpeg'},timeout=(10,60))
            response.raise_for_status();created=True
        response.raise_for_status();obj=response.json()
        assert int(obj['size'])==len(data) and obj['md5Hash']==base64.b64encode(hashlib.md5(data).digest()).decode()
        checks.append(dict(path=m['storage_path'],sha256=sha(data),generation=obj['generation'],created=created))
        if len(checks)%10==0:print('Images verified',len(checks),flush=True)
    save(RUN/'storage.json',dict(at=now(),checks=checks))
    print('Uploaded and verified',len(checks),'images',flush=True)


def apply():
    p=pinned();assert not (RUN/'applied.json').exists(),'Already delivered; run verify'
    b=load('backup.json')['backup']
    backup_status=json.loads(gcloud('sql','backups','describe',str(b['id']),'--instance='+INSTANCE,'--format=json'))
    assert backup_status['status']=='SUCCESSFUL'
    assert len(load('storage.json')['checks'])==len(p['rows']['media_assets'])==43
    with connect('production',False) as db,db.transaction():
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        owner=db.execute('SELECT * FROM curated_collections WHERE id=%s FOR UPDATE',(p['owner_id'],)).fetchone()
        assert owner['curator_kind']=='owner' and owner['institution_id'] is None and owner['status']!='archived'
        existing_artists=getrows(db,'artists','id=ANY(%s::uuid[])',([x['id'] for x in p['before']['existing_artists']],))
        assert existing_artists==p['before']['existing_artists'],'Selected existing artist changed after preflight'
        for table in ORDER:assert not selected_rows(db,table,p['rows'][table]),'Concurrent selected insert: '+table
        save(BACKUP/('locked-preimages-'+now().replace(':','-')+'.json'),dict(owner=owner,existing_artists=existing_artists,
             plan_sha256=load('plan-pin.json')['sha256'],before=p['before']))
        position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(p['owner_id'],)).fetchone()['n']
        assert position+177<=100000
        for table in ORDER:
            for row in p['rows'][table]:
                row=copy.deepcopy(row)
                if table=='curated_collection_items':position+=1;row['position']=position
                insert(db,table,row)
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(p['owner_id'],))
        assert getrows(db,'artists','id=ANY(%s::uuid[])',([x['id'] for x in existing_artists],))==existing_artists
        checks=database_checks(db,p)
    save(RUN/'applied.json',dict(at=now(),plan_sha256=load('plan-pin.json')['sha256'],backup_id=b['id'],
        artworks=len(p['rows']['artworks']),artists=len(p['rows']['artists']),images=43,status='review',checks=checks))
    print('Production review import complete: 177 artworks,',len(p['rows']['artists']),'artists, 43 images',flush=True)


def database_checks(db,p):
    for table in ORDER:
        actual={key(table,x):x for x in selected_rows(db,table,p['rows'][table])}
        for expected in p['rows'][table]:
            found=actual[key(table,expected)]
            for field,value in expected.items():
                if table=='curated_collection_items' and field=='position':continue
                assert found[field]==value,(table,field,expected.get('id'))
    assert not getrows(db,'artwork_location_assertions','artwork_id=ANY(%s::uuid[])',(p['ids'],))
    return {'all_rows_match':True,'artworks':177,'review_status_preserved':True,'no_holding_or_display_assertions':True}


def verify():
    p=pinned();assert (RUN/'applied.json').exists()
    with connect('production') as db:checks=database_checks(db,p)
    def image_check(m):
        response=requests.get(SITE+m['storage_path'],timeout=(10,50));response.raise_for_status()
        assert sha(response.content)==m['checksum_sha256']
        return dict(path=m['storage_path'],status=response.status_code,sha256=sha(response.content))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        images=list(pool.map(image_check,p['rows']['media_assets']))
    # Existing research preview can show review records; published-only reads
    # must keep excluding them. Do not change server visibility settings.
    access=[]
    for wid in p['ids'][:3]:
        response=requests.get(SITE+'/api/backend/v1/atlas/artworks/'+wid+'?preview=0',timeout=(10,40))
        assert response.status_code==404,(wid,response.status_code)
        access.append(dict(id=wid,status=response.status_code,expected='review record hidden from published-only API'))
    def detail_check(work):
        response=requests.get(SITE+'/api/backend/v1/atlas/artworks/'+work['id'],timeout=(10,40))
        response.raise_for_status();data=response.json()
        assert data['id']==work['id'] and data['title']==work['title'] and data['status']=='review'
        return {'id':work['id'],'status':response.status_code}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        details=list(pool.map(detail_check,p['rows']['artworks']))
    save(RUN/'verification.json',dict(at=now(),database=checks,images=images,public_research_details=details,published_only_access=access,errors=[]))
    print('Verified production metadata, 177 research detail responses, 43 public image hashes, and published-only restrictions',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['plan','backup','upload','apply','verify'])
    globals()[parser.parse_args().phase]()
