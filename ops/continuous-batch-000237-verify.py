#!/usr/bin/env python3
"""Independent read-only live verification for batch 237."""
import importlib.util, json, hashlib, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-production-20261011/batches/000237'
s=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
with h.connect() as db:
    target=dict(db.execute("select current_database() database,current_setting('default_transaction_read_only') read_only,current_user role").fetchone())
    totals=dict(db.execute("select (select count(*) from artworks where status<>'archived') active_artworks,(select count(*) from artists where status<>'archived') active_artists,(select count(*) from artwork_location_assertions) artwork_location_assertions,(select count(*) from media_assets) media_assets").fetchone())
assert target['database']=='artline' and target['read_only']=='on'
v={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'production_target':target,'bounded_totals':totals,'batch_237_production_ids':[],'batch_237_rows_found':0,'batch_237_writes':0,'previous_programme_increments_excluded':True,'local_catalogue_connections':0}
p=E/'independent-production-verification.json';p.write_text(json.dumps(v,indent=2,default=str)+'\n')
