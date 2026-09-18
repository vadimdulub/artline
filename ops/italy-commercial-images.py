#!/usr/bin/env python3
"""Selected Italy image additions under the confirmed public/commercial standard."""
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('italy_campaign',ROOT/'ops/italy-image-campaign.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
PREVIOUS=c.RUN
c.RUN=ROOT/'docs/research/italy-commercial-images-20260917'
c.BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/italy-commercial-images-20260917')
c.SOURCE_IMAGES=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/italy-commercial-images-20260917')
c.core.VERSION='italy-commercial-selected-images-v1'
c.core.HOSTS.add('collezioni.museoegizio.it')
c.core.PROVIDERS['italy-egizio']='Museo Egizio, Torino'
base_attach=c.core.attach
def checked_attach(db,image,target):
    if image['provider']=='italy-egizio':
        spec=importlib.util.spec_from_file_location('egizio_source_review',ROOT/'ops/italy-egizio-native.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.validate(image)
    return base_attach(db,image,target)
c.core.attach=checked_attach
original_policy=c.institution_policy_reason
def policy(record):
    reason=original_policy(record)
    if reason:return reason
    for path in (PREVIOUS/'institution-rights-holds').glob('*.json'):
        saved=c.load(path)
        if record.get('institution_slug') in saved.get('institution_slugs',[saved['institution_slug']]):
            return saved['decision']
    return None
c.institution_policy_reason=policy

def audit():
    if not (c.RUN/'campaign.json').exists():
        c.save(c.RUN/'campaign.json',{'started_at':c.core.now(),
            'authorization':'User requested more pictures after confirming public/potentially commercial app use.',
            'scope':'Italy holdings and Italian artists abroad; selected eligible existing image gaps only.',
            'use':'Public or potentially commercial app',
            'publication':'Retain artwork review status; no new artwork records or metadata edits.',
            'prior_campaign':str(PREVIOUS.relative_to(ROOT)),
            'prior_retained_images':10,'prior_permissions_holds_preserved':True})
    c.audit()

def backup():
    c.BACKUP.mkdir(parents=True,exist_ok=True)
    dump=c.BACKUP/'local-before.dump'
    if not dump.exists():
        subprocess.run(['pg_dump','-Fc','--no-owner','--no-acl','-d','postgres://127.0.0.1/artline','-f',str(dump)],check=True)
    subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
    description='Italy selected commercial image additions 20260917'
    request=c.BACKUP/'production-backup-request.json'
    if not request.exists():
        result=subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres',
            '--project=artline-508319','--description='+description,'--format=json'])
        c.save(request,result)
    records=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres',
        '--project=artline-508319','--limit=30','--format=json']))
    cloud=next(r for r in records if r.get('description')==description)
    if cloud['status']!='SUCCESSFUL':raise ValueError('Production backup incomplete')
    c.save(c.RUN/'backups.json',{'local':{'path':str(dump),'bytes':dump.stat().st_size,
        'sha256':c.core.sha(dump.read_bytes()),'archive_directory_verified':True},'production':cloud})
    print('Fresh local and production recovery backups verified',flush=True)

def primary_research(label):
    spec=importlib.util.spec_from_file_location('commercial_primary',ROOT/'ops/italy-primary-photo-research.py')
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    p.c=c
    p.PHOTOS={'RL480-00038':39455810}
    cohort=c.RUN/'moroni-photo-selection'/'selected-existing-gaps.json'
    if not cohort.exists():
        c.save(cohort,{'records':[r for r in c.load(c.RUN/'eligible-image-gaps.json')
            if r['artwork_id']=='13b226b1-9f49-41b5-842e-2e58e876d47a']})
    p.select(label,'moroni-photo-selection')
    p.research(label)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['audit','backup','select','native-research','primary-research','prepare','apply','verify'])
    a.add_argument('--provider',default='met');a.add_argument('--label',default='round-01-selected')
    a.add_argument('--limit',type=int,default=24);a.add_argument('--work-type',default='painting')
    args=a.parse_args()
    if args.phase=='audit':audit()
    elif args.phase=='backup':backup()
    elif args.phase=='primary-research':primary_research(args.label)
    elif args.phase=='select':c.select(args.provider,args.limit,args.label,args.work_type)
    elif args.phase=='native-research':c.native_research(args.label,args.limit)
    elif args.phase=='prepare':c.prepare(args.label,args.limit)
    elif args.phase=='apply':c.apply(args.label,args.limit)
    else:c.verify(args.label,True)
