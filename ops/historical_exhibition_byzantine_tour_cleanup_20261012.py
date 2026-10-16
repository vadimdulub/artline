#!/usr/bin/env python3
"""Remove one truncated 1988–1990 tour from the pre-1990 catalogue."""
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup
import requests
import exhibitions_common as c

OUT = Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/byzantine-historical'
BACKUP = Path.home()/'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/byzantine-tour'
EID = '9cc2f92f-9789-569c-8fd2-83824c5c9dcd'
TABLES = ['exhibition_object_entries','exhibition_research_people','exhibition_research','exhibition_entries',
          'exhibition_publications','exhibition_participants','exhibition_occurrences','exhibition_source_records']


def normal(value):
    return json.loads(json.dumps(value, default=str))


def comparable(rows):
    return sorted(json.dumps(r, sort_keys=True, default=str) for r in rows)


def evidence():
    receipts = []
    for filename in ['walters-37-1187.html','cmapr3607.pdf','cmapr3607.txt']:
        path = OUT/filename; receipt = c.load(path.with_suffix(path.suffix+'.receipt.json'))
        assert receipt['status'] == 200 and c.sha(path.read_bytes()) == receipt['sha256']
        receipts.append(receipt)
    walters = BeautifulSoup((OUT/'walters-37-1187.html').read_bytes(),'html.parser').get_text(' ',strip=True)
    assert '1988-1990 Holy Image, Holy Space: Icons and Frescoes from Greece.' in walters
    assert all(v in walters for v in ['The Cleveland Museum of Art, Cleveland','Virginia Museum of Fine Arts, Richmond'])
    text = (OUT/'cmapr3607.txt').read_text()
    assert 'February 25-April 29, 1990' in text and 'U.S. tour' in text
    return receipts


def plan():
    receipts = evidence(); audit = c.load(OUT/'holy-image-cleanup-audit.json')
    assert audit['event']['id'] == EID and audit['event']['start_year'] == audit['event']['end_year'] == 1989
    assert audit['event']['parent_exhibition_id'] is None and not audit['children']
    assert all(not audit[t] for t in TABLES[:4])
    assert len(audit['exhibition_publications']) == 4 and len(audit['exhibition_participants']) == 1
    with c.connect() as db:
        assert normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone()) == audit['event']
        assert not db.execute('SELECT id FROM exhibitions WHERE parent_exhibition_id=%s',(EID,)).fetchall()
        for table in TABLES:
            assert comparable(db.execute(f'SELECT * FROM {table} WHERE exhibition_id=%s',(EID,)).fetchall()) == comparable(audit[table])
        total = db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    c.save(BACKUP/'preimage.json.gz', audit)
    p = dict(at=c.now(), exhibitionID=EID, title=audit['event']['title'], beforeActive=total,
        decision='remove_date', fullTourYears=[1988,1990], receipts=receipts,
        reason='The stored 1989 Cleveland stop is part of the single 1988–1990 tour independently documented by organizer Walters and Cleveland’s 1989 press release. The tour includes Detroit and Richmond in 1990; retaining a cropped stop as a standalone pre-1990 event misstates identity and scope.',
        pressReleasePDFPageVisuallyInspected=6, confirmedRetrospectiveSource='https://art.thewalters.org/object/37.1187/',
        dateDiscrepanciesPreserved='The 1988 library itinerary forecast a January 14 Detroit close. The later Cleveland release gives January 28 and a subsequent Richmond stop through April 29, 1990. VMFA search output gives February 26 opening rather than the release’s February 25; the direct VMFA PDF returned HTTP 202 and is held. No guessed full-tour day boundaries are imported.',
        counts={t:len(audit[t]) for t in TABLES}, backupPath=str(BACKUP/'preimage.json.gz'), backupSHA256=c.sha((BACKUP/'preimage.json.gz').read_bytes()),
        mainCatalogueWrites=False, realLocalDatabaseWrites=False)
    c.save(OUT/'holy-image-cleanup-plan.json',p)
    print('Prepared one source-confirmed 1988–1990 tour removal; no artwork or image deletion.',flush=True)


def apply():
    p = c.load(OUT/'holy-image-cleanup-plan.json'); audit = c.load(Path(p['backupPath']))
    assert evidence() == p['receipts'] and c.sha(Path(p['backupPath']).read_bytes()) == p['backupSHA256']
    counts = {}
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR UPDATE',(EID,)).fetchone()) == audit['event']
        assert not db.execute('SELECT id FROM exhibitions WHERE parent_exhibition_id=%s',(EID,)).fetchall()
        for table in TABLES:
            rows = db.execute(f'SELECT * FROM {table} WHERE exhibition_id=%s FOR UPDATE',(EID,)).fetchall()
            assert comparable(rows) == comparable(audit[table]), table
            counts[table] = db.execute(f'DELETE FROM {table} WHERE exhibition_id=%s',(EID,)).rowcount
            assert counts[table] == p['counts'][table]
        counts['exhibitions'] = db.execute('DELETE FROM exhibitions WHERE id=%s',(EID,)).rowcount
        assert counts['exhibitions'] == 1
        after = db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
        assert after == p['beforeActive']-1
    c.save(OUT/'holy-image-cleanup-delivered.json',dict(at=c.now(),counts=counts,activeExhibitions=after,
        planSHA256=c.sha((OUT/'holy-image-cleanup-plan.json').read_bytes()),mainCatalogueWrites=False,realLocalDatabaseWrites=False))
    print('Removed the truncated tour record and seven dependent rows; main artworks and images unchanged.',flush=True)


def verify():
    with c.connect() as db:
        assert db.execute('SELECT id FROM exhibitions WHERE id=%s',(EID,)).fetchone() is None
        for table in TABLES:
            assert not db.execute(f'SELECT exhibition_id FROM {table} WHERE exhibition_id=%s',(EID,)).fetchall()
        counts = db.execute("""SELECT count(*) active,
          count(*) FILTER(WHERE start_year BETWEEN 1600 AND 1989) dated_start_within_scope,
          count(*) FILTER(WHERE start_year BETWEEN 1600 AND 1989 AND end_year BETWEEN start_year AND 1989) fully_bounded_intervals,
          count(*) FILTER(WHERE start_year BETWEEN 1600 AND 1989 AND end_year IS NULL) within_scope_start_unknown_end,
          count(*) FILTER(WHERE start_year IS NULL) undated_legacy,
          count(*) FILTER(WHERE start_year<1600 OR start_year>=1990 OR end_year>=1990) outside_by_date_fields,
          min(start_year) earliest_dated,count(*) FILTER(WHERE event_state='held') confirmed_held
          FROM exhibitions WHERE status<>'archived'""").fetchone()
    response = requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID,timeout=30)
    assert response.status_code == 404
    listing = requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions',params={'limit':1},timeout=30)
    listing.raise_for_status(); assert listing.json()['total'] == counts['active']
    assert listing.json()['heldTotal'] == counts['confirmed_held']
    assert counts['active'] == 9180 and counts['confirmed_held'] == 8996 and counts['outside_by_date_fields'] == 0
    c.save(OUT/'holy-image-cleanup-verified.json',dict(at=c.now(),productionDateAudit=counts,removedDetailHTTP=404,publicHeldCount=listing.json()['heldTotal'],mainCatalogueWrites=False,realLocalDatabaseWrites=False))
    print('Verified removal, public 404, 9,180 active records and 8,996 confirmed-held records.',flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['plan','apply','verify']:
        raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
