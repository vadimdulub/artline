#!/usr/bin/env python3
"""Bounded Greek metadata research and established transactional delivery."""
import importlib.util,inspect,json,gzip,csv,subprocess,fcntl,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('helper',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
E=ROOT/'docs/research/continuous-production-20261011/batches/000015';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000015'
h.OP='continuous-greek-20261011-b000015';h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/h.OP
MUSEUM='National Gallery - Alexandros Soutsos Museum';PHASE='selected';FIELD='continuous_museum_batch_000015'
original_save=h.save
def stable_save(p,v):
 if p.exists():
  def strip(x):
   if isinstance(x,dict):return {k:strip(y) for k,y in x.items() if k!='at'}
   if isinstance(x,list):return [strip(y) for y in x]
   return x
  assert strip(h.load(p))==strip(h.safe(v)),str(p)
  return
 original_save(p,v)
h.save=stable_save

h.SCHEMES['athens']=['continuous-athens-object','museum-native-nationalgallery-gr','nationalgallery-gr-artwork','museum-native-athens-object']
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 lines=subprocess.check_output(['ps','ax','-o','command'],text=True).splitlines();assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x for x in lines)
 with h.connect() as db:
  state=db.execute('SELECT current_database() db,pg_is_in_recovery() recovery').fetchone();assert state['db']=='artline' and not state['recovery']
 return dict(at=h.now(),connection_name=actual,port=55519,helper='ops/india-300-delivery-20261011.py',database=state,local_connections=0)
src=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User-authorized continuous production enrichment, bounded Greek batch 000015; uncertain dates retain review treatment.')
exec(compile(src,__file__,'exec'),h.__dict__)
src=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300", "assert 1<=len(rows)<=50").replace('india_minimum_300_museum_coverage_20261011',FIELD)
src=src.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'", "  inventory=db.execute('SELECT id::text,accession_number FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall();assert {x['id'] for x in inventory}<={r['artwork_id'] for r in rows if r['before']},'Concurrent object insert; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(src,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 
 if not (E/'production-target-before-plan.json').exists():h.save(E/'production-target-before-plan.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rows=list(csv.DictReader(registry.open()));assert len(rows)==111
 h.save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,source=next(x for x in rows if x['source_id']=='national_gallery_athens'),policy='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',access='Five object pages and artist index HTTP 200',retained_holds=['docs/research/continuous-production-20261011/batches/000003/source-access-holds.json','docs/research/museum-expansion-20261006/athens-followup-holds.json','docs/research/russian-icon-images-20260921/commons-search-hold.json']))
 with h.connect() as db:
  inst=db.execute("SELECT id::text,name,slug,website_url FROM institutions WHERE website_url ILIKE '%%nationalgallery.gr%%' AND status<>'archived'").fetchall();print('INSTITUTIONS',inst)
  assert len(inst)==1;h.museums=lambda:{MUSEUM:(inst[0]['slug'],inst[0]['website_url'])}
  artists=db.execute("SELECT id::text,display_name FROM artists WHERE display_name ILIKE '%%koutouzis%%' OR display_name ILIKE '%%koutouz%%'").fetchall();h.save(E/'creator-global-review.json',dict(at=h.now(),original_label='Koutouzis Nikolaos (1741 - 1813)',candidates=artists));print('ARTISTS',artists)
  matches=[x for x in artists if 'nikola' in x['display_name'].lower()];assert len(matches)<=1
  records=[]
  for p in sorted(E.glob('*.body.gz')):
   if p.name in ['tzanes.body.gz','moskos-greek.body.gz','koutouzis.body.gz']:continue
   raw=gzip.decompress(p.read_bytes());rc=h.load(p.with_name(p.name.replace('.body.gz','.receipt.json')));assert rc['status']==200 and h.sha(raw)==rc['sha256'];rc['retrieved_at']=rc['at']
   soup=BeautifulSoup(raw,'html.parser');head=soup.select_one('h1.artwork');date=head.find('span');dated=date.get_text(strip=True) if date else '';date.extract() if date else None;title=head.get_text(strip=True).rstrip(',').strip();acc=soup.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip();image=soup.select_one('img[src*="/wp-content/uploads/"]')['src'];key=rc['url'].rstrip('/').split('/')[-1]
   evidence_file=p.with_suffix('').with_suffix('.html');evidence_file.write_bytes(raw)
   desc=soup.select_one('p.description').get_text(' ',strip=True);medium,dimensions=desc.split(', ',1);year=1803 if dated=='ca 1803' else 1800 if dated=='ca 1800' else None
   records.append(dict(provider='athens',source_id=key,museum=MUSEUM,title=title,date_display=dated,year_start=year,year_end=year,date_decision='eligible' if dated else 'date_review',source_type='drawing' if medium=='India ink' else 'painting',creator_label='Koutouzis Nikolaos (1741 - 1813)',verified_artist_id=matches[0]['id'] if matches else None,accession_number=acc,medium=medium,dimensions=dimensions,source_url=rc['url'],evidence=rc,evidence_file=str(evidence_file.relative_to(ROOT)),raw=dict(image_url=image,original_title=None),identity_review='Distinct official inventory, title, dimensions and composition. Ionian portraiture; not classified as Byzantine on nationality alone. No on-view assertion imported. Unknown creation not inferred from lifespan.'))
 h.save(E/PHASE/'source-records.json.gz',records);h.plan(PHASE)
 plan,pin=h.pinned(PHASE);print('PLAN',[(x['title'],bool(x['before']),x['add_holding']) for x in plan['records']])
def deliver():
 plan,pin=h.pinned(PHASE);assert plan['records'],'No eligible selections'
 with h.connect() as db:
  states=h.snapshot(db,[r['artwork_id'] for r in plan['records']]);notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,[r['artwork_id'] for r in plan['records']]))]
 if notes:
  assert len(notes)==len(plan['records']) and all(x['pin']==pin for x in notes);assert (h.BACKUP/PHASE/'locked-before.json.gz').exists();return
 assert states=={r['artwork_id']:r['before'] for r in plan['records'] if r['before']}
 rc=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert rc['status']=='SUCCESSFUL';h.save(E/'cloud-sql-backup.json',rc);h.save(h.BACKUP/'cloud-sql-backup.json',rc)
 h.save(E/'production-target-before-write.json',target());h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(stage=stage,deliver=deliver)[sys.argv[1]]()
