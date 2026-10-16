#!/usr/bin/env python3
"""Bounded Walters supplement; adapts established atomic ingestion without altering it."""
import importlib.util,inspect,json,gzip,csv,io,re,fcntl,sys,requests
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
E=ROOT/'docs/research/continuous-production-20261011/batches/000022';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000022';R.mkdir(parents=True,exist_ok=True)
h.OP='continuous-walters-20261011-b000022';h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/h.OP;h.SCHEMES={'walters':['walters-object','museum-native-walters-object','walters-art-object']}
PHASE='walters-icons';FIELD='continuous_walters_object_evidence_20261011_b000022'
# Minimum 300 is specific to India. This bounded authorized supplement is 1–25.
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1 <= sum(not r['before'] for r in rows) <= 25, 'Bounded supplement requires new physical objects'").replace('india_minimum_300_museum_coverage_20261011',FIELD)
exec(compile(code,'established-india-helper-bounded-walters-adaptation','exec'),h.__dict__)
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized source-backed production inserts through established workflow; batch 22 bounded Walters icon supplement; new objects only.')
exec(compile(code,'established-india-planner-walters-adaptation','exec'),h.__dict__)
h.museums=lambda:{'Walters Art Museum':('wikimedia-museum-q210081','https://thewalters.org/')}
def save(name,v):
 if (E/name).exists():return h.load(E/name)
 h.save(E/name,v)
def capture(url,name):
 p=E/'source-captures'/(name+'.receipt.json')
 if p.exists():return h.load(p)
 rr=requests.get(url,timeout=(15,45));body=rr.content;bp=p.with_name(name+'.body.gz');bp.write_bytes(gzip.compress(body,mtime=0));rc=dict(at=h.now(),retrieved_at=h.now(),url=url,status=rr.status_code,sha256=h.sha(body),body_path=str(bp.relative_to(ROOT)),retry_after=rr.headers.get('Retry-After'));h.save(p,rc)
 if rr.status_code in [401,403,429]:raise RuntimeError('Provider access hold '+url+' '+str(rr.status_code))
 rr.raise_for_status();return rc

def stage():
 save('production-target-reconciliation.json',base.target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 save('source-register.json',dict(at=h.now(),registry_sha256=h.sha(registry.read_bytes()),registry_records=len(reg),route=[r for r in reg if 'walters' in r['source_id']],policy='docs/ARTLINE_IMAGE_USE.md',metadata_only_selection_first=True))
 save('policy-route-reconciliation.json',dict(at=h.now(),direct_policy_route_hold=h.load(E/'source-captures/rights-policy.receipt.json'),official_static_route='https://github.com/WaltersArtMuseum/api-thewalters-org',policy_source='Official repository README states data and images CC0; web browser separately read official policy including artist-rights and loan exceptions. Main-site direct 403 not retried.',policy_url='https://thewalters.org/about/policies/rights-reproductions/'))
 creators={x['id']:x for x in csv.DictReader(io.StringIO(gzip.decompress((E/'source-captures/creators.csv.body.gz').read_bytes()).decode()))}
 candidates=h.load(E/'walters-icon-candidates.json');eligible=[];checks=[]
 with h.connect() as db:
  for x in sorted(candidates,key=lambda x:int(x['ObjectID']))[:50]:
   # Global accession reconciliation, not merely the preferred institution.
   matches=[dict(y) for y in db.execute("SELECT id::text,title,current_institution_id::text FROM artworks WHERE accession_number=%s AND status<>'archived'",(x['AccessionNumber'],))]
   native=[dict(y) for y in db.execute("SELECT entity_id::text,scheme FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE '%%walters%%' AND external_id=%s",(x['ObjectID'],))]
   urls=[dict(y) for y in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(x['ResourceURL'],x['ResourceURL']))]
   reason=None
   if matches or native or urls:reason='existing_identity_or_accession_global_skip'
   elif x['RelatedObjects']:reason='related_object_component_identity_review'
   elif re.search(r'loan|lent|deaccession',x['CreditLine']+' '+x['Provenance'],re.I):reason='ownership_loan_review'
   elif not re.search(r'Walters Art Museum',x['CreditLine']):reason='holding_evidence_review'
   if len(eligible)>=25:reason=reason or 'bounded_unselected'
   checks.append(dict(source_id=x['ObjectID'],accession=x['AccessionNumber'],reason=reason or 'selected',matches=matches,native=native,urls=urls))
   if reason:continue
   record={'object':x,'creators':[creators[k] for k in x['Creators'].split('|') if k in creators],'art_receipt':h.load(E/'source-captures/art.csv.receipt.json'),'creators_receipt':h.load(E/'source-captures/creators.csv.receipt.json')}
   ep=E/'selected-source-records'/(x['ObjectID']+'.json');h.save(ep,record)
   labels='; '.join(y['name'] for y in record['creators'])
   # Geography/culture labels are not invented painters. All creators retained verbatim.
   eligible.append(dict(provider='walters',source_id=x['ObjectID'],source_url=x['ResourceURL'],museum='Walters Art Museum',title=x['Title'],creator_label=labels or None,creator_link_hold=True,culture=x['Culture'] or None,date_display=x['DateText'],year_start=int(x['DateBeginYear']),year_end=int(x['DateEndYear']),date_decision='eligible',accession_number=x['AccessionNumber'],source_type='sculpture' if 'relief' in x['ObjectName'] else 'painting' if 'Painting' in x['Classification'] else 'unknown',medium=x['Medium'] or None,dimensions=x['Dimensions'] or None,credit=x['CreditLine'],raw=x,evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=h.now(),sha256=h.sha(ep.read_bytes()),url=x['ResourceURL'])))
 save('walters-global-identity-reconciliation.json',dict(at=h.now(),checked=len(checks),selected=len(eligible),records=checks,resume_after_object_id=checks[-1]['source_id'],remaining_candidate_count=len(candidates)-len(checks)))
 assert eligible
 h.save(E/PHASE/'source-records.json.gz',eligible);h.plan(PHASE)
 save('helper-adaptation.json',dict(helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Separate OP/RUN/BACKUP, Walters identifier aliases and institution','India minimum replaced by bounded 1–25 minimum','Separate programme citation field and current user authorization'],source_plan_sha256=h.pinned(PHASE)[1]))

def apply():
 save('production-target-before-write.json',base.target(True))
 # Verify existing approved successful Cloud SQL recovery backup freshly.
 import subprocess
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791718979252','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-sql-backup.json',backup)
 base.target(True);h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
