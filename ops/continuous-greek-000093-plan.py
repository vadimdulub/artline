import importlib.util,fcntl,json
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000093.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
holds={
'grinzing-on-the-outskirts-of-vienna':'Compound inventory Π.11533/3α,β may denote recto/verso or paired views. Exact catalogue unit and supplied image side require review; no guessed drawing type or split units.',
'hymn-to-the-dawn':'Existing same creator/title and 60 x 20 cm dimensions (reversed order); reconcile existing unknown-date work rather than insert.',
'landscape-62':'Generic landscape with 1904–1909 range; resolve exact composition and existing landscape identities.',
'landscape-50':'Generic landscape with ca 1909–1911 date; resolve exact composition and existing landscape identities.',
'still-life-17':'Existing same title/creator and 1930–1935 date. Reconcile existing record rather than insert.',
'agia-sofia':'Existing same creator/title and 85 x 78 cm support; reconcile unknown-date existing record.',
'pine-tree':'Existing same creator/title with similar 60 x 70 cm dimensions and unknown date; exact physical match requires review.',
'the-annunciation':'Multiple same-creator Annunciation versions with overlapping 1910–1911 dates. Distinct support and size not sufficient alone; compare complete compositions.',
'hydra':'Existing same creator/title and exact 23 x 31 cm size, missing date; do not insert duplicate.',
'still-life-10':'Existing Still Life with Bottles has unknown date; review composition and inventory before claiming distinct version.'}
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 rs=h.load(b.E/b.PHASE/'source-records.json.gz');chosen=[r for r in rs if r['source_id'] not in holds];assert len(chosen)==5
 overlay={'athens/'+k:{'editorial_hold':v} for k,v in holds.items()};overlay['athens/candle-lighting']=dict(medium='Oil on canvas mounted on panel',dimensions=None,source_type='painting',parser_correction='Source description contains support only; no dimensions provided. Preserve absent dimension.')
 h.save(b.E/b.PHASE/'final-editorial-review.json.gz',overlay)
 with h.connect() as db:
  inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
  prior=h.load(b.E/'preserved-parthenis-before.json.gz')['artworks'];assert h.snapshot(db,list(prior))==prior
  checks=[];allcandidates=set()
  for r in chosen:
   ex=list(db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme=ANY(%s) AND external_id=%s))",(r['source_url'],h.SCHEMES['athens'],r['source_id'])))
   ac=list(db.execute('SELECT id::text,title FROM artworks WHERE accession_number=%s',(r['accession_number'],)))
   ci=list(db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(r['source_url'],)))
   ti=list(db.execute('SELECT a.id::text,a.title,a.unlinked_creator_label,a.date_display,a.work_type,a.accession_number,a.current_institution_id::text,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists FROM artworks a WHERE a.normalized_title=%s',(h.norm(r['title']),)))
   unresolved=[x for x in ti if r['verified_artist_id'] in x['artists'] or not x['artists'] or x['current_institution_id']==b.MID]
   separated=[]
   for x in unresolved[:]:
    if x['id'] in {'67215440-db96-51cc-9488-fbc2b108fd2f','159ab116-942c-545b-9b2d-970b5fbbd364','862dd40e-49ee-4db0-89a9-d5a43ea226bc'}:
     assert x['unlinked_creator_label'] in ['Hugh Lauren Mills; Albert Carman; Artist Color Proof Associates','Nicholas Chevalier','Charles-François Daubigny']
     separated.append(dict(artwork_id=x['id'],basis='Named other creator, different source inventory/date/type; not Parthenis Π.6485 dated 1917–1920. Source label retained.',record=x));unresolved.remove(x)
   if r['source_id']=='saint-sebastian':
    reviewed_labels={'German 15th Century','Giovanni Battista Cima da Conegliano','Antonio Pirri','Antonio Rimpacta','Gerrit van Honthorst','Bernardino Zaganelli','Italian, Tuscany','Anonymous, Italian, Roman-Bolognese, 17th century','Anonymous; Raphael Sadeler I; After Titian (Tiziano Vecellio)','Hans Friedrich Schorer; After Jacopo Tintoretto (Jacopo Robusti)','Raphael Sadeler I; Anonymous; After Titian (Tiziano Vecellio)','Gerolamo Giovenone','anonymous',None,'Giorgio Schiavone','Matteo di Giovanni','Guido Reni','Antonio Bellucci','Joseph Benoît Suvée;  Augustin van den Berghe','Paduan 16th Century','North Italian 15th Century'}
    for x in unresolved[:]:
     assert x['unlinked_creator_label'] in reviewed_labels and x['current_institution_id'] and x['current_institution_id']!=b.MID
     assert x['date_display'] and x['date_display'] not in ['?', 'Unknown date']
     separated.append(dict(artwork_id=x['id'],basis='Reviewed historic 15th–18th-century attribution/date and independent museum identity; not Parthenis 1935–1938 oil Π.6457. Type, inventory and source date retained in record.',record=x));unresolved.remove(x)
   print(r['source_id'],'title_candidates',len(ti),'UNRESOLVED',unresolved,flush=True)
   assert not ex and not ac and not ci and not unresolved
   checks.append(dict(source_id=r['source_id'],native=ex,accession=ac,citations=ci,title_candidates=ti,unresolved=unresolved,explicit_separations=separated,separation='Global exact-title candidates belong to other linked creators; all selected creator records separately inspected.'))
   allcandidates.update(x['id'] for x in ti)
  b.save('other-title-candidates-before.json.gz',dict(at=h.now(),artworks=h.snapshot(db,list(allcandidates))))
  b.save('final-global-identity-reconciliation.json',dict(at=h.now(),records=checks,existing_creator_works_reviewed=len(prior),scope='All 68 creator works reviewed by title, date, medium, dimensions, accession. Fifty existing images actually viewed in six immutable prior sheets; 18 unillustrated works metadata-only. Ten version/duplicate/unit holds.'))
  previous=h.load(b.E.parent/'000092/norway/independent-production-verification.json');ids=list(previous['after']);assert h.snapshot(db,ids)==previous['after']
  for row in previous['rows']:
   actual=db.execute('SELECT a.primary_media_id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=%s',(row['id'],)).fetchone();assert actual['primary_media_id']==row['primary_media_id'] and actual['adapter_version']==row['adapter_version'] and actual['evidence_json']==row['evidence_json']
  b.save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=92,previous_batch_verified=True,verified_ids=ids,snapshot_equal=True,rights_selection_and_operation_equal=True,counted_as_current_batch=0))
 if not (b.E/b.PHASE/'plan-pin.json').exists():h.plan(b.PHASE)
 p,pin=h.pinned(b.PHASE);assert len(p['records'])==5 and len(p['held'])==10 and not p['new_institutions'] and all(not x['before'] for x in p['records'])
 checks=h.load(b.E/'parthenis-global-identity-reconciliation.json')['records']
 b.save('editorial-selection-review.json',dict(at=h.now(),selected=[r['source_id'] for r in p['records']],held_versions=holds,date_holds=[r for r in checks if 'date' in r['outcome'].lower() or 'boundary' in r['outcome'].lower()],existing_excluded=sum(bool(r['existing']) for r in checks),plan_sha256=pin))
 b.save('authorization.json',dict(at=h.now(),batch=93,production_authorization='User explicitly authorizes bounded source-backed inserts, authentic images and documented holdings without batch approval.',image_authorization='Greek museum extension for eligible works through 1955; actual museum rights restricted, not a copyright-holder licence.',source_registry_id='national_gallery_athens',policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',local_catalogue_read_only=True))
 b.images()
