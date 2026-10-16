#!/usr/bin/env python3
"""Independent postwrite verification for bounded Rijks batch 193."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=(root/'ops/continuous-image-batch-000002-verify.py').read_text()
source=source.replace("ops/continuous-image-batch-000002.py", "ops/continuous-rijks-images-000193.py")
source=source.replace("assert search==25", "assert search==len(ids)")
source=source.replace("newly_illustrated=25", "newly_illustrated=len(ids)")
source=source.replace("'25 locked transaction preimages lacked primary media; 25 current assets carry this separate campaign adapter plus exact selection and visual-review checksums. Existing campaign increments excluded.'", "str(len(ids))+' locked transaction preimages lacked primary media; current assets carry this batch adapter plus exact selection and visual-review checksums. Existing campaign increments excluded.'")
source=source.replace("verified_public_images=25,verified_api_rows=25", "verified_public_images=len(ids),verified_api_rows=len(ids)")
start=source.index("backup=json.loads(")
end=source.index("counts=dict(",start)
source=source[:start]+source[end:]
source=source.replace("'Select a bounded undercovered NGA or WikiArt primary-image gap route; retain Rijks 044 cursor for later varied-source rotation.'", "'Research Rijksmuseum reserve positions 600–624, or rotate to another undercovered open-image registry route; do not revisit the exhausted French reserve.'")
exec(compile(source,__file__,'exec'),globals())
