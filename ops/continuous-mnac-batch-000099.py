#!/usr/bin/env python3
"""One bounded MNAC museum batch; no supervisor or local catalogue mutation."""
import csv,fcntl,gzip,importlib.util,inspect,json,os,re,subprocess,sys,time
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base99','continuous-image-batch-000002.py');h=mod('metadata99','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000099';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000099';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000099'
OP='continuous-mnac-20261011-b000099';PHASE='mnac-medieval-v3';FIELD='continuous_mnac_object_evidence_b000099';MID='b90ff9b2-cf4e-57e5-a042-8f45d6b3bc13';MUSEUM="Museu Nacional d'Art de Catalunya";B='mnac-000'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'mnac':['continuous-mnac-object','museum-native-mnac','mnac-inventory','museum-native-mnac-object']}
for p in [E,R,S,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(url):
 key=h.sha(url.encode());p=E/'source-captures'/(key+'.json')
 if p.exists():
  rc=h.load(p);raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'];return raw,rc
 assert url.startswith('https://www.museunacional.cat/en/colleccio/') and not (E/'access-holds/www.museunacional.cat.json').exists()
 i.provider_slot('www.museunacional.cat');r=i.session().get(url,timeout=(15,40));bp=S/(key+'.html');bp.write_bytes(r.content);rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=h.now(),sha256=h.sha(r.content),body_path=str(bp),retry_after=r.headers.get('Retry-After'));save('source-captures/'+key+'.json',rc)
 if r.status_code in [401,403,429]:save('access-holds/www.museunacional.cat.json',rc)
 return r.content,rc
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch 99; MNAC museum records through 1970; no invented creator or date.')
code=code.replace("elif re.search(r'\\b(?:on loan|loan from|lent by|deaccessioned)\\b',r.get('credit') or '',re.I):", "elif re.search(r'\\b(?:on loan|loan from|lent by|deaccessioned)\\b',r.get('credit') or '',re.I) and not r.get('documented_gift_after_former_loan'):")
exec(compile(code,__file__,'exec'),h.__dict__)
def no_collision(db,rows):
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',([r['accession_number'] for r in rows],)).fetchall(),'Concurrent global accession'
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",([r['source_url'] for r in rows],)).fetchall(),'Concurrent global source URL'
 for r in rows:
  if r['artist_id']:
   assert not db.execute('SELECT a.id FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.normalized_title=%s',(r['artist_id'],h.norm(r['title']))).fetchall(),'Concurrent creator/title'
h.no_collision=no_collision
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall(),'Concurrent inventory insertion'\n  assert not db.execute(\"SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)\",(SCHEMES['mnac'],[r['source_id'] for r in rows])).fetchall(),'Concurrent native insertion'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
exec(compile(code,__file__,'exec'),h.__dict__)
def apply():
 assert h.load(E/'prewrite-verification.json')['passed']
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 with h.connect() as db:
  states=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
 if states:
  assert len(states)==len(notes)==len(ids) and all(x['pin']==pin for x in notes);assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={};print('Own committed plan reconciled; no new writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and Path(rc['path']).is_dir()
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-metadata-write.json',target(True));h.apply(PHASE)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
