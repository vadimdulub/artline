#!/usr/bin/env python3
"""One bounded image worker. External supervisor and completed campaigns untouched."""
import ast, csv, fcntl, gzip, importlib.util, json, os, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base74','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000074'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000074'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000074'
B='wikiart-000';MID='10f88aa8-da2e-58a1-99f1-dc7c360f55b7'
i.OP='continuous-primary-images-20261011-b000074';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,DATA,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)

# Retain the established transactional image-only attachment workflow, replacing
# its retired Cloud SQL backup prerequisite with current verified local recovery.
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text()
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply')
code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    initial=m.load(RUN/'gap-input.json.gz')['before'][aid]\n    assert before[aid]['creators']==initial['creators'] and before[aid]['holdings']==initial['holdings'],'Creator or holding changed since selection'")
exec(compile(code,__file__,'exec'),i.__dict__)

def capture(url):
 host=urlsplit(url).hostname
 assert host in ['www.wikiart.org','www.ngv.vic.gov.au']
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=DATA/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds'/(host+'.json')).exists(),'Source host is access-held'
 i.provider_slot(host);res=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=res.content
 bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=res.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After'))
 h.save(rp,rc)
 if res.status_code in [401,403,429]:save('access-holds/'+host+'.json',dict(rc,retry_allowed=False))
 assert res.status_code==200,('Source HTTP',res.status_code,url)
 return raw,rc
i.m.m.capture=capture

def preflight():
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rows=list(csv.DictReader(registry.open()));assert len(rows)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),complete_registry=rows,precedence='Current production authorization; local catalogue read-only; external supervisor untouched.'))
 save('source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json'
 save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 ledgers=[p for p in E.parent.glob('*/source-access-holds.json') if p.parent!=E]+list((base.OLD/'access-holds').glob('*.json'))
 matches=[]
 for p in ledgers:
  value=load(p)
  if any(v in json.dumps(value).lower() for v in ['wikiart.org','ngv.vic']):matches.append(dict(path=str(p.relative_to(ROOT)),data=value))
 save('source-hold-ledger-reconciliation.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in ledgers],relevant=matches,historical_ngv_access=load(ROOT/'docs/research/all-museums-20260910/access-summary.json'),policy='No provider hold bypass. NGV images require explicit open rights; WikiArt separate approval.'))
 save('production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Unknown previous write: reconcile before retry'
  previous=load(E.parent/'000073/independent-production-verification.json');before=previous['after'];live=h.snapshot(db,list(before));assert live==before
  old=load(E.parent/'000073/batch-verification-receipt.json')
  cit=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(before),))]
  assert all(any(c['entity_id']==aid and old['plan_sha256'] in c['evidence_note'] for c in cit) for aid in before)
  gaps=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,a.work_type,(SELECT string_agg(ar.display_name,' / ') FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a WHERE a.current_institution_id=%s AND a.status<>'archived' AND a.primary_media_id IS NULL ORDER BY a.id LIMIT 100",(MID,))]
  ids=[a['id'] for a in gaps];states=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=73,live=live,citations=cit,previous_increments_counted=0,current_campaign_rows=own))
 save('gap-input.json.gz',dict(at=h.now(),limit=100,rows=gaps,before=states,citations=citations,identifiers=identifiers,after_artwork_id=ids[-1]))
 print('Verified target and prior batch; saved',len(gaps),'NGV gaps')

def research():
 raw,rc=capture('https://www.ngv.vic.gov.au/about/reports-and-documents/copyright-and-reproductions/')
 text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
 save('ngv-terms-review.json',dict(at=h.now(),receipt=rc,terms_text=text,native_image_decision='held_without_object_specific_explicit_open_reuse',reason='Personal study/research and specified noncommercial education do not establish public/commercial image clearance. No NGV image bytes requested.'))
 profiles={'Charles Conder':'charles-conder','Frank Bernard Dicksee':'frank-dicksee','Lindsay Bernard Hall':'bernard-hall'}
 gaps=load(E/'gap-input.json.gz');indexes={};outcomes=[]
 for creator,profile in profiles.items():
  group=[r for r in gaps['rows'] if (r['creator'] or r['unlinked_creator_label'])==creator]
  url='https://www.wikiart.org/en/'+profile+'/all-works/text-list'
  try:raw,rc=capture(url)
  except AssertionError as exc:
   outcomes.extend(dict(artwork_id=r['id'],outcome='index_unavailable',profile=profile,error=str(exc)) for r in group)
   if (E/'access-holds/www.wikiart.org.json').exists():break
   continue
  entries=[]
  for li in BeautifulSoup(raw,'html.parser').select('li'):
   for a in li.select('a[href]'):
    link=urljoin(url,a['href'])
    if link.startswith('https://www.wikiart.org/en/'+profile+'/') and 'all-works' not in link:entries.append(dict(title=a.get_text(' ',strip=True),url=link,text=li.get_text(' ',strip=True)))
  indexes[profile]=dict(receipt=rc,entries=entries)
  for r in group:
   matches=[x for x in entries if h.norm(x['title'])==h.norm(r['title'])]
   out=dict(artwork_id=r['id'],title=r['title'],profile=profile,matches=matches,outcome='no_unique_exact_title')
   if len(matches)==1:
    page=i.m.m.wiki_fields(matches[0]['url']);save('objects/'+r['id']+'.json',page);out.update(outcome='object_page_captured',source_url=page['source_url'])
    print(json.dumps(dict(id=r['id'],title=page['title'],creator=page['creator'],date=page['date'],fields=page['fields'],image=page['image_url'],rights=page['rights_label'])),flush=True)
   outcomes.append(out)
 save('wikiart-index-research.json',indexes);save('discovery-outcomes.json',dict(at=h.now(),rows=outcomes))

def prepare():
 aid='35018ccc-0418-5dab-8fdd-ec082342f03d';gaps=load(E/'gap-input.json.gz');a=gaps['before'][aid]['artwork'];page=load(E/'objects'/(aid+'.json'))
 note=next(json.loads(c['evidence_note']) for c in gaps['citations'] if c['entity_id']==aid)
 ent=note['source_entity'];rc=note['source_receipt'];body=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(body)==rc['sha256'] and json.loads(body)['entities'][ent['id']]==ent
 assert ent['id']=='Q20441907' and page['creator']=='Charles Conder'
 values={k:[x.get('mainsnak',{}).get('datavalue',{}).get('value') for x in v if x.get('rank')!='deprecated'] for k,v in ent['claims'].items()}
 assert values['P217']==['A44-1980'] and values['P4684']==['5216']
 assert values['P2048'][0]['amount']=='+30.6' and values['P2049'][0]['amount']=='+45.6'
 native=load(E/'ngv-summer-idyll.json');text=native['text'];assert all(x in text for x in ['A44-1980','(Summer Idyll)','1889','30.6','45.6','CONDER'])
 assert page['fields']['Dimensions']=='30.6 x 45.6 cm' and page['fields']['Location']=='National Gallery of Victoria (NGV), Melbourne, Australia'
 assert page['date']['first']==page['date']['last']==1889 and h.norm(a['title'])==h.norm(page['title'])
 assert a['creation_year_start'] is None and a['creation_year_end'] is None
 assert urlsplit(page['metadata']['image']).path==urlsplit(page['image_url']).path.split('!')[0]
 with connect() as db:
  live=h.snapshot(db,[aid]);assert live[aid]==gaps['before'][aid]
  duplicate=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikiart-artwork' AND external_id=%s) OR canonical_url=ANY(%s) OR (scheme='wikidata' AND external_id=%s))",(page['source_id'],[page['source_url'],native['receipt']['url']],ent['id']))]
  assert duplicate and all(x['entity_id']==aid for x in duplicate)
  titles=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,current_institution_id::text,primary_media_id::text FROM artworks WHERE normalized_title=ANY(%s)",([a['normalized_title'],'summer idyll','orchard at box hill'],))]
  assert all(x['id']==aid or x['current_institution_id']!=MID for x in titles)
  inventories=[dict(x) for x in db.execute('SELECT id::text,title FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(MID,'A44-1980'))];assert not inventories or all(x['id']==aid for x in inventories)
  media=[dict(x) for x in db.execute('SELECT id::text,source_page_url FROM media_assets WHERE source_page_url=%s',(page['source_url'],))];assert not media
  creators=live[aid]['creators'];assert len(creators)==1 and creators[0]['artist_id']=='b4102d86-a457-5c15-8d8e-f607ce9f539a' and creators[0]['attribution_role']=='primary'
 basis='Exact Charles Conder, normalized title Summer Idyll, NGV location and 30.6 x 45.6 cm. Preserved source Q20441907 links accession A44-1980 to NGV object 5216; fresh official object metadata agrees. WikiArt and NGV give 1889; unknown catalogue dates remain unchanged. Artist catalogue, native identifier, source URL, title and accession collisions reconciled globally. One complete primary reproduction; actual visual decision recorded separately.'
 save('global-identity-reconciliation.json',dict(at=h.now(),artwork_id=aid,source_entity=ent,source_receipt=rc,wikiart_receipt=page['receipt'],ngv_receipt=native['receipt'],duplicate_identifiers=duplicate,title_candidates=titles,accession_candidates=inventories,existing_source_media=media,creator_catalogue='conder-global-catalogue.json',identity_basis=basis,editorial_confidence=.98,date_decision='Source-dated 1889 eligible for image; unknown catalogue fields preserved',museum_connection_update=False))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='6 October WikiArt source approval; current bounded production image enrichment instruction.',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',copyright_holder_licence=False,actual_rights_labels_preserved=True,native_museum_image_permission_not_generalized=True,local_catalogue_read_only=True))
 row=dict(artwork_id=aid,native_id=ent['id'],current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=page['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='wikiart',expected_museum_id=MID,expected_primary_artist_id=creators[0]['artist_id'],rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis'],image=dict(native_url=page['metadata']['image'],image_url=page['image_url'],source=dict(page,official_identity_metadata=native),receipt=page['receipt']),plan_sha256=note['plan_sha256'],identity_confidence=.98,identity_basis=basis,manual_visual_required=True)
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='wikiart',batch=B,rows=[row],selection_basis='Exact NGV physical painting primary-image gap; WikiArt selected before downloading; native metadata only.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 im=i.prepare_one(row,B);print(json.dumps(im),flush=True);i.audit(B)

def deliver():
 images,_,_=i.accepted(B);assert len(images)==1
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
