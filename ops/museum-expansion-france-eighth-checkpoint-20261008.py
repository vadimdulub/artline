"""Freeze wave63 and verify all inherited and new evidence pins."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-eighth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='f53e1cb17359f63f1f1558e2b5a7453eb2494e86fa54e4a4a0de1ff6a54d9191'
 changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==1
 for dep in prior['artifacts']:
  if dep['path'] in changed:
   c=changed[dep['path']];saved=m.load(Path(c['backup_path']));assert sha(Path(c['backup_path']))==c['backup_sha256'];assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==dep['sha256']==c['before_sha256'];assert sha(m.ROOT/dep['path'])==c['after_sha256'];continue
  a.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.b.prior.old.h.OLD else a.checked(dep)
 p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
 with m.connect() as db:verified=a.verify(db,p,digest)
 report=m.load(m.RUN/'verification-after-wave-63.json');assert report['verified_new_artworks']==6918 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==178 and not report['unrelated_coverage_changes_since_prior_report']
 assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_eighth_museum_changes'])==4
 assert (report['after']['museums_below_100'],report['after']['museums_below_200'])==(1167,1288)
 csvcounts={}
 for name,count in [('added-artworks-after-wave-63.csv',6918),('reconciled-artworks-after-wave-63.csv',785),('museum-coverage-after-wave-63.csv',1491),('gac-date-enrichments-after-wave-63.csv',6)]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==32 and checks['historical_tests_passed']==1046 and checks['cumulative_verified_tests']==1078 and checks['replay_zero_writes']
 external=prior['external_artifacts']+list(checks['logs'].values())+[m.load(a.RUN/'logs-finalized-001.json')['completed_delivery_log']]+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=p['backup_path'],sha256=p['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 grouped={}
 for dep in external:
  assert dep['path'] not in grouped or grouped[dep['path']]==dep;grouped[dep['path']]=dep
 external=list(grouped.values())
 for dep in external:assert sha(Path(dep['path']))==dep['sha256']
 other=prior['other_job_status_reference'];a.checked(other)
 paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*eighth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-63*')}

 paths|={m.ROOT/v['path'] for v in m.load(a.RUN/'physical-comparison-context-001.json.gz')['dependencies']}
 artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
 result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=6918,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=178,source_pass_museums=350,source_pass_institutions=351,new_additions=246,new_existing_links=0,verification=verified,museum_changes=report['france_eighth_museum_changes'],museums_below_100=1167,museums_below_200=1288,new_tests_passed=32,historical_tests_passed=1046,cumulative_verified_tests=1078,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=other,other_job_totals_separate=True,next_work='La Châtre117, Arbois112, Fabre116 and Nice119 eligible works exceed100; Montargis82 remains below100. All preferred200 targets remain unfinished. Preserve19 captured holds and4208 index-held/unselected leads. This pass made246 verified additions, so no repeated blocking condition. Global goal remains active with1167 canonical museums below100 linked records. All workers completed. Baltimore access hold remains; no retry or alternate-route bypass.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=246,campaign_new=6918,campaign_links=785,museums_below100=1167)),flush=True)
if __name__=='__main__':main()
