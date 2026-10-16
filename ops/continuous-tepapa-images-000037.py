#!/usr/bin/env python3
"""One bounded exact-object Te Papa image batch. No supervisor changes."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base37','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000037';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000037'
B='tepapa-direct-001';MID='da3b80d7-dc07-5573-90ff-25a76a7b8d2e'
i.OP='continuous-primary-images-20261011-b000037';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(key,url):
 rp=E/'source-captures'/(key+'.receipt.json');bp=rp.with_name(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 host=urlsplit(url).hostname;hold=E/'access-holds'/(host+'.json');assert not hold.exists(),'Provider held'
 i.provider_slot(host);r=i.session().get(url,timeout=(15,45));raw=r.content;bp.parent.mkdir(exist_ok=True,parents=True);bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=r.url,status=r.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(bp.relative_to(ROOT)),retry_after=r.headers.get('Retry-After'));save(rp,rc)
 if r.status_code in [401,403,429]:save(hold,rc)
 return raw,rc
def crosswalks():
 data=load(E/'tepapa-bounded-gap-input.json.gz');rows=[]
 for a in data['rows']:
  cs=[r for r in data['citations'] if r['entity_id']==a['id'] and r['field_name']=='museum_source_metadata_and_holding'];
  if len(cs)!=1:continue
  note=json.loads(cs[0]['evidence_note']);ent=note['raw_source_record']['entity'];ids=set(re.findall(r'collections\.tepapa\.govt\.nz/[Oo]bject/(\d+)',cs[0]['evidence_note']));
  if len(ids)!=1:continue
  inv=[r['mainsnak']['datavalue']['value'] for r in ent['claims'].get('P217',[])];assert len(inv)==1
  rows.append(dict(artwork=a,native_id=ids.pop(),wikidata_id=ent['id'],inventory=inv[0],citation=cs[0],claims=ent['claims'],plan_sha256=note['plan_sha256']))
 return rows
def research():
 rows=crosswalks();save(E/'identity-crosswalk-input.json.gz',rows)
 for r in rows:
  raw,rc=capture(r['native_id'],'https://collections.tepapa.govt.nz/object/'+r['native_id']);sp=BeautifulSoup(raw,'html.parser');txt=sp.get_text(' ',strip=True)
  save(E/'object-research'/(r['native_id']+'.json'),dict(at=h.now(),native_id=r['native_id'],receipt=rc,text=txt,links=[dict(href=a.get('href'),text=a.get_text(' ',strip=True)) for a in sp.select('a[href]') if any(x in a['href'].lower() for x in ['rights','download','creativecommons','media/'])],images=[dict(a.attrs) for a in sp.select('img')]))
  print(r['native_id'],rc['status'],txt[:250],flush=True)
  if rc['status'] in [401,403,429]:break

POLICY='https://www.tepapa.govt.nz/learn/research/datasets/collections-api/api-terms-of-use'
i.CFG['tepapa']=dict(mid=MID,scheme='wikidata',name='Museum of New Zealand Te Papa Tongarewa',rights='restricted',license='No Known Copyright Restrictions',policy=POLICY,host='co3-api-mediastorage.s3.ap-southeast-2.amazonaws.com')
old_uid=i.m.uid;i.m.uid=lambda k:i.uid(k) if k=='source/tepapa' else old_uid(k)
def object_from_page(raw):
 sp=BeautifulSoup(raw,'html.parser')
 for script in sp.select('script'):
  if script.text.startswith('self.__next_f.push('):
   part=json.loads(script.text[len('self.__next_f.push('):-1])
   if len(part)>1 and isinstance(part[1],str) and '"entity":{"results":' in part[1]:
    for x in json.loads(part[1].split(':',1)[1]):
     if isinstance(x,list) and isinstance(x[-1],dict) and 'entity' in x[-1]:return x[-1]['entity']['results']
 raise AssertionError('No native object in server-rendered public page')
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 data=load(E/'tepapa-bounded-gap-input.json.gz');cross=load(E/'identity-crosswalk-input.json.gz');selected=[];holds=[];identities=[]
 for a in data['rows']:
  if not any(r['artwork']['id']==a['id'] for r in cross):
   cs=next(c for c in data['citations'] if c['entity_id']==a['id']);urls=sorted(set(re.findall(r'https?://collections\.tepapa\.govt\.nz/[Oo]bject/\d+',cs['evidence_note'])))
   holds.append(dict(artwork_id=a['id'],reason='Different historical import evidence shape or conflicting native references; separate object crosswalk required',source_urls=urls,images_requested=0))
 raw,prc=capture('tepapa-api-policy','https://www.tepapa.govt.nz/api-terms-of-use');pt=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
 assert '"No Known Copyright Restrictions" or "Creative Commons 0", you may use the media object as you choose' in pt
 save(E/'source-policy-verification.json',dict(at=h.now(),policy=prc,public_pages_used=True,api_keys_used=False,api_requests=0,statement='Record-specific NKCR media may be used as chosen under native accessRights policy. Exact source label retained; separate about-collections-online statement limits no-copyright assertion to New Zealand. Not converted to global public domain. Caption and official URL preserved.',rights_guide='source-captures/tepapa-rights.receipt.json',metadata_refresh_due='2026-11-08',metadata_scope='Immutable provenance captures; no public mirror of raw API data. Current-source metadata refresh due in four weeks.'))
 with connect() as db:
  for r in cross:
   a=r['artwork'];aid=a['id'];oid=r['native_id'];x=load(E/'object-research'/(oid+'.json'));raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes());assert h.sha(raw)==x['receipt']['sha256'];o=object_from_page(raw);ims=o.get('hasRepresentation',[])
   if not ims:holds.append(dict(artwork_id=aid,native_id=oid,reason='No source image supplied',images_requested=0));continue
   photo=ims[0]
   if photo['rights']['title']!='No Known Copyright Restrictions' or not photo['rights'].get('allowsDownload'):
    holds.append(dict(artwork_id=aid,native_id=oid,reason='No record-specific commercially reusable image rights',rights=photo['rights'],images_requested=0));continue
   if oid=='37972':
    holds.append(dict(artwork_id=aid,native_id=oid,reason='Current source measurements omit units (615 / 750); historical 61.5 / 75 cm crosswalk and source cropped photograph need separate physical composition review',images_requested=0));continue
   assert str(o['id'])==oid and o['identifier']==r['inventory'] and o['title']==a['title']
   prod=o['production'];assert len(prod)==1 and int(prod[0]['verbatimCreatedDate'])==a['creation_year_start']==a['creation_year_end']<=1955
   creator_variant=None
   if h.norm(prod[0]['contributor']['title'])!=h.norm(a['unlinked_creator_label']):
    assert oid=='1118264' and prod[0]['contributor']['title']=='Johannes Keulemans' and a['unlinked_creator_label']=='John Gerrard Keulemans'
    historical=json.loads(r['citation']['evidence_note'])['raw_source_record']['creators']['Q1335286'];ce=historical['entity'];crc=historical['receipt'];cr=gzip.decompress((ROOT/crc['body_path']).read_bytes());assert h.sha(cr)==crc['sha256'] and json.loads(cr)['entities']['Q1335286']==ce
    assert 'Johannes Keulemans' in [v['value'] for v in ce['aliases']['en']] and ce['labels']['en']['value']==a['unlinked_creator_label']
    for prop,key in [('P569','birthDate'),('P570','deathDate')]:assert ce['claims'][prop][0]['mainsnak']['datavalue']['value']['time'][1:11]==prod[0]['contributor'][key]
    creator_variant=dict(catalogue_label=a['unlinked_creator_label'],native_label=prod[0]['contributor']['title'],wikidata_id='Q1335286',same_explicit_alias=True,exact_birth_and_death_agree=True,source=historical)

   note=json.loads(r['citation']['evidence_note']);rc=note['source_receipt'];oldraw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(oldraw)==rc['sha256']
   ent=json.loads(oldraw)['entities'][r['wikidata_id']];assert ent==note['raw_source_record']['entity']
   dimensions=[]
   for prop,key in [('P2048','height'),('P2049','width')]:
    values=[v['mainsnak']['datavalue']['value'] for v in ent['claims'].get(prop,[])];dims=[v for v in o.get('observedDimension',[]) if v.get('extentType').lower() in ['image','support','sheet'] and key in v]
    if values and dims:
     val=values[0];assert val['unit'].endswith('/Q174728');d=dims[0];native=float(d[key])/(10 if d.get('sizeUnitText')=='mm' else 1);assert abs(native-float(val['amount']))<.11,(oid,key,native,val);dimensions.append(dict(field=key,source=d,wikidata_cm=val['amount']))
   global_ids=[dict(v) for v in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikidata' AND external_id=%s) OR (scheme ILIKE '%%tepapa%%' AND external_id=%s) OR canonical_url=ANY(%s))",(r['wikidata_id'],oid,['http://collections.tepapa.govt.nz/Object/'+oid,'https://collections.tepapa.govt.nz/object/'+oid]))];assert {v['entity_id'] for v in global_ids}=={aid}
   similar=[dict(v) for v in db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE current_institution_id=%s AND (lower(title)=lower(%s) OR accession_number=%s)",(MID,a['title'],r['inventory']))];assert [v['id'] for v in similar]==[aid] and similar[0]['primary_media_id'] is None
   assert o['collection']=='Art' and not any(k in o for k in ['culturalRights','culturalSensitivity','restriction'])
   sourceurl=x['receipt']['url'];assert photo['previewUrl']==BeautifulSoup(raw,'html.parser').select_one('meta[property="og:image"]')['content'];assert str(photo['id']) in photo['previewUrl'] and '/preview' in photo['previewUrl']
   ident=dict(artwork_id=aid,native_id=oid,wikidata_id=r['wikidata_id'],source_inventory=o['identifier'],source_title=o['title'],source_creator=prod[0]['contributor']['title'],source_production=prod,creator_variant=creator_variant,physical_dimensions=o.get('observedDimension',[]),checked_dimensions=dimensions,global_identifiers=global_ids,institution_title_inventory_matches=similar,historical_source_sha256=rc['sha256'],current_source_sha256=x['receipt']['sha256'],source_image_id=photo['id'],confidence=.99,confidence_basis='Exact referenced native object, registration number, unique Wikidata identity, creator, literal creation date and title; physical dimensions crosschecked where available. Editorial judgment, not calibrated probability.',current_display_claim=False)
   identities.append(ident)
   selected.append(dict(artwork_id=aid,native_id=r['wikidata_id'],current_source_id=oid,title=a['title'],creator_label=a['unlinked_creator_label'],source_url=sourceurl,accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='tepapa',image=dict(image_url=photo['previewUrl'],source=o,receipt=x['receipt']),plan_sha256=r['plan_sha256'],identity_citation=r['citation'],identity_reconciliation=ident,rights_status='restricted',rights_label=photo['rights']['title'],rights_basis='Exact native image has No Known Copyright Restrictions and Unrestricted/Downloadable flags. Native accessRights policy expressly permits use as chosen. Preserve separate New Zealand jurisdictional qualification, so catalogue rights remain restricted rather than asserting worldwide public domain. Object and photographic media rights checked separately; full source caption and individual credits retained. User production authorization is separate and not a copyright-holder licence.',manual_visual_required=True))
 assert selected
 save(E/'global-identity-reconciliation.json',dict(at=h.now(),records=identities));save(E/'research-holds.json',dict(at=h.now(),records=holds));save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='tepapa',batch=B,rows=selected,selection_basis='Existing exact-identity primary gaps; bounded native public pages. Explicit reusable NKCR media. No API key or paid service. Preview is native complete-image rendition, not detail or thumbnail.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())));print('Selected',len(selected),'Held',len(holds),flush=True);finish()
def finish():
 for row in i.selected(B)['rows']:print(row['current_source_id'],i.prepare_one(row,B)['state'],flush=True)
 i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)
old_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={load(p)['media_id']:selected[load(p)['artwork_id']] for p in (i.folder(B)/'prepared').glob('*.json') if load(p)['state']=='prepared'}
 if table=='media_assets':
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/tepapa'),i.OP+'-tepapa','Te Papa exact native object image evidence','https://collections.tepapa.govt.nz',i.OP))
  for row in rows:
   r=images[row['id']];o=r['image']['source'];photo=o['hasRepresentation'][0];credit=o['caption'];row['creator_credit']=credit;row['attribution_text']=credit+' '+photo['title']+'. '+r['rights_label']+' (source statement concerns New Zealand). Complete supplied composition retained; proportional resizing and JPEG compression.'
 if table=='media_rights_evidence':
  for row in rows:
   r=images[row['media_id']];ev=json.loads(row['evidence_json']);ev['identity_reconciliation']=r['identity_reconciliation'];ev['identity_citation']=r['identity_citation'];ev['source_policy']=load(E/'source-policy-verification.json');ev['actual_source_rights']=r['image']['source']['hasRepresentation'][0]['rights'];ev['user_authorization']=dict(production_image_attachment=True,copyright_holder_licence=False);row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return old_copy(db,table,rows)
i.n.copy_rows=copy_rows
def locked_identities(db,ids,rows):
 out={}
 for aid in ids:
  r=rows[aid];cs=r['identity_citation'];live=db.execute('SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE id=%s',(cs['id'],)).fetchone();assert dict(live)==cs
  native=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s",(r['native_id'],)).fetchall();assert [x['entity_id'] for x in native]==[aid];out[aid]=native[0]['external_id']
 return out
code=inspect.getsource(i.apply);old="native_ids={r['entity_id']:r['external_id'] for r in db.execute(\"SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme=%s\",(ids,cfg['scheme']))}"
assert old in code;i.locked_identities=locked_identities;exec(compile(code.replace(old,'native_ids=locked_identities(db,ids,rows)'),__file__,'exec'),i.__dict__)
def deliver():
 images,_,_=i.accepted(B)
 with connect() as db:
  states=h.snapshot(db,[v['artwork_id'] for v in images]);present=[v for v in images if states[v['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(states[v['artwork_id']]['artwork']['primary_media_id']==v['media_id'] for v in present)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Own transaction preimage required for recovery'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
def prepare_direct():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 parent=i.folder('tepapa-000')/'selection.json.gz';p=load(parent);rows=[]
 for row in p['rows']:
  diag=load(E/'media-response-diagnostics'/(row['current_source_id']+'.json'));assert diag['status']==303 and diag['url']==row['image']['image_url']
  photo=row['image']['source']['hasRepresentation'][0];assert diag['location']=='https://co3-api-mediastorage.s3.ap-southeast-2.amazonaws.com/'+str(photo['id'])+'/preview'
  row=dict(row,image=dict(row['image'],image_url=diag['location'],native_media_url=diag['url'],redirect_receipt=diag));rows.append(row)
 save(i.folder(B)/'selection.json.gz',dict(p,at=h.now(),batch=B,rows=rows,parent_selection_sha256=h.sha(parent.read_bytes()),selection_basis=p['selection_basis']+' Official HTTP 303 redirect followed to exact same media ID and preview rendition; no access restriction or endpoint bypass.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())));finish()
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
