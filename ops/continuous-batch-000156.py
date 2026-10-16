#!/usr/bin/env python3
"""Bounded batch 156: process Smithsonian SAAM shard 12."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000155.py")
source = BASE.read_text()
for old, new in [
    ("000155", "000156"), ("batch 155", "batch 156"), ("b000155", "b000156"),
    ("saam-011", "saam-012"), ("saam-11", "saam-12"),
    ("shard11", "shard12"), ("shard 11", "shard 12"), ("shard-11", "shard-12"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/11.txt", "/metadata/edan/saam/12.txt")

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
