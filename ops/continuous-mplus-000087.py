#!/usr/bin/env python3
"""One resumable M+ metadata batch; the external supervisor owns continuation."""
import csv,fcntl,gzip,importlib.util,inspect,io,json,os,re,subprocess,sys
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base87','continuous-image-batch-000002.py');h=base.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000087'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000087'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000087'
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
def capture(key,url):
 p=E/(key+'.receipt.json')
 if p.exists():
  rc=h.load(p);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 res=requests.get(url,headers={'User-Agent':'Artline bounded collection research/1.0'},timeout=(15,50));raw=res.content
 assert len(raw)<30000000
 fp=S/(key+'.body.gz');assert not fp.exists();fp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=res.url,method='GET',status=res.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(fp),retry_after=res.headers.get('Retry-After'))
 save(key+'.receipt.json',rc);return raw,rc
def init():
 queue=E.parents[1]/'source-queue.json';save('source-queue-before.json',h.load(queue))
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',queue,E.parent/'000086/CHECKPOINT.json',E.parent/'000086/source-access-holds.json',ROOT/'ops/india-300-delivery-20261011.py']
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
 save('required-input-verification.json',dict(at=h.now(),inputs=[ref(p) for p in paths],complete_registry=reg,registry_rows=111,precedence='One bounded worker; external supervisor unchanged. Production authorized, real local catalogue read-only. Newer source-specific approvals prevail.'))
 save('production-target-reconciliation.json',target())
 old=E.parent/'000086';rc=h.load(old/'batch-verification-receipt.json');pr=h.load(old/'independent-production-verification.json')
 with h.connect() as db:
  live=h.snapshot(db,rc['production_ids']);assert live==pr['after']
  rights=[dict(x) for x in db.execute('SELECT a.id::text,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(rc['production_ids'],))];assert len(rights)==1
  for x in rights:
   v=x['evidence_json'];v=json.loads(v) if isinstance(v,str) else v;assert v['selection_sha256']==rc['selection_sha256'] and v['batch_visual_review_sha256']==rc['visual_review_sha256']
  institutions=[x['v'] for x in db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE website_url ILIKE '%%mplus.org.hk%%' OR name ILIKE 'M+%%'")]
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=86,live=live,rights=rights,prior_increments=0,previous_batch_verified=True))
 save('institution-reconciliation.json',dict(at=h.now(),rows=institutions))
 save('source-access-holds.json',dict(at=h.now(),inherited_ledger=ref(paths[-2]),source_queue_holds=ref(E/'source-queue-before.json'),mplus_historical_access=dict(status=200,method='HEAD',at='2026-09-10T08:43:47.835Z',meaning='Reachability only'),mplus_current_route='Public institution-published GitHub metadata; API documentation now requires developer token, no GraphQL requests or authentication bypass.',held_provider_requests=0))
 print('Prior batch reconciled. M+ institutions:',[(x['id'],x['name'],x['slug']) for x in institutions],flush=True)
def discover():
 raw,rc=capture('github-repository','https://api.github.com/repos/mplusmuseum/collection-data');assert rc['status']==200
 branch=json.loads(raw)['default_branch']
 raw,rc=capture('github-commit','https://api.github.com/repos/mplusmuseum/collection-data/commits/'+branch);assert rc['status']==200
 commit=json.loads(raw)['sha'];save('dataset-pin.json',dict(commit=commit,repository='mplusmuseum/collection-data',branch=branch))
 for key,path in [('dataset-readme','README.md'),('dataset-objects','objects.csv'),('dataset-creators','constituents.csv')]:
  raw,rc=capture(key,'https://raw.githubusercontent.com/mplusmuseum/collection-data/'+commit+'/'+path);assert rc['status']==200
  if path.endswith('.csv'):
   rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));save(key+'.json.gz',dict(rows=rows,receipt=rc));print(key,len(rows),'fields',list(rows[0]),'sample',rows[0],flush=True)
  else:print(raw.decode()[:5000],flush=True)
 raw,rc=capture('api-documentation','https://api.mplus.org.hk/en/documentation');print('API docs',rc['status'],flush=True)

def reconcile():
 rows=h.load(E/'dataset-objects.json.gz')['rows'];cc={r['id']:r for r in h.load(E/'dataset-creators.json.gz')['rows']}
 eligible=sorted([r for r in rows if json.loads(r['category'] or '[]')==['Painting'] and r['publicAccess']=='true' and r['beginDate'].isdigit() and r['endDate'].isdigit() and 0<int(r['beginDate'])<=int(r['endDate'])<=1970],key=lambda r:int(r['id']))
 candidates=eligible[:50];creatorids=sorted({str(c) for r in candidates for c in json.loads(r['constituents'])});checks=[];creators={}
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  artists=[dict(x) for x in db.execute("SELECT id::text,display_name,birth_year,death_year,status FROM artists")]
  aliases=[dict(x) for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases')]
  names={a['id']:[a['display_name']] for a in artists}
  for a in aliases:names[a['artist_id']].append(a['alias'])
  for cid in creatorids:
   c=cc[cid];nn=[h.norm(c['name']),h.norm(c['nameTC'])];nt=[sorted(n.split()) for n in nn if n]
   matched=[a for a in artists if any(h.norm(n) in nn or sorted(h.norm(n).split()) in nt for n in names[a['id']])]
   creators[cid]=dict(source=c,candidates=matched)
  save('creator-global-reconciliation.json',dict(at=h.now(),creators=creators,global_artists_inspected=len(artists),global_aliases_inspected=len(aliases)))
  for r in candidates:
   cs=[creators[str(c)] for c in json.loads(r['constituents'])];aids=list({a['id'] for c in cs for a in c['candidates']})
   titles=[r['title'],r['titleTC']];normalized=[h.norm(x) for x in titles if x]
   accession=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,dimensions_text,current_institution_id::text FROM artworks WHERE accession_number=%s',(r['objectNumber'],))]
   urls=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (scheme ILIKE '%%mplus%%' OR canonical_url ILIKE '%%mplus%%') AND (external_id=%s OR canonical_url ILIKE %s)",(r['id'],'%'+r['objectNumber'].replace('.','')+'%'))]
   # Single-creator bounded foreign-key and date lookup catches translated/generic titles.
   works=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) AND (creation_year_start IS NULL OR creation_year_end IS NULL OR (creation_year_start<=%s AND creation_year_end>=%s)) ORDER BY id LIMIT 1001',(aids,int(r['endDate']),int(r['beginDate'])))] if aids else []
   assert len(works)<=1000,'Creator date scope needs keyset continuation'
   titlematches=[]
   if h.norm(r['title']) not in ['untitled','work','dream','stairs','hong kong']:
    titlematches=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE normalized_title=ANY(%s) OR title=ANY(%s) ORDER BY id LIMIT 101',(normalized,titles))]
    assert len(titlematches)<=100
   labelnames=[v for c in cs for v in [c['source']['name'],c['source']['nameTC']]]
   labels=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE unlinked_creator_label=ANY(%s) ORDER BY id LIMIT 501',(labelnames,))]
   assert len(labels)<=500
   checks.append(dict(source=r,creator_native_ids=[str(c) for c in json.loads(r['constituents'])],global_accession_matches=accession,native_matches=urls,global_title_matches=titlematches,creator_date_works=works,unlinked_creator_works=labels))
 save('object-global-reconciliation.json.gz',dict(at=h.now(),rows=checks,eligible_painting_records=len(eligible),candidate_count=len(candidates),remaining_native_ids=[r['id'] for r in eligible[50:]],last_candidate_native_id=candidates[-1]['id'],metadata_only=True))
 print('Candidate rows',len(checks),'eligible total',len(eligible),flush=True)
 for cid,c in creators.items():print(cid,c['source']['name'],c['source']['displayBio'],'matches',[(a['id'],a['display_name'],a['birth_year'],a['death_year']) for a in c['candidates']],flush=True)
 for x in checks:print(x['source']['id'],x['source']['title'],'acc',len(x['global_accession_matches']),'native',len(x['native_matches']),'title',len(x['global_title_matches']),'creator/date',len(x['creator_date_works']),'unlinked',len(x['unlinked_creator_works']),flush=True)

def objects():
 checks=h.load(E/'object-global-reconciliation.json.gz')['rows'];pin=h.load(E/'dataset-pin.json')['commit'];out=[]
 for x in checks:
  r=x['source'];rid=int(r['id']);path=f'objects_JSON/{rid//1000*1000}/{rid:05d}.json'
  raw,rc=capture('object-'+r['id'],'https://raw.githubusercontent.com/mplusmuseum/collection-data/'+pin+'/'+path)
  if rc['status']!=200:
   save('object-access-hold.json',rc);raise RuntimeError('Object metadata route stopped; inspect receipt, no retry')
  o=json.loads(raw);assert str(o['id'])==r['id'] and o['objectNumber']==r['objectNumber']
  fields=dict(title=(r['title'],o['title']['en']),date=(r['displayDate'],o['displayDate']['en']),first=(int(r['beginDate']),o['beginDate']),last=(int(r['endDate']),o['endDate']),medium=(r['medium'],o['medium']['en']),credit=(r['creditLine'],o['creditLine']['en']))
  equal=all(v[0]==v[1] for v in fields.values())
  fp=S/f'object-{rid}.json'
  if not fp.exists():fp.write_bytes(raw)
  out.append(dict(native_id=r['id'],receipt=rc,evidence_file=str(fp),object=o,csv_consistent=equal,comparisons=fields,source_url='https://github.com/mplusmuseum/collection-data/blob/'+pin+'/'+path))
  print(rid,'metadata',rc['status'],'CSV consistency',equal,flush=True)
 save('individual-object-captures.json.gz',dict(at=h.now(),rows=out,images_requested=0))

MUSEUM='M+'
OP='continuous-mplus-20261012-b000087';PHASE='mplus-metadata';FIELD='continuous_mplus_object_evidence_b000087'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'mplus':['museum-native-mplus']}
h.museums=lambda:{MUSEUM:('mplus-hong-kong','https://www.mplus.org.hk/')}
def collision(db,rows):
 ids=[r['source_id'] for r in rows];urls=[r['source_url'] for r in rows];acc=[r['accession_number'] for r in rows]
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',(acc,)).fetchall(),'New exact inventory collision'
 assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='museum-native-mplus' AND external_id=ANY(%s)) OR canonical_url=ANY(%s))",(ids,urls)).fetchall()
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall()
 # Selected works had no global exact title collisions. Recheck within shared lock.
 assert not db.execute('SELECT id FROM artworks WHERE normalized_title=ANY(%s) OR title=ANY(%s)',([h.norm(r['title']) for r in rows],[r['title'] for r in rows])).fetchall(),'Concurrent title evidence requires reconciliation'
 assert not db.execute("SELECT id FROM institutions WHERE slug='mplus-hong-kong' OR name='M+' OR website_url ILIKE '%%mplus.org.hk%%'").fetchall(),'Institution changed; replan'
h.collision=collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized one bounded continuous production batch 87: eligible museum-native M+ physical paintings, metadata and documented holdings; unresolved creator labels retained; review status only.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def select():
 checks=h.load(E/'object-global-reconciliation.json.gz')['rows'];objects={r['native_id']:r for r in h.load(E/'individual-object-captures.json.gz')['rows']};creators=h.load(E/'creator-global-reconciliation.json')['creators'];rows=[];holds=[]
 for x in checks:
  r=x['source'];cap=objects[r['id']];o=cap['object'];cs=[creators[c] for c in x['creator_native_ids']];reason=None
  if not cap['csv_consistent']:reason='CSV and JSON source fact discrepancy requires review'
  elif x['global_accession_matches'] or x['native_matches']:reason='Existing accession/native candidates require exact physical-version reconciliation'
  elif x['global_title_matches']:reason='Existing exact title candidates require composition/version review'
  elif h.norm(r['title']) in ['untitled','work','dream','stairs','hong kong','forest','tai kok tsui waterfront']:reason='Generic or repeated title requires broader variant/composition reconciliation'
  elif r['displayDate']=='mid-20th century':reason='Broad source bounds and creator chronology require date review'
  elif len(cs)!=1 or len(o['constituents'])!=1 or o['constituents'][0]['role']['en']!='Artist':reason='Multiple or non-primary creator role requires review'
  elif len(cs[0]['candidates'])>1:reason='Multiple existing painter records unresolved; do not choose duplicate creator'
  elif x['creator_date_works'] or x['unlinked_creator_works']:reason='Creator/date works require individual translated-title/version comparison'
  if reason:holds.append(dict(native_id=r['id'],title=r['title'],reason=reason));continue
  c=cs[0];a=c['candidates'][0] if len(c['candidates'])==1 else None
  # Do not silently resolve existing artist biographical discrepancies.
  birth=c['source']['beginDate'];death=c['source']['endDate']
  link=bool(a and a['status']!='archived' and (not birth.isdigit() or a['birth_year'] in [None,int(birth)]) and (not death.isdigit() or a['death_year'] in [None,int(death)]))
  raw=dict(original_title=r['titleTC'] or None,object=o,source_csv=r,source_creator=c['source'],dataset_commit=h.load(E/'dataset-pin.json')['commit'],physical_unit='One museum accession; full object, not an image, crop or generic composition.',metadata_credit='source: M+ Museum, Hong Kong',metadata_transformations='English title displayed with original Traditional Chinese title retained; source bounds and dimensions preserved; work_type mapped from Painting; no endorsement implied.',image_decision='Image rights excluded from metadata CC0; no native image requested or approval inferred.',creator_resolution='Verified unique name/alias and compatible source life dates' if link else 'Source creator label preserved; no new painter fabricated; global reconciliation evidence retained.')
  rows.append(dict(provider='mplus',source_id=r['id'],source_url=cap['source_url'],museum=MUSEUM,title=r['title'],creator_label=c['source']['name'],creator_link_hold=not link,verified_artist_id=a['id'] if link else None,date_display=r['displayDate'],year_start=int(r['beginDate']),year_end=int(r['endDate']),date_decision='eligible',accession_number=r['objectNumber'],source_type='painting',medium=r['medium'],dimensions=r['dimension'],credit=r['creditLine'],raw=raw,evidence_file=cap['evidence_file'],evidence=cap['receipt'],dataset_receipt=h.load(E/'dataset-objects.receipt.json'),creator_receipt=h.load(E/'dataset-creators.receipt.json'),metadata_licence='CC0 1.0; source: M+ Museum, Hong Kong. Images excluded.',identity_review='Exact native ID, unique accession, bilingual titles, role, source date bounds, medium and dimensions; no accession/native/title/creator-date production matches in bounded global reconciliation.',date_basis='Explicit museum object creation fields, not acquisition or creator life dates.'))
 assert 1<=len(rows)<=50
 save('editorial-selections-and-holds.json',dict(at=h.now(),selected_native_ids=[r['source_id'] for r in rows],held=holds,selected_count=len(rows),held_count=len(holds),new_painters=0,artist_links=sum(bool(r['verified_artist_id']) for r in rows),images_selected=0))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert not p['held'] and all(not r['before'] for r in p['records'])
 with h.connect() as db:collision(db,p['records'])
 print('Frozen selected',len(rows),'held',len(holds),'pin',pin,flush=True)
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  present=h.snapshot(db,ids)
  if present:
   notes=db.execute("SELECT evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
   assert len(present)==len(notes)==len(ids) and all(x['pin']==pin for x in notes),'Partial or different plan requires reconciliation'
   assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={}
   print('Own plan recovered; zero replay writes.');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'prewrite-verification.json')['passed']
 save('production-target-before-metadata-write.json',checked);h.apply(PHASE)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
