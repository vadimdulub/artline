#!/usr/bin/env python3
"""Execute the established bounded French reserve worker as batch 226."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-french-reserve-batch-000001.py").read_text()
source = source.replace("000001", "000226")
# Preserve a complete reconciliation receipt when concurrent workers have
# consumed every reserve candidate; the immutable source plan is unchanged.
source = source.replace(
    "assert selected\n m.save(RUN/'reserve-reconciliation.json'",
    "m.save(RUN/'reserve-reconciliation.json'",
)
source = source.replace(
    "m.save(RUN/'prior-visual-evidence.json'",
    "\n if not selected:\n  print(json.dumps(dict(selected=0, reserve_inspected=len(rows), skipped=len(skipped))))\n  return\n m.save(RUN/'prior-visual-evidence.json'",
)
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
