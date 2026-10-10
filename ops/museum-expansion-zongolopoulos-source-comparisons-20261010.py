"""Selected unresolved Greek-title source images; research comparison only."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN;PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/zongolopoulos-delivery-20261010'

def main():
    assert not(RUN/'additional-comparisons-001.json').exists();focus=m.load(RUN/'focused-comparators-001.json.gz');snap=focus['snapshot'];rows=[v for root in [c.RESEARCH,c.DATED]for v in m.load(root/'editorial-source-decisions-001.json.gz')['rows']];titles={m.norm(v['title'])for v in rows};frames=[];missing=[]
    for a in snap['artworks']:
        if a['primary_media_id']or a['current_institution_id']==c.IID or a['normalized_title']not in titles:continue
        matches=[]
        for cite in snap['citations']:
            if cite['entity_id']!=a['id']or not cite['source_url'].startswith('https://www.searchculture.gr/'):continue
            try:e=json.loads(cite['evidence_note'])
            except (ValueError,TypeError):continue
            f=e.get('facts',{});raw=f.get('raw',{});url=raw.get('thumbnail')or raw.get('index',{}).get('image_url')
            if url:matches.append((cite,url))
        if not matches:missing.append(dict(id=a['id'],title=a['title'],reason='No directly recorded source thumbnail in existing citations.'));continue
        cite,url=matches[0];assert url.startswith('https://www.searchculture.gr/aggregator/thumbnails/');rc=RUN/'additional-image-receipts'/(a['id']+'.json')
        if rc.exists():v=m.load(rc)
        else:
            response=requests.get(url,timeout=(15,40));response.raise_for_status();data=response.content;im=Image.open(io.BytesIO(data));im.load();p=PROOF/'additional-comparison-images'/(a['id']+'.jpg');p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(data)
            v=dict(at=m.now(),artwork_id=a['id'],title=a['title'],creator_label=a['unlinked_creator_label'],url=url,final_url=response.url,status=response.status_code,path=str(p),sha256=hashlib.sha256(data).hexdigest(),width=im.width,height=im.height,source_page_url=cite['source_url'],source_citation_id=cite['id'],purpose='Bounded identity comparison only; unknown dates not cleared for public image attachment.');m.save(rc,v)
        frames.append(v)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14);canvas=Image.new('RGB',(1440,((len(frames)+3)//4)*360),'#eeeae3');draw=ImageDraw.Draw(canvas)
    for j,v in enumerate(frames):
        im=Image.open(v['path']);im.thumbnail((340,300));x=j%4*360+(360-im.width)//2;y=j//4*360;canvas.paste(im,(x,y));draw.text((j%4*360+8,y+304),v['artwork_id'][:8]+' | '+v['title'][:30],fill='black',font=font);draw.text((j%4*360+8,y+329),(v['creator_label']or'Anonymous')[:40],fill='black',font=font)
    p=PROOF/'additional-comparison-contact.jpg';canvas.save(p,quality=92)
    m.save(RUN/'additional-comparisons-001.json',dict(at=m.now(),frames=frames,missing=missing,contact=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()),comparison_reference=c.ref(RUN/'focused-comparators-001.json.gz'),script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(comparison_images=len(frames),missing=len(missing))),flush=True)
if __name__=='__main__':main()
