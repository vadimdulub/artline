#!/usr/bin/env python3
"""Apply individually reviewed primary cultural affiliations without replacing others."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=m.x.BASE/'country-context-corrections/primary-additions';SOURCE='overnight-primary-country-additions-20260913'
SOURCE_NAME='Individually reviewed primary museum cultural affiliation context'
SOURCE_ROOT='https://artsandculture.google.com/partner/national-art-museum-of-ukraine'
def plan():
    p=RUN/'plan.json'
    if p.exists():return
    entries=json.loads((RUN/'reviewed-evidence.json').read_text())['entries'];targets={}
    for e in entries:
        assert e['reviewed'] and e['country_relationship']=='cultural_affiliation'
        for proof in e['evidence']:
            raw=(m.x.ROOT/proof['capture_path']).read_bytes();assert CORE.sha(raw)==proof['capture_sha256']
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
            for e in entries:
                a=rows[e['slug']];assert a['row']['status']=='review' and a['row']['published_at'] is None
                assert (a['row']['birth_year'],a['row']['death_year'])==tuple(e['identity_lifespan'])
                assert dict(scheme='wikidata',id=e['qid']) in a['authorities']
                assert not any(c['country_code']==e['add_code'] and c['relationship_type']=='cultural_affiliation' for c in a['countries'])
                assert db.execute('SELECT 1 FROM countries WHERE code=%s',(e['add_code'],)).fetchone()
        targets[target]=rows;CORE.save_new(m.BACKUPS/f'primary-country-additions-{target}-preimages.json',rows)
    for e in entries:assert g.signature(targets['local'][e['slug']])==g.signature(targets['production'][e['slug']])
    CORE.save_new(p,dict(at=CORE.now(),entries=entries,targets=targets));CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(p.read_bytes()),painters=len(entries)));print('Primary country plan',len(entries),flush=True)
def apply():
    raw=(RUN/'plan.json').read_bytes();data=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256']
    for target in ('local','production'):
        path=RUN/f'{target}-verified.json'
        if path.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,SOURCE_NAME,'collection_page',SOURCE_ROOT)
                for e in data['entries']:
                    old=data['targets'][target][e['slug']];aid=old['row']['id'];db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(aid,))
                    if db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
                    assert g.c.selected(db,[{'artist':{'slug':e['slug']}}])[e['slug']]==old
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(aid,e['add_code'],e['conclusion']))
                    for proof in e['evidence']:
                        m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='geography',source_record_id=e['qid'],source_url=proof['url'],retrieved_at=proof['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,evidence=e,publication_status='review'),ensure_ascii=False)))
                    db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,aid))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in data['entries']])
                for e in data['entries']:
                    old=data['targets'][target][e['slug']];now=rows[e['slug']];ignore={'geography_review_state','revision','updated_at','updated_by'}
                    assert {k:v for k,v in old['row'].items() if k not in ignore}=={k:v for k,v in now['row'].items() if k not in ignore}
                    assert old['authorities']==now['authorities'] and all(c in now['countries'] for c in old['countries'])
                    assert {(c['country_code'],c['relationship_type']) for c in now['countries']}=={(c['country_code'],c['relationship_type']) for c in old['countries']}|{(e['add_code'],'cultural_affiliation')}
        CORE.save_new(path,dict(at=CORE.now(),plan_sha256=pin,painters_verified=len(data['entries']),original_affiliations_dates_and_review_preserved=True));print(target,'primary cultural context verified',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
