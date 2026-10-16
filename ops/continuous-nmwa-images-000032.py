#!/usr/bin/env python3
"""One bounded NMWA image-gap continuation. External supervisor untouched."""
import csv, fcntl, gzip, importlib.util, json, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base32','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000032'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000032'
B='fng-000'
i.OP='continuous-primary-images-20261011-b000032';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
MID='688a05df-a339-5dde-9fd0-4263559553f1';SID='a1289df1-6bd3-4276-b6f5-7d46fc3a2429'
i.CFG['fng']=dict(mid=MID,scheme='fng-object',name='Finnish National Gallery',rights='cc0',license='CC0 1.0',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='kokoelma.kansallisgalleria.fi')
old_uid=i.m.uid;i.m.uid=lambda k:SID if k=='source/fng' else old_uid(k)
def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(key,url):
 rp=E/'source-captures'/(key+'.receipt.json');bp=rp.with_name(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 host=urlsplit(url).hostname;assert not (E/'access-holds'/(host+'.json')).exists(),'Recorded provider hold'
 i.provider_slot(host);r=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=r.content
 bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(raw),body_path=str(bp.relative_to(ROOT)),retry_after=r.headers.get('Retry-After'),location=r.headers.get('Location'))
 save(rp,rc)
 if r.status_code in [401,403,429]:save(E/'access-holds'/(host+'.json'),rc)
 return raw,rc
def reconcile():
 save(E/'production-target-reconciliation.json',target())
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),registry_records=111,complete_registry=reg,precedence='Current bounded production image authorization; real local catalogue read-only; original registry authoritative. External supervisor untouched.'))
 q=load(E.parents[1]/'source-queue.json');save(E/'source-queue-before.json',q)
 save(E/'source-access-holds.json',dict(at=h.now(),inherited=[r for r in q['sources'] if 'hold' in r['status'] or '403' in r['status']],prior_batch=load(E.parent/'000031/source-access-holds.json'),policy='Do not retry held providers without a documented state change.'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 old=E.parent/'000031';receipt=load(old/'batch-verification-receipt.json');ids=receipt['production_ids']
 with connect() as db:
  states=h.snapshot(db,ids);assert len(states)==5 and all(x['artwork']['primary_media_id'] for x in states.values())
  ev=[dict(r) for r in db.execute('SELECT a.id::text,m.adapter_version,m.evidence_json,m.source_checksum FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(ev)==5
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Uncertain earlier write needs pinned-plan reconciliation'
 save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=31,live_states=states,rights_evidence=ev,prior_receipt_sha256=h.sha((old/'batch-verification-receipt.json').read_bytes()),new_increments=0,current_campaign_rows=len(own)))
 with connect() as db:
  inst=[dict(r) for r in db.execute("SELECT id::text,name,slug,website_url,status FROM institutions WHERE name ILIKE '%western art%' OR website_url ILIKE '%nmwa.go.jp%' ORDER BY id LIMIT 20")]
  mids=[r['id'] for r in inst]
  rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,unlinked_creator_label,current_institution_id::text,primary_media_id::text,status FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' AND primary_media_id IS NULL ORDER BY id LIMIT 100",(mids,))]
  native=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme",([r['id'] for r in rows],))]
 save(E/'bounded-gap-input.json',dict(at=h.now(),institutions=inst,rows=rows,identifiers=native,limit=100))
 for key,url in [('nmwa-policy','https://www.nmwa.go.jp/en/collection/images.html'),('nmwa-collection','https://collection.nmwa.go.jp/en/')]:
  raw,rc=capture(key,url);print(key,rc,BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)[:12000],flush=True)
 print('INSTITUTIONS',json.dumps(inst),'GAPS',len(rows),'SAMPLE',json.dumps(rows[:5]),flush=True)
def prepare():
 if (E/'gap-reconciliation.json').exists() and load(E/'gap-reconciliation.json')['selected']==0:
  print('Pinned FNG slice contains no eligible source images; preserve cursor and use the Princeton continuation.');return
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 import hashlib
 fng=mod('fng32','overnight-fng-images.py')
 pool=load(E/'fng-bounded-gap-input.json');ids=[r['id'] for r in pool['rows']];exts={r['entity_id']:r for r in pool['identifiers'] if r['scheme']=='fng-object'}
 capath=ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json';cap=load(capath);export=Path(cap['path'])
 with export.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
 wanted={v['external_id'] for v in exts.values()};objects={}
 with export.open('rb') as f:
  for obj in json.load(f):
   if str(obj['objectId']) in wanted:objects[str(obj['objectId'])]=obj
 save(E/'fng-export-reuse-verification.json',dict(at=h.now(),original_receipt_path=str(capath.relative_to(ROOT)),original_receipt=cap,verified_export_sha256=cap['sha256'],objects_extracted=len(objects),metadata_date_preserved=True,export_redownloaded=False,unselected_images_downloaded=0))
 raw,policy=capture('fng-api-documentation','https://kokoelma.kansallisgalleria.fi/api/swagger/')
 print('FNG API documentation',policy['status'],flush=True)
 with connect() as db:
  before=h.snapshot(db,ids)
  creators=[dict(r) for r in db.execute("SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name,ar.birth_year,ar.death_year,p.external_id FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id LEFT JOIN external_identifiers p ON p.entity_type='artist' AND p.entity_id=aa.artist_id AND p.scheme='fng-person' WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id",(ids,))]
  native=[dict(r) for r in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='fng-object' AND external_id=ANY(%s)",(list(wanted),))]
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before=before,creators=creators,global_native_identifiers=native))
 chosen=[];checks=[]
 for x in pool['rows']:
  aid=x['id'];ext=exts.get(aid)
  if not ext:
   checks.append(dict(artwork_id=aid,title=x['title'],native_id=None,outcome='No exact native FNG object identifier; separate source identity review required'));continue
  oid=ext['external_id'];reason=None;o=objects.get(oid)
  try:
   assert o,'Object absent from source export'
   a=before[aid]['artwork'];cr=[r for r in creators if r['artwork_id']==aid]
   assert a['primary_media_id'] is None and a['status']!='archived','No longer active primary gap'
   assert [r['entity_id'] for r in native if r['external_id']==oid]==[aid],'Global native identifier conflict'
   assert len(cr)==1,'Qualified/multiple creator needs separate review'
   c=dict(a,external_id=oid,fng_people=[cr[0]['external_id']],roles=[cr[0]['attribution_role']])
   photo,url=fng.source_match(c,o,require_state_owner=False)
   assert o['responsibleOrganisation']=='Kansallisgalleria / Ateneumin taidemuseo'
   assert (o.get('yearTo') or o['yearFrom'])<=1955
   person=next(p for p in o['people'] if p.get('role',{}).get('en')=='Artist')
   for key,nativekey in [('birth_year','birthYear'),('death_year','deathYear')]:
    assert cr[0][key] is None or person.get(nativekey) is None or cr[0][key]==person[nativekey],'Creator authority date conflict'
   op=E/'objects'/(oid+'.json.gz');save(op,o);raw=json.dumps(o,ensure_ascii=False,sort_keys=True).encode();bp=E/'source-captures'/('fng-object-'+oid+'.body.gz');bp.write_bytes(gzip.compress(raw,mtime=0))
   rc=dict(at=h.now(),url=cap['url'],status=200,sha256=h.sha(raw),body_path=str(bp.relative_to(ROOT)),extraction=True,original_export_receipt=cap,source_retrieved_at=cap['retrieved_at'])
   save(E/'source-captures'/('fng-object-'+oid+'.receipt.json'),rc)
   credit=cr[0]['display_name']+'; Finnish National Gallery'+('; photograph: '+photo['photographer_name'] if photo.get('photographer_name') else '')
   chosen.append(dict(artwork_id=aid,native_id=oid,title=a['title'],creator_label=cr[0]['display_name'],source_url=ext['canonical_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='fng',expected_primary_artist_id=cr[0]['artist_id'],image=dict(image_url=url,source=o,receipt=rc,selected_photo=photo),source_credit=credit,plan_sha256=h.sha(op.read_bytes()),plan_path=str(op),rights_basis='Exact FNG object ID, inventory, title, native creator authority, date and unique preferred reproduction with photograph-specific CC0 label. Public anonymous metadata export captured 10 October 2026 and checksum verified; no API-key route used. Owner and responsible museum preserved as evidence; no holdings or current-display changes.',manual_visual_required=True))
  except (AssertionError,ValueError,KeyError) as exc:reason=str(exc)
  checks.append(dict(artwork_id=aid,native_id=oid,title=x['title'],outcome=reason or 'selected_exact_cc0_primary_image'))
 save(E/'gap-reconciliation.json',dict(at=h.now(),checked=len(checks),selected=len(chosen),rows=checks,resume_after_artwork_id=pool['rows'][-1]['id'],processed_native_ids=[exts[x['id']]['external_id'] for x in pool['rows'] if x['id'] in exts]))
 assert chosen,'No eligible selected source images'
 save(i.folder(B)/'selection.json.gz',dict(provider='fng',batch=B,rows=chosen,metadata_first=True,source_export=cap,selection_basis='25 bounded Ateneum active primary gaps; exact native authority and object checks; unique preferred photograph explicitly CC0.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()
def finish():
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)
original_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 if table=='media_assets':
  selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={im['media_id']:im for im in i.accepted(B)[0]}
  for row in rows:
   im=images[row['id']];credit=selected[im['artwork_id']]['source_credit'];row['creator_credit']=credit;row['attribution_text']=credit+'. CC0 1.0. Full source frame preserved; proportional resizing and JPEG compression.'
 return original_copy(db,table,rows)
i.n.copy_rows=copy_rows
def deliver():
 images,_,_=i.accepted(B);ids=[r['artwork_id'] for r in images];assert 1<=len(ids)<=100
 with connect() as db:
  states=h.snapshot(db,ids);present=[r for r in images if states[r['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(states[r['artwork_id']]['artwork']['primary_media_id']==r['media_id'] for r in images)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Own recovery preimages required'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
