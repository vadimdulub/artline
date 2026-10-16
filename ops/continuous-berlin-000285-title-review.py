import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000285.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
ids=['aac79b47-9634-5ca9-9f46-5fd1c0d65af2','20a5fc6d-0109-595c-944f-3d41a88e12e1']
with h.connect() as db:
 rows=h.snapshot(db,ids);cites=[dict(x) for x in db.execute('SELECT entity_id::text,source_record_id,source_url,field_name,evidence_note FROM citations WHERE entity_type=\'artwork\' AND entity_id=ANY(%s::uuid[])',(ids,))]
 artists=[dict(x) for x in db.execute('SELECT aa.artwork_id::text,a.id::text,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,))]
 ext=[dict(x) for x in db.execute('SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type=\'artwork\' AND entity_id=ANY(%s::uuid[])',(ids,))]
 b.save('global-title-collision-evidence.json',dict(at=h.now(),snapshots=rows,citations=cites,artists=artists,identifiers=ext))
 for aid,v in rows.items():
  a=v['artwork'];print(json.dumps({k:a.get(k) for k in ['id','title','date_display','work_type','medium_text','dimensions_text','unlinked_creator_label','primary_media_id']},ensure_ascii=False));print([x for x in artists if x['artwork_id']==aid]);print([x for x in ext if x['entity_id']==aid]);print(json.dumps([x for x in cites if x['entity_id']==aid],ensure_ascii=False)[:10000])
