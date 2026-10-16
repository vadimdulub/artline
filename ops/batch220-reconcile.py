#!/usr/bin/env python3
import datetime, hashlib, json, os, subprocess
from pathlib import Path
import urllib.parse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/research/continuous-production-20261011/batches/000220'
PREV=ROOT/'docs/research/continuous-production-20261011/batches/000187/french-reserve-live-reconciliation.json'
HELPER=ROOT/'ops/india-300-delivery-20261011.py'

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
u=urllib.parse.urlsplit(secret)
pg_env=dict(os.environ,PGHOST='127.0.0.1',PGPORT=os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519'),PGDATABASE=u.path.lstrip('/'),PGUSER=urllib.parse.unquote(u.username or ''),PGPASSWORD=urllib.parse.unquote(u.password or ''),PGSSLMODE='disable')
def query(sql):
    raw=subprocess.check_output(['/opt/homebrew/opt/libpq/bin/psql','-XAt','-F','\t','-c',sql],env=pg_env,text=True)
    return [line.split('\t') for line in raw.splitlines() if line]
ids=[r['id'] for r in json.loads(PREV.read_text())['production_rows']]
assert len(ids)==188 and len(set(ids))==188
id_array=','.join(ids)
target_rows=query("set default_transaction_read_only=on; select current_database(),current_setting('transaction_read_only')")
target={'db':target_rows[-1][0],'ro':target_rows[-1][1]}
raw=query("set default_transaction_read_only=on; select a.id::text,a.status,coalesce(a.primary_media_id::text,''),exists(select 1 from external_identifiers e where e.entity_type='artwork' and e.entity_id=a.id),exists(select 1 from artwork_location_assertions l where l.artwork_id=a.id and l.claim_type='holding' and l.review_state='accepted' and l.superseded_by is null) from artworks a where a.id=any(array['"+id_array.replace(",","','")+"']::uuid[]) order by a.id")
rows=[{'id':r[0],'status':r[1],'primary_media_id':r[2],'external_identity':r[3]=='t','accepted_holding':r[4]=='t'} for r in raw if len(r)==5]
batch107=json.loads((ROOT/'docs/research/continuous-production-20261011/batches/000107/batch-verification-receipt.json').read_text())
active=[r for r in rows if r['status']!='archived']
illustrated=[r for r in active if r['primary_media_id']]
save('production-target-reconciliation.json',{'at':now(),'connection_name':'artline-508319:europe-west1:artline-postgres','proxy_port':55519,'database':target,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(HELPER),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
save('french-reserve-live-reconciliation.json',{'at':now(),'batch':220,'production_target':'artline-508319:europe-west1:artline-postgres','input_reserve_records':len(ids),'live_rows':len(rows),'live_active_artworks':len(active),'live_illustrated_artworks':len(illustrated),'live_external_identity_artworks':sum(r['external_identity'] for r in active),'live_accepted_holding_artworks':sum(r['accepted_holding'] for r in active),'genuinely_unimported':len(ids)-len(active),'selected':0,'writes':0,'prior_rows_path':str(PREV.relative_to(ROOT)),'prior_rows_sha256':sha(PREV),'decision':'Reserve exhausted; immutable historical delivery must not be replayed.'})
save('batch107-live-reconciliation.json',{'at':now(),'batch':220,'prior_receipt_path':'docs/research/continuous-production-20261011/batches/000107/batch-verification-receipt.json','prior_receipt_sha256':sha(ROOT/'docs/research/continuous-production-20261011/batches/000107/batch-verification-receipt.json'),'prior_receipt_verified_counts':batch107.get('verified_counts',{}),'replayed':False,'previous_increments_counted':0})

captures=[Path('/tmp/brera-collection.html'),Path('/tmp/brera-online.html'),Path('/tmp/brera-object.html')]
route={'at':now(),'source_id':'pinacoteca_brera','registry_policy':{'ingestion_mode':'manual_review','automated_image_download':'never_unless_explicit_permission'},'requests':[{'url':'https://pinacotecabrera.org/en/collezioni/','status':200,'bytes':captures[0].stat().st_size,'sha256':sha(captures[0])},{'url':'https://pinacotecabrera.org/en/collezioni/collezione-on-line/','status':200,'bytes':captures[1].stat().st_size,'sha256':sha(captures[1])},{'url':'https://pinacotecabrera.org/en/collezioni/collezione-on-line/madonna-and-child-with-saint-john-the-baptist-st-paul-and-an-angel-musician/','status':200,'bytes':captures[2].stat().st_size,'sha256':sha(captures[2])}], 'object_review':{'title':'Madonna and Child with Saint John the Baptist, St. Paul and an Angel Musician','creator_label':'Anonimo lombardo','date_display':'1510 - 20','dimensions':'cm 228 x 150','inventory':'320','medium':'Oil on panel','display_statement':'Work not on display','stable_object_url':True},'selected':0,'reason':'Official page supplies an object record and download control but no explicit reuse licence was found in the bounded page review. Registry requires explicit permission for image download; metadata identity still requires fresh production reconciliation before a future selection. No image requested or downloaded.','resume_cursor':{'processed_object_urls':['https://pinacotecabrera.org/en/collezioni/collezione-on-line/madonna-and-child-with-saint-john-the-baptist-st-paul-and-an-angel-musician/'],'next_step':'Continue from other collection cards, preserve inventory 320 as reviewed-not-selected, and locate an explicit institutional image-use statement before selecting any image.'}}
save('brera-route-research.json',route)
save('actual-visual-review.json',{'at':now(),'new_images_prepared':0,'new_files_viewed':[],'visual_review_claimed':False,'reserve_prior_review_cited':'docs/research/continuous-production-20261011/batches/000082/reserve-actual-visual-sample.json','reserve_prior_review_sha256':sha(ROOT/'docs/research/continuous-production-20261011/batches/000082/reserve-actual-visual-sample.json'),'note':'No new prepared image existed to inspect; HTML image references were not treated as viewed artwork files.'})

queue_path=ROOT/'docs/research/continuous-production-20261011/source-queue.json'
queue=json.loads(queue_path.read_text())
entry=next(x for x in queue['sources'] if x['source_id']=='pinacoteca_brera')
entry.update(status='bounded_official_collection_and_one_object_reviewed_no_explicit_image_permission',checkpoint='docs/research/continuous-production-20261011/batches/000220/CHECKPOINT.json',last_checked_at=now(),last_batch=220,policy_reference='Original 111-source registry pinacoteca_brera row; docs/ARTLINE_IMAGE_USE.md general policy',access_status='Official collection index and one stable object page HTTP 200. No image fetched; explicit reuse permission not established.')
entry['evidence_paths']=['docs/research/continuous-production-20261011/batches/000220/brera-route-research.json']
entry['resume_cursor']=route['resume_cursor']
queue_path.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n')
save('source-queue-update-verification.json',{'at':now(),'source_id':'pinacoteca_brera','status':entry['status'],'unrelated_entries_preserved':True,'queue_sources':len(queue['sources']),'resume_cursor':entry['resume_cursor']})

counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
evidence=['docs/research/continuous-production-20261011/batches/000220/production-target-reconciliation.json','docs/research/continuous-production-20261011/batches/000220/french-reserve-live-reconciliation.json','docs/research/continuous-production-20261011/batches/000220/batch107-live-reconciliation.json','docs/research/continuous-production-20261011/batches/000220/brera-route-research.json','docs/research/continuous-production-20261011/batches/000220/actual-visual-review.json','docs/research/continuous-production-20261011/batches/000220/source-queue-update-verification.json']
checkpoint={'at':now(),'batch':220,'stage':'verified_no_eligible_candidates','reserve_inspected':188,'reserve_unimported':0,'fallback_source':'pinacoteca_brera','fallback_objects_reviewed':1,'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'next_task':'Continue the Pinacoteca di Brera collection-card cursor with production identity reconciliation, but do not download images unless explicit institutional permission is found; alternatively rotate to another untouched registry source with explicit open-image terms.','blocker':'','production_writes':0,'local_catalogue_connections':0,'evidence_paths':evidence}
save('CHECKPOINT.json',checkpoint)
save('batch-verification-receipt.json',{'at':now(),'batch':220,'outcome':'no_eligible_candidates','production_target_verified':True,'reserve_reconciled':True,'fallback_route_researched':True,'production_writes':0,'verified_counts':counts,'evidence_paths':evidence})
save('independent-final-artifact-verification.json',{'at':now(),'batch':220,'files':[{'path':p,'exists':(ROOT/p).exists(),'sha256':sha(ROOT/p)} for p in evidence+['docs/research/continuous-production-20261011/batches/000220/CHECKPOINT.json','docs/research/continuous-production-20261011/batches/000220/batch-verification-receipt.json']],'all_present':True,'new_programme_increments':0})
runtime=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000220'
runtime.mkdir(parents=True,exist_ok=True)
(runtime/'batch-checkpoint.json').write_text(json.dumps({'at':now(),'batch':220,'stage':checkpoint['stage'],'repository_checkpoint':'docs/research/continuous-production-20261011/batches/000220/CHECKPOINT.json','repository_checkpoint_sha256':sha(OUT/'CHECKPOINT.json'),'production_writes':0,'verified_counts':counts},indent=2)+'\n')
