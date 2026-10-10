"""Pin delivered wave70 and preserve all remaining museum research."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fifteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='61b23540868b370d4a67d81391462b63114650a911c49fc401ec2ede583cfad2'
    changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==2
    for c in changes:
        saved=m.load(Path(c['backup_path']));assert sha(Path(c['backup_path']))==c['backup_sha256'];assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==c['before_sha256'];assert sha(m.ROOT/c['path'])==c['after_sha256']
    for dep in prior['artifacts']:
        if dep['path'] in changed:assert dep['sha256']==changed[dep['path']]['before_sha256']
        else:a.checked(dep)
    p,digest=a.validate_plan();applied=m.load(a.RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==digest
    with m.connect() as db:verified=a.verify(db,p,digest)
    report=m.load(m.RUN/'verification-after-wave-70.json');assert report['verified_new_artworks']==9337 and report['verified_existing_artworks_linked']==785 and report['institutions_with_new_records_or_reconciled_holdings']==200
    growth=m.load(a.RUN/'coverage-registry-growth-001.json');a.checked(report['external_registry_growth_reference']);assert len(growth['added_institutions'])==108 and report['newly_observed_institutions']==growth['added_institutions'];assert len(report['unrelated_coverage_changes_since_prior_report'])==1
    assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_fifteenth_museum_changes'])==3
    assert (report['after']['museums_below_100'],report['after']['museums_below_200'])==(1257,1390)
    csvcounts={}
    for name,count in [('added-artworks-after-wave-70.csv',9337),('reconciled-artworks-after-wave-70.csv',785),('museum-coverage-after-wave-70.csv',1599),('gac-date-enrichments-after-wave-70.csv',6)]:
        with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
        assert len(rows)==count;csvcounts[name]=count
    checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==43 and checks['historical_tests_passed']==1356 and checks['cumulative_verified_tests']==1399 and checks['replay_zero_writes']
    assert checks['added']==291 and checks['captured_review_holds']==58 and checks['deferred_identity_candidates']==301
    external=prior['external_artifacts']+list(checks['logs'].values())+[m.load(a.RUN/'logs-finalized-001.json')['completed_delivery_log']]+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=p['backup_path'],sha256=p['backup_sha256'])]
    reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==p;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
    grouped={}
    for dep in external:
        assert dep['path'] not in grouped or grouped[dep['path']]==dep;grouped[dep['path']]=dep
    external=list(grouped.values())
    for dep in external:assert sha(Path(dep['path']))==dep['sha256']
    other=prior['other_job_status_reference'];a.checked(other)
    paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*fifteenth*20261008.py') if v.name!='museum-expansion-france-fifteenth-working-notes-20261008.py'};paths|={v for v in m.RUN.glob('*after-wave-70*')}
    for name in ['physical-comparison-context-001.json.gz','physical-comparison-context-002.json.gz']:
        paths|={m.ROOT/v['path'] for v in m.load(a.RUN/name)['dependencies']}
    artifacts=[a.reference(v) for v in sorted(paths)];assert len({v['path'] for v in artifacts})==len(artifacts)
    result=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=9337,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=200,source_pass_museums=350,source_pass_institutions=351,new_additions=291,new_existing_links=0,verification=verified,museum_changes=report['france_fifteenth_museum_changes'],museums_below_100=1257,museums_below_200=1390,newly_observed_institution_rows=108,global_coverage_snapshot_at=report['global_coverage_snapshot_at'],external_registry_growth_reference=report['external_registry_growth_reference'],new_tests_passed=43,historical_tests_passed=1356,cumulative_verified_tests=1399,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=external,prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=other,other_job_totals_separate=True,deferred_identity_candidates=301,editorial_holds=58,release_notes_reference=a.reference(a.r.NOTEFILE),review_reference=a.reference(a.REVIEW),next_work='Estève127, Avelines152 and Dobrée151 eligible works now exceed100. Continue301 deferred candidates and58 holds where new evidence is available, especially Cognacq-Jay and Écouen; preserve the291 delivered identities. Supplemental comparison458 remains unreviewed; initial generic pools and specific pending questions still require work. Rebase future identity queries on this post-release checkpoint; do not reuse the pre-release279-record/count preflight for new writes. Mutable working notes excluded from checkpoint; frozen release snapshot authoritative. No repeated blocking condition:291 verified additions. Global goal active,1257 canonical museums below100 linked records. Existing access holds unchanged. All workers complete.')
    m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(external),new=291,campaign_new=9337,campaign_links=785,museums_below100=1257)),flush=True)
if __name__=='__main__':main()
