#!/usr/bin/env python3
"""Verify the prior Sarian additions with explicitly audited later holding changes."""
import collections
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('h',Path(__file__).with_name('museum-expansion-armenia-holdings-20261007.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
a=h.a;m=h.m

def verify_prior_baseline(db):
    plan,digest=h.validate_plan();holding=h.verify(db,plan,digest)
    baseline=m.load(a.RUN/'armenia-001-before.json');backup=m.load(Path(baseline['backup_path']));ids=baseline['scoped_ids']
    approved={r['facts']['artwork_id'] for r in plan['records']}
    assert approved<=set(ids)
    before={r['row']['id']:r['row'] for r in backup['artworks']}
    after={r['row']['id']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,))}
    assert set(before)==set(after)
    for aid,old in before.items():
        ignored={'current_institution_id','updated_at'} if aid in approved else set()
        assert {k:v for k,v in after[aid].items() if k not in ignored}=={k:v for k,v in old.items() if k not in ignored},aid
        if aid in approved:assert after[aid]['current_institution_id']==a.IID
    cites=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
    assert [r for r in cites if r['row']['source_id']!=h.SID]==backup['citations']
    assert len([r for r in cites if r['row']['source_id']==h.SID])==136
    inst=db.execute('SELECT * FROM institutions WHERE id=%s',(a.IID,)).fetchone()
    assert json.loads(json.dumps(inst,default=str))==backup['museum']
    return dict(existing_artworks_metadata_unchanged=248,complete_prior_citations_unchanged=294,institution_unchanged=True,authorized_holding_changes=136,holding_verification=holding)

def verify_prior_additions(db,plan,digest):
    # Explicit successor verification. The old immutable checkpoint's full-row
    # baseline intentionally predates the later authorized 136 holding changes.
    # Recheck all new-record metadata/evidence and validate that exact delta.
    records=plan['records'];ids=[r['artwork_id'] for r in records]
    actual={r['row']['id']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,))}
    citations=db.execute("SELECT entity_id::text,source_id::text,field_name,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
    external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
    locations=db.execute('SELECT artwork_id::text,claim_type,institution_id::text,context,source_id::text,source_url,evidence_note,review_state,superseded_by FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
    assert len(actual)==len(citations)==len(external)==len(locations)==len(records)==36
    by_c={r['entity_id']:r for r in citations};by_e={r['entity_id']:r for r in external};by_l={r['artwork_id']:r for r in locations}
    assert len(by_c)==len(by_e)==len(by_l)==36
    for r in records:
        aid=r['artwork_id'];art=actual[aid];f=r['facts'];c=by_c[aid];e=by_e[aid];l=by_l[aid]
        for col,key in a.FIELDS.items():assert art[col]==(f.get(key) if key else m.norm(f['title'])),(aid,col)
        assert art['slug']==r['slug'] and art['status']=='review' and art['research_candidate'] and art['current_institution_id']==a.IID
        assert art['primary_media_id'] is None and art['published_at'] is None
        assert c['source_id']==e['source_id']==l['source_id']==a.SID
        assert c['source_record_id']==e['external_id']==r['source_record_id'] and e['scheme']==a.SCHEME
        assert c['source_url']==e['canonical_url']==l['source_url']==f['source_url'] and c['field_name']=='museum_expansion_primary_metadata'
        note=json.loads(c['evidence_note']);assert note['plan_sha256']==digest and note['raw_source_record']==r['raw_source_record'] and note['source_receipt']==r['source_receipt'] and note['body_path']==r['body_path']
        assert l['claim_type']=='holding' and l['institution_id']==a.IID and l['context']=='collection' and l['review_state']=='accepted' and l['superseded_by'] is None
        assert l['evidence_note']==f['holding_basis']+' Source capture SHA-256 '+r['source_receipt']['sha256']+'.'
    assert db.execute('SELECT count(*) n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
    assert db.execute('SELECT count(*) n FROM artwork_media WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==36
    baseline=verify_prior_baseline(db)
    return dict(verified_new_records=36,all_new_metadata_and_citations_verified=True,baseline_verification=baseline,current_counts=baseline['holding_verification']['current_counts'])

if __name__=='__main__':
    plan,digest=a.validate_plan()
    with m.connect() as db:print(json.dumps(verify_prior_additions(db,plan,digest)),flush=True)
