#!/usr/bin/env python3
"""Record explicit human/assistant sheet inspection; does not inspect images itself."""
import argparse, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('cesi-top100-20261010.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def record(sheet,holds):
    d=m.load(m.RUN/'sheets'/f'{sheet:03}.json')
    assert m.sha(Path(d['path']).read_bytes())==d['sha256']
    assert set(holds)<=set(str(r['number']) for r in d['items'])
    cesi={r['artwork_id'] for r in m.load(m.RUN/'visual-review/cesi-individual.json')['decisions']}
    decisions=[]
    for r in d['items']:
        if r['artwork_id'] in cesi:continue
        reason=holds.get(str(r['number']))
        decisions.append(dict(artwork_id=r['artwork_id'],sha256=r['sha256'],decision='hold' if reason else 'accept',note=reason or 'Assistant inspected this contact-sheet image: recognizable source artwork, legible composition, no placeholder or obvious corrupt file. Metadata and duplicate/version checks remain separate.'))
    m.save(m.RUN/'visual-review'/f'sheet-{sheet:03}.json',dict(at=m.now(),sheet=sheet,sheet_sha256=d['sha256'],decisions=decisions))
    print('Recorded inspected sheet',sheet,'images',len(decisions),'holds',len(holds))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('sheet',type=int);p.add_argument('holds_json');a=p.parse_args();record(a.sheet,json.loads(a.holds_json))
