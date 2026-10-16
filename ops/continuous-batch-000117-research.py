"""Bounded source research with immutable receipts; no scheduling or local DB writes."""
import importlib.util,json,gzip,requests,fcntl,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b114',ROOT/'ops/continuous-image-batch-000002.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base);h=base.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000117';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000117';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000117'
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def capture(key,url):
 p=E/(key+'.receipt.json')
 if p.exists():rc=h.load(p);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 res=requests.get(url,timeout=(15,40));raw=res.content;bp=S/(key+'.body.gz');bp.write_bytes(gzip.compress(raw,mtime=0));rc=save(key+'.receipt.json',dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=res.url,status=res.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After')));return raw,rc
