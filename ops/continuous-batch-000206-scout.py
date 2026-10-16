#!/usr/bin/env python3
"""Run the established bounded Cleveland gap scout for batch 206."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-batch-000189.py").read_text()
source = source.replace("000189", "000206")
source = source.replace("batch':189", "batch':206")
exec(compile(source, str(root / "ops/continuous-batch-000189.py"), "exec"))
