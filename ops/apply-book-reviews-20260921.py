#!/usr/bin/env python3
"""Apply the pinned, sourced date reviews and highlight additions locally only."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from reviewed_book_dates import manifest, MANIFEST

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/revolution-discovery-20260921'
spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('revolution-discovery-20260921.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def apply():
    data=manifest();stamp=digest(data)
    receipt=RUN/'book-apply-receipt.json'
    if receipt.exists():
        assert json.loads(receipt.read_text())['manifestSha256']==stamp
        print('Preserving completed book reconciliation');return
    backup=json.loads((RUN/'local-backup.json').read_text())
    assert Path(backup['path']).stat().st_size==backup['bytes']
    pre=json.loads((RUN/'book-review-preimages.json').read_text())
    dates={x['bookId']:x for x in data['dates']};highlights={x['bookId']:x for x in data['highlights']}
    ids=sorted(dates.keys()|highlights.keys())
    for review in dates.values():
        assert review['fields']['startYear']<=review['fields']['endYear']
        assert review['fields']['dateSources'] and review['fields']['dateBasis']
        for source in review['sources']:
            proof=source['evidence'];assert hashlib.sha256((ROOT/proof['path']).read_bytes()).hexdigest()==proof['sha256']
            assert 'queue-it' not in proof.get('final_url','') and 'error400' not in proof.get('final_url','')
    core.save(core.BACKUP/'book-review-preimages.json',pre)
    with psycopg.connect(core.DSN,row_factory=dict_row) as db,db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(202609210101)')
        db.execute('LOCK TABLE book_records,book_discovery,book_creator_links,book_creators IN SHARE ROW EXCLUSIVE MODE')
        before=db.execute('select count(*) n,count(*) filter(where top100) highlights from book_discovery').fetchone()
        for id in ids:
            old=db.execute('select * from book_discovery where book_id=%s',(id,)).fetchone()
            expected=pre['discovery'][id]
            assert old and old['projection_checksum']==expected['projection_checksum'], 'Discovery changed; review again: '+id
            book=db.execute('select record,source_checksum,status from book_records where id=%s',(id,)).fetchone()
            assert book['status']=='review' and book['source_checksum']==old['book_checksum']
            if id in dates:
                review=dates[id];assert book['source_checksum']==review['expectedChecksum']
                record=copy.deepcopy(book['record']);record.update(review['fields'])
                creators=db.execute("select c.record||jsonb_build_object('credit',l.credit) record from book_creator_links l join book_creators c on c.id=l.creator_id where l.book_id=%s order by l.position",(id,)).fetchall()
                checksum=digest(dict(record,creators=[r['record'] for r in creators]))
                db.execute('update book_records set record=%s,source_checksum=%s where id=%s',(Jsonb(record),checksum,id))
                # The database invalidates the projection. Rebuild it from its
                # locked preimage: these reviews change dates only, not creators,
                # countries, languages or gender evidence.
                old['book_checksum']=checksum
                old['evidence']['dateReview']={'version':data['version'],'sources':review['fields']['dateSources'],'basis':review['fields']['dateBasis']}
            if id in highlights:
                old['top100']=True
                old['evidence']['editorial']={'version':data['version'],'basis':highlights[id]['basis'],'sourceUrl':highlights[id]['sourceUrl']}
            old['checked_at']=core.now();old['projection_checksum']=digest({k:v for k,v in old.items() if k!='projection_checksum'})
            columns=list(old)
            db.execute('INSERT INTO book_discovery ('+','.join(columns)+') VALUES ('+','.join(['%s']*len(columns))+') ON CONFLICT(book_id) DO UPDATE SET '+','.join(k+'=excluded.'+k for k in columns if k!='book_id'),tuple(Jsonb(old[k]) if k=='evidence' else old[k] for k in columns))
        after=db.execute('select count(*) n,count(*) filter(where top100) highlights from book_discovery').fetchone()
        assert after['n']==before['n'] and after['highlights']==before['highlights']+len(highlights)
        assert db.execute('select count(*) n from book_discovery d join book_records b on b.id=d.book_id where d.book_checksum<>b.source_checksum').fetchone()['n']==0
    core.save(receipt,{'at':core.now(),'manifestSha256':stamp,'datesCorrected':len(dates),'highlightsAdded':len(highlights),'before':before,'after':after,'status':'All records remain in review.'})
    print(json.dumps(json.loads(receipt.read_text()),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['apply']);parser.parse_args();apply()
