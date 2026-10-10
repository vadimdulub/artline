"""Resolve comparator evidence and legacy inventory spellings without changing records."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-girodet-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);m=i.m;RUN=i.RUN
TARGETS=['064e06fb-64e5-4823-acab-1a237f8467ff','febcd0d4-6726-53db-ab27-68e20841f7e6','89090e50-6787-568b-9366-20cab6617b63','a43ec18f-15b6-4faf-b477-c619907c6f7a','faa6d0c4-4beb-4033-90fe-283850ed249c','66c57f0e-6a5b-499b-859a-14d4d259948e']
def main():
 x=m.load(RUN/'production-identity-001.json.gz');cs=m.load(RUN/'production-identity-citations-001.json.gz')['citations'];out=[]
 for key,url in [('luce-pasture','https://www.wikiart.org/en/maximilien-luce/pasture-in-rolleboise-1939'),('luce-banks','https://www.wikiart.org/en/maximilien-luce/the-banks-of-the-seine-in-the-surroundings-of-rolleboise-1935')]:
  p=RUN/'captures'/(key+'.json');body=p.with_suffix('.body.gz')
  with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected same-work comparator)'},timeout=(12,45),stream=True) as r:
   raw=b''
   for c in r.iter_content(65536):raw+=c;assert len(raw)<2_000_000
   assert not p.exists();body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),body_path=str(body.relative_to(m.ROOT)));m.save(p,rc);out.append(rc)
   if r.status_code in [403,429]:break
 with i.prod.connect() as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');legacy=db.execute('SELECT '+i.q.ARTCOLS+' FROM artworks a WHERE accession_number=ANY(%s) ORDER BY id',(['D.008.1.1','D00811','D 008 1 1'],)).fetchall()
 m.save(RUN/'comparator-context-001.json.gz',dict(at=m.now(),references=[i.ref(RUN/'production-identity-001.json.gz'),i.ref(RUN/'production-identity-citations-001.json.gz')],selected_existing_ids=TARGETS,artworks=[v for v in x['state']['artworks'] if v['id'] in TARGETS],citations=[v for v in cs if v['entity_id'] in TARGETS],legacy_inventory_hits=legacy,captures=out,read_only=True,unexecuted_identity_script='museum-expansion-girodet-identity-v2-20261009.py is not used; complete v1 identity capture plus this exact legacy-inventory query are authoritative.'))
 print(json.dumps(dict(comparators=len(TARGETS),legacy_inventory_hits=len(legacy),captured=[(v['status'],v['bytes']) for v in out])),flush=True)
if __name__=='__main__':main()
