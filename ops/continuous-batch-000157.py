#!/usr/bin/env python3
"""Bounded batch 157: process Smithsonian SAAM shard 13."""
from pathlib import Path

BASE = Path(__file__).with_name("continuous-batch-000146.py")
source = BASE.read_text()
for old, new in [
    ("000146", "000157"), ("batch 146", "batch 157"), ("b000146", "b000157"),
    ("saam-002", "saam-013"), ("saam-02", "saam-13"),
    ("shard02", "shard13"), ("shard 02", "shard 13"), ("shard-02", "shard-13"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/02.txt", "/metadata/edan/saam/13.txt")
# Preserve the established catalogue precision for circa ranges such as 1908–1909.
source = source.replace(
    "precision='circa' if date.startswith('ca.') else 'exact'",
    "precision='circa_range' if date.startswith('ca.') and a['creation_year_start'] != a['creation_year_end'] else ('circa' if date.startswith('ca.') else 'exact')",
)
source = source.replace(
    "(r['title'],r['first'],r['last'],r['precision'],r.get('expected_museum_id',cfg['mid']))",
    "(r['title'],r['first'],r['last'],('circa_range' if r['precision']=='circa' and r['first']!=r['last'] else r['precision']),r.get('expected_museum_id',cfg['mid']))",
)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
