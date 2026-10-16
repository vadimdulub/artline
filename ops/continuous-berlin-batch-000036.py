#!/usr/bin/env python3
"""One bounded Berlin Byzantine batch. Existing supervisor owns continuation."""
import csv, fcntl, gzip, importlib.util, inspect, json, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base36','continuous-image-batch-000002.py');h=mod('metadata36','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000036'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000036'
OP='continuous-berlin-20261011-b000036';PHASE='berlin-mosaics';FIELD='continuous_berlin_object_evidence_20261011_b000036';B='berlin-000'
MUSEUM='Skulpturensammlung und Museum für Byzantinische Kunst, Staatliche Museen zu Berlin'
SLUG='skulpturensammlung-museum-byzantinische-kunst-berlin';WEB='https://www.smb.museum/museen-einrichtungen/skulpturensammlung/home/'
SCHEME='smb-native-object';SELECTED=['1408418','1436813'];ALL=SELECTED+['1722054','1788002','1787214']
DATES={'1408418':('Datierung: 1. Viertel 12. Jahrhundert',1101,1125),'1436813':('Ende 13. Jahrhundert',1201,1300)}
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'berlin':[SCHEME,'smb-object','museum-native-smb-object']};h.museums=lambda:{MUSEUM:(SLUG,WEB)}
MID=h.uid('museum/'+SLUG)
for p in [E,R,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,value);return value
def target(write=False):
 name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert name=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=name,helper='ops/india-300-delivery-20261011.py',local_connections=0)
def native(oid):
 rc=h.load(E/'source-captures'/('object-'+oid+'.receipt.json'));raw=gzip.decompress((E/'source-captures'/('object-'+oid+'.body.gz')).read_bytes())
 assert rc['status']==200 and h.sha(raw)==rc['sha256']
 d=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NUXT_DATA__').string)
 def unpack(idx):
  if idx<0:return None
  v=d[idx]
  if isinstance(v,dict):return {k:unpack(n) for k,n in v.items()}
  if isinstance(v,list):
   if v and isinstance(v[0],str):return unpack(v[1]) if len(v)>1 else v
   return [unpack(n) for n in v]
  return v
 obj=next(v for v in unpack(0)['data'].values() if isinstance(v,dict) and v.get('id')=='obj-'+oid)
 assert obj==h.load(E/'objects'/(oid+'.json'))
 return obj,rc
def no_collision(db,rows):
 ids=[r['source_id'] for r in rows];urls=[u for r in rows for u in r['identity_urls']];acc=[r['accession_number'] for r in rows]
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',(acc,)).fetchall(),'Concurrent accession; replan'
 assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme ILIKE '%%smb%%'",(ids,)).fetchall(),'Concurrent native identity; replan'
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall(),'Concurrent source identity; replan'
h.no_collision=no_collision
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous source-backed production enrichment, batch 36 Berlin mosaics. Anonymous creators stay unknown; exact inventories and front-view image identities retained.')
code=code.replace('Separate city branch explicitly identified by the official national museum portal','Distinct named collection explicitly identified by the official institution page')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows),'Bounded new objects only'")
code=code.replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():print('Pinned plan retained');return
 save('production-target-reconciliation.json',target())
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 files=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=x,sha256=h.sha((ROOT/x).read_bytes())) for x in files],registry=dict(path=str(regpath),sha256=h.sha(regpath.read_bytes()),rows=reg),precedence='Current bounded worker instruction, production authorized, real local catalogue read-only; original 111-source registry authoritative; no supervisor changes.'))
 queue=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',queue)
 save('source-access-holds.json',dict(at=h.now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000035/source-access-holds.json',inherited_queue=[r for r in queue['sources'] if 'hold' in r['status'] or '403' in r['status']],berlin='No recorded SMB hold found. Native object and robots HTTP 200; robots permits search and AI input. No held providers retried.'))
 rc=h.load(E/'source-captures/collection.receipt.json');assert rc['status']==200
 h.save(E/'captures/collection.json.gz',rc);(E/'captures/collection.body.gz').write_bytes((E/'source-captures/collection.body.gz').read_bytes())
 rows=[];checks=[]
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  prior=h.load(E.parent/'000035/batch-verification-receipt.json');previous=prior['production_ids']
  live=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(previous,))]
  assert len(live)==6
  for x in live:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert ev['selection_sha256']==prior['selection_sha256']
  interrupted=db.execute('SELECT entity_id::text FROM citations WHERE field_name=%s',(FIELD,)).fetchall();assert not interrupted,'Reconcile prior own writes first'
  save('prior-write-reconciliation.json',dict(at=h.now(),batch35_live_rows=live,prior_receipt_sha256=h.sha((E.parent/'000035/batch-verification-receipt.json').read_bytes()),batch36_prior_citations=interrupted,prior_increments_counted=0))
  institutions=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i')]
  near=[x for x in institutions if any(t in (x['name']+' '+x['slug']).casefold() for t in ['berlin','bode','skulpturen'])]
  assert not any(x['slug']==SLUG or h.norm(x['name'])==h.norm(MUSEUM) for x in institutions)
  samehost=[x['id'] for x in institutions if x['website_url'] and urlsplit(x['website_url']).netloc.removeprefix('www.')=='smb.museum']
  h.save(E/'institution-branch-review.json',{MUSEUM:dict(same_host_institution_ids=samehost,evidence=rc,basis='Distinct named collection explicitly identified by the official institution page')})
  save('institution-reconciliation.json',dict(at=h.now(),existing_candidates=near,new_collection_id=MID,source_capture=rc,decision='Official distinct collection at Bode-Museum; generic network and Gemäldegalerie records are not the same collection. New institution only because two selected physical objects support it.'))
  scope=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])',([x['id'] for x in near],))];h.save(E/'institution-scope-before.json.gz',scope)
  for oid in ALL:
   o,orc=native(oid);urls=[o['permalink'],'https://search.smb.museum/en/object/obj-'+oid,'https://search.smb.museum/object/obj-'+oid,'https://recherche.smb.museum/detail/'+oid]
   titles=[o['title']]+[x['nameLine'] for x in o['additionalTitles']]
   matches=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text,dimensions_text FROM artworks WHERE accession_number=%s OR normalized_title=ANY(%s)',(o['ident'],[h.norm(x) for x in titles]))]
   sourceids=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=%s",(oid,))]
   sourceurls=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls))]
   why='Documented long-term loan to Frankfurt; ownership/custody representation must be reconciled before this route imports it.' if oid not in SELECTED else None
   if matches or sourceids or sourceurls:why='Existing or ambiguous global object identity; excluded from new increments.'
   checks.append(dict(source_id=oid,title=o['title'],inventory=o['ident'],global_matches=matches,native_matches=sourceids,url_matches=sourceurls,outcome=why or 'selected_new',source_receipt=orc))
   if why:continue
   date,lo,hi=DATES[oid];assert o['dating']==[dict(nameLine=date)] and not o['actors'] and 'Dauerleihgabe' not in o['html_text']
   assert o['org_unit']=='Skulpturensammlung und Museum für Byzantinische Kunst'
   front=o['images'][0];assert front['asset_content']=='Vorderseite' and front['obj_ref']==['obj:'+oid] and front['license']=='Public Domain Mark 1.0'
   ep=E/'objects'/(oid+'.json');dim='; '.join(x['nameLine'] for x in o['dimensions'])
   rows.append(dict(provider='berlin',source_id=oid,source_url=urls[1],identity_urls=urls,museum=MUSEUM,title=o['title'],creator_label=None,creator_link_hold=True,culture=None,date_display=date,year_start=lo,year_end=hi,date_decision='eligible',accession_number=o['ident'],source_type='mosaic',medium=o['material_desc'],dimensions=dim,credit=None,raw=dict(native=o,dimensions=dim,original_title=o['title']),evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=orc['at'],sha256=h.sha(ep.read_bytes()),url=urls[1]),source_receipt=orc,identity_review='Exact native object and inventory, full mosaic panel; additionalTitles reconciled globally. No current display claim. Named creator absent in official actors array: no artist invented. Native mosaic label retained, general work type unknown rather than invented painting subtype.',date_basis='First quarter of 12th century = 1101–1125. End of 13th century kept verbatim; conservative whole-century bounds 1201–1300, no invented narrower year.'))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,selected=len(rows),institution_scope_count=len(scope),directory_coverage='Only five exact objects reviewed; no complete coverage claim.'))
 assert len(rows)==2
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE);p,pin=h.pinned(PHASE)
 assert len(p['records'])==2 and len(p['new_institutions'])==1 and not p['artists'] and all(not x['before'] for x in p['records'])
 save('source-register.json',dict(at=h.now(),registry=next(x for x in reg if x['source_id']=='staatliche_museen_berlin'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Official native public catalogue HTTP 200; explicit per-image Public Domain Mark 1.0 front views; no provider extension generalized.',plan_sha256=pin,remaining_gaps='Three long-term loans held for separate custody/ownership modelling; wider Byzantine and post-Byzantine collection remains unresearched. Legacy doc_types search parameter was ignored: saved results rejected, not used for object selection.'))
 save('helper-adaptation.json',dict(metadata_helper='ops/india-300-delivery-20261011.py',metadata_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),image_helper='ops/illustrated-300k-20261011.py',image_sha256=h.sha((ROOT/'ops/illustrated-300k-20261011.py').read_bytes()),changes=['Dedicated operation and pinned citation field; bounded new objects only','Distinct institution evidence on shared domain','Shared artline-curated-ingestion transaction lock and exact identity rechecks','Native photographer credit preserved in media creator_credit'],plan_sha256=pin))
 print('STAGED',len(rows),pin,flush=True)
def source_verify():
 p,pin=h.pinned(PHASE);checks=[]
 for r in p['records']:
  o,rc=native(r['source_id']);date,lo,hi=DATES[r['source_id']]
  assert o==r['raw']['native'] and o['ident']==r['accession_number'] and o['title']==r['title']
  assert r['first']==lo and r['last']==hi and r['precision']=='range' and hi<=1970 and r['date_display']==date
  assert r['artist_id'] is None and r['creator_label'] is None and r['before'] is None
  assert not o['actors'] and not any(w in o['html_text'].lower() for w in ['dauerleihgabe','kriegsverlust','verschollen'])
  assert h.sha((ROOT/r['evidence_file']).read_bytes())==r['evidence']['sha256']
  checks.append(dict(source_id=r['source_id'],inventory=o['ident'],title=o['title'],date=date,conservative_bounds=[lo,hi],source_creators=o['actors'],creator_unknown_preserved=True,source_capture_sha256=rc['sha256'],evidence_sha256=r['evidence']['sha256'],image_id=o['images'][0]['id'],source_image_rights=o['images'][0]['license'],scope='Whole physical inventory object, not detail or counterpart; documented collection holding, no display assertion.'))
 save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 assert h.load(E/'independent-source-verification.json')['plan_sha256']==pin
 save('production-target-before-metadata-write.json',target(True))
 with h.connect() as db:
  existing=h.snapshot(db,ids)
  if existing:
   notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
   assert len(notes)==len(existing)==len(ids) and all(x['pin']==pin for x in notes)
   locked=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert locked['plan_sha256']==pin and locked['artworks']=={}
   print('Own committed plan recovered; no replay');return
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL'
 save('cloud-sql-backup.json',backup);save('cloud-backup.json',backup);target(True);h.apply(PHASE)
i.OP=OP+'-images';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['berlin']=dict(mid=MID,scheme=SCHEME,name=MUSEUM,rights='public_domain',license='Public Domain Mark 1.0',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='search.smb.museum')
old_uid=i.m.uid;i.m.uid=lambda k:h.uid('source/berlin/'+MUSEUM) if k=='source/berlin' else old_uid(k)
code=inspect.getsource(i.apply).replace("    tables['media_assets'].append", "    credit=r.get('creator_credit',credit)\n    tables['media_assets'].append")
exec(compile(code,__file__,'exec'),i.__dict__)
def images():
 p,pin=h.pinned(PHASE);rows=[]
 for r in p['records']:
  o=r['raw']['native'];im=o['images'][0];assert im['asset_content']=='Vorderseite' and im['license']=='Public Domain Mark 1.0'
  url='https://search.smb.museum/media'+im['xl_path']
  rows.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label='',source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),provider='berlin',image=dict(image_url=url,source=o,receipt=r['source_receipt']),plan_sha256=pin,creator_credit='Staatliche Museen zu Berlin, Skulpturensammlung und Museum für Byzantinische Kunst / '+im['photographer']+'. Public Domain Mark 1.0.',rights_basis='Specific native front-view image '+im['id']+' explicitly Public Domain Mark 1.0; exact obj_ref and photograph credit retained. User production authorization separate from native rights designation; no newly obtained licence claimed.',manual_visual_required=True))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='berlin',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 i.ORIG.mkdir(parents=True,exist_ok=True)
 for r in rows:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B);print('Review prepared individual images before deliver')
def deliver():
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
