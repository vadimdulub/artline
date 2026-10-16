"""Independent parsing, exact pinned crosswalk and file checks before mutations."""
import importlib.util,json,gzip,io,re
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000113.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
native=b.mod('independent113','museum-expansion-auckland-20261006.py');images,audit,review=i.accepted(b.B);assert len(images)==3 and not audit['identity_holds'];files=[];sources=[]
policy=b.load(b.E/'source-policy-verification.json');rc=policy['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==policy['text']
with b.connect() as db:
 for im in images:
  row=next(r for r in i.selected(b.B)['rows'] if r['artwork_id']==im['artwork_id']);aid=row['artwork_id'];recon=row['image']['source']['identity_reconciliation'];rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
  parsed=native.fields(raw);assert parsed==row['image']['source']['official_metadata']['parsed'];f=parsed['fields'];attrs=parsed['native_route']['attributes'];cite=recon['source_citation'];old=json.loads(cite['evidence_note'])
  assert str(attrs['id'])==row['current_source_id']==recon['native_id'] and row['native_id']==recon['wikidata_id']
  assert h.norm(f['Title'])==h.norm(row['title']) and f['Artist']==row['creator_label'] and native.creation_date(f['Production date'])[:2]==(row['first'],row['last']) and row['last']<=1955
  assert f['Copyright'].lower() in ['no known copyright restrictions','copyright expired'] and f['Copyright']==row['rights_label'] and row['rights_status']=='restricted'
  assert attrs['zoom_image']==row['image']['image_url']==im['source_image_url'] and all(recon['checks'].values()) and old['plan_sha256']==row['plan_sha256']
  assert recon['source_citation_sha256']==h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode())
  assert db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s",(aid,cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone()
  state=h.snapshot(db,[aid])[aid];assert state==b.load(b.E/'gap-input.json.gz')['before'][aid] and state['artwork']['primary_media_id'] is None
  assert db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikidata'",(aid,)).fetchone()['external_id']==row['native_id']
  data=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(data)==im['sha256'] and len(data)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
  with Image.open(io.BytesIO(data)) as p:p.verify()
  with Image.open(io.BytesIO(data)) as p:p.load();assert p.size==(im['width'],im['height'])
  with Image.open(io.BytesIO(original)) as p:p.load();assert list(p.size)==im['original_dimensions'] and abs(p.width/p.height-im['width']/im['height'])<.004
  dims=recon['dimensions_mm'];difference=abs(im['width']/im['height']-dims[1]/dims[0])/(dims[1]/dims[0]);assert difference<.04
  assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchone()
  dec=next(d for d in review['decisions'] if d['artwork_id']==aid);assert dec['decision']=='accept' and dec['viewed_individually'] and dec['sha256']==im['sha256']
  sources.append(dict(artwork_id=aid,source_sha256=rc['sha256'],source_citation_sha256=recon['source_citation_sha256'],wikidata_id=row['native_id'],native_id=row['current_source_id'],accession=f['Accession No'],source_rights=f['Copyright'],selection_identity_checks=recon['checks']))
  files.append(dict(artwork_id=aid,sha256=im['sha256'],bytes=len(data),original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,actually_viewed=True,physical_pixel_ratio_difference=difference))
b.save('independent-source-verification.json',dict(at=h.now(),records=sources));b.save('independent-file-verification.json',dict(at=h.now(),files=files))
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes()),visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=3,files_verified=3,unchanged_preimages=True,shared_ingestion_lock='artline-curated-ingestion',passed=True))
print('Independent checks passed: 3 exact source/image records')
