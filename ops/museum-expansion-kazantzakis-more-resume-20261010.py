"""Record restored access and a fresh pinned plan without changing prior evidence."""
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-kazantzakis-more-apply-20261009.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m;RUN=m.RUN/'native/kazantzakis-more-delivery-20261010'

def main():
    p,digest=a.validate_plan();assert digest=='6e43e487b4c4fa63455b230f53a64bb83d123c7c30ff8854c9ffac2a330386fd'
    prior=m.RUN/'native/larissa-20261010/research-checkpoint-001.json';cp=m.load(prior)
    assert a.reference(prior)['sha256']=='593f52af993318a98fc5de549d43f9160608de9621ca8e5222cdec2d1e6ea8d1'
    for pin in cp['artifacts']+cp['external_artifacts']:
        path=Path(pin['path']);path=path if path.is_absolute()else m.ROOT/path
        assert hashlib.sha256(path.read_bytes()).hexdigest()==pin['sha256']
    m.save(RUN/'access-restored-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_research_checkpoint=a.reference(prior),
        previous_pins_verified=dict(artifacts=len(cp['artifacts']),external=len(cp['external_artifacts'])),
        gcloud_token_refresh=dict(exit_code=0,token_output_suppressed=True),cloud_sql=dict(instance='artline-postgres',project='artline-508319',state='RUNNING'),
        initial_connection_failure='Expected loopback port55519 closed the connection; subsequent listener/process inspection found no55519 proxy. Two existing proxies were running on55478 and55445 and left untouched.',
        task_proxy=dict(binary='/tmp/artline-release-20261001-evening/cloud-sql-proxy',version='2.25.4+darwin.arm64',address='127.0.0.1',port=55519,gcloud_auth=True,instance='artline-508319:europe-west1:artline-postgres',pid_at_start=7614,exec_session_at_start=93421),
        recovery='Started the missing task-specific loopback listener using the existing gcloud identity; no existing proxy restarted, credential search, alternate account or authentication bypass.',
        read_only_comparators_completed=128,live_prepare_passed=True,protected_prior_records=921,plan_reference=a.reference(a.PLAN),
        script_reference=a.reference(Path(__file__).resolve())))
    m.save(RUN/'offline-test-observation-001.json',dict(at=m.now(),command="research-venv python -B ops/test_museum_expansion_kazantzakis_more_20261009.py",exit_code=0,tests_passed=20,
        observed_stdout='Ran 20 tests in 3.034s; OK',evidence_kind='Execution result observed in this continuation before preparation; not a new test run or a production verification.',
        test_script_reference=a.reference(m.ROOT/'ops/test_museum_expansion_kazantzakis_more_20261009.py'),plan_reference=a.reference(a.PLAN)))
    m.save(RUN/'backup-contention-001.json',dict(at=m.now(),requested_description='Before selected Kazantzakis continuation 20261010 wave121',create_exit_code=1,
        error='HTTP409: another operation was already in progress.',observed_running_operation=dict(name='8dc37cde-e0c5-458f-a8c2-1f9400000024',operationType='BACKUP_VOLUME',status='RUNNING',startTime='2026-10-10T11:12:23.386Z'),
        observed_backup=dict(id='1791630743296',description='Before random country collections BE LV HR 20261010',status='RUNNING',startTime='2026-10-10T11:12:23.306Z'),
        action='Observe completion of this specific unrelated backup operation without canceling or modifying it, then request the selected-delivery backup. No artwork writes attempted.'))
    print(dict(plan=digest,records=len(p['records']),access_restored=True,production_applied=False))

if __name__=='__main__':main()
