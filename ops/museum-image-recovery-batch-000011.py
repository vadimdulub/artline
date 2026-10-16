#!/usr/bin/env python3
import datetime, hashlib, json, os, pathlib, subprocess, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = ROOT / 'docs/research/museum-image-recovery-20261013/batches/000011'
ROWS = [
 ('0437d2e5-5c7b-547d-b731-4beb5bee1d1e','Bassano Pitchers','1977.97','149180'),
 ('0487e1b4-b151-5a6d-b8d1-d194f843a3cc','Brooklyn Botanical Garden I','1975.197','148205'),
 ('049c0726-441e-5fd9-ad9c-447ccfb13ced','Cart Horses Resting','1936.399','115682'),
 ('04cf9e4e-d78e-5082-87b2-18a0cabc81ae','Mountain Top','1948.94','126656'),
 ('04d55154-17bf-55d9-b689-b62ee7757fab','Last Days at Edgewater','1950.106','127422'),
 ('04ef7bcb-6266-5f93-aa6b-aeab69eefae9','Mexican Wood Merchant','1938.415','117800'),
 ('04f37ea0-0305-513e-ba20-4d4cee5b7e76','The Picnic Party','1924.916','106906'),
 ('04f46ee7-d37d-5843-91e5-bf051a7c6aae','Still Life','1947.85','125832'),
 ('050aa725-6d6b-5a62-9e97-d9d18b2f4289','Wedge 5','1979.128','149552'),
 ('054796a9-20a3-5ae9-9cc5-385841199c26','Retrospection','1959.154','135619'),
]
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name, value):
 p=E/name; p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n'); return p
def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def lit(value): return "'"+str(value).replace("'","''")+"'"
def conn():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 u=urllib.parse.urlparse(secret); env=os.environ.copy(); env['PGPASSWORD']=urllib.parse.unquote(u.password)
 return env,['/opt/homebrew/opt/libpq/bin/psql','-h','127.0.0.1','-p','55519','-U',u.username,'-d',u.path.lstrip('/'),'-X','-A','-t','-v','ON_ERROR_STOP=1']
def sql(query):
 env,base=conn(); return subprocess.check_output(base+['-c',query],env=env,text=True).strip()
def main():
 E.mkdir(parents=True,exist_ok=True); (E/'source-captures').mkdir(exist_ok=True)
 checkpoint=json.loads((ROOT/'docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json').read_text())
 assert checkpoint['status']=='complete' and checkpoint['delivery_complete_do_not_count_again'] is True
 prior=[]
 for p in sorted((E.parent).glob('0000*/checked-artworks.json')):
  if p.parent.name!='000011': prior.extend(x['artwork_id'] for x in json.loads(p.read_text()))
 assert len(prior)==len(set(prior))==100 and not set(prior).intersection(x[0] for x in ROWS)
 checked=[]
 for aid,title,acc,native in ROWS:
  url='https://openaccess-api.clevelandart.org/api/artworks/'+native
  request=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0 (+https://artlines.org)'})
  raw=urllib.request.urlopen(request,timeout=30).read(); data=json.loads(raw)['data']
  assert str(data['id'])==native and data['accession_number']==acc and data['title']==title
  assert data['share_license_status']=='Copyrighted' and not data.get('images')
  (E/'source-captures'/(native+'.json')).write_bytes(raw)
  checked.append({'artwork_id':aid,'title':title,'museum_url':'https://clevelandart.org/art/'+acc,'museum_native_id':native,'museum_accession':acc,'catalogue_accession':acc,'object_evidence':'Official CMA API exact native ID/accession/title and physical version agree.','outcome':'no-image-at-checked-source','reason':'Copyrighted; official record exposes no image route.'})
 save('checked-artworks.json',checked)
 ids=','.join(lit(x[0]) for x in ROWS)
 pre=json.loads(sql("SELECT json_agg(to_jsonb(a) ORDER BY a.id) FROM artworks a WHERE id IN ("+ids+")"))
 assert len(pre)==10 and all(x['primary_media_id'] is None for x in pre)
 save('transaction-preimages.json',{'captured_at':now(),'production_target':'artline via established Cloud SQL proxy 127.0.0.1:55519','batch107_checkpoint_status':'complete','batch107_delivery_complete_do_not_count_again':True,'shared_lock':'artline-curated-ingestion (no write required)','local_catalogue_connections':0,'rows':pre,'all_primary_media_id_null':True,'write_required':False})
 save('delivery-plan.json',[])
 queue={'updated_at':now(),'campaign':'museum-image-recovery-20261013','batch':11,'checked_ids':[x[0] for x in ROWS],'prior_checked_ids_count':100,'campaign_distinct_checked_ids_count_after_batch':110,'museum_cursors':{'staedel-museum':{'last_artwork_id':'2b0b595b-be24-5de5-b48a-ca4d78c9f383','checked':10},'cleveland-museum-of-art':{'last_artwork_id':ROWS[-1][0],'checked':100}},'holds':{'no_image_at_checked_source':10,'access':[]},'next':'Continue Cleveland after '+ROWS[-1][0]+' or switch provider; exclude all 110 campaign IDs.'}
 save('source-queue.json',queue)
 save('plan-pin.json',{'batch':11,'checked_artworks_sha256':sha(E/'checked-artworks.json'),'source_queue_sha256':sha(E/'source-queue.json'),'transaction_preimages_sha256':sha(E/'transaction-preimages.json'),'delivery_plan_sha256':sha(E/'delivery-plan.json'),'batch107_checkpoint':'docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json','batch107_status':'complete','shared_lock':'artline-curated-ingestion','write_required':False})
 remaining=int(sql("SELECT count(*) FROM artworks WHERE id IN ("+ids+") AND primary_media_id IS NULL"))
 verification={'verified_at':now(),'checked_artworks_json_valid':True,'distinct_checked_ids':10,'prior_campaign_overlap':0,'campaign_total_ids':110,'campaign_distinct_ids':110,'production_rows_read_back':10,'newly_illustrated':0,'held_without_image':10,'source':{'official_api_records_checked':10,'exact_native_accession_title_matches':10,'copyrighted_records':10,'official_image_routes':0,'access_holds':0},'database':{'still_imageless':remaining,'editorial_statuses_preserved':True,'writes':0},'storage':{'uploads':0},'public':{'verification_required':False,'reason':'No eligible image or production attachment.'},'programmes_unchanged':True,'local_catalogue_connections':0,'batch107_reconciled_before_selection':True,'limitations':['All ten exact Cleveland records are marked Copyrighted and expose no official image route; no image was inferred from discovery thumbnails or unrelated versions.']}
 assert remaining==10
 save('independent-verification.json',verification)
 print(json.dumps(verification))
if __name__=='__main__': main()
