#!/usr/bin/env python3
"""Apply pinned public identity evidence without changing artist publication."""
import importlib.util,json
from pathlib import Path
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-armenian-georgian-session.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def main():
 backup=json.loads((r.RUN/'backups.json').read_bytes());assert backup['production']['status']=='SUCCESSFUL';assert Path(backup['local']['path']).stat().st_size==backup['local']['bytes']
 path=r.RUN/'women-source-selection.json';raw=path.read_bytes();selected=json.loads(raw);assert len({x['qid'] for x in selected})==len(selected)
 migration=r.ROOT/'apps/server/db/migrations/0019_artist_gender_evidence.sql'
 for target in ['local','production']:
  if (r.RUN/('women-application-'+target+'.json')).exists():
   print(target,'existing application receipt retained',flush=True);continue
  output=[]
  with r.connect(target) as db:
   db.execute('SELECT pg_advisory_xact_lock(20250907001)')
   if not db.execute('SELECT 1 FROM schema_migrations WHERE filename=%s',(migration.name,)).fetchone():
    db.execute(migration.read_text());db.execute('INSERT INTO schema_migrations(filename) VALUES(%s)',(migration.name,))
   db.commit() # Release migration DDL/FK locks before acquiring evidence rows.
   for row in selected:
    rows=db.execute("SELECT a.id::text,a.slug,a.status FROM artists a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(row['qid'],)).fetchall()
    assert len(rows)<=1, 'Ambiguous artist authority'
    if not rows:output.append({'qid':row['qid'],'action':'missing_target_artist'});continue
    artist=rows[0];checksum=r.core.sha(json.dumps(row,sort_keys=True,ensure_ascii=False).encode())
    before=db.execute('SELECT to_jsonb(g) row FROM artist_gender_evidence g WHERE artist_id=%s',(artist['id'],)).fetchone()
    if before:
     assert before['row']['source_checksum']==checksum,'Existing gender evidence requires separate review'
    else:
     db.execute('INSERT INTO artist_gender_evidence(artist_id,is_woman,basis,source_url,source_record_id,source_checksum,evidence_json,checked_at) VALUES(%s,true,%s,%s,%s,%s,%s,%s)',(artist['id'],row['basis'],row['source_url'],row['qid'],checksum,Jsonb(row),row['checked_at']))
    db.commit() # One identity per transaction avoids catalogue editor lock-order cycles.
    output.append({'qid':row['qid'],**artist,'action':'already_applied' if before else 'inserted','checksum':checksum})
  r.save(r.RUN/('women-application-'+target+'.json'),{'at':r.core.now(),'selection_sha256':r.core.sha(raw),'migration_sha256':r.core.sha(migration.read_bytes()),'rows':output})
  print(target,len(output),'women evidence rows; artist publication preserved',flush=True)
if __name__=='__main__':main()
