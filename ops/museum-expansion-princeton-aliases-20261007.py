#!/usr/bin/env python3
"""Supplement native mixed-script maker labels with their literal Latin components."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-princeton-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m
PATTERNS=['%sawada%','%tetsuro%','%tetsurō%','%ryosho%','%ryōshō%']
def query(db):
 artists=db.execute('SELECT id::text,display_name,normalized_name FROM artists WHERE normalized_name LIKE ANY(%s) OR display_name ILIKE ANY(%s) ORDER BY id',(PATTERNS,PATTERNS)).fetchall()
 aliases=db.execute('SELECT artist_id::text,alias,normalized_alias FROM artist_aliases WHERE normalized_alias LIKE ANY(%s) OR alias ILIKE ANY(%s) ORDER BY artist_id,alias',(PATTERNS,PATTERNS)).fetchall()
 ids=sorted({v['id'] for v in artists}|{v['artist_id'] for v in aliases});aids=[v['artwork_id'] for v in db.execute('SELECT DISTINCT artwork_id::text FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id',(ids,))]
 unlinked=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id',(PATTERNS,))];aids=sorted(set(aids+unlinked));assert len(aids)<2000
 arts=db.execute('SELECT '+i.i.ARTCOLS+' FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(aids,)).fetchall()
 return dict(artists=artists,aliases=aliases,artworks=arts)
def main():
 path=i.RUN/'latin-creator-aliases-001.json.gz';assert not path.exists()
 with m.connect() as db:state=query(db)
 m.save(path,dict(at=m.now(),query_reference=i.ref(Path(__file__).resolve()),patterns=PATTERNS,state=state,source_references=[i.ref(i.RUN/'objects-001'/('object-%03d.json.gz'%n)) for n in [35,163,169]],read_only=True,policy='Use Latin parts of literal native mixed-script maker labels for additional discovery. No invented aliases are written and no painter authorities linked.'))
 print(json.dumps(state,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
