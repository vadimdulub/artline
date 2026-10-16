#!/usr/bin/env python3
"""One bounded continuation; reuses established selected-image ingestion, no supervisor."""
import importlib.util,sys,shutil,json,subprocess,hashlib,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
i=mod('images','illustrated-300k-20261011.py');h=mod('prod','india-300-delivery-20261011.py')
OLD=i.RUN;OLD_BACKUP=i.BACKUP;E=ROOT/'docs/research/continuous-production-20261011/batches/000007';B='rijks-000'
i.OP='continuous-primary-images-20261011-b000007';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
def connect(write=False,local=False):
 assert not local,'This bounded operation never connects to local catalogue'
 db=h.connect(write);db.autocommit=False;return db
i.m.m.connect=connect
save=i.saved;load=i.m.load

def target(write=False):
 lines=subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines();p=[x.strip() for x in lines if '/tmp/artline-cloud-sql-proxy ' in x and '55519' in x];assert len(p)==1 and 'artline-508319:europe-west1:artline-postgres' in p[0]
 with connect() as db:r=db.execute('SELECT current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone();assert r['db']=='artline' and not r['recovery']
 return dict(at=i.m.now(),proxy=p[0],database=r,write=write)

def prepare():
 f=mod("frenchcheck","continuous-image-batch-000004.py");f.E=E;f.french()
 if (i.folder(B)/'selection.json.gz').exists():
  target();print('Existing selection pinned; resume review, delivery or independent verification.');return
 if not (E/'production-target-reconciliation.json').exists():save(E/'production-target-reconciliation.json',target())
 registry=list(__import__('csv').DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')));assert len(registry)==111
 save(E/'rijks-source-register.json',dict(at=i.m.now(),registry=[r for r in registry if r['source_id']=='rijksmuseum'],holds={str(p):load(p) for p in (OLD/'access-holds').glob('*.json')},prior_campaign_complete=True,separate_campaign=i.OP))
 candidates=i.m.load(OLD/'batches/rijks-044/selection.json.gz')['rows'];prior=load(OLD/'batches/rijks-044/quality-audit.json');held=prior['identity_holds'];chosen=[];reconciled=[]
 with connect() as db:
  present={r['id']:r for r in db.execute('SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,current_institution_id::text,status,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[])',([r['artwork_id'] for r in candidates],))}
  for position,r in enumerate(candidates):
   a=present.get(r['artwork_id']);im=load(OLD/'batches/rijks-044/prepared'/(r['artwork_id']+'.json'))
   reason='eligible'
   if not a or a['status']=='archived':reason='missing_or_archived'
   elif a['primary_media_id']:reason='already_illustrated'
   elif r['artwork_id'] in held:reason='prior_identity_hold'
   elif im['state']!='prepared':reason='preparation_hold'
   elif im['flags']:reason='flagged_reserve_deferred'
   elif (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])!=(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],i.CFG['rijks']['mid']):reason='identity_fields_changed'
   elif db.execute('SELECT id FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchone():reason='existing_image_checksum'
   reconciled.append(dict(artwork_id=r['artwork_id'],position=position,reason=reason,primary_media_id=a['primary_media_id'] if a else None))
   if reason=='eligible':chosen.append((r,im,position))
   if len(chosen)==25:break
 save(E/'reserve-reconciliation.json',dict(at=i.m.now(),rows=reconciled,selected=len(chosen),resume_position=reconciled[-1]['position']+1))
 assert chosen,'No remaining eligible rows'
 save(i.folder(B)/'selection.json.gz',dict(provider='rijks',batch=B,rows=[x[0] for x in chosen],selection_basis='25 reconciled existing primary-image gaps, authentic prior prepared native museum images. Separate continuation campaign.'))
 save(i.folder(B)/'pin.json',dict(sha256=i.m.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r,im,pos in chosen:
  raw=Path(im['path']).read_bytes();assert i.m.sha(raw)==im['sha256'];sp=im['storage_path'].replace('illustrated-300k-20261011',i.OP);path=ROOT/'apps/web/public'/sp.lstrip('/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  im=dict(im,path=str(path),storage_path=sp,media_id=i.uid('media/'+r['artwork_id']+'/'+im['sha256']))
  save(i.folder(B)/'prepared'/(r['artwork_id']+'.json'),im)
 shutil.copyfile(OLD/'cloud-backup.json',E/'cloud-backup.json')
 i.audit(B)
 save(E/'CHECKPOINT.json',dict(stage='prepared_requires_actual_visual_review',batch=B,selected=len(chosen)))
 print('SHEET',load(i.folder(B)/'sheets/000.json')['path'])

if __name__=='__main__':
 runtime=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000007';runtime.mkdir(parents=True,exist_ok=True)
 worker_lock=(runtime/'worker.lock').open('a+');fcntl.flock(worker_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='deliver':
  checked=target(True)
  if not (E/'production-target-before-write.json').exists():save(E/'production-target-before-write.json',checked)
  i.upload(B);i.apply(B)
