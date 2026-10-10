"""Verify wave83 and read the existing Ferens scope before selected native additions."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-britain-six-apply-20261009.py'));prior=importlib.util.module_from_spec(z);z.loader.exec_module(prior);m=prior.m;ref=prior.reference;checked=prior.checked
RUN=m.RUN/'native/ferens-additions-20261009';IID='9172ebcd-f052-5736-a3ba-a8612ac75c60';CP=prior.RUN/'delivery-checkpoint-001.json';snapshot=prior.snapshot
def counts(db):return prior.s.BASE.counts(db,IID)
def main():
 dest=RUN/'initial-scope-001.json.gz';assert not dest.exists();assert ref(CP)['sha256']=='2dd3a398f4c0248a5c747409864859f81551984925033956198242fb2120d5b9';cp=m.load(CP)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');verified=prior.verify(db,p,d);ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))];snap=snapshot(db,ids);cs=counts(db)
 m.save(RUN/'continuation-001.json',dict(at=m.now(),previous_goal_turn='progress',verified_existing_links=227,previous_checkpoint=ref(CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=verified,policy='Prior227 links freshly verified. Continue selected Ferens native additions toward100/200; preserve all prior holdings,metadata,queues and source access holds. No repeated global blocker.'))
 m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=cs,read_only=True,script_reference=ref(Path(__file__).resolve())));print(json.dumps(dict(scope=len(ids),counts=cs,prior_verified=227)),flush=True)
if __name__=='__main__':main()
