#!/usr/bin/env python3
"""Compare selected images with scoped, checksum-verified production references."""
import importlib.util,collections,io,concurrent.futures,sys
from pathlib import Path
from PIL import Image
sp=importlib.util.spec_from_file_location('d','ops/random-ten-twenty-batches-delivery-20261010.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
r=d.r;RUN=d.RUN

def references():
 ids=[x['artist']['id'] for x in d.m.cohort()]
 with r.connect('production') as db:
  refs=db.execute("SELECT a.id::text,aa.artist_id::text,a.title,ma.storage_path,ma.delivery_url,ma.checksum_sha256,ma.source_page_url FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN media_assets ma ON ma.id=a.primary_media_id WHERE aa.artist_id=ANY(%s::uuid[])",(ids,)).fetchall()
 def one(x):
  dest=RUN/'reference-hashes'/(x['id']+'.json')
  if dest.exists():return r.load(dest)
  try:
   path=d.ROOT/'apps/web/public'/(x.get('storage_path') or '').lstrip('/')
   if path.is_file():raw=path.read_bytes();via='local existing asset'
   else:
    url=x.get('delivery_url') or ('https://artlines.org'+x['storage_path']);resp=d.requests.get(url,timeout=(15,45));resp.raise_for_status();raw=resp.content;via='public existing catalogue asset'
   assert not x.get('checksum_sha256') or r.sha(raw)==x['checksum_sha256'],'Reference bytes differ from database checksum'
   with Image.open(io.BytesIO(raw)) as image:
    gray=image.convert('L').resize((17,16));pixels=list(gray.getdata());bits=''.join('1' if pixels[y*17+k]>pixels[y*17+k+1] else '0' for y in range(16) for k in range(16))
   x.update(dhash=hex(int(bits,2))[2:].zfill(64),actual_sha256=r.sha(raw),outcome='verified',via=via)
  except Exception as exc:x.update(outcome='unavailable',error=str(exc)[:400])
  r.save(dest,x);return x
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,x in enumerate(pool.map(one,refs),1):
   results.append(x)
   if n%250==0:print('Existing picture references',n,'/',len(refs),flush=True)
 r.save_gz(RUN/'existing-image-reference-hashes.json.gz',results);print('Existing image reference outcomes',dict(collections.Counter(x['outcome'] for x in results)),flush=True)

def audit():
 ready=[r.load(p) for p in (RUN/'prepared-images').glob('*.json') if r.load(p)['outcome']=='prepared'];refs=r.load(RUN/'existing-image-reference-hashes.json.gz');old_by_artist=collections.defaultdict(list);old_by_sha=collections.defaultdict(list);new_by_artist=collections.defaultdict(list);held={};groups=[]
 for x in refs:
  old_by_artist[x['artist_id']].append(x)
  for digest in {x.get('actual_sha256'),x.get('checksum_sha256')}-{None}:old_by_sha[digest].append(x)
 for im in ready:
  new_by_artist[im['artist_id']].append(im)
  comparators={old['id']:old for old in old_by_artist[im['artist_id']]}
  for digest in {im['sha256'],im['download']['sha256']}:
   comparators.update({old['id']:old for old in old_by_sha[digest]})
  for old in comparators.values():
   if im['artwork_id']==old['id']:continue
   distance=(int(im['dhash'],16)^int(old['dhash'],16)).bit_count() if old.get('dhash') else None
   exact=bool({im['sha256'],im['download']['sha256']}&({old.get('actual_sha256'),old.get('checksum_sha256')}-{None}))
   if exact or (im['artist_id']==old['artist_id'] and distance is not None and distance<=8):
    groups.append(dict(candidate=im['artwork_id'],artist=im['artist'],title=im['title'],source_url=im['source_page_url'],existing_id=old['id'],existing_title=old['title'],existing_source=old.get('source_page_url'),distance=distance,exact=exact));held[im['artwork_id']]='Selected reproduction may duplicate an existing artwork under another title; preserve current record and investigate exact object/version identity.'
 for values in new_by_artist.values():
  for i,im in enumerate(values):
   for other in values[i+1:]:
    distance=(int(im['dhash'],16)^int(other['dhash'],16)).bit_count()
    if im['download']['sha256']==other['download']['sha256'] or distance<=5:
     groups.append(dict(candidate=im['artwork_id'],artist=im['artist'],title=im['title'],other_candidate=other['artwork_id'],other_title=other['title'],distance=distance))
     for x in [im,other]:held[x['artwork_id']]='Same or nearly identical selected reproduction under different source identities; version remains unresolved.'
 r.save(RUN/'additional-image-reference-audit.json',dict(at=r.now(),prepared_references=len(ready),existing_references=len(refs),unavailable_references=[x for x in refs if x['outcome']!='verified'],groups=groups,held_artwork_ids=held))
 print('Existing-image duplicate audit',len(ready),'selected;',len(refs),'existing;',len(held),'held',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
