#!/usr/bin/env python3
"""Two independently reviewed Pavia catalogue pairs, preserving source variants."""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;CORE=p.CORE;p.RUN=m.x.BASE/'duplicates/pavia-physical-objects';p.BACK=m.BACKUPS/'pavia-physical-objects';p.SOURCE='overnight-pavia-physical-objects-20260913'
p.SOURCE_NAME='Pavia: exact primary SIRBeC museum inventories and physical-object reconciliation';p.SOURCE_ROOT='https://www.lombardiabeniculturali.it/'
def plan():
 if (p.RUN/'plan.json').exists():return
 root=m.x.BASE/'duplicates/same-title-deep-review';data=json.loads((root/'candidates.json').read_text());entries=[]
 cases=[('P1657','lanca alla zelata','F0060-00008','SWF01-00507','3f882f3d1f30'),('P1655','figura in giardino','F0060-00009','SWF01-00505','ff8d5c1fe740')]
 for inventory,title,first,second,keepkey in cases:
  pair=next(e for e in data['pairs'] if e['key'][0]=='musei-civici-pavia' and e['key'][1]==title);keep=next(w for w in pair['works'] if keepkey in w['slug']);old=next(w for w in pair['works'] if w!=keep);evidence=[]
  for oid in (first,second):
   file=root/'captures'/(oid+'.pdf');receipt=json.loads(file.with_suffix('.pdf.receipt.json').read_text());assert CORE.sha(file.read_bytes())==receipt['sha256'];body=file.with_suffix('.pdf.txt').read_text()
   assert re.search(r'Numero:\s*P\s*'+inventory[1:]+r'\b',body) and 'Mariani' in body and '1857' in body and '1927' in body
   assert 'Morone' in body and '2001' in body
   evidence.append(dict(receipt=receipt,catalogue_id=oid,inventory=inventory,capture_path=str(file),independent_visual_review='Actual first-page museum reproductions inspected side by side: identical composition and pigment details for this pair. Images used only as research evidence, not republished catalogue assets.'))
  entries.append(dict(key=inventory,canonical_slug=keep['slug'],old_slug=old['slug'],primary={**evidence[0],'alternate_record':evidence[1]},institution_context='Same Musei Civici Pavia physical inventory, Pompeo Mariani, Morone donation 2001, oil on wood, matching dimensions and identical primary photographs. Preserve circa 1896 on Lanca canonical record. Figura signature position differs in source text and newer PDFs contain unrelated legacy inventory placeholders; those assertions are retained as evidence, not imported facts.',targets={}))
 snapshots={t:{} for t in ('local','production')}
 for target in snapshots:
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');p.a.ensure_schema(db)
   for e in entries:
    rows={r['slug']:r['id'] for r in db.execute('SELECT slug,id::text FROM artworks WHERE slug=ANY(%s)',([e['canonical_slug'],e['old_slug']],))};assert len(rows)==2
    old=rows[e['old_slug']];keep=rows[e['canonical_slug']];snap=p.a.snapshot(db,[old,keep]);w={r['id']:r for r in snap['artworks']}
    assert all(r['status']=='review' and r['published_at'] is None and r['accession_number'] is None for r in w.values())
    assert all(w[old][k]==w[keep][k] for k in ('title','creation_year_start','creation_year_end','current_institution_id','work_type'))
    maker=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid}
    assert maker(old)==maker(keep) and maker(keep)
    assert not w[old]['primary_media_id']
    for table in ('artwork_places','curated_collection_items','artwork_media'):assert not any(r['artwork_id']==old for r in snap[table]),table
    for aid,oid in ((keep,e['primary']['catalogue_id']),(old,e['primary']['alternate_record']['catalogue_id'])):assert any(r['entity_id']==aid and (r['source_url'] or '').rstrip('/').endswith('/'+oid) for r in snap['citations'])
    assert any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
    common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep}
    e['targets'][target]=dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common),issues=[]);snapshots[target][e['key']]=snap
 for e in entries:
  comparable=lambda t:[{k:w[k] for k in ('slug','title','date_precision','creation_year_start','creation_year_end','status','accession_number')} for w in sorted(snapshots[t][e['key']]['artworks'],key=lambda w:w['slug'])]
  assert comparable('local')==comparable('production')
 for target,snap in snapshots.items():CORE.save_new(p.BACK/(target+'-preimages.json'),snap)
 CORE.save_new(p.RUN/'plan.json',entries);CORE.save_new(p.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((p.RUN/'plan.json').read_bytes()),pairs=len(entries)));print('Pavia two physical-object merges planned',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','apply','verify']);parser.add_argument('--target',choices=['local','production']);args=parser.parse_args()
 if args.command=='plan':assert not args.target;plan()
 else:getattr(p,args.command)(targets=(args.target,) if args.target else ('local','production'))
