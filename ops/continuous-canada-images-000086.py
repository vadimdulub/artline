#!/usr/bin/env python3
"""Bounded, independent continuation campaign; external supervisor untouched."""
import ast,csv,fcntl,gzip,importlib.util,json,os,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base86','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000086'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000086'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000086'
B='wikiart-000';MID='09f7571d-6d9d-5572-a4ce-cef4db332a25'
i.OP='continuous-primary-images-20261011-b000086';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
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
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','artbooks.artcanada.com'] and '/store/' not in url
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
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rows=list(csv.DictReader(reg.open()));assert len(rows)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(reg),registry_sha256=h.sha(reg.read_bytes()),complete_registry=rows,precedence='Current bounded batch; no supervisor changes, no local catalogue writes, WikiArt source approval distinct from actual rights.'))
 save('source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 ledgers=list((ROOT/'docs/research').glob('**/access-holds/*.json'));matches=[]
 for p in ledgers:
  v=load(p)
  if any(x in json.dumps(v).lower() for x in ['wikiart','gallery.ca','artcanada']):matches.append(dict(path=str(p.relative_to(ROOT)),data=v))
 hist=load(ROOT/'docs/research/all-museums-20260910/access-summary.json')
 save('source-access-holds.json',dict(at=h.now(),relevant=matches,historical_access=hist,policy='Canada native 403 and WikiArt store 403 preserved, no requests to either. Independent approved WikiArt artwork/index pages allowed.'))
 save('production-target-reconciliation.json',target())
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Unknown previous writes'
  prior=load(E.parent/'000085/independent-production-verification.json');live=h.snapshot(db,list(prior['after']));assert live==prior['after']
  cites=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(live),))]
  assert all(any(c['entity_id']==aid and prior['plan_sha256'] in c['evidence_note'] for c in cites) for aid in live)
  gaps=load(E/('initial-gaps-'+MID+'.json'))['rows'];ids=[r['id'] for r in gaps];before=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=85,live=live,citations=cites,current_campaign_rows=own,previous_increments_counted=0))
 save('gap-input.json.gz',dict(at=h.now(),museum_id=MID,limit=35,rows=gaps,before=before,citations=citations,identifiers=identifiers))
 print('Preflight and 35 existing gaps saved',flush=True)

PROFILES={'William Brymner':'william-brymner','James Ensor':'james-ensor','Camille Pissarro':'camille-pissarro','Cornelius Krieghoff':'cornelius-krieghoff','Alfred Pellan':'alfred-pellan','Kazuo Nakamura':'kazuo-nakamura','Pierre-Henri de Valenciennes':'pierre-henri-de-valenciennes','John Linnell':'john-linnell'}
def research():
 gaps=load(E/'gap-input.json.gz');outcomes=[]
 for creator,profile in PROFILES.items():
  group=[r for r in gaps['rows'] if (r['creator'] or r['unlinked_creator_label'])==creator];url='https://www.wikiart.org/en/'+profile+'/all-works/text-list'
  try:raw,rc=capture(url)
  except AssertionError as exc:
   outcomes.extend(dict(artwork_id=r['id'],profile=profile,outcome='index_unavailable',error=str(exc)) for r in group)
   if (E/'access-holds/www.wikiart.org.json').exists():break
   continue
  entries=[]
  for li in BeautifulSoup(raw,'html.parser').select('li'):
   for a in li.select('a[href]'):
    link=urljoin(url,a['href'])
    if link.startswith('https://www.wikiart.org/en/'+profile+'/') and 'all-works' not in link:entries.append(dict(title=a.get_text(' ',strip=True),url=link,text=li.get_text(' ',strip=True)))
  save('indexes/'+profile+'.json',dict(receipt=rc,entries=entries))
  for r in group:
   matches=[x for x in entries if h.norm(x['title'])==h.norm(r['title'])];out=dict(artwork_id=r['id'],title=r['title'],profile=profile,matches=matches,outcome='no_unique_exact_title')
   if len(matches)==1:
    try:
     page=i.m.m.wiki_fields(matches[0]['url']);save('objects/'+r['id']+'.json',page);out.update(outcome='object_page_captured',source_url=page['source_url']);print(json.dumps(dict(id=r['id'],title=page['title'],creator=page['creator'],date=page['date'],fields=page['fields'],rights=page['rights_label'])),flush=True)
    except AssertionError as exc:out.update(outcome='object_unavailable',error=str(exc))
   outcomes.append(out)
 save('discovery-outcomes.json',dict(at=h.now(),rows=outcomes))

def reconcile():
 out=[];gaps=load(E/'gap-input.json.gz')
 with connect() as db:
  for path in sorted((E/'objects').glob('*.json')):
   aid=path.stem;page=load(path);a=gaps['before'][aid]['artwork'];url=page['source_url'];sid=page['source_id'];title=a['title']
   ident=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.primary_media_id::text,e.scheme,e.external_id,e.canonical_url FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND (e.canonical_url=%s OR e.external_id=%s)",(url,sid))]
   media=[dict(x) for x in db.execute('SELECT am.artwork_id::text,ma.id::text,ma.source_page_url,ma.storage_path FROM media_assets ma LEFT JOIN artwork_media am ON am.media_id=ma.id WHERE ma.source_page_url=%s',(url,))]
   titles=[dict(x) for x in db.execute('SELECT id::text,title,primary_media_id::text,creation_year_start,creation_year_end,unlinked_creator_label,current_institution_id::text FROM artworks WHERE lower(title)=lower(%s)',(title,))]
   artistids=[dict(x) for x in db.execute('SELECT id::text,display_name FROM artists WHERE lower(display_name)=lower(%s)',(page['creator'],))]
   works=[dict(x) for x in db.execute('SELECT a.id::text,a.title,a.primary_media_id::text,a.creation_year_start,a.creation_year_end,a.current_institution_id::text FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=ANY(%s::uuid[]) ORDER BY a.id LIMIT 2000',([x['id'] for x in artistids],))] if artistids else []
   r=dict(artwork_id=aid,page=page['source_url'],identifiers=ident,media=media,titles=titles,artistids=artistids,creator_catalogue=works);save('reconciliation/'+aid+'.json',r)
   out.append(dict(artwork_id=aid,title=title,source_matches=ident,existing_media=media,title_matches=titles,creator_work_count=len(works),candidate_titles=[x for x in works if any(w in h.norm(x['title']).split() for w in h.norm(title).split() if len(w)>4)]))
 save('global-reconciliation-summary.json',dict(at=h.now(),rows=out));print(json.dumps(out,ensure_ascii=False),flush=True)

def deliver():
 images,_,_=i.accepted(B);assert 0<len(images)<=100
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
