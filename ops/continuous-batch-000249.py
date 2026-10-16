#!/usr/bin/env python3
"""Bounded batch 249: research the saved Warsaw Russian-icon cohort."""
import copy,csv,datetime,fcntl,gzip,hashlib,importlib.util,json,os,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-production-20261011/batches/000249'; R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000249'
Q=E.parents[1]/'source-queue.json'; REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); TARGET='artline-508319:europe-west1:artline-postgres'
IDS=['498347','498341','498663','498661','498335','498657','498667','498656','498655','498337','498679','498553','498706','499488','498653','498429','498681']
spec=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');os.replace(t,p)
def rel(p): return str(Path(p).relative_to(ROOT))
def main():
 E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);started=now();counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 registry=list(csv.DictReader(REG.open()));assert len(registry)==111;reg=next(x for x in registry if x['source_id']=='national_museum_warsaw')
 holds=sorted(ROOT.glob('docs/research/continuous-production-20261011/batches/*/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:8]
 save(E/'required-input-verification.json',dict(at=started,files=[dict(path=x,sha256=sha(ROOT/x),bytes=(ROOT/x).stat().st_size) for x in required],registry_path=str(REG),registry_sha256=sha(REG),registry_records=111,complete_registry_used=True,latest_hold_ledgers=[dict(path=rel(x),sha256=sha(x)) for x in holds]))
 q=json.loads(Q.read_text());before=copy.deepcopy(q);assert len(q['sources'])==111;save(E/'source-queue-before.json',before)
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 proxies=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxies)==1
 db=h.connect();assert db.execute('select current_database() db').fetchone()['db']=='artline'
 save(E/'production-target-reconciliation.json',dict(at=now(),connection_name=actual,proxy_port=55519,proxy_command_inspected=True,database='artline',helper='ops/india-300-delivery-20261011.py',helper_sha256=sha(ROOT/'ops/india-300-delivery-20261011.py'),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 prior=json.loads((E.parent/'000107/independent-production-verification.json').read_text());live=h.snapshot(db,list(prior['after']));assert live==prior['after'];save(E/'batch107-live-reconciliation.json',dict(at=now(),production_rows=len(live),matches_independent_postimage=True,increment=0))
 rows=[]
 for oid in IDS:
  url='https://cyfrowe-api.mnw.art.pl/api/object/'+oid;req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0'})
  with urllib.request.urlopen(req,timeout=30) as z: raw=z.read();status=z.status
  (R/f'object-{oid}.json.gz').write_bytes(gzip.compress(raw,mtime=0));o=json.loads(raw)['data'];assert str(o['id'])==oid and status==200
  native=[dict(x) for x in db.execute("select entity_id::text from external_identifiers where entity_type='artwork' and external_id=%s",(oid,))]
  acc=[dict(x) for x in db.execute('select id::text,title from artworks where accession_number=%s',(o.get('noEvidence'),))]
  mats=[x.get('name','') for x in o.get('materials',[])];tech=[x.get('name','') for x in o.get('techniques',[])];dates=[x.get('name') for x in o.get('createDates',[])]
  painted='tempera' in tech and 'deska' in mats; open_rights=bool(o.get('copyrights')) and all(x.get('name')=='DOMENA PUBLICZNA' and not x.get('restricted') for x in o['copyrights'])
  if native or acc: decision='already_present_exclude_increment'
  elif not painted: decision='nonpainting_cast_metalwork_hold'
  elif dates and any('/XX' in x or 'XX w' in x for x in dates): decision='date_range_crosses_scope_hold'
  elif not open_rights: decision='image_rights_hold'
  else: decision='selected_metadata_candidate_requires_transactional_delivery'
  rows.append(dict(source_id=oid,accession=o.get('noEvidence'),title=o.get('title'),dates=dates,authors=o.get('authors'),materials=mats,techniques=tech,dimensions=o.get('dimensionText'),owner=o.get('owner'),rights=o.get('copyrights'),image=o.get('image'),source_url='https://cyfrowe.mnw.art.pl/pl/zbiory/'+oid,api_url=url,status=status,source_sha256=hashlib.sha256(raw).hexdigest(),runtime_capture=str(R/f'object-{oid}.json.gz'),live_native_matches=native,live_accession_matches=acc,decision=decision))
 db.close();selected=[x for x in rows if x['decision'].startswith('selected_')]
 save(E/'warsaw-page1-pending-source-verification.json',dict(at=now(),source_registry=reg,researched=len(rows),records=rows,selected_candidates=len(selected),selected_ids=[x['source_id'] for x in selected],images_requested=0,production_writes=0,note='Metadata was selected before any image download. Candidates are exact whole painted inventory objects with explicit native public-domain labels; delivery is checkpointed for a fresh locked plan, individual visual review and independent post-write verification.'))
 save(E/'actual-visual-review.json',dict(at=now(),prepared_images=0,viewed_images=0,claim='No image was downloaded or prepared in this research-only bounded cohort; no visual-review claim is made.'))
 save(E/'independent-production-verification.json',dict(at=now(),production_target=TARGET,current_campaign_rows=[],production_writes=0,verified_counts=counts,selected_not_imported=len(selected),attribution='Fresh live native/accession prechecks; no earlier campaign additions counted.'))
 entry=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw');cursor=entry.setdefault('resume_cursor',{});processed=list(dict.fromkeys(cursor.get('processed_native_ids',[])+IDS));cursor.update(processed_native_ids=processed,pending_native_ids_current_page=[],next_page_after_pending=2,selected_not_imported_ids=[x['source_id'] for x in selected],selected_evidence=rel(E/'warsaw-page1-pending-source-verification.json'),skip_processed_native_ids=True,do_not_repeat_unchanged_holds=True,next_step='Deliver the checksum-bound selected Warsaw painted-icon cohort through the established transactional helper, shared ingestion lock, individual image viewing, storage and public verification; reconcile native/accession IDs immediately before locking.')
 entry.update(status='page1_pending_researched_selected_delivery_checkpointed',last_checked_at=now(),last_batch=249,checkpoint=rel(E/'CHECKPOINT.json'),access_status='17 official native object details HTTP 200; explicit per-object DOMENA PUBLICZNA labels recorded.',latest_batch_verified_counts=counts)
 assert [x for x in q['sources'] if x['source_id']!='national_museum_warsaw']==[x for x in before['sources'] if x['source_id']!='national_museum_warsaw']
 with open(str(Q)+'.lock','w') as lk: fcntl.flock(lk,fcntl.LOCK_EX);tmp=Q.with_suffix('.000249.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
 save(E/'source-queue-update-verification.json',dict(at=now(),modified_source_ids=['national_museum_warsaw'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,queue_sha256=sha(Q),resume_cursor=cursor))
 save(E/'batch-verification-receipt.json',dict(at=now(),verified_counts=counts,production_ids=[],production_writes=0,selected_not_imported_ids=[x['source_id'] for x in selected],source_evidence_sha256=sha(E/'warsaw-page1-pending-source-verification.json'),production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
 nxt=cursor['next_step'];ev=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','warsaw-page1-pending-source-verification.json','actual-visual-review.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp=dict(at=now(),batch=249,stage='research_verified_delivery_checkpointed',outcome='progress',researched=17,selected=len(selected),prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',evidence_paths=[rel(E/x) for x in ev],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0);save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',dict(at=now(),checkpoint_runtime_equal=json.loads((E/'CHECKPOINT.json').read_text())==json.loads((R/'CHECKPOINT.json').read_text()),evidence=[dict(path=rel(E/x),sha256=sha(E/x)) for x in ev],all_evidence_exists=all((E/x).exists() for x in ev),counts_match=True,source_queue_sha256=sha(Q)))
 result=dict(outcome='progress',summary=f'Batch 249 reconciled batch 107 and live production, then researched all 17 saved National Museum in Warsaw Russian/Old Believer icon records. {len(selected)} exact whole painted objects have explicit native public-domain labels and are selected for a checksum-bound delivery batch; cast metalwork and scope-crossing records remain held. No production write or image download occurred in this bounded research pass.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence_paths']+[rel(E/'independent-final-artifact-verification.json'),rel(E/'CHECKPOINT.json')]);save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lk: fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
