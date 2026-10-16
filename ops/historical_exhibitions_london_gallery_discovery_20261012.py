"""Selected scholarly gallery records and cited exhibition leads; no DB writes."""
import sys,json
from bs4 import BeautifulSoup
import exhibitions_common as c
OUT=c.RUN/'london-gallery-project'
NAMES={"Agnew's Gallery",'Agnew and Sons','Carfax Gallery','Goupil Gallery','The Fine Art Society','Leicester Gallery','Dutch Gallery','Chenil Gallery'}
rows=[]
for lead in c.load(OUT/'index.json')['records']:
 if lead['name']not in NAMES:continue
 key=lead['url'].rsplit('/',1)[-1].replace('.html','');path=OUT/(key+'.json')
 if path.exists():row=c.load(path)
 else:
  raw,rc=c.capture(lead['url']);s=BeautifulSoup(raw,'html.parser');text=s.get_text('\n',strip=True);start=text.lower().find('selected exhibitions');section=None
  if start>=0:
   tail=text[start:];ends=[tail.find(x)for x in ['For more exhibitions','\nSources','\nBowdoin College']if tail.find(x)>0];section=tail[:min(ends)]if ends else tail
  row=dict(lead=lead,receipt=rc,selectedExhibitionsText=section,sourceText=text);c.save(path,row)
 rows.append(row);print(key,lead['name'],bool(row['selectedExhibitionsText']),flush=True)
result=dict(at=c.now(),indexLocationRecords=114,selectedLocationRecords=len(rows),recordsWithSelectedExhibitions=sum(bool(x['selectedExhibitionsText'])for x in rows),records=rows,newProductionEvents=0,basis='Location records and lists are research leads, not counts of distinct galleries or new events. Reconcile repeated location lists, original catalogues, event dates, artwork types and existing production records.',accessHolds=[dict(url='https://www.exhibitionculture.arts.gla.ac.uk/search.php',status=403,decision='No retry or alternate endpoint access in this pass')])
c.save(OUT/'selected-discovery.json.gz',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/london-gallery-discovery.json',{k:v for k,v in result.items()if k!='records'});print(json.dumps({k:v for k,v in result.items()if k!='records'}))
