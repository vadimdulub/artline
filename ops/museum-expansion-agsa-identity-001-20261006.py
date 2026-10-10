#!/usr/bin/env python3
"""Read-only creator-scoped duplicate leads for the first AGSA selection."""
import importlib.util
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('agsa',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
m=i.m


def main():
    research=m.load(i.RUN/'agsa-001-research.json.gz')
    names=sorted({v for r in research['records'] for v in r['raw_source_record']['native_fields']['creator_names']})
    native_names=list(names)
    # Qualifications remain on artworks; stripped forms only widen duplicate leads.
    variants=[re.sub(r' and studio$','',re.sub(r'^(?:attributed to|after|studio of|workshop of|circle of|Sir)\s+','',v,flags=re.I),flags=re.I) for v in names]
    names=sorted(set(names+variants+['Peter Graham','William Charles Piguenit','Charles Douglas Richardson','Emanuel Phillips Fox','Henry James Johnstone','1835-1907, Henry James Johnstone','Cornelis de Vos','Hans Herrmann','Spencer Gore']))
    keys=[m.norm(v) for v in names]
    with m.connect() as db:
        artists=db.execute('''SELECT id::text,display_name,normalized_name,sort_name,slug FROM artists
          WHERE normalized_name=ANY(%s) OR lower(display_name)=ANY(%s) ORDER BY id''',(keys,[s.lower() for s in names])).fetchall()
        aliases=db.execute('''SELECT aa.artist_id::text,aa.alias,aa.normalized_alias,a.display_name
          FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s)
          ORDER BY aa.artist_id,aa.alias''',(keys,)).fetchall()
        ids=sorted({r['id'] for r in artists}|{r['artist_id'] for r in aliases})
        rows=db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,
          a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.dimensions_text,
          ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) s
          JOIN artworks a ON a.id=s.artwork_id ORDER BY a.id''',(ids,)).fetchall()
        patterns=['%'+v+'%' for v in names if not any(w in v.lower() for w in ['unknown','century']) and v not in ['China','Japan','Myanmar (Burma)']]
        unlinked=db.execute('''SELECT id::text,title,alternate_title,creation_year_start,creation_year_end,date_display,
          accession_number,unlinked_creator_label,current_institution_id::text,work_type,dimensions_text,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM artworks a WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id''',(patterns,)).fetchall()
        collisions=i.title_collisions(db,research['records'])
    m.save(i.RUN/'creator-identity-review-001.json',dict(at=m.now(),names=names,native_names=native_names,artists=artists,aliases=aliases,artworks=rows,
        unlinked_artworks=unlinked,title_collisions=collisions,policy='Creator names and aliases are duplicate-search leads only; no identity or artist link is inferred.'))
    print('Creator review:',len(artists),'artists,',len(aliases),'aliases,',len(rows),'linked artwork rows,',len(unlinked),'unlinked labels,',len(collisions),'title collisions',flush=True)


if __name__=='__main__':main()
