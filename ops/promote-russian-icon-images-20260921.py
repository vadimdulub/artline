#!/usr/bin/env python3
"""Promote only the 217 reviewed illustrated icons, with scoped production recovery."""
import argparse, base64, collections, concurrent.futures, hashlib, importlib.util, json, os, re, time
from pathlib import Path
import psycopg, requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('research',ROOT/'ops/russian-icon-images-20260921.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c=r.core();RUN=r.RUN/'production';BACKUP=r.BACKUP/'production';save=r.save;read=r.read
PUBLIC='https://artline-web-lpuqqlugnq-ew.a.run.app'
TABLES=['artworks','media_assets','artwork_artists','external_identifiers','citations','artwork_location_assertions','curated_collection_items','media_rights_evidence']

def connection(dsn,readonly=True):
    return psycopg.connect(dsn,options="-c timezone=UTC -c statement_timeout=60000"+(' -c default_transaction_read_only=on' if readonly else ''),row_factory=dict_row)

def rows(db,table,where,params):
    return [v['record'] for v in db.execute('SELECT to_jsonb(t) record FROM '+table+' t WHERE '+where+' ORDER BY to_jsonb(t)::text',params).fetchall()]

def images():
    approved=read(r.RUN/'visual-review.json')['approved'];out=[]
    for key,checksum in sorted(approved.items()):
        im=read(r.RUN/'prepared'/(key+'.json'));raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert c.sha(raw)==checksum==im['sha256'] and len(raw)==im['bytes']<=100000
        out.append(im)
    assert len(out)==217
    return out

def snapshot(db,ids,media_ids):
    result={}
    for table in TABLES:
        if table=='artworks':where,key='id=ANY(%s::uuid[])',ids
        elif table=='media_assets':where,key='id=ANY(%s::uuid[])',media_ids
        elif table=='media_rights_evidence':where,key='media_id=ANY(%s::uuid[])',media_ids
        elif table in ('citations','external_identifiers'):where,key="entity_type='artwork' AND entity_id=ANY(%s::uuid[])",ids
        else:where,key='artwork_id=ANY(%s::uuid[])',ids
        result[table]=rows(db,table,where,(key,))
    return result

def export():
    ims=images();ids=[im['work']['artwork_id'] for im in ims];mids=[im['media_id'] for im in ims]
    with connection(r.DSN) as db:
        out=snapshot(db,ids,mids)
        assert len(out['artworks'])==len(out['media_assets'])==len(out['media_rights_evidence'])==217
        assert all(w['status']=='review' and w['published_at'] is None and w['object_form']=='icon' and w['creation_year_end']<=1955 for w in out['artworks'])
        assert all(m['rights_status']=='restricted' and m['verified_at'] is None for m in out['media_assets'])
        for im in ims:
            w=next(w for w in out['artworks'] if w['id']==im['work']['artwork_id']);m=next(m for m in out['media_assets'] if m['id']==im['media_id'])
            assert w['primary_media_id']==m['id'] and m['storage_path']==im['path'] and m['checksum_sha256'].strip()==im['sha256']
        sids={v['source_id'] for k in TABLES for v in out[k] if v.get('source_id')}
        iids={v['current_institution_id'] for v in out['artworks'] if v['current_institution_id']}|{v['institution_id'] for v in out['artwork_location_assertions']}
        aids={v['artist_id'] for v in out['artwork_artists']};cids={v['collection_id'] for v in out['curated_collection_items']}
        for table,keys in [('sources',sids),('institutions',iids),('artists',aids),('curated_collections',cids)]:out[table]=rows(db,table,'id=ANY(%s::uuid[])',(list(keys),))
        assert len(out['curated_collections'])==1 and out['curated_collections'][0]['curator_kind']=='owner' and out['curated_collections'][0]['institution_id'] is None
        assert all(v['claim_type']=='holding' and v['review_state']=='accepted' and v['venue_id'] is None and v['superseded_by'] is None for v in out['artwork_location_assertions'])
        out['source_schema']={t:[x['column_name'] for x in db.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",(t,))] for t in TABLES+['sources','institutions','curated_collections']}
    out['at']=c.now();out['images']=[{'artwork_id':im['work']['artwork_id'],'media_id':im['media_id'],'path':im['path'],'sha256':im['sha256'],'bytes':im['bytes']} for im in ims]
    save(RUN/'local-export.json',out);save(BACKUP/'local-export.json',out)
    print('Pinned local export', {k:len(v) for k,v in out.items() if isinstance(v,list)},flush=True)

def accession_key(value):
    value=re.sub(r'\s+','',value or '').upper()
    return re.sub(r'^КП-','КП',value) # Never remove internal accession punctuation.

def preflight():
    data=read(RUN/'local-export.json');ids=[w['id'] for w in data['artworks']];mids=[m['id'] for m in data['media_assets']]
    report={'at':c.now(),'local_export_sha256':c.sha((RUN/'local-export.json').read_bytes()),'conflicts':[],'maps':{},'new':{},'existing':{}}
    with connection(c.cloud_dsn()) as db:
        for table in data['source_schema']:
            columns={x['column_name'] for x in db.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s",(table,))}
            assert set(data['source_schema'][table])<=columns,('Missing production columns',table)
        assert db.execute("SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active",(r.ACTOR,)).fetchone()
        current=snapshot(db,ids,mids);report['before']=current
        matching=rows(db,'artworks','id=ANY(%s::uuid[]) OR slug=ANY(%s)',(ids,[w['slug'] for w in data['artworks']]))
        if matching:report['conflicts'].append({'kind':'artwork_id_or_slug_already_present','records':matching})
        if current['media_assets']:report['conflicts'].append({'kind':'media_id_already_present','records':current['media_assets']})
        matches=rows(db,'media_assets','storage_path=ANY(%s)',([m['storage_path'] for m in data['media_assets']],))
        if matches:report['conflicts'].append({'kind':'media_path_already_present','records':matches})
        # Resolve dependencies by their stable catalogue identities, preserving production rows.
        for table in ['sources','institutions','artists']:
            existing=rows(db,table,'slug=ANY(%s) OR id=ANY(%s::uuid[])',([v['slug'] for v in data[table]],[v['id'] for v in data[table]]))
            report['existing'][table]=existing;report['new'][table]=[];mapping={}
            for v in data[table]:
                matches=[x for x in existing if x['slug']==v['slug'] or x['id']==v['id']]
                assert len(matches)<=1,('Ambiguous dependency',table,v['slug'])
                if matches:
                    assert matches[0]['slug']==v['slug'];mapping[v['id']]=matches[0]['id']
                    if table=='artists':assert matches[0]['display_name']==v['display_name']
                else:
                    assert table!='artists','Do not create substitute creator biographies'
                    if table=='institutions':assert v['place_id'] is None and v['status']=='review'
                    mapping[v['id']]=v['id'];report['new'][table].append(v)
            report['maps'][table]=mapping
        collection=data['curated_collections'][0]
        matches=rows(db,'curated_collections',"institution_id IS NULL AND curator_kind='owner'",())
        assert len(matches)==1 and matches[0]['status']=='review'
        report['collection_before']=matches[0];report['maps']['curated_collections']={collection['id']:matches[0]['id']}
        report['collection_items_before_count']=db.execute('SELECT count(*) n FROM curated_collection_items WHERE collection_id=%s',(matches[0]['id'],)).fetchone()['n']
        # Scope native-ID and URL matching by indexed scheme/entity lookups.
        native=[]
        for scheme in {v['scheme'] for v in data['external_identifiers']}:
            group=[v for v in data['external_identifiers'] if v['scheme']==scheme]
            native+=rows(db,'external_identifiers',"entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(scheme,[v['external_id'] for v in group]))
        if native:report['conflicts'].append({'kind':'native_identifiers_already_present','records':native})
        # Cross-scheme duplicate protection uses only the three holding institutions.
        for local_iid,cloud_iid in report['maps']['institutions'].items():
            if any(i['id']==cloud_iid for i in report['new']['institutions']):continue
            candidates=rows(db,'artworks','current_institution_id=%s AND accession_number IS NOT NULL',(cloud_iid,))
            scoped=[w for w in data['artworks'] if w['current_institution_id']==local_iid]
            for w in scoped:
                matches=[v for v in candidates if accession_key(v['accession_number'])==accession_key(w['accession_number'])]
                if matches:report['conflicts'].append({'kind':'same_museum_accession','local_artwork_id':w['id'],'records':matches})
        report['id_query_plan']=db.execute('EXPLAIN (ANALYZE,FORMAT JSON) SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['QUERY PLAN']
    save(RUN/'preflight.json',report);save(BACKUP/'production-preflight.json',report)
    print('Preflight conflicts',len(report['conflicts']),'new dependencies',{k:len(v) for k,v in report['new'].items()},flush=True)
    assert not report['conflicts'],'Reconcile existing production identities before proceeding'

def insert(db,table,value):
    columns=sql.SQL(',').join(sql.Identifier(k) for k in value)
    db.execute(sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_record(NULL::{},%s)').format(sql.Identifier(table),columns,columns,sql.Identifier(table)),(Jsonb(value),))

def pinned():
    data=read(RUN/'local-export.json');plan=read(RUN/'preflight.json')
    assert not plan['conflicts'] and c.sha((RUN/'local-export.json').read_bytes())==plan['local_export_sha256']
    assert c.sha((BACKUP/'local-export.json').read_bytes())==plan['local_export_sha256']
    assert read(BACKUP/'production-preflight.json')==plan
    return data,plan

def upload():
    from google.cloud import storage
    from google.api_core.exceptions import PreconditionFailed
    data,plan=pinned();credentials=c.GcloudCredentials();credentials.refresh(None)
    bucket=storage.Client(project='artline-508319',credentials=credentials).bucket(c.BUCKET)
    def one(im):
        path=RUN/'uploads'/(im['artwork_id']+'.json')
        if path.exists():return read(path)
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert c.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'artwork-id':im['artwork_id'],'campaign':'russian-icon-images-20260921'}
        blob.cache_control='public,max-age=31536000,immutable';created=True
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except PreconditionFailed:blob.reload(timeout=30);created=False
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode(),'GCS object differs'
        result={'at':c.now(),**im,'bucket':c.BUCKET,'object':blob.name,'generation':blob.generation,'created':created,'md5_base64':blob.md5_hash}
        save(path,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for number,result in enumerate(pool.map(one,data['images']),1):
            if number%25==0 or number==217:print('Uploaded and checksum checked',number,'/ 217',flush=True)

def remap(table,value,plan):
    v=dict(value)
    for key,dependency in [('source_id','sources'),('institution_id','institutions'),('current_institution_id','institutions'),('artist_id','artists'),('collection_id','curated_collections')]:
        if v.get(key):v[key]=plan['maps'][dependency][v[key]]
    return v

def apply():
    data,plan=pinned();receipt=RUN/'applied.json'
    if receipt.exists():print('Already applied; use verify',flush=True);return
    for im in data['images']:
        uploaded=read(RUN/'uploads'/(im['artwork_id']+'.json'));assert uploaded['sha256']==im['sha256']
    ids=[w['id'] for w in data['artworks']];mids=[w['id'] for w in data['media_assets']]
    inserted=collections.Counter();collection_id=plan['collection_before']['id'];started=c.now()
    with connection(c.cloud_dsn(),readonly=False) as db:
        db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        db.execute('SELECT id FROM curated_collections WHERE id=%s FOR UPDATE',(collection_id,))
        # The complete new-record batch is atomic; changed preimages abort before writes.
        assert snapshot(db,ids,mids)==plan['before'],'Production target changed after preflight'
        current_collection=rows(db,'curated_collections','id=%s',(collection_id,))[0]
        # Other authorized collection jobs may append items. Capture the fresh locked preimage.
        previous_max=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(collection_id,)).fetchone()['n']
        assert current_collection['status']=='review' and current_collection['curator_kind']=='owner' and current_collection['institution_id'] is None
        for table in ('sources','institutions','artists'):
            for before in plan['existing'][table]:
                assert rows(db,table,'id=%s',(before['id'],))==[before],('Existing dependency changed',table)
            for new in plan['new'][table]:
                assert not rows(db,table,'id=%s OR slug=%s',(new['id'],new['slug'])),('New dependency appeared',table)
        backup=BACKUP/('locked-preimage-'+str(time.time_ns())+'.json')
        save(backup,{'at':c.now(),'scope':plan['before'],'existing_dependencies':plan['existing'],'collection':current_collection,'previous_max_position':previous_max,'new_dependency_ids':{t:[v['id'] for v in values] for t,values in plan['new'].items()},'new_artwork_ids':ids,'new_media_ids':mids,'new_relationship_ids':{t:[v['id'] for v in data[t] if 'id' in v] for t in TABLES[2:]}})
        for table in ('sources','institutions'):
            for v in plan['new'][table]:insert(db,table,v);inserted[table]+=1
        for table in ['media_assets','artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions','media_rights_evidence']:
            # Pipeline dependent inserts in their foreign-key order; transaction rollback stays atomic.
            with db.pipeline():
                for v in data[table]:insert(db,table,remap(table,v,plan));inserted[table]+=1
        with db.pipeline():
            for offset,v in enumerate(sorted(data['curated_collection_items'],key=lambda x:x['position']),1):
                mapped=remap('curated_collection_items',v,plan);mapped['position']=previous_max+offset
                insert(db,'curated_collection_items',mapped);inserted['curated_collection_items']+=1
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
        checks=db.execute('''SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND primary_media_id IS NOT NULL AND object_form='icon') valid,
          count(*) FILTER(WHERE artline_has_selection_evidence(id)) selected FROM artworks WHERE id=ANY(%s::uuid[])''',(ids,)).fetchone()
        assert checks=={'n':217,'valid':217,'selected':217},checks
        after_collection=rows(db,'curated_collections','id=%s',(collection_id,))[0]
    save(receipt,{'started_at':started,'committed_at':c.now(),'inserted':dict(inserted),'artwork_ids':ids,'checks':checks,'locked_preimage':str(backup),'locked_preimage_sha256':c.sha(backup.read_bytes()),'collection_after':after_collection,'published':False})
    print('Production transaction committed',dict(inserted),flush=True)

def verify():
    data,plan=pinned();receipt=read(RUN/'applied.json');ids=receipt['artwork_ids'];mids=[m['id'] for m in data['media_assets']]
    checks={};snapshot_hash=None
    with connection(c.cloud_dsn()) as db:
        actual=snapshot(db,ids,mids)
        for table in TABLES:
            expected=[remap(table,v,plan) for v in data[table]];observed=actual[table]
            if table=='curated_collection_items':
                expected=[{k:v for k,v in row.items() if k!='position'} for row in expected]
                observed=[{k:v for k,v in row.items() if k!='position'} for row in observed]
            canon=lambda values:sorted(json.dumps(v,sort_keys=True,ensure_ascii=False) for v in values)
            assert canon(expected)==canon(observed),('Production data differs',table)
            checks[table]=len(observed)
        for table in ('sources','institutions','artists'):
            for before in plan['existing'][table]:assert rows(db,table,'id=%s',(before['id'],))==[before]
            for new in plan['new'][table]:assert rows(db,table,'id=%s',(new['id'],))==[new]
        assert all(w['status']=='review' and w['published_at'] is None for w in actual['artworks'])
        assert all(w['rights_status']=='restricted' and w['verified_at'] is None and w['verified_by'] is None for w in actual['media_assets'])
        db_scope=db.execute('SELECT id::text,artline_has_selection_evidence(id) selected FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        assert all(w['selected'] for w in db_scope)
        save(BACKUP/'production-after.json',actual);snapshot_hash=c.sha((BACKUP/'production-after.json').read_bytes())
    # Ensure uploading has not changed any local catalogue data.
    with connection(r.DSN) as db:
        current=snapshot(db,ids,mids)
        assert all(current[t]==data[t] for t in TABLES),'Local data changed during promotion'
    save(RUN/'database-verification.json',{'at':c.now(),'passed':True,'rows':checks,'local_data_unchanged':True,'existing_production_dependencies_unchanged':True,'production_after_sha256':snapshot_hash,'review_status_preserved':True,'rights_status_preserved':True})
    print('Verified production rows and unchanged local data',checks,flush=True)

def verify_public():
    data,plan=pinned();byid={w['id']:w for w in data['artworks']};media={m['id']:m for m in data['media_assets']}
    def one(im):
        w=byid[im['artwork_id']];m=media[im['media_id']]
        response=requests.get(PUBLIC+'/api/backend/v1/atlas/artworks/'+w['id'],timeout=45)
        assert response.status_code==200,('Public detail',w['id'],response.status_code)
        d=response.json();assert d['id']==w['id'] and d['title']==w['title'] and d['media_url']==im['path']
        for field in ('status','date_display','date_precision','creation_year_start','creation_year_end','object_form','unlinked_creator_label','cultural_context'):assert d[field]==w[field],(w['id'],field)
        for field in ('rights_status','license_label','license_url','source_page_url','alt_text','attribution_text'):assert d[field]==m[field],(w['id'],field)
        assert d['display'] is None and len(d['creators'])==sum(v['artwork_id']==w['id'] for v in data['artwork_artists'])
        image_response=requests.get(PUBLIC+im['path'],timeout=45)
        assert image_response.status_code==200 and c.sha(image_response.content)==im['sha256'],('Public image',w['id'],image_response.status_code)
        return {'artwork_id':w['id'],'detail_status':response.status_code,'image_status':image_response.status_code,'sha256':im['sha256'],'rights_source_and_creator_context_verified':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=[]
        for n,result in enumerate(pool.map(one,data['images']),1):
            results.append(result)
            if n%25==0 or n==217:print('Production HTTP verified',n,'/ 217',flush=True)
    save(RUN/'public-verification.json',{'at':c.now(),'passed':True,'base_url':PUBLIC,'records':results})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['export','preflight','upload','apply','verify','verify_public']);args=parser.parse_args();globals()[args.stage]()
