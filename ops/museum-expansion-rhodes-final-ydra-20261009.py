"""Resolve a stale WikiArt image URL using its current public object page."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-rhodes-final-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
u='https://www.wikiart.org/en/periklis-vyzantios/ydra-1959';bp=RUN/'captures/wikiart-ydra-001.body.gz';rp=RUN/'captures/wikiart-ydra-001.json'
if rp.exists():rc=m.load(rp);raw=gzip.decompress(bp.read_bytes())
else:
 res=requests.get(u,timeout=(15,45));res.raise_for_status();raw=res.content;bp.write_bytes(gzip.compress(raw));rc=dict(url=u,final_url=res.url,status=res.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(bp.relative_to(m.ROOT)));m.save(rp,rc)
soup=BeautifulSoup(raw,'html.parser');image=soup.find('meta',property='og:image')['content'];dest=Path('/Users/vadimdulub/Library/Application Support/Artline/research-proofs/rhodes-final-20261009/identity-images/292-ydra-current.jpg');res=requests.get(image,timeout=(15,45));res.raise_for_status();assert res.headers.get('Content-Type','').startswith('image/');dest.write_bytes(res.content)
m.save(RUN/'ydra-reference-001.json',dict(at=m.now(),existing_id='642e5277-f67a-53f4-8cf6-62a48b363bd6',page_receipt=rc,url=image,path=str(dest),sha256=hashlib.sha256(res.content).hexdigest(),bytes=len(res.content),rights_label='Fair Use',purpose='Physical identity reference only. No attachment.',previous_image_failure=dict(url='https://uploads8.wikiart.org/images/periklis-vyzantios/ydra-1959.jpg!Large.jpg',status=404,basis='Observed HTTPError in initial visual capture; stale URL not retried. Current object page explicitly supplies this image.'),script_reference=s.ref(Path(__file__).resolve())));print(str(dest))
