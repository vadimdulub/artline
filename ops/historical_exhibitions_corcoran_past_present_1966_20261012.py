#!/usr/bin/env python3
"""Exact NGA paintings added to an existing Corcoran 1966 exhibition."""
import collections,json,re,sys
from concurrent.futures import ThreadPoolExecutor
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-corcoran-past-present-1966-20261012'
OUT=n.OUT.parent/'corcoran-past-present-1966'
BACKUP=n.BACKUP.parent/'corcoran-past-present-1966'
EID='4a3456ba-71fc-51dc-87c6-2294fb139336'
OID='0b199dc4-8c17-5c6b-8078-0551745358db'


def plan():
    lead=c.load(n.OUT/'other-venue-next-cohort.json.gz')['candidates'][67];assert lead['year']==1966 and lead['prefix'].startswith('Past and Present: 250 Years')
    byindex={r['index']:r for r in c.load(n.OUT/'prefix-discovery.json.gz')['records']};rows=[byindex[ix]for ix in lead['recordIndexes']];assert len(rows)==35
    audit=c.load(n.OUT/'artwork-audit.json.gz');native=collections.defaultdict(set);works={r['id']:r for r in audit['artworks']}
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    entries=[];held=[]
    for r in rows:
        nid=r['objectID'];obj=r['object']
        if len(native[nid])!=1:held.append(r);continue
        aid=next(iter(native[nid]));w=works[aid]
        assert w['status']!='archived' and w['current_institution_id']==n.MID and w['accession_number']==obj['accessionnum']
        assert obj['classification']in ['Painting'] and obj['isvirtual']=='0'and int(obj['endyear'])<=1970
        num=None
        entries.append(dict(id=c.uid(OP+'/entry/'+nid),sourceID=c.uid(OP+'/source/'+nid),artworkID=aid,objectID=nid,number=None,history=r,workBefore=w))
    assert len(entries)==34 and len(held)==1
    with c.connect()as db:
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())
        occ=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall())
        assert any(r['id']==OID and r['start_date']=='1966-04-14'and r['end_date']=='1966-09-15'for r in occ)
        assert event['start_year']==1966 and event['end_year']==1966 and event['checklist_state']=='partial'
        existing=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert len(existing)==1 and not {r['artwork_id']for r in existing}&{e['artworkID']for e in entries}
        participants=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert not any(r['artist_id']for r in participants)
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(EID,)).fetchone()
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([e['artworkID']for e in entries],)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['workBefore']for e in entries}
        people=n.normal(db.execute("SELECT aa.artwork_id,a.id,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) AND aa.attribution_role='primary' AND a.status<>'archived'",([e['artworkID']for e in entries],)).fetchall())
    artists={}
    for person in people:
        entry=next(e for e in entries if e['artworkID']==person['artwork_id']);label=entry['history']['object']['attribution']
        if c.norm(person['display_name'])==c.norm(label)and not re.search(r'Attributed|after|Workshop|Studio| or ',label):artists.setdefault(person['id'],dict(id=person['id'],display_name=person['display_name'],sourceID=entry['sourceID']))
    p=dict(at=c.now(),sourcePins=n.pins(),receipt=c.load(n.OUT/'source-receipt.json'),entries=entries,held=held,eventBefore=event,occurrencesBefore=occ,entriesBefore=existing,participantsBefore=participants,artists=list(artists.values()),counts=dict(newEvents=0,newLinks=34,illustratedConnections=sum(bool(e['workBefore']['primary_media_id'])for e in entries),artistConnections=len(artists),heldObjects=1),mainCatalogueWrites=False,realLocalDatabaseWrites=False)
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(json.dumps(p['counts']))


def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['sourcePins']==n.pins();rc=p['receipt']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR SHARE',(EID,)).fetchone())==p['eventBefore']
        for table,key in [('exhibition_entries','entriesBefore'),('exhibition_occurrences','occurrencesBefore'),('exhibition_participants','participantsBefore')]:assert n.normal(db.execute('SELECT * FROM '+table+' WHERE exhibition_id=%s ORDER BY id FOR SHARE',(EID,)).fetchall())==p[key]
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',([e['artworkID']for e in p['entries']],)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['workBefore']for e in p['entries']}
        for e in p['entries']:
            obj=e['history']['object'];ev=dict(operation=OP,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),nativeObjectID=e['objectID'],originalHistory=e['history']['text'],catalogueNumber=e['number'],sourceAttribution=obj['attribution'],checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,occurrenceBasis='Exact Corcoran 1966 venue and title; current event dates independently established by existing museum source. Historical titles and unpublished/unnumbered checklist references preserved.')
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sourceID'],EID,OP,e['objectID'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['history']),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],EID,e['sourceID'],OID,e['artworkID'],e['objectID'],e['number'],obj['title'],obj['attribution'],obj['displaydate'],obj['medium'],obj['dimensions'],Jsonb(ev),'Exact NGA native ID, accession and institution; museum object history identifies Corcoran 1966; catalogue number remains unknown.'))
        for artist in p['artists']:
            db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/artist/'+artist['id']),EID,artist['sourceID'],artist['id'],artist['display_name'],Jsonb(dict(operation=OP,basis='Unqualified current primary creator agrees with museum source label.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])


def verify():
    p=c.load(OUT/'plan.json.gz')
    with c.connect()as db:
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())==p['eventBefore']
        assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall())==p['occurrencesBefore']
        people=n.normal(db.execute('SELECT artist_id FROM exhibition_participants WHERE exhibition_id=%s',(EID,)).fetchall());assert {x['artist_id']for x in people}=={x['id']for x in p['artists']}
        es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert len(es)==35
        assert [r for r in es if r['id']in {x['id']for x in p['entriesBefore']}]==p['entriesBefore']
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([e['artworkID']for e in p['entries']],)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['workBefore']for e in p['entries']}
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID;r=requests.get(api+'/entries',params=dict(limit=100),timeout=30);r.raise_for_status();data=r.json();items={r['id']:r for r in data['items']};assert len(items)==35 and not data.get('nextCursor')
    for e in p['entries']:assert items[e['id']]['artworkId']==e['artworkID']and bool(items[e['id']].get('image'))==bool(e['workBefore']['primary_media_id'])
    paths=sorted({items[e['id']]['image']for e in p['entries']if items[e['id']].get('image')});assert all(s.startswith('/assets/artworks/')for s in paths)
    def check(path):
        r=requests.head('https://artlines.org'+path,timeout=30);return dict(path=path,status=r.status_code,contentType=r.headers.get('content-type'))
    with ThreadPoolExecutor(max_workers=3)as pool:assets=list(pool.map(check,paths))
    assert all(r['status']==200 and r['contentType'].startswith('image/')for r in assets)
    c.save(OUT/'assets.json',assets)
    result=dict(at=c.now(),counts=p['counts'],eventURL='https://artlines.org/exhibitions/'+EID,totalEntries=35,allNewLinksAndAssetsVerified=True,eventAndOccurrencesPreserved=True,mainArtworksPreserved=True,realLocalDatabaseWrites=False,checklistComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/corcoran-past-present-1966-delivery.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
