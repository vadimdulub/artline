"""Immutable wave71 continuation checkpoint; goal remains active."""
import csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-sixteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=a.RUN/'delivery-checkpoint-001.json';assert not dest.exists();prior=m.load(a.CHECKPOINT);assert sha(a.CHECKPOINT)=='ea8bd395f4ba3321df5b305d09e469a0b79a45db53948d579e1e0927f2a7c8e2'
    changes=m.load(a.RUN/'readme-supersessions-001.json')['changes'];changed={v['path']:v for v in changes};assert len(changed)==1
    for c in changes:
        p=Path(c['backup_path']);assert sha(p)==c['backup_sha256'];saved=m.load(p);assert hashlib.sha256(saved['text'].encode()).hexdigest()==saved['sha256']==c['before_sha256'];assert sha(m.ROOT/c['path'])==c['after_sha256']
    for dep in prior['artifacts']:
        if dep['path'] in changed:assert dep['sha256']==changed[dep['path']]['before_sha256']
        else:a.checked(dep)
    plan,digest=a.validate_plan()
    with m.connect() as db:verified=a.verify(db,plan,digest)
    assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
    report=m.load(m.RUN/'verification-after-wave-71.json');assert report['verified_new_artworks']==9458 and report['verified_existing_artworks_linked']==785
    assert sum(v['new'] for v in report['france_sixteenth_museum_changes'])==121
    assert sum(v['eligible_before']<100<=v['eligible_after'] for v in report['france_sixteenth_museum_changes'])==1
    checks=m.load(a.RUN/'checks-001.json');assert checks['new_offline_tests_passed']==9 and checks['cumulative_verified_tests']==1408 and checks['replay_zero_writes'];assert checks['added']==121 and checks['editorial_holds']==60 and checks['deferred_identity_candidates']==178
    a.checked(report['external_registry_growth_reference']);audit=m.load(m.RUN/'after-wave-71.json');csvcounts={}
    for name,count in [('added-artworks-after-wave-71.csv',9458),('reconciled-artworks-after-wave-71.csv',785),('gac-date-enrichments-after-wave-71.csv',6),('museum-coverage-after-wave-71.csv',len(audit['institutions']))]:
        with (m.RUN/name).open(newline='') as fp:rows=list(csv.DictReader(fp))
        assert len(rows)==count;csvcounts[name]=count
    external=prior['external_artifacts']+list(checks['logs'].values())+[dict(path=v['backup_path'],sha256=v['backup_sha256']) for v in changes]+[dict(path=plan['backup_path'],sha256=plan['backup_sha256'])]
    reviewed=m.BACKUP/(a.KEY+'-reviewed-plan.json.gz');assert m.load(reviewed)==plan;external.append(dict(path=str(reviewed),sha256=sha(reviewed)))
    deliverylog=Path('/Users/vadimdulub/Library/Logs/artline-france-sixteenth-delivery-20261008.log');assert '"documented": 121' in deliverylog.read_text();external.append(dict(path=str(deliverylog),sha256=sha(deliverylog)))
    first_attempt=Path('/Users/vadimdulub/Library/Logs/artline-france-sixteenth-checkpoint-20261008.log');assert "KeyError: 'additional_visual_confirmation_reference'" in first_attempt.read_text();external.append(dict(path=str(first_attempt),sha256=sha(first_attempt)))
    unique={}
    for dep in external:
        assert dep['path'] not in unique or unique[dep['path']]==dep;unique[dep['path']]=dep;assert sha(Path(dep['path']))==dep['sha256']
    a.checked(prior['other_job_status_reference'])
    paths={m.ROOT/v['path'] for v in prior['artifacts']}|{a.CHECKPOINT,Path(__file__).resolve()};paths|={v for v in a.RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*france*sixteenth*20261008.py')};paths|={v for v in m.RUN.glob('*after-wave-71*')}
    for row in m.load(a.RUN/'existing-targeted-context-001.json.gz')['rows']:
        a.checked(row['body_reference']);paths.add(m.ROOT/row['body_reference']['path'])
    visual=m.load(a.RUN/'rieux-visual-confirmation-001.json');assert visual['database_writes']==0 and visual['catalogue_image_attachments']==0
    addendum=m.load(a.RUN/'report-visual-confirmation-001.json');a.checked(addendum['unchanged_report_reference']);a.checked(addendum['additional_visual_confirmation_reference'])
    for key in ['native_image_reference','native_receipt_reference','wikiart_image_reference']:a.checked(visual[key])
    assert report['identity_reference_downloads_this_wave']==dict(selected_wikiart_jpeg=2,catalogue_image_attachments=0)
    artifacts=[a.reference(p) for p in sorted(paths)]
    result=dict(at=m.now(),goal_complete=False,local_only=True,new_additions=121,new_existing_links=0,campaign_new_artworks=9458,campaign_existing_links=785,institutions_with_new_records_or_reconciled_holdings=report['institutions_with_new_records_or_reconciled_holdings'],source_pass_museums=report['source_pass_museums'],source_pass_institutions=report['source_pass_institutions'],verification=verified,museum_changes=report['france_sixteenth_museum_changes'],museums_below_100=report['after']['museums_below_100'],museums_below_200=report['after']['museums_below_200'],global_coverage_snapshot_at=report['global_coverage_snapshot_at'],external_registry_growth_reference=report['external_registry_growth_reference'],new_tests_passed=9,historical_tests_passed=1399,cumulative_verified_tests=1408,plan_sha256=digest,csv_counts_verified=csvcounts,artifacts=artifacts,external_artifacts=list(unique.values()),prior_checkpoint_reference=a.reference(a.CHECKPOINT),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=changes,other_job_status_reference=prior['other_job_status_reference'],other_job_totals_separate=True,editorial_holds=60,deferred_identity_candidates=178,release_notes_reference=a.reference(Path(a.r.n.__file__).resolve()),review_reference=a.reference(a.REVIEW),next_work='119Écouen and2Cognacq-Jay additions verified. Écouen now119linked/eligible; Cognacq-Jay81linked/3eligible. Continue remaining178 deferred and60 held notices as evidence allows, then broader museum register. Rebase identity queries on691 target records and10243 campaign records; do not reuse pre-release570-record preflight. Candidate458 generic portrait pool remains unfinished. Hamilton comparator470 resolved specifically, other portrait comparisons remain. New wax584/586 cross-aliasCL22278 conflict held. Met339838HTTP429 and earlier access holds retained without retry/bypass. No repeated blocking condition:121 verified additions. All workers complete; global goal active.')
    result['additional_visual_confirmation_reference']=a.reference(a.RUN/'rieux-visual-confirmation-001.json');result['total_identity_reference_images_this_wave']=dict(wikiart=2,paris_musees=1,catalogue_attachments=0)
    m.save(dest,result);print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)),sha256=sha(dest),artifacts=len(artifacts),external_artifacts=len(unique),new=121,campaign_new=9458,campaign_links=785,below100=result['museums_below_100'])),flush=True)
if __name__=='__main__':main()
