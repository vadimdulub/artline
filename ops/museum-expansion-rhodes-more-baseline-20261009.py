"""Rhodes museum selected native sources with fresh read-only baselines."""
import argparse,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-rhodes-more-common-20261009.py');src=module('src','museum-expansion-beziers-source-20261009.py');prior=module('prior','museum-expansion-rhodes-apply-20261009.py');m=s.m;RUN=s.RUN;src.RUN=RUN;prod=src.prod
def baseline():
 assert s.ref(s.CP)['sha256']=='85128076d9d2ea89f626f157c1adea9704d4f1c60195037ce8efb250545ae09a'
 for key,connect in [('initial',m.connect),('production-initial',prod.connect)]:
  dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
  with connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
   if key=='production-initial':p,d=prior.validate_plan();verification=prior.verify(db,p,d)
  m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(target=key,scope=len(ids),counts=counts)),flush=True)
 cp=m.load(s.CP);m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_checkpoint=s.ref(s.CP),previous_goal_turn='progress',verification=verification,prior_production_ids=p['prior_ids']+[v['artwork_id'] for v in p['records']],prior_plan=prior.reference(prior.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],policy='Fresh previous production delivery and all712prior production records verified. Historical archive proof inherited by pinned checkpoint. Local catalogue read-only; all source holds persist.'))
if __name__=='__main__':baseline()
