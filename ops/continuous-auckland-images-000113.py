#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base113','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000113'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000113'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000113'
B='auckland-native-113';MID='3db0938a-e500-5263-9890-2997fa1d0d44'
i.OP='continuous-auckland-images-20261011-b000113';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return load(p)
 h.save(p,value);return value
def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text();node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply');code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'")
code=code.replace("tables['media_assets'].append(dict(", "credit+=(' '+r['source_credit'] if r.get('source_credit') else '')\n    tables['media_assets'].append(dict(")
code=code.replace("assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'", "assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'\n    cite=r['image']['source']['identity_reconciliation']['source_citation']\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s\",(aid,cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone(),'Pinned identity citation changed'")
exec(compile(code,__file__,'exec'),i.__dict__)
POLICY='https://www.aucklandartgallery.com/privacy-policy'
i.CFG['auckland']=dict(mid=MID,scheme='wikidata',name='Auckland Art Gallery Toi o Tāmaki',rights='restricted',license='No known copyright restrictions',policy=POLICY,host='artgallery-collection-api.cdn.aucklandunlimited.com')
old_uid=i.m.uid;i.m.uid=lambda k:i.uid(k) if k=='source/auckland' else old_uid(k)
old_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={load(p)['media_id']:selected[load(p)['artwork_id']] for p in (i.folder(B)/'prepared').glob('*.json') if load(p)['state']=='prepared'}
 if table=='media_assets':
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/auckland'),i.OP+'-auckland','Auckland exact native object image evidence','https://www.aucklandartgallery.com',i.OP))
  for row in rows:
   r=images[row['id']];row['creator_credit']=r['source_credit'];row['attribution_text']=r['source_credit']+'. '+r['rights_label']+' (museum statement concerns New Zealand). Complete supplied composition retained; proportional resizing and JPEG compression. Source accessed '+r['image']['receipt']['retrieved_at']
 if table=='media_rights_evidence':
  for row in rows:
   r=images[row['media_id']];ev=json.loads(row['evidence_json']);ev.update(identity=r['identity_basis'],identity_confidence=r['identity_confidence'],source_policy=load(E/'source-policy-verification.json'),actual_source_rights=r['rights_label'],user_authorization=load(E/'authorization.json'));row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return old_copy(db,table,rows)
i.n.copy_rows=copy_rows

def capture(url):
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','commons.wikimedia.org','www.aucklandartgallery.com'] and '/store/' not in url
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=DATA/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];assert rc['status']==200;return raw,rc
 assert not (E/'access-holds'/(host+'.json')).exists(),'Source host held'
 i.provider_slot(host);res=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=res.content
 bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=res.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After'))
 h.save(rp,rc)
 if res.status_code in [401,403,429]:save('access-holds/'+host+'.json',dict(rc,retry_allowed=False))
 assert res.status_code==200,('Source HTTP',res.status_code,url)
 return raw,rc
i.m.m.capture=capture
def deliver():
 images,_,_=i.accepted(B);assert 0<len(images)<=100
 ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images}
 with connect() as db:
  states=h.snapshot(db,ids);present=[aid for aid in ids if states[aid]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(ids) and all(states[aid]['artwork']['primary_media_id']==expected[aid]['media_id'] for aid in ids),'Concurrent or mixed image state: replan, never overwrite'
   old=load(i.BACKUP/B/'before-000.json.gz');assert all(old[aid]['artwork']['primary_media_id'] is None for aid in ids)
   rights=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in images],))];assert len(rights)==len(ids)
   pin=h.sha((i.folder(B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(B)/'visual-review.json').read_bytes())
   for r in rights:
    ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
   save('pre-replay-attribution-reconciliation.json',dict(at=h.now(),own_committed_rows=len(ids),own_selection_sha256=pin,transaction_preimage_sha256=h.sha((i.BACKUP/B/'before-000.json.gz').read_bytes()),no_new_increments=True))
  else:assert not any((i.folder(B)/'applied').glob('*.json')),'Saved applied receipts disagree with live state'
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)


if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert sys.argv[1]=='deliver'
  deliver()
