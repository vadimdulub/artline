import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
ids=['78be24b0-c7c2-56ae-b6cc-76307f784dac','d2a7f881-57cc-5c0f-97be-036bd3ceca93','826518d4-5da4-5497-91d6-aaae06aee7ad']
with h.connect() as db:
 rows=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 b.save('closest-collision-source-evidence.json',dict(at=h.now(),rows=rows))
 for r in rows:print(r['entity_id'],r['field_name'],r['evidence_note'][:10000])
