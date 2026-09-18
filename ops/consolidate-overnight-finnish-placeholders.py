#!/usr/bin/env python3
"""Exact FNG object IDs and inventories reconcile named legacy placeholders."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;CORE=p.CORE;ROOT=m.x.BASE/'duplicates/finnish-primary-placeholders';RESEARCH=m.x.BASE/'finland/primary-followup'
def configure(target):
 p.RUN=ROOT/target;p.BACK=m.BACKUPS/'finnish-primary-placeholders'/target;p.SOURCE='overnight-finnish-placeholder-physical-identity-20260913';p.SOURCE_NAME='Finnish National Gallery: exact primary object and inventory reconciliation';p.SOURCE_ROOT='https://kokoelma.kansallisgalleria.fi/'
def plan(target):
 configure(target)
 if (p.RUN/'plan.json').exists():return
 reviewed=json.loads((RESEARCH/'application-plan-local.json').read_text())['entries'];entries=[];snapshots={};holds=[]
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");p.a.ensure_schema(db)
  for review in reviewed:
   evidence=review['evidence'];obj=evidence['primary_object'];oid=str(obj['objectId']);slug=review['targets']['local']['slug']
   owner=db.execute("SELECT w.id::text,w.slug FROM external_identifiers e JOIN artworks w ON w.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='fng-object' AND e.external_id=%s",(oid,)).fetchone()
   if not owner or owner['slug']==slug:continue
   keep_row=db.execute('SELECT id::text FROM artworks WHERE slug=%s',(slug,)).fetchone();assert keep_row;old=owner['id'];keep=keep_row['id'];snap=p.a.snapshot(db,[old,keep]);works={w['id']:w for w in snap['artworks']};a=works[old];b=works[keep];reasons=[]
   if not a['slug'].startswith('research-candidate-'):reasons.append('not a legacy research placeholder')
   if any(w['status']!='review' or w['published_at'] is not None for w in works.values()):reasons.append('publication state requires review')
   if any(m.m.accession_key(w['accession_number'])!=m.m.accession_key(obj['inventoryNumber']) for w in works.values()):reasons.append('primary inventory conflict')
   primary_titles={m.m.r.norm(v) for v in obj['title'].values() if v};old_titles={m.m.r.norm(a['title']),m.m.r.norm(a['alternate_title'] or '')}
   if not old_titles&primary_titles:reasons.append('legacy title not exact primary language title')
   makers=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid}
   if not makers(old) or not makers(old)<=makers(keep):reasons.append('linked creator or attribution differs')
   if not b['current_institution_id'] or a['current_institution_id'] not in (None,b['current_institution_id']):reasons.append('holding context differs')
   if a['primary_media_id']:reasons.append('legacy primary media needs individual transfer review')
   for table in ('artwork_places','curated_collection_items','artwork_media'):
    if any(r['artwork_id']==old for r in snap[table]):reasons.append('legacy '+table+' needs individual preservation review')
   if not any(r['entity_id']==keep and r['scheme']=='wikidata' and r['external_id']==review['qid'] for r in snap['external_identifiers']):reasons.append('canonical exact Wiki identity missing')
   common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep}
   if reasons:holds.append(dict(qid=review['qid'],old_slug=a['slug'],canonical_slug=slug,reasons=reasons));continue
   context='Exact existing FNG object authority plus current primary inventory, full source-language title and identical linked creator/attribution. Legacy placeholder lacks holding institution; reviewed named record supplies documented museum holding and selected reproduction where available. Preserve all original dates, titles, attributions, rights and immutable source assertions on archived identity; no silent date replacement or current-display inference.'
   if any(a[k]!=b[k] for k in ('creation_year_start','creation_year_end','date_precision')):context+=' Existing date assertions differ; retain both originals and resolve primary missing-date enrichment separately.'
   e=dict(key=oid,canonical_slug=slug,old_slug=a['slug'],primary=dict(receipt=evidence['primary_receipt'],object_url=evidence['object_url'],primary_object=obj,identity_review=evidence,existing_exact_authority='fng-object:'+oid),institution_context=context,targets={target:dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common),issues=[])});entries.append(e);snapshots[oid]=snap
 assert len({e['old_slug'] for e in entries})==len(entries) and len({e['canonical_slug'] for e in entries})==len(entries)
 CORE.save_new(p.BACK/(target+'-preimages.json'),snapshots);CORE.save_new(p.RUN/'plan.json',entries);pin=CORE.sha((p.RUN/'plan.json').read_bytes());CORE.save_new(p.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=pin,pairs=len(entries),holds=holds,target=target));print(target,'FNG physical-object merge plan',len(entries),'holds',len(holds),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','apply','verify']);parser.add_argument('--target',choices=['local','production'],required=True);args=parser.parse_args();configure(args.target)
 if args.command=='plan':plan(args.target)
 else:getattr(p,args.command)(targets=(args.target,))
