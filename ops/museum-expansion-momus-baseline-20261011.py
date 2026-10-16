"""Reverify Jewish Museum delivery and capture fresh MOMus and protected production state."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-momus-common-20261011.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    assert not(RUN/'baseline-verification-001.json').exists();assert c.ref(c.CP)['sha256']==c.CP_SHA
    cp=m.load(c.CP);historical=c.module('historical','museum-expansion-jewish-historical-validation-20261011.py');prior=historical.a;plan,digest=historical.validate_plan()
    protected=m.load(c.checked(cp['protected_production_ids_reference']))['ids'];assert len(protected)==2938
    for key,connect in [('initial',m.connect),('production-initial',c.prod.connect)]:
        dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
        with connect() as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
            ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(c.IID,c.IID))]
            snap,counts=c.snapshot(db,ids),c.counts(db);institution=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(c.IID,)).fetchone()
            if key=='production-initial':verification=prior.verify(db,plan,digest);protected_state=c.s.prior_state(db,protected)
        m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution=institution,read_only=True,script_reference=c.ref(Path(__file__).resolve())))
        print(json.dumps(dict(scope=key,works=len(ids),counts=counts)),flush=True)
    m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_checkpoint=c.ref(c.CP),previous_delivery_verification=verification,prior_production_ids=protected,prior_state=protected_state,prior_plan=prior.c.ref(prior.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],historical_pin_reconciliation_reference=cp['historical_pin_reconciliation_reference'],policy='Previous Jewish Museum delivery140new/131images verified;148catalogue/142numericeligible/139primary. Mutable policy additions preserved via exact historical copies. Fresh MOMus initial scope and2938protectedIDs captured read-only; production multi-museum identities need reconciliation. Local database read-only. Proxy restored after absent listener; no import repeated.'))
    print(json.dumps(dict(baseline_complete=True,protected_prior=len(protected))),flush=True)

if __name__=='__main__':main()
