#!/usr/bin/env python3
"""Bounded recovery/delivery of the six Warsaw icons selected in batch 249."""
import fcntl, gzip, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("warsaw105", ROOT / "ops/continuous-warsaw-batch-000105.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

b.E = ROOT / "docs/research/continuous-production-20261011/batches/000251/warsaw"
b.R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000251"
b.OP = "continuous-warsaw-20261014-b000251"
b.PHASE = "warsaw-icons"
# The inherited, checksum-pinned helper retains its established citation field.
b.FIELD = "continuous_warsaw_object_evidence_20261011_b000105"
b.B = "warsaw-000"
b.SELECTED = [498663, 498335, 498657, 498667, 498656, 498653]
b.ALL_IDS = b.SELECTED
b.DATES = {
    498663: ("XIX w.", 1801, 1900),
    498335: ("XVIII w.", 1701, 1800),
    498657: ("XVIII/XIX w.", 1701, 1900),
    498667: ("XVIII/XIX w.", 1701, 1900),
    498656: ("XVIII/XIX w.", 1701, 1900),
    498653: ("koniec  XIX w.", 1876, 1900),
}
b.REVIEWS = {
    498663: "One painted wooden icon combining the Resurrection and twelve feast scenes; not thirteen separate works. Native inventory IK 50 MNW and dimensions distinguish this version.",
    498335: "One painted wooden icon in a metal oklad, inventory IK 115/a-b MNW. The support and cover are components of one physical object, not separate artworks.",
    498657: "One Deesis icon of the Mother of God with feast scenes and border saints, inventory IK 46 MNW. It is distinct from the companion Saint John icon IK 45 MNW despite matching dimensions.",
    498667: "One Resurrection icon, inventory IK 53 MNW. Exact inventory and dimensions distinguish it from the other Resurrection versions in this cohort.",
    498656: "One Deesis icon of Saint John the Baptist with feast scenes and border saints, inventory IK 45 MNW. It is distinct from companion inventory IK 46 MNW.",
    498653: "One late-nineteenth-century Resurrection icon, inventory IK 42 MNW. Exact inventory and 29.5 by 25 cm dimensions distinguish this version.",
}

for p in [b.E, b.R]:
    p.mkdir(parents=True, exist_ok=True)
b.h.OP = b.OP
b.h.RUN = b.E
b.h.BACKUP = Path.home() / "Library/Application Support/Artline/backups" / b.OP
b.h.BACKUP.mkdir(parents=True, exist_ok=True)
b.i.OP = b.OP + "-images"
b.i.RUN = b.E
b.i.ORIG = Path.home() / "Library/Application Support/Artline/source-images" / b.i.OP
b.i.BACKUP = Path.home() / "Library/Application Support/Artline/backups" / b.i.OP

ledger_path = ROOT / "docs/research/continuous-production-20261011/batches/000249/warsaw-page1-pending-source-verification.json"
ledger = {str(x["source_id"]): x for x in json.loads(ledger_path.read_text())["records"]}
runtime249 = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000249"

def capture(oid):
    raw = gzip.decompress((runtime249 / f"object-{oid}.json.gz").read_bytes())
    assert b.h.sha(raw) == ledger[str(oid)]["source_sha256"]
    payload = json.loads(raw)
    obj = payload.get("data", payload)
    assert int(obj["id"]) == oid
    receipt = {
        "status": 200,
        "url": ledger[str(oid)]["api_url"],
        "retrieved_at": json.loads(ledger_path.read_text())["at"],
        "sha256": b.h.sha(raw),
        "body_path": str(runtime249 / f"object-{oid}.json.gz"),
    }
    b.h.save(b.E / f"object-{oid}.json", {"data": obj})
    b.h.save(b.E / f"object-{oid}.receipt.json", receipt)
    return obj, receipt

b.capture = capture

policy_receipt = ROOT / "docs/research/continuous-production-20261011/batches/000105/warsaw/policy-project.receipt.json"
if not (b.E / "policy-project.receipt.json").exists():
    b.h.save(b.E / "policy-project.receipt.json", json.loads(policy_receipt.read_text()))

# Re-export the adapted helper surface for the established independent verifiers.
h=b.h; i=b.i; E=b.E; R=b.R; PHASE=b.PHASE; B=b.B; MID=b.MID; MUSEUM=b.MUSEUM; FIELD=b.FIELD; OP=b.OP; SCHEME=b.SCHEME
pinned=h.pinned; target=b.target; save=b.save; stage=b.stage; images=b.images; apply=b.apply; deliver=b.deliver

if __name__ == "__main__":
    with (b.R / "worker.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        getattr(b, sys.argv[1])()
