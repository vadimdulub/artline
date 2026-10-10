#!/usr/bin/env python3
"""Read-only Yale University Art Gallery scope and bounded public collection discovery, without images."""
import importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m
IID='127cc862-91c7-5c9b-af5e-03bfdfe33859';RUN=m.RUN/'native/yale';BASE='https://lux.collections.yale.edu';n.SITES['yale']=BASE

def snapshot(db,ids):
    queries=dict(artworks='SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',artists='SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',media='SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',identifiers="SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",citations="SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",assertions='SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id')
    out={k:[r['row'] for r in db.execute(q,(ids,))] for k,q in queries.items()}
    out['museum']=db.execute('SELECT to_jsonb(x) row FROM institutions x WHERE id=%s',(IID,)).fetchone()['row'];return out

def main():
    RUN.mkdir(exist_ok=True)
    scope=RUN/'initial-scope-001.json.gz'
    if not scope.exists():
        with m.connect() as db:
            ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))]
            assert len(ids)<=1000
            snap=snapshot(db,ids)
            counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
            authorities=db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='institution' AND entity_id=%s ORDER BY id",(IID,)).fetchall()
        m.save(scope,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution_authorities=[r['row'] for r in authorities],read_only=True))
    x=m.load(scope);print(json.dumps(dict(scoped_records=len(x['scoped_ids']),counts=x['counts'],museum=x['snapshot']['museum'])),flush=True)

if __name__=='__main__':main()
