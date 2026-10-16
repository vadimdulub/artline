#!/usr/bin/env python3
"""One bounded batch: reconcile exhausted reserves and research London metadata."""
import csv, fcntl, gzip, importlib.util, inspect, json, os, re, subprocess, sys
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base85','continuous-image-batch-000002.py');h=base.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000085'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000085'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000085'
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def ref(p):return dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size)
def target(write=False):
 name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert name=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=name,helper='ops/india-300-delivery-20261011.py',local_database_connections=0)
def capture(key,url,payload=None):
 p=E/(key+'.receipt.json')
 if p.exists():
  rc=h.load(p);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 resp=requests.get(url,json=payload,headers={'User-Agent':'Artline bounded collection research/1.0'},timeout=(15,40))
 raw=resp.content;assert len(raw)<6000000
 fp=S/(key+'.body.gz');assert not fp.exists();fp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=resp.url,method='GET',payload=payload,status=resp.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(fp),retry_after=resp.headers.get('Retry-After'))
 save(key+'.receipt.json',rc);return raw,rc
def init():
 queue=E.parents[1]/'source-queue.json';save('source-queue-before.json',h.load(queue))
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',queue,E.parent/'000084/CHECKPOINT.json',E.parent/'000084/source-access-holds.json',ROOT/'ops/india-300-delivery-20261011.py']
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
 save('required-input-verification.json',dict(at=h.now(),inputs=[ref(p) for p in paths],original_registry=reg,registry_rows=111,precedence='One bounded worker; external supervisor remains unmodified. Production authorized, real local catalogue read-only. Source-specific newer approvals prevail.'))
 save('production-target-reconciliation.json',target())
 old=E.parent/'000084';rc=h.load(old/'batch-verification-receipt.json');pr=h.load(old/'independent-production-verification.json')
 with h.connect() as db:
  live=h.snapshot(db,rc['production_ids'])
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND evidence_note::jsonb->>'plan_sha256'=%s",(rc['production_ids'],rc['metadata_plan_sha256']))]
  assert len(live)==len(notes)==4
  rights=[dict(x) for x in db.execute('SELECT e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(rc['production_ids'],))]
  assert len(rights)==3
  for x in rights:
   v=x['evidence_json'];v=json.loads(v) if isinstance(v,str) else v;assert v['selection_sha256']==rc['image_selection_sha256']
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch_verified=True,batch=84,live=live,citations=notes,rights=rights,prior_increments=0))
 reserve=mod('reserve85','continuous-reserve-warsaw-000052-research.py');reserve.E=E;reserve.PREVIOUS=E.parent/'000082';reserve.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with h.connect() as db:
  live=h.snapshot(db,ids)
  cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for row in p['rows']:
   a=live[row['artwork_id']]['artwork'];im=p['images'][row['artwork_id']]
   assert a['accession_number']==row['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived' and all(a[k]==v for k,v in row['date'].items())
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,selected=0,physical_date_holds_preserved=['80082','80437','81054'],next_action='Reserve exhausted; switch to National Gallery London metadata API without historical plan mutation.'))
 hold=E.parent/'000084/source-access-holds.json'
 save('source-access-holds.json',dict(at=h.now(),inherited_ledger=ref(hold),source_queue_holds=ref(E/'source-queue-before.json'),held_provider_requests=0,national_gallery_london='No previous provider-access hold found in source queue or searched hold ledgers; images remain CC BY-NC-ND held.'))
 print('Reserve live: 188 prior deliveries, zero unimported. Prior batch reconciled.',flush=True)
def discover():
 for key,suffix in [('london-policy','licences'),('london-api-doc','collection-data/elasticsearch-api')]:
  raw,rc=capture(key,'https://www.nationalgallery.org.uk/documentation/ngacuk/'+suffix);print(key,rc['status'],len(raw),flush=True)
  if rc['status']!=200:return
 payload={'size':25,'query':{'bool':{'filter':{'term':{'@datatype.base':'object'}}}}}
 raw,rc=capture('london-objects-page1','https://data.ng.ac.uk/es/public/_search',payload)
 print('API',rc['status'],len(raw),flush=True)
 if rc['status']==200:
  obj=json.loads(raw);save('london-objects-page1.json',obj);print('Objects',len(obj['hits']['hits']))
MID='2c909ffb-2614-4273-b76b-a0daa2a74833'
MUSEUM='National Gallery';OP='continuous-london-20261012-b000085';PHASE='london-metadata';FIELD='continuous_london_object_evidence_b000085'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'london':['european-popular-ng-object']}
h.museums=lambda:{MUSEUM:('national-gallery-london','https://www.nationalgallery.org.uk')}
URLS={'NG1036':'https://www.nationalgallery.org.uk/paintings/follower-of-jan-van-scorel-a-man-with-pansies-and-a-skull','NG1301':'https://www.nationalgallery.org.uk/paintings/italian-florentine-portrait-of-savonarola'}
def collision(db,rows):
 for r in rows:
  ids=[r['source_id'],r['accession_number']]+r['raw']['alternate_native_ids'];urls=[r['source_url'],'https://data.ng.ac.uk/'+r['source_id']+'.html']
  assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))",(ids,urls)).fetchall()
  assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall()
  assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s) OR normalized_title=%s',([r['accession_number'],r['accession_number'].replace('NG','NG ')],h.norm(r['title']))).fetchall()
h.collision=collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized one bounded continuous production batch 85: exact National Gallery London inventory objects, qualified/anonymous makers retained as labels; review status only.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=25 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def reconcile():
 objects=[x['_source'] for x in h.load(E/'london-objects-page1.json')['hits']['hits']];checks=[]
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  scope=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=%s',(MID,))]
  save('london-institution-before.json.gz',scope)
  for o in objects:
   pid=o['@admin']['uid'];acc=next(x['value'] for x in o['identifier'] if x['type']=='object number');titles=[x['value'] for x in o['title']];native=[x['value'] for x in o['identifier'] if x['type'] in ['PID','PID (NG alternative)']]+[o['@admin']['id']]
   ac=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',([acc,acc.replace('NG','NG ')],))]
   ex=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s)",(native+[acc],))]
   tt=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s) OR title=ANY(%s)',([h.norm(t) for t in titles],titles))]
   scoped=[dict(id=x['id'],title=x['title'],accession=x['accession_number']) for x in scope if h.norm(x['accession_number'])==h.norm(acc) or h.norm(x['title']) in [h.norm(t) for t in titles]]
   checks.append(dict(pid=pid,accession=acc,title=titles[0],creator=[x['value'] for x in o['creation'][0]['attribution'] if x['type']=='attribution'],accession_matches=ac,native_matches=ex,global_title_matches=tt,institution_matches=scoped,outcome='held_existing_or_ambiguous' if ac or ex or tt or scoped else 'candidate'))
 save('london-initial-reconciliation.json',dict(at=h.now(),records=checks,scope_count=len(scope)))
 for x in checks:print(x['accession'],x['title'],x['outcome'],'matches',len(x['accession_matches']),len(x['native_matches']),len(x['global_title_matches']),flush=True)
def stage():
 if (E/PHASE/'plan-pin.json').exists():print('Pinned plan retained');return
 from bs4 import BeautifulSoup
 save('production-target-before-plan.json',target())
 rc=h.load(E/'london-objects-page1.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 objects=[x['_source'] for x in json.loads(raw)['hits']['hits']];rows=[]
 for o in objects:
  acc=next(x['value'] for x in o['identifier'] if x['type']=='object number')
  if acc not in URLS:continue
  html,pr=capture('london-'+acc,URLS[acc]);assert pr['status']==200
  text=BeautifulSoup(html,'html.parser').get_text(' ',strip=True);c=o['creation'][0];date=c['date'][0];title=o['title'][0]['value'];label=next(x['value'] for x in c['attribution'] if x['type']=='attribution');dimensions=o['measurements'][0]['display'];medium=next(x['value'] for x in o['material'] if x.get('type')=='detailed')
  assert acc in text and title in text and label in text and dimensions in text and date['value'].lower() in text.lower()
  assert o['@datatype']['virtual'] is False and o['legal']['status']=='Accessioned object' and 'Main Collection' in text and not o.get('parent')
  fp=S/(acc+'.html');fp.write_bytes(html)
  factual=dict(pid=o['@admin']['uid'],native_tms_id=o['@admin']['id'],alternate_native_ids=[x['value'] for x in o['identifier'] if x['type']=='PID (NG alternative)'],titles=o['title'],source_creation=c,source_measurements=o['measurements'],material=o['material'],legal=o['legal'],source_provenance=o['provenance'],image_rights='CC BY-NC-ND 4.0',native_images_requested=False)
  if acc=='NG1301':factual['physical_unit']='One double-sided panel: portrait recto and execution verso. Both sides are one inventory object; no separate reverse record.'
  rows.append(dict(provider='london',source_id=o['@admin']['uid'],source_url=URLS[acc],museum=MUSEUM,title=title,creator_label=label,creator_link_hold=True,date_display=date['value'],year_start=int(date['from']),year_end=int(date['to']),date_decision='eligible',accession_number=acc,source_type='painting',medium=medium,dimensions=dimensions,credit=o['legal']['credit'],raw=factual,evidence_file=str(fp),evidence=dict(pr,sha256=h.sha(html)),api_receipt=rc,metadata_licence='CC0 structured data; narrative provenance CC BY 4.0, National Gallery London, source URLs retained.',identity_review='Exact official inventory, PID, title, date, material, dimensions and provenance; qualified attribution retained without a named artist link.',date_basis='Museum supplied approximate bounds retained with circa precision. No exact creation year inferred.'))
 assert len(rows)==2
 with h.connect() as db:
  collision(db,rows)
  related=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,dimensions_text,current_institution_id::text,unlinked_creator_label FROM artworks WHERE unlinked_creator_label ILIKE '%%Scorel%%' ORDER BY id LIMIT 201")]
  assert len(related)<=200
  save('scorel-unlinked-related-works.json',dict(at=h.now(),rows=related))
  print('Unlinked Scorel rows',len(related),flush=True)
  for x in related:print(x,flush=True)
 save('selected-source-records-pending-final-review.json',dict(at=h.now(),records=rows))
 print('Two exact metadata candidates captured; review related labels before freezing.',flush=True)
def freeze():
 rows=h.load(E/'selected-source-records-pending-final-review.json')['records']
 assert h.load(E/'final-identity-review.json')['accepted_inventory_ids']==['NG1036','NG1301']
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==2 and not p['artists'] and not p['new_institutions'] and not p['held']
 print('Frozen',pin)
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  present=h.snapshot(db,ids)
  if present:
   notes=db.execute("SELECT evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
   assert len(present)==len(notes)==len(ids) and all(x['pin']==pin for x in notes)
   assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={}
   print('Own plan recovered; zero replay writes.');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'prewrite-verification.json')['passed']
 save('production-target-before-metadata-write.json',checked);h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
