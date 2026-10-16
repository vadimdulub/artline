#!/usr/bin/env python3
"""Batch 236: resume bounded SAAM shard 42 reconciliation at offset 50."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000234.py").read_text()
source = source.replace("batch 234", "batch 236")
source = source.replace("Batch 234", "Batch 236")
source = source.replace("000234", "000236")
source = source.replace("[:50]", "[50:100]")
source = source.replace("bounded_limit=50", "bounded_limit=50,record_offset=50")
source = source.replace("captured_records=len(objects)", "captured_records=len(objects),records_before_offset=50")
source = source.replace("first50", "offset50_remaining")
source = source.replace("last_batch=234", "last_batch=236")
source = source.replace("records_classified=50", "records_classified=50+len(objects)")
source = source.replace("next_record_offset=50", "next_record_offset=50+len(objects)")
source = source.replace("Continue untouched SAAM shard 42 at record offset 50, then rotate to an untouched National Gallery Athens creator route.", "Shard 42 is complete; rotate to an undercovered permitted registry museum route and do not replay records 0–64.")
source = source.replace("Continue untouched SAAM shard 42 at record offset 50; then rotate to a newly selected National Gallery Athens creator route. Do not replay exhausted Lembesis/Bouzianis or unchanged source holds.", "Research an undercovered permitted registry museum route with stable object identity and explicit image evidence; do not replay completed SAAM shard 42, exhausted Lembesis/Bouzianis, or unchanged access holds.")
source = source.replace("the first 50 distinct records in untouched Smithsonian SAAM shard 42", "the remaining records in Smithsonian SAAM shard 42 from offset 50")
source = source.replace("the offset-50 resume cursor", "the completed-shard resume cursor")
source = source.replace("researched=50", "researched=len(objects)")
source = source.replace("discovered=len(objects)", "discovered=len(objects),record_offset=50")
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
