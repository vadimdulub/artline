#!/usr/bin/env python3
"""Bounded batch 159: process Smithsonian SAAM shard 15."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000158.py")
source = BASE.read_text()
for old, new in [
    ("000158", "000159"), ("batch 158", "batch 159"), ("b000158", "b000159"),
    ("saam-014", "saam-015"), ("saam-14", "saam-15"),
    ("shard14", "shard15"), ("shard 14", "shard 15"), ("shard-14", "shard-15"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/14.txt", "/metadata/edan/saam/15.txt")

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
