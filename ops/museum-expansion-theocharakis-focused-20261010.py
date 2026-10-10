"""Preserve and inspect relevant Papaloukas and unresolved-title comparator records."""
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-theocharakis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN;PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/theocharakis-delivery-20261010'

def main():
    assert not(RUN/'focused-review-inputs-001.json').exists()
    obs=m.load(RUN/'production-identity-001.json.gz');s=obs['state'];linked={v['artwork_id'] for v in s['creator_links']};painter={v['artwork_id']for v in s['creator_links']if v['artist_id']in s['artist_ids']}
    uncertain={v['id']for v in s['artworks']if v['id']not in linked and (not v['unlinked_creator_label'] or re.search('unknown|anonymous|unidentified|inconnu|unbekannt',v['unlinked_creator_label'],re.I)) and (v['creation_year_end']is None or v['creation_year_end']>=1892)and(v['creation_year_start']is None or v['creation_year_start']<=1957)}
    ids=sorted(painter|uncertain|set(s['scoped_ids']));assert len(ids)==65
    dest=RUN/'focused-comparators-001.json.gz'
    if dest.exists():focus=m.load(dest)
    else:
        with c.prod.connect() as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids)
            artist=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id',(s['artist_ids'],)).fetchall()
            aliases=db.execute('SELECT to_jsonb(a) row FROM artist_aliases a WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,alias',(s['artist_ids'],)).fetchall()
            identifiers=db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme",(s['artist_ids'],)).fetchall()
        focus=dict(at=m.now(),ids=ids,snapshot=snap,artist_rows=[v['row']for v in artist],artist_aliases=[v['row']for v in aliases],artist_identifiers=[v['row']for v in identifiers],painter_artwork_ids=sorted(painter),unresolved_creator_comparators=sorted(uncertain),read_only=True);m.save(dest,focus)
    snap=focus['snapshot'];media={v['id']:v for v in snap['media_assets']};frames=[]
    for a in snap['artworks']:
        if a['id']not in painter or a['id']in s['scoped_ids']or not a['primary_media_id']:continue
        mr=media[a['primary_media_id']];path=mr['storage_path'];url='https://artlines.org'+path if path.startswith('/')else path;assert url.startswith('https://artlines.org/')
        receipt=RUN/'comparison-image-receipts'/(a['id']+'.json')
        if receipt.exists():v=m.load(receipt)
        else:
            response=requests.get(url,timeout=(15,40));response.raise_for_status();data=response.content;checksum=hashlib.sha256(data).hexdigest();assert checksum==mr['checksum_sha256'];im=Image.open(io.BytesIO(data));im.load();p=PROOF/'comparison-images'/(a['id']+'.jpg');p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(data)
            v=dict(at=m.now(),artwork_id=a['id'],title=a['title'],url=url,status=response.status_code,path=str(p),sha256=checksum,width=im.width,height=im.height,source_page_url=mr['source_page_url']);m.save(receipt,v)
        frames.append(v)
    assert len(frames)==18
    canvas=Image.new('RGB',(1440,1800),'#eeeae3');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    for j,v in enumerate(frames):
        im=Image.open(v['path']);im.thumbnail((340,320));x=j%4*360+(360-im.width)//2;y=j//4*360;canvas.paste(im,(x,y));draw.text((j%4*360+8,y+323),v['artwork_id'][:8]+' | '+v['title'][:33],fill='black',font=font)
    p=PROOF/'existing-papaloukas-contact.jpg';canvas.save(p,quality=91)
    m.save(RUN/'focused-review-inputs-001.json',dict(at=m.now(),frames=frames,contact=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()),snapshot_reference=c.ref(dest),source_citations_reference=c.ref(RUN/'production-identity-citations-001.json.gz'),policy='65 records protected;18 existing Papaloukas primary images examined as comparison references, not new attachments. Unknown source dates remain unchanged. Age bounds only broaden identity research, never assign artwork creation dates.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(snapshot=65,comparison_images=18,artist_rows=len(focus['artist_rows']))),flush=True)
if __name__=='__main__':main()
