"""Read-only planner diagnostics; no blanket count execution or database modifications."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-beziers-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
def main():
 prior=m.load(m.RUN/'native/girodet-20261009/production-institution-register-001.json.gz');ids=[v['id'] for v in prior['rows'] if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id']][:50]
 sql="SELECT current_institution_id,count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id"
 with s.prod.connect() as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');plans={key:db.execute('EXPLAIN (FORMAT JSON) '+sql,(iids,)).fetchone() for key,iids in [('beziers',s.s.IIDS),('fifty_museums',ids)]};stats=db.execute("SELECT relname,n_live_tup,n_dead_tup,last_analyze,last_autoanalyze FROM pg_stat_user_tables WHERE relname='artworks'").fetchall();indexes=db.execute("SELECT indexname,indexdef FROM pg_indexes WHERE tablename='artworks' ORDER BY indexname").fetchall()
 m.save(RUN/'production-count-planner-diagnostics-001.json.gz',dict(at=m.now(),plans=plans,stats=stats,indexes=indexes,explain_analyze=False,executed_count_queries=False,policy='Planning evidence only; not representative10million-row load testing. No third blanket count retry.'))
 print(json.dumps(dict(plans=plans,stats=stats),default=str),flush=True)
if __name__=='__main__':main()
