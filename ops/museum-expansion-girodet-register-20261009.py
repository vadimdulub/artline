"""Retain complete production institution directory and explicit count-audit gap."""
import csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-girodet-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s)
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('catalogue-expansion-20261008.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p)
with p.connect() as db,db.transaction():
 db.execute('SET TRANSACTION READ ONLY');rows=db.execute('SELECT i.id::text,i.slug,i.name,i.kind,i.status,i.canonical_institution_id::text,i.website_url,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id ORDER BY i.id').fetchall()
 historical={v['id']:v for v in s.m.load(s.m.RUN/'after-wave-100.json')['institutions']}
 for v in rows:
  local=historical.get(v['id'],{});v.update(historical_local_linked_works=local.get('works'),historical_local_eligible_works=local.get('eligible_works'),historical_local_count_at='2026-10-09T10:31:37Z',fresh_production_count_state='verified_in_Girodet_delivery' if v['id']==s.IID else 'not_refreshed_this_pass')
 s.m.save(s.RUN/'production-institution-register-001.json.gz',dict(at=s.m.now(),read_only=True,rows=rows,count_audit_gap='Whole-catalogue query and first50institutionbatch exceeded120secondstatementtimeout. No third blanket retry. Historical local counts are labelled separately and are not production counts. ExactGirodetscoped countsverified independently. Further performance diagnostics/currentglobalcounts remain required.'))
 with(s.RUN/'production-institution-register-001.csv').open('x',newline='') as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(dict(production_institutions=len(rows),canonical_museums=sum(v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] for v in rows))))
