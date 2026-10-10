#!/usr/bin/env python3
"""Sixteen individually reviewed existing holdings; preserve complete prior state."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-armenia-wikiart-20261007.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
m=w.m;h=w.c.h;RUN=w.RUN;IID=w.IID;KEY='armenia-existing-holdings-002';SID=m.uid('source/'+KEY)
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'existing-holding-editorial-review-002.json'
MULES='0049c2da-bd83-51c9-a441-ac034b997d2b'
EXCLUDED={'Q55284022','Q55283902','Q61904289','Q77863193','Q28925577','Q28871584'}

def capture_body(cap):
    raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());r=cap['receipt']
    assert r['status']==200 and hashlib.sha256(raw).hexdigest()==r['sha256']
    assert r['url']==r['final_url'] and r['url'].startswith(('https://www.wikidata.org/','https://www.wikiart.org/','https://www.sarian.am/'))
    return raw

def source_rows():
    result={}
    for b in m.load(RUN/'existing-holding-current-entities-002.json.gz')['batches']:
        entities=json.loads(capture_body(b['capture']))['entities'];assert entities==b['entities'] and set(entities)==set(b['ids'])
        for qid,e in entities.items():result[qid]=dict(entity=e,capture=b['capture'])
    return result

def one(e,p):return h.singleton(e,p)
def val(e,p):return h.value(one(e,p))

def facts(e,art,creator_qid):
    assert e['id'] not in EXCLUDED
    assert art['current_institution_id'] is None
    for prop in ['P170','P195','P571']:
        statement=one(e,prop);allowed={'P217'} if prop=='P195' else set()
        assert not set(statement.get('qualifiers',{}))-allowed,'Unreviewed source qualifier'
    assert val(e,'P170')['id']==creator_qid and val(e,'P195')['id']=='Q2087788'
    for prop in ['P276','P127']:
        if h.best(e,prop):
            statement=one(e,prop);assert h.value(statement)['id']=='Q2087788'
            assert not set(statement.get('qualifiers',{}))-({'P217'} if prop=='P276' else set())
    # A qualified inventory is identity evidence, never a substituted unknown field.
    for prop in ['P195','P276']:
        for statement in h.best(e,prop):
            for q in statement.get('qualifiers',{}).get('P217',[]):
                inv=q.get('datavalue',{}).get('value');assert isinstance(inv,str) and inv
                if art['accession_number'] is not None:assert inv==art['accession_number']
    if h.best(e,'P217'):
        inv=one(e,'P217');assert not set(inv.get('qualifiers',{}))-{'P195'}
        for q in inv.get('qualifiers',{}).get('P195',[]):assert q['datavalue']['value']['id']=='Q2087788'
        assert art['accession_number']==h.value(inv)
    else:assert art['accession_number'] is None
    titles=[v['value'] for v in e.get('labels',{}).values()]+[v['value'] for a in e.get('aliases',{}).values() for v in a]
    assert m.norm(art['title']) in {m.norm(t) for t in titles}
    d=val(e,'P571');assert d['precision']>=9 and d['before']==d['after']==0 and d['time'].startswith('+')
    assert d['calendarmodel']=='http://www.wikidata.org/entity/Q1985727'
    year=int(d['time'][1:5]);assert 100<=year<=1970
    assert (art['creation_year_start'],art['creation_year_end'],art['date_precision'])==(year,year,'exact')
    assert {h.value(s)['id'] for s in h.best(e,'P31')}=={'Q3305213'}
    assert not any(h.best(e,p) for p in ['P518','P361','P1877'])
    return dict(artwork_id=art['id'],qid=e['id'],title=art['title'],year=year,inventory=art['accession_number'],creator_qid=creator_qid,source_record_id=e['id'],source_url='https://www.wikidata.org/wiki/'+e['id'])

def records():
    scope=m.load(RUN/'existing-holding-followup-002.json.gz');arts={r['id']:r for r in scope['before']['artworks']};sources=source_rows();out=[]
    for decision in m.load(REVIEW)['decisions']:
        if decision['decision']!='accept_holding':continue
        aid=decision['artwork_id'];art=arts[aid]
        creators=[r for r in scope['before']['artists'] if r['artwork_id']==aid]
        assert len(creators)==1 and creators[0]['attribution_role']=='primary'
        authorities=[r['external_id'] for r in scope['artist_identifiers'] if r['entity_id']==creators[0]['artist_id'] and r['scheme']=='wikidata']
        assert decision['creator_qid'] in authorities and 0.8<=decision['confidence']<=1
        if aid==MULES:
            obj=m.load(RUN/'sarian-object-captures-001/008.json');parsed=w.c.a.s.captions(capture_body(obj['capture']))
            assert parsed==([w.c.a.s.clean(t) for t in obj['title_fields']],[w.c.a.s.clean(t) for t in obj['detail_fields']])
            f=w.c.a.s.fields(obj,8);assert f['first']==f['last']==1910 and f['dimensions']=='36.5x70 cm'
            assert art['title']=='Mules, laden with hay' and art['creation_year_start']==art['creation_year_end']==1910
            facts_row=dict(artwork_id=aid,qid=None,title=art['title'],year=1910,inventory=None,creator_qid=decision['creator_qid'],source_record_id='other_natgalleryarm_ger_8',source_url=obj['entry']['url'])
            source=dict(capture=obj['capture'],artist_museum_object=obj)
        else:
            source=sources[decision['qid']];facts_row=facts(source['entity'],art,decision['creator_qid'])
        out.append(dict(facts=facts_row,decision=decision,source=source,holding_id=m.uid(KEY+'/'+aid)))
    assert len(out)==16 and len({r['facts']['artwork_id'] for r in out})==16
    return out

def validate_plan():
    p=m.load(PLAN)
    for ref in p['evidence']:w.checked_reference(ref)
    assert p['records']==records()
    return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()

def note(r,digest):return json.dumps(dict(plan_sha256=digest,evidence=r,policy='Holding only; preserve existing catalogue metadata, unknowns, artist/media links and publication status.'),ensure_ascii=False)

def holding_note(r,digest):
    d=r['decision'];return d['basis']+' Editorial confidence '+str(d['confidence'])+' (not a calibrated probability). '+d['limitation']+' Collection association only, without legal ownership, physical custody or current display. Plan SHA-256 '+digest

def prepare():
    assert not PLAN.exists();selected=records();target_ids={r['facts']['artwork_id'] for r in selected}
    scope=m.load(RUN/'existing-holding-followup-002.json.gz');old_ids=set(m.load(RUN/'armenia-wikiart-001-before.json')['scoped_ids'])
    prior_plans=[]
    for importer in [w.c.a,w]:
        p,d=importer.validate_plan();old_ids|={r['artwork_id'] for r in p['records']};prior_plans.append(dict(source=importer.SOURCE,plan_sha256=d,path=str(importer.PLAN.relative_to(m.ROOT)),new_ids=[r['artwork_id'] for r in p['records']]))
    ids=sorted(old_ids|{r['id'] for r in scope['artist_scope']['artworks']}|{r['row']['id'] for r in scope['unlinked']}|target_ids)
    with m.connect() as db:
        prior=w.verify(db,*w.validate_plan());before=h.snapshot(db,ids)
        assert h.snapshot(db,[r['id'] for r in scope['before']['artworks']])==scope['before'],'Research snapshot changed'
        assert prior['current_counts']==dict(linked=184,eligible=183)
        for r in selected:
            aid=r['facts']['artwork_id'];art=next(x for x in before['artworks'] if x['id']==aid)
            assert art['current_institution_id'] is None and art['status']=='review' and art['published_at'] is None
            claims=[x for x in before['assertions'] if x['artwork_id']==aid]
            assert all(x['institution_id']==IID and x['claim_type']=='holding' and x['context']=='collection' and x['review_state']=='review' and not x['superseded_by'] for x in claims)
    names=['existing-holding-followup-002.json.gz','existing-holding-current-entities-002.json.gz','existing-holding-editorial-review-002.json','sarian-existing-version-review-captures-001.json','existing-holding-version-comparisons-002.json','zakarian-orsay-comparison-001.json','wikiart-followup-review-001.json','wikiart-bashinjaghian-followup-001.json']
    p=dict(at=m.now(),records=selected,before=before,scoped_ids=ids,prior_verification=prior,prior_plans=prior_plans,evidence=[w.reference(RUN/n) for n in names]+[w.reference(Path(__file__).resolve())],policy='Sixteen selected existing museum links after individual source/version review. Mostly Wikidata evidence with explicit limitations; unknown inventories remain NULL. Two artist-museum captions and the approved WikiArt Harem page supplement exact object identities. No changes to metadata, dates, artists, images or publication.')
    m.save(PLAN,p);print('Pinned 16 holdings',hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)

def verify(db,plan,digest):
    after=h.snapshot(db,plan['scoped_ids']);before=plan['before'];targets={r['facts']['artwork_id'] for r in plan['records']}
    byid={r['id']:r for r in after['artworks']};assert set(byid)=={r['id'] for r in before['artworks']}
    for old in before['artworks']:
        new=byid[old['id']];ignored={'current_institution_id','updated_at'} if old['id'] in targets else set()
        assert {k:v for k,v in old.items() if k not in ignored}=={k:v for k,v in new.items() if k not in ignored}
        if old['id'] in targets:assert new['current_institution_id']==IID
    for key in ['artists','media','identifiers','museum']:assert after[key]==before[key],key
    assert [r for r in after['citations'] if r['source_id']!=SID]==before['citations']
    newc={r['entity_id']:r for r in after['citations'] if r['source_id']==SID};newh={r['artwork_id']:r for r in after['assertions'] if r['source_id']==SID}
    assert set(newc)==set(newh)==targets
    assert len(after['citations'])==len(before['citations'])+16 and len(after['assertions'])==len(before['assertions'])+16
    for r in plan['records']:
        f=r['facts'];aid=f['artwork_id'];c=newc[aid];a=newh[aid]
        assert c['evidence_note']==note(r,digest) and c['source_record_id']==f['source_record_id'] and c['source_url']==f['source_url'] and c['field_name']=='museum_expansion_holding_reconciliation'
        assert a['id']==r['holding_id'] and a['claim_type']=='holding' and a['institution_id']==IID and a['review_state']=='accepted' and a['context']=='collection' and not a['superseded_by']
        assert a['source_url']==f['source_url'] and a['evidence_note']==holding_note(r,digest)
    expected_assertions=[dict(r,superseded_by=newh[r['artwork_id']]['id']) if r['artwork_id'] in targets else r for r in before['assertions']]
    assert [r for r in after['assertions'] if r['source_id']!=SID]==expected_assertions
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(list(targets),)).fetchone()['n']==16
    counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
    return dict(existing_artworks_linked=16,new_artworks=0,scoped_artwork_metadata_preserved=len(byid),old_citations_preserved=len(before['citations']),artist_links_preserved=len(before['artists']),media_links_preserved=len(before['media']),identifiers_preserved=len(before['identifiers']),old_assertions_preserved=len(before['assertions']),prior_assertions_superseded=sum(r['artwork_id'] in targets for r in before['assertions']),new_citations=16,current_counts=counts,new_images=0,new_publications=0,new_display_claims=0)

def verify_prior_additions(db,importer,p,digest):
    plan,holding_digest=validate_plan();result=verify(db,plan,holding_digest)
    pin=next(r for r in plan['prior_plans'] if r['source']==importer.SOURCE)
    assert digest==pin['plan_sha256'] and {r['artwork_id'] for r in p['records']}==set(pin['new_ids'])
    assert set(pin['new_ids'])<=set(plan['scoped_ids']) and not set(pin['new_ids'])&{r['facts']['artwork_id'] for r in plan['records']}
    # prepare ran the complete prior WikiArt/Sarian verifier, then saved complete
    # rows and all related evidence. Exact successor comparison proves those
    # verified rows and relations remain intact after the sixteen holding deltas.
    return dict(verified_new_records=len(p['records']),all_prior_rows_and_relations_unchanged=True,current_counts=result['current_counts'],successor_snapshot_verification=result)

def apply(digest):
    plan,actual=validate_plan();assert actual==digest;ids=[r['facts']['artwork_id'] for r in plan['records']]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        t=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert t['db']=='artline' and t['addr'] in [None,'127.0.0.1','::1'] and t['port'] in [None,5432]
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,plan,digest);print('Unchanged replay: 16 holdings; zero writes',flush=True);return
        assert h.snapshot(db,plan['scoped_ids'])==plan['before'],'Baseline changed'
        m.save(m.BACKUP/(KEY+'-preimages.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,'museum-expansion-20261006-'+KEY,'National Gallery of Armenia reviewed existing holdings, follow-up 7 October 2026','authority_data','https://www.wikidata.org/'))
        for r in plan['records']:
            f=r['facts'];aid=f['artwork_id'];rc=r['source']['capture']['receipt']
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_record_id'],f['source_url'],note(r,digest),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['holding_id'],aid,IID,SID,f['source_url'],holding_note(r,digest),rc['retrieved_at']))
            for old in plan['before']['assertions']:
                if old['artwork_id']==aid:db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(r['holding_id'],old['id']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=200,eligible=199)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,local_only=True,verification=result));print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
