#!/usr/bin/env python3
"""Fill missing inventory, medium and dimensions from 222 exact museum pages.

These objects were individually distinguished in 111 same-title pair reviews.
No chronology, creator, holding, display, country, image or status is changed.
"""
import argparse,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;ROOT=m.x.BASE/'russian-primary-inventory-followup';SOURCE='overnight-russian-primary-inventory-20260913'
def plan(target):
 path=ROOT/(target+'-plan.json')
 if path.exists():return
 reviewed=[]
 for p in sorted((m.x.BASE/'duplicates/same-title-deep-review/inventory-review').glob('*.json')):
  r=json.loads(p.read_text());e=r['reviews'][0]
  if 'rusmuseumvrm.ru' not in e.get('receipt',{}).get('url',''):continue
  assert len(r['reviews'])==1 and e['title_matches'] and e['inventory'] and e['medium'] and e['dimensions'];assert CORE.sha(Path(e['capture']).read_bytes())==e['receipt']['sha256'];reviewed.append(r)
 assert len(reviewed)==222 and len({r['reviews'][0]['inventory'] for r in reviewed})==222
 entries=[];holds=[]
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
  for r in reviewed:
   e=r['reviews'][0];row=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',(r['slug'],)).fetchone();assert row;w=row['row'];assert w['status']=='review' and w['published_at'] is None and m.m.r.norm(w['title'])==m.m.r.norm(e['title']) and w['current_institution_id']
   assert db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND rtrim(source_url,'/')=%s",(w['id'],e['receipt']['url'].rstrip('/'))).fetchone()
   assert db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(w['id'],)).fetchone()
   conflicts=db.execute("SELECT slug FROM artworks WHERE status<>'archived' AND current_institution_id=%s AND id<>%s AND upper(regexp_replace(accession_number,'\\s','','g'))=%s LIMIT 4",(w['current_institution_id'],w['id'],m.m.accession_key(e['inventory']))).fetchall()
   if conflicts:holds.append(dict(slug=w['slug'],reason='existing same-institution inventory needs reconciliation',conflicts=conflicts));continue
   fields={'accession_number':e['inventory'],'medium_text':e['medium'],'dimensions_text':e['dimensions']};changes={k:v for k,v in fields.items() if not w[k]}
   if any(w[k] and w[k]!=v for k,v in fields.items()):holds.append(dict(slug=w['slug'],reason='nonempty current field differs; no overwrite'));continue
   if changes:entries.append(dict(slug=w['slug'],before=w,changes=changes,evidence=e,review='Exact current museum object URL already cited by this record; full source-language title matches. Current DOM explicitly labels inventory, material and dimensions. All222 inventories distinct; each same-title pair remains separate. Dimensions retained verbatim without invented units or orientation. Source creation/date and artist-life wording not imported.'))
 CORE.save_new(m.BACKUPS/'russian-primary-inventories'/(target+'-preimages.json'),[e['before'] for e in entries]);CORE.save_new(path,dict(at=CORE.now(),target=target,entries=entries,holds=holds));CORE.save_new(ROOT/(target+'-manifest.json'),dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),updates=len(entries),holds=len(holds)));print(target,'Russian primary plan',len(entries),'holds',len(holds),flush=True)
def apply(target):
 path=ROOT/(target+'-plan.json');d=json.loads(path.read_text());pin=CORE.sha(path.read_bytes());assert pin==json.loads((ROOT/(target+'-manifest.json')).read_text())['plan_sha256'];qa=json.loads((ROOT/(target+'-quality-review.json')).read_text());assert qa['approved'] and qa['plan_sha256']==pin;dest=ROOT/(target+'-verified.json')
 if dest.exists():return
 with m.m.r.base.connect(target=='production') as db:
  with db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute("SET LOCAL statement_timeout='120s'");sid=m.m.source(db,SOURCE,'Russian Museum: exact object inventory, material and dimensions','collection_page','https://rusmuseumvrm.ru/')
   for e in d['entries']:
    aid=e['before']['id'];w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row'];done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone()
    if done:continue
    assert w==e['before'],'Reviewed row changed; re-review before applying'
    sets=[sql.SQL('{}=%s').format(sql.Identifier(k)) for k in e['changes']];query=sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sets));db.execute(query,(*e['changes'].values(),m.m.ACTOR,aid))
    r=e['evidence']['receipt'];m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='primary_object_metadata',source_id=sid,source_record_id=e['evidence']['inventory'],source_url=r['url'],retrieved_at=r['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary=e['evidence'],review=e['review'],previous_fields={k:e['before'][k] for k in e['changes']}),ensure_ascii=False)))
  with db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for e in d['entries']:
    w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(e['before']['id'],)).fetchone()['row'];ignore={'revision','updated_at','updated_by'}|set(e['changes']);assert {k:v for k,v in w.items() if k not in ignore}=={k:v for k,v in e['before'].items() if k not in ignore};assert all(w[k]==v for k,v in e['changes'].items())
 CORE.save_new(dest,dict(at=CORE.now(),target=target,plan_sha256=pin,updated_objects=len(d['entries']),field_updates={k:sum(k in e['changes'] for e in d['entries']) for k in ('accession_number','medium_text','dimensions_text')},review_country_dates_holdings_images_preserved=True));print(target,'Russian primary metadata verified',len(d['entries']),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production'],required=True);a=p.parse_args();globals()[a.command](a.target)
