"""Capture only selected Paris museum object metadata; no image fetches or retries."""
import gzip,hashlib,importlib.util,json,re,sys,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fourteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN
def main():
    lo,hi=map(int,sys.argv[1:]);assert 6<=lo<=hi<=605
    root=RUN/'paris-object-context-001';root.mkdir(exist_ok=True)
    assert not list(root.glob('*.error.json')),'Prior access/fetch error must remain held, without automatic retries'
    candidates=RUN/'native-candidates-001.json.gz';rows=[r for r in m.load(candidates)['rows'] if lo<=r['number']<=hi];done=[]
    for r in rows:
        number=r['number'];sid=r['source_id'];url=r['facts']['source_fields']['Lien_site_associe'].strip();u=urlparse(url)
        assert u.scheme=='https' and u.hostname=='www.parismuseescollections.paris.fr' and re.fullmatch(r'/node/\d+',u.path) and not u.query
        base=root/f'{number:03d}-{sid}';rp=Path(str(base)+'.receipt.json');hp=Path(str(base)+'.html.gz');tp=Path(str(base)+'.txt')
        if rp.exists():
            x=m.load(rp);assert x['status']==200 and x['url']==url and hp.exists() and tp.exists() and hashlib.sha256(gzip.decompress(hp.read_bytes())).hexdigest()==x['sha256'];done.append(f.ref(rp));continue
        try:
            time.sleep(1)
            with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected object catalogue metadata)'},timeout=(15,45),stream=True) as response:
                raw=b''
                for chunk in response.iter_content(65536):
                    raw+=chunk
                    if len(raw)>4_000_000:raise ValueError('Response exceeds selected metadata bound')
                x=dict(number=number,source_id=sid,url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                hp.write_bytes(gzip.compress(raw,mtime=0));m.save(rp,x);response.raise_for_status()
            soup=BeautifulSoup(raw,'html.parser')
            for tag in soup(['script','style','noscript']):tag.decompose()
            tp.write_text(soup.get_text('\n',strip=True));done.append(f.ref(rp));print(json.dumps(dict(number=number,status=x['status'],bytes=len(raw))),flush=True)
        except Exception as e:
            m.save(Path(str(base)+'.error.json'),dict(at=m.now(),url=url,error=repr(e),policy='Stop on first failure; no automatic retry or alternate-route bypass.'));raise
    p=RUN/f'paris-object-context-{lo:03d}-{hi:03d}-complete.json';assert not p.exists();m.save(p,dict(at=m.now(),capture_script=f.ref(Path(__file__).resolve()),candidate_reference=f.ref(candidates),receipts=done,read_only=True,images=0))
if __name__=='__main__':main()
