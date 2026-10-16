"""One bounded read-only reconciliation and source discovery; no supervisor."""
import importlib.util, pathlib, json, csv, gzip, fcntl, requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'ops'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('h109','india-300-delivery-20261011.py');base=mod('base109','continuous-image-batch-000002.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000109';R=pathlib.Path.home()/'Library/Application Support/Artline/continuous-research/batches/000109';R.mkdir(parents=True,exist_ok=True)
S=pathlib.Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000109';S.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def capture(key,url):
 p=E/(key+'.receipt.json')
 if p.exists():rc=h.load(p);return gzip.decompress(pathlib.Path(rc['body_path']).read_bytes()),rc
 res=requests.get(url,timeout=(15,40));raw=res.content;bp=S/(key+'.body.gz');bp.write_bytes(gzip.compress(raw,mtime=0));rc=save(key+'.receipt.json',dict(at=h.now(),url=url,final_url=res.url,status=res.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After')));return raw,rc

def reconcile():
 paths=[ROOT/'AGENTS.md',pathlib.Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000108/CHECKPOINT.json',E.parent/'000108/source-access-holds.json']
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
 save('required-input-verification.json',dict(at=h.now(),inputs=[dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in paths if p.exists()],registry=reg,local_catalogue_connections=0,supervisor_unchanged=True))
 save('source-queue-before.json',h.load(E.parents[1]/'source-queue.json'))
 reserve=mod('reserve109','continuous-reserve-warsaw-000052-research.py');reserve.E=E;reserve.reserve()
 save('production-target-reconciliation.json',base.target())
 pth=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pth);pin=h.sha(pth.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for r in p['rows']:
   a=live[r['artwork_id']]['artwork'];im=p['images'][r['artwork_id']];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived';assert all(a[k]==v for k,v in r['date'].items())
  prev=h.load(E.parent/'000108/prior-batch-live-reconciliation.json');prior=[]
  for row in prev['live']:
   cur=db.execute('SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256 FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=%s',(row['id'],)).fetchone();assert cur and all(cur[k]==row[k] for k in cur);prior.append(dict(cur))
  prior108=h.load(E.parent/'000108/independent-production-verification.json');assert h.snapshot(db,list(prior108['after']))==prior108['after']
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,physical_date_holds_preserved=['80082','80437','81054']))
 save('prior-batches-live-verification.json',dict(at=h.now(),batch107_verified_images=prior,batch108_unchanged=True,prior_batch107_receipt_sha256=h.sha((E.parent/'000108/prior-batch-live-reconciliation.json').read_bytes()),new_increments=0,write_replays=0))
 print('188 reserve already delivered; batch 107 and 108 live reconciled',flush=True)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);reconcile()
  for key,url in [('mds-home','https://museumdata.uk/'),('mds-search','https://museumdata.uk/object-search/'),('mds-terms','https://museumdata.uk/using-data/search-api-terms-and-fair-use-guidance/')]:
   raw,rc=capture(key,url);print(key,rc['status']);
   if key=='mds-search' and rc['status']==200:
    soup=BeautifulSoup(raw,'html.parser');print([(f.get('action'),[(x.get('name'),x.get('value')) for x in f.select('input')]) for f in soup.select('form')][:3])
