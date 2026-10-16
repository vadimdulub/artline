#!/usr/bin/env python3
"""Batch 270: bounded SAAM shard 44 reconciliation using the established read-only workflow."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000195.py").read_text()
source = source.replace("000195", "000270")
source = source.replace("batch=195", "batch=270")
source = source.replace("last_batch=195", "last_batch=270")
source = source.replace(".195.tmp", ".270.tmp")
source = source.replace("shard28", "shard44")
source = source.replace("shard 28", "shard 44")
source = source.replace("saam-28", "saam-44")
source = source.replace("/28.txt", "/44.txt")
source = source.replace("'28'", "'44'")
source = source.replace("next_shard='29'", "next_shard='45'")
source = source.replace("resume_cursor']['next_shard']=='29'", "resume_cursor']['next_shard']=='45'")
source = source.replace("Batch 195 classified", "Batch 270 classified")
source = source.replace("resume at shard29", "resume at shard45")
source = source.replace("at shard29", "at shard45")
source = source.replace("returning to SAAM shard29", "returning to SAAM shard45")
source = source.replace("objects=[json.loads(x) for x in raw.splitlines()]", "all_objects=[json.loads(x) for x in raw.splitlines()];objects=all_objects[:50]")
source = source.replace("records_classified=len(objects),candidate_native_ids", "records_classified=len(objects),next_record_offset=50,total_records_in_shard=len(all_objects),candidate_native_ids")
source = source.replace("All shard records classified; candidate matches held", "First 50 shard records classified; candidate matches held")
source = source.replace("completed_shard='44',next_shard='45'", "completed_shard=None,next_shard='44'")
source = source.replace("assert s['resume_cursor']['next_shard']=='44'", "assert s['resume_cursor']['next_shard']=='44'")
source = source.replace("then resume at shard45", "then resume shard44 at record offset 50")
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
