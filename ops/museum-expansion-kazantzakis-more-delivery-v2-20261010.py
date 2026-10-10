"""Use the reconciled immutable plan with the established apply/readback contract."""
import argparse
import contextlib
import importlib.util
import io
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

d=module('d','museum-expansion-kazantzakis-more-delivery-20261010.py')
b=module('b','museum-expansion-kazantzakis-more-reconciled-20261010.py')
a,m,RUN=b.a,b.m,b.RUN
d.a=a

def apply(digest):
    assert not(RUN/'apply-command-001.json').exists()
    completed=m.load(RUN/'cloud-backup-completed-001.json');a.checked(completed['backup_reference'])
    plan,current=a.validate_plan();assert current==digest
    assert plan['supersedes_plan']==completed['plan_reference']==a.reference(b.ORIGINAL)
    policy=m.load(RUN/'policy-reconciliation-001.json');assert policy['live_preflight_repeated']and policy['records_unchanged']==105
    output=io.StringIO()
    with contextlib.redirect_stdout(output):a.apply(digest)
    receipt=m.load(a.RUN/(a.KEY+'-applied.json'))
    assert receipt['plan_sha256']==digest and receipt['created']==105 and receipt['local_unchanged']
    m.save(RUN/'apply-command-001.json',dict(at=m.now(),plan_sha256=digest,stdout=output.getvalue(),completed=True,
        applied_reference=a.reference(a.RUN/(a.KEY+'-applied.json')),policy_reconciliation_reference=a.reference(RUN/'policy-reconciliation-001.json'),
        script_reference=a.reference(Path(__file__).resolve())))
    print(output.getvalue(),end='',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['apply','verify','report']);parser.add_argument('--plan-sha',required=True);args=parser.parse_args()
    plan,digest=a.validate_plan();assert args.plan_sha==digest
    d.EXPECTED=digest
    if args.command=='apply':apply(digest)
    elif args.command=='verify':d.verify()
    else:d.report()
