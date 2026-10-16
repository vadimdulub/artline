#!/usr/bin/env python3
"""Bounded existing image gaps; external supervisor owns continuation."""
import csv, fcntl, gzip, importlib.util, json, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base44','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000044'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000044'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000044'
B='wikiart-000'
i.OP='continuous-primary-images-20261011-b000044';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return load(p)
 h.save(p,value);return value
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(url):
 assert urlsplit(url).hostname=='www.wikiart.org'
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=DATA/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds/www.wikiart.org.json').exists()
 i.provider_slot('www.wikiart.org');resp=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=resp.content
 bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=resp.headers.get('Retry-After'))
 h.save(rp,rc)
 if resp.status_code in [401,403,429]:save('access-holds/www.wikiart.org.json',rc)
 assert resp.status_code==200,resp.status_code
 return raw,rc
i.m.m.capture=capture
def preflight():
 save('production-target-reconciliation.json',target())
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(reg.open()));assert len(registry)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(reg),registry_sha256=h.sha(reg.read_bytes()),registry_rows=111,complete_registry=registry,precedence='Current production authorization supersedes legacy local mutation instructions. External supervisor unchanged.'))
 queue=load(E.parents[1]/'source-queue.json');save('source-queue-before.json',queue)
 holds=list(E.parent.glob('*/source-access-holds.json'))+list((ROOT/'docs/research/illustrated-300k-20261011/access-holds').glob('*.json'))
 save('source-access-holds.json',dict(at=h.now(),inherited_ledger_references=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in holds if p.parent!=E],queue_holds=[{k:r[k] for k in ['source_id','status','checkpoint','resume_cursor'] if k in r} for r in queue['sources'] if 'hold' in r['status'] or '403' in r['status']],policy='Inherited ledgers referenced without recursively copying prior ledgers; no held provider retried.'))
 stops=list((ROOT/'docs/research/illustrated-300k-20261011').glob('stop-*.json'))
 save('campaign-stop-preservation.json',dict(at=h.now(),separate_campaign=i.OP,files=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),data=load(p)) for p in stops]))
 prev=load(E.parent/'000043/batch-verification-receipt.json');ids=prev['production_ids']
 with connect() as db:
  states=h.snapshot(db,ids);rights=[dict(x) for x in db.execute('SELECT a.id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(states)==len(rights)==2
  for r in rights:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert ev['selection_sha256']==prev['selection_sha256']
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists()
  museums=[dict(x) for x in db.execute("SELECT id::text,slug,name FROM institutions WHERE name ILIKE '%tate%' AND status<>'archived' ORDER BY name LIMIT 25")]
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=43,live=states,rights=rights,previous_increment_counted=0,current_batch_existing_rights=own))
 save('institution-discovery.json',dict(at=h.now(),institutions=museums));print(json.dumps(museums))
def gaps():
 museums=load(E/'institution-discovery.json')['institutions'];ids=[m['id'] for m in museums if m['name'] in ['Tate','Tate Britain']];assert ids
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.normalized_title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.current_institution_id::text,a.unlinked_creator_label,a.work_type FROM artworks a WHERE a.current_institution_id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status<>'archived' ORDER BY a.id LIMIT 80",(ids,))]
  aids=[r['id'] for r in rows];states=h.snapshot(db,aids)
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(aids,))]
  cit=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(aids,))]
  artists=[dict(x) for x in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(aids,))]
 save('gap-reconciliation.json',dict(at=h.now(),rows=rows,before=states,identifiers=ext,citations=cit,artists=artists,institution_ids=ids))
 for r in rows:print(json.dumps(dict(r,artists=[x['display_name'] for x in artists if x['artwork_id']==r['id']],identifiers=[x for x in ext if x['entity_id']==r['id']],citation_urls=list({x['source_url'] for x in cit if x['entity_id']==r['id']}))))
def indexes():
 from bs4 import BeautifulSoup
 from urllib.parse import urljoin
 out={}
 for profile in ['walter-sickert','spencer-gore','james-tissot','william-orpen','john-everett-millais','john-linnell']:
  url='https://www.wikiart.org/en/'+profile+'/all-works/text-list'
  try:raw,rc=capture(url)
  except AssertionError:
   rc=load(E/'source-captures'/(h.sha(url.encode())+'.json'))
   if rc['status']==404:out[profile]=dict(receipt=rc,entries=[],outcome='No WikiArt profile at this candidate slug; not retried');continue
   raise
  if rc['status']==404:out[profile]=dict(receipt=rc,entries=[],outcome='No WikiArt profile at this candidate slug; not retried');continue
  sp=BeautifulSoup(raw,'html.parser');entries=[]
  for li in sp.select('li'):
   for a in li.select('a[href]'):
    link=urljoin(url,a['href'])
    if link.startswith('https://www.wikiart.org/en/'+profile+'/') and 'all-works' not in link:entries.append(dict(title=a.get_text(' ',strip=True),text=li.get_text(' ',strip=True),url=link))
  out[profile]=dict(receipt=rc,entries=entries);print(profile,len(entries),flush=True)
 save('wikiart-index-research.json',out)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
