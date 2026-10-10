"""Second bounded Béziers Fine Arts selection with fresh read-only baselines."""
import argparse,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-beziers-more-common-20261009.py');src=module('src','museum-expansion-beziers-source-20261009.py');prior=module('prior','museum-expansion-beziers-apply-20261009.py');m=s.m;RUN=s.RUN;src.RUN=RUN;prod=src.prod
def baseline():
 assert s.ref(s.CP)['sha256']=='171b0d8b0c8bb7e90437ea3898ab1ef3d0b3cf0cc4c30308e3f71a68614bdc64'
 for key,connect in [('initial',m.connect),('production-initial',prod.connect)]:
  dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
  with connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
   if key=='production-initial':p,d=prior.validate_plan();verification=prior.verify(db,p,d)
  m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(target=key,scope=len(ids),counts=counts)),flush=True)
 cp=m.load(s.CP);m.save(RUN/'baseline-verification-001.json',dict(at=m.now(),previous_checkpoint=s.ref(s.CP),previous_goal_turn='progress',verification=verification,prior_production_ids=p['prior_ids']+[v['artwork_id'] for v in p['records']],prior_plan=prior.reference(prior.PLAN),inherited_artifact_pins=len(cp['artifacts']),inherited_external_pins=len(cp['external_artifacts']),full_historical_verification=cp['initial_full_historical_verification_reference'],policy='Fresh previous production delivery and prior50Girodet records verified. Historical archive proof inherited by pinned checkpoint. Local catalogue read-only; all source holds persist.'))
def source():
 url='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/?Code_Museofile__exact=M0467&Domaine__contains=beaux-arts&page=3&page_size=100'
 raw,rc=src.capture('joconde-finearts-201-300-001',url);data=json.loads(raw);assert len(data['data'])<=100 and all(v['Code_Museofile']=='M0467' and 'beaux-arts' in v['Domaine'] for v in data['data']);old=m.load(m.RUN/'native/beziers-20261009/joconde-selected-001.json.gz');known={v['Reference'] for v in old['rows']}
 m.save(RUN/'joconde-selected-001.json.gz',dict(at=m.now(),receipts=[rc],rows=sorted(data['data'],key=lambda v:v['Reference']),finearts_total=data['meta']['total'],finearts_next=data['links']['next'],previous_discovery=s.ref(m.RUN/'native/beziers-20261009/joconde-selected-001.json.gz'),overlap_previous_ids=sorted(known&{v['Reference'] for v in data['data']}),policy='At most100 additional FineArts metadata records, positions201–300. Prior discovery and holds remain separate. No exhaustive retrieval or image download.'))
 print(json.dumps(dict(total=data['meta']['total'],selected=len(data['data']),overlap=len(known&{v['Reference'] for v in data['data']}))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['baseline','source']);v=p.parse_args();globals()[v.command]()
