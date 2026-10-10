"""Revalidate delivered wave69 before the next selected museum pass."""
import hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fourteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
RUN=m.RUN/'native/france-fifteenth-minimum-20261008'
def main():
    dest=RUN/'continuation-001.json';assert not dest.exists();cp=a.RUN/'delivery-checkpoint-001.json'
    assert a.reference(cp)['sha256']=='61b23540868b370d4a67d81391462b63114650a911c49fc401ec2ede583cfad2';x=m.load(cp)
    for dep in x['artifacts']:a.checked(dep)
    for dep in x['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
    p,digest=a.validate_plan()
    with m.connect() as db:verified=a.verify(db,p,digest)
    assert verified['verified_new_records']==481 and x['goal_complete'] is False
    m.save(dest,dict(at=m.now(),previous_goal_turn='progress',verified_additions=481,previous_checkpoint=a.reference(cp),artifacts_verified=len(x['artifacts']),external_artifacts_verified=len(x['external_artifacts']),verification=verified,read_only=True,goal_complete=False,verifier_reference=a.reference(Path(__file__).resolve()),next_codes=['M0231','M0416','M0745','M5012','M1107'],other_job_status_reference=x['other_job_status_reference'],other_job_totals_separate=True,access_hold='Baltimore, Orsay Coubertin and the failed Hugo583 request remain unretried.'))
    print(json.dumps(dict(verified_additions=481,prior_artifacts=len(x['artifacts']),external_artifacts=len(x['external_artifacts']),goal_complete=False)),flush=True)
if __name__=='__main__':main()
