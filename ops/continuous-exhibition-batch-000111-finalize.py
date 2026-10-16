#!/usr/bin/env python3
import copy, datetime, fcntl, gzip, hashlib, json, subprocess, urllib.request
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000111'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000111'
Q=E.parents[1]/'source-queue.json'; SCHEME='european-cleveland-cleveland-museum-of-art-object'
IDS=['93309','93464','98388','100179','100194','100353','100585','100677','100688','101061']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def save(name,value):
 p=E/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n');return p
def connect():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 k=psycopg.conninfo.conninfo_to_dict(secret);k.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
 return psycopg.connect(**k,row_factory=dict_row,autocommit=True,options='-c default_transaction_read_only=on -c statement_timeout=60000')
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
ps=subprocess.check_output(['ps','-axo','pid,command='],text=True);proxy=next(x for x in ps.splitlines() if 'cloud-sql-proxy' in x and '--port 55519' in x);assert 'artline-508319:europe-west1:artline-postgres' in proxy
with connect() as db:
 target=db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone()
 rows=[dict(x) for x in db.execute("""select a.id::text artwork_id,a.title,a.accession_number,e.external_id,a.primary_media_id::text,
 (select count(*) from exhibition_entries x where x.artwork_id=a.id) exact_links
 from artworks a join external_identifiers e on e.entity_id=a.id and e.entity_type='artwork' and e.scheme=%s
 where e.external_id=any(%s) order by e.external_id::int""",(SCHEME,IDS)).fetchall()]
 assert len(rows)==10 and all(x['primary_media_id'] is None and x['exact_links']>0 for x in rows)
save('recovery-check.json',{'at':now(),'batch':111,'prior_attempt_receipts':[],'uncertain_writes_found':False,'production_rows_reconciled':len(rows),'previous_batch_not_counted':110})
save('production-target-reconciliation.json',{'at':now(),'instance':'artline-508319:europe-west1:artline-postgres','database':target,'proxy_port':55519,'helper_inspected':'ops/exhibitions_common.py','writes':0,'local_catalogue_connections':0})
checks=[]
for row in rows:
 url='https://openaccess-api.clevelandart.org/api/artworks/'+row['external_id'];req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0'})
 with urllib.request.urlopen(req,timeout=30) as res: raw=res.read(); status=res.status
 data=json.loads(raw)['data']; cap=R/'source-captures'/(row['external_id']+'.json.gz');cap.parent.mkdir(parents=True,exist_ok=True);cap.write_bytes(gzip.compress(raw,mtime=0))
 exact=(str(data['id']),data.get('title'),data.get('accession_number'))==(row['external_id'],row['title'],row['accession_number'])
 web=((data.get('images') or {}).get('web') or {}).get('url'); eligible=exact and data.get('share_license_status')=='CC0' and bool(web)
 checks.append({**row,'url':url,'status':status,'capture':str(cap),'source_sha256':sha(raw),'identity_exact':exact,'share_license_status':data.get('share_license_status'),'copyright':data.get('copyright'),'web_image_present':bool(web),'decision':'eligible' if eligible else ('cc0_no_supplied_image' if data.get('share_license_status')=='CC0' else 'copyright_no_supplied_image')})
assert not [x for x in checks if x['decision']=='eligible']
src=save('source-capture-verification.json',{'at':now(),'provider':'The Cleveland Museum of Art','policy_url':'https://www.clevelandart.org/open-access','route':'exact exhibition-linked primary-image gaps after native 93169','checks':checks,'eligible':0,'copyright_holds':sum(x['decision'].startswith('copyright') for x in checks),'cc0_without_image':sum(x['decision']=='cc0_no_supplied_image' for x in checks)})
save('candidate-review-verification.json',{'at':now(),'selected':10,'prepared':0,'visual_review_required':False,'reason':'No source image binary was supplied for any candidate; no file was represented as visually reviewed.','no_generated_or_version_substitute':True,'exact_links_affected':sum(x['exact_links'] for x in checks)})
with open(str(Q)+'.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=json.loads(Q.read_text());before=copy.deepcopy(q);route=next(x for x in q['sources'] if x['source_id']=='cleveland_museum')
 holds=route.setdefault('holds',[]);known={(str(x.get('nativeID')),x.get('reason')) for x in holds if isinstance(x,dict)}
 for x in checks:
  item=(x['external_id'],x['decision'])
  if item not in known: holds.append({'nativeID':x['external_id'],'id':x['artwork_id'],'reason':x['decision'],'checkedAt':now(),'evidence':'docs/research/continuous-exhibitions-20261013/batches/000111/source-capture-verification.json'})
 route.update(research_status='batch111_ten_exact_image_gaps_held_no_source_binary',last_checked_at=now(),last_batch=111)
 route['cursor']['next']='Rotate to another undercovered official open-image route; do not replay Cleveland native IDs 93309–101061 unless the provider publishes a new eligible image.'
 Q.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 unrelated=all(a==b for a,b in zip([x for x in before['sources'] if x['source_id']!='cleveland_museum'],[x for x in q['sources'] if x['source_id']!='cleveland_museum']))
save('queue-update-verification.json',{'at':now(),'source_id':'cleveland_museum','researched_native_ids':IDS,'unrelated_entries_preserved':unrelated,'queue_sha256_after':sha(Q.read_bytes()),'resume':'Rotate to another undercovered official open-image route; do not replay this held window.'})
counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']}
receipt=save('independent-production-verification.json',{'at':now(),'selected':10,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'storage_writes':0,'attribution':'No eligible source binary and no mutation; prior and concurrent jobs excluded.','shared_lock_not_acquired_because_no_write':True})
cp=save('CHECKPOINT.json',{'at':now(),'batch':111,'stage':'complete_no_eligible_candidates','selected':10,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'next_task':'Rotate to another undercovered official source with explicit open-image eligibility; do not replay Cleveland native IDs 93309–101061 unless source state changes.','blocker':''})
final=save('final-verification.json',{'at':now(),'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())} for p in [src,receipt,cp]],'verified_counts':counts,'outcome':'no_eligible_candidates'})
print(json.dumps({'outcome':'no_eligible_candidates','summary':'Reviewed ten exact Cleveland exhibition-linked image gaps. Official records supplied no image binaries: nine are copyrighted and one is CC0 but has no image. No production or Storage write was made.','next_task':'Rotate to another undercovered official source with explicit open-image eligibility; do not replay Cleveland native IDs 93309–101061 unless source state changes.','blocker':'','verified_counts':counts,'evidence_paths':[str(p.relative_to(ROOT)) for p in [src,E/'candidate-review-verification.json',receipt,E/'queue-update-verification.json',cp,final]]}))
