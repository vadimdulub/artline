#!/usr/bin/env python3
"""Apply the owner-authorized pinned Danish selection to local or production."""
import argparse,hashlib,importlib.util,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-painters-20260913'
PIN='71ce94f8d7dba2048ce139de6934f3385c9c5ce8df262cd828d2d5c3b6aa2b66'
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['preview','apply']);p.add_argument('--target',choices=['local','production'],required=True);p.add_argument('--label',required=True);a=p.parse_args()
 path=RUN/'batch';assert hashlib.sha256((path/'manifest.json').read_bytes()).hexdigest()==PIN
 env=dict(os.environ);env.pop('ARTLINE_TEST_DATABASE_URL',None);env['DATABASE_URL']='postgres://127.0.0.1/artline?sslmode=disable' if a.target=='local' else core.cloud_dsn()
 cmd=['/tmp/artline-ingest-danish','-dir',str(path),'-manifest-sha',PIN,'-reports',str(RUN/a.label),'-target',a.target]
 if a.phase=='apply':cmd.append('-apply')
 subprocess.run(cmd,env=env,check=True)
