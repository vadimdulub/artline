#!/usr/bin/env python3
"""Preserve read-only subject/version leads for Auckland's selected objects."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('u',Path(__file__).with_name('museum-expansion-auckland-20261006.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
m=u.m
TERMS=['Lavington','Eclipse','Straton','Antioch','Wakatipu','Earnslaw','Wharekauri','Tahuna','Kapekape','Ahinata',
 'Tarapata','Harata','Heeni','Hirini','Heta Te','Haora','Koinaki','Ropiha','Mamaku','Taiaroa','Anaua','Anaūa',
 'Hautākiri','Wharepapa','Karaitiana','Te Rango','Keeta','Kani','Anehana','Tamaikōhā','Te Ata','Hāmiora','Hamiora',
 'Knucklebones','Koruru','Hairnet','résille','resille','Bleached Objects','Laurel','Bridesmaid','Lancashire Family',
 'Masoch','La tasse','Pistons','Lamia','Coming Storm','Last Voyage','Hundred Years Have Passed']


def main():
    research=m.load(u.RUN/'auckland-001-research.json.gz')
    identity=m.load(u.RUN/'creator-identity-review-001.json')
    extra=m.load(u.RUN/'supplemental-creator-artworks-001.json')
    comparison=m.load(u.RUN/'creator-title-comparison-leads-001.json')['records']
    all_rows={r['id']:r for r in identity['artworks']+identity['unlinked_artworks']+extra['artworks']+extra['unlinked_artworks']}
    terms=['%'+v+'%' for v in TERMS]
    with m.connect() as db:
        ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE title ILIKE ANY(%s) OR alternate_title ILIKE ANY(%s) ORDER BY id',(terms,terms)).fetchall()]
        rows=db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,
          a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.dimensions_text,
          ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id''',(ids,)).fetchall()
    focused=[]
    for c in comparison:
        if c['source_record_id'] not in ['15692','16129','14898','16130','16124','5754','1703','2701','3120','9173','11062','9722']:continue
        pool=[all_rows[oid] for oid in c['pool_ids']]
        # All known paintings and unclassified records retained; drawings/prints
        # remain available in the complete creator-scoped evidence.
        paintings=[r for r in pool if r['work_type'] in ['painting',None,'unknown','']]
        focused.append(dict(source_record_id=c['source_record_id'],title=c['title'],pool_size=len(pool),painting_or_unknown_rows=paintings))
    result=dict(at=m.now(),subject_search_terms=TERMS,subject_rows=rows,focused_painting_pools=focused,
        policy='Broad titles and creator-scoped versions are editorial leads only. Native object identities and source evidence determine decisions; no creator links or holdings inferred by title similarity.')
    m.save(u.RUN/'subject-version-identity-leads-001.json',result)
    print('Preserved',len(rows),'subject leads and',len(focused),'focused painting pools',flush=True)


if __name__=='__main__':main()
