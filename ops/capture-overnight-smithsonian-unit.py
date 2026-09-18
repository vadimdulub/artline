#!/usr/bin/env python3
"""Capture a documented public Smithsonian unit's metadata, never its image corpus."""
import argparse,concurrent.futures,importlib.util,json,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
HOST='smithsonian-open-access.s3-us-west-2.amazonaws.com';core.HOSTS.add(HOST)
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--unit',required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();assert re.fullmatch('[a-z]+',a.unit)
    index=a.run/'index.txt';receipt=json.loads((a.run/'index.receipt.json').read_text());assert core.sha(index.read_bytes())==receipt['sha256'];urls=index.read_text().splitlines();assert len(urls)==256
    def stripe(group):
        f=core.Fetcher(a.run/'discovery')
        for u in group:
            if time.time()>=a.deadline:return
            assert re.fullmatch('https://'+re.escape(HOST)+'/metadata/edan/'+a.unit+'/[a-f0-9]{2}\.txt',u)
            path=a.run/'metadata'/u.rsplit('/',1)[-1];capture=path.with_suffix('.receipt.json')
            if path.exists():
                old=json.loads(capture.read_text());assert old['url']==u and core.sha(path.read_bytes())==old['sha256'];continue
            raw,headers=f.get(u,20_000_000)
            for line in raw.splitlines():assert json.loads(line)['unitCode'].casefold()==a.unit
            core.save_new(path,raw);core.save_new(capture,{'url':u,'retrieved_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),'headers':headers})
            with core.LOCK:
                count=len(list((a.run/'metadata').glob('*.txt')))
                if count%32==0:print(core.now(),a.unit,'metadata shards captured',count,'of',len(urls),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for job in [pool.submit(stripe,urls[n::3]) for n in range(3)]:job.result()
    print(core.now(),a.unit,'metadata capture pass complete',len(list((a.run/'metadata').glob('*.txt'))),flush=True)
if __name__=='__main__':main()
