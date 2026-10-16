#!/usr/bin/env python3
"""Record explicit contact-sheet decisions after actual visual inspection.

Argument maps sheet numbers to one-based positions and hold reasons. An empty
map for a sheet approves the displayed images. This does not perform review.
"""
import importlib.util,json,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('s',Path(__file__).with_name('soviet-realism-20261011.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for number,held in json.loads(sys.argv[1]).items():
 sheet=m.load(m.RUN/'visual-sheets'/(number+'.json'))
 decisions={sheet['images'][int(i)-1]['artwork_id']:reason for i,reason in held.items()}
 m.save(m.RUN/'visual-decisions'/(number+'.json'),dict(at=m.now(),sheet_sha256=m.sha(Path(sheet['sheet']).read_bytes()),approved=[x['artwork_id'] for x in sheet['images'] if x['artwork_id'] not in decisions],held=decisions,review='All displayed source frames visually inspected for artwork content, source/title coherence, frame completeness and repeated or composite reproductions. Original source frames retained. Automated source/date/identity checks remain independent.'))
