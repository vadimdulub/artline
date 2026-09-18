#!/usr/bin/env python3
"""Canonicalize five exact Wikidata person redirects without losing old IDs."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'duplicates/wikidata-person-redirects';SOURCE='overnight-wikidata-person-redirects-20260913'
QS=['Q110476382','Q110103899','Q66809948','Q104135165','Q109939748']

def selected(db,q):
    row=db.execute("SELECT to_jsonb(a) artist,to_jsonb(e) authority FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.external_id=%s AND e.scheme IN ('wikidata','wikidata-redirect')",(q,)).fetchone();assert row
    row['identifiers']=[r['row'] for r in db.execute("SELECT to_jsonb(e) row FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY e.id",(row['artist']['id'],))];return row

def plan():
    if (RUN/'plan.json').exists():return
    entries=[]
    for q in QS:
        path=m.x.r.RUN/'entities'/(q+'.json');ev=json.loads(path.read_text());entity=ev['entity'];assert entity['id']!=q and 'Q5' in [v.get('id') for v in m.m.r.values(entity,'P31') if isinstance(v,dict)]
        e=dict(old_qid=q,canonical_qid=entity['id'],capture=str(path.relative_to(m.x.ROOT)),capture_sha256=CORE.sha(path.read_bytes()),receipt=ev['receipt'],labels=m.m.r.labels(entity),targets={})
        for target in ('local','production'):
            with m.m.r.base.connect(target=='production') as db,db.transaction():
                db.execute('SET TRANSACTION READ ONLY');row=selected(db,q);a=row['artist'];assert a['status']=='review' and a['published_at'] is None
                assert row['authority']['scheme']=='wikidata' and m.f.names.namekey(a['display_name']) in {m.f.names.namekey(n) for n in e['labels']}
                for prop,field in [('P569','birth_year'),('P570','death_year')]:
                    value=m.m.r.year(entity,prop);assert value is None or a[field] is None or a[field]==value
                assert not db.execute('SELECT 1 FROM external_identifiers WHERE scheme=%s AND external_id=%s',('wikidata',entity['id'])).fetchone()
                assert not any(i['scheme']=='wikidata-redirect' for i in row['identifiers']);e['targets'][target]=row
        assert e['targets']['local']['artist']['slug']==e['targets']['production']['artist']['slug'];entries.append(e)
    CORE.save_new(RUN/'plan.json',entries);pin=CORE.sha((RUN/'plan.json').read_bytes());CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=pin,painters=len(entries)))
    for target in ('local','production'):CORE.save_new(m.BACKUPS/f'wikidata-person-redirects-{target}-preimages.json',{e['old_qid']:e['targets'][target] for e in entries})
    print('Five canonical person redirect plans prepared',flush=True)

def apply():
    raw=(RUN/'plan.json').read_bytes();pin=CORE.sha(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256'];qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    entries=json.loads(raw)
    for target in ('local','production'):
        dest=RUN/(target+'-verified.json')
        if dest.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Canonical Wikidata person redirects with archived identifier preservation','authority_data','https://www.wikidata.org/')
                for e in entries:
                    before=e['targets'][target];aid=before['artist']['id'];db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(aid,))
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='authority_redirect' AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone()
                    if done:continue
                    assert selected(db,e['old_qid'])==before
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(e['canonical_qid'],)).fetchone()
                    db.execute("UPDATE external_identifiers SET scheme='wikidata-redirect' WHERE id=%s AND scheme='wikidata'",(before['authority']['id'],))
                    m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=aid,scheme='wikidata',external_id=e['canonical_qid'],canonical_url='https://www.wikidata.org/wiki/'+e['canonical_qid'],source_id=sid,retrieved_at=e['receipt']['retrieved_at']))
                    m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='authority_redirect',source_record_id=e['old_qid'],source_url='https://www.wikidata.org/wiki/'+e['old_qid'],retrieved_at=e['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,old_qid=e['old_qid'],canonical_qid=e['canonical_qid'],receipt=e['receipt'],capture_sha256=e['capture_sha256'],decision='Exact authority redirect and same named person. Old external identifier row retained under wikidata-redirect; artist UUID, slug, country, biography, dates and review status unchanged. Lorenzo Costa birth uncertainty is not resolved by this identifier repair.'),ensure_ascii=False)))
                    db.execute('UPDATE artists SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(m.m.ACTOR,aid))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY')
                for e in entries:
                    before=e['targets'][target];now=selected(db,e['old_qid']);ignore={'revision','updated_at','updated_by'};assert {k:v for k,v in before['artist'].items() if k not in ignore}=={k:v for k,v in now['artist'].items() if k not in ignore}
                    ids={r['id']:r for r in now['identifiers']}
                    for row in before['identifiers']:assert ids[row['id']]=={**row,'scheme':'wikidata-redirect' if row['id']==before['authority']['id'] else row['scheme']}
                    assert len(now['identifiers'])==len(before['identifiers'])+1 and any(r['scheme']=='wikidata' and r['external_id']==e['canonical_qid'] for r in now['identifiers'])
        CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,painters_verified=len(entries),review_preserved=True));print(target,'canonical redirects verified',len(entries),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);args=p.parse_args();globals()[args.command]()
