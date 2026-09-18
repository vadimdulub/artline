#!/usr/bin/env python3
"""Reconcile nine independently reviewed FNG objects across country campaigns.

Exact current inventory, source-language title, P9834 object crosswalk and
already identical linked creator are required. Date assertions are preserved.
"""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;CORE=p.CORE;ROOT=m.x.BASE/'duplicates/fng-cross-country-objects'
REVIEWED={'Q20791325','Q20789268','Q20776121','Q20782186','Q20788929','Q20792884','Q11895977','Q20800494','Q20792625'}
def configure(target):
 p.RUN=ROOT/target;p.BACK=m.BACKUPS/'fng-cross-country-objects'/target;p.SOURCE='overnight-fng-cross-country-physical-identity-20260913';p.SOURCE_NAME='FNG: primary object identities across country catalogues';p.SOURCE_ROOT='https://kokoelma.kansallisgalleria.fi/'
def plan(target):
 configure(target)
 if (p.RUN/'plan.json').exists():return
 api=m.x.BASE/'finland/primary-api/objects.json';receipt=json.loads(api.with_name('objects.receipt.json').read_text());assert CORE.sha(api.read_bytes())==receipt['sha256'];objects={str(o['objectId']):o for o in json.loads(api.read_text())}
 leads=json.loads((m.x.BASE/'duplicates/primary-crosswalk-0320/local-audit.json').read_text())['leads']['artwork_authority_crosswalk'];entries=[];snapshots={}
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');p.a.ensure_schema(db)
  for lead in leads:
   q=lead['wikidata']
   if q not in REVIEWED:continue
   oid=lead['museum_object_id'];obj=objects[oid];rows={w['slug']:w['id'] for w in db.execute('SELECT slug,id::text FROM artworks WHERE slug=ANY(%s)',([w['slug'] for w in lead['works']],))};assert len(rows)==2
   old_slug=next(s for s in rows if s.startswith('research-candidate-'));keep_slug=next(s for s in rows if s!=old_slug);old=rows[old_slug];keep=rows[keep_slug];snap=p.a.snapshot(db,[old,keep]);works={w['id']:w for w in snap['artworks']};a=works[old];b=works[keep]
   assert all(w['status']=='review' and w['published_at'] is None for w in works.values())
   assert all(m.m.accession_key(w['accession_number'])==m.m.accession_key(obj['inventoryNumber']) for w in works.values())
   titles={m.m.r.norm(v) for v in obj['title'].values() if v};assert all(m.m.r.norm(w['title']) in titles for w in works.values())
   makers=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid}
   assert makers(old)==makers(keep) and len(makers(keep))==1
   people=[v for v in obj['people'] if v.get('role',{}).get('en')=='Artist'];assert len(people)==1 and not people[0].get('attribution')
   artist=db.execute('SELECT birth_year,death_year FROM artists WHERE id=%s',(next(iter(makers(keep)))[0],)).fetchone()
   assert all(artist[k+'_year'] is None or people[0].get(k+'Year') is None or artist[k+'_year']==people[0][k+'Year'] for k in ('birth','death'))
   assert not a['current_institution_id'] and b['current_institution_id'] and not a['primary_media_id']
   for table in ('artwork_places','curated_collection_items','artwork_media'):assert not any(r['artwork_id']==old for r in snap[table]),table
   assert any(r['entity_id']==old and r['scheme']=='fng-object' and r['external_id']==oid for r in snap['external_identifiers'])
   assert any(r['entity_id']==keep and r['scheme']=='wikidata' and r['external_id']==q for r in snap['external_identifiers'])
   wiki=json.loads(Path(lead['entity_capture']).read_text());entity=wiki.get('entity',wiki);assert oid in [str(v) for v in m.m.r.values(entity,'P9834')]
   common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep}
   context='Exact current FNG object ID and inventory, full source-language title and identical existing primary creator link. Cross-country research duplicate with missing legacy institution. All creation assertions, rights, media and original fields retained; broad primary date bounds are not silently imported. Museum location is not creator country; existing cultural affiliations unchanged.'
   entries.append(dict(key=oid,canonical_slug=keep_slug,old_slug=old_slug,primary=dict(receipt=receipt,object_url='https://kokoelma.kansallisgalleria.fi/en/object/'+oid,primary_object=obj,wikidata=q,entity_capture=lead['entity_capture'],entity_sha256=CORE.sha(Path(lead['entity_capture']).read_bytes())),institution_context=context,targets={target:dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common),issues=[])}));snapshots[oid]=snap
 assert len(entries)==len(REVIEWED)
 CORE.save_new(p.BACK/(target+'-preimages.json'),snapshots);CORE.save_new(p.RUN/'plan.json',entries);pin=CORE.sha((p.RUN/'plan.json').read_bytes());CORE.save_new(p.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=pin,pairs=len(entries),target=target));print(target,'FNG cross-country plan',len(entries),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','apply','verify']);parser.add_argument('--target',choices=['local','production'],required=True);args=parser.parse_args();configure(args.target)
 if args.command=='plan':plan(args.target)
 else:getattr(p,args.command)(targets=(args.target,))
