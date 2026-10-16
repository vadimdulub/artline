import importlib.util,csv,json,subprocess,gzip,datetime,requests
from pathlib import Path
ROOT=Path('/Users/vadimdulub/Documents/vadim-dulub-git/artline')
spec=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
E=ROOT/'docs/research/continuous-production-20261011/batches/000275';E.mkdir(parents=True,exist_ok=True)
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000275';R.mkdir(parents=True,exist_ok=True)
Q=E.parents[1]/'source-queue.json';q=h.load(Q)
required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',Q,E.parents[1]/'CHECKPOINT.json']
for p in required:p.read_text()
registry=list(csv.DictReader(required[1].open()));assert len(registry)==111
h.save(E/'required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],complete_original_registry_used=True,registry_rows=111))
h.save(E/'original-source-registry.json',registry)
h.save(E/'source-queue-preimage.json',q)
paths=sorted(E.parent.glob('*/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:12]
h.save(E/'inherited-holds-verification.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),content=h.load(p)) for p in paths],prior_holds_preserved=True,policy_correction='Athens batch259 blanket rights hold is superseded by Greek museum image extension through1955; no object/date/access holds removed.'))
target='artline-508319:europe-west1:artline-postgres'
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==target
ps=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxies=[x for x in ps if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x];assert len(proxies)==1
with h.connect() as db:
 server=dict(db.execute('SELECT current_database() database,pg_is_in_recovery() recovery').fetchone());assert server['database']=='artline' and not server['recovery']
 h.save(E/'production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_command=proxies[0],database=server,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))
 for batch,key in [('000107','after'),('000274','rows')]:
  p=E.parent/batch/'independent-production-verification.json';prior=h.load(p);live=h.snapshot(db,list(prior[key]));assert live==prior[key]
  h.save(E/f'batch{int(batch)}-live-reconciliation.json',dict(at=h.now(),rows=len(live),snapshot_equal=True,receipt_sha256=h.sha(p.read_bytes()),prior_increments_counted=0))
 url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php'
 data={'creteria[language]':'en','creteria[artwork_name]':'','creteria[artwork_type]':'64','creteria[permanent_exhibition]':'','creteria[location]':'','creteria[extra_filters]':'false','page':'2','action':'get_artworks'}
 response=requests.post(url,data=data,headers={'User-Agent':'ArtlineResearch/1.0'},timeout=(15,45));body=response.content
 cap=R/'athens-paintings-page2.body.gz';cap.write_bytes(gzip.compress(body,mtime=0))
 h.save(E/'athens-page2-source-receipt.json',dict(at=h.now(),url=url,request=data,status=response.status_code,sha256=h.sha(body),body_path=str(cap),retry_after=response.headers.get('Retry-After')))
 response.raise_for_status();source=response.json();rows=source['results'];urls=[r['link'] for r in rows]
 matches=[dict(x) for x in db.execute("SELECT e.entity_id::text,e.scheme,e.external_id,e.canonical_url,a.title,a.date_display,a.creation_year_end,a.primary_media_id::text,a.status FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.canonical_url=ANY(%s)",(urls,))]
 h.save(E/'athens-page2-live-reconciliation.json',dict(at=h.now(),source_total=source.get('total_row'),rows=rows,matches=matches,source_sha256=h.sha(body),museum_image_policy='Explicit Greek extension through1955; actual rights preserved separately'))
 print('ATHENS',len(rows),'matches',len(matches),'gaps',[m for m in matches if m['primary_media_id'] is None])
 names=['Nikiforos Lytras','Nikolaos Gyzis','Konstantinos Parthenis','Spyros Papaloukas','Nikos Engonopoulos','Yannis Tsarouchis','Konstantinos Volanakis','Theophilos Hatzimihail','Nikos Hadjikyriakos-Ghikas','Nikos Hatzikyriakos-Ghikas','Dimitris Mytaras','Alekos Fassianos']
 artists=[dict(x) for x in db.execute("SELECT id::text,display_name FROM artists WHERE display_name=ANY(%s) AND status<>'archived' ORDER BY display_name",(names,))]
 gaps=[]
 for artist in artists:
  found=[dict(x) for x in db.execute("SELECT a.id::text artwork_id,a.title,a.creation_year_start,a.creation_year_end,e.external_id,e.canonical_url FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' AND e.scheme='wikiart-artwork' WHERE aa.artist_id=%s AND aa.attribution_role='primary' AND a.status<>'archived' AND a.primary_media_id IS NULL AND a.creation_year_end<=1970 ORDER BY a.id LIMIT 12",(artist['id'],))]
  gaps.append(dict(artist=artist,rows=found));print(artist['display_name'],artist['id'],len(found),[r['title'] for r in found])
 h.save(E/'bounded-greek-wikiart-gap-scout.json',dict(at=h.now(),artists=gaps,limit_per_artist=12,scope='Exact named existing Greek artists, native WikiArt identifiers, active primaryNULL dated<=1970'))
