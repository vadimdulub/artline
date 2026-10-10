"""Bounded current national catalogue query scoped to one museum, M0284."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-girodet-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
URL='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'
def main():
 dest=RUN/'joconde-current-001.json.gz';assert not dest.exists()
 response=requests.get(URL,params={'Code_Museofile__exact':'M0284','page_size':250},headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded single museum metadata)'},timeout=(15,60));raw=response.content;assert len(raw)<6_000_000
 body=RUN/'captures/joconde-current-001.body.gz';body.parent.mkdir(parents=True,exist_ok=True);assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(body.relative_to(m.ROOT)));m.save(RUN/'captures/joconde-current-001.json',rc);response.raise_for_status();data=response.json();print(json.dumps(dict(meta=data.get('meta'),first=data.get('data',[{}])[0],links=data.get('links')),ensure_ascii=False),flush=True)
 assert data['meta']['total']<=250 and not data['links'].get('next');assert all(v['Code_Museofile']=='M0284' for v in data['data']);m.save(dest,dict(at=m.now(),receipt=rc,data=data,read_only=True))
if __name__=='__main__':main()
