#!/usr/bin/env python3
"""One bounded Walters icon continuation. External supervisor is untouched."""
import csv,fcntl,gzip,importlib.util,inspect,io,json,os,re,subprocess,sys
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
h=mod('metadata102','india-300-delivery-20261011.py');base=mod('base102','continuous-image-batch-000002.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000102';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000102'
OLD=E.parent/'000024';OP='continuous-walters-20261011-b000102';PHASE='painted-icons';FIELD='continuous_walters_object_evidence_b000102';MUSEUM='Walters Art Museum'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.SCHEMES={'walters':['walters-object','museum-native-walters-object','walters-art-object']}
h.museums=lambda:{MUSEUM:('wikimedia-museum-q210081','https://thewalters.org/')}
for path in [E,R,h.BACKUP]:path.mkdir(parents=True,exist_ok=True)
def save(name,value):h.save(E/name,value)
def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def static(name):
 raw=gzip.decompress((OLD/'source-captures'/(name+'.body.gz')).read_bytes());rc=h.load(OLD/'source-captures'/(name+'.receipt.json'))
 assert rc['status']==200 and h.sha(raw)==rc['sha256'];return raw,rc
def objects():return list(csv.DictReader(io.StringIO(static('art.csv')[0].decode('utf-8-sig'))))
def no_collision(db,rows):
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',([r['accession_number'] for r in rows],)).fetchall(),'Concurrent global inventory'
 urls=[r['source_url'] for r in rows]
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall(),'Concurrent global URL'
 assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE '%%walters%%' AND external_id=ANY(%s)",([r['source_id'] for r in rows],)).fetchall(),'Concurrent native identity'
h.no_collision=no_collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized continuous production; bounded batch 102, exact painted icon records and documented holdings, through 1970, anonymous and workshop labels preserved.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def probe():
 save('started.json',dict(at=h.now(),batch=102,external_supervisor_unchanged=True))
 save('production-target-reconciliation.json',target())
 qp=E.parent.parent/'source-queue.json';q=h.load(qp);save('source-queue-before.json',q)
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 required=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parent.parent/'CHECKPOINT.json',qp,E.parent/'000101/source-access-holds.json',OLD/'source-access-holds.json']
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in required],registry_rows=len(reg),source_registry_review_supplementary_only=True))
 save('source-register.json',dict(at=h.now(),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,route=[r for r in reg if r['source_id']=='walters_art_museum'],policy='docs/ARTLINE_IMAGE_USE.md',access='Official public static metadata reused; native image HTTP403 hold retained',remaining='Painted icon selection from unfinished saved queue; not whole collection coverage'))
 save('source-access-holds.json',h.load(OLD/'source-access-holds.json'))
 rr=requests.get('https://raw.githubusercontent.com/WaltersArtMuseum/api-thewalters-org/main/README.md',timeout=(15,40));save('official-readme-current.json',dict(at=h.now(),url=rr.url,status=rr.status_code,sha256=h.sha(rr.content),text=rr.text));rr.raise_for_status()
 assert 'CC0' in rr.text and 'static data' in rr.text
 sourcefiles=[]
 for name in ['README.md','art.csv','creators.csv','relationships.csv']:
  raw,rc=static(name);sourcefiles.append(dict(name=name,path=str(OLD/'source-captures'/(name+'.body.gz')),sha256=rc['sha256'],status=rc['status'],bytes=len(raw)))
 save('immutable-source-reuse-verification.json',dict(at=h.now(),files=sourcefiles,images_requested=0))
 cand=h.load(OLD/'walters-icon-candidates.json');remaining=[x for x in cand if int(x['ObjectID'])>16958]
 candidates=[x for x in remaining if re.search('tempera|oil on',x['Medium'],re.I)];assert len(candidates)<=50
 creators={x['id']:x for x in csv.DictReader(io.StringIO(static('creators.csv')[0].decode()))}
 relations=list(csv.DictReader(io.StringIO(static('relationships.csv')[0].decode())))
 out=[];ids=set()
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE slug=%s',('wikimedia-museum-q210081',)).fetchone()['v'];save('institution-before.json',inst)
  prior=h.load(E.parent/'000101/independent-production-verification.json');before=prior['after'];assert h.snapshot(db,list(before))==before
  for x in prior['rows']:
   actual=db.execute('SELECT e.adapter_version,e.evidence_json FROM media_rights_evidence e WHERE e.media_id=%s',(x['primary_media_id'],)).fetchone();assert actual['adapter_version']==x['adapter_version'] and actual['evidence_json']==x['evidence_json']
  save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=101,verified_prior_images=len(prior['rows']),snapshots_and_rights_equal=True,counted_as_current=0,ambiguous_prior_writes=False))
  for x in candidates:
   acc=list(db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=%s',(x['AccessionNumber'],)))
   native=list(db.execute("SELECT entity_id::text,scheme FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE '%%walters%%' AND external_id=%s",(x['ObjectID'],)))
   urls=list(db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s",(x['ResourceURL'],x['ResourceURL'])))
   titles=list(db.execute('SELECT a.id::text,a.title,a.date_display,a.accession_number,a.dimensions_text,a.unlinked_creator_label,a.current_institution_id::text,a.status,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists FROM artworks a WHERE a.normalized_title=%s',(h.norm(x['Title']),)))
   related=[y for y in relations if x['ObjectID'] in [y['art1'],y['art2']]]
   record=dict(object=x,creators=[creators[k] for k in x['Creators'].split('|') if k in creators],relationships=related,art_receipt=static('art.csv')[1],creators_receipt=static('creators.csv')[1])
   save('selected-source-records/'+x['ObjectID']+'.json',record)
   out.append(dict(source_id=x['ObjectID'],accession=x['AccessionNumber'],title=x['Title'],matches=acc,native=native,urls=urls,title_candidates=titles,relationships=related,source_related=x['RelatedObjects'],creators=[c['name'] for c in record['creators']]))
   ids.update(y['id'] for y in acc+titles);ids.update(y['entity_id'] for y in native+urls)
  preserved=h.snapshot(db,sorted(ids));save('preserved-existing-before.json.gz',dict(at=h.now(),artworks=preserved));h.save(h.BACKUP/'preserved-existing-before.json.gz',dict(artworks=preserved))
 save('candidate-reconciliation.json',dict(at=h.now(),remaining_saved_objects=len(remaining),pictorial_candidates=len(out),records=out,non_painted_deferred=[dict(source_id=x['ObjectID'],title=x['Title'],medium=x['Medium'],reason='Not a confirmed painted icon in this batch; metal/relief/ceramic/unit review retained') for x in remaining if x not in candidates]))
 print(json.dumps([dict(id=x['source_id'],title=x['title'],existing=len(x['matches'])+len(x['native'])+len(x['urls']),titles=len(x['title_candidates']),relations=len(x['relationships'])) for x in out]))
def plan():
 decisions=h.load(E/'editorial-decisions.json');checks=h.load(E/'candidate-reconciliation.json')['records'];rows=[]
 for c in checks:
  if decisions[c['source_id']]['decision']!='select':continue
  assert not c['matches'] and not c['native'] and not c['urls']
  ep=E/'selected-source-records'/(c['source_id']+'.json');src=h.load(ep);x=src['object'];label='; '.join(y['name'] for y in src['creators']) or None
  rows.append(dict(provider='walters',source_id=x['ObjectID'],source_url=x['ResourceURL'],museum=MUSEUM,title=x['Title'],creator_label=label,creator_link_hold=True,culture=x['Culture'] or None,date_display=x['DateText'],year_start=int(x['DateBeginYear']),year_end=int(x['DateEndYear']),date_decision='eligible',accession_number=x['AccessionNumber'],source_type='painting',medium=x['Medium'],dimensions=x['Dimensions'] or None,credit=x['CreditLine'],raw=x,evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=src['art_receipt']['at'],sha256=h.sha(ep.read_bytes()),url=x['ResourceURL']),editorial_review=decisions[c['source_id']]))
 assert 1<=len(rows)<=50
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==len(rows) and not p['held'] and not p['new_institutions'] and not p['artists'] and all(not r['before'] and not r['artist_id'] for r in p['records'])
 save('helper-adaptation.json',dict(helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Batch-specific OP/RUN/BACKUP/identifiers/citation field','Bounded 1–50 new paintings rather than India-specific 300 minimum','Fresh target assertion; shared transactional advisory lock; collision guard','Schema and scoped preimage recovery instead of new Cloud SQL backup'],source_plan_sha256=pin))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 with h.connect() as db:
  states=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
 if states:
  assert len(states)==len(notes)==len(ids) and all(x['pin']==pin for x in notes);assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={};print('Own checksum-bound transaction reconciled; no repeated writes');return
 assert h.load(E/'prewrite-verification.json')['passed']
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-metadata-write.json',target(True));h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
