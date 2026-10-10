"""Verify delivered wave75; rebase three-museum continuation without DB writes."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-italy-fourth-apply-20261008.py'));prior=importlib.util.module_from_spec(z);z.loader.exec_module(prior);m=prior.m;ref=prior.reference;checked=prior.checked;RUN=m.RUN/'native/italy-fifth-minimum-20261008';CP=prior.RUN/'delivery-checkpoint-001.json'
def main():
 dest=RUN/'continuation-001.json';assert not dest.exists();assert ref(CP)['sha256']=='a3c9fc7e88c495ffcad685720d19c063ebb2d59074d326bab5c613b4b1345968';cp=m.load(CP)
 for d in cp['artifacts']:checked(d)
 for d in cp['external_artifacts']:assert hashlib.sha256(Path(d['path']).read_bytes()).hexdigest()==d['sha256']
 p,digest=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');result=prior.verify(db,p,digest)
  ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(prior.IIDS,prior.IIDS))];assert len(ids)==505
  initial=dict(at=m.now(),scoped_ids=ids,snapshot=prior.snapshot(db,ids),counts=prior.counts(db),institutions=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(prior.IIDS,))],read_only=True)
 m.save(RUN/'initial-scope-001.json.gz',initial);m.save(dest,dict(at=m.now(),previous_goal_turn='progress',verified_new=135,previous_checkpoint=ref(CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=result,script_reference=ref(Path(__file__).resolve()),policy='Continue researched Cenacolo, Ala Ponzone and Villa Guinigi objects. Previous135 additions verified, not a no-progress turn. Initial five-museum scope rebased505; prior campaign10833. All access holds unchanged.'))
 print(json.dumps(dict(verified_previous=135,scoped=len(ids),counts=initial['counts'],pins=len(cp['artifacts']))),flush=True)
if __name__=='__main__':main()
