#!/usr/bin/env python3
"""One bounded exact-native WikiArt primary-gap continuation; no supervisor."""
import copy,csv,datetime,fcntl,gzip,importlib.util,io,json,os,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit,urljoin
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
h=module('production173','india-300-delivery-20261011.py')
i=module('images173','illustrated-300k-20261011.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000173'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000173'
OP='continuous-greek-wikiart-20261013-b000173-images';B='wikiart-native-000'
TARGET='artline-508319:europe-west1:artline-postgres'
ARTISTS=['611e3ea8-f874-5bb7-b3d0-2dbc3530b690']
for p in [E,R]:p.mkdir(parents=True,exist_ok=True)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
i.CFG['wikiart']['scheme']='wikiart-artwork'
def connect(write=False,local=False):
 assert not local,'Real local catalogue remains read only; no local connection in this batch'
 db=h.connect(write);db.autocommit=False;return db
i.m.m.connect=connect
r=i.m.m
ORIGINAL_SOURCE_RUN=r.RUN
r.RUN=E

def save(name,value):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,value);return value
def rel(p):return str(Path(p).relative_to(ROOT))
def target(stage):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 commands=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxies=[x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxies)==1
 with h.connect() as db:
  server=dict(db.execute('SELECT current_database() database,pg_is_in_recovery() recovery').fetchone());assert server['database']=='artline' and not server['recovery']
 return save('production-target-'+stage+'.json',dict(at=h.now(),connection_name=actual,proxy_command=proxies[0],database=server,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))

def preflight():
 target('reconciliation')
 registry_path=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(registry_path.open()));qp=E.parents[1]/'source-queue.json';queue=h.load(qp)
 assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in queue['sources']}
 required=[ROOT/'AGENTS.md',registry_path,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',qp]
 # Read the complete required files and complete original registry, not its supplement.
 for p in required:p.read_text()
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],registry_rows=111,complete_original_registry_used=True,real_local_catalogue_read_only=True))
 save('original-source-registry.json',registry)
 save('source-queue-preimage.json',queue)
 hold_paths=[ORIGINAL_SOURCE_RUN/'access-holds/www.wikiart.org.json',ROOT/'docs/research/illustrated-300k-20261011/access-holds/www.ernstfuchs-zentrum.com.json']
 hold_paths += [p for n in ['000141','000166','000168','000172'] for p in (E.parent/n).glob('*holds*.json')]
 holds=[]
 for p in hold_paths:
  if p.exists():holds.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),content=h.load(p)))
 # The WikiArt shop denial is a separate surface; never revisit it.
 wiki_hold=h.load(hold_paths[0]);assert wiki_hold['status']==403 and urlsplit(wiki_hold['url']).path.startswith('/store/')
 save('inherited-holds-verification.json',dict(at=h.now(),files=holds,all_queue_sources_read=111,prior_provider_and_object_holds_preserved=True,shop403_not_requested=True,athens_completed_native_gap_keyset_not_replayed=True,route='Exact native WikiArt gaps for Panayiotis Tetsis; current explicit through1970 programme authorization and WikiArt approval, not Greek museum source extension'))
 for batch,key in [('000107','after'),('000172','rows')]:
  path=E.parent/batch/'independent-production-verification.json';prev=h.load(path)
  with h.connect() as db:live=h.snapshot(db,list(prev[key]))
  assert live==prev[key]
  save('batch'+str(int(batch))+'-live-reconciliation.json',dict(at=h.now(),rows=len(live),snapshot_equal=True,prior_receipt_sha256=h.sha(path.read_bytes()),previous_increments_counted=0))
 save('authorization.json',dict(at=h.now(),user_approval='Current bounded continuous-production instruction explicitly authorizes authentic primary images from WikiArt, through1970 creation scope; no per-batch approval.',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',catalogue_creation_scope='through1970',source='WikiArt only; Greek museum source approval not generalized',actual_rights_preserved=True,copyright_holder_licence=False,production_sql_and_storage_authorized=True,translation_prohibited=True))
 # These are additional native-ID-linked gaps, not restarted target-complete work.
 stopfiles=[p for p in (ROOT/'docs/research/illustrated-300k-20261011').glob('*') if any(t in p.name.lower() for t in ['stop','complete']) and p.is_file()]
 save('separate-continuation-campaign.json',dict(at=h.now(),operation=OP,previous_campaign_files_unchanged=[dict(path=rel(p),sha256=h.sha(p.read_bytes())) for p in stopfiles],no_supervisor_or_schedule_launched=True))
 print('PREFLIGHT production proxy verified; batches107/172 receipts reconciled; original111 registry and holds read.',flush=True)

def discover():
 assert (E/'required-input-verification.json').exists()
 dest=E/'gap-input.json.gz'
 if dest.exists():print('Pinned gap input exists; resume source review');return
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  rows=[dict(x) for x in db.execute("SELECT a.id::text artwork_id,to_jsonb(a) artwork,to_jsonb(e) native,ar.id::text artist_id,ar.display_name artist_name FROM artists ar JOIN artwork_artists aa ON aa.artist_id=ar.id AND aa.attribution_role='primary' JOIN artworks a ON a.id=aa.artwork_id JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' AND e.scheme='wikiart-artwork' WHERE ar.id=ANY(%s::uuid[]) AND a.status<>'archived' AND a.primary_media_id IS NULL AND a.creation_year_end<=1970 ORDER BY a.id LIMIT 10",(ARTISTS,))]
  profiles=[dict(x) for x in db.execute("SELECT entity_id::text,canonical_url,external_id FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) AND scheme='wikiart-artist'",(ARTISTS,))]
  aliases=[dict(x) for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])',(ARTISTS,))]
  before=h.snapshot(db,[x['artwork_id'] for x in rows])
 save('gap-input.json.gz',dict(at=h.now(),rows=rows,before=before,profiles=profiles,aliases=aliases,scope='One existing Greek creator Panayiotis Tetsis + exact wikiart-artwork native identity + active + primaryNULL + creation_end<=1970; bounded LIMIT10. Metadata before downloads.'))
 print('DISCOVERED',len(rows),'existing gaps',flush=True)

def research():
 inputs=h.load(E/'gap-input.json.gz');selected=[];decisions=[]
 # Prior per-object/manual holds are checked without calling denied providers.
 hold_files=[p for p in (ROOT/'docs/research').glob('*/manual*holds*.json') if p.is_file()]
 previous_holds={}
 for p in hold_files:
  value=h.load(p)
  if isinstance(value,dict):previous_holds.update(value.get('held_artwork_ids',{}))
 save('prior-object-hold-check.json',dict(at=h.now(),files=[dict(path=rel(p),sha256=h.sha(p.read_bytes())) for p in hold_files],candidate_holds={x['artwork_id']:previous_holds[x['artwork_id']] for x in inputs['rows'] if x['artwork_id'] in previous_holds}))
 for entry in inputs['rows']:
  aid=entry['artwork_id'];path=E/'source-research'/(aid+'.json')
  if path.exists():decision=h.load(path)
  else:
   decision=dict(artwork_id=aid,source_url=entry['native']['canonical_url'],native_id=entry['native']['external_id'])
   try:
    assert aid not in previous_holds,'Prior individual image/version hold'
    url=entry['native']['canonical_url'];assert urlsplit(url).hostname=='www.wikiart.org' and urlsplit(url).path.startswith('/en/') and '/store/' not in url
    i.d.core.provider_rate_slot('www.wikiart.org');page=r.wiki_fields(url)
    a=entry['artwork'];assert page['source_id']==entry['native']['external_id'],'Current native ID changed'
    assert urlsplit(urljoin(url,page['metadata']['paintingUrl'])).path.rstrip('/')==urlsplit(url).path.rstrip('/'),'Current object URL changed'
    assert h.norm(page['title']) in {h.norm(a['title']),h.norm(a['alternate_title'])},'Title/version changed'
    assert page['date'] and (page['date']['first'],page['date']['last'])==(a['creation_year_start'],a['creation_year_end']) and page['date']['last']<=1970,'Source creation-date conflict'
    aliases={h.norm(x['alias']) for x in inputs['aliases'] if x['artist_id']==entry['artist_id']};aliases.add(h.norm(entry['artist_name']))
    profiles={x['canonical_url'].rstrip('/') for x in inputs['profiles'] if x['entity_id']==entry['artist_id'] and x['canonical_url']}
    assert h.norm(page['creator']) in aliases and page['artist_url'].rstrip('/') in profiles,'Creator authority differs'
    meta=page['metadata']['image'];display=page['image_url'];assert re.fullmatch(r'uploads\d*\.wikiart\.org',urlsplit(meta).hostname or '')
    assert display and '/Content/images/' not in display,'Placeholder must remain held'
    assert urlsplit(meta).path.split('!')[0]==urlsplit(display).path.split('!')[0],'Display/metadata image identity conflict'
    with h.connect() as db:
     live=h.snapshot(db,[aid])[aid];assert live==inputs['before'][aid],'Catalogue changed during selection'
     owners=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=%s",(page['source_id'],))];assert owners==[dict(entity_id=aid)],'Native object assigned to another work'
     prior_media=[dict(x) for x in db.execute("SELECT ma.id::text,am.artwork_id::text FROM media_assets ma LEFT JOIN artwork_media am ON am.media_id=ma.id WHERE ma.source_page_url=%s",(url,))];assert not prior_media,'Source page already has media; reconciliation needed'
    row=dict(artwork_id=aid,provider='wikiart',native_id=page['source_id'],current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=url,accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],expected_museum_id=a['current_institution_id'],expected_primary_artist_id=entry['artist_id'],rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis']+' Current source-backed continuous production approval; exact native object dated through1970.',image=dict(native_url=meta,image_url=meta,source=page,receipt=page['receipt']),plan_sha256=h.sha((E/'gap-input.json.gz').read_bytes()),identity_confidence=.99,identity_basis='Exact globally unique persisted native WikiArt artwork ID, canonical current object URL, unchanged title, literal creation bounds and globally existing creator identity/profile. Display and embedded native image agree. No inferred museum holding or date mutation.',manual_visual_required=True)
    decision.update(decision='selected_requires_actual_visual_review',confidence=.99,page=page,global_native_owners=owners,prior_media=prior_media,row=row)
   except Exception as exc:decision.update(decision='held',reason=type(exc).__name__+': '+str(exc)[:500])
   h.save(path,decision)
  decisions.append(decision)
  if decision['decision']=='selected_requires_actual_visual_review':selected.append(decision['row'])
  print(aid,decision['decision'],decision.get('reason',''),flush=True)
 assert len({x['native_id'] for x in selected})==len(selected)
 assert len({x['image']['image_url'] for x in selected})==len(selected)
 save('exact-identity-decisions.json',dict(at=h.now(),rows=decisions,selected=len(selected),metadata_updates=0))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='wikiart',batch=B,rows=selected,selection_basis='Separate bounded exact-native WikiArt continuation for One existing Greek creator Panayiotis Tetsis. Metadata selected before downloading; explicit current through1970 instruction retained.'))
 h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 assert selected,'No eligible candidates; retain exact holds and checkpoint without writes'

def prepare():
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 i.audit(B)
 for path in (i.folder(B)/'prepared').glob('*.json'):
  im=h.load(path);print('IMAGE',im.get('original_path'),im.get('path'),im.get('flags'),im.get('reason',''),flush=True)
 save('PREPARED.json',dict(at=h.now(),stage='prepared_requires_actual_visual_review',selected=len(i.selected(B)['rows']),next_action='View all prepared originals and derivatives; record individual decisions before delivery'))

def deliver():
 images,audit,review=i.accepted(B);assert images and all(x['viewed_individually'] and x['original_viewed'] for x in review['decisions'])
 assert len(images)==sum(x['decision']=='accept' for x in review['decisions'])
 target('before-storage-write')
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791897658924','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-backup.json',backup)
 i.upload(B);target('before-database-write');i.apply(B)
 print('DELIVERY complete; run independent verification next',flush=True)

def finalize():
 images,audit,review=i.accepted(B);ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images};rows={x['artwork_id']:x for x in i.selected(B)['rows']};selection=h.sha((i.folder(B)/'selection.json.gz').read_bytes());prepath=i.BACKUP/B/'before-000.json.gz';before=h.load(prepath)
 assert all(before[x]['artwork']['primary_media_id'] is None for x in ids)
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
  media=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.width,ma.height,ma.rights_status,ma.license_label,ma.creator_credit,ma.source_page_url,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])",(ids,))]
  search=[dict(x) for x in db.execute('SELECT a.id::text,s.primary_media_id::text,s.status,s.title FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,))]
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[expected[x]['media_id'] for x in ids]))]
 assert len(ids)==len(after)==len(media)==len(search)==len(events)
 for aid in ids:
  assert after[aid]['artwork']['primary_media_id']==expected[aid]['media_id']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
 for event in events:
  assert event['before_json']==before[event['entity_id']]['artwork'] and event['after_json']==after[event['entity_id']]['artwork']
 for item in media:
  aid=item['id'];im=expected[aid];row=rows[aid];ev=item['evidence_json'] if isinstance(item['evidence_json'],dict) else json.loads(item['evidence_json'])
  assert (item['checksum_sha256'],item['byte_size'],item['adapter_version'],item['rights_status'],item['license_label'],item['source_record_id'],item['source_checksum'])==(im['sha256'],im['bytes'],OP,row['rights_status'],row['rights_label'],row['native_id'],row['image']['receipt']['sha256'])
  assert ev['selection_sha256']==selection and ev['identity_confidence']>=.90 and ev['visual_review']['sha256']==im['sha256'] and ev['visual_review']['original_viewed'] and ev['visual_review']['viewed_individually']
  assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and im['bytes']<=100000 and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
  assert Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline/source-images')
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 save('independent-production-verification.json',dict(at=h.now(),before=before,after=after,media=media,search_documents=search,selection_sha256=selection,transaction_preimage_path=str(prepath),preimage_sha256=h.sha(prepath.read_bytes()),verified_counts=counts,metadata_creators_holdings_status_unchanged=True,passed=True,local_catalogue_connections=0))
 save('independent-audit-history-verification.json',dict(at=h.now(),events=events,preimage_sha256=h.sha(prepath.read_bytes()),selection_sha256=selection,passed=True))
 public=[]
 for aid in ids:
  im=expected[aid];url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;api=requests.get(url,timeout=(15,45));api.raise_for_status();pic=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));pic.raise_for_status();assert im['storage_path'] in api.text and h.sha(pic.content)==im['sha256']
  with Image.open(io.BytesIO(pic.content)) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
  public.append(dict(artwork_id=aid,api_status=api.status_code,api_sha256=h.sha(api.content),image_status=pic.status_code,storage_path=im['storage_path'],sha256=h.sha(pic.content),bytes=len(pic.content),full_decode=True))
 save('independent-public-verification.json',dict(at=h.now(),rows=public,passed=True))
 from google.cloud import storage
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);bucket=storage.Client(project='artline-508319',credentials=credentials).bucket(i.d.core.BUCKET);stored=[]
 for aid in ids:
  im=expected[aid];blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=blob.download_as_bytes();assert h.sha(raw)==im['sha256'] and blob.size==im['bytes'] and blob.metadata['operation']==OP and blob.metadata['sha256']==im['sha256'];stored.append(dict(artwork_id=aid,object_key=blob.name,generation=blob.generation,bytes=blob.size,sha256=h.sha(raw),metadata=blob.metadata))
 save('independent-storage-verification.json',dict(at=h.now(),rows=stored,passed=True))
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=selection,transaction_preimage_sha256=h.sha(prepath.read_bytes()),production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Null primary image in locked transaction preimage and matching audit before/after. Unique batch173 adapter, selection checksum, exact source page checksum and visual decisions persisted in media rights evidence. Fresh independent database/search/storage/public reads; previous programmes excluded.'))
 source_checks=[]
 for aid,row in rows.items():
  rc=row['image']['receipt'];body=E/'captures'/(h.sha(rc['url'].encode())+'.body.gz');raw=gzip.decompress(body.read_bytes());assert h.sha(raw)==rc['sha256'];source_checks.append(dict(artwork_id=aid,source_capture=rel(body),source_sha256=h.sha(raw),rights_label=row['rights_label'],rights_status=row['rights_status'],source_id=row['native_id'],confidence=row['identity_confidence']))
 save('independent-source-and-visual-verification.json',dict(at=h.now(),sources=source_checks,visual_review_sha256=h.sha((i.folder(B)/'visual-review.json').read_bytes()),actual_visual_decisions=review['decisions'],prepared_images=len(audit['prepared_images']),delivered_images=len(ids),passed=True))
 nxt='Process saved Smithsonian SAAM metadata shard24 (metadata/edan/saam/24.txt) for exact existing primary-image gaps, reconciling live primaries and CC0 designations before selected downloads. Then rotate to an untouched Greek museum creator route. Tetsis dated native WikiArt gaps processed through UUID899961a7-73a5-5dc5-a0ec-8283cf3104ba; French188 reserve and completed Athens routes remain excluded.'
 cursor=dict(route='wikiart-native-greek-tetsis',artist_ids=ARTISTS,processed_artwork_ids=[x['artwork_id'] for x in h.load(E/'gap-input.json.gz')['rows']],after_artwork_id=h.load(E/'gap-input.json.gz')['rows'][-1]['artwork_id'],selected=len(rows),verified=len(ids),processed_native_ids=[x['native_id'] for x in rows.values()],delivered_artwork_ids=ids,query_scope='active exact native wikiart-artwork + primaryNULL + dated through1970; bounded LIMIT10',next_task=nxt)
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);queue=h.load(qp);old=copy.deepcopy(queue)
  route=dict(route_id='wikiart-native-greek-tetsis',provider='WikiArt',policy_reference='docs/ARTLINE_IMAGE_USE.md WikiArt approval and current explicit continuous through1970 image instruction',status='bounded_native_primary_gaps_verified',last_checked_at=h.now(),last_batch=173,access_status='Exact catalogue pages and selected images HTTP200; denied shop not requested.',resume_cursor=cursor,latest_batch_verified_counts=counts,checkpoint=rel(E/'CHECKPOINT.json'),verification_receipt=rel(E/'batch-verification-receipt.json'),remaining_gaps=['Only this dated native gap query covered; no complete artist oeuvre or museum coverage claim.','Unknown-date records and distinct versions require separate review; original holds remain preserved.'])
  existing=[x for x in queue.get('supplementary_image_routes',[]) if x.get('route_id')==route['route_id']]
  if existing:
   assert len(existing)==1 and existing[0]['resume_cursor']==cursor and existing[0]['latest_batch_verified_counts']==counts and existing[0]['last_batch']==173,'Conflicting queue recovery'
   route=existing[0]
  else:
   queue.setdefault('supplementary_image_routes',[]).append(route)
   assert queue['sources']==old['sources'] and queue['supplementary_image_routes'][:-1]==old['supplementary_image_routes']
   tmp=qp.with_suffix('.173.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_route=cursor['route'],all111_registry_entries_unchanged=True,existing_supplementary_entries_unchanged=True,prior_holds_preserved=True,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor))
 save('source-register-final.json',dict(at=h.now(),provider='WikiArt',original_registry_rows=111,original_registry_remains_complete=True,policy_reference=route['policy_reference'],access_status=route['access_status'],directory_coverage_count=0,discovered=len(h.load(E/'gap-input.json.gz')['rows']),selected=len(rows),prepared=len(audit['prepared_images']),imported=len(ids),verified=len(ids),actual_visual_review_count=len(review['decisions']),resume_cursor=cursor,remaining_gaps=route['remaining_gaps']))
 save('failures-and-holds.json',dict(at=h.now(),research_holds=[x for x in h.load(E/'exact-identity-decisions.json')['rows'] if x['decision']=='held'],image_holds=audit['preparation_holds'],identity_holds=audit['identity_holds'],visual_holds=[x for x in review['decisions'] if x['decision']!='accept'],prior_provider_holds_unchanged=True,unchanged_failed_provider_retries=0,local_setup_errors=[dict(error='System Python lacks psycopg',resolution='Used established /tmp/artline-cesi-venv/bin/python')],web_tool_errors=[]))
 start=h.load(E/'production-target-reconciliation.json')['at'];finish=h.now();seconds=(datetime.datetime.fromisoformat(finish)-datetime.datetime.fromisoformat(start)).total_seconds()
 names=['required-input-verification.json','original-source-registry.json','inherited-holds-verification.json','batch107-live-reconciliation.json','batch172-live-reconciliation.json','separate-continuation-campaign.json','production-target-reconciliation.json','production-target-before-storage-write.json','production-target-before-database-write.json','gap-input.json.gz','exact-identity-decisions.json','batches/'+B+'/quality-audit.json','batches/'+B+'/visual-review.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','independent-source-and-visual-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json','failures-and-holds.json']
 cp=dict(at=finish,batch=173,stage='independently_verified_complete',operation=OP,discovered=len(h.load(E/'gap-input.json.gz')['rows']),selected=len(rows),prepared=len(audit['prepared_images']),imported=len(ids),verified=len(ids),verified_counts=counts,production_ids=ids,next_task=nxt,blocker='',evidence=[rel(E/x) for x in names],started_at=start,finished_at=finish,measured_runtime_seconds=seconds,external_supervisor_unchanged=True,local_catalogue_connections=0)
 cp=save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 artifacts=[]
 for name in names+['CHECKPOINT.json']:
  p=E/name;h.load(p);artifacts.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=artifacts,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,passed=True))
 result=dict(outcome='progress',summary=f'Batch173 independently verified {len(ids)} authentic primary images on existing Greek artworks after exact native WikiArt identity review. All delivered originals and derivatives were actually viewed; production, audit, source attribution, Storage and public delivery passed. Batches107/172 reconciled; metadata and local catalogue unchanged.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in ['independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','independent-source-and-visual-verification.json','source-queue-update-verification.json','independent-final-artifact-verification.json','CHECKPOINT.json']])
 save('verified-batch-result.json',result);h.save(R/'verified-batch-result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
