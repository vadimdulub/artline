#!/usr/bin/env python3
"""Bounded Whitney metadata reconciliation for continuous-production batch 264."""
import copy, csv, fcntl, gzip, importlib.util, io, json, os, subprocess
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
E=ROOT/'docs/research/continuous-production-20261011/batches/000264'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000264'
TARGET='artline-508319:europe-west1:artline-postgres'
for p in (E,R,E/'source-captures'):p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name;p.parent.mkdir(parents=True,exist_ok=True);data=json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n'
 if p.exists(): assert p.read_text()==data
 else:p.write_text(data)
 return v
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxy=[x for x in cmds if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxy)==1
 with h.connect() as db: server=dict(db.execute('select current_database() database,pg_is_in_recovery() recovery').fetchone())
 assert server=={'database':'artline','recovery':False};return save('production-target-verification.json',{'at':h.now(),'connection_name':actual,'proxy_command':proxy[0],'database':server,'helper':'ops/india-300-delivery-20261011.py','shared_ingestion_lock':'artline-curated-ingestion','writes':0})
def main():
 started=h.now();target();reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(reg.open()));assert len(registry)==111
 qp=E.parents[1]/'source-queue.json';queue=h.load(qp);assert len(queue['sources'])==111
 required=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',qp]
 save('required-input-verification.json',{'at':h.now(),'files':[{'path':str(x),'sha256':h.sha(x.read_bytes())} for x in required],'original_registry_rows':111,'real_local_catalogue_read_only':True})
 prev=E.parent/'000107/independent-production-verification.json';pv=h.load(prev)
 with h.connect() as db: live=h.snapshot(db,list(pv['after']))
 assert live==pv['after'];save('batch107-live-reconciliation.json',{'at':h.now(),'snapshot_equal':True,'rows':len(live),'previous_increments_counted':0,'receipt_sha256':h.sha(prev.read_bytes())})
 url='https://raw.githubusercontent.com/whitneymuseum/open-access/main/artworks.csv';resp=requests.get(url,timeout=(15,60));resp.raise_for_status();raw=resp.content
 body=E/'source-captures/whitney-artworks.csv.gz';body.write_bytes(gzip.compress(raw,mtime=0))
 save('source-captures/whitney-artworks.receipt.json',{'url':url,'final_url':resp.url,'status':resp.status_code,'retrieved_at':h.now(),'sha256':h.sha(raw),'bytes':len(raw),'body_path':str(body.relative_to(ROOT)),'retry_after':resp.headers.get('Retry-After')})
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));cols=rows[0].keys();candidates=[];excluded={}
 for r in rows:
  classification=(r.get('classification') or r.get('Classification') or '').lower();date=(r.get('date') or r.get('display_date') or r.get('Date') or '')
  years=[int(x) for x in __import__('re').findall(r'(?<!\d)(1[0-9]{3}|200[0-9])(?!\d)',date)]
  reason=None
  if 'painting' not in classification:reason='not_classified_painting'
  elif not years:reason='date_unresolved'
  elif max(years)>1970:reason='post_1970_or_crossing_cutoff'
  if reason:excluded[reason]=excluded.get(reason,0)+1;continue
  candidates.append(r)
  if len(candidates)==50:break
 decisions=[]
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  for r in candidates:
   wid=str(r.get('id') or r.get('ID'));title=r.get('title') or r.get('Title');acc=r.get('accession_number') or r.get('Accession Number');artist=r.get('artists') or r.get('display_artist_text') or r.get('Artist')
   ext=[dict(x) for x in db.execute("select entity_id::text from external_identifiers where entity_type='artwork' and scheme='whitney-object' and external_id=%s",(wid,))]
   exact=[dict(x) for x in db.execute("select id::text,title,accession_number,current_institution_id::text,status from artworks where normalized_title=%s and status<>'archived'",(h.norm(title),))]
   if ext:decision='already_reconciled_by_native_id'
   elif len([x for x in exact if x['accession_number']==acc])==1:decision='existing_exact_accession_needs_native_identifier_review'
   else:decision='new_metadata_candidate_requires_creator_and_global_identity_review'
   decisions.append({'native_id':wid,'title':title,'artist_label':artist,'display_date':r.get('display_date') or r.get('date'),'classification':r.get('classification'),'accession_number':acc,'source_url':'https://whitney.org/collection/works/'+wid,'native_matches':ext,'title_matches':exact,'decision':decision})
 counts={x:sum(d['decision']==x for d in decisions) for x in sorted({d['decision'] for d in decisions})}
 save('whitney-bounded-reconciliation.json',{'at':h.now(),'source_sha256':h.sha(raw),'source_rows':len(rows),'selected_rows':len(decisions),'selection_rule':'first 50 source-order rows classified Painting with explicit creation year(s) ending no later than 1970','excluded_before_selection':excluded,'decisions':counts,'rows':decisions,'images_selected':0,'image_policy':'Registry says never; metadata only. No image downloads attempted.','production_writes':0})
 save('failures-and-holds.json',{'at':h.now(),'holds':[{'route':'whitney','reason':'All selected rows require either no action or deeper creator/global identity review before insert; registry permits metadata only and forbids automated image delivery.'}],'provider_failures':[],'next_retry':'Do not replay this slice; continue Whitney cursor at source row after the 50th eligible painting or rotate to an open-image route.'})
 counts0={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0};cursor={'unit':'official_open_access_csv','source_sha256':h.sha(raw),'eligible_paintings_reviewed':50,'next_eligible_offset':50,'source_rows':len(rows)}
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);qnow=h.load(qp);prior=copy.deepcopy(qnow);q=next(x for x in qnow['sources'] if x['source_id']=='whitney');assert q['status']=='not_yet_reconciled_for_this_programme'
  q.update(status='first_50_eligible_paintings_reconciled_metadata_only_no_verified_additions',last_checked_at=h.now(),last_batch=264,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),resume_cursor=cursor,latest_batch_verified_counts=counts0,access_status={'official_open_access_csv':'HTTP200','collection_images':'not requested; registry automated download never'},remaining_gaps=['Creator/global artwork identity review remains for unresolved candidates.','Images prohibited on this route absent separate permission.','Continue at eligible offset 50 or rotate to an explicit-open-image source.'])
  q['evidence_paths']=[str((E/'whitney-bounded-reconciliation.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]
  assert [x for x in prior['sources'] if x['source_id']!='whitney']==[x for x in qnow['sources'] if x['source_id']!='whitney']
  tmp=qp.with_suffix('.264.tmp');tmp.write_text(json.dumps(qnow,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',{'at':h.now(),'updated_source':'whitney','unrelated_entries_preserved':True,'resume_cursor':cursor,'queue_sha256':h.sha(qp.read_bytes())})
 finished=h.now();cp={'at':finished,'batch':264,'stage':'bounded_research_complete_no_safe_production_insert','researched':{'whitney_eligible_paintings':50},'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts0,'next_task':'Rotate to an untouched explicit-open-image registry route; retain Whitney eligible offset 50 for later metadata reconciliation.','blocker':'','evidence':[str((E/x).relative_to(ROOT)) for x in ['production-target-verification.json','required-input-verification.json','batch107-live-reconciliation.json','source-captures/whitney-artworks.receipt.json','whitney-bounded-reconciliation.json','failures-and-holds.json','source-queue-update-verification.json']],'production_writes':0,'local_catalogue_connections':0,'started_at':started,'finished_at':finished}
 text=json.dumps(cp,ensure_ascii=False,indent=2)+'\n';(E/'CHECKPOINT.json').write_text(text);(R/'CHECKPOINT.json').write_text(text)
 result={'outcome':'progress','summary':'Batch 264 researched and production-reconciled 50 eligible pre-1971 Whitney paintings from the official open-access metadata CSV. No safe new insert was made: selected records were already reconciled or require deeper creator/global identity review, and the registry restricts this route to metadata-only with no automated image use. Batch 107 and the production target were reverified; the local catalogue was untouched.','next_task':cp['next_task'],'blocker':'','verified_counts':counts0,'evidence_paths':[str((E/x).relative_to(ROOT)) for x in ['whitney-bounded-reconciliation.json','batch107-live-reconciliation.json','production-target-verification.json','source-queue-update-verification.json','CHECKPOINT.json']]}
 (E/'worker-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(R/'worker-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
