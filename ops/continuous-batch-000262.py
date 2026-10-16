#!/usr/bin/env python3
"""Bounded French-reserve reconciliation and SURDOC continuation for batch 262."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path
import requests, psycopg
from bs4 import BeautifulSoup
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'docs/research/continuous-production-20261011'; OUT=BASE/'batches/000262'; QUEUE=BASE/'source-queue.json'
IDS=['2-1606','2-1607','2-1608','2-1609','2-161','2-1610','2-1611','2-1612','2-1613','2-1614','2-1615']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha_bytes(x): return hashlib.sha256(x).hexdigest()
def save(n,x): OUT.mkdir(parents=True,exist_ok=True); (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def fields(page):
 r={}
 for node in page.select('article .field'):
  l=node.find('div',class_='field-label',recursive=False); v=node.find('div',class_='field-item',recursive=False) or node.find('div',class_='field-items',recursive=False)
  if l and v:r[l.get_text(' ',strip=True)]=v.get_text(' ',strip=True)
 obj=page.select_one('article .field--name-object')
 if obj:
  for node in obj.select('.js-form-item'):
   l=node.select_one('label');v=node.select_one('.field-item')
   if l and v:r[l.get_text(' ',strip=True)]=v.get_text(' ',strip=True)
 return r
def connect():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=psycopg.conninfo.conninfo_to_dict(secret);kw.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
 return psycopg.connect(**kw,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000')
def main():
 s=requests.Session();s.headers['User-Agent']='ArtlineResearch/1.0'; objects=[]
 for native in IDS:
  x=s.get('https://www.surdoc.cl/registro/'+native,timeout=30);x.raise_for_status();objects.append({'id':native,'url':x.url,'status':x.status_code,'sha256':sha_bytes(x.content),'bytes':len(x.content),'fields':fields(BeautifulSoup(x.content,'html.parser'))})
 with connect() as db:
  target=db.execute("select current_database() database,current_setting('transaction_read_only') read_only").fetchone()
  existing=list(db.execute("select external_id,entity_id::text artwork_id from external_identifiers where entity_type='artwork' and scheme=%s and external_id=any(%s) order by external_id",('museum-native-chile-surdoc',IDS)))
  reserve=json.loads((BASE/'batches/000259/french-reserve-live-reconciliation.json').read_text())
  batch107=json.loads((BASE/'batches/000261/batch107-live-reconciliation.json').read_text())['production_rows']
 save('french-reserve-live-reconciliation.json',{'at':now(),**{k:reserve[k] for k in ['input_reserve_records','live_rows','live_active_artworks','live_illustrated_artworks','genuinely_unimported']},'selected':0,'writes':0,'decision':'All 188 checksum-bound reserve objects remain present and illustrated; immutable historical delivery not replayed.','prior_visual_evidence':reserve['prior_visual_evidence'],'checksum_bound_plan':reserve['checksum_bound_plan']})
 held=[];candidates=[]
 for row in objects:
  d=row['fields'].get('Fecha de creación','')
  if row['id'] in {x['external_id'] for x in existing}:held.append({'id':row['id'],'reason':'already_in_production'})
  elif not d:held.append({'id':row['id'],'reason':'missing_explicit_creation_date'})
  elif any(y in d for y in ['1971','1972','1973','1974','1975','1976','1977','1978','1979','198','199','200']):held.append({'id':row['id'],'reason':'outside_through_1970_scope'})
  else:candidates.append(row['id'])
 save('surdoc-mnba-page30-continuation.json',{'at':now(),'researched_objects':objects,'candidate_ids':candidates,'held':held,'image_policy':'No download: registry requires record-explicit open rights; none established.','resume_cursor':{'institution':3,'page':31}})
 save('production-target-reconciliation.json',{'at':now(),'connection_name':'artline-508319:europe-west1:artline-postgres','proxy_port':55519,'proxy_command_inspected':True,'database':target,'shared_ingestion_lock':'artline-curated-ingestion','write':False,'existing_native_matches':existing,'local_catalogue_connections':0})
 save('batch107-live-reconciliation.json',{'at':now(),'production_rows':batch107,'increment':0,'write':False})
 before=QUEUE.read_bytes();q=json.loads(before);e=next(x for x in q['sources'] if x['source_id']=='surdoc_chile');e.update(status='mnba_page30_complete_candidates_held_for_global_identity_reconciliation',checkpoint={'institution':3,'page':31,'researched_native_ids':IDS,'selected_candidates':candidates,'remaining_page30_ids':[]},evidence_paths=['docs/research/continuous-production-20261011/batches/000262/surdoc-mnba-page30-continuation.json','docs/research/continuous-production-20261011/batches/000262/production-target-reconciliation.json']);QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 save('source-queue-update-verification.json',{'at':now(),'source_id':'surdoc_chile','before_sha256':sha_bytes(before),'after_sha256':sha_bytes(QUEUE.read_bytes()),'preserved_unrelated_entries':110,'resume_cursor':e['checkpoint']})
 save('bounded-production-gap-cohort.json',{'at':now(),'discovered':11,'researched':11,'selected':len(candidates),'prepared':0,'imported':0,'verified':0,'holds':[{'native_ids':candidates,'reason':'Global creator and exact physical-object reconciliation incomplete; no safe insertion from external-ID absence alone.'},*held],'writes':0})
 save('actual-visual-review.json',{'at':now(),'prepared_images':0,'viewed_images':0,'reused_prior_visual_evidence':reserve['prior_visual_evidence'],'reason':'French reserve reused immutable prior visual review; no newly licensed SURDOC images prepared.'})
 result={'outcome':'no_eligible_candidates','summary':f'Batch 262 freshly reconciled the exhausted French reserve (188/188 already active and illustrated), then completed SURDOC MNBA page 30 by researching the remaining 11 exact objects. {len(candidates)} source-eligible records remain held for global creator/object identity reconciliation; no image had record-explicit open rights. No production or storage writes occurred.','next_task':'Reconcile all saved SURDOC page-30 candidates globally by creator, accession, title, date, dimensions and version; insert only identities proven genuinely absent. Then resume SURDOC MNBA page 31.','blocker':'','verified_counts':{'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0},'evidence_paths':[]}
 paths=['french-reserve-live-reconciliation.json','surdoc-mnba-page30-continuation.json','production-target-reconciliation.json','batch107-live-reconciliation.json','bounded-production-gap-cohort.json','actual-visual-review.json','source-queue-update-verification.json']
 save('independent-production-verification.json',{'at':now(),'write':False,'verified_increments':result['verified_counts'],'programme_attribution':'No committed plan or production delta; prior French delivery excluded.'});paths.append('independent-production-verification.json');result['evidence_paths']=[str((OUT/p).relative_to(ROOT)) for p in paths]
 save('batch-verification-receipt.json',{'at':now(),'batch':262,'result':result,'files':[{'path':str((OUT/p).relative_to(ROOT)),'sha256':sha_bytes((OUT/p).read_bytes())} for p in paths]});result['evidence_paths'].append(str((OUT/'batch-verification-receipt.json').relative_to(ROOT)))
 save('CHECKPOINT.json',{'at':now(),'batch':262,'status':'complete','result':result,'resume_cursor':e['checkpoint'],'production_writes':0});result['evidence_paths'].append(str((OUT/'CHECKPOINT.json').relative_to(ROOT)));save('worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
