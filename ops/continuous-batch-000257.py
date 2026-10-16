#!/usr/bin/env python3
"""Bounded batch 257: resume Getty Byzantine discovery at offset 300."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000248.py").read_text()
source = source.replace("batch 248", "batch 257")
source = source.replace("Batch 248", "Batch 257")
source = source.replace("000248", "000257")
source = source.replace("offset 250", "offset 300")
source = source.replace("offset250", "offset300")
source = source.replace("from=250", "from=300")
source = source.replace("offset=250", "offset=300")
source = source.replace("last_offset=250,next_offset=300", "last_offset=300,next_offset=350")
source = source.replace("last_offset=300,next_offset=300", "last_offset=300,next_offset=350")
source = source.replace("Getty offset-250", "Getty offset-300")
source = source.replace("Getty offset250", "Getty offset300")
source = source.replace("Getty offset 250", "Getty offset 300")
source = source.replace("Getty offset250", "Getty offset300")
source = source.replace("getty-offset250", "getty-offset300")
source = source.replace("last_batch=248", "last_batch=257")
source = source.replace("batch=248", "batch=257")
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
