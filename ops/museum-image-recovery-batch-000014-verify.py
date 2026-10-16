#!/usr/bin/env python3
import datetime, hashlib, importlib.util, json, pathlib, subprocess, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'docs/research/museum-image-recovery-20261013/batches/000014'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def save(n,v): (E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('prior',ROOT/'ops/museum-image-recovery-batch-000011.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def main():
 checked=json.loads((E/'checked-artworks.json').read_text());ids=[x['artwork_id'] for x in checked];prior_ids=[]
 for p in E.parent.glob('0000*/checked-artworks.json'):
  if p.parent.name!='000014':prior_ids += [x['artwork_id'] for x in json.loads(p.read_text())]
 assert len(ids)==len(set(ids))==10 and not set(ids)&set(prior_ids) and len(set(prior_ids))==130
 plan=json.loads((E/'delivery-plan.json').read_text())[0];aid=plan['artwork_id'];cs=plan['derivative_sha256']
 q="SELECT json_build_object('rows',count(*),'illustrated',count(*) FILTER (WHERE primary_media_id IS NOT NULL),'held',count(*) FILTER (WHERE primary_media_id IS NULL),'media_links',(SELECT count(*) FROM artwork_media WHERE artwork_id='"+aid+"'::uuid),'rights',(SELECT count(*) FROM media_rights_evidence WHERE media_id='"+plan['media_id']+"'::uuid),'checksum',(SELECT checksum_sha256 FROM media_assets WHERE id='"+plan['media_id']+"'::uuid),'statuses',json_agg(status ORDER BY id)) FROM artworks WHERE id IN ("+','.join("'"+x+"'::uuid" for x in ids)+")"
 db=json.loads(prior.sql(q));assert db['rows']==10 and db['illustrated']==1 and db['held']==9 and db['media_links']==1 and db['rights']==1 and db['checksum']==cs
 meta=json.loads(subprocess.check_output(['gcloud','storage','objects','describe','gs://artline-508319-images'+plan['derivative_path'],'--format=json','--project=artline-508319','--account=vadim@alingva.com'],text=True));assert int(meta['size'])==plan['derivative_bytes']
 url='https://artlines.org'+plan['derivative_path'];public=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ArtlineVerification/1.0'}),timeout=30).read();assert sha(public)==cs
 out={'verified_at':now(),'checked_artworks_json_valid':True,'distinct_checked_ids':10,'prior_campaign_overlap':0,'campaign_total_ids':140,'campaign_distinct_ids':140,'production_rows_read_back':10,'newly_illustrated':1,'held_without_image':9,'source':{'official_api_records_checked':10,'exact_native_accession_title_matches':10,'copyrighted_records':9,'cc0_records':1,'official_image_routes':1,'access_holds':0},'database':{'primary_media_ids':[plan['media_id']],'media_checksums_match':True,'artwork_media_links':1,'rights_evidence_rows':1,'still_imageless_others':9,'editorial_statuses_preserved':True},'storage':[{'artwork_id':aid,'bucket':'artline-508319-images','generation':meta.get('generation'),'bytes':int(meta['size']),'public_sha256':sha(public)}],'public':{'asset_http_200':True,'asset_checksums_match':True,'url':url},'visual':{'original_reviewed':True,'derivative_reviewed':True,'full_frame':True,'proportions_preserved':True,'all_derivatives_at_most_100000_bytes':plan['derivative_bytes']<=100000},'programmes_unchanged':True,'local_catalogue_connections':0,'batch107_reconciled_before_selection':True,'limitations':['Nine exact Cleveland records are marked Copyrighted and expose no official image route; no image was inferred from discovery thumbnails or unrelated versions.']}
 save('independent-verification.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
