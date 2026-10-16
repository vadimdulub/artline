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
E=ROOT/'docs/research/continuous-production-20261011/batches/000126'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000126'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000126'
OP='continuous-ireland-20261011-b000126';PHASE='ireland-paintings'
FIELD='continuous_ireland_object_evidence_b000126'
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
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production enrichment batch 126: selected exact Irish collection objects with original creator qualifications; new works remain review.')
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
i=base.i;B='ireland-commons-000'
i.OP=OP+'-images';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['ireland-commons']=dict(mid=MID,scheme='wikidata',name='National Gallery of Ireland / Wikimedia Commons',rights='public_domain',license='Public domain / PD-Art — Wikimedia Commons; National Gallery of Ireland source',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='upload.wikimedia.org')
old_uid=i.m.uid;i.m.uid=lambda k:'de4bd5ae-b280-4e0f-ba55-d462f47613d9' if k=='source/ireland-commons' else old_uid(k)
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid], 'Selected object changed after preparation'")
code=code.replace("assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid], 'Selected object changed after preparation'", "assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid], 'Selected object changed after preparation'\n    citation=m.load(RUN/'gap-input.json.gz')['pinned_catalogue_citation']['citation']\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s\",(aid,citation['field_name'],citation['source_url'],citation['evidence_note'])).fetchone(), 'Pinned existing source citation changed'")
exec(compile(code,__file__,'exec'),i.__dict__)
def deliver():
    assert h.load(E/'independent-prewrite-verification.json')['passed']
    rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
    for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
    save('production-target-before-storage-write.json',target(True));i.upload(B)
    save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for command in sys.argv[1:]:globals()[command]()
