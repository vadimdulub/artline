"""Bounded official Acropolis sculpture metadata discovery; no image downloads."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-acropolis-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;SITE='https://www.theacropolismuseum.gr'
def main():
 rows=[];receipts=[]
 for page in[0,1]:
  url=SITE+'/en/explore-collections?field_exhibit_category_value=Sculpture&items_per_page=90&page='+str(page)
  raw,rc=s.src.capture('sculpture-index-'+str(page)+'-001',url);h=BeautifulSoup(raw,'html.parser');main=h.find('main')or h;full=main.get_text(' ',strip=True);total=int(re.search(r'Found:\s*(\d+)\s*results',full).group(1));batch=[]
  for a in main.select('a[href]'):
   text=a.get_text(' ',strip=True)
   if text.startswith('Title ')and' Category Sculpture Date 'in text:batch.append(dict(url=urljoin(SITE,a['href']),index_text=text))
  assert len(batch)==90;rows+=batch;receipts.append(rc);print(json.dumps(dict(page=page,rows=len(batch),total=total)),flush=True)
 unique={v['url']:v for v in rows};assert len(unique)==179;duplicates=[u for u in unique if sum(v['url']==u for v in rows)>1];rows=list(unique.values());m.save(RUN/'native-discovery-001.json.gz',dict(at=m.now(),rows=rows,receipts=receipts,duplicate_page_boundary_urls=duplicates,raw_rows=180,reported_sculpture_count=total,next_page=2,policy='First two90-row pages,179unique official sculpture metadata entries; duplicate page-boundary URL retained in audit; selected objects need individual source,original/cast,parent/component and duplicate checks. No exhaustive artwork or image download.'))
if __name__=='__main__':main()
