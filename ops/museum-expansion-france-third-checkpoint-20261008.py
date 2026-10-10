#!/usr/bin/env python3
"""Freeze wave58 evidence with an explicit root README successor receipt."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-third-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='5de12be285dabf7d34db405e7a6f3fd53a0f39becfd4004962b9a0af0d35df55'
    path=m.RUN/'README.md';backup=m.BACKUP/'france-third-root-readme-before-001.json.gz';saved=m.load(backup);relative=str(path.relative_to(m.ROOT));oldref=next(v for v in prior['artifacts'] if v['path']==relative)
    assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==oldref['sha256']
    change=dict(path=relative,before_sha256=saved['sha256'],after_sha256=sha(path),backup_path=str(backup),backup_sha256=sha(backup))
    for dep in prior['artifacts']:
        if dep['path']==relative:continue
        a.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.b.prior.old.h.OLD else a.checked(dep)
    m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave58 progress update. Prior README bytes retained in Library; historical source evidence, plans, reports and code stay immutable.'))
    p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
    with m.connect() as db:verified=a.verify(db,p,digest)
    report=m.load(m.RUN/'verification-after-wave-58.json');assert report['verified_new_artworks']==5959 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==169 and not report['unrelated_coverage_changes_since_prior_report']
    assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_third_museum_changes'])==2
    csvcounts={}
    for name,count in [('added-artworks-after-wave-58.csv',5959),('reconciled-artworks-after-wave-58.csv',785),('museum-coverage-after-wave-58.csv',1491),('gac-date-enrichments-after-wave-58.csv',6)]:
        with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
        assert len(rows)==count;csvcounts[name]=count
    checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==22 and checks['historical_tests_passed']==904 and checks['replay_zero_writes']
    external=prior['external_artifacts']+list(checks['logs'].values())+[dict(path=str(backup),sha256=sha(backup)),dict(path=p['backup_path'],sha256=p['backup_sha256'])]
    reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)));external=list({v['path']:v for v in external}.values())
    for dep in external:assert sha(Path(dep['path']))==dep['sha256']
    other=prior['other_job_status_reference'];a.checked(other)
    paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*third*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-58*')}
    artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
    result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=5959,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=169,source_pass_museums=350,source_pass_institutions=351,new_additions=73,new_existing_links=0,verification=verified,museum_changes=report['france_third_museum_changes'],museums_below_100=report['after']['museums_below_100'],museums_below_200=report['after']['museums_below_200'],new_tests_passed=22,historical_tests_passed=904,cumulative_verified_tests=926,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=[change],other_job_status_reference=other,other_job_totals_separate=True,next_work='Evreux and Tournus now exceed100 eligible records; Flers, Montargis and Carpentras still need supported additions. Continue other underfilled museums with selected current source-backed additions and exact existing-object reconciliation. Preserve50 captured holds and1275 unique index held/unselected leads from this pass. Do not retry Baltimore Cloudflare challenge through alternate host or transport. Current workers completed; global goal unfinished with1184 canonical museum entries below100 linked records. Same blocking condition has not repeated: this turn made73 verified additions.')
    m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=73,links=0,campaign_new=5959,campaign_links=785,museums_below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
