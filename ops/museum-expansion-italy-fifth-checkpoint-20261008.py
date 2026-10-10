"""Freeze wave76 evidence, readback and unfinished museum queue."""
import csv,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-italy-fifth-apply-20261008.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();previous=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='a3c9fc7e88c495ffcad685720d19c063ebb2d59074d326bab5c613b4b1345968'
 changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert set(changed)=={str((a.RUN/'README.md').relative_to(m.ROOT)),str((m.RUN/'README.md').relative_to(m.ROOT))}
 for c in changes:
  assert sha(Path(c['backup_path']))==c['backup_sha256'];saved=m.load(Path(c['backup_path']));assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==c['before_sha256'];assert sha(m.ROOT/c['path'])==c['after_sha256']
 policy=m.load(a.RUN/'policy-change-001.json');assert sha(m.ROOT/'AGENTS.md')==policy['after_sha256'];assert hashlib.sha256(policy['prior_text'].encode()).hexdigest()==policy['before_sha256']
 for dep in previous['artifacts']:
  if dep['path'] in changed:assert dep['sha256']==changed[dep['path']]['before_sha256']
  elif dep['path']=='AGENTS.md':assert dep['sha256']==policy['before_sha256']
  else:a.checked(dep)
 plan,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,plan,digest)
 assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 report=m.load(m.RUN/'verification-after-wave-76.json');assert report['verified_new_artworks']==10259 and report['verified_existing_artworks_linked']==785;assert sum(v['new'] for v in report['italy_fifth_museum_changes'])==211;assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['italy_fifth_museum_changes'])==3
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==13 and checks['cumulative_verified_tests']==1470 and checks['replay_zero_writes'];assert checks['added']==211 and checks['editorial_holds']==139 and checks['deferred_identity_candidates']==51
 audit=m.load(m.RUN/'after-wave-76.json');csvcounts={}
 for name,count in [('added-artworks-after-wave-76.csv',10259),('reconciled-artworks-after-wave-76.csv',785),('gac-date-enrichments-after-wave-76.csv',6),('museum-coverage-after-wave-76.csv',len(audit['institutions']))]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 external=previous['external_artifacts']+list(checks['logs'].values())+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=plan['backup_path'],sha256=plan['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan-001.json.gz');assert m.load(reviewed)==plan;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 proof=m.BACKUP/(a.KEY+'-transaction-identity-001.json.gz');x=m.load(proof);assert x['selected_comparisons_equal'] and len(x['selected_comparisons'])==211;external.append(dict(path=str(proof),sha256=sha(proof)))
 log=Path('/Users/vadimdulub/Library/Logs/artline-italy-fifth-delivery-20261008.log');assert '"documented": 211' in log.read_text();external.append(dict(path=str(log),sha256=sha(log)))
 unique={}
 for dep in external:
  assert dep['path'] not in unique or unique[dep['path']]==dep;unique[dep['path']]=dep;assert sha(Path(dep['path']))==dep['sha256']
 a.checked(previous['other_job_status_reference']);ctx=m.load(a.RUN/'comparison-source-context-001.json.gz');assert len(ctx['body_references'])==517 and len(ctx['rows'])==3674;assert {v['number'] for v in ctx['museum_local_inventory_hits']}=={475};assert not {v['number'] for v in ctx['museum_local_inventory_hits']}&set(a.r.NOTES)
 paths={m.ROOT/v['path'] for v in previous['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*italy*fifth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-76*')};paths|={a.checked(v) for v in ctx['body_references']}
 artifacts=[a.reference(p) for p in sorted(paths)];queue=m.load(a.RUN/'remaining-research-001.json.gz');assert len(queue['rows'])==352;nextq=m.load(a.RUN/'next-museum-pass-001.json');assert len(nextq['italian_museums'])==226
 result=dict(at=m.now(),goal_complete=False,local_only=True,new_additions=211,new_existing_links=0,campaign_new_artworks=10259,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=report['institutions_with_new_records_or_reconciled_holdings'],verification=verified,museum_changes=report['italy_fifth_museum_changes'],museums_below_100=report['after']['museums_below_100'],museums_below_200=report['after']['museums_below_200'],global_coverage_snapshot_at=report['global_coverage_snapshot_at'],external_registry_growth_reference=report['external_registry_growth_reference'],new_tests_passed=13,historical_tests_passed=1457,cumulative_verified_tests=1470,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=list(unique.values()),prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(previous['artifacts']),intentional_supersessions=changes,external_policy_change_reference=a.reference(a.RUN/'policy-change-001.json'),other_job_status_reference=previous['other_job_status_reference'],other_job_totals_separate=True,editorial_holds=139,deferred_identity_candidates=51,review_reference=a.reference(a.REVIEW),remaining_research_reference=a.reference(a.RUN/'remaining-research-001.json.gz'),next_museum_pass_reference=a.reference(a.RUN/'next-museum-pass-001.json'),next_work='211 additions verified: Cenacolo114 linked/105 eligible, Ala Ponzone123/120, Villa Guinigi132/110. All five researched museums exceed100 eligible;200 remains preferred. Continue226 underfilled Italian museums and wider global queue. Remaining352 notices preserved:190 current and162 prior Vicenza/Devanna. Rebase five-museum scope716 and prior campaign protection11044. All698 source facts reconstructed;401 notices reviewed in current release. Historical inventory audit3674 contexts plus209 recent structured citations;475 remains held. Preserve all access holds. No repeated blocking condition:211 real additions. Goal active.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(unique),new=211,campaign_new=10259,campaign_links=785,below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
