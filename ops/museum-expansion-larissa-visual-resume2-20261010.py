"""Continue selected native image review, retaining missing files as explicit gaps."""
import collections
import importlib.util
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-larissa-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF=v.m,v.RUN,v.PROOF

def missing(src,rc,rp):
    return dict(number=src['number'],source_id=src['source_id'],source_url=src['source_url'],native_url=src['native_url'],role=src['role'],
        title=src['native_fields']['Τίτλος έργου'],creator=src['native_fields'].get('Καλλιτέχνης'),date=src['native_fields'].get('Χρονολογία έργου'),
        path=None,image_available=False,missing_native_receipt=v.ref(rp),status=rc['status'],rights_links=src['rights_links'],
        reason='Observed native image URL returned404; no path guessing. Row46 also had a non-image response from its observed aggregator thumbnail; no valid image retained.')

def main():
    m.save(RUN/'missing-native-image-continuation-002.json',dict(at=m.now(),number=46,prior_script=v.ref(m.ROOT/'ops/museum-expansion-larissa-visual-resume-20261010.py'),
        observation='Aggregator thumbnail request passed HTTP raise_for_status but failed the image/* content-type assertion. That response body and headers were not retained by the first continuation; no exact status/content-type claimed. No further thumbnail retry. Native404receipt is retained.',
        policy='Continue other selected native files. Missing individual404images remain unillustrated metadata leads. Stop on access denial, rate limit, server failure or network error.',script_reference=v.ref(Path(__file__).resolve())))
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];rows=[]
    for src in sources:
        n=src['number'];rp=RUN/'captures'/('native-image-'+str(n).zfill(3)+'-001.json')
        if rp.exists()and m.load(rp)['status']==404:row=missing(src,m.load(rp),rp)
        else:
            try:row=dict(v.fetch(src),image_available=True)
            except Exception:
                if not rp.exists()or m.load(rp)['status']!=404:raise
                row=missing(src,m.load(rp),rp)
        v.STOP.clear();rows.append(row)
        if len(rows)%40==0:print(json.dumps(dict(records=len(rows),images=sum(bool(x['path'])for x in rows),total=216)),flush=True)
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1400,1200),'white');draw=ImageDraw.Draw(canvas)
        for k,row in enumerate(batch):
            x,y=k%5*280,k//5*300;draw.text((x+4,y+4),str(row['number'])+' | '+(row['date']or'Unknown')+(' | OLD'if row['role']=='existing_comparator'else''),font=font,fill='black')
            draw.text((x+4,y+24),row['title'][:35],font=small,fill='black');draw.text((x+4,y+41),(row['creator']or'Unknown')[:37],font=small,fill='black')
            if row['path']:
                with Image.open(row['path'])as im:
                    thumb=ImageOps.contain(im.convert('RGB'),(272,238));canvas.paste(thumb,(x+(280-thumb.width)//2,y+58+(238-thumb.height)//2))
            else:draw.text((x+15,y+140),'SOURCE IMAGE MISSING',font=font,fill='gray')
        p=PROOF/('contact-'+str(page)+'.jpg');assert not p.exists();canvas.save(p,quality=94);sheets.append(dict(v.ref(p),numbers=[row['number']for row in batch]))
    groups=collections.defaultdict(list)
    for row in rows:
        if row['path']:groups[row['sha256']].append(row['number'])
    m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=rows,sheets=sheets,exact_duplicate_images=[ns for ns in groups.values()if len(ns)>1],missing_images=[row['number']for row in rows if not row['path']],
        source_reference=v.ref(RUN/'selected-source-records-001.json.gz'),selection_reference=v.ref(RUN/'object-selection-001.json'),script_reference=v.ref(Path(__file__).resolve()),
        original_script_reference=v.ref(Path(v.__file__).resolve()),policy='Selected full native repository frames only. Missing native files retain404evidence and are not retried or replaced by guessed URLs. All contacts are internal review, not catalogue placeholders. No claim of completed visual review until separate decisions.'))
    print(json.dumps(dict(records=len(rows),images=sum(bool(row['path'])for row in rows),missing=[row['number']for row in rows if not row['path']],contacts=len(sheets),exact_duplicates=[ns for ns in groups.values()if len(ns)>1])),flush=True)

if __name__=='__main__':main()
