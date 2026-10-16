#!/usr/bin/env python3
"""One bounded Warsaw icon batch; reuse established production helpers."""
import csv, fcntl, gzip, importlib.util, inspect, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def mod(name, filename):
    s = importlib.util.spec_from_file_location(name, ROOT/'ops'/filename)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
base = mod('base100w', 'continuous-image-batch-000002.py')
h = mod('metadata100w', 'india-300-delivery-20261011.py'); i = base.i
E = ROOT/'docs/research/continuous-production-20261011/batches/000100/warsaw'
R = Path.home()/'Library/Application Support/Artline/continuous-research/batches/000100'
OP = 'continuous-warsaw-20261011-b000100'; PHASE = 'warsaw-icons'
FIELD = 'continuous_warsaw_object_evidence_20261011_b000100'
MID = '6c8ae01a-f6a5-5591-9635-a4af407cd2dc'; MUSEUM = 'National Museum in Warsaw'
SCHEME = 'mnw-current-object-2026'; B = 'warsaw-000'
SELECTED = [460094, 456544, 498560, 440236, 455229, 498717, 498514, 498377, 498384, 499235]
ALL_IDS = SELECTED
DATES = {460094: ('ok. 1710', 1710, 1710), 456544: ('XIX w.', 1801, 1900), 498560: ('XIX w.', 1801, 1900), 440236: ('XVII - XVIII w.', 1601, 1800), 455229: ('XVIII w.', 1701, 1800), 498717: ('XVI/XVII w.', 1501, 1700), 498514: ('XIX w.', 1801, 1900), 498377: ('XVIII w.', 1701, 1800), 498384: ('2. poł. XVIII w.', 1751, 1800), 499235: ('ok. 1850', 1850, 1850)}
h.OP=OP; h.RUN=E; h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'warsaw':[SCHEME]}
h.museums=lambda:{MUSEUM:('wikimedia-museum-q153306','https://www.mnw.art.pl/')}
for p in [E,R,h.BACKUP]: p.mkdir(parents=True,exist_ok=True)
def save(name, value):
    p=E/name
    if p.exists(): return h.load(p)
    h.save(p,value); return value
def target(write=False):
    assert __import__('os').environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
    name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
    assert name=='artline-508319:europe-west1:artline-postgres'
    return dict(base.target(write),connection_name=name,helper='ops/india-300-delivery-20261011.py',local_connections=0)
def capture(oid):
    rc=h.load(E/f'object-{oid}.receipt.json'); raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert rc['status']==200 and h.sha(raw)==rc['sha256']
    o=json.loads(raw)['data']; assert o['id']==oid and o==h.load(E/f'object-{oid}.json')['data']
    return o,rc
def attribution(o):
    return '; '.join(a['name']+(' ['+a['comment']+']' if a.get('comment') else '')+(' — '+a['role'] if a.get('role') else '') for a in o['authors'])
def no_collision(db, rows):
    ids=[r['source_id'] for r in rows]; urls=[r['source_url'] for r in rows]
    acc=[r['accession_number'] for r in rows]
    assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',(acc,)).fetchall(),'Concurrent inventory identity; replan'
    assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(SCHEME,ids)).fetchall(),'Concurrent native identity; replan'
    assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall(),'Concurrent source identity; replan'
h.no_collision=no_collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized continuous production enrichment, batch 100: selected Warsaw page-twelve painted icons; qualified workshop/school makers stay object-level.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows),'Bounded newly reconciled objects only'")
code=code.replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'", "  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)

def stage():
    if (E/PHASE/'plan-pin.json').exists(): print('Pinned plan retained'); return
    save('production-target-before-plan.json',target())
    regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    reg=list(csv.DictReader(regpath.open())); assert len(reg)==111
    checks=[]; rows=[]
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        scope=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=%s',(MID,))]
        h.save(E/'institution-scope-before.json.gz',scope)
        for oid in ALL_IDS:
            o,rc=capture(oid); url='https://cyfrowe.mnw.art.pl/pl/zbiory/'+str(oid)
            acc=o['noEvidence']; forms=list(dict.fromkeys([acc,acc.replace(' MNW',''),acc.replace(' ','')]))
            historical=[str(x['number']) for x in o.get('extraNumPatterns',[])]
            native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (scheme=%s OR scheme ILIKE '%%mnw%%' OR scheme ILIKE '%%warsaw%%') AND external_id=ANY(%s)",(SCHEME,[str(oid)]+historical))]
            globalacc=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',(forms,))]
            exact=[x for x in scope if h.norm(x['accession_number'])==h.norm(acc) or h.norm(x['title'])==h.norm(o['title'])]
            urls=[url,'https://cyfrowe.mnw.art.pl/en/catalog/'+str(oid),'https://cyfrowe.mnw.art.pl/en/collections/'+str(oid)]
            cit=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls))]
            reason=None
            if native or globalacc or exact or cit: reason='Existing or ambiguous global object identity; excluded from new increments.'
            checks.append(dict(source_id=str(oid),accession=acc,title=o['title'],native=native,global_accession=globalacc,scoped_title_or_accession=exact,source_url_matches=cit,historical_numbers=historical,outcome=reason or 'selected_new'))
            if reason: continue
            date,lo,hi=DATES[oid]; assert o['createDates']==[dict(o['createDates'][0])] and len(o['createDates'])==1 and o['createDates'][0]['name']==date and not o['createDates'][0]['comment']
            assert o['owner']=={'id':107515,'name':'Muzeum Narodowe w Warszawie'}
            assert all(re.search(r'warsztat|szkoła',a['name'],re.I) for a in o['authors'])
            assert any(x['name'] in ['tempera','olej'] for x in o['techniques'])
            assert all(c['name']=='DOMENA PUBLICZNA' and not c['restricted'] for c in o['copyrights']) and o['copyrights']
            ep=E/f'object-{oid}.json'
            rows.append(dict(provider='warsaw',source_id=str(oid),source_url=url,museum=MUSEUM,title=o['title'],creator_label=attribution(o),creator_link_hold=True,culture=None,date_display=date,year_start=lo,year_end=hi,date_decision='eligible',accession_number=acc,source_type='metalwork' if 'odlew' in [x['name'] for x in o['techniques']] else 'painting',medium='; '.join(x['name']+(' ('+x['comment']+')' if x.get('comment') else '') for x in o['techniques']+o['materials']),dimensions=o['dimensionText'],credit=MUSEUM+'; explicit native owner',raw=o,evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=rc['retrieved_at'],sha256=h.sha(ep.read_bytes()),url=url),api_receipt=rc,creator_reconciliation='Only source workshop and school labels; globally reconcile labels but do not equate a workshop to a person. Retain authority IDs, original roles and tentative Stroganov-school question mark. No fabricated painter or unqualified artist link.',identity_review='One separately inventoried surviving physical object. IK 159 retains its complete architectural surround and uncertain original function as side altar or iconostasis fragment; not the entire parent structure. IK 90 is one hinged triptych; primary view does not imply reverse-side coverage. Its reconstructed book and other conservation evidence remain in raw museum description. IK 105 retains historical deposit and uncertain donor details while the explicit current owner supports the current holding only. Earlier acquisition numbers, dimensions, full supplied compositions, workshop qualifications and source descriptions distinguish repeated subjects. Full-century bounds preserve broad wording; circa years remain approximate.',date_basis='Closed century/half-century/quarter-century bounds parsed conservatively from source wording; original text unchanged.'))
    save('global-identity-reconciliation.json',dict(at=h.now(),institution_scope_count=len(scope),previous_icon_titles=[x['title'] for x in scope if 'ikon' in x['title'].lower()],records=checks,selected=len(rows),all_checked_native_ids=[str(x) for x in ALL_IDS],remaining_coverage='Page twelve researched; separately inventoried painted icons selected. Casts remain unselected research candidates. No whole-institution coverage claim.'))
    save('selected-before-images.json',dict(at=h.now(),source_ids=[r['source_id'] for r in rows],metadata_selected_before_any_image_download=True))
    assert rows and len(rows)<=50
    h.save(E/PHASE/'source-records.json.gz',rows); h.plan(PHASE)
    plan,pin=h.pinned(PHASE); assert len(plan['records'])==len(rows) and not plan['artists'] and not plan['new_institutions'] and all(not x['before'] for x in plan['records'])
    policy=h.load(E/'policy-project.receipt.json'); text=gzip.decompress(Path(policy['body_path']).read_bytes()).decode()
    assert 'komercyjnym' in text
    save('source-register.json',dict(at=h.now(),registry=next(x for x in reg if x['source_id']=='national_museum_warsaw'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Official native object API HTTP 200; prior museum digital-project policy HTTP 200 capture reused and rehashed',policy_capture=policy,rights='Actual DOMENA PUBLICZNA label, restricted=false; project expressly supports commercial reuse. No CC0 assertion; museum credit retained.',last_checked_at=h.now(),plan_sha256=pin,remaining_gaps='Prior holds preserved. Page-eleven candidates globally reconciled; all saved source/date/component holds retained. No blanket approval for other providers.'))
    save('helper-adaptation.json',dict(helper='ops/india-300-delivery-20261011.py',sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Bounded up to 50 new objects; dedicated operation/citation field','Source-qualified makers stay object labels','Same shared production ingestion advisory lock plus concurrent inventory/native/URL guard','Locked preimages and pinned plan retained in established backup directory']))
    print('Selected',len(rows),'new icon records; plan',pin,flush=True)

def apply():
    p,pin=h.pinned(PHASE); ids=[r['artwork_id'] for r in p['records']]
    accepted_images,audit,review=i.accepted(B)
    assert {x['artwork_id'] for x in accepted_images}==set(ids)
    assert all(x['viewed_individually'] for x in review['decisions'])
    assert len(h.load(E/'prewrite-file-verification.json')['files'])==len(ids)
    source_check=h.load(E/'independent-source-verification.json')
    assert source_check['plan_sha256']==pin and len(source_check['records'])==len(ids)
    assert h.load(E.parent/'prior-batch-live-reconciliation.json')['exact_snapshot_equal']
    save('production-target-before-metadata-write.json',target(True))
    with h.connect() as db:
        present=h.snapshot(db,ids)
        notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
        if present:
            assert len(present)==len(notes)==len(ids) and all(x['pin']==pin for x in notes)
            assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={}
            print('Own committed plan recovered; independent verification required'); return
    recovery=h.load(E/'local-recovery-verification.json'); assert recovery['status']=='VERIFIED' and recovery['plan_sha256']==pin
    for f in recovery['files']: assert h.sha(Path(f['path']).read_bytes())==f['sha256']
    h.apply(PHASE)

i.OP=OP+'-images'; i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['warsaw']=dict(mid=MID,scheme=SCHEME,name=MUSEUM,rights='public_domain',license='DOMENA PUBLICZNA — National Museum in Warsaw',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='cyfrowe-cdn.mnw.art.pl')
old_uid=i.m.uid
i.m.uid=lambda k:h.uid('source/warsaw/'+MUSEUM) if k=='source/warsaw' else old_uid(k)
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
exec(compile(code,__file__,'exec'),i.__dict__)
def images():
    p,pin=h.pinned(PHASE); rows=[]
    for r in p['records']:
        o=r['raw']; im=o['image']; assert im['position']==1
        url='https://cyfrowe-cdn.mnw.art.pl/upload/cache/multimedia_detail/'+im['filePath']+'.'+im['extension']
        rows.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),provider='warsaw',image=dict(image_url=url,source=o,receipt=r['api_receipt']),plan_sha256=pin,plan_path=str(E/PHASE/'plan.json.gz'),rights_basis='Exact native inventory object labels reproduction DOMENA PUBLICZNA with restricted=false; museum Otwarte Narodowe project explicitly supports commercial reuse. Preserve native label and owner/museum credit. User authorization is separate from museum rights evidence.',manual_visual_required=True))
    h.save(i.folder(B)/'selection.json.gz',dict(provider='warsaw',batch=B,rows=rows)); h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
    for r in rows: print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
    (i.ORIG/B).mkdir(parents=True,exist_ok=True); i.audit(B)
    print('SHEETS', [str(x) for x in (i.folder(B)/'sheets').glob('*.json')])
def deliver():
    save('production-target-before-storage-write.json',target(True)); i.upload(B)
    save('production-target-before-image-write.json',target(True)); i.apply(B)
if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); globals()[sys.argv[1]]()
