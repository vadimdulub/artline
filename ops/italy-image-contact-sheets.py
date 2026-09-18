#!/usr/bin/env python3
"""Create inspection sheets from prepared files; never approves images."""
import argparse
import hashlib
import json
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/italy-images-4h-20260916'

def main(label):
    run=RUN/label
    reviewed=json.loads((run/'visual-review.json').read_text())['images'] if (run/'visual-review.json').exists() else []
    done={(r['artwork_id'],r['sha256']) for r in reviewed}
    rows=[json.loads(p.read_text()) for p in sorted((run/'images').glob('*/*.json'))]
    rows=[r for r in rows if (r['artwork_id'],r['sha256']) not in done]
    digest=hashlib.sha256(json.dumps([(r['artwork_id'],r['sha256']) for r in rows]).encode()).hexdigest()[:12]
    out=run/'visual'/digest
    out.mkdir(parents=True,exist_ok=True)
    manifest=[]
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for start in range(0,len(rows),12):
        sheet=Image.new('RGB',(1320,1200),'#f4f1ea')
        draw=ImageDraw.Draw(sheet)
        for n,r in enumerate(rows[start:start+12]):
            idx=start+n+1;x=(n%4)*330;y=(n//4)*400
            with Image.open(ROOT/'apps/web/public'/r['path'].lstrip('/')) as im:
                im.thumbnail((310,278));sheet.paste(im,(x+(330-im.width)//2,y+5))
            caption=f"{idx}. {r['artist']} | {r['title']} | {r['institution_name']}"
            for j,line in enumerate(textwrap.wrap(caption,43)[:6]):
                draw.text((x+8,y+286+j*17),line,font=font,fill='black')
            manifest.append({k:r[k] for k in ('artwork_id','sha256','path','title','artist','institution_name')})
            manifest[-1].update(index=idx,sheet=f'contact-{start//12+1:02d}.jpg')
        path=out/f'contact-{start//12+1:02d}.jpg'
        if not path.exists():sheet.save(path,quality=92)
        print(path,flush=True)
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Prepared for inspection',len(rows),'images; no approval recorded',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();main(a.label)
