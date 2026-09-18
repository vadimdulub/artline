#!/usr/bin/env python3
"""Two exact primary/Commons object matches; one similar seascape stays held."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-greek-primary-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;a.RUN=m.x.BASE/'greek-historical/primary-objects/existing-image-crosswalks';SOURCE='overnight-greek-image-object-crosswalk-20260913'
CASES=[('Q56706738','childrens-concert','greek-childrens-concert','Π.475'),('Q128259005','church-in-blooming-field-in-bavaria-8063','greek-primary-church-in-blooming-field-in-bavaria-8063','Κ.355')]
def plan():
 if (a.RUN/'application-plan.json').exists():return
 visual=json.loads((m.x.BASE/'greek-historical/primary-objects/image-comparison/visual-review.json').read_text());images=[];targets={t:[] for t in ('local','production')}
 for q,key,slug,accession in CASES:
  assert q in visual['accepted'];ready=m.x.BASE/'greek-historical/GR/round-15/delivery/ready'/(q+'.json');im=json.loads(ready.read_text())['image'];assert im and im['rights_status']=='public_domain'
  capture=json.loads((m.x.BASE/'greek-historical/primary-objects/image-comparison'/(q+'.json')).read_text())
  mid=m.m.uid('image/'+q+'/'+im['sha256']);image={**im,'qid':q,'key':key,'media_id':mid,'page':im['source_page_url'],'identity':dict(choice=dict(page=im['commons_page'],receipt=im['commons_receipt']),identity_basis=visual['accepted'][q],primary_image_inspection=capture,ready_sha256=CORE.sha(ready.read_bytes()))}
  for target in targets:
   with m.m.r.base.connect(target=='production') as db,db.transaction():
    db.execute('SET TRANSACTION READ ONLY');w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',(slug,)).fetchone()['row'];assert w['status']=='review' and w['published_at'] is None and not w['primary_media_id'] and w['accession_number']==accession and w['creation_year_end']<=1970
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(q,)).fetchone()
    maker=db.execute("SELECT p.slug,p.display_name,p.birth_year,p.death_year FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id JOIN external_identifiers ei ON ei.entity_type='artist' AND ei.entity_id=p.id AND ei.scheme='nationalgallery-gr-artist' AND ei.external_id='iakovidis-georgios' WHERE aa.artwork_id=%s AND aa.attribution_role='primary'",(w['id'],)).fetchone();assert maker and (maker['birth_year'],maker['death_year'])==(1853,1932)
    person=json.loads((m.x.r.RUN/'entities/Q510723.json').read_text())['entity'];assert maker['display_name'] in m.m.r.labels(person) and (m.m.r.year(person,'P569'),m.m.r.year(person,'P570'))==(1853,1932)
    assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='nationalgallery-gr-work' AND external_id=%s",(w['id'],key)).fetchone()
    targets[target].append(dict(key=key,work=w));image.update(title=w['title'],artist=maker['display_name'],artwork_slug=slug,artist_slug=maker['slug'])
  images.append(image)
 for t in targets:CORE.save_new(m.BACKUPS/('greek-existing-image-crosswalk-'+t+'-preimages.json'),targets[t])
 data=dict(at=CORE.now(),images=images,targets=targets,qa=visual);CORE.save_new(a.RUN/'application-plan.json',data);CORE.save_new(a.RUN/'application-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((a.RUN/'application-plan.json').read_bytes()),images=2));print('Greek existing image plan2',flush=True)
def apply():
 a.apply();data,pin=a.read_plan();images={im['key']:im for im in data['images']}
 for target in ('local','production'):
  dest=a.RUN/('crosswalk-'+target+'-verified.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Greek primary museum object and exact Commons composition crosswalk','collection_page','https://www.nationalgallery.gr/')
    for row in data['targets'][target]:
     im=images[row['key']];q=im['qid'];aid=row['work']['id'];found=db.execute("SELECT entity_id::text,entity_type FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(q,)).fetchone()
     if found:assert found==dict(entity_id=aid,entity_type='artwork')
     else:m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=q,canonical_url='https://www.wikidata.org/wiki/'+q,source_id=sid,retrieved_at=im['commons_receipt']['retrieved_at']))
     if not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s",(aid,sid,q)).fetchone():
      m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='exact_image_object_crosswalk',source_id=sid,source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,retrieved_at=im['commons_receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary_identity=im['identity'],source_image=im['source_page_url'],museum_creation_preserved=row['work']['date_display'],publication_status='review'),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY')
    for row in data['targets'][target]:assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(row['work']['id'],images[row['key']]['qid'])).fetchone()
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,verified_crosswalks=2));print(target,'Greek object crosswalks2',flush=True)
 a.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);x=p.parse_args();globals()[x.command]()
