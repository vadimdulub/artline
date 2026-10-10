#!/usr/bin/env python3
"""Add six individually reviewed, pre-1970 CMA works with CC0 reproductions.

Retains uncertain creator authorities as object labels, original museum dates,
and review status. Never claims current display or assigns owner highlights.
Plan and apply are separate, backed up, guarded and idempotent operations.
"""
import argparse,base64,hashlib,importlib.util,json,uuid
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('audit',ROOT/'ops/audit-museum-gaps-20261005.py').r
core=module('images',ROOT/'ops/enrich-artwork-images.py')
OP='selected-museum-works-20261005';RUN=r.RUN/'new-cma-works';BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
EDITOR='local-european-research'
SELECTED={160885:'frans-hals-q167654',122338:None,171296:'robert-seldon-duncanson-nga-22843',97165:None,170235:'johann-georg-platzer-round3-22f0cedbdce9',132367:None}
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+str(k)))
def insert(db,table,row):
 db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder()for _ in row)),tuple(row.values()))

def duplicate_check(db,w,institution,artist):
 url=w['url'];oid=str(w['id'])
 assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme ILIKE %s AND external_id=%s)) LIMIT 1",(url,'%cleveland%',oid)).fetchone(),'Source identity already exists'
 assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork'AND source_url=%s LIMIT 1",(url,)).fetchone(),'Source citation already exists'
 assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s LIMIT 1',(institution,w['accession_number'])).fetchone(),'Museum accession already exists'
 if artist:
  assert not db.execute('SELECT 1 FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND (lower(a.title)=lower(%s) OR lower(a.alternate_title)=lower(%s)) LIMIT 1',(artist,w['title'],w['title'])).fetchone(),'Creator/title requires identity review'

def plan():
 assert not (RUN/'plan.json.gz').exists(),'Plan already pinned'
 review=r.load(r.RUN/'new-cma-review.json.gz');works=[]
 for oid,artist_slug in SELECTED.items():
  candidates=[x for x in review if x['object']['id']==oid];assert len(candidates)==2 and not any(x['existing_identities']for x in candidates)
  raw,receipt=r.capture('https://openaccess-api.clevelandart.org/api/artworks/'+str(oid),tag='new-cma-primary',timeout=30)
  assert receipt['status']==200;w=json.loads(raw)['data'];assert w['id']==oid and w['type']=='Painting' and w['share_license_status']=='CC0'
  assert 0<w['creation_date_earliest']<=w['creation_date_latest']<=1970 and len(w['creators'])==1 and not w['creators'][0].get('qualifier')
  assert w['title']==candidates[0]['object']['title'] and w['accession_number']==candidates[0]['object']['accession_number']
  works.append(dict(object=w,source_receipt=receipt,artist_slug=artist_slug,artwork_id=uid('work/'+str(oid)),media_id=uid('media/'+str(oid))))
 targets={}
 for target in ['local','production']:
  with r.connect(target)as db:
   inst=db.execute("SELECT to_jsonb(i)row FROM institutions i WHERE slug='cleveland-museum-of-art'").fetchone()['row'];artists={}
   for row in works:
    slug=row['artist_slug'];artist=None
    if slug:
     artist=db.execute('SELECT to_jsonb(a)row FROM artists a WHERE slug=%s AND status<>\'archived\'',(slug,)).fetchone()['row'];artists[slug]=artist
    duplicate_check(db,row['object'],inst['id'],artist['id']if artist else None)
   targets[target]={'institution':inst,'artists':artists}
 r.save_gz(RUN/'plan.json.gz',dict(works=works,targets=targets,at=r.now(),policy='Six selected museum paintings; explicit CC0; no publication, no invented creators or display assertions.'))
 print('Pinned',len(works),'new works for both databases')

def prepare():
 plan=r.load(RUN/'plan.json.gz');fetcher=core.Fetcher(RUN/'image-captures')
 for row in plan['works']:
  w=row['object'];dest=RUN/'images'/(str(w['id'])+'.json.gz')
  if dest.exists():continue
  url=w['images']['web']['url'];body,headers=fetcher.get(url)
  original=ORIGINALS/(str(w['id'])+'.source');r.save(original,body)
  data,width,height,quality=core.compress(body);digest=core.sha(data);path='/assets/artworks/open-museums/cleveland/'+row['artwork_id']+'-'+digest[:16]+'.jpg'
  assert len(data)<=100000;r.save(ROOT/'apps/web/public'/path.lstrip('/'),data)
  r.save_gz(dest,dict(path=path,sha256=digest,bytes=len(data),width=width,height=height,jpeg_quality=quality,source_image_url=url,source_sha256=core.sha(body),source_bytes=len(body),original_path=str(original),headers=headers,downloaded_at=r.now(),transform='Proportional full-composition resize and JPEG compression; no cropping.'))
  print(w['title'],len(data),'bytes',flush=True)

def upload():
 p=r.load(RUN/'plan.json.gz');bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket('artline-508319-images');receipts=[]
 for row in p['works']:
  w=row['object'];im=r.load(RUN/'images'/(str(w['id'])+'.json.gz'));data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(data)==im['sha256']and len(data)<=100000
  blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'artwork-id':row['artwork_id'],'provider':'cleveland','source-record-id':str(w['id']),'license':'CC0 1.0'};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
  except PreconditionFailed:blob.reload(timeout=30)
  assert blob.size==len(data)and blob.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
  receipts.append(dict(path=im['path'],generation=str(blob.generation),sha256=im['sha256'],bytes=len(data)))
 r.save_gz(RUN/'uploaded.json.gz',receipts);print('Verified cloud uploads',len(receipts))

def apply(target):
 path=RUN/'plan.json.gz';p=r.load(path);digest=core.sha(path.read_bytes());old=p['targets'][target];sid=uid('source');ids=[w['artwork_id']for w in p['works']]
 assert len(r.load(RUN/'uploaded.json.gz'))==len(ids)
 with r.connect(target,readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  exists=db.execute('SELECT id::text,primary_media_id::text,status FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
  if exists:
   assert len(exists)==len(ids)and all(x['status']=='review'for x in exists);print(target,'already added');return
  for row in p['works']:
   w=row['object'];artist=old['artists'].get(row['artist_slug']);duplicate_check(db,w,old['institution']['id'],artist['id']if artist else None)
   if artist:assert db.execute('SELECT to_jsonb(a)row FROM artists a WHERE id=%s FOR SHARE',(artist['id'],)).fetchone()['row']==artist,'Creator authority changed'
  r.save_gz(BACKUP/(target+'-preimages.json.gz'),dict(plan_sha256=digest,**old,new_artwork_ids=ids))
  insert(db,'sources',dict(id=sid,slug=OP,name='Cleveland Museum of Art: selected collection additions, 5 October 2026',source_type='museum_api',base_url='https://openaccess-api.clevelandart.org/api/artworks/'))
  for row in p['works']:
   w=row['object'];aid=row['artwork_id'];mid=row['media_id'];im=r.load(RUN/'images'/(str(w['id'])+'.json.gz'));artist=old['artists'].get(row['artist_slug']);label=w['creators'][0]['description'].split(' (')[0]
   insert(db,'media_assets',dict(id=mid,storage_kind='local',storage_path=im['path'],source_page_url=w['url'],provider_name='The Cleveland Museum of Art',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=w['title']+' — '+label,rights_status='cc0',license_label='CC0 1.0',license_url='https://creativecommons.org/publicdomain/zero/1.0/',creator_credit=label+'; The Cleveland Museum of Art',attribution_text=w['creditline'],retrieved_at=im['downloaded_at'],verified_at=r.now(),verified_by=EDITOR))
   insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=str(w['id']),source_checksum=row['source_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url='https://www.clevelandart.org/open-access',rights_basis='CMA object API explicitly declares share_license_status CC0.',adapter_version=OP,checked_at=row['source_receipt']['retrieved_at'],evidence_json=Jsonb(dict(source=row['source_receipt'],image=im,share_license_status=w['share_license_status']))))
   circa=w['creation_date'].lower().startswith(('c.','circa','about'));precision=('circa'if circa else'exact')if w['creation_date_earliest']==w['creation_date_latest']else('circa_range'if circa else'range')
   insert(db,'artworks',dict(id=aid,slug='cma-selected-'+str(w['id']),title=w['title'],normalized_title=w['title'].lower(),creation_year_start=w['creation_date_earliest'],creation_year_end=w['creation_date_latest'],date_display=w['creation_date'],date_precision=precision,work_type='painting',medium_text=w['technique'],dimensions_text=w['measurements'],accession_number=w['accession_number'],primary_media_id=mid,status='review',research_candidate=True,unlinked_creator_label=None if artist else label,created_by=EDITOR,updated_by=EDITOR))
   if artist:insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist['id'],attribution_role='primary',attribution_note='Named creator reconciled with the museum catalogue; existing authority dates preserved.'))
   insert(db,'artwork_media',dict(artwork_id=aid,media_id=mid,view_label='Full composition'))
   insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='cleveland-object',external_id=str(w['id']),canonical_url=w['url'],source_id=sid,retrieved_at=row['source_receipt']['retrieved_at']))
   note='Selected museum collection record '+str(w['id'])+', accession '+w['accession_number']+'. Creator, creation interval, title, medium and dimensions transcribed from the primary object API. Reproduction explicitly CC0. Artwork remains in review; no current-display claim. Plan SHA-256 '+digest+'.'
   insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='museum_source_metadata',source_id=sid,source_record_id=str(w['id']),source_url=row['source_receipt']['url'],evidence_note=note,retrieved_at=row['source_receipt']['retrieved_at'],created_by=EDITOR))
   insert(db,'artwork_location_assertions',dict(id=uid('holding/'+str(w['id'])),artwork_id=aid,claim_type='holding',institution_id=old['institution']['id'],context='collection',source_id=sid,source_url=w['url'],evidence_note='Current CMA object record identifies this accession as part of its collection. Holdings only; no display assertion.',checked_at=row['source_receipt']['retrieved_at'],review_state='accepted'))
  after=[x['row']for x in db.execute('SELECT to_jsonb(a)row FROM artworks a WHERE id=ANY(%s::uuid[])ORDER BY id',(ids,)).fetchall()]
  assert len(after)==len(ids)and all(x['current_institution_id']==old['institution']['id']and x['status']=='review'and x['primary_media_id']for x in after)
 r.save_gz(BACKUP/(target+'-after.json.gz'),dict(plan_sha256=digest,artworks=after));print(target,'added',len(ids),'new works with images, in review')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','prepare','upload','apply']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.command=='apply':assert args.target;apply(args.target)
 else:globals()[args.command]()
