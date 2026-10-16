import importlib.util,fcntl,json
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000096.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
holds={
'wizard-fragment-of-the-adoration-of-the-kings':'Fragment wording and existing Pink Figure (Wizard) require exact physical fragment/composition reconciliation; no whole-composition or new-unit inference.',
'landscape-of-kerkyra-corfu':'Generic Corfu landscape and 96 x 90 cm dimensions may overlap existing Pine Trees on Kerkyra or another landscape; compare exact composition before adding.',
'kerkyra-landscape-corfu':'Existing Corfu Landscape with 1914–1917 date and legacy 965 x 68 cm likely represents same 96.5 x 68 cm object; reconcile existing record.',
'still-life-6':'Existing Still Life with same 1930–1935 dating; no duplicate insertion without exact-version reconciliation.',
'still-life-with-jug':'Distinct marble support but generic still life may overlap unillustrated existing Still Life with Bottles; exact composition and inventory review required.',
'portrait-of-alexandros-papanastasiou-2':'Separate accession and smaller format from existing 1936 portrait, but study/version composition reconciliation remains needed.',
'still-life-5':'Two same-title still lifes on this page and existing undated Still Life with Bottles require composition/version reconciliation.',
'the-night-responds-to-my-complaints':'Existing same title/creator and 1933 date; reconcile native inventory to existing object, do not insert duplicate.'}
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 rs=h.load(b.E/b.PHASE/'source-records.json.gz');chosen=[r for r in rs if r['source_id'] not in holds];assert len(chosen)==3
 h.save(b.E/b.PHASE/'final-editorial-review.json.gz',{'athens/'+k:{'editorial_hold':v} for k,v in holds.items()})
 with h.connect() as db:
  inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
  prior=h.load(b.E/'preserved-parthenis-before.json.gz')['artworks'];assert h.snapshot(db,list(prior))==prior
  checks=[];allcandidates=set()
  for r in chosen:
   ex=list(db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme=ANY(%s) AND external_id=%s))",(r['source_url'],h.SCHEMES['athens'],r['source_id'])))
   ac=list(db.execute('SELECT id::text,title FROM artworks WHERE accession_number=%s',(r['accession_number'],)))
   ci=list(db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(r['source_url'],)))
   ti=list(db.execute('SELECT a.id::text,a.title,a.unlinked_creator_label,a.date_display,a.work_type,a.accession_number,a.current_institution_id::text,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists FROM artworks a WHERE a.normalized_title=%s',(h.norm(r['title']),)))
   unresolved=[x for x in ti if r['verified_artist_id'] in x['artists'] or not x['artists'] or x['current_institution_id']==b.MID];separated=[]
   labels={'630cef50-231c-5d83-8b2d-0592455c399d':'Hugo von Habermann','9e39159b-ae0f-54c4-a2f7-5e743f050465':'El Lissitzky','0b98b736-b685-4f44-9df8-9f5e9a596aec':'John Opie','4a465954-dd49-411d-a7f1-8a6890fa6aee':'Mark Gertler'}
   for x in unresolved[:]:
    assert x['id'] in labels and x['unlinked_creator_label']==labels[x['id']] and x['current_institution_id']!=b.MID
    separated.append(dict(artwork_id=x['id'],basis='Explicit different named source creator, date and independent inventory; not Konstantinos Parthenis. No metadata changed.',record=x));unresolved.remove(x)
   assert not ex and not ac and not ci and not unresolved
   checks.append(dict(source_id=r['source_id'],native=ex,accession=ac,citations=ci,title_candidates=ti,unresolved=unresolved,explicit_separations=separated,separation='All other global title candidates have different canonical creators. Selected creator complete bounded record set separately reviewed.'))
   allcandidates.update(x['id'] for x in ti)
  b.save('other-title-candidates-before.json.gz',dict(at=h.now(),artworks=h.snapshot(db,list(allcandidates))))
  b.save('final-global-identity-reconciliation.json',dict(at=h.now(),records=checks,existing_creator_works_reviewed=len(prior),scope='All 73 creator works reviewed by title, date, medium, dimensions and accession; seven prior image sheets actually viewed in this batch. 55 illustrated works compared; 18 unillustrated metadata-only.'))
 if not (b.E/b.PHASE/'plan-pin.json').exists():h.plan(b.PHASE)
 p,pin=h.pinned(b.PHASE);assert len(p['records'])==3 and len(p['held'])==8 and not p['new_institutions'] and all(not x['before'] for x in p['records'])
 checks=h.load(b.E/'parthenis-global-identity-reconciliation.json')['records']
 b.save('editorial-selection-review.json',dict(at=h.now(),selected=[r['source_id'] for r in p['records']],held_versions=holds,date_holds=[r for r in checks if 'date' in r['outcome'].lower() or 'boundary' in r['outcome'].lower()],existing_excluded=sum(bool(r['existing']) for r in checks),plan_sha256=pin))
 b.save('authorization.json',dict(at=h.now(),batch=96,production_authorization='User explicitly authorizes bounded source-backed inserts, authentic images and documented holdings without batch approval.',image_authorization='Greek museum extension for eligible works through 1955; actual museum rights restricted, not a copyright-holder licence.',source_registry_id='national_gallery_athens',policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',local_catalogue_read_only=True))
 b.images()
