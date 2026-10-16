#!/usr/bin/env python3
"""Chicago Byzantine metadata fallback; immutable plans and shared ingestion lock."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys,time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('fallback25','continuous-image-batch-000025.py');h=mod('metadata25','india-300-delivery-20261011.py');E=base.E;R=base.RUNTIME
OP='continuous-chicago-20261011-b000025';h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
MID='9e75033c-8e6b-464b-974b-d94fcc91c6a3';MUSEUM='Art Institute of Chicago';PHASE='chicago-byzantine-reviewed';FIELD='continuous_chicago_object_evidence_20261011_b000025'
h.SCHEMES={'chicago':['aic-artwork','chicago-artwork','museum-native-chicago-object','aic-object','artic-object']}
h.museums=lambda:{MUSEUM:('art-institute-of-chicago','https://www.artic.edu')}
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized continuous source-backed production enrichment; bounded batch 25 Chicago Byzantine metadata fallback; source labels retained and images access held.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=sum(not r['before'] for r in rows)<=25, 'Bounded new physical objects only'").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'", "  inventory=db.execute('SELECT id::text,accession_number FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall();assert not inventory,'Concurrent accession insert; replan'\n  native=db.execute(\"SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND (scheme ~* 'aic|chicago|artic') AND external_id=ANY(%s)\",([r['source_id'] for r in rows],)).fetchall();assert not native,'Concurrent native object insert; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
save=base.save;FIELDS='id,title,artist_display,date_display,date_start,date_end,main_reference_number,medium_display,dimensions,credit_line,publication_history,exhibition_history,provenance_text,artwork_type_title,department_title,artist_id,artist_ids,place_of_origin,api_link,is_public_domain,image_id,is_deaccessioned'
def capture(url,name,params=None):
 p=E/'chicago-source-captures'/(name+'.receipt.json');bp=p.with_name(name+'.body.gz');p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():rc=h.load(p);body=gzip.decompress(bp.read_bytes());assert h.sha(body)==rc['sha256'];return json.loads(body),rc
 # Official API asks for a single request stream, maximum one per second.
 base.i.provider_slot('api.artic.edu');time.sleep(1.05)
 r=requests.get(url,params=params,timeout=(15,45));body=r.content;bp.write_bytes(gzip.compress(body,mtime=0));rc=dict(at=h.now(),retrieved_at=h.now(),url=r.url,status=r.status_code,sha256=h.sha(body),body_path=str(bp.relative_to(ROOT)),retry_after=r.headers.get('Retry-After'));h.save(p,rc)
 if r.status_code in [401,403,429]:save(E/'access-holds/api.artic.edu.json',rc)
 r.raise_for_status();return r.json(),rc
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save(E/'chicago-production-target-before-plan.json',base.target())
 d,rc=capture('https://api.artic.edu/api/v1/artworks/search','byzantine-search',dict(q='Byzantine',limit=50,fields=FIELDS))
 selected=[];checks=[]
 with h.connect() as db:
  for x in d['data']:
   oid=str(x['id']);url='https://www.artic.edu/artworks/'+oid;reason=None
   native=[dict(t) for t in db.execute("SELECT entity_id::text,scheme FROM external_identifiers WHERE entity_type='artwork' AND scheme ~* 'aic|chicago|artic' AND external_id=%s",(oid,))]
   acc=[dict(t) for t in db.execute("SELECT id::text,title,current_institution_id::text FROM artworks WHERE accession_number=%s AND status<>'archived'",(x['main_reference_number'],))]
   urls=[dict(t) for t in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(url,url))]
   if native or acc or urls:reason='Existing global native, accession or URL identity; excluded'
   elif not (x.get('artist_display') or '').startswith('Byzantine'):reason='Search lead outside explicit Byzantine source culture; not inferred from subject'
   elif x.get('is_deaccessioned') or re.search(r'deaccession',x.get('provenance_text') or '',re.I):reason='Deaccessioned object held'
   elif not x['date_start'] or not x['date_end'] or not x['date_start']<=x['date_end']<=1970:reason='Unknown or ineligible creation interval'
   elif re.search(r'probably|possibly|\?|late|early',x['date_display'],re.I):reason='Qualified date interval requires separate editorial review'
   elif re.search(r'loan|lent|promised',x['credit_line'] or '',re.I) or not re.search(r'gift|purchase|collection|fund',x['credit_line'] or '',re.I):reason='Holding evidence review'
   elif len(selected)>=12:reason='Bounded unselected'
   if reason:checks.append(dict(source_id=oid,accession=x['main_reference_number'],reason=reason,native=native,accessions=acc,urls=urls));continue
   obj,orc=capture('https://api.artic.edu/api/v1/artworks/'+oid,'object-'+oid,dict(fields=FIELDS));o=obj['data'];assert o['id']==x['id'] and all(o[k]==x[k] for k in ['title','main_reference_number','date_start','date_end','artist_display'])
   # Preserve cultural/mint attribution without fabricating a named maker.
   ep=E/'chicago-selected-source-records'/(oid+'.json');h.save(ep,o)
   kind='metalwork' if o['artwork_type_title']=='Coin' else 'unknown'
   if o['artwork_type_title']=='Textile':kind='textile'
   if o['artwork_type_title']=='Painting':kind='painting'
   selected.append(dict(provider='chicago',source_id=oid,source_url=url,museum=MUSEUM,title=o['title'],creator_label=o['artist_display'],creator_link_hold=True,culture='Byzantine',date_display=o['date_display'],year_start=o['date_start'],year_end=o['date_end'],date_decision='eligible',accession_number=o['main_reference_number'],source_type=kind,medium=o['medium_display'],dimensions=o['dimensions'],credit=o['credit_line'],raw=o,evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=orc['retrieved_at'],sha256=h.sha(ep.read_bytes()),url=url),original_api_receipt=orc,source_api_id=oid,image_hold='Native IIIF HTTP 403 hold from batch 000008; no image requests',identity_review='Exact native accession and official object metadata, globally reconciled. Distinct coins and fragments retain museum inventory identity; cultural attribution is not a painter; exhibition_history is retained only as source context, never current display.'))
   checks.append(dict(source_id=oid,accession=o['main_reference_number'],reason='selected',native=native,accessions=acc,urls=urls))
 save(E/'chicago-global-identity-reconciliation.json',dict(at=h.now(),query='Byzantine',page=1,search_sha256=rc['sha256'],checked=len(checks),selected=len(selected),records=checks,resume=dict(inspected_ids=[x['source_id'] for x in checks],unselected_ids=[x['source_id'] for x in checks if x['reason']=='Bounded unselected'],next_page=2,limit=50)))
 assert selected,'No new eligible Chicago objects'
 h.save(E/PHASE/'source-records.json.gz',selected);h.plan(PHASE)
 plan,pin=h.pinned(PHASE);assert all(not r['before'] and r['artist_id'] is None for r in plan['records'])
 reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
 save(E/'chicago-source-register.json',dict(at=h.now(),source=next(x for x in reg if x['source_id']=='artic'),actual_access='Official native metadata API HTTP 200; image endpoint retains 403 hold',metadata_policy='https://api.artic.edu/docs/',request_policy='Single stream, at most one request per second; bounded 50-object search, selected native details only',directory_coverage='No directory additions or nationwide coverage claim',plan_sha256=pin))
 save(E/'metadata-helper-adaptation.json',dict(at=h.now(),helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Separate OP/RUN/BACKUP and citation field','Bounded 1–25 instead of India-specific 300 minimum','Chicago native aliases and exact canonical institution','Under shared transaction lock recheck native IDs and accessions'],plan_sha256=pin))
 print('Selected',len(plan['records']),[(r['source_id'],r['title']) for r in plan['records']],flush=True)
def review():
 if (E/PHASE/'plan-pin.json').exists():return
 parent,parent_pin=h.pinned('chicago-byzantine');held=[r for r in parent['records'] if r['source_id']=='35355'];assert len(held)==1
 reason='Source display says 5th century but structured bounds are 301–500; retained for date reconciliation, not silently rewritten or delivered.'
 rows=[r for r in parent['records'] if r['source_id']!='35355'];assert len(rows)==11
 p=dict(parent,at=h.now(),phase=PHASE,records=rows,held=parent['held']+[dict(record=held[0],reason=reason)],parent_plan_sha256=parent_pin)
 h.save(E/PHASE/'plan.json.gz',p);pin=h.sha((E/PHASE/'plan.json.gz').read_bytes());h.save(E/PHASE/'plan-pin.json',dict(sha256=pin));h.save(h.BACKUP/PHASE/'plan-preimages.json.gz',p)
 save(E/'final-editorial-review.json',dict(at=h.now(),parent_plan_sha256=parent_pin,final_plan_sha256=pin,selected=11,held=[dict(source_id='35355',reason=reason)],immutable_parent_preserved=True))
 print('Final reviewed plan',len(rows),pin,flush=True)
def apply():
 plan,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in plan['records']]
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids))]
  if present:
   assert len(present)==len(notes)==len(ids) and all(x['plan_sha256']==pin for x in notes) and (h.BACKUP/PHASE/'locked-before.json.gz').exists();print('Recovered own committed plan; independent verification required');return
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-sql-backup.json',backup)
 save(E/'production-target-before-metadata-write.json',base.target(True));h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(stage=stage,review=review,apply=apply)[sys.argv[1]]()
