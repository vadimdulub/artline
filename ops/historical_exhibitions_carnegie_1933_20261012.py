#!/usr/bin/env python3
"""Original periodical dates and exact NGA objects for Carnegie's 1933 show."""
import collections
import gzip
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from psycopg.types.json import Jsonb
import requests
import historical_exhibitions_nga_histories_20261012 as n
import exhibitions_common as c

OP='historical-exhibitions-carnegie-1933-20261012'
OUT=n.OUT.parent/'carnegie-1933'
BACKUP=n.BACKUP.parent/'carnegie-1933'
EID=c.uid(OP+'/event');OID=c.uid(OP+'/occurrence');SID=c.uid(OP+'/event-source')
TITLE='An Exhibition of Prints from the Collection of Lessing J. Rosenwald'
MID='bc6e479e-2d28-526a-bf46-c78f5e73308a'
LIFETIME_RANGES={'6828':('Will Dyson','1880','1938'),'10714':('Salomon van Abbé','1883','1955')}


def pins():
    result=n.pins()
    result['reviewed-event-lead.json.gz']=c.sha((OUT/'reviewed-event-lead.json.gz').read_bytes())
    for file in ['cmu-april11','cmu-april19','cmu-may17']:
        rc=c.load(OUT/(file+'-receipt.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert c.sha(raw)==rc['sha256']
        result[file]=rc['sha256']
    return result


def plan():
    review=c.load(OUT/'reviewed-event-lead.json.gz');audit=c.load(n.OUT/'artwork-audit.json.gz')
    native=collections.defaultdict(set);works={r['id']:r for r in audit['artworks']}
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    entries=[];held=[]
    for row in review['sourceObjectRows']:
        obj=row['object'];nid=row['objectID'];assert row['prefix']==review['sourceTitlePrefix']and row['year']==1933
        assert obj['classification']=='Print'and obj['isvirtual']=='0'
        if obj['endyear']and int(obj['endyear'])>1933:
            assert nid in LIFETIME_RANGES and not obj['displaydate']
            assert (obj['attribution'],obj['beginyear'],obj['endyear'])==LIFETIME_RANGES[nid]
        assert not n.NEGATIVE.search(row['text'])
        if len(native[nid])!=1:
            held.append(dict(objectID=nid,title=obj['title'],attribution=obj['attribution'],history=row['text'],reason='No unique existing native object match.'));continue
        aid=next(iter(native[nid]));work=works[aid]
        assert work['status']!='archived'and work['work_type']=='print'and work['accession_number']==obj['accessionnum']and work['current_institution_id']==n.MID
        assert not work['creation_year_start']or work['creation_year_start']<=1933
        assert not work['creation_year_end']or work['creation_year_end']<=1970
        number=re.search(r'\bno\.\s*(\d+[A-Za-z]?)\b',row['tail']);assert number
        entries.append(dict(id=c.uid(OP+'/entry/'+nid),artworkID=aid,objectID=nid,sourceID=c.uid(OP+'/object-source/'+nid),catalogueNumber=number.group(1),history=row['text'],historyIndex=row['index'],before=work,
            dateReview='Source display date is blank and numeric bounds coincide with the named artist lifetime. Creation date remains unknown; explicit 1933 object history is participation evidence, not a newly assigned creation year.'if nid in LIFETIME_RANGES else None,
            object={k:obj[k]for k in ['objectid','accessionnum','title','displaydate','beginyear','endyear','medium','dimensions','attribution','classification','parentid','isvirtual']}))
    assert len({e['artworkID']for e in entries})==len(entries)
    with c.connect()as db:
        ids=[e['artworkID']for e in entries]
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall());assert {r['id']:r for r in current}=={e['artworkID']:e['before']for e in entries}
        people=n.normal(db.execute('SELECT aa.*,a.display_name,a.status artist_status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,)).fetchall())
        nearby=n.normal(db.execute("SELECT e.* FROM exhibitions e WHERE e.start_year BETWEEN 1932 AND 1934 AND (strpos(lower(e.title),'rosenwald')>0 OR EXISTS(SELECT 1 FROM exhibition_occurrences o WHERE o.exhibition_id=e.id AND o.institution_id=%s)) ORDER BY e.id",(MID,)).fetchall());assert not nearby
        institution=n.normal(db.execute('SELECT id,name FROM institutions WHERE id=%s',(MID,)).fetchone());assert institution['name']=='Carnegie Museum of Art'
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        before=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    byart={e['artworkID']:e for e in entries};participants={};personholds=[]
    for link in people:
        if link['attribution_role']!='primary'or link['artist_status']=='archived':continue
        entry=byart[link['artwork_id']];label=entry['object']['attribution'].strip()
        if n.QUALIFIED.search(label):
            maker=re.split(r',?\s+after\s+',label,flags=re.I)[0].strip()
            if n.QUALIFIED.search(maker)or c.norm(maker)!=c.norm(link['display_name']):
                personholds.append(dict(artworkID=link['artwork_id'],artistID=link['artist_id'],label=label,canonical=link['display_name'],reason='Qualified source creator requires manual person reconciliation; exact artwork entry retains its label.'));continue
        key=link['artist_id']
        if key not in participants:participants[key]=dict(id=c.uid(OP+'/artist/'+key),artistID=key,name=link['display_name'],sourceID=entry['sourceID'],artworkIDs=[])
        participants[key]['artworkIDs'].append(entry['artworkID'])
    publications=[]
    for key,title,date in [('cmu-april11','Rosenwald Prints Now on Exhibit — The Carnegie Tartan','1933-04-11'),('cmu-april19','Faculty Bulletin, no. 13, series 1932–1933','1933-04-19'),('cmu-may17','Faculty Bulletin, no. 15, series 1932–1933','1933-05-17')]:
        publications.append(dict(key=key,id=c.uid(OP+'/publication/'+key),sourceID=c.uid(OP+'/source/'+key),title=title,date=date,page='1',receipt=c.load(OUT/(key+'-receipt.json'))))
    p=dict(at=c.now(),operation=OP,sourcePins=pins(),sourceReceipt=c.load(n.OUT/'source-receipt.json'),review=review,entries=entries,held=held,participants=list(participants.values()),participantHolds=personholds,publications=publications,
        beforeActive=before,institution=institution,duplicateReview='Full nearby Rosenwald title and Carnegie venue check has no existing candidate. The 1933 Chicago print display is a separately named and dated exhibition; no tour identity inferred.',
        checklistComplete=False,mainCatalogueWrites=False,newImages=0,realLocalDatabaseWrites=False)
    p['counts']=dict(newEvents=1,newEntries=len(entries),illustratedConnections=sum(bool(e['before']['primary_media_id'])for e in entries),participants=len(participants),publications=len(publications),sources=len(entries)+1+len(publications),heldObjects=len(held))
    c.save(OUT/'delivery-plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(json.dumps(p['counts']),flush=True)


def apply():
    p=c.load(OUT/'delivery-plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['sourcePins']==pins()
    rc=p['sourceReceipt'];base=dict(operation=OP,planSHA256=c.sha((OUT/'delivery-plan.json.gz').read_bytes()),historyCSV_SHA256=rc['sha256'],objectCSV_SHA256=p['sourcePins']['objectCSV'],checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,mainCatalogueMetadataPreserved=True)
    expected={e['artworkID']:e['before']for e in p['entries']}
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert not db.execute('SELECT 1 FROM exhibitions WHERE id=%s OR (start_year=1933 AND normalized_title=%s)',(EID,c.norm(TITLE))).fetchone()
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
        current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(expected),)).fetchall());assert {r['id']:r for r in current}==expected
        with db.pipeline():
            db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,'1933-04-06','1933-05-21',1933,1933,'6 April–21 May 1933','day','held',%s,'physical','partial','review',%s)",
                (EID,TITLE,c.norm(TITLE),'Contemporary Carnegie Tartan reports the exhibition opened 6 April and runs through 21 May; two Faculty Bulletins corroborate the closing date. Native museum object histories independently document participation.',OP))
            ev=base|dict(duplicateReview=p['duplicateReview'],descriptionBasis=p['review']['descriptionBasis'],sourceNumberReview=p['review']['sourceNumberReview'],originalPagesVisuallyReviewed=True)
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (SID,EID,OP,'event',n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(title=TITLE,sourceTitle=p['review']['sourceTitlePrefix'],year=1933,dateEvidence=p['review']['proofs'])),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,'Carnegie Institute','Pittsburgh','United States','US','1933-04-06','1933-05-21','6 April–21 May 1933',%s)",
                (OID,EID,SID,MID,Jsonb(ev|dict(location='Balcony of Sculpture Hall and four second-floor galleries',historicalVenueLabelPreserved=True,institutionIdentityBasis='Historical fine-art galleries of Carnegie Institute; current institution is Carnegie Museum of Art.',identityEditorialConfidence=0.98))))
            for pub in p['publications']:
                source=pub['receipt']
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (pub['sourceID'],EID,OP,pub['key'],source['url'],source['retrieved_at'],source['body_path'],source['sha256'],Jsonb(dict(title=pub['title'],date=pub['date'],page=1)),Jsonb(ev|dict(primaryPeriodical=True,checklistSource=False))))
                db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,publication_date_label,url,source_identifier,page_label,evidence) VALUES(%s,%s,%s,'other',%s,%s,%s,%s,'1',%s)",
                    (pub['id'],EID,pub['sourceID'],pub['title'],pub['date'],source['url'],pub['key'],Jsonb(ev|dict(kind='contemporary exhibition announcement/report',notAnExhibitionCatalogue=True))))
            for e in p['entries']:
                o=e['object'];ev=base|dict(nativeObjectID=e['objectID'],historyIndex=e['historyIndex'],originalHistory=e['history'],sourceAttribution=o['attribution'],dateReview=e['dateReview'],catalogueNumberShared=len(p['review']['groupedNumbers'].get(e['catalogueNumber'],[]))>1,sourceNumberReview=p['review']['sourceNumberReview'])
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (e['sourceID'],EID,OP,'object/'+e['objectID'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(object=o,history=e['history'])),Jsonb(ev)))
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",
                    (e['id'],EID,e['sourceID'],OID,e['artworkID'],e['objectID'],e['catalogueNumber'],o['title'],o['attribution'],o['displaydate'],o['medium'],o['dimensions'],Jsonb(ev),'Exact NGA native object, accession and institution match. Museum object history names this Carnegie exhibition and catalogue number; independent periodicals establish the event and dates. Series components retain distinct identities.'))
            for person in p['participants']:
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",
                    (person['id'],EID,person['sourceID'],person['artistID'],person['name'],Jsonb(base|dict(artworkIDs=person['artworkIDs'],basis='Existing primary artwork creators; after-model relationships retained separately from printmaker identity.'))))
            db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,%s,1933,1933,'partial',%s)",
                (c.uid(OP+'/coverage'),MID,OP,p['publications'][0]['receipt']['url'],Jsonb(base|dict(counts=p['counts'],remaining='Original catalogue contents, 39 unmatched native objects, 24 missing images, qualified-person holds, and wider institutional chronology.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],planSHA256=base['planSHA256']));print('Committed',json.dumps(p['counts']),flush=True)


def verify():
    p=c.load(OUT/'delivery-plan.json.gz');expected={e['artworkID']:e['before']for e in p['entries']}
    with c.connect()as db:
        now=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall());assert {r['id']:r for r in now}==expected
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone());assert(event['start_date'],event['end_date'],event['status'],event['checklist_state'])==('1933-04-06','1933-05-21','review','partial')
        es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchall());assert {(e['id'],e['artwork_id'],e['catalogue_number'])for e in es}=={(e['id'],e['artworkID'],e['catalogueNumber'])for e in p['entries']}
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()['n']==p['counts']['sources']
        people=db.execute('SELECT artist_id FROM exhibition_participants WHERE exhibition_id=%s',(EID,)).fetchall();assert {str(r['artist_id'])for r in people}=={r['artistID']for r in p['participants']}
        assert db.execute('SELECT count(*) n FROM exhibition_publications WHERE exhibition_id=%s',(EID,)).fetchone()['n']==3
        totals=n.normal(db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+1
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions';items=[];after='';pages=0
    while True:
        response=requests.get(api+'/'+EID+'/entries',params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json();items+=data['items'];after=data.get('nextCursor')or'';pages+=1
        if not after:break
        assert pages<10
    assert len(items)==len({r['id']for r in items})==len(p['entries']);by={r['id']:r for r in items}
    for e in p['entries']:assert by[e['id']]['artworkId']==e['artworkID']and bool(by[e['id']].get('image'))==bool(e['before']['primary_media_id'])
    c.save(OUT/'api-entries.json.gz',items)
    paths=sorted({r['image']for r in items if r.get('image')});assert all(s.startswith('/assets/artworks/')for s in paths)
    def check(path):
        response=requests.head('https://artlines.org'+path,timeout=40,allow_redirects=False);return dict(path=path,status=response.status_code,contentType=response.headers.get('content-type'))
    with ThreadPoolExecutor(max_workers=4)as pool:assets=list(pool.map(check,paths))
    c.save(OUT/'asset-checks.json',dict(at=c.now(),checks=assets));assert all(r['status']==200 and(r['contentType']or'').startswith('image/')for r in assets)
    for e in [p['entries'][0],p['entries'][-1]]:
        response=requests.get(api,params=dict(artwork=e['artworkID'],limit=100),timeout=40);response.raise_for_status();assert EID in {r['id']for r in response.json()['items']}
    response=requests.get(api+'/'+EID,timeout=40);response.raise_for_status();detail=response.json();assert detail['entryCount']==len(items)
    result=dict(at=c.now(),counts=p['counts'],totals=totals,eventURL='https://artlines.org/exhibitions/'+EID,apiPages=pages,allNewLinksAndImagesVerified=True,publicImageAssetsVerified=len(assets),reverseSamples=2,mainArtworkRecordsPreserved=True,newArtworks=0,newArtists=0,newImageFiles=0,realLocalDatabaseWrites=False,checklistComplete=False,evidenceDirectory=str(OUT))
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/carnegie-1933-delivery.json',result);print('Verified',json.dumps(result),flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply','verify']:raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
