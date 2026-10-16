#!/usr/bin/env python3
"""Group source venue records by explicit exhibition identity and audit production candidates."""
import json,difflib,concurrent.futures
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_ra1953_discovery_20261012 import OUT

def fetch(url):
 raw,rc=c.capture(url);d=json.loads(raw);c.save(OUT/'exhibitions'/(url.rsplit('/',1)[-1]+'.json'),dict(receipt=rc,data=d));return url,dict(receipt=rc,data=d)
def main():
 scope=c.load(OUT/'activity-scope-review.json.gz');groups={}
 for x in scope['activities']:
  if x['scope']!='historical':continue
  src=c.load(OUT/'activities'/(x['id'].rsplit('/',1)[-1]+'.json'));parents=src['data']['motivated_by'];assert len(parents)==1
  e=parents[0];groups.setdefault(e['id'],dict(title=e['_label'],activities=[]))['activities'].append(src)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:parents=dict(pool.map(fetch,groups))
 years=sorted({int(a['data']['timespan'][field][:4])for g in groups.values()for a in g['activities']for field in ['begin_of_the_begin','end_of_the_end']})
 with c.connect()as db:
  existing=n.normal(db.execute("SELECT e.id,e.title,e.start_year,e.end_year,e.date_display,(SELECT jsonb_agg(jsonb_build_object('id',o.id,'venue',o.venue_label,'city',o.city_label,'start',o.start_date,'end',o.end_date)) FROM exhibition_occurrences o WHERE o.exhibition_id=e.id) venues FROM exhibitions e WHERE e.status<>'archived'AND e.start_year<=%s AND COALESCE(e.end_year,e.start_year)>=%s",(max(years),min(years))).fetchall())
 results=[]
 for url,g in groups.items():
  first=min(int(a['data']['timespan']['begin_of_the_begin'][:4])for a in g['activities']);last=max(int(a['data']['timespan']['end_of_the_end'][:4])for a in g['activities']);title=c.norm(g['title']);candidates=[]
  for e in existing:
   if e['start_year']>last or(e['end_year']or e['start_year'])<first:continue
   other=c.norm(e['title']);score=difflib.SequenceMatcher(None,title,other).ratio()
   if score>=.43:candidates.append(e|dict(titleSimilarity=round(score,3)))
  candidates.sort(key=lambda e:-e['titleSimilarity'])
  results.append(dict(sourceID=url,title=g['title'],firstYear=first,lastYear=last,activities=g['activities'],parent=parents[url],candidateMatches=candidates[:5],sourceVenueCount=len(g['activities']),additionalSourceVenues=[a for a in parents[url]['data'].get('motivated',[])if a['id']not in {x['data']['id']for x in g['activities']}],state='needs-editorial-reconciliation'))
 result=dict(at=c.now(),groups=results,sourceActivities=51,sourceExhibitions=len(groups),existingRowsCompared=len(existing),limitations=['Similarity ranks candidates only; no automatic identity merge.','Tour bounds are not venue-specific dates.','Uncaptured additional source venues need date checks before event creation.'])
 c.save(OUT/'event-reconciliation.json.gz',result)
 for e in results:print(e['sourceID'].rsplit('/',1)[-1],e['firstYear'],e['title'],'VENUES',e['sourceVenueCount'],'EXTRA',len(e['additionalSourceVenues']),'MATCHES',[(x['id'],x['title'],x['titleSimilarity'])for x in e['candidateMatches'][:2]])
 print('Grouped',len(groups),'source exhibitions')
if __name__=='__main__':main()
