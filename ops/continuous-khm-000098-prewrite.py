"""Independent read-only identity/file checks; pinned exact-production recovery."""
import importlib.util,fcntl,gzip,json,io,html,os,subprocess
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-khm-images-000098.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert len(images)==2 and not audit['identity_holds'];ids=[r['artwork_id'] for r in images]
rows=[r for r in i.selected(b.B)['rows'] if r['artwork_id'] in ids];pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());source=[];files=[]
for row in rows:
 im=next(x for x in images if x['artwork_id']==row['artwork_id']);rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');tag=sp.select_one('.wiki-layout-painting-info-bottom[ng-init]');md=json.loads(tag['ng-init'].split('=',1)[1].strip());assert md==row['image']['source']['metadata'] and md['_id']==row['current_source_id']
 assert html.unescape(md['artistName'])==row['creator_label'];assert sp.select_one('img[itemprop=image]')['src']==im['source_image_url']
 assert sp.select_one('.copyright-wrapper .copyright').get_text(' ',strip=True)==row['rights_label']=='Public domain' and row['rights_status']=='public_domain'
 native=row['image']['source']['official_metadata'];rc2=native['receipt'];raw2=gzip.decompress(Path(rc2['body_path']).read_bytes());assert h.sha(raw2)==rc2['sha256'] and rc2['status']==200
 text=BeautifulSoup(raw2,'html.parser').get_text(' ',strip=True);assert text==native['text']
 recon=row['image']['source']['identity_reconciliation'];citation=recon['source_citation'];note=json.loads(citation['evidence_note']);assert h.sha(json.dumps(citation,sort_keys=True,ensure_ascii=False).encode())==recon['source_citation_sha256'];assert note['accession']==row['accession_number'] and row['identity_confidence']>=.9
 if row['accession_number']=='GG_6739':
  assert all(t in text for t in ['Gemäldegalerie, 6739','1502','56 cm × 41,5 cm','Limewood','Cranach']) and row['first']==row['last']==1502
  assert md['year']=='1502' and row['image']['source']['fields']['Dimensions']=='55.5 x 41.5 cm';ratio=41.5/56
 else:
  assert row['accession_number']=='GG_488' and all(t in text for t in ['Gemäldegalerie, 488','1629/1630','159,5 × 129','Anthonis van Dyck']) and row['first']==row['last']==1629
  assert md['year']=='1629-1630' and row['image']['source']['fields']['Dimensions']=='160 x 128 cm';ratio=129/159.5
 assert row['image']['source']['fields']['Location']=='Kunsthistorisches Museum, Vienna, Austria'
 source.append(dict(artwork_id=row['artwork_id'],source_id=row['current_source_id'],native_id=row['native_id'],accession=row['accession_number'],wikiart_source_sha256=rc['sha256'],official_source_sha256=rc2['sha256'],persisted_original_citation_sha256=recon['source_citation_sha256'],editorial_confidence=row['identity_confidence'],source_dates_and_measurement_differences_preserved=True,native_image_downloaded=False))
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG' and abs(pic.width/pic.height-ratio)/ratio<.02
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.003
 dec=next(d for d in review['decisions'] if d['artwork_id']==row['artwork_id']);assert dec['decision']=='accept' and dec['viewed_individually'] and dec['sha256']==im['sha256']
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],dimensions=[im['width'],im['height']],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,prepared_image_actually_viewed=True,original_separately_viewed=False))
with b.connect() as db:
 live=h.snapshot(db,ids);assert all(live[aid]==b.load(b.E/'gap-input.json.gz')['before'][aid] and live[aid]['artwork']['primary_media_id'] is None for aid in ids)
 for row in rows:
  cite=row['image']['source']['identity_reconciliation']['source_citation'];fresh=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s",(row['artwork_id'],cite['field_name']))];assert cite in fresh
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
b.save('independent-source-verification.json',dict(at=h.now(),records=source));b.save('independent-file-verification.json',dict(at=h.now(),files=files))
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=len(rows),files_verified=len(images),unchanged_preimages=True,duplicate_checks_passed=True,shared_ingestion_lock='artline-curated-ingestion',passed=True))
print('Two exact sources, prepared images and unchanged live gaps independently verified')
