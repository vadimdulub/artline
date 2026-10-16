#!/usr/bin/env python3
"""Finalize bounded batch 191 from the established batch-190 verifier."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000190-finalize.py").read_text()
source = source.replace("batches/000190", "batches/000191")
source = source.replace("batches/000190'", "batches/000191'")
source = source.replace("batch=190", "batch=191")
source = source.replace("start_position']==500", "start_position']==525")
source = source.replace("resume_position']==525", "resume_position']==550")
source = source.replace("range(500,525)", "range(525,550)")
source = source.replace("old['position']==500", "old['position']==525")
source = source.replace("position=525", "position=550")
source = source.replace("positions_500_524", "positions_525_549")
source = source.replace("positions 525 onward", "positions 550 onward")
source = source.replace("old_position=500,new_position=525", "old_position=525,new_position=550")
source = source.replace("batch=190,", "batch=191,")
source = source.replace("rijks_positions=25", "rijks_positions=25")
source = source.replace("positions 525–549", "positions 550–574")
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
