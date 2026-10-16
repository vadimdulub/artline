#!/usr/bin/env python3
"""One bounded Sinebrychoff image-gap continuation. External supervisor untouched."""
import csv, fcntl, gzip, importlib.util, inspect, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base38','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000038'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000038'
B='fng-000'
i.OP='continuous-primary-images-20261011-b000038';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
MID='6f2f70d1-457b-57b5-9f1a-ac72f1525524';SID='a1289df1-6bd3-4276-b6f5-7d46fc3a2429'
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
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000037/source-access-holds.json',inherited_queue='source-queue-before.json',new_route_hold='mauritshuis-route-verification.json',policy='No access-held provider retry; metadata export reuse and permitted selected CC0 image route only.'))
 save(E/'mauritshuis-route-verification.json',dict(at=h.now(),registry_id='mauritshuis',existing_access_hold='docs/research/all-museums-20260910/access-summary.json',existing_hold_status=403,object_page='https://www.mauritshuis.nl/en/our-collection/artworks/765-cavalry-engagement',policy_page='https://www.mauritshuis.nl/en/contact/requesting-visual-material',verification='Read-only indexed web-tool pages: current general image policy allows royalty-free reuse; indexed object download modal requests contact for commercial use. Historical direct collection HEAD access hold preserved.',decision='hold_direct_access_and_conflicting_object_terms',direct_provider_requests=0,images_downloaded=0,next_step='Resolve provider access and reconcile current object-specific terms before any image download; switch sources.'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 old=E.parent/'000037';receipt=load(old/'batch-verification-receipt.json');ids=receipt['production_ids']
 with connect() as db:
  states=h.snapshot(db,ids);assert len(states)==4 and all(x['artwork']['primary_media_id'] for x in states.values())
  ev=[dict(r) for r in db.execute('SELECT a.id::text,m.adapter_version,m.evidence_json,m.source_checksum FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(ev)==4
  for r in ev:
   e=r['evidence_json'];e=json.loads(e) if isinstance(e,str) else e
   assert e['selection_sha256']==receipt['selection_sha256'] and e['batch_visual_review_sha256']==receipt['visual_review_sha256']
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Uncertain earlier write needs pinned-plan reconciliation'
 save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=37,live_states=states,rights_evidence=ev,prior_receipt_sha256=h.sha((old/'batch-verification-receipt.json').read_bytes()),new_increments=0,current_campaign_rows=len(own)))
 if (E/'fng-bounded-gap-input.json').exists():return
 with connect() as db:
  rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,unlinked_creator_label,current_institution_id::text,primary_media_id::text,status FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 ORDER BY id LIMIT 80",(MID,))]
  native=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme",([r['id'] for r in rows],))]
 save(E/'fng-bounded-gap-input.json',dict(at=h.now(),institution_id=MID,rows=rows,identifiers=native,limit=80,route='Sinebrychoff existing primary gaps; distinct from Ateneum cursor'))
 save(E/'source-register.json',dict(at=h.now(),registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),sources=[x for x in reg if x['source_id'] in ['mauritshuis','finnish_national_gallery']],policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access='Saved official anonymous FNG export; unique per-photo CC0 required',remaining_gaps='Bounded Sinebrychoff branch only, Ateneum queue preserved, no nationwide completeness claim.'))
 print('Staged',len(rows),flush=True)
def prepare():
 if (E/'gap-reconciliation.json').exists() and load(E/'gap-reconciliation.json')['selected']==0:
  print('Pinned FNG slice contains no eligible source images; preserve cursor and select another source.');return
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 import hashlib
 fng=mod('fng38','overnight-fng-images.py')
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
   assert o['responsibleOrganisation']=='Kansallisgalleria / Sinebrychoffin taidemuseo'
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
 save(i.folder(B)/'selection.json.gz',dict(provider='fng',batch=B,rows=chosen,metadata_first=True,source_export=cap,selection_basis='80 bounded Sinebrychoff active primary gaps; exact native authority and object checks; unique preferred photograph explicitly CC0.'))
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

def prepare_cited():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 pool=load(E/'fng-bounded-gap-input.json');prior=load(E/'preparation-production-snapshot.json.gz')['before']
 citations=load(E/'native-citation-crosswalk.json')['citations'];objects=load(E/'cited-source-objects.json.gz')
 cap=load(ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json')
 import hashlib
 with Path(cap['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
 historical={};history_checks=[]
 for c in citations:
  note=json.loads(c['evidence_note']);path=ROOT/note['evidence_path']
  if str(path) not in historical:
   raw=gzip.decompress(path.read_bytes());assert h.sha(raw)==note['source_response_sha256']
   historical[str(path)]={str(o['objectId']):o for o in json.loads(raw)}
   history_checks.append(dict(path=str(path),sha256=h.sha(raw),current_export_sha256=cap['sha256']))
 chosen=[];checks=[];reconciled=[]
 with connect() as db:
  for x in pool['rows']:
   aid=x['id'];cs=[c for c in citations if c['entity_id']==aid];reason=None
   try:
    assert len(cs)==1,'Needs unique native holding citation'
    c=cs[0];note=json.loads(c['evidence_note']);oid=note['object_id'];o=objects[oid];a=prior[aid]['artwork']
    assert note['scheme']=='fng-object' and note['identity_basis']=='unique_exact_supplied_creator_title_collection_date'
    old=historical[str(ROOT/note['evidence_path'])][oid]
    for k in ['objectId','inventoryNumber','title','yearFrom','yearTo','datePrefix','people','dimensions','owner','responsibleOrganisation','parents','children']:
     assert o.get(k)==old.get(k),'Source identity changed since documented holding crosswalk: '+k
    assert o['responsibleOrganisation']=='Kansallisgalleria / Sinebrychoffin taidemuseo'
    assert o.get('category',{}).get('categoryId')=='artwork' and not o.get('parents') and not o.get('children'),'Multipart source object needs review'
    assert h.norm(a['title']) in {h.norm(v) for v in o['title'].values() if v},'Current title mismatch'
    people=[v for v in o['people'] if v.get('role',{}).get('en')=='Artist']
    assert len(people)==1 and not people[0].get('attribution'),'Qualified/multiple creator requires separate review'
    person=people[0];name=' '.join(v for v in [person.get('firstName'),person.get('familyName')] if v)
    assert not prior[aid]['creators'] and h.norm(a['unlinked_creator_label'])==h.norm(name),'Exact existing creator label not established'
    lo=o['yearFrom'];hi=o.get('yearTo') or lo
    assert isinstance(lo,int) and isinstance(hi,int) and 1000<=lo<=hi<=1955,'Source creation scope needs review'
    assert (lo,hi)==(a['creation_year_start'],a['creation_year_end']),'Source date differs'
    assert not (lo!=hi and lo==person.get('birthYear') and hi==person.get('deathYear')),'Source interval repeats artist lifespan'
    prefix=(o.get('datePrefix') or {}).get('en');assert prefix in [None,'','circa'],'Open-ended creation date'
    precision=('circa' if lo==hi else 'circa_range') if prefix=='circa' else ('exact' if lo==hi else 'range')
    assert precision==a['date_precision'],'Source date precision differs'
    if a['accession_number']:assert h.norm(a['accession_number'])==h.norm(o['inventoryNumber'])
    assert a['primary_media_id'] is None and a['status']!='archived'
    external=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme='fng-object' AND external_id=%s))",(c['source_url'],oid))]
    cited=[dict(r) for r in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(c['source_url'],))]
    inventory=[dict(r) for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(MID,o['inventoryNumber']))]
    assert {r['entity_id'] for r in external+cited}|{r['id'] for r in inventory}=={aid},'Global object/citation/inventory identity conflict'
    photos=[v for v in o.get('multimedia',[]) if v.get('isRiaDisplayImage') and v.get('license')=='CC0']
    assert len(photos)==1,'No unique preferred CC0 reproduction'
    photo=photos[0];path=photo.get('jpg',{}).get('1000');assert path and re.fullmatch(r'/media-assets/\d+/jpg/1000/[\w.-]+',path)
    if len(chosen)>=20:
     checks.append(dict(artwork_id=aid,native_id=oid,outcome='eligible_deferred_to_next_bounded_batch'));continue
    ident=dict(artwork_id=aid,native_id=oid,source_inventory=o['inventoryNumber'],catalogue_inventory=a['accession_number'],source_person_id=person['id'],creator_label=name,dates=[lo,hi],date_precision=precision,source_dimensions=o.get('dimensions'),global_identifiers=external,global_citations=cited,inventory_matches=inventory,prior_citation=c,confidence=.98,basis='Pinned historical and current official object records agree on inventory, creator, title, dates, dimensions, ownership and physical-object relationships. Existing source citation uniquely identifies this catalogue record; global source/inventory collisions excluded. Missing catalogue inventory retained, not filled.')
    reconciled.append(ident)
    op=Path.home()/'Library/Application Support/Artline/source-metadata'/i.OP/(oid+'.json.gz');save(op,o)
    body=json.dumps(o,ensure_ascii=False,sort_keys=True).encode();bp=op.with_name(oid+'.body.gz');bp.write_bytes(gzip.compress(body,mtime=0))
    rc=dict(at=h.now(),url=cap['url'],status=200,sha256=h.sha(body),body_path=str(bp),extraction=True,original_export_receipt=cap,source_retrieved_at=cap['retrieved_at'])
    save(E/'source-captures'/(oid+'.receipt.json'),rc)
    chosen.append(dict(artwork_id=aid,native_id=oid,title=a['title'],creator_label=name,source_url=c['source_url'],accession_number=a['accession_number'],first=lo,last=hi,precision=precision,work_type=a['work_type'],provider='fng',image=dict(image_url='https://kokoelma.kansallisgalleria.fi'+path,source=o,receipt=rc,selected_photo=photo),source_credit=name+'; Finnish National Gallery / Sinebrychoff Art Museum; photograph: '+str(photo.get('photographer_name') or 'not supplied'),plan_sha256=note['plan_sha256'],plan_path=note['evidence_path'],identity_citation=c,identity_reconciliation=ident,rights_basis='Exact official source object and photograph-specific CC0 label, preserved from verified anonymous export. Prior and current object identity reconciled through persisted unique native citation; no catalogue metadata or holdings changed.',manual_visual_required=True))
   except (AssertionError,KeyError,ValueError) as exc:reason=str(exc) or 'Missing or unexpected source preferred-photo path'
   checks.append(dict(artwork_id=aid,native_id=json.loads(cs[0]['evidence_note'])['object_id'] if cs else None,outcome=reason or 'selected_exact_cited_cc0_primary_image'))
 save(E/'historical-source-verification.json',dict(at=h.now(),sources=history_checks))
 save(E/'cited-gap-reconciliation.json',dict(at=h.now(),checked=len(checks),selected=len(chosen),rows=checks,selection_limit=20,initial_native_identifier_screen='gap-reconciliation.json',resume_after_artwork_id=pool['rows'][-1]['id']))
 save(E/'global-identity-reconciliation.json',dict(at=h.now(),records=reconciled))
 assert chosen
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='fng',batch=B,rows=chosen,source_export=cap,selection_basis='Existing gaps reconciled through unique persisted native holding citations, historical/current object identity and explicit preferred CC0 photographs. 20-image bounded selection before downloads.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()

def locked_identities(db,ids,rows):
 out={}
 for aid in ids:
  r=rows[aid];c=r['identity_citation'];live=dict(db.execute('SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE id=%s',(c['id'],)).fetchone());assert live==c
  matches=db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme='fng-object' AND external_id=%s))",(c['source_url'],c['source_url'],r['native_id'])).fetchall();assert {v['entity_id'] for v in matches}=={aid}
  out[aid]=r['native_id']
 return out
code=inspect.getsource(i.apply);old="native_ids={r['entity_id']:r['external_id'] for r in db.execute(\"SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme=%s\",(ids,cfg['scheme']))}"
assert old in code;i.locked_identities=locked_identities;exec(compile(code.replace(old,'native_ids=locked_identities(db,ids,rows)'),__file__,'exec'),i.__dict__)
previous_copy=i.n.copy_rows
def copy_with_identity(db,table,rows):
 if table=='media_rights_evidence':
  selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={im['media_id']:im for im in i.accepted(B)[0]}
  for row in rows:
   r=selected[images[row['media_id']]['artwork_id']];ev=json.loads(row['evidence_json']);ev.update(identity_citation=r['identity_citation'],identity_reconciliation=r['identity_reconciliation'],actual_photo_rights=r['image']['selected_photo'],user_authorization=dict(production_attachment=True,copyright_holder_licence=False));row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return previous_copy(db,table,rows)
i.n.copy_rows=copy_with_identity

def retry_octet_stream():
 if (E/'mime-retry-amendment.json').exists():
  assert all(load(i.folder(B)/'prepared'/(r['artwork_id']+'.json'))['state']=='prepared' for r in i.selected(B)['rows']), 'A bounded MIME retry already occurred; reconcile any remaining failures before retrying'
  return finish()
 diagnostic=load(E/'fng-unexpected-response-diagnostic.json')
 assert diagnostic['status']==200 and diagnostic['content_type']=='application/octet-stream' and diagnostic['location'] is None
 moved=[]
 for p in (i.folder(B)/'prepared').glob('*.json'):
  im=load(p)
  if im['state']=='held' and im['reason']=='AssertionError: Unexpected source image response':
   dest=i.folder(B)/'preparation-attempt1'/p.name;dest.parent.mkdir(exist_ok=True)
   moved.append(dict(old_path=str(p),preserved_path=str(dest),sha256=h.sha(p.read_bytes())));p.rename(dest)
 audit=i.folder(B)/'quality-audit.json'
 if audit.exists():audit.rename(audit.with_name('quality-audit-attempt1.json'))
 sheets=i.folder(B)/'sheets'
 if sheets.exists():sheets.rename(sheets.with_name('sheets-attempt1'))
 sheet=i.ORIG/B/'review-000.jpg'
 if sheet.exists():sheet.rename(sheet.with_name('review-attempt1-000.jpg'))
 save(E/'mime-retry-amendment.json',dict(at=h.now(),diagnostic='fng-unexpected-response-diagnostic.json',preserved_failed_receipts=moved,reason='Official selected jpg/1000 image URLs sometimes return application/octet-stream. Permit this MIME only for this FNG provider; require JPEG signature, full decoding, exact object/CC0 identity and actual visual review. This is not an access restriction. No rights or identity threshold relaxed.',retries_per_affected_selected_object=1))
 code=inspect.getsource(i.prepare_one)
 old="assert response.status_code==200 and (rc['content_type'] or '').startswith('image/'),'Unexpected source image response'"
 new="assert response.status_code==200 and ((rc['content_type'] or '').startswith('image/') or (row['provider']=='fng' and host=='kokoelma.kansallisgalleria.fi' and rc['content_type']=='application/octet-stream')),'Unexpected source image response'"
 assert old in code;code=code.replace(old,new)
 old='raw=bytes(payload);rc.update(bytes=len(raw),sha256=m.sha(raw))'
 new="raw=bytes(payload);assert raw[:3]==b'\\xff\\xd8\\xff','Selected FNG payload is not JPEG';rc.update(bytes=len(raw),sha256=m.sha(raw))"
 assert old in code;exec(compile(code.replace(old,new),__file__,'exec'),i.__dict__)
 finish()
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
