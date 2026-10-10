import importlib.util
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.base.load(m.RUN/'gap-final-plan-v2.json.gz');prior={str(r['artist_id']):r for r in m.base.load(m.BACKUP/'local-gap-before.json.gz')['keys']};changed=[]
with m.base.connect('local',readonly=False) as db:
 db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 for r in rows:
  old=prior.get(r['artist_id']);t=r['targets']['local']
  if not old or str(old['artwork_id'])==t['artwork_id']:continue
  current=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=%s',(r['artist_id'],)).fetchone()
  if str(current['artwork_id'])!=t['artwork_id']:continue
  evidence=current['evidence_json'];keys=['operation','artist_qid','artwork_qid','source_revision','recorded_year','source_collection_ids','source_inventory','holding_not_reconciled','display_not_claimed','publication_preserved','artist_slug','artwork_slug','artwork_title','selection_policy','image_available'];evidence={k:evidence[k] for k in keys}
  db.execute('UPDATE artist_key_artworks SET source_urls=%s,evidence_json=%s WHERE artist_id=%s',([r['source_url'],r['image_info']['descriptionurl']],Jsonb(evidence),r['artist_id']));changed.append(r['artist_id'])
 final=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id',([r['artist_id'] for r in rows],)).fetchall();m.base.save(m.BACKUP/'local-gap-key-evidence-final.json.gz',final)
m.save('local-gap-evidence-reconciliation.json',dict(updated=len(changed),artist_ids=changed,reason='When replacing a different key work, retain its previous evidence in audit history only; current sources describe the newly selected object.'))
print('Selection evidence reconciled',len(changed))
