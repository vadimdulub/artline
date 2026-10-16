"""Read-only independent source, identity and file verification for batch 101."""
import importlib.util,fcntl,gzip,json,io,re
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000101.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
native=b.mod('nativeverify101','museum-expansion-auckland-20261006.py')
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);ids=[r['artwork_id'] for r in images];assert 0<len(ids)<=100 and not audit['identity_holds']
rows=[r for r in i.selected(b.B)['rows'] if r['artwork_id'] in ids];pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());source=[];files=[]
policy=b.load(b.E/'source-policy-verification.json');rc=policy['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==policy['text']
for row in rows:
 im=next(x for x in images if x['artwork_id']==row['artwork_id']);rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 current=native.fields(raw);assert current==row['image']['source']['official_metadata']['parsed'];f=current['fields'];attrs=current['native_route']['attributes'];recon=row['image']['source']['identity_reconciliation'];c=recon['source_citation'];old=json.loads(c['evidence_note'])
 rawold=gzip.decompress((b.ROOT/old['body_path']).read_bytes());assert h.sha(rawold)==old['source_receipt']['sha256'];historical=native.fields(rawold);assert historical==old['raw_source_record']['native_fields']
 assert str(attrs['id'])==row['native_id']==row['current_source_id'] and f['Title']==row['title'] and f['Artist']==row['creator_label'] and f['Accession No']==row['accession_number']
 assert f['Copyright'].lower() in ['no known copyright restrictions','copyright expired'] and row['rights_status']=='restricted' and row['rights_label']==f['Copyright']
 assert native.creation_date(f['Production date'])[:2]==(row['first'],row['last']) and row['last']<=1955
 assert row['image']['image_url']==attrs['zoom_image']==im['source_image_url'] and row['plan_sha256']==old['plan_sha256']
 assert h.sha(json.dumps(c,sort_keys=True,ensure_ascii=False).encode())==recon['source_citation_sha256'] and row['identity_confidence']>=.9
 assert all(f[k]==historical['fields'][k] for k in ['Artist','Title','Production date','Medium','Dimensions','Credit line','Accession No','Copyright'])
 source.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],accession=row['accession_number'],current_source_sha256=rc['sha256'],historical_source_sha256=old['source_receipt']['sha256'],original_catalogue_plan_sha256=row['plan_sha256'],rights_label=row['rights_label'],rights_policy_sha256=policy['receipt']['sha256'],source_citation_sha256=recon['source_citation_sha256'],editorial_confidence=row['identity_confidence']))
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.004
 dec=next(d for d in review['decisions'] if d['artwork_id']==row['artwork_id']);assert dec['decision']=='accept' and dec['viewed_individually'] and dec['sha256']==im['sha256']
 ratio=recon['dimensions_mm'][1]/recon['dimensions_mm'][0];difference=abs(im['width']/im['height']-ratio)/ratio
 assert difference<.04 or dec.get('dimension_discrepancy_review'),'Unreviewed physical/pixel ratio discrepancy'
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],dimensions=[im['width'],im['height']],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,prepared_image_actually_viewed=True,physical_pixel_ratio_difference=difference,original_separately_viewed=dec.get('original_separately_viewed',False)))
with b.connect() as db:
 live=h.snapshot(db,ids);assert all(live[aid]==b.load(b.E/'gap-input.json.gz')['before'][aid] and live[aid]['artwork']['primary_media_id'] is None for aid in ids)
 for row in rows:
  cite=row['image']['source']['identity_reconciliation']['source_citation'];fresh=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s",(row['artwork_id'],cite['field_name']))];assert cite in fresh
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
b.save('independent-source-verification.json',dict(at=h.now(),records=source));b.save('independent-file-verification.json',dict(at=h.now(),files=files))
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=len(rows),files_verified=len(images),unchanged_preimages=True,duplicate_checks_passed=True,shared_ingestion_lock='artline-curated-ingestion',passed=True))
print('Independently verified',len(ids),'sources/files/unchanged image gaps')
