#!/usr/bin/env python3
"""Reconcile Blake 1939 catalogue 155 with Cleveland's explicit object history."""
import gzip,json,sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-blake-matthew-20261012'
OUT=n.OUT.parent/'blake-philadelphia-1939'/'matthew-match'
BACKUP=n.BACKUP.parent/'blake-matthew-match'
EID='5c64ef50-18f0-5cf3-8a19-e86adf45c299'
AID='ed0304a4-f20c-40b3-b4c0-ea9bf9384e0d'
URL='https://openaccess-api.clevelandart.org/api/artworks/294155'
BASIS='Exact Cleveland native object 294155, accession 2017.4. Museum exhibition history explicitly names Philadelphia 1939, bibliography identifies catalogue no. 155, and provenance places the work with catalogue lender Mrs. William Emerson in 1893–1958.'

def plan():
    raw,rc=c.capture(URL);d=json.loads(raw)['data']
    assert d['accession_number']=='2017.4' and d['title']=='St. Matthew'
    assert any('Philadelphia' in e['description'] and '1939' in e['description'] for e in d['exhibitions']['legacy'])
    assert any('1939' in e['citation'] and '155' in (e['page_number'] or '') for e in d['citations'])
    assert any('Mrs. William Emerson' in e['description'] and e['date']=='1893-1958' for e in d['provenance'])
    with c.connect() as db:
        entry=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s AND catalogue_number=%s',(EID,'155')).fetchone())
        work=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone())
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())
        assert entry and entry['artwork_id'] is None and 'Emerson' in entry['lender_label']
        assert work['accession_number']=='2017.4' and work['primary_media_id'] and work['status']!='archived'
        assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_id=%s AND scheme='cleveland-object' AND external_id='294155'",(AID,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(EID,)).fetchone()
    p=dict(at=c.now(),receipt=rc,data=d,entryBefore=entry,artworkBefore=work,eventBefore=event,basis=BASIS)
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print('Planned one existing illustrated artwork match')

def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');rc=p['receipt']
    assert c.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256']
    sid=c.uid(OP+'/source/294155')
    with c.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=%s FOR UPDATE',(p['entryBefore']['id'],)).fetchone())==p['entryBefore']
        assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s FOR SHARE',(AID,)).fetchone())==p['artworkBefore']
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR SHARE',(EID,)).fetchone())==p['eventBefore']
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(EID,)).fetchone()
        ev=dict(operation=OP,basis=BASIS,mainCataloguePreserved=True,currentDisplayClaim=False,historicalLenderPreserved=True)
        db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,EID,OP,'294155',rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(p['data']),Jsonb(ev)))
        evidence=dict(p['entryBefore']['evidence']);evidence.update(canonicalObjectMatchPending=False,canonicalMatch=ev,canonicalMatchSourceRecordID=sid)
        db.execute('UPDATE exhibition_entries SET artwork_id=%s,evidence=%s,match_basis=%s WHERE id=%s',(AID,Jsonb(evidence),BASIS,p['entryBefore']['id']))
    c.save(OUT/'delivered.json',dict(at=c.now(),newIllustratedConnections=1,newArtworks=0,newImages=0));print('Committed one match')

def verify():
    p=c.load(OUT/'plan.json.gz')
    with c.connect() as db:
        assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone())==p['artworkBefore']
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())==p['eventBefore']
        e=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=%s',(p['entryBefore']['id'],)).fetchone())
        assert e['artwork_id']==AID
        assert {k:v for k,v in e.items() if k not in ['artwork_id','evidence','match_basis']}=={k:v for k,v in p['entryBefore'].items() if k not in ['artwork_id','evidence','match_basis']}
    r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID+'/entries',params=dict(limit=100),timeout=30);r.raise_for_status();items=r.json()['items']
    assert len(items)==28 and sum(bool(x.get('image')) for x in items)==5
    entry=next(x for x in items if x['id']==e['id']);assert entry['artworkId']==AID and entry['image'].startswith('/assets/artworks/')
    r=requests.head('https://artlines.org'+entry['image'],timeout=30);assert r.status_code==200 and r.headers.get('content-type','').startswith('image/')
    result=dict(at=c.now(),newIllustratedConnections=1,eventEntries=28,eventIllustratedEntries=5,newArtworks=0,newImages=0,mainArtworkPreserved=True,originalEntryLabelsPreserved=True,assetStatus=200,realLocalDatabaseWrites=False,checklistComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/blake-matthew-match.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['plan','apply','verify'];globals()[sys.argv[1]]()
