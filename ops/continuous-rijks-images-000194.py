#!/usr/bin/env python3
"""Bounded batch 194 Rijks reserve continuation using the established batch-65 adapter."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "ops/continuous-rijks-images-000065.py").read_text()
source = source.replace("batches/000065", "batches/000194")
source = source.replace("batch=65", "batch=194")
source = source.replace("B='rijks-065'", "B='rijks-194'")
source = source.replace("b000065", "b000194")
source = source.replace("assert cursor==100", "assert cursor==600")
source = source.replace("cursor:cursor+400", "cursor:cursor+25")
source = source.replace("if len(selected)==20", "if len(selected)==25")
source = source.replace("window_limit=400", "window_limit=25")
exec(compile(source, __file__, "exec"), globals())
