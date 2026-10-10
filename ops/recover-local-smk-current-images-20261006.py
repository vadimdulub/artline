#!/usr/bin/env python3
"""Selected current SMK images, exact source matches and local-only attachment."""
import argparse,importlib.util,json,re
from pathlib import Path

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('base','recover-local-commons-images-20261005.py');smk=module('smk','overnight-smk-selected-images.py');core=base.core
RUN=core.ROOT/'docs/research/local-smk-current-images-20261006';base.RUN=RUN
PROVIDER='smk-current-native';core.PROVIDERS[PROVIDER]='Statens Museum for Kunst (SMK)';core.VERSION='local-smk-current-image-only-v1'
ALTERNATE_ID='4104e117-075d-4de5-8cd1-b39f0d093a7c'
ALTERNATE_URL='https://iip.smk.dk/iiif/jp2/c247dz364_kms9205.tif.jp2/full/!1000,1000/0/default.jpg'
RECTO_ID='c9ce9f81-56f1-4a27-9a66-a162cd0ef5fe'
RECTO_NOTE='Portrait on the front of the sheet; the related reverse-side landscape is not shown.'

def source_image_review(im,obj,primary):
 if im['artwork_id']!=ALTERNATE_ID:return primary,None
 if (im['external_id'],obj['id'])!=('KMS9205','1170308715_object'):raise ValueError('Individually reviewed alternate object differs')
 rejected=json.loads((RUN/'primary-image-rejection.json').read_bytes());alternate=json.loads((RUN/'alternate-image-receipt.json').read_bytes())
 if rejected['source_image_url']!=primary or rejected['source_sha256']!='435cad074ddde4ec21dcde77fea0c0153f7d0613176dbcb4d50638a0cf9c9dbd' or rejected['decision']!='rejected_black_image':raise ValueError('Rejected primary evidence differs')
 if core.sha(Path(rejected['source_archive']).read_bytes())!=rejected['source_sha256'] or (core.ROOT/'apps/web/public'/rejected['path'].lstrip('/')).exists():raise ValueError('Rejected primary is not preserved privately')
 if obj.get('alternative_images')!=[alternate['native_alternate']] or alternate['url']!=ALTERNATE_URL or ALTERNATE_URL!=alternate['native_alternate']['iiif_id']+'/full/!1000,1000/0/default.jpg':raise ValueError('Explicit native alternate image differs')
 if core.sha(Path(alternate['source_archive']).read_bytes())!=alternate['sha256'] or im.get('source_sha256',alternate['sha256'])!=alternate['sha256']:raise ValueError('Reviewed alternate source bytes differ')
 return ALTERNATE_URL,dict(primary_rejection=rejected,alternate_capture=alternate,note='Native primary reproduction is black and rejected. The same native object explicitly lists this alternate photograph; full composition visually verified before attachment.')

def select():
 if (RUN/'candidates.json').exists():return
 capture=json.loads((RUN.parent/'local-smk-current-metadata-20261006/capture.json').read_bytes())
 prior={x['artwork_id'] for x in json.loads((RUN.parent/'local-smk-native-image-20261006/candidates.json').read_bytes())['candidates']}
 ids=[x['artwork_id'] for x in capture['current_leads'] if x['current_index_occurrences']==1 and x['artwork_id'] not in prior]
 if not 1<=len(ids)<=20:raise ValueError('New native leads outside bounded selection')
 with base.connect() as db:
  rows=db.execute("""SELECT a.id::text artwork_id,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,to_jsonb(a) before_record,
   i.id::text institution_id,i.slug institution_slug,i.name museum,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
   WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review' AND e.source_id IS NOT NULL
   AND e.scheme IN ('smk-object','european-smk-statens-museum-for-kunst-object') AND i.slug='statens-museum-for-kunst'
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id) ORDER BY a.id""",(ids,)).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
  for c in rows:
   if len(c['creator_links'])!=1 or c['roles']!=['primary']:raise ValueError('Creator is not a single primary maker')
   aid=c['creator_links'][0]['artist_id'];artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(aid,)).fetchone()['record']
   identifiers=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(aid,)).fetchall()]
   native=[x['external_id'] for x in identifiers if x['scheme']=='smk-person']
   if len(native)!=1:raise ValueError('Exact existing native artist ID unavailable')
   c.update(provider=PROVIDER,artist=artist['display_name'],artist_authority=native[0],creator_authority=dict(artist_record=artist,artist_identifiers=identifiers),target_ids={'local':c['artwork_id']})
 if len(rows)!=len(ids):raise ValueError('Selected missing-image records changed')
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows))

def verify_image(im):
 rc=im['raw']['metadata_capture'];url='https://api.smk.dk/api/v1/art?object_number='+im['external_id'];path=RUN/'metadata'/(core.sha(url.encode())+'.json')
 data=path.read_bytes()
 if rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']:raise ValueError('Pinned native object capture differs')
 objects=json.loads(data)['items']
 if len(objects)!=1 or im['raw']['object']!=objects[0]:raise ValueError('Native object is not exact and unique')
 obj=objects[0];photo,facts=smk.source_match(im,obj);photo,review=source_image_review(im,obj,photo)
 if im['source_image_url']!=photo or im['raw']['native_facts']!=facts or im['raw'].get('source_image_review')!=review:raise ValueError('Native photograph or source facts differ')
 proof=im['creator_authority'];artist=proof['artist_record'];native=[x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='smk-person'];person=smk.primary_maker(obj)
 if native!=[im['artist_authority']] or im['creator_links'][0]['artist_id']!=artist['id']:raise ValueError('Existing creator authority differs')
 if smk.norm(artist['display_name'])!=smk.norm(person.get('creator_forename','')+' '+person.get('creator_surname','')):raise ValueError('Native creator name differs')
 for local,source in [('birth_year','creator_date_of_birth'),('death_year','creator_date_of_death')]:
  value=person.get(source,'')
  if artist[local] is not None and re.match(r'^\d{4}-',value) and artist[local]!=int(value[:4]):raise ValueError('Known creator life dates differ')
 credit=im['artist']+'; Statens Museum for Kunst (SMK)'
 if (im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'],im['page'])!=('public_domain','Public Domain Mark 1.0',smk.PDM,credit,obj['frontend_url']):raise ValueError('Image grant or source credit differs')
 if any(x not in im['attribution_text'] for x in [credit,smk.PDM,im['page']]):raise ValueError('Source attribution incomplete')
 if im['artwork_id']==RECTO_ID and (im['external_id']!='KKS14704' or [x['reference'] for x in obj.get('related_objects',[])]!=['KKS14704 verso'] or RECTO_NOTE not in im['attribution_text']):raise ValueError('Portrait-bearing side qualification differs')

def research():
 select();fetch=core.Fetcher(RUN/'metadata')
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  path=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if path.exists():verify_image(json.loads(path.read_bytes()));continue
  try:
   url='https://api.smk.dk/api/v1/art?object_number='+c['external_id'];obj=fetch.metadata(url)['items']
   if len(obj)!=1:raise ValueError('Native object is ambiguous or absent')
   obj=obj[0];c=dict(c,source_api_id=obj['id']);photo,facts=smk.source_match(c,obj);photo,review=source_image_review(c,obj,photo)
   cap=json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_bytes());credit=c['artist']+'; Statens Museum for Kunst (SMK)'
   im=dict(c,source_image_url=photo,rights_status='public_domain',license_label='Public Domain Mark 1.0',policy_url=smk.PDM,creator_credit=credit,checked_at=cap['retrieved_at'],raw=dict(object=obj,metadata_capture=cap,native_facts=facts),attribution_text=f"{c['artist']}. {c['title']}, {c['date_display']}. Inventory {c['accession_number']}. {credit}. Public Domain Mark ({smk.PDM}). {c['page']}. Full-frame proportional resize and JPEG compression.")
   if review:im['raw']['source_image_review']=review
   if im['artwork_id']==RECTO_ID:im['attribution_text']+=' '+RECTO_NOTE
   verify_image(im);core.save_new(path,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'));print('Selected:',c['title'],flush=True)
  except ValueError as error:core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)));print('Held:',c['title'],str(error),flush=True)

def authority_unchanged(db,im):
 proof=im['creator_authority'];aid=proof['artist_record']['id']
 artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(aid,)).fetchone()['record']
 ids=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(aid,)).fetchall()]
 holding=[r['record'] for r in db.execute('SELECT to_jsonb(la) record FROM artwork_location_assertions la WHERE artwork_id=%s ORDER BY id',(im['artwork_id'],)).fetchall()]
 if artist!=proof['artist_record'] or ids!=proof['artist_identifiers'] or holding!=im['holding_assertions']:raise ValueError('Creator authority or holding evidence changed')

def attach(db,im,target):
 if target!='local':raise ValueError('Only local image attachment authorized')
 verify_image(im);authority_unchanged(db,im);result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact current SMK object, inventory, existing native maker authority, title/type/date and native image Public Domain Mark. Preferred photograph or explicitly documented same-object alternate, individually visually reviewed. Image-only local attachment; no holding or ownership assertion changed.',im['media_id']))
 return result
base.m.attach=attach

def verify():
 for im in base.prepared():verify_image(im)
 base.verify();approved={r['artwork_id'] for r in json.loads((RUN/'apply-receipt.json').read_bytes())['receipts'] if r['result']=='attached'};checks=[];held=[]
 with base.connect() as db:
  for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
   authority_unchanged(db,c)
   if c['artwork_id'] not in approved:
    if db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']!=c['before_record']:raise ValueError('Held artwork changed')
    held.append(c['artwork_id']);continue
   im=json.loads((RUN/'images'/(c['artwork_id']+'.json')).read_bytes());row=db.execute('SELECT m.creator_credit,m.attribution_text,m.rights_status,e.evidence_json,e.source_checksum FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
   if any(row[k]!=im[k] for k in ['creator_credit','attribution_text','rights_status']) or row['source_checksum']!=core.sha(core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete stored image evidence differs')
   checks.append(c['artwork_id'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=len(checks),artwork_ids=checks,creator_and_holding_evidence_unchanged=True,complete_stored_evidence_verified=True,unchanged_held_artworks=held))
 core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=len(checks)+len(held),attached=len(checks),still_unattached=len(held),public_domain_attached=len(checks),baseline_after=baseline,all_catalogue_metadata_and_holdings_preserved=True,production_changed=False,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:verify()
