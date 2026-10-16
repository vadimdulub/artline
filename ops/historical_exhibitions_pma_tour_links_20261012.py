#!/usr/bin/env python3
"""Selected exact NGA objects for existing Manet and Romantic Art tours."""
import collections,csv,json,re,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-pma-tour-links-20261012'
OUT=n.OUT.parent/'pma-tour-links';BACKUP=n.BACKUP.parent/'pma-tour-links'
MANET='e7f81764-f16c-50be-94a1-bd637396053a';ROMANTIC='0a681d9b-6b60-5939-be3c-6b7f74ebc104'
PHILLY='83cdd636-b3c3-5824-a7a0-a19c02769e8c'
OBJECTS=Path.home()/'Library/Application Support/Artline/source-metadata/million-catalogue-20261010/nga/objects.csv'

def plan():
    rows=[r for r in c.load(n.OUT/'histories.json.gz')['records']if ('Manet' in r['text'] and r['year']=='1966' or 'Romantic Art in Britain' in r['text'] and r['year']=='1968') and 'Philadelphia Museum of Art' in r['text']];assert len(rows)==15
    ids={r['objectid']for r in rows};objects={r['objectid']:r for r in csv.DictReader(OBJECTS.open())if r['objectid']in ids}
    audit=c.load(n.OUT/'artwork-audit.json.gz');native=collections.defaultdict(set)
    for e in audit['external']:native[e['external_id']].add(e['entity_id'])
    entries=[];held=[];snap={}
    with c.connect()as db:
        for eid in [MANET,ROMANTIC]:
            snap[eid]={k:n.normal(db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=%s ORDER BY id',(eid,)).fetchall())for k,t in [('event','exhibitions'),('entries','exhibition_entries'),('occurrences','exhibition_occurrences')]}
            assert len(snap[eid]['event'])==1 and snap[eid]['event'][0]['checklist_state']=='partial'
            assert len(snap[eid]['entries'])==2
            assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(eid,)).fetchone()
        for row in rows:
            nid=row['objectid'];o=objects[nid];eid=MANET if 'Manet' in row['text']else ROMANTIC
            reason=None
            if len(native[nid])!=1:reason='No unique existing canonical object for native ID.'
            elif int(o['endyear'])>snap[eid]['event'][0]['end_year']:reason='Object date extends beyond exhibition: edition/state or date conflict requires review.'
            if reason:held.append(dict(history=row,object=o,reason=reason));continue
            w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(next(iter(native[nid])),)).fetchone())
            assert w['status']!='archived'and w['current_institution_id']==n.MID and w['accession_number']==o['accessionnum']and w['primary_media_id']
            assert o['classification']in ['Painting','Drawing','Print']and o['isvirtual']=='0'and int(o['endyear'])<=1970
            assert w['id']not in {e['artwork_id']for e in snap[eid]['entries']}
            num=re.search(r'\bno\.? (\d+[a-z]?)',row['text']);assert num
            occurrence=PHILLY if '(Philadelphia only)'in row['text']else None
            if occurrence:assert any(x['id']==occurrence for x in snap[eid]['occurrences'])
            entries.append(dict(id=c.uid(OP+'/entry/'+nid),sourceID=c.uid(OP+'/source/'+nid),eventID=eid,occurrenceID=occurrence,number=num.group(1),history=row,object=o,workBefore=w))
    assert len(entries)==10 and len(held)==5
    p=dict(at=c.now(),pins=n.pins(),objectsSHA=c.sha(OBJECTS.read_bytes()),receipt=c.load(n.OUT/'source-receipt.json'),snapshots=snap,entries=entries,held=held,counts=dict(newLinks=10,illustratedConnections=10,newEvents=0,newArtworks=0,newImages=0,heldCandidates=5))
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(p['counts'])

def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['pins']==n.pins()and p['objectsSHA']==c.sha(OBJECTS.read_bytes());rc=p['receipt']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        for eid,snap in p['snapshots'].items():
            for k,t in [('event','exhibitions'),('entries','exhibition_entries'),('occurrences','exhibition_occurrences')]:assert n.normal(db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=%s ORDER BY id FOR SHARE',(eid,)).fetchall())==snap[k]
            assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(eid,)).fetchone()
        for e in p['entries']:
            w=e['workBefore'];o=e['object'];assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s FOR SHARE',(w['id'],)).fetchone())==w
            ev=dict(operation=OP,nativeObjectID=o['objectid'],accession=o['accessionnum'],originalHistory=e['history']['text'],sourceAttribution=o['attribution'],checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,venueScope='Philadelphia only'if e['occurrenceID']else'Tour-level history; individual venue participation not inferred',mainCataloguePreserved=True)
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sourceID'],e['eventID'],OP,o['objectid'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(history=e['history'],object=o)),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],e['eventID'],e['sourceID'],e['occurrenceID'],w['id'],o['objectid'],e['number'],o['title'],o['attribution'],o['displaydate'],o['medium'],o['dimensions'],Jsonb(ev),'Exact native NGA ID and accession; museum object history names matching tour venues, years and catalogue number. Venue-specific restriction retained where explicit.'))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])

def verify():
    p=c.load(OUT/'plan.json.gz');paths=[];results=[]
    with c.connect()as db:
        for eid,snap in p['snapshots'].items():
            assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(eid,)).fetchall())==snap['event']
            assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s ORDER BY id',(eid,)).fetchall())==snap['occurrences']
            es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(eid,)).fetchall());prior={x['id']for x in snap['entries']};assert [x for x in es if x['id']in prior]==snap['entries']
            added=[e for e in p['entries']if e['eventID']==eid]
            r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid+'/entries',params=dict(limit=100),timeout=30);r.raise_for_status();data=r.json();items={x['id']:x for x in data['items']};assert len(items)==len(prior)+len(added)and not data.get('nextCursor')
            for e in added:
                assert items[e['id']]['artworkId']==e['workBefore']['id'];paths.append(items[e['id']]['image'])
                assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(e['workBefore']['id'],)).fetchone())==e['workBefore']
                assert next(x for x in es if x['id']==e['id'])['occurrence_id']==e['occurrenceID']
            results.append(dict(eventID=eid,totalEntries=len(items),newIllustratedLinks=len(added)))
    assert all(x.startswith('/assets/artworks/')for x in paths)
    def check(path):
        r=requests.head('https://artlines.org'+path,timeout=30);return dict(path=path,status=r.status_code,contentType=r.headers.get('content-type'))
    with ThreadPoolExecutor(max_workers=3)as pool:assets=list(pool.map(check,paths))
    assert all(x['status']==200 and x['contentType'].startswith('image/')for x in assets)
    result=dict(at=c.now(),counts=p['counts'],events=results,assets=assets,mainArtworksPreserved=True,eventAndOccurrencesPreserved=True,existingEntriesPreserved=True,realLocalDatabaseWrites=False,checklistsComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/pma-tour-links.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
