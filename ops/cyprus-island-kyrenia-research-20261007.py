#!/usr/bin/env python3
"""Selected public Kyrenia Ship catalogue metadata; no media or authenticated data."""
import argparse,gzip,importlib.util,json,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('island',Path(__file__).with_name('cyprus-island-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
h,R=x.h,x.R
BASE='https://www.kyreniaship.com'
TYPES={'AMPHORA','BASIN','BEAD','BOWL','CASSEROLE','CAULDRON','CHYTRA','COIN','CUP','FIGURINE','FISHPLATE','GUTTUS','JAR','JUG','KANTHAROS','KRATER','LAMP','LEKANIS','OLPE','PITCHER','PLATE','POT','SAUCER'}
class Reader:
    def __init__(self):
        self.session=requests.Session();self.token=None
    def read(self,path,payload):
        assert path in ['/objects/filters','/objects/results'] or path.startswith('/objects/') and path.endswith('/show.json') and path.split('/')[2].isdigit()
        digest=h.sha((path+json.dumps(payload,sort_keys=True)).encode());file=R/'kyrenia-selected'/(digest+'.json')
        if file.exists():return h.load(file)
        if self.token is None:
            response=self.session.get(BASE+'/objects',timeout=45);response.raise_for_status()
            self.token=BeautifulSoup(response.content,'html.parser').select_one('meta[name="csrf-token"]')['content']
        time.sleep(1.1)
        response=self.session.post(BASE+path,json=payload,headers={'X-CSRF-Token':self.token,'Accept':'application/javascript'},timeout=45)
        response.raise_for_status();assert len(response.content)<8_000_000
        data=response.json();body=R/'captures'/(digest+'.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(response.content))
        rc=dict(url=BASE+path,method='POST',public_read_payload=payload,status=response.status_code,sha256=h.sha(response.content),body_path=str(body.relative_to(x.n.REPO)),retrieved_at=h.now(),note='Anonymous public catalogue read. Session cookie and CSRF token are not retained.')
        result=dict(data=data,receipt=rc);h.save(file,result);return result
def run(sample=False):
    reader=Reader();filters=h.load(R/'indexes/kyrenia-filters.json')
    options=next(s for s in filters['data']['sections']if s['id']=='object_type')['options'];ids=[o['id']for o in options if o['label']in TYPES]
    payload={'filters':{'object_type':ids},'page':1};first=reader.read('/objects/results',payload)
    h.save(R/'indexes/kyrenia-selected-first.json',first)
    print('PAGINATION',first['data']['pagination'],flush=True)
    if sample:
        for obj in first['data']['objects'][:4]:
            value=reader.read('/objects/'+str(obj['id'])+'/show.json',{})
            print(json.dumps(value['data'],ensure_ascii=False)[:14000],flush=True)
        return
    pagination=first['data']['pagination'];print('OBJECTS FIRST',len(first['data']['objects']),flush=True)
    pages=pagination.get('total_pages');assert pages and pages<=40,pagination
    objects=list(first['data']['objects'])
    for page in range(2,pages+1):
        result=reader.read('/objects/results',{'filters':{'object_type':ids},'page':page});objects.extend(result['data']['objects'])
    assert len({o['id']for o in objects})==len(objects)
    h.save(R/'indexes/kyrenia-selected-objects.json',dict(objects=objects,filters=payload['filters'],pagination=pagination,policy='Selected ceramic, figurative, ornamental and coin objects only. Individual identity, dating and holding still require review.'))
    print('INDEXED',len(objects),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sample',action='store_true');args=p.parse_args();run(args.sample)
