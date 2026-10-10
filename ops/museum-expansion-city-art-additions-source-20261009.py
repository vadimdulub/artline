"""Revalidate the last completed wave and snapshot City Art Centre."""
import hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-city-art-additions-common-20261009.py');prior=module('prior','museum-expansion-box-continuation-apply-20261009.py');m=s.m;RUN=s.RUN
def main():
 dest=RUN/'initial-scope-001.json.gz';assert not dest.exists();assert s.ref(s.CP)['sha256']=='7004b77d2b41e2b9b3062316063959e3410353db974acf20d6bbebb918dbad25';cp=m.load(s.CP)
 for dep in cp['artifacts']:s.checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';verified=prior.verify(db,p,d);ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
 m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_checkpoint=s.ref(s.CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=verified,policy='Fresh readback verifies21Box additions and preservation of13889prior campaign artworks. Box118/56. Previous goal turn made concrete progress; no repeated global blocker. Continue CityArtCentre88/29toward100and200. All earlier queues,unknown fields and provider holds persist.'))
 m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(scope=len(ids),counts=counts,verified_previous_additions=21)),flush=True)
if __name__=='__main__':main()
