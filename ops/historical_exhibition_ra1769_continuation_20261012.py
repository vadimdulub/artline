#!/usr/bin/env python3
"""Reviewed continuation of the original 1769 catalogue, not an OCR bulk import.

The earlier 15-entry delivery is immutable. This adds eligible remaining entries,
preserving unidentified works as exhibition labels rather than inventing objects.
"""
from pathlib import Path
import json
import sys

from psycopg.types.json import Jsonb
import exhibitions_common as c

OUT = Path.home() / 'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/royal-academy/1769'
EID = c.uid('royal-academy/summer/1769')
SID = c.uid('source/royal-academy/1769')

# Catalogue number | printed page | original creator heading (RA suffix omitted)
# | title transcription | explicit medium. Long-s and broken lines normalized.
TRANSCRIPTION = '''
3|3|John Baker|A piece of flowers.|
4|3|John Baker|Its companion.|
5|3|George Barret|A view in Penton Lynn, on the river Liddle, running through Canonby, in the county of Dumfries, three miles south-east of the first Turnpike on the new Road from Carlisle, through the Duke of Buccleugh's estate, to Edinburgh.|
6|3|George Barret|Part of Melross Abbey on the river Tweed, by moon-light, belonging to his Grace the Duke of Buccleugh.|
7|4|Francesco Bartolozzi|Cupid and Psyche, in crayons.|crayons
8|4|Francesco Bartolozzi|Clitia, a drawing, from a picture of Annibale Carracci.|drawing after Annibale Carracci
10|4|Charles Catton|Tygers reposing.|
11|4|Mason Chamberlin|Portrait of a gentleman, half length.|
12|4|Mason Chamberlin|Ditto, three quarters.|
13|4|Mason Chamberlin|Ditto, three quarters.|
14|4|Mason Chamberlin|Ditto, three quarters.|
30|6|Nathaniel Dance|The King, whole length.|
31|6|Nathaniel Dance|The Queen, ditto.|
32|6|Nathaniel Dance|A portrait of a gentleman, half length.|
33|6|Nathaniel Dance|Ditto of a Bishop.|
34|6|Nathaniel Dance|Ditto of a gentleman, three quarters.|
35|6|Thomas Gainsborough|A portrait of a lady, whole length.|
36|6|Thomas Gainsborough|Ditto of a gentleman.|
37|6|Thomas Gainsborough|A large landscape.|
38|6|Thomas Gainsborough|A boy's head.|
39|6|Edmund Garvy|A view of Rome.|
40|6|Edmund Garvy|A water-fall near Chamberi, in Savoy.|
41|6|Edmund Garvy|A view from Piercefield, the seat of Val. Morris, Esq;|
42|6|Edmund Garvy|Another view of the same place.|
43|6|Edmund Garvy|A view of Tinton Abbey in Wales, water colours.|water colours
44|6|Edmund Garvy|A water-fall in the Alps, ditto.|water colours (catalogue ditto)
45|6|S. H. Grimm|The death of Priam.|drawing (printed brace shared with no. 46)
46|6|S. H. Grimm|The feast of the Centaurs.|drawing (printed brace shared with no. 45)
47|7|S. H. Grimm|A composition of different antique buildings taken from nature, a coloured drawing.|coloured drawing
48|7|S. H. Grimm|The Castle at Canterbury, with St. Mildred's Church, ditto.|coloured drawing (catalogue ditto)
49|7|John Gwynn|An architectonick drawing designed for the alteration of an old room in Shropshire.|architectural drawing
50|7|Francis Hayman|The dispute with the Barber upon Mambrino's helmet.|
51|7|Francis Hayman|Meeting Cardenio in the Black Mountain.|
52|7|Nathaniel Hone|A small whole length.|
53|7|Nathaniel Hone|A portrait of a Clergyman, three quarters.|
54|7|Nathaniel Hone|A portrait of a young gentleman.|
55|7|Nathaniel Hone|A candle light.|
56|7|Nathaniel Hone|A piping boy.|
57|7|Nathaniel Hone|A portrait in enamel.|enamel portrait
58|8|William James|A side view of the Great Temple of Osiris, at Carnack, to which there were avenues of Sphynxes half a mile in length, adorned with triumphial arches; on the right hand is a Portico of a Temple at Amara.|
59|8|William James|The Temple of Osmanduas, at Luxor.|
60|8|William James|The Temple of Isis, at the Isle El Hief, a little above the first Cataract of the Nile; on the right hand is a small Temple called the Temple of the Hawk, because Isis was there worshiped under that symbol.|
65|9|Elias Martin|A view of Westminster-Bridge, with the King of Denmark's procession by water, taken from Mr. Searle's Timber-yard.|
66|9|Elias Martin|A landscape with figures and cattle.|
67|9|Elias Martin|A view in Sweden.|drawing (printed brace shared with no. 68)
68|9|Elias Martin|A watchman sleeping.|drawing (printed brace shared with no. 67)
69|9|Jeremiah Meyer|A portrait in enamel of his Royal Highness the Prince of Wales.|enamel portrait
70|9|Jeremiah Meyer|A portrait in enamel of his Royal Highness Prince Frederick, Bishop of Osnaberg.|enamel portrait
73|9|Mary Moser|A flower-piece in oil.|oil
74|9|Mary Moser|A flower-piece in water colours.|water colours
75|10|F. Milner Newton|A portrait of a lady.|
77|10|William Pars|An arch at Mylassa, in Asia Minor.|
78|10|William Pars|A ruin at Troas, ditto.|
79|10|William Pars|The Propylia, or entrance of the Acropolis at Athens.|
80|10|William Pars|The Castalian spring at Delphi.|
81|10|William Pars|A Temple in the Island Ægina.|
82|10|William Pars|The Cave of Archidamus, near Athens.|
83|10|William Pars|Miletus, with the ferry over the Meander.|
84|10|John Paxton|A portrait of a gentleman, small whole length.|
85|10|John Paxton|A boy in the character of Cupid.|
86|10|John Paxton|A girl playing on a sistrum.|
87|10|Edward Penny|I saw a smith stand with his hammer thus, The whilst his iron did on the anvil cool, With open mouth swallow a taylor's news.|
88|11|Mat. William Peters|A portrait of a lady, a drawing.|drawing
89|11|Sir Joshua Reynolds|A portrait of a lady and her son, whole lengths, in the character of Diana disarming love.|
90|11|Sir Joshua Reynolds|A ditto of a lady in the character of Juno, receiving the cestus from Venus.|
91|11|Sir Joshua Reynolds|Portraits of two ladies, half lengths. Et in Arcadia ego.|
92|11|Sir Joshua Reynolds|Hope nursing love.|
93|11|John Richards|A view of a Cascade at Hester-combe, in Somersetshire, the seat of C. W. Bampfylde, Esq;|
94|11|John Richards|A landscape and figures.|
95|11|John Richards|Ditto.|
96|11|Michael Angelo Rooker|A view of Liverpool.|stained drawing (printed brace shared with no. 97)
97|11|Michael Angelo Rooker|A view of ditto, across the River Mersey.|stained drawing (printed brace shared with no. 96)
98|12|John Russell|The portraits of Micoc, and her son Tootac, Esquimaux Indians, brought over by Commodore Pallisser.|
101|12|Paul Sandby|A view of Roch Abbey.|
102|12|Paul Sandby|A bonfire.|
103|12|Paul Sandby|A view of the old abbey gate at Reading.|
104|12|Paul Sandby|A view of ditto.|
105|12|J. Scouler|Portrait of a Turk, in miniature.|miniature
106|12|Dominick Serres|A view from the gun wharf at Portsmouth.|
107|12|Dominick Serres|The Siege of Fort Royal at Martinique.|
108|13|Dominick Serres|An English man of war chasing a French chebeck into a neutral port.|
109|13|Dominick Serres|A ship of the line and a frigate going upon a cruise in the Mediterranean, with a view of Gibraltar at a distance.|
110|13|Dominick Serres|A view of a ruined abbey by moonlight.|
112|13|William Tompkins|A view of Roehampton, the seat of the Earl of Besborough.|
113|13|William Tompkins|A view of Bolderwood Lodge in the New Forest, Hampshire, belonging to the Earl of Delawar.|
114|13|William Tompkins|A view of Belvena, in the county of Bamffshire, the seat of the Earl of Fife.|
115|13|Peter Toms|An allegorical picture.|
117|14|Samuel Wale|St. Austin preaching Christianity to King Ethelbert and Queen Bertha, in the Isle of Thanet, a sketch.|sketch
118|14|Samuel Wale|The Queen Dowager of King Edward in the Sanctuary delivering up the Duke of York to the Cardinal Archbishop of Canterbury.|
119|14|Thomas Watson|A drawing, after a picture of Rembrant.|drawing after Rembrant (source spelling)
120|14|Benjamin West|The departure of Regulus from Rome.|
121|14|Benjamin West|Venus lamenting the death of Adonis.|
122|14|Richard Wilson|A landskip.|
123|14|Richard Wilson|Its companion.|
124|14|Richard Wilson|A landskip.|
128|15|Francesco Zuccarelli|A landscape and figures, half lengths.|
129|15|Francesco Zuccarelli|Ditto, half lengths.|
130|15|A lady (unidentified; catalogue no. 130)|Portrait of a young lady in crayons.|crayons
131|15|A lady (unidentified; catalogue no. 131)|A landscape, a drawing.|drawing
132|15|Capt. Hamilton, of the 15th Regiment|The falls of Niagara, a drawing.|drawing
133|15|Theodosius Forrest|A view of Cliefden from the Meadows.|
134|15|Capt. Francis Grosse|Riding Gate, Canterbury.|
135|15|Capt. Francis Grosse|Croydon Church.|
136|15|A young gentleman (unidentified)|A Courier Francois.|
'''

# Deliberate identity decisions; missing or ambiguous canonical people stay labels.
CANONICAL = {
    'Francesco Bartolozzi': 'Francesco Bartolozzi',
    'Charles Catton': 'Charles Catton',
    'Nathaniel Dance': 'Sir Nathaniel Dance-Holland',
    'Thomas Gainsborough': 'Thomas Gainsborough',
    'Edmund Garvy': 'Edmund Garvey',
    'S. H. Grimm': 'Samuel Hieronymus Grimm',
    'John Gwynn': 'John Gwynn',
    'Francis Hayman': 'Francis Hayman',
    'Nathaniel Hone': 'Nathaniel Hone',
    'Elias Martin': 'Elias Martin',
    'Jeremiah Meyer': 'Jeremiah Meyer',
    'Mary Moser': 'Mary Moser',
    'William Pars': 'William Pars',
    'John Paxton': 'John Paxton',
    'Edward Penny': 'Edward Penny',
    'Mat. William Peters': 'Rev. Matthew William Peters',
    'Sir Joshua Reynolds': 'Joshua Reynolds',
    'John Russell': 'John Russell',
    'Paul Sandby': 'Paul Sandby',
    'J. Scouler': 'James Scouler',
    'Benjamin West': 'Benjamin West',
    'Francesco Zuccarelli': 'Francesco Zuccarelli',
    'Theodosius Forrest': 'Theodosius Forrest',
    'Capt. Francis Grosse': 'Francis Grose',
}
EXCLUDED = {
    1: 'medallion', 2: 'model', 9: 'equestrian statue model',
    71: 'bas-relief impression from gold chasing', 72: 'ditto bas-relief impression',
    76: 'wax model', 111: 'two portrait models', 116: 'marble bas-relief',
    125: 'marble bust', 126: 'plaster cast from seal', 127: 'sealing-wax impressions',
}
HELD = {n: 'Architectural design/ceiling/elevation; exact physical medium not yet resolved.' for n in [15,16,17,18,99,100]}


def plan():
    base = c.load(OUT / 'entry-delivery-plan-v2.json')
    manifest = c.load(OUT / 'manifest-0.json')
    rows = []
    for line in TRANSCRIPTION.strip().splitlines():
        number, page, creator, title, medium = line.split('|')
        canvas = manifest['sequences'][0]['canvases'][int(page)-1]
        scan = OUT / f'catalogue-scan-{int(page)-1}.jpg'
        rows.append(dict(id=c.uid('entry/royal-academy/1769/'+number), number=number,
            page=page, creator=creator, title=title, medium=medium or None,
            evidence=dict(primaryCatalogue=manifest['@id'], printedPage=page,
                catalogueNumber=number, canvas=canvas['@id'], scanSHA256=c.sha(scan.read_bytes()),
                scanReceipt=c.load(scan.with_name(scan.name+'.receipt.json')),
                transcription='Each selected page visually checked against the scan. Long-s, capitalization, line breaks and braces normalized; historical title/creator spellings and ditto preserved. No creation date inferred from exhibition year.',
                sourceCreatorLabel=creator,
                scope='Pictorial work; exact medium unknown unless stated. No. 49 is explicitly a drawing, not an architectural model.',
                notes='Historical source wording; no inferred identity for unnamed sitters or creators.'),
            artworkID=None, participation='catalogued', date=None))
    previous = {int(x['number']) for x in base['entries']}
    new = {int(x['number']) for x in rows}
    assert len(rows) == len(new) == 104
    assert not (previous & new or new & set(EXCLUDED) or new & set(HELD))
    assert previous | new | set(EXCLUDED) | set(HELD) == set(range(1,137))
    with c.connect() as db:
        current = db.execute('SELECT id,catalogue_number,artwork_id FROM exhibition_entries WHERE exhibition_id=%s ORDER BY catalogue_number', (EID,)).fetchall()
        assert len(current) == 15
        artists = db.execute("SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE display_name=ANY(%s) AND birth_year<1760 AND death_year>=1769 AND status<>'archived' ORDER BY display_name", (list(CANONICAL.values()),)).fetchall()
        assert len(artists) == len(CANONICAL)
        assert all(x['birth_year'] is not None and x['birth_year'] < 1760 and x['death_year'] >= 1769 for x in artists)
        event = db.execute('SELECT * FROM exhibitions WHERE id=%s', (EID,)).fetchone()
    lookup = {x['display_name']: str(x['id']) for x in artists}
    people = [dict(key=c.norm(name).replace(' ','-'),name=name,
        artistID=lookup.get(CANONICAL.get(name,'')),canonicalName=CANONICAL.get(name))
        for name in sorted({r['creator'] for r in rows})]
    c.save(OUT/'continuation-entry-plan.json', dict(at=c.now(),exhibitionID=EID,
        entries=rows,people=people,pinnedArtists=artists,pinnedPreviousEntries=current,
        pinnedExhibition=event,excluded=EXCLUDED,held=HELD,
        catalogueNumbersReviewed=136,eligibleTotal=119,fullChecklist=False,
        basis='104 further eligible entries; 15 delivered earlier; 11 excluded non-pictorial entries and 6 medium-uncertain designs held. All numbered source entries accounted for, but not a complete certified installed checklist.'))
    print('Prepared 104 additional entries; all 136 numbers reviewed; 11 excluded, 6 held.', flush=True)


def apply():
    p = c.load(OUT/'continuation-entry-plan.json')
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        current = db.execute('SELECT id,catalogue_number,artwork_id FROM exhibition_entries WHERE exhibition_id=%s ORDER BY catalogue_number FOR SHARE', (EID,)).fetchall()
        assert json.loads(json.dumps(current,default=str)) == p['pinnedPreviousEntries']
        artists = db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY display_name FOR SHARE', ([x['id'] for x in p['pinnedArtists']],)).fetchall()
        assert json.loads(json.dumps(artists,default=str)) == p['pinnedArtists']
        with db.pipeline():
            for person in p['people']:
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence) VALUES(%s,%s,%s,%s,%s,'Artist',%s,%s)",
                    (c.uid('participant/royal-academy/1769/'+person['key']), EID, SID,
                     person['artistID'],person['name'],person['key'],Jsonb(dict(
                         originalCreatorLabel=person['name'],canonicalName=person['canonicalName'],
                         identityBasis='Exact historical name or reviewed spelling/initial expansion with compatible lifespan.' if person['artistID'] else 'Canonical identity unresolved; no artist record invented.',
                         sourcePages=sorted({r['page'] for r in p['entries'] if r['creator']==person['name']},key=int)))))
            for e in p['entries']:
                db.execute('INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,source_page,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (e['id'],EID,SID,e['artworkID'],'RA1769/'+e['number'],e['number'],e['title'],e['creator'],e['date'],e['medium'],e['participation'],e['page'],Jsonb(e['evidence']),None))
            db.execute("UPDATE exhibitions SET checklist_state='partial',updated_at=now() WHERE id=%s",(EID,))
        result = db.execute('SELECT count(*) n,count(artwork_id) linked FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchone()
        assert result == dict(n=119,linked=2)
    c.save(OUT/'continuation-entry-delivery.json',dict(at=c.now(),additionalEntries=104,
        additionalParticipants=len(p['people']),canonicalParticipantLinks=sum(bool(x['artistID']) for x in p['people']),
        exhibitionEntriesAfter=119,sourceCatalogueNumbersReviewed=136,excludedEntries=11,
        heldEntries=6,mainCatalogueWrites=False,localDatabaseWrites=False,newImages=0,
        planSHA256=c.sha((OUT/'continuation-entry-plan.json').read_bytes())))
    print('Committed 104 additional source catalogue entries.',flush=True)


if __name__ == '__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ['plan','apply']:
        raise SystemExit('Use plan or apply')
    globals()[sys.argv[1]]()
