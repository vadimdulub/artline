#!/usr/bin/env python3
"""Bounded batch 160: process Smithsonian SAAM shard 16."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000159.py")
source = BASE.read_text()
for old, new in [
    ("000159", "000160"), ("batch 159", "batch 160"), ("b000159", "b000160"),
    ("saam-015", "saam-016"), ("saam-15", "saam-16"),
    ("shard15", "shard16"), ("shard 15", "shard 16"), ("shard-15", "shard-16"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/15.txt", "/metadata/edan/saam/16.txt")
# Preserve established catalogue precision for explicit non-circa year ranges.
source = source.replace(
    "('circa_range' if r['precision']=='circa' and r['first']!=r['last'] else r['precision'])",
    "('circa_range' if r['precision']=='circa' and r['first']!=r['last'] else ('range' if r['precision']=='exact' and r['first']!=r['last'] else r['precision']))",
)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
