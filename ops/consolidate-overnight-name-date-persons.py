#!/usr/bin/env python3
"""Individually corroborated painter identities with disputed source chronology.

Consolidation preserves every original chronology field; primary/source
discrepancies are retained in the canonical citation for a separate date review.
"""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-painters.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;BASE=m.x.BASE/'duplicates';EVIDENCE=BASE/'name-date-primary';c.RUN=BASE/'name-date-person-consolidation';c.SOURCE='overnight-name-date-person-identity-20260913';m.BACKUPS=m.BACKUPS/'name-date-person-consolidation'
REVIEWS={
 'Q1065745':('50110000440','Landon Charles-Paul (1760-1826)','French painter and writer, 1760-1826','Primary museum and Getty identify CharlesPaulLandon;1760/1761 birth uncertainty remains. Canonical unknown birth retained.'),
 'Q3059860':('02650002379','Faure Eugène (1822-1879)','French painter, 1822-1879','Museum author header1879 conflicts with its biographical detail1878; same named Grenoble painter. Canonical1878 retained; no imported Getty date overwrite.'),
 'Q326167':('06380004634','Roll Alfred Philippe (1846-1919)','French painter, 1846-1919','Full name and museum-linked works identify AlfredPhilippeRoll; primary1846 conflicts with canonical1845. Preserve dates during identity merge; separate correction review.'),
 'Q2979648':('09940004668','Régnier Nicolas (1591-1667)','Flemish painter, ca.1590-1667','NicolasRegnier/NiccoloRenieri authority aliases identify the same person. Circa1590/1591/1588 uncertainties retained; no modern country inferred from Flemish.'),
 'Q21638872':('M0540001126','Verschoot Bernard (1728-1783)','Flemish painter, 1728-1783','Same BernardVerschoot; Getty retains both1728 andRKD1727. Preserve canonical1727 and archived1728; no country reclassification.'),
 'Q63323783':('M0525000540','Leroux-Revault Laura (1872-1936)','French painter, 1872-1936','Same LauraLerouxRevault; Getty older1930 is an activity date while preferred and museum death1936. Preserve all fields during merge; separate death correction review.'),
 'Q16580735':('05290000327','Meiren Jan Baptist van der (1664-1708)','Flemish painter, 1664-ca.1708','Same JanBaptistvanderMeiren; circa1708 and1736 authority alternatives retained. Canonical death unknown stays unknown.'),
 'Q528968':('M0949001286','Zucchi Jacopo (1540-1590)','Italian painter, ca. 1540-1589/1590','Same JacopoZucchi; museum header1540–1590 and detail1541(?)–1589(?) plus multipleGettydatevariants retained. No chronology or country overwrite.'),
 'Q2055547':('000PE008168','Lorimier Henriette (1780-1850)','French painter, 1775-1854','Primary museum header1780–1850 conflicts with its own Paris1775–1854 biography. Gettypreferred matches canonical1775–1854; same uniqueHenrietteLorimier, not separate generations.'),
 'Q106859643':('09940005755','Pilliard Jacques (1811-1898)','French artist, 1814-1898','Primary header1811 conflicts with biographicaldetailJacquesDenisPilliardVienne1814–1898. Getty1814 corroborates same identity. Canonical unknown birth preserved.')}

def plan():
 if (c.RUN/'plan.json').exists():return
 groups=json.loads((BASE/'person-name-order-leads.json').read_text())['groups'];entries=[]
 for q,(oid,maker,bio,context) in REVIEWS.items():
  g=next(g for g in groups if any(any(e['scheme']=='wikidata' and e['id']==q for e in a['authorities']) for a in g['artists']));assert len(g['artists'])==2
  keep=next(a for a in g['artists'] if any(e['scheme']=='wikidata' and e['id']==q for e in a['authorities']));old=next(a for a in g['artists'] if a!=keep)
  gp=EVIDENCE/(q+'.html');gr=json.loads(gp.with_suffix('.json').read_text());assert m.m.core.sha(gp.read_bytes())==gr['receipt']['sha256'] and gr['receipt']['status']==200
  text=BeautifulSoup(gp.read_bytes(),'html.parser').get_text(' ',strip=True);assert bio in text
  wiki=json.loads((m.x.r.RUN/'entities'/(q+'.json')).read_text());assert gr['ulan'] in m.m.r.values(wiki['entity'],'P245')
  pp=EVIDENCE/'museum-objects/captures'/(oid+'.json');primary=json.loads(pp.read_text());assert m.m.core.sha(pp.with_suffix('.html').read_bytes())==primary['receipt']['sha256'] and primary['fields']['Auteur']==maker
  ev=dict(primary_url=primary['receipt']['url'],primary_person_facts=dict(museum=primary,getty=gr),primary_preferred_biography=bio,country_code=None,chronology=context,basis='Individually reviewed exact museum author identity, full-name authority alias and Getty/Wikidata crosswalk; conflicting chronology retained, not a name-only automatic merge.')
  e=dict(qid=q,old_slug=old['slug'],canonical_slug=keep['slug'],evidence=ev,targets={})
  for target in ('local','production'):
   with m.m.r.base.connect(target=='production') as db,db.transaction():
    db.execute('SET TRANSACTION READ ONLY');deps=c.dependencies(db);rows={r['row']['slug']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',([old['slug'],keep['slug']],))};assert len(rows)==2
    a=rows[old['slug']];b=rows[keep['slug']];assert all(x['status']=='review' and x['published_at'] is None and x['entity_type']=='person' for x in (a,b));assert not a['biography_md'] and not a['portrait_media_id']
    assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(b['id'],q)).fetchone()
    museum=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s",(a['id'],)).fetchall();assert museum
    issues=c.overlaps(db,a['id'],b['id'],deps);assert not issues,(q,target,issues)
    e['targets'][target]=dict(old_id=a['id'],canonical_id=b['id'],old_signature=c.signature(a),canonical_signature=c.signature(b),overlaps=issues,museum_creator_evidence=museum,dependencies=deps)
  assert e['targets']['local']['old_signature']==e['targets']['production']['old_signature'] and e['targets']['local']['canonical_signature']==e['targets']['production']['canonical_signature'];entries.append(e)
 m.m.core.save_new(c.RUN/'plan.json',entries);m.m.core.save_new(c.RUN/'manifest.json',dict(at=m.m.core.now(),plan_sha256=m.m.core.sha((c.RUN/'plan.json').read_bytes()),confirmed_pairs=len(entries)));print('Individual name/date identity plan',len(entries),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);args=p.parse_args();(plan if args.command=='plan' else getattr(c,args.command))()
