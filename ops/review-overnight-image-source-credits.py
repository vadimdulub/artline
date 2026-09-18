#!/usr/bin/env python3
"""Preserve Commons source credits and hold two contradictory generic PD claims.

Asset bytes, rights evidence and artwork relationships are preserved. Unknown
rights hide the image through the existing Go media gate without deleting it.
"""
import argparse,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('im',Path(__file__).with_name('prepare-wikimedia-catalogue-images.py'));im=importlib.util.module_from_spec(s);s.loader.exec_module(im)
CORE=m.m.core;RUN=m.x.BASE/'image-rights-followup/final-review';SOURCE='overnight-image-source-credit-review-20260913'
HOLDS={'wikimedia-artwork-q116313903':'Commons PD-old-100-1923 says author life plus100, while identified AngladaCamarasa died1959. The generic tag is concretely inconsistent; per-work reuse needs clarification. Metadata remainsreview.','wikimedia-artwork-q19161460':'Commons genericPD-Art expiry assumption conflicts with identified AngladaCamarasa death1959. No independent work permission captured; hold rights for individual review, preserve metadata and authentic asset.'}
def plan():
 if (RUN/'plan.json').exists():return
 targets={}
 for target in ('local','production'):
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');rows=db.execute("""SELECT to_jsonb(ma) media,to_jsonb(r) evidence,
    coalesce((SELECT jsonb_agg(to_jsonb(w)) FROM artworks w WHERE w.primary_media_id=ma.id),'[]') works
    FROM media_assets ma JOIN media_rights_evidence r ON r.media_id=ma.id JOIN sources s ON s.id=r.source_id
    WHERE s.slug='overnight-country-images-20260913' AND (ma.license_label LIKE 'CC BY%%' OR EXISTS(SELECT 1 FROM artworks w WHERE w.primary_media_id=ma.id AND w.slug=ANY(%s)))""",(list(HOLDS),)).fetchall()
  targets[target]={r['media']['storage_path']:r for r in rows}
 assert set(targets['local'])==set(targets['production']),'Finish both-database image applications before this review'
 entries=[]
 for path,before in targets['local'].items():
  media=before['media'];evidence=before['evidence']['evidence_json'];meta=evidence['commons_page']['imageinfo'][0]['extmetadata'];credit=im.image_credit(meta);updates={};context=[]
  if credit!=media['creator_credit']:
   updates.update(creator_credit=credit,attribution_text=media['attribution_text']+' Additional source attribution: '+credit+'. File page: '+media['source_page_url']);context.append('Preserve source/photographer and required attribution fields in addition to the depicted painter; no image pixels or licence changed.')
  for w in before['works']:
   if w['slug'] in HOLDS:
    updates.update(rights_status='unknown',verified_at=None,verified_by=None);context.append(HOLDS[w['slug']])
  if not updates:continue
  other=targets['production'][path];assert all(media[k]==other['media'][k] for k in ('storage_path','checksum_sha256','creator_credit','attribution_text','rights_status','license_label','verified_at'))
  entries.append(dict(path=path,updates=updates,context=context,source_page_url=media['source_page_url'],source_receipt=evidence['commons_receipt'],targets={t:targets[t][path] for t in targets}))
 for t in targets:CORE.save_new(m.BACKUPS/('image-source-review-'+t+'-preimages.json'),{e['path']:e['targets'][t] for e in entries})
 CORE.save_new(RUN/'plan.json',entries);CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/'plan.json').read_bytes()),media=len(entries),rights_holds=sum('rights_status' in e['updates'] for e in entries)));print('Image source-review plan',len(entries),flush=True)
def apply():
 raw=(RUN/'plan.json').read_bytes();entries=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256']
 for target in ('local','production'):
  dest=RUN/(target+'-verified.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   for e in entries:
    old=e['targets'][target];mid=old['media']['id']
    with db.transaction():
     db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Selected Commons image attribution and source-claim consistency review','collection_page','https://commons.wikimedia.org/')
     if db.execute("SELECT 1 FROM citations WHERE entity_type='media' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(mid,sid,'%'+pin+'%')).fetchone():continue
     assert db.execute('SELECT to_jsonb(ma) row FROM media_assets ma WHERE id=%s FOR UPDATE',(mid,)).fetchone()['row']==old['media']
     fields=e['updates'];query=sql.SQL('UPDATE media_assets SET {},updated_at=now() WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in fields));db.execute(query,(*fields.values(),mid))
     m.m.r.base.insert(db,'citations',dict(entity_type='media',entity_id=mid,field_name='rights_source_review',source_id=sid,source_record_id=e['path'],source_url=e['source_page_url'],retrieved_at=e['source_receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,context=e['context'],source_receipt=e['source_receipt'],before={k:old['media'][k] for k in fields},updates=fields,original_evidence_preserved=True),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY')
    for e in entries:
     old=e['targets'][target];now=db.execute('SELECT to_jsonb(ma) row FROM media_assets ma WHERE id=%s',(old['media']['id'],)).fetchone()['row'];expected={**old['media'],**e['updates']};assert {k:v for k,v in now.items() if k!='updated_at'}=={k:v for k,v in expected.items() if k!='updated_at'}
     assert db.execute('SELECT to_jsonb(r) row FROM media_rights_evidence r WHERE media_id=%s',(now['id'],)).fetchone()['row']==old['evidence']
     for w in old['works']:assert db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(w['id'],)).fetchone()['row']==w
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,verified_media=len(entries),rights_holds=sum('rights_status' in e['updates'] for e in entries),assets_and_artworks_preserved=True));print(target,'image source review verified',len(entries),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
