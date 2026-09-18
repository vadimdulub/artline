#!/usr/bin/env python3
"""Consolidate exact public-image delivery proofs and check current country/artwork APIs."""
import argparse,csv,importlib.util,json,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('export-overnight-research-handoff.py'));e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
C=e.CORE;B=e.BASE

def main(phase,index_path):
 folder=B/'final-audit'/phase;dest=folder/'public-delivery.json';assert not dest.exists();snap=json.loads((folder/'production-semantic-snapshot.json').read_text());index=json.loads(index_path.read_text());proofs={}
 paths=list(B.glob('*/*/round-*/delivery/verification.json'))+list(B.glob('*/*/round-*/delivery/primary-images*/verification.json'))
 for p in paths:
  d=json.loads(p.read_text());db=d.get('databases',{})
  if set(db)!={'local','production'}:continue
  for im in d.get('public_images',[]):
   assert im['status']==200;proofs.setdefault((im['url'],im['sha256']),[]).append(dict(path=str(p.relative_to(B)),at=d['at'],sha256=C.sha(p.read_bytes())))
 rows=[]
 for path,im in sorted(snap['images'].items()):
  url=e.m.SITE+path;key=(url,im['checksum_sha256']);assert key in proofs,(path,'missing both-database/public-byte verification');assert im['verified'];rows.append(dict(storage_path=path,public_image_url=url,sha256=im['checksum_sha256'],bytes=im['byte_size'],width=im['width'],height=im['height'],rights_status=im['rights_status'],licence=im['license_label'],licence_url=im['license_url'],creator_credit=im['creator_credit'],source_page_url=im['source_page_url'],active_primary=im['active_primary'],local_and_production_verified=True,public_byte_verification_receipts=proofs[key]))
 countries=sorted({r['country'] for r in index['country_rounds']});pages=[];session=requests.Session();session.headers['User-Agent']='Artline/1.0 (public catalogue verification)'
 def get(url):
  for attempt in range(3):
   try:
    res=session.get(url,timeout=(10,45));res.raise_for_status();return res
   except requests.RequestException:
    if attempt==2:raise
    time.sleep(5)
 for code in countries:
  url=e.m.SITE+'/api/backend/v1/timeline?start=1100&end=2000&popular=false&women=false&country='+code;res=get(url);data=res.json();assert data['total']>0;pages.append(dict(kind='country_timeline',country=code,url=url,status=res.status_code,total=data['total'],sha256=C.sha(res.content)));print('Public timeline',code,data['total'],flush=True)
 with (B/'chatgpt-handoff'/phase/'artworks_added_this_session.csv').open(encoding='utf-8-sig',newline='') as f:works=[r for r in csv.DictReader(f) if r['status']=='review' and r['public_artwork_url']]
 chosen=set()
 for code in countries:
  w=next(r for r in works if code in r['artist_country_codes'].split(';') and r['artwork_slug'] not in chosen);chosen.add(w['artwork_slug']);url=w['public_artwork_url'];res=get(url);api=url.replace(e.m.SITE+'/',e.m.SITE+'/api/backend/v1/',1);detail=get(api);payload=detail.json();assert w['production_artwork_id'] in detail.text;pages.append(dict(kind='artwork_detail',country=code,slug=w['artwork_slug'],url=url,status=res.status_code,api_url=api,api_status=detail.status_code,api_sha256=C.sha(detail.content)));print('Public artwork',code,w['artwork_slug'],flush=True)
 root=B/'chatgpt-handoff'/phase;writer=e.CSV(root,'verified_selected_images',list(rows[0]) if rows else ['storage_path']);[writer.add(r) for r in rows];csv_receipt=writer.finish();result=dict(at=C.now(),image_count=len(rows),active_primary_images=sum(r['active_primary'] for r in rows),all_session_images_have_both_database_and_public_byte_proof=True,image_proofs_scope='Existing completed delivery checks compared exact served bytes with local SHA256 for every image in the final session snapshot. Those checks are reused with their timestamps and file hashes; this report does not falsely claim every byte was downloaded again at final audit time.',images_csv=csv_receipt,current_public_checks=pages,unauthenticated=True)
 C.save_new(dest,result);print('Public receipt coverage',len(rows),'images; current endpoints',len(pages),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',required=True);p.add_argument('--session-index',type=Path,required=True);a=p.parse_args();assert all(c.isalnum() or c in '-_' for c in a.phase);main(a.phase,a.session_index)
