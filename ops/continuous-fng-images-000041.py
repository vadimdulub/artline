#!/usr/bin/env python3
"""One bounded pending Sinebrychoff image continuation; external supervisor owns scheduling."""
import fcntl, gzip, hashlib, importlib.util, inspect, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fng41base',ROOT/'ops/continuous-fng-images-000038.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
i=b.i;h=b.h;load=b.load;save=b.save;connect=b.connect;target=b.target
E=ROOT/'docs/research/continuous-production-20261011/batches/000041'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000041'
B='fng-000';OLD=E.parent/'000038'
b.E=E;b.RUNTIME=RUNTIME;b.B=B
i.OP='continuous-primary-images-20261011-b000041';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
# Reuse the documented source-specific MIME correction, before first download.
code=inspect.getsource(i.prepare_one)
old="assert response.status_code==200 and (rc['content_type'] or '').startswith('image/'),'Unexpected source image response'"
new="assert response.status_code==200 and ((rc['content_type'] or '').startswith('image/') or (row['provider']=='fng' and host=='kokoelma.kansallisgalleria.fi' and rc['content_type']=='application/octet-stream')),'Unexpected source image response'"
assert old in code;code=code.replace(old,new)
old='raw=bytes(payload);rc.update(bytes=len(raw),sha256=m.sha(raw))'
new="raw=bytes(payload);assert raw[:3]==b'\\xff\\xd8\\xff','Selected FNG payload is not JPEG';rc.update(bytes=len(raw),sha256=m.sha(raw))"
assert old in code;exec(compile(code.replace(old,new),__file__,'exec'),i.__dict__)
# This batch is bounded by the 27 pending source identities, not the old 20-image cap.
code=inspect.getsource(b.prepare_cited).replace('len(chosen)>=20','len(chosen)>=100').replace('selection_limit=20','selection_limit=100').replace('20-image bounded selection','At most 27-image bounded selection')
exec(compile(code,__file__,'exec'),b.__dict__)

def reconcile():
 save(E/'production-target-reconciliation.json',target())
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json'
 save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000040/source-access-holds.json',inherited_queue='source-queue-before.json',new_holds=['nsw-route-verification.json'],policy='No direct NSW requests or access circumvention. FNG pending native CC0 photo route has no access hold. Historical object/date holds remain unchanged.'))
 save(E/'nsw-route-verification.json',dict(at=h.now(),registry_id='art_gallery_nsw',bounded_production_gaps=35,evidence='nsw-bounded-gap-input.json',requests=[dict(url='https://www.artgallery.nsw.gov.au/terms/',tool='web.run',result='URL inaccessible'),dict(url='https://www.artgallery.nsw.gov.au/collection/works/611.1897/',tool='web.run',result='URL inaccessible'),dict(query='site:artgallery.nsw.gov.au terms images',tool='web.run',result='Blocked by robots.txt; non-retryable domain restriction'),dict(url='https://images.ag.nsw.gov.au/fotoweb/views/login-terms-and-conditions',tool='web.run',result='Official indexed image-system terms require Rights & Image Licensing permission for distribution/publication')],decision='Official object route access-held; independent record-specific reusable image rights not established. Do not retry unchanged route or download images.',object_pages_captured=0,images_downloaded=0,source_url='https://images.ag.nsw.gov.au/fotoweb/views/login-terms-and-conditions',remaining_gaps='35 bounded gaps are inventory only, not exact researched objects. Later permitted WikiArt matching remains a separate possible route.'))
 save(E/'courtauld-discovery-verification.json',dict(at=h.now(),registry_id='courtauld_gallery',url='https://gallerycollections.courtauld.ac.uk/terms',surface='web.run',result='URL inaccessible',decision='Terms not established. No direct requests or object/image research in this batch; do not treat a tool failure as a museum-wide denial.'))
 cp=load(OLD/'CHECKPOINT.json');pending=cp['resume']['pending_artwork_ids'];assert len(pending)==27
 if (E/'source-register.json').exists():return
 oldpool=load(OLD/'fng-bounded-gap-input.json');oldstates=load(OLD/'preparation-production-snapshot.json.gz')['before']
 with connect() as db:
  states=h.snapshot(db,pending)
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own,'Earlier own writes require pinned-selection reconciliation before preparation'
  eligible=[];excluded=[]
  for aid in pending:
   a=states[aid]['artwork'];assert a['status']!='archived'
   if a['primary_media_id'] is not None:excluded.append(dict(artwork_id=aid,reason='already_illustrated_by_another_job',primary_media_id=a['primary_media_id']));continue
   assert states[aid]==oldstates[aid],'Metadata changed since pending selection; re-research required'
   eligible.append(aid)
  citations=[dict(r) for r in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND source_url LIKE 'https://kokoelma.kansallisgalleria.fi/en/object/%%'",(eligible,))]
  prior=load(OLD/'batch-verification-receipt.json')
  delivered=h.snapshot(db,prior['production_ids'])
  ev=[dict(r) for r in db.execute('SELECT a.id::text,mre.adapter_version,mre.evidence_json FROM artworks a JOIN media_rights_evidence mre ON mre.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(prior['production_ids'],))]
  assert len(ev)==20
  for r in ev:
   e=r['evidence_json'];e=json.loads(e) if isinstance(e,str) else e
   assert e['selection_sha256']==prior['selection_sha256'] and e['batch_visual_review_sha256']==prior['visual_review_sha256']
 save(E/'pending-live-reconciliation.json',dict(at=h.now(),pending_ids=pending,eligible_ids=eligible,excluded=excluded,prior_delivered_ids=prior['production_ids'],prior_delivered_rights=ev,current_campaign_rows=len(own),prior_campaign_increment=0))
 rows=[r for r in oldpool['rows'] if r['id'] in eligible]
 save(E/'fng-bounded-gap-input.json',dict(at=h.now(),rows=rows,institution_id=b.MID,limit=27,pending_origin=str(OLD/'CHECKPOINT.json')))
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before={aid:states[aid] for aid in eligible}))
 crosswalk=E/'native-citation-crosswalk.json'
 if crosswalk.exists() and not load(crosswalk)['citations']:
  crosswalk.rename(E/'native-citation-crosswalk-attempt1.json')
  save(E/'preparation-failure-correction.json',dict(at=h.now(),failure='Read-only citation query used www.kansallisgalleria.fi rather than persisted kokoelma.kansallisgalleria.fi URLs; zero results and assertion stopped preparation.',correction='Exact historical citation URL host now used; failed receipt preserved. No downloads or production writes occurred.',retry_count=1))
 save(crosswalk,dict(at=h.now(),citations=citations))
 cap=load(ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json')
 with Path(cap['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
 wanted={json.loads(c['evidence_note'])['object_id'] for c in citations}
 objects={str(o['objectId']):o for o in json.load(open(cap['path'])) if str(o['objectId']) in wanted}
 assert len(objects)==len(wanted)==len(eligible)
 save(E/'cited-source-objects.json.gz',objects)
 save(E/'metadata-and-mime-reuse-verification.json',dict(at=h.now(),source_export=cap,export_checksum_verified=True,unselected_images_downloaded=0,metadata_refresh_due=cp['resume']['metadata_refresh_due'],mime_correction_origin='docs/research/continuous-production-20261011/batches/000038/mime-retry-amendment.json',mime_correction_sha256=h.sha((OLD/'mime-retry-amendment.json').read_bytes()),correction='FNG jpg paths only: accept application/octet-stream if JPEG magic and complete decoding succeed; no access bypass.'))
 reg=load(E/'required-input-reconciliation.json')['registry']
 save(E/'source-register.json',dict(at=h.now(),sources=[r for r in reg if r['source_id'] in ['art_gallery_nsw','courtauld_gallery','finnish_national_gallery']],policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',source_capture_date=cap['retrieved_at'],source_export_sha256=cap['sha256'],access='NSW held; Courtauld terms unresolved; FNG verified saved official metadata and photograph-specific CC0.',remaining_gaps='Only the 27 pending Sinebrychoff identities selected for revalidation; 33 prior source/date holds and the later source cursor preserved.'))
 print('Reconciled pending gaps',len(eligible),'already illustrated',len(excluded),flush=True)

def prepare():b.prepare_cited()
def deliver():b.deliver()
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
