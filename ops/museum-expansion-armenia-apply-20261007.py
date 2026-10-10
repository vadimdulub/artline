#!/usr/bin/env python3
"""Pinned local review additions from the Sarian House-Museum Armenian holdings."""
import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-armenia-sarian-20261007.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m;RUN=s.RUN;IID=s.IID;SOURCE='armenia-001'
PLAN=m.RUN/(SOURCE+'-current-plan.json.gz');SID=m.uid('source/'+SOURCE)
SOURCE_SLUG='museum-expansion-20261006-'+SOURCE;SCHEME='sarian-object-page'
TRIAGE=RUN/'sarian-editorial-triage-001.json';IDENTITY=RUN/'sarian-identity-001.json.gz'
reference=s.reference

def checked_reference(ref):
    path=m.ROOT/ref['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256'],'Changed pinned evidence: '+ref['path'];return path

def validate(plan):
    for ref in plan['evidence']:checked_reference(ref)
    triage=m.load(checked_reference(plan['editorial_triage']))
    decisions={d['source_record_id']:d for d in triage['decisions'] if d['decision']=='approved_review_only_addition'}
    assert len(decisions)==36 and len(plan['records'])==36
    assert {r['source_record_id'] for r in plan['records']}==set(decisions)
    assert len({r['facts']['source_url'] for r in plan['records']})==36
    for r in plan['records']:
        oid=r['source_record_id'];d=decisions[oid]
        assert r['museum']['id']==IID and r['museum']['slug']==s.SLUG
        assert r['museum']['canonical_institution_id'] is None and r['museum']['status']!='archived'
        assert r['raw_source_record']['editorial_review']==d and r['facts']==d['facts']
        assert s.validate_record(r,s.body(dict(receipt=r['source_receipt'],body_path=r['body_path'])))==r['facts']
        assert r['artwork_id']==m.uid(SOURCE+'/'+oid)
        assert r['slug']=='museum-expansion-'+SOURCE+'-'+hashlib.sha256(oid.encode()).hexdigest()[:20]
    return plan

def validate_plan():
    raw=PLAN.read_bytes();return validate(m.load(PLAN)),hashlib.sha256(raw).hexdigest()

def baseline_unchanged(db):
    baseline=m.load(RUN/'armenia-001-before.json');backup=m.load(Path(baseline['backup_path']));ids=baseline['scoped_ids']
    inst=db.execute('SELECT * FROM institutions WHERE id=%s',(IID,)).fetchone()
    assert json.loads(json.dumps(inst,default=str))==backup['museum'],'Prior institution changed'
    arts=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
    cites=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
    assert arts==backup['artworks'] and cites==backup['citations'],'Prior artwork or complete citation changed'
    return dict(existing_artworks_unchanged=len(arts),complete_citations_unchanged=len(cites),institution_unchanged=True)

def preflight(db,plan):
    records=plan['records'];baseline=baseline_unchanged(db)
    expected=m.load(checked_reference(plan['identity_snapshot']))
    actual=s.current_identity(db,m.load(RUN/'sarian-caption-research-001.json.gz')['records'])
    for key,rows in actual.items():assert rows==expected[key],'Changed '+key+' identity evidence'
    ids=[r['artwork_id'] for r in records];urls=[r['facts']['source_url'] for r in records]
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) LIMIT 1",(urls,)).fetchone(),'Existing source citation'
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=%s AND external_id=ANY(%s))) LIMIT 1",(urls,SCHEME,[r['source_record_id'] for r in records])).fetchone(),'Existing source identity'
    counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
    assert counts==dict(linked=5,eligible=4),'Museum scope changed; re-review'
    assert db.execute("SELECT bool_and(artline_creation_scope(f,l,p)='eligible') ok FROM unnest(%s::integer[],%s::integer[],%s::text[]) x(f,l,p)",([r['facts']['first'] for r in records],[r['facts']['last'] for r in records],[r['facts']['date_precision'] for r in records])).fetchone()['ok']
    return dict(**baseline,identity_rows={k:len(v) for k,v in actual.items()},eligible_records=len(records),source_identity_collisions=0,current_counts=counts)

def prepare():
    assert not PLAN.exists(),'Keep prior pinned plan'
    triage=m.load(TRIAGE);byid={r['source_record_id']:r for r in m.load(RUN/'sarian-caption-research-001.json.gz')['records']};records=[]
    for d in triage['decisions']:
        if d['decision']!='approved_review_only_addition':continue
        r=copy.deepcopy(byid[d['source_record_id']]);oid=r['source_record_id']
        r['raw_source_record']['editorial_review']=d;r['artwork_id']=m.uid(SOURCE+'/'+oid)
        r['slug']='museum-expansion-'+SOURCE+'-'+hashlib.sha256(oid.encode()).hexdigest()[:20];records.append(r)
    held=[d for d in triage['decisions'] if d['decision']!='approved_review_only_addition']+triage['source_holds']
    evidence=triage['evidence']+[reference(TRIAGE),reference(IDENTITY),reference(m.ROOT/'ops/museum-expansion-armenia-sarian-20261007.py')]
    plan=dict(at=m.now(),records=records,held=held,evidence=evidence,editorial_triage=reference(TRIAGE),identity_snapshot=reference(IDENTITY),policy='36 selected local review additions from the artist museum explicit National Gallery of Armenia collection. All trilingual captions and material discrepancies retained; disputed medium/type left unknown. Accessions unknown. No existing metadata, creator links, images, display or publication changes.')
    validate(plan)
    with m.connect() as db:checks=preflight(db,plan)
    m.save(PLAN,plan);digest=hashlib.sha256(PLAN.read_bytes()).hexdigest()
    m.save(RUN/'preflight-verification-001.json',dict(at=m.now(),plan_sha256=digest,**checks))
    print('Pinned',len(records),'records;',len(held),'held;',digest,flush=True)


FIELDS={'title':'title','normalized_title':None,'date_display':'date_display','creation_year_start':'first','creation_year_end':'last','date_precision':'date_precision','work_type':'work_type','medium_text':'medium','dimensions_text':'dimensions','accession_number':'accession','unlinked_creator_label':'creator_label','object_form':'object_form','cultural_context':'cultural_context'}


def verify(db,plan,digest):
    records=plan['records'];ids=[r['artwork_id'] for r in records]
    actual={r['id']:r for r in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)) for r in [r['row']]}
    assert len(actual)==len(records)
    citations=db.execute("SELECT entity_id::text,source_id::text,field_name,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
    external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
    locations=db.execute('SELECT artwork_id::text,claim_type,institution_id::text,context,source_id::text,source_url,evidence_note,review_state,superseded_by FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
    assert len(citations)==len(external)==len(locations)==len(records)
    by_c={r['entity_id']:r for r in citations};by_e={r['entity_id']:r for r in external};by_l={r['artwork_id']:r for r in locations}
    assert len(by_c)==len(by_e)==len(by_l)==len(records)
    for r in records:
        aid=r['artwork_id'];a=actual[aid];f=r['facts'];c=by_c[aid];e=by_e[aid];l=by_l[aid]
        for column,key in FIELDS.items():assert a[column]==(f.get(key) if key else m.norm(f['title'])),(aid,column)
        assert a['slug']==r['slug'] and a['status']=='review' and a['research_candidate'] and a['current_institution_id']==IID
        assert a['primary_media_id'] is None and a['published_at'] is None
        assert c['source_id']==e['source_id']==l['source_id']==SID
        assert c['source_record_id']==e['external_id']==r['source_record_id'] and e['scheme']==SCHEME
        assert c['source_url']==e['canonical_url']==l['source_url']==f['source_url']
        assert c['field_name']=='museum_expansion_primary_metadata'
        note=json.loads(c['evidence_note']);assert note['plan_sha256']==digest and note['raw_source_record']==r['raw_source_record'] and note['source_receipt']==r['source_receipt'] and note['body_path']==r['body_path']
        assert l['claim_type']=='holding' and l['institution_id']==IID and l['context']=='collection' and l['review_state']=='accepted' and l['superseded_by'] is None
        assert l['evidence_note']==f['holding_basis']+' Source capture SHA-256 '+r['source_receipt']['sha256']+'.'
    assert db.execute('SELECT count(*) n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
    assert db.execute('SELECT count(*) n FROM artwork_media WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
    scope=db.execute("SELECT count(*) n FROM artworks a WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n'];assert scope==len(records)
    baseline=baseline_unchanged(db)
    counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
    return dict(**baseline,verified_new_records=len(records),current_counts=counts,distinct_source_entries=len({r['source_record_id'] for r in records}),source_inventory_count=sum(r['facts']['accession'] is not None for r in records),work_types=dict(collections.Counter(r['facts']['work_type'] for r in records)),new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,verified_all_metadata_and_citations=True)


def apply(expected_sha):
    plan,digest=validate_plan();assert digest==expected_sha,'Plan digest changed';records=plan['records'];ids=[r['artwork_id'] for r in records]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone()
        assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432],'Only the local catalogue is allowed'
        old=db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        if old:
            assert len(old)==len(records),'Partial batch requires review';result=verify(db,plan,digest)
            print('Unchanged replay:',result['verified_new_records'],'records; zero inserts',flush=True);return
        checks=preflight(db,plan)
        db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,)).fetchone()
        backup=m.BACKUP/(SOURCE+'-preimages.json.gz')
        if backup.exists():assert m.load(backup)['plan_sha256']==digest
        else:m.save(backup,dict(at=m.now(),plan_sha256=digest,new_artwork_ids=ids,existing_new_ids=old,checks=checks,baseline_backup=m.load(RUN/'armenia-001-before.json')['backup_path']))
        m.save(m.BACKUP/(SOURCE+'-reviewed-plan.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Museum expansion — reviewed National Gallery of Armenia records, 7 October 2026','authority_data','https://www.sarian.am/'))
        for r in records:
            f=r['facts'];aid=r['artwork_id'];rc=r['source_receipt']
            db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
              work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,cultural_context,created_by,updated_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s,%s)''',
              (aid,r['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions'],f['accession'],f['creator_label'],f.get('object_form'),f.get('cultural_context'),m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,r['source_record_id'],f['source_url'],SID,rc['retrieved_at']))
            note=dict(plan_sha256=digest,raw_source_record=r['raw_source_record'],source_receipt=rc,body_path=r['body_path'],policy=plan['policy'])
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_primary_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,r['source_record_id'],f['source_url'],json.dumps(note,ensure_ascii=False),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,f['source_url'],f['holding_basis']+' Source capture SHA-256 '+rc['sha256']+'.',rc['retrieved_at']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=41,eligible=40)
    m.save(m.RUN/(SOURCE+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=len(records),museums=1,local_only=True,images_added=0,published=0,verification=result))
    m.save(RUN/'progress-verification-001.json',dict(at=m.now(),plan_sha256=digest,**result))
    print('Added',len(records),'review artworks; Armenia now',result['current_counts'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','apply','verify']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
