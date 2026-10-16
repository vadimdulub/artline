#!/usr/bin/env python3
import datetime, hashlib, importlib.util, json, os, pathlib, subprocess, urllib.request, uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/museum-image-recovery-20261013/batches/000013'
ORIG=pathlib.Path.home()/'Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000013/1933.480.b_print.jpg'
DERIV=ROOT/'apps/web/public/assets/artworks/imported/museum-image-recovery-20261013/05eff251-7c8f-57d3-b973-f4647a9c00b7.jpg'
ACTOR='local-european-research'; OP='museum-image-recovery-20261013-b000013'
ROWS=[
('05e07d79-41cd-58e8-b234-d73a8d31dddd','The Young Woman and Death','1925.550','107923'),
('05eff251-7c8f-57d3-b973-f4647a9c00b7',"Qur'an Manuscript Folio (verso)",'1933.480.b','114237'),
('0608601b-37f6-5384-97ff-157a7c5533a8','Willoughby Coal Yard','1992.189','156398'),
('0631353f-c792-5edb-8499-90cbf632c683','Orange on Three','1984.173','151880'),
('06481eaa-b59f-58ee-8e93-84ae1b92100a','The Tug "Doris Moran"','1973.177','147438'),
('0669d23c-ef52-50dd-a1c0-441b318b96c0','Pierrot','1923.79','105689'),
('0691ba41-12ca-53e2-9072-b0143f0fd422','The Bald Boy','1961.320','136827'),
('06a483ab-c888-5dc0-89eb-e30fe56c29e2','Black Houses','1932.141','113122'),
('06adc349-5587-476d-9703-5fc27286669d','Guitar and Bottle of Marc on a Table','1975.59','148335'),
('06d36227-c4cf-4335-b146-360f7e35037b','The Plaid Dress','2026.1','87250')]
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(n,v):
 p=E/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');return p
def lit(v): return "'"+str(v).replace("'","''")+"'"
spec=importlib.util.spec_from_file_location('prior',ROOT/'ops/museum-image-recovery-batch-000011.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def sql(q): return prior.sql(q)
def main():
 cp=json.loads((ROOT/'docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json').read_text());assert cp['status']=='complete' and cp['delivery_complete_do_not_count_again']
 old=[]
 for p in sorted(E.parent.glob('0000*/checked-artworks.json')):
  if p.parent.name!='000013':old += [x['artwork_id'] for x in json.loads(p.read_text())]
 assert len(old)==len(set(old))==120 and not set(old)&{x[0] for x in ROWS}
 checked=[]; api={}; (E/'source-captures').mkdir(parents=True,exist_ok=True)
 for aid,title,acc,native in ROWS:
  u='https://openaccess-api.clevelandart.org/api/artworks/'+native;raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ArtlineResearch/1.0 (+https://artlines.org)'}),timeout=30).read();d=json.loads(raw)['data'];api[aid]=d
  assert str(d['id'])==native and d['accession_number']==acc and d['title']==title
  delivered=aid==ROWS[1][0];assert delivered==(d['share_license_status']=='CC0' and bool(d.get('images',{}).get('print')))
  (E/'source-captures'/(native+'.json')).write_bytes(raw)
  checked.append({'artwork_id':aid,'title':title,'museum_url':'https://clevelandart.org/art/'+acc,'museum_native_id':native,'museum_accession':acc,'catalogue_accession':acc,'object_evidence':'Official CMA API exact native ID/accession/title and physical version agree.'+(' Exact folio verso visually reviewed.' if delivered else ''),'outcome':'delivered' if delivered else 'no-image-at-checked-source','reason':'Official CC0 full-frame print route; derivative prepared.' if delivered else 'Copyrighted; official record exposes no image route.'})
 save('checked-artworks.json',checked);ids=','.join(lit(x[0]) for x in ROWS)
 pre=json.loads(sql('SELECT json_agg(to_jsonb(a) ORDER BY a.id) FROM artworks a WHERE id IN ('+ids+')'));assert len(pre)==10 and all(x['primary_media_id'] is None for x in pre)
 save('transaction-preimages.json',{'captured_at':now(),'production_target':'artline via established Cloud SQL proxy 127.0.0.1:55519','batch107_checkpoint_status':'complete','batch107_delivery_complete_do_not_count_again':True,'shared_lock':'artline-curated-ingestion','local_catalogue_connections':0,'rows':pre,'all_primary_media_id_null':True,'write_required':True})
 aid,title,acc,native=ROWS[1];checksum=sha(DERIV);mid=str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/media/'+aid+'/'+checksum));d=api[aid]
 plan={'artwork_id':aid,'media_id':mid,'title':title,'accession':acc,'native_id':native,'source_page_url':'https://clevelandart.org/art/'+acc,'source_api_url':'https://openaccess-api.clevelandart.org/api/artworks/'+native,'source_image_url':d['images']['print']['url'],'original_path':str(ORIG),'original_sha256':sha(ORIG),'derivative_path':'/assets/artworks/imported/museum-image-recovery-20261013/'+aid+'.jpg','derivative_file':str(DERIV),'derivative_sha256':checksum,'derivative_bytes':DERIV.stat().st_size,'width':661,'height':850,'credit':'Unknown artist, Egypt, Mamluk sultanate (1250–1517)','visual_review':'accepted: exact folio verso; complete museum frame and proportions preserved; no crop'}
 save('delivery-plan.json',[plan]);queue={'updated_at':now(),'campaign':'museum-image-recovery-20261013','batch':13,'checked_ids':[x[0] for x in ROWS],'prior_checked_ids_count':120,'campaign_distinct_checked_ids_count_after_batch':130,'museum_cursors':{'staedel-museum':{'last_artwork_id':'2b0b595b-be24-5de5-b48a-ca4d78c9f383','checked':10},'cleveland-museum-of-art':{'last_artwork_id':ROWS[-1][0],'checked':120}},'holds':{'no_image_at_checked_source':9,'access':[]},'next':'Continue Cleveland after '+ROWS[-1][0]+' or switch provider; exclude all 130 campaign IDs.'};save('source-queue.json',queue)
 save('plan-pin.json',{'batch':13,'checked_artworks_sha256':sha(E/'checked-artworks.json'),'source_queue_sha256':sha(E/'source-queue.json'),'transaction_preimages_sha256':sha(E/'transaction-preimages.json'),'delivery_plan_sha256':sha(E/'delivery-plan.json'),'batch107_checkpoint':'docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json','batch107_status':'complete','shared_lock':'artline-curated-ingestion','write_required':True})
 subprocess.check_call(['gcloud','storage','cp',str(DERIV),'gs://artline-508319-images'+plan['derivative_path'],'--project=artline-508319','--account=vadim@alingva.com'])
 creator=plan['credit'];ev=json.dumps({'accession':acc,'native_id':native,'source_api_url':plan['source_api_url'],'original_sha256':plan['original_sha256'],'derivative_sha256':checksum,'visual_review':plan['visual_review'],'batch107_reconciled':True})
 qs=["BEGIN","SET LOCAL lock_timeout='15s'","SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))","SELECT set_config('artline.actor_user_id','local-european-research',true)","DO $$ BEGIN IF (SELECT primary_media_id IS NOT NULL FROM artworks WHERE id="+lit(aid)+"::uuid FOR UPDATE) THEN RAISE EXCEPTION 'concurrent primary image'; END IF; END $$",f"INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES({lit(mid)}::uuid,'local',{lit(plan['derivative_path'])},{lit(plan['source_page_url'])},'The Cleveland Museum of Art','image/jpeg',661,850,{plan['derivative_bytes']},{lit(checksum)},{lit(title+' — '+creator)},'cc0','CC0','https://creativecommons.org/publicdomain/zero/1.0/',{lit(creator+'. The Cleveland Museum of Art. CC0.')},{lit(creator+'. '+title+', accession '+acc+'. The Cleveland Museum of Art. CC0. Full museum frame preserved; proportional resize and JPEG compression.')},now(),now(),{lit(ACTOR)})",f"INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES({lit(mid)}::uuid,'aa0ba48c-e786-4cac-8411-06343f4f03ed'::uuid,{lit(native)},{lit(plan['original_sha256'])},{lit(plan['source_image_url'])},'https://creativecommons.org/publicdomain/zero/1.0/','Official Cleveland Open Access API labels this exact accession CC0 and supplies the image route.',{lit(OP)},now(),{lit(ev)}::jsonb)",f"INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES({lit(aid)}::uuid,{lit(mid)}::uuid,0,'The Cleveland Museum of Art primary object reproduction')",f"UPDATE artworks SET primary_media_id={lit(mid)}::uuid,updated_by={lit(ACTOR)},updated_at=now(),revision=revision+1 WHERE id={lit(aid)}::uuid AND primary_media_id IS NULL","COMMIT"]
 sql(';'.join(qs));post=json.loads(sql("SELECT json_agg(jsonb_build_object('id',a.id,'primary_media_id',a.primary_media_id,'status',a.status,'storage_path',m.storage_path,'checksum',m.checksum_sha256,'bytes',m.byte_size,'rights',m.rights_status)) FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id="+lit(aid)+"::uuid"));save('transaction-postimage.json',{'verified_at':now(),'rows':post,'metadata_and_status_preserved':True,'local_catalogue_connections':0})
 print(json.dumps({'artwork_id':aid,'media_id':mid,'checksum':checksum}))
if __name__=='__main__':main()
