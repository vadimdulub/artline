"""Freeze verified wave73 delivery and preserve the active research goal."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-italy-second-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();previous=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='eaccf56309c175c737fcfb8c49c643a2be06316cc17bf51b0f5291f9e389a3fb'
 changes=m.load(a.RUN/'readme-supersessions-001.json')['changes']+[m.load(a.RUN/'policy-supersession-001.json')];changed={v['path']:v for v in changes};assert set(changed)=={'AGENTS.md',str((m.RUN/'README.md').relative_to(m.ROOT))}
 for c in changes:
  assert sha(Path(c['backup_path']))==c['backup_sha256'];saved=m.load(Path(c['backup_path']));assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==c['before_sha256'];assert sha(m.ROOT/c['path'])==c['after_sha256']
 for dep in previous['artifacts']:
  if dep['path'] in changed:assert dep['sha256']==changed[dep['path']]['before_sha256']
  else:a.checked(dep)
 plan,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,plan,digest)
 assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 report=m.load(m.RUN/'verification-after-wave-73.json');assert report['verified_new_artworks']==9671 and report['verified_existing_artworks_linked']==785;assert sum(v['new'] for v in report['italy_second_museum_changes'])==88;assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['italy_second_museum_changes'])==4
 checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==10 and checks['cumulative_verified_tests']==1431 and checks['replay_zero_writes'];assert checks['added']==88 and checks['editorial_holds']==416 and checks['deferred_identity_candidates']==389
 audit=m.load(m.RUN/'after-wave-73.json');csvcounts={}
 for name,count in [('added-artworks-after-wave-73.csv',9671),('reconciled-artworks-after-wave-73.csv',785),('gac-date-enrichments-after-wave-73.csv',6),('museum-coverage-after-wave-73.csv',len(audit['institutions']))]:
  with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
  assert len(rows)==count;csvcounts[name]=count
 external=previous['external_artifacts']+list(checks['logs'].values())+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=plan['backup_path'],sha256=plan['backup_sha256'])]
 reviewed=m.BACKUP/(a.KEY+'-reviewed-plan-001.json.gz');assert m.load(reviewed)==plan;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
 proof=m.BACKUP/(a.KEY+'-transaction-identity-001.json.gz');x=m.load(proof);assert x['selected_comparisons_equal'] and len(x['selected_comparisons'])==88;external.append(dict(path=str(proof),sha256=sha(proof)))
 log=Path('/Users/vadimdulub/Library/Logs/artline-italy-second-delivery-20261008.log');assert '"documented": 88' in log.read_text();external.append(dict(path=str(log),sha256=sha(log)))
 unique={}
 for dep in external:
  assert dep['path'] not in unique or unique[dep['path']]==dep;unique[dep['path']]=dep;assert sha(Path(dep['path']))==dep['sha256']
 a.checked(previous['other_job_status_reference']);inventory=m.load(a.RUN/'citation-inventory-audit-001.json.gz');assert not inventory['hits'] and len(inventory['body_references'])==140
 for dep in inventory['body_references']:a.checked(dep)
 paths={m.ROOT/v['path'] for v in previous['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*italy*second*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-73*')};paths|={m.ROOT/v['path'] for v in inventory['body_references']}
 for v in m.load(a.RUN/'comparison-source-context-001.json.gz')['rows']:paths.add(a.checked(v['body_reference']))
 artifacts=[a.reference(p) for p in sorted(paths)];queue=m.load(a.RUN/'remaining-research-001.json.gz');assert len(queue['rows'])==805;nextq=m.load(a.RUN/'next-museum-pass-001.json');assert len(nextq['italian_museums'])==236
 result=dict(at=m.now(),goal_complete=False,local_only=True,new_additions=88,new_existing_links=0,campaign_new_artworks=9671,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=report['institutions_with_new_records_or_reconciled_holdings'],verification=verified,museum_changes=report['italy_second_museum_changes'],museums_below_100=report['after']['museums_below_100'],museums_below_200=report['after']['museums_below_200'],global_coverage_snapshot_at=report['global_coverage_snapshot_at'],external_registry_growth_reference=report['external_registry_growth_reference'],new_tests_passed=10,historical_tests_passed=1421,cumulative_verified_tests=1431,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=list(unique.values()),prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(previous['artifacts']),intentional_supersessions=changes,other_job_status_reference=previous['other_job_status_reference'],other_job_totals_separate=True,editorial_holds=416,deferred_identity_candidates=389,review_reference=a.reference(a.REVIEW),remaining_research_reference=a.reference(a.RUN/'remaining-research-001.json.gz'),next_museum_pass_reference=a.reference(a.RUN/'next-museum-pass-001.json'),next_work='88 additions verified: Estense149linked/110eligible, Albertina111/100, Corsini176/101, Fano139/104. Pavia291/80 unchanged. Four targets now meet100eligible. Prefer other underfilled museums from236-museum Italian queue while retaining805 researched notices for follow-up toward200. Fresh object/city/custody/version/date checks required. Rebase five-target initial scope to895 records and prior campaign protection to10456; do not reuse807 or10368. Keep two object timeouts and all access holds, do not retry or bypass. Pavia159 empty HTML shells have RDF but require independent complete primary pages; six regional URLs identify existing objects. Fano532 is an existing Ceccarini reconciliation lead. Ambiguous Vernier sheets, anatomical canvases, historical external deposits and sparse same-era comparisons stay deferred. No repeated blocking condition:88 real additions. Goal remains active.')
 m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(unique),new=88,campaign_new=9671,campaign_links=785,below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
