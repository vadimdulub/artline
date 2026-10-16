#!/usr/bin/env python3
"""Finalize the three verified image attachments from bounded SAAM shard 12."""
from pathlib import Path

base = Path(__file__).with_name("continuous-batch-000155-finalize.py")
source = base.read_text()
for old, new in [
    ("000155", "000156"), ("batch 155", "batch 156"), ("Batch 155", "Batch 156"),
    ("b000155", "b000156"), ("saam-011", "saam-012"), ("saam-11", "saam-12"),
    ("shard11", "shard12"), ("shard 11", "shard 12"), ("shard-11", "shard-12"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/11.txt", "/metadata/edan/saam/12.txt")
source = source.replace("four verified image attachments", "three verified image attachments")
source = source.replace("four new primary images", "three new primary images")
source = source.replace("All four derivatives", "All three derivatives")
source = source.replace("73 shard-12 records", "68 shard-12 records")
source = source.replace("records_classified=73,eligible_exact_missing_image_matches=5", "records_classified=68,eligible_exact_missing_image_matches=4")
source = source.replace("saam_shard12_records=73", "saam_shard12_records=68")
source = source.replace("completed_shard='11',next_shard='12'", "completed_shard='12',next_shard='13'")
source = source.replace("last_batch=155", "last_batch=156")
source = source.replace("shards 01–11", "shards 01–12")
source = source.replace("shard-11 hold", "shard-12 hold")

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
