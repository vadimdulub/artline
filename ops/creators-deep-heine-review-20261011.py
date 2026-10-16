#!/usr/bin/env python3
"""Freeze Heine's reviewed selection after fresh production identity research."""
import copy
import importlib.util
import json
from pathlib import Path

sp = importlib.util.spec_from_file_location('campaign', Path(__file__).with_name('creators-deep-continuation-20261011.py'))
x = importlib.util.module_from_spec(sp); sp.loader.exec_module(x)
x.configure('thomas-theodor-heine')
plan = x.r.load(x.RUN/'research-selection.json.gz')
allrows = plan['rows']
assert len(x.r.load(x.RUN/'expanded-existing-records.json.gz')) == 4
selected = [3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 20]

def native(url, publisher, facts, review, record=None, locator=None):
    value = x.r.load(x.RUN/'native-objects'/(x.r.sha(url.encode())+'.json'))
    assert value['receipt']['status'] == 200 and 'Making sure' not in (value['title'] or '')
    return dict(url=url, publisher=publisher, receipt=value['receipt'], facts=facts,
                review=review, record_id=record, locator=locator, confidence=.98)

def document(name, publisher, facts, review, locator):
    receipt = x.r.load(x.RUN/(name+'-receipt.json'))
    assert receipt['status'] == 200 and not receipt.get('hold')
    return dict(url=receipt['url'], publisher=publisher, receipt=receipt, facts=facts,
                review=review, locator=locator, confidence=.98)

def title(row, value):
    w = row['work']; w['alternate_title'] = w['title']; w['title'] = value
    w['normalized_title'] = x.q.norm(value)

book = {7: ('Der Herrscher', 67), 8: ('Regierungssorgen', 35),
        9: ('Der südafrikanische Riesenkater', 41), 11: ('Im Damenbad', 51)}
rows = []
for i in selected:
    row = copy.deepcopy(allrows[i-1]); w = row['work']
    row['selection_index'] = i
    row['source_work_before_editorial_review'] = copy.deepcopy(w)
    row['confidence'] = .98
    row['native_sources'] = []
    note = ''
    if i == 3:
        title(row, 'Halbe Unschuld (cover design for Marcel Prévost)')
        w.update(creation_year_start=1895, creation_year_end=1895, date_display='1895', date_precision='exact', work_type='print', medium_text='lithograph')
        note = 'Matching couple, lilies, three dragons and lettering identify the cover design. The visible imprint and Kunstbibliothek record establish 1895; preserve WikiArt’s 1896 Pan-reproduction label in evidence. No impression-specific dimensions or museum ownership are transferred.'
        row['native_sources'].append(native('https://search.smb.museum/object/obj-2431451', 'Staatliche Museen zu Berlin, Kunstbibliothek', dict(title='Buchumschlag Marcel Prévost, Halbe Unschuld', publication_year=1895, technique='Lithografie', accession='14272246', actual_native_image_label='Public Domain Mark 1.0'), note, '14272246'))
        row['date_review'] = 'New design record uses the primary catalogue and visible 1895 imprint. Original WikiArt title and 1896 value remain preserved; this is not a new claim about the date of a specific Pan impression.'
    elif i == 4:
        title(row, 'Ein Kinderspiel (Simplicissimus)')
        note = 'The two panels with children playing monarchs, geese and a dog match the scholarly reproduction exactly. Its caption identifies issue 5, 1896. The number 5 is an issue number, not a September date.'
        row['native_sources'].append(document('danguy', 'Laurence Danguy, research publication deposited at Université de Lausanne', dict(title='Ein Kinderspiel', issue=5, publication_year=1896, illustration_credit='Klassik Stiftung Weimar'), note, 'printed p. 400, fig. 64; PDF p. 12'))
    elif i == 5:
        title(row, 'Simplicissimus (red bulldog poster)')
        w.update(work_type='print', medium_text='colour lithograph')
        note = 'Red bulldog, broken chain, signature and lettering match ALBERTINA DG2003/1983, dated 1896/97. WikiArt’s 1897 fits that range and is retained. DG2003/1980 and the Delaware poster instead depict a woman and devil; those matches are rejected. No physical-impression holding is inferred.'
        row['native_sources'].append(native('https://sammlungenonline.albertina.at/en/objects/147649/simplicissimus', 'ALBERTINA, Vienna', dict(title='Simplicissimus', date='1896/97', technique='Farblithographie', accession='DG2003/1983'), note, 'DG2003/1983'))
    elif i == 6:
        note = 'The selected source depicts the cover for Knut Hamsun’s Hunger, including the source reproduction caption. Retain WikiArt’s 1900 date, without inventing a specific edition, physical dimensions or technique. No independent exact-edition confirmation was obtained.'
    elif i in book:
        name, scan = book[i]; title(row, name+' (Thorheiten)')
        w.update(creation_year_start=None, creation_year_end=None, date_precision='unknown', date_display='Unknown creation date; published c. 1901')
        note = 'Exact composition matched to the digitized Thorheiten page; native caption supplies the distinguishing title. The library dates the book approximately 1901, an inferred publication date rather than the original drawing’s creation year. The book is not evidence of holding the original drawing.'
        row['date_review'] = 'WikiArt supplies 1901. Because this is a reprinted illustration, original creation years stay null; the c. 1901 publication provides image-age evidence only.'
        row['image_date_evidence'] = dict(creation_year_end=1901, date_display='Published c. 1901', basis='Exact selected illustration in the Jüdisches Museum Berlin digitized book. METS dateIssued 1901 is qualified inferred; publication establishes that the design predates the image cutoff.', source_receipt=x.r.load(x.RUN/'thorheiten-mets-receipt.json'))
        rc = x.r.load(x.RUN/'book-page-receipts'/f'{scan:04d}.json')
        row['native_sources'].append(dict(url=rc['url'], publisher='Jüdisches Museum Berlin, library digitization', receipt=rc,
            record_id=f'heinthor_00025443/physical-{scan}', locator=f'physical scan {scan}',
            facts=dict(title=name, book='Thorheiten', image_match='Exact composition and caption'), review=note, confidence=.99))
        rc = x.r.load(x.RUN/'thorheiten-mets-receipt.json')
        row['native_sources'].append(dict(url=rc['url'], publisher='Jüdisches Museum Berlin, library digitization', receipt=rc,
            record_id='heinthor_00025443', facts=dict(publication_year=1901, date_qualifier='inferred', shelfmark='II.12.Heine 563', publisher='Albert Langen, München'),
            review='Book-publication evidence only; original drawing date and holding remain unknown.', confidence=.99))
    elif i == 12:
        title(row, 'Berlin Secession poster design (magazine reproduction)')
        w.update(creation_year_start=None, creation_year_end=None, date_precision='unknown', date_display='Unknown creation date; reproduced 1906 (WikiArt)')
        note = 'The bear and woman match the pictorial design of Christie’s 1906 poster, whose catalogue notes first use in 1901. WikiArt reproduces only the design without the poster lettering and calls it a 1906 magazine illustration. Keep that reproduction distinct from the complete auctioned poster; no physical dimensions, impression identity or holding is transferred.'
        row['date_review'] = 'Source dates concern first poster use (1901) and a later poster/publication (1906). Original design creation is not dated precisely; leave numerical creation years null.'
        row['image_date_evidence'] = dict(creation_year_end=1906, date_display='Design documented in 1901 and 1906', basis='Matched dated native poster design and explicit WikiArt reproduction date; this is not a date inferred from the artist lifespan.')
        row['native_sources'].append(native('https://www.christies.com/en/lot/lot-1988313', 'Christie’s, primary auction catalogue', dict(title='Berliner Secession', poster_year=1906, first_design_use=1901, comparison_scope='pictorial design; different surrounding lettering'), note, '1988313'))
    elif i == 13:
        note = 'Distinct symmetrical two-dachshund composition with a central red heart, flame and wreath. Direct source identity and 1906 date are retained. The exact publication, technique and physical dimensions remain unknown.'
    elif i == 14:
        title(row, 'Dies ist das Hundevieh (Simplicissimus cover)')
        w.update(creation_year_start=1905, creation_year_end=1905, date_precision='exact', date_display='1905')
        note = 'The source reproduction visibly says volume 10, issue 1. Hitotsubashi University Library reproduces the identical cover and identifies 4 April 1905. Correct WikiArt’s conflicting 1910 value for this new record and preserve it in source evidence.'
        row['date_review'] = note
        row['native_sources'].append(document('hitotsubashi', 'Hitotsubashi University Library, 2017 exhibition catalogue', dict(title='Dies ist das Hundevieh', publication_date='1905-04-04', volume=10, issue=1), note, 'PDF p. 3, exhibit 3'))
    elif i == 16:
        title(row, 'Der Friedenskuß (Simplicissimus cover)')
        note = 'Cover title, angel-and-devil composition, volume 24 issue 15 and printed 8 July 1919 agree with the Haus der Bayerischen Geschichte exhibition document. No current-display or ownership assertion follows from that exhibition reproduction.'
        row['native_sources'].append(document('friedenskuss', 'Haus der Bayerischen Geschichte, Dachau exhibition documentation', dict(title='Der Friedenskuß', publication_date='1919-07-08', exhibit_number=1151), note, 'PDF p. 1, item 1151'))
    elif i == 17:
        title(row, 'Wahlparolen (Simplicissimus)')
        note = 'Four dogs face a sausage-shaped cloud; the printed title reads Wahlparolen. WikiArt supplies 1920. The Wikisource contents index independently lists Heine’s Wahlparolen in volume 25 (1920/21), issue 8, page 113; that transcription is supporting evidence, not a museum holding.'
        row['native_sources'].append(native('https://de.wikisource.org/wiki/Simplicissimus/Inhalt_1914%E2%80%931929', 'Wikisource, transcribed publication contents', dict(title='Wahlparolen', creator='Thomas Theodor Heine', volume=25, volume_years='1920/21', issue=8, page=113, source_kind='secondary transcription'), note, locator='25. Jg, 1920/21; Heft 08; S. 113'))
    elif i == 18:
        note = 'The distinct red-devil festival poster visibly gives Tuesday 29 January; WikiArt supplies the year 1929. Preserve the complete supplied poster frame. No MoMA physical impression or museum holding is assigned from search snippets; its direct site request was denied.'
    elif i == 20:
        title(row, 'Die 11 Scharfrichter (Münchener Künstler poster)')
        w.update(creation_year_start=1901, creation_year_end=1901, date_precision='exact', date_display='1901', work_type='print', medium_text='colour lithograph')
        note = 'Figure, heads and the exact Münchener Künstler lettering match ALBERTINA DG2003/1981, dated 1901. DG2003/1979 has different daily-performance/address lettering and is excluded as a different variant. The museum’s physical impression is not identified as the photographed WikiArt copy.'
        row['date_review'] = 'WikiArt has no date. The visually matched lettering variant in the ALBERTINA catalogue supplies 1901; not inferred from creator lifespan.'
        row['native_sources'].append(native('https://sammlungenonline.albertina.at/en/objects/147647/die-11-scharfrichter', 'ALBERTINA, Vienna', dict(title='Die 11 Scharfrichter', year=1901, accession='DG2003/1981', technique='Farblithographie'), note, 'DG2003/1981'))
    assert note
    row['editorial_review'] = note
    row['identity_basis'] += ' '+note
    row['image_identity_review'] = 'Authentic WikiArt original visually inspected; unique composition, creator and stable object IDs checked. '+note
    row['research_flags_resolved'] = row.pop('research_flags', [])
    rows.append(row)

exclusions = {
    1: 'Existing exact WikiArt artwork and image; preserve.',
    2: 'Existing exact WikiArt artwork and image; preserve.',
    10: 'Fifth generic Thorheiten image shows men and ballet dancers. Its precise native caption/page remains unresolved after selected-page research; defer rather than assign another illustration’s title.',
    15: 'Probable same composition as existing Met Woman Nursing Fawns, 1911, object 398014 / artwork 145a7447-7868-5e2c-9cc3-f0f73305e482. Exact print/impression cannot be visually reconciled from the unavailable Met reproduction. No duplicate creation or image attachment.',
    19: 'Eifersucht has no source creation date or independent object-specific age evidence. No year inferred from artist lifespan; held.'
}
plan['rows'] = rows
plan['held'] += [dict(selection_index=i, title=allrows[i-1]['work']['title'], source_url=allrows[i-1]['source_url'], reason=reason) for i, reason in exclusions.items()]
plan.update(reviewed_at=x.r.now(), reviewer='Codex editorial and paired visual research',
    additional_identity_inventory=dict(path=str((x.RUN/'expanded-existing-records.json.gz').relative_to(x.ROOT)), sha256=x.r.sha((x.RUN/'expanded-existing-records.json.gz').read_bytes()), records=4),
    research_limitations=['15 selected additions; two existing linked artworks and two further raw-label Met records remain preserved.', 'Five creation dates remain unknown: four reprinted Thorheiten illustrations and the Berlin Secession magazine reproduction. Publication evidence supports their images.', 'No new museum holding or current-display claim. Sources can establish a print design without identifying a particular surviving impression.', 'Source denials and bot challenges were retained and not bypassed. WikiArt source approval is distinct from each actual Public domain label.'])

with x.r.connect('production') as db, db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    assert x.inventory(db) == x.r.load(x.RUN/'expanded-existing-records.json.gz')
    conflicts = x.c.collisions(db, rows)
    assert not any(conflicts.values()), conflicts
    urls = [s['url'] for row in rows for s in row['native_sources']]
    native_conflicts = db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)", (urls,)).fetchall()
    assert not native_conflicts, native_conflicts
x.r.save(x.RUN/'native-identity-collision-check.json', dict(at=x.r.now(), exact_source_collisions=conflicts, native_url_collisions=native_conflicts, comparison_records=4, local_database_connected=False))
count = x.c.validate(plan)
x.r.save_gz(x.RUN/'reviewed-plan.json.gz', plan)
x.r.save_gz(x.RUN/'image-selection.json.gz', plan)
print(json.dumps(dict(new=len(rows), source_bodies=count, native_citations=sum(len(v['native_sources']) for v in rows), holdings=0, unknown_creation_dates=sum(v['work']['creation_year_start'] is None for v in rows))))
