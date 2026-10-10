import importlib.util,requests,hashlib,concurrent.futures,json,time
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.base.load(m.RUN/'gap-production-plan-v3.json.gz');samples=rows[::20]
def verify(r):
 p=r['prepared'];response=requests.get('https://artlines.org'+p['path'],timeout=45);response.raise_for_status();assert hashlib.sha256(response.content).hexdigest()==p['sha256']
 a=requests.get('https://artlines.org/api/backend/v1/artists/'+r['artist_slug'],timeout=45);a.raise_for_status();data=a.json();assert data.get('key_artwork') and data['key_artwork'].get('media_url');w=data['key_artwork'];detail=requests.get('https://artlines.org/api/backend/v1/artists/'+r['artist_slug']+'/works/'+w['id'],timeout=45);detail.raise_for_status();assert detail.json()['id']==w['id']
 return dict(artist=r['artist_slug'],key_artwork=w['title'],image_verified=p['path'],status=200)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(verify,samples))
m.save('live-gap-verification-v2.json',dict(passed=True,samples=results));print('New live image checksums and painter key responses verified',len(results))
