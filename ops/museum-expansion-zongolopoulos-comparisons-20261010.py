"""Focused identity montages from the already-selected source thumbnails."""
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

spec=importlib.util.spec_from_file_location('z',Path(__file__).with_name('museum-expansion-zongolopoulos-source-20261010.py'))
z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
m,q,RUN=z.m,z.q,z.RUN
GROUPS=[[61,62,63],[21,22,23,24,27],[36,37],[51,52,53,54,79],[80,81,82,85,92,93],
    [97,100,101,102],[98,99],[104,105,109],[110,111,112,116,125],[122,123,126],[28,68]]


def main():
    visual=m.load(RUN/'visual-references-001.json');rows={r['number']:r for r in visual['rows']}
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
    dest=Path.home()/'Library/Application Support/Artline/research-proofs/zongolopoulos-20261010/comparisons'
    dest.mkdir(parents=True,exist_ok=True);sheets=[]
    for nums in GROUPS:
        cols=min(3,len(nums));nr=(len(nums)+cols-1)//cols
        im=Image.new('RGB',(cols*450,nr*480),'white');dr=ImageDraw.Draw(im)
        for i,n in enumerate(nums):
            r=rows[n];x=(i%cols)*450;y=(i//cols)*480
            dr.text((x+5,y+5),str(n)+' | '+r['source_id'].split('-')[-1],fill='black',font=font)
            with Image.open(r['path'])as raw:
                thumb=ImageOps.contain(raw.convert('RGB'),(430,430))
                im.paste(thumb,(x+(450-thumb.width)//2,y+35+(430-thumb.height)//2))
        path=dest/('compare-'+'-'.join(map(str,nums))+'.jpg');assert not path.exists();im.save(path,quality=94)
        sheets.append(dict(numbers=nums,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    m.save(RUN/'comparison-references-001.json',dict(at=m.now(),sheets=sheets,
        source_reference=q.s.ref(RUN/'visual-references-001.json'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Eleven internal comparison montages from the128 already selected unaltered thumbnails; no additional image retrieval. Source resolution remains bounded; do not infer casting identity from different photographs alone.'))
    print(json.dumps(dict(comparison_sheets=len(sheets))),flush=True)


if __name__=='__main__':main()
