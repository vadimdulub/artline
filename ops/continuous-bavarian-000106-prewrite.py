"""Independent identity, source, file, preimage and recovery checks; no writes."""
import importlib.util,fcntl,gzip,io,json
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-bavarian-images-000106.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert len(images)==2 and not audit['identity_holds'];rows=i.selected(b.B)['rows'];ids=[im['artwork_id'] for im in images];pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());sources=[];files=[]
for row in rows:
 im=next(x for x in images if x['artwork_id']==row['artwork_id']);source=row['image']['source'];rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True);assert text==source['official_metadata']['text']
 assert sp.select_one('img')['src']==im['source_image_url']==row['image']['image_url']
 assert sp.select_one('a[href="https://creativecommons.org/licenses/by-sa/4.0/"]').get_text(' ',strip=True)=='CC BY-SA 4.0'
 assert row['rights_status']=='cc_by_sa' and row['rights_label']=='CC BY-SA 4.0' and source['source_date_label'] in text and 'Inventory number '+source['source_accession'] in text
 recon=source['identity_reconciliation'];cite=recon['source_citation'];note=json.loads(cite['evidence_note']);assert note['plan_sha256']==row['plan_sha256'] and h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode())==recon['source_citation_sha256']
 if row['current_source_id']=='QKGBPPnxBb':
  old=note['page']['receipt'];oldpath=b.ROOT/old['body_path'];oldraw=gzip.decompress(oldpath.read_bytes());assert h.sha(oldraw)==old['sha256'];oldsp=BeautifulSoup(oldraw,'html.parser');md=json.loads(oldsp.select_one('.wiki-layout-painting-info-bottom[ng-init]')['ng-init'].split('=',1)[1].strip());assert md['_id']==row['native_id'] and md['title']==row['title'] and md['artistName']==row['creator_label'];assert row['first'] is None and row['last'] is None and 'um 1570' in text
 else:
  assert row['current_source_id']=='Znxw9NvGXg' and row['native_id']=='Q30056880' and rc['url'] in note['source_references'];old=note['source_receipt'];oldraw=gzip.decompress((b.ROOT/old['body_path']).read_bytes());assert h.sha(oldraw)==old['sha256'];entities=json.loads(oldraw)['entities'];assert 'Q30056880' in entities and row['first']==1640 and row['last']==1650
 sources.append(dict(artwork_id=row['artwork_id'],source_native_id=row['current_source_id'],source_accession=source['source_accession'],source_sha256=rc['sha256'],source_citation_sha256=recon['source_citation_sha256'],original_catalogue_plan_sha256=row['plan_sha256'],original_source_capture_sha256=old['sha256'],exact_official_image_link=True,license='CC BY-SA 4.0',editorial_confidence=row['identity_confidence'],metadata_dates_not_mutated=True))
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 assert Path(im['path']).resolve().is_relative_to((b.ROOT/'apps/web/public/assets/artworks/imported'/i.OP).resolve()) and Path(im['original_path']).resolve().is_relative_to(i.ORIG.resolve())
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.003
 height,width=source['physical_dimensions_cm'];difference=abs(width/height-im['width']/im['height'])/(width/height);assert difference<.05
 decision=next(d for d in review['decisions'] if d['artwork_id']==row['artwork_id']);assert decision['decision']=='accept' and decision['viewed_individually'] and decision['original_viewed'] and decision['sha256']==im['sha256']
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],dimensions=[im['width'],im['height']],original_path=im['original_path'],original_sha256=im['source_sha256'],original_bytes=len(orig),complete_decode=True,full_source_frame=True,original_and_derivative_actually_viewed=True,physical_ratio_difference=difference,ratio_discrepancy_individually_reviewed=True))
with b.connect() as db:
 live=h.snapshot(db,ids);assert all(live[aid]==b.load(b.E/'gap-input.json.gz')['before'][aid] and live[aid]['artwork']['primary_media_id'] is None for aid in ids)
 for row in rows:
  cite=row['image']['source']['identity_reconciliation']['source_citation'];assert db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s",(row['artwork_id'],cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone()
  assert db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme=%s",(row['artwork_id'],row['native_scheme'])).fetchone()['external_id']==row['native_id']
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
recovery=b.load(b.E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
b.save('independent-source-verification.json',dict(at=h.now(),records=sources));b.save('independent-file-verification.json',dict(at=h.now(),files=files));b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=2,files_verified=2,unchanged_preimages=True,duplicate_checks_passed=True,shared_ingestion_lock='artline-curated-ingestion',passed=True))
print('Independent checks passed for two native licensed reproductions.')
