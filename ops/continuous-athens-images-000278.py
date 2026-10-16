"""Bounded existing Athens image-gap continuation; immutable evidence and shared ingestion lock."""
import fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base278','continuous-image-batch-000002.py');h=base.h;i=base.i;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000278';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000278';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000278'
B='athens-278';MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';OP='continuous-athens-images-20261011-b000278'
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
POLICY='https://www.nationalgallery.gr/en/terms-of-use/'
i.CFG['athens']=dict(mid=MID,scheme='museum-native-nationalgallery-gr',name='National Gallery - Alexandros Soutsos Museum',rights='restricted',license='Museum copyright; no open image licence asserted',policy=POLICY,host='www.nationalgallery.gr')
old_uid=i.m.uid;i.m.uid=lambda k:i.uid(k) if k=='source/athens' else old_uid(k)
for p in [E,RUNTIME,S,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(key,url):
 dest=E/'source-captures'/(key+'.json');bp=S/(key+'.html')
 if dest.exists():
  rc=load(dest);raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds/www.nationalgallery.gr.json').exists()
 i.provider_slot('www.nationalgallery.gr');r=i.session().get(url,timeout=(15,45));bp.write_bytes(r.content)
 rc=dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=r.url,status=r.status_code,sha256=h.sha(r.content),body_path=str(bp),retry_after=r.headers.get('Retry-After'))
 save(dest,rc)
 if r.status_code in [401,403,429]:save(E/'access-holds/www.nationalgallery.gr.json',rc)
 return r.content,rc

def stage():
 if (E/'gap-input.json.gz').exists():return
 ids=load(E/'athens-live-image-gap-query.json')['eligible_known_dates']
 with connect() as db:
  states=h.snapshot(db,ids)
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  citations=[dict(x) for x in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  artists=[dict(x) for x in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,a.display_name,aa.attribution_role FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,))]
  save(E/'gap-input.json.gz',dict(at=h.now(),states=states,identifiers=identifiers,citations=citations,artists=artists))
  pages=load(E/'athens-page3-index.json')['results'];urls=[v['link'] for v in pages]
  matches=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.primary_media_id::text,c.source_url FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_url=ANY(%s) UNION SELECT a.id::text,a.title,a.primary_media_id::text,e.canonical_url FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.canonical_url=ANY(%s)",(urls,urls))]
  save(E/'athens-page3-existing-identity-verification.json',dict(at=h.now(),index_rows=len(pages),exact_url_matches=matches,not_imported_urls=[url for url in urls if url not in {v['source_url'] for v in matches}],scope='Index URL reconciliation only; unlinked leads require object-level date/inventory/version research. No image downloads from index thumbnails.'))
 print(json.dumps(dict(identifiers=identifiers,artists=artists,citations=[dict(x,evidence_note=x['evidence_note'][:1800]) for x in citations]),ensure_ascii=False))

def research():
 data=load(E/'gap-input.json.gz')
 for aid,state in data['states'].items():
  dest=E/'object-research'/(aid+'.json')
  if dest.exists():continue
  es=[v for v in data['identifiers'] if v['entity_id']==aid and v['canonical_url'] and 'nationalgallery.gr/en/artwork/' in v['canonical_url']]
  urls=set(v['canonical_url'] for v in es)
  if not urls:urls={v['source_url'] for v in data['citations'] if v['entity_id']==aid and v['source_url'] and '/en/artwork/' in v['source_url']}
  assert len(urls)==1,(aid,urls)
  url=next(iter(urls));raw,rc=capture(aid,url)
  if rc['status']!=200:save(dest,dict(artwork_id=aid,hold='HTTP '+str(rc['status']),receipt=rc));continue
  sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True) if head.span else '';head.span.extract() if head.span else None
  im=sp.select_one('.img-magnifier-container img');creator=sp.select_one('p.artist').get_text(' ',strip=True)
  out=dict(artwork_id=aid,receipt=rc,title=head.get_text(' ',strip=True).rstrip(',').strip(),date=date,accession_number=sp.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip(),creator_label=creator,description=sp.select_one('p.description').get_text(' ',strip=True),credit=sp.select_one('p.obtainment').get_text(' ',strip=True) if sp.select_one('p.obtainment') else '',image_url=(im.get('data-zoom-image') or im.get('src')) if im else None,image_alt=im.get('alt') if im else None,source_text=sp.get_text(' ',strip=True))
  save(dest,out);print(json.dumps({k:v for k,v in out.items() if k!='source_text'},ensure_ascii=False),flush=True)

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 data=load(E/'gap-input.json.gz');rows=[];checks=[]
 oldplan=E.parent/'000228/greek-aivazovsky-objects-v1/plan.json.gz';pin=h.sha(oldplan.read_bytes());plan=load(oldplan)
 with connect() as db:
  for aid,state in data['states'].items():
   a=state['artwork'];x=load(E/'object-research'/(aid+'.json'));cs=next(v for v in data['citations'] if v['entity_id']==aid);note=json.loads(cs['evidence_note']);native=next(v for v in data['identifiers'] if v['entity_id']==aid)
   assert not x.get('hold') and x['receipt']['status']==200
   assert x['title']==a['title']==note['title'] and x['accession_number']==a['accession_number']==note['accession_number']
   assert x['creator_label']==a['unlinked_creator_label']==note['creator_label']
   assert x['description']==a['medium_text']+', '+a['dimensions_text']==note['medium']+', '+note['dimensions']
   assert x['date']==a['date_display']==note['date_display'] and int(x['date'])==a['creation_year_start']==a['creation_year_end']<=1955
   assert x['image_url']==note['raw']['image_url'] and x['credit']==note['credit']
   assert note['plan_sha256']==pin and any(r['artwork_id']==aid for r in plan['records'])
   oldraw=Path(note['evidence_file']).read_bytes();assert h.sha(oldraw)==note['evidence']['sha256']
   raw=Path(x['receipt']['body_path']).read_bytes();assert h.sha(raw)==x['receipt']['sha256']
   hits=[dict(v) for v in db.execute("SELECT a.id::text FROM artworks a WHERE current_institution_id=%s AND accession_number=%s UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=%s AND external_id=%s) OR canonical_url=%s) UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(MID,a['accession_number'],native['scheme'],native['external_id'],native['canonical_url'],native['canonical_url']))]
   assert {v['id'] for v in hits}=={aid} and a['primary_media_id'] is None
   ident=dict(artwork_id=aid,inventory=a['accession_number'],native_id=native['external_id'],creator=x['creator_label'],date=x['date'],description=x['description'],credit=x['credit'],old_source_sha256=note['evidence']['sha256'],new_source_sha256=x['receipt']['sha256'],exact_global_matches=hits,metadata_plan_sha256=pin,existing_creator_label_preserved=True)
   checks.append(ident)
   rows.append(dict(artwork_id=aid,provider='athens',native_id=native['external_id'],title=a['title'],creator_label=x['creator_label'],source_url=native['canonical_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],plan_sha256=pin,image=dict(image_url=x['image_url'],source=x,receipt=x['receipt']),identity_citation=cs,identity_reconciliation=ident,rights_basis='Explicit Greek museum source extension for dated works through 1955. Museum copyright and lack of independent licence retained separately from user authorization.',manual_visual_required=True))
 save(E/'global-identity-reconciliation.json',dict(at=h.now(),records=checks))
 prior=E.parent/'000228/batch-verification-receipt.json'
 save(E/'date-hold-correction-verification.json',dict(at=h.now(),prior_receipt=str(prior),prior_sha256=h.sha(prior.read_bytes()),prior_reason=load(prior)['images_reason'],verified_years=sorted({r['last'] for r in rows}),cutoff=1955,all_years_at_or_before_cutoff=all(r['last']<=1955 for r in rows),correction='The prior statement that these 1856–1898 works postdate 1955 is an arithmetic error. Exact original and fresh museum notices agree. No date or source-policy change is required; only that erroneous date hold is resolved. Original receipt preserved.',source_access_holds_overridden=False))
 save(E/'authorization.json',dict(at=h.now(),operation=OP,production_images=True,source_policy='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',cutoff=1955,rights_status='restricted',copyright_holder_licence=False,local_catalogue_read_only=True,translation_prohibited=True))
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='athens',batch=B,rows=rows,selection_basis='Eight existing dated native Athens inventory gaps; exact original and live source identity. No catalogue metadata mutation.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()
def finish():
 (i.ORIG/B).mkdir(parents=True,exist_ok=True)
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 i.audit(B)
 for p in (i.folder(B)/'prepared').glob('*.json'):
  im=load(p);print(im['artwork_id'],im.get('path'),im.get('flags'),im.get('reason'),flush=True)

i.CFG['athens']['scheme']='continuous-athens-object'
old_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 if table=='media_assets':
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/athens'),OP+'-athens','National Gallery Athens exact object image evidence','https://www.nationalgallery.gr',OP))
  selection={r['artwork_id']:r for r in i.selected(B)['rows']};images={load(p)['media_id']:selection[load(p)['artwork_id']] for p in (i.folder(B)/'prepared').glob('*.json') if load(p)['state']=='prepared'}
  for row in rows:
   credit=images[row['id']]['image']['source']['credit'];row['creator_credit']+=' Source collection credit: '+credit+'.';row['attribution_text']+=' Source collection credit: '+credit+'.'
 if table=='media_rights_evidence':
  selection={r['native_id']:r for r in i.selected(B)['rows']}
  for row in rows:
   r=selection[row['source_record_id']];ev=json.loads(row['evidence_json']);ev['identity_citation']=r['identity_citation'];ev['identity_reconciliation']=r['identity_reconciliation'];ev['user_authorization']=load(E/'authorization.json');ev['date_hold_correction']=load(E/'date-hold-correction-verification.json');row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return old_copy(db,table,rows)
i.n.copy_rows=copy_rows
def locked_identities(db,ids,rows):
 out={}
 for aid in ids:
  r=rows[aid];cs=r['identity_citation'];live=db.execute('SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE id=%s',(cs['id'],)).fetchone();assert dict(live)==cs
  native=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='continuous-athens-object' AND external_id=%s",(r['native_id'],)).fetchall();assert [v['entity_id'] for v in native]==[aid];out[aid]=r['native_id']
 return out
code=inspect.getsource(i.apply);old="native_ids={r['entity_id']:r['external_id'] for r in db.execute(\"SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme=%s\",(ids,cfg['scheme']))}"
assert old in code;i.locked_identities=locked_identities
exec(compile(code.replace(old,'native_ids=locked_identities(db,ids,rows)').replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'"),__file__,'exec'),i.__dict__)
def deliver():
 images,_,_=i.accepted(B);assert 1<=len(images)<=100
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes()) and pre['visual_review_sha256']==h.sha((i.folder(B)/'visual-review.json').read_bytes())
 rc=load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 with connect() as db:
  states=h.snapshot(db,[im['artwork_id'] for im in images]);present=[im for im in images if states[im['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(states[im['artwork_id']]['artwork']['primary_media_id']==im['media_id'] for im in present)
   assert (i.BACKUP/B/'before-000.json.gz').exists()
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
