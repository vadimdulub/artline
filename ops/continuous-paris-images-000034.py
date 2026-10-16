#!/usr/bin/env python3
"""One bounded Paris Musees image batch; external supervisor remains untouched."""
import csv, fcntl, gzip, importlib.util, inspect, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base34','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000034'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000034'
B='paris-000';MID='089556c5-0f7d-5ac4-8734-0471ae418da4'
i.OP='continuous-primary-images-20261011-b000034';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
i.CFG['paris']=dict(mid=MID,scheme='joconde-object',name='Paris Musées / Musée Carnavalet - Histoire de Paris',rights='cc0',license='CC0 1.0',policy=CC0,host='apicollections.parismusees.paris.fr')
old_uid=i.m.uid;i.m.uid=lambda k:i.uid(k) if k=='source/paris' else old_uid(k)
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
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
 host=urlsplit(url).hostname;hold=E/'access-holds'/(host+'.json');assert not hold.exists(),'Provider access held'
 i.provider_slot(host);r=i.session().get(url,timeout=(15,45));raw=r.content
 bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=r.url,status=r.status_code,sha256=h.sha(raw),bytes=len(raw),body_path=str(bp.relative_to(ROOT)),retry_after=r.headers.get('Retry-After'))
 save(rp,rc)
 if r.status_code in [401,403,429]:save(hold,rc)
 return raw,rc
def reconcile():
 save(E/'production-target-reconciliation.json',target())
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=x,sha256=h.sha((ROOT/x).read_bytes())) for x in required],original_registry=dict(path=str(regpath),sha256=h.sha(regpath.read_bytes()),rows=reg),precedence='Current production authorization supersedes historical local-mutation instructions. Real local catalogue read-only. Original 111-source CSV is authoritative registry; supplementary JSON is not substituted.'))
 q=load(E.parents[1]/'source-queue.json');save(E/'source-queue-before.json',q)
 save(E/'source-access-holds.json',dict(at=h.now(),inherited=[r for r in q['sources'] if 'hold' in r['status'] or '403' in r['status']],previous_ledger='docs/research/continuous-production-20261011/batches/000033/source-access-holds.json',paris_ledger_search='No Paris Musees provider hold found in repository hold ledgers. GraphQL token-required API is not used; documented public IIIF route only.'))
 if not (E/'french-reserve-live-reconciliation.json').exists():
  d=mod('french34','french-printmaking-delivery-20261011.py');main=d.RUN
  original,pin=d.final_plan();reserve=set(original['eligible_reserve'])-{r['artwork_id'] for r in load(main/'scope-topup/delivery-plan.json.gz')['rows']};assert len(reserve)==188
  rows=[r for r in d.identity_rows() if r['artwork_id'] in reserve]
  with connect() as db:
   states=h.snapshot(db,sorted(reserve));assert len(states)==188
   citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(sorted(reserve),))]
   identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme ILIKE '%%yale%%'",(sorted(reserve),))]
   for r in rows:
    a=states[r['artwork_id']]['artwork'];assert a['accession_number']==r['accession_number'] and a['primary_media_id'] and a['status']!='archived'
    assert any(x['entity_id']==r['artwork_id'] and x['external_id']==r['native_id'] for x in identifiers)
   assert set(x['entity_id'] for x in citations)==reserve
  save(E/'french-reserve-live-reconciliation.json',dict(at=h.now(),historical_plan_sha256=pin,reserve_inspected=188,already_in_production=188,unimported=0,new_programme_increments=0,rows=[dict(artwork_id=r['artwork_id'],native_id=r['native_id'],accession=r['accession_number'],primary_media_id=states[r['artwork_id']]['artwork']['primary_media_id']) for r in rows],citations=citations,prior_visual_evidence='docs/research/printmaking-continuation-20261011/french-reserve/; immutable checksum-bound visual approvals unchanged. No reserve selected or replayed.'))
 if not (E/'prior-batch-live-reconciliation.json').exists():
  old=E.parent/'000033';receipt=load(old/'batch-verification-receipt.json');pv=load(old/'independent-production-verification.json')
  ids=receipt.get('production_ids') or [x['artwork_id'] for x in load(old/'warsaw-icons/plan.json.gz')['records']]
  with connect() as db:
   states=h.snapshot(db,ids);assert len(states)==6 and all(x['artwork']['primary_media_id'] for x in states.values())
  save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),batch=33,source_receipt_sha256=h.sha((old/'batch-verification-receipt.json').read_bytes()),live_artworks=states,verified_rows=6,new_increments_for_batch34=0))
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Uncertain own writes require selection reconciliation'
 save(E/'interrupted-write-reconciliation.json',dict(at=h.now(),existing_campaign_rows=len(own),rows=own))
 print('French reserve: 188 existing, 0 new. Previous six Warsaw images live.',flush=True)
def stage():
 reconcile()
 if (E/'bounded-gap-input.json.gz').exists():return
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.unlinked_creator_label FROM artworks a WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 ORDER BY id LIMIT 25",(MID,))]
  ids=[a['id'] for a in rows];states=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  artists=[dict(x) for x in db.execute("SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,aa.attribution_note,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE artwork_id=ANY(%s::uuid[])",(ids,))]
 save(E/'bounded-gap-input.json.gz',dict(at=h.now(),rows=rows,states=states,citations=citations,artists=artists))
def crosswalk():
 data=load(E/'bounded-gap-input.json.gz');out=[]
 for a in data['rows']:
  cs=[x for x in data['citations'] if x['entity_id']==a['id'] and x['field_name']=='museum_holding_research'];assert len(cs)==1
  c=cs[0];note=json.loads(c['evidence_note']);path=ROOT/note['evidence_path'];raw=gzip.decompress(path.read_bytes());assert h.sha(raw)==note['source_response_sha256']
  body=json.loads(raw)
  if note['scheme']=='joconde-object':
   matches=[x for x in body['data'] if x['Reference']==note['object_id']];assert len(matches)==1;obj=matches[0]
   entry=dict(artwork=a,citation=c,source_note=note,source_object=obj,source_body_sha256=h.sha(raw))
   out.append(entry);print(a['id'],json.dumps({k:v for k,v in obj.items() if any(s in k.lower() for s in ['titre','auteur','invent','lien','dat','dimension'])},ensure_ascii=False),flush=True)
  else:out.append(dict(artwork=a,citation=c,source_note=note,hold='Wikidata-only native identity crosswalk requires separate research; not used as image identity proof'))
 save(E/'joconde-inventory-crosswalk.json.gz',dict(at=h.now(),rows=out))
def research():
 assert not (E/'portal-discovery-hold.json').exists(),'Automated portal extraction held; existing permitted CC0 download only'
 from bs4 import BeautifulSoup
 data=load(E/'joconde-inventory-crosswalk.json.gz');out=[]
 for x in data['rows'][:13]:
  aid=x['artwork']['id'];dest=E/'object-research'/(aid+'.json')
  if dest.exists():out.append(load(dest));continue
  if x.get('hold'):out.append(save(dest,x));continue
  obj=x['source_object'];url=obj['Lien_site_associe'].strip()
  raw,rc=capture('node-'+url.rsplit('/',1)[-1],url)
  if rc['status']!=200:
   out.append(save(dest,dict(x,hold='Native object page HTTP '+str(rc['status']),page_receipt=rc)));break
  soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True)
  manifests=list(dict.fromkeys(re.findall(r'https://apicollections.parismusees.paris.fr/iiif/\d+/manifest',raw.decode())))
  if len(manifests)!=1:out.append(save(dest,dict(x,hold='Missing unique public IIIF manifest',page_receipt=rc)));continue
  oid=manifests[0].split('/')[-2];body,mrc=capture('manifest-'+oid,manifests[0])
  if mrc['status']!=200:
   out.append(save(dest,dict(x,hold='Public manifest HTTP '+str(mrc['status']),page_receipt=rc,manifest_receipt=mrc)));break
  manifest=json.loads(body);out.append(save(dest,dict(x,page_receipt=rc,page_text=text,manifest_receipt=mrc,manifest=manifest,paris_id=oid)))
  print(aid,obj['Numero_inventaire'],oid,manifest.get('label'),flush=True)
 save(E/'native-research-summary.json',dict(at=h.now(),processed_ids=[x['artwork']['id'] for x in out],unresearched_ids=[x['artwork']['id'] for x in data['rows'] if x['artwork']['id'] not in {r['artwork']['id'] for r in out}],limit=13))
def policy():
 from bs4 import BeautifulSoup
 raw,rc=capture('terms','https://www.parismuseescollections.paris.fr/conditions-generales-d-utilisation');assert rc['status']==200
 text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
 assert '1.3.1.a' in text and '1.10' in text and "L'accès à l'API est conditionné par la création d'un compte" in text
 save(E/'portal-discovery-hold.json',dict(at=h.now(),source_id='paris_musees',source_receipt=rc,status='automated_portal_discovery_and_unconfigured_API_held',reason='Section 1.6 restricts robots/direct extraction outside permitted uses; section 1.10 requires API account and acceptance. No configured Paris API account established. Further automated discovery stopped immediately after terms review; one in-flight second object request interrupted.',permitted_selected_image='Sections 1.3.1.a and 1.4 explicitly permit download and reuse of CC0 reproductions. Exact P1515 object and image-level CC0 already obtained; one selected full-frame CC0 file may be downloaded. This is not a provider-wide API authorization.',completed_native_ids=['320026898'],interrupted_node='153161',further_api_requests=False))
 save(E/'source-register.json',dict(at=h.now(),providers=['yale_lux','paris_musees','france_pop_joconde'],registry_reference='required-input-reconciliation.json',policy_reference='docs/ARTLINE_IMAGE_USE.md',paris_terms=rc,access_status='One public object page and self-linked public IIIF manifest HTTP 200; no authentication bypass. Registry legacy terms URL HTTP 404; current footer terms HTTP 200. Broader automated discovery held; exact selected CC0 file download remains permitted.',remaining_gaps='24 other bounded candidates remain unresolved or unresearched at native image level. Directory and museum artwork coverage incomplete.'))
def prepare():
 policy()
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 aid='0350edf0-95b3-424c-8bd5-f3111333aff5';path=E/'object-research'/(aid+'.json');x=load(path);a=x['artwork'];j=x['source_object'];o=x['manifest'];m={v['label']:v['value'] for v in o['metadata']}
 assert h.norm(o['label'])==h.norm(j['Titre'])==h.norm(a['title'])
 assert m['Numéro d’inventaire']==j['Numero_inventaire']=='P1515'
 assert m['Auteur']==['Burdin, Amélie'] and j['Auteur']==a['unlinked_creator_label']=='Burdin Amélie (1834-1865)'
 assert m['Dimensions']==['Oeuvre - Hauteur 65 cm','Oeuvre - Largeur 54 cm'] and j['Mesures']=='Hauteur 65 cm ; Largeur 54 cm'
 assert j['Millesime_de_creation']=='1865' and a['creation_year_start']==a['creation_year_end']==1865 and '>1865<' in m['Date de production']
 assert m['Institution']=='Musée Carnavalet, Histoire de Paris' and '1931' in m['Date d’acquisition'] and j['Date_d_acquisition']=='1931'
 canvases=o['sequences'][0]['canvases'];assert len(canvases)==1
 c=canvases[0];rights={v['label']:v['value'] for v in c['metadata']};assert rights['Copyright']==CC0 and rights['Droits']=='CC0 Paris Musées / Musée Carnavalet - Histoire de Paris'
 url=c['images'][0]['resource']['@id'];assert len(c['images'])==1 and urlsplit(url).hostname=='apicollections.parismusees.paris.fr'
 with connect() as db:
  before=h.snapshot(db,[aid]);assert before[aid]['artwork']['primary_media_id'] is None
  candidates=[dict(r) for r in db.execute('SELECT id::text,title,accession_number,status FROM artworks WHERE current_institution_id=%s AND (accession_number=%s OR normalized_title=%s)',(MID,'P1515',h.norm(a['title'])))];assert [r['id'] for r in candidates]==[aid]
  matches=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s)",(['320026898','M1104320026898'],))];assert all(r['entity_id']==aid for r in matches)
  citations=[dict(r) for r in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND field_name='museum_holding_research' AND evidence_note::jsonb->>'object_id'=%s",('M1104320026898',))];assert [r['entity_id'] for r in citations]==[aid] and citations[0]==x['citation']
 save(E/'global-identity-reconciliation.json',dict(at=h.now(),existing_target=aid,title_inventory_candidates=candidates,global_native_ids=matches,global_object_citations=citations,source_inventory='P1515',paris_id='320026898',joconde_id='M1104320026898',creator_note='Native Amélie Burdin is the same supplied name; newer source qualifies her lifespan as after 1865. Existing creator label and all metadata remain unchanged.',exact_physical_identity='Same title, creator, 1865 creation, inventory P1515, 65 x 54 cm, acquisition 1931; primary complete-composition photograph, not alternate physical object.'))
 row=dict(artwork_id=aid,native_id='M1104320026898',current_source_id='320026898',title=a['title'],creator_label='Burdin, Amélie',source_url=m['Catalogue des œuvres de Paris Musées'],accession_number=a['accession_number'],first=1865,last=1865,precision=a['date_precision'],work_type=a['work_type'],provider='paris',image=dict(image_url=url,source=o,receipt=x['manifest_receipt']),plan_sha256=h.sha(path.read_bytes()),plan_path=str(path),identity_citation=x['citation'],identity_basis='Exact existing Joconde holding citation, source accession P1515, title, creator, physical dimensions, production and acquisition dates, native object and unique CC0 canvas reconciled; null catalogue accession preserved.',rights_basis='Native exact image canvas explicitly labels CC0 with museum credit. Current terms 1.3.1.a and 1.4 authorize selected CC0 reproduction downloads and reuse. User production authorization separate from the CC0 assertion.',rights_label=rights['Droits'],manual_visual_required=True)
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='paris',batch=B,rows=[row],selection_basis='One individually researched exact CC0 gap; broader discovery held under newly checked source terms. No generated creator and no catalogue metadata edits.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 save(E/'gap-reconciliation.json',dict(at=h.now(),database_candidates=25,archived_joconde_crosswalks=24,native_objects_verified=1,selected=1,held_identity_ids=['03371e25-2e11-5664-b661-c1dbf0c20c98'],unresearched_native_ids=[r['id'] for r in load(E/'bounded-gap-input.json.gz')['rows'] if r['id'] not in [aid,'03371e25-2e11-5664-b661-c1dbf0c20c98']],resume_after_artwork_id=aid,portal_hold='portal-discovery-hold.json',images_downloaded_before_selection=0))
 finish()
def finish():
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)
def locked_native_ids(db,ids,rows):
 out={}
 for aid in ids:
  r=rows[aid];old=r['identity_citation'];live=db.execute('SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE id=%s',(old['id'],)).fetchone();assert dict(live)==old,'Identity citation changed'
  assert db.execute('SELECT current_institution_id::text FROM artworks WHERE id=%s',(aid,)).fetchone()['current_institution_id']==MID
  same=db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND (accession_number=%s OR normalized_title=%s)',(MID,'P1515',h.norm(r['title']))).fetchall();assert [a['id'] for a in same]==[aid],'Concurrent exact object conflict'
  out[aid]=json.loads(live['evidence_note'])['object_id'];assert out[aid]==r['native_id']
 return out
code=inspect.getsource(i.apply)
old="native_ids={r['entity_id']:r['external_id'] for r in db.execute(\"SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme=%s\",(ids,cfg['scheme']))}"
assert old in code
i.locked_native_ids=locked_native_ids;exec(compile(code.replace(old,'native_ids=locked_native_ids(db,ids,rows)'),__file__,'exec'),i.__dict__)
old_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 if table=='media_assets':
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/paris'),i.OP+'-paris','Paris Musées — selected Carnavalet image evidence','https://www.parismuseescollections.paris.fr',i.OP))
 if table=='media_rights_evidence':
  for row in rows:
   ev=json.loads(row['evidence_json']);ev['identity_crosswalk']=load(E/'global-identity-reconciliation.json');ev['source_access_review']=load(E/'portal-discovery-hold.json');ev['user_authorization']=dict(production_image_attachment=True,copyright_holder_licence=False,actual_CC0_label_preserved=True);row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return old_copy(db,table,rows)
i.n.copy_rows=copy_rows
def deliver():
 images,_,_=i.accepted(B);assert len(images)==1
 with connect() as db:
  state=h.snapshot(db,[im['artwork_id'] for im in images]);present=[im for im in images if state[im['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert all(state[im['artwork_id']]['artwork']['primary_media_id']==im['media_id'] for im in present)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Missing own transaction preimage'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
