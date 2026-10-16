#!/usr/bin/env python3
"""Finalize no-write batch 154 from the established batch-152 verifier."""
from pathlib import Path

base = Path(__file__).with_name("continuous-batch-000152-finalize.py")
source = base.read_text()
for old, new in [
    ("000152", "000154"), ("batch 152", "batch 154"), ("Batch 152", "Batch 154"),
    (".152.tmp", ".154.tmp"), ("saam-08", "saam-10"),
    ("shard08", "shard10"), ("shard-08", "shard-10"),
    ("shard 09", "shard 11"), ("shards 01–08", "shards 01–10"),
    ("completed_shard='08'", "completed_shard='10'"),
    ("next_shard='09'", "next_shard='11'"),
    ("last_batch=152", "last_batch=154"),
]:
    source = source.replace(old, new)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
