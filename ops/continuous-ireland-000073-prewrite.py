#!/usr/bin/env python3
"""Independent source and scoped recovery checks before batch 73 writes."""
import fcntl, importlib.util, os, subprocess
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b73',Path(__file__).with_name('continuous-ireland-000073.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
assert len(ids)==len(set(ids))==2 and len(p['artists'])==1 and not p['new_institutions']
checks=[]
for r in p['records']:
    raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
    parsed=b.native.fields(raw);facts,reason=b.native.facts(parsed,r['index_record']);assert not reason
    assert (r['title'],r['date_display'],r['accession_number'],r['creator_label'],r['medium'],r['dimensions'])==(facts['title'],facts['date_display'],facts['accession'],facts['creator_label'],facts['medium'],facts['dimensions'])
    rc=r['index_capture'];raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256']
    indexed,_=b.native.index_rows(raw,rc['url']);assert r['index_record'] in indexed
    assert r['first']==facts['first'] and r['last']==facts['last']<=1970 and r['precision']==facts['date_precision']
    assert not r['before'] and r['add_holding'] and r['institution_id']==b.MID
    if r['source_id']=='8923':assert r['artist_id'] is None and r['creator_label'].startswith('After Guercino') and r['precision']=='century'
    else:
        assert r['artist_id']=='84614a67-9ffe-4e05-a37d-63686cc21565'
        artist=p['artists'][r['artist_id']];assert artist['display_name']=='Jan Weenix' and (artist['birth_year'],artist['death_year'])==(1642,1719)
    checks.append(dict(source_id=r['source_id'],artwork_id=r['artwork_id'],source_sha256=r['evidence']['sha256'],title=r['title'],creator_label=r['creator_label'],date=r['date_display'],inventory=r['accession_number'],dimensions=r['dimensions'],source_qualified_attribution_preserved=True))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,source_identity_verified=True,images_require_separate_review=True))
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
        artists=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))]
        inst=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,))]
        sources=[x['v'] for x in db.execute('SELECT to_jsonb(t) v FROM sources t WHERE id=ANY(%s::uuid[])',([h.uid('source/ireland/'+b.MUSEUM),'de4bd5ae-b280-4e0f-ba55-d462f47613d9'],))];assert len(sources)==1 and sources[0]['slug']=='wikimedia-commons'
        old=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
        h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,artworks=before,artists=artists,institutions=inst,sources=sources,preserved_artworks=old))
    files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz',backup/'preserved-existing-before.json.gz']
    for f in files:
        if f.suffix=='.gz':h.load(f)
    receipt=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,path=str(backup),files=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files],schema_archive_fully_decoded=True,all_json_exports_decoded=True,full_database_backup=False,cloud_backups_created=0,additional_locked_preimages_required=True,local_catalogue_connections=0,recovery='Reconcile exact source/plan/rights checksums and audit inserts against locked-before and image before-000 snapshots before corrective work; no recovery mutation executed.')
    b.save('local-recovery-verification.json',receipt);h.save(backup/'local-recovery-verification.json',receipt)
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,source_records=2,existing_artists=1,new_artists=0,new_institutions=0,holdings=2,all_sources_hashed_and_parsed=True,local_catalogue_connections=0,shared_ingestion_lock='artline-curated-ingestion'))
print('Two source identities and scoped recovery verified; metadata write ready.')
