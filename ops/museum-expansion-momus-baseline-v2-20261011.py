"""Fresh MOMus baseline preserving independently added prior artist/citation evidence."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-momus-common-20261011.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    cp=m.load(c.CP);assert c.ref(c.CP)['sha256']==c.CP_SHA
    historical=c.module('historical','museum-expansion-jewish-historical-validation-20261011.py');a=historical.a;p,digest=historical.validate_plan()
    protected=m.load(c.checked(cp['protected_production_ids_reference']))['ids'];assert len(protected)==2938
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        observed=a.c.s.prior_state(db,p['prior_ids']);changed={k:dict(before=p['prior_state'][k],after=v) for k,v in observed.items() if v!=p['prior_state'][k]}
        assert set(changed)=={'artists','citations'}
        assert changed['artists']['after']['rows']==changed['artists']['before']['rows']+1
        assert changed['citations']['after']['rows']==changed['citations']['before']['rows']+2
        comparison=dict(p);comparison['prior_state']=observed
        verification=a.verify(db,comparison,digest)
        ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(c.IID,c.IID))]
        snap,counts=c.snapshot(db,ids),c.counts(db);institution=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(c.IID,)).fetchone()
        protected_state=c.s.prior_state(db,protected)
        evidence=db.execute("SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND created_at>%s ORDER BY created_at LIMIT 100",(p['prior_ids'],p['at'])).fetchall()
    m.save(RUN/'production-initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution=institution,read_only=True))
    m.save(RUN/'prior-evidence-additions-001.json.gz',dict(at=m.now(),changed=changed,citations=evidence,policy='Observed independent additions since previous baseline. No attribution to an actor without audit evidence; preserve current state. Old plan and delivery evidence unchanged.'))
    m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_checkpoint=c.ref(c.CP),previous_delivery_verification=verification,previous_protected_hash_changes=changed,previous_delivery_note='All 140 W134 records, images, citations, holdings and old8 verified. Prior protected set differs by one artist link and two citations. Verify used current prior hashes only for this documented comparison, without changing plan or database.',prior_production_ids=protected,prior_state=protected_state,prior_plan=c.ref(a.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],historical_pin_reconciliation_reference=cp['historical_pin_reconciliation_reference'],policy='Fresh scoped production read-only state and2938protectedIDs; local snapshot captured by v1 before its prior-state mismatch. No catalogue changes.'))
    print(json.dumps(dict(baseline_complete=True,protected_prior=len(protected),counts=counts,scoped=len(ids),recent_citations=len(evidence))),flush=True)

if __name__=='__main__':main()
