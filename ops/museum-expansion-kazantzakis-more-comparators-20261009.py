"""Protect all bounded identity comparators and current museum records."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-kazantzakis-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);m=i.m;RUN=i.RUN
x=m.load(RUN/'production-identity-001.json.gz');ids=x['state']['artwork_ids']
with i.prod.connect()as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=i.s.snapshot(db,ids)
m.save(RUN/'subject-comparators-001.json.gz',dict(at=m.now(),ids=ids,snapshot=snap,identity_reference=i.s.ref(RUN/'production-identity-001.json.gz'),script_reference=i.s.ref(Path(__file__).resolve()),assessment='All128 bounded records and149citations reviewed and protected:118existing museum artworks plus10 translated-title comparators. External Costume Design entries belong to Larionov1915 andStepanova1922; Stage Design to MauroAntonioTesi c1755; Olympia records toManet,Mueller,Maleas,Humphrey,Twombly. Their sources,versions,dates andcreators differ from the selected1940–1941 Greek theatre designs. No exact source IDs,URLs,citations or artist-authority matches. Repeated theatre titles do not establish physical identity. Current source35040 is a finished green Emma design,related by source toF032a/030; existing34229 and34224 are distinct unfinished1943Popolaros supports. Retain all conflicting contextual evidence,no date orattribution rewrite.',read_only=True));print(json.dumps(dict(protected_comparators=len(ids))),flush=True)
