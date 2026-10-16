#!/usr/bin/env python3
"""Selected Cambridge exhibition object metadata review, no images or DB writes."""
import json,collections
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_cambridge_drawings_20261012 as r
c=r.c;OUT=r.OUT/'objects'
def fetch(nid):
 path=OUT/(nid+'.json')
 if path.exists():return c.load(path)
 raw,rc=c.capture('https://data.fitzmuseum.cam.ac.uk/id/object/'+nid+'?format=json');d=json.loads(raw);assert d['admin']['id']=='object-'+nid
 row=dict(nativeID=nid,data=d,receipt=rc);c.save(path,row);return row
if __name__=='__main__':
 discovery=c.load(r.OUT/'discovery.json.gz');expected=collections.defaultdict(set)
 for e in discovery['records']:
  for o in e['objects']:expected[o['nativeID']].add(e['lead']['nativeID'])
 rows=[]
 with ThreadPoolExecutor(max_workers=2)as pool:
  for i,row in enumerate(pool.map(fetch,sorted(expected)),1):
   rows.append(row)
   if i%50==0:print('Captured objects',i,'/',len(expected),flush=True)
 kinds=collections.Counter();missing=[];reviews=[]
 for row in rows:
  d=row['data'];nid=row['nativeID'];types=[x.get('reference',{}).get('summary_title',x.get('value','unknown'))for x in d.get('name',[])];kinds[str(types)]+=1
  refs={x['admin']['id']:x for x in d.get('exhibitions',[])}
  for eid in expected[nid]:
   if eid not in refs:missing.append(dict(nativeID=nid,eventID=eid))
  reviews.append(dict(nativeID=nid,title=d.get('title'),types=types,creation=d.get('lifecycle',{}).get('creation'),acquisition=d.get('lifecycle',{}).get('acquisition'),exhibitionReferences=[refs[e]for e in sorted(expected[nid])if e in refs]))
 result=dict(at=c.now(),objects=len(rows),typeCounts=dict(kinds),expectedConnections=sum(len(v)for v in expected.values()),missingReciprocalReferences=missing,records=reviews,newProductionEvents=0,newArtworks=0,newImages=0,reviewState='Discovery only. Per-object medium/date/attribution, duplicate events and canonical identity review required.')
 c.save(r.OUT/'object-review.json.gz',result);print(json.dumps({k:v for k,v in result.items()if k!='records'}),flush=True)
