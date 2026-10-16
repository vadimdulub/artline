#!/usr/bin/env python3
"""One bounded image worker. External supervisor and completed campaigns untouched."""
import ast, csv, fcntl, gzip, importlib.util, json, os, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base98','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000098'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000098'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000098'
B='wikiart-000';MID='3db0938a-e500-5263-9890-2997fa1d0d44'
i.OP='continuous-primary-images-20261011-b000098';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)

# Retain the established transactional image-only attachment workflow, replacing
# its retired Cloud SQL backup prerequisite with current verified local recovery.
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text()
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply')
code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    initial=m.load(RUN/'gap-input.json.gz')['before'][aid]\n    assert before[aid]['creators']==initial['creators'] and before[aid]['holdings']==initial['holdings'],'Creator or holding changed since selection'")
exec(compile(code,__file__,'exec'),i.__dict__)

def capture(url):
 host=urlsplit(url).hostname
 assert host in ['www.wikiart.org']
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=DATA/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];assert rc['status']==200,('Cached source HTTP',rc['status'],url);return raw,rc
 assert not (E/'access-holds'/(host+'.json')).exists(),'Source host is access-held'
 i.provider_slot(host);res=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=res.content
 bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=res.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After'))
 h.save(rp,rc)
 if res.status_code in [401,403,429]:save('access-holds/'+host+'.json',dict(rc,retry_allowed=False))
 assert res.status_code==200,('Source HTTP',res.status_code,url)
 return raw,rc
i.m.m.capture=capture

def preflight():
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rows=list(csv.DictReader(registry.open()));assert len(rows)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),complete_registry=rows,precedence='Current production authorization; local catalogue read-only; external supervisor untouched.'))
 q=save('source-queue-before.json',load(E.parents[1]/'source-queue.json'));source=next(r for r in q['sources'] if r['source_id']=='auckland_art_gallery')
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 ledgers=[p for p in E.parent.glob('*/access-holds/*.json') if E not in p.parents]+list((base.OLD/'access-holds').glob('*.json'))
 relevant=[dict(path=str(p.relative_to(ROOT)),data=load(p)) for p in ledgers if any(s in p.name for s in ['wikiart','wikipaintings','auckland'])]
 assert not any('wikiart' in x['path'] or 'wikipaintings' in x['path'] for x in relevant),'WikiArt access hold requires reconciliation'
 save('source-access-holds.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in ledgers],relevant=relevant,source_queue=source,policy='No requests to held Auckland museum surfaces. Approved WikiArt alternate provider; do not generalize permissions.'))
 save('production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists(),'Reconcile unknown interrupted writes'
  previous=load(E.parent/'000097/warsaw/independent-production-verification.json')
  ids=load(E.parent/'000097/batch-verification-receipt.json')['production_ids'];live=h.snapshot(db,ids)
  old=load(E.parent/'000097/CHECKPOINT.json');cit=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  assert all(any(c['entity_id']==aid and old['metadata_plan_sha256'] in c['evidence_note'] for c in cit) for aid in ids)
  assert all(a['artwork']['primary_media_id'] for a in live.values())
  pending=source['resume_cursor']['pending_artwork_ids'];states=h.snapshot(db,pending)
  gaps=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,a.work_type,(SELECT string_agg(ar.display_name,' / ') FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id",(pending,))]
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(pending,))]
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(pending,))]
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=97,live=live,citations=cit,previous_increments_counted=0,current_campaign_rows=own))
 save('gap-input.json.gz',dict(at=h.now(),limit=100,rows=gaps,before=states,citations=citations,identifiers=identifiers,pending_ids=pending))
 print('Staged',len(gaps),'existing Auckland gaps')
def research():
 profiles={r['creator'] or r['unlinked_creator_label']:h.norm(r['creator'] or r['unlinked_creator_label']).replace(' ','-') for r in load(E/'gap-input.json.gz')['rows']}
 profiles.update({'Sir David Murray':'david-murray','Charles F Goldie':'charles-frederick-goldie','Anna Lois White':'lois-white'})
 gaps=load(E/'gap-input.json.gz');outcomes=[]
 for row in gaps['rows']:
  creator=row['creator'] or row['unlinked_creator_label']
  if creator not in profiles:continue
  url='https://www.wikiart.org/en/'+profiles[creator]+'/all-works/text-list'
  try:
   raw,rc=capture(url);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
   outcomes.append(dict(artwork_id=row['id'],title=row['title'],creator=creator,url=url,status=200,text=text,outcome='index_captured_requires_exact_match_review'))
  except AssertionError as exc:
   rc=load(E/'source-captures'/(h.sha(url.encode())+'.json'))
   outcomes.append(dict(artwork_id=row['id'],title=row['title'],creator=creator,url=url,status=rc['status'],outcome='candidate_profile_unavailable',receipt=rc))
   if rc['status'] in [401,403,429]:break
 save('discovery-outcomes.json',dict(at=h.now(),rows=outcomes,source_scope='25 untouched Auckland gap candidates; 404 does not prove artist absent elsewhere',official_museum_requests=0,image_downloads=0))
 print(json.dumps([{k:v for k,v in r.items() if k!='text'} for r in outcomes]))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
