#!/usr/bin/env python3
"""Version-level recovery of three Warsaw icons held by batch 251."""
import fcntl, importlib.util, inspect, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("warsaw251", ROOT / "ops/continuous-warsaw-batch-000251.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

b.E = ROOT / "docs/research/continuous-production-20261011/batches/000252/warsaw"
b.R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000252"
b.OP = "continuous-warsaw-20261014-b000252"
b.PHASE = "warsaw-icons"
b.B = "warsaw-000"
b.SELECTED = [498663, 498667, 498653]
b.ALL_IDS = b.SELECTED
b.DATES = {
    498663: ("XIX w.", 1801, 1900),
    498667: ("XVIII/XIX w.", 1701, 1900),
    498653: ("koniec  XIX w.", 1876, 1900),
}
b.REVIEWS = {
    498663: "Inventory IK 50 MNW, 31.5 by 26 cm, is a separate physical icon from same-title IK 58 MNW, 32.5 by 25.8 cm; native record and image show a separately inventoried composition/version.",
    498667: "Inventory IK 53 MNW, 31.5 by 26.5 cm, is a separate physical Resurrection icon from same-title IK 168 MNW, 48.5 by 40 cm; native record and image establish distinct scale and composition.",
    498653: "Inventory IK 42 MNW, 29.5 by 25 cm, is a separate late-nineteenth-century Resurrection icon from same-title IK 168 MNW, 48.5 by 40 cm; native record and image establish distinct scale and composition.",
}
for name in ['E','R','OP','PHASE','B','SELECTED','ALL_IDS','DATES','REVIEWS','FIELD']:
    setattr(b.b,name,getattr(b,name))
for p in [b.E, b.R]: p.mkdir(parents=True, exist_ok=True)
b.h.OP=b.OP; b.h.RUN=b.E
b.h.BACKUP=Path.home()/"Library/Application Support/Artline/backups"/b.OP
b.h.BACKUP.mkdir(parents=True,exist_ok=True)
b.i.OP=b.OP+"-images"; b.i.RUN=b.E
b.i.ORIG=Path.home()/"Library/Application Support/Artline/source-images"/b.i.OP
b.i.BACKUP=Path.home()/"Library/Application Support/Artline/backups"/b.i.OP

# Batch 251 intentionally held normalized-title matches. Here exact inventory,
# dimensions and composition have been reviewed, so title alone is not identity.
src=inspect.getsource(b.stage).replace(
    "if native or globalacc or exact or cit: reason='Existing or ambiguous global object identity; excluded from new increments.'",
    "if native or globalacc or cit: reason='Existing global object identity; excluded from new increments.'")
exec(compile(src,__file__,'exec'),b.b.__dict__)
b.stage=b.b.stage

h=b.h; i=b.i; E=b.E; R=b.R; PHASE=b.PHASE; B=b.B; OP=b.OP; SCHEME=b.SCHEME; FIELD=b.FIELD; MID=b.MID; MUSEUM=b.MUSEUM
pinned=h.pinned; target=b.target; save=b.save; stage=b.stage; images=b.images; apply=b.apply; deliver=b.deliver
b=b.b
b.FIELD='continuous_warsaw_object_evidence_20261011_b000105'

if __name__ == "__main__":
    with (b.R/"worker.lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        getattr(b,sys.argv[1])()
