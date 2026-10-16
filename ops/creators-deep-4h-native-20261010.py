#!/usr/bin/env python3
"""Bounded primary object captures for an already selected creator."""
import importlib.util,json,sys,gzip,threading,time,os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,urlsplit
from pathlib import Path
spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name(os.environ.get('ARTLINE_CREATOR_DRIVER','creators-deep-4h-20261010.py')))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
x.configure(sys.argv[1])
LOCK=threading.Lock()
BLOCKED={}
for p in (x.RUN/'native-captures').glob('*.receipt.json'):
    rc=x.r.load(p)
    if rc.get('status') in [403,429]: BLOCKED[urlsplit(rc['url']).netloc]=rc
stop=x.RUN/'progress/source-access-stop.json'
if stop.exists():
    rc=x.r.load(stop);BLOCKED[urlsplit(rc['url']).netloc]=rc
def fetch(url):
    # The reused WikiArt capture helper has a campaign-wide stop flag. Native
    # hosts are independent: preserve every denial, stop that host, and allow
    # unrelated official museum hosts. Never change identity or bypass denial.
    key=x.r.sha(url.encode());dest=x.RUN/'native-captures'/(key+'.receipt.json')
    if dest.exists():
        rc=x.r.load(dest);raw=gzip.decompress((x.ROOT/rc['body_path']).read_bytes())
        assert x.r.sha(raw)==rc['sha256'];return raw,rc
    host=urlsplit(url).netloc
    with LOCK:
        if host in BLOCKED: raise RuntimeError('This host is paused after a recorded HTTP 403/429: '+host)
        time.sleep(.25)
    response=x.m.requests.get(url,headers={'User-Agent':'ArtlineCatalogueResearch/1.0 (selected creator research)'},timeout=(15,45))
    body=x.RUN/'native-captures'/(key+'.body.gz');raw=response.content
    rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=x.r.now(),sha256=x.r.sha(raw),bytes=len(raw),body_path=str(body.relative_to(x.ROOT)),content_type=response.headers.get('Content-Type'))
    x.r.save(body,gzip.compress(raw,mtime=0));x.r.save(dest,rc)
    if response.status_code in [403,429]:
        with LOCK:BLOCKED[host]=rc
    return raw,rc
def capture(url):
    dest=x.RUN/'native-objects'/(x.r.sha(url.encode())+'.json')
    if dest.exists(): return x.r.load(dest)
    try:
        raw,rc=fetch(url)
        if rc['status'] != 200:
            x.r.save(x.RUN/'native-host-holds'/(x.r.sha(url.encode())+'.json'),dict(url=url,receipt=rc,reason='Source returned non-success status; no access-control bypass attempted'))
            print('HELD',rc['status'],url,flush=True)
            return None
    except Exception as error:
        x.r.save(x.RUN/'native-host-holds'/(x.r.sha(url.encode())+'.json'),dict(url=url,error=str(error),reason='Source request failed; no bypass attempted'))
        print('HELD',type(error).__name__,url,flush=True)
        return None
    soup=x.m.BeautifulSoup(raw,'html.parser')
    images=[dict(url=urljoin(url,im.get('src','')),alt=im.get('alt')) for im in soup.select('img[src]')]
    meta=soup.select_one('meta[property="og:image"]')
    value=dict(url=url,receipt=rc,title=soup.title.get_text(' ',strip=True) if soup.title else None,
        text=soup.get_text(' ',strip=True),images=images,og_image=urljoin(url,meta.get('content','')) if meta else None)
    x.r.save(dest,value)
    print(value['title'],url,flush=True)
    return value
urls=json.loads(Path(sys.argv[2]).read_text())
with ThreadPoolExecutor(max_workers=3) as pool:
    for value in pool.map(capture,urls): pass
