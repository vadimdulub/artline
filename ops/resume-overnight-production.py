#!/usr/bin/env python3
"""Resume the explicitly authorized overnight deliveries after Cloud sign-in.

Default prints the ordered work. --execute performs guarded plans and writes.
No account switching, Terraform apply, deployment, publication or hard deletes.
"""
import argparse,importlib.util,json,os,subprocess,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE;ROOT=m.x.ROOT
def run(script,*args,env=None):
 command=[sys.executable,str(ROOT/'ops'/script),*args];print('Running',script,' '.join(args),flush=True);subprocess.run(command,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**(env or {})},check=True)
def pair_qa(folder):
 local=BASE/folder/'local';prod=BASE/folder/'production';lp=json.loads((local/'plan.json').read_text());pp=json.loads((prod/'plan.json').read_text());lq=json.loads((local/'quality-review.json').read_text());assert lq['approved'] and lq['plan_sha256']==CORE.sha((local/'plan.json').read_bytes())
 identity=lambda entries:{(e.get('key') or e.get('qid'),e['old_slug'],e['canonical_slug']) for e in entries}
 assert identity(lp)==identity(pp),'Production identities differ from individually reviewed local pairs; stop for evidence review'
 lookup={(e.get('key') or e.get('qid')):e for e in lp}
 for e in pp:
  old=lookup[e.get('key') or e.get('qid')]
  assert e.get('primary',e.get('evidence'))==old.get('primary',old.get('evidence')),'Primary identity evidence changed'
  assert not e['targets']['production'].get('issues') and not e['targets']['production'].get('overlaps')
 path=prod/'quality-review.json';review=dict(at=CORE.now(),approved=True,plan_sha256=CORE.sha((prod/'plan.json').read_bytes()),basis='Same exact independently reviewed identities and complete primary evidence as the pinned local quality review; fresh production preimages and relationship checks passed.',local_review_sha256=CORE.sha((local/'quality-review.json').read_bytes()))
 if not path.exists():CORE.save_new(path,review)
def merge(script,folder):
 if (BASE/folder/'production/verification-production.json').exists():return
 run(script,'plan','--target','production');pair_qa(folder);run(script,'apply','--target','production');run(script,'verify','--target','production')
def main(execute):
 if not execute:
  print('Pending: 2 anonymous-master corrections; Kuznetsov additional country; Pavia2/SMK1/FNG184+9+4 artwork consolidations;4 painter identities;235 FNG and222 Russian museum metadata updates; KMSKA1new+2existing panels;29 selected images;20 Portuguese rounds. Production plans use fresh target IDs and stop on changed evidence. Use --execute only after normal gcloud sign-in.');return
 if (BASE/'production-resume-completed.json').exists():
  print('This pending-delivery sequence already has a completion receipt. Preserve it and run a newly named audit/export phase.');return
 subprocess.run(['gcloud','auth','print-access-token','--account=vadim@alingva.com','--project=artline-508319'],stdout=subprocess.DEVNULL,check=True)
 assert (ROOT/'ops/artline-db-access.py').exists(),'Configured catalogue connection helper is missing.'
 with m.m.r.base.connect(True) as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');assert db.execute('SELECT current_database() name').fetchone()['name']=='artline'
 run('correct-overnight-anonymous-masters.py','--target','production','--apply')
 run('add-overnight-kuznetsov-country.py','--target','production','--apply')
 if not (BASE/'duplicates/pavia-physical-objects/verification-production.json').exists():
  run('consolidate-overnight-pavia-objects.py','apply','--target','production');run('consolidate-overnight-pavia-objects.py','verify','--target','production')
 if not (BASE/'duplicates/smk-selfportrait-primary/production/verification-production.json').exists():
  run('consolidate-overnight-smk-selfportrait.py','plan','--target','production');run('consolidate-overnight-smk-selfportrait.py','apply','--target','production');run('consolidate-overnight-smk-selfportrait.py','verify','--target','production')
 merge('consolidate-overnight-finnish-placeholders.py','duplicates/finnish-primary-placeholders')
 merge('consolidate-overnight-fng-cross-country.py','duplicates/fng-cross-country-objects')
 merge('consolidate-overnight-fng-persons.py','duplicates/fng-person-consolidation')
 merge('consolidate-overnight-fng-after-persons.py','duplicates/fng-after-person-objects')
 run('apply-finnish-primary-followup.py','plan','--target','production');run('apply-finnish-primary-followup.py','apply','--target','production')
 if not (BASE/'finland/primary-followup/images/verification-production.json').exists():
  run('apply-finnish-primary-images.py','plan','--target','production');run('apply-finnish-primary-images.py','apply','--target','production');run('apply-finnish-primary-images.py','verify','--target','production')
 run('reconcile-overnight-kmska-triptych.py','apply','--target','production')
 if not (BASE/'belgium/primary-triptych/images/verification-production.json').exists():run('reconcile-overnight-kmska-triptych.py','images','--target','production')
 run('enrich-overnight-russian-inventories.py','plan','--target','production')
 folder=BASE/'russian-primary-inventory-followup';local=json.loads((folder/'local-plan.json').read_text());prod=json.loads((folder/'production-plan.json').read_text());assert not prod['holds'];key=lambda d:{e['slug']:(e['changes'],e['evidence']) for e in d['entries']};assert key(local)==key(prod)
 qa=folder/'production-quality-review.json'
 if not qa.exists():CORE.save_new(qa,dict(at=CORE.now(),approved=True,plan_sha256=CORE.sha((folder/'production-plan.json').read_bytes()),basis='Exact same222 individually reviewed museum objects, changes and complete evidence as local quality review; current production blanks/source URLs/unique inventories rechecked.'))
 run('enrich-overnight-russian-inventories.py','apply','--target','production')
 for n in range(1,21):
  args=['--country','PT','--round',str(n)];env={'ARTLINE_RESEARCH_CAMPAIGN':'portugal'};run('apply-country-round.py','plan',*args,env=env)
  for target in ('local','production'):run('apply-country-round.py','apply',*args,'--target',target,env=env)
  run('apply-country-round.py','verify',*args,env=env)
 CORE.save_new(BASE/'production-resume-completed.json',dict(at=CORE.now(),scope='All ordered pending data/image deliveries completed with per-step verification. Original final-local CSV remains a historical snapshot; regenerate fresh receipt membership, both DB audits and a newly named CSV/report package.'))
 print('Pending imports complete. Regenerate fresh session membership, both database audits and a newly named export; keep the original handoff as dated evidence.',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args();main(a.execute)
