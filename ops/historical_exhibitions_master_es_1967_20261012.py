#!/usr/bin/env python3
"""Exact NGA prints documented at the Master E.S. Philadelphia 1967 exhibition."""
import collections,json,re,sys
from concurrent.futures import ThreadPoolExecutor
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-master-es-1967-20261012'
OUT=n.OUT.parent/'master-es-philadelphia-1967'
BACKUP=n.BACKUP.parent/'master-es-philadelphia-1967'
EID='3f5a934e-5c8e-5067-941c-ad57021a838c'
OID='256acad7-d2f6-568b-a3e0-6de3916bf1d2'


def plan():
    rows=[r for r in c.load(n.OUT/'prefix-discovery.json.gz')['records']if r['year']==1967 and r['prefix']=='Master E.S.: Five Hundredth Anniversary Exhibition, Philadelphia Museum of Art']
    assert len(rows)==17
    audit=c.load(n.OUT/'artwork-audit.json.gz');native=collections.defaultdict(set);works={r['id']:r for r in audit['artworks']}
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    entries=[];held=[]
    for r in rows:
        nid=r['objectID'];obj=r['object']
        if len(native[nid])!=1:held.append(r);continue
        aid=next(iter(native[nid]));w=works[aid]
        assert w['status']!='archived' and w['current_institution_id']==n.MID and w['accession_number']==obj['accessionnum'] and w['primary_media_id']
        assert obj['classification']in ['Print'] and obj['isvirtual']=='0'and int(obj['endyear'])<=1970
        num=re.search(r'\bno\. (\d+)',r['text']);assert num
        entries.append(dict(id=c.uid(OP+'/entry/'+nid),sourceID=c.uid(OP+'/source/'+nid),artworkID=aid,objectID=nid,number=num.group(1),history=r,workBefore=w))
    assert len(entries)==15 and [r['objectID']for r in held]==['4536','46386']
    with c.connect()as db:
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())
        occ=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall())
        assert any(r['id']==OID and r['start_date']=='1967-09-05'and r['end_date']=='1967-10-03'for r in occ)
        assert event['start_year']==1967 and event['end_year']==1967 and event['checklist_state']=='unknown'
        existing=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert len(existing)==0 and not {r['artwork_id']for r in existing}&{e['artworkID']for e in entries}
        participants=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert not any(r['artist_id']for r in participants)
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(EID,)).fetchone()
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([e['artworkID']for e in entries],)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['workBefore']for e in entries}
    p=dict(at=c.now(),sourcePins=n.pins(),receipt=c.load(n.OUT/'source-receipt.json'),entries=entries,held=held,eventBefore=event,occurrencesBefore=occ,entriesBefore=existing,participantsBefore=participants,counts=dict(newEvents=0,newLinks=15,illustratedConnections=15,artistConnections=0,heldObjects=2),mainCatalogueWrites=False,realLocalDatabaseWrites=False)
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(json.dumps(p['counts']))


def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['sourcePins']==n.pins();rc=p['receipt']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR SHARE',(EID,)).fetchone())==p['eventBefore']
        for table,key in [('exhibition_entries','entriesBefore'),('exhibition_occurrences','occurrencesBefore'),('exhibition_participants','participantsBefore')]:assert n.normal(db.execute('SELECT * FROM '+table+' WHERE exhibition_id=%s ORDER BY id FOR SHARE',(EID,)).fetchall())==p[key]
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',([e['artworkID']for e in p['entries']],)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['workBefore']for e in p['entries']}
        for e in p['entries']:
            obj=e['history']['object'];ev=dict(operation=OP,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),nativeObjectID=e['objectID'],originalHistory=e['history']['text'],catalogueNumber=e['number'],sourceAttribution=obj['attribution'],checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,occurrenceBasis='Exact Philadelphia 1967 exhibition and catalogue numbers; archival dates independently confirmed. Individual creator labels retained, including followers and other makers.')
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sourceID'],EID,OP,e['objectID'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['history']),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],EID,e['sourceID'],OID,e['artworkID'],e['objectID'],e['number'],obj['title'],obj['attribution'],obj['displaydate'],obj['medium'],obj['dimensions'],Jsonb(ev),'Exact NGA native ID, accession and institution; museum object history identifies Philadelphia 1967 and catalogue number.'))
        db.execute("UPDATE exhibitions SET checklist_state='partial',updated_at=now() WHERE id=%s",(EID,))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])


def verify():
    p=c.load(OUT/'plan.json.gz')
    with c.connect()as db:
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone());assert event['checklist_state']=='partial';assert {k:v for k,v in event.items()if k not in ['checklist_state','updated_at']}=={k:v for k,v in p['eventBefore'].items()if k not in ['checklist_state','updated_at']}
        assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall())==p['occurrencesBefore']
        es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert len(es)==15
        assert [r for r in es if r['id']in {x['id']for x in p['entriesBefore']}]==p['entriesBefore']
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([e['artworkID']for e in p['entries']],)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['workBefore']for e in p['entries']}
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID;r=requests.get(api+'/entries',params=dict(limit=100),timeout=30);r.raise_for_status();data=r.json();items={r['id']:r for r in data['items']};assert len(items)==15 and not data.get('nextCursor')
    for e in p['entries']:assert items[e['id']]['artworkId']==e['artworkID']and items[e['id']].get('image')
    paths=sorted({items[e['id']]['image']for e in p['entries']});assert all(s.startswith('/assets/artworks/')for s in paths)
    def check(path):
        r=requests.head('https://artlines.org'+path,timeout=30);return dict(path=path,status=r.status_code,contentType=r.headers.get('content-type'))
    with ThreadPoolExecutor(max_workers=3)as pool:assets=list(pool.map(check,paths))
    assert all(r['status']==200 and r['contentType'].startswith('image/')for r in assets)
    c.save(OUT/'assets.json',assets)
    result=dict(at=c.now(),counts=p['counts'],eventURL='https://artlines.org/exhibitions/'+EID,totalEntries=15,allNewLinksAndAssetsVerified=True,eventDatesAndOccurrencesPreserved=True,mainArtworksPreserved=True,realLocalDatabaseWrites=False,checklistComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/master-es-1967-delivery.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
