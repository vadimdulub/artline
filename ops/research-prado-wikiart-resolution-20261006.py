#!/usr/bin/env python3
"""Evidence-preserving, selected Prado conflict and additional-work research."""
import gzip, hashlib, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT/'docs/research/prado-wikiart-20261006'
RUN=PREV/'resolution-20261006'
spec=importlib.util.spec_from_file_location('wikiart',PREV/'scripts/wikiart-research.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.RUN=RUN
network=m.fetch
FOLDERS=(RUN,PREV/'deep-research-20261006',PREV/'delivery',PREV/'round-2',PREV)

def fetch(url):
    key=hashlib.sha256(url.encode()).hexdigest()
    for folder in FOLDERS:
        f=folder/'captures'/(key+'.json')
        if f.exists():
            rc=json.loads(f.read_text());raw=gzip.decompress(f.with_suffix('.html.gz').read_bytes())
            assert hashlib.sha256(raw).hexdigest()==rc['sha256']
            return raw,rc
    return network(url)
m.fetch=fetch

def page(url):
    f=RUN/'pages'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if not f.exists():m.save(f,{'url':url,**m.page(url)})
    return json.loads(f.read_text())

if __name__=='__main__':
    queue=json.loads((RUN/(sys.argv[1] if len(sys.argv)>1 else 'resolution-queue.json')).read_text())
    for item in queue:
        p=page(item['url']);print(json.dumps({'url':item['url'],'metadata':{k:p.get('metadata',{}).get(k) for k in ('title','artistName','year','width','height')},'fields':p.get('attributes'),'rights':p.get('rights_label'),'error':p.get('error')},ensure_ascii=False),flush=True)
