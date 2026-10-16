#!/usr/bin/env python3
import datetime, hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000221'
Q=E.parents[1]/'source-queue.json'
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=load(E/'batch-verification-receipt.json'); cp=load(E/'CHECKPOINT.json'); research=load(E/'brera-route-research.json'); visual=load(E/'actual-visual-review.json')
assert receipt['verified_counts']==cp['verified_counts']==dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
assert receipt['production_writes']==0 and visual['prepared_images']==visual['actually_viewed_images']==0
assert len(research['object_reviews'])==10 and research['selected']==research['downloaded']==0
assert all(not x['explicit_image_reuse_terms'] for x in research['object_reviews'])
queue=load(Q); row=next(x for x in queue['sources'] if x['source_id']=='pinacoteca_brera')
assert row['last_batch']==221 and len(row['resume_cursor']['processed_object_urls'])==11
p=ROOT/'ops/india-300-delivery-20261011.py'; s=importlib.util.spec_from_file_location('h',p); h=importlib.util.module_from_spec(s); s.loader.exec_module(h)
with h.connect() as db:
 target=db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone()
 live=db.execute("select count(*) total,count(*) filter(where primary_media_id is null) gaps from artworks where status<>'archived' and current_institution_id=%s",('735f66cb-4b8b-4fbe-b238-d8cce44c845a',)).fetchone()
assert target=={'db':'artline','ro':'on'} and live=={'total':794,'gaps':780}
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,production_target=target,live_brera=live,queue_sha256=sha(Q),queue_cursor_count=11,reviewed_this_batch=10,selected=0,prepared=0,production_writes=0,verified_counts=receipt['verified_counts'],prior_campaign_increments_excluded=True)
(E/'independent-final-artifact-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out))
