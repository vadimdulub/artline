#!/usr/bin/env python3
"""Lawrence and Washington nineteenth-century exhibitions with exact object histories."""
import collections,json,re,sys,time
from concurrent.futures import ThreadPoolExecutor
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-lawrence-washington-nineteenth-century-20261012'
OUT=n.OUT.parent/'lawrence-washington-nineteenth-century';BACKUP=n.BACKUP.parent/'lawrence-washington-nineteenth-century'
# Source cohort index, historical venue label, city, optional securely matched institution.
SELECTED=[(0,"Messrs. Woodburn's Gallery",'London',None,'United Kingdom','GB'),(1,'The Lawrence Gallery','London',None,'United Kingdom','GB'),(2,'American Art-Union Gallery','New York',None,'United States','US'),(3,'Washington Art Association','Washington, D.C.',None,'United States','US')]


def plan():
    leads=c.load(OUT/'selected-leads.json')['candidates'];hist={r['index']:r for r in c.load(n.OUT/'prefix-discovery.json.gz')['records']};audit=c.load(n.OUT/'artwork-audit.json.gz');native=collections.defaultdict(set);works={w['id']:w for w in audit['artworks']}
    for x in audit['external']:native[x['external_id']].add(x['entity_id'])
    events=[];entries=[];held=[]
    for ix,venue,city,mid,country,code in SELECTED:
        g=leads[ix];assert venue in g['prefix'];title=g['prefix'].split(', '+venue)[0];key=str(ix);eid=c.uid(OP+'/event/'+key);source=c.uid(OP+'/source/'+key)
        ev=dict(id=eid,sourceID=source,occurrenceID=c.uid(OP+'/occurrence/'+key),title=title,year=g['year'],venue=venue,city=city,country=country,countryCode=code,institutionID=mid,lead=g);events.append(ev)
        for index in g['recordIndexes']:
            r=hist[index];o=r['object'];nid=r['objectID'];assert o['classification']in ['Print','Drawing','Painting']and o['isvirtual']=='0'
            if len(native[nid])!=1:held.append(dict(eventID=eid,history=r,reason='No unique existing native object match'));continue
            aid=next(iter(native[nid]));w=works[aid]
            if w['status']=='archived' or w['creation_year_end'] and w['creation_year_end']>1970:held.append(dict(eventID=eid,history=r,reason='Archived or creation date exceeds scope'));continue
            assert w['current_institution_id']==n.MID and w['accession_number']==o['accessionnum']and w['work_type']in ['print','drawing','painting']
            assert not w['creation_year_start']or w['creation_year_start']<=g['year']
            num=re.search(r'\bno\.\s*(\d+[a-z]?)',r['tail'])
            assert num or r['tail'].strip()in ['.',', no.',', no cat.',', no catalogue.',', (hors de catalogue).','(as "St. James the Less").'],r['tail']
            prior=next((e for e in entries if e['eventID']==eid and e['history']['objectID']==nid),None)
            if prior:
                assert prior['history']['text']==r['text'];prior.setdefault('duplicateSourceIndexes',[]).append(r['index']);continue
            entries.append(dict(id=c.uid(OP+'/entry/'+key+'/'+nid),sourceID=c.uid(OP+'/source/'+key+'/'+nid),eventID=eid,occurrenceID=ev['occurrenceID'],workBefore=w,history=r,number=num.group(1)if num else None))
    assert len({e['id']for e in entries})==len(entries)
    with c.connect()as db:
        ids=sorted({e['workBefore']['id']for e in entries});current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall());assert {w['id']:w for w in current}=={e['workBefore']['id']:e['workBefore']for e in entries}
        people=n.normal(db.execute("SELECT aa.*,a.display_name,a.status artist_status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) AND aa.attribution_role='primary'",(ids,)).fetchall())
        nearby=n.normal(db.execute('SELECT * FROM exhibitions WHERE start_year=ANY(%s) ORDER BY id',([e['year']for e in events],)).fetchall())
        assert not any(c.norm(x['title'])==c.norm(e['title'])and x['start_year']==e['year']for x in nearby for e in events)
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        count=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    participants={};creatorHolds=[]
    bywork=collections.defaultdict(list)
    for e in entries:bywork[e['workBefore']['id']].append(e)
    for person in people:
        for e in bywork[person['artwork_id']]:
            label=e['history']['object']['attribution']
            if person['artist_status']=='archived' or re.search(r'Century|Workshop|Studio|Attributed| after |^after | or |\(publisher\)',label)or c.norm(label)!=c.norm(person['display_name']):creatorHolds.append(dict(entryID=e['id'],label=label));continue
            key=(e['eventID'],person['artist_id']);participants.setdefault(key,dict(id=c.uid(OP+'/artist/'+key[0]+'/'+key[1]),eventID=key[0],artistID=key[1],name=person['display_name'],sourceID=e['sourceID']))
    p=dict(at=c.now(),pins=n.pins(),receipt=c.load(n.OUT/'source-receipt.json'),events=events,entries=entries,participants=list(participants.values()),held=held,creatorHolds=creatorHolds,nearby=nearby,beforeActive=count,duplicateReview='All existing 1836, 1853 and 1857 events reviewed; none matches selected shows. Lawrence fifth and sixth exhibitions remain distinct, not combined by same year and gallery. New York 1853 is distinct from Washington DC 1857 first annual. No exact days or current institution holdings inferred',counts=dict(newEvents=len(events),newEntries=len(entries),illustratedConnections=sum(bool(e['workBefore']['primary_media_id'])for e in entries),artistConnections=len(participants),heldHistories=len(held),newArtworks=0,newImages=0))
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(json.dumps(p['counts']))

def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['pins']==n.pins();rc=p['receipt']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
        expected={e['workBefore']['id']:e['workBefore']for e in p['entries']};current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(expected),)).fetchall());assert {w['id']:w for w in current}==expected
        for e in p['events']:assert not db.execute('SELECT 1 FROM exhibitions WHERE start_year=%s AND normalized_title=%s',(e['year'],c.norm(e['title']))).fetchone()
        base=dict(operation=OP,planSHA=c.sha((OUT/'plan.json.gz').read_bytes()),basis='Official NGA native object exhibition histories name the event, historical venue and year. Exact dates unknown.',currentDisplayClaim=False,holdingClaim=False,checklistComplete=False,mainCataloguePreserved=True)
        with db.pipeline():
            for e in p['events']:
                db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,'year','held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['year'],str(e['year']),base['basis'],OP))
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sourceID'],e['id'],OP,'event/'+e['id'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e),Jsonb(base)))
                db.execute("INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(e['occurrenceID'],e['id'],e['sourceID'],e['institutionID'],e['venue'],e['city'],e['country'],e['countryCode'],str(e['year']),Jsonb(base)))
            for e in p['entries']:
                r=e['history'];o=r['object'];evidence=base|dict(nativeObjectID=r['objectID'],accession=o['accessionnum'],originalHistory=r['text'],creatorLabel=o['attribution'],catalogueNumber=e['number'],groupNumberCanRepeat=True)
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sourceID'],e['eventID'],OP,e['eventID']+'/'+r['objectID'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(history=r,duplicateSourceIndexes=e.get('duplicateSourceIndexes',[]))),Jsonb(evidence)))
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],e['eventID'],e['sourceID'],e['occurrenceID'],e['workBefore']['id'],r['objectID'],e['number'],o['title'],o['attribution'],o['displaydate'],o['medium'],o['dimensions'],Jsonb(evidence),'Exact NGA native ID and accession with explicit object exhibition history. Repeated catalogue group numbers do not merge distinct native objects.'))
            for e in p['participants']:db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(e['id'],e['eventID'],e['sourceID'],e['artistID'],e['name'],Jsonb(base|dict(artistBasis='Unqualified current primary attribution agrees with source object creator.'))))
            db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,1836,1857,'partial',%s)",(c.uid(OP+'/coverage'),OP,n.URL,Jsonb(base|dict(counts=p['counts'],remaining='Exact dates, full catalogues, unmatched objects and remaining images; four selected nineteenth-century exhibitions only.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'],flush=True)

def verify():
    p=c.load(OUT/'plan.json.gz');expected={e['workBefore']['id']:e['workBefore']for e in p['entries']};paths=set();events=[]
    with c.connect()as db:
        assert {w['id']:w for w in n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall())}==expected
        for ev in p['events']:
            e=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(ev['id'],)).fetchone());assert e['start_year']==ev['year']and e['start_date']is None and e['end_date']is None and e['end_year']is None
            occurrence=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(ev['id'],)).fetchone());assert occurrence['country_code']==ev['countryCode'] and occurrence['city_label']==ev['city'] and occurrence['venue_label']==ev['venue']
            es=[x for x in p['entries']if x['eventID']==ev['id']];items=[];after=''
            while True:
                r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+ev['id']+'/entries',params=dict(limit=100,after=after),timeout=40);r.raise_for_status();d=r.json();items+=d['items'];after=d.get('nextCursor')or''
                if not after:break
            by={x['id']:x for x in items};assert len(items)==len(by)==len(es)
            for x in es:assert by[x['id']]['artworkId']==x['workBefore']['id']and bool(by[x['id']].get('image'))==bool(x['workBefore']['primary_media_id'])
            paths.update(x['image']for x in items if x.get('image'));events.append(dict(id=ev['id'],title=ev['title'],year=ev['year'],entries=len(items),illustrated=sum(bool(x.get('image'))for x in items)))
        totals=n.normal(db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+len(p['events'])
        assert db.execute('SELECT count(*) n FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',([e['id']for e in p['events']],)).fetchone()['n']==len(p['participants'])
    assert all(x.startswith('/assets/artworks/')for x in paths)
    def check(path):
        r=requests.head('https://artlines.org'+path,timeout=40);return dict(path=path,status=r.status_code,contentType=r.headers.get('content-type'))
    with ThreadPoolExecutor(max_workers=4)as pool:assets=list(pool.map(check,sorted(paths)))
    assert all(x['status']==200 and x['contentType'].startswith('image/')for x in assets)
    c.save(OUT/'assets.json',assets)
    result=dict(at=c.now(),counts=p['counts'],events=events,totals=totals,uniqueAssetsVerified=len(assets),allEntryLinksVerified=True,mainArtworkRecordsPreserved=True,realLocalDatabaseWrites=False,checklistsComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/lawrence-washington-nineteenth-century-delivery.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
