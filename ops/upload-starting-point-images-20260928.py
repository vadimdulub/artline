import importlib.util,json,base64,hashlib,concurrent.futures
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path('ops/audit-production-release.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
out=Path('docs/research/production-starting-points-20260928');plan=json.loads((out/'catalogue-plan.json').read_bytes());rows=plan['inserts']['media_assets'];assert len(rows)==883
bucket=r.core.storage.Client(project='artline-508319',credentials=r.core.GcloudCredentials()).bucket(r.core.BUCKET)
# The separately completed decolonisation batch remains a research preview.
# Preserve its territorial/fair-use/unknown labels; never upgrade its clearance.
deep=r.ROOT/'docs/research/decolonization-deep-20260928'
qa=json.loads((deep/'visual-review.json').read_bytes());assert qa['approved']
assert hashlib.sha256((deep/'images.json').read_bytes()).hexdigest()==qa['images_sha256']
research={v['media_id']:v for v in json.loads((deep/'images.json').read_bytes())}
assert len(research)==10

def upload(m):
 if m['id'] in research:
  assert m['checksum_sha256']==research[m['id']]['sha256'] and m['storage_path']==research[m['id']]['path']
 else:
  assert m['rights_status'] in ['cc0','public_domain','licensed'] and m['verified_at'] and m['verified_by']
 path=m['storage_path'].lstrip('/');assert path.startswith('assets/artworks/imported/') and '..' not in path
 raw=(r.ROOT/'apps/web/public'/path).read_bytes();assert len(raw)==m['byte_size']<=100000 and hashlib.sha256(raw).hexdigest()==m['checksum_sha256'];md5=base64.b64encode(hashlib.md5(raw).digest()).decode();blob=bucket.get_blob(path);created=blob is None
 if created:
  blob=bucket.blob(path);blob.metadata={'sha256':m['checksum_sha256'],'license':m['license_label'],'source':m['source_page_url'],'release':'starting-points-20260928'};blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(raw,content_type=m['mime_type'],if_generation_match=0);blob.reload()
 assert blob.size==len(raw) and blob.md5_hash==md5
 print('Verified',path,flush=True);return {'media_id':m['id'],'path':path,'sha256':m['checksum_sha256'],'bytes':len(raw),'generation':blob.generation,'created':created}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:objects=list(pool.map(upload,rows))
r.core.save_new(out/'new-image-delivery.json',{'at':r.core.now(),'objects':objects})
