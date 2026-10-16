#!/usr/bin/env python3
"""Consolidate three individually confirmed paintings, preserving qualifications."""
import argparse,importlib.util,json,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('im',Path(__file__).with_name('million-nga-images-20261010.py'));im=importlib.util.module_from_spec(s);s.loader.exec_module(im);n=im.n;m=n.m;d=im.d
RUN=n.RUN/'identity-followup-002'
DAVID='8f0b5eb9-e231-5361-9efa-1a1be418539d';ZURBARAN='dcdc3591-2aac-54a9-8a65-7d709483404a'

def plan():
 dest=RUN/'plan.json.gz'
 if dest.exists():return m.load(dest)
 visual=m.load(n.RUN/'duplicate-followup-visual-review.json');pairs=[x for x in visual['decisions'] if x['decision']=='same_painting'];assert len(pairs)==3
 ids=[aid for p in pairs for aid in [p['new_id'],p['existing_id']]];source={x['artwork_id']:x for x in m.load(n.RUN/n.PLAN)['new_artworks']}
 with m.m.connect() as db:
  before=d.snapshot(db,ids)
  ext=db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
  media=db.execute('SELECT a.id::text artwork_id,to_jsonb(ma) media,to_jsonb(re) evidence FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence re ON re.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',([p['new_id'] for p in pairs],)).fetchall()
  for p in pairs:
   old=before[p['existing_id']]['artwork'];new=before[p['new_id']]['artwork'];assert old['status']=='review' and new['status']=='review' and old['current_institution_id'] is None and new['current_institution_id']==n.MID
   assert len(before[p['existing_id']]['creators'])==1 and before[p['existing_id']]['creators'][0]['attribution_role']=='primary'
   if p['existing_id'] in [DAVID,ZURBARAN]:assert old['primary_media_id'] is None and old['creation_year_start'] is None and old['creation_year_end'] is None
   else:assert old['primary_media_id'] is not None and old['date_display']=='1916'
   assert not before[p['existing_id']]['holdings']
  for item in media:
   assert item['media']['provider_name']=='National Gallery of Art' and item['evidence']['source_record_id']==source[item['artwork_id']]['native_id']
   response=requests.get('https://artlines.org'+item['media']['storage_path'],timeout=(15,60));response.raise_for_status();assert m.sha(response.content)==item['media']['checksum_sha256']
 assert len(media)==2
 out=dict(at=m.now(),pairs=pairs,before=before,identifiers=[x['v'] for x in ext],media=media,source_rows={p['new_id']:source[p['new_id']] for p in pairs},visual_review=visual,
  basis='Each pair is the same individually inspected physical painting. Canonical older records retain their title/status and original images. Two missing dates receive NGA literal creation statements. Circle/workshop qualifications remain explicit; native IDs, museum holding and already-delivered images connect to the canonical record. Duplicate source records are archived with redirects and full history retained.',confidence='At least 98% editorial confidence; not a calibrated probability')
 m.save(dest,out);m.save(RUN/'pin.json',dict(sha256=m.sha(dest.read_bytes())));m.save(m.BACKUP/'nga/identity-followup-002/plan.json.gz',out);return out

def apply():
 if (RUN/'applied.json').exists():return
 p=plan();pin=m.load(RUN/'pin.json')['sha256'];assert m.sha((RUN/'plan.json.gz').read_bytes())==pin;ids=list(p['before'])
 with m.m.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  assert d.snapshot(db,ids)==p['before'],'Selected record changed since preflight'
  ext=db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall();assert sorted([x['v'] for x in ext],key=lambda x:x['id'])==sorted(p['identifiers'],key=lambda x:x['id'])
  for pair in p['pairs']:
   newer,older=pair['new_id'],pair['existing_id'];old=p['before'][older]['artwork'];new=p['before'][newer]['artwork'];row=p['source_rows'][newer];artist=p['before'][older]['creators'][0]['artist_id'];wiki=m.load(n.RUN/'duplicate-followup-pages'/(older+'.json'))
   moving=[x for x in p['identifiers'] if x['entity_id']==newer]
   for x in moving:assert not any(y['entity_id']==older and y['scheme']==x['scheme'] for y in p['identifiers'])
   db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s",(older,newer))
   n.copy_rows(db,'artwork_location_assertions',[dict(id=m.uid('reconciled-holding/'+newer),artwork_id=older,claim_type='holding',institution_id=n.MID,context='collection',source_id=n.SID,source_url=row['source_url'],evidence_note=json.dumps(dict(native_object=row['raw'],basis=pair['basis'],confidence=p['confidence']),ensure_ascii=False),checked_at=m.now(),review_state='accepted')])
   if older==DAVID:
    db.execute("UPDATE artwork_artists SET attribution_role='circle_of',attribution_note=%s WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",('NGA attribution: Circle of Jacques-Louis David. Prior WikiArt primary attribution retained in reconciliation evidence.',older,artist))
   elif older==ZURBARAN:
    n.copy_rows(db,'artwork_artists',[dict(artwork_id=older,artist_id=artist,attribution_role='workshop',representative_order=2,attribution_note='NGA explicitly credits Francisco de Zurbarán and Workshop; the primary artist and workshop participation are both retained.')])
   for attachment in p['before'][newer]['attachments']:
    if not any(x['media_id']==attachment['media_id'] for x in p['before'][older]['attachments']):
     order=db.execute('SELECT coalesce(max(sort_order),-1)+1 n FROM artwork_media WHERE artwork_id=%s',(older,)).fetchone()['n'];n.copy_rows(db,'artwork_media',[dict(artwork_id=older,media_id=attachment['media_id'],sort_order=order,view_label=attachment['view_label'])])
   if older in [DAVID,ZURBARAN]:
    db.execute('UPDATE artworks SET primary_media_id=%s,date_display=%s,creation_year_start=%s,creation_year_end=%s,date_precision=%s,unlinked_creator_label=%s,updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s',(new['primary_media_id'],row['date_display'],row['first'],row['last'],row['precision'],row['creator_label'],m.ACTOR,older))
   evidence=dict(plan_sha256=pin,archived_duplicate_id=newer,canonical_id=older,prior_record=p['before'][older],native_object=row['raw'],native_creators=row['creators'],wikiart_receipt=wiki['receipt'],visual_basis=pair['basis'],qualification_and_date_basis=row['creator_label']+'; literal NGA creation statement: '+row['date_display'],identifiers_before=moving)
   n.copy_rows(db,'citations',[dict(id=m.uid('reconciliation/'+newer),entity_type='artwork',entity_id=older,field_name='million_catalogue_identity_reconciliation',source_id=n.SID,source_record_id=row['native_id'],source_url=row['source_url'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
   db.execute("UPDATE artworks SET status='archived',updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s",(m.ACTOR,newer));n.copy_rows(db,'slug_redirects',[dict(id=m.uid('redirect/'+newer),entity_type='artwork',entity_id=older,old_slug=new['slug'])])
  after=d.snapshot(db,ids)
  for pair in p['pairs']:
   newer,older=pair['new_id'],pair['existing_id'];assert after[newer]['artwork']['status']=='archived' and after[older]['artwork']['status']==p['before'][older]['artwork']['status'] and after[older]['artwork']['current_institution_id']==n.MID
   assert all(a in after[older]['attachments'] for a in p['before'][older]['attachments'])
  db.commit()
 receipt=dict(at=m.now(),plan_sha256=pin,canonical_map={x['new_id']:x['existing_id'] for x in p['pairs']},archived_new_duplicates=3,existing_records_connected=3,existing_images_reused=2,new_image_files=0,unknown_dates_resolved=2,qualified_attributions_preserved=True)
 m.save(RUN/'applied.json',receipt);print(json.dumps(receipt),flush=True)

def verify():
 p=plan();receipt=m.load(RUN/'applied.json');ids=list(p['before']);public=[]
 with m.m.connect() as db:
  after=d.snapshot(db,ids)
  for pair in p['pairs']:
   newer,older=pair['new_id'],pair['existing_id'];old=after[older]['artwork'];new=after[newer]['artwork'];original=p['before'][older]['artwork'];source=p['source_rows'][newer]
   assert new['status']=='archived' and old['status']==original['status'] and old['title']==original['title'] and old['current_institution_id']==n.MID
   for x in p['identifiers']:
    if x['entity_id']==newer:assert db.execute('SELECT entity_id::text FROM external_identifiers WHERE id=%s',(x['id'],)).fetchone()['entity_id']==older
   roles={x['attribution_role'] for x in after[older]['creators']}
   assert roles==({'circle_of'} if older==DAVID else {'primary','workshop'} if older==ZURBARAN else {'primary'})
   if older in [DAVID,ZURBARAN]:assert (old['creation_year_start'],old['creation_year_end'],old['date_precision'],old['unlinked_creator_label'],old['primary_media_id'])==(source['first'],source['last'],source['precision'],source['creator_label'],p['before'][newer]['artwork']['primary_media_id'])
   else:assert old['primary_media_id']==original['primary_media_id'] and old['date_display']==original['date_display']
   assert db.execute('SELECT 1 FROM artwork_search_documents s JOIN artworks a USING(id) WHERE s.id=%s AND s.primary_media_id=%s AND s.status=a.status AND s.title=a.title',(older,old['primary_media_id'])).fetchone()
   assert db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND old_slug=%s AND entity_id=%s",(new['slug'],older)).fetchone()
   artist=after[older]['creators'][0]['artist_id'];slug=db.execute('SELECT slug FROM artists WHERE id=%s',(artist,)).fetchone()['slug'];path=db.execute('SELECT storage_path FROM media_assets WHERE id=%s',(old['primary_media_id'],)).fetchone()['storage_path'];url='https://artlines.org/api/backend/v1/artists/'+slug+'/works/'+older;response=requests.get(url,timeout=(15,60));response.raise_for_status();assert path in response.text;public.append(dict(artwork_id=older,url=url,status=response.status_code))
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts'];m.save(RUN/'verification.json',dict(at=m.now(),canonical_records=3,archived_duplicates=3,qualified_creator_checks=2,known_date_checks=2,reused_images=2,public_routes=public,local_baseline_equal=True));print('Verified three reconciled paintings and public routes.',flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['plan','apply','verify']);args=ap.parse_args();globals()[args.action]()
