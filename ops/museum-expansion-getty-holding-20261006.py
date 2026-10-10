#!/usr/bin/env python3
"""Resolve one exact existing Getty identity; preserve artwork metadata and review."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('getty',Path(__file__).with_name('museum-expansion-getty-20261006.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
m=g.m
AID='d943e866-09c4-5902-84e6-48e33eeff3ff'
IID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c'
KEY='getty-existing-exaltation-holding'
SID=m.uid('source/'+KEY)
HID=m.uid('holding/'+KEY)
PLAN=g.RUN/(KEY+'-plan.json.gz')


def snapshot(db):
    artwork=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(AID,)).fetchone()['row']
    result=dict(artwork=artwork)
    for key,sql in {
        'artists':'SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=%s ORDER BY artist_id,attribution_role',
        'media':'SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=%s ORDER BY media_id',
        'identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=%s ORDER BY id",
        'citations':"SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=%s ORDER BY id",
        'assertions':'SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=%s ORDER BY id',
    }.items():result[key]=[v['row'] for v in db.execute(sql,(AID,))]
    result['museum']=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(IID,)).fetchone()['row']
    return result


def evidence():
    row=m.load(g.RUN/'existing-exaltation-primary-review.json.gz')
    obj=json.loads(g.read_capture(row['api_capture']));native=g.html_fields(g.read_capture(row['native_capture']))
    index=json.loads(g.read_capture(row['index_capture']))
    assert row['index_record'] in index['data'] and obj==row['api_object'] and native==row['native_fields']
    facts,reason=g.facts(obj,row['index_record'],native)
    assert not reason and facts==row['facts'] and row['artwork_id']==AID
    assert row['api_capture']['receipt']['url']==g.API+row['index_record']['id']
    assert row['native_capture']['receipt']['url']==facts['source_url']
    return row


def prepare():
    row=evidence();f=row['facts']
    with m.connect() as db:
        before=snapshot(db);a=before['artwork']
        creators=db.execute('''SELECT ar.display_name,aa.attribution_role FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
          WHERE aa.artwork_id=%s''',(AID,)).fetchall()
        assert creators==[dict(display_name='Juan de Valdés Leal',attribution_role='primary')]
        assert a['title']==f['title'] and a['accession_number']==f['accession'] and a['work_type']==f['work_type']
        assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(f['first'],f['last'],f['date_precision'])
        assert a['status']=='review' and a['research_candidate'] and not a['current_institution_id']
        assert any(c['source_url']==f['source_url'] for c in before['citations'])
        assert before['museum']['slug']==g.SLUG and before['museum']['canonical_institution_id'] is None
        pending=before['assertions']
        assert len(pending)==1 and pending[0]['institution_id']==IID and pending[0]['claim_type']=='holding' and pending[0]['review_state']=='review' and not pending[0]['superseded_by']
    plan=dict(at=m.now(),before=before,evidence=row,policy='Exact native URL, inventory, title, creator and creation bounds agree. Add official holding evidence and supersede the older pending Wikidata claim. Preserve all artwork metadata, artists, media, review and publication status.')
    m.save(PLAN,plan);print(hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)


def verify(db,plan):
    after=snapshot(db);before=plan['before']
    assert after['artwork']['current_institution_id']==IID
    ignored={'current_institution_id','updated_at'}
    assert {k:v for k,v in after['artwork'].items() if k not in ignored}=={k:v for k,v in before['artwork'].items() if k not in ignored}
    for key in ['artists','media','identifiers','museum']:assert after[key]==before[key]
    citations=[c for c in after['citations'] if c['source_id']==SID]
    assert len(citations)==1 and json.loads(citations[0]['evidence_note'])['evidence']==plan['evidence']
    assert [c for c in after['citations'] if c['source_id']!=SID]==before['citations']
    previous=dict(before['assertions'][0],superseded_by=HID)
    assert previous in after['assertions'] and len(after['assertions'])==2
    current=next(h for h in after['assertions'] if h['id']==HID)
    assert current['claim_type']=='holding' and current['review_state']=='accepted' and current['institution_id']==IID and not current['superseded_by']
    assert not any(h['claim_type']=='display' for h in after['assertions'])
    return after


def apply(digest):
    plan=m.load(PLAN);assert hashlib.sha256(PLAN.read_bytes()).hexdigest()==digest
    assert evidence()==plan['evidence']
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,
        options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(AID,))
        if db.execute('SELECT 1 FROM artwork_location_assertions WHERE id=%s',(HID,)).fetchone():
            verify(db,plan);print('Unchanged replay: existing Getty holding verified; zero writes',flush=True);return
        assert snapshot(db)==plan['before'],'Existing record changed since the pinned review'
        assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
        m.save(m.BACKUP/(KEY+'-preimages.json.gz'),plan)
        row=plan['evidence'];f=row['facts'];rc=row['native_capture']['receipt']
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',
          (SID,'museum-expansion-20261006-'+KEY,'Getty existing artwork holding verification, 6 October 2026','authority_data',g.SITE+'/'))
        db.execute('''INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
          VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)''',
          (AID,SID,row['index_record']['id'],f['source_url'],json.dumps(dict(plan_sha256=digest,evidence=row),ensure_ascii=False),rc['retrieved_at'],m.ACTOR))
        db.execute('''INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
          VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')''',
          (HID,AID,IID,SID,f['source_url'],f['holding_basis']+' Existing artwork exact identity confirmed; catalogue metadata retained. Plan SHA-256 '+digest,rc['retrieved_at']))
        db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(HID,plan['before']['assertions'][0]['id']))
        after=verify(db,plan)
    m.save(g.RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,existing_artworks_linked=1,new_artworks=0,after=after,local_only=True))
    print('Verified existing Getty artwork linked; catalogue metadata, review status and media preserved',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.command=='prepare':prepare()
    else:assert args.plan_sha;apply(args.plan_sha)
