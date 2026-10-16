#!/usr/bin/env python3
"""Bounded batch 76. No supervisor, local catalogue, or historical-plan mutation."""
import csv,fcntl,gzip,importlib.util,json,os,re,subprocess,sys,hashlib
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'ops'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base76','continuous-image-batch-000002.py');h=mod('h76','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000076';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000076';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000076'
OP='continuous-colbase-20261011-b000076';PHASE='colbase-objects';FIELD='continuous_colbase_object_evidence_b000076'
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if p.exists():return h.load(p)
 h.save(p,v);return v
def ref(p):
 p=Path(p);return dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size)
def target(write=False):
 v=base.target(write);actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(v,connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(key,url):
 p=E/(key+'-capture.json')
 if p.exists():
  rc=h.load(p);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 host=__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(url).hostname
 assert not (E/'access-holds'/str(host+'.json')).exists()
 try:
  resp=requests.get(url,timeout=(15,35),headers={'User-Agent':'Artline bounded catalogue research/1.0'});raw=resp.content;status=resp.status_code;final=resp.url;retry=resp.headers.get('Retry-After')
 except requests.RequestException as ex:raw=b'';status=None;final=url;retry=None
 bp=S/(key+'.gz');bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=final,status=status,retry_after=retry,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(bp),attempts=1)
 h.save(p,rc)
 if status in [401,403,429]:h.save(E/'access-holds'/str(host+'.json'),rc)
 print(key,status,len(raw),flush=True);return raw,rc
def init():
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 files=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000075/CHECKPOINT.json',E.parent/'000075/source-access-holds.json',E.parent/'000074/source-hold-ledger-reconciliation.json',ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
 save('required-input-verification.json',dict(at=h.now(),files=[ref(p) for p in files],complete_original_registry=reg,registry_count=111,precedence='Bounded worker: one batch, production only, original registry authoritative; newer source policies prevail; no supervisor changes.'))
 save('source-queue-before.json',h.load(E.parents[1]/'source-queue.json'));save('batch-start.json',dict(at=h.now(),batch=76));save('production-target-initial.json',target())
 old=E.parent/'000075';rc=h.load(old/'batch-verification-receipt.json');ids=rc['production_ids']
 with h.connect() as db:
  state=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name='continuous_greek_object_evidence_b000075' AND entity_id=ANY(%s::uuid[])",(ids,))]
  rights=[dict(x) for x in db.execute('SELECT a.id::text,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(state)==len(cit)==len(rights)==5 and all(x['pin']==rc['metadata_plan_sha256'] for x in cit)
  for x in rights:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert ev['selection_sha256']==rc['image_selection_sha256']
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_receipt=ref(old/'batch-verification-receipt.json'),states=state,citations=cit,rights=rights,prior_campaign_increments=0))
def reserve():
 r=mod('reserve76','continuous-reserve-warsaw-000052-research.py');r.E=E;r.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with h.connect() as db:
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for row in p['rows']:
   a=live[row['artwork_id']]['artwork'];im=p['images'][row['artwork_id']];assert a['accession_number']==row['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived';assert all(a[k]==v for k,v in row['date'].items())
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,plan_sha256=pin,source_citations=cit,live_rows=live,new_programme_increments=0,physical_date_holds_preserved=['80082','80437','81054'],next_action='Undercovered ColBase Japan; no unchanged Yale source requests.'))
 print('188 reserve already delivered; excluded from increments.',flush=True)
def discover():
 from bs4 import BeautifulSoup
 raw,rc=capture('colbase-sample','https://colbase.nich.go.jp/collection_items/tnm/A-11189?locale=en')
 for n,s in enumerate(BeautifulSoup(raw,'html.parser').select('script[src]')):
  url='https://colbase.nich.go.jp'+s['src'];js,r=capture('colbase-js-'+str(n),url);txt=js.decode()
  out=[]
  for match in re.finditer(r'collection_items|baseURL|api\.|/api|\.json|terms',txt):out.append(txt[max(0,match.start()-120):match.start()+160])
  save('colbase-js-'+str(n)+'-routes.json',out)
  print(json.dumps(out[:25],ensure_ascii=False)[:7500])
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
