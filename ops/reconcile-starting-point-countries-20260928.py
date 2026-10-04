#!/usr/bin/env python3
"""Source-backed missing US cultural-affiliation links; no artwork-origin claims."""
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('expansion', Path(__file__).with_name('expand-starting-points-20260928.py'))
e = importlib.util.module_from_spec(s)
s.loader.exec_module(e)
c = e.c
selected = [
    ('wikiart-artist-edmonia-lewis', 'https://americanart.si.edu/artist/edmonia-lewis-2914', 'Smithsonian American Art Museum documents Lewis as an African American sculptor, her American origins and subsequent practice in Rome.'),
    ('wikiart-artist-augusta-savage', 'https://americanart.si.edu/artist/augusta-savage-4269', 'Smithsonian American Art Museum documents Savage as an African American sculptor and director of the Harlem Community Art Center.'),
    ('wikiart-artist-meta-vaux-warrick-fuller', 'https://nmaahc.si.edu/object/nmaahc_2013.242.1', 'Smithsonian National Museum of African American History and Culture identifies Fuller as American, 1877–1968.'),
]

def main():
    if (c.RUN / 'country-links-applied.json').exists():
        print('Country reconciliation already applied'); return
    recovery = c.load('backup.json')
    assert c.sha(Path(recovery['path']).read_bytes()) == recovery['sha256']
    captures = []
    for slug, url, note in selected:
        if 'nmaahc.si.edu' in url:
            path = c.RUN / 'captures/country-source-web.json'
            proof = c.json.loads(path.read_bytes())
            assert url in path.read_text() and 'American, 1877' in path.read_text()
            capture = {'url': url, 'at': proof['at'], 'sha256': c.sha(path.read_bytes()), 'path': str(path)}
        else:
            _, capture = c.fetch(url, c.RUN / 'captures' / (slug + '-country.html'))
        captures.append(capture)
    source = {'id': c.uid('source/country-reconciliation'), 'slug': c.CAMPAIGN+'-country-reconciliation', 'name': 'Smithsonian — reviewed American artist affiliations', 'base_url': 'https://www.si.edu/', 'source_type': 'collection_page'}
    with c.connect(False) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        artists = [db.execute('SELECT to_jsonb(a) record FROM artists a WHERE slug=%s FOR UPDATE', (slug,)).fetchone()['record'] for slug, _, _ in selected]
        for a in artists:
            assert not db.execute('SELECT 1 FROM artist_countries WHERE artist_id=%s', (a['id'],)).fetchone(), 'Country links changed after review'
        c.save(c.BACKUP / 'country-links-preimages.json', {'artists': artists, 'country_links': []})
        c.insert(db, 'sources', source)
        for a, (_, url, note), capture in zip(artists, selected, captures):
            c.insert(db, 'artist_countries', {'artist_id': a['id'], 'country_code': 'US', 'relationship_type': 'cultural_affiliation', 'is_primary': True, 'note': note+' Source: '+url+' This does not assert where individual works were made.'})
            c.insert(db, 'citations', {'id': c.uid('citation/us-affiliation/'+a['slug']), 'entity_type': 'artist', 'entity_id': a['id'], 'field_name': 'country.cultural_affiliation', 'source_id': source['id'], 'source_url': url, 'evidence_note': note+' Capture SHA-256: '+capture['sha256'], 'retrieved_at': capture['at'], 'created_by': c.ACTOR})
    c.save(c.RUN / 'country-links-applied.json', {'at': c.now(), 'artist_ids': [a['id'] for a in artists], 'sources': captures, 'source_id': source['id']})
    print('Added three documented US cultural-affiliation links')

if __name__ == '__main__':
    main()
