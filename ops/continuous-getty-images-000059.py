#!/usr/bin/env python3
"""One bounded existing-image-gap batch; external continuation is left untouched."""
import csv, fcntl, gzip, importlib.util, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('base59', ROOT/'ops/continuous-image-batch-000002.py')
base = importlib.util.module_from_spec(s); s.loader.exec_module(base)
i=base.i; h=base.h; connect=base.connect; load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000059/getty'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000059'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000059'
B='getty-059'; MID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c'
API='https://data.getty.edu/museum/collection/'
LOCAL='https://data.getty.edu/local/thesaurus/'; AAT='http://vocab.getty.edu/aat/'
CC0='http://creativecommons.org/publicdomain/zero/1.0/'
i.OP='continuous-getty-images-20261011-b000059'; i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['getty']=dict(mid=MID,scheme='getty-object',name='J. Paul Getty Museum',rights='cc0',license='CC0 1.0 Universal — Getty Open Content',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='media.getty.edu')
for p in [E,RUNTIME,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)

def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v

def target(write=False):
 assert __import__('os').environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519','Unexpected helper proxy port'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)

def capture(key,url):
 dest=E/'source-captures'/(key+'.receipt.json'); bodypath=DATA/(key+'.body.gz')
 if dest.exists():return load(dest)
 host=urlsplit(url).hostname
 assert not (E/'access-holds'/(host+'.json')).exists(),'Source access held'
 i.provider_slot(host)
 r=i.session().get(url,timeout=(15,60));raw=r.content
 bodypath.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),url=url,final_url=r.url,status=r.status_code,sha256=h.sha(raw),body_path=str(bodypath),retry_after=r.headers.get('Retry-After'))
 save(dest,rc)
 if r.status_code in [401,403,429]:save(E/'access-holds'/(host+'.json'),rc)
 return rc

def body(rc):
 raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return raw

def contents(rows,typ):
 return list(dict.fromkeys(v['content'] for v in rows if any(t.get('id')==typ for t in v.get('classified_as',[])) and v.get('content')))

def preflight():
 save(E/'production-target-reconciliation.json',target())
 q=load(E.parent/'source-queue-before.json');save(E/'source-queue-before.json',q)
 registry_path=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(registry_path.open()));assert len(registry)==111
 save(E/'source-register.json',dict(at=h.now(),route=next(r for r in registry if r['source_id']=='getty_museum'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',image_rule='Exact native image explicitly CC0; no metadata-licence substitution',source_registry_path=str(registry_path),registry_sha256=h.sha(registry_path.read_bytes())))
 save(E/'source-access-holds.json',dict(at=h.now(),getty_access_hold_found=False,inherited_queue=str(E.parent/'source-queue-before.json'),object_holds=['da597b1b-0239-59a6-ae00-61a7b3099dba','e46e122e-af07-5bdd-ad57-dba58e354e57'],held_provider_requests=0))
 stops=list((ROOT/'docs/research/illustrated-300k-20261011').glob('stop*.json'))+[ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json']
 save(E/'completed-campaign-stop-preservation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in stops],separate_campaign=i.OP,restarted=False))
 with connect() as db:
  own=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Own interrupted write needs pinned-plan reconciliation'
  save(E/'own-prior-write-reconciliation.json',dict(at=h.now(),rows=own,earlier_increments=0))
  if not (E/'bounded-gap-input.json.gz').exists():
   rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,date_display,work_type,unlinked_creator_label FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 AND work_type='painting' AND accession_number IS NOT NULL AND id>'ea1f74c8-1d54-5aba-94bf-1826c31214d2'::uuid ORDER BY id LIMIT 16",(MID,))]
   ids=[r['id'] for r in rows]
   notes=[dict(r) for r in db.execute("SELECT entity_id::text,source_id::text,source_url,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
   ext=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
   save(E/'bounded-gap-input.json.gz',dict(at=h.now(),rows=rows,before=h.snapshot(db,ids),citations=notes,identifiers=ext))
 print('Prior batch reconciled; bounded Getty painting gaps:',len(load(E/'bounded-gap-input.json.gz')['rows']),flush=True)

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 data=load(E/'bounded-gap-input.json.gz');chosen=[];checks=[]
 with connect() as db:
  states=h.snapshot(db,[r['id'] for r in data['rows']])
  for a in data['rows']:
   aid=a['id']; reason=None;rc=None
   try:
    assert states[aid]==data['before'][aid],'Catalogue changed since gap snapshot'
    ns=[r for r in data['citations'] if r['entity_id']==aid and r['field_name'] in ['museum_expansion_primary_metadata','museum_primary_metadata_and_holding']];assert len(ns)==1,'Missing exact original source metadata'
    note=json.loads(ns[0]['evidence_note']);old=note['raw_source_record'];original=old['api_object'];oldn=old['native_fields']['object'];oid=original['id'];slug=old['native_fields']['identity']['slug']
    ex=[r for r in data['identifiers'] if r['entity_id']==aid and r['scheme']=='getty-object'];assert len(ex)==1 and API+ex[0]['external_id']==oid
    globalids=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme LIKE '%%getty%%' AND external_id=ANY(%s)",([ex[0]['external_id'],oid,oid.rsplit('/',1)[-1],slug],))]
    assert {r['entity_id'] for r in globalids}=={aid},'Global source identity conflict'
    acc=[dict(r) for r in db.execute('SELECT id::text,title FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(MID,a['accession_number']))];assert [r['id'] for r in acc]==[aid],'Duplicate museum inventory'
    arc=capture(slug+'-api',oid);assert arc['status']==200,'Native API unavailable'
    obj=json.loads(body(arc));rc=capture(slug+'-native',oldn['url']);assert rc['status']==200,'Native object unavailable'
    soup=BeautifulSoup(body(rc),'html.parser');n=json.loads(soup.select_one('script[type="application/ld+json"]').get_text());identity=json.loads(soup.select_one('script#local_id_manager').get_text())
    assert obj['id']==oid and identity==old['native_fields']['identity']
    assert n['name']==a['title']==oldn['name'];assert contents(obj['identified_by'],LOCAL+'object-title-primary')==[a['title']]
    assert contents(obj['identified_by'],AAT+'300312355')==[a['accession_number']] and n['identifier']==oldn['identifier']
    assert LOCAL+'object-record-structure-whole' in {v['id'] for v in obj['classified_as']} and not obj.get('part_of')
    for k in ['creator','temporal','material','size']:assert n.get(k)==oldn.get(k),'Source field changed: '+k
    for k in ['produced_by','current_owner','current_keeper','dimension']:assert obj.get(k)==original.get(k),'Native physical/creator/provenance changed: '+k
    span=obj['produced_by']['timespan'];lo=int(span['begin_of_the_begin'][:4]);hi=int(span['end_of_the_end'][:4]);assert hi<=1955
    assert lo<=a['creation_year_start']<=a['creation_year_end']<=hi,'Catalogue creation outside native range'
    assert n.get('license')==CC0,'Exact native image lacks CC0 label'
    thumb=n.get('thumbnailUrl','');assert re.fullmatch(r'https://media\.getty\.edu/iiif/image/[0-9a-f-]+/full/!300,300/0/default\.jpg',thumb),'No exact full-composition native image'
    reps=[v for v in obj.get('representation',[]) if v['id'].split('/full/')[0]==thumb.split('/full/')[0]];assert len(reps)==1 and reps[0]['_label'].startswith(('Main View Image','Object Overall Image')),'Native image not designated main/overall view'
    asset=contents(reps[0]['identified_by'],LOCAL+'asset-identifier');assert len(asset)==1
    mediarefs=[v for v in obj.get('shows',[]) if contents(v.get('identified_by',[]),LOCAL+'asset-identifier')==asset];assert len(mediarefs)==1
    mrc=capture(slug+'-image-rights',mediarefs[0]['id']);assert mrc['status']==200,'Native digital-object rights unavailable'
    media=json.loads(body(mrc));assert media['id']==mediarefs[0]['id']
    rights={v['id'] for t in media.get('subject_to',[]) for v in t.get('classified_as',[])}
    assert CC0 in rights and LOCAL+'clearance/download' in rights,'Exact digital object lacks CC0/download clearance'
    dob=[v for v in media.get('digitally_shown_by',[]) if any(ap['id']==thumb.split('/full/')[0] for ap in v.get('access_point',[]))];assert len(dob)==1
    source=dict(native=n,api=obj,identity=identity,api_receipt=arc,main_view=reps[0],digital_object=media,digital_object_receipt=mrc,original_source_plan_sha256=note['plan_sha256'])
    p=E/'selected-source-records-final'/(slug+'.json');save(p,source)
    chosen.append(dict(artwork_id=aid,native_id=ex[0]['external_id'],current_source_id=slug,title=a['title'],creator_label=a['unlinked_creator_label'],source_url=n['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='getty',source_id=ns[0]['source_id'],image=dict(image_url=thumb.replace('/full/!300,300/','/full/!1200,1200/'),source=source,receipt=rc),plan_path=str(p),plan_sha256=h.sha(p.read_bytes()),rights_basis='Exact native object JSON-LD explicitly labels the selected main-view reproduction CC0. API asset UUID agrees. Metadata CC0 is not used as an image licence. Native credits retained, no current-display assertion.',manual_visual_required=True))
   except (AssertionError,KeyError,TypeError,ValueError) as exc:reason=type(exc).__name__+': '+str(exc)
   checks.append(dict(artwork_id=aid,title=a['title'],outcome=reason or 'selected_exact_native_main_view',source_receipt=rc))
   print(a['accession_number'],checks[-1]['outcome'],flush=True)
 save(E/'global-identity-reconciliation-final.json',dict(at=h.now(),records=checks,selected=len(chosen),all_existing_records=True))
 save(E/'research-holds-final.json',dict(at=h.now(),records=[r for r in checks if r['outcome']!='selected_exact_native_main_view']))
 assert chosen,'No eligible native main views'
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='getty',batch=B,rows=chosen,selection_basis='Bounded existing Getty painting gaps with globally unique native inventory, exact current creator/date/dimensions/provenance, native main-view identity and per-image CC0.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()

def finish():
 for r in i.selected(B)['rows']:
  prior=E/'superseded-preparation/getty-047/prepared'/(r['artwork_id']+'.json')
  if prior.exists():
   im=load(prior);assert im['source_image_url']==r['image']['image_url'] and h.sha(Path(im['path']).read_bytes())==im['sha256'];save(i.folder(B)/'prepared'/prior.name,im)
  print(r['current_source_id'],i.prepare_one(r,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True)
 i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)

original_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={im['media_id']:im for im in i.accepted(B)[0]}
 for row in rows:
  if table not in ['media_assets','media_rights_evidence']:continue
  im=images[row['id'] if table=='media_assets' else row['media_id']];r=selected[im['artwork_id']];n=r['image']['source']['native']
  if table=='media_rights_evidence':
   row['source_id']=r['source_id'];ev=json.loads(row['evidence_json']);ev['actual_image_rights']=dict(license=n['license'],creditText=n.get('creditText'));ev['user_approval']='Production enrichment authorized; native CC0 label retained, not replaced by user permission';row['evidence_json']=json.dumps(ev,ensure_ascii=False)
  else:
   credit=r['creator_label']+'. J. Paul Getty Museum. '+BeautifulSoup(' '.join(n.get('creditText',[])),'html.parser').get_text(' ',strip=True)
   row['creator_credit']=credit;row['attribution_text']=credit+' Full supplied main-view composition; proportional resizing and JPEG compression.'
 return original_copy(db,table,rows)
i.n.copy_rows=copy_rows

def deliver():
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes());assert pre['visual_review_sha256']==h.sha((i.folder(B)/'visual-review.json').read_bytes())
 images,_,_=i.accepted(B);ids=[r['artwork_id'] for r in images];assert 1<=len(ids)<=100
 with connect() as db:
  states=h.snapshot(db,ids);present=[r for r in images if states[r['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(states[r['artwork_id']]['artwork']['primary_media_id']==r['media_id'] for r in images),'Concurrent primary: replan required'
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Own locked preimages required'
   evs=[dict(r) for r in db.execute('SELECT e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
   pin=load(i.folder(B)/'pin.json')['sha256']
   assert len(evs)==len(ids)
   for r in evs:
    ev=json.loads(r['evidence_json']) if isinstance(r['evidence_json'],str) else r['evidence_json'];assert r['adapter_version']==i.OP and ev['selection_sha256']==pin
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)

if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
