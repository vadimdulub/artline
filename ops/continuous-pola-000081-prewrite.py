#!/usr/bin/env python3
"""Independent source checks and scoped production recovery; no catalogue writes."""
import fcntl,importlib.util,json,gzip,re,subprocess,os
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-pola-000081.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];assert len(ids)==9
 shrc=h.load(b.E.parent/'000076/shuzo-kishida-page1-capture.json');shraw=gzip.decompress(Path(shrc['body_path']).read_bytes());assert h.sha(shraw)==shrc['sha256'];xs=json.loads(shraw)['data']['searchWorks']['items'];checks=[]
 for r in p['records']:
  raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
  sp=BeautifulSoup(raw,'html.parser');text=sp.select_one('main').get_text(' ',strip=True);x=next(v for v in xs if v['id']==r['raw']['shuzo_id'])
  assert x['accessionNumber']==r['accession_number']==r['source_id'] and r['source_url'].rstrip('/').endswith('/'+r['accession_number'])
  assert all(v in text for v in [x['title']['ja'],x['medium'][0]['ja'],x['yearLabel']['ja'],x['dimension']['ja'],'岸田劉生','ポーラ美術館が収蔵する'])
  assert r['title']==x['title']['en'] and r['date_display']==x['yearLabel']['en'] and r['first']==r['last']==int(re.search(r'\d{4}',r['date_display'])[0])<=1970
  assert r['precision']==('circa' if r['date_display'].startswith('ca.') else 'exact') and r['artist_id']==b.ARTIST and r['institution_id']==b.MID and not r['before'] and r['add_holding']
  assert 'exhibition' not in r['raw'] and r['raw']['native_images_requested'] is False
  if r['source_id']=='997-0090':assert r['raw']['medium'][0]['en']=='Color on paper, flamed' and r['medium']=='Color on paper, framed' and r['raw']['medium'][0]['ja']=='紙本彩色/額装'
  checks.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],shuzo_id=x['id'],native_sha256=r['evidence']['sha256'],shuzo_sha256=shrc['sha256'],title=r['title'],original_title=x['title']['ja'],date=r['date_display'],dimensions=r['dimensions'],source_fields_independently_verified=True))
 # Verify the other same-title Reiko work from already captured museum-contributed metadata.
 tokyo=next(x for x in xs if x['id']=='W107155');assert tokyo['accessionNumber']=='A-10568' and tokyo['yearLabel']['ja']=='大正10年(1921)' and tokyo['medium'][0]['en']=='Oil on canvas' and tokyo['dimension']['ja']=='44.2×36.4'
 rights=h.load(b.E/'pola-terms-capture.json');raw=gzip.decompress(Path(rights['body_path']).read_bytes());assert h.sha(raw)==rights['sha256'];txt=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert '無断で転載・複製・改変・頒布・使用することを禁止' in txt
 terms=h.load(b.E.parent/'000076/shuzo-terms-current-capture.json');traw=gzip.decompress(Path(terms['body_path']).read_bytes());assert h.sha(traw)==terms['sha256'];assert 'Attribution' in BeautifulSoup(traw,'html.parser').get_text(' ',strip=True)
 b.save('prewrite-source-verification.json',dict(at=h.now(),metadata_plan_sha256=pin,records=checks,source_attribution_recorded=True,shuzo_terms=b.ref(b.E.parent/'000076/shuzo-terms-current-capture.json'),pola_rights=b.ref(b.E/'pola-terms-capture.json'),images_selected=0,images_downloaded=0,actual_images_viewed=0,grouped_originals_held=['W33645'],version_separation='Pola 1922 watercolor distinct from Tokyo 1921 oil; both exact dimension and material evidence corroborated.'))
 b.save('production-target-before-scoped-recovery.json',b.target())
 backup=h.BACKUP;backup.chmod(0o700)
 if not (b.E/'local-recovery-verification.json').exists():
  secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
  kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
  path=backup/'production-schema-before.pgdump';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert out.returncode==0,'Schema export failed';path.chmod(0o600)
  toc=backup/'production-schema-before.toc';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc.write_bytes(out.stdout);toc.chmod(0o600)
  with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
  with h.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.collision(db,p['records']);before=h.snapshot(db,ids);assert not before
   artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.ARTIST,)).fetchone()['v'];assert artist==p['artists'][b.ARTIST]
   old=h.load(b.E/'global-identity-reconciliation.json')['existing_creator_works'];old.update(h.snapshot(db,[x['id'] for x in h.load(b.E/'global-unlinked-creator-works.json')]))
   assert len(old)==13 and h.snapshot(db,list(old))==old
   h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,artworks=before,artists=[artist],institutions=[],sources=[],preserved=old))
   for r in p['records']:assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['first'],r['last'],r['precision'])).fetchone()['scope']=='eligible'
  files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz']
  for f in files:
   if f.suffix=='.gz':h.load(f)
  rc=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,files=[b.ref(f) for f in files],schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,additional_locked_preimages_required=True,local_catalogue_connections=0,recovery='Reconcile own plan/source checksums and insert audit events against locked empty preimages before recovery. Retain unrelated records and audit history; no recovery mutation performed.')
  b.save('local-recovery-verification.json',rc);h.save(backup/'local-recovery-verification.json',rc)
 b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,new_artworks=9,new_artists=0,new_institutions=1,source_checks=9,holdings=9,images_selected=0,shared_ingestion_lock='artline-curated-ingestion',recovery=b.ref(b.E/'local-recovery-verification.json'),local_catalogue_connections=0))
 print('Nine sources, exact-version distinctions and scoped recovery verified.')
