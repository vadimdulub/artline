#!/usr/bin/env python3
"""Fill missing inventory/material fields from exact already-cited museum pages.

Read-only planning excludes title, maker, holding, chronology and media changes.
No inventory is adopted if it collides with another active object at the museum.
"""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.SESSION_BASE;RUN=BASE/'duplicates/russian-primary-inventory-enrichment';BACK=m.BACKUPS/'russian-primary-inventory-enrichment'
FIELDS=('accession_number','medium_text','dimensions_text')
CHECK=('id','slug','title','status','published_at','revision','current_institution_id','primary_media_id','creation_year_start','creation_year_end','date_precision','date_display','work_type',*FIELDS)
def dump(x):return json.loads(json.dumps(x,default=str,ensure_ascii=False))
def current(db,slugs):return {r['slug']:dump(r) for r in db.execute('SELECT '+','.join(CHECK)+' FROM artworks WHERE slug=ANY(%s)',(slugs,)).fetchall()}
def plan():
 if (RUN/'plan.json').exists():return
 candidates=[]
 for f in sorted((BASE/'duplicates/inventory-second-pass').glob('round-*/inventory-review/europe-russian-session*.json')):
  d=json.loads(f.read_text());rs=d['reviews']
  if len(rs)!=1:continue
  r=rs[0]
  if not r.get('title_matches') or not r.get('inventory') or 'unknown_painter' in (r.get('creator_path') or ''):continue
  assert CORE.sha(Path(r['capture']).read_bytes())==r['receipt']['sha256'];assert r['receipt']['url'].startswith('https://rusmuseumvrm.ru/data/collections/')
  assert r.get('creator_path') and len(d['existing']['creators'])==1 and d['existing']['creators'][0]['role']=='primary'
  candidates.append(dict(slug=d['slug'],evidence_file=str(f),evidence_sha256=CORE.sha(f.read_bytes()),primary=r,expected_artist_slug=d['existing']['creators'][0]['slug'],targets={}))
 assert len(candidates)==500;slugs=[e['slug'] for e in candidates];assert len(set(slugs))==500;holds={};preimages={}
 for target in ('local','production'):
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");works=current(db,slugs);assert set(works)==set(slugs)
   iid=db.execute("SELECT id::text FROM institutions WHERE slug='state-russian-museum'").fetchone()['id']
   existing_inventory={}
   for row in db.execute("SELECT slug,accession_number FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND accession_number IS NOT NULL",(iid,)):
    existing_inventory.setdefault(m.m.accession_key(row['accession_number']),set()).add(row['slug'])
   artists={};citations={}
   for row in db.execute("SELECT w.slug,a.slug AS artist_slug,aa.attribution_role FROM artworks w JOIN artwork_artists aa ON aa.artwork_id=w.id JOIN artists a ON a.id=aa.artist_id WHERE w.slug=ANY(%s)",(slugs,)):artists.setdefault(row['slug'],[]).append((row['artist_slug'],row['attribution_role']))
   for row in db.execute("SELECT w.slug,c.source_url FROM artworks w JOIN citations c ON c.entity_type='artwork' AND c.entity_id=w.id WHERE w.slug=ANY(%s)",(slugs,)):citations.setdefault(row['slug'],set()).add(row['source_url'])
   preimages[target]=works
   for e in candidates:
    w=works[e['slug']];r=e['primary'];assert w['status']=='review' and not w['published_at'] and w['current_institution_id']==iid
    assert m.m.r.norm(w['title'])==m.m.r.norm(r['title']);assert artists[e['slug']]==[(e['expected_artist_slug'],'primary')]
    # Exact already-cited object URL is the provenance anchor, not a title search.
    normalized=lambda u:(u or '').replace('http://','https://').rstrip('/')
    assert normalized(r['receipt']['url']) in {normalized(u) for u in citations.get(e['slug'],set())}
    collision=existing_inventory.get(m.m.accession_key(r['inventory']),set())-{e['slug']}
    if collision:holds[e['slug']]='Current exact museum inventory already exists on another active object: '+', '.join(sorted(collision));continue
    desired=dict(accession_number=r['inventory'],medium_text=r.get('medium'),dimensions_text=r.get('dimensions'))
    updates={k:v for k,v in desired.items() if v and not w[k]}
    if w['accession_number'] and m.m.accession_key(w['accession_number'])!=m.m.accession_key(r['inventory']):holds[e['slug']]='Existing inventory conflicts with current primary source';continue
    e['targets'][target]=dict(id=w['id'],updates=updates)
 for e in candidates:
  if e['slug'] in holds:continue
  assert e['targets']['local']['updates']==e['targets']['production']['updates']
 selected=[e for e in candidates if e['slug'] not in holds and e['targets']['local']['updates']]
 for target in preimages:CORE.save_new(BACK/(target+'-preimages.json'),preimages[target])
 CORE.save_new(RUN/'plan.json',selected);CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),selected=len(selected),holds=holds,plan_sha256=CORE.sha((RUN/'plan.json').read_bytes()),policy='Exact existing citation URL, creator unchanged, title and holding crosschecks, hash-verified primary capture, no inventory collision; only missing inventory/material/dimensions. No dates/units inferred. Review retained.'))
 print('Planned',len(selected),'held',len(holds),flush=True)
def reviewed_preimages(target):
 pre=json.loads((BACK/(target+'-preimages.json')).read_text());path=RUN/'preimage-addendum.json'
 if not path.exists():return pre
 add=json.loads(path.read_text());assert add['approved'] and add['plan_sha256']==CORE.sha((RUN/'plan.json').read_bytes())
 proof=Path(add['image_proof_file']);assert CORE.sha(proof.read_bytes())==add['image_proof_sha256']
 for slug,entry in add['targets'][target].items():
  assert entry['original']==pre[slug] and entry['reason']
  now=entry['reviewed'];old=pre[slug];assert {k for k in now if now[k]!=old[k]}=={'revision','primary_media_id'}
  assert now['revision']==old['revision']+1 and old['primary_media_id'] is None and now['primary_media_id']==add['preserved_existing_media_id']
  pre[slug]=now
 return pre

def apply():
 raw=(RUN/'plan.json').read_bytes();pin=CORE.sha(raw);qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin;entries=json.loads(raw)
 for target in ('local','production'):
  pre=reviewed_preimages(target)
  with m.m.r.base.connect(target=='production') as db:
   for e in entries:
    dest=RUN/'applied'/target/(e['slug']+'.json')
    if dest.exists():continue
    r=e['primary'];t=e['targets'][target]
    with db.transaction():
     db.execute("SET LOCAL lock_timeout='30s'");db.execute("SET LOCAL statement_timeout='90s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(t['id'],))
     sid=m.m.source(db,m.x.SESSION_NAME+'-russian-primary-inventory','Russian Museum — exact existing object inventory verification','collection_page','https://rusmuseumvrm.ru/')
     done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='museum_inventory_verification' AND source_record_id=%s AND evidence_note LIKE %s",(t['id'],sid,r['inventory'],'%'+pin+'%')).fetchone()
     if not done:
      assert current(db,[e['slug']])[e['slug']]==pre[e['slug']],'Scoped artwork changed since read-only plan'
      keys=list(t['updates']);assert set(keys)<=set(FIELDS)
      db.execute('UPDATE artworks SET '+','.join(k+'=%s' for k in keys)+',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',tuple(t['updates'][k] for k in keys)+(m.m.ACTOR,t['id']))
      m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=t['id'],field_name='museum_inventory_verification',source_id=sid,source_record_id=r['inventory'],source_url=r['receipt']['url'],retrieved_at=r['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary=r,evidence_file=e['evidence_file'],evidence_sha256=e['evidence_sha256'],filled=t['updates'],preimage_addendum_sha256=CORE.sha((RUN/'preimage-addendum.json').read_bytes()) if (RUN/'preimage-addendum.json').exists() else None,interpretation='Only missing fields copied from exact already-cited museum page; no title/maker/date/country/display/publication inference.'),ensure_ascii=False)))
    CORE.save_new(dest,dict(at=CORE.now(),slug=e['slug'],artwork_id=t['id'],plan_sha256=pin,filled=t['updates']));print(target,e['slug'],'fields',list(t['updates']),flush=True)
def verify():
 raw=(RUN/'plan.json').read_bytes();entries=json.loads(raw);out={}
 for target in ('local','production'):
  pre=reviewed_preimages(target)
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');works=current(db,[e['slug'] for e in entries]);out[target]=[]
   for e in entries:
    w=works[e['slug']];old=pre[e['slug']];t=e['targets'][target];assert all(w[k]==v for k,v in t['updates'].items());allowed=set(t['updates'])|{'revision'};assert {k:v for k,v in w.items() if k not in allowed}=={k:v for k,v in old.items() if k not in allowed};assert w['revision']==old['revision']+1
    out[target].append(dict(slug=e['slug'],filled=t['updates'],status=w['status']))
 assert out['local']==out['production'];CORE.save_new(RUN/'verification.json',dict(at=CORE.now(),plan_sha256=CORE.sha(raw),verified_records=len(entries),both_targets_verified=True,targets=out));print('Both inventories verified',len(entries))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
