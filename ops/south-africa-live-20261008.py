#!/usr/bin/env python3
"""Read-only production HTTP checks, bounded keyset pages; no database writes."""
import collections,concurrent.futures,gzip,json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]/'docs/research/south-africa-20261008'
PLAN=json.loads(gzip.decompress((ROOT/'publication-plan-final.json.gz').read_bytes()))
BASE='https://artlines.org/api/backend/v1'
def get(path,params=None):
 r=requests.get(BASE+path,params=params,timeout=(15,60));r.raise_for_status();return r.json()
def collection_check(group):
 slug=group[0]['institution_slug'];wanted={w['id']:w for w in group};seen=set();cursor=None;pages=0;total=None
 while True:
  params={'limit':60}
  if cursor:params['cursor']=cursor
  data=get('/museums/'+slug+'/works',params);pages+=1;total=data['total']
  assert pages<=10 and len(data['items'])<=60
  for item in data['items']:
   assert item['id'] not in seen;seen.add(item['id'])
   if item['id'] in wanted:assert item['title']==wanted[item['id']]['title'] and item['date_display']==wanted[item['id']]['date_display'] and item['display'] is None
  cursor=data.get('next_cursor')
  if not cursor:break
 assert len(seen)==total and set(wanted)<=seen,(slug,total,len(seen),set(wanted)-seen)
 sample=group[0];detail=get('/museums/'+slug+'/works/'+sample['id']);assert detail['id']==sample['id'] and detail['title']==sample['title'] and detail['status']=='published'
 assert detail['creation_year_end']<=1970 and any(c['source_url']==sample['source_url'] for c in detail['citations'])
 result=dict(museum=sample['institution_name'],slug=slug,new_records_visible=len(wanted),total_visible=total,pages=pages,detail_verified=sample['id']);print(result,flush=True);return result
if __name__=='__main__':
 groups=collections.defaultdict(list)
 for w in PLAN['artworks']:groups[w['institution_id']].append(w)
 directory=get('/museums',{'country':'ZA','limit':60});items={i['id']:i for i in directory['items']}
 assert set(groups)<=set(items)
 assert all(items[i]['country']=='ZA' and items[i]['work_count']>0 for i in groups)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(collection_check,groups.values()))
 assert sum(r['new_records_visible'] for r in results)==342
 out=dict(passed=True,new_records_visible=342,collections_verified=len(results),directory_total=directory['total'],results=results)
 path=ROOT/'live-api-verification.json';assert not path.exists();path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('All 342 published records visible through the live API')
