"""Extract narrative and alternate Greek links from captured object pages."""
import gzip,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-acropolis-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
rows=[]
for v in m.load(RUN/'native-details-001.json.gz')['rows']:
 h=BeautifulSoup(gzip.decompress((m.ROOT/v['receipt']['body_path']).read_bytes()),'html.parser');desc=h.select_one('#menu1');text=desc.get_text(' ',strip=True)if desc else'';gr=h.select_one('link[hreflang=el]')or h.select_one('link[hreflang=el-gr]')or h.select_one('a[hreflang=el]');grurl=urljoin(v['source_url'],gr['href'])if gr else None
 row=dict(number=v['number'],source_url=v['source_url'],inventory=v['fields']['Inventory number'],description=text,greek_url=grurl)
 if 'Translation from Greek text under progress'in text:
  assert grurl and '/en/'not in grurl
  b,rc=s.src.capture('native-greek-'+str(v['number'])+'-001',grurl);gh=BeautifulSoup(b,'html.parser');gd=gh.select_one('#menu1');row.update(greek_description=gd.get_text(' ',strip=True)if gd else'',greek_receipt=rc)
 rows.append(row)
 print(json.dumps(dict(number=v['number'],greek_fetched='greek_receipt'in row)),flush=True)
m.save(RUN/'native-narratives-001.json.gz',dict(at=m.now(),rows=rows,script_reference=s.s.ref(Path(__file__).resolve()),source_reference=s.s.ref(RUN/'native-details-001.json.gz')))
