#!/usr/bin/env python3
"""Exact NGA objects and museum bibliographic evidence for Chicago printmaking 1941."""
import collections
import re
import gzip
import json
import sys
import time
from pathlib import Path
from psycopg.types.json import Jsonb
import requests
import historical_exhibitions_nga_histories_20261012 as n
import exhibitions_common as c

OP='historical-exhibitions-first-century-chicago-1941-20261012'
OUT=n.OUT.parent/'first-century-chicago-1941'
BACKUP=n.BACKUP.parent/'first-century-chicago-1941'
EID=c.uid(OP+'/event');OID=c.uid(OP+'/occurrence');SID=c.uid(OP+'/event-source')
TITLE='The First Century of Printmaking 1400-1500'
MID='9e75033c-8e6b-464b-974b-d94fcc91c6a3'
LIBRARY='https://parismuseescollections.paris.fr/en/node/263980'


def plan():
    lead=next(g for g in c.load(n.OUT/'other-venue-next-cohort.json.gz')['candidates']if g['year']==1941 and g['prefix']==TITLE+', The Art Institute of Chicago')
    assert lead['year']==1941 and lead['prefix']==TITLE+', The Art Institute of Chicago'
    allrows={r['index']:r for r in c.load(n.OUT/'prefix-discovery.json.gz')['records']}
    rows=[allrows[ix]for ix in lead['recordIndexes']];audit=c.load(n.OUT/'artwork-audit.json.gz')
    native=collections.defaultdict(set);objects={r['id']:r for r in audit['artworks']}
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    entries={};held=[]
    for r in rows:
        obj=r['object'];nid=r['objectID']
        assert obj['classification']in ['Print','Drawing'] and obj['isvirtual']=='0'
        assert obj['accessionnum']
        number=re.search(r'no\.\s*(\d+[a-z]?)',r['tail']);assert number
        if len(native[nid])!=1:
            held.append(dict(objectID=nid,title=obj['title'],creator=obj['attribution'],history=r['text'],reason='No unique existing native object match; no placeholder created.'));continue
        aid=next(iter(native[nid]));work=objects[aid]
        assert work['status']!='archived'and work['current_institution_id']==n.MID and work['accession_number']==obj['accessionnum']
        assert work['work_type']in ['drawing','print']and(not work['creation_year_end']or work['creation_year_end']<=1970)
        assert not work['creation_year_start']or work['creation_year_start']<=1941
        if aid not in entries:
            entries[aid]=dict(id=c.uid(OP+'/entry/'+nid),artworkID=aid,objectID=nid,number=number.group(1),sourceID=c.uid(OP+'/object-source/'+nid),before=work,
                object={k:obj[k]for k in ['objectid','accessionnum','title','displaydate','beginyear','endyear','medium','dimensions','attribution','classification','parentid','isvirtual']},histories=[])
        assert entries[aid]['objectID']==nid
        entries[aid]['histories'].append(dict(index=r['index'],text=r['text'],year=r['year']))
    with c.connect()as db:
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(entries),)).fetchall())
        assert {r['id']:r for r in current}=={aid:e['before']for aid,e in entries.items()}
        people=n.normal(db.execute("SELECT aa.*,a.display_name,a.status artist_status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])",(list(entries),)).fetchall())
        nearby=n.normal(db.execute("SELECT e.* FROM exhibitions e WHERE e.start_year BETWEEN 1940 AND 1942 AND (e.title ~* 'first century|1400.?1500' OR EXISTS(SELECT 1 FROM exhibition_occurrences o WHERE o.exhibition_id=e.id AND o.institution_id=%s)) ORDER BY e.id",(MID,)).fetchall())
        venues=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY id',([r['id']for r in nearby],)).fetchall())
        assert not any('first century' in r['title'].lower() or '1400' in r['title'] for r in nearby)
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        before=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    participants={};participant_holds=[]
    for r in people:
        if r['attribution_role']!='primary'or r['artist_status']=='archived':continue
        e=entries[r['artwork_id']]
        if re.search(r'Century|Workshop|Studio|Attributed| after |^after | or ',e['object']['attribution']) or c.norm(r['display_name'])!=c.norm(e['object']['attribution']):
            participant_holds.append(dict(artworkID=r['artwork_id'],sourceAttribution=e['object']['attribution'],reason='Qualified studio/joint attribution preserved at object level. No additional named participation inferred.'));continue
        if r['artist_id']not in participants:participants[r['artist_id']]=dict(artistID=r['artist_id'],name=r['display_name'],sourceID=e['sourceID'],artworkIDs=[])
        participants[r['artist_id']]['artworkIDs'].append(r['artwork_id'])
    library=c.load(OUT/'library-capture.json');assert 'January 30-March 2, 1941' in library['text'] and '152 p.' in library['text']
    p=dict(at=c.now(),operation=OP,title=TITLE,id=EID,sourceReceipt=c.load(n.OUT/'source-receipt.json'),sourcePins=n.pins(),library=library,
        entries=list(entries.values()),participants=list(participants.values()),participantHolds=participant_holds,held=held,
        beforeActive=before,nearbyExistingEvents=nearby,nearbyVenues=venues,
        duplicateReview='Reviewed same-period Art Institute exhibitions and global First Century/1400–1500 titles; no equivalent event found. Paris Musees independently identifies the exact venue and 30 January–2 March 1941 dates. Full catalogue not read',
        checklistComplete=False,mainCatalogueWrites=False,newImages=0,realLocalDatabaseWrites=False)
    p['counts']=dict(newEvents=1,newEntries=len(entries),illustratedConnections=sum(bool(e['before']['primary_media_id'])for e in entries.values()),
        sourceHistories=len(rows),distinctNativeObjects=len({r['objectID']for r in rows}),heldObjects=len({e['objectID']for e in held}),
        participants=len(participants),sources=len(entries)+2,publications=1,types=dict(collections.Counter(e['before']['work_type']for e in entries.values())))
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(json.dumps(p['counts']),flush=True)


def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['sourcePins']==n.pins()
    receipt=p['sourceReceipt'];expected={e['artworkID']:e['before']for e in p['entries']}
    library=p['library']['receipt'];assert c.sha(gzip.decompress(Path(library['body_path']).read_bytes()))==library['sha256']
    base=dict(operation=OP,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),sourceCSV_SHA256=receipt['sha256'],objectCSV_SHA256=p['sourcePins']['objectCSV'],
        checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,mainCatalogueMetadataPreserved=True,
        participationBasis='NGA native object exhibition history explicitly identifies the 1941 Art Institute of Chicago exhibition; same-work native ID and accession match. Distinct print impressions retained.')
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert not db.execute('SELECT 1 FROM exhibitions WHERE id=%s OR (start_year=1941 AND normalized_title=%s)',(EID,c.norm(TITLE))).fetchone()
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(expected),)).fetchall());assert {r['id']:r for r in current}==expected
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
        with db.pipeline():
            db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,'1941-01-30','1941-03-02',1941,1941,'1941-01-30 – 1941-03-02','day','held',%s,'physical','partial','review',%s)",
                (EID,TITLE,c.norm(TITLE),'Official museum object histories identify the exhibition; Paris Musees catalogue record supplies exact Chicago exhibition dates.',OP))
            for sid,key,url,path,sha,payload in [(SID,'event',n.URL,receipt['body_path'],receipt['sha256'],dict(title=TITLE,year=1941,duplicateReview=p['duplicateReview'],histories=p['entries'][0]['histories']))]:
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (sid,EID,OP,key,url,receipt['retrieved_at'],path,sha,Jsonb(payload),Jsonb(base)))
            db.execute("INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,'library/263980',%s,%s,%s,%s,%s,%s)",(c.uid(OP+'/library-source'),EID,OP,LIBRARY,library['retrieved_at'],library['body_path'],library['sha256'],Jsonb(p['library']),Jsonb(base|dict(bibliographicRecordOnly=True))))
            db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,'Art Institute of Chicago','Chicago','United States','US','1941-01-30','1941-03-02','1941-01-30 – 1941-03-02',%s)",(OID,EID,SID,MID,Jsonb(base|dict(dateSource=LIBRARY))))
            db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,publication_date_label,url,source_identifier,page_label,evidence) VALUES(%s,%s,%s,'catalogue',%s,'1941',%s,'Paris Musees 263980','152 pages',%s)",(c.uid(OP+'/publication'),EID,c.uid(OP+'/library-source'),TITLE,LIBRARY,Jsonb(dict(bibliographicRecordOnly=True,catalogueContentsRead=False,editors=['Elizabeth Mongan','Carl O. Schniewind']))))
            for e in p['entries']:
                o=e['object'];ev=base|dict(nativeObjectID=e['objectID'],originalHistories=e['histories'],sourceAttribution=o['attribution'],catalogueNumber=e['number'])
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (e['sourceID'],EID,OP,'object/'+e['objectID'],n.URL,receipt['retrieved_at'],receipt['body_path'],receipt['sha256'],Jsonb(dict(object=o,histories=e['histories'])),Jsonb(ev)))
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",
                    (e['id'],EID,e['sourceID'],OID,e['artworkID'],e['objectID'],e['number'],o['title'],o['attribution'],o['displaydate'],o['medium'],o['dimensions'],Jsonb(ev),base['participationBasis']))
            for person in p['participants']:
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",
                    (c.uid(OP+'/artist/'+person['artistID']),EID,person['sourceID'],person['artistID'],person['name'],Jsonb(base|dict(artworkIDs=person['artworkIDs'],basis='Current unqualified primary attribution independently agrees with museum object metadata. Qualified studio and joint creator labels remain at entry level.'))))
            db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,1941,1941,'partial',%s)",
                (c.uid(OP+'/coverage'),OP,n.URL,Jsonb(base|dict(counts=p['counts'],remaining='Full original catalogue contents; unmatched native impressions; qualified and anonymous creator identities; remaining image gaps.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],planSHA256=base['planSHA256']));print('Committed',json.dumps(p['counts']),flush=True)


def verify():
    p=c.load(OUT/'plan.json.gz');expected={e['artworkID']:e['before']for e in p['entries']}
    with c.connect()as db:
        rows=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall());assert {r['id']:r for r in rows}==expected
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone());assert event['start_year']==1941 and event['end_year']==1941 and event['start_date']=='1941-01-30' and event['end_date']=='1941-03-02'
        assert event['event_state']=='held'and event['checklist_state']=='partial'and event['status']=='review'
        es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchall())
        assert {(e['id'],e['artwork_id'],e['participation'],e['catalogue_number'])for e in es}=={(e['id'],e['artworkID'],'exhibited',e['number'])for e in p['entries']}
        people=db.execute('SELECT artist_id FROM exhibition_participants WHERE exhibition_id=%s',(EID,)).fetchall();assert {str(r['artist_id'])for r in people}=={r['artistID']for r in p['participants']}
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()['n']==p['counts']['sources']
        assert db.execute('SELECT count(*) n FROM exhibition_publications WHERE exhibition_id=%s',(EID,)).fetchone()['n']==1
        totals=n.normal(db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+1
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions';items=[];after='';pages=0
    while True:
        response=requests.get(api+'/'+EID+'/entries',params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json();items+=data['items'];pages+=1;after=data.get('nextCursor')or''
        if not after:break
        assert pages<10
    assert len(items)==len({r['id']for r in items})==len(p['entries']);by={r['id']:r for r in items}
    for e in p['entries']:assert by[e['id']]['artworkId']==e['artworkID']and bool(by[e['id']].get('image'))==bool(e['before']['primary_media_id'])
    for e in [p['entries'][0],p['entries'][-1]]:
        response=requests.get(api,params=dict(artwork=e['artworkID'],limit=100),timeout=40);response.raise_for_status();assert EID in {r['id']for r in response.json()['items']}
    url='https://artlines.org/exhibitions/'+EID;response=requests.get(url,timeout=40);response.raise_for_status();assert TITLE in response.text
    result=dict(at=c.now(),counts=p['counts'],totals=totals,eventURL=url,allEntryLinksAndImagesVerified=True,apiPages=pages,reverseChecks=2,
        mainArtworkRecordsPreserved=True,newArtworks=0,newImages=0,newArtists=0,realLocalDatabaseWrites=False,checklistComplete=False,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),evidenceDirectory=str(OUT))
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/first-century-chicago-1941-delivery.json',result)
    print('Verified',json.dumps(result),flush=True)


def assets():
    from concurrent.futures import ThreadPoolExecutor
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID+'/entries'
    items=[];after=''
    while True:
        response=requests.get(api,params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json();items+=data['items'];after=data.get('nextCursor')or''
        if not after:break
    assert len(items)==c.load(OUT/'plan.json.gz')['counts']['newEntries']
    c.save(OUT/'api-entries.json.gz',items)
    paths=sorted({r['image']for r in items if r.get('image')});assert all(s.startswith('/assets/artworks/')for s in paths)
    def check(path):
        for attempt in range(3):
            try:
                response=requests.head('https://artlines.org'+path,timeout=40,allow_redirects=False)
                return dict(path=path,status=response.status_code,contentType=response.headers.get('content-type'),bytes=response.headers.get('content-length'))
            except requests.RequestException as exc:
                if attempt==2:return dict(path=path,status=None,contentType=None,error=type(exc).__name__)
                time.sleep(1+attempt)
    with ThreadPoolExecutor(max_workers=4)as pool:checked=list(pool.map(check,paths))
    result=dict(at=c.now(),distinctImages=len(paths),connections=len(items),checks=checked)
    c.save(OUT/'asset-head-checks.json',result)
    failures=[r for r in checked if r['status']!=200 or not(r['contentType']or'').startswith('image/')]
    assert not failures,failures
    print('Verified',len(paths),'distinct public artwork image assets for',len(items),'connections.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply','verify','assets']:raise SystemExit('Use plan, apply, verify or assets')
    globals()[sys.argv[1]]()
