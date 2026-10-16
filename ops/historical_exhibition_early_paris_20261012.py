"""Selected Academy exhibitions, supported by inspected original-minute pages.

Production-only, pinned, atomic import. No local catalogue or artwork mutations.
Competition marks are documentary identities, never invented catalogue numbers.
"""
from pathlib import Path
import json
import sys

from psycopg.types.json import Jsonb
import exhibitions_common as c

OUT = Path.home() / 'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/early-paris'
BATCH = 'historical-exhibitions-early-paris-20261012'
PROVIDER = 'academie-royale-minutes-vol1'
PLAN = OUT / 'import-plan.json'
BOOK_URL = 'https://archive.org/details/procsverbauxde01acaduoft'
BOOK_TITLE = 'Procès-verbaux de l’Académie royale de peinture et de sculpture, tome I, 1648–1672'
CORNEILLE = 'a581e48e-f4f9-544e-bcc8-fb2bb72578a9'
PAGES = [294, 295, 296, 347, 348, 349, 369, 388, 389]


def native(year):
    return f'{year}-' + ('prize-paintings' if year == 1664 else 'academy-exhibition')


def eid(year):
    return c.uid(PROVIDER + '/' + native(year))


def sid(year):
    return c.uid('source/' + PROVIDER + '/' + native(year))


def normalized(value):
    return json.loads(json.dumps(value, default=str))


def receipts():
    result = {}
    for key, name in [('minutes', 'procsverbauxde01acaduoft.pdf'),
                      ('monier', 'catzarts-monier-bio.html'),
                      ('corneille', 'catzarts-corneille-bio.html'),
                      ('louvre_candidate', 'louvre-inv2622.html')]:
        rc = c.load(OUT / (name + '.receipt.json'))
        assert rc['status'] == 200
        assert c.sha((OUT / name).read_bytes()) == rc['sha256']
        result[key] = rc
    return result


def records():
    shared = ['Opening and closing days are unknown; attested meeting dates are not fabricated event boundaries.',
              'Meeting signatories are not an exhibition checklist or proof that each signer exhibited.',
              'Historical venue labels do not assign the event to a present-day museum or imply holdings.']
    rows = [
        dict(year=1664, title='Exposition publique des tableaux du prix de l’Académie royale (1664)',
             dateDisplay='August–September 1664; exact opening and closing dates unknown',
             venue='Salle des étudiants, Académie royale de peinture et de sculpture',
             printedPages=[264, 265, 266], pdfPages=[294, 295, 296],
             basis='The minutes of 30 August order the prize paintings to remain publicly exposed for eight days; 6 September extends the display until Colbert can judge. The 10 September vote distinguishes eight paintings, A–H, and two bas-reliefs, J and L. The awards name Meunier and Corneille as the first two painters.',
             attestations=[dict(date='1664-08-30', claim='Public display in the students’ room and public discussion expressly recorded.'),
                           dict(date='1664-09-06', claim='Paintings remain exposed while the award decision is postponed.'),
                           dict(date='1664-09-10', claim='Paintings A–H judged; first prize A, second prize E. Meunier and Corneille named in the award minute.')],
             issues=['Editorial event title: no contemporary printed livret title is asserted.',
                     'A–H are competition marks, not printed catalogue numbers. Six painting titles and creators are unknown.',
                     'The two bas-reliefs J and L are excluded from the pictorial checklist.',
                     'Louvre INV 2622 is a candidate for the Golden Fleece painting, but its object history calls it a 1676 reception piece and records enlargement and attribution confusion. No exact-object link or image is attached until that conflict is resolved.']),
        dict(year=1667, title='Exposition de l’Académie royale de peinture et de sculpture (1667)',
             dateDisplay='April 1667; exact opening and closing dates unknown',
             venue='Académie royale de peinture et de sculpture',
             printedPages=[317, 318, 319], pdfPages=[347, 348, 349],
             basis='The 9 April minute records Colbert considering the exhibited works. On 30 April the Academy compensates its usher for the full two weeks of public exhibition of the Academicians’ paintings.',
             attestations=[dict(date='1667-04-02', claim='Exhibition arrangement planned; this alone does not establish occurrence.'),
                           dict(date='1667-04-09', claim='Colbert’s inspection of the works is recorded.'),
                           dict(date='1667-04-30', claim='Two weeks of public exhibition retrospectively confirmed.')],
             issues=['The two-week duration does not establish exact opening or closing days.',
                     'Raphael’s Saint Michael is mentioned for a separate lecture at the Cabinet du Roi because it could not be transported; it is not imported as an exhibited work.']),
        dict(year=1669, title='Exposition de l’Académie royale de peinture et de sculpture (1669)',
             dateDisplay='April 1669; documented on 20 April; opening and closing dates unknown',
             venue='Académie royale de peinture et de sculpture', printedPages=[339], pdfPages=[369],
             basis='The 20 April minute expressly records Colbert considering paintings specially exhibited for the anniversary solemnity of the Academy’s establishment.',
             attestations=[dict(date='1669-04-20', claim='Paintings already exposed for the Academy solemnity and considered by Colbert.')],
             issues=['The earlier proposal to display drawings arriving from Rome is not a second confirmed exhibition or a checklist for this event.']),
        dict(year=1671, title='Exposition de l’Académie royale de peinture et de sculpture (1671)',
             dateDisplay='March–April 1671; documented on 28 March and extended through the following week',
             venue='Cour de l’Hôtel de Richelieu, Académie royale de peinture et de sculpture',
             printedPages=[358, 359], pdfPages=[388, 389],
             basis='On 28 March the minute records paintings and sculptures exposed, including paintings around the Hôtel de Richelieu courtyard. The continuation orders the works to remain exposed throughout the following week.',
             attestations=[dict(date='1671-03-28', claim='Existing display and Colbert visit; display extended through the following week.')],
             issues=['The courtyard is explicitly documented; it is not assigned to today’s Louvre museum.',
                     'Prize drawings presented for judging and Baudesson’s two reception flower paintings are not silently treated as a public exhibition checklist.',
                     'Sculpture is documented as part of the event but no sculpture entry is imported.']),
    ]
    for r in rows:
        r.update(id=eid(r['year']), nativeID=native(r['year']), issues=shared + r['issues'])
    return rows


def plan():
    rc = receipts()
    reconciliation = c.load(OUT / 'duplicate-reconciliation.json')
    # All 154 early-or-undated titles inspected; none represents these events.
    assert len(reconciliation['earlyOrUndatedEvents']) == 154
    assert not [x for x in reconciliation['earlyOrUndatedEvents'] if x['start_year'] is not None]
    assert reconciliation['corneillePin']['birth_year'] == 1649
    with c.connect() as db:
        assert db.execute('SELECT count(*) n FROM exhibitions WHERE start_year=ANY(%s)', ([1664,1667,1669,1671],)).fetchone()['n'] == 0
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE source_key=%s', (PROVIDER,)).fetchone()['n'] == 0
        artist = db.execute('SELECT id,display_name,birth_year,death_year,status,revision FROM artists WHERE id=%s', (CORNEILLE,)).fetchone()
        assert normalized(artist) == reconciliation['corneillePin']
        before = db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    entries = []
    for mark in 'ABCDEFGH':
        title = {'A': 'La Conqueste de la Toison d’or', 'E': 'La fable de Danaée'}.get(mark)
        creator = {'A': 'Meunier (Pierre Monier)', 'E': 'Corneille (Jean-Baptiste Corneille)'}.get(mark)
        entries.append(dict(id=c.uid(f'entry/{PROVIDER}/1664/prize-mark-{mark}'), mark=mark,
                            title=title or f'Unidentified prize painting (competition mark {mark})',
                            editorialTitle=title is None, creator=creator, artworkID=None,
                            sourceArtworkID='prize-mark-' + mark,
                            rank={'A': 1, 'E': 2}.get(mark), sourcePages='264–266'))
    people = [dict(name='Pierre Monier', originalName='Meunier', key='monier', artistID=None,
                   basis='First-prize painting author in the original minute. Beaux-Arts de Paris authority biography explicitly identifies Pierre Monier, born 1641, died 1703, and his Golden Fleece prize in 1664. No matching canonical artist exists among inspected Monier/Mosnier/Monnier/Meunier variants.'),
              dict(name='Jean-Baptiste Corneille', originalName='Corneille', key='corneille', artistID=CORNEILLE,
                   basis='Second-prize painting author. Beaux-Arts de Paris authority biography explicitly names his 1664 Danaë second prize, with 1649–1695 lifespan matching the existing artist. Michel Corneille and the twentieth-century Corneille are excluded.')]
    review = [dict(pdfPage=n, printedPage=n-30, sha256=c.sha((OUT/f'minutes-page-{n}.png').read_bytes()),
                   checked='Rendered original page inspected; date headings, medium wording, competition marks and printed pagination checked against OCR.') for n in PAGES]
    c.save(PLAN, dict(at=c.now(), batch=BATCH, records=records(), entries=entries, people=people,
                     receipts=rc, visualReview=review, beforeActive=before, pinnedArtist=artist,
                     reconciliationSHA256=c.sha((OUT/'duplicate-reconciliation.json').read_bytes()),
                     counts=dict(events=4, sourceRows=6, occurrences=4, publications=6, participants=2, linkedParticipants=1, entries=8, linkedEntries=0),
                     mainCatalogueWrites=False, realLocalDatabaseWrites=False, newImages=0))
    print('Prepared four events, eight documented paintings, two artists and one canonical artist link.')


def insert_source(db, source_id, exhibition_id, key, record_id, rc, payload, interpretation):
    db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
               (source_id, exhibition_id, key, record_id, rc['url'], rc['retrievedAt'], rc['path'], rc['sha256'], Jsonb(payload), Jsonb(interpretation)))


def apply():
    p = c.load(PLAN)
    assert p['receipts'] == receipts()
    assert p['counts'] == dict(events=4, sourceRows=6, occurrences=4, publications=6, participants=2, linkedParticipants=1, entries=8, linkedEntries=0)
    assert c.sha((OUT/'duplicate-reconciliation.json').read_bytes()) == p['reconciliationSHA256']
    for page in p['visualReview']:
        assert c.sha((OUT/f"minutes-page-{page['pdfPage']}.png").read_bytes()) == page['sha256']
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s OR start_year=ANY(%s)', (BATCH,[1664,1667,1669,1671])).fetchone()['n'] == 0
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE source_key=%s', (PROVIDER,)).fetchone()['n'] == 0
        artist = db.execute('SELECT id,display_name,birth_year,death_year,status,revision FROM artists WHERE id=%s FOR SHARE', (CORNEILLE,)).fetchone()
        assert normalized(artist) == p['pinnedArtist']
        with db.pipeline():
            for r in p['records']:
                year=r['year']; source_id=sid(year); occurrence_id=c.uid(f'occurrence/{PROVIDER}/{year}')
                db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,series_label,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,'month','held',%s,'physical',%s,%s,'review',%s)",
                           (r['id'], r['title'], c.norm(r['title']),year,year,r['dateDisplay'],r['basis'],'partial' if year==1664 else 'unavailable',
                            'Prix de l’Académie royale' if year==1664 else 'Expositions de l’Académie royale de peinture et de sculpture',BATCH))
                insert_source(db,source_id,r['id'],PROVIDER,r['nativeID'],p['receipts']['minutes'],r,
                              dict(operation=BATCH,printedPages=r['printedPages'],pdfPages=r['pdfPages'],issues=r['issues'],originalScanVisuallyReviewed=True))
                db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence) VALUES(%s,%s,%s,'other',%s,%s,'1875',%s,%s,%s,%s)",
                           (c.uid(f'publication/{PROVIDER}/{year}'),r['id'],source_id,BOOK_TITLE,'Académie royale; edited by Anatole de Montaiglon',BOOK_URL,
                            'Internet Archive: procsverbauxde01acaduoft',', '.join(map(str,r['printedPages'])),
                            Jsonb(dict(kind='Scholarly edition of original institutional minutes, not an exhibition livret.',publicationYearIsNotEventYear=True,sourceSHA256=p['receipts']['minutes']['sha256']))))
                db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,'Paris','France','FR',%s,%s)",
                           (occurrence_id,r['id'],source_id,r['venue'],r['dateDisplay'],Jsonb(dict(printedPages=r['printedPages'],exactBuildingUnknown=year in(1664,1667,1669),holdingClaim=False,currentDisplayClaim=False))))
            for person in p['people']:
                source_id=c.uid(f"source/beaux-arts-paris-authority/1664/{person['key']}")
                rc=p['receipts'][person['key']]
                insert_source(db,source_id,eid(1664),'beaux-arts-paris-authority',f"1664-prize/{person['key']}",rc,person,
                              dict(operation=BATCH,claim='Artist identity and explicitly named 1664 prize painting.',objectDepictedOnPageNotAnExhibitionEntry=True))
                db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,url,source_identifier,evidence) VALUES(%s,%s,%s,'other',%s,%s,%s,%s)",
                           (c.uid(f"publication/{BATCH}/biography/{person['key']}"),eid(1664),source_id,'Beaux-Arts de Paris authority biography: '+person['name'],rc['url'],rc['url'],
                            Jsonb(dict(biographySupports=person['basis'],receptionPaintingOnPageNotExhibitedIn1664=True))))
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence) VALUES(%s,%s,%s,%s,%s,'Artist',%s,%s)",
                           (c.uid(f"participant/{BATCH}/{person['key']}"),eid(1664),source_id,person['artistID'],person['name'],person['key'],Jsonb(dict(person,originalMinuteSourceID=sid(1664),originalMinutePage=266,personalAttendanceNotInferred=True))))
            for entry in p['entries']:
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,source_artwork_id,title_label,creator_label,medium_label,participation,source_page,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,'Painting','exhibited',%s,%s,%s)",
                           (entry['id'],eid(1664),sid(1664),c.uid(f'occurrence/{PROVIDER}/1664'),entry['sourceArtworkID'],entry['title'],entry['creator'],entry['sourcePages'],
                            Jsonb(dict(entry,publicDisplayPages=[264],votePage=265,awardPage=266,competitionMarkIsNotCatalogueNumber=True,
                                       creationDateUnknown=True,mediumBasis='Tableaux explicitly distinguished from bas-reliefs J and L.',
                                       artworkIdentityUnresolved=True)),
                            'Unmatched documentary painting. Original competition identity preserved; no image, modern inventory or canonical work inferred.'))
            db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,claimed_start_year,claimed_end_year,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,1648,1672,1664,1671,'partial',%s)",
                       (c.uid('coverage/'+BATCH),PROVIDER,BOOK_URL,Jsonb(dict(counts=p['counts'],selectedOriginalPages=PAGES,wholeVolumeReviewed=False,worldwideComplete=False,remaining='Other minutes and original catalogue checklists; exact surviving objects and images.'))))
        assert db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(BATCH,)).fetchone()['n']==4
    c.save(OUT/'delivered.json',dict(at=c.now(),batch=BATCH,counts=p['counts'],planSHA256=c.sha(PLAN.read_bytes()),newImages=0,mainCatalogueWrites=False,realLocalDatabaseWrites=False))
    print('Committed four historical exhibitions and eight painting entries.')


def verify():
    p=c.load(PLAN); ids=[r['id'] for r in p['records']]
    with c.connect() as db:
        actual=db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY start_year',(ids,)).fetchall()
        assert len(actual)==4
        for a,r in zip(actual,p['records']):
            assert str(a['id'])==r['id'] and a['title']==r['title'] and a['date_display']==r['dateDisplay']
            assert a['start_year']==a['end_year']==r['year'] and a['start_date'] is None and a['end_date'] is None
            assert (a['date_precision'],a['event_state'],a['status'],a['import_batch'])==('month','held','review',BATCH)
        counts=dict(events=len(actual))
        for key,table in [('sourceRows','exhibition_source_records'),('occurrences','exhibition_occurrences'),('publications','exhibition_publications'),('participants','exhibition_participants'),('entries','exhibition_entries')]:
            counts[key]=db.execute(f'SELECT count(*) n FROM {table} WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
        counts['linkedParticipants']=db.execute('SELECT count(*) n FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[]) AND artist_id IS NOT NULL',(ids,)).fetchone()['n']
        counts['linkedEntries']=db.execute('SELECT count(*) n FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[]) AND artwork_id IS NOT NULL',(ids,)).fetchone()['n']
        assert counts==p['counts']
        entries=db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY source_artwork_id',(eid(1664),)).fetchall()
        for a,r in zip(entries,p['entries']):
            assert str(a['id'])==r['id'] and a['title_label']==r['title'] and a['creator_label']==r['creator']
            assert a['catalogue_number'] is None and a['date_label'] is None and a['artwork_id'] is None
            assert a['participation']=='exhibited' and a['medium_label']=='Painting'
            assert a['evidence']['mark']==r['mark'] and str(a['source_record_id'])==sid(1664)
        artist=db.execute('SELECT id,display_name,birth_year,death_year,status,revision FROM artists WHERE id=%s',(CORNEILLE,)).fetchone()
        assert normalized(artist)==p['pinnedArtist']
        for row in db.execute('SELECT capture_url,capture_sha256 FROM exhibition_source_records WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchall():
            assert c.sha(Path(row['capture_url']).read_bytes())==row['capture_sha256']
        active=db.execute("SELECT count(*) active,count(*) FILTER(WHERE start_year BETWEEN 1600 AND 1989) dated_start_within_scope,count(*) FILTER(WHERE start_year IS NULL) undated_legacy,count(*) FILTER(WHERE start_year<1600 OR start_year>1989 OR end_year>1989) outside_by_date_fields,min(start_year) earliest_dated FROM exhibitions WHERE status<>'archived'").fetchone()
    c.save(OUT/'verified.json',dict(at=c.now(),counts=counts,activeExhibitions=active,allEventsAndEntriesChecked=True,sourceHashesChecked=True,canonicalArtistUnchanged=True,mainCatalogueWrites=False,realLocalDatabaseWrites=False,newImages=0))
    print('Verified',counts,active)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('plan','apply','verify'):
        raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
