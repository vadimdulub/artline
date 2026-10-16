#!/usr/bin/env python3
"""One bounded Met gap continuation; never starts or modifies a supervisor."""
import ast, csv, fcntl, gzip, importlib.util, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('met21',ROOT/'ops/continuous-image-batch-000021.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
i=base.i;h=base.h;connect=base.connect;target=base.target;load=base.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000071'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000071'
B='met-000';MID=base.MID;SID='e9d31deb-98ad-4d21-b71a-ec10005434bf';SCHEME=base.SCHEME
i.OP='continuous-primary-images-20261011-b000071';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 if p.exists():return load(p)
 return i.saved(p,v)

# Established attachment transaction, with the current local recovery policy,
# object-level credits and pinned creator reconciliation persisted as evidence.
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text()
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply')
code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("tables['media_assets'].append", "credit=r['source_credit']\n    tables['media_assets'].append")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    initial=m.load(RUN/'preparation-production-snapshot.json.gz')['before'][aid]\n    assert before[aid]['creators']==initial['creators'] and before[aid]['holdings']==initial['holdings'],'Creator or holding changed since selection'")
code=code.replace("if p['provider']=='wikiart':evidence.update", "evidence.update(identity_reconciliation=r['identity_reconciliation'],user_authorization='Bounded programme production image attachment; actual museum CC0 declaration preserved separately.')\n    if p['provider']=='wikiart':evidence.update")
exec(compile(code,__file__,'exec'),i.__dict__)

def reconcile():
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json','docs/research/continuous-production-20261011/batches/000070/source-access-holds.json','docs/research/continuous-production-20261011/batches/000069/source-access-holds.json']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=x,sha256=h.sha((ROOT/x).read_bytes())) for x in paths],complete_registry=reg,registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),registry_records=111,precedence='Newer source approvals; real local catalogue read-only. One bounded batch; external supervisor untouched.'))
 save(E/'source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json'
 save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 save(E/'production-target-reconciliation.json',target())
 with connect() as db:
  own=list(db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,)))
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Earlier writes require pinned recovery'
  old=E.parent/'000070';receipt=load(old/'batch-verification-receipt.json');ids=receipt['production_ids']
  previous=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(previous)==13
  for x in previous:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert x['adapter_version']=='continuous-primary-images-20261011-b000070' and ev['selection_sha256']==receipt['selection_sha256']
  save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),batch=70,previous_rows=previous,current_campaign_rows=len(own),prior_campaign_increments=0))
 holds={str(p.relative_to(ROOT)):load(p) for p in (base.base.OLD/'access-holds').glob('*.json')}
 assert not any('metmuseum' in k for k in holds)
 save(E/'inherited-source-access-holds.json',dict(at=h.now(),ledgers=paths[-2:],queue='source-queue-before.json',historical_image_holds=holds,met_route='No recorded native API/image access hold. Preserve all unrelated holds.'))
 save(E/'source-register.json',dict(at=h.now(),sources=[r for r in reg if r['source_id']=='met_museum'],policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',policy_url='https://www.metmuseum.org/hubs/open-access',policy_verified='Official open-access page read through web tool 2026-10-12; per-object isPublicDomain required.',access='Anonymous native object API and selected official primary images',remaining_gaps='Only saved UUID priority-subject slice; holdings and current display unchanged.'))
 print('Target, prior delivery and holds reconciled',flush=True)

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 route=next(r for r in load(E/'source-queue-before.json')['sources'] if r['source_id']=='met_museum');cursor=route['resume_cursor']['after_artwork_id']
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.unlinked_creator_label,a.dimensions_text,e.external_id FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' AND e.scheme=%s WHERE a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.status<>'archived' AND a.creation_year_end<=1955 AND a.id>%s::uuid AND a.title ~* 'icon|byzantine|virgin|saint' ORDER BY a.id LIMIT 50",(SCHEME,MID,cursor))]
  ids=[a['id'] for a in rows];states=h.snapshot(db,ids)
  creators=[dict(x) for x in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,))]
 save(E/'bounded-gap-input.json',dict(at=h.now(),after_artwork_id=cursor,rows=rows,limit=50))
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before=states,creators=creators))
 chosen=[];checks=[]
 for a in rows:
  native=a['external_id'];rp=E/'source-captures'/(native+'.receipt.json');body=E/'source-captures'/(native+'.body.gz')
  if rp.exists():rc=load(rp);raw=gzip.decompress(body.read_bytes());assert h.sha(raw)==rc['sha256']
  else:
   url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+native;i.provider_slot('collectionapi.metmuseum.org');r=i.session().get(url,timeout=(15,40));raw=r.content
   body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(raw),body_path=str(body.relative_to(ROOT)),retry_after=r.headers.get('Retry-After'));save(rp,rc)
  if rc['status'] in [401,403,429]:save(E/'source-access-holds.json',dict(rc,retry_allowed=False));break
  if rc['status']!=200:checks.append(dict(artwork_id=a['id'],native_id=native,reason='source_http_'+str(rc['status'])));continue
  d=json.loads(raw);reason='eligible';image=d.get('primaryImageSmall') or d.get('primaryImage')
  cr=[c for c in creators if c['artwork_id']==a['id']];label=d.get('artistDisplayName') or d.get('culture') or ''
  known=[a.get('unlinked_creator_label')]+[c['display_name'] for c in cr]
  if not d.get('isPublicDomain') or not image:reason='no_explicit_cc0_primary_image'
  elif (str(d['objectID']),d['title'],d['accessionNumber'],d['objectBeginDate'],d['objectEndDate'])!=(native,a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end']):reason='identity_or_date_mismatch'
  elif not re.search('paint|draw|print|etch|engrav|woodcut|lithograph|icon',d.get('classification','')+' '+d.get('objectName',''),re.I):reason='non_pictorial_object'
  elif not image.startswith('https://images.metmuseum.org/'):reason='unverified_image_host'
  elif d.get('artistPrefix') or d.get('artistSuffix'):reason='qualified_creator_requires_review'
  elif d.get('artistDisplayName') and h.norm(label) not in {h.norm(x) for x in known if x}:reason='creator_label_requires_review'
  elif len(cr)>1:reason='multiple_creator_roles_require_review'
  checks.append(dict(artwork_id=a['id'],native_id=native,reason=reason))
  if reason=='eligible':
   identity=dict(native_id=native,inventory=a['accession_number'],catalogue_creator_labels=known,source_creator=label,source_dimensions=d.get('dimensions'),catalogue_dimensions=a.get('dimensions_text'),source_credit=d.get('creditLine'),source_attribution_prefix=d.get('artistPrefix'),source_attribution_suffix=d.get('artistSuffix'),basis='Unique exact museum native object ID, accession, title, dates and creator label; native primary image. No version substitution.',editorial_confidence=.99)
   credit='; '.join(v for v in [label,d.get('creditLine'),'The Metropolitan Museum of Art','CC0 1.0'] if v)
   chosen.append(dict(artwork_id=a['id'],native_id=native,title=a['title'],creator_label=label,source_url=d['objectURL'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=d['objectName'].lower(),provider='met',image=dict(native_url=image,image_url=image,source=dict(d,assistivetext=d.get('objectName') or ''),receipt=rc),plan_sha256=h.sha(body.read_bytes()),plan_path=str(body),source_credit=credit,identity_reconciliation=identity,rights_basis='Exact native object API isPublicDomain=true and official Open Access CC0 policy; '+d.get('creditLine','')))
  if len(chosen)>=16:break
 save(E/'gap-reconciliation.json',dict(at=h.now(),rows=checks,selected=len(chosen),after_artwork_id=cursor,resume_after_artwork_id=checks[-1]['artwork_id'] if checks else cursor))
 if not chosen:print('No eligible Met gaps in bounded slice');return
 save(i.folder(B)/'selection.json.gz',dict(provider='met',batch=B,rows=chosen,selection_basis='Existing exact native accession/title/date/creator gaps; native CC0 primary image evidence.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()

def finish():
 for row in i.selected(B)['rows']:i.prepare_one(row,B)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 print('Review sheet:',load(i.folder(B)/'sheets/000.json')['path'],flush=True)

def deliver():
 images,_,_=i.accepted(B);assert 1<=len(images)<=16
 assert load(E/'prewrite-identity-verification.json')['preparation_state_unchanged']
 assert load(E/'prewrite-source-verification.json')['records_verified']==len(images)
 rc=load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)

if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
