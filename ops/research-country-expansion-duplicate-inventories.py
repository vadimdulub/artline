#!/usr/bin/env python3
"""Twenty scoped primary checks for unresolved existing catalogue overlaps.

Read-only real catalogue audit. Previously adjudicated exact pairs are excluded;
new work is bounded to the selected missing-inventory groups and museum pages.
"""
import importlib.util,json,hashlib,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-overnight-same-title-inventories.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
ROOT=r.m.x.SESSION_BASE/'duplicates/inventory-second-pass'
def select():
 path=ROOT/'selection.json'
 if path.exists():return json.loads(path.read_text())
 previous=r.m.x.ROOT/'docs/research/overnight-countries-20260913/duplicates/same-title-deep-review/final-pair-decisions.json'
 old=json.loads(previous.read_text());closed={frozenset((d['first_slug'],d['second_slug'])) for d in old['decisions']}
 audit=r.m.x.SESSION_BASE/'duplicates/interim-deep-research/local-audit.json';data=json.loads(audit.read_text());groups=[]
 for g in data['leads']['same_title_creator_institution']:
  if not any(not w['accession_number'] for w in g['works']):continue
  if frozenset(w['slug'] for w in g['works']) in closed:continue
  if g['key'][0] not in {'state-russian-museum','accademia-brera-collections','castello-sforzesco-graphic-collections','museo-poldi-pezzoli','musei-civici-arte-storia-brescia','pinacoteca-ambrosiana','accademia-carrara','musei-civici-pavia'}:continue
  groups.append(g)
 slugs=sorted({w['slug'] for g in groups for w in g['works']})
 with r.m.m.r.base.connect(False) as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
  rows=db.execute('SELECT id::text,slug,status FROM artworks WHERE slug=ANY(%s)',(slugs,)).fetchall();ids={w['slug']:w['id'] for w in rows};assert len(ids)==len(slugs) and all(w['status']=='review' for w in rows)
  citations=db.execute("SELECT entity_id::text,source_url,field_name,source_record_id FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND (source_url LIKE 'https://rusmuseumvrm.ru/%%' OR source_url LIKE 'http://rusmuseumvrm.ru/%%' OR source_url LIKE 'https://www.lombardiabeniculturali.it/%%')",(list(ids.values()),)).fetchall()
 for g in groups:
  for w in g['works']:w['id']=ids[w['slug']]
 out=dict(at=r.CORE.now(),groups=groups,citations=citations,unique_objects=len(slugs),prior_pair_review=str(previous),prior_pair_review_sha256=r.CORE.sha(previous.read_bytes()),current_audit_sha256=r.CORE.sha(audit.read_bytes()),policy='New research scopes on unresolved real catalogue objects; no test fixtures, writes or image republication. Previous170pair findings are not counted again.')
 r.CORE.save_new(path,out);return out

def main():
 data=select()
 for n in range(1,21):
  scope=data['groups'][n-1::20];assert scope,'Do not count empty research rounds';run=ROOT/f'round-{n:02}';ids={w['id'] for g in scope for w in g['works']};p=run/'candidates.json'
  if not p.exists():r.CORE.save_new(p,dict(at=r.CORE.now(),round=n,pairs=scope,citations=[c for c in data['citations'] if c['entity_id'] in ids]))
  r.RUN=run;r.main();print('Inventory research round',n,'groups',len(scope),'objects',len(ids),flush=True)
if __name__=='__main__':main()
