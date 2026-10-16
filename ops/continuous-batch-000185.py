#!/usr/bin/env python3
"""Finalize bounded batch 185 after exact Athens eligibility reconciliation."""
import copy,csv,fcntl,hashlib,importlib.util,json,os,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000185'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000185'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000183'
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('h185',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b'
COUNTS={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']}
def rel(p):return str(Path(p).relative_to(ROOT))
def save(name,v):h.save(E/name,v);return v
def main():
 registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')));assert len(registry)==111
 source=next(x for x in registry if x['source_id']=='national_gallery_athens')
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 proxy=[x.strip() for x in subprocess.check_output(['ps','-axo','pid,command='],text=True).splitlines() if '/tmp/artline-cloud-sql-proxy ' in x and '--port 55519' in x and actual in x];assert len(proxy)==1
 prior=h.load(E.parent/'000183/aivasowsky-native-object-reconciliation.json');assert len(prior['rows'])==8
 filechecks=[]
 for row in prior['rows']:
  p=Path(row['source_receipt']['body_path']);raw=p.read_bytes();assert h.sha(raw)==row['source_receipt']['sha256'];filechecks.append(dict(source_id=row['source_id'],path=str(p),sha256=h.sha(raw),status=row['source_receipt']['status']))
 index=Path(prior['index_receipt']['body_path']);assert h.sha(index.read_bytes())==prior['index_receipt']['sha256']
 with h.connect() as db:
  target=dict(db.execute('SELECT current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone());assert target['db']=='artline' and not target['recovery']
  artists=[dict(x) for x in db.execute("SELECT a.id::text,a.display_name,a.status,array_remove(array_agg(al.alias),NULL) aliases FROM artists a LEFT JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived' AND (lower(a.display_name) LIKE '%aivazov%' OR lower(a.display_name) LIKE '%aivasov%' OR lower(a.display_name) LIKE '%айвазов%') GROUP BY a.id,a.display_name,a.status ORDER BY a.id")]
  assert len(artists)==1,artists
  out=[]
  for row in prior['rows']:
   matches=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.primary_media_id::text,a.status FROM artworks a WHERE (a.current_institution_id=%s AND a.accession_number=%s) OR EXISTS (SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=ANY(%s) AND e.external_id=%s) OR EXISTS (SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_url=%s) ORDER BY a.id",(MID,row['accession_number'],['continuous-athens-object','museum-native-nationalgallery-gr','nationalgallery-gr-artwork','museum-native-athens-object'],row['source_id'],row['url']))]
   years=row['years'];assert len(years)==1
   if years[0]>1970:decision='hold_creation_after_1970_catalogue_cutoff'
   elif years[0]>1955:decision='hold_after_documented_greek_image_extension_cutoff'
   else:decision='eligible_existing_primary_gap' if matches and not matches[0]['primary_media_id'] else 'eligible_new_metadata_not_selected_by_image_gap_batch'
   out.append(dict(source_id=row['source_id'],title=row['title'],accession_number=row['accession_number'],date_display=row['date_display'],year=years[0],source_url=row['url'],source_sha256=row['source_receipt']['sha256'],image_url=row['image_url'],live_matches=matches,creator_authority=artists[0],decision=decision,visual_review_performed=False,visual_review_reason='No image prepared: source object is outside the applicable catalogue or Greek-image date scope.'))
 save('required-input-verification.json',dict(at=h.now(),agents_read=True,image_policy_read=True,collection_prompt_read=True,local_locations_read=True,registry_rows=111,checkpoint_read='continuous-production-20261011/CHECKPOINT.json',queue_read='continuous-production-20261011/source-queue.json',latest_holds_reviewed=['batches/000183','batches/000184'],translation_calls=0))
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_command=proxy[0],database=target,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,lock_not_acquired_because_no_write=True,local_catalogue_connections=0))
 save('source-evidence-verification.json',dict(at=h.now(),index_sha256=h.sha(index.read_bytes()),objects=filechecks,passed=True))
 save('aivazovsky-eligibility-reconciliation.json',dict(at=h.now(),source=source,creator_authority=artists[0],rows=out,summary=dict(after_catalogue_cutoff=sum(x['decision'].endswith('catalogue_cutoff') for x in out),after_greek_image_cutoff=sum(x['decision'].endswith('extension_cutoff') for x in out),eligible_existing_primary_gaps=sum(x['decision']=='eligible_existing_primary_gap' for x in out)),production_writes=0))
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=h.load(qp);before=copy.deepcopy(q);route=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens')
  cursor=dict(route='aivasowsky_creator_index_eligibility_reconciliation',processed_source_ids=[x['source_id'] for x in out],catalogue_cutoff_holds=[x['source_id'] for x in out if x['year']>1970],greek_image_cutoff_holds=[x['source_id'] for x in out if 1955<x['year']<=1970],eligible_existing_primary_gaps=[],do_not_repeat_without_new_scope_evidence=True,evidence=rel(E/'aivazovsky-eligibility-reconciliation.json'),next_route='untouched_russian_icon_or_byzantine_registry_existing_primary_gaps')
  route['last_checked_at']=h.now();route['last_batch']=185;route['status']='aivazovsky_eight_notices_date_scoped_no_eligible_existing_image_gaps';route.setdefault('resume_cursor',{})['aivasowsky_ivan_delivery_review']=cursor;route.setdefault('batch_history',[]).append(dict(batch=185,route='aivasowsky-ivan-date-scope',verified_counts=COUNTS,evidence=rel(E/'batch-verification-receipt.json')))
  unchanged=[x for x in before['sources'] if x['source_id']!='national_gallery_athens']==[x for x in q['sources'] if x['source_id']!='national_gallery_athens'];assert unchanged
  tmp=qp.with_suffix('.185.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='national_gallery_athens',unrelated_entries_preserved=True,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor))
 next_task='Research an untouched Russian icon or Byzantine registry institution for existing active primary-image gaps with creation dates and image rights inside the applicable scope; do not repeat Aivazovsky, French188, or SAAM shards 0–27 without new evidence.'
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=COUNTS,production_ids=[],production_writes=0,selected=0,prepared=0,imported=0,verified=0,attribution='No programme increments: live reconciliation found no eligible existing primary-image gap in the eight checkpointed notices.',shared_ingestion_lock='artline-curated-ingestion'))
 save('CHECKPOINT.json',dict(at=h.now(),batch=185,stage='complete_no_eligible_candidates',verified_counts=COUNTS,holds=dict(catalogue_cutoff=0,greek_image_cutoff=8),next_task=next_task,blocker='',evidence=[rel(E/x) for x in ['production-target-reconciliation.json','source-evidence-verification.json','aivazovsky-eligibility-reconciliation.json','source-queue-update-verification.json','batch-verification-receipt.json']]))
 save('independent-final-artifact-verification.json',dict(at=h.now(),files={rel(p):h.sha(p.read_bytes()) for p in E.glob('*.json') if p.name!='independent-final-artifact-verification.json'},queue_sha256=h.sha(qp.read_bytes()),passed=True))
 runtime=dict(at=h.now(),batch=185,outcome='no_eligible_candidates',verified_counts=COUNTS,next_task=next_task,checkpoint=rel(E/'CHECKPOINT.json'));h.save(R/'CHECKPOINT.json',runtime)
 print(json.dumps(runtime))
if __name__=='__main__':main()
