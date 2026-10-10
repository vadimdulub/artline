#!/usr/bin/env python3
"""Promote the pinned local image recovery to production without catalogue changes."""
import argparse,base64,collections,concurrent.futures,gzip,hashlib,importlib.util,json,subprocess,uuid
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime
import requests
from PIL import Image
from psycopg.types.json import Jsonb
from psycopg import sql
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('local_base','recover-local-commons-images-20261005.py');core=base.core
q=module('production_connection','research-production-wikiart-images-20261006.py');r=q.r
OP='production-local-image-recovery-20261008';RUN=ROOT/'docs/research'/OP
BACKUP=base.ARCHIVE/'backups'/OP;ARCHIVE=base.ARCHIVE/'source-images'/OP
COMBINED=RUN.parent/'local-image-recovery-20261006';ACTOR='local-european-research'
MEDIA_FIELDS=['id','storage_kind','storage_path','delivery_url','source_page_url','provider_name','mime_type','width','height','byte_size','checksum_sha256','alt_text','rights_status','license_label','license_url','creator_credit','attribution_text','retrieved_at','verified_at','verified_by']
SOURCE_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/source'))
def load(path):
 raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
def save(path,data):
 raw=core.encode(data)
 if path.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
 core.save_new(path,raw)
def pin(path):return dict(path=str(path.relative_to(ROOT)),sha256=core.sha(path.read_bytes()))
def stored_equal(actual,expected,timestamps=()):
 if set(actual)!=set(expected):return False
 for k in expected:
  if k in timestamps and actual[k] is not None and expected[k] is not None:
   if datetime.fromisoformat(actual[k])!=datetime.fromisoformat(expected[k]):return False
  elif actual[k]!=expected[k]:return False
 return True
def snapshot(db,ids):
 result={x['record']['id']:dict(artwork=x['record'],creators=[],identifiers=[],holdings=[],attachments=[]) for x in db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
 for key,table,fk,order in [('creators','artwork_artists','artwork_id','artist_id'),('identifiers','external_identifiers','entity_id','id'),('holdings','artwork_location_assertions','artwork_id','id'),('attachments','artwork_media','artwork_id','media_id')]:
  extra=" AND entity_type='artwork'" if key=='identifiers' else ''
  rows=db.execute(f'SELECT {fk}::text aid,to_jsonb(x) record FROM {table} x WHERE {fk}=ANY(%s::uuid[]){extra} ORDER BY {fk},{order}',(ids,)).fetchall()
  for x in rows:result[x['aid']][key].append(x['record'])
 return result

def prepare():
 dest=RUN/'local-delivery-package.json.gz'
 if dest.exists():package();print('Pinned local delivery package preserved',flush=True);return
 report=load(COMBINED/'report.json');images={};pins=[]
 for name in report['operations']:
  operation=COMBINED.parent/name;applied=operation/'apply-receipt.json'
  if not applied.exists():continue
  withdrawn={aid for p in operation.glob('source-policy-correction*.json') for aid in load(p)['artwork_ids']}
  for receipt in load(applied)['receipts']:
   aid=receipt['artwork_id']
   if receipt['result']!='attached' or aid in withdrawn:continue
   path=operation/'images'/(aid+'.json');im=load(path);assert aid not in images
   images[aid]=dict(image=im,operation=name,image_record_pin=pin(path))
  pins.append(pin(applied))
 assert len(images)==report['new_images_attached']==1214
 with base.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  current=snapshot(db,list(images))
  media={x['media']['id']:x for x in db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence,to_jsonb(s) source FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id JOIN sources s ON s.id=e.source_id WHERE m.id=ANY(%s::uuid[])',([x['image']['media_id'] for x in images.values()],)).fetchall()}
  for aid,row in images.items():
   im=row['image'];imdb=media[im['media_id']];state=current[aid];assert state['artwork']['primary_media_id']==im['media_id']
   allowed={'primary_media_id','revision','updated_at','updated_by'}
   assert {k:v for k,v in state['artwork'].items() if k not in allowed}=={k:v for k,v in im['before_record'].items() if k not in allowed},aid
   assert state['creators']==im['creator_links'] and state['identifiers']==im['identifiers'],aid
   am=[x for x in state['attachments'] if x['media_id']==im['media_id']];assert len(am)==1
   assert am[0]['view_label']==im.get('view_label','Full composition')
   m=imdb['media'];assert (m['storage_path'],m['checksum_sha256'],m['byte_size'],m['rights_status'])==(im['path'],im['sha256'],im['bytes'],im['rights_status'])
   assert imdb['evidence']['source_image_url']==im['source_image_url'] and m['source_page_url']==im['page']
   raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
   assert core.sha(Path(im['source_archive']).read_bytes())==im['source_sha256']
   with Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/')) as picture:picture.verify()
   row.update(local_state=state,media=imdb['media'],evidence=imdb['evidence'],original_source=imdb['source'],attachment=am[0])
 authorization=dict(at=core.now(),user_request='push to prod',target='production',scope='Deliver the 1,214 verified local recovery images; image-only production attachments. Preserve existing images, catalogue metadata, holdings, rights labels and publication status.',per_batch_confirmation_required=False)
 save(RUN/'authorization.json',authorization)
 data=dict(at=core.now(),authorization=authorization,combined_report_pin=pin(COMBINED/'report.json'),operation_receipts=pins,images=images)
 save(dest,data);save(RUN/'local-package-pin.json',dict(**pin(dest),images=len(images)))
 save(BACKUP/'local-delivery-package.json.gz',data)
 print('Prepared and verified local production package:',len(images),'images',flush=True)

def package():
 p=RUN/'local-delivery-package.json.gz';assert core.sha(p.read_bytes())==load(RUN/'local-package-pin.json')['sha256'];return load(p)

def creator_crosswalk():
 path=RUN/'creator-crosswalk-review.json'
 if not path.exists():return {}
 assert core.sha(path.read_bytes())==load(RUN/'creator-crosswalk-pin.json')['sha256']
 proofs=load(path)['proofs']
 for x in proofs:
  left=x['local_authority'];right=x['production_authority']
  assert left['record']['id']==x['local_id'] and right['record']['id']==x['production_id']
  assert left['record']['display_name']==right['record']['display_name']==x['local_name']==x['production_name']
  li={(e['scheme'],e['external_id']) for e in left['identifiers']};ri={(e['scheme'],e['external_id']) for e in right['identifiers']}
  assert li&ri=={tuple(v) for v in x['shared']} and any(s=='wikidata' or s.endswith('-person') or s=='nga-constituent' for s,v in li&ri)
  assert {v for s,v in li if s=='wikidata'}=={v for s,v in ri if s=='wikidata'}==set(x['local_qids'])==set(x['production_qids'])
 return {(x['local_id'],x['production_id']):x for x in proofs}

def verify_creator_authorities(db,lock=False):
 expected={x['production_id']:x['production_authority'] for x in creator_crosswalk().values()};ids=sorted(expected)
 suffix=' FOR SHARE' if lock else ''
 actual={x['record']['id']:dict(record=x['record'],identifiers=[]) for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id'+suffix,(ids,)).fetchall()}
 for x in db.execute("SELECT entity_id::text,to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id"+suffix,(ids,)).fetchall():actual[x['entity_id']]['identifiers'].append(x['record'])
 assert actual==expected,'Production creator authority changed since crosswalk review'

def identity(row,prod):
 im=row['image'];local=row['local_state'];a=prod['artwork'];old=local['artwork']
 if a['status']=='archived':return 'production_record_archived'
 for key in ['title','accession_number','creation_year_start','creation_year_end','date_precision','work_type','current_institution_id']:
  if a[key]!=old[key]:return 'production_identity_difference:'+key
 creators=lambda x:sorted((c['artist_id'],c['attribution_role']) for c in x['creators'])
 if creators(prod)!=creators(local):
  crosswalk=creator_crosswalk();remaining=list(creators(prod))
  for lid,role in creators(local):
   matches=[(pid,p_role) for pid,p_role in remaining if role==p_role and ((lid==pid) or (lid,pid) in crosswalk)]
   if len(matches)!=1:return 'production_creator_identity_differs'
   pid,p_role=matches[0]
   if lid!=pid:
    d=crosswalk[lid,pid]
    if d['decision']!='same_creator' or d['local_name']!=d['production_name'] or not d['shared'] or set(d['local_qids'])!=set(d['production_qids']):return 'production_creator_crosswalk_invalid'
   remaining.remove(matches[0])
  if remaining:return 'production_creator_identity_differs'
 localids={(x['scheme'],x['external_id']) for x in local['identifiers']};prodids={(x['scheme'],x['external_id']) for x in prod['identifiers']}
 if not localids.intersection(prodids):return 'no_shared_object_identifier'
 for scheme in {x[0] for x in localids&prodids}:
  if {value for s,value in localids if s==scheme}!={value for s,value in prodids if s==scheme}:return 'conflicting_shared_identifier_scheme:'+scheme
 return None

def preflight():
 data=package();images=data['images'];dest=RUN/'production-plan.json.gz'
 if dest.exists():pinned();print('Existing pinned production plan preserved',flush=True);return
 with r.connect('production') as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
  verify_creator_authorities(db)
  # Look up only the prepared IDs and their pinned object identifiers.
  ids=list(images);found=snapshot(db,ids);missing=[aid for aid in ids if aid not in found];mapping={aid:aid for aid in found};matches=collections.defaultdict(set)
  if missing:
   lookup=[dict(local_id=aid,scheme=e['scheme'],external_id=e['external_id']) for aid in missing for e in images[aid]['local_state']['identifiers']]
   rows=db.execute("""SELECT p.local_id,e.entity_id::text FROM jsonb_to_recordset(%s::jsonb) p(local_id text,scheme text,external_id text)
    JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=p.scheme AND e.external_id=p.external_id""",(Jsonb(lookup),)).fetchall()
   for x in rows:matches[x['local_id']].add(x['entity_id'])
   for aid,values in matches.items():
    if len(values)==1:mapping[aid]=next(iter(values))
   found.update(snapshot(db,sorted({v for v in mapping.values() if v not in found})))
  ready={};held=[];preserved=[]
  primary_ids=[x['artwork']['primary_media_id'] for x in found.values() if x['artwork']['primary_media_id']]
  existing_media={x['media']['id']:x for x in db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m LEFT JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(primary_ids,)).fetchall()}
  for aid,row in images.items():
   pid=mapping.get(aid)
   if not pid or pid not in found:held.append(dict(artwork_id=aid,reason='production_object_missing_or_ambiguous',matches=sorted(matches[aid])));continue
   state=found[pid];reason=identity(row,state)
   if reason:held.append(dict(artwork_id=aid,production_id=pid,reason=reason));continue
   existing=state['artwork']['primary_media_id']
   item=dict(production_id=pid,preimage=state,mode='new_primary')
   if existing:
    previous=existing_media[existing];local_media=row['media'];pm=previous['media']
    exact=all(pm[k]==local_media[k] for k in ('checksum_sha256','byte_size','rights_status','source_page_url','license_url')) and pm['storage_kind']=='local' and previous['evidence'] is not None
    item.update(mode='reuse_existing' if exact else 'new_secondary',existing_media=previous)
    preserved.append(dict(artwork_id=aid,production_id=pid,media_id=existing,reason='existing_production_primary_preserved',delivery_mode=item['mode']))
   ready[aid]=item
  mids=[images[aid]['media']['id'] for aid,x in ready.items() if x['mode']!='reuse_existing'];paths=[images[aid]['media']['storage_path'] for aid,x in ready.items() if x['mode']!='reuse_existing']
  collisions=db.execute('SELECT id::text,storage_path FROM media_assets WHERE id=ANY(%s::uuid[]) OR storage_path=ANY(%s)',(mids,paths)).fetchall()
  if collisions:raise ValueError('Existing media needs explicit reuse review: '+json.dumps(collisions)[:1000])
  assert len({x['production_id'] for x in ready.values()})==len(ready),'Multiple local images map to one production object'
  institution_ids=sorted({images[aid]['local_state']['artwork']['current_institution_id'] for aid in ready}-{None})
  institutions={x['id']:x for x in db.execute('SELECT id::text,slug,name FROM institutions WHERE id=ANY(%s::uuid[])',(institution_ids,)).fetchall()}
 plan=dict(at=core.now(),local_package_sha256=load(RUN/'local-package-pin.json')['sha256'],ready=ready,held=held,preserved=preserved,institutions=institutions,creator_crosswalk_pin=load(RUN/'creator-crosswalk-pin.json'))
 save(dest,plan);save(RUN/'production-plan-pin.json',pin(dest));save(BACKUP/'production-preimages.json.gz',plan)
 print(json.dumps(dict(ready=len(ready),modes=dict(collections.Counter(x['mode'] for x in ready.values())),existing_images_preserved=len(preserved),held=held),ensure_ascii=False),flush=True)

def pinned():
 p=RUN/'production-plan.json.gz';assert core.sha(p.read_bytes())==load(RUN/'production-plan-pin.json')['sha256'];plan=load(p)
 assert plan['local_package_sha256']==load(RUN/'local-package-pin.json')['sha256']
 if plan.get('creator_crosswalk_pin'):assert core.sha((ROOT/plan['creator_crosswalk_pin']['path']).read_bytes())==plan['creator_crosswalk_pin']['sha256']
 return plan

def backup():
 pinned();description='Before 1214 local recovery image promotion 20261008'
 def cloud(*args):return json.loads(subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
 rows=cloud('sql','backups','list','--instance=artline-postgres','--limit=60');matching=[x for x in rows if x.get('description')==description]
 if not matching:
  operation=cloud('sql','backups','create','--instance=artline-postgres','--description='+description,'--async');save(BACKUP/'cloud-sql-backup-operation.json',operation);print('Recovery backup requested',flush=True);return
 current=max(matching,key=lambda x:int(x['id']))
 if current['status']!='SUCCESSFUL':print('Recovery backup:',current['status'],flush=True);return
 save(BACKUP/'cloud-sql-backup.json',current);save(RUN/'cloud-sql-backup.json',dict(id=current['id'],status=current['status']));print('Recovery backup verified:',current['id'],flush=True)

def upload():
 plan=pinned();data=package();plan_sha=load(RUN/'production-plan-pin.json')['sha256'];bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
 def one(aid):
  im=data['images'][aid]['image'];item=plan['ready'][aid];dest=RUN/'uploads'/(aid+'.json')
  if dest.exists():
   old=load(dest);assert old['plan_sha256']==plan_sha and old['public_bytes_verified'];return old
  raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
  path=item['existing_media']['media']['storage_path'] if item['mode']=='reuse_existing' else im['path'];generation=None
  if item['mode']!='reuse_existing':
   blob=bucket.blob(path.lstrip('/'));blob.metadata=dict(sha256=im['sha256'],operation=OP,artwork_id=item['production_id']);blob.cache_control='public,max-age=31536000,immutable'
   try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
   except PreconditionFailed:blob.reload(timeout=30)
   assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();generation=str(blob.generation)
  response=requests.get('https://artlines.org'+path,timeout=(15,45));response.raise_for_status();assert core.sha(response.content)==im['sha256']
  receipt=dict(at=core.now(),artwork_id=aid,production_id=item['production_id'],plan_sha256=plan_sha,path=path,sha256=im['sha256'],generation=generation,mode=item['mode'],public_http_status=response.status_code,public_bytes_verified=True)
  save(dest,receipt);return receipt
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,_ in enumerate(pool.map(one,plan['ready']),1):
   if n%25==0:print('Uploaded and verified',n,'/',len(plan['ready']),flush=True)
 print('Production files verified:',len(plan['ready']),flush=True)

def expected_evidence(row,aid,pid,plan_sha):
 e=dict(row['evidence']);e['source_id']=SOURCE_ID;e['adapter_version']=OP
 e['evidence_json']=dict(e['evidence_json'],production_delivery=dict(operation=OP,user_request='push to prod',target='production',local_artwork_id=aid,production_artwork_id=pid,original_local_source=row['original_source'],original_source_id=row['evidence']['source_id'],local_operation=row['operation'],plan_sha256=plan_sha))
 return e

def reuse_evidence(row,aid,item,plan_sha):
 # Preserve the original rights record and append the independently reviewed
 # local evidence. Identical pixels do not justify duplicating a gallery image.
 existing=dict(item['existing_media']['evidence']);body=dict(existing['evidence_json']);key='local_recovery_delivery_20261008'
 assert key not in body,'Delivery evidence already present'
 body[key]=dict(production_delivery=expected_evidence(row,aid,item['production_id'],plan_sha)['evidence_json']['production_delivery'],local_image=row['image'],local_media=row['media'],local_rights_evidence=row['evidence'],reviewed_view_label=row['attachment']['view_label'])
 existing['evidence_json']=body;return existing

def reuse_media(row,item):
 result=dict(item['existing_media']['media'])
 if row['image'].get('view_label'):
  result['alt_text']=row['media']['alt_text']
  result['attribution_text']=(result['attribution_text'] or '')+'\nAdditional inspected view and source evidence: '+row['media']['attribution_text']
 return result

def apply():
 plan=pinned();data=package();plan_sha=load(RUN/'production-plan-pin.json')['sha256'];ready=plan['ready'];ids=[x['production_id'] for x in ready.values()]
 assert ready and load(BACKUP/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 for aid in ready:
  receipt=load(RUN/'uploads'/(aid+'.json'));assert receipt['plan_sha256']==plan_sha and receipt['public_bytes_verified']
 with r.connect('production',readonly=False) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(202610081214)');db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  expected={v['production_id']:v['preimage'] for v in ready.values()};assert snapshot(db,ids)==expected,'Production records changed since preflight; no changes applied'
  verify_creator_authorities(db,True)
  previous={x['existing_media']['media']['id']:x['existing_media'] for x in ready.values() if x.get('existing_media')}
  db.execute('SELECT id FROM media_assets WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(sorted(previous),)).fetchall()
  db.execute('SELECT media_id FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id FOR UPDATE',(sorted(previous),)).fetchall()
  actual={x['media']['id']:x for x in db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m LEFT JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(sorted(previous),)).fetchall()};assert actual==previous,'Existing production image evidence changed'
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'manual','https://artlines.org/')",(SOURCE_ID,OP,'Verified local artwork image recovery: production delivery, 8 October 2026'))
  changed=[]
  with db.pipeline():
   for n,(aid,item) in enumerate(ready.items(),1):
    row=data['images'][aid];m=row['media'];pid=item['production_id'];e=expected_evidence(row,aid,pid,plan_sha)
    if item['mode']=='reuse_existing':
     reused=reuse_evidence(row,aid,item,plan_sha);mid=item['existing_media']['media']['id']
     db.execute('UPDATE media_rights_evidence SET evidence_json=%s WHERE media_id=%s',(Jsonb(reused['evidence_json']),mid))
     if row['image'].get('view_label'):
      revised=reuse_media(row,item)
      db.execute('UPDATE media_assets SET alt_text=%s,attribution_text=%s,updated_at=now() WHERE id=%s',(revised['alt_text'],revised['attribution_text'],mid))
      db.execute('UPDATE artwork_media SET view_label=%s WHERE artwork_id=%s AND media_id=%s',(row['attachment']['view_label'],pid,mid))
    else:
     mid=m['id']
     db.execute(sql.SQL('INSERT INTO media_assets ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,MEDIA_FIELDS)),sql.SQL(',').join(sql.Placeholder() for _ in MEDIA_FIELDS)),[m[k] for k in MEDIA_FIELDS])
     fields=list(e);db.execute(sql.SQL('INSERT INTO media_rights_evidence ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields)),[Jsonb(e[k]) if k=='evidence_json' else e[k] for k in fields])
     order=0 if item['mode']=='new_primary' else max([a['sort_order'] for a in item['preimage']['attachments']]+[0])+1
     db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,%s,%s)',(pid,mid,order,row['attachment']['view_label']))
     if item['mode']=='new_primary':changed.append(db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(mid,ACTOR,pid)))
    note=core.encode(dict(operation=OP,plan_sha256=plan_sha,local_artwork_id=aid,local_media_id=row['media']['id'],production_media_id=mid,delivery_mode=item['mode'],source_operation=row['operation'],reviewed_view_label=row['attachment']['view_label'],scope='Verified image and original review evidence delivered; catalogue and publication state preserved.')).decode()
    db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,'image_identity',%s,%s,%s,%s,%s,%s)",(str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/citation/'+aid)),pid,SOURCE_ID,row['image']['external_id'],row['image']['page'],note,row['image']['checked_at'],ACTOR))
    if n%100==0:print('Queued production images',n,'/',len(ready),flush=True)
  assert all(x.rowcount==1 for x in changed)
  after=snapshot(db,ids);check_states(data,plan,after)
 save(BACKUP/'production-after.json.gz',dict(at=core.now(),plan_sha256=plan_sha,records=after))
 save(RUN/'production-applied.json',dict(at=core.now(),plan_sha256=plan_sha,attached=len(ready),delivery_modes=dict(collections.Counter(x['mode'] for x in ready.values())),artwork_ids=ids,catalogue_metadata_preserved=True,publication_preserved=True,local_database_changed=False))
 print('Committed production image attachments:',len(ready),flush=True)

def check_states(data,plan,after):
 for aid,item in plan['ready'].items():
  old=item['preimage'];new=after[item['production_id']];im=data['images'][aid]['media'];allowed={'primary_media_id','revision','updated_at','updated_by'}
  assert {k:v for k,v in old['artwork'].items() if k not in allowed}=={k:v for k,v in new['artwork'].items() if k not in allowed},aid
  if item['mode']=='new_primary':assert new['artwork']['primary_media_id']==im['id'] and new['artwork']['revision']==old['artwork']['revision']+1
  else:assert new['artwork']==old['artwork']
  for key in ['creators','identifiers','holdings']:assert new[key]==old[key],(aid,key)
  if item['mode']=='reuse_existing':
   expected=[dict(x) for x in old['attachments']]
   if data['images'][aid]['image'].get('view_label'):
    for x in expected:
     if x['media_id']==old['artwork']['primary_media_id']:x['view_label']=data['images'][aid]['attachment']['view_label']
   assert new['attachments']==expected
  else:
   previous=[x for x in new['attachments'] if x['media_id']!=im['id']];assert previous==old['attachments']
   matches=[x for x in new['attachments'] if x['media_id']==im['id']];assert len(matches)==1 and matches[0]['view_label']==data['images'][aid]['attachment']['view_label']

def verify():
 plan=pinned();data=package();receipt=load(RUN/'production-applied.json');plan_sha=load(RUN/'production-plan-pin.json')['sha256'];assert receipt['plan_sha256']==plan_sha
 with r.connect('production') as db:
  after=snapshot(db,receipt['artwork_ids']);check_states(data,plan,after)
  mids=[item['existing_media']['media']['id'] if item['mode']=='reuse_existing' else data['images'][aid]['media']['id'] for aid,item in plan['ready'].items()]
  media={x['media']['id']:x for x in db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(mids,)).fetchall()}
  for aid,item in plan['ready'].items():
   row=data['images'][aid];m=reuse_media(row,item) if item['mode']=='reuse_existing' else row['media'];actual=media[m['id']]
   assert stored_equal({k:actual['media'][k] for k in MEDIA_FIELDS},{k:m[k] for k in MEDIA_FIELDS},('retrieved_at','verified_at')),aid
   expected=reuse_evidence(row,aid,item,plan_sha) if item['mode']=='reuse_existing' else expected_evidence(row,aid,item['production_id'],plan_sha)
   assert stored_equal(actual['evidence'],expected,('checked_at',)),aid
  citations=db.execute("SELECT entity_id::text,source_record_id FROM citations WHERE source_id=%s AND field_name='image_identity'",(SOURCE_ID,)).fetchall();assert len(citations)==len(plan['ready'])
 samples={}
 for aid,item in plan['ready'].items():
  iid=data['images'][aid]['local_state']['artwork']['current_institution_id']
  if iid:samples.setdefault(iid,aid)
 def api(aid):
  row=data['images'][aid];item=plan['ready'][aid];iid=row['local_state']['artwork']['current_institution_id'];slug=plan['institutions'][iid]['slug'];url='https://artlines.org/api/backend/v1/museums/'+slug+'/works/'+item['production_id']
  expected=row['media']['storage_path'] if item['mode']=='new_primary' else item['existing_media']['media']['storage_path']
  response=requests.get(url,timeout=(15,45));body=response.json() if response.status_code==200 else {};return dict(artwork_id=item['production_id'],url=url,status=response.status_code,expected_path=expected,actual_path=body.get('media_url'),verified=response.status_code==200 and body.get('media_url')==expected)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(api,samples.values()))
 result=dict(at=core.now(),database_images_verified=len(plan['ready']),public_files_verified=len(list((RUN/'uploads').glob('*.json'))),api_checks=checks,api_verified=sum(x['verified'] for x in checks),all_catalogue_metadata_and_publication_preserved=True,rights_credits_and_view_labels_preserved=True,local_database_changed=False,held=plan['held'],existing_images_preserved=plan['preserved'])
 save(RUN/'production-verification.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('api_checks','held','existing_images_preserved')}),flush=True)
 assert all(x['verified'] for x in checks),'Live API mismatch recorded for investigation'

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','preflight','backup','upload','apply','verify']);a=p.parse_args();globals()[a.phase]()
