#!/usr/bin/env python3
"""Two Commons portraits with current, inventory-matched Warsaw rights evidence."""
import argparse,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base);core=base.core
RUN=core.ROOT/'docs/research/local-commons-multiple-images-20261006';base.RUN=RUN
PROVIDER_DIR='night-commons-native-reviewed'
POLICY='https://www.mnw.art.pl/en/news/the-new-digital-nmw-website,61.html'
core.HOSTS.add('www.mnw.art.pl');core.VERSION='local-commons-warsaw-current-inventory-rights-v1'
REVIEWS={
 'Q24694971':dict(oid=1048018,inventory='M.Ob.2688 MNW',title='Portret Marii de Castellane Radziwiłłowej (1840-1915)',author='Pape, William (1859-1920)',role=None,year='1897',legacy_id='502111',note='Current native Maria/Marie portrait, exact full inventory and sole William Pape identify the same 1897 painting. The Commons filename uses Elżbieta; native title and stored Marie are retained without adopting that filename as a sitter correction. Old native object ID 502111 now returns 404.'),
 'Q28173180':dict(oid=444971,inventory='MP 191 MNW',title='Portret pani Herse',author='Okuń, Edward (1872-1945)',role='malarz',year='1908',legacy_id='508047',note='Exact full inventory MP 191 MNW, sole Edward Okuń, Mrs Herse title and 1908 identify the portrait. The old source ID 508047 now resolves to an unrelated Utamaro print and is not used as current artwork evidence.'),
}

def capture(path,receipt):
 data=path.read_bytes()
 if core.sha(data)!=receipt['sha256']:raise ValueError('Pinned source capture differs')
 return data

def verify_native_proof(im):
 review=REVIEWS.get(im['qid']);proof=im['raw'].get('current_originating_museum_review')
 if not review or not proof or proof['decision']!=review:raise ValueError('Individual current museum review missing')
 rc=proof['object_capture'];p=core.ROOT/rc['path']
 if not p.resolve().is_relative_to((RUN/'metadata/native-sources').resolve()):raise ValueError('Native evidence outside operation')
 if rc['url']!='https://cyfrowe-api.mnw.art.pl/api/object/'+str(review['oid']):raise ValueError('Current native object ID differs')
 obj=json.loads(capture(p,rc))['data'];sr=proof['inventory_search_capture'];search=json.loads(capture(core.ROOT/sr['path'],sr))['data']
 if search['paginatorDetails']['totalItemsCount']!=1 or len(search['items'])!=1 or search['items'][0]['id']!=review['oid']:raise ValueError('Inventory crosswalk is not exact and unique')
 if obj['id']!=review['oid'] or obj['noEvidence']!=review['inventory'] or obj['title']!=review['title']:raise ValueError('Native identity changed')
 if review['inventory'] not in base.m.values(im['raw']['wikidata'],'P217'):raise ValueError('Artwork authority does not corroborate native inventory')
 if (len(obj['authors'])!=1 or obj['authors'][0]['name']!=review['author']
     or obj['authors'][0].get('role')!=review['role'] or obj['authors'][0].get('comment')
     or obj['authors'][0].get('additionalRoles') or obj['authors'][0].get('dcClassification',{}).get('name')!='autor'):
  raise ValueError('Sole unqualified native authorship differs')
 if len(obj['createDates'])!=1 or obj['createDates'][0]['name']!=review['year'] or obj['createDates'][0].get('comment'):raise ValueError('Native creation date differs')
 if im['creation_year_start']!=int(review['year']) or im['creation_year_end']!=int(review['year']):raise ValueError('Catalogue date conflicts')
 if obj['owner']['name']!='Muzeum Narodowe w Warszawie':raise ValueError('Native institution differs')
 rights=obj['copyrights']
 if len(rights)!=1 or rights[0]['name']!='DOMENA PUBLICZNA' or rights[0]['restricted'] is not False:raise ValueError('Current native rights are not unrestricted public domain')
 pr=proof['policy_capture'];html=capture(core.ROOT/pr['path'],pr);text=BeautifulSoup(html,'html.parser').get_text(' ',strip=True)
 if pr['url']!=POLICY or 'can be downloaded, processed and used without any restrictions, also commercially' not in text:raise ValueError('Museum reproduction reuse policy not confirmed')
 if im['rights_status']!='public_domain' or im['policy_url']!=base.m.PDM:raise ValueError('Image rights differ')
 base.m.entity_match(im,im['raw']['wikidata'],False)
 return obj

def verify_source(im):
 verify_native_proof(im)
 base.m.rights_and_identity(im,im['raw']['wikidata'],im['raw']['commons'],im['raw']['structured_data'],im.get('rendered_licence_evidence'))

def research():
 f=core.Fetcher(RUN/'metadata/native-sources');p=f.cache/'museum-reuse-policy.html'
 if not p.exists():
  data,headers=f.get(POLICY,3_000_000);core.save_new(p,data);core.save_new(p.with_suffix('.receipt.json'),dict(at=core.now(),url=POLICY,path=str(p.relative_to(core.ROOT)),sha256=core.sha(data),headers=headers))
 policy=json.loads(p.with_suffix('.receipt.json').read_bytes())
 leads={r['object_id']:r for r in json.loads((RUN/'warsaw-native-current-objects.json').read_bytes())['objects']}
 for path in (RUN/'selected/night-commons').glob('*.json'):
  im=json.loads(path.read_bytes());review=REVIEWS[im['qid']];lead=leads[review['oid']];rc=json.loads((core.ROOT/lead['capture']).with_suffix('.receipt.json').read_bytes());rc['path']=lead['capture'];sr=json.loads((core.ROOT/lead['search']['capture']).with_suffix('.receipt.json').read_bytes())
  im['raw']['current_originating_museum_review']=dict(decision=review,object_capture=rc,inventory_search_capture=sr,policy_capture=policy,current_native_url='https://cyfrowe.mnw.art.pl/en/catalog/'+str(review['oid']))
  verify_source(im);core.save_new(RUN/'selected'/PROVIDER_DIR/path.name,im)
 print('Current native identity and rights verified:',len(REVIEWS),flush=True)

original_attach=base.m.attach
def attach(db,im,target):
 if target!='local':raise ValueError('Only local attachment is authorized')
 verify_source(im);result=original_attach(db,im,target)
 if result=='attached':db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact authority-linked Commons file and current Warsaw full-inventory crosswalk; originating museum marks the exact work unrestricted public domain and permits commercial image reuse. Legacy numeric source URLs are preserved as history, not treated as current object IDs.',im['media_id']))
 return result
base.m.attach=attach

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER_DIR).glob('*.json'):verify_source(json.loads(path.read_bytes()))
  base.prepare(PROVIDER_DIR)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():verify_source(im)
  base.verify()
