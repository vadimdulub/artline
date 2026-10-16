#!/usr/bin/env python3
"""Bounded reserve supplement; preserves historical plans and source UUIDs."""
import importlib.util,json,gzip,csv,subprocess,fcntl
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('delivery',ROOT/'ops/french-printmaking-delivery-20261011.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;MAIN=d.RUN;OLD_BACKUP=d.BACKUP
RUN=ROOT/'docs/research/continuous-production-20261011/batches/000001'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/continuous-production-20261011/000001'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000001'
for p in [RUN,BACKUP,RUNTIME]:p.mkdir(parents=True,exist_ok=True)
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 commands=subprocess.check_output(['ps','ax','-o','command'],text=True).splitlines()
 assert any(line.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in line and actual in line for line in commands)
 return dict(at=m.now(),connection_name=actual,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def stage():
 original,pin=d.final_plan();top=m.load(MAIN/'scope-topup/delivery-plan.json.gz')
 reserve=set(original['eligible_reserve'])-{r['artwork_id'] for r in top['rows']};assert len(reserve)==188
 rows=[r for r in d.identity_rows() if r['artwork_id'] in reserve];assert len(rows)==188
 holds=dict(original['held']);approved={};visual=[]
 for p in (MAIN/'visual-decisions').glob('*.json'):
  decision=m.load(p);sheet=m.load(MAIN/'visual-sheets'/p.name)
  assert decision['sheet_sha256']==m.sha(Path(sheet['sheet']).read_bytes())
  for im in sheet['images']:
   if im['artwork_id'] in decision['approved']:approved[im['artwork_id']]=dict(decision=str(p.relative_to(ROOT)),decision_sha256=m.sha(p.read_bytes()),sheet=sheet['sheet'],sheet_sha256=decision['sheet_sha256'],image_sha256=im['sha256'])
 for p in (MAIN/'cross-sheet-review').glob('*.json'):holds.update(m.load(p).get('held',{}))
 selected=[];skipped=[];images={}
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  collection={r['artwork_id'] for r in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s',(d.COLLECTION,))}
  states=m.dbutil.snapshot(db,[r['artwork_id'] for r in rows])
  for r in sorted(rows,key=lambda r:(r['artist_id'],r['date']['creation_year_start'],int(r['native_id']))):
   aid=r['artwork_id'];reason=None
   if aid in states:reason='Already in production'
   elif aid in holds:reason=holds[aid]
   elif not m.dates(r['date']['date_display'],1970):reason='Creation date held'
   native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)",(['yale-object','museum-expansion-yale-object','yale-lux-object'],[r['native_id'],r['receipt']['url'].rsplit('/',1)[1]])).fetchall()
   acc=db.execute("SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s AND status<>'archived'",(d.IID,r['accession_number'])).fetchall()
   if native or acc:reason='Existing native identity/accession'
   if reason:skipped.append(dict(artwork_id=aid,native_id=r['native_id'],reason=reason));continue
   if len(selected)>=25:continue
   im=m.load(MAIN/'prepared-images'/(aid+'.json'));assert im['outcome']=='prepared' and aid in approved and approved[aid]['image_sha256']==im['sha256']
   raw=Path(im['local_path']).read_bytes();assert m.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
   with Image.open(im['local_path']) as img:img.load();assert img.size==(im['width'],im['height'])
   path=ROOT/r['source_record_reference'];assert m.sha(path.read_bytes())==r['source_record_sha256'];obj=m.load(path)
   for key,rkey in [('raw','receipt'),('manifest','manifest_receipt')]:
    rc=obj[rkey];body=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and m.sha(body)==rc['sha256'] and json.loads(body)==obj[key]
   assert obj['manifest']['id']==r['manifest_receipt']['url'] and obj['native_id']==r['native_id']
   assert any(x['id']==r['source_url'] for x in obj['manifest']['homepage'])
   assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['date']['creation_year_start'],r['date']['creation_year_end'],r['date']['date_precision'])).fetchone()['scope']=='eligible'
   a=db.execute('SELECT id::text,display_name,birth_year,death_year,status FROM artists WHERE id=%s',(r['artist_id'],)).fetchone();assert a and a['status']!='archived'
   r['artist_identity']=dict(r['artist_identity'],action='existing',existing=dict(a))
   selected.append(r);images[aid]=im;visual.append(dict(artwork_id=aid,**approved[aid]))
 assert selected
 m.save(RUN/'reserve-reconciliation.json',dict(at=m.now(),reserve_inspected=len(rows),selected=len(selected),skipped=skipped,remaining_unselected=len(rows)-len(selected)-len(skipped),production_target=target()))
 m.save(RUN/'prior-visual-evidence.json',dict(policy='Reuse immutable actual prior visual reviews, checksum bound to each selected derivative. New batch contact sheet also viewed separately.',records=visual))
 data=dict(at=m.now(),rows=selected,images=images,held={},image_gaps={},authorization_sha256=original['authorization_sha256'],baseline_sha256=original['baseline_sha256'],selection=original['selection'],parent_plan_sha256=pin,position_offset=len(collection),collection_expected_ids=sorted(collection|set(images)))
 m.save(RUN/'authorization.json',(MAIN/'authorization.json').read_bytes());m.save(RUN/'delivery-plan.json.gz',data);newpin=m.sha((RUN/'delivery-plan.json.gz').read_bytes());m.save(RUN/'delivery-plan-pin.json',dict(sha256=newpin))
 m.save(BACKUP/'cloud-backup.json',m.load(OLD_BACKUP/'cloud-backup.json'))
 m.save(BACKUP/'delivery-preimages.json.gz',dict(at=m.now(),plan_sha256=newpin,artworks={},artists={r['artist_id']:r['artist_identity']['existing'] for r in selected}))
 canvas=Image.new('RGB',(1250,1750),'white');draw=ImageDraw.Draw(canvas)
 for n,r in enumerate(selected):
  im=Image.open(images[r['artwork_id']]['local_path']);im.thumbnail((240,290));x=(n%5)*250;y=(n//5)*350;canvas.paste(im,(x+(250-im.width)//2,y));draw.text((x+5,y+295),r['native_id']+' '+r['creator_label'][:25],fill='black');draw.text((x+5,y+315),r['title'][:32],fill='black')
 canvas.save(RUNTIME/'selected-contact-sheet.jpg')
 print(json.dumps(dict(selected=len(selected),sheet=str(RUNTIME/'selected-contact-sheet.jpg'))))
def run(command):
 if command=='stage':return stage()
 d.RUN=RUN;d.BACKUP=BACKUP
 if command=='apply':
  m.save(RUN/'production-target-before-write.json',target());assert (RUN/'batch-visual-review.json').exists()
 if command=='verify':
  original_final=d.final_plan
  data,pin=original_final()
  with m.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
   actual={r['artwork_id'] for r in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s',(d.COLLECTION,))}
   assert set(data['collection_expected_ids'])<=actual
   reserve=set(m.load(MAIN/'delivery-plan.json.gz')['eligible_reserve'])
   extra=actual-set(data['collection_expected_ids']);assert extra<=reserve
   citations=[dict(r) for r in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(list(data['images']),))]
   assert len(citations)==len(data['rows'])
   attributable=[r['entity_id'] for r in citations if r['plan_sha256']==pin]
  m.save(RUN/'concurrent-ingestion-reconciliation.json',dict(at=m.now(),own_plan_sha256=pin,selected_source_citations=citations,attributable_artwork_ids=attributable,additional_collection_ids=sorted(extra),expected_collection_count=len(data['collection_expected_ids']),actual_collection_count=len(actual),policy='Other campaign committed reserve objects during preparation; shared lock and native identity checks avoided duplicate inserts. Do not count other plan writes. Historical plan unchanged.'))
  d.final_plan=lambda:(dict(data,collection_expected_ids=sorted(actual)),pin)
 getattr(d,command)()
if __name__=='__main__':
 import sys
 with (RUNTIME/'worker.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run(sys.argv[1])
