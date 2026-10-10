#!/usr/bin/env python3
"""Reuse museum adapters against only the frozen 5,000 production artworks."""
import argparse,collections,gzip,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
task=module('sample_task','ops/random-5000-museum-research-20261006.py');r=task.r;RUN=task.RUN
OLD=ROOT/'docs/research/artwork-locations-20261004'

def input_rows():
    rows=r.load(RUN/'baseline.json.gz');supplied=collections.defaultdict(list)
    for x in r.load(RUN/'supplied-research-links.json.gz'):supplied[x['artwork_id']].append(x['raw_json']['csv']['cells'])
    result=[]
    for aid,x in rows.items():result.append({**x,'artists':x['creator_keys'],'supplied':supplied.get(aid,[])})
    r.save_gz(RUN/'primary-input-rows.json.gz',result);print('Selected primary-adapter input',len(result),'with supplied provenance',len(supplied),flush=True)

def index(p):
    value=p.Index.__new__(p.Index);value.rows=r.load(RUN/'primary-input-rows.json.gz');value.institutions=r.load(RUN/'institutions.json.gz');value.by_id={x['artwork']['id']:x for x in value.rows};value.external=collections.defaultdict(list);value.supplied=collections.defaultdict(list)
    for row in value.rows:
        for e in row['identifiers']:value.external[(e['scheme'],e['external_id'])].append(row)
        for cells in row['supplied']:value.supplied[(r.namekey(cells[0]),p.titlekey(cells[1]),p.titlekey(cells[3]))].append(row)
    return value

def cached_source(url):
    for path in (OLD/'primary').glob('*.receipt.json'):
        rc=r.load(path)
        if rc.get('url')==url and rc.get('status')==200:
            raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert r.sha(raw)==rc['sha256'];return raw,rc
    raise RuntimeError('No previously captured complete museum dataset; use bounded object queries: '+url)

def france():
    f=module('selected_france','ops/research-artwork-location-france-20261004.py');f.r.RUN=RUN;f.r.PORT=r.PORT
    r.save(RUN/'french-institution-crosswalk-v2.json',(OLD/'french-institution-crosswalk-v2.json').read_bytes())
    i=index(f.p);f.selection(i);f.capture(i);f.plan(i)

def lombardia():
    f=module('selected_lombardia','ops/research-artwork-location-italy-20261004.py');f.r.RUN=RUN;f.r.PORT=r.PORT
    connect=f.r.connect;f.r.connect=lambda target='production',readonly=True:connect('production',readonly=readonly)
    i=index(f.p);f.selection(i);f.capture(i);f.plan(i)

def fng():
    p=module('selected_fng','ops/research-artwork-location-primary-20261004.py');p.r.RUN=RUN;p.r.PORT=r.PORT;p.source=cached_source;p.fng(index(p))

def arco():
    a=module('selected_arco','ops/research-artwork-location-arco-20261005b.py');a.r.RUN=RUN;a.r.PORT=r.PORT
    def selection():
        rows=[x for x in r.load(RUN/'primary-input-rows.json.gz')if any(c[4]=='Italy'for c in x['supplied'])]
        pairs=sorted({(title,c[2])for x in rows for c in x['supplied']if c[4]=='Italy'for title in a.variants(c[1])});return rows,pairs
    a.selection=selection;a.capture();a.identify();a.objects()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['input_rows','france','lombardia','fng','arco']);args=parser.parse_args();globals()[args.phase]()
