#!/usr/bin/env python3
"""Independent source and recovery checks; no database mutations."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b69',Path(__file__).with_name('continuous-iceland-000069.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
assert len(ids)==len(set(ids))==4 and len(p['new_artists'])==1 and len(p['new_institutions'])==1
for r in p['records']:
    raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256']
    o=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['content'];d=o['sarpur']
    assert r['title']==o['title']==d['name'] and r['accession_number']==d['listasafnidId'] and r['date_display']==d['year']
    assert r['creator_label']==d['artists'][0]['name'] and r['dimensions']==d['size'] and r['medium']=='; '.join(d['material'])
    assert r['first']<=r['last']<=1970 and r['source_type']=='painting' and 'Málaralist / Olíumálverk' in d['category']
    assert not r['before'] and r['add_holding'] and r['institution_id']==b.MID
    assert 'exhibitionText' not in r['raw'] and 'description' not in r['raw']
rc=h.load(b.E/'creator-authority-capture.json');raw=Path(rc['body_path']).read_bytes();assert rc['status']==200 and h.sha(raw)==rc['sha256']
txt=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
assert 'Kristján Davíðsson Born 1917 Died 2013' in txt
b.save('production-target-before-scoped-recovery.json',b.target())
backup=h.BACKUP;backup.chmod(0o700)
if not (b.E/'local-recovery-verification.json').exists():
    secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
    kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
    path=backup/'production-schema-before.pgdump'
    result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert result.returncode==0,'Schema export failed'
    path.chmod(0o600)
    result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=backup/'production-schema-before.toc';toc.write_bytes(result.stdout);toc.chmod(0o600)
    with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);before=h.snapshot(db,ids);assert before=={}
        artists=[r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists'])+[b.NEW_ARTIST],))];assert len(artists)==3
        inst=[r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,))];assert not inst
        sources=[r['v'] for r in db.execute('SELECT to_jsonb(s) v FROM sources s WHERE id=%s',(h.uid('source/iceland/'+b.MUSEUM),))];assert not sources
        old=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
        h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,artworks=before,artists=artists,new_artist_preimages=[],institutions=inst,sources=sources,preserved_artworks=old))
    files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz',backup/'preserved-existing-before.json.gz']
    for f in files:
        if f.suffix=='.gz':h.load(f)
    receipt=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,path=str(backup),files=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files],schema_archive_fully_decoded=True,all_json_exports_decoded=True,full_database_backup=False,cloud_backups_created=0,additional_locked_preimages_required=True,local_catalogue_connections=0,recovery='Reconcile exact plan/source checksums and audit events against locked transaction preimages before any corrective action. New artist, institution and artwork preimages are explicitly empty. No recovery mutation executed.')
    b.save('local-recovery-verification.json',receipt);h.save(backup/'local-recovery-verification.json',receipt)
with h.connect() as db:
    b.no_collision(db,p['records']);assert not h.snapshot(db,ids)
    actor=db.execute('SELECT id FROM users WHERE id=%s',(h.ACTOR,)).fetchone() if False else None
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,source_records=4,new_review_artists=1,existing_artists=3,new_institutions=1,holdings=4,images_selected=0,all_sources_hashed_and_parsed=True,creator_authority_independently_checked=True,local_catalogue_connections=0,shared_ingestion_lock='artline-curated-ingestion'))
print('Source identities, creator authority, empty preimages and scoped recovery independently verified')
