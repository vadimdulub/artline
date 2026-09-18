#!/usr/bin/env python3
"""Ten individually researched museum-object overlaps; retain archival rows.

Planning is read-only and must follow the four exact FNG painter reconciliations.
Application uses the existing dependency-preserving archive/redirect writer.
"""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;CORE=c.CORE;BASE=m.x.SESSION_BASE;RUN=BASE/'duplicates/selected-physical-object-second-pass';BACK=m.BACKUPS/'selected-physical-object-second-pass'
c.RUN=RUN;c.BACK=BACK;c.SOURCE=m.x.SESSION_NAME+'-reviewed-museum-physical-objects';c.SOURCE_NAME='Individually researched primary museum physical-object reconciliation';c.SOURCE_ROOT='https://github.com/vadimdulub/artline'
FNG={'Q20798021':('412079','67240'),'Q20787970':('609681','60293'),'Q20795444':('609279','67570'),'Q20796787':('526938','63943'),'Q20791162':('513883','62521'),'Q20792028':('404316','63344')}
def proposals():
 audit=json.loads((BASE/'duplicates/interim-deep-research/local-audit.json').read_text())['leads'];leads=[*audit['artwork_authority_crosswalk'],*audit['same_creator_inventory_missing_institution']];out=[]
 for q in [*FNG,'Q19883699','Q1154410','Q104152302']:
  lead=next(x for x in leads if any(w['slug']=='wikimedia-artwork-'+q.lower() for w in x['works']));keep=next(w for w in lead['works'] if w['current_institution_id']);old=next(w for w in lead['works'] if not w['current_institution_id']);assert len(lead['works'])==2 and keep['slug']=='wikimedia-artwork-'+q.lower()
  assert old['accession_number'] and m.m.accession_key(old['accession_number'])==m.m.accession_key(keep['accession_number']);assert not old['primary_media_id']
  if q in FNG:
   oid,pid=FNG[q];f=BASE/'duplicates/selected-primary/fng'/(oid+'.json');ev=json.loads(f.read_text());o=ev['object'];people=[p for p in o['people'] if p['role']['en']=='Artist'];assert len(people)==1 and str(people[0]['id'])==pid and not people[0].get('attribution');assert str(o['objectId'])==oid and m.m.accession_key(o['inventoryNumber'])==m.m.accession_key(keep['accession_number'])
   primary={**ev,'object_url':'https://kokoelma.kansallisgalleria.fi/en/object/'+oid,'evidence_file':str(f),'evidence_sha256':CORE.sha(f.read_bytes())};context='Same exact Finnish National Gallery object ID and inventory; unqualified FNG person ID is checked against the canonical artist authority after person reconciliation. Finnish, Swedish and English title variants describe one physical painting. Original date precision and all prior assertions are preserved. Genetz1885–1943source range repeats lifespan and remains a separate chronology correction; it does not establish a different physical object.'
   expected_person=('fng-person',pid)
  else:
   f=BASE/'duplicates/selected-primary'/(q+'.review.json');ev=json.loads(f.read_text());primary={**ev,'evidence_file':str(f),'evidence_sha256':CORE.sha(f.read_bytes())};expected_person=None
   if q=='Q104152302':
    o=ev['object'];assert any(i.get('content')=='SK-A-5067' for i in o['identified_by']);parts=o['produced_by']['part'];makers=[a for p in parts for a in p.get('carried_out_by',[])];assert len(makers)==1 and any(z.get('id','').endswith('/Q1375979') for z in makers[0]['equivalent']);assert o['produced_by']['timespan']['begin_of_the_begin'].startswith('1832-')
    context='Exact RijksmuseumSKA5067LinkedArt physical object and unqualified RadenSalehQ1375979maker. Current primary1832is compatible with canonical1831–32range; do not silently tighten existing chronology. Dutch and English titles identify the same Baud family portrait.'
   else:
    assert ev['review']=='primary_object_and_creator_corroborated' and m.m.accession_key(ev['object']['accession'])==m.m.accession_key(keep['accession_number']);context='Exact MoMA object number, independently read official object page, same existing canonical painter and compatible exact1913/1914creation date. Title variants and missing placeholder holding do not describe another physical object. No new reproduction or display rights inferred.'
  out.append(dict(key=q,old_slug=old['slug'],canonical_slug=keep['slug'],accession=keep['accession_number'],primary=primary,institution_context=context,expected_person=expected_person,targets={}))
 works=next(g['works'] for g in audit['same_title_creator_institution'] if g['key'][0]=='musei-civici-pavia' and g['key'][1]=='la falconiera');assert len(works)==2
 old=next(w for w in works if '56aec6e38f63' in w['slug']);keep=next(w for w in works if '38cfa0d31d59' in w['slug']);evidence=[]
 for w in (old,keep):
  files=list((BASE/'duplicates/inventory-second-pass').glob('round-*/inventory-review/'+w['slug']+'.json'));assert len(files)==1;d=json.loads(files[0].read_text());r=d['reviews'][0];raw=Path(r['capture']).read_bytes();assert CORE.sha(raw)==r['receipt']['sha256'];text=Path(r['full_text_path']).read_text();assert all(t in text for t in ('P 1659','144','102','Segantini','olio su tela','Comune di Pavia'));assert any(i['number']=='P 1659' and i['label']=='Inventario corrente' for i in r['inventories']);evidence.append(r)
 assert keep['creation_year_start']==1879 and keep['creation_year_end']==1880 and old['creation_year_start']==1870 and old['creation_year_end']==1880
 out.append(dict(key='Pavia-P1659',old_slug=old['slug'],canonical_slug=keep['slug'],accession='P 1659',primary=dict(receipt=evidence[1]['receipt'],object_url='https://www.lombardiabeniculturali.it/opere-arte/schede/SWF01-00509/',records=evidence),institution_context='Both museum-authored SIRBeC records identify the same Pavia inventoryP1659,Segantini1858–1899,oilcanvas144×102cm,2001Moronegift,ComunePaviaownership. Retain newer2024SWF01-00509canonicaldating1879–80and originalolderF0060-00010c1870–80assertion on archived row. Identical title alone was not used.',expected_person=None,targets={}))
 assert len(out)==10;return out
def plan():
 if (RUN/'plan.json').exists():return
 prerequisite=BASE/'duplicates/fng-person-second-pass/verification.json';assert prerequisite.exists() and json.loads(prerequisite.read_text())['both_targets_verified']
 entries=proposals();snapshots={t:{} for t in ('local','production')}
 for target in snapshots:
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");c.a.ensure_schema(db)
   for e in entries:
    ids={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],))};assert len(ids)==2;old=ids[e['old_slug']];keep=ids[e['canonical_slug']];snap=c.a.snapshot(db,[old,keep]);works={w['id']:w for w in snap['artworks']};assert all(w['status']=='review' and not w['published_at'] for w in works.values());assert not works[old]['primary_media_id']
    artists=lambda wid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==wid};assert artists(old)==artists(keep) and len(artists(keep))==1;aid,role=next(iter(artists(keep)));assert role=='primary'
    if e['expected_person']:assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme=%s AND external_id=%s",(aid,*e['expected_person'])).fetchone()
    for table in ('artwork_media','artwork_places','curated_collection_items'):assert not any(r['artwork_id']==old for r in snap[table]),(e['key'],table)
    assert any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
    common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep};e['targets'][target]=dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common));snapshots[target][e['key']]=snap;print(target,e['key'],'source reviewed object pair',flush=True)
 for e in entries:
  comparable=lambda t:[{k:w[k] for k in ('slug','title','accession_number','creation_year_start','creation_year_end','date_precision','work_type','status')} for w in sorted(snapshots[t][e['key']]['artworks'],key=lambda w:w['slug'])]
  assert comparable('local')==comparable('production')
 for t in snapshots:CORE.save_new(BACK/(t+'-preimages.json'),snapshots[t])
 CORE.save_new(RUN/'plan.json',entries);CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),pairs=len(entries),plan_sha256=CORE.sha((RUN/'plan.json').read_bytes())));print('Ten physical-object pairs staged; hash-pinned QA still required',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();plan() if a.command=='plan' else getattr(c,a.command)()
