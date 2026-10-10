"""Freeze wave68 and verify all inherited and new evidence pins."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-thirteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='74cb7096ecce5905a750bca49761f1d264fa1876ac8954da36814e8c922d4a9c'
 changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==1
 for dep in prior['artifacts']:
  if dep['path'] in changed:
   c=changed[dep['path']];saved=m.load(Path(c['backup_path']));assert sha(Path(c['backup_path']))==c['backup_sha256'];assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==dep['sha256']==c['before_sha256'];assert sha(m.ROOT/dep['path'])==c['after_sha256'];continue
  a.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.b.prior.old.h.OLD else a.checked(dep)
 p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
 with m.connect() as db:verified=a.verify(db,p,digest)
 report=m.load(m.RUN/'verification-after-wave-68.json');assert report['verified_new_artworks']==8565 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==195 and not report['unrelated_coverage_changes_since_prior_report']
 assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_thirteenth_museum_changes'])==5
 assert sum(v['eligible_before']<200<=v['eligible_after'] for v in report['france_thirteenth_museum_changes'])==0
 assert (report['after']['museums_below_100'],report['after']['museums_below_200'])==(1155,1285)
 csvcounts={}
 for name,count in [('added-artworks-after-wave-68.csv',8565),('reconciled-artworks-after-wave-68.csv',785),('museum-coverage-after-wave-68.csv',1491),('gac-date-enrichments-after-wave-68.csv',6)]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==59 and checks['historical_tests_passed']==1277 and checks['cumulative_verified_tests']==1336 and checks['replay_zero_writes']
 external=prior['external_artifacts']+list(checks['logs'].values())+[m.load(a.RUN/'logs-finalized-001.json')['completed_delivery_log']]+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=p['backup_path'],sha256=p['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 grouped={}
 for dep in external:
  assert dep['path'] not in grouped or grouped[dep['path']]==dep;grouped[dep['path']]=dep
 external=list(grouped.values())
 for dep in external:assert sha(Path(dep['path']))==dep['sha256']
 other=prior['other_job_status_reference'];a.checked(other)
 paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*thirteenth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-68*')}

 for name in ['physical-comparison-context-001.json.gz','physical-comparison-context-002.json.gz','manual-comparison-supplement-001.json.gz','final-object-context-001.json.gz']:
  paths|={m.ROOT/v['path'] for v in m.load(a.RUN/name)['dependencies']}
 artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
 result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=8565,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=195,source_pass_museums=350,source_pass_institutions=351,new_additions=571,new_existing_links=0,verification=verified,museum_changes=report['france_thirteenth_museum_changes'],museums_below_100=1155,museums_below_200=1285,new_tests_passed=59,historical_tests_passed=1277,cumulative_verified_tests=1336,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=other,other_job_totals_separate=True,next_work='Despiau-Wlérick 110, Musée de l’Image 121, La Piscine 151, Jean de La Fontaine 117 and Tomi Ungerer 119 now exceed 100 eligible works. Research further eligible objects toward 200 and continue underfilled museums elsewhere. Preserve 49 captured holds and 16762 index-held or unselected leads. This pass made 571 verified additions, so no repeated blocking condition. The global goal remains active with 1155 canonical museums below 100 linked records. All workers completed. Baltimore and Orsay Coubertin-page access holds remain; no retries or alternate retrieval.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=571,campaign_new=8565,campaign_links=785,museums_below100=1155)),flush=True)
if __name__=='__main__':main()
