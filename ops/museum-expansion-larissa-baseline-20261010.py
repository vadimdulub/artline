"""Fresh production/local Larissa scopes and verification of the previous delivery."""
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    assert not (RUN/'baseline-verification-001.json').exists()
    pins=c.research_verify();prior=c.module('prior','museum-expansion-kazantzakis-more-reconciled-20261010.py').a
    plan,digest=prior.validate_plan();cp=m.load(c.CP);protected=m.load(c.checked(cp['protected_production_ids_reference']))['ids'];assert len(protected)==1026
    for key,connect in [('initial',m.connect),('production-initial',c.prod.connect)]:
        dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
        with connect() as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
            ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(c.IID,c.IID))]
            snap=c.snapshot(db,ids);counts=c.counts(db)
            if key=='production-initial':
                verification=prior.verify(db,plan,digest)
                protected_state=c.s.prior_state(db,protected)
        m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=c.ref(Path(__file__).resolve())))
        print(json.dumps(dict(scope=key,works=len(ids),counts=counts)),flush=True)
    m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_checkpoint=c.ref(c.CP),research_checkpoint=c.ref(c.RESEARCH_CP),research_pins_verified=pins,
        previous_delivery_verification=verification,prior_production_ids=protected,prior_state=protected_state,prior_plan=prior.reference(prior.PLAN),
        inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],
        policy='Previous turn added105 verified Kazantzakis works. Fresh Larissa snapshot and1026prior campaign records protected; local database read-only. No new catalogue writes or image uploads.'))
    print(json.dumps(dict(baseline_complete=True,protected_prior=len(protected),research_pins_verified=pins)),flush=True)

if __name__=='__main__':main()
