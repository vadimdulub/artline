#!/usr/bin/env python3
"""Two museum-corroborated corrections, separated from identity consolidation."""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
from psycopg import sql
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'duplicates/primary-person-date-corrections';SOURCE='overnight-primary-person-date-corrections-20260913'
CASES=[('wikimedia-painter-q326167','roll-louvre','ROLL Alfred (1846-1919)',{'birth_year':1846,'birth_precision':'exact'},'PrimaryLouvrecreator and Gettypreferred1846–1919 corroborate correction of numericbirth1845; existing biography already1846.'),('wikimedia-painter-q63323783','laura-henner','LE ROUX ou LEROUX ou LEROUX-REVAULT Laura (1872-1936)',{'death_year':1936,'death_precision':'exact','biography_md':'Laura Leroux-Revault (1872–1936) was a French painter. The Musée national Jean-Jacques Henner identifies her as a pupil of Henner and the wife of Louis Revault.\n\nSource: [Musée national Jean-Jacques Henner](https://musee-henner.fr/repertoire-des-eleves). Biography remains in review.'},'PrimaryHenner1872–1936, PrinceriecatalogueandGettypreferred corroborate1936. Gettyolder1930 was activity, not death. Original incorrect short authority biography preserved in backup/citation.')]
def plan():
 if (RUN/'plan.json').exists():return
 entries=[]
 for slug,key,fact,updates,note in CASES:
  path=m.x.BASE/'duplicates/name-date-primary/followup'/(key+'.html');receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert CORE.sha(path.read_bytes())==receipt['sha256'];assert fact in BeautifulSoup(path.read_bytes(),'html.parser').get_text(' ',strip=True)
  e=dict(slug=slug,updates=updates,note=note,primary=receipt,reviewed_fact=fact,targets={})
  for target in ('local','production'):
   with m.m.r.base.connect(target=='production') as db,db.transaction():
    db.execute('SET TRANSACTION READ ONLY');row=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=%s',(slug,)).fetchone()['row'];assert row['status']=='review' and row['published_at'] is None
    assert row['birth_year']==1845 if key=='roll-louvre' else row['death_year']==1930
    e['targets'][target]=row
  assert all(e['targets']['local'][k]==e['targets']['production'][k] for k in ('slug','birth_year','death_year','biography_md','status'));entries.append(e)
 for target in ('local','production'):CORE.save_new(m.BACKUPS/('primary-person-date-corrections-'+target+'.json'),{e['slug']:e['targets'][target] for e in entries})
 CORE.save_new(RUN/'plan.json',entries);CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/'plan.json').read_bytes()),painters=2))
def apply():
 raw=(RUN/'plan.json').read_bytes();entries=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256']
 for target in ('local','production'):
  dest=RUN/(target+'-verified.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Primary museum painter chronology corrections','authority_data','https://collections.louvre.fr/')
    for e in entries:
     old=e['targets'][target];aid=old['id']
     if db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
     assert db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']==old
     fields=e['updates'];query=sql.SQL('UPDATE artists SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in fields));db.execute(query,(*fields.values(),m.m.ACTOR,aid))
     m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,field_name='chronology',source_id=sid,source_record_id=e['slug'],source_url=e['primary']['url'],retrieved_at=e['primary']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary=e['primary'],reviewed_fact=e['reviewed_fact'],context=e['note'],before={k:old[k] for k in fields},updates=fields,publication='review'),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY')
    for e in entries:
     old=e['targets'][target];now=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s',(old['id'],)).fetchone()['row'];expected={**old,**e['updates']};ignore={'revision','updated_at','updated_by'};assert {k:v for k,v in now.items() if k not in ignore}=={k:v for k,v in expected.items() if k not in ignore}
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,painters_verified=2,review_preserved=True));print(target,'primary person dates verified2',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
