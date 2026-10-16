#!/usr/bin/env python3
"""Incremental visual sheets for source qualifications, without approving them."""
import importlib.util
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('review','ops/wikiart-500-painters-review-20261011.py')
x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x)
r=x.r;RUN=x.RUN

def main():
    x.quality_progress();x.components()
    quality=r.load(RUN/'progress/quality-candidates.json')
    flags={v['artwork_id']:v for k in ['lifespan_or_qualified_creator','title_review_candidates','architectural_version_candidates']for v in quality[k]}
    flags.update({v['artwork_id']:v for v in r.load(RUN/'progress/component-candidates.json')['rows']})
    # Sampling revealed mixed book pages and interface overlays for these artists.
    # Review every prepared reproduction in these two source groups.
    for data,pin in x.d.plans():
        if data['artist']['display_name'] not in ['Ivan Bilibin','Mariam Aslamazian']:continue
        for row in data['rows']:
            if row['action'] not in ['create','existing']:continue
            flags.setdefault(row['artwork_id'],dict(artist=data['artist']['display_name'],artwork_id=row['artwork_id'],title=row['title'],source_url=row['source_url'],date=row['page'].get('date'),source_fields=row['page']['fields']))
    indexed={v['artwork_id']for p in(RUN/'quality-visual-batches').glob('*.json')for v in r.load(p)['images']}
    items=[]
    for aid,flag in flags.items():
        path=RUN/'prepared-images'/(aid+'.json')
        if aid in indexed or not path.exists():continue
        im=r.load(path)
        if im['outcome']=='prepared':items.append((flag,im))
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    number=len(list((RUN/'quality-visual-batches').glob('*.json')))
    for start in range(0,len(items),24):
        group=items[start:start+24];canvas=Image.new('RGB',(1680,360*((len(group)+5)//6)),'#eee');draw=ImageDraw.Draw(canvas)
        for i,(flag,im)in enumerate(group):
            col=i%6*280;top=i//6*360
            with Image.open(im['visual_path'])as picture:
                picture.thumbnail((270,280));canvas.paste(picture,(col+(280-picture.width)//2,top+(280-picture.height)//2))
            date=(flag.get('date')or{}).get('date_display')or flag.get('source_fields',{}).get('Date','Unknown date')
            for j,label in enumerate([str(i+1)+'. '+flag['artist'][:29],flag['title'][:37],str(date)[:36]]):draw.text((col+4,top+287+20*j),label,fill='black',font=font)
        path=x.d.ORIGINALS/'quality-contact-sheets'/f'{number:03d}.jpg';path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,quality=93)
        r.save(RUN/'quality-visual-batches'/f'{number:03d}.json',dict(at=r.now(),path=str(path),sha256=r.sha(path.read_bytes()),images=[dict(artwork_id=im['artwork_id'],artist=flag['artist'],title=flag['title'],sha256=im['sha256'],source_url=flag['source_url'])for flag,im in group]))
        print('Quality sheet',number,len(group),'images',str(path),flush=True);number+=1
def duplicates():
    byid={row['artwork_id']:row for data,pin in x.d.plans()for row in data['rows']if row['action']in['create','existing']}
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    for audit in (RUN/'image-audits').glob('*.json'):
        for group in r.load(audit)['duplicate_groups']:
            key=r.sha('|'.join(sorted(group['ids'])).encode())[:20];dest=RUN/'duplicate-visual-batches'/(key+'.json')
            if dest.exists():continue
            canvas=Image.new('RGB',(1200,760),'#eee');draw=ImageDraw.Draw(canvas);items=[]
            for j,aid in enumerate(group['ids']):
                row=byid[aid];im=r.load(RUN/'prepared-images'/(aid+'.json'))
                with Image.open(im['visual_path'])as picture:
                    picture.thumbnail((580,590));canvas.paste(picture,(j*600+(600-picture.width)//2,(590-picture.height)//2))
                labels=[str(j+1)+'. '+row['title'][:58],str(row['page']['date']),str(row['page']['fields'].get('Location',''))[:70],row['action']+' '+aid]
                for k,label in enumerate(labels):draw.text((j*600+5,600+k*30),label,font=font,fill='black')
                items.append(dict(artwork_id=aid,title=row['title'],action=row['action'],source_url=row['source_url'],date=row['page']['date'],source_fields=row['page']['fields'],sha256=im['sha256']))
            path=x.d.ORIGINALS/'duplicate-contact-sheets'/(key+'.jpg');path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,quality=93)
            r.save(dest,dict(at=r.now(),path=str(path),sha256=r.sha(path.read_bytes()),group=group,images=items))
            print('Duplicate pair',key,[(v['title'],v['date'])for v in items],flush=True)
if __name__=='__main__':duplicates()if len(sys.argv)>1 and sys.argv[1]=='duplicates'else main()
