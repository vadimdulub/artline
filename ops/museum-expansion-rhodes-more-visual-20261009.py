"""Four selected reference images for two object-identity comparisons; no attachments."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-rhodes-more-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
DEST=Path('/Users/vadimdulub/Library/Application Support/Artline/research-proofs/rhodes-more-20261009/identity-images');DEST.mkdir(parents=True,exist_ok=True)
wiki={192:'https://uploads5.wikiart.org/images/alekos-kontopoulos/one-country-1959.jpg',211:'https://uploads8.wikiart.org/images/konstantinos-parthenis/still-life-1935.jpg'}
out=[]
for r in m.load(RUN/'native-selection-001.json.gz')['rows']:
 if r['n']not in wiki:continue
 ds=m.load(RUN/('captures/datastreams-'+r['uuid']+'-001.body.gz'));assert len(ds['content'])==1;obj=ds['content'][0];assert obj['parent']==r['uuid'];url=obj['bitstreamFile']['thumbnails']['mediumUrl'];assert url.startswith('https://repox.mgamuseum.gr/api/files/')
 for provider,u in [('native',url),('wikiart',wiki[r['n']])]:
  key=str(r['n'])+'-'+provider;file=DEST/(key+'.jpg');rcpath=RUN/'captures'/(key+'-visual-001.json')
  if rcpath.exists():
   rc=m.load(rcpath);assert file.exists()and hashlib.sha256(file.read_bytes()).hexdigest()==rc['sha256']
  else:
   response=requests.get(u,timeout=(15,45));response.raise_for_status();raw=response.content;assert response.headers.get('Content-Type','').startswith('image/')and len(raw)<3_000_000;file.write_bytes(raw);rc=dict(url=u,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),path=str(file),source_url=r['source_url']if provider=='native'else wiki[r['n']],purpose='Bounded visual identity comparison only. No delivery, attachment or public image-use assertion. Actual native CC0 and WikiArt Fair Use labels retained separately.');m.save(rcpath,rc)
  out.append(dict(number=r['n'],provider=provider,receipt=rc));print(key,str(file),flush=True)
m.save(RUN/'visual-reference-captures-001.json',dict(at=m.now(),rows=out,script_reference=s.s.ref(Path(__file__).resolve())))
