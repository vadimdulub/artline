#!/usr/bin/env python3
"""Publish only the source-pinned Morocco/Africa batch, with production CAS guards."""
import collections, importlib.util, json, os, subprocess
import psycopg
from psycopg.rows import dict_row
from pathlib import Path
os.umask(0o077)
spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('morocco-africa-20261008.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pre=m.load(m.RUN/'publication-preflight.json.gz');plan=m.load(m.RUN/'application-plan.json.gz')
assert not (m.RUN/'production-publication-receipt.json').exists(),'Already published; inspect the receipt'
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'],text=True).strip()
fields=psycopg.conninfo.conninfo_to_dict(secret);fields.update(host='127.0.0.1',port='55518',sslmode='disable',connect_timeout='20')
ids=list(pre['mapping'].values());iids=[x['id'] for x in plan['institutions']];vids=[x['id'] for x in plan['venues']]
specs=[('artworks','id',ids),('institutions','id',iids),('institution_venues','id',vids),('artwork_artists','artwork_id',ids),('artwork_media','artwork_id',ids),('artwork_location_assertions','artwork_id',ids),('citations','entity_id',ids+iids),('external_identifiers','entity_id',ids+iids)]
def snapshot(db,lock=False):
 return {t:[r['row'] for r in db.execute(f'SELECT to_jsonb(t) row FROM {t} t WHERE {col}=ANY(%s::uuid[]) ORDER BY to_jsonb(t)::text'+(' FOR UPDATE' if lock else ''),(vals,))] for t,col,vals in specs}
def canon(rows):return sorted(json.dumps(r,sort_keys=True) for r in rows)
identity_notes={
 '0d559fd5-fc67-5697-936f-60c907627a97':{'same_work_confidence':'high (editorial assessment, >90%)','basis':'Visually compared WikiArt image with official Mahmoud Said PDF page 14: identical sitter, hair, hand at chin, black clothing, book and hand on lap. Title and creator match. Existing WikiArt dates and dimensions preserved.','uncertainty':'Official PDF caption gives 88 x 70 cm; existing WikiArt record gives 73 x 52 cm. Do not infer frame measurements or overwrite either source.','source_url':'https://www.fineart.gov.eg/AllPics/Catalogs/PDF/376/Mahmoud-Said.pdf#page=14'},
 '6b7c290a-f0d8-50b6-b013-16237ef8ee2e':{'same_work_confidence':'high (editorial assessment, >90%)','basis':'Exact distinctive creator/title identity and matching dimensions 81 x 65 cm in official catalogue and existing WikiArt record. Preserve established date 1923.','source_url':'https://www.fineart.gov.eg/AllPics/Catalogs/PDF/376/Mahmoud-Said.pdf#page=17'}}
with psycopg.connect(**fields,autocommit=True,row_factory=dict_row,options='-c timezone=UTC -c statement_timeout=120000 -c lock_timeout=15000') as db:
 with db.transaction():
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  current=snapshot(db,True)
  for t in current:assert canon(current[t])==canon(pre['before'][t]),f'Concurrent change in {t}; stop before any write'
  assert len(ids)==len(set(ids))==98 and len(iids)==109 and len(vids)==2
  enriched=[]
  for w in plan['artworks']:
   artid=pre['mapping'][w['key']];old=next(x for x in current['artworks'] if x['id']==artid)
   worktype=old['work_type']
   if worktype=='unknown':
    assert artid in identity_notes and w['work_type']=='painting' and w['medium']=='Oil on canvas'
    worktype='painting';enriched.append(artid)
   assert old['status'] in ('review','published')
   db.execute("UPDATE artworks SET status='published',research_candidate=false,work_type=%s,published_at=coalesce(published_at,now()),revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(worktype,m.ACTOR,artid))
  db.execute("UPDATE institutions SET status='published',updated_at=now() WHERE id=ANY(%s::uuid[]) AND status<>'published'",(iids,))
  db.execute("UPDATE institution_venues SET status='published' WHERE id=ANY(%s::uuid[]) AND status<>'published'",(vids,))
  after=snapshot(db)
  allowed={'artworks':{'status','research_candidate','work_type','published_at','revision','updated_at','updated_by'},'institutions':{'status','updated_at'},'institution_venues':{'status'}}
  for t in after:
   ignored=allowed.get(t,set());clean=lambda rows:[{k:v for k,v in x.items() if k not in ignored} for x in rows]
   assert canon(clean(after[t]))==canon(clean(current[t])),f'Unexpected data change: {t}'
  assert all(a['status']=='published' and not a['research_candidate'] and a['work_type']!='unknown' for a in after['artworks'])
  assert all(a['status']=='published' for a in after['institutions']+after['institution_venues'])
  scope=db.execute('SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n,bool_and(artline_has_selection_evidence(id)) source_supported FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1',(ids,)).fetchall()
  assert canon(scope)==canon(pre['scope']),'Creation eligibility or source evidence changed'
  m.save(m.BACKUP/'production-publication-postimages.json.gz',after)
 receipt={'at':m.now(),'project':'artline-508319','authorization':pre['authorization'],'published_artworks':98,'published_institutions':109,'published_venues':2,'scope':scope,'artwork_type_enrichment':enriched,'production_identity_reconciliations':identity_notes,'preserved':['object/version identities','existing dates and dimensions','unknown dates and scope classification','creator links and qualified labels','sources and citations','images and rights labels','holdings and display assertions'],'preimage_file':'publication-preflight.json.gz','postimage_backup':str(m.BACKUP/'production-publication-postimages.json.gz')}
 m.save(m.RUN/'production-publication-receipt.json',receipt)
 print(json.dumps({k:receipt[k] for k in ['at','published_artworks','published_institutions','published_venues','scope']}))
