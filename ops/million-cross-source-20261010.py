#!/usr/bin/env python3
"""Find unresolved cross-source identities, including records without holdings."""
import collections,importlib.util,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m
def find_candidates(db,rows):
    titles=sorted({r['normalized_title'] for r in rows});existing=[]
    for ts in m.chunks(titles,600):
        existing+=db.execute("SELECT id::text,title,normalized_title,work_type,creation_year_start,creation_year_end,accession_number,primary_media_id::text FROM artworks WHERE status<>'archived' AND current_institution_id IS NULL AND normalized_title=ANY(%s)",(ts,)).fetchall()
    ids=[r['id'] for r in existing];creators=collections.defaultdict(list);media={}
    for batch in m.chunks(ids,600):
        for x in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(batch,)):creators[x['artwork_id']].append(x)
    mids=[r['primary_media_id'] for r in existing if r['primary_media_id']]
    for batch in m.chunks(mids,600):
        for im in db.execute('SELECT id::text,storage_path,checksum_sha256 FROM media_assets WHERE id=ANY(%s::uuid[])',(batch,)):media[im['id']]=im
    bytitle=collections.defaultdict(list)
    for e in existing:e.update(creators=creators[e['id']],media=media.get(e['primary_media_id']));bytitle[e['normalized_title']].append(e)
    result=[]
    for r in rows:
        artistids={c['artist_id'] for c in r['links']};label=m.norm(r['creator_label'])
        for e in bytitle[r['normalized_title']]:
            if e['id']==r['artwork_id']:continue
            samecreator=any(c['artist_id'] in artistids or len(m.norm(c['display_name']))>=8 and m.norm(c['display_name']) in label for c in e['creators'])
            if not samecreator:continue
            # A candidate is a hold, never an automatic merge. Copies, cast dates,
            # distinct impressions and artist-after relations remain possible.
            result.append(dict(new_id=r['artwork_id'],native_id=r['native_id'],title=r['title'],creator_label=r['creator_label'],native_work_type=r['work_type'],native_date=r['date_display'],native_accession=r['accession_number'],existing=e))
    return result
def scan():
    p=m.load(n.RUN/n.PLAN)
    with m.m.connect() as db:rows=find_candidates(db,p['new_artworks'])
    hashes={}
    for r in rows:
        e=r['existing'];im=e.get('media')
        if im and im.get('storage_path'):
            path=m.ROOT/'apps/web/public'/im['storage_path'].lstrip('/')
            if path.exists():
                try:
                    with Image.open(path) as opened:hashes[e['id']]=dict(dhash=m.m.imagehash(opened),aspect=opened.width/opened.height,path=str(path))
                except Exception:pass
        prep=n.RUN/'images-001/prepared'/(r['new_id']+'.json')
        if prep.exists() and e['id'] in hashes:
            data=m.load(prep)
            if data['state']=='prepared':
                with Image.open(data['path']) as opened:
                    h=m.m.imagehash(opened);r['visual_comparison']=dict(hamming_distance=(int(h,16)^int(hashes[e['id']]['dhash'],16)).bit_count(),aspect_difference=abs((opened.width/opened.height)/hashes[e['id']]['aspect']-1),new_path=data['path'],existing_path=hashes[e['id']]['path'])
    m.save(n.RUN/'cross-source-candidates.json.gz',dict(at=m.now(),rows=rows,scope='Same-title and creator candidates among active records missing museum links. No automated merge from names, dates or perceptual hash alone.'))
    print('Cross-source candidates',len(rows),'new objects',len({r['new_id'] for r in rows}),'prepared comparisons',sum('visual_comparison' in r for r in rows),flush=True)
    print(json.dumps([dict(new_id=r['new_id'],old_id=r['existing']['id'],title=r['title'],comparison=r['visual_comparison']) for r in rows if 'visual_comparison' in r],ensure_ascii=False),flush=True)
if __name__=='__main__':scan()
