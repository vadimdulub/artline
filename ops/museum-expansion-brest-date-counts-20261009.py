"""Bounded museum date-eligibility threshold audit: each indexed lookup stops after 200 active works with eligible creation dates."""
import argparse,importlib.util,json,time,csv
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-brest-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN
SQL="""SELECT i.id::text,i.slug,i.name,i.kind,i.status,i.website_url,p.name city,p.country_code,c.n date_eligible_count_to_200
FROM institutions i LEFT JOIN places p ON p.id=i.place_id
CROSS JOIN LATERAL (SELECT count(*) n FROM (SELECT a.id FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' LIMIT 200) bounded) c
WHERE i.id=ANY(%s::uuid[]) ORDER BY i.id"""
def main(command):
 out=[];pages=[];pilot=command=='pilot';dest=RUN/('production-date-threshold-pilot-001.json.gz' if pilot else 'production-date-threshold-audit-001.json.gz');assert not dest.exists()
 with a.i.prod.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');db.execute("SET LOCAL statement_timeout='20s'");db.execute("SET LOCAL application_name='artline-bounded-museum-thresholds'");start=m.now();register=db.execute("SELECT id::text FROM institutions WHERE kind='museum' AND status<>'archived' AND canonical_institution_id IS NULL ORDER BY id").fetchall();allids=[v['id'] for v in register];pageids=allids[:50] if pilot else allids
  if not pilot:
   previous=m.load(RUN/'production-date-threshold-pilot-001.json.gz');assert previous['page_size']==50 and previous['rows_per_institution_cap']==200 and len(previous['rows'])==50
   assert a.counts(db)=={a.IID:dict(linked=112,eligible=112)}
  plan=db.execute('EXPLAIN (FORMAT JSON) '+SQL,(pageids[:50],)).fetchone()
  for offset in range(0,len(pageids),50):
   ids=pageids[offset:offset+50];tick=time.monotonic();rows=db.execute(SQL,(ids,)).fetchall();elapsed=time.monotonic()-tick;assert [v['id'] for v in rows]==ids
   for v in rows:v.update(count_state='at_least_200' if v['date_eligible_count_to_200']==200 else 'exact',gap_to_100=max(100-v['date_eligible_count_to_200'],0),gap_to_200=max(200-v['date_eligible_count_to_200'],0))
   pages.append(dict(offset=offset,institutions=len(rows),elapsed_seconds=round(elapsed,3)));out+=rows

   if offset==0 or offset+50>=len(pageids):print(json.dumps(dict(page=len(pages),museums=len(out),seconds=round(elapsed,3))),flush=True)
  assert len({v['id'] for v in out})==len(out)==len(pageids)
 summary=dict(canonical_museums=len(allids),audited=len(out),below100=sum(v['date_eligible_count_to_200']<100 for v in out),below200=sum(v['date_eligible_count_to_200']<200 for v in out),at_least200=sum(v['date_eligible_count_to_200']==200 for v in out),gap_to_100=sum(v['gap_to_100'] for v in out),gap_to_200=sum(v['gap_to_200'] for v in out))
 result=dict(at=m.now(),snapshot_started_at=start,read_only=True,complete_canonical_museum_date_threshold_audit=not pilot,global_exact_counts_refreshed=False,date_eligible_thresholds_refreshed=True,page_size=50,rows_per_institution_cap=200,sql=SQL,explain=plan,pages=pages,rows=out,summary=summary,script_reference=a.reference(Path(__file__).resolve()),policy='Direct current_institution_id links, all active artwork statuses; canonical active museum records only. Each indexed lookup stops at200. Values below200 are exact;200 means at least200. Creation eligibility uses the authoritative PostgreSQL artline_creation_scope function; unknown,open-after and crossing1970 dates are not automatically eligible. Repeatable-read snapshot; no global unbounded artwork CTE or prior timed-out query retry. Production measurement is not a representative10-million-row load test.')
 m.save(dest,result)
 if not pilot:
  with (RUN/'production-date-threshold-audit-001.csv').open('x',newline='') as fp:w=csv.DictWriter(fp,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 print(json.dumps(summary),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['pilot','audit']);v=p.parse_args();main(v.command)
