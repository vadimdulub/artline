#!/usr/bin/env python3
"""Private metadata-only Commons candidate discovery for ART500K references."""
import argparse, html, json, re, sqlite3, time, io, tarfile, os
from pathlib import Path
import requests
from PIL import Image, ImageOps, UnidentifiedImageError
APPROVED={'Public Domain Mark','CC0','CC BY','CC BY-SA'}
def clean(s): return re.sub(r'\s+',' ',re.sub(r'[^\w\s-]',' ',s or '',flags=re.UNICODE)).strip()
def ahash(data,size=16):
 with Image.open(io.BytesIO(data)) as im:
  im=ImageOps.exif_transpose(im).convert('L').resize((size,size));px=list(im.getdata());avg=sum(px)/len(px);v=0
  for x in px:v=(v<<1)|(x>=avg)
  return v
def ref_bytes(source,member):
 if Path(source).is_dir(): return (Path(source)/member).read_bytes()
 with tarfile.open(source,'r:gz') as t:
  f=t.extractfile(member)
  if not f: raise FileNotFoundError(member)
  return f.read()
def main():
 p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--limit',type=int,default=100);a=p.parse_args();w=Path(a.work);c=sqlite3.connect(w/'reference-state.sqlite3',timeout=60);c.execute('PRAGMA busy_timeout=60000');rows=c.execute("SELECT id,artist_hint,title_hint FROM reference_items WHERE status IN ('parsed','temporary_error','unresolved') ORDER BY id LIMIT ?",(a.limit,)).fetchall();s=requests.Session();s.headers['User-Agent']='ArtlinePrivateReference/1.0 (metadata discovery; no reference images)';found=rights=0
 for rid,artist,title in rows:
  q=' '.join(x for x in (clean(artist),clean(title)) if x)
  try:
   r=s.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':5,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':120},timeout=(10,30));r.raise_for_status();pages=r.json().get('query',{}).get('pages',{})
   if not pages:
    c.execute("UPDATE reference_items SET status='unresolved',updated_at=datetime('now') WHERE id=?",(rid,));continue
   try:
    source=Path(os.environ['ART500K_PRIVATE_ROOT']); member=c.execute('select private_path from reference_items where id=?',(rid,)).fetchone()[0]
    # Do not repeatedly scan a multi-gigabyte tarball. Visual comparison is
    # enabled for the private extracted cache; tar references are queued for a
    # later single-pass cache build.
    rh=ahash(ref_bytes(source,member)) if source.is_dir() else None
   except (FileNotFoundError,KeyError): rh=None
   best=None
   for hit in pages.values():
    info=(hit.get('imageinfo') or [{}])[0];meta=info.get('extmetadata',{});label=html.unescape((meta.get('LicenseShortName') or {}).get('value','')).strip();url=info.get('url','')
    if not url.startswith('https://upload.wikimedia.org/'): continue
    try:
     cr=s.get(url,timeout=(10,30));cr.raise_for_status();score=(rh^ahash(cr.content)).bit_count()/256 if rh is not None else 1.0
     if best is None or score<best[0]:best=(score,hit,info,meta,label)
    except (requests.RequestException, UnidentifiedImageError): continue
   if not best: c.execute("UPDATE reference_items SET status='unresolved',updated_at=datetime('now') WHERE id=?",(rid,));continue
   score,hit,info,meta,label=best;url=info.get('url','');page='https://commons.wikimedia.org/wiki/'+hit.get('title','').replace(' ','_');ok=label in APPROVED
   artist_text=html.unescape((meta.get('Artist') or {}).get('value','')).lower();title_text=html.unescape((meta.get('ObjectName') or meta.get('ImageDescription') or {}).get('value','')).lower();identity=clean(artist).lower() in artist_text and clean(title).lower().split()[:1] and clean(title).lower().split()[0] in title_text
   confidence='confirmed' if ok and score<=0.18 and identity else 'probable'
   c.execute("UPDATE reference_items SET status='candidate_found',source_name='Wikimedia Commons',source_record_id=?,source_url=?,image_url=?,rights_label=?,rights_uri=?,match_confidence=?,error=?,updated_at=datetime('now') WHERE id=?",(hit.get('title'),page,url,label,(meta.get('LicenseUrl') or {}).get('value',''),confidence,json.dumps({'visual_distance':score,'independent_metadata':identity}),rid));found+=1;rights+=ok
  except requests.RequestException as e:c.execute("UPDATE reference_items SET status='temporary_error',error=?,updated_at=datetime('now') WHERE id=?",(str(e)[:240],rid))
  time.sleep(1.5)
 c.commit();print(json.dumps({'searched':len(rows),'candidates':found,'approved_rights_candidates':rights,'reference_pixels_sent':False,'production_imports':0}))
if __name__=='__main__':main()
