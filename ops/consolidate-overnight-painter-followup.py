#!/usr/bin/env python3
"""Resolve eleven held painter pairs against individually inspected museums."""
import argparse,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-painters.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;BASE=m.x.BASE/'duplicates';c.RUN=BASE/'painter-primary-followup';c.SOURCE='overnight-person-primary-followup-20260913';m.BACKUPS=m.BACKUPS/'painter-primary-followup'

def plan():
    path=c.RUN/'plan.json'
    if path.exists():return
    held=json.loads((BASE/'painter-consolidation/holds.json').read_text());entries=[];holds=[]
    for h in held:
        r=h['review'];q=h['qid'];p=BASE/'remaining-person-primary'/(q+'.html');raw=p.read_bytes();receipt=json.loads(p.with_suffix('.receipt.json').read_text());assert receipt['status']==200 and m.m.core.sha(raw)==receipt['sha256']
        soup=BeautifulSoup(raw,'html.parser')
        for node in soup(['script','style','nav','footer']):node.decompose()
        text=soup.get_text(' ',strip=True);birth,death=r['life']
        if q=='Q762544':assert all(t in text for t in ('Pierre Gobert','Geburtsjahr 1662','Sterbejahr 1744'))
        elif q=='Q57584612':assert all(t in text for t in ('Brouardel, Laure','30–03–1852','31–12–1935'))
        else:
            assert re.search(r'Auteur\s+.{0,100}?\('+str(birth)+'-'+str(death)+r'\)',text),(q,'Exact primary creator name/lifespan not found')
        context='Individually reviewed museum creator identity and closed source chronology; original numeric date fields preserved.'
        if q=='Q11879':context+=' Getty lists1630or1631; Fécamp primary catalogue uses1631–1705. The original two catalogue dates already agree; no chronology is overwritten.'
        if q=='Q2871029':context+=' Getty1806–1867 conflicts with primary Musée Grobet-Labadié1814–1865. Do not add the questionable Getty crosswalk or alter the two matching original museum-based timelines.'
        if q=='Q527919':context+=' Getty explicitly labels1624 as baptism, while museum creator fields use1624–1700. Merge identity only; preserve original dates and the baptism qualification in evidence.'
        e=dict(qid=q,old_slug=r['slugs'][0],canonical_slug=r['slugs'][1],life=r['life'],evidence=dict(primary_url=receipt['url'],primary_person_facts=dict(receipt=receipt,life=r['life'],names=r['names']),primary_preferred_biography=context,country_code=None,basis=context),targets={})
        for target in ('local','production'):
            with m.m.r.base.connect(target=='production') as db,db.transaction():
                db.execute('SET TRANSACTION READ ONLY');deps=c.dependencies(db)
                rows={r['row']['slug']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],))};assert len(rows)==2
                old=rows[e['old_slug']];keep=rows[e['canonical_slug']]
                assert all(a['status']=='review' and a['published_at'] is None and a['entity_type']=='person' and [a['birth_year'],a['death_year']]==e['life'] for a in (old,keep))
                assert m.f.names.namekey(old['display_name'])==m.f.names.namekey(keep['display_name']) and not old['biography_md'] and not old['portrait_media_id']
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(keep['id'],q)).fetchone()
                citations=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s",(old['id'],)).fetchall();assert citations
                e['targets'][target]=dict(old_id=old['id'],canonical_id=keep['id'],old_signature=c.signature(old),canonical_signature=c.signature(keep),overlaps=c.overlaps(db,old['id'],keep['id'],deps),museum_creator_evidence=citations,dependencies=deps)
        if any(t['overlaps'] for t in e['targets'].values()):holds.append(e);continue
        assert e['targets']['local']['old_signature']==e['targets']['production']['old_signature'] and e['targets']['local']['canonical_signature']==e['targets']['production']['canonical_signature'];entries.append(e)
    m.m.core.save_new(path,entries);m.m.core.save_new(c.RUN/'holds.json',holds);manifest=dict(at=m.m.core.now(),plan_sha256=m.m.core.sha(path.read_bytes()),confirmed_pairs=len(entries),held_pairs=len(holds),policy='Individually inspected primary museum records corroborate full creator identity and existing closed timelines. Preserve all artwork, image, alias, authority, country and citation rows; archive redundant profile and redirect old slug. No publication.');m.m.core.save_new(c.RUN/'manifest.json',manifest);print(manifest,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();(plan if a.command=='plan' else getattr(c,a.command))()
