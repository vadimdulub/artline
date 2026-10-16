#!/usr/bin/env python3
"""One bounded image-gap batch; external supervisor and historical plans untouched."""
import csv, fcntl, gzip, importlib.util, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=mod('national30','continuous-nationalmuseum-images-000030.py');i=n.i;h=n.h;base=n.b.base
OLD=n.E;E=OLD.parent/'000031';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000031';B=sys.argv[2] if __name__=='__main__' and len(sys.argv)>2 else 'nationalmuseum-000'
i.OP='continuous-nationalmuseum-images-20261011-b000031';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 if p.exists():return h.load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(name,url,method='GET'):
 rp=E/'source-captures'/(name+'.receipt.json');bp=rp.with_name(name+'.body.gz');host=urlsplit(url).hostname
 if rp.exists():
  rc=h.load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds'/(host+'.json')).exists(),'Access held'
 i.provider_slot(host)
 resp=i.session().request(method,url,timeout=(15,45),allow_redirects=False);raw=resp.content
 bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),method=method,operation='read-only public source retrieval',url=url,status=resp.status_code,sha256=h.sha(raw),body_path=str(bp.relative_to(ROOT)),retry_after=resp.headers.get('Retry-After'))
 h.save(rp,rc)
 if resp.status_code in [401,403,429]:save(E/'access-holds'/(host+'.json'),rc)
 assert resp.status_code==200,(name,resp.status_code)
 return raw,rc
def reconcile():
 save(E/'production-target-reconciliation.json',target())
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),registry_records=111,complete_registry=reg,precedence='Current bounded production authorization; local catalogue read-only; external supervisor unchanged.'))
 save(E/'source-register.json',dict(at=h.now(),registry_sha256=h.sha(regpath.read_bytes()),sources=[r for r in reg if r['source_id'] in ['yale_lux','nationalmuseum_sweden']],policy='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',source_rule='Selected media must individually state Public Domain; retain photographer credit. Public media portal distinct from held direct image host.'))
 save(E/'source-access-holds.json',h.load(OLD/'source-access-holds.json'))
 planpath=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=h.load(planpath);rows=plan['rows'];assert len(rows)==188
 original=h.load(ROOT/'docs/research/french-printmaking-20261011/delivery-plan.json.gz');top=h.load(ROOT/'docs/research/french-printmaking-20261011/scope-topup/delivery-plan.json.gz');assert {r['artwork_id'] for r in rows}==set(original['eligible_reserve'])-{r['artwork_id'] for r in top['rows']}
 with h.connect() as db:
  live=h.snapshot(db,[r['artwork_id'] for r in rows]);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(list(live),))]
  assert len(live)==len(cit)==188
  for r in rows:
   a=live[r['artwork_id']]['artwork'];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==plan['images'][r['artwork_id']]['media_id'];assert a['status']!='archived'
  assert all(x['plan_sha256']==h.sha(planpath.read_bytes()) for x in cit)
  previous=h.load(OLD/'combined-batch-verification-receipt.json');ids=previous['production_ids'];prior=h.snapshot(db,ids);assert len(prior)==10
  known=previous['newly_illustrated_ids'][0];assert prior[known]['artwork']['primary_media_id']
  current=list(db.execute('SELECT media_id::text FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,)))
  assert not current or (i.folder(B)/'selection.json.gz').exists(),'Uncertain existing writes; reconcile pinned selection'
 save(E/'french-reserve-live-reconciliation.json',dict(at=h.now(),reserve_inspected=188,already_imported_and_illustrated=188,unimported=0,new_programme_increments=0,plan_path=str(planpath.relative_to(ROOT)),plan_sha256=h.sha(planpath.read_bytes()),source_citations=cit,live_rows=live,prior_actual_visual_review='docs/research/printmaking-continuation-20261011/french-reserve/; immutable checksum-bound visual evidence unchanged; none selected or replayed',next_action='Switch to Nationalmuseum exact-image gaps. Three physical-date holds unchanged.'))
 save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=30,live_rows=prior,prior_receipt_sha256=h.sha((OLD/'combined-batch-verification-receipt.json').read_bytes()),previous_new_works_not_counted=True,current_batch_rights_rows=len(current)))
def discover():
 reconcile()
 if (E/'media-discovery.json').exists():return
 capture('official-image-policy','https://www.nationalmuseum.se/en/explore-art-and-design/images')
 oldplan,pin=h.pinned(n.b.PHASE);pending=h.load(OLD/'CHECKPOINT.json')['resume_cursor']['image_pending_native_ids'];results=[]
 for r in oldplan['records']:
  oid=r['source_id']
  if oid not in pending:continue
  raw,rc=capture('object-'+oid,r['source_url']);o=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];assert o==h.load(OLD/'objects'/(oid+'.json')),'Object metadata changed'
  url='https://media.nationalmuseum.se/api/v1/search/category/2?'+urlencode(dict(search=r['accession_number'],offset=0,limit=10))
  raw,searchrc=capture('search-'+oid,url,'POST');search=json.loads(raw);items=[]
  for lead in search['data']:
   mid=lead['id'];raw,mrc=capture('media-'+str(mid),'https://media.nationalmuseum.se/api/v1/media/'+str(mid));m=json.loads(raw);p=m['properties'];value=lambda k:p.get(k,{}).get('value')
   exact=value('inventarienummer')==[r['accession_number']] and value('titel_en')==[r['title']] and value('titel')==[o['ObjTitleMainTxt_sv']] and value('konstnar')==['Okänd']
   items.append(dict(media_id=mid,inventory=value('inventarienummer'),title=value('titel_en'),maker=value('konstnar'),rights=value('licens'),credit=value('photocreditline'),filename=m['filename'],exact_identity=exact,source_sha256=mrc['sha256'],downloadables=m['downloadables']))
  results.append(dict(native_id=oid,artwork_id=r['artwork_id'],inventory=r['accession_number'],title=r['title'],total_records=search['meta']['totalRecords'],limit=10,offset=0,items=items))
  print(oid,r['accession_number'],[(x['media_id'],x['exact_identity'],x['rights'],x['filename']) for x in items],flush=True)
 save(E/'media-discovery.json',dict(at=h.now(),records=results,prior_metadata_plan_sha256=pin,unselected_images_downloaded=0))
def prepare():
 if not (i.folder(B)/'selection.json.gz').exists():
  policy,prc=capture('rights-and-reproductions','https://www.nationalmuseum.se/en/explore-art-and-design/images/rights-and-reproductions')
  assert b'https://creativecommons.org/licenses/by-sa/4.0/' in policy
  discovery=h.load(E/('media-discovery-refined.json' if (E/'media-discovery-refined.json').exists() else 'media-discovery.json'));plan,pin=h.pinned(n.b.PHASE);byid={r['source_id']:r for r in plan['records']};chosen=[];holds=[]
  with h.connect() as db:
   before=h.snapshot(db,[x['artwork_id'] for x in discovery['records']]);save(E/'preparation-production-snapshot.json.gz',before)
  for x in discovery['records']:
   matches=[v for v in x['items'] if v['exact_identity'] and v['rights'] in ['Public Domain','CC BY-SA'] and v['credit']]
   public=[v for v in matches if v['rights']=='Public Domain']
   if len(public)==1:matches=public
   if len(matches)!=1:holds.append(dict(native_id=x['native_id'],reason='Requires individual review: '+str(len(matches))+' exact public-domain media items'));continue
   v=matches[0];r=byid[x['native_id']];a=before[r['artwork_id']]['artwork']
   if a['primary_media_id']:holds.append(dict(native_id=x['native_id'],reason='Already illustrated by another transaction'));continue
   assert a['title']==r['title'] and a['accession_number']==r['accession_number'] and a['status']!='archived'
   raw,rc=capture('media-'+str(v['media_id']),'https://media.nationalmuseum.se/api/v1/media/'+str(v['media_id']));m=json.loads(raw)
   full=[z for z in m['downloadables'] if z['templateName']=='Full JPEG'];assert len(full)==1
   chosen.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type='painting',provider='nationalmuseum',image=dict(image_url='https://media.nationalmuseum.se'+full[0]['url'],source=m,receipt=rc),plan_sha256=pin,source_credit=v['credit'],manual_visual_required=True,rights_basis='Exact official public media portal record independently matches inventory, both museum titles and Unknown maker; reproduction is explicitly Public Domain with original photographer credit. Complete composition subject to actual visual review. Direct collection-host image access hold preserved.'))
   chosen[-1].update(rights_label=v['rights'],rights_status='public_domain' if v['rights']=='Public Domain' else 'cc_by_sa',license_url='https://creativecommons.org/publicdomain/mark/1.0/' if v['rights']=='Public Domain' else 'https://creativecommons.org/licenses/by-sa/4.0/',rights_policy_receipt=prc)
   chosen[-1]['rights_basis']='Exact official public media portal inventory, both titles and maker agree. Actual image label: '+v['rights']+'. Nationalmuseum rights policy explicitly maps CC BY-SA images to version 4.0. Photographer credit, source URL, licence link and change notice preserved; CC BY-SA derivatives distributed under the same licence without additional restrictions. Direct collection image hold preserved.'
  save(E/'selection-holds.json',dict(at=h.now(),holds=holds))
  assert chosen,'No uniquely matched images; review metadata outcomes before proceeding'
  save(i.folder(B)/'selection.json.gz',dict(provider='nationalmuseum',batch=B,rows=chosen,metadata_first=True));save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r in i.selected(B)['rows']:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',h.load(p)['path'])
def prepare_renditions():
 assert B=='nationalmuseum-small-001'
 if not (i.folder(B)/'selection.json.gz').exists():
  old=i.selected('nationalmuseum-000');rows=[]
  for r in old['rows']:
   im=h.load(i.folder('nationalmuseum-000')/'prepared'/(r['artwork_id']+'.json'))
   if im['state']!='held':continue
   assert r['native_id'] in ['26564','26589'] and im['reason'].startswith('AssertionError')
   small=next(x for x in r['image']['source']['downloadables'] if x['templateName']=='Small_Powerpoint_web')
   rows.append(dict(r,image=dict(r['image'],image_url='https://media.nationalmuseum.se'+small['url']),rendition_note='Official complete-frame small web rendition selected after full JPEG exceeded configured 12-megapixel decoding ceiling. Original immutable plan and failed attempt preserved; same source image and composition.'))
  assert len(rows)==2
  save(i.folder(B)/'selection.json.gz',dict(provider='nationalmuseum',batch=B,rows=rows,metadata_first=True,parent_selection_sha256=h.sha((i.folder('nationalmuseum-000')/'selection.json.gz').read_bytes())))
  save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r in i.selected(B)['rows']:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',h.load(p)['path'])
original_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 if table in ['media_assets','media_rights_evidence']:
  selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={im['media_id']:im for im in i.accepted(B)[0]}
  for row in rows:
   im=images[row['id'] if table=='media_assets' else row['media_id']];r=selected[im['artwork_id']]
   if table=='media_assets':
    row['license_url']=r['license_url']
    if r['rights_label']=='CC BY-SA':row['attribution_text']+=' Derivative distributed under CC BY-SA 4.0; no additional restrictions.'
   else:
    row['policy_url']=r['license_url'];ev=json.loads(row['evidence_json']);ev['rights_policy_receipt']=r['rights_policy_receipt'];ev['actual_rights_label']=r['rights_label'];ev['user_approval_separate_from_source_licence']=True;row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return original_copy(db,table,rows)
i.n.copy_rows=copy_rows
def deliver():
 images,_,_=i.accepted(B);ids=[x['artwork_id'] for x in images]
 with h.connect() as db:
  state=h.snapshot(db,ids);present=[x for x in images if state[x['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(state[x['artwork_id']]['artwork']['primary_media_id']==x['media_id'] for x in images)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Locked preimage required to attribute recovered writes'
   print('Own media already committed; no writes replayed. Run independent verification.');return
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/(B+'-target-before-storage-write.json'),target(True));i.upload(B)
 save(E/(B+'-target-before-database-write.json'),target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
