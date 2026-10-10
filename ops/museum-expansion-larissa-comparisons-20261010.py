"""Bounded offline image comparisons; no source downloads or database access."""
import importlib.util
import itertools
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-larissa-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF,ref=v.m,v.RUN,v.PROOF,v.ref
GROUPS=[('Repeated titles: distinct physical works',[118,119,109,187,155,159]),
    ('Georgiadis copies and print/version checks',[70,90,91,27,42,99]),
    ('Kanas album: twelve plate views, one aggregate',[176,177,178,179,180,181,182,183,184,185,186,188]),
    ('Date conflicts and unresolved creator',[51,54,102,193,32,168])]

def dhash(path):
    with Image.open(path)as im:
        im=im.convert('L').resize((17,16));px=list(im.getdata())
    value=0
    for y in range(16):
        for x in range(16):value=(value<<1)|(px[y*17+x]>px[y*17+x+1])
    return value

def main():
    visual=m.load(RUN/'visual-references-001.json');frames={r['number']:r for r in visual['rows']}
    facts={r['number']:r for r in m.load(RUN/'candidate-facts-001.json.gz')['rows']};sheets=[]
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    for page,(label,numbers)in enumerate(GROUPS,1):
        columns=3;cellw,cellh=430,460
        canvas=Image.new('RGB',(columns*cellw,((len(numbers)+columns-1)//columns)*cellh+40),'white');draw=ImageDraw.Draw(canvas)
        draw.text((8,8),label,font=font,fill='black')
        for k,n in enumerate(numbers):
            f=facts[n];x=k%columns*cellw;y=k//columns*cellh+40
            draw.text((x+5,y+3),str(n)+' | '+f['title'][:43],font=font,fill='black')
            draw.text((x+5,y+25),(f['native_date_literal']or'Unknown')+' | '+(f['dimensions_text']or'No dimensions'),font=font,fill='black')
            with Image.open(frames[n]['path'])as im:
                thumb=ImageOps.contain(im.convert('RGB'),(cellw-12,cellh-60));canvas.paste(thumb,(x+(cellw-thumb.width)//2,y+55+(cellh-60-thumb.height)//2))
        p=PROOF/('focused-'+str(page)+'.jpg');assert not p.exists();canvas.save(p,quality=94)
        sheets.append(dict(ref(p),label=label,numbers=numbers))
    hashes={n:dhash(f['path'])for n,f in frames.items()if f['path']}
    nearest=sorted((dict(a=a,b=b,distance=(hashes[a]^hashes[b]).bit_count())for a,b in itertools.combinations(hashes,2)),key=lambda r:r['distance'])[:12]
    m.save(RUN/'comparison-references-001.json',dict(at=m.now(),sheets=sheets,nearest_dhash_pairs=nearest,
        hash_limit='256-bit difference hash is a bounded triage aid, not identity evidence; nearest pairs require visual review.',
        visual_review_complete=False,source_reference=ref(RUN/'visual-references-001.json'),script_reference=ref(Path(__file__).resolve())))
    print(dict(sheets=len(sheets),nearest=nearest))

if __name__=='__main__':main()
