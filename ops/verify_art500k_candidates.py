#!/usr/bin/env python3
import argparse,html,json,re,sqlite3,time
from pathlib import Path
import requests
APPROVED={'Public Domain Mark','CC0','CC BY','CC BY-SA'}
def norm(s):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s or '')).strip().casefold()
def main():
 p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--limit',type=int,default=100);a=p.parse_args();w=Path(a.work);c=sqlite3.connect(w/'reference-state.sqlite3',timeout=60);c.execute('PRAGMA busy_timeout=60000');rows=c.execute("SELECT id,artist_hint,title_hint,source_record_id FROM reference_items WHERE source_name='Wikimedia Commons' ORDER BY id LIMIT ?",(a.limit,)).fetchall();s=requests.Session();s.headers['User-Agent']='ArtlinePrivateReference/1.0 (independent metadata verification)';confirmed=0;rights=0
 for rid,artist,title,filetitle in rows:
  try:
   q=s.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','titles':filetitle,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':1200},timeout=(10,30));q.raise_for_status();page=next(iter(q.json().get('query',{}).get('pages',{}).values()),{});info=(page.get('imageinfo') or [{}])[0];meta=info.get('extmetadata',{});label=html.unescape((meta.get('LicenseShortName') or {}).get('value','')).strip();url=info.get('url','');at=norm((meta.get('Artist') or {}).get('value',''));ot=norm((meta.get('ObjectName') or meta.get('ImageDescription') or {}).get('value',''));identity=norm(artist) in at and any(tok in ot for tok in norm(title).split()[:2]);ok=label in APPROVED and url.startswith('https://upload.wikimedia.org/')
   if ok:rights+=1
   confidence='confirmed' if ok and identity else 'probable'
   c.execute("UPDATE reference_items SET match_confidence=?,rights_label=?,rights_uri=?,image_url=?,error=?,updated_at=datetime('now') WHERE id=?",(confidence,label,(meta.get('LicenseUrl') or {}).get('value',''),url,json.dumps({'independent_metadata':identity,'rights_approved':ok}),rid));confirmed+=confidence=='confirmed'
  except requests.RequestException as e:c.execute("UPDATE reference_items SET status='temporary_error',error=?,updated_at=datetime('now') WHERE id=?",(str(e)[:240],rid))
  time.sleep(1.5)
 c.commit();print(json.dumps({'verified':len(rows),'confirmed':confirmed,'approved_rights':rights,'production_imports':0,'reference_pixels_sent':False}))
if __name__=='__main__':main()
