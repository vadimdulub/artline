#!/usr/bin/env python3
"""Add reviewed cultural affiliations while preserving documented birth countries."""
import argparse,collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=m.x.BASE/'country-gap-followup/birth-only-context';SOURCE='overnight-birth-cultural-context-20260913'
def plan():
    path=RUN/'plan.json'
    if path.exists():return
    research=json.loads((RUN/'research.json').read_text());records=research['records'];targets={};entries=[];held=[]
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':r['artist']['slug']}} for r in records]);countries={r['code'] for r in db.execute('SELECT code FROM countries')}
        targets[target]=rows
    for r in records:
        slug=r['artist']['slug'];codes=r['proposed_codes'];reasons=[]
        if not codes:reasons.append('no_corroborated_explicit_cultural_role')
        if set(codes)-countries:reasons.append('country_not_configured')
        e=r['entity'];qid=r['qid']
        if e.get('id')!=qid:reasons.append('source_authority_redirect_needs_identity_review')
        if not any(v.get('id')=='Q5' for v in m.m.r.values(e,'P31') if isinstance(v,dict)):reasons.append('not_human_person')
        for target in targets:
            row=targets[target][slug];a=row['row']
            if a['status']!='review' or a['published_at'] is not None or a['entity_type']!='person':reasons.append('not_unpublished_review_person')
            if any(c['relationship_type']=='cultural_affiliation' for c in row['countries']):reasons.append('cultural_context_changed')
            if dict(scheme='wikidata',id=qid) not in row['authorities']:reasons.append('authority_identity_changed')
            for field in ('birth','death'):
                if r['source_'+field] is not None and a[field+'_year'] is not None and r['source_'+field]!=a[field+'_year']:reasons.append('source_lifespan_conflict')
        if g.signature(targets['local'][slug])!=g.signature(targets['production'][slug]):reasons.append('cross_database_identity_context_differs')
        if reasons:held.append(dict(slug=slug,qid=qid,reasons=sorted(set(reasons)),description=r['description'],proposed_codes=codes));continue
        entries.append(dict(slug=slug,qid=qid,codes=codes,evidence=r))
    selected={t:{e['slug']:rows[e['slug']] for e in entries} for t,rows in targets.items()}
    for t,rows in selected.items():CORE.save_new(m.BACKUPS/f'birth-cultural-context-{t}-preimages.json',rows)
    CORE.save_new(path,dict(at=CORE.now(),entries=entries,holds=held,targets=selected));CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),painters=len(entries),affiliations=sum(len(e['codes']) for e in entries),countries=dict(collections.Counter(c for e in entries for c in e['codes'])),holds=len(held)));print('Birth-cultural plan',len(entries),'held',len(held),flush=True)
def apply():
    raw=(RUN/'plan.json').read_bytes();pin=CORE.sha(raw);data=json.loads(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256'];qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    held=qa.get('held_painters',{});assert set(held)<=set(e['slug'] for e in data['entries']);entries=[e for e in data['entries'] if e['slug'] not in held]
    for target in ('local','production'):
        done=RUN/f'{target}-verified.json'
        if done.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            for start in range(0,len(entries),40):
                with db.transaction():
                    db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Painter cultural affiliation distinguished from recorded birthplace','authority_data','https://www.wikidata.org/')
                    for e in entries[start:start+40]:
                        old=data['targets'][target][e['slug']];aid=old['row']['id'];db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(aid,))
                        if db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
                        assert g.c.selected(db,[{'artist':{'slug':e['slug']}}])[e['slug']]==old
                        for code in e['codes']:db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(aid,code,'Explicit cultural affiliation corroborated by Wikidata description and Wikipedia introductory artist role. The preexisting birth-country relation is preserved separately and is not used as nationality evidence. Nonexclusive; publication remains in review.'))
                        ev=e['evidence'];m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='geography',source_record_id=e['qid'],source_url=ev['biography']['url'],retrieved_at=ev['biography']['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,codes=e['codes'],description=ev['description'],biography=ev['biography'],entity_receipt=ev['entity_receipt'],existing_authority=e['qid'],country_relationships_preserved=old['countries'],publication_status='review'),ensure_ascii=False)))
                        db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,aid))
                print(target,'birth-cultural batch',start//40+1,'applied',flush=True)
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
                for e in entries:
                    old=data['targets'][target][e['slug']];now=rows[e['slug']];ignore={'geography_review_state','revision','updated_at','updated_by'}
                    assert {k:v for k,v in old['row'].items() if k not in ignore}=={k:v for k,v in now['row'].items() if k not in ignore}
                    assert old['authorities']==now['authorities'] and all(c in now['countries'] for c in old['countries'])
                    assert {(c['country_code'],c['relationship_type']) for c in now['countries']}=={(c['country_code'],c['relationship_type']) for c in old['countries']}|{(c,'cultural_affiliation') for c in e['codes']}
        CORE.save_new(done,dict(at=CORE.now(),plan_sha256=pin,painters_verified=len(entries),affiliations=sum(len(e['codes']) for e in entries),birth_relations_dates_review_and_authorities_preserved=True));print(target,'birth-cultural verified',len(entries),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
