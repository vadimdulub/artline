#!/usr/bin/env python3
"""Finalize independent zero-write evidence and the batch-230 SAAM cursor."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000229-finalize.py").read_text()
source = source.replace("batch-229", "batch-230").replace("000229", "000230")
source = source.replace('== "37"', '== "__COMPLETED__"').replace('= "38"', '= "39"').replace('== "__COMPLETED__"', '== "38"')
source = source.replace("shard37", "shard38").replace("shard 37", "shard 38")
source = source.replace("saam-shard37", "saam-shard38")
source = source.replace("shard 38.", "shard 39.")
source = source.replace('"shard": 37', '"shard": 38').replace('"next_shard": 38', '"next_shard": 39')
source = source.replace('"queue_next_shard": 38', '"queue_next_shard": 39')
source = source.replace('s["last_batch"] = 229', 's["last_batch"] = 230')
source = source.replace('"classified": 83', '"classified": 58')
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
