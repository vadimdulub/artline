#!/usr/bin/env python3
"""Individually reviewed museum facts; preserve conflicting source assertions."""
import argparse,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE;RUN=BASE/'primary-object-final-followup';SOURCE='overnight-primary-object-followup-20260913'
def evidence(rel,receipt_rel=None):
 p=BASE/rel;rp=BASE/receipt_rel if receipt_rel else p.with_suffix('.receipt.json');r=json.loads(rp.read_text());assert CORE.sha(p.read_bytes())==r['sha256'];return dict(capture_path=str(p.relative_to(m.x.ROOT)),receipt=r)
def cases():
 bx=evidence('greek-historical/primary-objects/bxm-01564.body')
 sunrise=evidence('france/primary-objects/followup/rouen-sunrise.html')
 conde=evidence('france/primary-objects/followup/conde-santeul.html');agen=evidence('france/primary-objects/followup/agen-galatee.html')
 pop=BASE/'duplicates/pop-object-followup/captures/07290022457.json';d=json.loads(pop.read_text());raw=pop.with_suffix('.html');assert CORE.sha(raw.read_bytes())==d['receipt']['sha256'];natoire=dict(capture_path=str(raw.relative_to(m.x.ROOT)),receipt=d['receipt'],fields=d['fields'])
 return [
 dict(slug='wikimedia-artwork-q113129404',accession='ΒΧΜ 01564',updates=dict(dimensions_text='105 × 65 cm',alternate_title='The Virgin Brephokratousa Enthroned'),evidence=[bx],conclusion='Exact BCM01564 portable icon, Emmanuel Tzanes. English museum page explicitly reads signed1664 and105×65cm. Preserve1664; conflicting1644 wording on Greek page remains a source-review issue. No material or display inference.'),
 dict(slug='wikimedia-artwork-q105444120',accession='822.1.2',updates=dict(creation_year_start=1672,creation_year_end=1672,date_precision='circa',date_display='c. 1672',medium_text='Oil on canvas',research_candidate=False),evidence=[sunrise],conclusion='Current Rouen object page explicitly identifies822.1.2, Charles deLaFosse, Vers1672, oiloncanvas. Preserve museum currentaccession; POP1822.1.2 and1672–1681 remain alternate primary assertions. Do not substitute the Versailles ceiling or another preparatory sketch.'),
 dict(slug='wikimedia-artwork-q121071408',accession='22 Ai',updates=dict(medium_text='Oil paint',dimensions_text='H. 1.04 m × W. 1.31 m'),evidence=[agen],conclusion='Current Agen22Ai object page supports existingc1670, oilpaint and1.04×1.31m. Supportmaterialnotstatedinthetechnicalfield; do notinventcanvas. Older POP1698–1700contradictionretained. Museum renovation/current-restoration wording does not establish display.'),
 dict(slug='wikimedia-artwork-q122472941',accession='PE 638',updates=dict(medium_text='Oil on canvas',dimensions_text='131 × 96 cm'),evidence=[conde],conclusion='Current CondéPE638 namesLECHEVALIERDUMEE, oiloncanvas131×96cm, fourthquarter17century. Existing1675–1700range retained. Does not independently settle full first-name authority.'),
 dict(slug='europe-normandy-joconde-m0729-f8bf0226cf30-l-entrevue-de-cleopatre-et-marc-antoine-a-tarse',accession='1907.1.64',updates=dict(date_precision='circa',date_display='1740 (?)'),evidence=[natoire],conclusion='Rouen1907.1.64 physicaloilsketch: structuredyear1740butprimaryhistoricalparagraphqualifies1740(?). Preserveyearandqualifycertainty; distinctfromNimescartoonandGobelinstapestry1759–1761.')]
def plan():
 if (RUN/'plan.json').exists():return
 entries=cases();targets={}
 for target in ('local','production'):
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');rows={}
   for e in entries:
    w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',(e['slug'],)).fetchone()['row'];assert w['status']=='review' and w['published_at'] is None and w['accession_number']==e['accession'];assert w['creation_year_end'] is None or w['creation_year_end']<=1970
    for k in ('medium_text','dimensions_text','alternate_title'):
     if k in e['updates']:assert w[k] is None,(e['slug'],k)
    rows[e['slug']]=w
  targets[target]=rows;CORE.save_new(m.BACKUPS/('primary-object-final-'+target+'-preimages.json'),rows)
 for e in entries:
  l=targets['local'][e['slug']];r=targets['production'][e['slug']];assert all(l[k]==r[k] for k in ['title','accession_number','creation_year_start','creation_year_end','date_precision',*e['updates']])
 CORE.save_new(RUN/'plan.json',dict(at=CORE.now(),entries=entries,targets=targets));CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/'plan.json').read_bytes()),artworks=len(entries)));print('Primary object followup plan',len(entries),flush=True)
def apply():
 raw=(RUN/'plan.json').read_bytes();d=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256']
 for target in ('local','production'):
  dest=RUN/(target+'-verified.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   for e in d['entries']:
    old=d['targets'][target][e['slug']];aid=old['id']
    with db.transaction():
     db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Individually reviewed current museum object descriptions','collection_page','https://www.wikidata.org/')
     if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
     assert db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']==old
     updates=e['updates'];query=sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in updates));db.execute(query,(*updates.values(),m.m.ACTOR,aid))
     for ev in e['evidence']:m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='primary_object_metadata_review',source_record_id=e['accession'],source_url=ev['receipt']['url'],retrieved_at=ev['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,review=e,previous={k:old[k] for k in updates},publication_status='review'),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY')
    for e in d['entries']:
     old=d['targets'][target][e['slug']];now=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(old['id'],)).fetchone()['row'];expected={**old,**e['updates']};ignore={'revision','updated_at','updated_by'};assert {k:v for k,v in now.items() if k not in ignore}=={k:v for k,v in expected.items() if k not in ignore};assert now['revision']==old['revision']+1
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,artworks_verified=len(d['entries']),review_and_other_fields_preserved=True));print(target,'primary object followup verified',len(d['entries']),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
