"""Native pages for15 selected Kilkis sculptures and reliefs; literal metadata only."""
import importlib.util,json,time
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-source-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;RUN=m.RUN/'native/kilkis-20261010';q.RUN=RUN;q.CAP=RUN/'captures'
xs=m.load(RUN/'selected-object-discovery-001.json.gz')['rows'];rows=[]
for r in xs:
 urls=sorted({v['url']for v in r['native_links']if v['url'].rstrip('/')!='https://www.efa-kilkis.gr/artworks'});assert len(urls)==1,(r['source_id'],urls);url=urls[0];soup,rc=q.capture('native-'+r['source_id'].split('/')[-1]+'-001',url);main=soup.find('main')or soup;imgs=[dict(alt=v.get('alt'),src=urljoin(url,v.get('src','')),srcset=v.get('srcset'))for v in main.select('img[src]')];rows.append(dict(number=r['number'],source_id=r['source_id'],native_url=url,receipt=rc,title=soup.title.get_text(' ',strip=True),text=main.get_text(' ',strip=True),images=imgs));print(json.dumps(dict(number=r['number'],source_id=r['source_id'],native_text=main.get_text(' ',strip=True)[:6500]),ensure_ascii=False),flush=True);time.sleep(.15)
m.save(RUN/'native-selected-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=q.s.ref(RUN/'selected-object-discovery-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),policy='15 selected sculpture/relief native pages,not all65sourceobjects. ImagesURLs captured butimagesnotdownloaded. Sourceperiods remainliteral; EKT numericalrangesarenot nativeexact dates. Productionduplicates andlocal preservationstillneedfreshread-onlybaselines.'))
