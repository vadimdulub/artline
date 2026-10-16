"""Bounded reserve reconciliation and independent Basel discovery audit; read-only production."""
import importlib.util,json,gzip,csv,fcntl,subprocess,datetime
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base118',ROOT/'ops/continuous-image-batch-000002.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000118';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000118';R.mkdir(parents=True,exist_ok=True)
def save(n,v):h.save(E/n,v)
zero=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
start=datetime.datetime.fromtimestamp((E/'web-discovery-results.json').stat().st_mtime,datetime.timezone.utc).isoformat()
with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')]+[ROOT/'docs'/n for n in ['ARTLINE_IMAGE_USE.md','DATA_AND_IMAGE_COLLECTION_PROMPT.md','LOCAL_DATA_LOCATIONS.md']]
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
 save('required-input-verification.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],registry_rows=111,local_mutation_instructions_superseded=True))
 prior=E.parent/'000115/independent-reserve-evidence-verification.json';d=h.load(prior);assert len(d['records'])==188
 checks=[]
 for r in d['records']:
  for f in [r['source_record'],r['prior_visual_decision']]:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
  obj=h.load(Path(r['source_record']['path']));assert str(obj['native_id'])==r['source_id'];assert obj['receipt']['sha256']==r['source_capture_sha256']
  raw=Path(r['local_path']).read_bytes();assert h.sha(raw)==r['derivative_sha256'] and len(raw)==r['bytes']<=100000
  with Image.open(Path(r['local_path'])) as im:im.load()
  checks.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],source_record_sha256=r['source_record']['sha256'],derivative_sha256=r['derivative_sha256'],prior_visual_decision=r['prior_visual_decision'],complete_decode=True))
 for f in d['immutable_plans']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('independent-reserve-evidence-verification.json',dict(at=h.now(),records=checks,inspected=188,prior_evidence=str(prior.relative_to(ROOT)),prior_evidence_sha256=h.sha(prior.read_bytes()),immutable_plans_unchanged=True,new_visual_reviews=1,prior_visual_evidence_preserved=True))
 sample=d['records'][0];save('actual-visual-sample.json',dict(at=h.now(),artwork_id=sample['artwork_id'],path=sample['local_path'],sha256=sample['derivative_sha256'],viewed_with='view_image',observation='Complete sheet visible with margins and lower inscription; woman seated at keyboard. No blank/corrupt image or obvious derivative crop.',scope='Only this one derivative viewed now; other188 records rely on immutable prior visual decisions, not new individual visual inspection.'))
 target=b.target();actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres';save('production-target-verification.json',dict(target,connection_name=actual,helper='ops/india-300-delivery-20261011.py'))
 qp=E.parents[1]/'source-queue.json';q=h.load(qp);basel=next(x for x in q['sources'] if x['source_id']=='kunstmuseum_basel');c=basel['resume_cursor'];ids=sorted(set(c['pending_artwork_ids'])-set(c['researched_artwork_ids']));assert len(ids)==10
 gap=h.load(E.parent/'000104/gap-input.json.gz');rows=[r for r in gap['rows'] if r['id'] in ids]
 with b.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  states=h.snapshot(db,[r['artwork_id'] for r in d['records']]);assert len(states)==188
  cites=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND evidence_note::jsonb->>'plan_sha256'=%s",(list(states),d['prior_campaign_plan_sha256']))];assert {r['entity_id'] for r in cites}==set(states)
  assert all(states[r['artwork_id']]['artwork']['primary_media_id']==r['prior_primary_media_id'] and states[r['artwork_id']]['artwork']['status']!='archived' for r in d['records'])
  save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,prior_campaign_plan_sha256=d['prior_campaign_plan_sha256'],citations=cites,new_programme_increments=zero))
  p=h.load(E.parent/'000114/batch107-live-reconciliation.json');prev=next(v for v in p.values() if isinstance(v,dict) and v and all(isinstance(x,dict) and 'artwork' in x for x in v.values()));assert h.snapshot(db,list(prev))==prev
  save('batch107-live-reconciliation.json',dict(at=h.now(),verified_ids=list(prev),unchanged=True,new_increments=0,prior_evidence_sha256=h.sha((E.parent/'000114/batch107-live-reconciliation.json').read_bytes())))
  p=h.load(E.parent/'000109/independent-production-verification.json');assert h.snapshot(db,list(p['after']))==p['after'];save('batch109-live-reconciliation.json',dict(at=h.now(),verified_ids=list(p['after']),unchanged=True,new_increments=0))
  before=h.snapshot(db,ids);assert all(v['artwork']['primary_media_id'] is None for v in before.values());save('independent-production-verification.json',dict(at=h.now(),read_only=True,basel_objects=before,production_writes=0,storage_writes=0,verified_counts=zero))
 reasons={'02c6c549-33fe-5640-8084-5cb69d6c1b30':'WikiArt Nymphs bathing c1865 belongs to Winterthur, not Basel Z.821 Musizierende Nymphen1864 with fake(?) attribution. Rejected different work; qualified attribution preserved.', '0425054c-b38e-5a27-85c3-8488ae6bc127':'Official Basel provenance list identifies G1975.25 and lists date o.J.; no image found. Preserve existing metadata and document unknown source date; do not use Jacob van Ruisdael images for Salomon.', '046a89c6-9ebf-5251-91cd-e014de708cb3':'Cranach catalogue lead describes a1499 Mair Nativity impression in Basel but lacks reconciled accession/image. Same plate in another collection cannot substitute for Aus K.8.62.', '030b2ff1-ba34-527d-949a-1f64717f3fc2':'Old-copy-after Lotto attribution retained. Generic Lotto religious paintings do not identify Basel627.', '01d1a41f-0162-5800-bd77-2be7bb69cb6a':'Search surfaced Durer Karlsruhe2183 and Met prints; different maker/object/institution from anonymous German Basel900.'}
 holds=[dict(r,decision='no_exact_image_in_bounded_search',reason=reasons.get(r['id'],'No accession-bound eligible reproduction surfaced in exact-title/creator Basel and independent Commons/WikiArt discovery. No inference of global absence.'),native_image_requests=0) for r in rows]
 save('research-holds.json',dict(at=h.now(),records=holds,distinct_unresearched_objects=10,selected=0,downloaded=0,scope='Search discovery only; no new image identity accepted.'))
 save('source-access-holds.json',dict(at=h.now(),inherited=['docs/research/continuous-production-20261011/batches/000104/source-access-holds.json','docs/research/continuous-production-20261011/batches/000115/source-access-holds.json'],held_surface_requests=0,retries=0,native_multimedia_hold_preserved=True,commons_api_hold_preserved=True))
 save('independent-source-verification.json',dict(at=h.now(),gap_input_sha256=h.sha((E.parent/'000104/gap-input.json.gz').read_bytes()),new_researched_ids=ids,overlap_with_previous_researched=0,search_evidence=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in sorted(E.glob('web-discovery*.json'))],selected=0,qualification='Bounded search outputs, not exhaustive absence or new primary-object confirmation'))
 next_task='Rotate to an undercovered registry route: inspect the next untouched KHM gap IDs from its saved cursor, using permitted independent sources. French188 reserve exhausted; Basel frozen25 now fully searched, all unresolved holds retained. Do not repeat these searches without new evidence.'
 with qp.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX);old=h.load(qp);new=json.loads(json.dumps(old));changed=['yale_lux','kunstmuseum_basel','wikimedia_commons','wikiart']
  for r in new['sources']:
   if r['source_id'] not in changed:continue
   r.setdefault('research_history',[]).append(dict(batch=118,at=h.now(),evidence=str((E/'independent-source-verification.json').relative_to(ROOT)),verified_counts=zero));r['last_checked_at']=h.now();r['last_batch']=118
   if r['source_id']=='yale_lux':r['status']='french_reserve_exhausted_188_live_verified_no_new_objects'
   if r['source_id']=='kunstmuseum_basel':
    rc=r['resume_cursor'];assert set(ids).isdisjoint(rc['researched_artwork_ids']);rc['researched_artwork_ids']=sorted(set(rc['researched_artwork_ids'])|set(ids));rc['held_artwork_ids']=sorted(set(rc['held_artwork_ids'])|set(ids));rc['pending_artwork_ids']=[a for a in rc['pending_artwork_ids'] if a not in rc['researched_artwork_ids']];rc['next_step']=next_task;r['status']='frozen_25_researched_two_delivered_remaining_unresolved';r['remaining_gaps']=['23 unresolved records in frozen25; some carry leads rather than definitive source holds. No exhaustive museum coverage claim.']
  assert all(a==z for a,z in zip(old['sources'],new['sources']) if a['source_id'] not in changed)
  save('source-queue-before.json',old);tmp=qp.with_name('source-queue.b118.tmp');tmp.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');tmp.replace(qp);assert h.load(qp)==new
  save('independent-queue-verification.json',dict(at=h.now(),unrelated_entries_preserved=True,changed_source_ids=[r['source_id'] for r in new['sources'] if r['source_id'] in changed],basel_unresearched_remaining=0,queue_sha256=h.sha(qp.read_bytes())))
 save('source-register.json',dict(at=h.now(),registry=[r for r in reg if r['source_id'] in changed],policy_reference='docs/ARTLINE_IMAGE_USE.md',directory_coverage_added=0,artwork_research_count=10,access_status='Independent search outputs usable; native multimedia and Commons API holds unchanged'))
 end=h.now();receipt=dict(batch=118,at=end,outcome='no_eligible_candidates',verified_counts=zero,selected=0,prepared=0,imported=0,french_reserve_already_imported=188,basel_newly_researched=10,production_writes=0,local_catalogue_connections=0,prior107_reconciled=True,prior109_reconciled=True,measured_runtime_seconds=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds(),runtime_scope='Measured from first persisted discovery artifact; initial inspection precedes interval',next_task=next_task)
 save('batch-verification-receipt.json',receipt);cp=dict(receipt,status='complete',supervisor_unmodified=True);save('CHECKPOINT.json',cp);h.save(R/'worker-checkpoint.json',cp);print(json.dumps(receipt))
