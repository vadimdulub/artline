#!/usr/bin/env python3
"""Four individually researched Finnish transliterations of existing painters.

Read-only planning; separate hash-approved application preserves every dependent
relationship and original biography/date value, including Akimov's date conflict.
"""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-painters.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;CORE=m.m.core;BASE=m.x.SESSION_BASE;ROOT=BASE/'duplicates/fng-person-second-pass';BACK=m.BACKUPS/'fng-person-second-pass'
c.RUN=ROOT;c.SOURCE=m.x.SESSION_NAME+'-fng-person-primary';c.SOURCE_ROOT='https://kokoelma.kansallisgalleria.fi/';m.BACKUPS=BACK
CASES={'Q4059515':('412079','67240','Q4059515',[1754,1814],[1755,1814],None),'Q2509630':('609681','60293','Q2509630-tretyakov',[1810,1885],[1810,1885],'BY'),'Q4372384':('609279','67570','Q4372384',[1832,1896],[1832,1896],None),'Q4257944':('526938','63943','Q4257944',[1841,1910],[1841,1910],None)}
def plan():
 if (ROOT/'plan.json').exists():return
 leads=json.loads((BASE/'duplicates/interim-deep-research/local-audit.json').read_text())['leads']['artwork_authority_crosswalk'];entries=[]
 for q,(oid,pid,primarykey,oldlife,keeplife,code) in CASES.items():
  primary=BASE/'duplicates/selected-primary'/(primarykey+'.review.json');ev=json.loads(primary.read_text());html=primary.with_name(primarykey+'.html');assert CORE.sha(html.read_bytes())==ev['receipt']['sha256'];text=BeautifulSoup(html.read_bytes(),'html.parser').get_text(' ',strip=True)
  if q=='Q2509630':assert 'Belarussian/Russian painter' in text and '1810' in text and 'Khrutsky' in text
  elif q=='Q4059515':assert all(t in text for t in ('АКИМОВ Иван Акимович','1754','1814'))
  elif q=='Q4372384':assert all(t in text for t in ('ПОПОВ Андрей Андреевич','1832','1896'))
  else:assert all(t in text for t in ('Карл Иоганн Лемох','1841','1910','русский жанровый живописец'))
  f=BASE/'duplicates/selected-primary/fng'/(oid+'.json');fng=json.loads(f.read_text());obj=fng['object'];people=[p for p in obj['people'] if p.get('role',{}).get('en')=='Artist'];assert len(people)==1;person=people[0];assert str(person['id'])==pid and not person.get('attribution') and [person['birthYear'],person['deathYear']]==oldlife
  lead=next(l for l in leads if l['museum_object_id']==oid);wp=Path(lead['entity_capture']);e=json.loads(wp.read_text());e=e.get('entity',e);assert oid in m.m.r.values(e,'P9834') and q in [v.get('id') for v in m.m.r.values(e,'P170') if isinstance(v,dict)]
  entry=dict(qid=q,evidence=dict(primary_url=ev['receipt']['url'],country_code=code,primary_person_facts=dict(primary_capture=str(html),primary_receipt=ev['receipt'],fng_object=obj,fng_receipt=fng['receipt'],fng_origin_capture=fng['origin_capture'],object_wikidata=lead['wikidata'],object_entity_sha256=CORE.sha(wp.read_bytes())),basis='Exact FNG person identifier and same physical-object P9834/P170 crosswalk, source-language full-name transliteration and independent museum/curatorial biography establish one person. Preserve all source fields and relationships. For Akimov, museum1754and existing1755birth remain explicit competing assertions; identity consolidation does not choose a new numeric birth. Lemoch German family origin does not replace explicit Russian cultural affiliation. Khrutsky Belarusian/Russian affiliation is explicit curatorial wording, not birth-place inference.'),targets={})
  for target in ('local','production'):
   with m.m.r.base.connect(target=='production') as db,db.transaction():
    db.execute('SET TRANSACTION READ ONLY');deps=c.dependencies(db)
    find=lambda scheme,ident:db.execute("SELECT to_jsonb(a) row FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme=%s AND e.external_id=%s",(scheme,ident)).fetchone()['row']
    old=find('fng-person',pid);keep=find('wikidata',q);assert old['id']!=keep['id'];assert all(x['status']=='review' and not x['published_at'] and x['entity_type']=='person' for x in (old,keep));assert [old['birth_year'],old['death_year']]==oldlife and [keep['birth_year'],keep['death_year']]==keeplife
    assert not old['biography_md'] and not old['portrait_media_id'];assert not c.overlaps(db,old['id'],keep['id'],deps)
    if code:assert db.execute('SELECT 1 FROM countries WHERE code=%s',(code,)).fetchone()
    source=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s",(old['id'],)).fetchall();assert source
    entry.update(old_slug=old['slug'],canonical_slug=keep['slug']);entry['targets'][target]=dict(old_id=old['id'],canonical_id=keep['id'],old_signature=c.signature(old),canonical_signature=c.signature(keep),overlaps=[],museum_creator_evidence=source,dependencies=deps)
  assert entry['targets']['local']['old_signature']==entry['targets']['production']['old_signature'] and entry['targets']['local']['canonical_signature']==entry['targets']['production']['canonical_signature'];entries.append(entry)
 CORE.save_new(ROOT/'plan.json',entries);pin=CORE.sha((ROOT/'plan.json').read_bytes());CORE.save_new(ROOT/'manifest.json',dict(at=CORE.now(),plan_sha256=pin,confirmed_pairs=len(entries)));print('FNG painter pairs planned',len(entries),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();plan() if a.command=='plan' else getattr(c,a.command)()
