#!/usr/bin/env python3
"""Bounded early-painting and fresco research; local review delivery only."""
import argparse
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('icons',ROOT/'ops/byzantine-russian-expansion.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=m.RUN=ROOT/'docs/research/early-paintings-frescoes-20260920'
m.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
m.SOURCE=RUN.name
m.IMAGE_CAMPAIGN=m.IMAGE_ASSET_FOLDER=RUN.name
m.IMAGE_CONTACT_SHEET='/tmp/artline-early-paintings-frescoes-contact.jpg'
m.HOSTS.update({'www.museunacional.cat'})


def audit():
    with m.psycopg.connect(m.DSN,options='-c default_transaction_read_only=on',row_factory=m.dict_row) as db:
        rows=db.execute("""SELECT to_jsonb(a) artwork FROM artworks a
          WHERE creation_year_end<=1500 OR work_type='fresco' ORDER BY id""").fetchall()
        summary=db.execute("""SELECT work_type,count(*) total,count(*) FILTER(WHERE primary_media_id IS NOT NULL) illustrated
          FROM artworks WHERE creation_year_end<=1500 OR work_type='fresco' GROUP BY work_type ORDER BY total DESC""").fetchall()
    if not (RUN/'baseline.json').exists():m.save(RUN/'baseline.json',{'at':m.now(),'summary':summary,'records':rows})
    print(json.dumps(summary),flush=True)


def record(provider,obj,capture):
    key=str(obj['objectID'] if provider=='met' else obj['id'])
    path=RUN/(provider+'-objects')/(key+'.json')
    if not path.exists():m.save(path,{'object':obj,'capture':capture})


def collect_met():
    c=m.Capture();leads=set()
    queries=[{'q':'fresco'},{'q':'wall painting','title':'true'},
             {'q':'painting','medium':'Paintings','dateBegin':-5000,'dateEnd':1500},
             {'q':'tempera','medium':'Paintings','dateBegin':-5000,'dateEnd':1500}]
    for query in queries:
        url='https://collectionapi.metmuseum.org/public/collection/v1.1/search?'+urlencode({**query,'offset':0,'limit':400})
        raw,receipt=c.get(url);data=json.loads(raw)
        leads.update(data.get('objectIDs') or [])
        print('Met metadata search',query['q'],'total',data['total'],'bounded leads',len(data.get('objectIDs') or []),flush=True)
    assert len(leads)<=1600
    for index,oid in enumerate(sorted(leads)):
        path=RUN/'met-objects'/(str(oid)+'.json')
        if path.exists():continue
        url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+str(oid)
        try:
            raw,receipt=c.get(url);record('met',json.loads(raw),receipt)
        except Exception as exc:
            held=RUN/'fetch-held'/('met-'+str(oid)+'.json')
            if not held.exists():m.save(held,{'url':url,'error':str(exc),'at':m.now()})
        if (index+1)%40==0:print('Met object metadata',index+1,'/',len(leads),flush=True)


def collect_cleveland():
    c=m.Capture()
    for query,pages in [({'type':'Painting','created_before':1501},3),({'q':'fresco'},1),({'q':'wall painting'},1)]:
        for page in range(pages):
            url='https://openaccess-api.clevelandart.org/api/artworks/?'+urlencode({**query,'limit':200,'skip':page*200})
            raw,receipt=c.get(url);data=json.loads(raw)
            for obj in data['data']:record('cleveland',obj,receipt)
            print('Cleveland metadata',query,'page',page+1,'records',len(data['data']),'total',data['info']['total'],flush=True)
            if (page+1)*200>=data['info']['total']:break


def collect():
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=[pool.submit(fn) for fn in (collect_met,collect_cleveland)]
        for result in results:result.result()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit','collect','fetch']);p.add_argument('urls',nargs='*');args=p.parse_args()
    if args.stage=='fetch':m.fetch_pages(args.urls)
    else:globals()[args.stage]()
