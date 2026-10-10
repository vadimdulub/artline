"""Selected public Kazantzakis collection metadata with immutable receipts."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-kazantzakis-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;CAP=RUN/'captures';CAP.mkdir(parents=True,exist_ok=True)
def capture(key,u):
 rp=CAP/(key+'.json');bp=CAP/(key+'.body.gz')
 if rp.exists():rc=m.load(rp);raw=gzip.decompress(bp.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256'];assert rc['status']==200;return BeautifulSoup(raw,'html.parser'),rc
 res=requests.get(u,timeout=(15,45));raw=res.content;bp.write_bytes(gzip.compress(raw));rc=dict(url=u,final_url=res.url,status=res.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(bp.relative_to(m.ROOT)));m.save(rp,rc);res.raise_for_status();return BeautifulSoup(raw,'html.parser'),rc
if __name__=='__main__':
 old=m.load(m.RUN/'native/rhodes-final-20261009/next-source-discovery-001.json.gz');selected=[('searchculture-art-ert0075-001',old['rows'][0]['leads'][0]['url']),('searchculture-theatre-34205-001',old['rows'][1]['leads'][0]['url']),('repository-art-category-001',next(v['url']for v in old['rows'][2]['navigation']if v['title']=='Έργα τέχνης'))];rows=[]
 for key,u in selected:
  soup,rc=capture(key,u);links=[dict(title=a.get_text(' ',strip=True),url=urljoin(u,a['href']))for a in soup.select('a[href]')];rows.append(dict(key=key,receipt=rc,text=soup.get_text(' ',strip=True),links=links));print(json.dumps(dict(key=key,status=rc['status'],bytes=rc['bytes'],text=soup.get_text(' ',strip=True)[:11000]),ensure_ascii=False),flush=True)
 m.save(RUN/'source-discovery-001.json.gz',dict(at=m.now(),rows=rows,prior_discovery_reference=s.ref(m.RUN/'native/rhodes-final-20261009/next-source-discovery-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Three selected source pages only,no images. Main www.kazantzaki.gr archive403 hold preserved.'))
