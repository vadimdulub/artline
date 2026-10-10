"""Production-wide museum counts in bounded institution batches, excluding unlinked works."""
import argparse,collections,csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-girodet-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s)
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('catalogue-expansion-20261008.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=s.m;RUN=s.RUN
COUNTSQL="SELECT current_institution_id::text institution_id,count(*) works,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible_works,count(primary_media_id) illustrated_works FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id"
PENDINGSQL="SELECT l.institution_id::text,count(DISTINCT l.artwork_id) pending_associations FROM artwork_location_assertions l JOIN artworks a ON a.id=l.artwork_id WHERE l.institution_id=ANY(%s::uuid[]) AND l.claim_type='holding' AND l.review_state='review' AND l.superseded_by IS NULL AND a.status<>'archived' AND a.current_institution_id IS DISTINCT FROM l.institution_id GROUP BY l.institution_id"
def main(label):
 dest=RUN/(label+'.json');assert not dest.exists()
 with p.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');rows=db.execute('SELECT i.id::text,i.slug,i.name,i.kind,i.status,i.website_url,i.wikidata_id,i.canonical_institution_id::text,p.name city,c.name country FROM institutions i LEFT JOIN places p ON p.id=i.place_id LEFT JOIN countries c ON c.code=p.country_code ORDER BY i.id').fetchall();counts={};pending={};plans=[]
  for start in range(0,len(rows),50):
   ids=[v['id'] for v in rows[start:start+50]]
   if not start:plans=db.execute('EXPLAIN (FORMAT JSON) '+COUNTSQL,(ids,)).fetchall()
   counts.update({v['institution_id']:v for v in db.execute(COUNTSQL,(ids,))});pending.update({v['institution_id']:v['pending_associations'] for v in db.execute(PENDINGSQL,(ids,))});print('Institution count batch',start+len(ids),'/',len(rows),flush=True)
  stats=db.execute('SELECT status,count(*) artworks FROM artworks GROUP BY status ORDER BY status').fetchall()
 for v in rows:
  v.update({k:counts.get(v['id'],{}).get(k,0) for k in ['works','eligible_works','illustrated_works']});v['pending_associations']=pending.get(v['id'],0)
  for target in [100,200]:v['gap_'+str(target)]=max(0,target-v['works']);v['eligible_gap_'+str(target)]=max(0,target-v['eligible_works'])
 museums=[v for v in rows if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id']]
 summary=dict(at=m.now(),production=True,read_only=True,institution_rows=len(rows),canonical_museums=len(museums),museums_below_100=sum(v['works']<100 for v in museums),museums_below_200=sum(v['works']<200 for v in museums),artworks=stats,pending_associations=sum(v['pending_associations'] for v in museums),policy='All active statuses count. SQL scopes each count batch to50institutionIDs before creation-date classification; excludes unlinked works. Representative current database query plan retained, not evidence of10millionrow performance.')
 m.save(dest,dict(summary=summary,institutions=rows,plans=plans,script_reference=s.ref(Path(__file__).resolve())))
 with (RUN/(label+'.csv')).open('x',newline='') as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(summary),flush=True)
if __name__=='__main__':
 q=argparse.ArgumentParser();q.add_argument('label');main(q.parse_args().label)
