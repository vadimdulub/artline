#!/usr/bin/env python3
"""Attach selected FNG CC0 photographs locally without changing holding claims."""
import argparse,functools,hashlib,importlib.util,json
from pathlib import Path

def module(name,file):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

base=module('base','recover-local-commons-images-20261005.py');fng=module('fng','overnight-fng-images.py');core=base.core
RUN=core.ROOT/'docs/research/local-fng-native-images-20261006';base.RUN=RUN
PROVIDER='fng-native';core.PROVIDERS[PROVIDER]='Finnish National Gallery';core.HOSTS.add('kokoelma.kansallisgalleria.fi')
core.VERSION='local-fng-image-only-owner-preserved-v1'
ORGANISATIONS={'ateneum-art-museum':'Kansallisgalleria / Ateneumin taidemuseo','sinebrychoff-art-museum':'Kansallisgalleria / Sinebrychoffin taidemuseo'}
OWNER_NOTE='Image-only attachment: the native owner and responsible collection are retained as source evidence; existing catalogue ownership and holding assertions are unchanged.'
DATE_REVIEW='The current museum record dates this work 1903–1913; the existing catalogue range 1900–1919 is retained for editorial review.'
MONOCHROME_ID='fc4d8780-976b-4d9c-adf5-4149002d7caf'
MONOCHROME_NOTE='Source-provided archival monochrome reproduction; original painting colours are not represented.'
MONOCHROME_SHA='5561ae705aaffd300d53347e1f606f64809e34943b782948e40c8d55bdd62624'

def visual_source_review(im):
 if im['artwork_id']!=MONOCHROME_ID:return None
 if (im['external_id'],im['source_image_url'])!=('430074','https://kokoelma.kansallisgalleria.fi/media-assets/1/jpg/1000/245177.jpg'):raise ValueError('Individually reviewed monochrome photograph differs')
 if im.get('source_sha256',MONOCHROME_SHA)!=MONOCHROME_SHA:raise ValueError('Monochrome source bytes differ')
 return dict(monochrome=True,full_composition=True,photo_id=245177,source_sha256=MONOCHROME_SHA,note=MONOCHROME_NOTE)

@functools.lru_cache(maxsize=1)
def source():
 cap=json.loads((RUN/'metadata/export-receipt.json').read_bytes());path=Path(cap['path'])
 if cap['url']!='https://kokoelma.kansallisgalleria.fi/api/v1/objects' or not path.resolve().is_relative_to((base.ARCHIVE/'source-images'/RUN.name/'metadata').resolve()):raise ValueError('Public native export identity differs')
 with path.open('rb') as stream:checksum=hashlib.file_digest(stream,'sha256').hexdigest()
 if checksum!=cap['sha256'] or path.stat().st_size!=cap['decoded_bytes']:raise ValueError('Pinned public export differs')
 selected=set(json.loads((RUN/'discovery.json').read_bytes())['selected_ids'])
 with base.connect() as db:ids={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='fng-object' AND entity_id=ANY(%s::uuid[])",(list(selected),)).fetchall()}
 ids.add('388924') # Current comparison record for the two Aert van der Neer person IDs.
 objects={}
 for row in json.loads(path.read_bytes()):
  oid=str(row['objectId'])
  if oid in ids:
   if oid in objects:raise ValueError('Ambiguous native object ID')
   objects[oid]=row
 return objects,cap

def select():
 if (RUN/'candidates.json').exists():return
 ids=json.loads((RUN/'discovery.json').read_bytes())['selected_ids']
 if not 1<=len(ids)<=40:raise ValueError('Native image selection exceeds reviewed bound')
 with base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   COALESCE((SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'birth',ar.birth_year,'death',ar.death_year) ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators,
   COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='fng-object'
   WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review' AND e.source_id IS NOT NULL
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id) ORDER BY a.id''',(ids,)).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
  for c in rows:
   c.update(provider=PROVIDER,artist='; '.join(x['name'] for x in c['creators']),target_ids={'local':c['artwork_id']})
   if len(c['creator_links'])!=1:raise ValueError('Selection needs an exact single linked creator')
   aid=c['creator_links'][0]['artist_id'];artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(aid,)).fetchone()['record']
   identifiers=[x['record'] for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(aid,)).fetchall()]
   c['creator_authority']=dict(artist_record=artist,artist_identifiers=identifiers)
   c['fng_people']=[x['external_id'] for x in identifiers if x['scheme']=='fng-person']
 if len(rows)!=len(ids):raise ValueError('Selected missing-image records changed before research')
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows))

def facts(c,o):
 if ORGANISATIONS.get(c['institution_slug'])!=o.get('responsibleOrganisation'):raise ValueError('Responsible native collection needs individual review')
 proof=c['creator_authority'];artist=proof['artist_record'];ids=proof['artist_identifiers']
 if c['creator_links'][0]['artist_id']!=artist['id'] or [x['external_id'] for x in ids if x['scheme']=='fng-person']!=c['fng_people']:raise ValueError('Pinned linked creator authority differs')
 expected=c;context=dict(native_owner=o.get('owner'),responsible_organisation=o['responsibleOrganisation'],review=OWNER_NOTE)
 if c['artwork_id']=='905a44d8-b433-49ca-ae1a-24491608247f':
  # Compare native person records before using this reviewed concordance as
  # the image expectation. The catalogue's existing authority stays intact.
  if (c['external_id'],c['accession_number'],c['fng_people'])!=('392848','A I 673',['62412']):raise ValueError('Individual Aert authority case differs')
  objects,_=source();other=objects['388924'];persons=[x for x in other['people'] if x.get('role',{}).get('en')=='Artist'];current=[x for x in o['people'] if x.get('role',{}).get('en')=='Artist']
  if len(persons)!=1 or len(current)!=1 or (persons[0]['id'],current[0]['id'])!=(62412,62968):raise ValueError('Native comparison authorities differ')
  keys=('firstName','familyName','birthYear','deathYear','birthPlace','deathPlace','attribution','role')
  if any(persons[0].get(k)!=current[0].get(k) for k in keys) or fng.norm(artist['display_name'])!=fng.norm(current[0]['firstName']+' '+current[0]['familyName']):raise ValueError('Native person concordance is not exact')
  if (current[0]['birthYear'],current[0]['deathYear'])!=(1603,1677):raise ValueError('Aert life-year concordance differs')
  context['creator_concordance']=dict(catalogue_person_id='62412',native_object_person_id='62968',comparison_object_id='388924',comparison_person=persons[0],object_person=current[0],note='Both current native person records identify Aert van der Neer with matching names, life years and birth/death places. Existing catalogue artist and identifiers are preserved.')
  expected=dict(c,fng_people=['62968'])
 if c['artwork_id']=='f430c2ae-c999-42db-8b4f-12a8723b22a4':
  if (c['external_id'],c['accession_number'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['date_display'])!=('6127043','A-2026-55',1900,1919,'range','1900–1919') or (o['yearFrom'],o['yearTo'],o.get('datePrefix'))!=(1903,1913,None):raise ValueError('Individually reviewed date narrowing differs')
  context['date_review']=dict(catalogue_bounds=[1900,1919],current_native_bounds=[1903,1913],note=DATE_REVIEW)
  expected=dict(c,creation_year_start=1903,creation_year_end=1913)
 photo,url=fng.source_match(expected,o,require_state_owner=False)
 person=next(x for x in o['people'] if x.get('role',{}).get('en')=='Artist')
 for key,native in [('birth_year','birthYear'),('death_year','deathYear')]:
  if artist[key] is not None and person.get(native) is not None and artist[key]!=person[native]:raise ValueError('Known creator life dates conflict')
 return photo,url,context

def verify_image(im):
 objects,cap=source();obj=objects.get(im['external_id'])
 if obj is None or im['raw']['object']!=obj or im['raw']['metadata_capture']!=cap:raise ValueError('Exact native object or capture differs')
 photo,url,context=facts(im,obj)
 credit=im['artist']+'; Finnish National Gallery'
 if photo.get('photographer_name'):credit+='; photograph: '+photo['photographer_name']
 if (im['source_image_url'],im['rights_status'],im['policy_url'],im['license_label'],im['creator_credit'])!=(url,'cc0',fng.LICENCE,'CC0 1.0',credit):raise ValueError('Exact image grant, URL or photographer credit differs')
 if im['raw'].get('owner_context')!=context or any(x not in im['attribution_text'] for x in [credit,fng.LICENCE]):raise ValueError('Source credit or image-only context missing')
 if context.get('date_review') and DATE_REVIEW not in im['attribution_text']:raise ValueError('Native date narrowing omitted from attribution')
 if im['page']!='https://kokoelma.kansallisgalleria.fi/en/object/'+im['external_id']:raise ValueError('Native artwork URL differs')
 visual=visual_source_review(im)
 if im['raw'].get('visual_source_review')!=visual or (visual and MONOCHROME_NOTE not in im['attribution_text']):raise ValueError('Monochrome source qualification missing or changed')

def research(retry_held=False):
 select();objects,cap=source();done={} if retry_held else core.latest_events(RUN)
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  path=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if path.exists():verify_image(json.loads(path.read_bytes()));continue
  if c['artwork_id'] in done:continue
  try:
   obj=objects[c['external_id']];photo,url,context=facts(c,obj);credit=c['artist']+'; Finnish National Gallery'
   if photo.get('photographer_name'):credit+='; photograph: '+photo['photographer_name']
   page='https://kokoelma.kansallisgalleria.fi/en/object/'+c['external_id']
   im=dict(c,page=page,source_image_url=url,rights_status='cc0',license_label='CC0 1.0',policy_url=fng.LICENCE,creator_credit=credit,checked_at=cap['at'],raw=dict(object=obj,metadata_capture=cap,owner_context=context),attribution_text=f"{c['artist']}. {c['title']}, {c['date_display']}. Inventory {c['accession_number']}. {credit}. CC0 ({fng.LICENCE}). {page}. Full-frame proportional resize and JPEG compression.")
   if context.get('date_review'):im['attribution_text']+=' '+DATE_REVIEW
   visual=visual_source_review(im)
   if visual:im['raw']['visual_source_review']=visual;im['attribution_text']+=' '+MONOCHROME_NOTE
   verify_image(im);core.save_new(path,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'));print('Selected CC0:',c['title'],flush=True)
  except (ValueError,KeyError) as error:
   core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)));print('Held:',c['title'],str(error),flush=True)

def attach(db,im,target):
 if target!='local':raise ValueError('Only local image attachment authorized')
 verify_image(im);proof=im['creator_authority'];aid=proof['artist_record']['id']
 artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s FOR SHARE',(aid,)).fetchone()['record']
 ids=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(aid,)).fetchall()]
 holding=[r['record'] for r in db.execute('SELECT to_jsonb(la) record FROM artwork_location_assertions la WHERE artwork_id=%s ORDER BY id FOR SHARE',(im['artwork_id'],)).fetchall()]
 if artist!=proof['artist_record'] or ids!=proof['artist_identifiers'] or holding!=im['holding_assertions']:raise ValueError('Creator authority or holding evidence changed')
 result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact current FNG object, inventory, native creator ID, title/type/date and preferred photograph-specific CC0 grant. Native owner retained as evidence; image-only update, no holding or ownership assertion changed.',im['media_id']))
 return result
base.m.attach=attach

def verify():
 for im in base.prepared():verify_image(im)
 base.verify();approved={x['artwork_id'] for x in json.loads((RUN/'visual-review.json').read_bytes())['images'] if x['decision']=='approved'};checks=[];held=[]
 with base.connect() as db:
  for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
   holding=[r['record'] for r in db.execute('SELECT to_jsonb(la) record FROM artwork_location_assertions la WHERE artwork_id=%s ORDER BY id',(c['artwork_id'],)).fetchall()]
   proof=c['creator_authority'];aid=proof['artist_record']['id'];artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(aid,)).fetchone()['record']
   ids=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(aid,)).fetchall()]
   if holding!=c['holding_assertions'] or artist!=proof['artist_record'] or ids!=proof['artist_identifiers']:raise ValueError('Holding evidence or creator authority changed')
   if c['artwork_id'] not in approved:
    if db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']!=c['before_record']:raise ValueError('Held artwork changed')
    held.append(c['artwork_id']);continue
   im=json.loads((RUN/'images'/(c['artwork_id']+'.json')).read_bytes())
   row=db.execute('SELECT m.creator_credit,m.attribution_text,m.rights_status,e.evidence_json,e.source_checksum FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
   if any(row[k]!=im[k] for k in ['creator_credit','attribution_text','rights_status']) or row['source_checksum']!=core.sha(core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete stored image evidence differs')
   checks.append(dict(artwork_id=im['artwork_id'],native_owner=im['raw']['object'].get('owner'),creator_and_holding_evidence_unchanged=True,complete_stored_evidence_verified=True))
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=len(checks),checks=checks,unchanged_held_artworks=held))
 core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=len(checks)+len(held),attached=len(checks),still_unattached=len(held),cc0_attached=len(checks),baseline_after=baseline,all_catalogue_metadata_and_holdings_preserved=True,production_changed=False,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);p.add_argument('--retry-held',action='store_true');a=p.parse_args()
 if a.phase=='research':research(a.retry_held)
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:verify()
