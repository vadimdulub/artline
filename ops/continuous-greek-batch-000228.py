#!/usr/bin/env python3
"""Batch 228: reuse the established Greek metadata delivery for eight Aivazovsky objects."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-greek-batch-000180.py").read_text()
source = source.replace("000180", "000228").replace("b000180", "b000228")
source = source.replace("greek-objects-v3", "greek-aivazovsky-objects-v1")
source = source.replace("athens-000", "athens-aivazovsky-228")
source = source.replace("ionian-all-object-urls.json", "aivazovsky-all-object-urls.json")
source = source.replace("h.no_collision=no_collision;h.NEW_ARTISTS=[new_artist()]", "h.no_collision=old_collision;h.NEW_ARTISTS=[]")
source = source.replace("code=code.replace('  after=snapshot(db,ids)','  add_creator_evidence(db,p,digest)\\n  after=snapshot(db,ids)')", "code=code.replace('  after=snapshot(db,ids)','  after=snapshot(db,ids)')")
exec(compile(source, __file__, "exec"), globals())
