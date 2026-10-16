#!/usr/bin/env python3
"""Selected explicit painting/print exhibition dates in PMA's archival inventory."""
import datetime as dt
import gzip
import json
import re
import sys
from pathlib import Path
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n

OP='historical-exhibitions-pma-archive-wave2-20261012'
OUT=n.OUT.parent/'philadelphia-museum-archive'
BACKUP=n.BACKUP.parent/'philadelphia-museum-archive-wave2'
URL='https://findingaids.library.upenn.edu/records/PMA_PMA.EXH'
MID='1f6f49e0-f986-57b3-8e9f-6aa4f6ae6dd7'
SELECTED=[110,120,124,130,157,173]
DATE=re.compile(r'(\d{4} [A-Z][a-z]+ \d{1,2})\s*[-–]\s*(\d{4} [A-Z][a-z]+ \d{1,2})')


def pins():
    p=OUT/'finding-aid-discovery.json.gz';v=c.load(p);rc=v['receipt']
    assert rc['status']==200 and c.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256']
    return dict(discovery=c.sha(p.read_bytes()),source=rc['sha256'])


def plan():
    discovery=c.load(OUT/'finding-aid-discovery.json.gz');by={r['elementID']:r for r in discovery['rows']};events=[]
    for num in SELECTED:
        row=by[f'collection-{num}-title'];text=row['text'];dates=DATE.findall(text)
        assert not row['proposed'] and len(dates)==1 and row['title']
        start,end=[dt.datetime.strptime(s,'%Y %B %d').date().isoformat() for s in dates[0]]
        assert start<=end and '1600'<=start[:4]<=end[:4]<='1989'
        assert row['title'] not in [e['title'] for e in events]
        events.append(dict(id=c.uid(OP+'/event/'+str(num)),sourceID=c.uid(OP+'/source/'+str(num)),occurrenceID=c.uid(OP+'/occurrence/'+str(num)),title=row['title'],start=start,end=end,row=row))
    with c.connect()as db:
        museum=n.normal(db.execute('SELECT id,name FROM institutions WHERE id=%s',(MID,)).fetchone());assert museum['name']=='Philadelphia Museum of Art'
        nearby=n.normal(db.execute("SELECT e.* FROM exhibitions e WHERE e.start_year BETWEEN 1937 AND 1955 AND (EXISTS(SELECT 1 FROM exhibition_occurrences o WHERE o.exhibition_id=e.id AND o.institution_id=%s) OR e.normalized_title=ANY(%s)) ORDER BY e.id",(MID,[c.norm(e['title'])for e in events])).fetchall())
        assert not any(r['normalized_title']==c.norm(e['title']) and r['start_year']==int(e['start'][:4])for r in nearby for e in events)
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        count=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    p=dict(at=c.now(),sourcePins=pins(),receipt=discovery['receipt'],events=events,museum=museum,nearby=nearby,beforeActive=count,
        counts=dict(events=len(events),entries=0,images=0,artists=0),
        scope='Individually selected explicit print/drawing/painting titles or painter movements, archival folders 101–180 only; Blake and Toulouse-Lautrec additionally corroborated by NGA native object histories. No photographs/sculpture/decorative arts; no automatic import of keyword matches.',
        duplicateReview='Selected title/year checks and all existing PMA-linked 1937–1955 events reviewed. Source element IDs represent separate dated exhibitions in this selection, not folder duplicates.',
        mainCatalogueWrites=False,realLocalDatabaseWrites=False)
    c.save(OUT/'wave2-plan-v2.json',p);c.save(BACKUP/'preimage-v2.json',p);print(json.dumps(p['counts']))
    print(json.dumps([dict(title=e['title'],start=e['start'],end=e['end'])for e in events]))


def apply():
    p=c.load(OUT/'wave2-plan-v2.json');assert p==c.load(BACKUP/'preimage-v2.json')and p['sourcePins']==pins();rc=p['receipt']
    ev=dict(operation=OP,planSHA256=c.sha((OUT/'wave2-plan-v2.json').read_bytes()),basis='Institutional Director exhibition archive inventory explicitly states exhibition dates inside parentheses; trailing folder dates are not used.',
        catalogueContentsRead=False,checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,sourceOwner='Philadelphia Museum of Art Archives',institutionEditorialConfidence=0.98)
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
        for e in p['events']:
            assert not db.execute('SELECT 1 FROM exhibitions WHERE id=%s OR (start_year=%s AND normalized_title=%s)',(e['id'],int(e['start'][:4]),c.norm(e['title']))).fetchone()
            db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'day','held',%s,'physical','unknown','review',%s)",
                (e['id'],e['title'],c.norm(e['title']),e['start'],e['end'],int(e['start'][:4]),int(e['end'][:4]),e['start']+' – '+e['end'],ev['basis'],OP))
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (e['sourceID'],e['id'],OP,e['row']['elementID'],URL+'#'+e['row']['elementID'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['row']),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,'Philadelphia Museum of Art','Philadelphia','United States','US',%s,%s,%s,%s)",
                (e['occurrenceID'],e['id'],e['sourceID'],MID,e['start'],e['end'],e['start']+' – '+e['end'],Jsonb(ev|dict(venueLabelBasis='Current institutional name for the archive-owning museum; historical building and room not inferred.'))))
        db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,%s,1937,1955,'partial',%s)",
            (c.uid(OP+'/coverage'),MID,OP,URL,Jsonb(ev|dict(counts=p['counts'],selectedSourceElements=[e['row']['elementID']for e in p['events']],remaining='Remaining folders, mixed or ambiguous media, compound events, full checklists and exact object/image links.'))))
    c.save(OUT/'wave2-delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])


def verify():
    p=c.load(OUT/'wave2-plan-v2.json');api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'
    with c.connect()as db:
        for e in p['events']:
            r=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(e['id'],)).fetchone())
            assert(r['title'],r['start_date'],r['end_date'],r['status'])==(e['title'],e['start'],e['end'],'review')
            assert db.execute('SELECT count(*) n FROM exhibition_entries WHERE exhibition_id=%s',(e['id'],)).fetchone()['n']==0
            response=requests.get(api+e['id'],timeout=30);response.raise_for_status();d=response.json();assert d['entryCount']==0 and d['id']==e['id']
        totals=n.normal(db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+len(p['events'])
    result=dict(at=c.now(),counts=p['counts'],totals=totals,allEventDetailsAPIVerified=True,mainCatalogueWrites=False,realLocalDatabaseWrites=False,checklistsComplete=False,evidenceDirectory=str(OUT))
    c.save(OUT/'wave2-verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/pma-archive-wave2-delivery.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
