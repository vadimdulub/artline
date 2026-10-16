"""Capture reciprocal native object histories for the early London leads."""
import json,collections
from concurrent.futures import ThreadPoolExecutor
import historical_exhibitions_fitzwilliam_london_early_discovery_20261012 as d
c=d.c;OUT=d.OUT/'objects'
def fetch(nid):
 path=OUT/(nid+'.json')
 if path.exists():return c.load(path)
 raw,rc=c.capture('https://data.fitzmuseum.cam.ac.uk/id/object/'+nid+'?format=json');data=json.loads(raw);assert data['admin']['id']=='object-'+nid
 row=dict(nativeID=nid,data=data,receipt=rc);c.save(path,row);return row
if __name__=='__main__':
 discovery=c.load(d.OUT/'discovery.json.gz');ids=sorted({o['nativeID']for e in discovery['records']for o in e['objects']})
 with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(fetch,ids))
 byid={r['nativeID']:r for r in rows};connections=[]
 for e in discovery['records']:
  for o in e['objects']:
   obj=byid[o['nativeID']]['data'];refs=[r for r in obj.get('exhibitions',[])if r['admin']['id']==e['lead']['nativeID']];assert len(refs)==1
   types=[x['reference']['summary_title']for x in obj['name']];eligible=len(types)==1 and types[0]in ['drawing','painting','print','miniature (painting)']
   connections.append(dict(exhibition=e['lead']['nativeID'],nativeID=o['nativeID'],title=o['title'],types=types,mediumCandidate=eligible,reference=refs[0]))
 result=dict(at=c.now(),objects=len(rows),reciprocalConnections=len(connections),mediumCandidates=sum(x['mediumCandidate']for x in connections),heldMediumConnections=[x for x in connections if not x['mediumCandidate']],connections=connections,newProductionEvents=0)
 c.save(d.OUT/'object-review.json.gz',result);print(json.dumps({k:v for k,v in result.items()if k!='connections'}))
