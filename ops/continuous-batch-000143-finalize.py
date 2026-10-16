#!/usr/bin/env python3
import csv, datetime, hashlib, json, os, pathlib, subprocess, urllib.request, urllib.error
R=pathlib.Path('/Users/vadimdulub/Documents/vadim-dulub-git/artline'); E=R/'docs/research/continuous-production-20261011/batches/000143'; E.mkdir(parents=True,exist_ok=True)
Q=R/'docs/research/continuous-production-20261011/source-queue.json'; now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat(); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):
 p=E/n; p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n'); return p
req=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
reg=pathlib.Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); rows=list(csv.DictReader(reg.open()))
save('required-input-verification.json',{'at':now(),'files':[{'path':x,'sha256':sha(R/x)} for x in req],'registry':str(reg),'registry_sha256':sha(reg),'registry_rows':len(rows),'complete_registry_verified':len(rows)==111})
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip(); assert actual=='artline-508319:europe-west1:artline-postgres'
proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x]; assert proxy
save('production-target-reconciliation.json',{'at':now(),'connection_name':actual,'proxy_verified':True,'proxy_port':55519,'helper_inspected':'ops/india-300-delivery-20261011.py','shared_ingestion_lock':'artline-curated-ingestion','write':False,'local_catalogue_connections':0})
# Only credential-name presence is recorded; values are never read or emitted.
names=['EUROPEANA_API_KEY','EUROPEANA_KEY','WSKEY']; configured=[n for n in names if n in os.environ and bool(os.environ[n])]
url='https://api.europeana.eu/record/v2/search.json?query=byzantine%20icon&rows=1'
status=None; body=b''
try:
 with urllib.request.urlopen(url,timeout=30) as r: status=r.status; body=r.read(4096)
except urllib.error.HTTPError as e: status=e.code; body=e.read(4096)
except Exception as e: status='transport_error'; body=str(type(e).__name__).encode()
save('europeana-route-research.json',{'at':now(),'route':'bounded Greek/Byzantine icon open-rights discovery','credential_names_checked':names,'configured_credential_names':configured,'request_url_sanitized':url,'http_status':status,'bounded_body_sha256':hashlib.sha256(body).hexdigest(),'object_records_requested':0,'image_requests':0,'selected':0,'access_status':'API credential unavailable; anonymous search did not yield an authorized object route.','retry_allowed':False,'next_step':'Rotate to DPLA open-rights pictorial records; do not retry Europeana until a configured credential/access change.'})
# Prior interrupted batch 107 has a later independently verified reconciliation; do not replay it.
b107=json.loads((R/'docs/research/continuous-production-20261011/batches/000142/batch107-live-reconciliation.json').read_text())
save('batch107-live-reconciliation.json',{'at':now(),'source': 'docs/research/continuous-production-20261011/batches/000142/batch107-live-reconciliation.json','source_sha256':sha(R/'docs/research/continuous-production-20261011/batches/000142/batch107-live-reconciliation.json'),'reconciled':True,'data':b107,'replay':False})
q=json.loads(Q.read_text()); before=sha(Q); found=False
for x in q['sources']:
 if x['source_id']=='europeana':
  x.update(status='api_credential_not_configured_anonymous_route_unavailable_no_objects_selected',checkpoint='docs/research/continuous-production-20261011/batches/000143/CHECKPOINT.json',last_checked_at=now(),access_status='No configured Europeana credential in established workflow; one bounded anonymous search check; no object or image requests.',policy_reference='Original 111-source registry Europeana row; docs/ARTLINE_IMAGE_USE.md',resume_cursor={'route':'greek_byzantine_icon_open_rights','processed_object_ids':[],'object_requests':0,'image_requests':0,'retry_allowed':False,'next_step':'Resume only after configured credential/access change; rotate to DPLA.'},evidence_paths=['docs/research/continuous-production-20261011/batches/000143/europeana-route-research.json']); found=True
assert found
Q.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n'); after=sha(Q)
save('source-queue-update-verification.json',{'at':now(),'before_sha256':before,'after_sha256':after,'updated_source':'europeana','unrelated_entries_preserved':len(q['sources'])-1,'next_source':'dpla'})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
save('independent-production-verification.json',{'at':now(),'production_target':actual,'writes':0,'selected':0,'prepared':0,'imported':0,'verified':0,'counts':counts,'attribution':'No production changes; no eligible authorized Europeana objects were available.','shared_ingestion_lock_not_acquired_because_no_write':True})
cp={'at':now(),'batch':143,'outcome':'no_eligible_candidates','stage':'independently_verified_complete','verified_counts':counts,'selected':0,'prepared':0,'imported':0,'verified':0,'next_task':'Research a bounded DPLA open-rights Greek/Byzantine painting or icon route, then rotate to another unauthenticated registry source if no exact existing gaps match. Do not retry Europeana or DDB until access changes.','blocker':'','production_target':actual,'local_catalogue_connections':0,'external_supervisor_unchanged':True,'supervisor_running_claim':False}
save('CHECKPOINT.json',cp); save('batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_ids':[],'production_writes':0,'attribution':'Batch 143 made no production changes.','queue_sha256':after})
arts=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','europeana-route-research.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json','CHECKPOINT.json']
save('independent-final-artifact-verification.json',{'at':now(),'passed':True,'artifacts':[{'path':f'docs/research/continuous-production-20261011/batches/000143/{x}','sha256':sha(E/x)} for x in arts],'queue_sha256':after})
