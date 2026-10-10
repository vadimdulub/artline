"""Read-only verification of the completed wave before further selected research."""
import hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-france-thirteenth-discovery-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
def main():
 a=d.prior;m=d.m;dest=d.RUN/'continuation-001.json';assert not dest.exists();cp=a.RUN/'delivery-checkpoint-001.json'
 assert a.reference(cp)['sha256']=='74cb7096ecce5905a750bca49761f1d264fa1876ac8954da36814e8c922d4a9c';x=m.load(cp)
 for dep in x['artifacts']:a.checked(dep)
 for dep in x['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 assert verified['verified_new_records']==218 and x['goal_complete'] is False
 m.save(dest,dict(at=m.now(),previous_goal_turn='progress',verified_additions=218,previous_checkpoint=a.reference(cp),artifacts_verified=len(x['artifacts']),external_artifacts_verified=len(x['external_artifacts']),verification=verified,read_only=True,goal_complete=False,verifier_reference=a.reference(Path(__file__).resolve()),next_codes=d.CODES,other_job_status_reference=x['other_job_status_reference'],other_job_totals_separate=True,access_hold='Baltimore unchanged; no retry or alternate route.'))
 print(json.dumps(dict(verified_additions=218,prior_artifacts=len(x['artifacts']),external_artifacts=len(x['external_artifacts']),goal_complete=False)),flush=True)
if __name__=='__main__':main()
