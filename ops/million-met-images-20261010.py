#!/usr/bin/env python3
"""Selected Met paintings: current object identity, authentic images, explicit review."""
import argparse,base64,collections,concurrent.futures,hashlib,importlib.util,io,json,time
from pathlib import Path
import requests
import psycopg
from PIL import Image,ImageOps
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
met=module('met','million-met-20261010.py');g=module('images','million-nga-images-20261010.py');m=met.m;n=met.n;cap=g.cap;d=g.d
RUN=met.RUN/'images-001';ORIG=Path.home()/'Library/Application Support/Artline/source-images'/m.OP/'met-001';POLICY='https://www.metmuseum.org/hubs/open-access'
PROVIDER='met';NAME='The Metropolitan Museum of Art';RIGHTS='cc0';LICENSE='The Met Open Access — CC0';VIEW='The Met open-access reproduction'
IDENTITY='Exact current native object ID and accession; current title matches a literal source title translation and creator matches a literal source creator. Both creation-date statements are eligible and preserved without metadata rewriting. Source primaryImage and isPublicDomain=true.'
RIGHTS_BASIS='The Met Open Access CC0; current API isPublicDomain=true and primaryImage. Object identity and complete source frame checked.'
def selection():return m.load(RUN/'selection.json.gz')
def prepare():
 ORIG.mkdir(parents=True,exist_ok=True)
 def one(row):
  aid=row['artwork_id'];dest=RUN/'prepared'/(aid+'.json')
  if dest.exists():return m.load(dest)['state']
  out=dict(artwork_id=aid,title=row['title'],artist=row['creator_label'],source_url=row['source_url'])
  try:
   oid=row['native_id'];key='met/image-api/'+oid+'.json';url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid
   if RUN.name=='images-002':assert (m.RUN/'sources'/(key+'.receipt.json')).exists(),'Cached metadata required; API access remains held'
   if not (m.DATA/key).exists():d.core.provider_rate_slot('collectionapi.metmuseum.org')
   api=m.load(cap.capture(key,url));rc=m.load(m.RUN/'sources'/(key+'.receipt.json'))
   assert str(api['objectID'])==oid and api['accessionNumber']==row['accession_number'],'Current object identity differs'
   assert m.norm(api['title']) in {m.norm(t) for t in row['title'].split('|')},'Current source title differs from supplied title translations'
   assert api['isPublicDomain'] is True,'Current public-domain designation missing'
   current_date=met.dates({'Object Date':api['objectDate'],'Classification':row['raw']['Classification']});assert current_date and current_date[1]<=1955,'Current creation date requires review'
   assert m.norm(api['artistDisplayName']) in {m.norm(t) for t in row['raw']['Artist Display Name'].split('|')},'Current creator wording differs'
   url=api['primaryImage'];assert url.startswith('https://images.metmuseum.org/'),'No approved primary reproduction'
   out.update(api=api,api_receipt=rc,source_image_url=url)
   hold=RUN/'access-hold.json';assert not hold.exists(),'Image source access held'
   original=ORIG/(aid+'.source');receipt=ORIG/(aid+'.receipt.json')
   if receipt.exists():download=m.load(receipt);raw=original.read_bytes();assert m.sha(raw)==download['sha256']
   else:
    d.core.provider_rate_slot('images.metmuseum.org');response=cap.session().get(url,timeout=(15,60));download=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=m.sha(response.content),bytes=len(response.content),content_type=response.headers.get('Content-Type'))
    if response.status_code in (401,403,429):m.save(hold,download)
    response.raise_for_status();raw=response.content;assert download['content_type'].startswith('image/') and len(raw)<30000000;original.write_bytes(raw);m.save(receipt,download)
   with Image.open(io.BytesIO(raw)) as opened:
    assert opened.width*opened.height<70000000;opened.load();im=ImageOps.exif_transpose(opened).convert('RGB');output=None
    for edge in [1200,1000,850,700,600,500]:
     im.thumbnail((edge,edge),Image.Resampling.LANCZOS)
     for quality in [90,85,80,75,70,65,60]:
      buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
      if buf.tell()<=100000:output=buf.getvalue();break
     if output:break
    assert output and min(im.size)>=40
    digest=m.sha(output);sp='/assets/artworks/imported/'+m.OP+'/'+aid+'-'+digest[:16]+'.jpg';local=m.ROOT/'apps/web/public'/sp.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
    if local.exists():assert local.read_bytes()==output
    else:local.write_bytes(output)
    out.update(state='prepared',path=str(local),storage_path=sp,sha256=digest,bytes=len(output),width=im.width,height=im.height,media_id=m.uid('media/met/'+aid+'/'+digest),download=download,original_path=str(original))
  except Exception as e:out.update(state='held',reason=type(e).__name__+': '+str(e)[:500])
  m.save(dest,out);return out['state']
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for i,state in enumerate(pool.map(one,selection()['rows']),1):
   counts[state]+=1
   if i%40==0:print('Prepared',i,dict(counts),flush=True)
 print(dict(counts),flush=True)
def sheets():
 g.RUN=RUN;g.ORIG=ORIG;g.select=selection;g.sheets()
def deliver():
 for attempt in range(20):
  try:return deliver_once()
  except (psycopg.OperationalError,psycopg.errors.LockNotAvailable,psycopg.errors.DeadlockDetected,psycopg.errors.SerializationFailure) as error:
   state=getattr(error,'sqlstate',None)
   if state and not (state.startswith('08') or state in ('57P01','57P02','57P03','55P03','40P01','40001')):raise
   if attempt==19:raise
   print('Image transaction interrupted; checking committed identities before resuming.',flush=True);time.sleep(5)
def deliver_once():
 p=selection();reviews=m.load(RUN/'visual-review.json');rows=[r for r in p['rows'] if reviews.get(r['artwork_id'],{}).get('decision')=='accept'];bucket=storage.Client(project='artline-508319',credentials=d.core.GcloudCredentials()).bucket(d.core.BUCKET)
 def upload(r):
  im=m.load(RUN/'prepared'/(r['artwork_id']+'.json'));assert im['sha256']==reviews[r['artwork_id']]['sha256'];raw=Path(im['path']).read_bytes();assert m.sha(raw)==im['sha256'];dest=RUN/'uploads'/(r['artwork_id']+'.json')
  if dest.exists():return
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':m.OP};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
  except PreconditionFailed:pass
  blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,60));response.raise_for_status();assert m.sha(response.content)==im['sha256'];m.save(dest,dict(at=m.now(),sha256=im['sha256'],generation=blob.generation,public_verified=True))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(upload,rows))
 for batch,group in enumerate(m.chunks(rows,40)):
  rp=RUN/'applied'/(str(batch).zfill(3)+'.json')
  if rp.exists():continue
  ids=[r['artwork_id'] for r in group]
  with m.m.connect(write=True) as db:
   db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
   before={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))};assert len(before)==len(ids)
   expected={r['artwork_id']:m.load(RUN/'prepared'/(r['artwork_id']+'.json')) for r in group}
   committed=[aid for aid in ids if before[aid]['primary_media_id']==expected[aid]['media_id']]
   if committed:
    assert len(committed)==len(ids),'Partial image batch requires investigation'
    backup=m.load(m.BACKUP/PROVIDER/RUN.name/('before-'+str(batch).zfill(3)+'.json.gz'))
    for aid in ids:
     source=expected[aid];current=before[aid]
     assert all(current[k]==v for k,v in backup[aid].items() if k not in ['primary_media_id','updated_by','updated_at','revision'])
     media=db.execute('SELECT checksum_sha256,storage_path FROM media_assets WHERE id=%s',(source['media_id'],)).fetchone()
     assert media and media['checksum_sha256']==source['sha256'] and media['storage_path']==source['storage_path']
     assert db.execute('SELECT 1 FROM artwork_media WHERE artwork_id=%s AND media_id=%s',(aid,source['media_id'])).fetchone()
     assert db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s AND source_id=%s AND source_record_id=%s',(source['media_id'],met.SID,next(r['native_id'] for r in group if r['artwork_id']==aid))).fetchone()
    db.commit();m.save(rp,dict(at=m.now(),artworks=ids,images=len(ids),recovered_committed_transaction=True));print('Recovered image batch',batch,len(ids),flush=True);continue
   m.save(m.BACKUP/PROVIDER/RUN.name/('before-'+str(batch).zfill(3)+'.json.gz'),before)
   for r in group:
    im=m.load(RUN/'prepared'/(r['artwork_id']+'.json'));a=before[r['artwork_id']];assert a['status']=='review' and a['primary_media_id'] is None and a['creation_year_end']==r['last'] and a['title']==r['title']
    credit=(r['creator_label']+'. ' if r['creator_label'] else '')+im['api']['creditLine']+'. '+NAME+'.'
    n.copy_rows(db,'media_assets',[dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=r['source_url'],provider_name=NAME,mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title']+' — '+r['creator_label'],rights_status=RIGHTS,license_label=LICENSE,license_url=POLICY,creator_credit=credit,attribution_text=credit+' Full source frame preserved; proportionally resized and JPEG compressed.',retrieved_at=im['download']['retrieved_at'],verified_at=m.now(),verified_by=m.ACTOR)])
    evidence=dict(plan_sha256=p['plan_sha256'],source_metadata=im['api'],metadata_receipt=im['api_receipt'],download=im['download'],visual_review=reviews[r['artwork_id']],identity_basis=IDENTITY,policy_observation=m.load(RUN/'policy-observation.json'))
    n.copy_rows(db,'media_rights_evidence',[dict(media_id=im['media_id'],source_id=met.SID,source_record_id=r['native_id'],source_checksum=im['api_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=POLICY,rights_basis=RIGHTS_BASIS,adapter_version=m.OP,checked_at=m.now(),evidence_json=json.dumps(evidence,ensure_ascii=False))])
    order=db.execute('SELECT coalesce(max(sort_order),-1)+1 n FROM artwork_media WHERE artwork_id=%s',(r['artwork_id'],)).fetchone()['n']
    n.copy_rows(db,'artwork_media',[dict(artwork_id=r['artwork_id'],media_id=im['media_id'],sort_order=order,view_label=reviews[r['artwork_id']].get('view_label',VIEW))]);db.execute('UPDATE artworks SET primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s',(im['media_id'],m.ACTOR,r['artwork_id']))
   after={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,))}
   for aid,a in before.items():
    assert all(after[aid][k]==v for k,v in a.items() if k not in ['primary_media_id','updated_by','updated_at','revision'])
   db.commit()
  m.save(rp,dict(at=m.now(),artworks=ids,images=len(ids)));print('Attached',batch,len(ids),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','sheets','deliver']);ap.add_argument('--phase',choices=['001','002'],default='001');a=ap.parse_args();RUN=met.RUN/('images-'+a.phase);ORIG=ORIG.parent/('met-'+a.phase);globals()[a.action]()
