"""One bounded worker setup: evidence reuse and read-only production recovery."""
import csv, datetime, gzip, hashlib, importlib.util, json, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000273'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000273'
PRE=E.parent/'000271'
for p in [E,R,E/'source-captures',E/'objects']:p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(n,x):
 p=E/n
 if not p.exists():p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
contents={str(p):p.read_text() for p in required}
registry=list(csv.DictReader(required[1].open()));q=load(required[-1]);assert len(registry)==len(q['sources'])==111
save('required-input-verification.json',dict(at=now(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in required],original_registry_rows=111,supplementary_review_not_substituted=True,local_catalogue_connections=0))
save('original-source-registry.json',dict(at=now(),source_csv=str(required[1]),sha256=sha(required[1]),rows=registry))
ledgers=sorted(E.parent.glob('*/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:10]
save('inherited-holds-verification.json',dict(at=now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),content=load(p)) for p in ledgers],recorded_provider_holds=[dict(source_id=x['source_id'],status=x['status'],access_status=x.get('access_status')) for x in q['sources'] if any(k in str(x.get('status','')).lower() for k in ['hold','403','429','blocked'])],berlin_prior_held_ids=next(x for x in q['sources'] if x['source_id']=='staatliche_museen_berlin')['resume_cursor']['held_object_ids'],unchanged_held_provider_requests=0))
files=['source-captures/booklet.receipt.json']+[f'{folder}/{stem}{oid}{suffix}' for oid in ['1787232','1787229','1792596','1757016','1787240','1791012'] for folder,stem,suffix in [('objects','','.json'),('source-captures','object-','.receipt.json')]]
for f in files:
 if not(E/f).exists():shutil.copyfile(PRE/f,E/f)
 rc=load(E/f)
 if 'body_path' in rc:
  p=Path(rc['body_path']);raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256']
save('source-reuse-verification.json',dict(at=now(),prior_batch=271,files=[dict(source=str((PRE/f).relative_to(ROOT)),copy=str((E/f).relative_to(ROOT)),sha256=sha(E/f)) for f in files],raw_body_checksums_verified=True,new_native_object_requests=0,reason='Captured within this morning; immutable raw evidence reused, not counted as fresh discovery.'))
pdf=load(E/'source-captures/booklet.receipt.json');text=subprocess.check_output(['pdftotext',pdf['body_path'],'-'],text=True)
save('booklet-text-review.json',dict(at=now(),source_sha256=pdf['sha256'],pages=[dict(pdf_page=n+1,text=p) for n,p in enumerate(text.split('\f')) if n+1 in [11,12,16]],demetrios_inventory_9638_in_full_text='9638' in text,source_label_conflicts={'1791012':'Native 16th century; booklet no.21 15th century. Held.','1792596':'Native 18th century is within booklet 17th/18th century; broader 1601–1800 union retained with both original labels.'}))
viewed=[]
for n in [11,12,16]:
 src=Path('/tmp/artline-b273-pdf')/f'page-{n}.png';dest=R/f'booklet-page-{n}.png'
 if not dest.exists():shutil.copyfile(src,dest)
 viewed.append(dict(pdf_page=n,path=str(dest),sha256=sha(dest),actually_viewed=True,tool='view_image'))
save('booklet-visual-review.json',dict(at=now(),source_sha256=pdf['sha256'],pages=viewed,decision='Exact catalogue inventory, front composition and provenance checked. Source differences remain explicit; no current custody/display claim.'))
s=importlib.util.spec_from_file_location('old','ops/continuous-berlin-batch-000271.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old);h=old.h
save('production-target-reconciliation.json',old.target())
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 for batch in [107,271,272]:
  p=E.parent/f'{batch:06d}'/'independent-production-verification.json';prior=load(p);before=prior.get('after',prior.get('rows'));assert isinstance(before,dict),(batch,list(prior))
  live=h.snapshot(db,list(before));assert live==before,('Recovery drift',batch)
  save(f'batch{batch}-live-reconciliation.json',dict(at=now(),prior_receipt=str(p.relative_to(ROOT)),prior_receipt_sha256=sha(p),matched_rows=len(live),matches_verified_postimage=True,uncertain_writes_found=False,prior_increments_counted=0))
 # All spellings searched across names and aliases, including archived records.
 artists=[dict(x) for x in db.execute("SELECT DISTINCT a.id::text,a.display_name,a.birth_year,a.death_year,a.status FROM artists a LEFT JOIN artist_aliases al ON al.artist_id=a.id WHERE a.display_name ~* 'pitzam|pizam|bitzam|bizzam|bizam|πιτζα|μπιτζ|пицам|бицам|бизам' OR al.alias ~* 'pitzam|pizam|bitzam|bizzam|bizam|πιτζα|μπιτζ|пицам|бицам|бизам' LIMIT 50")]
 save('creator-reconciliation.json',dict(at=now(),candidates=artists,query_scope='Global artist names and aliases including archived; spelling and transliteration variants',booklet_name='Angelo Bizzamano',booklet_signature='Angelus Bizzamanus pinxit in Hotranto',official_authority_url='https://art.thewalters.org/object/37.748/',official_authority_name='Angelos Bitzamanos',official_authority_signature='Angelus Bizamanus Gr(a)ecus Ca(n)diotus pinxit a Otranto',basis='Same distinctive signed name, documented Cretan apprenticeship and Otranto practice; existing Walters authority; death-year disagreement1532/1535 preserved, biography unchanged.',new_painters=0))
save('CHECKPOINT-inflight.json',dict(at=now(),batch=273,stage='recovery_and_six_candidate_review',selected_object_ids=['1787229','1792596','1757016','1787240'],held_object_ids=['1787232','1791012'],next_action='Pin eligible source records, prepare and visually review exact PDM images before writes',external_supervisor_unchanged=True))
print('Required inputs, six source notices, PDF review and previous production writes reconciled.')
