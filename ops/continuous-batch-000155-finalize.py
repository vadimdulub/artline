#!/usr/bin/env python3
"""Finalize the four verified image attachments from bounded SAAM shard 11."""
from pathlib import Path

base = Path(__file__).with_name("continuous-batch-000146.py")
source = base.read_text()
for old, new in [
    ("000146", "000155"), ("batch 146", "batch 155"), ("Batch 146", "Batch 155"),
    ("b000146", "b000155"), ("saam-002", "saam-011"), ("saam-02", "saam-11"),
    ("shard02", "shard11"), ("shard 02", "shard 11"), ("shard-02", "shard-11"),
]:
    source = source.replace(old, new)
source = source.replace("/metadata/edan/saam/02.txt", "/metadata/edan/saam/11.txt")
source = source.replace(
    "ids=[x['artwork_id'] for x in rows];expected={x['artwork_id']:x for x in images}",
    "ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images}",
)
source = source.replace("status='saam_shard02_one_exact_legacy_primary_image_verified'", "status='saam_shard11_four_exact_legacy_primary_images_verified_one_source_hold'")
source = source.replace("last_batch=146", "last_batch=155")
source = source.replace("completed_shard='02',next_shard='03'", "completed_shard='11',next_shard='12'")
source = source.replace("records_classified=67,eligible_exact_missing_image_matches=1", "records_classified=73,eligible_exact_missing_image_matches=5")
source = source.replace("newly_illustrated_native_ids=[r['native_id'] for r in rows]", "newly_illustrated_native_ids=[r['native_id'] for r in rows if r['artwork_id'] in ids]")
source = source.replace(
    "All 67 shard records classified; one exact existing SAAM legacy work was eligible and illustrated. Other records were nonmatches, already identified, already illustrated, out of scope, or lacked the required exact identity evidence.",
    "All 73 shard records classified; five exact existing SAAM legacy image gaps were selected, four were illustrated and one remains on a bounded source connection hold. Other records were nonmatches, already identified, already illustrated, out of scope, or lacked exact identity evidence.",
)
source = source.replace(
    "Process a bounded Smithsonian SAAM shard 03 segment, prioritizing exact missing-image legacy paintings; shard 02 is fully classified and the exhausted French reserve must not be replayed.",
    "Process bounded Smithsonian SAAM shard 12 or rotate to another undercovered permitted registry museum; do not replay shards 01–11 or the exhausted French reserve. Retain the single shard-11 source connection hold for a later changed-state retry.",
)
source = source.replace("saam_shard02_records=67", "saam_shard11_records=73")
source = source.replace(
    "verified one new primary image on an exact existing Smithsonian American Art Museum painting after classifying all 67 shard-02 records.",
    "verified four new primary images on exact existing Smithsonian American Art Museum paintings after classifying all 73 shard-11 records.",
).replace("The derivative was individually viewed, is checksum-bound", "All four derivatives were individually viewed and are checksum-bound")
source = source.replace("status='saam_shard11_one_exact_legacy_primary_image_verified'", "status='saam_shard11_four_exact_legacy_primary_images_verified_one_source_hold'")
source = source.replace("saam_shard11_records=67", "saam_shard11_records=73")
source = source.replace(
    "Process a bounded Smithsonian SAAM shard 03 segment, prioritizing exact missing-image legacy paintings; shard 11 is fully classified and the exhausted French reserve must not be replayed.",
    "Process bounded Smithsonian SAAM shard 12 or rotate to another undercovered permitted registry museum; do not replay shards 01–11 or the exhausted French reserve. Retain the single shard-11 source connection hold for a later changed-state retry.",
)
source = source.replace(
    "Batch 155 verified one new primary image on an exact existing Smithsonian American Art Museum painting after classifying all 67 shard-11 records. All four derivatives were individually viewed and are checksum-bound to the CC0 source record, and is publicly delivered;",
    "Batch 155 verified four new primary images on exact existing Smithsonian American Art Museum paintings after classifying all 73 shard-11 records. All four derivatives were individually viewed, checksum-bound to their CC0 source records, and publicly delivered;",
)

globals_dict = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, globals_dict["__file__"], "exec"), globals_dict)
