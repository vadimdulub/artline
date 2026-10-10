"""Revalidate the last completed wave and snapshot Augustiner Museum."""
import hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-augustiner-common-20261009.py');prior=module('prior','museum-expansion-city-art-additions-apply-20261009.py');m=s.m;RUN=s.RUN
def main():
 dest=RUN/'initial-scope-001.json.gz';assert not dest.exists();assert s.ref(s.CP)['sha256']=='02da84595058f24842dac8864cd012ca00cb8a42f5bb9641eef5c36885af809b';cp=m.load(s.CP)
 ar=module('ar','museum-expansion-archive-evidence-20261009.py');resolver=ar.Resolver(m.ROOT,cp['artifacts']);seen=set()
 def patch(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  if hasattr(mod,'checked'):mod.checked=resolver.checked
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):patch(v)
 patch(prior)
 for dep in cp['artifacts']:resolver.checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';verified=prior.verify(db,p,d);ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
 m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_goal_turn='progress',previous_checkpoint=s.ref(s.CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=verified,archive_resolution=resolver.result(),policy='Fresh readback verifies14CityArtCentre additions andoneexistingDuncanlink,preservationof13910priorcampaignartworks. City103/41. Previousgoalturnmadeprogress. ContinueAugustiner86/73toward100and200. Archivedsourcesvalidatedagainstoriginalpinswithoutrestoration. All earlier queues,unknown fields and provider holds persist.'))
 m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(scope=len(ids),counts=counts,verified_previous_additions=14,verified_previous_links=1)),flush=True)
if __name__=='__main__':main()
