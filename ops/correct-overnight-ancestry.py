#!/usr/bin/env python3
"""Remove two own-run country inferences that incorrectly used ancestry."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=m.x.BASE/'country-context-corrections'
raw=(RUN/'ancestry-correction-plan.json').read_bytes();data=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'ancestry-correction-manifest.json').read_text())['plan_sha256']
for target in ('local','production'):
    dest=RUN/f'ancestry-correction-{target}-verified.json'
    if dest.exists():continue
    with m.m.r.base.connect(target=='production') as db:
        with db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,'overnight-ancestry-context-correction-20260913','Country review: ancestry is distinct from cultural affiliation','authority_data','https://www.wikidata.org/')
            for e in data['entries']:
                old=data['targets'][target][e['slug']];aid=old['row']['id'];qid=e['slug'].rsplit('-',1)[-1].upper();db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(aid,))
                done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone()
                if done:continue
                assert g.c.selected(db,[{'artist':{'slug':e['slug']}}])[e['slug']]==old
                assert db.execute("DELETE FROM artist_countries WHERE artist_id=%s AND country_code='DE' AND relationship_type='cultural_affiliation' AND note=%s",(aid,e['unsupported_relation']['note'])).rowcount==1
                m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='geography',source_record_id=qid,source_url='https://www.wikidata.org/wiki/'+qid,retrieved_at=CORE.now(),created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,correction=e,publication_status='review'),ensure_ascii=False)))
                db.execute('UPDATE artists SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(m.m.ACTOR,aid))
        with db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in data['entries']])
            for e in data['entries']:
                old=data['targets'][target][e['slug']];now=rows[e['slug']];ignore={'revision','updated_at','updated_by'}
                assert {k:v for k,v in old['row'].items() if k not in ignore}=={k:v for k,v in now['row'].items() if k not in ignore}
                assert now['authorities']==old['authorities'] and now['countries']==[c for c in old['countries'] if c['country_code']!='DE']
    CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,corrections=2,original_descriptions_dates_status_preserved=True));print(target,'ancestry corrections verified',flush=True)
