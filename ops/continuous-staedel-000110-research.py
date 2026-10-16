import importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-staedel-images-000110.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.load(b.E/'gap-input.json.gz');parser=b.mod('parser110','popular-staedel-images.py')
for x in g['identifiers']:
 if x['scheme']!='staedel-object':continue
 aid=x['entity_id'];url=x['canonical_url'];raw,rc=b.capture(url)
 if rc['status']!=200: print('held',aid,rc['status']);continue
 sp=BeautifulSoup(raw,'html.parser');props={}
 for dl in sp.select('dl.dsProperty'):
  if dl.dt and dl.dd:props.setdefault(dl.dt.get_text(' ',strip=True),[]).append(dl.dd.get_text(' ',strip=True))
 b.save('native/'+aid+'.json',dict(url=url,receipt=rc,properties=props,date=sp.select_one('h1 .dsArtwork__titleYear').get_text(' ',strip=True),canonical=sp.select_one('meta[property="og:url"]')['content'],image=sp.select_one('meta[property="og:image"]')['content']))
 print(aid,props.get('Title'),props.get('Picture Copyright'),flush=True)
 if props.get('Picture Copyright')==['Public Domain']:
  raw,rc=b.capture(url+'/download');assert rc['status']==200
  rights=parser.parse_download(json.loads(raw),url)
  b.save('rights/'+aid+'.json',dict(receipt=rc,rights=rights))
