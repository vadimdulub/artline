#!/usr/bin/env python3
"""Classify native venue histories for the selected Getty catalogue cohort."""
import json,concurrent.futures
import exhibitions_common as c
from historical_exhibitions_getty_catalogue_next_20261012 import OUT

def main():
 p=c.load(OUT/'discovery.json.gz');objects=p['objects']+c.load(OUT/'corrected-accessions.json')['objects'];refs={a['id']for o in objects for a in o['activities']};rows=[];errors=[]
 def fetch(url):
  raw,rc=c.capture(url);d=json.loads(raw);c.save(OUT/'activities'/(url.rsplit('/',1)[-1]+'.json'),dict(receipt=rc,data=d));t=d.get('timespan',{});first=t.get('begin_of_the_begin','')[:4];last=t.get('end_of_the_end','')[:4];scope='unknown'
  if first.isdigit()and last.isdigit():scope='historical'if 1600<=int(first)<=int(last)<=1989 else'outside'
  members={x['id']for group in d.get('used_specific_object',[])for x in group.get('member',[])};connections=[dict(objectID=o['id'],accession=o['accession'],reciprocal=o['id']in members)for o in objects if url in {x['id']for x in o['activities']}];return dict(id=url,title=d.get('_label'),scope=scope,timespan=t,connections=connections,parentExhibitions=d.get('motivated_by',[]),venues=d.get('took_place_at',[]),source=rc)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs={pool.submit(fetch,u):u for u in refs}
  for f in concurrent.futures.as_completed(jobs):
   try:rows.append(f.result())
   except Exception as e:errors.append(dict(url=jobs[f],error=repr(e)))
   if (len(rows)+len(errors))%20==0:print('Classified',len(rows),'errors',len(errors),flush=True)
 hist=[r for r in rows if r['scope']=='historical'];result=dict(at=c.now(),activities=rows,errors=errors,counts=dict(objects=len(objects),uniqueActivities=len(refs),historicalVenues=len(hist),historicalObjectVenueConnections=sum(len(r['connections'])for r in hist),historicalParentExhibitions=len({e['id']for r in hist for e in r['parentExhibitions']}),nonreciprocal=sum(not x['reciprocal']for r in hist for x in r['connections']),outsideVenues=sum(r['scope']=='outside'for r in rows),unknownVenues=sum(r['scope']=='unknown'for r in rows)),productionChanges=0)
 c.save(OUT/'activity-scope-expanded.json.gz',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-catalogue-next-scope-expanded.json',dict(at=result['at'],counts=result['counts'],errors=errors,productionChanges=0));print(result['counts'])
if __name__=='__main__':main()
