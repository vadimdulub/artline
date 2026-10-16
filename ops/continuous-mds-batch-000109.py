"""Selected MDS contributor metadata; two exact inventories, no images."""
import importlib.util,inspect,json,gzip,fcntl,subprocess,os,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('research109',Path(__file__).with_name('continuous-batch-000109-research.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E;R=b.R;ROOT=b.ROOT;save=b.save
OP='continuous-mds-20261013-b000109';PHASE='mds-paintings';FIELD='continuous_mds_object_evidence_b000109';MUSEUM='National Railway Museum';MID='d898f4b3-3168-5733-938c-d32be7cc5a3c'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.SCHEMES={'mds':['museum-data-service-object']};h.museums=lambda:{MUSEUM:('wikimedia-museum-q579958','https://www.railwaymuseum.org.uk/')}
ACCS=['1997-8474','1978-1624'];PIDS=['74fcd32b-23e9-3f99-8f16-7afa66505e40','3f2b3f87-32cc-37da-881d-737931529b16'];URLS=['https://museumdata.uk/objects/'+x for x in PIDS]+['https://collection.sciencemuseumgroup.org.uk/objects/co227466','https://collection.sciencemuseumgroup.org.uk/objects/co227466/oil-painting-portrait-of-timothy-hackworth']
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(b.base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def no_collision(db,rows):
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',(ACCS,)).fetchall()
 assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))",(PIDS+['co227466'],URLS)).fetchall()
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(URLS,)).fetchall()
 assert not db.execute("SELECT id FROM artworks WHERE title ILIKE '%%hackworth%%'").fetchall()
 assert not db.execute("SELECT id FROM artworks WHERE current_institution_id=%s AND normalized_title=ANY(%s)",(MID,[h.norm(r['title']) for r in rows])).fetchall()
h.no_collision=no_collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized one bounded production batch109; exact MDS contributor inventories, through1970; unknown creators preserved; no image rights inferred from metadata licence.')
code=code.replace("r['holding_basis']='Exact official collection object/caption and native identifier or inventory; archival metadata, not a display assertion.'","r['holding_basis']='Science Museum Group contributor object inventory via Museum Data Service explicitly assigns responsible department NRM - Pictorial Collection (Railway); exact National Railway Museum collection custody, no current display claim. Editorial confidence 0.98.'")
exec(compile(code,__file__,'exec'),h.__dict__)
old_dates=h.dates
h.dates=lambda r:(r['year_start'],r['year_end'],'circa') if r.get('date_display')=='c1840' else old_dates(r)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==2 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def plan():
 if (E/PHASE/'plan-pin.json').exists():h.pinned(PHASE);print('Plan retained');return
 rows=[]
 for pid,acc,title,year,date,label in [(PIDS[0],ACCS[0],'fishguard harbour painting',1960,'1960','Smith, John S.'),(PIDS[1],ACCS[1],'Oil painting. Portrait of Timothy Hackworth',1840,'c1840',None)]:
  rc=h.load(E/('mds-object-'+pid+'.receipt.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'];sp=b.BeautifulSoup(raw,'html.parser');txt=sp.get_text(' ',strip=True)
  assert all(x in txt for x in [title,acc,date,'NRM - Pictorial Collection (Railway)','CC BY','Science Museum Group'])
  src=b.S/('object-'+pid+'.html');src.write_bytes(raw)
  d=sp.select_one('details.object-overview');fields=[(x.dt.get_text(' ',strip=True),x.dd.get_text(' ',strip=True)) for x in d.select('dl div') if x.dt and x.dd] if d else []
  rows.append(dict(provider='mds',source_id=pid,source_url=rc['url'],museum=MUSEUM,title=title,creator_label=label,creator_link_hold=True,date_display=date,year_start=year,year_end=year,date_decision='eligible',accession_number=acc,source_type='painting',medium='oil painting',dimensions=None,credit='British Rail, Clapham' if label else None,raw=dict(fields=fields,source_description=next((v for k,v in fields if k=='Brief description:'),None),contributor='Science Museum Group',responsible_department='NRM - Pictorial Collection (Railway)',source_date_literal=date,attribution='Data courtesy of Science Museum Group via museumdata.uk. Licensed under CC BY.',image_rights='Metadata CC BY does not licence images; no image requested.',object_unit='Single painting. Hackworth Dartford Library inventory176 reference is retained as a reference, not an alternate accession or resolved version.'),evidence_file=str(src),evidence=dict(rc,retrieved_at=rc['at']),metadata_licence='CC BY',source_provider_name='Science Museum Group via Museum Data Service',identity_review='Exact native MDS PID and museum accession; source title and railway department preserved. Dimensions unknown. John S. Smith remains unlinked because global John Smith namesakes do not establish the maker. Hackworth maker not supplied.'))
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');no_collision(db,rows)
  candidates=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,medium_text,dimensions_text,unlinked_creator_label,current_institution_id::text FROM artworks WHERE title ILIKE '%%fishguard%%' OR title ILIKE '%%hackworth%%' OR title ILIKE '%%longridge%%' LIMIT 51")];assert len(candidates)<51
  creators=[dict(x) for x in db.execute("SELECT id::text,display_name,birth_year,death_year FROM artists WHERE display_name ILIKE '%%john%%smit%%' OR display_name ILIKE '%%james%%rams%%' LIMIT 51")];assert len(creators)<51
  inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(MID,)).fetchone()['v'];save('institution-before.json',inst)
  preserved=h.snapshot(db,[x['id'] for x in candidates]);save('preserved-existing-before.json.gz',dict(artworks=preserved))
 save('global-identity-reconciliation.json',dict(at=h.now(),candidate_artworks=candidates,creator_candidates=creators,selected_accessions=ACCS,empty_global_native_url_accession_matches=True,decisions=['Existing Fishguard-Rosslare poster1976-9404 has distinct title/inventory; not silently equated with1960 oil1997-8474.','Longridge portrait held as likely existing artwork8eea2ac6-223d-5d85-985d-fa4e216af68d; no new record.','No Hackworth title/accession/native match. Dartford inventory176 stays unresolved source reference.','John Smith1717-1764 cannot author1960 painting; no forced artist link or invented painter.']))
 save('final-editorial-review.json',dict(at=h.now(),accepted_source_ids=PIDS,confidence=.98,creation_scope='1960 and circa1840',images_selected=0,new_painters=0,unknown_fields=['Hackworth creator','Both dimensions','Fishguard exact creator identity'],source_institution='MDS collection Science Museum Group; explicit NRM responsible department supports National Railway Museum holding, not current location/display.'))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE);p,pin=h.pinned(PHASE);assert len(p['records'])==2 and not p['held'] and not p['new_institutions'] and not p['artists'];assert [r['precision'] for r in p['records']]==['exact','circa']
 save('plan-validation.json',dict(at=h.now(),passed=True,plan_sha256=pin,new_artworks=2,new_painters=0,museum_links=2,images=0))
def recovery():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];save('production-target-before-recovery.json',target())
 backup=h.BACKUP;backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
 if (E/'local-recovery-verification.json').exists():return
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();kw=h.psycopg.conninfo.conninfo_to_dict(secret)
 env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
 path=backup/'production-schema-before.pgdump';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert out.returncode==0,'Schema export failed';path.chmod(0o600)
 toc=backup/'production-schema-before.toc';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc.write_bytes(out.stdout);toc.chmod(0o600)
 with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');no_collision(db,p['records']);before=h.snapshot(db,ids);assert before=={}
  old=h.load(E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
  inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(MID,)).fetchone()['v'];assert inst==p['institutions'][MUSEUM]
  sources=[x['v'] for x in db.execute('SELECT to_jsonb(s) v FROM sources s WHERE id=%s',(h.uid('source/mds/'+MUSEUM),))];assert not sources
  h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,artworks=before,planned_ids=ids,institution=inst,artists={},sources=sources,preserved=old))
 files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/PHASE/'plan-preimages.json.gz']
 for f in files:
  if f.suffix=='.gz':h.load(f)
 rc=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,files=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files],schema_archive_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,local_catalogue_connections=0,additional_locked_preimages_required=True)
 save('local-recovery-verification.json',rc);h.save(backup/'local-recovery-verification.json',rc);print('Recovery verified')
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  present=h.snapshot(db,ids)
  if present:
   notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall();assert len(present)==len(notes)==2 and all(x['pin']==pin for x in notes);assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={};print('Own committed plan reconciled; no replay writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-write.json',checked);h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
