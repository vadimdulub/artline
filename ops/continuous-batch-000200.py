#!/usr/bin/env python3
"""Execute bounded batch 200 using the established SAAM shard reconciler."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000195.py").read_text()
source = source.replace("000195", "000200")
source = source.replace("batch=195", "batch=200")
source = source.replace("last_batch=195", "last_batch=200")
source = source.replace(".195.tmp", ".200.tmp")
source = source.replace("shard28", "shard30")
source = source.replace("shard 28", "shard 30")
source = source.replace("saam-28", "saam-30")
source = source.replace("/28.txt", "/30.txt")
source = source.replace("'28'", "'30'")
source = source.replace("next_shard='29'", "next_shard='31'")
source = source.replace("resume_cursor']['next_shard']=='29'", "resume_cursor']['next_shard']=='31'")
source = source.replace("Batch 195 classified", "Batch 200 classified")
source = source.replace("resume at shard29", "resume at shard31")
source = source.replace("at shard29", "at shard31")
source = source.replace("returning to SAAM shard29", "returning to SAAM shard31")
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
