#!/usr/bin/env python3
"""NGA impression-level evidence for the Free Library's 1931 Whistler show."""
import collections
import json
import sys
from pathlib import Path
from psycopg.types.json import Jsonb
import requests
import historical_exhibitions_nga_histories_20261012 as n
import exhibitions_common as c

OP='historical-exhibitions-whistler-philadelphia-1931-20261012'
OUT=n.OUT.parent/'whistler-philadelphia-1931'
BACKUP=n.BACKUP.parent/'whistler-philadelphia-1931'
EID=c.uid(OP+'/event');OID=c.uid(OP+'/occurrence');SID=c.uid(OP+'/event-source');PUBSID=c.uid(OP+'/library-source')
TITLE='Etchings, Lithographs, Original Drawings, and Autograph Letters by James A. McNeill Whistler'
LIBRARY='https://catalog.freelibrary.org/Record/150798'


def plan():
    lead=c.load(n.OUT/'other-venue-next-cohort.json.gz')['candidates'][0]
    assert lead['year']==1931 and lead['prefix']==TITLE+', The Free Library of Philadelphia'
    allrows={r['index']:r for r in c.load(n.OUT/'prefix-discovery.json.gz')['records']}
    rows=[allrows[ix]for ix in lead['recordIndexes']];audit=c.load(n.OUT/'artwork-audit.json.gz')
    native=collections.defaultdict(set);objects={r['id']:r for r in audit['artworks']}
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    entries={};held=[]
    for r in rows:
        obj=r['object'];nid=r['objectID']
        assert obj['classification']in ['Print','Drawing'] and obj['isvirtual']=='0'
        assert r['tail'].strip()=='.' and obj['accessionnum']
        if len(native[nid])!=1:
            held.append(dict(objectID=nid,title=obj['title'],creator=obj['attribution'],history=r['text'],reason='No unique existing native object match; no placeholder created.'));continue
        aid=next(iter(native[nid]));work=objects[aid]
        assert work['status']!='archived'and work['current_institution_id']==n.MID and work['accession_number']==obj['accessionnum']
        assert work['work_type']in ['drawing','print']and(not work['creation_year_end']or work['creation_year_end']<=1970)
        assert not work['creation_year_start']or work['creation_year_start']<=1931
        if aid not in entries:
            entries[aid]=dict(id=c.uid(OP+'/entry/'+nid),artworkID=aid,objectID=nid,sourceID=c.uid(OP+'/object-source/'+nid),before=work,
                object={k:obj[k]for k in ['objectid','accessionnum','title','displaydate','beginyear','endyear','medium','dimensions','attribution','classification','parentid','isvirtual']},histories=[])
        assert entries[aid]['objectID']==nid
        entries[aid]['histories'].append(dict(index=r['index'],text=r['text'],year=r['year']))
    with c.connect()as db:
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(entries),)).fetchall())
        assert {r['id']:r for r in current}=={aid:e['before']for aid,e in entries.items()}
        people=n.normal(db.execute("SELECT aa.*,a.display_name,a.status artist_status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])",(list(entries),)).fetchall())
        nearby=n.normal(db.execute("SELECT e.* FROM exhibitions e WHERE e.start_year BETWEEN 1928 AND 1934 AND (lower(e.title) LIKE '%whistler%' OR lower(e.title) LIKE '%rosenwald%' OR EXISTS(SELECT 1 FROM exhibition_occurrences o WHERE o.exhibition_id=e.id AND lower(o.venue_label) LIKE '%free library%')) ORDER BY e.id").fetchall())
        venues=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY id',([r['id']for r in nearby],)).fetchall())
        assert not any(r['start_year']==1931 and c.norm(r['title'])==c.norm(TITLE)for r in nearby)
        assert not any('free library'in(r['venue_label']or'').lower()for r in venues)
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        before=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    # After-Whistler is a source-model relationship, not uncertain authorship of Beatrix's two prints.
    participants={}
    for r in people:
        if r['attribution_role']!='primary'or r['artist_status']=='archived':continue
        assert r['display_name']in ['James Abbott McNeill Whistler','Beatrix Godwin Whistler'],r
        e=entries[r['artwork_id']]
        if r['display_name']=='Beatrix Godwin Whistler':assert e['objectID']in ['11283','11285']and e['object']['attribution']=='Beatrix Godwin Whistler, after James McNeill Whistler'
        else:assert e['object']['attribution']=='James McNeill Whistler'
        if r['artist_id']not in participants:participants[r['artist_id']]=dict(artistID=r['artist_id'],name=r['display_name'],sourceID=e['sourceID'],artworkIDs=[])
        participants[r['artist_id']]['artworkIDs'].append(r['artwork_id'])
    publication=dict(url=LIBRARY,catalogueRecord='150798',oclc='8881811',year=1931,publisher='The Free Library, Philadelphia',physicalPages=14,
        title='Etchings, lithographs, original drawings and autograph letters by James A. McNeill Whistler, 1834–1903, lent by Lessing J. Rosenwald, esq.',
        observationMethod='Public web search reader returned the Free Library bibliographic record before the direct retrieval returned HTTP 403; no subsequent retry or bypass.',
        observedAt=c.now(),readerReference='turn213search0',catalogueDescribesHeld1931Exhibition=True,fullChecklistRead=False,directAccessHeld=True)
    c.save(OUT/'library-index-evidence.json',publication)
    p=dict(at=c.now(),operation=OP,title=TITLE,id=EID,sourceReceipt=c.load(n.OUT/'source-receipt.json'),sourcePins=n.pins(),publication=publication,
        libraryEvidenceSHA256=c.sha((OUT/'library-index-evidence.json').read_bytes()),entries=list(entries.values()),participants=list(participants.values()),held=held,
        beforeActive=before,nearbyExistingEvents=nearby,nearbyVenues=venues,
        duplicateReview='Nearby 1932–1934 Whistler events are documented at Cleveland, Chicago and MoMA. No Free Library occurrence or 1931 Whistler event exists in this audit; library bibliography confirms the distinct 1931 Philadelphia event.',
        checklistComplete=False,mainCatalogueWrites=False,newImages=0,realLocalDatabaseWrites=False)
    p['counts']=dict(newEvents=1,newEntries=len(entries),illustratedConnections=sum(bool(e['before']['primary_media_id'])for e in entries.values()),
        sourceHistories=len(rows),distinctNativeObjects=len({r['objectID']for r in rows}),heldObjects=len({e['objectID']for e in held}),
        participants=len(participants),sources=len(entries)+2,publications=1,types=dict(collections.Counter(e['before']['work_type']for e in entries.values())))
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(json.dumps(p['counts']),flush=True)


def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['sourcePins']==n.pins()
    assert c.sha((OUT/'library-index-evidence.json').read_bytes())==p['libraryEvidenceSHA256']
    receipt=p['sourceReceipt'];expected={e['artworkID']:e['before']for e in p['entries']}
    base=dict(operation=OP,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),sourceCSV_SHA256=receipt['sha256'],objectCSV_SHA256=p['sourcePins']['objectCSV'],
        checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,mainCatalogueMetadataPreserved=True,
        participationBasis='NGA native object exhibition history explicitly identifies the 1931 Free Library of Philadelphia exhibition; same-work native ID and accession match. Distinct print impressions retained.')
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert not db.execute('SELECT 1 FROM exhibitions WHERE id=%s OR (start_year=1931 AND normalized_title=%s)',(EID,c.norm(TITLE))).fetchone()
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(expected),)).fetchall());assert {r['id']:r for r in current}==expected
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
        with db.pipeline():
            db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,1931,'1931','year','held',%s,'physical','partial','review',%s)",
                (EID,TITLE,c.norm(TITLE),'Museum object histories and the host library catalogue identify a held 1931 exhibition. Exact opening/closing dates remain unknown.',OP))
            for sid,key,url,path,sha,payload in [(SID,'event',n.URL,receipt['body_path'],receipt['sha256'],dict(title=TITLE,year=1931,duplicateReview=p['duplicateReview'],histories=p['entries'][0]['histories'])),
                (PUBSID,'library/150798',LIBRARY,str(OUT/'library-index-evidence.json'),p['libraryEvidenceSHA256'],p['publication'])]:
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (sid,EID,OP,key,url,receipt['retrieved_at']if sid==SID else p['publication']['observedAt'],path,sha,Jsonb(payload),Jsonb(base)))
            db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,'The Free Library of Philadelphia','Philadelphia','United States','US','1931',%s)",(OID,EID,SID,Jsonb(base|dict(exactDatesUnknown=True,institutionIdentityNotInvented=True))))
            for e in p['entries']:
                o=e['object'];ev=base|dict(nativeObjectID=e['objectID'],originalHistories=e['histories'],sourceAttribution=o['attribution'],catalogueNumberUnknown=True)
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (e['sourceID'],EID,OP,'object/'+e['objectID'],n.URL,receipt['retrieved_at'],receipt['body_path'],receipt['sha256'],Jsonb(dict(object=o,histories=e['histories'])),Jsonb(ev)))
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",
                    (e['id'],EID,e['sourceID'],OID,e['artworkID'],e['objectID'],o['title'],o['attribution'],o['displaydate'],o['medium'],o['dimensions'],Jsonb(ev),base['participationBasis']))
            for person in p['participants']:
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",
                    (c.uid(OP+'/artist/'+person['artistID']),EID,person['sourceID'],person['artistID'],person['name'],Jsonb(base|dict(artworkIDs=person['artworkIDs'],basis='Current source-backed primary attribution; Beatrix remains the creator of two after-Whistler prints, not reassigned to James.'))))
            pub=p['publication']
            db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence) VALUES(%s,%s,%s,'catalogue',%s,'Lessing J. Rosenwald','1931',%s,'OCLC 8881811','14 pages',%s)",
                (c.uid(OP+'/publication'),EID,PUBSID,pub['title'],LIBRARY,Jsonb(base|dict(bibliographicRecordOnly=True,fullChecklistRead=False,source=pub))))
            db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,1931,1931,'partial',%s)",
                (c.uid(OP+'/coverage'),OP,n.URL,Jsonb(base|dict(counts=p['counts'],remaining='Original 14-page catalogue contents and event dates; eleven unmatched native works; related archival correspondence. Library direct access held after HTTP 403.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],planSHA256=base['planSHA256']));print('Committed',json.dumps(p['counts']),flush=True)


def verify():
    p=c.load(OUT/'plan.json.gz');expected={e['artworkID']:e['before']for e in p['entries']}
    with c.connect()as db:
        rows=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall());assert {r['id']:r for r in rows}==expected
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone());assert event['start_year']==1931 and event['end_year']is None and event['start_date']is None and event['end_date']is None
        assert event['event_state']=='held'and event['checklist_state']=='partial'and event['status']=='review'
        es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchall())
        assert {(e['id'],e['artwork_id'],e['participation'],e['catalogue_number'])for e in es}=={(e['id'],e['artworkID'],'exhibited',None)for e in p['entries']}
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
    for e in [p['entries'][0],next(e for e in p['entries']if e['objectID']=='11283')]:
        response=requests.get(api,params=dict(artwork=e['artworkID'],limit=100),timeout=40);response.raise_for_status();assert EID in {r['id']for r in response.json()['items']}
    url='https://artlines.org/exhibitions/'+EID;response=requests.get(url,timeout=40);response.raise_for_status();assert TITLE in response.text
    result=dict(at=c.now(),counts=p['counts'],totals=totals,eventURL=url,allEntryLinksAndImagesVerified=True,apiPages=pages,reverseChecks=2,
        mainArtworkRecordsPreserved=True,newArtworks=0,newImages=0,newArtists=0,realLocalDatabaseWrites=False,checklistComplete=False,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),evidenceDirectory=str(OUT))
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/whistler-philadelphia-1931-delivery.json',result)
    print('Verified',json.dumps(result),flush=True)


def assets():
    from concurrent.futures import ThreadPoolExecutor
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID+'/entries'
    items=[];after=''
    while True:
        response=requests.get(api,params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json();items+=data['items'];after=data.get('nextCursor')or''
        if not after:break
    assert len(items)==390
    c.save(OUT/'api-entries.json.gz',items)
    paths=sorted({r['image']for r in items});assert all(s.startswith('/assets/artworks/')for s in paths)
    def check(path):
        response=requests.head('https://artlines.org'+path,timeout=40,allow_redirects=False)
        return dict(path=path,status=response.status_code,contentType=response.headers.get('content-type'),bytes=response.headers.get('content-length'))
    with ThreadPoolExecutor(max_workers=4)as pool:checked=list(pool.map(check,paths))
    result=dict(at=c.now(),distinctImages=len(paths),connections=len(items),checks=checked)
    c.save(OUT/'asset-head-checks.json',result)
    failures=[r for r in checked if r['status']!=200 or not(r['contentType']or'').startswith('image/')]
    assert not failures,failures
    print('Verified',len(paths),'distinct public artwork image assets for',len(items),'connections.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply','verify','assets']:raise SystemExit('Use plan, apply, verify or assets')
    globals()[sys.argv[1]]()
