#!/usr/bin/env python3
"""Bounded batch 158: process Smithsonian SAAM shard 14."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000157.py")
source = BASE.read_text()
for old, new in [
    ("000157", "000158"), ("batch 157", "batch 158"), ("b000157", "b000158"),
    ("saam-013", "saam-014"), ("saam-13", "saam-14"),
    ("shard13", "shard14"), ("shard 13", "shard 14"), ("shard-13", "shard-14"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/13.txt", "/metadata/edan/saam/14.txt")

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
