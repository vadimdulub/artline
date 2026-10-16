#!/usr/bin/env python3
"""Date-scope Getty activities from eleven selected drawing histories, metadata only."""
import json,concurrent.futures
import exhibitions_common as c
from historical_exhibitions_getty_ra1953_discovery_20261012 import OUT

def fetch(url):
 raw,rc=c.capture(url);d=json.loads(raw);c.save(OUT/'activities'/(url.rsplit('/',1)[-1]+'.json'),dict(receipt=rc,data=d))
 span=d.get('timespan',{});start=span.get('begin_of_the_begin','');end=span.get('end_of_the_end','');label='; '.join(x.get('content','')for x in span.get('identified_by',[]))
 scope='unresolved'
 if start and end:
  first=int(start[:4]);last=int(end[:4]);scope='historical'if first>=1600 and last<=1989 else 'outside'if first>=1990 or last<1600 else 'crosses-boundary'
 return dict(id=url,title=d.get('_label'),dateLabel=label,dateBounds=span,scope=scope,source=rc)
def main():
 discovery=c.load(OUT/'discovery.json.gz');urls=sorted({x['id']for o in discovery['objects']for x in o['otherExhibitions']});rows=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs={pool.submit(fetch,u):u for u in urls}
  for job in concurrent.futures.as_completed(jobs):
   try:rows.append(job.result())
   except Exception as e:errors.append(dict(url=jobs[job],error=str(e)))
   if (len(rows)+len(errors))%20==0:print('Reviewed',len(rows),'activities; errors',len(errors),flush=True)
 counts={s:sum(x['scope']==s for x in rows)for s in ['historical','outside','unresolved','crosses-boundary']}
 result=dict(at=c.now(),counts=counts,activities=sorted(rows,key=lambda x:x['id']),errors=errors,sourceObjectCount=11,distinctActivityCount=len(urls),limitations=['Activity/venue records are not automatically unique exhibitions.','Numeric year bounds are not exact dates when the display gives only a year.','Historical candidates need event duplicate reconciliation and medium review before ingestion.'])
 c.save(OUT/'activity-scope-review.json.gz',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-activity-scope-review.json',{k:v for k,v in result.items()if k!='activities'});print(json.dumps({k:v for k,v in result.items()if k!='activities'}))
if __name__=='__main__':main()
