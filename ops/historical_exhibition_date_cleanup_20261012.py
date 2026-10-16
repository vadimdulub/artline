from pathlib import Path
import sys,json,hashlib,collections
import exhibitions_common as c
from psycopg import sql
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012'

def plan_dates():
 with c.connect()as db:
  rows=db.execute("SELECT id,title,start_year,end_year,status FROM exhibitions WHERE start_year>=1990 OR end_year>=1990 OR start_year<1600 ORDER BY id").fetchall()
  ids=[r['id']for r in rows]
  refs=db.execute('SELECT id,parent_exhibition_id FROM exhibitions WHERE parent_exhibition_id=ANY(%s::uuid[]) AND NOT(id=ANY(%s::uuid[]))',(ids,ids)).fetchall();assert not refs,refs
  counts={t:db.execute('SELECT count(*) n FROM '+t+' WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']for t in ['exhibition_entries','exhibition_publications','exhibition_participants','exhibition_occurrences','exhibition_source_records']}
 c.save(OUT/'date-removal-plan.json',dict(at=c.now(),reason='User-requested exhibition scope 1600–1989 inclusive; remove records with known dates outside that interval. Unknown dates retain research status pending date evidence.',events=rows,counts=counts))
 print('Date removal plan',len(rows),counts,flush=True)

def apply_dates():
 p=c.load(OUT/'date-removal-plan.json');ids=[r['id']for r in p['events']]
 with c.connect(write=True)as db:
  db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  current=db.execute('SELECT id,title,start_year,end_year,status FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  assert json.loads(json.dumps(current,default=str))==p['events'],'Exhibitions changed since plan'
  counts={}
  for t in ['exhibition_entries','exhibition_publications','exhibition_participants','exhibition_occurrences','exhibition_source_records']:
   cur=db.execute('DELETE FROM '+t+' WHERE exhibition_id=ANY(%s::uuid[])',(ids,));counts[t]=cur.rowcount;assert cur.rowcount==p['counts'][t]
  counts['exhibitions']=db.execute('DELETE FROM exhibitions WHERE id=ANY(%s::uuid[])',(ids,)).rowcount;assert counts['exhibitions']==len(ids)
  assert db.execute('SELECT count(*) n FROM exhibitions WHERE start_year>=1990 OR end_year>=1990 OR start_year<1600').fetchone()['n']==0
 c.save(OUT/'date-removal-delivered.json',dict(at=c.now(),counts=counts,planSHA256=c.sha((OUT/'date-removal-plan.json').read_bytes()),localDatabaseWrites=False));print(counts,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
