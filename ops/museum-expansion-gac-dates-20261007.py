#!/usr/bin/env python3
"""Six source-explicit date enrichments; five holdings, one missing-object hold."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-gac-holdings-20261007.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
m=w.m;RUN=w.RUN;IID=w.IID;KEY='gac-date-enrichment-001';SID=m.uid('source/'+KEY)
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'date-enrichment-editorial-001.json'
SCOPE=RUN/'date-enrichment-scope-001.json.gz';MISSING='Q119915053'
DATE_FIELDS={'date_display','creation_year_start','creation_year_end','date_precision'}
reference=w.reference;checked_reference=w.checked_reference


def capture_body(cap):
    raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());r=cap['receipt']
    assert r['status']==200 and hashlib.sha256(raw).hexdigest()==r['sha256']
    assert r['url']==r['final_url']
    return raw


def source_rows():
    out={}
    for path in sorted((RUN/'new-entities-001').glob('*.gz')):
        row=m.load(path);data=json.loads(capture_body(row['capture']))['entities']
        assert data==row['entities'] and set(data)==set(row['ids'])
        for q,e in data.items():
            assert q not in out;out[q]=dict(entity=e,capture=row['capture'])
    assert len(out)==106
    return out


def creation(value):
    decade=re.fullmatch(r'(\d{3}0)s',value or '')
    if decade:
        first=int(decade[1]);assert 100<=first<=1960
        return first,first+9,'range'
    return w.native_dates(value)


def facts(art,entity,native,artist,authority,decision):
    parsed=w.parse_native(capture_body(native['capture']));assert parsed==native['parsed'];f=parsed['fields']
    assert art['id']==native['artwork_id']==decision['artwork_id'] and entity['id']==native['qid']==decision['qid']
    assert art['current_institution_id'] is None and art['status']=='review' and art['published_at'] is None
    assert art['creation_year_start'] is art['creation_year_end'] is None and art['date_precision']=='unknown'
    assert art['date_display']=='Creation date under review', 'Only initially unknown dates may be filled'
    assert m.norm(art['title'])==m.norm(f['Title']) and parsed['headings']==[f['Title']] and not parsed['repeated']
    assert native['url']==native['capture']['receipt']['url']
    if parsed['canonical']!=native['url']:
        assert entity['id']=='Q118895964' and parsed['canonical']=='https://artcollection.dcms.gov.uk/object/18775/'
        alias=m.load(RUN/'date-canonical-alias-001.json');raw=gzip.decompress((m.ROOT/alias['body_path']).read_bytes())
        assert alias['receipt']['url']==parsed['canonical'] and alias['receipt']['final_url']==native['url'] and alias['receipt']['status']==200
        assert hashlib.sha256(raw).hexdigest()==alias['receipt']['sha256']==native['capture']['receipt']['sha256']
    assert f['GAC number']==art['accession_number']==w.val(entity,'P217')
    assert w.qualifier_value(w.one(entity,'P217'),'P195')['id']==w.QID
    assert set(w.one(entity,'P217').get('qualifiers',{}))=={'P195'}
    assert w.val(entity,'P195')['id']==w.QID and not set(w.one(entity,'P195').get('qualifiers',{}))-{'P580'}
    assert artist['artwork_id']==art['id'] and artist['attribution_role']=='primary'
    assert authority['entity_id']==artist['artist_id'] and authority['external_id']==w.val(entity,'P170')['id']
    assert not w.one(entity,'P170').get('qualifiers')
    assert decision['creator_pair']==[artist['display_name'],f['Artist']] and decision['creator_basis']
    assert not re.search(r'\b(after|circle|attributed|workshop|manner|school|unknown)\b',f['Artist'],re.I)
    assert not any(w.h.best(entity,p) for p in ['P518','P361','P1877','P527'])
    for claim in w.h.best(entity,'P18'):
        assert not re.search(r'\b(after|circle|attributed|workshop|manner|school)\b',w.h.value(claim).split(' - ')[0],re.I)
    first,last,precision=creation(f['Date'])
    assert f.get('Dimensions') and f.get('Acquisition','').startswith('Purchased')
    missing=bool(re.search(r'\bmissing\b',f.get('Location',''),re.I))
    assert missing==(entity['id']==MISSING) and decision['accept_holding']==(not missing)
    assert decision['source_date']==f['Date'] and decision['physical_identity_basis'] and decision['source_limitations']
    if entity['id']=='Q118895964':
        proof=m.load(RUN/'carlile-pdf-review-001.json');raw=gzip.decompress((m.ROOT/proof['source']['body_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==proof['source']['receipt']['sha256']
        assert f['Date']=='1650s' and f['Inscription']=='on stretcher verso bottom left: by Peter Lely 1665'
    patch=dict(date_display=f['Date'],creation_year_start=first,creation_year_end=last,date_precision=precision)
    assert set(patch)==DATE_FIELDS
    return dict(artwork_id=art['id'],qid=entity['id'],inventory=f['GAC number'],source_url=native['url'],
                title=art['title'],native_creator=f['Artist'],patch=patch,accept_holding=not missing)


def records():
    scope=m.load(SCOPE);before=m.load(Path(scope['backup_path']));arts={r['id']:r for r in before['artworks']};sources=source_rows();out=[]
    for decision in m.load(REVIEW)['decisions']:
        aid=decision['artwork_id'];q=decision['qid'];native=m.load(RUN/'native-objects-002'/(q+'.json.gz'))
        artists=[r for r in scope['artists'] if r['artwork_id']==aid];assert len(artists)==1
        authorities=[r for r in scope['artist_authorities'] if r['entity_id']==artists[0]['artist_id']];assert len(authorities)==1
        f=facts(arts[aid],sources[q]['entity'],native,artists[0],authorities[0],decision)
        out.append(dict(facts=f,decision=decision,source=native,wikidata=sources[q],holding_id=m.uid(KEY+'/'+aid) if f['accept_holding'] else None))
    assert len(out)==len({r['facts']['artwork_id'] for r in out})==6 and sum(r['facts']['accept_holding'] for r in out)==5
    return out


def identity_state(db,scope):
    ids=[r['artwork_id'] for r in scope['selected']]
    queries={
      'artists':('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name,a.birth_year,a.death_year FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',ids),
      'artist_authorities':("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,external_id",scope['artist_ids']),
      'artist_artworks':('''SELECT a.id::text,a.title,a.alternate_title,a.normalized_title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.dimensions_text,a.current_institution_id::text,aa.artist_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) ORDER BY a.id,aa.artist_id''',scope['artist_ids']),
      'inventory_lookup':('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s::text[]) ORDER BY id',[r['inventory'] for r in scope['selected']]),
      'exact_title_lookup':('SELECT id::text,title,alternate_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s::text[]) ORDER BY id',[m.norm(r['native_title']) for r in scope['selected']]),
      'qid_lookup':("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s::text[]) ORDER BY entity_id",[r['qid'] for r in scope['selected']])}
    for key,(sql,values) in queries.items():assert db.execute(sql,(values,)).fetchall()==scope[key], 'Identity comparison changed: '+key


def prepare():
    assert not PLAN.exists();selected=records();scope=m.load(SCOPE);initial=m.load(Path(scope['backup_path']))
    with m.connect() as db:
        prior_plan,prior_digest=w.validate_plan();prior=w.verify(db,prior_plan,prior_digest)
        before=w.snapshot(db,scope['scoped_ids'])
        assert all(before[k]==initial[k] for k in before) and w.counts(db)==dict(linked=140,eligible=137)
        identity_state(db,scope)
        for r in selected:
            claims=[x for x in before['assertions'] if x['artwork_id']==r['facts']['artwork_id']]
            assert len(claims)==1 and all(x['institution_id']==IID and x['claim_type']=='holding' and x['review_state']=='review' and not x['superseded_by'] for x in claims)
    files=[SCOPE,REVIEW,w.PLAN,Path(__file__).resolve(),Path(w.__file__).resolve(),RUN/'carlile-pdf-review-001.json',RUN/'carlile-pdf-source-001.json',RUN/'date-enrichment-version-review-001.json',RUN/'date-canonical-alias-001.json']
    files+=sorted((RUN/'new-entities-001').glob('*.gz'))
    files+=[RUN/'native-objects-002'/(r['facts']['qid']+'.json.gz') for r in selected]
    plan=dict(at=m.now(),records=selected,before=before,scoped_ids=scope['scoped_ids'],prior_verification=prior,prior_plan_sha256=prior_digest,evidence=[reference(p) for p in files],policy='Six explicit native date enrichments of existing unknown-date review records. Five separately supported collection holdings; missing Mynott object receives date evidence only. Preserve all other metadata, artists, images, unknowns and publication states.')
    m.save(PLAN,plan);print('Pinned six date enrichments and five holdings',hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)


def validate_plan():
    p=m.load(PLAN)
    for ref in p['evidence']:checked_reference(ref)
    assert p['records']==records();return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()


def note(r,digest):
    return json.dumps(dict(plan_sha256=digest,evidence=r,policy='Fill only the four unknown creation fields with literal source-supported dates. Collection holding only where explicitly accepted; no display/publication claim.'),ensure_ascii=False)


def holding_note(r,digest):
    return r['decision']['physical_identity_basis']+' Editorial confidence 0.95 (not calibrated). '+r['decision']['source_limitations']+' Plan SHA-256 '+digest


def assert_delta(before,after,selected,digest):
    byid={r['id']:r for r in after['artworks']};changes={r['facts']['artwork_id']:r for r in selected}
    assert set(byid)=={r['id'] for r in before['artworks']}
    for old in before['artworks']:
        new=byid[old['id']];record=changes.get(old['id']);expected=dict(old)
        ignored=set()
        if record:
            expected.update(record['facts']['patch']);ignored={'updated_at','updated_by'}
            assert new['updated_by']==m.ACTOR
            if record['facts']['accept_holding']:expected['current_institution_id']=IID
        assert {k:v for k,v in new.items() if k not in ignored}=={k:v for k,v in expected.items() if k not in ignored}, old['id']
    for key in ['artists','media','identifiers','museum']:assert before[key]==after[key],key
    assert [r for r in after['citations'] if r['source_id']!=SID]==before['citations']
    newc={r['entity_id']:r for r in after['citations'] if r['source_id']==SID};newh={r['artwork_id']:r for r in after['assertions'] if r['source_id']==SID}
    assert set(newc)==set(changes) and set(newh)=={aid for aid,r in changes.items() if r['facts']['accept_holding']}
    assert len(after['citations'])==len(before['citations'])+6 and len(after['assertions'])==len(before['assertions'])+5
    for r in selected:
        f=r['facts'];aid=f['artwork_id'];c=newc[aid]
        assert c['field_name']=='museum_expansion_native_date_enrichment' and c['source_record_id']==f['inventory'] and c['source_url']==f['source_url'] and c['evidence_note']==note(r,digest)
        if f['accept_holding']:
            a=newh[aid]
            assert a['id']==r['holding_id'] and a['claim_type']=='holding' and a['institution_id']==IID and a['context']=='collection' and a['review_state']=='accepted'
            assert a['source_url']==f['source_url'] and a['evidence_note']==holding_note(r,digest) and not a['superseded_by']
            assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
    expected=[dict(r,superseded_by=newh[r['artwork_id']]['id']) if r['artwork_id'] in newh else r for r in before['assertions']]
    assert [r for r in after['assertions'] if r['source_id']!=SID]==expected


def verify(db,plan,digest):
    after=w.snapshot(db,plan['scoped_ids']);assert_delta(plan['before'],after,plan['records'],digest)
    ids=[r['facts']['artwork_id'] for r in plan['records']]
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND status='review' AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'",(ids,)).fetchone()['n']==6
    return dict(existing_date_enrichments=6,existing_artworks_linked=5,new_artworks=0,scoped_artworks=242,metadata_unchanged_artworks=236,old_citations_preserved=len(plan['before']['citations']),artist_links_preserved=len(plan['before']['artists']),media_links_preserved=len(plan['before']['media']),identifiers_preserved=len(plan['before']['identifiers']),new_citations=6,new_accepted_holdings=5,missing_object_without_new_holding=1,current_counts=w.counts(db),new_images=0,new_publications=0,new_display_claims=0)


def verify_prior_holdings(db):
    plan,digest=validate_plan();result=verify(db,plan,digest);prior,prior_digest=w.validate_plan()
    assert plan['prior_plan_sha256']==prior_digest
    assert set(prior['scoped_ids'])==set(plan['scoped_ids'])
    assert not {r['facts']['artwork_id'] for r in prior['records']}&{r['facts']['artwork_id'] for r in plan['records']}
    # prepare revalidated the full prior118 operation before capturing every row
    # and relation. The exact successor delta proves these118 remain intact.
    return {**plan['prior_verification'],'current_counts':result['current_counts'],'successor_verified':True}


def apply(expected_sha):
    plan,digest=validate_plan();assert digest==expected_sha;ids=[r['facts']['artwork_id'] for r in plan['records']]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():
            verify(db,plan,digest);print('Unchanged replay: six date enrichments, five holdings; zero writes',flush=True);return
        assert w.snapshot(db,plan['scoped_ids'])==plan['before'];identity_state(db,m.load(SCOPE))
        m.save(m.BACKUP/(KEY+'-preimages.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,'museum-expansion-20261006-'+KEY,'Government Art Collection native creation-date enrichment, 7 October 2026','collection_page','https://artcollection.dcms.gov.uk/'))
        for r in plan['records']:
            f=r['facts'];p=f['patch'];aid=f['artwork_id'];rc=r['source']['capture']['receipt']
            db.execute('UPDATE artworks SET date_display=%s,creation_year_start=%s,creation_year_end=%s,date_precision=%s,updated_by=%s WHERE id=%s',(p['date_display'],p['creation_year_start'],p['creation_year_end'],p['date_precision'],m.ACTOR,aid))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_date_enrichment',%s,%s,%s,%s,%s,%s)",(aid,SID,f['inventory'],f['source_url'],note(r,digest),rc['retrieved_at'],m.ACTOR))
            if f['accept_holding']:
                db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['holding_id'],aid,IID,SID,f['source_url'],holding_note(r,digest),rc['retrieved_at']))
                old=next(x for x in plan['before']['assertions'] if x['artwork_id']==aid)
                db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(r['holding_id'],old['id']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=145,eligible=142)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,local_only=True,verification=result));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='apply':assert a.plan_sha;apply(a.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
