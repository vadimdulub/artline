#!/usr/bin/env python3
"""One bounded museum batch using established production and image helpers."""
import csv,fcntl,gzip,importlib.util,inspect,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'Library/Application Support/Artline/continuous-research/batches/000003/dependencies'))
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('bounded_metadata','india-300-delivery-20261011.py')
original_save=h.save
def save_stable(path,value):
 if path.exists():
  actual=h.load(path);expected=h.safe(value)
  def without_check_times(v):
   if isinstance(v,dict):return {k:without_check_times(x) for k,x in v.items() if k!='at'}
   if isinstance(v,list):return [without_check_times(x) for x in v]
   return v
  assert without_check_times(actual)==without_check_times(expected),'Existing immutable evidence changed: '+str(path)
  return
 original_save(path,value)
h.save=save_stable
i=module('bounded_images','illustrated-300k-20261011.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000003'
OP='continuous-icons-20261011-b000003';PHASE='selected';B='cleveland-000'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000003'
IID='729385eb-92b0-4cc8-9229-1ac3a46aee1f';MUSEUM='The Cleveland Museum of Art'
h.OP=OP;h.RUN=E;h.BACKUP=BACKUP
h.SCHEMES['cleveland']=['continuous-cleveland-object','cleveland-object','museum-expansion-cleveland-object','museum-native-cleveland-object']
h.museums=lambda:{MUSEUM:('cleveland-museum-of-art','https://www.clevelandart.org/')}
# Retain the established validation and transaction implementation, adjusting
# only this batch's scope, authorization, minimum, and audit field name.
src=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User-authorized continuous source-backed production enrichment, bounded batch 000003. Only independently verified new physical objects count.')
exec(compile(src,__file__,'exec'),h.__dict__)
src=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300", "assert 1<=sum(not r['before'] for r in rows)<=50").replace('india_minimum_300_museum_coverage_20261011','continuous_museum_batch_000003')
src=src.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'", "  concurrent=db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall();assert not concurrent,'Concurrent inventory identity; replan instead of duplicate insertion'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(src,__file__,'exec'),h.__dict__)
i.OP=OP;i.RUN=E;i.BACKUP=BACKUP;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP
def connect(write=False,local=False):
 assert not local,'Real local catalogue is never connected'
 db=h.connect(write);db.autocommit=False;return db
i.m.m.connect=connect
i.CFG['cleveland']=dict(mid=IID,scheme='continuous-cleveland-object',name=MUSEUM,rights='cc0',license='CC0 1.0',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='openaccess-cdn.clevelandart.org',limit=2)
old_uid=i.m.uid
i.m.uid=lambda key:h.uid('source/cleveland/'+MUSEUM) if key=='source/cleveland' else old_uid(key)
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 commands=subprocess.check_output(['ps','ax','-o','command'],text=True).splitlines()
 assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x for x in commands)
 with h.connect() as db:
  state=db.execute('SELECT current_database() db,pg_is_in_recovery() recovery').fetchone();assert state['db']=='artline' and not state['recovery']
 return dict(at=h.now(),connection_name=actual,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',database=state,local_catalogue_connections=0)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 registry_path=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(registry_path.open()));assert len(registry)==111
 h.save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry_path),registry_sha256=h.sha(registry_path.read_bytes()),registry_records=111,sources=[x for x in registry if x['source_id'] in ['national_gallery_athens','walters_art_museum','cleveland_museum']],policy_reference='docs/ARTLINE_IMAGE_USE.md',walters_access_hold=h.load(E/'walters/57.1818.receipt.json'),retained_holds=['docs/research/museum-expansion-20261006/athens-followup-holds.json','docs/research/russian-icon-images-20260921/commons-search-hold.json','docs/research/illustrated-300k-20261011/access-holds/www.ernstfuchs-zentrum.com.json']))
 h.save(E/'production-target-before-plan.json',target())
 rows=[];global_review=[]
 with h.connect() as db:
  for native in [129825,149363]:
   rc=h.load(E/'captures'/(str(native)+'.json.gz'));raw=gzip.decompress((E/'captures'/(str(native)+'.body.gz')).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
   obj=json.loads(raw)['data'];assert obj['id']==native and obj['share_license_status']=='CC0' and obj['creators']==[]
   urls=[obj['url'],obj['url'].replace('https://clevelandart.org','https://www.clevelandart.org')];wiki=obj['external_resources'].get('wikidata',[])
   matches=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((canonical_url=ANY(%s)) OR (scheme ILIKE '%%cleveland%%' AND external_id=%s) OR (scheme='wikidata' AND external_id=ANY(%s)))",(urls,str(native),[u.rsplit('/',1)[-1] for u in wiki]))]
   citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
   assert not matches and not citations,'Global existing identity requires reconciliation'
   global_review.append(dict(native_id=native,urls=urls,external_matches=matches,citation_matches=citations))
   rows.append(dict(provider='cleveland',source_id=str(native),museum=MUSEUM,title=obj['title'],date_display=obj['creation_date'],year_start=obj['creation_date_earliest'],year_end=obj['creation_date_latest'],date_decision='eligible',source_type=obj['type'],creator_label=None,creator_link_hold=True,culture=obj['culture'],accession_number=obj['accession_number'],medium=obj['technique'],dimensions=obj['measurements'],credit=obj['creditline'],source_url=obj['url'],evidence=rc,raw=obj,identity_review='Complete accessioned surviving object; not a generated crop, triptych component, pendant component, or a duplicate ensemble. Frame has its own accession and provenance. Textile title retains the uncertain subject (?) and physical fragment identity. No invented painter or Byzantine classification.'))
 h.save(E/'global-identity-review.json',dict(at=h.now(),records=global_review,excluded_components=[128825,128826,136863,136864,136865],reason='Existing parent pendant or triptych has catalogue representation; do not inflate new physical object totals with components.'))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 plan,pin=h.pinned(PHASE);assert len(plan['records'])==2 and all(not r['before'] for r in plan['records'])
 image_rows=[]
 for r in plan['records']:
  obj=r['raw'];rc=r['evidence'];image_rows.append(dict(artwork_id=r['artwork_id'],provider='cleveland',native_id=r['source_id'],title=r['title'],creator_label='Creator not named by source',source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),plan_sha256=pin,image=dict(image_url=obj['images']['web']['url'],source=obj,receipt=rc),rights_basis='Official object API explicitly supplies share_license_status CC0 for the supplied primary image; user approval recorded separately.'))
 i.saved(i.folder(B)/'selection.json.gz',dict(provider='cleveland',batch=B,rows=image_rows));i.saved(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 i.ORIG.mkdir(parents=True,exist_ok=True)
 for r in image_rows:i.prepare_one(r,B)
 i.audit(B)
 h.save(E/'authorization.json',dict(at=h.now(),production_inserts_and_images=True,user_instruction='Continuously discover and add verified source-backed production objects and authentic images, bounded batch 3; no per-batch approval. Real local catalogue read-only.',copyright_holder_license='CC0 as supplied by this source, separately from user authorization.'))
 print('SHEETS',[(str(x),h.load(x)['path']) for x in (i.folder(B)/'sheets').glob('*.json')],flush=True)
def backup():
 rc=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert rc['status']=='SUCCESSFUL'
 h.save(E/'cloud-sql-backup.json',rc);h.save(E/'cloud-backup.json',rc);h.save(BACKUP/'cloud-sql-backup.json',rc)
def deliver():
 assert (i.folder(B)/'visual-review.json').exists();backup()
 if not(E/PHASE/'applied.json').exists():
  plan,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in plan['records']]
  with h.connect() as db:
   present=h.snapshot(db,ids)
   if present:
    assert set(present)==set(ids),'Partial uncertain metadata transaction; never replay'
    before=h.load(BACKUP/PHASE/'locked-before.json.gz');assert before['artworks']=={} and before['plan_sha256']==pin
    notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name='continuous_museum_batch_000003'",(ids,)).fetchall();assert len(notes)==len(ids) and all(n['pin']==pin for n in notes)
    h.save(E/PHASE/'applied.json',dict(at=h.now(),recovered=True,plan_sha256=pin,artwork_ids=ids,policy='Recovered own attributed transaction from empty locked preimages and persisted source citations; increments still require independent verification.'))
  if not present:h.save(E/'production-target-before-metadata-write.json',target());h.apply(PHASE)
 i.upload(B)
 if not(i.folder(B)/'applied/000.json').exists():h.save(E/'production-target-before-image-write.json',target());i.apply(B)
if __name__=='__main__':
 RUNTIME.mkdir(parents=True,exist_ok=True)
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  dict(stage=stage,backup=backup,deliver=deliver)[sys.argv[1]]()
