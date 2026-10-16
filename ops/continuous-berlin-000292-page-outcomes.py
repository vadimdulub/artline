import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
reasons={
'2291559':'Saved for metadata/qualified-creator reconciliation. Primary front5808602 isCC BY-NC-SA4.0; open backs/details are not substitutes. No image download.',
'2388716':'Saved for metadata reconciliation. Only native Arbeitsfoto5827810 has no rights label; do not download before rights/version review. Unknown material remains unknown.',
'1787259':'Saved for exact metadata/composition reconciliation. Archive front5756113 isPublic Domain Mark1.0 with photographerSBM Archivaufnahme; modernMarionBoehl views include side/back. Review actual full-front choice before preparation.',
'1720838':'Saved for named-creator reconciliation. Structured actors empty but narrative namesEmmanuelTzanes and1640; never classify as anonymous from empty actors alone. Reconcile global1640Annunciation exact version and artist aliases before insert.',
'1791014':'Saved for metadata reconciliation. Open image5876774 explicitlyDetailansicht; fullAufsicht5606173 has unknown rights. No detail substitute or image download.',
'1787264':'Saved for exact work and image-version reconciliation. Two MarionBoehl images5739090/5739089 bothVorderseite; inspect and select complete composition after metadata dedup.'}
rows=[]
with h.connect() as db:
 for oid in h.load(E/'berlin-discovery.json')['source_ids']:
  o,rc=b.native(oid);urls=[o['permalink'],'https://search.smb.museum/en/object/obj-'+oid,'https://search.smb.museum/object/obj-'+oid,'https://recherche.smb.museum/detail/'+oid]
  exact=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((external_id=%s AND scheme ILIKE '%%smb%%') OR canonical_url=ANY(%s))",(oid,urls))]
  scope=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,date_display FROM artworks WHERE current_institution_id=%s AND (accession_number=%s OR normalized_title=%s)',(b.MID,o['ident'],h.norm(o['title'])))];assert len(scope)<100
  rows.append(dict(source_id=oid,title=o['title'],inventory=o['ident'],native_dates=o['dating'],source_url=rc['url'],capture_sha256=rc['sha256'],native_identity_matches=exact,scoped_title_inventory_candidates=scope,state='selected_for_delivery' if oid in b.SELECTED else 'saved_unselected_pending_review',reason='Pinned metadata and images' if oid in b.SELECTED else reasons[oid],image_downloaded=oid in b.SELECTED))
b.save('page4-object-outcomes.json',dict(at=h.now(),index_page=4,source_ids=[r['source_id'] for r in rows],notices_researched=10,rows=rows,selected=4,pending=6,provider_access_failures=[],no_unspecified_date_inferred=True))
print('All ten page4 notices accounted for; six saved for separate bounded reconciliation')
