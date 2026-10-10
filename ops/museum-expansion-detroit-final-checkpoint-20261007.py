#!/usr/bin/env python3
"""Pin wave52 delivery and explicitly preserve the superseded README bytes."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-detroit-final-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists()
 prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='1bb84ef12601ee2a933bd9724ebdece28bfb8108c25d9835f6cb8da106c817ae'
 backup=m.BACKUP/'detroit-final-root-readme-before-001.json.gz';saved=m.load(backup);readme=m.RUN/'README.md';relative=str(readme.relative_to(m.ROOT));assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']
 oldref=next(x for x in prior['artifacts'] if x['path']==relative);assert oldref['sha256']==saved['sha256']
 for dep in prior['artifacts']:
  if dep==oldref:continue
  a.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.old.h.OLD else a.checked(dep)
 change=dict(path=relative,before_sha256=saved['sha256'],after_sha256=sha(readme),backup_path=str(backup),backup_sha256=sha(backup))
 m.save(a.RUN/'root-readme-supersession-001.json',dict(at=m.now(),**change,policy='Intentional wave52 progress update. All prior README bytes preserved; no historical report, plan or research evidence rewritten.'))
 plan,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
 with m.connect() as db:verification=a.verify(db,plan,digest)
 report=m.load(m.RUN/'verification-after-wave-52.json');assert report['verified_new_artworks']==5426 and report['verified_existing_artworks_linked']==767 and report['institutions_with_new_records_or_reconciled_holdings']==163 and not report['unrelated_coverage_changes_since_prior_report']
 csv_counts={}
 for name,n in [('added-artworks-after-wave-52.csv',5426),('reconciled-artworks-after-wave-52.csv',767),('museum-coverage-after-wave-52.csv',1491),('gac-date-enrichments-after-wave-52.csv',6)]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==n;csv_counts[name]=n
 checks=m.load(a.RUN/'checks-001.json');assert checks['offline_tests_passed']==830
 external=list(plan['external_evidence'])+list(checks['logs'].values())+[dict(path=str(backup),sha256=sha(backup)),dict(path=plan['backup_path'],sha256=plan['backup_sha256'])]
 for dep in external:assert sha(Path(dep['path']))==dep['sha256']
 other=prior['other_job_status_reference'];a.checked(other)
 paths={m.ROOT/x['path'] for x in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve(),readme}
 for directory in [a.RUN,m.RUN/'native/detroit-resume',m.RUN/'native/baltimore']:
  paths|={p for p in directory.rglob('*') if p.is_file()}
 paths|={p for p in (m.ROOT/'ops').glob('*detroit*20261007.py')}
 paths|={p for p in m.RUN.glob('*after-wave-52*')}
 artifacts=[a.reference(p) for p in sorted(paths)];assert len({x['path'] for x in artifacts})==len(artifacts)
 result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=5426,campaign_existing_links=767,institutions_with_new_records_or_reconciled_holdings=163,source_pass_museums=348,source_pass_institutions=349,new_additions=92,new_existing_links=2,verification=verification,museums_below_100=1197,tests_passed=830,new_tests_passed=8,plan_sha256=digest,csv_counts_verified=csv_counts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=[change],other_job_status_reference=other,other_job_totals_separate=True,next_work='Baltimore Museum of Art native catalogue discovery has begun. Its fresh scope contains one linked eligible artwork; no Baltimore additions or approved source selection are included in wave52 totals. Continue bounded source capture, creator/version identity review and selected additions. Detroit needs100 more eligible works for preferred200;18 captured holds and one timeout remain held. Overall1197 museums remain below100. No background capture worker is assumed by this checkpoint.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),new=92,existing_links=2,detroit=verification['current_counts'],campaign_new=5426,campaign_links=767,museums_below100=1197)),flush=True)
if __name__=='__main__':main()
