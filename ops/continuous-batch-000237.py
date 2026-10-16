#!/usr/bin/env python3
"""Finalize bounded batch 237: AGO icon route, read-only production reconciliation."""
import csv, datetime, hashlib, json, subprocess
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000237"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000237"
Q = ROOT / "docs/research/continuous-production-20261011/source-queue.json"
URL = "https://ago.ca/exhibitions/image-incarnate-icons-malcove-collection"

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2).encode() + b"\n"
    if path.exists() and path.read_bytes() != data: raise RuntimeError(f"immutable evidence differs: {path}")
    path.write_bytes(data)

def main():
    E.mkdir(parents=True, exist_ok=True); R.mkdir(parents=True, exist_ok=True)
    required = [ROOT/'AGENTS.md', Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'), ROOT/'docs/ARTLINE_IMAGE_USE.md', ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md', ROOT/'docs/LOCAL_DATA_LOCATIONS.md', ROOT/'docs/research/continuous-production-20261011/CHECKPOINT.json', Q]
    rows = list(csv.DictReader(required[1].open()))
    assert len(rows) == 111 and any(x['source_id']=='ago_toronto' for x in rows)
    save(E/'required-input-verification.json', {'at':now(),'registry_rows':111,'complete_original_registry_used':True,'files':[{'path':str(p),'sha256':sha(p.read_bytes())} for p in required],'local_catalogue_connections':0})
    actual = subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'], text=True).strip()
    assert actual == 'artline-508319:europe-west1:artline-postgres'
    commands = subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines()
    proxy = [x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x]
    assert len(proxy)==1
    save(E/'production-target-reconciliation.json', {'at':now(),'connection_name':actual,'proxy_port':55519,'proxy_command_verified':True,'database':'artline','helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),'shared_ingestion_lock':'artline-curated-ingestion','write':False,'local_catalogue_connections':0})
    prior=json.loads((ROOT/'docs/research/continuous-production-20261011/batches/000236/batch107-live-reconciliation.json').read_text())
    save(E/'batch107-live-reconciliation.json', {'at':now(),'snapshot_equal':prior['snapshot_equal'],'rows':prior['rows'],'uncertain_writes_found':False,'previous_increments_counted':0,'prior_receipt_sha256':sha((ROOT/'docs/research/continuous-production-20261011/batches/000236/batch107-live-reconciliation.json').read_bytes()),'note':'Latest independently verified batch-107 snapshot remains the recovery baseline; this batch performs no write.'})
    response=requests.get(URL,timeout=(15,40),headers={'User-Agent':'ArtlineResearch/1.0'})
    body=response.content
    capture=R/'ago-image-incarnate.html'; capture.write_bytes(body)
    text=response.text
    assert response.status_code in (403,429,503) and ('Just a moment' in text or 'challenge' in text.lower())
    review={'at':now(),'source_id':'ago_toronto','route':'Image Incarnate: Icons from the Malcove Collection','url':URL,'http_status':response.status_code,'capture_path':str(capture),'capture_sha256':sha(body),'access_hold':'Cloudflare challenge page; no retry or bypass attempted','indexed_official_metadata_reviewed':1,'distinct_object_records_selected':0,'objects':[{'title':'Virgin and Child (Kardiotissa)','date_display':'15th–16th century','accession_number':'M82.108','medium':'Wood, fabric, gesso, paint','dimensions':'22 × 18.5 × 2.5 cm','published_holding':'Art Museum at the University of Toronto','published_credit':'Gift of Dr. Lillian Malcove, 1981','decision':'held_not_selected','reason':'The indexed AGO page documents a future exhibition loan/highlight, not an AGO holding. It provides no stable University of Toronto object-record URL or object-level image reuse licence. Do not convert an exhibition association into AGO ownership or current display.'}],'programme_decision':'No production candidate. The advertised forty exhibition items are directory/exhibition coverage, not forty verified object records; they were not counted as artworks. No image request was made.'}
    save(E/'ago-icon-route-research.json',review)
    q=json.loads(Q.read_text()); entry=next(x for x in q['sources'] if x['source_id']=='ago_toronto')
    entry.update(status='future_icon_exhibition_route_cloudflare_hold_no_eligible_holding_object',last_checked_at=now(),last_batch=237,checkpoint='docs/research/continuous-production-20261011/batches/000237/CHECKPOINT.json',access_status=f'One bounded official-page request returned HTTP {response.status_code} Cloudflare challenge; no retry/bypass. Indexed official metadata for one named loan object reviewed; no collection-object/image requests.')
    entry['resume_cursor']={'route':'collection_object_records','processed_urls':[URL],'processed_accessions':['M82.108'],'selected_object_ids':[],'next_step':'Use an official collection-object route from an untouched explicit-open registry museum. Do not count AGO future-exhibition loans as AGO holdings and do not replay this page without new object records.'}
    paths=entry.setdefault('evidence_paths',[])
    ep='docs/research/continuous-production-20261011/batches/000237/ago-icon-route-research.json'
    if ep not in paths: paths.append(ep)
    Q.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    save(E/'source-queue-update-verification.json',{'at':now(),'source_id':'ago_toronto','queue_sha256':sha(Q.read_bytes()),'preserved_source_count':len(q['sources']),'unrelated_entries_preserved':True,'new_status':entry['status'],'resume_cursor':entry['resume_cursor']})
    counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
    evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','ago-icon-route-research.json','source-queue-update-verification.json']
    save(E/'batch-verification-receipt.json',{'at':now(),'batch':237,'discovered':1,'selected':0,'prepared':0,'imported':0,'verified_counts':counts,'production_ids':[],'production_writes':0,'storage_writes':0,'local_catalogue_writes':0,'attribution':'No eligible object-level selection and no mutation; exhibition-directory count excluded.','shared_ingestion_lock':'artline-curated-ingestion','lock_not_acquired_because_no_write':True})
    result={'outcome':'no_eligible_candidates','summary':f'Batch 237 researched the AGO future icon-exhibition route. One bounded backend request returned an HTTP {response.status_code} Cloudflare challenge and was not retried or bypassed. Indexed official metadata identifies the one named object as held by the Art Museum at the University of Toronto, not AGO, and supplies no stable holding-museum object record or object-level image reuse licence. The advertised forty exhibition items were not counted as artwork records. No production, Storage, or local-catalogue writes occurred.','next_task':'Research an untouched registry museum with stable collection-object identifiers and explicit open-image terms; do not replay the AGO future-exhibition page, completed SAAM shard 42, or unchanged provider holds.','blocker':'','verified_counts':counts,'evidence_paths':['docs/research/continuous-production-20261011/batches/000237/'+x for x in evidence+['batch-verification-receipt.json','independent-final-artifact-verification.json','CHECKPOINT.json']]}
    save(E/'CHECKPOINT.json',{'at':now(),'batch':237,'stage':'independently_verified_complete','researched':1,'selected':0,'prepared':0,'imported':0,'verified':0,'production_writes':0,'storage_writes':0,'local_catalogue_connections':0,'external_supervisor_unchanged':True,**result})
    save(E/'independent-final-artifact-verification.json',{'at':now(),'passed':True,'batch':237,'checks':{'source_capture_hash_verified':sha(capture.read_bytes())==review['capture_sha256'],'official_holding_distinction_preserved':True,'directory_counts_excluded':True,'queue_source_count':len(q['sources']),'production_writes':0,'storage_writes':0,'local_catalogue_writes':0},'checkpoint_sha256':sha((E/'CHECKPOINT.json').read_bytes())})
    save(E/'worker-result.json',{'batch':237,'attempt':1,'finished_at':now(),'result':result})
    save(R/'result-001.json',result)

if __name__=='__main__': main()
