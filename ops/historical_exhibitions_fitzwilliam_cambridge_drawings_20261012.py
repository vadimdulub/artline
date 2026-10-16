#!/usr/bin/env python3
"""Bounded Cambridge drawing-exhibition object and duplicate discovery; no DB writes."""
import re,json
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_medium_cohort_20261012 as m
c=m.f.c;n=m.f.n
OUT=m.f.OUT/'cambridge-drawings-review'
def fetch(lead):
 key=lead['nativeID'];base='https://data.fitzmuseum.cam.ac.uk/id/exhibition/'+key;objects={};pages=[];page=1;expected=None
 while True:
  raw,rc=c.capture(base+(''if page==1 else '?page='+str(page)));s=m.f.BeautifulSoup(raw,'html.parser');text=s.get_text(' ',strip=True);paging=re.search(r'Showing ([\d,]+) to ([\d,]+) of ([\d,]+) results',text)
  if paging:
   first,last,total=[int(x.replace(',',''))for x in paging.groups()];assert expected in [None,total];expected=total
  else:
   assert page==1 and not s.select('a[rel="next"]');last=total=None
  for a in s.select('a[href]'):
   if '/id/object/'in a['href']and a.get_text(' ',strip=True):objects[a['href']]=a.get_text(' ',strip=True)
  pages.append(dict(page=page,receipt=rc))
  if not paging or last==total:break
  page+=1;assert page<=50
 if expected is not None:assert len(objects)==expected
 result=dict(lead=lead,pages=pages,objects=[dict(url=u,title=t,nativeID=u.rsplit('/',1)[-1])for u,t in objects.items()]);c.save(OUT/(key+'.json'),result);print(key,len(objects),flush=True);return result
if __name__=='__main__':
 leads=[r for r in c.load(m.f.OUT/'cambridge-drawings-cohort.json')['records']if r['nativeID']not in ['exhibition-1668','exhibition-1670','exhibition-1093']]
 with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(fetch,leads))
 overlaps=[]
 for i,a in enumerate(rows):
  for b in rows[i+1:]:
   aset={x['nativeID']for x in a['objects']};bset={x['nativeID']for x in b['objects']};shared=aset&bset
   if shared and a['lead']['dates'][0][:4]==b['lead']['dates'][0][:4]:overlaps.append(dict(a=a['lead']['nativeID'],b=b['lead']['nativeID'],shared=sorted(shared),aCount=len(aset),bCount=len(bset)))
 result=dict(at=c.now(),exhibitionReferences=len(rows),objectConnections=sum(len(x['objects'])for x in rows),uniqueObjects=len({o['nativeID']for x in rows for o in x['objects']}),records=rows,sameYearObjectOverlaps=overlaps,excludedExisting=['exhibition-1668','exhibition-1670'],heldMixedMedia=['exhibition-1093'],newProductionEvents=0)
 c.save(OUT/'discovery.json.gz',result);print(json.dumps({k:v for k,v in result.items()if k!='records'}),flush=True)
