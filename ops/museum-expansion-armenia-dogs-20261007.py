#!/usr/bin/env python3
"""Add the independently identified National Gallery Dogs painting in local review."""
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-armenia-holdings2-20261007.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
a=v.w.c.a;s=a.s;m=v.m;RUN=v.RUN;IID=v.IID;SOURCE='armenia-002'
PLAN=m.RUN/(SOURCE+'-current-plan.json.gz');SID=m.uid('source/'+SOURCE)
SOURCE_SLUG='museum-expansion-20261006-'+SOURCE;SCHEME='sarian-object-page'
reference=a.reference;checked_reference=a.checked_reference

def record():
    r=copy.deepcopy(next(r for r in m.load(RUN/'sarian-caption-research-001.json.gz')['records'] if r['raw_source_record']['queue_number']==7))
    assert s.validate_record(r,s.body(dict(receipt=r['source_receipt'],body_path=r['body_path'])))==r['facts']
    evidence=m.load(RUN/'sarian-distinct-version-entities-001.json');entities=json.loads(v.capture_body(evidence['capture']))['entities'];assert entities==evidence['entities']
    e=entities['Q56248088'];assert v.val(e,'P170')['id']=='Q718409' and v.val(e,'P195')['id']=='Q2087788'
    assert v.val(e,'P217')=='217' and v.val(e,'P2048')['amount']=='+41' and v.val(e,'P2049')['amount']=='+98.5'
    assert r['facts']['dimensions']=='41x98.5 cm' and r['facts']['first']==r['facts']['last']==1910
    comparison=m.load(RUN/'sarian-existing-version-review-captures-001.json')['records'][0]
    titles,details=s.captions(v.capture_body(comparison['capture']))
    assert titles==[s.clean(t) for t in comparison['caption_titles']] and details==[s.clean(t) for t in comparison['caption_details']]
    assert '104' in details[2] and '139.2' in details[2] and "Martiros Sarian's Museum" in details[2]
    r['raw_source_record']['version_review']=dict(decision='approved_review_only_addition',basis='The primary artist-museum pages identify two separate 1910 Dogs paintings: National Gallery 41 x 98.5 cm and house-museum 104 x 139.2 cm. The existing catalogue object Q28925577 matches the latter. Current source Q56248088 confirms the gallery object, including inventory217; no existing catalogue source identity was found. Preserve NULL accession because the primary object caption omits it.',distinct_gallery_entity=e,entity_capture=evidence['capture'],house_museum_comparison=comparison,existing_house_museum_id='bb1be2f2-3cb7-54b5-8549-4d71fa406b8e')
    oid=r['source_record_id'];r['artwork_id']=m.uid(SOURCE+'/'+oid);r['slug']='museum-expansion-'+SOURCE+'-'+hashlib.sha256(oid.encode()).hexdigest()[:20]
    return r

def validate(plan):
    for ref in plan['evidence']:checked_reference(ref)
    assert plan['records']==[record()];return plan

def validate_plan():return validate(m.load(PLAN)),hashlib.sha256(PLAN.read_bytes()).hexdigest()

def baseline_unchanged(db,plan):
    hp,hd=v.validate_plan();v.verify(db,hp,hd)
    assert v.h.snapshot(db,plan['scoped_ids'])==plan['before'],'Prior scope changed'
    return dict(existing_artworks_unchanged=len(plan['before']['artworks']),complete_citations_unchanged=len(plan['before']['citations']),institution_unchanged=True)

def preflight(db,plan):
    result=baseline_unchanged(db,plan);r=plan['records'][0];url=r['facts']['source_url']
    assert s.current_identity(db,plan['records'])==plan['identity_snapshot'],'Creator/title scope changed'
    assert not db.execute('SELECT 1 FROM artworks WHERE id=%s OR slug=%s',(r['artwork_id'],r['slug'])).fetchone()
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=%s",(url,)).fetchone()
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme='wikidata' AND external_id='Q56248088'))",(url,)).fetchone()
    return dict(**result,eligible_records=1,source_identity_collisions=0)

def prepare():
    assert not PLAN.exists();r=record();hp,hd=v.validate_plan()
    with m.connect() as db:
        prior=v.verify(db,hp,hd);assert prior['current_counts']==dict(linked=200,eligible=199)
        identity=s.current_identity(db,[r]);assert len(identity['linked'])==21 and len(identity['unlinked'])==36
        assert identity['collisions']==[]
        ids=sorted(set(hp['scoped_ids'])|{x['id'] for k in ['linked','unlinked','collisions','museum_scope'] for x in identity[k]})
        before=v.h.snapshot(db,ids)
        evidence=[reference(RUN/f) for f in ['sarian-caption-research-001.json.gz','sarian-distinct-version-entities-001.json','sarian-existing-version-review-captures-001.json','existing-holding-followup-002.json.gz']]+[reference(v.PLAN),reference(Path(__file__).resolve())]
        plan=dict(at=m.now(),records=[r],held=[],evidence=evidence,scoped_ids=ids,before=before,identity_snapshot=identity,prior_holding_verification=prior,policy='One distinct original Dogs painting from the artist-museum explicit National Gallery holdings. Keep literal trilingual captions, unknown primary inventory, and review state. Existing house-museum record remains unchanged. No images, publication or current-display claims.')
        validate(plan);checks=preflight(db,plan)
    m.save(PLAN,plan);digest=hashlib.sha256(PLAN.read_bytes()).hexdigest();m.save(RUN/(SOURCE+'-preflight.json'),dict(at=m.now(),plan_sha256=digest,**checks));print('Pinned Dogs addition',digest,flush=True)

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
    baseline=baseline_unchanged(db,plan)
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
        else:m.save(backup,dict(at=m.now(),plan_sha256=digest,new_artwork_ids=ids,existing_new_ids=old,checks=checks,before=plan['before']))
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
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=201,eligible=200)
    m.save(m.RUN/(SOURCE+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=len(records),museums=1,local_only=True,images_added=0,published=0,verification=result))
    m.save(RUN/(SOURCE+'-verification.json'),dict(at=m.now(),plan_sha256=digest,**result))
    print('Added',len(records),'review artworks; Armenia now',result['current_counts'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
