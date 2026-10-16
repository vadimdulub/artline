import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000288.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
checks=[];tids=set();aids=set()
with h.connect() as db:
 for oid in b.SELECTED:
  o,rc=b.native(oid);titles=[o['title']]+b.ALIASES[oid]
  titles.extend(x['nameLine'] for x in o.get('additionalTitles',[]))
  matches=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text,date_display,dimensions_text,unlinked_creator_label FROM artworks WHERE normalized_title=ANY(%s) LIMIT 100',([h.norm(t) for t in titles],))]
  acc=[str(x['id']) for x in db.execute('SELECT id FROM artworks WHERE accession_number=%s',(o['ident'],))]
  tids.update(x['id'] for x in matches);aids.update(acc);checks.append(dict(source_id=oid,aliases=titles,matches=matches));print(oid,json.dumps(matches,ensure_ascii=False))
 for name,ids in [('global-title-collision-evidence.json',tids),('global-accession-collision-evidence.json',aids)]:
  b.save(name,dict(at=h.now(),snapshots=h.snapshot(db,list(ids)),identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(ids),))],citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) LIMIT 150",(list(ids),))]))
b.save('global-title-collision-selection.json',dict(at=h.now(),rows=checks))
