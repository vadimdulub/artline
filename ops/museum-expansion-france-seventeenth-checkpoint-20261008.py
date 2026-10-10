"""Verified wave72 continuation checkpoint. Global goal remains active."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-seventeenth-apply-v2-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT)
 assert sha(a.CHECKPOINT)=='c9745f05d4aa386409dddd99b373cfeea59b1650da19bfd621c2d64bb22e4fd2'
 changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==1
 for c in changes:
  p=Path(c['backup_path']);assert sha(p)==c['backup_sha256'];saved=m.load(p);assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==c['before_sha256'];assert sha(m.ROOT/c['path'])==c['after_sha256']
 for dep in prior['artifacts']:
  if dep['path'] in changed:assert dep['sha256']==changed[dep['path']]['before_sha256']
  else:a.checked(dep)
 plan,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,plan,digest)
 assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 report=m.load(m.RUN/'verification-after-wave-72.json');assert report['verified_new_artworks']==9583 and report['verified_existing_artworks_linked']==785
 assert sum(v['new'] for v in report['france_seventeenth_museum_changes'])==125
 assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_seventeenth_museum_changes'])==1
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==13 and checks['cumulative_verified_tests']==1421 and checks['replay_zero_writes'];assert checks['added']==125 and checks['editorial_holds']==60 and checks['deferred_identity_candidates']==53
 a.checked(report['external_registry_growth_reference']);audit=m.load(m.RUN/'after-wave-72.json');csvcounts={}
 for name,count in [('added-artworks-after-wave-72.csv',9583),('reconciled-artworks-after-wave-72.csv',785),('gac-date-enrichments-after-wave-72.csv',6),('museum-coverage-after-wave-72.csv',len(audit['institutions']))]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 external=prior['external_artifacts']+list(checks['logs'].values())+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=plan['backup_path'],sha256=plan['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan-002.json.gz');assert m.load(reviewed)==plan;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 transaction_identity=m.BACKUP/(a.KEY+'-transaction-identity-002.json.gz');proof=m.load(transaction_identity);assert proof['selected_comparisons_equal'] and len(proof['selected_comparisons'])==125;external.append(dict(path=str(transaction_identity),sha256=sha(transaction_identity)))
 deliverylog=Path('/Users/vadimdulub/Library/Logs/artline-france-seventeenth-delivery-20261008.log');assert '"documented": 125' in deliverylog.read_text();external.append(dict(path=str(deliverylog),sha256=sha(deliverylog)))
 prioritylog=Path('/Users/vadimdulub/Library/Logs/artline-france-seventeenth-priority-20261008.log');assert '"museums": 101' in prioritylog.read_text();external.append(dict(path=str(prioritylog),sha256=sha(prioritylog)))
 queue=m.load(a.RUN/'next-museum-pass-001.json');assert queue['database_writes']==0 and len(queue['italian_museums'])==240 and queue['france_museums_with_enough_cached_leads_for_minimum']==0
 unique={}
 for dep in external:
  assert dep['path'] not in unique or unique[dep['path']]==dep;unique[dep['path']]=dep;assert sha(Path(dep['path']))==dep['sha256']
 a.checked(prior['other_job_status_reference'])
 paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*seventeenth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-72*')}
 artifacts=[a.reference(p) for p in sorted(paths)]
 result=dict(at=m.now(),goal_complete=False,local_only=True,new_additions=125,new_existing_links=0,campaign_new_artworks=9583,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=report['institutions_with_new_records_or_reconciled_holdings'],source_pass_museums=report['source_pass_museums'],source_pass_institutions=report['source_pass_institutions'],verification=verified,museum_changes=report['france_seventeenth_museum_changes'],museums_below_100=report['after']['museums_below_100'],museums_below_200=report['after']['museums_below_200'],global_coverage_snapshot_at=report['global_coverage_snapshot_at'],external_registry_growth_reference=report['external_registry_growth_reference'],new_tests_passed=13,historical_tests_passed=1408,cumulative_verified_tests=1421,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=list(unique.values()),prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=prior['other_job_status_reference'],other_job_totals_separate=True,editorial_holds=60,deferred_identity_candidates=53,release_notes_reference=a.reference(Path(a.r.n.__file__).resolve()),review_reference=a.reference(a.REVIEW),next_work='125 Cognacq-Jay additions verified:206linked/128eligible. Continue remaining53 deferred and60 held notices as evidence allows, then wider museum register. Rebase initial scope on816 target records and10368 campaign records; do not reuse691-record preflight. Source identity, copies/versions and sparse same-era portraits remain the next questions. No access-hold retry or bypass. No repeated blocking condition:125 real additions. Goal active.')
 result['next_museum_pass_reference']=a.reference(a.RUN/'next-museum-pass-001.json')
 result['next_work']='125 Cognacq-Jay additions verified:206linked/128eligible. All five French targets now exceed100eligible. Prioritize other underfilled museums via the refreshed Italian queue:240 museums,24190 cached leads requiring fresh known-ID, primary custody/date, city-scoped authority and physical-unit checks. Consider Corsini, Galleria Estense, Fano, Pavia and Albertina for the next bounded pass; cached numbers are not approved additions. Remaining French cached scan has603 leads across101 museums, none sufficient alone to reach100; use other primary sources or existing-record reconciliation. Preserve53 deferred and60 held notices, including23 Cognacq-Jay cases. For any five-museum follow-up rebase on816 target/10368 campaign records; no stale691-record preflight. Original failed transaction wrote nothing; V2 preserved unrelated image enrichment and recomputed selected identity hits inside transaction. Access holds retained without retry/bypass. No repeated blocking condition:125 real additions. Goal active.'
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(unique),new=125,campaign_new=9583,campaign_links=785,below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
