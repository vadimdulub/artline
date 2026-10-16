#!/usr/bin/env python3
"""Independent source, visual, and scoped recovery gates for batch 251."""
import gzip, importlib.util, io, json, os, re, subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('w251',ROOT/'ops/continuous-warsaw-batch-000251.py');w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
b=w.b;h=b.h;i=b.i;E=b.E
p,pin=h.pinned(b.PHASE); ids=[r['artwork_id'] for r in p['records']]

checks=[]
for r in p['records']:
    o=r['raw']; rc=h.load(E/f"object-{r['source_id']}.receipt.json")
    raw=gzip.decompress(Path(rc['body_path']).read_bytes()); assert h.sha(raw)==rc['sha256']
    assert o['owner']['name']=='Muzeum Narodowe w Warszawie'
    assert o['copyrights'] and all(x['name']=='DOMENA PUBLICZNA' and not x['restricted'] for x in o['copyrights'])
    assert r['last']<=1970 and r['before'] is None and r['creator_link_hold']
    checks.append(dict(source_id=r['source_id'],inventory=r['accession_number'],source_sha256=rc['sha256'],source_date=r['date_display'],creation_bounds=[r['first'],r['last']],source_creators=o['authors'],source_owner=o['owner'],source_rights=o['copyrights'],dimensions=o['dimensionText'],identity_review=b.REVIEWS[int(r['source_id'])]))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,current_display_claims=0))

observations={
'498335':'Original and derivative individually viewed. One complete rectangular painted icon/oklad object with upper narrative register, central row of haloed saints, and lower scenes. Complete supplied edges retained; no component counted separately.',
'498657':'Original and derivative individually viewed. One complete slightly bowed rectangular icon with the Mother of God centrally, narrative scenes around the border and lower register. Full supplied support and margins retained; distinct inventory IK 46 MNW.',
'498656':'Original and derivative individually viewed. One complete rectangular icon with Saint John centrally holding a scroll and bowl, surrounded by narrative and border scenes. Full supplied support and margins retained; distinct inventory IK 45 MNW.'}
files=[]; decisions=[]
for r in i.selected(b.B)['rows']:
    im=h.load(i.folder(b.B)/'prepared'/(r['artwork_id']+'.json')); raw=Path(im['path']).read_bytes(); orig=Path(im['original_path']).read_bytes()
    assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'] and len(raw)<=100000
    with Image.open(io.BytesIO(raw)) as pic: pic.load(); assert pic.format=='JPEG'
    with Image.open(io.BytesIO(orig)) as pic: pic.load(); assert abs(pic.width/pic.height-im['width']/im['height'])<.03
    decisions.append(dict(artwork_id=r['artwork_id'],source_id=r['native_id'],artist=r['creator_label'],sha256=im['sha256'],decision='accept',viewed_individually=True,viewed_path=im['path'],viewed_original_path=im['original_path'],original_sha256=im['source_sha256'],original_viewed_individually=True,tool='functions tools.view_image',observations=observations[r['native_id']],flag_resolution='Actual original and derivative viewed; authentic complete museum reproduction, not a placeholder or detail crop.',identity_confidence=.99,confidence_basis='Exact native object/image, inventory, dimensions, title, and observed composition; editorial judgment.'))
    files.append(dict(artwork_id=r['artwork_id'],sha256=im['sha256'],bytes=im['bytes'],complete_decode=True,proportions_preserved=True,original_sha256=im['source_sha256'],original_path=im['original_path']))
review=dict(at=h.now(),batch_quality_decision='accept',reviewer='Codex actual image viewing',decisions=decisions,all_selected_files_individually_viewed=True,sample_only_files=[],limitations='All three originals and derivatives viewed. Small inscriptions and unavailable reverse sides were not claimed as inspected.')
h.save(i.folder(b.B)/'visual-review.json',review); b.save('actual-visual-review.json',review); b.save('prewrite-file-verification.json',dict(at=h.now(),files=files,plan_sha256=pin))

b.save('production-target-before-scoped-recovery.json',b.target())
backup=h.BACKUP; backup.mkdir(parents=True,exist_ok=True); backup.chmod(0o700)
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
kw=h.psycopg.conninfo.conninfo_to_dict(secret); env=os.environ.copy(); env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
schema=backup/'production-schema-before.pgdump'; subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(schema)],env=env,check=True,capture_output=True,timeout=180); schema.chmod(0o600)
toc=backup/'production-schema-before.toc'; toc.write_bytes(subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(schema)],check=True,capture_output=True).stdout); toc.chmod(0o600)
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'); b.no_collision(db,p['records']); before=h.snapshot(db,ids); assert before=={}
    institution=[x['v'] for x in db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,))]
    existing=h.load(E/'institution-scope-before.json.gz'); preserved=h.snapshot(db,[x['id'] for x in existing])
    out=dict(at=h.now(),scope='Exact planned objects, institution, and existing institution artworks.',plan_sha256=pin,planned_artwork_ids=ids,artworks=before,artists=[],institutions=institution,sources=[],preserved=preserved)
    h.save(backup/'affected-row-recovery-before.json.gz',out)
files2=[schema,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz']
manifest=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files2]
v=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',path=str(backup),files=manifest,plan_sha256=pin,planned_artworks=len(ids),artwork_preimages=0,linked_artists=0,preserved_existing_artworks=len(preserved),schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,local_catalogue_connections=0,cloud_backups_created=0,full_database_backup=False,additional_locked_preimages_required=True)
b.save('local-recovery-verification.json',v); h.save(backup/'local-recovery-verification.json',v)
print('Prepared independent gates for',len(ids),'records')
