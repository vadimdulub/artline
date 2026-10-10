#!/usr/bin/env python3
"""Freeze wave59 and verify every retained delivered/research evidence pin."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fourth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='0721a7f80e6f9e445bba0d842ab64c14d05c01518944dd0339d3dcf852253624'
 research_path=a.RUN/'research-checkpoint-001.json';assert sha(research_path)=='efce77474d7deab8d8390ebfba2f6e50c7e3ca1a9bc37b9475627f33704872a7';research=m.load(research_path);changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==2
 for cp in [prior,research]:
  for dep in cp['artifacts']:
   if dep['path'] in changed:
    change=changed[dep['path']];saved=m.load(Path(change['backup_path']));assert sha(Path(change['backup_path']))==change['backup_sha256'];assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==dep['sha256']==change['before_sha256'];assert sha(m.ROOT/dep['path'])==change['after_sha256'];continue
   a.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.b.prior.old.h.OLD else a.checked(dep)
 p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
 with m.connect() as db:verified=a.verify(db,p,digest)
 report=m.load(m.RUN/'verification-after-wave-59.json');assert report['verified_new_artworks']==6160 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==169 and not report['unrelated_coverage_changes_since_prior_report']
 assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_fourth_museum_changes'])==5
 assert (report['after']['museums_below_100'],report['after']['museums_below_200'])==(1179,1288)
 csvcounts={}
 for name,count in [('added-artworks-after-wave-59.csv',6160),('reconciled-artworks-after-wave-59.csv',785),('museum-coverage-after-wave-59.csv',1491),('gac-date-enrichments-after-wave-59.csv',6)]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==27 and checks['historical_tests_passed']==926 and checks['replay_zero_writes']
 external=prior['external_artifacts']+research['external_artifacts']+list(checks['logs'].values())+[m.load(a.RUN/'logs-finalized-001.json')['completed_delivery_log']]+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=p['backup_path'],sha256=p['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 # A path may appear in more than one prior pin set only with the same bytes.
 grouped={}
 for dep in external:
  assert dep['path'] not in grouped or grouped[dep['path']]==dep
  grouped[dep['path']]=dep
 external=list(grouped.values())
 for dep in external:assert sha(Path(dep['path']))==dep['sha256']
 other=prior['other_job_status_reference'];a.checked(other)
 paths={m.ROOT/v['path'] for cp in [prior,research] for v in cp['artifacts']}|{a.CHECKPOINT,research_path,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*fourth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-59*')}
 artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
 result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=6160,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=169,source_pass_museums=350,source_pass_institutions=351,new_additions=201,new_existing_links=0,verification=verified,museum_changes=report['france_fourth_museum_changes'],museums_below_100=1179,museums_below_200=1288,new_tests_passed=27,historical_tests_passed=926,cumulative_verified_tests=953,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),research_checkpoint_reference=a.reference(research_path),research_artifacts_verified=len(research['artifacts']),intentional_supersessions=changes,other_job_status_reference=other,other_job_totals_separate=True,next_work='All five museums now exceed100 eligible records, with preferred200 still unfinished. Continue selected current-source research for other underfilled museums and reconcile existing identities where supported. Preserve39 captured holds and7683 unique index-held/unselected leads. No retry or alternate transport for Baltimore Cloudflare hold. Current workers completed; this turn made201 verified additions, so no repeated blocking condition. Global goal remains unfinished with1179 canonical museum entries below100 linked records.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=201,campaign_new=6160,campaign_links=785,museums_below100=1179)),flush=True)
if __name__=='__main__':main()
