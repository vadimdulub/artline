#!/usr/bin/env python3
"""Capture metadata for the 105 selected exhibition objects; no image downloads."""
import json
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_rembrandt_discovery_20261012 as r
f=r.f
if __name__=='__main__':
 discovery=f.c.load(r.OUT/'discovery.json')
 def fetch(nid):
  raw,rc=f.c.capture('https://data.fitzmuseum.cam.ac.uk/id/object/'+nid+'?format=json');d=json.loads(raw);assert d['admin']['id']=='object-'+nid
  row=dict(nativeID=nid,data=d,receipt=rc);f.c.save(r.OUT/'objects'/(nid+'.json'),row);return row
 with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(fetch,discovery['nativeIDs']))
 counts={};connections=[];held=[]
 for row in rows:
  d=row['data'];types=[x['reference']['summary_title']for x in d.get('name',[])if 'reference'in x];counts[str(types)]=counts.get(str(types),0)+1
  for e in discovery['events']:
   if not any(x['url'].endswith('/'+row['nativeID'])for x in e['objects']):continue
   refs=[x for x in d.get('exhibitions',[])if x['admin']['id']==e['eventID']]
   if len(refs)!=1:held.append(dict(nativeID=row['nativeID'],eventID=e['eventID'],reason='Missing or ambiguous reciprocal exhibition reference'));continue
   connections.append(dict(nativeID=row['nativeID'],eventID=e['eventID'],title=d.get('title'),types=types,catalogue=refs[0].get('@link',{}).get('catalogue'),creation=d.get('lifecycle',{}).get('creation'),accessions=d.get('identifier')))
 result=dict(at=f.c.now(),objectCount=len(rows),typeCounts=counts,connections=connections,held=held,newProductionRecords=0,reviewState='Metadata captured; editorial type/date/attribution review and original-impression image matching remain required.')
 f.c.save(r.OUT/'object-review-discovery.json.gz',result)
 print(json.dumps(dict(objects=len(rows),typeCounts=counts,connections=len(connections),held=len(held))),flush=True)
