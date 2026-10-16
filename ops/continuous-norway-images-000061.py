#!/usr/bin/env python3
"""Bounded native Norwegian museum image continuation; no supervisor changes."""
import csv, fcntl, gzip, importlib.util, inspect, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base61n','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000061/norway'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000061'
B='norway-000';MID='5f550b6e-7d78-4fab-89f5-5f54a9bc1241'
i.OP='continuous-norway-images-20261011-b000061';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
POLICY='https://www.nasjonalmuseet.no/en/collection/about-the-collection/about-copyright/'
LICENSE='https://creativecommons.org/licenses/by/4.0/'
i.CFG['norway']=dict(mid=MID,scheme='nasjonalmuseet-object',name='Nasjonalmuseet / The National Museum, Oslo',rights='cc_by',license='CC BY 4.0',policy=LICENSE,host='ms01.nasjonalmuseet.no')
old_uid=i.m.uid;i.m.uid=lambda k:i.uid(k) if k=='source/norway' else old_uid(k)
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 assert __import__('os').environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(key,url):
 rp=E/'norway-source-captures'/(key+'.receipt.json');bp=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000061/norway'/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 host=urlsplit(url).hostname;hold=E/'access-holds'/(host+'.json');assert not hold.exists(),'Provider held'
 i.provider_slot(host);r=i.session().get(url,timeout=(15,45));raw=r.content
 bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=r.url,status=r.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(bp),retry_after=r.headers.get('Retry-After'))
 save(rp,rc)
 if r.status_code in [401,403,429]:save(hold,rc)
 return raw,rc
def stage():
 save(E/'production-target-before-research.json',target())
 if (E/'oslo-bounded-gap-input.json.gz').exists():return
 cursor=next(r for r in load(E.parents[2]/'source-queue.json')['sources'] if r['source_id']=='nasjonalmuseet_norway')['resume_cursor']['after_artwork_id']
 with connect() as db:
  institutions=[dict(r) for r in db.execute('SELECT id::text,name,slug FROM institutions WHERE id=ANY(%s::uuid[])',([MID,'f3ca11bf-84ce-5e7d-9a3a-fc52b57a353b'],))]
  rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,date_display,creation_year_start,creation_year_end,date_precision,work_type,unlinked_creator_label FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 AND id>%s::uuid ORDER BY id LIMIT 12",(MID,cursor))]
  ids=[r['id'] for r in rows]
  identifiers=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  citations=[dict(r) for r in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  artists=[dict(r) for r in db.execute("SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,aa.attribution_note,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE artwork_id=ANY(%s::uuid[])",(ids,))]
  counts=[dict(r) for r in db.execute("SELECT current_institution_id::text,count(*) total,count(*) FILTER (WHERE primary_media_id IS NULL AND creation_year_end<=1955) eligible_date_gaps FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id",([MID,'f3ca11bf-84ce-5e7d-9a3a-fc52b57a353b'],))]
  save(E/'oslo-bounded-gap-input.json.gz',dict(at=h.now(),after_artwork_id=cursor,rows=rows,identifiers=identifiers,citations=citations,artists=artists,states=h.snapshot(db,ids)))
  save(E/'norway-institution-reconciliation.json',dict(at=h.now(),institutions=institutions,counts=counts,decision='Legacy institution has 4 already illustrated works; main National Museum Oslo holds the active native object queue. Neither institution merged or changed.'))
 print(json.dumps(rows,ensure_ascii=False),flush=True)
def research():
 raw,rc=capture('norway-policy',POLICY);assert rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True)
 assert 'All works not labeled with copyright can be reproduced and published freely' in text
 links=[a['href'] for a in sp.select('a[href]') if 'creativecommons.org/licenses/by/' in a['href']];assert links
 save(E/'norway-policy.json',dict(at=h.now(),receipt=rc,license_links=links,text=text))
 data=load(E/'oslo-bounded-gap-input.json.gz')
 for a in data['rows']:
  aid=a['id'];dest=E/'object-research'/(aid+'.json')
  if dest.exists():continue
  native_links=[v['canonical_url'] for v in data['identifiers'] if v['entity_id']==aid and v['scheme']=='nasjonalmuseet-object' and v['canonical_url']]
  url=native_links[0] if len(native_links)==1 else 'https://www.nasjonalmuseet.no/en/collection/object/'+quote(a['accession_number'],safe='')
  assert urlsplit(url).hostname=='www.nasjonalmuseet.no'
  raw,rc=capture(aid,url)
  if rc['status']!=200:
   save(dest,dict(artwork=a,page_receipt=rc,hold='Native page HTTP '+str(rc['status'])))
   if rc['status'] in [401,403,429]:break
   continue
  sp=BeautifulSoup(raw,'html.parser');fields={}
  for dt in sp.select('.description-list dt'):
   dd=dt.find_next_sibling('dd')
   if dd:fields[dt.get_text(' ',strip=True).rstrip(':')]=dd.get_text(' ',strip=True)
  head=sp.select_one('.collection-object-header')
  out=dict(artwork=a,page_receipt=rc,fields=fields,title=head.select_one('h1').get_text(' ',strip=True) if head else None,creators=[a.get_text(' ',strip=True) for a in head.select('a[href*="/producer/"]')] if head else [],images=[dict(im.attrs) for im in sp.select('img')],page_text=sp.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in sp.select('a[href]') if any(x in a['href'].lower() for x in ['download','image','creativecommons'])])
  save(dest,out);print(json.dumps({k:out[k] for k in ['artwork','title','creators','fields','links']},ensure_ascii=False),flush=True)
def component(raw):
 text=raw.decode();needle='createSSRApp(Components.SiteLayout, '
 obj,_=json.JSONDecoder().raw_decode(text[text.index(needle)+len(needle):]);return obj['child']['component']
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 data=load(E/'oslo-bounded-gap-input.json.gz');chosen=[];held=[];identities=[];capture_cache={}
 with connect() as db:
  for a in data['rows']:
   aid=a['id'];x=load(E/'object-research'/(aid+'.json'))
   if x.get('hold'):held.append(dict(artwork_id=aid,reason=x['hold'],next_step='Use saved canonical underscore URL for inventory ampersand; a documented URL normalization, not an access restriction.'));continue
   raw=gzip.decompress((ROOT/x['page_receipt']['body_path']).read_bytes());assert h.sha(raw)==x['page_receipt']['sha256'];c=component(raw);media=c['collectionItemImageComponent']['media']
   if media['copyright']:held.append(dict(artwork_id=aid,reason='Object-specific copyright restriction',rights_label=media['copyright']));continue
   es=[v for v in data['identifiers'] if v['entity_id']==aid and v['scheme']=='nasjonalmuseet-object']
   cs=[v for v in data['citations'] if v['entity_id']==aid and '"source_scheme": "nasjonalmuseet-object"' in v['evidence_note']]
   if len(es)!=1 or len(cs)!=1:held.append(dict(artwork_id=aid,reason='Needs separate native identifier and historical title crosswalk reconciliation'));continue
   note=json.loads(cs[0]['evidence_note']);native=note['source_evidence'];assert es[0]['external_id']==note['external_id']==native['_id']
   oldrc=note['receipt'];path=ROOT/oldrc['body_path']
   if str(path) not in capture_cache:
    payload=gzip.decompress(path.read_bytes());assert h.sha(payload)==oldrc['sha256'];capture_cache[str(path)]=json.loads(b'{'+payload+b'}') if payload.startswith(b'"hits":') else json.loads(payload)
   source=capture_cache[str(path)];items=source['hits'] if isinstance(source,dict) else source
   if isinstance(items,dict):items=items['hits']
   assert native in items,'Historical source object not in checksum-verified export'
   assert media['nmId']==x['fields']['Inventory no.']==a['accession_number']==note['accession']==native['_source']['NmId']
   assert x['creators']==[note['creator_label']]==[media['producer']] and h.norm(a['unlinked_creator_label'])==h.norm(media['producer'])
   years=[int(y) for y in re.findall(r'\b[12]\d{3}\b',x['fields'].get('Creation date',''))];assert years and min(years)==a['creation_year_start'] and max(years)==a['creation_year_end']<=1955
   aliases=note['title_aliases'];translation=None
   if h.norm(x['title']) not in {h.norm(t) for t in aliases}:
    held.append(dict(artwork_id=aid,reason='New translated title requires individual reconciliation',source_title=x['title'],stored_aliases=aliases));continue
   dims=native['_source']['MetaData']['Dimensions'];physical={v['DimensionsType']:v for v in dims if v.get('DimensionsCategory')=='Hovedmål' and v.get('DimSizeUnit') in ['cm','mm']}
   def number(v):return float(str(v).replace(',','.'))
   for sourcekey,currentkey in [('Høyde','Height'),('Bredde','Width')]:
    if sourcekey in physical:
     v=physical[sourcekey];mt=re.search(currentkey+r':\s*([\d.,]+)\s*'+v['DimSizeUnit'],x['fields']['Dimensions']);assert mt and number(mt.group(1))==number(v['DimensionNum'])
   im=media['images'][0];assert not any(im[k] for k in ['panorama','is360','isGigapixel']);assert im['photocredit']
   sp=BeautifulSoup(raw,'html.parser');url=sp.select_one('meta[property="og:image"]')['content'];assert url==media['iiifImageUrlTemplate'].format(im['originalFile'],'1200','')
   assert '/full/' in url and urlsplit(url).hostname=='ms01.nasjonalmuseet.no'
   live=[dict(v) for v in db.execute('SELECT id::text,title,accession_number,primary_media_id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND accession_number=%s',([MID,'f3ca11bf-84ce-5e7d-9a3a-fc52b57a353b'],a['accession_number']))];assert [v['id'] for v in live]==[aid] and live[0]['primary_media_id'] is None
   global_ids=[dict(v) for v in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=%s AND external_id=%s) OR canonical_url=%s)",('nasjonalmuseet-object',es[0]['external_id'],es[0]['canonical_url']))];assert {v['entity_id'] for v in global_ids}=={aid}
   ident=dict(artwork_id=aid,inventory=a['accession_number'],source_id=es[0]['external_id'],global_identifiers=global_ids,inventory_matches=live,source_title=x['title'],catalogue_title=a['title'],title_aliases=aliases,translation=translation,creator=media['producer'],creation_date=x['fields']['Creation date'],physical_dimensions=x['fields']['Dimensions'],historical_source_sha256=oldrc['sha256'],current_source_sha256=x['page_receipt']['sha256'],original_image_file=im['originalFile'],photographer_credit=im['photocredit'],copyright_label=media['copyright'])
   identities.append(ident)
   chosen.append(dict(artwork_id=aid,native_id=es[0]['external_id'],title=a['title'],creator_label=media['producer'],source_title=x['title'],source_url=x['page_receipt']['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='norway',image=dict(image_url=url,source=media,receipt=x['page_receipt']),plan_sha256=note['plan_sha256'],identity_citation=cs[0],identity_reconciliation=ident,rights_status='cc_by',rights_label='CC BY 4.0 — Nasjonalmuseet photographic licence; no object copyright restriction',rights_basis='Current official museum policy expressly allows commercial reuse under CC BY 4.0 for works without copyright labels. Exact native object media has an empty copyright restriction; photograph credit preserved. User production approval separately recorded and is not a copyright-holder licence.',photographer_credit=im['photocredit'],manual_visual_required=True))
 assert chosen
 save(E/'global-identity-reconciliation.json',dict(at=h.now(),records=identities,exact_native_identity_and_inventory=True))
 save(E/'research-holds.json',dict(at=h.now(),records=held))
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='norway',batch=B,rows=chosen,selection_basis='Bounded existing gaps with exact native inventories, creator/date/dimension and source title crosswalks. First native full-object photograph with no copyright label; explicit CC BY policy. Images selected before download.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 print('Selected',len(chosen),'Held',len(held),flush=True);finish()
def finish():
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)
old_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={load(p)['media_id']:selected[load(p)['artwork_id']] for p in (i.folder(B)/'prepared').glob('*.json') if load(p)['state']=='prepared'}
 if table=='media_assets':
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/norway'),i.OP+'-norway','Nasjonalmuseet selected exact object image evidence','https://www.nasjonalmuseet.no',i.OP))
  for row in rows:
   r=images[row['id']];credit=r['creator_label']+', '+r['source_title']+'. Photo: '+ '; '.join(r['photographer_credit'])+' / The National Museum. CC BY 4.0.';row['creator_credit']=credit;row['attribution_text']=credit+' Complete supplied composition retained; proportional resizing and JPEG compression.'
 if table=='media_rights_evidence':
  for row in rows:
   r=images[row['media_id']];ev=json.loads(row['evidence_json']);ev['identity_reconciliation']=r['identity_reconciliation'];ev['identity_citation']=r['identity_citation'];ev['source_policy']=load(E/'norway-policy.json');ev['user_authorization']=dict(production_image_attachment=True,copyright_holder_licence=False);row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return old_copy(db,table,rows)
i.n.copy_rows=copy_rows
def locked_identities(db,ids,rows):
 out={}
 for aid in ids:
  r=rows[aid];cs=r['identity_citation'];live=db.execute('SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE id=%s',(cs['id'],)).fetchone();assert dict(live)==cs
  native=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='nasjonalmuseet-object' AND external_id=%s",(r['native_id'],)).fetchall();assert [x['entity_id'] for x in native]==[aid];out[aid]=native[0]['external_id']
 return out
code=inspect.getsource(i.apply);old="native_ids={r['entity_id']:r['external_id'] for r in db.execute(\"SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme=%s\",(ids,cfg['scheme']))}"
assert old in code;i.locked_identities=locked_identities;exec(compile(code.replace(old,'native_ids=locked_identities(db,ids,rows)'),__file__,'exec'),i.__dict__)
def deliver():
 images,_,_=i.accepted(B)
 assert 1<=len(images)<=100
 pre=load(E/'independent-prewrite-verification.json')
 assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 assert pre['visual_review_sha256']==h.sha((i.folder(B)/'visual-review.json').read_bytes())
 with connect() as db:
  states=h.snapshot(db,[v['artwork_id'] for v in images]);present=[v for v in images if states[v['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(states[v['artwork_id']]['artwork']['primary_media_id']==v['media_id'] for v in present)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Own transaction preimage required for recovery'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
