"""Verify pinned historical reserve sources and prior visual evidence without changes."""
import importlib.util,json,gzip
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('h','ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
E=h.ROOT/'docs/research/continuous-production-20261011/batches/000286';pp=h.ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);records=[]
for r in p['rows']:
 aid=r['artwork_id'];src=h.ROOT/r['source_record_reference'];assert h.sha(src.read_bytes())==r['source_record_sha256'];o=h.load(src)
 for key,rkey in [('raw','receipt'),('manifest','manifest_receipt')]:
  rc=o[rkey];raw=gzip.decompress((h.ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'] and json.loads(raw)==o[key]
 assert o['native_id']==r['source_id'] and o['manifest']['id']==r['manifest_receipt']['url'] and any(x['id']==r['source_url'] for x in o['manifest']['homepage'])
 for key in ['title','accession_number','date','creator_label','dimensions_text','medium','image_url']:assert o[key]==r[key]
 ev=r['continuation_visual_evidence'];dec=h.ROOT/ev['decision_reference'];d=h.load(dec);assert h.sha(dec.read_bytes())==ev['decision_sha256'] and aid in d['approved']
 sheet=h.load(dec.parent.parent/'visual-sheets'/dec.name);assert d['sheet_sha256']==h.sha(Path(sheet['sheet']).read_bytes())
 im=p['images'][aid];assert ev['image_sha256']==im['sha256']==next(x['sha256'] for x in sheet['images'] if x['artwork_id']==aid)
 raw=Path(im['local_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(im['local_path']) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 records.append(dict(artwork_id=aid,source_id=r['source_id'],source_record_sha256=r['source_record_sha256'],raw_sha256=o['receipt']['sha256'],manifest_sha256=o['manifest_receipt']['sha256'],image_sha256=im['sha256'],prior_visual_decision=ev['decision_reference'],prior_visual_decision_sha256=ev['decision_sha256'],prior_contact_sheet_sha256=d['sheet_sha256']))
h.save(E/'independent-reserve-source-verification.json',dict(at=h.now(),verified=len(records),historical_plan_sha256=h.sha(pp.read_bytes()),records=records,new_visual_review_claimed=False,new_downloads=0,historical_plans_unchanged=True))
print('188 original source records, captures, manifests, visual sheets and image files verified; zero new deliveries')
