#!/usr/bin/env python3
"""Capture bounded painting metadata for the 40 largest unresolved creator groups."""
import collections,concurrent.futures,datetime,hashlib,json,pathlib,time,urllib.request,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parent.parent;SRC=ROOT/'content/imports/expanded-round7-20260913';SRC.mkdir(parents=True,exist_ok=True)
def fetch(url,name):
 path=SRC/name;receipt=path.with_name(path.name+'.snapshot.json')
 if path.exists() and receipt.exists():
  raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==json.loads(receipt.read_text())['sha256'];return json.loads(raw)
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=35) as response:raw=response.read(3_000_001)
   assert len(raw)<=3_000_000;data=json.loads(raw);break
  except Exception:
   if attempt==2:raise
   time.sleep(2*(attempt+1))
 path.write_bytes(raw);receipt.write_text(json.dumps({'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_path':str(path.relative_to(ROOT))},indent=2));return data

def search(pair):
 name,count=pair;url='https://data.rijksmuseum.nl/search/collection?'+urllib.parse.urlencode({'creator':name,'type':'painting'});ids=[]
 for page in range(1,6):
  data=fetch(url,'search-'+hashlib.sha256(name.encode()).hexdigest()[:16]+f'-{page}.json');ids.extend(x['id'] for x in data.get('orderedItems',[]));url=data.get('next',{}).get('id')
  if not url:break
 return {'creator':name,'pending':count,'ids':ids,'has_more':bool(url)}
def main():
 rows=json.loads((ROOT/'docs/research/expanded-round6-20260913/unlinked.json').read_text());names=collections.Counter(r['cells'][0] for r in rows if r['source'] is None and r['cells'][3]=='Rijksmuseum').most_common(40)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:selection=list(ex.map(search,names))
 (SRC/'selection.json').write_text(json.dumps(selection,indent=2));ids=sorted({id for s in selection for id in s['ids']});print('Selected creator groups',len(selection),'object identifiers',len(ids),flush=True)
 def obj(uri):return fetch('https://data.rijksmuseum.nl/'+uri.rsplit('/',1)[1]+'?_profile=la-framed','object-'+uri.rsplit('/',1)[1]+'.json')
 people=set()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for i,o in enumerate(ex.map(obj,ids),1):
   for part in o.get('produced_by',{}).get('part',[]):
    for a in part.get('carried_out_by',[]):
     if a.get('type')=='Person' and a.get('id','').startswith('https://id.rijksmuseum.nl/'):people.add(a['id'])
   if i%100==0:print('Rijks object metadata',i,'of',len(ids),flush=True)
 def person(uri):return fetch('https://data.rijksmuseum.nl/'+uri.rsplit('/',1)[1]+'?_profile=la-framed','person-'+uri.rsplit('/',1)[1]+'.json')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for i,_ in enumerate(ex.map(person,sorted(people)),1):
   if i%100==0:print('Rijks creator authorities',i,'of',len(people),flush=True)
 print('Rijks capture complete',len(ids),'objects',len(people),'creator authorities',flush=True)
if __name__=='__main__':main()
