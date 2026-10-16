#!/usr/bin/env python3
"""One bounded, recoverable SMK gap batch after live French reserve reconciliation."""
import csv, fcntl, gzip, importlib.util, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base25','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect
smk=mod('smk25','overnight-smk-selected-images.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000025'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000025'
B='smk-000';MID='ee9976cf-63a1-48f7-9e34-eb5444e0486c';SID='7d0510eb-8810-485a-a602-9752dd03260a'
i.OP='continuous-primary-images-20261011-b000025';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['smk']=dict(mid=MID,scheme=smk.SCHEME,name=smk.NAME,rights='public_domain',license='Public Domain Mark 1.0',policy=smk.PDM,host='iip.smk.dk')
old_uid=i.m.uid;i.m.uid=lambda k:SID if k=='source/smk' else old_uid(k)
load=h.load
def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v
for p in [E,RUNTIME,i.ORIG,i.BACKUP,E/'source-captures']:p.mkdir(parents=True,exist_ok=True)
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def reconcile():
 save(E/'production-target-reconciliation.json',target())
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 inputs=[]
 for f in required:
  raw=(ROOT/f).read_bytes();raw.decode();inputs.append(dict(path=f,sha256=h.sha(raw),bytes=len(raw)))
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=inputs,registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,registry=reg,precedence='Current user authorization supersedes historical local mutation instructions; real local catalogue read-only. External supervisor unchanged.',python='/tmp/artline-cyprus-venv/bin/python',dependency_failure='System Python lacks psycopg; existing project venv reused without package installation'))
 if not(E/'french-reserve-live-reconciliation.json').exists():
  d=mod('french25','french-printmaking-delivery-20261011.py');main=d.RUN
  original,pin=d.final_plan();top=load(main/'scope-topup/delivery-plan.json.gz');reserve=set(original['eligible_reserve'])-{r['artwork_id'] for r in top['rows']};assert len(reserve)==188
  rows=[r for r in d.identity_rows() if r['artwork_id'] in reserve];assert len(rows)==188
  with connect() as db:
   states=h.snapshot(db,sorted(reserve));assert len(states)==188
   citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(sorted(reserve),))]
   identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme ILIKE '%%yale%%'",(sorted(reserve),))]
   for r in rows:
    a=states[r['artwork_id']]['artwork'];assert a['accession_number']==r['accession_number'] and a['primary_media_id'] and a['status']!='archived'
    assert any(x['entity_id']==r['artwork_id'] and x['external_id']==r['native_id'] for x in identifiers)
   assert set(x['entity_id'] for x in citations)==reserve
  save(E/'french-reserve-live-reconciliation.json',dict(at=h.now(),historical_plan_sha256=pin,reserve_inspected=188,already_in_production=188,unimported=0,new_programme_increments=0,rows=[dict(artwork_id=r['artwork_id'],native_id=r['native_id'],accession=r['accession_number'],primary_media_id=states[r['artwork_id']]['artwork']['primary_media_id']) for r in rows],citations=citations,prior_visual_evidence='docs/research/printmaking-continuation-20261011/french-reserve/; immutable checksum-bound visual approvals unchanged; no reserve selected or replayed'))
 if not(E/'prior-batch-live-reconciliation.json').exists():
  previous=E.parent/'000024';p=load(previous/'walters-icons/plan.json.gz');pin=h.sha((previous/'walters-icons/plan.json.gz').read_bytes());ids=[r['artwork_id'] for r in p['records']]
  with connect() as db:
   states=h.snapshot(db,ids);notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE field_name='continuous_walters_object_evidence_20261011_b000024' AND entity_id=ANY(%s::uuid[])",(ids,))]
   assert len(states)==len(notes)==25 and all(x['plan_sha256']==pin for x in notes)
  save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=24,verified_rows=25,citations=notes,new_batch_increments=0,uncertain_writes=False))
 save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,sources=[x for x in reg if x['source_id'] in ['yale_lux','smk_denmark']],policy='docs/ARTLINE_IMAGE_USE.md; exact per-object PDM required for SMK, no generalized provider approval',remaining_gaps='Only a bounded SMK image-gap keyset researched; no museum-wide completion asserted.'))
 # Preserve known provider holds and the individual SMK identity hold.
 qp=load(E.parents[1]/'source-queue.json');held=[x for x in qp['sources'] if 'hold' in x['status'] or '403' in x['status']]
 save(E/'source-access-holds.json',dict(at=h.now(),preserved_routes=held,additional_ledgers=['docs/research/images-followup-20260916/direct-inherited-holds.json','docs/research/continuous-production-20261011/batches/000024/source-access-holds.json'],smk_object_hold='0e4cf4a9-1bfa-4114-8e17-5438abb2a0c3',smk_surface_hold_found=False,policy='Do not retry held image surfaces or change hosts to bypass restrictions.'))
def prepare():
 reconcile()
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 with connect() as db:
  rows=[dict(x) for x in db.execute("""SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,e.external_id,
    (SELECT jsonb_agg(jsonb_build_object('id',aa.artist_id,'role',aa.attribution_role,'name',ar.display_name,'native',ex.external_id)) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id LEFT JOIN external_identifiers ex ON ex.entity_id=ar.id AND ex.entity_type='artist' AND ex.scheme='smk-person' WHERE aa.artwork_id=a.id) creators
    FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' AND e.scheme=%s WHERE a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.status<>'archived' AND a.creation_year_end<=1955 ORDER BY a.id LIMIT 80""",(smk.SCHEME,MID))]
 save(E/'bounded-gap-input.json',dict(at=h.now(),rows=rows,limit=80,ordering='artwork UUID ascending within exact institution and native scheme'))
 chosen=[];checks=[]
 for a in rows:
  reason=None;oid=a['external_id'];creators=a['creators'] or [];rc=None
  if a['id']=='0e4cf4a9-1bfa-4114-8e17-5438abb2a0c3':reason='Existing terminal source/identity hold preserved'
  elif len(creators)!=1 or creators[0]['role']!='primary' or not creators[0]['native']:reason='Requires separate anonymous/workshop or multiple-creator workflow; no inferred painter'
  if reason:checks.append(dict(artwork_id=a['id'],native_id=oid,reason=reason));continue
  url='https://api.smk.dk/api/v1/art/?object_number='+quote(oid,safe='')
  rp=E/'source-captures'/(a['id']+'.receipt.json');bp=rp.with_name(a['id']+'.body.gz')
  if rp.exists():rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256']
  else:
   i.provider_slot('api.smk.dk');response=i.session().get(url,timeout=(15,40));raw=response.content;bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=h.now(),retrieved_at=h.now(),url=url,status=response.status_code,sha256=h.sha(raw),body_path=str(bp.relative_to(ROOT)),retry_after=response.headers.get('Retry-After'));save(rp,rc)
  if rc['status'] in [401,403,429]:save(E/'access-holds/api.smk.dk.json',rc);checks.append(dict(artwork_id=a['id'],native_id=oid,reason='Provider metadata access hold'));break
  try:
   assert rc['status']==200,'Metadata HTTP '+str(rc['status'])
   objects=json.loads(raw)['items'];assert len(objects)==1,'Ambiguous source response';o=objects[0]
   c=dict(a,source_api_id=o['id'],artist_authority=creators[0]['native'],roles=[creators[0]['role']])
   image,facts=smk.source_match(c,o)
   assert image and a['creation_year_end']<=1955
   assert not re.search(r'loan|lent|deaccession',json.dumps(o.get('acquisition',{})),re.I),'Holding review'
   chosen.append(dict(artwork_id=a['id'],native_id=oid,title=a['title'],creator_label=creators[0]['name'],source_url=o['frontend_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='smk',image=dict(image_url=image,source=o,receipt=rc),plan_sha256=h.sha(bp.read_bytes()),plan_path=str(bp),expected_primary_artist_id=creators[0]['id'],artist_authority=creators[0]['native'],source_match_input=c,source_match_facts=facts,rights_basis='SMK native exact-object API explicitly supplies Public Domain Mark 1.0 and primary image. Original source maker labels, qualifiers, date notes and rights preserved; no independent copyright-holder licence asserted.'))
  except (ValueError,AssertionError,KeyError) as exc:reason=str(exc)
  checks.append(dict(artwork_id=a['id'],native_id=oid,reason=reason or 'selected',source_sha256=rc['sha256']))
  if len(chosen)>=10:break
 save(E/'gap-reconciliation.json',dict(at=h.now(),checked=len(checks),selected=len(chosen),rows=checks,resume_after_artwork_id=checks[-1]['artwork_id'] if checks else None))
 assert chosen,'No eligible SMK gaps in bounded selection'
 save(i.folder(B)/'selection.json.gz',dict(provider='smk',batch=B,rows=chosen,selection_basis='Existing unillustrated objects; exact source accession, native maker authority, title, dates and explicit PDM.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()
def finish():
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)
def deliver():
 # Reconcile interrupted writes before uploading or opening the write connection.
 images,_,_=i.accepted(B);ids=[x['artwork_id'] for x in images];assert 1<=len(ids)<=10
 with connect() as db:
  state=h.snapshot(db,ids);present=[x for x in images if state[x['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(state[x['artwork_id']]['artwork']['primary_media_id']==x['media_id'] for x in images)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Missing own transaction recovery preimage'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(reconcile=reconcile,prepare=prepare,deliver=deliver)[sys.argv[1]]()
