import importlib.util,copy,collections
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
local=m.base.load(m.RUN/'local-plan.json.gz');selected=[];missing=[]
with m.base.connect('production') as db:
 for offset in range(0,len(local),500):
  batch=local[offset:offset+500]
  data=db.execute('''SELECT p.artist_id original_artist_id,a.id artist_id,w.id artwork_id,w.slug,w.status,w.primary_media_id,
    artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision) creation_scope
    FROM jsonb_to_recordset(%s) AS p(artist_id uuid,artwork_id uuid,attribution_role text,evidence_json jsonb)
    JOIN artists a ON a.slug=p.evidence_json->>'artist_slug'
    JOIN artworks w ON w.slug=p.evidence_json->>'artwork_slug'
    JOIN artwork_artists aa ON aa.artist_id=a.id AND aa.artwork_id=w.id AND aa.attribution_role=p.attribution_role
    WHERE a.status<>'archived' AND w.status<>'archived' ''',(Jsonb(batch),)).fetchall()
  byid={str(r['original_artist_id']):r for r in data}
  for plan in batch:
   row=byid.get(plan['artist_id'])
   if not row or row['creation_scope']!='eligible':missing.append(plan);continue
   out=copy.deepcopy(plan);out.update(artist_id=str(row['artist_id']),artwork_id=str(row['artwork_id']))
   out['evidence_json'].update(publication_preserved=row['status'],image_available=bool(row['primary_media_id']),production_identity_basis='Exact artist slug, exact artwork slug, linked attribution and eligible date; sources preserved from aligned catalogue')
   selected.append(out)
  db.commit()
  if offset%2500==0:print('production identity checked',offset+len(batch),flush=True)
m.save('production-plan.json.gz',selected);m.save('production-unmatched-local-selections.json.gz',missing)
m.save('production-plan-summary.json',dict(selected=len(selected),with_images=sum(s['evidence_json']['image_available'] for s in selected),unmatched_local_choices=len(missing),bases=dict(collections.Counter(s['selection_basis'] for s in selected))))
print('production plan',len(selected),'unmatched',len(missing),flush=True)
