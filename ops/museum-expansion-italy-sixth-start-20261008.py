"""Verify wave76 delivery before continuing the full museum expansion goal."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-italy-fifth-apply-20261008.py'));prior=importlib.util.module_from_spec(z);z.loader.exec_module(prior)
m=prior.m;ref=prior.reference;checked=prior.checked;RUN=m.RUN/'native/italy-sixth-minimum-20261008';CP=prior.RUN/'delivery-checkpoint-001.json'
def main():
 dest=RUN/'continuation-001.json';assert not dest.exists();assert ref(CP)['sha256']=='60374c24e205784f261668cacfa13530bcb2ed49afc3e21d7e30a73261ce10e0';cp=m.load(CP)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');result=prior.verify(db,p,d)
 m.save(dest,dict(at=m.now(),previous_goal_turn='progress',verified_new=211,previous_checkpoint=ref(CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=result,script_reference=ref(Path(__file__).resolve()),policy='Previous211 local additions reverified. Continue full goal with Pavia, Poldi Pezzoli and Sabauda research. Prior campaign11044 records; all previous access holds retained. No repeated blocking condition.'))
 print(json.dumps(dict(verified_previous=211,artifacts=len(cp['artifacts']),external=len(cp['external_artifacts']))),flush=True)
if __name__=='__main__':main()
