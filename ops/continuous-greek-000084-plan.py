#!/usr/bin/env python3
import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000084.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');overlay=h.load(b.E/b.PHASE/'final-editorial-review.json.gz');chosen=[r for r in rs if 'athens/'+r['source_id'] not in overlay];assert len(chosen)==4
with h.connect() as db:
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
 old=h.load(b.E/'aphrodite-global-collision-review.json')['artworks'];assert h.snapshot(db,list(old))==old
 globalchecks=[]
 for r in chosen:
  ex=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme=ANY(%s) AND external_id=%s))",(r['source_url'],h.SCHEMES['athens'],r['source_id']))]
  ac=[dict(x) for x in db.execute('SELECT id::text,title FROM artworks WHERE accession_number=%s',(r['accession_number'],))]
  ci=[dict(x) for x in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=%s",(r['source_url'],))]
  titles=[dict(x) for x in db.execute('SELECT a.id::text,a.title,a.current_institution_id::text,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists FROM artworks a WHERE a.normalized_title=%s',(h.norm(r['title']),))]
  unresolved=[x for x in titles if r['verified_artist_id'] in x['artists'] or not x['artists'] or x['current_institution_id']==b.MID]
  separated=[]
  for x in unresolved[:]:
   if r['source_id']=='aphrodite' and x['id'] in old:
    a=old[x['id']]['artwork'];assert (a['work_type']=='sculpture' and a['creation_year_end']==-200) or (a['unlinked_creator_label']=='Geraldine Owen' and a['creation_year_end']==1929)
    separated.append(dict(artwork_id=x['id'],basis='Different creator/date/medium: '+str(a['unlinked_creator_label'])+', '+a['work_type']+', '+str(a['creation_year_start'])+'–'+str(a['creation_year_end'])+'; distinct accession '+a['accession_number']));unresolved.remove(x)
  assert not ex and not ac and not ci and not unresolved,(r['source_id'],ex,ac,ci,unresolved)
  globalchecks.append(dict(source_id=r['source_id'],global_native=ex,global_accession=ac,global_source_citations=ci,global_title_candidates=titles,explicit_version_separation=separated,unresolved=[]))
 b.save('final-global-identity-reconciliation.json',dict(at=h.now(),records=globalchecks,creator_all_existing_works=61,identity_basis='Official inventories, distinct subject/person/site, creation dates, media and dimensions; global source/native/accession/title and all existing creator objects reviewed.'))
if not (b.E/b.PHASE/'plan-pin.json').exists():h.plan(b.PHASE)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==4 and len(p['held'])==14 and all(not x['before'] for x in p['records']) and not p['new_institutions']
b.save('editorial-selection-review.json',dict(at=h.now(),selected=[r['source_id'] for r in p['records']],held_versions={k:v['editorial_hold'] for k,v in overlay.items()},unselected_existing_objects=5,open_date_holds=['angel'],image_date_hold=['aphrodite'],metadata_plan_sha256=pin,normalization_correction='Held Allegorical Composition: Oil on canvas is a medium; no dimensions supplied.'))
print('Four new selected; fourteen identity/catalogue-unit holds; five existing; one open date hold')
