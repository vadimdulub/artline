"""Brest bounded source selection with fresh read-only baselines."""
import argparse,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-brest-common-20261009.py');src=module('src','museum-expansion-beziers-source-20261009.py');prior=module('prior','museum-expansion-beziers-more-apply-20261009.py');m=s.m;RUN=s.RUN;src.RUN=RUN;prod=src.prod
def baseline():
 assert s.ref(s.CP)['sha256']=='5a352fa20c8c092a42b88e2b4d8cc97b3c057d38681cc987fc6f75f606ea8fcc'
 for key,connect in [('initial',m.connect),('production-initial',prod.connect)]:
  dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
  with connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
   if key=='production-initial':p,d=prior.validate_plan();verification=prior.verify(db,p,d)
  m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(target=key,scope=len(ids),counts=counts)),flush=True)
 cp=m.load(s.CP);m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_checkpoint=s.ref(s.CP),previous_goal_turn='progress',verification=verification,prior_production_ids=p['prior_ids']+[v['artwork_id'] for v in p['records']],prior_plan=prior.reference(prior.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],policy='Fresh previous production delivery and all138prior production records verified. Historical archive proof inherited by pinned checkpoint. Local catalogue read-only; all source holds persist.'))
def source():
 paths=[m.RUN/'native/beziers-more-20261009'/n for n in ['next-brest-source-leads-001.json.gz','next-brest-overall-leads-001.json.gz']];inputs=[m.load(p) for p in paths];rows={v['Reference']:v for x in inputs for v in x['rows']};assert len(rows)==103 and all(v['Code_Museofile']=='M0197' for v in rows.values());receipts=[x['receipt'] for x in inputs]
 m.save(RUN/'joconde-selected-001.json.gz',dict(at=m.now(),rows=sorted(rows.values(),key=lambda v:v['Reference']),receipts=receipts,context=inputs[0]['context'],dependencies=[s.ref(p) for p in paths],overall_total=124,unrequested_unique_records=21,overall_next=inputs[1]['next_page'],policy='103 previously captured distinct Brest metadata leads, 100 general plus14 FineArts minus11overlap; no new download. Prior native index HTTP500 retained without retry. Holding not current display.'))
 print(json.dumps(dict(selected=len(rows),remaining_unique=21)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['baseline','source']);v=p.parse_args();globals()[v.command]()
