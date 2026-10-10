"""Museum of Byzantine Culture selected native sources with fresh read-only baselines."""
import argparse,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-mbp-common-20261009.py');src=module('src','museum-expansion-beziers-source-20261009.py');prior=module('prior','museum-expansion-brest-apply-20261009.py');m=s.m;RUN=s.RUN;src.RUN=RUN;prod=src.prod
def baseline():
 assert s.ref(s.CP)['sha256']=='f7fe892665789f49617c7a7a5dd829bac848f30bede699f9f6a996266eaac454'
 for key,connect in [('initial',m.connect),('production-initial',prod.connect)]:
  dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
  with connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
   if key=='production-initial':p,d=prior.validate_plan();verification=prior.verify(db,p,d)
  m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(target=key,scope=len(ids),counts=counts)),flush=True)
 cp=m.load(s.CP);m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_checkpoint=s.ref(s.CP),previous_goal_turn='progress',verification=verification,prior_production_ids=p['prior_ids']+[v['artwork_id'] for v in p['records']],prior_plan=prior.reference(prior.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],policy='Fresh previous production delivery and all206prior production records verified. Historical archive proof inherited by pinned checkpoint. Local catalogue read-only; all source holds persist.'))
def source():
 from bs4 import BeautifulSoup
 rows=[];priorpath=m.RUN/'native/brest-20261009/next-mbp-icon-category-leads-001.json.gz';old=m.load(priorpath);links={a['url']:a for v in old['rows'] for a in v['links'] if '/en/exhibit/' in a['url']};assert len(links)==16
 for n,(url,index) in enumerate(links.items(),1):
  raw,rc=src.capture('icon-object-'+str(n).zfill(3)+'-001',url);soup=BeautifulSoup(raw,'html.parser');main=soup.select_one('main') or soup
  rows.append(dict(index=index,receipt=rc,title=[x.get_text(' ',strip=True) for x in main.select('h1')],text=main.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=a['href']) for a in main.select('a[href]')]))
  print(json.dumps(dict(number=n,url=url,titles=rows[-1]['title'])),flush=True)
 m.save(RUN/'native-icons-001.json.gz',dict(at=m.now(),rows=rows,discovery_reference=s.ref(priorpath),policy='16 selected individual icon/print highlights from two native collection categories. Metadata only, no image download. Index-card titles are discovery labels; object-page identity controls.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['baseline','source']);v=p.parse_args();globals()[v.command]()
