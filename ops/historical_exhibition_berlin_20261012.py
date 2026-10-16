#!/usr/bin/env python3
"""Selected historical Berlin events from the Academy's own catalogue index.

No catalogue images or main artwork records are downloaded/imported. The index
is evidence for events/publications, not an installed artwork checklist. The
Heidelberg viewer's access challenge remains a hold. Real local DB is read-only.
"""
from pathlib import Path
import collections
import datetime as dt
import json
import re
import sys

import pdfplumber
from psycopg.types.json import Jsonb
import exhibitions_common as c

OUT = Path.home() / 'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/berlin-academy'
URL = 'https://adk.de/files/archiv/PDFs/Preussische_Ausstellungskataloge_Uebersicht_nach_Reihen.pdf'
BATCH = 'historical-exhibitions-berlin-20261012'
PROVIDER = 'berlin-academy-historical-index'
PLAN = OUT / 'import-plan-v2.json'

# Zero-based rows in the captured 32-page index. Decisions apply to this exact
# extraction only; titles, pages and hashes are pinned in the delivery plan.
SPECIAL_SELECTED = {136,138,139,140,143,144,146,148,149,159,160,161,162,163,
                    164,165,167,168,169,170,171,172,174,176,178,183,188,191}
DUPLICATE_PUBLICATIONS = {65:64, 91:90, 137:58, 145:144, 150:149}
MEDIUM_EXCLUDED = {
    182:'Pottery exhibition', 186:'Photographic exhibition',
    187:'Sculpture exhibition', 193:'Porcelain/manufactories exhibition',
    196:'Sculpture groups by Ludwig Cauer',
}
SPECIFIC_HOLDS = {
    56:'Likely same event as existing 1883 Salon de Berlin, Charlottenburg (2816c0fa-13f4-5f81-a7bd-c1c9f663e0f1); hold pending original catalogue reconciliation.',
    97:'Possible section of the 1926 Great Berlin exhibition; do not count separately without event-identity evidence.',
    166:'Architecture exhibition: drawings versus models/photographs unresolved.',
    179:'Poelzig architecture exhibition: physical media unresolved.',
}
PEOPLE = {
    136:[('Adolph Menzel','Adolph Menzel')],
    138:[('Arnold Böcklin','Arnold Böcklin')],
    139:[('Paul Meyerheim',None)],
    140:[('Ludwig Knaus','Ludwig Knaus')],
    159:[('Josef Scheurenberg',None),('Karl Köpping','Karl Köpping')],
    162:[('Max Liebermann','Max Liebermann')],
    164:[('Karl Blechen','Carl Blechen')],
    165:[('Lovis Corinth','Lovis Corinth')],
    167:[('Daniel Chodowiecki','Daniel Chodowiecki')],
    168:[('Max Liebermann','Max Liebermann')],
    169:[('Hans Thoma','Hans Thoma')],
    170:[('Albrecht Dürer','Albrecht Dürer')],
    172:[('Max Slevogt','Max Slevogt')],
    174:[('Wilhelm Leibl','Wilhelm Leibl')],
    176:[('Rembrandt','Rembrandt van Rijn')],
    183:[('Adolph Menzel','Adolph Menzel')],
    191:[('Werner Peiner','Werner Peiner')],
}
# Manually transcribed event dates, not publication/artist-lifetime dates.
DATES = {
    0:('1786-05-20',None),1:('1787-05-21',None),2:('1788-09-25',None),
    3:('1789-09-25',None),4:('1791-05-22',None),5:('1793-05-27',None),
    6:('1794-09-26',None),7:('1795-09-26',None),8:('1797-09-26',None),
    9:('1798-09-15',None),10:('1800-09-15',None),11:('1802-09-15',None),
    12:('1804-10-01',None),13:('1806-09-22',None),14:('1808-05-29',None),
    15:('1810-09-23',None),16:('1812-09-20',None),17:('1814-10-09',None),
    18:('1815-10-04',None),19:('1816-09-22',None),20:('1818-09-27',None),
    21:('1820-09-24',None),22:('1822-09-22',None),23:('1824-09-26',None),
    24:('1826-09-24',None),25:('1828-09-21',None),26:('1830-09-19',None),
    27:('1832-09-16',None),28:('1834-09-14',None),29:('1836-09-18',None),
    30:('1838-09-16',None),31:('1839-09-15',None),32:('1840-09-20',None),
    33:('1842-09-18',None),34:('1844-09-15','1844-11-17'),
    35:('1846-09-01','1846-11-01'),37:('1850-03-31','1850-06-02'),
    38:('1852-09-01','1852-10-31'),39:('1854-09-01','1854-10-31'),
    40:('1856-09-01','1856-10-31'),50:('1876-09-06','1876-11-05'),
    51:('1877-09-02','1877-10-28'),52:('1878-09-01','1878-10-27'),
    53:('1879-08-31','1879-11-02'),54:('1880-08-29','1880-10-31'),
    55:('1881-09-04','1881-11-06'),57:('1884-08-24','1884-10-19'),
    61:('1889-09-01','1889-10-27'),62:('1890-06-29','1890-10-05'),
    63:('1892-05-15','1892-07-31'),64:('1893-05-14','1893-09-17'),
    105:('1940-12-04','1941-01-31'),106:('1942-05-31','1942-08-31'),
    138:('1897-12-02','1898-01-16'),139:('1900-04-01','1900-05-13'),
    140:('1900-01-12','1900-02-25'),143:('1908-10-18','1908-11-29'),
    144:('1908-01-26','1908-02-23'),146:('1908-12-09','1909-01-10'),
    148:('1910-01-26','1910-03-06'),170:('1928-03-10','1928-04-09'),
    176:('1930-02-22','1930-04-06'),178:('1931-01-17','1931-02-28'),
}
MONTH_LABELS = {
    58:'Mai–Oktober 1886',59:'31. Juli–Mitte Oktober 1887',60:'15. Juli–Oktober 1888',
    149:'März–April 1910',159:'März–Mai 1915',160:'Februar–April 1916',
    161:'Mai–Juni 1917',163:'April–Mai 1920',165:'Februar–März 1926',
    168:'Juni–Juli 1927',171:'Januar–Februar 1928',172:'Oktober–November 1928',
    174:'März–Mai 1929 (tour; venue dates unresolved)',
    183:'Februar–März 1935',188:'Frühjahr 1936',191:'Februar 1938',
}


def extract():
    receipt = c.load(OUT/'series-index.pdf.receipt.json')
    assert receipt['status'] == 200 and receipt['url'] == URL
    assert c.sha((OUT/'series-index.pdf').read_bytes()) == receipt['sha256']
    rows = []
    with pdfplumber.open(OUT/'series-index.pdf') as pdf:
        assert len(pdf.pages) == 32
        for i,page in enumerate(pdf.pages):
            starts = [v for v in page.extract_words() if v['text'] in list('ABCDEF')
                      and 45 < v['x0'] < 65 and v['top'] > 85]
            for j,a in enumerate(starts):
                top=a['top']-1
                bottom=starts[j+1]['top']-1 if j+1<len(starts) else 560
                def txt(x0,x1):
                    return (page.crop((x0,top,x1,bottom)).extract_text() or '').strip()
                rows.append(dict(index=len(rows),page=i+1,series=a['text'],year=txt(75,112),
                    title=txt(114,395),primary=txt(395,590),other=txt(590,805),bbox=[top,bottom]))
    assert len(rows) == 218
    assert rows == c.load(OUT/'extracted-rows.json'), 'Extraction differs from reviewed rows'
    assert all(re.fullmatch(r'\d{4}',r['year']) and r['title'] for r in rows)
    return rows, receipt


def links(row):
    result=[]
    for cell in ('primary','other'):
        text=re.sub(r'\s+','',row[cell])
        result.extend(re.findall(r'https?://.*?(?=https?://|$)',text))
    assert all('http' not in x[8:] for x in result)
    return result


def event_record(row, rows):
    i=row['index']; year=int(row['year']); series=row['series']
    original=' '.join(row['title'].split())
    if series=='A':
        title=f'Kunstausstellung der Königlichen Akademie der Künste ({year})'
        if i==18:title='Ausstellung zurückeroberter Gemälde und Kunstwerke (1815)'
        if i==58:title='Jubiläums-Ausstellung der Königlichen Akademie der Künste (1886)'
        series_label='Kunstausstellungen der Königlichen Akademie der Künste'
    elif series=='B':
        title=f'Große Berliner Kunstausstellung ({year})'
        series_label='Große Berliner Kunstausstellung'
    elif series=='C':
        title=('Frühjahrs-Ausstellung' if 'Frühjahr' in original else 'Herbst-Ausstellung')+f' der Preußischen Akademie der Künste ({year})'
        series_label='Frühjahrs- und Herbstausstellungen der Preußischen Akademie der Künste'
    else:
        title=original
        series_label='Sonderausstellungen der Akademie der Künste' if series=='D' else None
    start,end=DATES.get(i,(None,None))
    if start:assert dt.date.fromisoformat(start).year==year
    if end:assert dt.date.fromisoformat(start)<=dt.date.fromisoformat(end)
    display=(start+' – '+end if end else 'From '+start) if start else MONTH_LABELS.get(i,str(year))
    precision='day' if start else 'year'
    if i in MONTH_LABELS:precision='mixed' if i in (59,60,174,188) else 'month'
    if series=='C':
        month=re.search(r'(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)[ /–-]+(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)',original,re.I)
        if month:display=f'{month.group()} {year}';precision='month'
    venue=None;city='Berlin'
    # The series name does not prove a venue: 1917 explicitly took place in
    # Düsseldorf, and the 1918 row does not identify its city.
    if series=='A':venue='Akademie-Gebäude'
    if series=='D' and re.search(r'(?:in der|der Künste zu|Künste,) .*',original):
        venue='Akademie der Künste' if 'Akademie' in original else None
    if series=='A':
        if 'Marstall' in original:venue='Akademie der Künste über dem Königlichen Marstall, Neustadt'
        elif 'auf der Neustadt' in original:venue='Akademie-Gebäude auf der Neustadt'
        elif 'Linden' in original:venue='Akademie-Gebäude, Unter den Linden'+(' 38' if '38' in original else '')
        elif 'Museums-Insel' in original:venue='Provisorisches Ausstellungsgebäude auf der Museums-Insel'
        elif 'Cantianplatz' in original:venue='Provisorisches Ausstellungsgebäude auf dem Cantianplatz'
    # Explicit alternatives, case independent; no current-museum assignment.
    if re.search(r'Landes[ -]*ausstellungsgebäude',original,re.I):
        venue='Landes-Ausstellungsgebäude'+(' am Lehrter Bahnhof' if 'Lehrter' in original else '')
    if 'Bellevue' in original:venue='Schloss Bellevue'
    if i==88:venue='Kunstpalast';city='Düsseldorf'
    if i==89:city=None;venue=None
    if i==104:venue='Preußische Akademie der Künste'
    if i==105:venue='Haus der Kunst Berlin'
    if i==106:venue='Nationalgalerie'
    occurrences=[dict(venue=venue,city=city)]
    if i==174:
        occurrences=[dict(venue='Akademie der Künste',city='Berlin'),
            dict(venue='Wallraf-Richartz-Museum',city='Köln'),
            dict(venue='Galerie Matthiesen',city='Berlin')]
    source_rows=[row]+[rows[j] for j,parent in DUPLICATE_PUBLICATIONS.items() if parent==i]
    return dict(id=c.uid(f'{PROVIDER}/row/{i}'),index=i,title=title,year=year,
        endYear=int(end[:4]) if end else None,startDate=start,endDate=end,dateDisplay=display,
        datePrecision=precision,series=series_label,originalTitle=original,
        sourceRows=source_rows,occurrences=occurrences,people=PEOPLE.get(i,[]),
        issues=['Source is the institution archive’s bibliography, not a transcribed artwork checklist.',
            'Mixed-media exhibitions retained for pictorial content only; no sculpture or photographic entries imported.',
            'No artist presence, ownership, current display or complete checklist inferred.',
            'Listed catalogue links are evidence leads; their content has not been fetched. Heidelberg viewer access remains held.']+
            (['Touring exhibition counted once. Stop dates and artwork participation at each stop remain unresolved.'] if i==174 else [])+
            (['City is unknown in this index row; Berlin is part of the series title.'] if i==89 else [])+
            (['Catalogue includes registered/submitted works; acceptance and installation require separate checks.'] if i in (41,42,43) else []))


def plan():
    rows,receipt=extract();records=[];decisions=[]
    for row in rows:
        i=row['index'];s=row['series']
        if s=='E':action='excluded_non_event';reason='Academy chronicle volume, not a distinct exhibition.'
        elif i in MEDIUM_EXCLUDED:action='excluded_medium';reason=MEDIUM_EXCLUDED[i]
        elif i in DUPLICATE_PUBLICATIONS:action='additional_publication';reason=f'Same event as row {DUPLICATE_PUBLICATIONS[i]}; edition, section guide or related publication.'
        elif i in SPECIFIC_HOLDS:action='held';reason=SPECIFIC_HOLDS[i]
        elif s in ('A','B','C','F') or i in SPECIAL_SELECTED:
            action='new_event';reason='Documented historical pictorial or mixed fine-art exhibition; checklist work remains separate.'
            records.append(event_record(row,rows))
        else:action='held';reason='Special exhibition: pictorial scope, compound event identity or exact creator still needs original-catalogue review.'
        decisions.append(dict(index=i,page=row['page'],series=s,year=int(row['year']),title=row['title'],action=action,reason=reason))
    assert len(records)==163 and len({x['id'] for x in records})==163
    names=sorted({canonical for pairs in PEOPLE.values() for _,canonical in pairs if canonical})
    with c.connect() as db:
        artists=db.execute("SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE display_name=ANY(%s) AND status<>'archived' ORDER BY display_name",(names,)).fetchall()
        assert len(artists)==len(names) and {r['display_name'] for r in artists}==set(names)
        # Include archived records in duplicate checks, so an exclusion cannot
        # silently be reintroduced by a differently labelled source.
        existing=db.execute('SELECT id,title,start_year,status FROM exhibitions WHERE start_year BETWEEN 1786 AND 1943').fetchall()
        pairs={(e['start_year'],c.norm(e['title'])) for e in existing}
        assert not [(r['year'],r['title']) for r in records if (r['year'],c.norm(r['title'])) in pairs]
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE source_key=%s',(PROVIDER,)).fetchone()['n']==0
        before=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    byname={r['display_name']:r for r in artists}
    for r in records:
        r['people']=[dict(name=label,canonicalName=name,artistID=str(byname[name]['id']) if name else None) for label,name in r['people']]
        for person in r['people']:
            if person['canonicalName']:
                # Posthumous exhibitions are valid. Do not compare event dates
                # to artist death years as though they were artwork dates.
                assert byname[person['canonicalName']]['birth_year']<r['year']
    review=c.load(OUT/'german-existing-candidates.json')
    assert len(review)==9
    c.save(PLAN,dict(at=c.now(),batch=BATCH,records=records,decisions=decisions,
        receipt=receipt,sourceSHA256=receipt['sha256'],beforeActive=before,pinnedArtists=artists,
        existingGermanCandidates=review,existingReconciliation='Nine Berlin/German title/venue candidates reviewed. 1883 Charlottenburg row held as probable existing Salon de Berlin; 1893 Freie Berliner Kunstausstellung distinct from Große Berliner Kunstausstellung.',
        counts=dict(events=len(records),sourceRows=sum(len(r['sourceRows']) for r in records),
            occurrences=sum(len(r['occurrences']) for r in records),
            publications=sum(len(links(x)) or 1 for r in records for x in r['sourceRows']),
            participants=sum(len(r['people']) for r in records),
            linkedParticipants=sum(bool(p['artistID']) for r in records for p in r['people'])),
        decisionCounts=dict(collections.Counter(x['action'] for x in decisions)),
        visualReviewPages=[1,13,16,22,26,28],allTextRowsReviewed=True,
        mainCatalogueWrites=False,realLocalDatabaseWrites=False,newImages=0))
    print('Prepared',len(records),'events;',dict(collections.Counter(x['action'] for x in decisions)))


def apply():
    p=c.load(PLAN);assert p['counts']['events']==163
    assert c.sha((OUT/'series-index.pdf').read_bytes())==p['sourceSHA256']
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(BATCH,)).fetchone()['n']==0
        artists=db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY display_name FOR SHARE',([x['id'] for x in p['pinnedArtists']],)).fetchall()
        assert json.loads(json.dumps(artists,default=str))==p['pinnedArtists']
        current=db.execute('SELECT title,start_year FROM exhibitions WHERE start_year BETWEEN 1786 AND 1943').fetchall()
        pairs={(x['start_year'],c.norm(x['title'])) for x in current}
        assert not any((r['year'],c.norm(r['title'])) in pairs for r in p['records'])
        with db.pipeline():
            for r in p['records']:
                sid=c.uid(f"source/{PROVIDER}/{r['index']}")
                db.execute("INSERT INTO exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,series_label,status,import_batch)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','unknown',%s,'review',%s)",
                    (r['id'],r['title'],c.norm(r['title']),Jsonb([r['originalTitle']]),r['startDate'],r['endDate'],r['year'],r['endYear'],r['dateDisplay'],r['datePrecision'],
                     'Documented in the Akademie der Künste archive’s historical exhibition catalogue index. Event identity and original date/title/venue wording are preserved; no installed checklist is asserted.',r['series'],BATCH))
                for source_row in r['sourceRows']:
                    source_id=c.uid(f"source/{PROVIDER}/{source_row['index']}")
                    rc=p['receipt']
                    db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (source_id,r['id'],PROVIDER,str(source_row['index']),URL,rc['retrievedAt'],rc['path'],rc['sha256'],Jsonb(source_row),Jsonb(dict(operation=BATCH,issues=r['issues'],mainRow=r['index'],indexLinksFetched=False))))
                    for n,url in enumerate(links(source_row) or [URL+f"#page={source_row['page']}"]):
                        db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,publication_date_label,url,source_identifier,page_label,evidence)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (c.uid(f"publication/{PROVIDER}/{source_row['index']}/{n}"),r['id'],source_id,'other' if source_row['index'] in (65,137) else 'catalogue',
                             ' '.join(source_row['title'].split()),source_row['year'],url,url,str(source_row['page']),Jsonb(dict(indexURL=URL,indexPage=source_row['page'],indexSHA256=rc['sha256'],catalogueContentRetrieved=False,holdingClaim=False,currentDisplayClaim=False))))
                for n,o in enumerate(r['occurrences']):
                    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (c.uid(f"occurrence/{PROVIDER}/{r['index']}/{n}"),r['id'],sid,o['venue'],o['city'],'Germany','DE',None if r['index']==174 else r['startDate'],None if r['index']==174 else r['endDate'],None if r['index']==174 else r['dateDisplay'],Jsonb(dict(indexPage=r['sourceRows'][0]['page'],sourceOriginalTitle=r['originalTitle'],exactBuildingUnknown=o['venue'] in (None,'Akademie der Künste','Akademie-Gebäude'),stopDatesUnresolved=r['index']==174,holdingClaim=False,currentDisplayClaim=False))))
                for person in r['people']:
                    key=c.norm(person['name'])
                    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence)VALUES(%s,%s,%s,%s,%s,'Artist',%s,%s)",
                        (c.uid(f"participant/{PROVIDER}/{r['index']}/{key}"),r['id'],sid,person['artistID'],person['name'],key,Jsonb(dict(originalName=person['name'],canonicalName=person['canonicalName'],sourceTitle=r['originalTitle'],sourcePage=r['sourceRows'][0]['page'],basis='Named artist in exhibition title; original spelling preserved. No personal attendance or specific work inferred.'))))
            db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,claimed_start_year,claimed_end_year,inspected_start_year,inspected_end_year,research_state,details)VALUES(%s,%s,%s,1786,1943,1786,1943,'partial',%s)",
                (c.uid('coverage/'+BATCH),PROVIDER,URL,Jsonb(dict(indexRows=218,decisions=p['decisionCounts'],counts=p['counts'],checklistsTranscribed=0,worldwideComplete=False,viewerAccess='Heidelberg Anubis challenge: held, no bypass'))))
        actual=db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(BATCH,)).fetchone()['n'];assert actual==163
    c.save(OUT/'delivered.json',dict(at=c.now(),batch=BATCH,counts=p['counts'],decisions=p['decisionCounts'],planSHA256=c.sha(PLAN.read_bytes()),realLocalDatabaseWrites=False,mainCatalogueWrites=False,newImages=0))
    print('Committed',actual,'new historical events')


def verify():
    p=c.load(PLAN);ids=[r['id'] for r in p['records']]
    with c.connect() as db:
        counts=dict(events=db.execute('SELECT count(*) n FROM exhibitions WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n'])
        for key,table in [('sourceRows','exhibition_source_records'),('occurrences','exhibition_occurrences'),('publications','exhibition_publications'),('participants','exhibition_participants')]:
            counts[key]=db.execute(f'SELECT count(*) n FROM {table} WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
        counts['linkedParticipants']=db.execute('SELECT count(*) n FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[]) AND artist_id IS NOT NULL',(ids,)).fetchone()['n']
        assert counts==p['counts'],(counts,p['counts'])
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE id=ANY(%s::uuid[]) AND (status<>'review' OR start_year NOT BETWEEN 1600 AND 1989 OR end_year>1989)",(ids,)).fetchone()['n']==0
        assert db.execute('SELECT count(*) n FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
        active=db.execute("SELECT count(*) n,count(*) FILTER(WHERE start_year IS NULL) undated,count(*) FILTER(WHERE start_year<1600 OR start_year>1989 OR end_year>1989) outside FROM exhibitions WHERE status<>'archived'").fetchone()
        sample=db.execute('SELECT id,title,start_date,end_date,date_precision FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY start_year,id LIMIT 4',(ids,)).fetchall()
    c.save(OUT/'verified.json',dict(at=c.now(),counts=counts,activeExhibitions=active,samples=sample,mainCatalogueWrites=False,realLocalDatabaseWrites=False,artworkChecklistsComplete=False))
    print('Verified',counts,'active',active)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('plan','apply','verify'):
        raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
