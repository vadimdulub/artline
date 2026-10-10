"""Freeze wave65 and verify all inherited and new evidence pins."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-tenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='8a1c99b9c654f989a8f0eb2df58c9ce205a57f5b8846572dbd7716056b80f091'
 changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==1
 for dep in prior['artifacts']:
  if dep['path'] in changed:
   c=changed[dep['path']];saved=m.load(Path(c['backup_path']));assert sha(Path(c['backup_path']))==c['backup_sha256'];assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==dep['sha256']==c['before_sha256'];assert sha(m.ROOT/dep['path'])==c['after_sha256'];continue
  a.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.b.prior.old.h.OLD else a.checked(dep)
 p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
 with m.connect() as db:verified=a.verify(db,p,digest)
 report=m.load(m.RUN/'verification-after-wave-65.json');assert report['verified_new_artworks']==7454 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==187 and not report['unrelated_coverage_changes_since_prior_report']
 assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_tenth_museum_changes'])==2
 assert (report['after']['museums_below_100'],report['after']['museums_below_200'])==(1161,1288)
 csvcounts={}
 for name,count in [('added-artworks-after-wave-65.csv',7454),('reconciled-artworks-after-wave-65.csv',785),('museum-coverage-after-wave-65.csv',1491),('gac-date-enrichments-after-wave-65.csv',6)]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==49 and checks['historical_tests_passed']==1126 and checks['cumulative_verified_tests']==1175 and checks['replay_zero_writes']
 external=prior['external_artifacts']+list(checks['logs'].values())+[m.load(a.RUN/'logs-finalized-001.json')['completed_delivery_log']]+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=p['backup_path'],sha256=p['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 grouped={}
 for dep in external:
  assert dep['path'] not in grouped or grouped[dep['path']]==dep;grouped[dep['path']]=dep
 external=list(grouped.values())
 for dep in external:assert sha(Path(dep['path']))==dep['sha256']
 other=prior['other_job_status_reference'];a.checked(other)
 paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*tenth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-65*')}

 paths|={m.ROOT/v['path'] for v in m.load(a.RUN/'physical-comparison-context-001.json.gz')['dependencies']}
 artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
 result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=7454,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=187,source_pass_museums=350,source_pass_institutions=351,new_additions=217,new_existing_links=0,verification=verified,museum_changes=report['france_tenth_museum_changes'],museums_below_100=1161,museums_below_200=1288,new_tests_passed=49,historical_tests_passed=1126,cumulative_verified_tests=1175,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=other,other_job_totals_separate=True,next_work='Strasbourg CEDS104 and Bayonne123 eligible works exceed100; Belfort49, Saint-Denis45 and Honfleur44 remain below100. All preferred200 targets remain unfinished. Preserve114 captured holds and3102 distinct index-held/unselected leads. Research other eligible works and reconcile physical units, editions and sparse duplicates without quota overrides. This pass made217 verified additions, so no repeated blocking condition. Global goal remains active with1161 canonical museums below100 linked records. All workers completed. Baltimore access hold remains; no retry or alternate-route bypass.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=217,campaign_new=7454,campaign_links=785,museums_below100=1161)),flush=True)
if __name__=='__main__':main()
