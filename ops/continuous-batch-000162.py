#!/usr/bin/env python3
"""Bounded batch 162: process Smithsonian SAAM shard 18."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000160.py")
source = BASE.read_text()
for old, new in [
    ("000160", "000162"), ("batch 160", "batch 162"), ("b000160", "b000162"),
    ("saam-016", "saam-018"), ("saam-16", "saam-18"),
    ("shard16", "shard18"), ("shard 16", "shard 18"), ("shard-16", "shard-18"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/16.txt", "/metadata/edan/saam/18.txt")
source = source.replace("Batch 146", "Batch 162").replace("batch=146", "batch=162")
source = source.replace(
    "Process a bounded Smithsonian SAAM shard 03 segment, prioritizing exact missing-image legacy paintings; shard 18 is fully classified and the exhausted French reserve must not be replayed.",
    "Process bounded Smithsonian SAAM shard 19 or rotate to another undercovered permitted registry museum; do not replay shards 01–18 or the exhausted French reserve.",
)
source = source.replace("completed_shard='02',next_shard='03'", "completed_shard='18',next_shard='19'")

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
