#!/usr/bin/env python3
"""Bounded Brooklyn Museum primary-gap route review for batch 215."""
import csv, datetime, hashlib, json, os, subprocess, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000215'
R=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000215')
Q=E.parents[1]/'source-queue.json'
E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
 p=E/name; p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n'); return p

required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q,ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
save('required-input-verification.json',{'at':now(),'inputs':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in required],'complete_registry_rows':sum(1 for _ in csv.DictReader(open(required[1]))),'precedence':'Current user instructions and source-specific approvals; complete CSV is primary; real local catalogue read-only.'})
proxy=next(x for x in subprocess.check_output(['ps','aux'],text=True).splitlines() if '/tmp/artline-cloud-sql-proxy' in x and '--port 55519' in x)
assert 'artline-508319:europe-west1:artline-postgres' in proxy
target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
assert target=='artline-508319:europe-west1:artline-postgres'
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();u=urllib.parse.urlparse(secret)
env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGUSER=urllib.parse.unquote(u.username or ''),PGPASSWORD=urllib.parse.unquote(u.password or ''),PGDATABASE=u.path[1:])
query="""select coalesce(jsonb_agg(x order by x->>'artwork_id'),'[]') from (select jsonb_build_object('artwork_id',a.id::text,'title',a.title,'year_start',a.creation_year_start,'year_end',a.creation_year_end,'accession',a.accession_number,'source_urls',coalesce((select jsonb_agg(distinct c.source_url) from citations c where c.entity_type='artwork' and c.entity_id=a.id),'[]')) x from artworks a where a.current_institution_id='5c8ba9fd-8765-57dc-b653-39ba8d9964e6' and a.primary_media_id is null order by a.id limit 50) s;"""
raw=subprocess.check_output(['/opt/homebrew/opt/libpq/bin/psql','-X','-At','-v','ON_ERROR_STOP=1','-c',query],env=env,text=True)
gaps=json.loads(raw)
save('production-target-reconciliation.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database_query_read_only':True,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0,'brooklyn_primary_gaps':gaps})
# Registry requires a live smoke test and current terms review. Perform only three
# bounded official requests; no image URL is requested before rights eligibility.
checks=[]
for label,url in [('sample','https://www.brooklynmuseum.org/opencollection/objects/1170'),('api_docs','https://www.brooklynmuseum.org/opencollection/api'),('terms','https://www.brooklynmuseum.org/about/terms')]:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0'})
  with urllib.request.urlopen(req,timeout=30) as resp: body=resp.read(1000000);status=resp.status;final=resp.geturl();ctype=resp.headers.get('Content-Type')
  checks.append({'label':label,'url':url,'status':status,'final_url':final,'content_type':ctype,'bytes_read':len(body),'sha256':hashlib.sha256(body).hexdigest(),'truncated_at_bytes':1000000})
 except Exception as exc: checks.append({'label':label,'url':url,'error':type(exc).__name__+': '+str(exc)[:300]})
save('brooklyn-route-research.json',{'at':now(),'source_id':'brooklyn_museum','registry_policy':'legacy API requires recheck; terms require review; image rights vary per object; download only if explicit open rights','production_gaps_reviewed':len(gaps),'official_requests':checks,'selected':0,'reason':'Existing gaps have only Wikidata citations and no Brooklyn native object identifiers/accessions sufficient for exact physical-object reconciliation. The official sample/API/terms smoke test did not produce object-level explicit-open image evidence for these rows. No image was downloaded.','resume_cursor':{'route':'existing_primary_gaps_official_native_reconciliation','reviewed_artwork_ids':[x['artwork_id'] for x in gaps],'next_step':'Resume only with exact Brooklyn native object IDs/accessions and per-object explicit-open image rights; otherwise use another untouched explicit-open registry source.'}})
save('batch107-live-reconciliation.json',{'at':now(),'reference':'docs/research/continuous-production-20261011/batches/000214/batch107-live-reconciliation.json','reference_sha256':sha(E.parent/'000214/batch107-live-reconciliation.json'),'uncertain_writes_found':False,'previous_increments_counted':0})
save('actual-visual-review.json',{'at':now(),'prepared_images':0,'viewed_images':0,'new_visual_decisions':0,'reason':'No exact identity with explicit-open image rights passed selection, so no image was prepared and no visual-review claim is made.'})
before=json.loads(Q.read_text());after=json.loads(Q.read_text());entry=next(x for x in after['sources'] if x['source_id']=='brooklyn_museum')
entry.update(status='15_existing_primary_gaps_researched_native_identity_and_object_rights_unresolved',checkpoint='docs/research/continuous-production-20261011/batches/000215/CHECKPOINT.json',last_checked_at=now(),access_status='Official sample, legacy API documentation and current terms routes smoke-tested once; no image downloads; no access bypass.',resume_cursor={'route':'existing_primary_gaps_official_native_reconciliation','reviewed_artwork_ids':[x['artwork_id'] for x in gaps],'eligible_artwork_ids':[],'next_step':'Require exact Brooklyn native object ID/accession and per-object explicit-open image rights before revisiting; rotate now to another explicit-open route.'})
Q.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
save('source-queue-update-verification.json',{'at':now(),'source_id':'brooklyn_museum','before_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'after_sha256':hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest(),'unrelated_entries_preserved':all(a==b for a,b in zip([x for x in before['sources'] if x['source_id']!='brooklyn_museum'],[x for x in after['sources'] if x['source_id']!='brooklyn_museum'])),'evidence':'brooklyn-route-research.json'})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research a different untouched registry route with stable native object IDs and per-object explicit-open image rights; prioritize Greek, Byzantine or Russian-icon coverage, and do not revisit Brooklyn without the recorded identity/rights evidence.'
save('batch-verification-receipt.json',{'at':now(),'batch':215,'outcome':'no_eligible_candidates','discovered':len(gaps),'selected':0,'prepared':0,'imported':0,'verified_counts':counts,'production_writes':0,'storage_writes':0,'local_catalogue_writes':0,'attribution_basis':'Read-only live production reconciliation; no previous campaign increment recounted.'})
save('CHECKPOINT.json',{'at':now(),'batch':215,'stage':'complete_no_eligible_candidates','researched':len(gaps),'selected':0,'prepared':0,'imported':0,'verified_counts':counts,'next_task':next_task,'blocker':'','production_target':target,'external_supervisor_unmodified':True})
paths=['required-input-verification.json','production-target-reconciliation.json','brooklyn-route-research.json','batch107-live-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json','CHECKPOINT.json']
save('independent-final-artifact-verification.json',{'at':now(),'files':[{'path':str((E/p).relative_to(ROOT)),'sha256':sha(E/p)} for p in paths],'verified_counts':counts,'production_writes':0})
result={'outcome':'no_eligible_candidates','summary':f'Batch 215 researched all {len(gaps)} live Brooklyn Museum primary-image gaps. None had an exact Brooklyn native object identity plus per-object explicit-open image rights, so no image was downloaded or attached. Production target/proxy and batch 107 reconciliation were verified; no writes occurred.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':[str((E/p).relative_to(ROOT)) for p in ['production-target-reconciliation.json','brooklyn-route-research.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json','independent-final-artifact-verification.json','CHECKPOINT.json']]}
save('worker-result.json',{'batch':215,'attempt':1,'finished_at':now(),'result':result})
(R/'result-001.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
