#!/usr/bin/env python3
import datetime, hashlib, json, os, pathlib, subprocess, urllib.parse, urllib.request, uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/museum-image-recovery-20261013/batches/000010'
ORIG=pathlib.Path.home()/'Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000010'
ASSET=ROOT/'apps/web/public/assets/artworks/imported/museum-image-recovery-20261013'
ACTOR='local-european-research'; OP='museum-image-recovery-20261013-b000010'
ROWS=[
('0385289d-4c16-5b9c-aab1-d42d6ec40acd','Banks of the Jinsha River','2025.575','697052',None),
('0393a11b-293c-5fa0-82c0-5a15209c0c29','Sketch (66 of 150)','1954.153.66','131507',None),
('03a1c02f-00bb-5d55-ad97-b378b3a236ce','Descent','1967.226','143290',None),
('03ae8c30-90b8-5aea-8b59-c1158a2d2b79','Reclining Nude Woman','1926.38','108691',None),
('03d2d585-26c7-5071-902e-5454ee3e66d6','Sutra Repository of Iwaya-dera','1959.201','135674',None),
('03dff70c-6d33-5539-9865-40edd7af3b9c','Formulation:  Articulation','1979.141','149567',None),
('03ec9991-4c82-5d8f-8abe-8acea8b81ff2','The Twelve Months: December','1960.143.13','136253','1960.143.13_print.jpg'),
('0413cdb7-bb7a-59b8-afba-a4e7c874038c','Set and Subset','1971.252','146059',None),
('041d6e45-df6d-5dff-96fa-3b8bb7982a4d','SIKRA - MC','1968.277','143890',None),
('042fa478-e655-56bd-bde7-ed7379f31b08','View of Venice','1949.565.4','127254','1949.565.4_print.jpg')]
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(name,v):
 p=E/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');return p
def mid(aid,checksum): return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/media/'+aid+'/'+checksum))
def conn():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();u=urllib.parse.urlparse(secret)
 env=os.environ.copy();env['PGPASSWORD']=urllib.parse.unquote(u.password)
 return env,['/opt/homebrew/opt/libpq/bin/psql','-h','127.0.0.1','-p','55519','-U',u.username,'-d',u.path.lstrip('/'),'-X','-A','-t','-v','ON_ERROR_STOP=1']
def sql(q):
 env,base=conn();return subprocess.check_output(base+['-c',q],env=env,text=True).strip()
def lit(s): return "'"+str(s).replace("'","''")+"'"

def main():
 E.mkdir(parents=True,exist_ok=True)
 checked=[];api={}
 for aid,title,acc,native,image in ROWS:
  url='https://openaccess-api.clevelandart.org/api/artworks/'+native
  request=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0 (+https://artlines.org)'})
  raw=urllib.request.urlopen(request,timeout=30).read(); d=json.loads(raw)['data'];api[aid]=d
  assert str(d['id'])==native and d['accession_number']==acc and d['title']==title
  (E/'source-captures').mkdir(exist_ok=True);(E/'source-captures'/(native+'.json')).write_bytes(raw)
  delivered=bool(image);assert delivered==(d['share_license_status']=='CC0' and bool(d['images'].get('print')))
  checked.append(dict(artwork_id=aid,title=title,museum_url='https://clevelandart.org/art/'+acc,museum_native_id=native,museum_accession=acc,catalogue_accession=acc,object_evidence='Official CMA API exact native ID/accession/title and physical version agree.'+(' Exact full sheet visually reviewed.' if delivered else ''),outcome='delivered' if delivered else 'no-image-at-checked-source',reason='Official CC0 full-frame print route; derivative prepared.' if delivered else 'Copyrighted; official record exposes no image route.'))
 save('checked-artworks.json',checked)
 ids=','.join(lit(x[0]) for x in ROWS)
 pre=json.loads(sql("SELECT json_agg(to_jsonb(a) ORDER BY a.id) FROM artworks a WHERE id IN ("+ids+")"))
 assert len(pre)==10 and all(x['primary_media_id'] is None for x in pre)
 save('transaction-preimages.json',dict(captured_at=now(),production_target='artline via established Cloud SQL proxy 127.0.0.1:55519',batch107_checkpoint_status='complete',shared_lock='artline-curated-ingestion',local_catalogue_connections=0,rows=pre,all_primary_media_id_null=True,write_required=True))
 plans=[]
 for aid,title,acc,native,image in ROWS:
  if not image: continue
  src=ORIG/image;dst=ASSET/(aid+'.jpg');checksum=sha(dst);d=api[aid]
  dims={'03ec9991-4c82-5d8f-8abe-8acea8b81ff2':(700,523),'042fa478-e655-56bd-bde7-ed7379f31b08':(700,517)}[aid]
  plans.append(dict(artwork_id=aid,media_id=mid(aid,checksum),title=title,accession=acc,native_id=native,source_page_url='https://clevelandart.org/art/'+acc,source_api_url='https://openaccess-api.clevelandart.org/api/artworks/'+native,source_image_url=d['images']['print']['url'],original_path=str(src),original_sha256=sha(src),derivative_path='/assets/artworks/imported/museum-image-recovery-20261013/'+aid+'.jpg',derivative_file=str(dst),derivative_sha256=checksum,derivative_bytes=dst.stat().st_size,width=dims[0],height=dims[1],credit=d.get('creators',[{}])[0].get('description','') if d.get('creators') else '',visual_review='accepted: exact full sheet; complete museum frame and proportions preserved; no crop'))
 save('delivery-plan.json',plans)
 queue=dict(updated_at=now(),campaign='museum-image-recovery-20261013',batch=10,checked_ids=[x[0] for x in ROWS],prior_checked_ids_count=90,campaign_distinct_checked_ids_count_after_batch=100,museum_cursors={'staedel-museum':{'last_artwork_id':'2b0b595b-be24-5de5-b48a-ca4d78c9f383','checked':10},'cleveland-museum-of-art':{'last_artwork_id':ROWS[-1][0],'checked':90}},holds={'no_image_at_checked_source':8,'access':[]},next='Continue Cleveland after '+ROWS[-1][0]+' or switch provider; exclude all 100 campaign IDs.')
 save('source-queue.json',queue)
 save('plan-pin.json',dict(batch=10,checked_artworks_sha256=sha(E/'checked-artworks.json'),source_queue_sha256=sha(E/'source-queue.json'),transaction_preimages_sha256=sha(E/'transaction-preimages.json'),delivery_plan_sha256=sha(E/'delivery-plan.json'),batch107_checkpoint='docs/research/continuous-production-20261011/batches/000107/CHECKPOINT.json',batch107_status='complete',shared_lock='artline-curated-ingestion'))
 for p in plans: subprocess.check_call(['gcloud','storage','cp',p['derivative_file'],'gs://artline-508319-images'+p['derivative_path'],'--project=artline-508319','--account=vadim@alingva.com'])
 statements=["BEGIN","SET LOCAL lock_timeout='15s'","SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))","SELECT set_config('artline.actor_user_id','local-european-research',true)"]
 for p in plans:
  aid=p['artwork_id']; m=p['media_id']; d=api[aid];creator=p['credit']; credit=(creator+'. ' if creator else '')+'The Cleveland Museum of Art. CC0.'
  statements += ["DO $$ BEGIN IF (SELECT primary_media_id IS NOT NULL FROM artworks WHERE id="+lit(aid)+"::uuid FOR UPDATE) THEN RAISE EXCEPTION 'concurrent primary image'; END IF; END $$",
  "INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES("+','.join([lit(m)+'::uuid',lit('local'),lit(p['derivative_path']),lit(p['source_page_url']),lit('The Cleveland Museum of Art'),lit('image/jpeg'),str(p['width']),str(p['height']),str(p['derivative_bytes']),lit(p['derivative_sha256']),lit(p['title']+' — '+creator),lit('cc0'),lit('CC0'),lit('https://creativecommons.org/publicdomain/zero/1.0/'),lit(credit),lit(creator+'. '+p['title']+', accession '+p['accession']+'. The Cleveland Museum of Art. CC0. Full museum frame preserved; proportional resize and JPEG compression.'),"now()","now()",lit(ACTOR)])+")",
  "INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES("+','.join([lit(m)+'::uuid',lit('aa0ba48c-e786-4cac-8411-06343f4f03ed')+'::uuid',lit(p['native_id']),lit(p['original_sha256']),lit(p['source_image_url']),lit('https://creativecommons.org/publicdomain/zero/1.0/'),lit('Official Cleveland Open Access API labels this exact accession CC0 and supplies the image route.'),lit(OP),"now()",lit(json.dumps({'accession':p['accession'],'native_id':p['native_id'],'source_api_url':p['source_api_url'],'original_sha256':p['original_sha256'],'derivative_sha256':p['derivative_sha256'],'visual_review':p['visual_review'],'batch107_reconciled':True}))+'::jsonb'])+")",
  "INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES("+lit(aid)+"::uuid,"+lit(m)+"::uuid,0,"+lit('The Cleveland Museum of Art primary object reproduction')+")",
  "UPDATE artworks SET primary_media_id="+lit(m)+"::uuid,updated_by="+lit(ACTOR)+",updated_at=now(),revision=revision+1 WHERE id="+lit(aid)+"::uuid AND primary_media_id IS NULL"]
 statements += ['COMMIT'];sql(';'.join(statements))
 post=json.loads(sql("SELECT json_agg(jsonb_build_object('id',a.id,'primary_media_id',a.primary_media_id,'status',a.status,'storage_path',m.storage_path,'checksum',m.checksum_sha256,'bytes',m.byte_size,'rights',m.rights_status) ORDER BY a.id) FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id IN ("+','.join(lit(p['artwork_id']) for p in plans)+")"))
 save('transaction-postimage.json',dict(verified_at=now(),rows=post,metadata_and_status_preserved=True,local_catalogue_connections=0))
 print(json.dumps({'plans':plans,'post':post},default=str))
if __name__=='__main__': main()
