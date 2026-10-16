#!/usr/bin/env python3
"""Finalize four verified image attachments from bounded SAAM shard 13."""
from pathlib import Path

base = Path(__file__).with_name("continuous-batch-000146.py")
source = base.read_text()
for old, new in [
    ("000146", "000157"), ("batch 146", "batch 157"), ("Batch 146", "Batch 157"),
    ("b000146", "b000157"), ("saam-002", "saam-013"), ("saam-02", "saam-13"),
    ("shard02", "shard13"), ("shard 02", "shard 13"), ("shard-02", "shard-13"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/02.txt", "/metadata/edan/saam/13.txt")
source = source.replace("status='saam_shard13_one_exact_legacy_primary_image_verified'", "status='saam_shard13_four_exact_legacy_primary_images_verified'")
source = source.replace("last_batch=146", "last_batch=157")
source = source.replace("completed_shard='02',next_shard='03'", "completed_shard='13',next_shard='14'")
source = source.replace("records_classified=67,eligible_exact_missing_image_matches=1", "records_classified=62,eligible_exact_missing_image_matches=4")
source = source.replace(
    "All 67 shard records classified; one exact existing SAAM legacy work was eligible and illustrated. Other records were nonmatches, already identified, already illustrated, out of scope, or lacked the required exact identity evidence.",
    "All 62 shard records classified; four exact existing SAAM legacy image gaps were selected and illustrated. Other records were nonmatches, already identified, already illustrated, out of scope, or lacked exact identity evidence.",
)
source = source.replace(
    "Process a bounded Smithsonian SAAM shard 03 segment, prioritizing exact missing-image legacy paintings; shard 02 is fully classified and the exhausted French reserve must not be replayed.",
    "Process bounded Smithsonian SAAM shard 14 or rotate to another undercovered permitted registry museum; do not replay shards 01–13 or the exhausted French reserve.",
)
source = source.replace("saam_shard02_records=67", "saam_shard13_records=62")
source = source.replace(
    "verified one new primary image on an exact existing Smithsonian American Art Museum painting after classifying all 67 shard-02 records.",
    "verified four new primary images on exact existing Smithsonian American Art Museum paintings after classifying all 62 shard-13 records.",
).replace("The derivative was individually viewed, is checksum-bound", "All four derivatives were individually viewed and are checksum-bound")
source = source.replace(
    "Batch 157 verified one new primary image on an exact existing Smithsonian American Art Museum painting after classifying all 67 shard-13 records. All four derivatives were individually viewed and are checksum-bound to the CC0 source record, and is publicly delivered;",
    "Batch 157 verified four new primary images on exact existing Smithsonian American Art Museum paintings after classifying all 62 shard-13 records. All four derivatives were individually viewed, checksum-bound to their CC0 source records, and publicly delivered;",
)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
