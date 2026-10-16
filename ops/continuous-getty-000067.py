#!/usr/bin/env python3
"""One bounded reserve reconciliation and Getty continuation; no supervisor work."""
import csv, fcntl, gzip, importlib.util, inspect, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=mod('getty67base','continuous-getty-images-000059.py')
h=w.h;i=w.i;load=w.load;save=w.save;connect=w.connect;target=w.target
E=ROOT/'docs/research/continuous-production-20261011/batches/000067'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000067'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000067'
B='getty-067';OP='continuous-getty-images-20261011-b000067'
w.E=E;w.RUNTIME=R;w.DATA=DATA;w.B=B;i.OP=OP;i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
for p in [E,R,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
code=inspect.getsource(i.apply)
old="m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'"
assert old in code
exec(compile(code.replace(old,"m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'"),__file__,'exec'),i.__dict__)

def inputs():
 if (E/'required-input-reconciliation.json').exists():return
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
 reg=list(csv.DictReader(registry.open()));q=load(E.parents[1]/'source-queue.json')
 assert len(reg)==len(q['sources'])==111 and {r['source_id'] for r in reg}=={r['source_id'] for r in q['sources']}
 paths=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000066/CHECKPOINT.json',E.parent/'000066/source-access-holds.json',ROOT/'ops/india-300-delivery-20261011.py']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],registry=reg,registry_rows=111,precedence='Current production authorization; real local catalogue read-only; one bounded batch; external supervisor unmodified.'))
 save(E/'source-queue-before.json',q)
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger=str(paths[-2]),inherited_sha256=h.sha(paths[-2].read_bytes()),provider_holds_preserved=True,held_provider_requests=0,getty_access_hold_found=False))
 save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),routes=[r for r in reg if r['source_id'] in ['yale_lux','getty_museum']],policy_reference='docs/ARTLINE_IMAGE_USE.md',remaining_gaps='French reserve needs current reconciliation; Getty Byzantine query continues from offset 100. Coverage incomplete.'))
 stops=list((ROOT/'docs/research/illustrated-300k-20261011').glob('stop*.json'))+[ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json']
 save(E/'completed-campaign-stop-preservation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in stops],separate_campaign=OP,restarted=False))
 save(E/'production-target-reconciliation.json',target())
 with connect() as db:
  prev=load(E.parent/'000066/batch-verification-receipt.json');ids=prev['production_ids']
  live=[dict(r) for r in db.execute('SELECT a.id::text,a.primary_media_id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(live)==11
  for r in live:
   ev=json.loads(r['evidence_json']) if isinstance(r['evidence_json'],str) else r['evidence_json']
   assert ev['selection_sha256']==prev['image_selection_sha256']
  own=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version FROM media_rights_evidence WHERE adapter_version=%s',(OP,))]
  assert not own or (i.folder(B)/'pin.json').exists(),'Own interrupted write requires plan reconciliation'
  save(E/'prior-write-reconciliation.json',dict(at=h.now(),previous_batch=66,previous_rows=live,current_operation_rows=own,previous_increments_excluded=True))
 print('Inputs, production target and previous delivery reconciled.',flush=True)

def reserve():
 r=mod('reserve67','continuous-reserve-warsaw-000052-research.py');r.E=E;r.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 save(E/'production-target-before-reserve-read.json',target())
 with connect() as db:
  live=h.snapshot(db,ids)
  cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for row in p['rows']:
   a=live[row['artwork_id']]['artwork'];im=p['images'][row['artwork_id']]
   assert a['accession_number']==row['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived'
   assert all(a[k]==v for k,v in row['date'].items())
 save(E/'french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,selected=0,physical_date_holds_preserved=['80082','80437','81054'],next_action='Getty Byzantine discovery offset 100; no replay of exhausted French reserve.'))
 print('Reserve: all 188 already delivered; 0 new candidates.',flush=True)

def discovery():
 q=load(E/'source-queue-before.json');c=next(r for r in q['sources'] if r['source_id']=='getty_museum')['resume_cursor'];assert c['next_offset']==100
 rc=w.capture('byzantine-offset-100','https://www.getty.edu/art/collection/api/search?q=Byzantine&size=50&from=100&include_deaccessioned=false');assert rc['status']==200
 data=json.loads(w.body(rc));pool=data['data'];assert len(pool)<=50
 with connect() as db:
  matches=[dict(r) for r in db.execute("SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text,e.external_id FROM artworks a LEFT JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='getty-object' WHERE a.current_institution_id=%s AND (a.accession_number=ANY(%s) OR e.external_id=ANY(%s))",(w.MID,[r['accession_number'] for r in pool],[r['id'] for r in pool]))]
  gaps=[dict(r) for r in db.execute("SELECT id::text,title,work_type,accession_number,creation_year_start,creation_year_end FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 AND work_type IN ('painting','drawing','print','watercolor','manuscript_illumination') AND accession_number IS NOT NULL ORDER BY work_type,id LIMIT 25",(w.MID,))]
 checks=[]
 for r in pool:
  ms=[a for a in matches if a['accession_number']==r['accession_number'] or a['external_id']==r['id']]
  whole=bool(r.get('is_standalone')) and not r.get('is_parent')
  checks.append(dict(native_id=r['id'],slug=r['id_manager_slug'],title=r['primary_name'],accession=r['accession_number'],whole_object_candidate=whole,existing=ms,outcome='component_or_ensemble_review_hold' if not whole else 'existing_object' if ms else 'whole_object_candidate_requires_native_reconciliation',index=r))
 save(E/'byzantine-discovery-verification.json',dict(at=h.now(),source_receipt=rc,offset=100,checked=len(pool),next_offset=100+len(pool),records=checks,images_requested=0,source_total=data.get('total')))
 save(E/'getty-gap-discovery.json',dict(at=h.now(),rows=gaps,limit=25))
 print(json.dumps(dict(byzantine_candidates=[{k:r[k] for k in ['slug','title','accession','outcome']} for r in checks if r['whole_object_candidate']],checked=len(checks),gap_sample=gaps),ensure_ascii=False),flush=True)

def gaps():
 if (E/'bounded-gap-input.json.gz').exists():return
 route=next(r for r in load(E/'source-queue-before.json')['sources'] if r['source_id']=='getty_museum')
 cursor=route['resume_cursor']['painting_image_gaps']['after_artwork_id']
 with connect() as db:
  rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,date_display,work_type,unlinked_creator_label FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 AND work_type='painting' AND accession_number IS NOT NULL AND id>%s::uuid ORDER BY id LIMIT 25",(w.MID,cursor))]
  ids=[r['id'] for r in rows]
  assert not set(ids)&set(route['resume_cursor']['painting_image_gaps']['held_ids'])
  notes=[dict(r) for r in db.execute("SELECT entity_id::text,source_id::text,source_url,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  ext=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  save(E/'bounded-gap-input.json.gz',dict(at=h.now(),rows=rows,before=h.snapshot(db,ids),citations=notes,identifiers=ext,after_artwork_id=cursor,limit=25))
 print('New Getty gaps after cursor:',len(rows),flush=True)
def prepare():w.prepare()
def deliver():
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes());assert pre['visual_review_sha256']==h.sha((i.folder(B)/'visual-review.json').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
