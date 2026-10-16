#!/usr/bin/env python3
import importlib.util,fcntl
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000088.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 rs=h.load(b.E/b.PHASE/'source-records.json.gz')
 holds={
 'victory-triptych':'Existing Victory Triptych shares creator, date, medium and 50 x 92 cm; reconcile existing record rather than insert.',
 'figure-17':'Generic figure subject could overlap existing Angel/Pink Figure or related personifications; defer composition/version reconciliation.',
 'the-resurrection-2':'Existing same creator/title but unknown date and different recorded dimensions; resolve physical identity before new insertion.',
 'landscape-16':'Koutlidis Foundation Collection credit: separate ownership/custody evidence and generic-landscape identity review required.',
 'pine-trees-on-kerkyra':'Existing same creator/title/date/dimensions; exclude duplicate addition.',
 'the-harbor-of-kalamata':'Existing same creator/title/date/dimensions; exclude duplicate addition.',
 'landscape-35':'Generic landscape and overlapping 1912–1917 dates require comparison with all existing landscapes.',
 'landscape-27':'Generic landscape and overlapping 1912–1917 dates require comparison with all existing landscapes.',
 'musician':'Potential title or figure relationship to existing Music/St. Cecilia; defer exact composition reconciliation.',
 'portrait-of-pan-papanastasiou':'Existing Portrait of P. Papathanasiou shares 60 x 70 cm; spelling variation and unknown date require reconciliation.',
 'hut-with-hung-clothes':'Koutlidis Foundation Collection credit requires documented ownership/custody distinction before holding claim.',
 'portrait-of-a-woman-6':'Koutlidis Foundation Collection credit and generic portrait require ownership/custody and version reconciliation.',
 'pitcher-2':'Potential overlap with existing Still Life/Still Life with Bottles; exact composition comparison remains required.',
 'portrait-of-ioulia-partheni':'Existing full-length Portrait of Julia Parthenis with same 1911–1914 period; do not add duplicate based on translated name.'}
 chosen=[r for r in rs if r['source_id'] not in holds];assert {r['source_id'] for r in chosen}=={'scene-in-front-of-an-ancient-temple','the-artists-father','temple-of-olympian-zeus'}
 overlay={'athens/'+k:{'editorial_hold':v} for k,v in holds.items()};h.save(b.E/b.PHASE/'final-editorial-review.json.gz',overlay)
 with h.connect() as db:
  inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
  prior=h.load(b.E/'preserved-parthenis-before.json.gz')['artworks'];assert h.snapshot(db,list(prior))==prior
  checks=[]
  for r in chosen:
   ex=list(db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme=ANY(%s) AND external_id=%s))",(r['source_url'],h.SCHEMES['athens'],r['source_id'])))
   ac=list(db.execute('SELECT id::text,title FROM artworks WHERE accession_number=%s',(r['accession_number'],)))
   ci=list(db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(r['source_url'],)))
   ti=list(db.execute('SELECT a.id::text,a.title,a.current_institution_id::text,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists FROM artworks a WHERE a.normalized_title=%s',(h.norm(r['title']),)))
   unresolved=[x for x in ti if r['verified_artist_id'] in x['artists'] or not x['artists'] or x['current_institution_id']==b.MID]
   separated=[]
   for x in unresolved[:]:
    if r['source_id']=='the-artists-father' and x['id']=='635c4cde-95d0-5127-bede-523ea2c2a12e':
     old=h.load(b.E/'father-global-collision-review.json')['artworks'];assert h.snapshot(db,list(old))==old
     a=old[x['id']]['artwork'];assert a['unlinked_creator_label']=='Max Thalmann' and a['work_type']=='print' and a['creation_year_end']==1909
     separated.append(dict(artwork_id=x['id'],basis='Different creator Max Thalmann, lithograph, 1909, accession 2020.381.7, sheet 47 x 36.2 cm. Selected Parthenis oil on cloth is 1897–1899, 64 x 53 cm, Π.9992.'))
     unresolved.remove(x)
   assert not ex and not ac and not ci and not unresolved,(r['source_id'],ex,ac,ci,unresolved)
   checks.append(dict(source_id=r['source_id'],native=ex,accession=ac,citations=ci,title_candidates=ti,explicit_version_separation=separated,unresolved=unresolved))
  b.save('final-global-identity-reconciliation.json',dict(at=h.now(),records=checks,existing_creator_works_reviewed=len(prior),scope='All 65 creator works inspected by title/date/medium/dimensions/accession. Five saved contact sheets covering 47 existing images actually viewed. New selections subject to individual image comparison before apply. No new artists.'))
 if not (b.E/b.PHASE/'plan-pin.json').exists():h.plan(b.PHASE)
 p,pin=h.pinned(b.PHASE);assert len(p['records'])==3 and len(p['held'])==14 and not p['new_institutions'] and all(not x['before'] for x in p['records'])
 b.save('editorial-selection-review.json',dict(at=h.now(),selected=[r['source_id'] for r in p['records']],held_versions=holds,date_holds=[r for r in h.load(b.E/'parthenis-global-identity-reconciliation.json')['records'] if 'date' in r['outcome'].lower() or 'boundary' in r['outcome'].lower()],existing_excluded=2,plan_sha256=pin))
 b.save('authorization.json',dict(at=h.now(),batch=88,production_authorization='User explicitly authorizes bounded source-backed inserts and authentic images with documented holdings, no batch approval.',image_authorization='Greek museum extension for eligible works through 1955; actual museum rights retained restricted; not a copyright-holder licence.',source_registry_id='national_gallery_athens',policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',local_catalogue_read_only=True))
 print('Three selected for source/visual verification; fourteen identity/custody holds; five date holds; two existing excluded.')
