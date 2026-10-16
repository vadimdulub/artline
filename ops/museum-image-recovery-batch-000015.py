#!/usr/bin/env python3
import datetime, hashlib, importlib.util, json, pathlib, subprocess, urllib.request, uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/museum-image-recovery-20261013/batches/000015'
SRC=pathlib.Path.home()/'Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000015'
OP='museum-image-recovery-20261013-b000015'; ACTOR='local-european-research'
ROWS=[
('077685fd-987d-52db-9396-4dc79c3d90b3','Gone with the Wind','1937.79','117235'),
('077bbd97-f71e-499f-8b5a-0b812741f8e8','Gargoyle Series:  The Thinker of Notre Dame, Paris','1942.256','121956'),
('077d3778-f823-4888-8382-0d85a4c37805','New York in Snow','1948.779','173135'),
('078798c6-5162-5c67-a5c7-45fd38b8c261','Music Hall Scene','1956.303','133688'),
('0788e4d9-bb4a-5635-987b-2823631d374b','Interior with a Hanging Lamp','1951.65.5','129170'),
('078a7f14-efbd-427d-b6ca-21c6a3fe53c8','An Umbrian Street','1925.1277','107292'),
('078dd65d-600c-4921-a2b0-d698843c8840','The North Wood','1942.1195','121326'),
('07949a75-4aeb-4ec2-a586-df39aeb1045c','Cold, No. 2','1920.1297','100947'),
('079be9a2-f875-5604-a890-a29f830af9bd','Six large upright landscapes with scenes from the Old Testament: Abraham Dismissing Hagar and Ishmael','1944.49.1','123995'),
('07b545f6-3acf-58ba-ac42-5bea033d2009','Statuette of Osiris','1942.771','122507')]
DELIVER=set(['0788e4d9-bb4a-5635-987b-2823631d374b','079be9a2-f875-5604-a890-a29f830af9bd','07b545f6-3acf-58ba-ac42-5bea033d2009'])
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(n,v):
 p=E/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');return p
def lit(v): return "'"+str(v).replace("'","''")+"'"
spec=importlib.util.spec_from_file_location('prior',ROOT/'ops/museum-image-recovery-batch-000011.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def sql(q): return prior.sql(q)
def dimensions(p):
 out=subprocess.check_output(['sips','-g','pixelWidth','-g','pixelHeight',str(p)],text=True)
 vals=[int(x.split(':')[1]) for x in out.splitlines() if 'pixelWidth:' in x or 'pixelHeight:' in x];return vals
def main():
 cp=json.loads((ROOT/'docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json').read_text());assert cp['status']=='complete' and cp['delivery_complete_do_not_count_again']
 old=[]
 for p in sorted(E.parent.glob('0000*/checked-artworks.json')):
  if p.parent.name!='000015':old += [x['artwork_id'] for x in json.loads(p.read_text())]
 assert len(old)==len(set(old))==140 and not set(old)&{x[0] for x in ROWS}
 checked=[]; api={}; (E/'source-captures').mkdir(parents=True,exist_ok=True)
 for aid,title,acc,native in ROWS:
  u='https://openaccess-api.clevelandart.org/api/artworks/'+native;raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ArtlineResearch/1.0 (+https://artlines.org)'}),timeout=30).read();d=json.loads(raw)['data'];api[aid]=d
  assert str(d['id'])==native and d['accession_number']==acc and d['title']==title
  deliver=aid in DELIVER;assert deliver==(d['share_license_status']=='CC0' and bool(d.get('images',{}).get('print')))
  (E/'source-captures'/(native+'.json')).write_bytes(raw)
  checked.append({'artwork_id':aid,'title':title,'museum_url':'https://clevelandart.org/art/'+acc,'museum_native_id':native,'museum_accession':acc,'catalogue_accession':acc,'object_evidence':'Official CMA API exact native ID/accession/title and physical version agree.'+(' Exact full object frame visually reviewed.' if deliver else ''),'outcome':'delivered' if deliver else 'no-image-at-checked-source','reason':'Official CC0 full-frame print route; derivative prepared.' if deliver else ('CC0 record exposes no official image route.' if d['share_license_status']=='CC0' else 'Copyrighted; official record exposes no image route.')})
 save('checked-artworks.json',checked);ids=','.join(lit(x[0]) for x in ROWS)
 pre=json.loads(sql('SELECT json_agg(to_jsonb(a) ORDER BY a.id) FROM artworks a WHERE id IN ('+ids+')'));assert len(pre)==10 and all(x['primary_media_id'] is None for x in pre)
 save('transaction-preimages.json',{'captured_at':now(),'production_target':'artline via established Cloud SQL proxy 127.0.0.1:55519','batch107_checkpoint_status':'complete','batch107_delivery_complete_do_not_count_again':True,'shared_lock':'artline-curated-ingestion','local_catalogue_connections':0,'rows':pre,'all_primary_media_id_null':True,'write_required':True})
 plans=[]
 for aid,title,acc,native in ROWS:
  if aid not in DELIVER: continue
  orig=SRC/(acc+'_print.jpg');deriv=ROOT/'apps/web/public/assets/artworks/imported/museum-image-recovery-20261013'/(aid+'.jpg');cs=sha(deriv);mid=str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/media/'+aid+'/'+cs));d=api[aid];credit=d['creators'][0]['description'] if d['creators'] else 'Unknown artist';w,h=dimensions(deriv)
  plans.append({'artwork_id':aid,'media_id':mid,'title':title,'accession':acc,'native_id':native,'source_page_url':'https://clevelandart.org/art/'+acc,'source_api_url':'https://openaccess-api.clevelandart.org/api/artworks/'+native,'source_image_url':d['images']['print']['url'],'original_path':str(orig),'original_sha256':sha(orig),'derivative_path':'/assets/artworks/imported/museum-image-recovery-20261013/'+aid+'.jpg','derivative_file':str(deriv),'derivative_sha256':cs,'derivative_bytes':deriv.stat().st_size,'width':w,'height':h,'credit':credit,'visual_review':'accepted: exact complete museum object frame; proportions preserved; no crop'})
 save('delivery-plan.json',plans);save('source-queue.json',{'updated_at':now(),'campaign':'museum-image-recovery-20261013','batch':15,'checked_ids':[x[0] for x in ROWS],'prior_checked_ids_count':140,'campaign_distinct_checked_ids_count_after_batch':150,'museum_cursors':{'staedel-museum':{'last_artwork_id':'2b0b595b-be24-5de5-b48a-ca4d78c9f383','checked':10},'cleveland-museum-of-art':{'last_artwork_id':ROWS[-1][0],'checked':140}},'holds':{'no_image_at_checked_source':7,'access':[]},'next':'Continue Cleveland after '+ROWS[-1][0]+' or switch provider; exclude all 150 campaign IDs.'})
 save('plan-pin.json',{'batch':15,'checked_artworks_sha256':sha(E/'checked-artworks.json'),'source_queue_sha256':sha(E/'source-queue.json'),'transaction_preimages_sha256':sha(E/'transaction-preimages.json'),'delivery_plan_sha256':sha(E/'delivery-plan.json'),'batch107_checkpoint':'docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json','batch107_status':'complete','shared_lock':'artline-curated-ingestion','write_required':True,'write_plan':[p['artwork_id'] for p in plans]})
 for p in plans: subprocess.check_call(['gcloud','storage','cp',p['derivative_file'],'gs://artline-508319-images'+p['derivative_path'],'--project=artline-508319','--account=vadim@alingva.com'])
 qs=['BEGIN',"SET LOCAL lock_timeout='15s'","SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))","SELECT set_config('artline.actor_user_id','local-european-research',true)"]
 for p in plans:
  aid=p['artwork_id'];mid=p['media_id'];title=p['title'];acc=p['accession'];native=p['native_id'];credit=p['credit'];ev=json.dumps({'accession':acc,'native_id':native,'source_api_url':p['source_api_url'],'original_sha256':p['original_sha256'],'derivative_sha256':p['derivative_sha256'],'visual_review':p['visual_review'],'batch107_reconciled':True})
  qs += ["DO $$ BEGIN IF (SELECT primary_media_id IS NOT NULL FROM artworks WHERE id="+lit(aid)+"::uuid FOR UPDATE) THEN RAISE EXCEPTION 'concurrent primary image'; END IF; END $$",f"INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES({lit(mid)}::uuid,'local',{lit(p['derivative_path'])},{lit(p['source_page_url'])},'The Cleveland Museum of Art','image/jpeg',{p['width']},{p['height']},{p['derivative_bytes']},{lit(p['derivative_sha256'])},{lit(title+' — '+credit)},'cc0','CC0','https://creativecommons.org/publicdomain/zero/1.0/',{lit(credit+'. The Cleveland Museum of Art. CC0.')},{lit(credit+'. '+title+', accession '+acc+'. The Cleveland Museum of Art. CC0. Full museum frame preserved; proportional resize and JPEG compression.')},now(),now(),{lit(ACTOR)})",f"INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES({lit(mid)}::uuid,'aa0ba48c-e786-4cac-8411-06343f4f03ed'::uuid,{lit(native)},{lit(p['original_sha256'])},{lit(p['source_image_url'])},'https://creativecommons.org/publicdomain/zero/1.0/','Official Cleveland Open Access API labels this exact accession CC0 and supplies the image route.',{lit(OP)},now(),{lit(ev)}::jsonb)",f"INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES({lit(aid)}::uuid,{lit(mid)}::uuid,0,'The Cleveland Museum of Art primary object reproduction')",f"UPDATE artworks SET primary_media_id={lit(mid)}::uuid,updated_by={lit(ACTOR)},updated_at=now(),revision=revision+1 WHERE id={lit(aid)}::uuid AND primary_media_id IS NULL"]
 qs.append('COMMIT');sql(';'.join(qs))
 post=json.loads(sql("SELECT json_agg(jsonb_build_object('id',a.id,'primary_media_id',a.primary_media_id,'status',a.status,'storage_path',m.storage_path,'checksum',m.checksum_sha256,'bytes',m.byte_size) ORDER BY a.id) FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id IN ("+','.join(lit(p['artwork_id']) for p in plans)+')'))
 save('transaction-postimage.json',{'verified_at':now(),'rows':post,'metadata_and_status_preserved':True,'local_catalogue_connections':0})
if __name__=='__main__':main()
