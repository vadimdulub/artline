import importlib.util,requests,subprocess,base64,hashlib
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.base.load(m.RUN/'gap-final-plan-v2.json.gz');token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip();prefix='assets/artworks/imported/painter-key-artworks-20261008/'
r=requests.get('https://storage.googleapis.com/storage/v1/b/artline-508319-images/o',params={'prefix':prefix,'maxResults':1000,'fields':'items(name,size,md5Hash,generation),nextPageToken'},headers={'Authorization':'Bearer '+token},timeout=45);r.raise_for_status();data=r.json();assert not data.get('nextPageToken');by={i['name']:i for i in data.get('items',[])}
for row in rows:
 p=row['prepared'];obj=by[p['path'].lstrip('/')];file=Path.cwd()/'apps/web/public'/p['path'].lstrip('/');assert int(obj['size'])==p['byte_size'];assert obj['md5Hash']==base64.b64encode(hashlib.md5(file.read_bytes()).digest()).decode()
m.save('upload-verification.json',dict(passed=True,count=len(rows),objects=list(by.values()),plan_sha256=m.base.digest(m.RUN/'gap-final-plan-v2.json.gz')));print('Upload checksums verified',len(rows))
