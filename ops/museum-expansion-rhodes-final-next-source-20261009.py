"""Bounded next-museum source discovery; no ingestion or image downloading."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-rhodes-final-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
urls={'kazantzakis-searchculture':'https://www.searchculture.gr/aggregator/portal/collections/DigKazantzakis?language=en','anemoyannis-searchculture':'https://www.searchculture.gr/aggregator/portal/collections/Kazantzakis','kazantzakis-repository':'https://repository.kazantzaki.gr/'}
def capture(key,u):
 rp=RUN/'captures'/('next-'+key+'-001.json');bp=rp.with_suffix('.body.gz')
 if rp.exists():rc=m.load(rp);raw=gzip.decompress(bp.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256']
 else:
  res=requests.get(u,timeout=(15,45));raw=res.content;bp.write_bytes(gzip.compress(raw));rc=dict(url=u,final_url=res.url,status=res.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(bp.relative_to(m.ROOT)));m.save(rp,rc);res.raise_for_status()
 soup=BeautifulSoup(raw,'html.parser');links=[dict(title=a.get_text(' ',strip=True),url=urljoin(u,a['href']))for a in soup.select('a[href]')];return soup,links,rc
rows=[]
for key,u in urls.items():
 soup,links,rc=capture(key,u);leads=list({v['url']:v for v in links if '/aggregator/edm/' in v['url']}.values());navigation=[v for v in links if key.endswith('repository')and v['title']in['Έργα τέχνης','Θεατρικό υλικό']];rows.append(dict(key=key,receipt=rc,leads=leads,navigation=navigation,text=soup.get_text(' ',strip=True)));print(json.dumps(dict(key=key,leads=len(leads),navigation=navigation),ensure_ascii=False),flush=True)
m.save(RUN/'next-source-discovery-001.json.gz',dict(at=m.now(),museum_id='081a533b-4a9e-56df-89e0-407edf5c51be',rows=rows,main_website_hold=dict(url='https://www.kazantzaki.gr/en/nikos-kazantzakis-archive',status=403,evidence='web.open returned403 on9October2026; not retried. Independent museum repository and SearchCulture collections are directly linked public source catalogues.'),assessment='Two distinct museum collections:144 mixed Kazantzakis artworks/objects and2772 Anemoyannis theatre archive entries. These counts are not eligible artworks. First30 index leads from each captured only. Theatre entries can include separately catalogued painted costume/set designs, but physical units,creation versus performance dates,creator versus depicted/referenced persons,post1970 items and duplicates need individual review. No automatic attribution to Anemoyannis from referenced-person fields. No download of archive as a whole.',script_reference=s.ref(Path(__file__).resolve())))
