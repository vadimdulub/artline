#!/usr/bin/env python3
"""One exact Commons public-domain reproduction with RKD source credit."""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base);core=base.core
RUN=core.ROOT/'docs/research/local-commons-next-images-20261006';base.RUN=RUN
AID='803cd67f-594f-516a-b931-741703a46a72';QID='Q107860974';DIR='night-commons-rkd-reviewed'
CREDIT='RKD – Netherlands Institute for Art History, The Hague'
SOURCE_CREDIT_URL='https://rkd.nl/en/explore/images/242017'
POLICIES={'rkd-image-request':'https://www.rkd.nl/en/collection/visual-documentation/image-request','rkd-copyright':'https://www.rkd.nl/en/copyright'}
NOTE='Exact Commons artwork Q107860974 and explicit PD-Art/PDM for a faithful two-dimensional reproduction of the circa-1654 Fabritius painting. RKD policy applies rights-holder permission requirements to copyright-protected material; it is not itself a blanket open licence. No photograph-specific contrary claim is present in the exact Commons source. Retain Commons public-domain basis, both RKD policy captures and the requested full RKD source credit. Do not treat RKD subscription/download availability as image-use permission.'
core.HOSTS.add('www.rkd.nl');core.VERSION='local-commons-rkd-public-domain-credit-v1'

def verify_source(im):
 if (im['artwork_id'],im['qid'],im['rights_status'],im['policy_url'])!=(AID,QID,'public_domain',base.m.PDM):raise ValueError('Individual image identity/licence differs')
 p=im['raw']['commons'];meta=p['imageinfo'][0]['extmetadata']
 if SOURCE_CREDIT_URL not in meta['Credit']['value']:raise ValueError('Exact originating record differs')
 base.m.entity_match(im,im['raw']['wikidata'],False)
 base.m.rights_and_identity(im,im['raw']['wikidata'],p,im['raw']['structured_data'],im.get('rendered_licence_evidence'))
 review=im['raw']['rkd_policy_review']
 if review['decision']!=NOTE or CREDIT not in im['creator_credit'] or CREDIT not in im['attribution_text']:raise ValueError('Source decision or credit missing')
 for key,url in POLICIES.items():
  rc=review['captures'][key];path=core.ROOT/rc['path'];data=path.read_bytes()
  if not path.resolve().is_relative_to((RUN/'metadata/source-policies').resolve()) or rc['url']!=url or core.sha(data)!=rc['sha256']:raise ValueError('Pinned source policy differs')
  text=BeautifulSoup(data,'html.parser').get_text(' ',strip=True)
  expected='For copyright works, permission must be sought from the rights holder.' if key=='rkd-image-request' else 'If a work is still in copyright'
  if expected not in text:raise ValueError('Source policy review no longer corroborated')

def research():
 im=json.loads((RUN/'selected/night-commons'/(AID+'.json')).read_bytes());f=core.Fetcher(RUN/'metadata/source-policies');captures={}
 for key,url in POLICIES.items():
  p=f.cache/(key+'.html')
  if not p.exists():
   data,headers=f.get(url,3_000_000);core.save_new(p,data);core.save_new(p.with_suffix('.receipt.json'),dict(url=url,path=str(p.relative_to(core.ROOT)),sha256=core.sha(data),at=core.now(),headers=headers))
  captures[key]=json.loads(p.with_suffix('.receipt.json').read_bytes())
 im['raw']['rkd_policy_review']=dict(decision=NOTE,captures=captures)
 im['creator_credit']+='; '+CREDIT;im['attribution_text']+=' Source credit: '+CREDIT+'.'
 verify_source(im);core.save_new(RUN/'selected'/DIR/(AID+'.json'),im)
 held=0
 for p in (RUN/'selected/night-commons').glob('*.json'):
  other=json.loads(p.read_bytes());hold=base.policy_hold(other)
  if hold:
   core.event(RUN,dict(provider=other['provider'],artwork_id=other['artwork_id'],outcome='source_policy_hold',policy=hold));held+=1
 print('One exact public-domain reproduction selected;',held,'source-policy holds retained',flush=True)

original_attach=base.m.attach
def attach(db,im,target):
 if target!='local':raise ValueError('Only local attachment authorized')
 verify_source(im);result=original_attach(db,im,target)
 if result=='attached':db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(NOTE,im['media_id']))
 return result
base.m.attach=attach

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for p in (RUN/'selected'/DIR).glob('*.json'):verify_source(json.loads(p.read_bytes()))
  base.prepare(DIR)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():verify_source(im)
  base.verify()
