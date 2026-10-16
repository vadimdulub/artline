#!/usr/bin/env python3
"""One bounded Ireland continuation; no supervisor and no local catalogue writes."""
import csv, fcntl, gzip, importlib.util, inspect, json, os, re, subprocess, sys
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('metadata73','india-300-delivery-20261011.py')
native=mod('ireland73','museum-expansion-ireland-20261006.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000178'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000178'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000178'
OP='continuous-ireland-20261011-b000178';PHASE='ireland-paintings'
FIELD='continuous_ireland_object_evidence_b000178'
MID='8aa52843-c70a-4f48-8bdd-9965d04339ae';MUSEUM='National Gallery of Ireland'
SCHEME='ngi-object';SLUG='national-gallery-ireland'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'ireland':[SCHEME]};h.museums=lambda:{MUSEUM:(SLUG,'https://www.nationalgallery.ie/')}
for p in [E,R,S,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
    p=E/name
    if p.exists():return h.load(p)
    h.save(p,value);return value
def target(write=False):
    assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
    actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
    assert actual=='artline-508319:europe-west1:artline-postgres'
    commands=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines()
    proxy=[x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x];assert len(proxy)==1
    with h.connect() as db:
        state=dict(db.execute("SELECT current_database() AS database,pg_is_in_recovery() AS recovery,current_setting('default_transaction_read_only') AS read_only").fetchone());assert state['database']=='artline' and not state['recovery'] and state['read_only']=='on'
    return dict(at=h.now(),connection_name=actual,proxy_command=proxy[0],database=state,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0,shared_ingestion_lock='artline-curated-ingestion')
def capture(url,key):
    p=E/(key+'-capture.json')
    if p.exists():
        rc=h.load(p);raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'];return raw,rc
    import datetime,time
    # Official source robots.txt specifies Crawl-delay:30. Cached captures
    # require no requests; timestamp persistence also respects restart delay.
    prior=[h.load(x)['retrieved_at'] for x in E.glob('ireland-*-capture.json')]
    if prior:
        elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(max(prior))).total_seconds()
        if elapsed<30:time.sleep(30-elapsed)
    try:r=requests.get(url,timeout=(15,40),headers={'User-Agent':'Artline selected collection research/1.0'})
    except requests.RequestException as exc:
        save(key+'-failure.json',dict(at=h.now(),url=url,error_type=type(exc).__name__,automatic_retries=0,next_action='Checkpoint transient failure; switch source, no unchanged retry.'));raise
    raw=r.content;path=S/(key+'.html');path.write_bytes(raw)
    rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=h.now(),body_path=str(path),sha256=h.sha(raw),bytes=len(raw),retry_after=r.headers.get('Retry-After'))
    save(key+'-capture.json',rc);return raw,rc
def identity(db,rows):
    checks=[]
    for r in rows:
        oid=r['source_id'];url=r['source_url'];acc=r['accession_number'];forms=[acc,acc.replace('.',' '),acc.replace('NGI.','')]
        exact=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((external_id=%s AND (scheme ILIKE '%%ngi%%' OR scheme ILIKE '%%ireland%%')) OR canonical_url=%s)",(oid,url))]
        citations=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND (source_url=%s OR (source_record_id=%s AND source_url LIKE 'https://onlinecollection.nationalgallery.ie/%%'))",(url,oid))]
        accession=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=%s OR (current_institution_id=%s AND accession_number=ANY(%s))',(acc,MID,forms))]
        titles=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=%s OR lower(title)=lower(%s) OR lower(alternate_title)=lower(%s)',(h.norm(r['title']),r['title'],r['title']))]
        assert not(exact or citations or accession or titles),('Replan object collision',oid)
        checks.append(dict(source_id=oid,native=exact,citations=citations,accessions=accession,global_titles=titles,decision='no_exact_identity_found'))
    return checks
def no_collision(db,rows):identity(db,rows)
h.no_collision=no_collision
original_dates=h.dates
def dates(r):
    out=original_dates(r)
    return (out[0],out[1],'century') if r.get('native_date_precision')=='century' else out
h.dates=dates
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production enrichment batch 178: selected exact Irish collection objects with original creator qualifications; new works remain review.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=25 and all(not r['before'] for r in rows)")
code=code.replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace("WHERE entity_type='artwork' AND scheme=ANY(%s)\",(list({r['scheme'] for r in rows}),)","WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)\",(list({r['scheme'] for r in rows}),[r['source_id'] for r in rows])")
exec(compile(code,__file__,'exec'),h.__dict__)
def apply():
    p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
    with h.connect() as db:
        present=h.snapshot(db,ids)
        notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
        if present:
            assert len(present)==len(notes)==len(ids) and all(x['pin']==pin for x in notes)
            pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={}
            print('Own committed plan reconciled; no replay writes.');return
    rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
    for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
    assert h.load(E/'prewrite-verification.json')['passed']
    save('production-target-before-metadata-write.json',checked);h.apply(PHASE)

def preflight():
    from PIL import Image
    paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
    for p in paths:p.read_text()
    registry=list(csv.DictReader(paths[1].open()));q=h.load(paths[6]);assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in q['sources']}
    save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),read_complete=True) for p in paths],complete_original_registry=registry,registry_rows=111,supplementary_review_not_replacement=True,local_catalogue_connections=0))
    save('source-queue-preimage.json',q)
    ledgers=[]
    for name in ['000174/inherited-holds-verification.json','000175/failures-and-holds-final.json','000176/source-access-holds.json','000177/source-access-holds.json','000177/CHECKPOINT.json','000126/research-dispositions.json']:
        p=E.parent/name;p.read_text();ledgers.append(dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),read_complete=True))
    save('inherited-holds-verification.json',dict(at=h.now(),ledgers=ledgers,ireland=next(x for x in q['sources'] if x['source_id']=='national_gallery_ireland'),provider_holds_preserved=True))
    save('production-target-reconciliation.json',target())
    with h.connect() as db:
        previous=h.load(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(previous['after']))==previous['after']
        own=[dict(x) for x in db.execute('SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE field_name=%s',(FIELD,))]
        assert not own or (E/PHASE/'plan.json.gz').exists(),'Unknown prior writes require reconciliation'
    save('batch107-live-reconciliation.json',dict(at=h.now(),rows=len(previous['after']),snapshot_equal=True,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes()),prior_increments_counted=0))
    save('own-write-reconciliation.json',dict(at=h.now(),own_citations=own,unknown_writes=0))
    pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=h.load(pp);assert len(plan['rows'])==188
    evidence=[]
    for row in plan['rows']:
        source=ROOT/row['source_record_reference'];assert h.sha(source.read_bytes())==row['source_record_sha256']
        for key in ['receipt','manifest_receipt']:
            rc=row[key];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
        visual=row['continuation_visual_evidence'];decision=ROOT/visual['decision_reference'];assert h.sha(decision.read_bytes())==visual['decision_sha256']
        im=plan['images'][row['artwork_id']];assert im['sha256']==visual['image_sha256'];image=Path(im['local_path']);assert h.sha(image.read_bytes())==im['sha256'] and image.stat().st_size<=100000
        with Image.open(image) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
        evidence.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_record_reference=row['source_record_reference'],source_sha256=row['source_record_sha256'],prior_actual_visual_review=visual,derivative_sha256=im['sha256']))
    with h.connect() as db:
        live=h.snapshot(db,[x['artwork_id'] for x in plan['rows']]);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(list(live),))]
        media=[dict(x) for x in db.execute('SELECT id::text,checksum_sha256 FROM media_assets WHERE id=ANY(%s::uuid[])',([im['media_id'] for im in plan['images'].values()],))]
    digest=h.sha(pp.read_bytes());assert len(live)==len(cit)==188 and all(x['plan_sha256']==digest for x in cit)
    hashes={x['id']:x['checksum_sha256'] for x in media}
    assert all(live[x['artwork_id']]['artwork']['primary_media_id']==plan['images'][x['artwork_id']]['media_id'] and live[x['artwork_id']]['artwork']['status']!='archived' and hashes[plan['images'][x['artwork_id']]['media_id']]==plan['images'][x['artwork_id']]['sha256'] for x in plan['rows'])
    save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=digest,checksum_verified_prior_reviews=evidence,new_visual_review_claim=False,physical_date_holds_preserved=['80082','80437','81054'],source_citations=cit,live_rows=live,media_checks=media))
    cp=h.load(paths[5]);assert cp['inflight']['batch']==178;os.kill(cp['supervisor_pid'],0)
    save('external-continuation-verification.json',dict(at=h.now(),supervisor_pid=cp['supervisor_pid'],pid_alive=True,current_batch=178,external_supervisor_owns_continuation=True,created_supervisors=0,subagents=0,supervisor_not_edited=True))
    print('French reserve:188 already delivered, zero unimported. Batch107 and production target verified.',flush=True)

def discover():
    if (E/'discovery.json').exists():return
    from urllib.robotparser import RobotFileParser
    raw,rc=capture(native.SITE+'/robots.txt','ireland-robots');assert rc['status'] in [200,404]
    rp=RobotFileParser();rp.parse(raw.decode().splitlines() if rc['status']==200 else [])
    q=h.load(E/'source-queue-preimage.json');ir=next(x for x in q['sources'] if x['source_id']=='national_gallery_ireland');page=ir['resume_cursor']['next_page'];assert page==40
    url=ir['resume_cursor']['next_url'];assert rp.can_fetch('*',url)
    raw,rc=capture(url,'ireland-index-40');assert rc['status']==200
    rows,next_url=native.index_rows(raw,url)
    with h.connect() as db:
        known,titles,inventories=native.existing_keys(db,MID)
        names=[dict(x) for x in db.execute("SELECT id::text,display_name name,birth_year,death_year FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias name,a.birth_year,a.death_year FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'")]
    records=[];held=[]
    for idx in rows:
        reason=None
        if idx['source_id'] in known:reason='existing_source_identity'
        elif h.norm(idx['title']) in titles:reason='existing_institution_title_requires_version_review'
        elif not native.creation_date(idx['date']):reason='creation_date_review'
        if reason:held.append(dict(index=idx,reason=reason));continue
        assert rp.can_fetch('*',idx['url'])
        key='ireland-object-'+idx['source_id']
        if (E/(key+'-failure.json')).exists():
            held.append(dict(index=idx,reason='transient_source_failure_checkpointed_no_retry',failure=h.load(E/(key+'-failure.json'))));break
        try:body,cap=capture(idx['url'],key)
        except requests.RequestException:
            held.append(dict(index=idx,reason='transient_source_failure_checkpointed_no_retry',failure=h.load(E/(key+'-failure.json'))));break
        if cap['status']!=200:held.append(dict(index=idx,reason='provider_access_hold',capture=cap));break
        parsed=native.fields(body);facts,reason=native.facts(parsed,idx)
        if not reason and native.inventory_keys(facts['accession'])&inventories:reason='existing_inventory'
        matches={x['id']:x for x in names if h.norm(x['name'])==h.norm(idx['creator'])}
        if not reason and len(matches)!=1:reason='creator_requires_global_reconciliation'
        if reason:held.append(dict(index=idx,reason=reason,parsed=parsed,capture=cap,creator_matches=matches));continue
        records.append(dict(index=idx,parsed=parsed,facts=facts,capture=cap,artist=next(iter(matches.values()))))
    with h.connect() as db:
        collisions=[dict(x) for x in native.title_collisions(db,records)]
    collision_ids={h.norm(x[k]) for x in collisions for k in ['title','alternate_title'] if x[k]}
    eligible=[]
    for r in records:
        if h.norm(r['facts']['title']) in collision_ids:held.append(dict(**r,reason='global_title_collision_requires_physical_version_review'))
        else:eligible.append(r)
    save('global-title-reconciliation.json',dict(at=h.now(),collisions=collisions,selected=len(eligible)))
    save('discovery.json',dict(at=h.now(),page=page,index_capture=rc,rows=rows,records=eligible,held=held,next_url=next_url,unrequested_native_ids=[x['source_id'] for x in rows if x['source_id'] not in {v['index']['source_id'] for v in eligible+held}]))
    print(json.dumps(dict(page=page,rows=len(rows),candidates=len(eligible),held=len(held),next_url=next_url)),flush=True)
    for x in eligible:print(x['index']['source_id'],x['facts']['title'],x['facts']['date_display'],x['artist']['name'],x['facts']['accession'],flush=True)

def stage():
    discovery=h.load(E/'discovery.json');records=[]
    for x in discovery['records']:
        f=x['facts'];rc=x['capture'];parsed=native.fields(Path(rc['body_path']).read_bytes());assert parsed==x['parsed'];facts,reason=native.facts(parsed,x['index']);assert not reason and facts==f and f['last']<=1970
        records.append(dict(provider='ireland',source_id=x['index']['source_id'],source_url=f['source_url'],museum=MUSEUM,title=f['title'],creator_label=x['index']['creator'],date_display=f['date_display'],year_start=f['first'],year_end=f['last'],native_date_precision=f['date_precision'],date_decision='eligible',accession_number=f['accession'],source_type=f['work_type'],medium=f['medium'],dimensions=f['dimensions'],credit=parsed['fields']['Credit Line'],evidence_file=rc['body_path'],evidence=rc,verified_artist_id=x['artist']['id'],raw=dict(original_title=f['title'],index=x['index'],index_capture=discovery['index_capture'],native_fields=parsed,measurements=f['dimensions']),identity_review=f['holding_basis']))
    assert 0<len(records)<=25
    with h.connect() as db:checks=identity(db,records)
    save('global-identity-reconciliation.json',dict(at=h.now(),checks=checks))
    h.save(E/PHASE/'source-records.json.gz',records);h.plan(PHASE)
    p,pin=h.pinned(PHASE);assert len(p['records'])==len(records) and not p['held'] and not p['new_institutions'] and all(not r['before'] and r['artist_id'] for r in p['records'])
    save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,new_objects=len(records),source_index_native_identity_dates_dimensions_creator_and_credit_checked=True,existing_editorial_fields_preserved=True,primary_image_replacements=0))
    save('image-research-decision.json',dict(at=h.now(),native_image_host='nationalgalleryimages.ie',inherited_status=403,retry_allowed=False,no_blanket_image_approval=True,images_downloaded=0,images_prepared=0,storage_writes=0,actually_viewed_files=[],reason='Metadata-only supplement. Held native image host not requested; no explicit selected reusable alternative.'))
    print('Validated immutable plan',pin,flush=True)

def recovery():
    p,pin=h.pinned(PHASE);target(False)
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        states=h.snapshot(db,[x['artwork_id'] for x in p['records']]);assert not states
        prior=h.snapshot(db,[str(x['id']) for x in db.execute('SELECT id FROM artworks WHERE current_institution_id=%s ORDER BY id LIMIT 1000',(MID,))])
    h.save(h.BACKUP/'affected-preimages.json.gz',dict(at=h.now(),plan_sha256=pin,artworks=states,existing=prior,artists=p['artists'],institutions=p['institutions']))
    files=[h.BACKUP/'affected-preimages.json.gz',h.BACKUP/PHASE/'plan-preimages.json.gz',E/PHASE/'plan.json.gz',E/PHASE/'plan-pin.json']
    evidence=[]
    for path in files:
        raw=path.read_bytes();h.load(path);evidence.append(dict(path=str(path),sha256=h.sha(raw),bytes=len(raw),complete_decoding=True))
    save('local-recovery-verification.json',dict(at=h.now(),status='VERIFIED',plan_sha256=pin,files=evidence,procedure='Established bounded local recovery: complete affected/preexisting row preimages and immutable plan outside Documents; transactional SQL rollback and audit history retained.',cloud_backup_created=False,existing_preserved=len(prior)))

if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for command in sys.argv[1:]:globals()[command]()
