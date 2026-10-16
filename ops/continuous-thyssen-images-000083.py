#!/usr/bin/env python3
"""Bounded, independent continuation campaign; external supervisor untouched."""
import ast,csv,fcntl,gzip,importlib.util,json,os,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base83','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000083'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000083'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000083'
B='wikiart-000';MID='eb9e002b-1d26-4996-9b58-d34a4c372fc3'
i.OP='continuous-primary-images-20261011-b000083';i.RUN=E;i.CFG['wikiart']['scheme']='thyssen-object'
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
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    initial=m.load(RUN/'gap-input.json.gz')['before'][aid]\n    assert before[aid]['creators']==initial['creators'] and before[aid]['holdings']==initial['holdings'],'Creator or holding changed since selection'")
exec(compile(code,__file__,'exec'),i.__dict__)
def capture(url):
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','www.museothyssen.org'] and '/store/' not in url
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
def preflight():
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rows=list(csv.DictReader(registry.open()));assert len(rows)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),complete_registry=rows,precedence='Current production authorization; local catalogue read-only; external supervisor unchanged.'))
 save('source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 ledgers=list((ROOT/'docs/research').glob('**/access-holds/*.json'));matches=[]
 for p in ledgers:
  value=load(p)
  if any(v in json.dumps(value).lower() for v in ['wikiart','thyssen']):matches.append(dict(path=str(p.relative_to(ROOT)),data=value))
 save('source-access-holds.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes())) for p in ledgers],relevant=matches,policy='WikiArt shop 403 preserved; no shop requests. Artwork pages independently accessible. Thyssen native images require separate open evidence and are not selected under WikiArt approval.'))
 save('production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Unknown previous write'
  prior=load(E.parent/'000082/independent-production-verification.json');before=prior['rows'];live=h.snapshot(db,list(before));assert live==before
  previous=load(E.parent/'000082/batch-verification-receipt.json');cit=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(before),))]
  assert all(any(c['entity_id']==aid and previous['plan_sha256'] in c['evidence_note'] for c in cit) for aid in before)
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=82,live=live,citations=cit,previous_increments_counted=0,current_campaign_rows=own))
 print('Production target, complete registry, holds, campaign stop and previous writes reconciled.')
PROFILES={'Alvise Vivarini':'alvise-vivarini','David Bomberg':'david-bomberg','Ben Shahn':'ben-shahn','Christian Schad':'christian-schad','Sándor Bortnyik':'sandor-bortnyik','George Grosz':'george-grosz','August Macke':'august-macke','William Merritt Chase':'william-merritt-chase','Winslow Homer':'winslow-homer','Yves Tanguy':'yves-tanguy','František Kupka':'frantisek-kupka','László Moholy-Nagy':'laszlo-moholy-nagy'}
def research():
 gaps=load(E/'gap-input.json.gz');outcomes=[]
 for creator,profile in PROFILES.items():
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
  save('indexes/'+profile+'.json',dict(receipt=rc,entries=entries))
  for r in group:
   matches=[x for x in entries if h.norm(x['title'])==h.norm(r['title'])]
   out=dict(artwork_id=r['id'],title=r['title'],profile=profile,matches=matches,outcome='no_unique_exact_title')
   if len(matches)==1:
    try:
     page=i.m.m.wiki_fields(matches[0]['url']);save('objects/'+r['id']+'.json',page);out.update(outcome='object_page_captured',source_url=page['source_url'])
     print(json.dumps(dict(id=r['id'],title=page['title'],creator=page['creator'],date=page['date'],fields=page['fields'],rights=page['rights_label'])),flush=True)
    except AssertionError as exc:out.update(outcome='object_unavailable',error=str(exc))
   outcomes.append(out)
  if (E/'access-holds/www.wikiart.org.json').exists():break
 save('discovery-outcomes.json',dict(at=h.now(),rows=outcomes))
def deliver():
 images,_,_=i.accepted(B);assert 0<len(images)<=100
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)
def prepare():
 gaps=load(E/'gap-input.json.gz');ids=['3153f3a7-a606-5b8d-b5ed-11f72a2c2c69','32e352f8-7717-5b4f-ae5a-a4361cc293fb','5f718f09-4cb0-5177-b054-33fb9c7d6b85'];rows=[];proof=[]
 composition={ids[0]:'Two Neapolitan actresses by a theatre-box railing with strongly illuminated faces; to be confirmed against the actual WikiArt file during visual review.',ids[1]:'Two robot-like boxers within an angular mechanical/industrial composition; to be confirmed against the actual WikiArt file.',ids[2]:'Gouache on paper, specific numbered pink-and-blue composition; geometric diagonals, verticals, circles and quadrilaterals. The museum distinguishes this work from its related print album.'}
 with connect() as db:
  live=h.snapshot(db,ids);assert all(live[aid]==gaps['before'][aid] and live[aid]['artwork']['primary_media_id'] is None for aid in ids)
  for aid in ids:
   a=live[aid]['artwork'];page=load(E/'objects'/(aid+'.json'));native=load(E/'native'/(aid+'.json'));note=native['prior_source_note'];facts=note['source_record']['facts'];ref=note['source_record']['source_reference'];refpath=ROOT/ref['path'];assert h.sha(refpath.read_bytes())==ref['sha256']
   old=load(refpath);assert old['parsed']['source_id']==facts['source_id'] if 'source_id' in old['parsed'] else True
   obj=next(o for o in native['jsonld'] if o.get('@type')=='VisualArtwork')
   assert obj['identifier']==facts['source_id'] and h.norm(obj['name'])==h.norm(a['title'])==h.norm(page['title'])
   assert h.norm(page['creator'])==h.norm(facts['creator_label']);assert page['date']['first']==page['date']['last']==a['creation_year_start']==a['creation_year_end']<=1970
   assert str(page['date']['first']) in obj['dateCreated'] and facts['inventory']==a['accession_number']
   assert facts['dimensions_text'] in native['text']
   assert urlsplit(page['metadata']['image']).path==urlsplit(page['image_url']).path.split('!')[0]
   recon=load(E/'reconciliation'/(aid+'.json'));assert not recon['media'] and all(x['id']==aid for x in recon['identifiers'])
   for x in recon['titles']:
    if x['id']!=aid:assert aid==ids[1] and x['id']=='6894c578-8721-5875-9836-e5fdb93fb256' # Azim Azimzade, 1910; distinct creator and work.
   accessions=[dict(x) for x in db.execute('SELECT id::text,title FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(MID,a['accession_number']))];assert len(accessions)==1 and accessions[0]['id']==aid
   basis='Exact WikiArt title, creator and creation year agree with fresh official Thyssen VisualArtwork metadata and pinned original museum accession '+obj['identifier']+'. Museum physical size '+facts['dimensions_text']+'. Global source URL/ID, title and creator-catalogue reconciliation excludes duplicate physical-object candidates; original catalogue attribution/fields preserved. '+composition[aid]+' WikiArt has no explicit dimensions or location, so these are not claimed as WikiArt facts. Museum rights not generalized to WikiArt.'
   rows.append(dict(artwork_id=aid,native_id=obj['identifier'],current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=page['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='wikiart',expected_museum_id=MID,rights_status=('restricted' if page['rights_label']=='Public domain US' else page['rights_status']),rights_label=page['rights_label'],rights_basis=page['rights_basis'],image=dict(native_url=page['metadata']['image'],image_url=page['image_url'],source=dict(page,official_identity_metadata=native),receipt=page['receipt']),plan_sha256=note['plan_sha256'],identity_confidence=.96,identity_basis=basis,manual_visual_required=True))
   proof.append(dict(artwork_id=aid,source_reference=ref,source_record_hash_verified=True,accession_candidates=accessions,reconciliation=recon,editorial_confidence=.96,composition_check_pending=True))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=proof,creator_catalogue='creator-catalogue-reconciliation.json',alternate_titles='alternate-title-duplicate-reconciliation.json',decisions=['Azim Azimzade 1910 same title is another work, not Bortnyik 1927.','Bortnyik Blue-Red Composition/Constructive composition 1919 and Geometrical Composition 1922 are distinct date/title source identities; no alias to numbered 1921 work found.','Schad Zwei Mädche 1928 differs from named actresses Maria and Annunziata 1923.','Haustein and both Shahn candidates held as existing duplicate identities; Macke Circus has conflicting date and private location.']))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='6 October WikiArt source approval; current bounded production image enrichment instruction.',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',copyright_holder_licence=False,actual_rights_labels_preserved=True,native_museum_image_permission_not_generalized=True,local_catalogue_read_only=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='wikiart',batch=B,rows=rows,selection_basis='Three exact existing museum primary gaps selected before download. Museum metadata/reference captures and independent WikiArt source approval; no native museum image requests.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in rows:
  im=i.prepare_one(row,B);print(json.dumps(dict(artwork_id=row['artwork_id'],state=im['state'],path=im.get('path'),dimensions=im.get('original_dimensions'),flags=im.get('flags'),reason=im.get('reason'))),flush=True)
 i.audit(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
