#!/usr/bin/env python3
"""Museum object histories for the Philadelphia 1937 Spanish painting show."""
import gzip,json,sys
from pathlib import Path
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
import historical_exhibitions_pma_archive_wave2_20261012 as pma
OP='historical-exhibitions-spanish-1937-20261012'
OUT=pma.OUT/'spanish-1937-links';BACKUP=pma.BACKUP/'spanish-1937-links'
AID='ae33301d-2af2-552e-a2e9-a0f7c4801565'

def plan():
    event=next(e for e in c.load(pma.OUT/'wave2-plan-v2.json')['events']if e['title']=='Masters of Spanish Painting')
    cap=c.load(pma.OUT.parent/'goulandris-veronica/source.json');assert 'Philadelphia, Museum of Art, Masters of Spanish Painting , 1937' in cap['text']
    rows=[r for r in c.load(n.OUT/'prefix-discovery.json.gz')['records']if r['year']==1937 and r['prefix']=='Spanish Paintings, Philadelphia Museum of Art'];assert len(rows)==3
    audit=c.load(n.OUT/'artwork-audit.json.gz');entries=[]
    with c.connect()as db:
        ev=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(event['id'],)).fetchone());assert ev['checklist_state']=='unknown'
        assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s',(event['id'],)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(event['id'],)).fetchone()
        for row in rows:
            ids={r['entity_id']for r in audit['external']if r['external_id']==row['objectID']};assert len(ids)==1
            w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(next(iter(ids)),)).fetchone());o=row['object'];assert w['accession_number']==o['accessionnum'] and w['current_institution_id']==n.MID and w['primary_media_id'] and w['work_type']=='painting' and w['status']!='archived'
            entries.append(dict(key='nga/'+row['objectID'],before=w,title=o['title'],creator=o['attribution'],date=o['displaydate'],medium=o['medium'],dimensions=o['dimensions'],payload=row,receipt=c.load(n.OUT/'source-receipt.json'),basis='NGA native object and accession match; Spanish Paintings at Philadelphia Museum of Art in 1937 is the independently archived Masters of Spanish Painting show. No other venue inferred.'))
        w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone());ext=n.normal(db.execute("SELECT * FROM external_identifiers WHERE entity_id=%s AND scheme='goulandris-object'",(AID,)).fetchall());assert len(ext)==1 and ext[0]['canonical_url']==cap['receipt']['url'] and ext[0]['external_id']=='el-greco-the-holy-face'
        assert w['dimensions_text']=='51 × 66 cm' and w['primary_media_id'] and w['work_type']=='painting'
        entries.append(dict(key='goulandris/el-greco-the-holy-face',before=w,title=w['title'],creator='Doménikos Theotokópoulos (El Greco)',date='Early 1580s',medium='Oil on canvas',dimensions='51 × 66 cm',payload=dict(sourceURL=cap['receipt']['url'],exhibitionHistory='Philadelphia, Museum of Art, Masters of Spanish Painting, 1937',sourceIdentifier=ext),receipt=cap['receipt'],basis='Exact museum native source ID and URL, title, date and dimensions. Museum explicitly names the 1937 exhibition. Current holdings are not inferred from the historical venue.'))
    result=dict(at=c.now(),event=event,eventBefore=ev,entries=entries,pins=n.pins(),counts=dict(newLinks=4,illustratedConnections=4,newEvents=0,newImages=0),mainCatalogueWrites=False,realLocalDatabaseWrites=False)
    c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])

def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['pins']==n.pins();event=p['event']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR UPDATE',(event['id'],)).fetchone())==p['eventBefore']
        assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s',(event['id'],)).fetchone()
        for e in p['entries']:
            assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s FOR SHARE',(e['before']['id'],)).fetchone())==e['before']
            rc=e['receipt'];assert c.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256'];sid=c.uid(OP+'/source/'+e['key']);ev=dict(operation=OP,basis=e['basis'],checklistComplete=False,mainCataloguePreserved=True,currentDisplayClaim=False,holdingClaim=False)
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,event['id'],OP,e['key'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['payload']),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(c.uid(OP+'/entry/'+e['key']),event['id'],sid,event['occurrenceID'],e['before']['id'],e['key'],e['title'],e['creator'],e['date'],e['medium'],e['dimensions'],Jsonb(ev),e['basis']))
        db.execute("UPDATE exhibitions SET checklist_state='partial',updated_at=now() WHERE id=%s",(event['id'],))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])

def verify():
    p=c.load(OUT/'plan.json.gz');eid=p['event']['id'];checks=[]
    with c.connect()as db:
        for e in p['entries']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(e['before']['id'],)).fetchone())==e['before']
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(eid,)).fetchone());assert event['checklist_state']=='partial'
        assert {k:v for k,v in event.items()if k not in ['updated_at','checklist_state']}=={k:v for k,v in p['eventBefore'].items()if k not in ['updated_at','checklist_state']}
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid;r=requests.get(api+'/entries',timeout=30);r.raise_for_status();items=r.json()['items'];assert len(items)==4
    assert {x['artworkId']for x in items}=={e['before']['id']for e in p['entries']}
    for x in items:
        assert x.get('image','').startswith('/assets/artworks/');r=requests.head('https://artlines.org'+x['image'],timeout=30);assert r.status_code==200 and r.headers.get('content-type','').startswith('image/');checks.append(dict(artworkID=x['artworkId'],image=x['image'],status=r.status_code))
    result=dict(at=c.now(),counts=p['counts'],eventURL='https://artlines.org/exhibitions/'+eid,checks=checks,mainArtworksPreserved=True,realLocalDatabaseWrites=False,checklistComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/spanish-1937-links.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
