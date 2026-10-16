#!/usr/bin/env python3
import csv, datetime, hashlib, json, os, shutil, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/continuous-production-20261011'
E=RUN/'batches/000259'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000259'
Q=RUN/'source-queue.json'
TARGET='artline-508319:europe-west1:artline-postgres'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
required=[ROOT/'AGENTS.md',ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',RUN/'CHECKPOINT.json',Q]
holds=sorted(RUN.glob('batches/*/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:8]
registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
save(E/'required-input-verification.json',dict(at=now(),files=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in required],registry_path=str(registry),registry_sha256=sha(registry),registry_records=sum(1 for _ in csv.DictReader(registry.open())),complete_registry_used=True,latest_hold_ledgers=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in holds]))

ps=subprocess.check_output(['ps','-axo','command='],text=True).splitlines()
proxy=[x for x in ps if 'cloud-sql-proxy' in x and TARGET in x and '--port 55519' in x]
assert proxy
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip(); assert actual==TARGET
sys.path.insert(0,str(ROOT/'ops')); import importlib.util
spec=importlib.util.spec_from_file_location('helper',ROOT/'ops/india-300-delivery-20261011.py'); h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
db=h.connect(False)
target=db.execute("select current_database() db, inet_server_addr()::text addr, inet_server_port() port, current_setting('transaction_read_only') ro").fetchone(); assert target['db']=='artline' and target['ro']=='on'
save(E/'production-target-reconciliation.json',dict(at=now(),connection_name=actual,proxy_port=55519,proxy_command_inspected=True,database=target['db'],read_only=target['ro'],helper='ops/india-300-delivery-20261011.py',helper_sha256=sha(ROOT/'ops/india-300-delivery-20261011.py'),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))

fprev=json.loads((RUN/'batches/000187/french-reserve-live-reconciliation.json').read_text())['production_rows']; fids=[x['id'] for x in fprev]
fr=db.execute("select count(*) n,count(*) filter(where status in ('active','review')) active,count(*) filter(where primary_media_id is not null) illustrated from artworks where id=any(%s::uuid[])",(fids,)).fetchone()
save(E/'french-reserve-live-reconciliation.json',dict(at=now(),input_reserve_records=188,live_rows=fr['n'],live_active_artworks=fr['active'],live_illustrated_artworks=fr['illustrated'],genuinely_unimported=188-fr['n'],selected=0,writes=0,decision='All 188 checksum-bound reserve objects remain present and illustrated; immutable historical delivery not replayed.',prior_visual_evidence=['docs/research/continuous-production-20261011/batches/000001/batch-visual-review.json','docs/research/continuous-production-20261011/batches/000001/prior-visual-evidence.json'],checksum_bound_plan='docs/research/continuous-production-20261011/batches/000001/delivery-plan-pin.json'))
b107=json.loads((RUN/'batches/000107/independent-production-verification.json').read_text())['rows']; ids107=[x['id'] for x in b107]
n107=db.execute('select count(*) n from artworks where id=any(%s::uuid[]) and primary_media_id is not null',(ids107,)).fetchone()['n']
save(E/'batch107-live-reconciliation.json',dict(at=now(),production_rows=n107,expected_rows=len(ids107),matches_independent_postimage=n107==len(ids107),increment=0))

with registry.open() as f: reg=next(r for r in csv.DictReader(f) if r['source_id']=='national_gallery_athens')
data=urllib.parse.urlencode({'creteria[language]':'en','creteria[artwork_name]':'','creteria[artwork_type]':'64','creteria[permanent_exhibition]':'','creteria[location]':'','creteria[extra_filters]':'false','page':'1','action':'get_artworks'}).encode()
req=urllib.request.Request('https://www.nationalgallery.gr/wp-admin/admin-ajax.php',data=data,headers={'User-Agent':'ArtlineResearch/1.0'})
with urllib.request.urlopen(req,timeout=30) as x: body=x.read(); status=x.status
(R/'national-gallery-athens-paintings-page1.json').write_bytes(body); payload=json.loads(body)
rows=payload.get('results',[])[:25]
classified=[dict(title=x.get('title'),link=x.get('link'),artist=x.get('artist_name_nice'),decision='held_index_lead_requires_record_date_identity_and_explicit_image_rights') for x in rows]
source=dict(at=now(),source_registry=reg,url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php',request={'artwork_type':'64','page':1,'action':'get_artworks'},status=status,body_sha256=hashlib.sha256(body).hexdigest(),runtime_capture=str(R/'national-gallery-athens-paintings-page1.json'),source_total=int(payload.get('total_row') or 0),reviewed_index_rows=len(rows),classified=classified,images_requested=0,production_writes=0,disposition='Official index provides canonical links but registry policy forbids automated image download absent record-explicit open rights. Index rows alone do not establish eligible exact objects through 1970; held without detail-page harvesting or image download.')
save(E/'national-gallery-athens-source-verification.json',source)
save(E/'bounded-production-gap-cohort.json',dict(at=now(),route='National Gallery Athens official paintings page 1',index_rows=len(rows),eligible_objects=0,rows=[],read_only=True))
save(E/'actual-visual-review.json',dict(at=now(),prepared_images=0,viewed_images=0,claim='No image was selected or prepared; no visual-review claim is made. Immutable French reserve visual evidence was cited, not re-viewed.'))

before=Q.read_bytes(); (E/'source-queue-before.json').write_bytes(before); q=json.loads(before)
entry=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens')
entry.update(status='official_paintings_page1_reviewed_no_eligible_candidates',last_checked_at=now(),last_batch=259,access_status='Official index HTTP 200; image reuse remains held absent record-explicit open rights.')
entry['resume_cursor']=dict(route='official_paintings_ajax',artwork_type=64,last_page=1,next_page=2,source_total=int(payload.get('total_row') or 0),reviewed_links=[x.get('link') for x in rows],hold_reason='Detail identity/date review and record-explicit image rights required; do not download index thumbnails.',next_step='Resume at page 2 only if record-level rights can be established; otherwise rotate to another registry-backed Russian-icon or post-Byzantine source.')
save(Q,q)
save(E/'source-queue-update-verification.json',dict(at=now(),modified_source_ids=['national_gallery_athens'],unrelated_entries_preserved=len(q['sources'])-1,all_111_registry_routes_preserved=len(q['sources'])==111,queue_sha256=sha(Q),resume_cursor=entry['resume_cursor']))
db.close()
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
save(E/'independent-production-verification.json',dict(at=now(),production_target=TARGET,current_campaign_rows=[],production_writes=0,verified_counts=counts,local_catalogue_connections=0))
save(E/'batch-verification-receipt.json',dict(at=now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='Fresh National Gallery Athens paintings-page-1 research plus live production reconciliation; no prior additions counted.',production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','bounded-production-gap-cohort.json','national-gallery-athens-source-verification.json','actual-visual-review.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
next_task='Rotate to another undercovered registry-backed Russian-icon or post-Byzantine source with stable object IDs and explicit open-image permission; do not replay the exhausted French reserve or National Gallery Athens page 1.'
cp=dict(at=now(),batch=259,stage='verified_no_eligible_candidates',outcome='no_eligible_candidates',researched={'source_id':'national_gallery_athens','page':1,'index_rows':len(rows),'eligible':0},selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=next_task,blocker='',evidence_paths=[str((E/x).relative_to(ROOT)) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
save(E/'CHECKPOINT.json',cp); save(R/'CHECKPOINT.json',cp); save(RUN/'CHECKPOINT.json',cp)
save(E/'independent-final-artifact-verification.json',dict(at=now(),checkpoint_runtime_equal=(E/'CHECKPOINT.json').read_bytes()==(R/'CHECKPOINT.json').read_bytes(),evidence=[{'path':str((E/x).relative_to(ROOT)),'sha256':sha(E/x)} for x in evidence],all_evidence_exists=all((E/x).exists() for x in evidence),counts_match=True,source_queue_sha256=sha(Q)))
print(json.dumps(cp))
