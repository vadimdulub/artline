#!/usr/bin/env python3
"""Independent source and actual visual decisions for the bounded NSW batch."""
import fcntl,gzip,importlib.util,io,json
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-nsw-images-000043.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=i.selected(b.B);pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());assert h.load(i.folder(b.B)/'pin.json')['sha256']==pin
 descriptions={
 '345b3633-fa29-5b97-a366-722ac93efdf0':'Individually viewed actual prepared JPEG through view_image. Complete rectangular composition: large two-handled pale vessel with flowers in the foreground, pink sand and rightward shadow, distant white architecture and blue sea. No merchandise, detail crop, montage, placeholder or opaque clipping. Museum accession 1.1982 matches the source reproduction filename. Dimensions discrepancy stays in source evidence; no unverified frame explanation or metadata rewrite.',
 '39f03d16-2162-5bc6-9381-0112538f1904':'Individually viewed actual prepared JPEG through view_image. Complete tall composition: standing bearded prospector inspecting a circular pan, shovel and pick by rocks at lower left, full boots and ground visible, ferns at right, dark background. No merchandise, montage, placeholder or detail-only crop. Exact creator, title, date, NSW collection and 213.4 x 116.9 cm source dimensions support same physical work.'}
 images=[];decisions=[];sources=[]
 for r in p['rows']:
  im=h.load(i.folder(b.B)/'prepared'/(r['artwork_id']+'.json'));raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes()
  assert im['state']=='prepared' and h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
  with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
  with Image.open(io.BytesIO(original)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.005
  page=r['image']['source'];rc=page['receipt'];html=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(html)==rc['sha256'] and rc['status']==200
  soup=BeautifulSoup(html,'html.parser');md=json.loads(soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')['ng-init'].split('=',1)[1].strip())
  assert md==page['metadata'] and md['_id']==r['current_source_id'] and md['title']==r['title'] and md['artistName']==r['creator_label'] and int(md['year'])==r['last']<=1955
  assert soup.select_one('img[itemprop=image]')['src']==im['source_image_url']
  assert soup.select_one('.copyright-wrapper .copyright').get_text(' ',strip=True)=='Public domain' and r['rights_status']=='public_domain'
  assert r['identity_confidence']>=.9 and im['download']['status']==200
  images.append(dict(artwork_id=r['artwork_id'],path=im['path'],sha256=im['sha256'],bytes=im['bytes'],original_sha256=im['source_sha256'],original_path=im['original_path'],complete_decode=True,full_source_proportions_preserved=True))
  decisions.append(dict(artwork_id=r['artwork_id'],sha256=im['sha256'],artist=r['creator_label'],decision='accept',viewed_individually=True,view_tool='functions view_image',actual_viewed_path=im['path'],note=descriptions[r['artwork_id']],flag_resolution='source_display_placeholder is the generic manual_visual_required marker; actual displayed WikiArt image is a full artwork, not a placeholder'))
  sources.append(dict(artwork_id=r['artwork_id'],source_url=r['source_url'],wikiart_id=r['current_source_id'],source_sha256=rc['sha256'],source_image_url=im['source_image_url'],actual_rights_label='Public domain',user_approval_separate=True,source_fields=page['fields'],identity_confidence=r['identity_confidence'],identity_basis=r['identity_basis']))
 review=dict(at=h.now(),selection_sha256=pin,batch_quality_decision='accept',decisions=decisions,actually_viewed_count=2,unsampled_images_claimed_viewed=0)
 if not (i.folder(b.B)/'visual-review.json').exists():h.save(i.folder(b.B)/'visual-review.json',review)
 b.save('actual-visual-review.json',h.load(i.folder(b.B)/'visual-review.json'))
 with b.connect() as db:
  ids=[r['artwork_id'] for r in p['rows']];state=h.snapshot(db,ids);prior=h.load(b.E/'nsw-live-gap-reconciliation.json')['before']
  for aid in ids:assert state[aid]==prior[aid] and state[aid]['artwork']['primary_media_id'] is None
  assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
 b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,sources=sources,files=images,live_null_primary_ids=ids,unrelated_metadata_change_authorized=False,duplicate_hashes=0))
 print('Source, file, visual and live gap verification passed for 2 images')
