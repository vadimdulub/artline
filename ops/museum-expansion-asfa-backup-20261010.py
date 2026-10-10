"""Create and observe this selected delivery's own CloudSQL backup operation."""
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def command(args):
    result=subprocess.run(['gcloud','sql']+args+['--project=artline-508319','--format=json'],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)

def create():
    assert not(c.RUN/'cloud-backup-request-001.json').exists()
    result=command(['backups','create','--instance=artline-postgres','--description=Before selected ASFA248 artworks2 holdings142 images20261010','--async'])
    c.m.save(c.RUN/'cloud-backup-request-001.json',dict(at=c.m.now(),operation=result,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(result),flush=True)

def poll():
    assert not(c.RUN/'cloud-backup-001.json').exists();request=c.m.load(c.RUN/'cloud-backup-request-001.json')['operation']
    op=command(['operations','describe',request['name']]);n=len(list(c.RUN.glob('cloud-backup-observation-*.json')))+1
    c.m.save(c.RUN/('cloud-backup-observation-'+str(n).zfill(3)+'.json'),dict(at=c.m.now(),operation=op))
    if op['status']=='DONE':
        assert not op.get('error');bid=op['backupContext']['backupId'];backup=command(['backups','describe',str(bid),'--instance=artline-postgres']);assert backup['status']=='SUCCESSFUL';c.m.save(c.RUN/'cloud-backup-001.json',backup)
        print(json.dumps(dict(backup_id=bid,status=backup['status'],end=backup.get('endTime'))),flush=True)
    else:print(json.dumps(dict(operation=request['name'],status=op['status'])),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['create','poll']);args=parser.parse_args();globals()[args.command]()
