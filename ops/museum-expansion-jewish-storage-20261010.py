"""Upload only exact reviewed image bytes to new, generation-guarded storage keys."""
import base64
import concurrent.futures
import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
import requests
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-jewish-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def main():
    p,digest=a.validate_plan();assert not(a.RUN/'storage-upload-001.json').exists()
    token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip()
    def upload(im):
        dest=a.RUN/'storage-receipts'/(im['media_id']+'.json')
        if dest.exists():
            old=a.m.load(dest);assert old['sha256']==im['sha256'] and old['path']==im['storage_path'];return old
        raw=Path(im['prepared_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==im['sha256'] and len(raw)==im['bytes']<=100000
        name=im['storage_path'].lstrip('/');url='https://storage.googleapis.com/storage/v1/b/'+a.BUCKET+'/o/'+quote(name,safe='')
        with requests.Session() as session:
            session.headers['Authorization']='Bearer '+token
            for attempt in range(4):
                response=session.get(url,timeout=(15,35));created=False
                if response.status_code==404:
                    response=session.post('https://storage.googleapis.com/upload/storage/v1/b/'+a.BUCKET+'/o',params=dict(uploadType='media',name=name,ifGenerationMatch=0),data=raw,headers={'Content-Type':'image/jpeg'},timeout=(15,45));created=True
                if response.status_code in [408,412,429,500,502,503,504] and attempt<3:time.sleep(2**attempt);continue
                response.raise_for_status();obj=response.json();assert obj['name']==name and int(obj['size'])==len(raw) and obj['md5Hash']==base64.b64encode(hashlib.md5(raw).digest()).decode()
                rc=dict(at=a.m.now(),media_id=im['media_id'],artwork_id=im['artwork_id'],path=im['storage_path'],sha256=im['sha256'],bytes=len(raw),generation=obj['generation'],created=created,plan_sha256=digest)
                a.m.save(dest,rc);return rc
        raise RuntimeError('Storage upload did not complete')
    checks=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for rc in pool.map(upload,p['images']):
            checks.append(rc)
            if len(checks)%25==0:print(json.dumps(dict(uploaded=len(checks),total=131)),flush=True)
    a.m.save(a.RUN/'storage-upload-001.json',dict(at=a.m.now(),plan_sha256=digest,checks=checks,script_reference=a.c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(uploaded=len(checks),created=sum(x['created'] for x in checks))),flush=True)

if __name__=='__main__':main()
