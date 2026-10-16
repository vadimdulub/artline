#!/usr/bin/env python3
"""Run the established Rijks scoped recovery for bounded batch 193."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-rijks-000065-recovery.py").read_text()
source = source.replace("continuous-rijks-images-000065.py", "continuous-rijks-images-000193.py")
exec(compile(source, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
