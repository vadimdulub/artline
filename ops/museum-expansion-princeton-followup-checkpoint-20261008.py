#!/usr/bin/env python3
"""Freeze wave55 delivery, preserving explicit README successor history."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-princeton-followup-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='f83ff6b2c34a199dc93c3e74413110b388978ff87126b7620d08516429adf8b9';changes=[];backups=[]
    for name,path in [('root',m.RUN/'README.md'),('princeton',a.prior.RUN/'README.md')]:
        backup=m.BACKUP/('princeton-followup-'+name+'-readme-before-001.json.gz');saved=m.load(backup);relative=str(path.relative_to(m.ROOT));oldref=next(v for v in prior['artifacts'] if v['path']==relative)
        assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==oldref['sha256']
        changes.append(dict(path=relative,before_sha256=saved['sha256'],after_sha256=sha(path),backup_path=str(backup),backup_sha256=sha(backup)));backups.append(dict(path=str(backup),sha256=sha(backup)))
    for dep in prior['artifacts']:
        if dep['path'] in {v['path'] for v in changes}:continue
        a.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==a.prior.b.prior.old.h.OLD else a.checked(dep)
    m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=changes,policy='Intentional wave55 progress updates. Prior README bytes preserved in Library. Historical source captures, plans, reports and code remain unchanged.'))
    p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
    with m.connect() as db:verified=a.verify(db,p,digest)
    report=m.load(m.RUN/'verification-after-wave-55.json');assert report['verified_new_artworks']==5643 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==165 and not report['unrelated_coverage_changes_since_prior_report']
    csvcounts={}
    for name,count in [('added-artworks-after-wave-55.csv',5643),('reconciled-artworks-after-wave-55.csv',785),('museum-coverage-after-wave-55.csv',1491),('gac-date-enrichments-after-wave-55.csv',6)]:
        with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
        assert len(rows)==count;csvcounts[name]=count
    checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==10 and checks['historical_tests_passed']==864
    external=prior['external_artifacts']+list(checks['logs'].values())+backups+[dict(path=p['backup_path'],sha256=p['backup_sha256'])]
    reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)));external=list({v['path']:v for v in external}.values())
    for dep in external:assert sha(Path(dep['path']))==dep['sha256']
    other=prior['other_job_status_reference'];a.checked(other)
    paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*princeton*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-55*')}
    artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
    result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=5643,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=165,source_pass_museums=350,source_pass_institutions=351,new_additions=50,new_existing_links=0,verification=verified,museums_below_100=report['after']['museums_below_100'],museums_below_200=report['after']['museums_below_200'],new_tests_passed=10,historical_tests_passed=864,cumulative_verified_tests=874,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=other,other_job_totals_separate=True,next_work='Princeton now has214 eligible linked works and meets preferred200. Continue other underfilled museums with bounded source-backed selections and existing-object reconciliation. Preserve Princeton104 captured holds and248 index holds across both passes for later targeted research, without treating them as approved. Do not retry Baltimore Cloudflare challenge through another host or transport. All current source and verification workers completed. The global goal remains unfinished with1196 canonical museum entries below100.')
    m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=50,links=0,princeton=verified['current_counts'],campaign_new=5643,campaign_links=785,museums_below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
