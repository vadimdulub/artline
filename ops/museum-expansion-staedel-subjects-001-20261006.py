#!/usr/bin/env python3
"""Read-only translated-subject and historical-inventory identity leads."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-staedel-20261006.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);m=s.m
TERMS=['Geograph','Géograph','Goethe','Lucca','Medici Madonna','Vierge Médicis','Pyramus','Pyrame','Crotta','Narciss','Narziss','Cossmann','Janauschek','Leerse','Radowitz','Bernus','Pallmann','Weizs','Harcourt','Brutal Interrogation','Inquisizione','Dispute with the Libertines','Bishop Julian','San Giuliano','Blinding','Vittore','Helen in Troy','Elena a Troia','Hélène à Troie','Christianity','Christentum','Holzhausen','Zirkuswagen','Circus Caravan','Fishbone Forest','Grätenwald','Dangerous Wish','Gefährlicher Wunsch','Gesetzgeber','Legislator','Köder','Decoy','Koloß','Koloss','Capuchin Cress','Nasturtium','capucines','Kapuziner','Russi','Dog Lying','Liegender Hund','Farmhouse in Nuenen','Bauernhaus in Nuenen','Dîner','Luncheon','Hus at Constance','Huss in Konstanz','Hosenträger','Horatius','Mucius','Latona','Latone','Heitere Landschaft','Cheerful Landscape','Kallmünz','Light-Green Mountains','Walter’s Toys','Walters Spielsachen','Lady Adventure','Frau Aventiure','Pinscher','Dachpfanne','Roof Tile','Großer Vorhang','Large Curtain','Grand blanc','White and Cage','Himmelsrichtung','Ostseedünen','Baltic Dunes']

def main():
    identity=m.load(s.RUN/'creator-identity-review-002.json');comparisons=m.load(s.RUN/'creator-title-comparison-leads-002.json')['records']
    allrows={r['id']:r for r in identity['artworks']+identity['unlinked_artworks']}
    terms=['%'+v+'%' for v in TERMS]
    with m.connect() as db:
        ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE title ILIKE ANY(%s) OR alternate_title ILIKE ANY(%s) ORDER BY id',(terms,terms))]
        rows=db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,
          a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.medium_text,a.dimensions_text,
          ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id''',(ids,)).fetchall()
        historical=db.execute('''SELECT id::text,title,accession_number,current_institution_id::text FROM artworks
          WHERE regexp_replace(lower(coalesce(accession_number,'')),'[^a-z0-9]','','g')=ANY(%s) ORDER BY id''',(['sg292','sg277'],)).fetchall()
        historical_identifiers=db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND regexp_replace(lower(external_id),'[^a-z0-9]','','g')=ANY(%s) ORDER BY entity_id",(['sg292','sg277'],)).fetchall()
    focused=[dict(source_record_id=c['source_record_id'],title=c['title'],pool_size=c['pool_size'],painting_or_unknown_rows=[allrows[oid] for oid in c['pool_ids'] if allrows[oid]['work_type'] in ['painting','unknown',None,'']]) for c in comparisons]
    dest=s.RUN/'subject-version-identity-leads-001.json';assert not dest.exists()
    m.save(dest,dict(at=m.now(),subject_search_terms=TERMS,subject_rows=rows,historical_inventories=historical,historical_identifiers=historical_identifiers,focused_painting_pools=focused,policy='Duplicate-search leads only. No creator identities or holdings changed. Full creator evidence retains prints and drawings separately.'))
    print('Städel subject leads',len(rows),'historical inventories',len(historical),len(historical_identifiers),'focused pools',len(focused),flush=True)

if __name__=='__main__':main()
