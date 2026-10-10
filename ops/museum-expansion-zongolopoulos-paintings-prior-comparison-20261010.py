"""Compare previously reviewed pictorial works with the current selected batch."""
import importlib.util
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-comparisons-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    prior=m.load(c.v.t.OLD/'visual-references-001.json')['rows']
    numbers={1,3,13,16,17,19,20,65,66,67,103,127,128}
    rows=[dict(r,label='Previous '+str(r['number']))for r in prior if r['number']in numbers]
    current=m.load(RUN/'visual-references-001.json')['rows']
    rows.extend(dict(r,label='Current '+str(r['number']))for r in current if r['number']==97)
    assert len(rows)==14
    canvas=Image.new('RGB',(1600,1480),'white');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
    for i,r in enumerate(rows):
        x,y=(i%4)*400,(i//4)*370
        draw.text((x+5,y+5),r['label']+' | '+r['source_id'].rsplit('-',1)[1],font=font,fill='black')
        with Image.open(r['path'])as im:
            thumb=ImageOps.contain(im.convert('RGB'),(390,325));canvas.paste(thumb,(x+(400-thumb.width)//2,y+35+(325-thumb.height)//2))
    path=PROOF/'focused-review/prior-pictorial-works.jpg';assert not path.exists();canvas.save(path,quality=94)
    m.save(RUN/'prior-pictorial-comparison-001.json',dict(at=m.now(),sheet=c.ref(path),rows=rows,
        previous_visual_reference=c.ref(c.v.t.OLD/'visual-references-001.json'),current_visual_reference=c.ref(RUN/'visual-references-001.json'),
        script_reference=c.ref(Path(__file__).resolve()),policy='Internal full-thumbnail comparisons only. Earlier architectural sheets and sculpture photographs are already structurally distinct from this selected painting category. No claim of current production identity clearance.'))

if __name__=='__main__':main()
