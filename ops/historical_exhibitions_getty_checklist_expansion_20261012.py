#!/usr/bin/env python3
"""Bounded discovery of additional objects explicitly listed at delivered Getty venues."""
import json,concurrent.futures
import exhibitions_common as c
from historical_exhibitions_getty_ra1953_discovery_20261012 import OUT
DEST=OUT/'checklist-expansion'
def fetch(ref):
 raw,rc=c.capture(ref['id']);d=json.loads(raw);c.save(DEST/'objects'/(ref['id'].rsplit('/',1)[-1]+'.json'),dict(receipt=rc,data=d));prod=d.get('produced_by',{});span=prod.get('timespan',{});types=[t.get('_label')for t in d.get('classified_as',[])];acc=next((x['content']for x in d.get('identified_by',[])if x.get('_label')=='Accession Number'),None)
 return dict(id=ref['id'],title=d.get('_label'),accession=acc,types=types,medium=[x['content']for x in d.get('referred_to_by',[])if x.get('_label')=='Materials Description'],creator=[x['content']for x in prod.get('referred_to_by',[])if x.get('_label')=='Artist/Maker (Producer) Name'],dateLabel=[x['content']for x in span.get('identified_by',[])],dateBounds=span,activities=[a['id']for s in d.get('member_of',[])for a in s.get('used_for',[])],source=rc)
def main():
 leads=c.load(OUT/'checklist-expansion-leads.json.gz');rows=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs={pool.submit(fetch,r):r for r in leads['objects']}
  for f in concurrent.futures.as_completed(jobs):
   try:rows.append(f.result())
   except Exception as e:errors.append(dict(id=jobs[f]['id'],error=repr(e)))
   if (len(rows)+len(errors))%10==0:print('Captured',len(rows),'objects; errors',len(errors),flush=True)
 connections=[]
 for e in leads['connections']:
  obj=next((r for r in rows if r['id']==e['objectID']),None);connections.append(e|dict(reciprocal=bool(obj and e['activityID']in obj['activities'])))
 result=dict(at=c.now(),objects=sorted(rows,key=lambda x:x['id']),connections=connections,errors=errors,counts=dict(objects=len(rows),connections=len(connections),reciprocal=sum(e['reciprocal']for e in connections)),reviewState='Medium, date, creator, image and production duplicate review pending; source references are not new delivered entries.')
 c.save(DEST/'discovery.json.gz',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-checklist-expansion-discovery.json',{k:v for k,v in result.items()if k not in ['objects','connections']});print(result['counts'])
if __name__=='__main__':main()
