#!/usr/bin/env python3
"""Bounded five-show connected-object discovery; source evidence only."""
import re,json
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_discovery_20261012 as f
OUT=f.OUT/'rembrandt-five-shows'
SELECTED=['exhibition-1667','exhibition-1668','exhibition-1669','exhibition-1670','exhibition-1671']
def event(eid):
 base='https://data.fitzmuseum.cam.ac.uk/id/exhibition/'+eid
 records={};pages=[];number=1;expected=None
 while True:
  raw,rc=f.c.capture(base+(''if number==1 else '?page='+str(number)));s=f.BeautifulSoup(raw,'html.parser');t=s.get_text(' ',strip=True)
  m=re.search(r'Showing ([\d,]+) to ([\d,]+) of ([\d,]+) results',t);assert m,(eid,number)
  first,last,total=[int(x.replace(',',''))for x in m.groups()];assert expected in [None,total];expected=total
  for a in s.select('a[href]'):
   if '/id/object/'in a['href']and a.get_text(' ',strip=True):records[a['href']]=a.get_text(' ',strip=True)
  pages.append(dict(page=number,receipt=rc,first=first,last=last,total=total))
  if last==total:break
  number+=1;assert number<=20
 assert len(records)==expected,(eid,len(records),expected)
 result=dict(eventID=eid,pages=pages,objects=[dict(url=u,title=t)for u,t in records.items()]);f.c.save(OUT/(eid+'.json'),result);return result
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2)as pool:events=list(pool.map(event,SELECTED))
 ids=sorted({o['url'].rsplit('/',1)[-1]for e in events for o in e['objects']})
 with f.c.connect()as db:
  matches=f.n.normal(db.execute("SELECT x.*,a.title,a.work_type,a.accession_number,a.primary_media_id FROM external_identifiers x JOIN artworks a ON a.id=x.entity_id WHERE x.scheme='fitzwilliam-native-object' AND x.external_id=ANY(%s)",(ids,)).fetchall())
 f.c.save(OUT/'discovery.json',dict(at=f.c.now(),events=events,nativeIDs=ids,matches=matches))
 print(json.dumps(dict(events=[dict(id=e['eventID'],objects=len(e['objects']))for e in events],uniqueObjects=len(ids),existingMatches=len(matches))),flush=True)
