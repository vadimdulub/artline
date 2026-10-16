#!/usr/bin/env python3
"""One bounded existing-gap continuation. External supervisor remains untouched."""
import csv, fcntl, gzip, hashlib, importlib.util, inspect, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fng53base',ROOT/'ops/continuous-fng-images-000038.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
i=b.i;h=b.h;load=b.load;save=b.save;connect=b.connect;target=b.target
E=ROOT/'docs/research/continuous-production-20261011/batches/000053'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000053'
B='fng-000'
b.E=E;b.RUNTIME=RUNTIME;b.B=B
i.OP='continuous-primary-images-20261011-b000053';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for d in [E,RUNTIME,i.ORIG,i.BACKUP]:d.mkdir(parents=True,exist_ok=True)
# Reuse the documented FNG-specific MIME validation and a 40-image ceiling.
code=inspect.getsource(i.prepare_one)
old="assert response.status_code==200 and (rc['content_type'] or '').startswith('image/'),'Unexpected source image response'"
new="assert response.status_code==200 and ((rc['content_type'] or '').startswith('image/') or (row['provider']=='fng' and host=='kokoelma.kansallisgalleria.fi' and rc['content_type']=='application/octet-stream')),'Unexpected source image response'"
assert old in code;code=code.replace(old,new)
old='raw=bytes(payload);rc.update(bytes=len(raw),sha256=m.sha(raw))'
new="raw=bytes(payload);assert raw[:3]==b'\\xff\\xd8\\xff','Selected FNG payload is not JPEG';rc.update(bytes=len(raw),sha256=m.sha(raw))"
assert old in code;exec(compile(code.replace(old,new),__file__,'exec'),i.__dict__)
code=inspect.getsource(b.prepare_cited).replace('len(chosen)>=20','len(chosen)>=40').replace('selection_limit=20','selection_limit=40').replace('20-image bounded selection','At most 40-image bounded selection')
code=code.replace("citations=load(E/'native-citation-crosswalk.json')['citations']","citations=[c for c in load(E/'native-citation-crosswalk.json')['citations'] if c['field_name']=='museum_holding_research']")
exec(compile(code,__file__,'exec'),b.__dict__)

def reconcile():
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
 reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json','docs/research/continuous-production-20261011/batches/000052/source-access-holds.json']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=x,sha256=h.sha((ROOT/x).read_bytes())) for x in paths],registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),registry_records=111,complete_registry=reg,precedence='Current source-specific policies; real local catalogue read-only. One batch; no scheduling or supervisor changes.'))
 q=save(E/'source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 route=next(x for x in q['sources'] if x['source_id']=='finnish_national_gallery')
 cursor=route['continuation_routes']['sinebrychoff']['after_artwork_id']
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json'
 save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger=paths[-1],inherited_ledger_sha256=h.sha((ROOT/paths[-1]).read_bytes()),inherited_queue='source-queue-before.json',fng_route='No access hold for saved official export or selected native CC0 photographs',policy='All unrelated source holds preserved; no requests to held providers. API-key endpoint not used.'))
 save(E/'production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Earlier own writes require pinned-selection reconciliation'
  stalled=[dict(x) for x in db.execute("SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE adapter_version=ANY(%s)",(['continuous-primary-images-20261011-b000050','continuous-primary-images-20261011-b000051','continuous-primary-images-20261011-b000052'],))]
  assert not stalled,'An earlier authentication-blocked batch has writes requiring reconciliation'
  save(E/'interrupted-batches-live-verification.json',dict(at=h.now(),checked_campaigns=[50,51,52],rights_rows=stalled,earlier_campaign_increments=0,fresh_authentication_restored=True))
  old=E.parent/'000049';receipt=load(old/'batch-verification-receipt.json')
  previous=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(receipt['production_ids'],))]
  assert len(previous)==3
  for x in previous:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256']
  save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),batch=49,previous_rows=previous,current_campaign_rows=len(own),prior_campaign_increments=0,receipt_sha256=h.sha((old/'batch-verification-receipt.json').read_bytes())))
  if (E/'cited-source-objects.json.gz').exists():return
  rows=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,unlinked_creator_label,current_institution_id::text,primary_media_id::text,status FROM artworks WHERE current_institution_id=%s AND id>%s::uuid AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 ORDER BY id LIMIT 40",(b.MID,cursor))]
  ids=[x['id'] for x in rows];states=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND source_url LIKE 'https://kokoelma.kansallisgalleria.fi/en/object/%%'",(ids,))]
 save(E/'fng-bounded-gap-input.json',dict(at=h.now(),rows=rows,institution_id=b.MID,limit=40,after_artwork_id=cursor,route='fresh existing Sinebrychoff image gaps following saved cursor'))
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before=states))
 save(E/'native-citation-crosswalk.json',dict(at=h.now(),citations=citations))
 cap=load(ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json')
 with Path(cap['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
 wanted={json.loads(c['evidence_note'])['object_id'] for c in citations if c['field_name']=='museum_holding_research'}
 objects={str(o['objectId']):o for o in json.load(open(cap['path'])) if str(o['objectId']) in wanted}
 save(E/'cited-source-objects.json.gz',objects)
 save(E/'metadata-and-mime-reuse-verification.json',dict(at=h.now(),source_export=cap,export_checksum_verified=True,unselected_images_downloaded=0,metadata_refresh_due='2026-11-08',mime_correction_origin='docs/research/continuous-production-20261011/batches/000038/mime-retry-amendment.json',correction='FNG jpg paths only: application/octet-stream accepted with JPEG magic and complete decoding; no access bypass.'))
 save(E/'source-register.json',dict(at=h.now(),sources=[r for r in reg if r['source_id']=='finnish_national_gallery'],policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',source_capture_date=cap['retrieved_at'],source_export_sha256=cap['sha256'],access='Verified anonymous official export; native preferred photograph must explicitly be CC0',remaining_gaps='Bounded 40-object existing-gap slice only. Earlier holds and Ateneum route preserved. No completeness claim.'))
 print('Fresh existing gaps',len(rows),'source citation rows',len(citations),flush=True)

def prepare():b.prepare_cited()
def deliver():b.deliver()
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
