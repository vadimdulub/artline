#!/usr/bin/env python3
"""Pin wave53 delivery and preserve the superseded root README explicitly."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-baltimore-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='f7044ae5292b085019ba840d4c75ca9a5c2dd45b53af403774e25ae64d88616c'
 backup=m.BACKUP/'baltimore-root-readme-before-001.json.gz';saved=m.load(backup);readme=m.RUN/'README.md';relative=str(readme.relative_to(m.ROOT));oldref=next(x for x in prior['artifacts'] if x['path']==relative)
 assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==oldref['sha256']
 for dep in prior['artifacts']:
  if dep==oldref:continue
  a.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.old.h.OLD else a.checked(dep)
 change=dict(path=relative,before_sha256=saved['sha256'],after_sha256=sha(readme),backup_path=str(backup),backup_sha256=sha(backup))
 m.save(a.RUN/'root-readme-supersession-001.json',dict(at=m.now(),**change,policy='Intentional wave53 progress update with all prior README bytes preserved. Historical plans, reports and evidence unchanged.'))
 p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
 with m.connect() as db:verified=a.verify(db,p,digest)
 report=m.load(m.RUN/'verification-after-wave-53.json');assert report['verified_new_artworks']==5447 and report['verified_existing_artworks_linked']==767 and report['institutions_with_new_records_or_reconciled_holdings']==164 and not report['unrelated_coverage_changes_since_prior_report']
 counts={}
 for name,n in [('added-artworks-after-wave-53.csv',5447),('reconciled-artworks-after-wave-53.csv',767),('museum-coverage-after-wave-53.csv',1491),('gac-date-enrichments-after-wave-53.csv',6)]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==n;counts[name]=n
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==14 and checks['historical_tests_passed']==830
 external=prior['external_artifacts']+list(checks['logs'].values())+[dict(path=str(backup),sha256=sha(backup)),dict(path=p['backup_path'],sha256=p['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 external=list({x['path']:x for x in external}.values())
 for dep in external:assert sha(Path(dep['path']))==dep['sha256']
 other=prior['other_job_status_reference'];a.checked(other)
 paths={m.ROOT/x['path'] for x in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve(),readme}
 for directory in [a.RUN,m.RUN/'native/princeton']:paths|={p for p in directory.rglob('*') if p.is_file()}
 paths|={p for p in (m.ROOT/'ops').glob('*baltimore*20261007.py')};paths|={p for p in m.RUN.glob('*after-wave-53*')}
 artifacts=[a.reference(p) for p in sorted(paths)];assert len({x['path'] for x in artifacts})==len(artifacts)
 result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=5447,campaign_existing_links=767,institutions_with_new_records_or_reconciled_holdings=164,source_pass_museums=349,source_pass_institutions=350,new_additions=21,new_existing_links=0,verification=verified,museums_below_100=report['after']['museums_below_100'],new_tests_passed=14,historical_tests_passed=830,cumulative_verified_tests=844,plan_sha256=digest,csv_counts_verified=counts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=[change],other_job_status_reference=other,other_job_totals_separate=True,next_work='Continue Princeton public-API selection and reconcile its27 pending records. Initial public search and priority-icon sample are evidence, not approved additions or a counted completed source pass. Baltimore has22 eligible records,78 short of100; two captured holds and221 uncaptured leads remain excluded. Native source is on challenge access hold with no retry scheduled. Detroit has100 eligible records and needs100 more for preferred200. No background worker assumed. Overall1197 museums remain below100.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=21,baltimore=verified['current_counts'],campaign_new=5447,campaign_links=767,museums_below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
