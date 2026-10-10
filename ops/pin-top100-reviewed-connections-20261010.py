#!/usr/bin/env python3
"""Pin four individually corroborated teaching relationships; no database writes."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('cesi-top100-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    audit=m.load(m.RUN/'top100-connection-audit-final.json.gz');base=m.load(m.RUN/'baseline.json.gz')
    artists={r['record']['id']:r['record'] for r in base['artists']}|audit['artists']
    sources={
      'Matthew Smith':('https://assets.moma.org/documents/moma_catalogue_2887_300190205.pdf','Museum of Modern Art catalogue, printed page 115 (PDF page 120), visually inspected: Smith enrolled at Matisse’s Paris school in 1910.'),
      'Oleksandr Murashko':('https://museum.mincult.gov.ua/authors/murashko-oleksandr-oleksandrovich','The Ukrainian Ministry of Culture museum portal identifies Murashko as a pupil of Ilya Repin and as a student at the St Petersburg Academy.'),
      'Pieter van Hanselaere':('https://vlaamsekunstcollectie.be/en/collection/1820-b','Museum of Fine Arts Ghent collection text, via Vlaamse Kunstcollectie, says Van Hanselaere studied with David in Paris after his Ghent training. Pierre/Pieter variants refer to the same artist in this object record.'),
      'Giovanni Domenico Tiepolo':('https://sammlung.staedelmuseum.de/en/person/tiepolo-giovanni-domenico','Städel Museum biography documents training in his father Giambattista Tiepolo’s workshop beginning around 1740.')}
    rows=[];held=[]
    for r in audit['candidates']:
        name=artists[r['target_artist_id']]['display_name'];source=artists[r['source_artist_id']]['display_name']
        if name in sources and r['relationship_type']=='teacher_of':
            url,note=sources[name];raw,receipt=m.capture(url);assert receipt['status']==200
            rows.append(dict(source_artist_id=r['source_artist_id'],source_label=source,target_artist_id=r['target_artist_id'],relationship_type='teacher_of',evidence_level='documented',confidence='high',evidence_note=note+' Independently corroborates the retained WikiArt relationship lead. Artist endpoints resolved through exact WikiArt profile identifiers; no name-only authority merge.',status='review',source_url=url,receipt=receipt))
        else:
            reason='Additional independent corroboration and precise relationship type required'
            if name in ['Andrea Mantegna','Johannes Vermeer'] and source in ['Rembrandt van Rijn','Camille Pissarro']:reason='Source relationship direction contradicts chronology; rejected as stated'
            if name=='Nina Arbore':reason='Museum scholarship candidate found, but the primary PDF retrieval was denied; no bypass or new claim'
            held.append(dict(**r,source_name=source,target_name=name,hold=reason))
    assert len(rows)==4 and len(held)==19
    m.save(m.RUN/'top100-reviewed-connections.json',dict(at=m.now(),rows=rows,held=held,method='Explicit source assertion, exact artist identifier reconciliation, then independent primary museum corroboration. New claims remain review.'))
    print('Pinned',len(rows),'teacher relationships;',len(held),'resolved candidate pairs held')
if __name__=='__main__':main()
