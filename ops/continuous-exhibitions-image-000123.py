#!/usr/bin/env python3
"""Bounded batch 123 adapter for the established Cleveland image workflow."""
from pathlib import Path

source = (Path(__file__).with_name("continuous-exhibitions-image-000103.py")).read_text()
replacements = {
    "batch 103": "batch 123",
    "000103": "000123",
    "batch-000103": "batch-000123",
    "c03ca5a0-3a29-52f8-93fc-c9699db78b12": "47e3a636-bb6b-55d3-aa5c-635cc614533c",
    "111063": "111053",
    "1929.556": "1929.549",
    "(900,474)": "(900,696)",
    "anonymous 16th-century drawing added in batch 102": "Carletto Caliari’s c. 1586 recto/verso drawing",
    "Anonymous. The Cleveland Museum of Art.": "Carletto Caliari. The Cleveland Museum of Art.",
    " — Anonymous": " — Carletto Caliari",
    "five existing exact historical-exhibition links": "eleven existing exact historical-exhibition links",
    "len(entries)==5": "len(entries)==11",
    "len(entries)=5": "len(entries)=11",
    "exact_existing_links_illustrated=5": "exact_existing_links_illustrated=11",
    "exactExhibitionLinksIllustrated=5": "exactExhibitionLinksIllustrated=11",
    "batch=103": "batch=123",
    "97,550": "97,780",
    "after native 111053": "after native 111053",
}
for old, new in replacements.items():
    source = source.replace(old, new)
exec(compile(source, __file__, "exec"), globals())
