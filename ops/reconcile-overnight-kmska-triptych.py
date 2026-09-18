#!/usr/bin/env python3
"""Resolve KMSKA 1599a/b/c using authoritative IIIF start canvases.

The whole triptych 1599 and its three components remain distinct objects.
Source dimensions on the central panel appear inconsistent, so none are added.
"""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-greek-primary-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;RUN=m.x.BASE/'belgium/primary-triptych';SOURCE='overnight-kmska-triptych-primary-20260913'
CASES={'Q21619667':('1599a','2158','Pilgrims Moving Around the Church','Bedevaarders trekken rond de kerk'),'Q21619669':('1599b','2159','Arrival of the Procession','Aankomst van de processie'),'Q21619670':('1599c','2157','Pilgrims at the Moor','Bedevaarders in de heide')}
def plan():
 if (RUN/'metadata-plan.json').exists():return
 entries=[];targets={}
 for q,(acc,canvas,title,native) in CASES.items():
  p=RUN/('iiif'+acc+'.body');raw=p.read_bytes();d=json.loads(raw);receipt=json.loads(p.with_suffix('.receipt.json').read_text());assert CORE.sha(raw)==receipt['sha256']
  vals={next((l['@value'] for l in e['label'] if l.get('@language')=='en'),''):e['value'] for e in d['metadata'] if isinstance(e['label'],list)}
  assert vals['Inventory no.']==acc and vals['Creator']=='Schilder: Frans Van Leemputten'
  start=d['sequences'][0]['startCanvas'];selected=next(c for c in d['sequences'][0]['canvases'] if c['@id']==start);assert selected['label']==canvas
  assert d['license']=='https://creativecommons.org/publicdomain/mark/1.0/'
  entries.append(dict(qid=q,accession=acc,canvas=canvas,title=title,native=native,primary=d,receipt=receipt,source_image=selected['images'][0]['resource']['@id'],review='Actual inspection of three distinct source canvases: 2157 moor/procession approaching town; 2158 central church/candles; 2159 arrival with kneeling figures and carts. Museum startCanvas, inventory and maker identify each component. Source inventories do not imply left-to-right letter order. No dimensions imported for central panel because website dimensions contradict its aspect ratio.'))
 for target in ['local','production']:
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');works={}
   for e in entries:
    row=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',('wikimedia-artwork-'+e['qid'].lower(),)).fetchone()
    if e['qid']=='Q21619670':assert row is None;continue
    w=row['row'];assert w['status']=='review' and w['published_at'] is None and not w['primary_media_id'] and w['accession_number']==e['accession'];assert (w['creation_year_start'],w['creation_year_end'])==(1903,1905);works[e['qid']]=w
   keep=works['Q21619667'];people=db.execute("SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id JOIN external_identifiers i ON i.entity_type='artist' AND i.entity_id=p.id AND i.scheme='wikidata' AND i.external_id='Q18508181' WHERE aa.artwork_id=%s AND aa.attribution_role='primary'",(keep['id'],)).fetchall();assert len(people)==1;person=people[0]
   assert db.execute("SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code='BE' AND relationship_type='cultural_affiliation'",(person['id'],)).fetchone()
   assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id='Q21619670'").fetchone()
   assert not db.execute("SELECT 1 FROM artworks WHERE status<>'archived' AND current_institution_id=%s AND accession_number='1599c'",(keep['current_institution_id'],)).fetchone()
   targets[target]=dict(works=works,artist=person,institution_id=keep['current_institution_id'])
  CORE.save_new(m.BACKUPS/('kmska-triptych-'+target+'-preimages.json'),targets[target])
 CORE.save_new(RUN/'metadata-plan.json',dict(at=CORE.now(),entries=entries,targets=targets));CORE.save_new(RUN/'metadata-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/'metadata-plan.json').read_bytes()),existing_artworks=2,new_artworks=1));print('KMSKA three components planned; whole remains separate',flush=True)
def apply(targets=('local','production')):
 raw=(RUN/'metadata-plan.json').read_bytes();d=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'metadata-manifest.json').read_text())['plan_sha256']
 for target in targets:
  dest=RUN/(target+'-metadata-verified.json')
  if dest.exists():continue
  ctx=d['targets'][target]
  with m.m.r.base.connect(target=='production') as db:
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'KMSKA: primary triptych component identities and IIIF reproductions','museum_api','https://iiif.kmska.be/')
    for e in d['entries']:
     q=e['qid'];aid=ctx['works'][q]['id'] if q in ctx['works'] else m.m.uid('artwork/'+q)
     if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
     old=ctx['works'].get(q)
     if old:
      assert db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']==old
      db.execute('UPDATE artworks SET title=%s,normalized_title=%s,alternate_title=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(e['title'],m.m.r.norm(e['title']),e['native'],m.m.ACTOR,aid))
     else:
      m.m.r.base.insert(db,'artworks',dict(id=aid,slug='wikimedia-artwork-'+q.lower(),title=e['title'],normalized_title=m.m.r.norm(e['title']),alternate_title=e['native'],creation_year_start=1903,creation_year_end=1905,date_precision='circa_range',date_display='c. 1903–1905',work_type='painting',current_institution_id=ctx['institution_id'],accession_number=e['accession'],status='review',research_candidate=False,description_md='A component of the Candle Procession triptych by Frans Van Leemputten, in the Royal Museum of Fine Arts Antwerp collection. The exact primary museum inventory and image manifest identify pilgrims crossing the moor. The whole triptych and other panels are separate catalogue records.',created_by=m.m.ACTOR,updated_by=m.m.ACTOR))
      m.m.r.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=ctx['artist']['id'],attribution_role='primary',attribution_note='Exact primary KMSKA maker and component inventory; established Belgian cultural affiliation.'))
      m.m.r.base.insert(db,'artwork_location_assertions',dict(artwork_id=aid,claim_type='holding',institution_id=ctx['institution_id'],context='collection',source_id=sid,source_url=e['receipt']['url'],evidence_note='KMSKA exact inventory1599c and primary IIIF. No on-view assertion.',checked_at=e['receipt']['retrieved_at'],review_state='accepted'))
      m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=q,canonical_url='https://www.wikidata.org/wiki/'+q,source_id=sid,retrieved_at=e['receipt']['retrieved_at']))
     m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='primary_object_identity',source_id=sid,source_record_id=e['accession'],source_url=e['receipt']['url'],retrieved_at=e['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary=e,previous=old,candidate_wikidata='https://www.wikidata.org/wiki/'+q,date_policy='Existing circa1903–1905 interval retained; current IIIF begins1903 and collection website dates1903–1905. No exact date inferred.'),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY')
    for e in d['entries']:
     w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',('wikimedia-artwork-'+e['qid'].lower(),)).fetchone()['row'];assert w['status']=='review' and w['published_at'] is None and w['title']==e['title'] and w['accession_number']==e['accession'] and w['object_form'] is None
     if e['qid'] in ctx['works']:
      old=ctx['works'][e['qid']];ignore={'title','normalized_title','alternate_title','revision','updated_at','updated_by'};assert {k:v for k,v in w.items() if k not in ignore}=={k:v for k,v in old.items() if k not in ignore}
    assert db.execute("SELECT 1 FROM artworks WHERE slug='wikimedia-artwork-q21619666' AND status='review' AND accession_number='1599'").fetchone()
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,new_artworks=1,existing_artworks=2,whole_and_parts_distinct=True));print(target,'KMSKA component identities verified',flush=True)
def images(targets=('local','production')):
 a.RUN=RUN/'images'
 a.PLAN_NAME='application-plan.json' if len(targets)==2 else 'application-plan-'+targets[0]+'.json'
 a.MANIFEST_NAME='application-manifest.json' if len(targets)==2 else 'application-manifest-'+targets[0]+'.json'
 if not (a.RUN/a.PLAN_NAME).exists():
  d=json.loads((RUN/'metadata-plan.json').read_text());images=[];targets={t:[] for t in targets}
  for e in d['entries']:
   raw=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/kmska',e['canvas']+'.source-thumbnail.jpg').read_bytes();receipt=json.loads((RUN/(e['canvas']+'.image-receipt.json')).read_text());assert CORE.sha(raw)==receipt['sha256'];enc,w,h,quality=CORE.compress(raw);sha=CORE.sha(enc);path='/assets/artworks/imported/kmska/'+e['accession']+'-'+sha[:16]+'.jpg';CORE.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),enc);artist=d['targets']['local']['artist']['display_name'];credit='Frans Van Leemputten; photograph: Hugo Maertens; Royal Museum of Fine Arts Antwerp – Flemish Community'
   images.append(dict(key=e['accession'],media_id=m.m.uid('kmska-primary-image/'+e['accession']+'/'+sha),path=path,sha256=sha,bytes=len(enc),width=w,height=h,quality=quality,title=e['title'],artist=artist,page=e['receipt']['url'],provider_name='Royal Museum of Fine Arts Antwerp',source_slug='overnight-kmska-selected-images-20260913',source_name='KMSKA selected public-domain IIIF reproductions',source_root='https://iiif.kmska.be/',source_image_url=receipt['url'],rights_status='public_domain',license_label='Public domain',license_url=e['primary']['license'],creator_credit=credit,attribution_text=f"{e['title']}. {credit}. Museum manifest: CC0 / public domain ({e['primary']['license']}). Full-frame resize and JPEG compression.",download=receipt,checked_at=CORE.now(),identity=dict(choice=dict(page=dict(title=e['accession']),receipt=e['receipt']),identity_basis=e['review'],primary_manifest=e['primary'])))
   for target in targets:
    with m.m.r.base.connect(target=='production') as db,db.transaction():
     db.execute('SET TRANSACTION READ ONLY');w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',('wikimedia-artwork-'+e['qid'].lower(),)).fetchone()['row'];assert not w['primary_media_id'] and w['accession_number']==e['accession'] and w['status']=='review';targets[target].append(dict(key=e['accession'],work=w))
  for t,rows in targets.items():CORE.save_new(m.BACKUPS/('kmska-images-'+t+'-preimages.json'),rows)
  CORE.save_new(a.RUN/a.PLAN_NAME,dict(at=CORE.now(),images=images,targets=targets,qa='Three primary source canvases actually viewed; titles and startCanvas agree. Whole artwork not substituted for a panel.'));CORE.save_new(a.RUN/a.MANIFEST_NAME,dict(plan_sha256=CORE.sha((a.RUN/a.PLAN_NAME).read_bytes()),images=3))
 a.apply();a.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','images']);p.add_argument('--target',choices=['local','production']);args=p.parse_args();targets=(args.target,) if args.target else ('local','production')
 if args.command=='plan':plan()
 else:globals()[args.command](targets)
