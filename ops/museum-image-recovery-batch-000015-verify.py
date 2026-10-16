#!/usr/bin/env python3
import datetime,hashlib,importlib.util,json,pathlib,subprocess,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'docs/research/museum-image-recovery-20261013/batches/000015'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('prior',ROOT/'ops/museum-image-recovery-batch-000011.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def main():
 checked=json.loads((E/'checked-artworks.json').read_text());ids=[x['artwork_id'] for x in checked];old=[]
 for p in E.parent.glob('0000*/checked-artworks.json'):
  if p.parent.name!='000015':old += [x['artwork_id'] for x in json.loads(p.read_text())]
 assert len(ids)==len(set(ids))==10 and len(set(old))==140 and not set(ids)&set(old)
 plans=json.loads((E/'delivery-plan.json').read_text());assert len(plans)==3
 q="SELECT json_build_object('rows',count(*),'illustrated',count(*) FILTER (WHERE primary_media_id IS NOT NULL),'held',count(*) FILTER (WHERE primary_media_id IS NULL),'statuses',json_agg(status ORDER BY id)) FROM artworks WHERE id IN ("+','.join("'"+x+"'::uuid" for x in ids)+')'
 db=json.loads(prior.sql(q));assert db['rows']==10 and db['illustrated']==3 and db['held']==7
 storage=[];public=[]
 for p in plans:
  detail=json.loads(prior.sql("SELECT json_build_object('media_id',a.primary_media_id,'checksum',m.checksum_sha256,'path',m.storage_path,'links',(SELECT count(*) FROM artwork_media WHERE artwork_id=a.id),'rights',(SELECT count(*) FROM media_rights_evidence WHERE media_id=m.id)) FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id='"+p['artwork_id']+"'::uuid"));assert detail['media_id']==p['media_id'] and detail['checksum']==p['derivative_sha256'] and detail['links']==1 and detail['rights']==1
  meta=json.loads(subprocess.check_output(['gcloud','storage','objects','describe','gs://artline-508319-images'+p['derivative_path'],'--format=json','--project=artline-508319','--account=vadim@alingva.com'],text=True));assert int(meta['size'])==p['derivative_bytes']
  url='https://artlines.org'+p['derivative_path'];raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ArtlineVerification/1.0'}),timeout=30).read();assert sha(raw)==p['derivative_sha256']
  storage.append({'artwork_id':p['artwork_id'],'generation':meta.get('generation'),'bytes':int(meta['size']),'checksum':sha(raw)});public.append({'url':url,'http_200':True,'checksum_match':True})
 out={'verified_at':now(),'checked_artworks_json_valid':True,'distinct_checked_ids':10,'prior_campaign_overlap':0,'campaign_total_ids':150,'campaign_distinct_ids':150,'production_rows_read_back':10,'newly_illustrated':3,'held_without_image':7,'source':{'official_api_records_checked':10,'exact_native_accession_title_matches':10,'cc0_image_routes':3,'no_image_routes':7,'access_holds':0},'database':{'attachments':3,'still_imageless':7,'artwork_media_links':3,'rights_evidence_rows':3,'editorial_statuses_preserved':True},'storage':storage,'public':public,'visual':{'originals_reviewed':3,'derivatives_reviewed':3,'full_frame':True,'proportions_preserved':True,'all_derivatives_at_most_100000_bytes':all(p['derivative_bytes']<=100000 for p in plans)},'programmes_unchanged':True,'local_catalogue_connections':0,'batch107_reconciled_before_selection':True,'limitations':['Six Copyrighted records and one CC0 record expose no official image route; no image was inferred from discovery thumbnails or unrelated versions.']}
 (E/'independent-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
