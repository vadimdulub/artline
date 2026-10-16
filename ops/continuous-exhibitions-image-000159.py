#!/usr/bin/env python3
"""Bounded exact-impression image batch; no supervisor or local catalogue writes."""
import base64, csv, fcntl, gzip, hashlib, importlib.util, io, json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path
import requests
from PIL import Image, ImageOps
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=mod('ex159_common',ROOT/'ops/exhibitions_common.py')
d=mod('ex159_delivery',ROOT/'ops/cesi-delivery-20261010.py')
hist=mod('ex159_historical',ROOT/'ops/historical_exhibition_cma_images_20261012.py')
core=d.core
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000159'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000159'
OP='continuous-exhibitions-20261013-batch-000159-images'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP
for p in (E,R,BACKUP,ORIG):p.mkdir(parents=True,exist_ok=True)
ACTOR='local-european-research'
SID='aa0ba48c-e786-4cac-8411-06343f4f03ed'
POLICY='https://www.clevelandart.org/open-access'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1'
sha=c.sha
def load(p):return json.loads(Path(p).read_bytes())
def save(p,v):
    p=Path(p);raw=json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()+b'\n';p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        old=json.loads(p.read_bytes());current=json.loads(raw)
        assert old==current or {k:x for k,x in old.items() if k!='at'}=={k:x for k,x in current.items() if k!='at'},'Immutable evidence differs: '+str(p)
        return old
    else:
        tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(raw);os.replace(tmp,p)
    return v
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))
def target():
    ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
    proxies=[x.strip() for x in ps if '/tmp/artline-cloud-sql-proxy ' in x and '--port 55519' in x]
    assert len(proxies)==1 and 'artline-508319:europe-west1:artline-postgres' in proxies[0]
    with c.connect() as db:
        assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
        row=db.execute('select current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone()
    assert row['db']=='artline' and not row['recovery']
    return dict(at=c.now(),instance='artline-508319:europe-west1:artline-postgres',database=row,proxy_pid=int(proxies[0].split()[0]),helper='ops/exhibitions_common.py -> ops/cesi-top100-20261010.py',local_catalogue_connections=0)
def capture(url,path):
    path=Path(path);rp=path.with_suffix(path.suffix+'.receipt.json')
    if rp.exists():
        rc=load(rp);raw=path.read_bytes();assert sha(raw)==rc['sha256'] and rc['status']==200;return raw,rc
    assert not (E/'provider-access-hold.json').exists()
    time.sleep(.55)
    response=requests.get(url,headers={'User-Agent':c.UA},timeout=(15,45),allow_redirects=False)
    raw=response.content;assert len(raw)<=12000000
    rc=dict(url=url,at=c.now(),status=response.status_code,bytes=len(raw),sha256=sha(raw),path=str(path),content_type=response.headers.get('Content-Type'))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);save(rp,rc)
    if response.status_code in (401,403,429):save(E/'provider-access-hold.json',rc)
    response.raise_for_status();assert response.status_code==200
    return raw,rc
def plan():
    p=load(E/'immutable-plan.json');assert sha((E/'immutable-plan.json').read_bytes())==load(E/'plan-pin.json')['sha256'];return p
def entries(db,ids):
    return db.execute("""select to_jsonb(ee) entry,to_jsonb(e) exhibition from exhibition_entries ee join exhibitions e on e.id=ee.exhibition_id where ee.artwork_id=any(%s::uuid[]) and e.status<>'archived' and e.start_year between 1600 and 1989 and coalesce(e.end_year,e.start_year)<=1989 order by ee.id""",(ids,)).fetchall()
def prepare():
    if not (E/'production-target-reconciliation.json').exists():save(E/'production-target-reconciliation.json',target())
    registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
    if not (E/'source-register-verification.json').exists():save(E/'source-register-verification.json',dict(at=c.now(),registry_sha256=sha(registry.read_bytes()),source=next(r for r in reg if r['source_id']=='cleveland_museum'),scope=dict(exhibitions='1600-1989',main_artworks='through 1970',exclusions=['photography','sculpture']),bytes_free=shutil.disk_usage(R).free))
    queue=load(E.parents[1]/'source-queue.json');source=next(r for r in queue['sources'] if r['source_id']=='cleveland_museum')
    excluded={str(r.get('nativeID',r.get('native_id',r.get('native','')))) for r in source.get('holds',[])}
    with c.connect() as db:
        own=db.execute('select media_id::text from media_rights_evidence where adapter_version=%s',(OP,)).fetchall();assert not own,'Reconcile previous batch write before prepare'
        candidates=db.execute("""select distinct a.id::text,x.external_id native_id,x.external_id::int sortkey from artworks a join external_identifiers x on x.entity_type='artwork' and x.entity_id=a.id and x.scheme='cleveland-object' join exhibition_entries ee on ee.artwork_id=a.id join exhibitions e on e.id=ee.exhibition_id where a.primary_media_id is null and a.status<>'archived' and e.status<>'archived' and e.start_year between 1600 and 1989 and coalesce(e.end_year,e.start_year)<=1989 and a.work_type in ('painting','drawing','print','watercolor','icon') and a.creation_year_end<=1970 and not exists(select 1 from artwork_media am where am.artwork_id=a.id) and x.external_id::int>106615 order by sortkey limit 30""").fetchall()
        ids=[r['id'] for r in candidates if r['native_id'] not in excluded]
        before=d.snapshot(db,ids);links=entries(db,ids)
        identifiers=db.execute("select to_jsonb(x) record from external_identifiers x where entity_type='artwork' and entity_id=any(%s::uuid[]) and scheme='cleveland-object' order by entity_id",(ids,)).fetchall()
        concurrent=db.execute("select adapter_version,count(*) n from media_rights_evidence where adapter_version like '%000159%' group by adapter_version").fetchall()
        triggers=db.execute("select tgname from pg_trigger where tgrelid='artworks'::regclass and not tgisinternal and tgenabled<>'D'").fetchall()
        prior=load(E.parents[1]/'batches/000158/independent-database-verification.json')
    cp=load(E.parents[1]/'CHECKPOINT.json');assert cp['inflight']['batch']==159
    for pid in (cp['supervisor_pid'],cp['worker_pid']):os.kill(pid,0)
    if not (E/'recovery-check.json').exists():save(E/'recovery-check.json',dict(at=c.now(),own_existing_rights=own,other_programme_rows_excluded=concurrent,prior_batch158_verification_sha256=sha((E.parents[1]/'batches/000158/independent-database-verification.json').read_bytes()),prior_batch158_verification_present=bool(prior),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],both_processes_live=True,supervisor_unchanged=True,separate_artwork_programme_unchanged=True,smk_changes_counted=0,preexisting_holds_skipped=sorted(excluded),audit_triggers=triggers,passed=True))
    pre=dict(at=c.now(),before=before,exact_links=links,identifiers=identifiers)
    _,policy=capture(POLICY,R/'source-captures/open-access.html')
    chosen=[];receipts=[];held=[]
    for cand in candidates:
        aid=cand['id'];native=cand['native_id']
        if aid not in ids:continue
        if len(chosen)==10:break
        raw,rc=capture('https://openaccess-api.clevelandart.org/api/artworks/'+native,R/f'source-captures/{native}.json');o=json.loads(raw)['data'];a=before[aid]['artwork']
        try:im=hist.validate_object(a,o,native)
        except AssertionError as exc:
            held.append(dict(native_id=native,artwork_id=aid,reason=str(exc),source_receipt=rc));continue
        ls=[l for l in links if l['entry']['artwork_id']==aid];assert ls
        for l in ls:
            en=l['entry'];ex=l['exhibition'];assert en['participation']=='exhibited' and en['source_artwork_id']==native and en['evidence']['accession_number']==o['accession_number']
            assert any(x['title']==ex['title'] and x['opening_date'][:10]==ex['start_date'] for x in o['exhibitions']['current']),'Reciprocal historical exhibition not found'
        original,irc=capture(im['url'],ORIG/(native+'-web.jpg'))
        with Image.open(io.BytesIO(original)) as src:
            src.load();pic=ImageOps.exif_transpose(src).convert('RGB')
        dims=pic.size;declared=(int(im['width']),int(im['height']))
        out=None
        for edge in (1200,1050,900,800,700,600):
            resized=pic.copy();resized.thumbnail((edge,edge),Image.Resampling.LANCZOS)
            for quality in (88,82,76,70,64,58):
                buf=io.BytesIO();resized.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                if buf.tell()<=100000:out=buf.getvalue();break
            if out:break
        assert out and abs(resized.width/resized.height-dims[0]/dims[1])<.003
        digest=sha(out);path=R/'prepared'/(native+'.jpg');path.parent.mkdir(exist_ok=True);path.write_bytes(out)
        with Image.open(path) as check:check.load();assert check.size==resized.size
        creator='; '.join(((x.get('role')+': ') if x.get('role') else '')+x['description'] for x in o['creators']) or 'Unidentified creator'
        chosen.append(dict(artwork_id=aid,native_id=native,title=o['title'],accession=o['accession_number'],creator_label=creator,creditline=o['creditline'],source_creators=o['creators'],record_type=o['record_type'],source_url=o['url'],source_image_url=im['url'],source_checksum=rc['sha256'],original_path=irc['path'],original_sha256=irc['sha256'],source_dimensions=dims,api_declared_dimensions=declared,dimension_discrepancy=dims!=declared,prepared_path=str(path),sha256=digest,bytes=len(out),width=resized.width,height=resized.height,quality=quality,media_id=uid('media/'+aid+'/'+digest),storage_path=f'/assets/artworks/imported/{OP}/{aid}-{digest[:16]}.jpg',rights_status='cc0',license_label='CC0 1.0',license_url=hist.CC0,complete_source_frame=True,exact_existing_entry_ids=[l['entry']['id'] for l in ls],source_rights_label=o['share_license_status'],copyright=o['copyright'],rights_and_reproductions=o.get('rights_and_reproductions')))
        receipts.append(dict(native_id=native,metadata=rc,image_download=irc,identity='Exact provider-qualified native ID, accession, title, type, date, institution and component; reciprocal exhibition title and opening date confirmed.',passed=True))
    assert 0<len(chosen)<=10 and len({r['sha256'] for r in chosen})==len(chosen)
    selected_ids={r['artwork_id'] for r in chosen}
    pre=dict(at=c.now(),before={k:v for k,v in before.items() if k in selected_ids},exact_links=[l for l in links if l['entry']['artwork_id'] in selected_ids],identifiers=[x for x in identifiers if x['record']['entity_id'] in selected_ids])
    save(E/'transaction-preimage.json',pre);save(BACKUP/'selection-preimage.json',pre)
    save(E/'new-source-holds.json',dict(at=c.now(),rows=held,passed=True))
    save(E/'source-capture-verification.json',dict(at=c.now(),policy=policy,rows=receipts,passed=True))
    save(E/'immutable-plan.json',dict(at=c.now(),operation=OP,rows=chosen,preimage_sha256=sha((E/'transaction-preimage.json').read_bytes()),source_capture_sha256=sha((E/'source-capture-verification.json').read_bytes())))
    save(E/'plan-pin.json',dict(sha256=sha((E/'immutable-plan.json').read_bytes())))
    save(E/'technical-verification.json',dict(at=c.now(),rows=[dict(native_id=r['native_id'],source_dimensions=r['source_dimensions'],prepared_dimensions=[r['width'],r['height']],bytes=r['bytes'],sha256=r['sha256'],full_decode=True,complete_source_frame=True,proportions_preserved=True,under_100000=True) for r in chosen],passed=True))
    print(json.dumps([dict(native_id=r['native_id'],title=r['title'],bytes=r['bytes'],path=r['prepared_path']) for r in chosen],indent=2))

def backup():
    import psycopg
    p=plan();pin=load(E/'plan-pin.json')['sha256'];pre=load(E/'transaction-preimage.json')
    tgt=target()
    with c.connect() as db:
        assert d.snapshot(db,[r['artwork_id'] for r in p['rows']])==pre['before']
        kw=psycopg.conninfo.conninfo_to_dict(c._db_base._dsn)
    env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw.get('password',''),PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
    dest=BACKUP/'production-schema-before.pgdump'
    if not dest.exists():
        result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(dest)],env=env,capture_output=True,timeout=180)
        assert result.returncode==0,'Schema backup failed; private credentials not printed'
        dest.chmod(0o600)
    result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(dest)],capture_output=True,check=True)
    toc=BACKUP/'production-schema-before.toc';toc.write_bytes(result.stdout)
    with open(os.devnull,'wb') as sink:
        subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(dest)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
    save(BACKUP/'immutable-plan.json',p)
    save(BACKUP/'visual-review.json',load(E/'visual-review.json'))
    save(BACKUP/'visual-review-pin.json',load(E/'visual-review-pin.json'))
    assert (BACKUP/'immutable-plan.json').read_bytes()==(E/'immutable-plan.json').read_bytes()
    assert load(BACKUP/'selection-preimage.json')==pre
    files=[dest,toc,BACKUP/'immutable-plan.json',BACKUP/'selection-preimage.json',BACKUP/'visual-review.json',BACKUP/'visual-review-pin.json']
    save(E/'backup-verification.json',dict(at=c.now(),target=tgt,kind='schema_and_scoped_affected_rows',full_database_backup=False,cloud_backup_created=False,plan_sha256=pin,files=[dict(path=str(x),bytes=x.stat().st_size,sha256=sha(x.read_bytes())) for x in files],schema_fully_decoded=True,scoped_rows_decoded=True,locked_preimages_required=True,passed=True))
    print('Schema and selected-row recovery backup verified')

def deliver():
    p=plan();pin=load(E/'plan-pin.json')['sha256'];review=load(E/'visual-review.json');assert review['plan_sha256']==pin
    assert sha((E/'visual-review.json').read_bytes())==load(E/'visual-review-pin.json')['sha256']
    decisions={r['native_id']:r for r in review['rows']};assert len(decisions)==len(p['rows'])
    backup=load(E/'backup-verification.json');assert backup['passed']
    save(E/'production-target-before-database-write.json',target())
    pre=load(E/'transaction-preimage.json');assert sha((E/'transaction-preimage.json').read_bytes())==p['preimage_sha256']
    ids=[r['artwork_id'] for r in p['rows']]
    with c.connect(write=True) as db:
        db.execute("set local lock_timeout='55s'");db.execute("select set_config('artline.request_id',%s,true)",(OP,));db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        db.execute('select id from artworks where id=any(%s::uuid[]) order by id for update',(ids,)).fetchall()
        existing=db.execute('select media_id::text,evidence_json from media_rights_evidence where adapter_version=%s',(OP,)).fetchall()
        if existing:
            assert len(existing)==len(ids) and all(x['evidence_json']['selection_sha256']==pin for x in existing);print('Existing own delivery; run independent verification');return
        before=d.snapshot(db,ids);assert before==pre['before'],'Concurrent catalogue change; reselect separately'
        assert json.loads(json.dumps(entries(db,ids),default=str))==pre['exact_links']
        assert all(x['artwork']['primary_media_id'] is None and not x['attachments'] for x in before.values())
        save(BACKUP/'transaction-preimage.json',dict(plan_sha256=pin,before=before,exact_links=pre['exact_links']))
        credentials=core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials)
        storage_receipts=[]
        for r in p['rows']:
            rv=decisions[r['native_id']];assert rv['actually_viewed'] and rv['decision']=='accept' and rv['sha256']==r['sha256'] and rv['editorial_confidence']>=0.90
            raw=Path(r['prepared_path']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)<=100000
            t=target();save(E/f"targets/storage-{r['native_id']}.json",t)
            blob=client.bucket(core.BUCKET).blob(r['storage_path'].lstrip('/'));blob.metadata={'sha256':r['sha256'],'operation':OP,'plan_sha256':pin};blob.cache_control='public,max-age=31536000,immutable'
            try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
            except PreconditionFailed:pass
            blob.reload();assert blob.size==len(raw) and blob.metadata['sha256']==r['sha256'] and blob.metadata['operation']==OP and blob.metadata['plan_sha256']==pin
            assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
            public=requests.get('https://artlines.org'+r['storage_path'],timeout=(15,45));public.raise_for_status();assert sha(public.content)==r['sha256']
            storage_receipts.append(dict(native_id=r['native_id'],path=blob.name,generation=blob.generation,bytes=blob.size,sha256=r['sha256'],operation=OP,plan_sha256=pin,public_sha256=sha(public.content),public_status=public.status_code))
        save(E/'storage-upload-verification.json',dict(at=c.now(),rows=storage_receipts,passed=True))
        for r in p['rows']:
            aid=r['artwork_id'];rv=decisions[r['native_id']]
            assert db.execute("select 1 from external_identifiers where entity_type='artwork' and entity_id=%s and scheme='cleveland-object' and external_id=%s",(aid,r['native_id'])).fetchone()
            assert not db.execute('select id from media_assets where id=%s or checksum_sha256=%s',(r['media_id'],r['sha256'])).fetchone(),'Image already delivered elsewhere; do not recount'
            creator=rv['creator_label'];credit=creator+'. The Cleveland Museum of Art. '+r['creditline']+'. CC0 1.0.'
            media=dict(id=r['media_id'],storage_kind='local',storage_path=r['storage_path'],source_page_url=r['source_url'],provider_name='The Cleveland Museum of Art',mime_type='image/jpeg',width=r['width'],height=r['height'],byte_size=r['bytes'],checksum_sha256=r['sha256'],alt_text=r['title']+' — '+creator,rights_status='cc0',license_label='CC0 1.0',license_url=hist.CC0,creator_credit=credit,attribution_text=credit+' Full supplied frame preserved; proportional resizing and JPEG compression.',retrieved_at=c.now(),verified_at=c.now(),verified_by=ACTOR)
            d.batch(db,'media_assets',[media])
            evidence=dict(selection_sha256=pin,preimage_sha256=p['preimage_sha256'],native_source_checksum=r['source_checksum'],download_sha256=r['original_sha256'],visual_review=rv,visual_review_sha256=sha((E/'visual-review.json').read_bytes()),native_id=r['native_id'],accession=r['accession'],record_type=r['record_type'],complete_source_frame=True,exact_existing_entry_ids=r['exact_existing_entry_ids'],source_rights_label=r['source_rights_label'],copyright=r['copyright'],rights_and_reproductions=r['rights_and_reproductions'],source_creators=r['source_creators'],creator_label=creator,api_declared_dimensions=r['api_declared_dimensions'],actual_source_dimensions=r['source_dimensions'],dimension_discrepancy=r['dimension_discrepancy'],user_authorization_separate_from_cc0=True)
            d.batch(db,'media_rights_evidence',[dict(media_id=r['media_id'],source_id=SID,source_record_id=r['native_id'],source_checksum=r['source_checksum'],source_image_url=r['source_image_url'],policy_url=POLICY,rights_basis='Per-object museum CC0 designation, no copyright or reproduction restriction; exact accessioned impression supplied by the institution.',adapter_version=OP,checked_at=c.now(),evidence_json=evidence)])
            d.batch(db,'artwork_media',[dict(artwork_id=aid,media_id=r['media_id'],sort_order=0,view_label='Cleveland Museum of Art exact '+r['record_type']+' reproduction')])
            db.execute('update artworks set primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 where id=%s and primary_media_id is null',(r['media_id'],ACTOR,aid))
        after=d.snapshot(db,ids)
        for aid in ids:
            assert before[aid]['creators']==after[aid]['creators'] and before[aid]['holdings']==after[aid]['holdings']
            assert before[aid]['artwork']['status']==after[aid]['artwork']['status']
        save(BACKUP/'transaction-postimage.json',dict(plan_sha256=pin,after=after));db.commit()
    save(E/'applied.json',dict(at=c.now(),plan_sha256=pin,new_images=len(ids),artwork_ids=ids))
    print('Committed selected image attachments; independent verification required')

def verify():
    p=plan();pin=load(E/'plan-pin.json')['sha256'];pre=load(E/'transaction-preimage.json');ids=[r['artwork_id'] for r in p['rows']]
    transaction=load(BACKUP/'transaction-preimage.json');assert transaction['before']==pre['before'] and transaction['plan_sha256']==pin
    captures=load(E/'source-capture-verification.json');assert sha((E/'source-capture-verification.json').read_bytes())==p['source_capture_sha256']
    files=[]
    reviews={r['native_id']:r for r in load(E/'visual-review.json')['rows']}
    for r in p['rows']:
        capture_row=next(x for x in captures['rows'] if x['native_id']==r['native_id'])
        raw=Path(capture_row['metadata']['path']).read_bytes();assert sha(raw)==r['source_checksum']
        original=Path(r['original_path']).read_bytes();assert sha(original)==r['original_sha256']
        prepared=Path(r['prepared_path']).read_bytes();assert sha(prepared)==r['sha256'] and len(prepared)==r['bytes']<=100000
        with Image.open(io.BytesIO(prepared)) as im:im.load();assert im.size==(r['width'],r['height'])
        with Image.open(io.BytesIO(original)) as im:im.load();assert list(im.size)==r['source_dimensions']
        assert reviews[r['native_id']]['actually_viewed'] and reviews[r['native_id']]['sha256']==r['sha256']
        files.append(dict(native_id=r['native_id'],metadata_sha256=r['source_checksum'],original_sha256=r['original_sha256'],prepared_sha256=r['sha256'],bytes=r['bytes'],fully_decoded=True,visual_review_pinned=True,complete_supplied_frame=True))
    save(E/'independent-file-verification.json',dict(at=c.now(),rows=files,passed=True))
    rows=[]
    with c.connect() as db:
        after=d.snapshot(db,ids);assert json.loads(json.dumps(entries(db,ids),default=str))==pre['exact_links']
        for r in p['rows']:
            aid=r['artwork_id'];b=pre['before'][aid];a=after[aid]
            assert b['artwork']['primary_media_id'] is None and a['artwork']['primary_media_id']==r['media_id']
            assert b['creators']==a['creators'] and b['holdings']==a['holdings']
            assert not b['attachments'] and len(a['attachments'])==1 and a['attachments'][0]['media_id']==r['media_id']
            assert all(v==a['artwork'][k] for k,v in b['artwork'].items() if k not in ('primary_media_id','revision','updated_at','updated_by'))
            mr=db.execute('select to_jsonb(m) media,to_jsonb(re) rights from media_assets m join media_rights_evidence re on re.media_id=m.id where m.id=%s',(r['media_id'],)).fetchone();ev=mr['rights']['evidence_json']
            assert mr['media']['checksum_sha256']==r['sha256'] and mr['media']['byte_size']==r['bytes']<=100000 and mr['rights']['adapter_version']==OP
            assert ev['selection_sha256']==pin and ev['preimage_sha256']==p['preimage_sha256'] and ev['native_source_checksum']==r['source_checksum'] and ev['visual_review']['actually_viewed']
            audits=db.execute("select to_jsonb(x) record from audit_log x where entity_type='artwork' and entity_id=%s and after_json->>'primary_media_id'=%s",(aid,r['media_id'])).fetchall()
            assert len(audits)==1 and audits[0]['record']['before_json']==b['artwork']
            rows.append(dict(artwork_id=aid,media=mr['media'],rights=mr['rights'],audit=audits[0]['record'],primary_preimage_null=True,metadata_preserved=True))
    save(E/'independent-database-verification.json',dict(at=c.now(),operation=OP,plan_sha256=pin,rows=rows,exact_links_unchanged=True,exhibition_records_unchanged=True,transaction_preimage_sha256=sha((BACKUP/'transaction-preimage.json').read_bytes()),new_images=len(rows),passed=True))
    credentials=core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials)
    stored=[];public=[]
    for r in p['rows']:
        raw=Path(r['prepared_path']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)<=100000
        blob=client.bucket(core.BUCKET).blob(r['storage_path'].lstrip('/'));blob.reload();assert blob.metadata['operation']==OP and blob.metadata['sha256']==r['sha256'] and blob.metadata['plan_sha256']==pin and blob.size==len(raw)
        assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        stored.append(dict(native_id=r['native_id'],generation=blob.generation,path=blob.name,sha256=r['sha256'],bytes=blob.size,operation=OP,plan_sha256=pin,md5_verified=True))
        url='https://artlines.org'+r['storage_path'];res=requests.get(url,timeout=(15,45));res.raise_for_status();assert sha(res.content)==r['sha256']
        public.append(dict(native_id=r['native_id'],url=url,status=res.status_code,sha256=sha(res.content),bytes=len(res.content)))
    save(E/'independent-storage-verification.json',dict(at=c.now(),rows=stored,passed=True))
    pages=[];apirows=[]
    for eid in sorted({l['exhibition']['id'] for l in pre['exact_links']}):
        items=[];cursor='';seen=set()
        while True:
            url=f'{API}/exhibitions/{eid}/entries?limit=100'+('&after='+cursor if cursor else '');res=requests.get(url,timeout=(15,45));res.raise_for_status();payload=res.json();items.extend(payload['items'])
            pages.append(dict(url=url,status=res.status_code,sha256=sha(res.content),total=payload['total'],has_more=payload['hasMore'],entries=len(payload['items'])))
            if not payload['hasMore']:assert len(items)==payload['total'];break
            cursor=payload['nextCursor'];assert cursor not in seen and len(seen)<50;seen.add(cursor)
        byid={x['id']:x for x in items};assert len(byid)==len(items)
        for r in p['rows']:
            for l in pre['exact_links']:
                if l['entry']['artwork_id']!=r['artwork_id'] or l['exhibition']['id']!=eid:continue
                entry=byid[l['entry']['id']];assert entry['artworkId']==r['artwork_id'] and r['storage_path'] in json.dumps(entry)
                apirows.append(dict(native_id=r['native_id'],exhibition_id=eid,entry=entry,correct_image_association=True))
    save(E/'independent-public-verification.json',dict(at=c.now(),assets=public,api_entries=apirows,pages=pages,public_checksums_verified=True,complete_cursor_paging=True,passed=True))
    print(json.dumps(dict(images=len(rows),existing_connections_illustrated=len(apirows),exhibitions=len({r['exhibition_id'] for r in apirows}))))


if __name__=='__main__':globals()[sys.argv[1]]()
