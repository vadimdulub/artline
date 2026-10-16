"""Independent parsing, file checks and unchanged live preimages before production write."""
import importlib.util,json,gzip,io,fcntl
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-khm-images-000119.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert len(images)==1 and not audit['identity_holds'];row=i.selected(b.B)['rows'][0];im=images[0];aid=im['artwork_id'];src=row['image']['source'];rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
sp=BeautifulSoup(raw,'html.parser');md=json.loads(sp.select_one('.wiki-layout-painting-info-bottom[ng-init]')['ng-init'].split('=',1)[1].strip());assert md==src['metadata'] and md['_id']==row['current_source_id'] and md['year']=='1512';assert md['artistName']==row['creator_label'];assert sp.select_one('img[itemprop=image]')['src']==im['source_image_url'];assert sp.select_one('.copyright-wrapper .copyright').get_text(' ',strip=True)==row['rights_label']=='Public domain';assert 'Kunsthistorisches Museum, Vienna, Austria' in sp.get_text(' ',strip=True)
native=src['official_metadata'];rc2=native['receipt'];raw2=gzip.decompress(Path(rc2['body_path']).read_bytes());assert h.sha(raw2)==rc2['sha256'] and rc2['status']==200;text=BeautifulSoup(raw2,'html.parser').get_text(' ',strip=True);assert text==native['text'] and all(t in text for t in ['1512 datiert','49,3 × 37,4','Gemäldegalerie, 848','Albrecht Dürer'])
recon=src['identity_reconciliation'];citation=recon['source_citation'];assert h.sha(json.dumps(citation,sort_keys=True,ensure_ascii=False).encode())==recon['source_citation_sha256'];assert json.loads(citation['evidence_note'])['accession']==row['accession_number']=='GG_848';assert row['identity_confidence']>=.9 and row['first'] is None and row['last'] is None
raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
with Image.open(io.BytesIO(raw)) as pic:pic.verify()
with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG' and abs(pic.width/pic.height-37.4/49.3)/(37.4/49.3)<.02
with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.003
v=review['decisions'][0];assert v['decision']=='accept' and v['viewed_individually'] and v['original_separately_viewed'] and v['sha256']==im['sha256']
with b.connect() as db:
 state=h.snapshot(db,[aid]);assert state[aid]==h.load(b.E/'gap-input.json.gz')['before'][aid] and state[aid]['artwork']['primary_media_id'] is None
 fresh=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s",(aid,citation['field_name']))];assert citation in fresh
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchall()
b.save('independent-source-verification.json',dict(at=h.now(),records=[dict(artwork_id=aid,source_id=md['_id'],accession=row['accession_number'],wikiart_source_sha256=rc['sha256'],official_source_sha256=rc2['sha256'],persisted_citation_sha256=recon['source_citation_sha256'],editorial_confidence=row['identity_confidence'],catalogue_unknown_dates_preserved=True,source_date_1512=True,native_image_downloaded=False)]))
b.save('independent-file-verification.json',dict(at=h.now(),files=[dict(artwork_id=aid,path=im['path'],sha256=im['sha256'],bytes=len(raw),original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,prepared_image_actually_viewed=True,original_separately_viewed=True)]))
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes()),visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=1,files_verified=1,unchanged_preimages=True,duplicate_checks_passed=True,shared_ingestion_lock='artline-curated-ingestion',passed=True))
print('One source identity, files and unchanged live primary gap independently verified')
