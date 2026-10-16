#!/usr/bin/env python3
"""Two exact NGA objects connected to independently dated PMA exhibitions."""
import collections
import json
import sys
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
import historical_exhibitions_pma_archive_wave3_20261012 as pma
OP='historical-exhibitions-pma-links-wave3-20261012'
OUT=pma.OUT/'object-links-wave3'
BACKUP=pma.BACKUP/'object-links'
SELECTED={'53126':dict(number='25',basis='Exact NGA native ID and accession; museum history explicitly names Gustave Courbet, Philadelphia Museum of Art and Boston Museum of Fine Arts, 1959–1960, no. 25. Philadelphia occurrence dates independently supplied by its archive; no Boston dates inferred.'),'165887':dict(number=None,basis='Exact NGA native ID and accession; same Mary Cassatt exhibition, Philadelphia museum and 1960 year. Museum history retains historical title Eddy in Red Velvet (Edward Buchanan Cassatt).')}


def plan():
    audit=c.load(n.OUT/'artwork-audit.json.gz');works={r['id']:r for r in audit['artworks']};native=collections.defaultdict(set)
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    candidates=c.load(pma.OUT/'wave3-object-history-leads.json.gz');entries=[]
    with c.connect()as db:
        for g in candidates['groups']:
            for row in g['candidateHistories']:
                nid=row['objectID']
                if nid not in SELECTED:continue
                assert len(native[nid])==1;aid=next(iter(native[nid]));work=works[aid];obj=row['object']
                assert work['accession_number']==obj['accessionnum'] and work['current_institution_id']==n.MID and work['status']!='archived'
                assert obj['classification']in ['Painting','Drawing'] and int(obj['endyear'])<=1970
                current=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(aid,)).fetchone());assert current==work
                event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(g['eventID'],)).fetchone());assert event['checklist_state']=='unknown'and event['start_year']==row['year']
                assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(event['id'],)).fetchone()
                assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s',(event['id'],)).fetchone()
                occ=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(event['id'],)).fetchall());assert len(occ)==1 and occ[0]['institution_id']==pma.MID
                people=n.normal(db.execute("SELECT aa.*,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=%s AND aa.attribution_role='primary' AND a.status<>'archived'",(aid,)).fetchall());assert len(people)==1 and c.norm(people[0]['display_name'])==c.norm(obj['attribution'])
                entries.append(dict(id=c.uid(OP+'/entry/'+nid),sourceID=c.uid(OP+'/source/'+nid),participantID=c.uid(OP+'/participant/'+nid),artworkID=aid,eventID=event['id'],occurrenceID=occ[0]['id'],objectID=nid,history=row,object=obj,workBefore=work,eventBefore=event,person=people[0],review=SELECTED[nid]))
        assert len(entries)==2
    result=dict(at=c.now(),sourcePins=n.pins(),receipt=c.load(n.OUT/'source-receipt.json'),candidateSHA=c.sha((pma.OUT/'wave3-object-history-leads.json.gz').read_bytes()),entries=entries,counts=dict(entries=2,illustratedConnections=2,artistConnections=2,newEvents=0,newArtworks=0,newImages=0),held='Remaining complete checklists and Boston tour occurrence dates; contemporaries print show remains a separate event.',mainCatalogueWrites=False,realLocalDatabaseWrites=False)
    c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(json.dumps(result['counts']))


def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['sourcePins']==n.pins()
    assert p['candidateSHA']==c.sha((pma.OUT/'wave3-object-history-leads.json.gz').read_bytes())
    rc=p['receipt']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        for e in p['entries']:
            assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s FOR SHARE',(e['artworkID'],)).fetchone())==e['workBefore']
            assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR UPDATE',(e['eventID'],)).fetchone())==e['eventBefore']
            assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s',(e['eventID'],)).fetchone()
            obj=e['object'];ev=dict(operation=OP,planSHA256=c.sha((OUT/'plan.json.gz').read_bytes()),exactNativeID=e['objectID'],accession=obj['accessionnum'],originalHistory=e['history']['text'],eventIdentityBasis=e['review']['basis'],artworkIdentityConfidence=1.0,checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,mainCataloguePreserved=True)
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sourceID'],e['eventID'],OP,e['objectID'],n.URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['history']),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],e['eventID'],e['sourceID'],e['occurrenceID'],e['artworkID'],e['objectID'],e['review']['number'],obj['title'],obj['attribution'],obj['displaydate'],obj['medium'],obj['dimensions'],Jsonb(ev),e['review']['basis']))
            db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(e['participantID'],e['eventID'],e['sourceID'],e['person']['artist_id'],e['person']['display_name'],Jsonb(ev)))
            db.execute("UPDATE exhibitions SET checklist_state='partial',updated_at=now() WHERE id=%s",(e['eventID'],))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])


def verify():
    p=c.load(OUT/'plan.json.gz');verified=[]
    with c.connect()as db:
        for e in p['entries']:
            assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(e['artworkID'],)).fetchone())==e['workBefore']
            event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(e['eventID'],)).fetchone());before=e['eventBefore'];assert {k:v for k,v in event.items()if k not in ['checklist_state','updated_at']}=={k:v for k,v in before.items()if k not in ['checklist_state','updated_at']}and event['checklist_state']=='partial'
            url='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['eventID'];r=requests.get(url+'/entries',timeout=30);r.raise_for_status();items=r.json()['items'];assert len(items)==1 and items[0]['artworkId']==e['artworkID']and items[0]['id']==e['id']
            assert bool(items[0].get('image'))==bool(e['workBefore']['primary_media_id'])
            if items[0].get('image'):
                a=requests.head('https://artlines.org'+items[0]['image'],timeout=30);assert a.status_code==200 and a.headers.get('content-type','').startswith('image/')
            r=requests.get(url,timeout=30);r.raise_for_status();assert r.json()['entryCount']==1
            verified.append(dict(eventID=e['eventID'],artworkID=e['artworkID'],illustrated=bool(items[0].get('image'))))
    result=dict(at=c.now(),counts=p['counts'],verified=verified,mainArtworkRecordsPreserved=True,realLocalDatabaseWrites=False,checklistsComplete=False,remaining=p['held'])
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/pma-object-links-wave3.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
