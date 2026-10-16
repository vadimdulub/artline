#!/usr/bin/env python3
"""Bounded batch 161: process Smithsonian SAAM shard 17."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000160.py")
source = BASE.read_text()
for old, new in [
    ("000160", "000161"), ("batch 160", "batch 161"), ("b000160", "b000161"),
    ("saam-016", "saam-017"), ("saam-16", "saam-17"),
    ("shard16", "shard17"), ("shard 16", "shard 17"), ("shard-16", "shard-17"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/16.txt", "/metadata/edan/saam/17.txt")

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
