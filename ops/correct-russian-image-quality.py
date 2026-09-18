#!/usr/bin/env python3
"""Replace only this pass's newly attached, visually obstructed photograph."""
import base64,hashlib,importlib.util,json,uuid
from pathlib import Path
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-russian-deep-images.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
core=a.core;RUN=a.RUN;wid='a820917e-6d8d-405a-9e49-0d62ba4ccd9f'
def main():
 old=json.loads((a.IMAGES/'images/russian-deep-commons'/(wid+'.json')).read_bytes());i=json.loads((RUN/'quality-review/alternative-selection.json').read_bytes());download=json.loads((RUN/'quality-review/alternative-download.json').read_bytes());original=Path(download['path']).read_bytes();assert core.sha(original)==download['sha256'];data,width,height,quality=core.compress(original);digest=core.sha(data);path=f'/assets/artworks/open-museums/russian-deep-commons/{wid}-{digest[:16]}.jpg'
 i.update(path=path,sha256=digest,bytes=len(data),width=width,height=height,jpeg_quality=quality,source_sha256=core.sha(original),source_bytes=len(original),downloaded_at=download['at'],response_headers=download['headers'],transform='Full-frame proportional resize and JPEG compression; no crop or generated content',media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)),supersedes_media_id=old['media_id'],quality_reason='Visually verified unobstructed photograph replaces a newly attached photograph with a visitor covering the lower-left painting area.')
 core.save_new(a.r.ROOT/'apps/web/public'/path.lstrip('/'),data);core.save_new(RUN/'quality-review/final-image.json',i)
 bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET);blob=bucket.blob(path.lstrip('/'));blob.metadata={'sha256':digest,'artwork-id':wid,'provider':i['provider'],'source-record-id':i['external_id'],'license':i['license_label']};blob.cache_control='public,max-age=31536000,immutable'
 try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
 except PreconditionFailed:blob.reload(timeout=30)
 assert blob.size==len(data) and blob.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode();results={}
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  baseline=json.loads((RUN/(target+'-before.json')).read_bytes());prior=next(w for w in baseline['works'] if any(e['scheme']==i['scheme'] and e['id']==i['external_id'] for e in w['identifiers'] or []));assert prior['primary_media_id'] is None;target_id=prior['id']
  with a.r.psycopg.connect(dsn,row_factory=a.r.dict_row) as db:
   row=db.execute('SELECT id,primary_media_id::text FROM artworks WHERE id=%s FOR UPDATE',(target_id,)).fetchone();assert row['primary_media_id'] in (old['media_id'],i['media_id'])
   if row['primary_media_id']==old['media_id']:
    # Both steps are inside this one transaction; NULL is never externally visible.
    db.execute('UPDATE artworks SET primary_media_id=NULL WHERE id=%s AND primary_media_id=%s',(target_id,old['media_id']));assert a.attach(db,i,target)=='attached'
    db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) SELECT 'artwork',%s,'image_quality_review',id,%s,%s,%s,now(),%s FROM sources WHERE slug='russian-deep-image-research'",(target_id,i['scheme']+':'+i['external_id'],i['page'],json.dumps({'reason':i['quality_reason'],'previous_media_id':old['media_id'],'new_media_id':i['media_id'],'new_sha256':digest}),core.ACTOR))
   results[target]={'previous_media_id':old['media_id'],'final_media_id':i['media_id'],'sha256':digest,'old_media_retained':True}
 core.save_new(RUN/'quality-review/database-receipt.json',results);core.event(a.IMAGES,{'provider':i['provider'],'artwork_id':wid,'external_id':i['external_id'],'outcome':'complete','local':'attached','cloud':'attached','path':path,'sha256':digest,'bytes':len(data),'quality_correction':True});print('Verified unobstructed photograph applied to both databases',flush=True)
if __name__=='__main__':main()
