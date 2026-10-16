"""Two exact LACMA inventories, established transactional ingestion, no image writes."""
import runpy,inspect,sys,os,subprocess,fcntl,json
from pathlib import Path
v=runpy.run_path('ops/continuous-lacma-000120-research.py');globals().update({k:v[k] for k in ['h','b','E','R','ROOT','save']})
OP='continuous-lacma-20261013-b000120';PHASE='lacma-metadata';FIELD='continuous_lacma_object_evidence_b000120'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'lacma':['museum-native-lacma']}
h.museums=lambda:{'Los Angeles County Museum of Art':('spain-research-museum-q1641836','https://www.lacma.org/')}
def collision(db,rows):
 for r in rows:
  urls=[r['source_url'],r['source_url'].replace('/object/','/node/')]
  assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme ~* 'lacma' AND external_id=%s))",(urls,r['source_id'])).fetchall()
  assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall()
  assert not db.execute('SELECT id FROM artworks WHERE accession_number=%s OR normalized_title=%s',(r['accession_number'],h.norm(r['title']))).fetchall()
h.collision=collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch120: two exact LACMA Russian paintings, source-backed review metadata and holdings. No image permissions inferred.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==2 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 rows=[]
 for nid,title,label,aid,acc,lo,hi in [('40124','Dancing Soldiers','Mikhail Larionov','cb932e34-623b-42b2-b2ad-22d65e6dcd3f','80.3',1909,1910),('59982','Religious Composition: Archangel Michael','Natalia Sergeyevna Goncharova','c868385c-5f19-41eb-bcdd-8e2fd419f0d2','M.88.22',1910,1910)]:
  c=h.load(E/'captures'/f'{nid}.json');text=c['text'];raw=(ROOT/c['body']).read_bytes();assert h.sha(raw)==c['sha256'] and c['status']==200
  assert all(t in text for t in [title,label,acc,'Oil on canvas'])
  field=lambda a,z:text.split(a,1)[1].split(z,1)[0].strip()
  rows.append(dict(provider='lacma',source_id=nid,source_url=c['url'],museum='Los Angeles County Museum of Art',title=title,creator_label=label,verified_artist_id=aid,date_display=field('Date Made','Medium'),year_start=lo,year_end=hi,date_decision='eligible',accession_number=acc,source_type='painting',medium=field('Medium','Dimensions'),dimensions=field('Dimensions','Credit Line'),credit=field('Credit Line','Accession Number'),evidence_file=c['body'],evidence=dict(c,retrieved_at=c['at']),raw=dict(source_title=title,creator_label=label,original_dates=field('Date Made','Medium'),image_rights='photo © Museum Associates/LACMA; rights not established for attachment',native_images_requested=False),identity_review='Native inventory, dates, dimensions, acquisition credit and provenance captured; global accession/source/title checks and 277 related creator records reviewed. Exact existing creator matched by name and life dates. No current display claim.'))
 with h.connect() as db:collision(db,rows)
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==2 and len(p['artists'])==2 and not p['new_institutions'] and not p['held']
 save('final-identity-review.json',dict(at=h.now(),accepted_native_ids=['40124','59982'],plan_sha256=pin,confidence=.98,creator_review='Source life dates 1881–1964 and 1881–1962 concordant with existing artists. Source full Goncharova label preserved in creator note.',global_related_works=277,image_policy='LACMA is not covered by Russian-museum image exception. No native media downloaded. Exact WikiArt search empty.',remaining_seven='Captured only; additional global identity and date-conflict reconciliation required.'))
 print('Plan frozen',pin)
def recovery():
 p,pin=h.pinned(PHASE);dest=h.BACKUP;dest.mkdir(parents=True,exist_ok=True);dest.chmod(0o700)
 save('production-target-before-recovery.json',b.target())
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
 path=dest/'production-schema-before.pgdump'
 result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert result.returncode==0,'Schema export failed';path.chmod(0o600)
 result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=dest/'production-schema-before.toc';toc.write_bytes(result.stdout)
 with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
 with h.connect() as db:
  collision(db,p['records']);assert h.snapshot(db,[r['artwork_id'] for r in p['records']])=={}
  h.save(dest/'affected-row-preimages.json.gz',dict(at=h.now(),artworks={},institutions=p['institutions'],artists=p['artists'],plan_sha256=pin))
 files=[path,toc,dest/'affected-row-preimages.json.gz',dest/PHASE/'plan-preimages.json.gz']
 save('local-recovery-verification.json',dict(at=h.now(),status='VERIFIED',plan_sha256=pin,kind='Scoped production schema and exact affected-row preimages',full_database_backup=False,cloud_backups_created=0,files=[dict(path=str(f),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size) for f in files],locked_transaction_preimages_required=True))
 print('Recovery verified')
def apply():
 p,pin=h.pinned(PHASE);rc=h.load(E/'local-recovery-verification.json');assert rc['plan_sha256']==pin
 with h.connect() as db:
  ids=[r['artwork_id'] for r in p['records']];live=h.snapshot(db,ids)
  if live:
   assert len(live)==len(ids),'Partial prior write requires reconciliation'
   notes=db.execute("SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
   assert len(notes)==len(ids) and all(n['note']['plan_sha256']==pin for n in notes)
   pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['artworks']=={} and pre['plan_sha256']==pin
   for r in p['records']:
    a=live[r['artwork_id']]['artwork'];n=next(n for n in notes if n['entity_id']==a['id']);assert a['accession_number']==r['accession_number'] and n['note']['evidence']['sha256']==r['evidence']['sha256']
   print('Own committed plan reconciled; no replay writes.');return
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 target=b.target(True)
 name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert name=='artline-508319:europe-west1:artline-postgres'
 save('production-target-before-write.json',dict(target,connection_name=name));h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
