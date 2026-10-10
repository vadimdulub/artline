"""Bounded public Kilkis collection discovery while cloud auth needs restoration."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-source-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;RUN=m.RUN/'native/kilkis-20261010';q.RUN=RUN;q.CAP=RUN/'captures';q.CAP.mkdir(parents=True,exist_ok=True)
urls=[('museum-collection-001','https://www.efa-kilkis.gr/artworks/'),('searchculture-collection-001','https://www.searchculture.gr/aggregator/portal/collections/Efa_Kilkis_col?language=en'),('museum-profile-001','https://www.efa-kilkis.gr/pois/archaiologiko-mouseio-kilkis/')]
rows=[]
for key,url in urls:
 soup,rc=q.capture(key,url);links=[dict(title=a.get_text(' ',strip=True),url=urljoin(url,a['href']))for a in soup.select('a[href]')];rows.append(dict(key=key,receipt=rc,text=soup.get_text(' ',strip=True),links=links));print(json.dumps(dict(key=key,status=rc['status'],bytes=rc['bytes'],object_links=[v for v in links if '/artworks/'in v['url']or '/aggregator/edm/'in v['url']]),ensure_ascii=False),flush=True)
m.save(RUN/'source-discovery-001.json.gz',dict(at=m.now(),rows=rows,script_reference=q.s.ref(Path(__file__).resolve()),institution_id='4f3ac99d-d622-591d-8885-ac14362fbb50',production_count_note='Last observation18catalogue/0eligible at2026-10-09T12:21:32Z/12:23:56Z; no fresh cloud access. No new production snapshot or write.',policy='Three official/public collection pages only. Bounded object selection to follow. Collection ownership separate from current display. SearchCulture enriched periods/geographic labels must not override native object metadata. No images downloaded.'))
