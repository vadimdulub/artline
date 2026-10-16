import importlib.util,json
s=importlib.util.spec_from_file_location('h','ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
E=h.ROOT/'docs/research/continuous-production-20261011/batches/000283';p=h.load(E/'page2-global-identity-initial.json');ids=[x['id'] for r in p['records'] for x in r['exact']]
with h.connect() as db:
 snaps=h.snapshot(db,ids);ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))];cites=[dict(x) for x in db.execute("SELECT entity_id::text,source_url,field_name FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) LIMIT 100",(ids,))]
h.save(E/'global-accession-collision-evidence.json',dict(at=h.now(),snapshots=snaps,identifiers=ext,citations=cites,decision='Shared numeric inventory across independent museum namespaces; compare title, source URL, creator, dates and image. Do not merge based on accession alone.'))
for aid,row in snaps.items():
 a=row['artwork'];print(json.dumps({k:a[k] for k in ['id','title','date_display','creation_year_start','creation_year_end','work_type','unlinked_creator_label','current_institution_id']},ensure_ascii=False));print([x for x in ext if x['entity_id']==aid]);print([x for x in cites if x['entity_id']==aid])
