"""Create/poll the reviewed batch backup after the observed operation completes."""
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-kazantzakis-more-resume-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
a,m,RUN=r.a,r.m,r.RUN
DESCRIPTION='Before selected Kazantzakis continuation 20261010 wave121'
OTHER='8dc37cde-e0c5-458f-a8c2-1f9400000024'

def call(args):
    output=subprocess.check_output(['gcloud','sql']+args+['--project=artline-508319','--format=json'],text=True)
    return json.loads(output)

def minimal_operation(op):
    return {k:op[k]for k in ['name','operationType','status','insertTime','startTime','endTime','targetId','error']if k in op}

def create():
    dest=RUN/'cloud-backup-request-001.json';assert not dest.exists()
    op=call(['operations','describe',OTHER]);assert op['status']=='DONE'and not op.get('error'),minimal_operation(op)
    m.save(RUN/'previous-backup-completed-001.json',dict(at=m.now(),operation=minimal_operation(op),policy='Observed unrelated backup finished; no modification or cancellation.'))
    result=call(['backups','create','--instance=artline-postgres','--description='+DESCRIPTION,'--async'])
    if isinstance(result,list):assert len(result)==1;result=result[0]
    m.save(dest,dict(at=m.now(),description=DESCRIPTION,operation=minimal_operation(result),plan_reference=a.reference(a.PLAN),script_reference=a.reference(Path(__file__).resolve())))
    print(json.dumps(minimal_operation(result)),flush=True)

def poll():
    request=m.load(RUN/'cloud-backup-request-001.json');name=request['operation']['name'];op=call(['operations','describe',name])
    seq=len(list(RUN.glob('cloud-backup-observation-*.json')))+1
    m.save(RUN/('cloud-backup-observation-'+str(seq).zfill(3)+'.json'),dict(at=m.now(),operation=minimal_operation(op)))
    if op['status']!='DONE':print(json.dumps(minimal_operation(op)),flush=True);return
    assert not op.get('error'),minimal_operation(op)
    backups=call(['backups','list','--instance=artline-postgres','--filter=description="'+DESCRIPTION+'"']);assert len(backups)==1
    backup=call(['backups','describe',str(backups[0]['id']),'--instance=artline-postgres'])
    assert backup['status']=='SUCCESSFUL'and backup['description']==DESCRIPTION and backup['instance']=='artline-postgres'
    m.save(a.RUN/'cloud-backup-001.json',backup)
    m.save(RUN/'cloud-backup-completed-001.json',dict(at=m.now(),operation=minimal_operation(op),backup_reference=a.reference(a.RUN/'cloud-backup-001.json'),plan_reference=a.reference(a.PLAN)))
    print(json.dumps({k:backup[k]for k in ['id','status','description','startTime','endTime']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['create','poll']);args=p.parse_args()
    create()if args.command=='create'else poll()
