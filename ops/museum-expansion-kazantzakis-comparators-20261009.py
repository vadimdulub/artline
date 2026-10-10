"""Protect all bounded identity comparators and current museum records."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-kazantzakis-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);m=i.m;RUN=i.RUN
x=m.load(RUN/'production-identity-001.json.gz');ids=x['state']['artwork_ids']
with i.prod.connect()as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=i.s.snapshot(db,ids)
m.save(RUN/'subject-comparators-001.json.gz',dict(at=m.now(),ids=ids,snapshot=snap,identity_reference=i.s.ref(RUN/'production-identity-001.json.gz'),script_reference=i.s.ref(Path(__file__).resolve()),assessment='All21 identity candidates protected.18 existing Kazantzakis records have different native object IDs and subjects from the new selection; all their metadata,unknown dates and media preserved. Three other exact translated-title candidates are Mikhail Larionov Costume Design1915,Varvara Stepanova Costume Design1922,and Bernard Rosenthal Odyssey1968(Q27616189,MID.B.288). Different documented creators,physical versions and sources from the Greek theatre designs and Hans Enri Odyssey illustrations. No exact source/citation/identifier hits among134 candidates; no named artist authority matches to invent. Internal repeated-title/physical-sheet distinctions require separate visual review.',read_only=True));print(json.dumps(dict(protected_comparators=len(ids))),flush=True)
