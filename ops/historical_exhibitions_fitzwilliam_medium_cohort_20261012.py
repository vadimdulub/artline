#!/usr/bin/env python3
"""Bounded public metadata discovery for named pictorial-medium exhibition leads."""
import json,re,collections
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_discovery_20261012 as f
OUT=f.OUT/'medium-title-details'
def fetch(lead):
 key=lead['url'].rsplit('/',1)[-1];path=OUT/(key+'.json')
 if path.exists():return f.c.load(path)
 raw,rc=f.c.capture(lead['url']+'?format=json');data=json.loads(raw);assert data['admin']['id']==key
 row=dict(lead=lead,data=data,receipt=rc);f.c.save(path,row);return row

def classify(row):
 data=row['data'];values=[];conflicts=[]
 def walk(x):
  if not isinstance(x,dict):return
  val=x.get('value')
  if isinstance(val,str):
   if re.fullmatch(r'\d{4}(?:-\d{2}){0,2}',val):
    year=int(val[:4]);values.append(val)
    if any(x.get(k)not in [None,year]for k in ['earliest','latest']):conflicts.append(x)
   else:conflicts.append(x)
  for k in ['from','to']:walk(x.get(k))
 for venue in data.get('venues',[]):
  for date in venue.get('@link',{}).get('date',[]):walk(date)
 years=[int(x[:4])for x in values]
 state='date_unresolved'if not years else 'outside_date_scope'if min(years)<1600 or max(years)>1989 else 'historical_date_candidate'
 return dict(nativeID=data['admin']['id'],title=data['summary_title'],dates=values,venues=[v['summary_title']for v in data.get('venues',[])],state=state,dateFieldConflicts=conflicts,detailPath=str(OUT/(data['admin']['id']+'.json')))
if __name__=='__main__':
 leads=f.c.load(f.OUT/'medium-title-cohort.json')['leads'];rows=[]
 with ThreadPoolExecutor(max_workers=2)as pool:
  for ix,row in enumerate(pool.map(fetch,leads),1):
   rows.append(classify(row))
   if ix%25==0:print('Captured',ix,'/',len(leads),flush=True)
 counts=dict(collections.Counter(r['state']for r in rows));result=dict(at=f.c.now(),records=rows,counts=counts,dateFieldConflictRecords=sum(bool(r['dateFieldConflicts'])for r in rows),newProductionRecords=0,basis='Source date strings only; titles are not exhibition dates. Candidates require venue, medium, object and duplicate review. Missing endpoints/tour stops and malformed fields remain unresolved.')
 f.c.save(f.OUT/'medium-title-review.json.gz',result);print(json.dumps(dict(counts=counts,dateFieldConflictRecords=result['dateFieldConflictRecords'])),flush=True)
