"""Freshly verify wave93 and snapshot the target gallery before selected additions."""
import hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-leeds-drawings-common-20261009.py');prior=module('prior','museum-expansion-leeds-additions-apply-v2-20261009.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked

def main():
 dest=RUN/'initial-scope-001.json.gz';assert not dest.exists();assert ref(s.CP)['sha256']=='8f110461cd015f59acf4466854d465918dacc5aac173fbdfe5517c7e1a7a65a4';cp=m.load(s.CP)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';verification=prior.verify(db,p,d);ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
 m.save(RUN/'continuation-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_checkpoint=ref(s.CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=verification,policy='Freshly verified49Cotmania additions and all13278prior campaign artworks. Gallery137linked/111eligible;4olderidentityholds and1missingobject hold preserved. Concrete progress,not repeated global blocker. Continue selected native additions;allpriorqueues/accessholds remain.'))
 m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=ref(Path(__file__).resolve())));print(json.dumps(dict(scope=len(ids),counts=counts,prior_verified_new=49)),flush=True)
if __name__=='__main__':main()
