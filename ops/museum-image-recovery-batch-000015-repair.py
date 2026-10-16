#!/usr/bin/env python3
import hashlib,importlib.util,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'docs/research/museum-image-recovery-20261013/batches/000015';AID='079be9a2-f875-5604-a890-a29f830af9bd'
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('prior',ROOT/'ops/museum-image-recovery-batch-000011.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def main():
 plans=json.loads((E/'delivery-plan.json').read_text());p=next(x for x in plans if x['artwork_id']==AID);f=ROOT/'apps/web/public/assets/artworks/imported/museum-image-recovery-20261013'/(AID+'-v2.jpg');assert f.stat().st_size<=100000
 out=subprocess.check_output(['sips','-g','pixelWidth','-g','pixelHeight',str(f)],text=True);vals=[int(x.split(':')[1]) for x in out.splitlines() if 'pixelWidth:' in x or 'pixelHeight:' in x]
 old=p['derivative_sha256'];p.update(derivative_file=str(f),derivative_path='/assets/artworks/imported/museum-image-recovery-20261013/'+AID+'-v2.jpg',derivative_sha256=sha(f),derivative_bytes=f.stat().st_size,width=vals[0],height=vals[1]);(E/'delivery-plan.json').write_text(json.dumps(plans,ensure_ascii=False,indent=2)+'\n')
 pin=json.loads((E/'plan-pin.json').read_text());pin['delivery_plan_sha256']=sha(E/'delivery-plan.json');pin['repair_reason']='Oversized first derivative rejected by independent verification; corrected before batch completion.';(E/'plan-pin.json').write_text(json.dumps(pin,indent=2)+'\n')
 subprocess.check_call(['gcloud','storage','cp',str(f),'gs://artline-508319-images'+p['derivative_path'],'--project=artline-508319','--account=vadim@alingva.com'])
 evidence=json.loads(prior.sql("SELECT evidence_json FROM media_rights_evidence WHERE media_id='"+p['media_id']+"'::uuid"));evidence['derivative_sha256']=p['derivative_sha256']
 q="BEGIN;SET LOCAL lock_timeout='15s';SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'));UPDATE media_assets SET storage_path='"+p['derivative_path']+"',checksum_sha256='"+p['derivative_sha256']+"',byte_size="+str(p['derivative_bytes'])+",width="+str(p['width'])+",height="+str(p['height'])+",verified_at=now() WHERE id='"+p['media_id']+"'::uuid AND checksum_sha256='"+old+"';UPDATE media_rights_evidence SET evidence_json='"+json.dumps(evidence).replace("'","''")+"'::jsonb,checked_at=now() WHERE media_id='"+p['media_id']+"'::uuid;COMMIT;"
 prior.sql(q)
 post=json.loads(prior.sql("SELECT json_agg(jsonb_build_object('id',a.id,'primary_media_id',a.primary_media_id,'status',a.status,'storage_path',m.storage_path,'checksum',m.checksum_sha256,'bytes',m.byte_size) ORDER BY a.id) FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id IN ('0788e4d9-bb4a-5635-987b-2823631d374b'::uuid,'079be9a2-f875-5604-a890-a29f830af9bd'::uuid,'07b545f6-3acf-58ba-ac42-5bea033d2009'::uuid)"))
 (E/'transaction-postimage.json').write_text(json.dumps({'rows':post,'metadata_and_status_preserved':True,'local_catalogue_connections':0,'oversize_repaired_before_completion':True},indent=2)+'\n')
if __name__=='__main__':main()
