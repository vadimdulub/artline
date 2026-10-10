#!/usr/bin/env python3
"""Reconcile selected existing Armenian museum holdings, locally and with full preimages."""
import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-armenia-apply-20261007.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m;RUN=a.RUN;IID=a.IID;KEY='armenia-existing-holdings-001';SID=m.uid('source/'+KEY)
PLAN=RUN/(KEY+'-plan.json.gz');TRIAGE=RUN/'existing-holding-editorial-review-001.json'
EXCLUDED={'Q77862688':'Same-creator Tiflis with unknown date and inventory 9849 requires a version check against inventory 370.',
 'Q77863193':'Same-creator Field Flowers with unknown date and inventory 1222 requires a version check against inventory 1154.'}

def best(entity,prop):
    rows=[r for r in entity['claims'].get(prop,[]) if r['rank']!='deprecated']
    return [r for r in rows if r['rank']=='preferred'] or rows

def value(statement):return statement.get('mainsnak',{}).get('datavalue',{}).get('value')
def singleton(entity,prop):
    rows=best(entity,prop);assert len(rows)==1 and value(rows[0]) is not None,(entity['id'],prop)
    return rows[0]

def facts(entity,record,creator):
    assert entity['id'] not in EXCLUDED
    selected={p:singleton(entity,p) for p in ['P195','P127','P276','P170','P217','P5210','P571']}
    for p,statement in selected.items():
        allowed={'P195'} if p=='P217' else set()
        assert not set(statement.get('qualifiers',{}))-allowed,'Unreviewed qualifier: '+p
    for p in ['P195','P127','P276']:assert value(selected[p])['id']=='Q2087788'
    iq=selected['P217'].get('qualifiers',{}).get('P195',[])
    assert len(iq)==1 and iq[0]['datavalue']['value']['id']=='Q2087788'
    assert creator['attribution_role']=='primary' and value(selected['P170'])['id'] in creator['wikidata_ids']
    inventory=value(selected['P217']);native_id=value(selected['P5210'])
    assert inventory==record['accession_number'] and re.fullmatch(r'\d+',inventory) and re.fullmatch(r'\d+',native_id)
    labels=[v['value'] for v in entity.get('labels',{}).values()]+[v['value'] for vals in entity.get('aliases',{}).values() for v in vals]
    assert m.norm(record['title']) in {m.norm(t) for t in labels},'Title identity changed'
    date=value(selected['P571']);assert date['precision']>=9 and date['before']==date['after']==0
    assert date['calendarmodel']=='http://www.wikidata.org/entity/Q1985727'
    year=int(date['time'][1:5]);assert 100<=year<=1970
    assert date['time'].startswith('+') and (record['creation_year_start'],record['creation_year_end'],record['date_precision'])==(year,year,'exact')
    types={value(x)['id'] for x in best(entity,'P31')}
    assert types and types<={'Q3305213','Q21281546'}
    assert not any(best(entity,p) for p in ['P518','P361','P1877']),'Component/copy/series needs review'
    assert record.get('current_institution_id') is None
    return dict(artwork_id=record['id'],qid=entity['id'],title=record['title'],creator_id=creator['artist_id'],creator_label=creator['display_name'],creator_qid=value(selected['P170'])['id'],inventory=inventory,native_work_id=native_id,year=year,source_url='https://www.wikidata.org/wiki/'+entity['id'],native_reference_url='https://www.gallery.am/en/database/item/'+native_id+'/',collection_claim=selected['P195'])

def source_rows():
    source=m.load(RUN/'existing-holding-current-entities-001.json.gz');result={}
    for batch in source['batches']:
        cap=batch['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());rc=cap['receipt']
        assert rc['status']==200 and rc['url'].startswith('https://www.wikidata.org/w/api.php?') and rc['final_url']==rc['url']
        assert hashlib.sha256(raw).hexdigest()==rc['sha256']
        entities=json.loads(raw)['entities'];assert entities==batch['entities'] and set(entities)==set(batch['ids'])
        for qid,entity in entities.items():result[qid]=dict(entity=entity,capture=cap)
    return result

def snapshot(db,ids):
    result={}
    queries={
      'artworks':'SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',
      'artists':'SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',
      'media':'SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',
      'identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
      'citations':"SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
      'assertions':'SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id'}
    for k,sql in queries.items():result[k]=[r['row'] for r in db.execute(sql,(ids,))]
    result['museum']=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(IID,)).fetchone()['row']
    return result

def reviewed_records():
    review=m.load(TRIAGE);sources=source_rows();creators={r['artwork_id']:r for r in m.load(RUN/'existing-holding-creator-identities-001.json')['rows']}
    records=[]
    for decision in review['decisions']:
        if decision['decision']!='accept_holding':continue
        qid=decision['qid'];src=sources[qid];record=decision['existing_record'];creator=creators[record['id']]
        f=facts(src['entity'],record,creator);assert f==decision['facts'] and decision['confidence']>=0.8
        records.append(dict(facts=f,decision=decision,**src,holding_id=m.uid(KEY+'/'+record['id'])))
    assert len(records)==136 and len({r['facts']['inventory'] for r in records})==136
    return records

def prepare():
    assert not PLAN.exists();records=reviewed_records();ids=[r['facts']['artwork_id'] for r in records]
    with m.connect() as db:
        before=snapshot(db,ids);assert len(before['artworks'])==136
        assert before['museum']['slug']==a.s.SLUG and before['museum']['canonical_institution_id'] is None
        for r in records:
            aid=r['facts']['artwork_id'];art=next(x for x in before['artworks'] if x['id']==aid)
            assert art['current_institution_id'] is None and art['status']=='review'
            assert not art['published_at']
            for k,v in r['decision']['existing_record'].items():
                if k in art:assert art[k]==v,(aid,k)
            claims=[x for x in before['assertions'] if x['artwork_id']==aid]
            assert len(claims)==1 and claims[0]['institution_id']==IID and claims[0]['claim_type']=='holding' and claims[0]['context']=='collection'
            assert claims[0]['review_state']=='review' and not claims[0]['superseded_by']
            assert claims[0]['source_url']==r['facts']['source_url']
            assert any(e['entity_id']==aid and e['scheme']=='wikidata' and e['external_id']==r['facts']['qid'] for e in before['identifiers'])
        counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone();assert counts==dict(linked=41,eligible=40)
        # Preserve and verify the pre-reconciliation Sarian checkpoint first.
        prior,digest=a.validate_plan();prior_verification=a.verify(db,prior,digest)
    refs=[a.reference(RUN/f) for f in ['existing-holding-current-entities-001.json.gz','existing-holding-followup-001.json.gz','existing-holding-creator-identities-001.json','existing-holding-duplicate-scope-001.json.gz','existing-holding-duplicate-leads-001.json','existing-holding-editorial-review-001.json']]
    refs += [a.reference(Path(__file__).resolve())]
    plan=dict(at=m.now(),records=records,before=before,before_counts=counts,prior_addition_verification=prior_verification,evidence=refs,policy='Local holding reconciliation only. User accepts >=80% editorial confidence. Exact current Wikidata object, native title, creator authority, inventory, creation year and unqualified museum collection agree. Mostly unreferenced community catalogue evidence, not a fresh native museum validation; this limitation stays explicit. Existing metadata, dates, makers, images and review/publication states remain unchanged. No legal-ownership or display claim.')
    m.save(PLAN,plan);print('Pinned',len(records),'existing holdings;',hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)

def validate_plan():
    raw=PLAN.read_bytes();plan=m.load(PLAN)
    for ref in plan['evidence']:a.checked_reference(ref)
    assert plan['records']==reviewed_records()
    return plan,hashlib.sha256(raw).hexdigest()

def note(record,digest):return json.dumps(dict(plan_sha256=digest,evidence=record,policy='Holding only; existing metadata and publication state preserved.'),ensure_ascii=False)

def holding_note(record,digest):
    d=record['decision']
    return 'Current Wikidata collection statement reviewed against exact existing object, creator authority, inventory, title and creation year. Editorial confidence '+str(d['confidence'])+'; not a calibrated probability. '+d['limitation']+' No present-display or legal-ownership assertion. Plan SHA-256 '+digest

def verify(db,plan,digest):
    ids=[r['facts']['artwork_id'] for r in plan['records']];after=snapshot(db,ids);before=plan['before'];byid={r['id']:r for r in after['artworks']}
    assert len(byid)==136
    for old in before['artworks']:
        new=byid[old['id']];assert new['current_institution_id']==IID
        assert {k:v for k,v in new.items() if k not in ['current_institution_id','updated_at']}=={k:v for k,v in old.items() if k not in ['current_institution_id','updated_at']}
    for key in ['artists','media','identifiers','museum']:assert after[key]==before[key],key
    oldc=[r for r in after['citations'] if r['source_id']!=SID];assert oldc==before['citations']
    newc={r['entity_id']:r for r in after['citations'] if r['source_id']==SID};assert len(newc)==136
    newh={r['artwork_id']:r for r in after['assertions'] if r['source_id']==SID};assert len(newh)==136
    assert len(after['assertions'])==len(before['assertions'])+136
    for r in plan['records']:
        f=r['facts'];aid=f['artwork_id'];c=newc[aid];h=newh[aid];rc=r['capture']['receipt']
        assert c['evidence_note']==note(r,digest) and c['source_record_id']==f['qid'] and c['source_url']==f['source_url']
        assert c['field_name']=='museum_expansion_holding_reconciliation'
        assert h['id']==r['holding_id'] and h['claim_type']=='holding' and h['institution_id']==IID and h['review_state']=='accepted' and h['context']=='collection' and not h['superseded_by']
        assert h['source_url']==f['source_url'] and h['evidence_note']==holding_note(r,digest)
        old=next(x for x in before['assertions'] if x['artwork_id']==aid)
        assert dict(old,superseded_by=r['holding_id']) in after['assertions']
    counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==136
    return dict(existing_artworks_linked=136,new_artworks=0,metadata_unchanged=136,old_citations_preserved=len(before['citations']),artist_links_preserved=len(before['artists']),media_links_preserved=len(before['media']),identifiers_preserved=len(before['identifiers']),prior_assertions_preserved_and_superseded=136,new_citations=136,current_counts=counts,new_images=0,new_publications=0,new_display_claims=0)

def apply(digest):
    plan,actual=validate_plan();assert actual==digest;ids=[r['facts']['artwork_id'] for r in plan['records']]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone()
        assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        existing=db.execute('SELECT count(*) n FROM artwork_location_assertions WHERE source_id=%s',(SID,)).fetchone()['n']
        if existing:
            assert existing==136;verify(db,plan,digest);print('Unchanged replay: 136 holdings; zero writes',flush=True);return
        assert snapshot(db,ids)==plan['before'],'Existing data changed; re-review required'
        assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
        m.save(m.BACKUP/(KEY+'-preimages.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,'museum-expansion-20261006-'+KEY,'National Gallery of Armenia existing holding review, 7 October 2026','authority_data','https://www.wikidata.org/'))
        for r in plan['records']:
            f=r['facts'];aid=f['artwork_id'];rc=r['capture']['receipt']
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",(aid,SID,f['qid'],f['source_url'],note(r,digest),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['holding_id'],aid,IID,SID,f['source_url'],holding_note(r,digest),rc['retrieved_at']))
            old=next(x for x in plan['before']['assertions'] if x['artwork_id']==aid)
            db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(r['holding_id'],old['id']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=177,eligible=176)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,local_only=True,verification=result))
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
