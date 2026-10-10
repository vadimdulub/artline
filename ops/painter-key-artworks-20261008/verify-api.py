import json,requests,time
from pathlib import Path
out=Path.home()/'Library/Application Support/Artline/backups/key-artworks-20261008';url='https://key-artworks-20261008---artline-api-lpuqqlugnq-ew.a.run.app'
check=json.loads((out/'api-check.json').read_text());url=next(t['uri'] for t in check['trafficStatuses'] if t.get('tag')=='key-artworks-20261008');results=[]
for slug in ['leonardo-da-vinci','claude-monet','pablo-picasso-q5593','vincent-van-gogh-q5582','wikimedia-painter-q21453785']:
 start=time.monotonic();r=requests.get(url+'/api/v1/artists/'+slug,params={'preview':'1'},timeout=45);r.raise_for_status();data=r.json();w=data.get('key_artwork');results.append(dict(slug=slug,artwork=w and w['title'],work_id=w and w['id'],media=w and w['media_url'],milliseconds=round((time.monotonic()-start)*1000)));assert 'key_artwork' in data
 if slug=='leonardo-da-vinci':assert w and w['title']=='Mona Lisa'
 if slug=='wikimedia-painter-q21453785':assert w is None
 if w:
  detail=requests.get(url+'/api/v1/artists/'+slug+'/works/'+w['id'],params={'preview':'1'},timeout=30);detail.raise_for_status();assert detail.json()['id']==w['id']
  public=requests.get(url+'/api/v1/artists/'+slug,params={'preview':'0'},timeout=30)
  if public.ok and w['status']!='published':assert public.json().get('key_artwork') is None
(out/'api-candidate-verification.json').write_text(json.dumps(dict(passed=True,results=results,source='live candidate and existing production database; no fixtures'),indent=2));print(json.dumps(results))
