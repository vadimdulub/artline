#!/usr/bin/env python3
"""Bounded batch 155: process Smithsonian SAAM shard 11."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000146.py")
source = BASE.read_text()
replacements = [
    ("000146", "000155"), ("batch 146", "batch 155"), ("b000146", "b000155"),
    ("saam-002", "saam-011"), ("saam-02", "saam-11"), ("shard02", "shard11"),
    ("shard 02", "shard 11"), ("shard-02", "shard-11"),
]
for old, new in replacements:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/02.txt", "/metadata/edan/saam/11.txt")

# A fully classified shard may legitimately yield no exact legacy image gap.
source = source.replace(
    " assert rows\n save('saam-shard11-identity-reconciliation.json'",
    " save('saam-shard11-identity-reconciliation.json'",
).replace(
    " h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=rows));",
    "\n if not rows:return\n h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=rows));",
)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
