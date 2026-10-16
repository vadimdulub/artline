#!/usr/bin/env python3
"""One bounded production batch. Existing supervisor and historical plans untouched."""
import csv, fcntl, gzip, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fng70base',ROOT/'ops/continuous-fng-images-000064.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
b=base.b;i=base.i;h=base.h;load=base.load;save=base.save;connect=base.connect;target=base.target
E=ROOT/'docs/research/continuous-production-20261011/batches/000070'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000070'
B='fng-000'
for m in [base,b]:m.E=E;m.RUNTIME=RUNTIME;m.B=B
i.OP='continuous-primary-images-20261011-b000070';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for d in [E,RUNTIME,i.ORIG,i.BACKUP]:d.mkdir(parents=True,exist_ok=True)

def reconcile():
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
 reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json','docs/research/continuous-production-20261011/batches/000069/source-access-holds.json','docs/research/continuous-production-20261011/batches/000064/source-access-holds.json','docs/research/printmaking-continuation-20261011/README.md','docs/research/french-printmaking-20261011/README.md']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=x,sha256=h.sha((ROOT/x).read_bytes())) for x in paths],registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),registry_records=111,complete_registry=reg,precedence='Current source-specific policies; real local catalogue read-only. One batch; no scheduling or supervisor changes. Original registry authoritative, JSON review supplementary.'))
 q=save(E/'source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 assert {r['source_id'] for r in q['sources']}=={r['source_id'] for r in reg}
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json'
 save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledgers=paths[6:8],inherited_queue='source-queue-before.json',fng_route='No access hold for saved anonymous official export or selected native CC0 photographs; API-key endpoint not used.',policy='All unrelated holds preserved. No requests to held providers.'))
 save(E/'production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Earlier own writes require pinned-selection reconciliation'
  old=E.parent/'000069';receipt=load(old/'batch-verification-receipt.json');ids=receipt['production_ids']
  prior=load(old/'independent-production-verification.json')
  states=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND evidence_note LIKE %s",(ids,'%'+receipt['metadata_plan_sha256']+'%'))]
  assert len(states)==4 and set(ids)<={r['entity_id'] for r in citations}
  assert all(x['artwork']['primary_media_id'] is None and x['artwork']['status']=='review' for x in states.values())
  save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),batch=69,live_states=states,source_citations=citations,metadata_plan_sha256=receipt['metadata_plan_sha256'],current_campaign_rows=len(own),prior_campaign_increments=0,receipt_sha256=h.sha((old/'batch-verification-receipt.json').read_bytes())))
 print('Production target and prior batch reconciled.',flush=True)

def reserve():base.reserve()

def ateneum():
 if (E/'ateneum-route-verification.json').exists():return
 route=next(r for r in load(E/'source-queue-before.json')['sources'] if r['source_id']=='finnish_national_gallery')
 cursor=route['resume_cursor']['after_artwork_id'];mid='688a05df-a339-5dde-9fd0-4263559553f1'
 save(E/'production-target-before-ateneum-read.json',target())
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,unlinked_creator_label,current_institution_id::text,primary_media_id::text,status FROM artworks WHERE current_institution_id=%s AND id>%s::uuid AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 ORDER BY id LIMIT 25",(mid,cursor))]
  ids=[r['id'] for r in rows]
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme='fng-object'",(ids,))]
 cap=load(ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json')
 with Path(cap['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
 wanted={r['external_id'] for r in ext};objects={str(o['objectId']):o for o in json.load(open(cap['path'])) if str(o['objectId']) in wanted}
 save(E/'ateneum-source-objects.json.gz',objects)
 checks=[]
 for row in rows:
  ex=[r for r in ext if r['entity_id']==row['id']];obj=objects.get(ex[0]['external_id']) if len(ex)==1 else None
  preferred=[p for p in obj.get('multimedia',[]) if p.get('isRiaDisplayImage') and p.get('license')=='CC0'] if obj else []
  reason='eligible_photo_lead_requires_exact_source_and_creator_review' if preferred else ('no_multimedia_in_checked_export' if obj and not obj.get('multimedia') else 'no_unique_preferred_cc0_or_native_identity')
  checks.append(dict(artwork_id=row['id'],native_id=ex[0]['external_id'] if len(ex)==1 else None,title=row['title'],outcome=reason,preferred_cc0_photo_ids=[x['id'] for x in preferred]))
 save(E/'ateneum-route-verification.json',dict(at=h.now(),rows=rows,identifiers=ext,checks=checks,source_export=cap,export_checksum_verified=True,after_artwork_id=cursor,resume_after_artwork_id=rows[-1]['id'] if rows else cursor,inspected=len(rows),eligible_photo_leads=sum(bool(r['preferred_cc0_photo_ids']) for r in checks),downloaded=0,metadata_only=True,remaining_scope_not_exhausted=len(rows)==25))
 print('Ateneum checked',len(rows),'preferred photo leads',sum(bool(r['preferred_cc0_photo_ids']) for r in checks),flush=True)

def sinebrychoff():
 if (E/'cited-source-objects.json.gz').exists():return
 q=load(E/'source-queue-before.json');route=next(x for x in q['sources'] if x['source_id']=='finnish_national_gallery')
 cursor=route['continuation_routes']['sinebrychoff']['after_artwork_id']
 save(E/'production-target-before-sinebrychoff-read.json',target())
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,unlinked_creator_label,current_institution_id::text,primary_media_id::text,status FROM artworks WHERE current_institution_id=%s AND id>%s::uuid AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 ORDER BY id LIMIT 25",(b.MID,cursor))]
  ids=[x['id'] for x in rows];states=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND source_url LIKE 'https://kokoelma.kansallisgalleria.fi/en/object/%%'",(ids,))]
 save(E/'fng-bounded-gap-input.json',dict(at=h.now(),rows=rows,institution_id=b.MID,limit=25,after_artwork_id=cursor,route='fresh Sinebrychoff image gaps after saved UUID'))
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before=states))
 save(E/'native-citation-crosswalk.json',dict(at=h.now(),citations=citations))
 cap=load(ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json')
 with Path(cap['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
 wanted={json.loads(c['evidence_note'])['object_id'] for c in citations if c['field_name']=='museum_holding_research'}
 objects={str(o['objectId']):o for o in json.load(open(cap['path'])) if str(o['objectId']) in wanted}
 save(E/'cited-source-objects.json.gz',objects)
 reg=load(E/'required-input-reconciliation.json')['complete_registry']
 save(E/'source-register.json',dict(at=h.now(),sources=[r for r in reg if r['source_id'] in ['finnish_national_gallery','yale_lux']],policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',source_capture_date=cap['retrieved_at'],source_export_sha256=cap['sha256'],access='Verified anonymous official export; selected photograph must explicitly be CC0',remaining_gaps='Bounded slices only; no completeness claim',metadata_refresh_due='2026-11-08'))
 print('Sinebrychoff gaps',len(rows),flush=True)

def prepare():base.prepare()
def deliver():base.deliver()
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
