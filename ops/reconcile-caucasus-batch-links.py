#!/usr/bin/env python3
"""Reconcile object labels to exact authorities created later in the same batch."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;plan=json.loads((s.RUN/'batches/batch-001.json').read_bytes());records={x['record']['qid']:x['record'] for x in plan['entries']}
for target in ['local','production']:
 receipt=s.RUN/('batch-creator-links-'+target+'.json')
 if receipt.exists():continue
 updates=[]
 with s.connect(target) as db:
  for state in plan['targets'][target]:
   if state['artist_id']:continue
   rec=records[state['qid']];artist=db.execute("SELECT a.id::text,a.slug FROM external_identifiers e JOIN artists a ON a.id=e.entity_id AND e.entity_type='artist' WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status='review'",(rec['creator_qid'],)).fetchone()
   if not artist:db.commit();continue
   before=db.execute('SELECT id::text,unlinked_creator_label,status FROM artworks WHERE id=%s FOR UPDATE',(state['artwork_id'],)).fetchone();assert before['status']=='review'
   if not before['unlinked_creator_label']:db.commit();continue
   assert before['unlinked_creator_label']==rec['creator_label']
   assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(state['artwork_id'],)).fetchone()
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(state['artwork_id'],artist['id'],'Exact unqualified P170 '+rec['creator_qid']+' matches the authority profile created in this batch; original source capture '+rec['entity_receipt']['sha256']))
   db.execute("UPDATE artworks SET unlinked_creator_label=NULL,revision=revision+1,updated_at=now(),updated_by='local-european-research' WHERE id=%s",(state['artwork_id'],));db.commit();updates.append({'qid':state['qid'],'before':before,'artist':artist,'source_creator_qid':rec['creator_qid']})
 s.save(receipt,{'at':s.core.now(),'updates':updates});print(target,'exact creator links',len(updates),flush=True)
