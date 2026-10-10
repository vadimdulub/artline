#!/usr/bin/env python3
"""Reuse bounded museum adapters for the fixed second sample."""
import argparse,importlib.util,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=mod('round2','ops/random-5000-museums-round2-20261006.py');r=t.r;RUN=t.RUN
def primary(phase):
 p=mod('old_adapters','ops/research-random-5000-primary-20261006.py');p.RUN=RUN;p.r.RUN=RUN;p.r.PORT=55483
 if phase=='moma':
  x=mod('moma_adapter','ops/research-artwork-location-primary-20261004.py');x.r.RUN=RUN;x.r.PORT=55483;x.source=p.cached_source;x.moma(p.index(x))
 else:getattr(p,phase)()
def refine():
 p=mod('primary_refine','ops/refine-random-5000-primary-20261006.py');p.RUN=RUN;p.r.RUN=RUN;p.p.r.RUN=RUN;p.main()
def backup():
 data=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791313987669','--instance=artline-postgres','--project=artline-508319','--format=json']))
 assert data['status']=='SUCCESSFUL';r.save(t.BACKUP/'production-backup-verified.json',data);r.save(RUN/'backups.json',{'at':r.now(),'production':data,'local_database_writes':0})
def web():
 p=mod('web_review','ops/review-random-5000-web-discovery-20261006.py');p.RUN=RUN;p.r.RUN=RUN;oldload=p.r.load
 def load(path):
  path=Path(path)
  if path.name=='wikiart-holding-plan-v3.json.gz':path=path.with_name('wikiart-holding-plan-v5.json.gz')
  if path.name=='cached-institution-authorities.json.gz':path=path.with_name('institution-authorities-complete.json.gz')
  return oldload(path)
 p.r.load=load;p.run()
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['fng','moma','france','lombardia','backup','web','refine']);a=ap.parse_args()
 if a.phase in ['backup','web','refine']:globals()[a.phase]()
 else:primary(a.phase)
