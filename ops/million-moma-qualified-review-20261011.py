#!/usr/bin/env python3
"""Preserve explicit 'after' identities without unsupported primary authorship."""
import argparse,importlib.util,json,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('frey',Path(__file__).with_name('million-lifetime-corrections-20261011.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;n=f.n
RUN=m.RUN/'moma/002/qualified-review';BACKUP=m.BACKUP/'moma/002/qualified-review'
ROWS=[('14441680-c2e8-5119-b7b8-65b03eea6be1','a064ef31-0207-45f9-a365-9724b6ee69ab','Paul Cézanne'),('d0546f29-8401-59dc-b4d8-538427c7cb07','b0ca2d28-b9c1-442d-b9a4-7f03d332f547','Amedeo Modigliani')]
VILLON='571cb279-dc51-447a-94c2-399fb3df98a8'
def snapshot(db,aid):
 f.AID=aid;return f.snapshot(db)
def plan():
 if (RUN/'plan.json').exists():return
 source={r['artwork_id']:r for r in m.load(m.RUN/'moma/002/plan.json.gz')['new_artworks']};rows=[]
 with m.m.connect() as db:
  for aid,person,name in ROWS:
   rows.append(dict(artwork_id=aid,remove_primary_artist_id=person,qualified_label='Jacques Villon; after '+name,source=source[aid],before=snapshot(db,aid)))
 m.save(RUN/'plan.json',dict(at=m.now(),rows=rows,reason='Official MoMA titles explicitly say after Cézanne and after Modigliani. Jacques Villon is the printmaker. The current schema has no after role: withdraw the two unsupported secondary primary links and preserve the named composition sources in qualified object labels, titles and citations. Keep Villon primary. Neither artist lifespan nor print date is changed.',web_review=dict(url='https://www.moma.org/collection/works/70275',observation='Current official page identifies the 1927 aquatint after Modigliani, object 509.1954, with Jacques Villon as printer. CSV remains the direct source for 65546; its web page was unavailable.')))
 m.save(RUN/'pin.json',dict(sha256=m.sha((RUN/'plan.json').read_bytes())))
def apply():
 plan();p=m.load(RUN/'plan.json');pin=m.load(RUN/'pin.json')['sha256'];assert pin==m.sha((RUN/'plan.json').read_bytes())
 if (RUN/'applied.json').exists():return
 ids=[r['artwork_id'] for r in p['rows']]
 with m.m.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  done=db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])',([m.uid('moma-after-review/'+aid) for aid in ids],)).fetchone()['n']
  if not done:
   before={aid:snapshot(db,aid) for aid in ids}
   for row in p['rows']:
    aid=row['artwork_id'];assert before[aid]==row['before'];assert {v['artist_id'] for v in before[aid]['creators']}=={VILLON,row['remove_primary_artist_id']};assert all(v['attribution_role']=='primary' for v in before[aid]['creators'])
   m.save(BACKUP/'before.json.gz',before)
   for row in p['rows']:
    aid=row['artwork_id'];db.execute("DELETE FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(aid,row['remove_primary_artist_id']))
    db.execute('UPDATE artworks SET unlinked_creator_label=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s',(row['qualified_label'],m.ACTOR,aid))
    n.copy_rows(db,'citations',[dict(id=m.uid('moma-after-review/'+aid),entity_type='artwork',entity_id=aid,field_name='million_qualified_creator_review',source_id=m.uid('source/moma'),source_record_id=row['source']['native_id'],source_url=row['source']['source_url'],evidence_note=json.dumps(dict(reason=p['reason'],web_review=p['web_review'],raw=row['source']['raw'],before=row['before']['creators'],plan_sha256=pin),ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
   db.commit()
  else:assert done==2
 m.save(RUN/'applied.json',dict(at=m.now(),artwork_ids=ids,unsupported_primary_links_removed=2,plan_sha256=pin));print('Preserved two explicit after attributions and the actual printmaker',flush=True)
def verify():
 p=m.load(RUN/'plan.json');before=m.load(BACKUP/'before.json.gz');ignore={'unlinked_creator_label','updated_at','updated_by','revision'};public=[]
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');slug=db.execute('SELECT slug FROM artists WHERE id=%s',(VILLON,)).fetchone()['slug']
  for row in p['rows']:
   aid=row['artwork_id'];actual=snapshot(db,aid);old=before[aid]
   assert all(actual['artwork'][k]==v for k,v in old['artwork'].items() if k not in ignore);assert actual['artwork']['unlinked_creator_label']==row['qualified_label'];assert all(actual[k]==old[k] for k in ['media','identifiers'])
   assert actual['creators']==[v for v in old['creators'] if v['artist_id']==VILLON]
   assert db.execute('SELECT 1 FROM artwork_search_documents WHERE id=%s AND title=%s',(aid,row['source']['title'])).fetchone()
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']
 for row in p['rows']:
  url='https://artlines.org/api/backend/v1/artists/'+slug+'/works/'+row['artwork_id'];r=requests.get(url,timeout=(15,60));r.raise_for_status();assert row['source']['title'] in r.text and row['artwork_id'] in r.text;public.append(dict(url=url,status=r.status_code))
 m.save(RUN/'verification.json',dict(at=m.now(),artworks=2,printmaker_links_preserved=2,qualified_composition_labels=2,artwork_dates_images_holdings_and_status_unchanged=True,local_baseline_equal=True,public=public));print('Verified two qualified attributions, preserved object fields and public routes',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.action]()
