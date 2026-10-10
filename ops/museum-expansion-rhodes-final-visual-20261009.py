"""Selected images for physical identity comparisons; no production attachments."""
import hashlib,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-rhodes-final-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
DEST=Path('/Users/vadimdulub/Library/Application Support/Artline/research-proofs/rhodes-final-20261009/identity-images');DEST.mkdir(parents=True,exist_ok=True)
wiki={291:['boat-with-sails'],292:['summer-in-hydra','boats-hydra','port']}
citations=m.load(RUN/'production-identity-citations-001.json.gz')['citations'];out=[]
def fetch(key,u,source):
 file=DEST/(key+'.jpg');rcpath=RUN/'captures'/(key+'-visual-001.json')
 if rcpath.exists():
  rc=m.load(rcpath);assert file.exists()and hashlib.sha256(file.read_bytes()).hexdigest()==rc['sha256']
 else:
  response=requests.get(u,timeout=(15,45));response.raise_for_status();raw=response.content;assert response.headers.get('Content-Type','').startswith('image/')and len(raw)<5_000_000;file.write_bytes(raw);rc=dict(url=u,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),path=str(file),source_url=source,purpose='Selected visual identity reference only, no attachment or display claim. Actual source rights retained in metadata evidence.') ;m.save(rcpath,rc)
 print(key,str(file),flush=True);return rc
for r in sum([m.load(RUN/v)['rows']for v in ['native-selection-001.json.gz','native-selection-002.json.gz']],[]):
 if r['n']not in {291,292,320,360,363,364}:continue
 ds,receipt=s.capture('datastreams-'+r['uuid']+'-001','/public/containers/'+r['uuid']+'/datastreams');assert len(ds['content'])==1;obj=ds['content'][0];assert obj['parent']==r['uuid'];url=obj['bitstreamFile']['thumbnails']['mediumUrl'];assert url.startswith('https://repox.mgamuseum.gr/api/files/')
 out.append(dict(number=r['n'],provider='native',receipt=fetch(str(r['n'])+'-native',url,r['source_url'])))
 for slug in wiki.get(r['n'],[]):
  c=next(v for v in citations if v['source_url']=='https://www.wikiart.org/en/periklis-vyzantios/'+slug);e=json.loads(c['evidence_note']);url=e['metadata']['image'];out.append(dict(number=r['n'],provider='wikiart-'+slug,existing_id=c['entity_id'],receipt=fetch(str(r['n'])+'-'+slug,url,c['source_url'])))
# One official National Gallery comparator with an unspecified generic title.
u='https://www.nationalgallery.gr/en/artwork/landscape-9/';bp=RUN/'captures/comparator-giallinas-landscape-001.body.gz';rp=RUN/'captures/comparator-giallinas-landscape-001.json'
if rp.exists():rc=m.load(rp);raw=__import__('gzip').decompress(bp.read_bytes())
else:
 response=requests.get(u,timeout=(15,45));response.raise_for_status();raw=response.content;__import__('gzip').open(bp,'wb').write(raw);rc=dict(url=u,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(bp.relative_to(m.ROOT)));m.save(rp,rc)
soup=BeautifulSoup(raw,'html.parser');img=soup.find('meta',property='og:image');assert img and img.get('content');url=img['content'];out.append(dict(number=320,provider='nationalgallery-landscape',existing_id='e78f98cd-2310-5f83-8df5-b5ee49f01be5',receipt=fetch('320-nationalgallery-landscape',url,u)))
m.save(RUN/'visual-reference-captures-001.json',dict(at=m.now(),rows=out,script_reference=s.s.ref(Path(__file__).resolve())))
