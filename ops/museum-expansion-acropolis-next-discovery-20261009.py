"""One further sculpture index page for the remaining gap; no object/image fetches."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-acropolis-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;SITE='https://www.theacropolismuseum.gr'
url=SITE+'/en/explore-collections?field_exhibit_category_value=Sculpture&items_per_page=90&page=2';raw,rc=s.src.capture('sculpture-next-index-2-001',url);h=BeautifulSoup(raw,'html.parser');main=h.find('main')or h;full=main.get_text(' ',strip=True);total=int(re.search(r'Found:\s*(\d+)\s*results',full).group(1));rows=[]
for a in main.select('a[href]'):
 text=a.get_text(' ',strip=True)
 if text.startswith('Title ')and' Category Sculpture Date 'in text:rows.append(dict(url=urljoin(SITE,a['href']),index_text=text))
assert 0<len(rows)<=90;prior=m.load(RUN/'native-discovery-001.json.gz');seen={v['url']for v in prior['rows']};fresh=[];duplicates=[]
for row in rows:
 if row['url']in seen:duplicates.append(row)
 else:fresh.append(row);seen.add(row['url'])
m.save(RUN/'next-source-discovery-001.json.gz',dict(at=m.now(),receipt=rc,rows=fresh,raw_rows=len(rows),duplicates=duplicates,reported_sculpture_count=total,combined_unique=len(seen),reported_minus_discovered=total-len(seen),previous_discovery_reference=s.s.ref(RUN/'native-discovery-001.json.gz'),script_reference=s.s.ref(Path(__file__).resolve()),policy='Discovery metadata only. New object detail/source,physical version,fragment-parent and identity reviews required before any additional records. No images.'))
print(json.dumps(dict(new=len(fresh),raw=len(rows),duplicates=len(duplicates),combined_unique=len(seen),reported=total)),flush=True)
