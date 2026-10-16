#!/usr/bin/env python3
"""Add selected original-catalogue paintings/drawings without invented object matches."""
import gzip,json,re,sys
from pathlib import Path
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-blake-checklist-20261012'
OUT=n.OUT.parent/'blake-philadelphia-1939'/'checklist-wave1';BACKUP=n.BACKUP.parent/'blake-checklist-wave1'
EID='5c64ef50-18f0-5cf3-8a19-e86adf45c299'

def plan():
    review=c.load(OUT.parent/'paintings-drawings-selected-review.json');entries=review['entries'];assert len(entries)==24
    for e in entries:
        matches=re.findall(r'Lent\s+by\s+([^\n]+)',e['text']);assert matches
        e['lender']=' '.join(matches[0].split()).rstrip('.')
        e['date']={158:'1805 (signed, per 1939 catalogue)',163:'1805 (per 1939 catalogue)',166:'1806 (signed, per 1939 catalogue)',176:'1803 (signed, per 1939 catalogue)'}.get(e['number'])
    with c.connect()as db:
        before=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert len(before)==4 and not {r['catalogue_number']for r in before}&{str(e['number'])for e in entries}
        event=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone());assert event['checklist_state']=='partial'
        occ=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(EID,)).fetchall());assert len(occ)==1
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(EID,)).fetchone()
    p=dict(at=c.now(),reviewSHA=c.sha((OUT.parent/'paintings-drawings-selected-review.json').read_bytes()),receipt=review['receipt'],entries=entries,before=before,eventBefore=event,occurrence=occ[0],counts=dict(newCatalogueEntries=24,newArtworks=0,newImages=0,totalEntries=28),mainCatalogueWrites=False,realLocalDatabaseWrites=False)
    c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(p['counts'])

def apply():
    p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')and p['reviewSHA']==c.sha((OUT.parent/'paintings-drawings-selected-review.json').read_bytes());rc=p['receipt'];assert c.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256']
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id FOR SHARE',(EID,)).fetchall())==p['before']
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR SHARE',(EID,)).fetchone())==p['eventBefore']
        for e in p['entries']:
            key=str(e['number']);sid=c.uid(OP+'/source/'+key);ev=dict(operation=OP,originalCatalogueNumber=key,scope='Individually described painting or drawing; original catalogue text read. No bound books, letters or multi-work sets in this batch.',reviewMethod='Original-catalogue OCR with selected page visual checks; not a claim every new entry has a visually checked scan.',creatorLabelIsHistorical=True,canonicalObjectMatchPending=True,lenderIsHistorical=True,currentHoldingClaim=False,currentDisplayClaim=False,checklistComplete=False)
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,EID,OP,key,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e),Jsonb(ev)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,lender_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'catalogued',%s,%s)",(c.uid(OP+'/entry/'+key),EID,sid,p['occurrence']['id'],'williamblakedesc00phil/'+key,key,e['title'],e['creatorLabel'],e['date'],e['medium'],e['lender'],Jsonb(ev),'Original numbered catalogue entry; surviving object match unresolved. Same-title versions remain distinct by catalogue number and historical lender.'))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])

def verify():
    p=c.load(OUT/'plan.json.gz')
    with c.connect()as db:
        es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id',(EID,)).fetchall());assert len(es)==28
        assert [r for r in es if r['id']in {x['id']for x in p['before']}]==p['before']
        added=[r for r in es if r['id']not in {x['id']for x in p['before']}];assert {r['catalogue_number']for r in added}=={str(e['number'])for e in p['entries']}
        assert all(r['artwork_id']is None and r['participation']=='catalogued'for r in added)
        assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())==p['eventBefore']
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+EID;r=requests.get(api+'/entries',params=dict(limit=100),timeout=30);r.raise_for_status();data=r.json();assert len(data['items'])==28 and not data.get('nextCursor');assert {x['id']for x in data['items']}=={r['id']for r in es};assert sum(bool(x.get('image'))for x in data['items'])==4
    result=dict(at=c.now(),counts=p['counts'],allEntriesAPIVerified=True,existingIllustratedLinksPreserved=True,mainCatalogueWrites=False,realLocalDatabaseWrites=False,checklistComplete=False)
    c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/blake-checklist-wave1.json',result);print(json.dumps(result))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
