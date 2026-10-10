#!/usr/bin/env python3
"""Read-only variant-name and subject leads for Auckland object reconciliation."""
import difflib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('u',Path(__file__).with_name('museum-expansion-auckland-20261006.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
m=u.m
VARIANTS={
 'Charles F Goldie':['Charles Frederick Goldie'], 'William A Sutton':['William Alexander Sutton'],
 'Birket Foster':['Myles Birket Foster'], 'Ernest W Christmas':['Ernest William Christmas'],
 'Henry La Thangue':['Henry Herbert La Thangue'], 'Walter Sickert':['Walter Richard Sickert'],
 "Melchior d' Hondecoeter":['Melchior de Hondecoeter'], 'John Chalon':['John James Chalon'],
 "Alfred O'Keeffe":["Alfred Henry O'Keeffe"], 'H Linley Richardson':['Henry Linley Richardson'],
 'Archibald Nicoll':['Archibald Frank Nicoll'], 'Felice Ficherelli':['Francesco Furini'],
 'Alfred Munnings':['Alfred James Munnings'], 'John Alfred Arnesby Brown':['Sir Arnesby Brown','John Arnesby Brown'],
 'James Nairn':['James McLachlan Nairn'], 'Edouard Frere':['Édouard Frère','Pierre Edouard Frère'],
 'Edward Payton':['Edward William Payton'], 'Edward Cooke':['Edward William Cooke'],
 'Jan Boeckhorst':['Jan Philipsz van Boeckhorst'], 'Jan Mytens':['Johannes Mytens'],
 'Pat Hanly':['Patrick Hanly'], 'A Lois White':['Anna Lois White'], 'James Pyne':['James Baker Pyne'],
 'Frank Salisbury':['Francis Owen Salisbury','Frank O. Salisbury'],
 'Andrea Michieli (known as Andrea Vicentino)':['Andrea Vicentino','Andrea Michieli'],
 'John Waterhouse':['John William Waterhouse'], 'Eugène von Guérard':['Eugen von Guérard','Eugene von Guerard'],
 'Paul Cezanne':['Paul Cézanne'], 'Alexander Roche':['Alexander Ignatius Roche'],
 'Carlo Ceresa':['Ceresa Carlo'], 'Charles Blomfield':['Charles James Blomfield'],
 'May Smith':['May Aimée Smith'], 'Andrew Carrick Gow':['Andrew Gow'],
 'Charles Leslie':['Charles Robert Leslie'], 'John Nost Sartorius':['John Francis Sartorius'],
}


def main():
    research=m.load(u.RUN/'auckland-001-research.json.gz');identity=m.load(u.RUN/'creator-identity-review-001.json')
    surnames=m.load(u.RUN/'additional-creator-name-leads-001.json')
    relevant={m.norm(v) for vs in VARIANTS.values() for v in vs}
    extra_artists=[a for a in surnames['artists'] if m.norm(a['display_name']) in relevant]
    already={a['id'] for a in identity['artists']}|{a['artist_id'] for a in identity['aliases']}
    ids=sorted({a['id'] for a in extra_artists}-already)
    with m.connect() as db:
        rows=db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,
          a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.dimensions_text,
          ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) s JOIN artworks a ON a.id=s.artwork_id ORDER BY a.id''',(ids,)).fetchall()
        terms=['%Goldie%','%Lindauer%','%Nerli%','%Blomfield%','%La Thangue%','%Roche%','%Payton%','%Guerard%','%Guérard%','%Sartorius%']
        labels=db.execute('''SELECT id::text,title,alternate_title,creation_year_start,creation_year_end,date_display,accession_number,unlinked_creator_label,
          current_institution_id::text,work_type,dimensions_text,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM artworks a WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id''',(terms,)).fetchall()
    m.save(u.RUN/'supplemental-creator-artworks-001.json',dict(at=m.now(),variants=VARIANTS,additional_artist_ids=ids,artworks=rows,unlinked_artworks=labels,
        policy='Possible spelling, attribution-history and related-family leads only. No profile reconciliation or artist links inferred.'))
    aliases={}
    for a in identity['aliases']+surnames['aliases']:aliases.setdefault(m.norm(a['alias']),set()).add(a['display_name'])
    all_rows={r['id']:r for r in identity['artworks']+identity['unlinked_artworks']+rows+labels}
    comparisons=[]
    for r in research['records']:
        names=r['raw_source_record']['native_fields']['creator_names'];expanded=set(names)
        for name in names:expanded.update(VARIANTS.get(name,[]))
        for name in list(expanded):expanded.update(aliases.get(m.norm(name),[]))
        keys={m.norm(name) for name in expanded}
        pool=[v for v in all_rows.values() if keys&{m.norm(c) for c in v.get('creators',[])} or any(k in m.norm(v.get('unlinked_creator_label')) for k in keys)]
        def score(v):return max(difflib.SequenceMatcher(None,m.norm(r['facts']['title']),m.norm(v[k])).ratio() for k in ['title','alternate_title'] if v.get(k))
        leads=sorted(pool,key=score,reverse=True)[:8]
        comparisons.append(dict(source_record_id=r['source_record_id'],title=r['facts']['title'],creator_names=names,search_names=sorted(expanded),pool_size=len(pool),pool_ids=[v['id'] for v in pool],leads=leads))
    m.save(u.RUN/'creator-title-comparison-leads-001.json',dict(at=m.now(),records=comparisons,policy='Heuristic title ranking supports human review and does not establish same-work identity. Full scoped rows remain in identity evidence.'))
    print('Supplemental',len(ids),'artist leads,',len(rows),'artwork rows,',len(labels),'unlinked labels; comparisons',len(comparisons),flush=True)


if __name__=='__main__':main()
