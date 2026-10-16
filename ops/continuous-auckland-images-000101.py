#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base101','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000101'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000101'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000101'
B='auckland-native-101';MID='3db0938a-e500-5263-9890-2997fa1d0d44'
i.OP='continuous-auckland-images-20261011-b000101';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return load(p)
 h.save(p,value);return value
def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text();node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply');code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'")
code=code.replace("tables['media_assets'].append(dict(", "credit+=(' '+r['source_credit'] if r.get('source_credit') else '')\n    tables['media_assets'].append(dict(")
code=code.replace("assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'", "assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'\n    cite=r['image']['source']['identity_reconciliation']['source_citation']\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s\",(aid,cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone(),'Pinned identity citation changed'")
exec(compile(code,__file__,'exec'),i.__dict__)
POLICY='https://www.aucklandartgallery.com/privacy-policy'
i.CFG['auckland']=dict(mid=MID,scheme='auckland-object',name='Auckland Art Gallery Toi o Tāmaki',rights='restricted',license='No known copyright restrictions',policy=POLICY,host='artgallery-collection-api.cdn.aucklandunlimited.com')
old_uid=i.m.uid;i.m.uid=lambda k:i.uid(k) if k=='source/auckland' else old_uid(k)
old_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={load(p)['media_id']:selected[load(p)['artwork_id']] for p in (i.folder(B)/'prepared').glob('*.json') if load(p)['state']=='prepared'}
 if table=='media_assets':
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/auckland'),i.OP+'-auckland','Auckland exact native object image evidence','https://www.aucklandartgallery.com',i.OP))
  for row in rows:
   r=images[row['id']];row['creator_credit']=r['source_credit'];row['attribution_text']=r['source_credit']+'. '+r['rights_label']+' (museum statement concerns New Zealand). Complete supplied composition retained; proportional resizing and JPEG compression. Source accessed '+r['image']['receipt']['retrieved_at']
 if table=='media_rights_evidence':
  for row in rows:
   r=images[row['media_id']];ev=json.loads(row['evidence_json']);ev.update(identity=r['identity_basis'],identity_confidence=r['identity_confidence'],source_policy=load(E/'source-policy-verification.json'),actual_source_rights=r['rights_label'],user_authorization=load(E/'authorization.json'));row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return old_copy(db,table,rows)
i.n.copy_rows=copy_rows

def capture(url):
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','commons.wikimedia.org','www.aucklandartgallery.com'] and '/store/' not in url
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=DATA/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];assert rc['status']==200;return raw,rc
 assert not (E/'access-holds'/(host+'.json')).exists(),'Source host held'
 i.provider_slot(host);res=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=res.content
 bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=res.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After'))
 h.save(rp,rc)
 if res.status_code in [401,403,429]:save('access-holds/'+host+'.json',dict(rc,retry_allowed=False))
 assert res.status_code==200,('Source HTTP',res.status_code,url)
 return raw,rc
i.m.m.capture=capture
def deliver():
 images,_,_=i.accepted(B);assert 0<len(images)<=100
 ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images}
 with connect() as db:
  states=h.snapshot(db,ids);present=[aid for aid in ids if states[aid]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(ids) and all(states[aid]['artwork']['primary_media_id']==expected[aid]['media_id'] for aid in ids),'Concurrent or mixed image state: replan, never overwrite'
   old=load(i.BACKUP/B/'before-000.json.gz');assert all(old[aid]['artwork']['primary_media_id'] is None for aid in ids)
   rights=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in images],))];assert len(rights)==len(ids)
   pin=h.sha((i.folder(B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(B)/'visual-review.json').read_bytes())
   for r in rights:
    ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
   save('pre-replay-attribution-reconciliation.json',dict(at=h.now(),own_committed_rows=len(ids),own_selection_sha256=pin,transaction_preimage_sha256=h.sha((i.BACKUP/B/'before-000.json.gz').read_bytes()),no_new_increments=True))
  else:assert not any((i.folder(B)/'applied').glob('*.json')),'Saved applied receipts disagree with live state'
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)


def stage():
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');entries=list(csv.DictReader(registry.open()));assert len(entries)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),complete_registry=entries,precedence='Current production authorization; local catalogue read-only; external supervisor untouched.'))
 q=save('source-queue-before.json',load(E.parents[1]/'source-queue.json'));source=next(r for r in q['sources'] if r['source_id']=='auckland_art_gallery');cursor=source['resume_cursor']['next_keyset_after_frozen_input'];assert not source['resume_cursor']['pending_artwork_ids']
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 ledgers=[p for p in E.parent.rglob('*hold*.json') if E not in p.parents]+list((base.OLD/'access-holds').glob('*.json'))
 relevant=[dict(path=str(p.relative_to(ROOT)),data=load(p)) for p in ledgers if any(s in p.name for s in ['wikiart','wikipaintings','auckland'])]
 assert not any('wikiart.org' in x['path'] or 'wikipaintings' in x['path'] for x in relevant)
 save('source-access-holds.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in ledgers],relevant=relevant,source_queue=source,policy='Old Auckland URL HTTP404 only; no provider-wide hold. Preserve recorded URLs, no unchanged failed retries.'))
 save('production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists()
  previous=load(E.parent/'000100/batch-verification-receipt.json');ids=previous['production_ids'];live=h.snapshot(db,ids);old=load(E.parent/'000100/CHECKPOINT.json')
  cit=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  assert all(any(c['entity_id']==aid and old['metadata_plan_sha256'] in c['evidence_note'] for c in cit) for aid in ids)
  assert all(a['artwork']['primary_media_id'] for a in live.values())
  gaps=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,a.work_type,(SELECT string_agg(ar.display_name,' / ') FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a WHERE a.current_institution_id=%s AND a.id>%s AND a.primary_media_id IS NULL AND a.status<>'archived' AND a.creation_year_end<=1970 ORDER BY a.id LIMIT 60",(MID,cursor))]
  ids=[r['id'] for r in gaps];states=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=100,live=live,citations=cit,previous_increments_counted=0,current_campaign_rows=own))
 save('gap-input.json.gz',dict(at=h.now(),rows=gaps,before=states,citations=citations,identifiers=identifiers,institution_id=MID,previous_cursor=cursor,limit=60))
 print(json.dumps(gaps,ensure_ascii=False))

def native_research():
 from bs4 import BeautifulSoup
 native=mod('native101','museum-expansion-auckland-20261006.py')
 raw,rc=capture(POLICY);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
 assert "This material may be copied and otherwise re-used in New Zealand without copyright or other intellectual property right related restriction" in text
 save('source-policy-verification.json',dict(at=h.now(),receipt=rc,text=text,decision='Registry per-record reusable-image policy; current gallery explicitly permits reuse of NKCR/Copyright expired works, qualified to New Zealand. Retain restricted rights classification and full labels; no global public-domain or copyright-holder licence assertion.',old_route_404_not_provider_hold=True))
 data=load(E/'gap-input.json.gz');candidates=[];dispositions=[]
 for row in data['rows']:
  cs=[c for c in data['citations'] if c['entity_id']==row['id'] and c['field_name']=='museum_expansion_primary_metadata']
  if len(cs)!=1:dispositions.append(dict(artwork_id=row['id'],reason='Historical Wikidata/native object crosswalk needs separate review; no image download',stage='deferred'));continue
  c=cs[0];n=json.loads(c['evidence_note']);f=n['raw_source_record']['native_fields']['fields']
  if f.get('Copyright','').lower() not in ['no known copyright restrictions','copyright expired']:
   dispositions.append(dict(artwork_id=row['id'],reason='Native copying restrictions apply',rights_label=f.get('Copyright'),stage='held'));continue
  if row['creation_year_end']>1955:
   dispositions.append(dict(artwork_id=row['id'],reason='Date requires source-specific later work review',stage='held'));continue
  candidates.append(dict(artwork=row,citation=c,historical=n))
 save('native-metadata-candidates.json.gz',candidates);save('native-initial-dispositions.json',dispositions)
 for c in candidates:
  aid=c['artwork']['id'];raw,rc=capture(c['citation']['source_url']);parsed=native.fields(raw)
  save('native/'+aid+'.json',dict(receipt=rc,parsed=parsed,text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)))
  print(aid[:8],parsed['fields'].get('Copyright'),parsed['fields'].get('Title'),flush=True)


def prepare():
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  for r in i.selected(B)['rows']:i.prepare_one(r,B)
  i.audit(B);print('Resumed immutable prepared selection');return
 import re
 native=mod('nativeprep101','museum-expansion-auckland-20261006.py')
 data=load(E/'gap-input.json.gz');candidates=load(E/'native-metadata-candidates.json.gz');selected=[];held=[];identities=[]
 with connect() as db:
  states=h.snapshot(db,[c['artwork']['id'] for c in candidates])
  for c in candidates:
   row=c['artwork'];aid=row['id'];a=states[aid]['artwork'];historical=c['historical'];x=load(E/'native'/ (aid+'.json'));f=x['parsed']['fields'];attrs=x['parsed']['native_route']['attributes'];ext=next(e for e in data['identifiers'] if e['entity_id']==aid and e['scheme']=='auckland-object');oid=ext['external_id']
   assert states[aid]==data['before'][aid] and a['primary_media_id'] is None
   assert str(attrs['id'])==oid and f['Accession No']==a['accession_number']==attrs['accession_no'] and f['Title']==a['title']==attrs['name']
   assert x['parsed']['creator_names']==historical['raw_source_record']['native_fields']['creator_names']
   if x['parsed']['creator_names']!=[a['unlinked_creator_label']]:held.append(dict(artwork_id=aid,native_id=oid,reason='Literal creator label variant requires separate attribution review',source_creators=x['parsed']['creator_names'],catalogue_creator=a['unlinked_creator_label']));continue
   assert all(f[k]==historical['raw_source_record']['native_fields']['fields'][k] for k in ['Artist','Title','Production date','Medium','Dimensions','Credit line','Accession No','Copyright'])
   dates=native.creation_date(f['Production date']);assert dates[:2]==(a['creation_year_start'],a['creation_year_end']) and dates[1]<=1955
   assert f['Copyright'].lower() in ['no known copyright restrictions','copyright expired'] and f['Copyright']==attrs['copyright']
   oldbody=gzip.decompress((ROOT/historical['body_path']).read_bytes());assert h.sha(oldbody)==historical['source_receipt']['sha256'];assert native.fields(oldbody)==historical['raw_source_record']['native_fields']
   similar=[dict(v) for v in db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE status<>'archived' AND (lower(title)=lower(%s) OR (current_institution_id=%s AND accession_number=%s)) ORDER BY id LIMIT 100",(a['title'],MID,a['accession_number']))]
   ids=[dict(v) for v in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='auckland-object' AND external_id=%s) OR canonical_url=%s)",(oid,ext['canonical_url']))]
   if [v['id'] for v in similar]!=[aid] or {v['entity_id'] for v in ids}!={aid}:
    held.append(dict(artwork_id=aid,native_id=oid,reason='Existing same-title/inventory or native-ID catalogue rows require exact duplicate reconciliation; no image download',similar=similar,identifiers=ids));continue
   url=attrs['zoom_image']
   if not url:held.append(dict(artwork_id=aid,native_id=oid,reason='Current native record supplies no zoom image; no URL invented or image downloaded'));continue
   assert urlsplit(url).hostname==i.CFG['auckland']['host'] and '/images/xlarge/' in url
   assert '/'+url.split('/images/xlarge/',1)[1]== '/'+attrs['thumbnail_image'].split('/images/medium/',1)[1]
   dims=[float(v) for v in re.findall(r'[0-9]+(?:\.[0-9]+)?',f['Dimensions'])];assert f['Dimensions'].endswith(' mm') and len(dims) in [2,3]
   basis='Exact existing native object ID, accession, title, creator label, source creation range and physical dimensions; fresh museum fields equal checksum-verified original catalogue citation. Unique active same-title/inventory and native-ID records. Museum supplies the full zoom image for this object; visual composition review required.'
   identity=dict(artwork_id=aid,native_id=oid,accession=a['accession_number'],global_identifiers=ids,same_title_inventory_rows=similar,source_citation=c['citation'],source_citation_sha256=h.sha(json.dumps(c['citation'],sort_keys=True,ensure_ascii=False).encode()),historical_source_sha256=historical['source_receipt']['sha256'],current_source_sha256=x['receipt']['sha256'],dimensions_mm=dims,confidence=.99,confidence_basis=basis,current_display_claim=False)
   identities.append(identity)
   selected.append(dict(artwork_id=aid,native_id=oid,current_source_id=oid,title=a['title'],creator_label=f['Artist'],source_url=c['citation']['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='auckland',expected_museum_id=MID,rights_status='restricted',rights_label=f['Copyright'],rights_basis='Exact museum object/image has '+f['Copyright']+'. Current gallery policy explicitly allows copying and reuse of these labels; statement concerns New Zealand. No independent copyright-holder licence or worldwide public-domain claim. Native restricted labels and cultural notices excluded; user approval recorded separately.',source_credit=f['Artist']+'. '+f['Title']+'. '+f['Credit line'],image=dict(native_url=url,image_url=url,source=dict(official_metadata=x,identity_reconciliation=identity),receipt=x['receipt']),plan_sha256=historical['plan_sha256'],identity_confidence=.99,identity_basis=basis,manual_visual_required=True))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=identities,holds=held))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,policy_reference='Original 111-source CSV auckland_art_gallery + docs/ARTLINE_IMAGE_USE.md General image-use policy; current museum NKCR/Copyright expired exception',copyright_holder_licence=False,actual_rights_labels_and_territorial_qualification_preserved=True,local_catalogue_read_only=True))
 assert selected
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='auckland',batch=B,rows=selected,selection_basis='Bounded exact native Auckland primary gaps. Current per-object reusable labels and policy; selected before downloading; catalogue duplicates held.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 print('Selected',len(selected),'duplicate holds',len(held),flush=True)
 for r in selected:
  im=i.prepare_one(r,B);print(im['artwork_id'][:8],im['state'],im.get('bytes'),im.get('reason',''),flush=True)
 i.audit(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
