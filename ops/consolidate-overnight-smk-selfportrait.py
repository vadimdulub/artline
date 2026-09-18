#!/usr/bin/env python3
"""One exact SMK physical object represented by a placeholder and named work."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;CORE=p.CORE;ROOT=m.x.BASE/'duplicates/smk-selfportrait-primary'
OLD='research-candidate-5945875aa310300a6dc7876ff5ab4539e9a00f666b3ee1004e8b2110825f315e';KEEP='wikimedia-artwork-q20355651'
def configure(target):
 p.RUN=ROOT/target;p.BACK=m.BACKUPS/'smk-selfportrait'/target;p.SOURCE='overnight-smk-selfportrait-physical-identity-20260913';p.SOURCE_NAME='SMK: William Lönnberg self-portrait exact physical-object reconciliation';p.SOURCE_ROOT='https://open.smk.dk/'
def plan(target):
 configure(target)
 if (p.RUN/'plan.json').exists():return
 receipt=json.loads((ROOT/'KMS4523.receipt.json').read_text());raw=(ROOT/'KMS4523.json').read_bytes();assert CORE.sha(raw)==receipt['sha256'];items=json.loads(raw)['items'];assert len(items)==1;obj=items[0]
 assert obj['object_number']=='KMS4523' and obj['number_of_parts']==1 and obj['titles'][0]['title']=='Selvportræt' and obj['artist']==['William Lönnberg'] and obj['production'][0]['creator_nationality']=='Finsk' and obj['production_date'][0]['period']=='1947'
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');p.a.ensure_schema(db);rows={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([OLD,KEEP],))};assert len(rows)==2;old=rows[OLD];keep=rows[KEEP];snap=p.a.snapshot(db,[old,keep]);works={w['id']:w for w in snap['artworks']};a=works[old];b=works[keep]
  assert all(w['status']=='review' and w['published_at'] is None and w['creation_year_start']==w['creation_year_end']==1947 and w['date_precision']=='exact' and w['work_type']=='painting' for w in works.values())
  assert a['title']=='Selvportræt' and a['unlinked_creator_label']=='William Lönnberg' and a['current_institution_id'] is None and a['accession_number'] is None
  assert b['title']=='Self-Portrait' and b['accession_number']=='KMS4523'
  assert db.execute("SELECT 1 FROM institutions WHERE id=%s AND slug='statens-museum-for-kunst'",(b['current_institution_id'],)).fetchone()
  assert not any(r['artwork_id']==old for r in snap['artwork_artists'])
  maker=db.execute("SELECT a.* FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=%s AND aa.attribution_role='primary'",(keep,)).fetchall();assert len(maker)==1 and maker[0]['slug']=='wikimedia-painter-q11902436' and maker[0]['birth_year']==1887 and maker[0]['death_year']==1949
  assert any(r['entity_id']==old and r['source_record_id']=='KMS4523' and r['source_url']=='https://open.smk.dk/artwork/image/KMS4523' for r in snap['citations'])
  media={r['id']:r for r in snap['media_assets']};assert media[a['primary_media_id']]['checksum_sha256']==media[b['primary_media_id']]['checksum_sha256']=='cd420e7d08ca80431b5ce1fadd7224760f316192bddf67620f009b8443dbeeaa'
  for table in ('artwork_places','curated_collection_items'):assert not any(r['artwork_id']==old for r in snap[table])
  common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep};assert not common
 e=dict(key='KMS4523',canonical_slug=KEEP,old_slug=OLD,primary=dict(receipt=receipt,primary_object=obj,source_inventory='KMS4523',visual_review='Actual full-frame derivative inspected: male painter self-portrait. Both existing derivatives have identical SHA256; exact SMK primary object and original placeholder citation agree on1947,William Lönnberg,KMS4523. This is one-part painting, not a series or panel.'),institution_context='SMK explicitly identifies Finnish painter William Lönnberg1887–1949 and a single1947self-portrait. Original placeholder maker label/date/exactSMKsource and image agree. Richer linked Wikimedia record remains canonical. Preserve both original media assets and all source assertions; no on-view claim or new date added.',targets={target:dict(old_id=old,canonical_id=keep,preserve_archived_schemes=[],issues=[])})
 CORE.save_new(p.BACK/(target+'-preimages.json'),{'KMS4523':snap});CORE.save_new(p.RUN/'plan.json',[e]);pin=CORE.sha((p.RUN/'plan.json').read_bytes());CORE.save_new(p.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=pin,pairs=1,target=target));CORE.save_new(p.RUN/'quality-review.json',dict(at=CORE.now(),approved=True,plan_sha256=pin,review=e['institution_context']));print(target,'SMK self-portrait merge planned',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','apply','verify']);parser.add_argument('--target',choices=['local','production'],required=True);args=parser.parse_args();configure(args.target)
 if args.command=='plan':plan(args.target)
 else:getattr(p,args.command)(targets=(args.target,))
