#!/usr/bin/env python3
"""Bounded Russian-icon supplement using established production transactions."""
import fcntl,gzip,importlib.util,inspect,json,os,subprocess,sys,uuid
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base271','continuous-image-batch-000002.py');h=mod('metadata271','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000271';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000271'
OP='continuous-berlin-20261014-b000271';PHASE='berlin-icons';FIELD='continuous_berlin_object_evidence_20261014_b000271';B='berlin-271'
MUSEUM='Skulpturensammlung und Museum für Byzantinische Kunst, Staatliche Museen zu Berlin';MID='cf0f806e-05a5-5380-9a8d-c05f8b02b348';SCHEME='smb-native-object'
SELECTED=['1787252','1788551'];DATES={'1787252':('verbale Datierung: 17. Jahrhundert',1601,1700),'1788551':('verbale Datierung: 15. Jahrhundert',1401,1500)}
PAGES={'1787252':11,'1788551':17}
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.SCHEMES={'berlin':[SCHEME,'smb-object','museum-native-smb-object']}
old_uid=h.uid
SOURCE_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'continuous-berlin-20261011-b000036/source/berlin/'+MUSEUM))
h.uid=lambda k:SOURCE_ID if k=='source/berlin/'+MUSEUM else old_uid(k)
for p in [E,R,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();assert len([x for x in cmds if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x])==1
 with h.connect() as db:
  d=dict(db.execute("SELECT current_database() db,pg_is_in_recovery() recovery,current_setting('transaction_read_only') ro").fetchone());assert d==dict(db='artline',recovery=False,ro='on')
 return dict(at=h.now(),connection_name=actual,proxy_port=55519,proxy_inspected=True,database=d,helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),write=write,local_catalogue_connections=0)
def native(oid):
 rc=h.load(E/'source-captures'/('object-'+oid+'.receipt.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
 d=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NUXT_DATA__').string)
 def unpack(idx):
  if idx<0:return None
  v=d[idx]
  if isinstance(v,dict):return {k:unpack(n) for k,n in v.items()}
  if isinstance(v,list):
   if v and isinstance(v[0],str):return unpack(v[1]) if len(v)>1 else v
   return [unpack(n) for n in v]
  return v
 o=next(v for v in unpack(0)['data'].values() if isinstance(v,dict) and v.get('id')=='obj-'+oid);assert o==h.load(E/'objects'/(oid+'.json'));return o,rc
def no_collision(db,rows):
 ids=[r['source_id'] for r in rows];urls=[u for r in rows for u in r['identity_urls']];acc=[r['accession_number'] for r in rows]
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',(acc,)).fetchall(),'Accession collision requires reconciliation'
 assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme ILIKE '%%smb%%'",(ids,)).fetchall(),'Native collision'
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall(),'URL collision'
h.no_collision=no_collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User-authorized bounded continuous production batch271: two Russian icons; original titles, anonymous makers, Berlin collection and historical Frankfurt loan retained.')
code=code.replace("r['holding_basis']='Exact official collection object/caption and native identifier or inventory; archival metadata, not a display assertion.'","r['holding_basis']=r['ownership_custody_review']")
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==2 and all(not r['before'] for r in rows)")
code=code.replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace("scope='Documented collection record; no current display claim'","scope='Berlin collection ownership/affiliation only; Frankfurt historical loan documented 1999–2026; present physical custody and current display are not asserted'")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save('production-target-before-plan.json',target());book=h.load(E/'source-captures/booklet.receipt.json');assert h.sha(Path(book['body_path']).read_bytes())==book['sha256']
 rows=[];checks=[]
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(MID,)).fetchone()['v'];assert inst['name']==MUSEUM and inst['status']!='archived';h.museums=lambda:{MUSEUM:(inst['slug'],inst['website_url'])}
  assert db.execute('SELECT id FROM sources WHERE id=%s',(SOURCE_ID,)).fetchone()
  save('institution-reconciliation.json',dict(at=h.now(),existing_institution=inst,reused_source_id=SOURCE_ID,new_institutions=0,holding_relation='collection owner, not current physical custody'))
  scope=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=%s',(MID,))];h.save(E/'institution-scope-before.json.gz',scope)
  for oid in SELECTED:
   o,rc=native(oid);urls=[o['permalink'],'https://search.smb.museum/en/object/obj-'+oid,'https://search.smb.museum/object/obj-'+oid,'https://recherche.smb.museum/detail/'+oid]
   titles=[o['title']]+[x['nameLine'] for x in o.get('additionalTitles',[])]+(['Taufe Christi','Baptism of Christ'] if oid=='1787252' else ['Heiliger Theodor Tiro','Saint Theodore Tiro'])
   exact=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,current_institution_id::text,dimensions_text FROM artworks WHERE accession_number=%s OR (current_institution_id=%s AND normalized_title=ANY(%s))",(o['ident'],MID,[h.norm(x) for x in titles]))];assert not exact
   checks.append(dict(source_id=oid,inventory=o['ident'],title=o['title'],exact_matches=exact,aliases_checked=titles))
   date,lo,hi=DATES[oid];assert o['dating']==[dict(nameLine=date)] and not o['actors'] and o['org_unit']==MUSEUM.split(', Staatliche')[0]
   assert 'Dauerleihgabe' in o['html_text'] and not any(k in o['html_text'].lower() for k in ['kriegsverlust','verschollen'])
   front=o['images'][0];assert front['asset_content'] in ['Vorderseite','Aufsicht'] and front['obj_ref']==['obj:'+oid] and front['license']=='Public Domain Mark 1.0'
   ep=E/'objects'/(oid+'.json');dim='; '.join(x['nameLine'] for x in o['dimensions'])
   ownership='Exact SMB inventory '+o['ident']+' and official 2026 Frankfurt catalogue no. '+('10, printed pp.18–19' if oid=='1787252' else '23, printed pp.30–31')+' establish the Berlin collection and acquisition provenance. Frankfurt is explicitly a loan 1999–2026. The old 2020 online description still says long-term loan; actual return date and present custody are not verified. No current display or Frankfurt ownership claim.'
   rows.append(dict(provider='berlin',source_id=oid,source_url=urls[1],identity_urls=urls,museum=MUSEUM,title=o['title'],creator_label=None,creator_link_hold=True,culture='Russian',date_display=date,year_start=lo,year_end=hi,date_decision='eligible',accession_number=o['ident'],source_type='painting',medium=o['material_desc'],dimensions=dim,credit=None,raw=dict(native=o,dimensions=dim,original_title=o['title']),evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=rc['at'],sha256=h.sha(ep.read_bytes()),url=urls[1]),source_receipt=rc,identity_review='Exact inventory, subject, composition, dimensions and acquisition history crosschecked in official 2026 booklet; whole panel not reverse or detail.',date_basis='Conservative whole-century bounds preserve native source precision. Booklet narrows Theodore to second half of 15th century; native 15th-century date retained.',ownership_custody_review=ownership,secondary_source=book,secondary_pdf_page=PAGES[oid],secondary_source_review=dict(actually_viewed=True,source_dimension_difference='Native 24.5 x 23 x 3.5 cm; booklet 24.5 x 22 cm' if oid=='1787252' else 'Native 27 x 22 x 2.5 cm; booklet 27.2 x 21.9 cm',decision='Same native inventory and reproduced composition; both measurements retained without fabricated correction',source_dates_agree=True)))
  no_collision(db,rows)
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,selected=2,prior_french_additions_excluded=188,prior_berlin_held_ids_skipped=['1722054','1788002','1787214']))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE);p,pin=h.pinned(PHASE);assert len(p['records'])==2 and not p['new_institutions'] and not p['artists']
 save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=[dict(source_id=r['source_id'],source_sha256=r['evidence']['sha256'],raw_capture_sha256=r['source_receipt']['sha256'],booklet_sha256=book['sha256'],pdf_page=r['secondary_pdf_page'],review=r['secondary_source_review'],ownership_custody_review=r['ownership_custody_review']) for r in rows],no_artist_invented=True,all_before_empty=True))
def recover():
 if (E/'local-recovery-verification.json').exists():
  for f in h.load(E/'local-recovery-verification.json')['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
  return
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];save('production-target-before-backup.json',target());h.BACKUP.chmod(0o700)
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
 schema=h.BACKUP/'production-schema-before.pgdump'
 if not schema.exists():
  rr=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(schema)],env=env,capture_output=True,timeout=180);assert rr.returncode==0,'Scoped schema backup failed; stderr withheld to avoid credentials'
 rr=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(schema)],capture_output=True);assert rr.returncode==0 and b'TABLE public artworks' in rr.stdout
 with h.connect() as db:
  before=h.snapshot(db,ids);assert before=={};no_collision(db,p['records'])
 state=h.BACKUP/'affected-row-recovery-before.json.gz';h.save(state,dict(at=h.now(),plan_sha256=pin,artworks=before,planned_artwork_ids=ids))
 files=[schema,state,h.BACKUP/PHASE/'plan-preimages.json.gz'];v=dict(at=h.now(),status='VERIFIED',kind='schema_plus_exact_preimages',path=str(h.BACKUP),files=[dict(path=str(x),bytes=x.stat().st_size,sha256=h.sha(x.read_bytes())) for x in files],plan_sha256=pin,local_catalogue_connections=0)
 save('local-recovery-verification.json',v);h.save(h.BACKUP/'local-recovery-verification.json',v)
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 assert h.load(E/'independent-source-verification.json')['plan_sha256']==pin
 i.accepted(B)
 for f in h.load(E/'local-recovery-verification.json')['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 with h.connect() as db:
  existing=h.snapshot(db,ids)
  if existing:
   notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall();assert len(notes)==len(existing)==2 and all(x['pin']==pin for x in notes);assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={};print('Own committed plan reconciled');return
 save('production-target-before-metadata-write.json',target(True));h.apply(PHASE)
i.OP=OP+'-images';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=h.BACKUP/'images'
i.CFG['berlin']=dict(mid=MID,scheme=SCHEME,name=MUSEUM,rights='public_domain',license='Public Domain Mark 1.0',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='search.smb.museum')
old_image_uid=i.m.uid;i.m.uid=lambda k:SOURCE_ID if k=='source/berlin' else old_image_uid(k)
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'").replace("    tables['media_assets'].append","    credit=r.get('creator_credit',credit)\n    tables['media_assets'].append")
exec(compile(code,__file__,'exec'),i.__dict__)
def images():
 p,pin=h.pinned(PHASE);rows=[]
 for r in p['records']:
  o=r['raw']['native'];im=o['images'][0];url='https://search.smb.museum/media'+im['xl_path']
  rows.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label='',source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),provider='berlin',image=dict(image_url=url,source=o,receipt=r['source_receipt']),plan_sha256=pin,creator_credit=MUSEUM+' / '+im['photographer']+'. Public Domain Mark 1.0.',rights_basis='Native image '+im['id']+' explicitly Public Domain Mark 1.0; obj_ref exact; photographer retained. User production authorization is separate from rights designation.',manual_visual_required=True))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='berlin',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 i.ORIG.mkdir(parents=True,exist_ok=True)
 for r in rows:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B)
def deliver():
 for f in h.load(E/'local-recovery-verification.json')['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B);save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
