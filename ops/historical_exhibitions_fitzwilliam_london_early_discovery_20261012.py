"""Public object-level evidence for pre-1930 London exhibition references."""
import json
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_cambridge_drawings_20261012 as r
m=r.m;c=r.c
OUT=m.f.OUT/'london-early-discovery';r.OUT=OUT
EXCLUDE={'exhibition-975','exhibition-985','exhibition-1110','exhibition-1117','exhibition-1139','exhibition-1615','exhibition-94','exhibition-1327'}
def main():
 leads=[x for x in c.load(m.f.OUT/'medium-title-review.json.gz')['records']if x['state']=='historical_date_candidate' and x['venues']==['London']and max(int(d[:4])for d in x['dates'])<=1929 and x['nativeID']not in EXCLUDE]
 def fetch(lead):
  path=OUT/(lead['nativeID']+'.json')
  return c.load(path)if path.exists()else r.fetch(lead)
 with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(fetch,leads))
 overlaps=[]
 for i,a in enumerate(rows):
  for b in rows[i+1:]:
   if a['lead']['dates'][0][:4]!=b['lead']['dates'][0][:4]:continue
   shared={x['nativeID']for x in a['objects']}&{x['nativeID']for x in b['objects']}
   if shared:overlaps.append(dict(a=a['lead']['nativeID'],b=b['lead']['nativeID'],shared=sorted(shared)))
 result=dict(at=c.now(),records=rows,referenceCount=len(rows),objectConnections=sum(len(x['objects'])for x in rows),uniqueObjects=len({o['nativeID']for x in rows for o in x['objects']}),sameYearObjectOverlaps=overlaps,newProductionEvents=0,basis='Source references are leads, not deduplicated events. Check medium, object dates, reciprocal object histories, source catalogue evidence and production duplicates before release.')
 c.save(OUT/'discovery.json.gz',result);print(json.dumps({k:v for k,v in result.items()if k!='records'}))
if __name__=='__main__':main()
