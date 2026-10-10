#!/usr/bin/env python3
"""One inventory-matched Warsaw self-portrait, using its native public image."""
import argparse,importlib.util,json
from pathlib import Path

s=importlib.util.spec_from_file_location('warsaw',Path(__file__).with_name('recover-local-commons-warsaw-alternates-20261006.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
base=w.base;core=w.core
RUN=core.ROOT/'docs/research/local-commons-warsaw-followup-20261006';w.RUN=RUN;base.RUN=RUN
PROVIDER='warsaw-native';core.PROVIDERS[PROVIDER]='National Museum in Warsaw'
core.HOSTS.update({'cyfrowe-api.mnw.art.pl','cyfrowe-cdn.mnw.art.pl'})
core.VERSION='local-warsaw-exact-native-self-portrait-v1'
SID='836010a6-41fe-55f9-a77b-d3327dc0783d'
SOURCE_SLUG='country-expansion-20260914-warsaw-primary-images'
REVIEW=dict(oid=445144,inventory='MP 2100 MNW',title='Autoportret',author='Dukszyńska-Dukszta, Emilia (1847-1898)',role='malarz',year='1890',legacy_id='15170',note='Exact full stored and authority inventory MP 2100 MNW, sole Emilia Dukszyńska-Dukszta, self-portrait title and 1890 date identify current native object 445144. Use its own primary image 556504. The Commons legacy URL does not supply an independently sufficient file identity. Native birth-year and tag/date inconsistencies remain source evidence only; no artist or artwork metadata is changed.')
w.REVIEWS={'Q104599440':REVIEW}
IMAGE=dict(id=556504,position=1,filePath='01/52/0152fddadfe00d414cfe1633fe16d842',extension='jpg',altText=None,altTextEn=None,vimeoUrl=None)
URL='https://cyfrowe-cdn.mnw.art.pl/upload/cache/multimedia_big/'+IMAGE['filePath']+'.jpg'
PAGE='https://cyfrowe.mnw.art.pl/en/catalog/445144'
CREDIT='Emilia Dukszyńska-Dukszta; National Museum in Warsaw'

def native_check(im):
 obj=w.verify_native_proof(im)
 if im['accession_number']!=REVIEW['inventory'] or im['institution_qid']!='Q153306' or im['roles']!=['primary']:raise ValueError('Stored native identity differs')
 if len(im['creators'])!=1 or im['creators'][0]['qid']!='Q8861120' or im['creators'][0]['death']!=1898:raise ValueError('Creator authority differs')
 if obj['image']!=IMAGE or obj['additionalImages']:raise ValueError('Reviewed native primary image differs')
 if im['page']!=PAGE or im['source_image_url']!=URL or im['provider']!=PROVIDER or im['creator_credit']!=CREDIT:raise ValueError('Native delivery or credit differs')
 if obj['types'][0]['name']!='obraz' or im['work_type']!='painting':raise ValueError('Object is not the reviewed painting')
 if CREDIT not in im['attribution_text'] or base.m.PDM not in im['attribution_text']:raise ValueError('Native attribution incomplete')

def research():
 c=json.loads((RUN/'candidates.json').read_bytes())['candidates']
 if len(c)!=1 or c[0]['qid']!='Q104599440':raise ValueError('Expected one selected self-portrait')
 c=c[0];f=core.Fetcher(RUN/'metadata/native-sources');p=f.cache/'museum-reuse-policy.html'
 if not p.exists():
  data,headers=f.get(w.POLICY,3_000_000);core.save_new(p,data);core.save_new(p.with_suffix('.receipt.json'),dict(at=core.now(),url=w.POLICY,path=str(p.relative_to(core.ROOT)),sha256=core.sha(data),headers=headers))
 policy=json.loads(p.with_suffix('.receipt.json').read_bytes())
 lead=json.loads((RUN/'warsaw-native-current-objects.json').read_bytes())['objects'][0]
 rc=json.loads((core.ROOT/lead['capture']).with_suffix('.receipt.json').read_bytes());rc['path']=lead['capture']
 sr=json.loads((core.ROOT/lead['search']['capture']).with_suffix('.receipt.json').read_bytes());sr['path']=lead['search']['capture']
 authority=json.loads((RUN/'authorities/Q104599440.json').read_bytes())
 proof=dict(decision=REVIEW,object_capture=rc,inventory_search_capture=sr,policy_capture=policy,current_native_url=PAGE)
 im=dict(c,provider=PROVIDER,page=PAGE,source_image_url=URL,policy_url=base.m.PDM,rights_status='public_domain',license_label='Public domain',checked_at=core.now(),creator_credit=CREDIT,raw=dict(wikidata=authority['entity'],wikidata_capture=authority['receipt'],current_originating_museum_review=proof),attribution_text=f"{CREDIT}. Self-portrait, 1890. Inventory MP 2100 MNW, native object 445144, image 556504. Public domain ({base.m.PDM}). {PAGE}. Full-frame proportional resize and JPEG compression.")
 native_check(im);core.save_new(RUN/'selected'/PROVIDER/(im['artwork_id']+'.json'),im)
 core.event(RUN,dict(provider=PROVIDER,artwork_id=im['artwork_id'],outcome='rights_selected',reason=REVIEW['note']))
 print('Selected exact native self-portrait',flush=True)

def attach(db,im,target):
 if target!='local':raise ValueError('Only local attachment authorized')
 native_check(im)
 source=db.execute('SELECT id::text,base_url FROM sources WHERE slug=%s',(SOURCE_SLUG,)).fetchone()
 if source!={'id':SID,'base_url':'https://cyfrowe.mnw.art.pl/'}:raise ValueError('Existing native source differs')
 result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  db.execute('UPDATE media_rights_evidence SET source_id=%s,source_record_id=%s,rights_basis=%s WHERE media_id=%s',(SID,'445144/556504','Exact full-inventory native object and its primary image; unrestricted public-domain object and current museum policy permits commercial image reuse. Native biography discrepancies retained only in evidence.',im['media_id']))
 return result
base.m.attach=attach

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):native_check(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():native_check(im)
  base.verify()
