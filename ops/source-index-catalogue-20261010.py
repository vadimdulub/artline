#!/usr/bin/env python3
"""Source-index artwork delivery: immutable discovery and production-only additions."""
import argparse
from collections import Counter,defaultdict
import importlib.util,json,re,hashlib,gzip
from pathlib import Path
from urllib.parse import urlsplit,unquote

spec=importlib.util.spec_from_file_location('source_index',Path(__file__).with_name('source-index-20261009.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ROOT=m.ROOT;PREVIOUS=m.RUN;OP='source-index-delivery-20261010';RUN=ROOT/'docs/research'/OP
save=m.save;load=m.load;now=m.now


def resources():return [json.loads(x) for x in (PREVIOUS/'sources.jsonl').read_text().splitlines()]


def inventory():
    assert not (RUN/'inventory.json.gz').exists(),'Preserve pinned initial inventory'
    sources=resources();ids=sorted({b['entity_id'] for s in sources for b in s['artline_bindings'] if b['entity_type']=='artwork'})
    artist_ids=sorted({b['entity_id'] for s in sources for b in s['artline_bindings'] if b['entity_type']=='artist'})
    works=[];identifiers=[];citations=[];creators=[];artists=[];artist_identifiers=[]
    with m.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for offset in range(0,len(ids),500):
            batch=ids[offset:offset+500]
            works.extend(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(batch,)).fetchall())
            identifiers.extend(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id",(batch,)).fetchall())
            citations.extend(db.execute("SELECT * FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(batch,)).fetchall())
            creators.extend(db.execute('SELECT aa.*,a.display_name,a.slug artist_slug FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(batch,)).fetchall())
            print('Current indexed artworks',min(offset+500,len(ids)),'/',len(ids),flush=True)
        all_artist_ids=sorted(set(artist_ids)|{str(c['artist_id']) for c in creators})
        for offset in range(0,len(all_artist_ids),1000):
            batch=all_artist_ids[offset:offset+1000]
            artists.extend(db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id',(batch,)).fetchall())
            artist_identifiers.extend(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id",(batch,)).fetchall())
        institutions=db.execute("SELECT * FROM institutions WHERE status<>'archived' ORDER BY id").fetchall()
        db_sources=db.execute('SELECT * FROM sources ORDER BY id').fetchall()
    out=dict(at=now(),production_read_only=True,index_path=str(PREVIOUS/'sources.jsonl'),index_sha256=m.sha(PREVIOUS/'sources.jsonl'),artworks=works,identifiers=identifiers,citations=citations,creators=creators,artists=artists,artist_identifiers=artist_identifiers,institutions=institutions,sources=db_sources)
    out=json.loads(json.dumps(out,default=str));works=out['artworks'];institutions=out['institutions']
    save(RUN/'inventory.json.gz',out)
    ws={w['id']:w for w in works};ledger=[]
    for s in sources:
        bindings=[b['entity_id'] for b in s['artline_bindings'] if b['entity_type']=='artwork'];current=[ws[b] for b in bindings if b in ws]
        kind=s['kind'];reason='reference_or_discovery_entrypoint'
        if current:reason='existing_artwork_missing_image' if any(not w['primary_media_id'] and w['status']!='archived' for w in current) else 'existing_artwork_image_present_or_archived'
        elif kind in ('museum_or_collection_object','object_or_artist_reference'):reason='object_url_or_artist_reference_needs_resolution'
        ledger.append(dict(source_index_id=s['id'],url=s['url'],provider_id=s['provider_id'],kind=kind,artwork_ids=bindings,state=reason))
    save(RUN/'full-index-ledger.json.gz',ledger)
    inst={i['id']:i for i in institutions};missing=[w for w in works if not w['primary_media_id'] and w['status']!='archived']
    summary=dict(at=now(),source_urls=len(sources),index_sha256=out['index_sha256'],indexed_artwork_ids=len(ids),existing_artworks=len(works),missing_artwork_ids=sorted(set(ids)-set(ws)),active_existing_artworks=sum(w['status']!='archived' for w in works),existing_images=sum(bool(w['primary_media_id']) for w in works),missing_primary_images=len(missing),missing_images_by_institution=dict(Counter(inst.get(w['current_institution_id'],{}).get('name','Unlinked institution') for w in missing).most_common()),ledger_states=dict(Counter(x['state'] for x in ledger)))
    save(RUN/'inventory-summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['inventory']);args=p.parse_args();inventory()
