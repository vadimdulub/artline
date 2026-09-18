#!/usr/bin/env python3
"""Guarded portrait delivery: preserve artists and artworks; attach verified media only."""
import argparse,base64,hashlib,importlib.util,json,subprocess,uuid
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('import-cypriot-more.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
ROOT=b.ROOT;RUN=ROOT/'docs/research/cyprus-greece-portraits-20260914';BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-greece-portraits-20260914');core=b.core;SOURCE='cyprus-greece-portraits-20260914';ACTOR=b.ACTOR
read=lambda n:json.loads((RUN/n).read_text());save=core.save_new
uid=lambda key:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/'+SOURCE+'/'+key))
def target_artist(im,target):
 original=im['artist'];a=next(a for a in read(target+'-before.json')['artists'] if a['slug']==original['slug'])
 assert all(a[k]==original[k] for k in ['display_name','birth_year','death_year','entity_type','qids','status'])
 return a
def images():
 fetcher=core.Fetcher(RUN/'image-captures');fetcher.session.headers['User-Agent']=b.w.SESSION.headers['User-Agent'];core.HOSTS.add('www.searchculture.gr');out=[]
 for item in read('selected.json')['items']:
  a=item['artist'];path=BACKUP/'selected-originals'/(a['slug']+'.original')
  if path.exists():raw=path.read_bytes()
  else:raw,_=fetcher.get(item['source_image_url'],20000000);save(path,raw)
  if item.get('source_metadata'):
   info=item['source_metadata']['imageinfo'][0];assert len(raw)==info['size'] and hashlib.sha1(raw).hexdigest()==info['sha1']
  content,width,height,quality=core.compress(raw);checksum=core.sha(content);asset='/assets/artists/imported/cyprus-greece/'+a['slug']+'-'+checksum[:16]+'.jpg';save(ROOT/'apps/web/public'/asset.lstrip('/'),content)
  im=dict(item,id=uid('media/'+checksum),path=asset,sha256=checksum,bytes=len(content),width=width,height=height,quality=quality,original_sha256=core.sha(raw),checked_at=core.now(),attribution_text=a['display_name']+'. '+item['subject_note']+'. Credit: '+item['creator_credit']+'. '+item['license_label']+' ('+item['license_url']+'). '+item['source_page_url']+'. Source frame preserved; resized and JPEG compressed. '+('Derivative under the same licence.' if item['rights_status']=='cc_by_sa' else ''))
  out.append(im);print('Prepared',a['display_name'],width,height,len(content),flush=True)
 save(RUN/'prepared-images.json',out)
def plan():
 images=read('prepared-images.json');ids=[i['artist']['id'] for i in images]
 assert len(ids)==len(set(ids)) and len({i['sha256'] for i in images})==len(images)
 for target in ['local','production']:
  ids=[target_artist(im,target)['id'] for im in images]
  with b.w.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   rows=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
   for im in images:
    a=next(v['row'] for v in rows if v['row']['id']==target_artist(im,target)['id']);assert a['portrait_media_id'] is None and a['display_name']==im['artist']['display_name']
   assert not db.execute('SELECT id FROM media_assets WHERE storage_path=ANY(%s)',([i['path'] for i in images],)).fetchall()
   save(BACKUP/(target+'-artist-preimages.json'),rows)
 plan=dict(images=images,artists=len(images),gaps=len(read('selected.json')['gaps']),audited_artists=70);save(RUN/'application-plan.json',plan);save(RUN/'application-manifest.json',dict(plan_sha256=core.sha((RUN/'application-plan.json').read_bytes()),portraits=len(images)));print('Plan',len(images),'portraits',flush=True)
def apply():
 raw=(RUN/'application-plan.json').read_bytes();pin=core.sha(raw);assert read('application-manifest.json')['plan_sha256']==pin
 assert read('quality-review.json')['approved'] and read('quality-review.json')['plan_sha256']==pin
 assert core.sha((BACKUP/'local-before.dump').read_bytes())==read('local-backup.json')['sha256'];assert read('production-backup.json')['status']=='SUCCESSFUL'
 data=json.loads(raw);bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
 for im in data['images']:
  content=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(content)==im['sha256'] and len(content)<=100000
  blob=bucket.blob(im['path'].lstrip('/'))
  if not blob.exists():
   blob.metadata={'sha256':im['sha256'],'license':im['license_label'],'source':im['source_page_url']};blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(content,content_type='image/jpeg',if_generation_match=0)
  blob.reload();assert blob.size==len(content) and blob.md5_hash==base64.b64encode(hashlib.md5(content).digest()).decode()
 for target in ['local','production']:
  if (RUN/('applied-'+target+'.json')).exists():continue
  pre={v['row']['id']:v['row'] for v in json.loads((BACKUP/(target+'-artist-preimages.json')).read_text())}
  ids=[target_artist(im,target)['id'] for im in data['images']]
  with b.w.base.connect(target=='production') as db,db.transaction():
   db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL statement_timeout='45s'");db.execute('SELECT pg_advisory_xact_lock(%s)',(559220260914,))
   b.w.base.insert(db,'sources',dict(id=uid('source'),slug=SOURCE,name='Cypriot and Greek artist portraits: selected Wikimedia and institutional archive sources',source_type='collection_page',base_url='https://commons.wikimedia.org/'))
   for im in data['images']:
    a=target_artist(im,target);current=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s FOR UPDATE',(a['id'],)).fetchone()['row'];assert current==pre[a['id']],a['display_name']
    b.w.base.insert(db,'media_assets',dict(id=im['id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_page_url'],provider_name=im['provider'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=a['display_name']+'. '+im['subject_note'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['receipt']['retrieved_at'],verified_at=im['checked_at'],verified_by=ACTOR))
    b.w.base.insert(db,'media_rights_evidence',dict(media_id=im['id'],source_id=uid('source'),source_record_id=im['source_record_id'],source_checksum=im['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis=im['rights_basis'],adapter_version=SOURCE,checked_at=im['checked_at'],evidence_json=Jsonb(im)))
    b.w.base.insert(db,'citations',dict(entity_type='artist',entity_id=a['id'],field_name='portrait_media_id',source_id=uid('source'),source_record_id=im['source_record_id'],source_url=im['source_page_url'],evidence_note=json.dumps(dict(subject=im['subject_note'],view_label=im['view_label'],license=im['license_label'],source_checksum=im['receipt']['sha256']),ensure_ascii=False),retrieved_at=im['receipt']['retrieved_at'],created_by=ACTOR))
    assert db.execute('UPDATE artists SET portrait_media_id=%s,updated_by=%s,revision=revision+1 WHERE id=%s AND portrait_media_id IS NULL RETURNING id',(im['id'],ACTOR,a['id'])).fetchone()
  save(RUN/('applied-'+target+'.json'),dict(at=core.now(),plan_sha256=pin,portraits=len(data['images']),publication_unchanged=True));print(target,'attached',len(data['images']),'portraits',flush=True)
def verify():
 data=read('application-plan.json');ids=[i['artist']['id'] for i in data['images']];snap={}
 for target in ['local','production']:
  pre={v['row']['id']:v['row'] for v in json.loads((BACKUP/(target+'-artist-preimages.json')).read_text())}
  ids=[target_artist(im,target)['id'] for im in data['images']]
  with b.w.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for im in data['images']:
    a=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s',(target_artist(im,target)['id'],)).fetchone()['row'];before=pre[a['id']];assert a['portrait_media_id']==im['id'] and a['revision']==before['revision']+1
    exclude={'portrait_media_id','updated_at','updated_by','revision'};assert {k:v for k,v in a.items() if k not in exclude}=={k:v for k,v in before.items() if k not in exclude}
   rows=db.execute('SELECT a.slug,a.display_name,a.status,m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,m.attribution_text FROM artists a JOIN media_assets m ON m.id=a.portrait_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.slug',(ids,)).fetchall();assert len(rows)==len(ids)
   snap[target]=rows;save(RUN/('verified-'+target+'.json'),rows)
 assert snap['local']==snap['production']
 checks=[]
 for im in data['images']:
  response=b.requests.get(b.SITE+im['path'],timeout=45);response.raise_for_status();assert core.sha(response.content)==im['sha256'];checks.append(dict(path=im['path'],sha256=im['sha256'],status=response.status_code))
 save(RUN/'final-verification.json',dict(at=core.now(),parity=True,portraits=len(ids),public_images=checks,artist_fields_preserved=True));print('Verified',len(ids),'portraits in both databases and public storage',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['images','plan','apply','verify']);globals()[p.parse_args().phase]()
