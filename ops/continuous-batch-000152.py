#!/usr/bin/env python3
"""Bounded batch 152: classify SAAM shard 08; no eligible exact image gaps."""
import sys
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000146.py")
source = BASE.read_text()
replacements = [
    ("000146", "000152"), ("batch 146", "batch 152"), ("b000146", "b000152"),
    ("saam-002", "saam-008"), ("saam-02", "saam-08"), ("shard02", "shard08"),
    ("shard 02", "shard 08"), ("shard-02", "shard-08"),
]
for old, new in replacements:
    source = source.replace(old, new)

# Shard 08 legitimately has no eligible exact legacy image gap. Preserve the
# complete classification and stop before image preparation or delivery.
source = source.replace(
    " assert rows\n save('saam-shard08-identity-reconciliation.json'",
    " save('saam-shard08-identity-reconciliation.json'",
).replace(
    " h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=rows));",
    "\n if not rows:return\n h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=rows));",
)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
