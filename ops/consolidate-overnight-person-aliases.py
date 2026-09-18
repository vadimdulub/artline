#!/usr/bin/env python3
"""Four primary-corroborated painter aliases discovered during country review."""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-painters.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;BASE=m.x.BASE/'duplicates';c.RUN=BASE/'person-alias-consolidation';c.SOURCE='overnight-person-alias-primary-20260913';m.BACKUPS=m.BACKUPS/'person-alias-consolidation'
PAIRS=[
 ('Q1349819','nikolai-nikanorovits-dubovskoi-round2-27449f201aa6','nikolay-nikanorovich-dubovskoy-q1349819','dubovskoy',['Дубовской Николай Никанорович','1859','1918','Dubovski, Nikolai Nikanorovich']),
 ('Q372277','aleksei-bogoljubov-round2-e67e4865ae5d','alexey-bogolyubov-q372277','bogolyubov',['Алексей Петрович Боголюбов','1824','1896']),
 ('Q468632','il-calabrese-round2-120e6c1234e7','mattia-preti-q468632','preti-louvre',['Preti, Mattia dit aussi Il Calabrese','1613','1699']),
 ('Q539078','gilbert-soest-research-d9380db98ec6','gerard-soest-nga-1887','soest',['Soest, Gerard (ou Gilbert)','vers 1600','1681'])]

def plan():
    if (c.RUN/'plan.json').exists():return
    entries=[]
    for q,oldslug,keepslug,name,facts in PAIRS:
        path=BASE/'redirect-person-primary'/(name+'.html');raw=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert m.m.core.sha(raw)==receipt['sha256'] and receipt['status']==200
        text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert all(f in text for f in facts),(q,'primary facts missing')
        ev=dict(primary_url=receipt['url'],primary_person_facts=dict(receipt=receipt,reviewed_facts=facts),primary_preferred_biography='Primary museum explicitly identifies the same named painter or alias. Original chronology and biographical fields retained.',country_code=None,basis='Individual museum alias/full-name evidence, original creator citations and existing exact Wikidata identity corroborate one person; no name-only merge.')
        if q=='Q539078':
            wiki=json.loads((m.x.r.RUN/'entities'/f'{q}.json').read_text());assert 'gilbert-soest-511' in m.m.r.values(wiki['entity'],'P2741')
            ev.update(authority_crosswalk=dict(wikidata=q,tate_person='511',receipt=wiki['receipt']),chronology='Tate-imported1605 is not treated as exact against primary circa1600. Canonical unknown birth/death fields and archived original fields remain unchanged; this is identity consolidation only.')
        e=dict(qid=q,old_slug=oldslug,canonical_slug=keepslug,evidence=ev,targets={})
        for target in ('local','production'):
            with m.m.r.base.connect(target=='production') as db,db.transaction():
                db.execute('SET TRANSACTION READ ONLY');deps=c.dependencies(db)
                rows={r['row']['slug']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',([oldslug,keepslug],))};assert len(rows)==2
                old=rows[oldslug];keep=rows[keepslug];assert all(a['status']=='review' and a['published_at'] is None and a['entity_type']=='person' for a in (old,keep));assert not old['biography_md'] and not old['portrait_media_id']
                if q!='Q539078':assert [old['birth_year'],old['death_year']]==[keep['birth_year'],keep['death_year']]
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(keep['id'],q)).fetchone()
                museum=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s",(old['id'],)).fetchall();assert museum
                issues=c.overlaps(db,old['id'],keep['id'],deps);assert not issues,(q,target,issues)
                e['targets'][target]=dict(old_id=old['id'],canonical_id=keep['id'],old_signature=c.signature(old),canonical_signature=c.signature(keep),overlaps=issues,museum_creator_evidence=museum,dependencies=deps)
        assert e['targets']['local']['old_signature']==e['targets']['production']['old_signature'] and e['targets']['local']['canonical_signature']==e['targets']['production']['canonical_signature'];entries.append(e)
    m.m.core.save_new(c.RUN/'plan.json',entries);m.m.core.save_new(c.RUN/'manifest.json',dict(at=m.m.core.now(),plan_sha256=m.m.core.sha((c.RUN/'plan.json').read_bytes()),confirmed_pairs=len(entries)));print('Primary alias painter plan',len(entries),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);args=p.parse_args();(plan if args.command=='plan' else getattr(c,args.command))()
