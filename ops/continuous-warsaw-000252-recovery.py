#!/usr/bin/env python3
"""Continue batch-252 scoped recovery after completed visual gates."""
from pathlib import Path
src=Path(__file__).with_name('continuous-warsaw-000251-prepare.py').read_text()
src=src.replace('continuous-warsaw-batch-000251.py','continuous-warsaw-batch-000252.py')
start=src.index("b.save('production-target-before-scoped-recovery.json'")
prefix=src[:src.index('checks=[]')]
exec(compile(prefix+src[start:],__file__,'exec'),globals())
