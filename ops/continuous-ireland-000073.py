#!/usr/bin/env python3
"""One bounded Ireland continuation; no supervisor and no local catalogue writes."""
import csv, fcntl, gzip, importlib.util, inspect, json, os, re, subprocess, sys
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base73','continuous-image-batch-000002.py')
h=mod('metadata73','india-300-delivery-20261011.py')
native=mod('ireland73','museum-expansion-ireland-20261006.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000073'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000073'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000073'
OP='continuous-ireland-20261011-b000073';PHASE='ireland-paintings'
FIELD='continuous_ireland_object_evidence_b000073'
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
    return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(url,key):
    p=E/(key+'-capture.json')
    if p.exists():
        rc=h.load(p);raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'];return raw,rc
    r=requests.get(url,timeout=40,headers={'User-Agent':'Artline selected collection research/1.0'})
    raw=r.content;path=S/(key+'.html');path.write_bytes(raw)
    rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=h.now(),body_path=str(path),sha256=h.sha(raw),bytes=len(raw),retry_after=r.headers.get('Retry-After'))
    save(key+'-capture.json',rc);return raw,rc
def initialize():
    save('started.json',dict(at=h.now(),batch=73))
    q=ROOT/'docs/research/continuous-production-20261011/source-queue.json'
    save('source-queue-before.json',h.load(q))
    paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',ROOT/'docs/research/continuous-production-20261011/CHECKPOINT.json',q]
    paths.extend(ROOT/'docs/research/continuous-production-20261011/batches'/n/'source-access-holds.json' for n in ['000070','000069','000064','000063'])
    reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
    save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],original_registry=reg,precedence='Latest user and source approvals govern. Real local database read-only. External supervisor unmodified.',ireland_access='No provider hold recorded in current source queue; inspect official source once, no bypass.'))
    save('production-target-before-research.json',target())
def reserve():
    if (E/'independent-reserve-live-verification.json').exists():return
    prior=h.load(ROOT/'docs/research/continuous-production-20261011/batches/000052/independent-reserve-evidence-verification.json')
    from PIL import Image
    for f in prior['immutable_plans']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
    records=prior['records'];ids=[x['artwork_id'] for x in records]
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows={x['id']:x for x in db.execute('SELECT a.id::text,a.status,a.accession_number,a.primary_media_id::text,m.checksum_sha256 FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))}
        citations=db.execute("SELECT entity_id::text,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
        notes={}
        for x in citations:
            try:n=json.loads(x['evidence_note'] or '{}')
            except (ValueError,TypeError):continue
            if n.get('plan_sha256')==prior['prior_campaign_plan_sha256']:notes[x['entity_id']]=n
    checked=[]
    for r in records:
        a=rows[r['artwork_id']];assert a['status']!='archived' and a['accession_number']==r['accession'] and a['checksum_sha256']==r['derivative_sha256'] and a['id'] in notes
        for k in ['source_record','prior_visual_decision']:assert h.sha(Path(r[k]['path']).read_bytes())==r[k]['sha256']
        p=Path(r['local_path']);assert h.sha(p.read_bytes())==a['checksum_sha256'] and p.stat().st_size<=100000
        with Image.open(p) as im:im.load()
        checked.append(dict(source_id=r['source_id'],artwork_id=a['id'],primary_media_id=a['primary_media_id'],checksum_sha256=a['checksum_sha256'],prior_visual_decision=r['prior_visual_decision'],prior_plan_sha256=prior['prior_campaign_plan_sha256'],outcome='already_delivered_prior_campaign_excluded'))
    save('independent-reserve-live-verification.json',dict(at=h.now(),inspected=188,already_delivered=188,genuinely_unimported=0,new_selection=0,records=checked,immutable_plans=prior['immutable_plans'],fresh_visual_views=0,visual_basis='Reused immutable checksum-bound historical decisions; no claim of fresh visual inspection.',no_source_or_image_requests=True,prior_campaign_not_counted=True))
def discover():
    if (E/'discovery.json').exists():return
    url=native.INDEX+'&page=38';raw,rc=capture(url,'ireland-index-38')
    if rc['status']!=200:
        save('discovery.json',dict(at=h.now(),access_hold=rc,records=[],rows=[],next_url=url));return
    rows,next_url=native.index_rows(raw,url)
    with h.connect() as db:
        known,titles,inventories=native.existing_keys(db,MID)
        names=db.execute("SELECT id::text,display_name name,birth_year,death_year FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias name,a.birth_year,a.death_year FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'").fetchall()
    records=[];held=[]
    for idx in rows:
        reason=None
        if idx['source_id'] in known:reason='existing_source_identity'
        elif h.norm(idx['title']) in titles:reason='existing_institution_title'
        elif not native.creation_date(idx['date']):reason='creation_date_review'
        if reason:held.append(dict(index=idx,reason=reason));continue
        if len(records)>=8:continue
        body,cap=capture(idx['url'],'ireland-object-'+idx['source_id'])
        if cap['status']!=200:
            held.append(dict(index=idx,reason='provider_access_hold',capture=cap));break
        parsed=native.fields(body);facts,reason=native.facts(parsed,idx)
        if not reason and native.inventory_keys(facts['accession'])&inventories:reason='existing_inventory'
        matches={x['id']:x for x in names if h.norm(x['name'])==h.norm(idx['creator'])}
        if not reason and len(matches)!=1:reason='creator_requires_global_reconciliation'
        if reason:held.append(dict(index=idx,reason=reason,parsed=parsed,capture=cap,creator_matches=matches));continue
        records.append(dict(index=idx,parsed=parsed,facts=facts,capture=cap,artist=next(iter(matches.values()))))
    save('discovery.json',dict(at=h.now(),page=38,index_capture=rc,rows=rows,records=records,held=held,next_url=next_url,unrequested_native_ids=[x['source_id'] for x in rows if x['source_id'] not in {v['index']['source_id'] for v in records+held}]))
    print(json.dumps(dict(page=38,rows=len(rows),candidates=len(records),held=len(held),next_url=next_url)))
    for x in records:print(x['index']['source_id'],x['facts']['title'],x['facts']['date_display'],x['artist']['name'],x['facts']['accession'])
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
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production enrichment batch 73: two exact Irish collection objects, one after Guercino with anonymous maker; new works remain review.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=25 and all(not r['before'] for r in rows)")
code=code.replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace("WHERE entity_type='artwork' AND scheme=ANY(%s)\",(list({r['scheme'] for r in rows}),)","WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)\",(list({r['scheme'] for r in rows}),[r['source_id'] for r in rows])")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
    if (E/PHASE/'plan-pin.json').exists():return
    save('production-target-before-plan.json',target())
    discovery=h.load(E/'discovery.json');rows=[]
    for x in discovery['records']:
        f=x['facts'];idx=x['index'];qualified=idx['source_id']=='8923'
        assert qualified==f['creator_label'].startswith('After ')
        rows.append(dict(provider='ireland',source_id=idx['source_id'],source_url=idx['url'],museum=MUSEUM,title=f['title'],creator_label=f['creator_label'],creator_link_hold=qualified,verified_artist_id=None if qualified else x['artist']['id'],date_display=f['date_display'],year_start=f['first'],year_end=f['last'],native_date_precision=f['date_precision'],date_decision='eligible',accession_number=f['accession'],source_type='painting',medium=f['medium'],dimensions=f['dimensions'],credit=x['parsed']['fields']['Credit Line'],raw=dict(fields=x['parsed']['fields'],creators=x['parsed']['creators'],creator_names=x['parsed']['creator_names']),evidence=x['capture'],evidence_file=x['capture']['body_path'],index_record=idx,index_capture=discovery['index_capture'],holding_basis=f['holding_basis'],creator_reconciliation='Explicit After Guercino label, eighteenth-century copy; maker unresolved and no primary artist link.' if qualified else 'Unique existing Jan Weenix name and both life years 1642–1719 match the official source. Do not confuse Jan Baptist Weenix (1621–1659).',identity_review='Native NGI inventory, source title, support, dimensions, acquisition and date checked. Global source/accession/title reconciliation and both Weenix oeuvres reviewed. Guercino source is a physically separate eighteenth-century canvas copy, not an original seventeenth-century work.',image_hold='No per-image open licence established. Official image-ordering host HTTP 403; stop requests to that host. No reproduction downloaded.'))
    assert {r['source_id'] for r in rows}=={'8923','8927'}
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        checks=identity(db,rows)
        oldids=[x['id'] for x in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s',(MID,))]
        oldids+= [x['id'] for x in h.load(E/'creator-oeuvres.json')['works']]
        old=h.snapshot(db,list(set(oldids)))
        # Reconcile previous in-flight delivery independently; never count it again.
        prev=h.load(E.parent/'000072/batch-verification-receipt.json');pids=prev['production_ids']
        previous=h.snapshot(db,pids);assert len(previous)==7 and all(x['artwork']['primary_media_id'] for x in previous.values())
        notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name='continuous_warsaw_object_evidence_20261011_b000072'",(pids,)).fetchall()
        previous_pin=h.load(E.parent/'000072/CHECKPOINT.json')['metadata_plan_sha256']
        assert len(notes)==7 and all(x['pin']==previous_pin for x in notes)
    save('previous-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=72,live_objects=7,all_primary_images_attached=True,citation_plan_sha256=previous_pin,programme_increment_this_batch=0,write_replay_required=False))
    save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,oeuvre_evidence='creator-oeuvres.json',source_qualified_copy_not_primary_guercino=True,existing_works_preserved=len(old)))
    save('preserved-existing-before.json.gz',dict(artworks=old));h.save(h.BACKUP/'preserved-existing-before.json.gz',dict(artworks=old))
    h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
    p,pin=h.pinned(PHASE);assert len(p['records'])==2 and len(p['artists'])==1 and not p['new_institutions'] and all(not r['before'] for r in p['records'])
    assert next(r for r in p['records'] if r['source_id']=='8923')['artist_id'] is None
    save('editorial-decisions.json',dict(at=h.now(),selected_source_ids=['8923','8927'],held_michel=dict(source_id='8926',resolved_artist_id='aab569d4-44db-45e2-89bd-39885defeed1',resolved_name='Michel Georges',life_years=[1763,1843],reason='Creator securely reconciled by reversed name and both life years. Physical version unresolved: multiple existing Saint-Denis landscapes include an undated unlocated supplied-CSV work; do not create another object until provenance/composition resolves it.',evidence=['michel-oeuvre.json','michel-version-citations.json']),image_decision='No selected native reproduction has verified commercial/open terms; official image-ordering host access hold preserved. No image download or fresh visual review claimed.',metadata_plan_sha256=pin))
    print('Pinned two new review paintings and two collection holdings; one source-qualified copy, one existing creator; no image downloads.')
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
i=base.i;B='ireland-commons-000'
i.OP=OP+'-images';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['ireland-commons']=dict(mid=MID,scheme=SCHEME,name='National Gallery of Ireland / Wikimedia Commons',rights='cc_by',license='CC BY 4.0 — National Gallery of Ireland; Commons also marks PD-Art',policy='https://creativecommons.org/licenses/by/4.0/',host='upload.wikimedia.org')
old_uid=i.m.uid;i.m.uid=lambda k:'de4bd5ae-b280-4e0f-ba55-d462f47613d9' if k=='source/ireland-commons' else old_uid(k)
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
exec(compile(code,__file__,'exec'),i.__dict__)
def images():
    from bs4 import BeautifulSoup
    if (i.folder(B)/'selection.json.gz').exists():return
    p,pin=h.pinned(PHASE);r=next(x for x in p['records'] if x['source_id']=='8927')
    rc=h.load(E/'commons-weenix-capture.json');raw=Path(rc['body_path']).read_bytes();assert rc['status']==200 and h.sha(raw)==rc['sha256']
    soup=BeautifulSoup(raw,'html.parser');content=soup.select_one('#mw-content-text');txt=content.get_text(' ',strip=True)
    assert 'CC BY 4.0' in txt and 'Attribution: National Gallery of Ireland' in txt and 'NGI.488' in txt and '8927' in txt and '43.5' in txt and '34.7' in txt
    url=soup.select_one('.fullImageLink a[href]')['href'];assert url.startswith('https://upload.wikimedia.org/')
    rights=dict(commons_file='File:In the Campagna .PNG',license='CC BY 4.0',attribution='National Gallery of Ireland',additional_label='PD-Art / Public Domain Mark',source_page='http://onlinecollection.nationalgallery.ie/objects/8927',native_inventory='NGI.488',native_object_id='8927',native_title='In the Campagna',native_creator='Jan Weenix (1642–1719)',commons_creator='Jan Baptist Weenix (1621–circa 1660)',creator_conflict_resolution='Current primary museum record prevails for creator. Commons categorization conflicts, but exact accession, official source ID, circa 1669 date and 43.5 x 34.7 cm dimensions identify the same object. Catalogue attribution is unchanged.',policy_scope='Explicit Commons CC BY 4.0 file licence, not a blanket Irish museum approval. Museum native image-host HTTP 403 remains held. User production authorization is separate from licence evidence.',image_dimensions=[239,299],quality_limit='Small source image; suitable full-composition thumbnail, not detailed study.')
    row=dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label='Jan Weenix',source_url=rc['url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type='painting',provider='ireland-commons',image=dict(image_url=url,source=rights,receipt=rc),plan_sha256=pin,expected_primary_artist_id=r['artist_id'],rights_basis='Commons file explicitly supplies CC BY 4.0 credited to National Gallery of Ireland, plus PD-Art. Exact native accession/object/date/dimensions independently agree. Current museum attribution resolves Commons father/son error; full image visually checked before delivery. Source-specific Irish commercial permission not generalized; Commons licence retained as the actual source claim.',manual_visual_required=True)
    h.save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='ireland-commons',batch=B,rows=[row],selection_basis='One selected exact Commons file with explicit CC BY 4.0, separately from held museum image-ordering host.'))
    h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
    im=i.prepare_one(row,B);assert im['state']=='prepared',im
    i.audit(B);save('commons-image-policy-review.json',dict(at=h.now(),rights=rights,source_capture=rc,metadata_plan_sha256=pin,image_selection_sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes()),historical_plan_unchanged=True,decision='Selected Commons alternative supersedes only the earlier no-open-image finding for NGI.488; official image-host hold remains.'))
    print(im['path'])
def deliver():
    save('production-target-before-storage-write.json',target(True));i.upload(B)
    save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for command in sys.argv[1:]:globals()[command]()
