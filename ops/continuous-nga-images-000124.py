#!/usr/bin/env python3
"""Bounded French reconciliation then NGA native primary-image enrichment."""
import importlib.util,json,sys,subprocess,gzip,fcntl,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base','continuous-image-batch-000002.py');i=base.i;h=base.h
OLD=base.OLD;P=ROOT/'docs/research/continuous-production-20261011/batches/000124';E=P/'nga';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000124';B='nga-000'
i.OP='continuous-primary-images-20261011-b000124-nga';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
original_save=i.saved
def save(path,value):
 if path.exists():return i.m.load(path)
 return original_save(path,value)
load=i.m.load;connect=base.connect;target0=base.target
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(target0(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
import ast
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text();node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply');code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'preparation-production-snapshot.json.gz')['before'][aid],'Full selected identity changed since selection'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    citation=m.load(RUN/'source-citation-pin-verification.json')['citations'][aid]\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND evidence_note=%s\",(aid,citation['field_name'],citation['evidence_note'])).fetchone(),'Pinned source citation changed'")
exec(compile(code,__file__,'exec'),i.__dict__)
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def prepare():
 # French reserve already reconciled in batch 19
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  return finish_preparation(i.selected(B)['rows'])
 save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(__import__('csv').DictReader(registry.open()));assert len(rs)==111
 holds={str(p.relative_to(ROOT)):load(p) for p in (OLD/'access-holds').glob('*.json')}
 save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,sources=[r for r in rs if r['source_id'] in ['nga_washington','yale_lux']],policy_reference='docs/ARTLINE_IMAGE_USE.md',retained_access_holds=holds))
 assert not (OLD/'access-holds/api.nga.gov.json').exists()
 planpath=i.m.RUN/'nga/plan-v2.json.gz';plan=load(planpath);pin=h.sha(planpath.read_bytes());excluded=set()
 for p in (OLD/'batches').glob('nga-*/quality-audit.json'):excluded.update(load(p)['identity_holds'])
 for p in (OLD/'batches').glob('nga-*/visual-review.json'):excluded.update(x['artwork_id'] for x in load(p)['decisions'] if x['decision']!='accept')
 for reviewpath in P.parent.glob('*/batches/nga-*/visual-review.json'):
  excluded.update(x['artwork_id'] for x in load(reviewpath)['decisions'] if x['decision']!='accept')
 candidates=[r for r in plan['new_artworks'] if i.native_image('nga',r)];reconciled=[];chosen=[];creators=collections.Counter()
 cursor=next(x for x in load(P/'source-queue-before.json')['sources'] if x['source_id']=='nga_washington')['resume_cursor']['position']
 save(E/'source-queue-before.json',load(P/'source-queue-before.json'))
 for filename in ['required-input-reconciliation.json','completed-campaign-stop-preservation.json']:save(E/filename,load(P/filename))
 ledgers=list(P.parent.glob('*/access-holds/*.json'))+list(P.parent.glob('*/*/access-holds/*.json'))+list((OLD/'access-holds').glob('*.json'))
 assert not any('api.nga.gov' in p.name for p in ledgers),'Preserve NGA access holds'
 save(E/'source-access-holds.json',dict(at=h.now(),checked=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in ledgers],nga_held=False))
 with connect() as db:
  present={}
  for part in i.m.chunks([r['artwork_id'] for r in candidates[cursor:cursor+500]],500):present.update({x['id']:x for x in db.execute('SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,current_institution_id::text,status,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[])',(part,))})
  for position,r in enumerate(candidates):
   if position<cursor:continue
   if position>=cursor+500:break
   a=present.get(r['artwork_id']);reason='eligible'
   if not a or a['status']=='archived':reason='missing_or_archived'
   elif a['primary_media_id']:reason='already_illustrated'
   elif r['artwork_id'] in excluded:reason='immutable_prior_identity_or_visual_hold'
   elif (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])!=(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],i.CFG['nga']['mid']):reason='source_identity_changed'
   elif r['work_type'] not in ['painting','drawing','watercolor','print','icon']:reason='excluded_medium_for_pictorial_gap_batch'
   elif creators[r['creator_label']]>=2:reason='creator_variety_deferred'
   if reason=='eligible':
    keep={k:r[k] for k in ['artwork_id','native_id','title','creator_label','source_url','accession_number','first','last','precision','work_type']}
    chosen.append(dict(keep,provider='nga',image=i.native_image('nga',r),plan_path=str(planpath),plan_sha256=pin));creators[r['creator_label']]+=1
   reconciled.append(dict(artwork_id=r['artwork_id'],position=position,reason=reason))
   if len(chosen)==8:break
  if chosen:
   ids=[r['artwork_id'] for r in chosen];before=h.snapshot(db,ids)
   save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before=before))
   own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own,'Unknown prior own write requires reconciliation'
 assert chosen
 save(E/'nga-gap-reconciliation.json',dict(at=h.now(),candidate_count=len(candidates),selected=len(chosen),prior_holds_excluded=sorted(excluded),rows=reconciled,resume_position=position+1,policy='Earlier delivered objects excluded, max two per creator for varied bounded selection; deferred earlier positions retained.'))
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='nga',batch=B,rows=chosen,selection_basis='Fresh production gaps beyond prior illustrated selection; exact native primary image, openaccess=1, through 1955; prior rejected identities excluded.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish_preparation(chosen)
def finish_preparation(chosen):
 for r in chosen:
  info=r['image']['native_url']+'/info.json'
  receiptpath=E/'source-captures'/(r['native_id']+'.info.receipt.json')
  if receiptpath.exists():
   receipt=load(receiptpath);body=gzip.decompress((ROOT/receipt['body_path']).read_bytes());assert h.sha(body)==receipt['sha256'] and receipt['status']==200;data=json.loads(body)
   assert data.get('@id',data.get('id'))==r['image']['native_url'];i.prepare_one(r,B);continue
  assert not (E/'access-holds/api.nga.gov.json').exists();i.provider_slot('api.nga.gov')
  res=i.session().get(info,timeout=(15,60),allow_redirects=False);body=res.content
  path=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000124/nga'/(r['native_id']+'.info.body.gz');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(gzip.compress(body,mtime=0));receipt=dict(at=h.now(),url=info,status=res.status_code,sha256=h.sha(body),body_path=str(path))
  save(receiptpath,receipt)
  if res.status_code in [401,403,429]:save(E/'access-holds/api.nga.gov.json',dict(receipt,retry_after=res.headers.get('Retry-After')));raise RuntimeError('NGA access hold')
  res.raise_for_status();data=res.json();assert data.get('@id',data.get('id'))==r['image']['native_url'];assert data['width']==int(r['image']['source']['width']) and data['height']==int(r['image']['source']['height'])
  i.prepare_one(r,B)
 i.audit(B)
 print('SHEET',load(i.folder(B)/'sheets/000.json')['path'])
def deliver():
 images,_,_=i.accepted(B);assert 1<=len(images)<=100
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 rc=load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
