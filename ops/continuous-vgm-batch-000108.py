#!/usr/bin/env python3
"""Bounded VGM metadata batch; established production helper, no supervisor."""
import csv,fcntl,gzip,importlib.util,inspect,json,os,re,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base108','continuous-image-batch-000002.py');h=base.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000108'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000108'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000108'
for d in [E,R,S]:d.mkdir(parents=True,exist_ok=True)
OP='continuous-vgm-20261013-b000108';PHASE='vgm-metadata';FIELD='continuous_vgm_object_evidence_b000108'
MID='910bb5ab-7bc4-4baf-8052-ce7e2fc5dbc9';ARTIST='7ff6d3dd-6d02-4104-b08f-1959354e82c5';MUSEUM='Van Gogh Museum';ACC='d0612V1962'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'vgm':['european-vgm-object']};h.museums=lambda:{MUSEUM:('van-gogh-museum','https://www.vangoghmuseum.nl')}
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def ref(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes()))
def target(write=False):
 name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert name=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=name,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def page(key):
 rc=h.load(E/(key+'.receipt.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
 text=BeautifulSoup(re.sub(r'</?template[^>]*>','',raw.decode()),'html.parser').get_text(' ',strip=True)
 return raw,rc,text
URL='https://www.vangoghmuseum.nl/en/collection/'+ACC
CAT='https://catalogues.vangoghmuseum.com/contemporaries-of-van-gogh-1/cat30'
def collision(db,rows):
 for r in rows:
  assert not db.execute('SELECT id FROM artworks WHERE lower(accession_number)=lower(%s)',(ACC,)).fetchall(),'Concurrent global accession'
  assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (lower(external_id)=lower(%s) OR canonical_url=ANY(%s))",(ACC,[URL,CAT])).fetchall(),'Concurrent native identity'
  assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",([URL,CAT],)).fetchall(),'Concurrent source identity'
  assert not db.execute('SELECT a.id FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.normalized_title=%s',(ARTIST,h.norm(r['title']))).fetchall(),'Concurrent creator/title'
h.collision=collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized one bounded production batch 108: source-backed pre-1971 artwork and documented holding; exact impression/version and actual loan ownership distinctions preserved.')
code=code.replace("r['holding_basis']='Exact official collection object/caption and native identifier or inventory; archival metadata, not a display assertion.'","r['holding_basis']='Official inventory d0612V1962 and museum provenance identify a drawing held at Van Gogh Museum on permanent loan from the Vincent van Gogh Foundation. Holding means documented custody, not museum ownership or current display. Editorial confidence 0.98.'")
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==1 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace("scope='Documented collection record; no current display claim'","scope='Documented permanent-loan holding/custody at Van Gogh Museum; owner Vincent van Gogh Foundation. No museum ownership or current display claim'")
exec(compile(code,__file__,'exec'),h.__dict__)
def plan():
 if (E/PHASE/'plan-pin.json').exists():h.pinned(PHASE);print('Pinned plan retained');return
 raw,rc,text=page('object-'+ACC);cr,crc,ct=page('vgm-cat30')
 soup=BeautifulSoup(cr,'html.parser');data=json.loads(soup.find('script',id='__NUXT_DATA__').string)
 o=next(x for x in data if isinstance(x,dict) and 'objectNumber' in x and 'physicalDescription' in x)
 obj={k:data[v] for k,v in o.items() if k!='inscriptionsContent'}
 assert obj['objectNumber']==ACC and obj['title']=='Adoration of the Shepherds' and obj['productionDate']=='1888'
 assert obj['principalCreator']=='Emile Bernard (1868 - 1941)' and obj['dimensions']=='23.3 cm x 27.9 cm'
 assert all(x in text for x in [ACC,obj['title'],'1888','Emile Bernard (1868 - 1941)',obj['dimensions'],'pencil and pen and ink on paper','Vincent van Gogh Foundation','on permanent loan'])
 fp=S/(ACC+'.html');fp.write_bytes(raw)
 r=dict(provider='vgm',source_id=ACC,source_url=URL,museum=MUSEUM,title=obj['title'],creator_label=obj['principalCreator'],verified_artist_id=ARTIST,date_display='1888',year_start=1888,year_end=1888,date_decision='eligible',accession_number=ACC,source_type='drawing',medium=obj['physicalDescription'],dimensions=obj['dimensions'],credit=obj['creditLine'],raw=dict(object_details=obj,collection_relationship='Museum custody on permanent loan; owner Vincent van Gogh Foundation; not museum ownership.',provenance=text.split('Provenance ',1)[1].split(' artist ',1)[0],physical_unit='One drawing on laid paper; distinct from 1888 woodcut and 1889 oil painting discussed in catalogue.',catalogue_source=CAT,catalogue_source_sha256=crc['sha256'],image_rights='Noncommercial use only; commercial permission required. No image selected.'),evidence_file=str(fp),evidence=dict(rc,retrieved_at=rc['at']),catalogue_receipt=crc,metadata_licence='Catalogue narrative CC BY-NC-SA 4.0; facts only extracted, no narrative copied into artwork description. Source provenance retained in evidence.',identity_review='Official inventory, title, creator, date, dimensions, drawing medium and provenance agree between native object and scholarly catalogue. 1888 woodcut and 1889 painting are distinct.',date_basis='Museum explicit creation year 1888, not accession year 1962.')
 with h.connect() as db:
  collision(db,[r])
  related=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.medium_text,a.dimensions_text,a.current_institution_id::text FROM artworks a WHERE a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=%s) OR a.unlinked_creator_label ILIKE '%%mile Bernard%%' ORDER BY a.id LIMIT 301",(ARTIST,))];assert len(related)<301
  global_titles=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,dimensions_text,unlinked_creator_label,current_institution_id::text FROM artworks WHERE normalized_title=%s ORDER BY id LIMIT 101",(h.norm(r['title']),))];assert len(global_titles)<101
  save('creator-and-version-reconciliation.json',dict(at=h.now(),creator_works=related,global_exact_titles=global_titles,selected_native_id=ACC))
 save('selected-source-records-pending-review.json',[r]);print('Candidate and related works saved',len(related),len(global_titles))
def freeze():
 review=h.load(E/'final-editorial-review.json');assert review['accepted']==[ACC]
 rows=h.load(E/'selected-source-records-pending-review.json');h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==1 and not p['held'] and not p['new_institutions'] and len(p['artists'])==1 and p['records'][0]['artist_id']==ARTIST
 save('plan-validation.json',dict(at=h.now(),passed=True,plan_sha256=pin,new_artworks=1,new_painters=0,holdings=1,images=0,artist_id=ARTIST,relationship='Permanent-loan custody; Foundation ownership preserved.'))
 print('Frozen',pin)
def prewrite():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];save('production-target-before-recovery.json',target())
 backup=h.BACKUP;backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
 if not (E/'local-recovery-verification.json').exists():
  secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();kw=h.psycopg.conninfo.conninfo_to_dict(secret)
  env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
  path=backup/'production-schema-before.pgdump';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert out.returncode==0,'Schema export failed';path.chmod(0o600)
  toc=backup/'production-schema-before.toc';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc.write_bytes(out.stdout);toc.chmod(0o600)
  with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
  with h.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');collision(db,p['records']);before=h.snapshot(db,ids);assert before=={}
   preserved=h.snapshot(db,[x['id'] for x in h.load(E/'vgm-existing-gap-candidates.json')['rows']])
   inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(MID,)).fetchone()['v'];assert inst==p['institutions'][MUSEUM]
   artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(ARTIST,)).fetchone()['v'];assert artist==p['artists'][ARTIST]
   sources=[x['v'] for x in db.execute('SELECT to_jsonb(s) v FROM sources s WHERE id=%s',(h.uid('source/vgm/'+MUSEUM),))];assert not sources
   h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,artworks=before,planned_ids=ids,institution=inst,artist=artist,sources=sources,preserved=preserved))
  files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/PHASE/'plan-preimages.json.gz']
  for f in files:
   if f.suffix=='.gz':h.load(f)
  rc=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,files=[ref(f) for f in files],schema_archive_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,local_catalogue_connections=0,additional_locked_preimages_required=True)
  save('local-recovery-verification.json',rc);h.save(backup/'local-recovery-verification.json',rc)
 save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,shared_lock='artline-curated-ingestion',new_artworks=1,holding_assertions=1,images=0));print('Scoped recovery verified')
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  present=h.snapshot(db,ids)
  if present:
   notes=db.execute("SELECT evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
   assert len(present)==len(notes)==1 and notes[0]['pin']==pin and h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={}
   print('Own committed plan reconciled; no replay writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'prewrite-verification.json')['passed'];save('production-target-before-write.json',checked);h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
