#!/usr/bin/env python3
"""Selected icon checklist from the RSL public reading text layer; no main writes."""
import gzip
import json
import sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c

OP = 'historical-exhibitions-moscow-icons-1913-20261012'
OUT = Path.home() / 'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/moscow-icons-1913'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/moscow-icons-1913'
EID = c.uid(OP + '/event')
SID = c.uid(OP + '/bibliography')
OID = c.uid(OP + '/occurrence')
VIEWER = 'https://viewer.rsl.ru/rsl01003801904'
TITLE = 'Выставка древнерусского искусства, устроенная в 1913 году в ознаменование чествования 300-летия царствования дома Романовых'
PAGES = [7, 9, 11, 12, 13, 14, 19, 20]


def pins():
    files = ['public-viewer-info.json', 'selected-icon-leads.json'] + [f'public-reading-page-{p}.json' for p in PAGES]
    result = {f: c.sha((OUT / f).read_bytes()) for f in files}
    for f in files:
        item = c.load(OUT / f)
        if 'receipt' in item:
            rc = item['receipt']
            assert rc['status'] == 200
            assert c.sha(gzip.decompress(Path(rc['body_path']).read_bytes())) == rc['sha256']
    return result


def duplicate_candidates(db):
    return db.execute("SELECT id,title,start_year,end_year FROM exhibitions WHERE start_year BETWEEN 1912 AND 1914 AND (lower(title) LIKE '%%icon%%' OR lower(title) LIKE '%%russ%%' OR title LIKE '%%рус%%' OR lower(title) LIKE '%%moscow%%' OR title LIKE '%%икон%%' OR title LIKE '%%Моск%%' OR normalized_title=%s) ORDER BY id", (c.norm(TITLE),)).fetchall()


def plan():
    info = c.load(OUT / 'public-viewer-info.json')
    assert info['data']['description']['imprint'] == 'Москва, 1913'
    assert info['data']['accessLevel'] == 'free'
    leads = c.load(OUT / 'selected-icon-leads.json')['entries']
    assert [e['catalogueNumber'] for e in leads] == [str(i) for i in range(1, 12)]
    assert all(e['artworkID'] is None and e['creator'] is None for e in leads)
    entries = []
    for row in leads:
        row = dict(row)
        row['id'] = c.uid(OP + '/entry/' + row['catalogueNumber'])
        row['sourceID'] = c.uid(OP + '/page/' + str(row['digitalPage']))
        row['sourcePages'] = [14, 19] if row['catalogueNumber'] == '5' else [row['digitalPage']]
        # Anonymous historical owner is unknown, not an invented lender name.
        row['lender'] = None if row['catalogueNumber'] == '1' else row['historicalCollection'].split(';')[0]
        entries.append(row)
    with c.connect() as db:
        assert not duplicate_candidates(db)
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s', (OP,)).fetchone()
        before = db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    result = dict(at=c.now(),sourcePins=pins(),entries=entries,beforeActive=before,
        duplicateReview='Read-only 1912–1914 icon/Russian/Moscow title search and normalized-title check found no candidate. St Petersburg 1913 is a distinct event.',
        counts=dict(events=1,entries=11,linkedArtworks=0,images=0,artists=0,publications=1,sources=9),
        checklistComplete=False,mainCatalogueWrites=False,realLocalDatabaseWrites=False,
        remaining=['Rest of icon-painting checklist','Visual check of fractional dimensions and historical typography','Current object/version reconciliation and authentic images','Exact event dates and historical venue'])
    c.save(OUT / 'delivery-plan.json', result)
    c.save(BACKUP / 'preimage.json', result)
    print(json.dumps(result['counts']))


def apply():
    p = c.load(OUT / 'delivery-plan.json')
    assert p == c.load(BACKUP / 'preimage.json') and p['sourcePins'] == pins()
    info = c.load(OUT / 'public-viewer-info.json')
    base = dict(operation=OP,planSHA256=c.sha((OUT/'delivery-plan.json').read_bytes()),
        partialChecklist=True,visualScanReviewed=False,readingMethod='Selected public text-layer pages',
        fullPDFDownloaded=False,currentDisplayClaim=False,holdingClaim=False,
        dateCaution='1913 catalogue attributions retained as historical labels; not modern accepted creation dates.',
        unknowns=p['remaining'])
    with c.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert not duplicate_candidates(db)
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n'] == p['beforeActive']
        db.execute("INSERT INTO exhibitions(id,title,normalized_title,alternate_titles,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,1913,1913,'1913','year','held',%s,'physical','partial','review',%s)",
            (EID,TITLE,c.norm(TITLE),Jsonb(['Exhibition of Ancient Russian Art — Moscow 1913']),
             'Original 1913 Moscow exhibition catalogue, RSL bibliographic authority and numbered icon-painting section; exact opening and closing dates unresolved.',OP))
        def source(sid,key,rc,payload):
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (sid,EID,OP,key,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(payload),Jsonb(base)))
        source(SID,'bibliography',info['receipt'],dict(description=info['data']['description'],publicViewer=VIEWER,pageCount=262))
        for page in PAGES:
            reading = c.load(OUT / f'public-reading-page-{page}.json')
            source(c.uid(OP+'/page/'+str(page)), 'page/'+str(page),reading['receipt'],
                dict(digitalPage=page,readingMethod=reading['method'],text=reading['text']))
        db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,city_label,country_label,date_display,evidence) VALUES(%s,%s,%s,'Moscow','Russian Empire','1913',%s)",
            (OID,EID,SID,Jsonb(base|dict(venueUnresolved=True,institutionNotInferredFromCurrentHoldings=True))))
        db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,publication_date_label,url,source_identifier,page_label,evidence) VALUES(%s,%s,%s,'catalogue',%s,'1913',%s,'rsl01003801904','Digital pages 7, 9, 11–14, 19–20',%s)",
            (c.uid(OP+'/publication'),EID,SID,TITLE+' : [Каталог]',VIEWER,Jsonb(base)))
        for e in p['entries']:
            ev = base|dict(sourcePages=e['sourcePages'],historicalSchoolLabel=e['sourceSchoolLabel'],historicalCollection=e['historicalCollection'],catalogueNumber=e['catalogueNumber'],titleSpellingModernized=True,
                attributionNote='Individual creator not named. Catalogue school and period are historical assessments.',
                scopeBasis='Section I is icon painting; no manuscript, embroidery, textile, silver, copper or photograph entries included.')
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,source_artwork_id,catalogue_number,title_label,date_label,medium_label,lender_label,participation,source_page,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'Icon painting',%s,'catalogued',%s,%s,%s)",
                (e['id'],EID,e['sourceID'],OID,'rsl01003801904/section-I/'+e['catalogueNumber'],e['catalogueNumber'],e['titleModernized'],e['historicalCatalogueDate']+' (1913 catalogue)',e['lender'],
                 'Digital page(s) '+', '.join(map(str,e['sourcePages'])),Jsonb(ev),'Direct numbered entry in section I of the original exhibition catalogue. Surviving artwork identity unresolved; no canonical artwork or named artist asserted.'))
        db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,1913,1913,'partial',%s)",
            (c.uid(OP+'/coverage'),OP,VIEWER,Jsonb(base|dict(counts=p['counts'],catalogueNumbersRead='Section I, 1–11',remaining=p['remaining']))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],eventID=EID))
    print('Committed',json.dumps(p['counts']))


def verify():
    p = c.load(OUT/'delivery-plan.json')
    with c.connect() as db:
        e = db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone()
        assert (e['start_year'],e['end_year'],e['start_date'],e['end_date'],e['status'],e['checklist_state']) == (1913,1913,None,None,'review','partial')
        entries = db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchall()
        assert {r['catalogue_number'] for r in entries} == {str(i) for i in range(1,12)} and len(entries)==11
        assert all(r['artwork_id'] is None and r['creator_label'] is None and r['participation']=='catalogued' for r in entries)
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE exhibition_id=%s',(EID,)).fetchone()['n']==9
        assert db.execute('SELECT count(*) n FROM exhibition_participants WHERE exhibition_id=%s',(EID,)).fetchone()['n']==0
        totals = db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated FROM exhibitions WHERE status<>'archived'").fetchone()
        assert totals['active']==p['beforeActive']+1
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID
    r=requests.get(api+'/entries',params=dict(limit=100),timeout=30);r.raise_for_status();data=r.json()
    assert len(data['items'])==11 and not data.get('nextCursor')
    assert {r['id'] for r in data['items']}=={e['id'] for e in p['entries']}
    assert all(not r.get('artworkId') and not r.get('image') for r in data['items'])
    r=requests.get(api,timeout=30);r.raise_for_status();assert r.json()['entryCount']==11
    c.save(OUT/'verified-api.json',data)
    result=dict(at=c.now(),counts=p['counts'],totals=totals,eventURL='https://artlines.org/exhibitions/'+EID,allEntriesAPIVerified=True,
        checklistComplete=False,mainCatalogueWrites=False,realLocalDatabaseWrites=False,evidenceDirectory=str(OUT))
    c.save(OUT/'verified.json',result)
    c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/moscow-1913-delivery.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['plan','apply','verify']
    globals()[sys.argv[1]]()
