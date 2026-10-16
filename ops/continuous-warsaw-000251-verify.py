#!/usr/bin/env python3
"""Run the established Warsaw independent verifier against batch 251."""
from pathlib import Path
src=(Path(__file__).with_name('continuous-warsaw-000105-verify.py').read_text()
     .replace("continuous-warsaw-batch-000105.py","continuous-warsaw-batch-000251.py"))
exec(compile(src,__file__,'exec'),globals())
