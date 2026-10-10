"""Fresh production readback of the previous delivery; inherited archive proof stays immutable."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-beziers-common-20261009.py');prior=module('prior','museum-expansion-girodet-apply-v3-20261009.py');m=s.m;RUN=s.RUN
def main():
 p,d=prior.validate_plan();assert s.ref(s.CP)['sha256']=='820d619b2efa7387fa8d307ecba63a696b11344f258072f7307beca4f390f6d7';cp=m.load(s.CP)
 with prior.i.prod.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');result=prior.verify(db,p,d)
 m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_checkpoint=s.ref(s.CP),previous_goal_turn='progress',verification=result,prior_production_ids=[v['artwork_id'] for v in p['records']],prior_plan=prior.reference(prior.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],policy='Fresh previous production delivery verified. Prior complete archive validation inherited with pinned checkpoint; no repeat claim that all35541 historical files were read again. Local catalogue remains read-only. All research queues and provider holds persist.'))
 print(json.dumps(dict(previous_added=result['verified_new_records'],previous_counts=result['current_counts'])),flush=True)
if __name__=='__main__':main()
