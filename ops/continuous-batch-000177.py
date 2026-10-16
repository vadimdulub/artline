#!/usr/bin/env python3
"""One bounded RMFAB worker; external supervisor and local catalogue untouched."""
import csv,fcntl,gzip,importlib.util,inspect,json,os,re,subprocess,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('prod177',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
E=ROOT/'docs/research/continuous-production-20261011/batches/000177'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000177'
OP='continuous-rmfab-20261013-b000177';PHASE='belgium-metadata';FIELD='continuous_rmfab_object_evidence_b000177'
MID='b7f7f11c-4b1c-5524-b190-8c214cd67ad2';TARGET='artline-508319:europe-west1:artline-postgres'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'rmfab':['museum-native-rmfab-inventory']}
h.museums=lambda:{'Royal Museums of Fine Arts of Belgium, Brussels, Belgium':('museum-source-1a4e0b935a6155cf33c1','https://fine-arts-museum.be/')}
for p in [E,R,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(n,v):h.save(E/n,v);return v
def rel(p):return str(Path(p).relative_to(ROOT))
def target(stage):
 commands=subprocess.check_output(['ps','axo','pid,command'],text=True).splitlines()
 proxy=[x.strip() for x in commands if re.search(r'^\s*\d+ /tmp/artline-cloud-sql-proxy ',x) and '--port 55519 ' in x]
 assert len(proxy)==1 and TARGET in proxy[0]
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 with h.connect() as db:
  state=dict(db.execute('SELECT current_database() db,pg_is_in_recovery() recovery,current_setting(\'default_transaction_read_only\') read_only').fetchone());assert state['db']=='artline' and not state['recovery'] and state['read_only']=='on'
 path='production-target-'+stage+'.json'
 if (E/path).exists():path='production-target-'+stage+'-'+str(len(list(E.glob('production-target-'+stage+'*.json')))).zfill(3)+'.json'
 return save(path,dict(at=h.now(),proxy=proxy[0],connection_name=actual,database=state,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0))
def preflight():
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
 for p in paths:p.read_text()
 registry=list(csv.DictReader(paths[1].open()));q=h.load(E.parents[1]/'source-queue.json');assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in q['sources']}
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),read_complete=True) for p in paths],complete_original_registry=registry,registry_rows=111,supplementary_review_not_replacement=True,local_catalogue_connections=0))
 save('source-queue-preimage.json',q)
 ledger=[]
 for name in ['000141/source-access-holds.json','000174/inherited-holds-verification.json','000175/failures-and-holds-final.json','000176/source-access-holds.json','000176/CHECKPOINT.json']:
  p=E.parent/name;v=h.load(p);ledger.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),read_complete=True))
 save('inherited-holds-verification.json',dict(at=h.now(),ledgers=ledger,registry_source=next(x for x in registry if x['source_id']=='rmfab_belgium'),queue_state=next(x for x in q['sources'] if x['source_id']=='rmfab_belgium'),priority_route_decision='Byzantine/icon access and unresolved identity holds preserved. Belgium untouched in this programme and prior handoff recommended it.',other_routes_unchanged=True))
 target('reconciliation')
 with h.connect() as db:
  prior=h.load(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(prior['after']))==prior['after']
  own=[dict(x) for x in db.execute('SELECT entity_id::text,source_record_id,evidence_note FROM citations WHERE field_name=%s',(FIELD,))]
  assert not own or (E/PHASE/'plan.json.gz').exists(),'Unknown own write requires reconciliation'
  base=h.snapshot(db,[str(x['id']) for x in db.execute('SELECT id FROM artworks WHERE current_institution_id=%s ORDER BY id LIMIT 200',(MID,))]);save('existing-institution-preimages.json.gz',base)
  ins=dict(db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(MID,)).fetchone()['v']);save('institution-reconciliation.json',dict(at=h.now(),institution=ins,existing_works=len(base)))
 save('batch107-live-reconciliation.json',dict(at=h.now(),rows=len(prior['after']),snapshot_equal=True,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes()),prior_increments_counted=0))
 save('own-write-reconciliation.json',dict(at=h.now(),own_rows=own,unknown_writes=0))
 cp=h.load(E.parents[1]/'CHECKPOINT.json');assert cp['inflight']['batch']==177
 pid=cp['supervisor_pid'];os.kill(pid,0)
 save('external-continuation-verification.json',dict(at=h.now(),supervisor_pid=pid,pid_alive=True,current_batch=177,external_supervisor_owns_continuation=True,created_supervisors=0,subagents=0,supervisor_not_edited=True))
 print('Preflight and live batch107 reconciliation verified.',flush=True)
def capture(name,url):
 p=E/'captures'/(name+'.json');body=p.with_suffix('.body.gz')
 if p.exists():
  rc=h.load(p);raw=gzip.decompress(body.read_bytes());assert h.sha(raw)==rc['sha256'];return rc,BeautifulSoup(raw,'html.parser')
 r=requests.get(url,headers={'User-Agent':'Artline source-backed catalogue research (bounded selected metadata)'},timeout=(15,50))
 raw=r.content;h.save(p,dict(at=h.now(),retrieved_at=h.now(),url=url,final_url=r.url,status=r.status_code,sha256=h.sha(raw),body_path=rel(body),retry_after=r.headers.get('Retry-After'),bytes=len(raw)))
 body.write_bytes(gzip.compress(raw,mtime=0));rc=h.load(p)
 print('Captured',name,r.status_code,flush=True)
 return rc,BeautifulSoup(raw,'html.parser')
def discover():
 rc,sp=capture('robots','https://fine-arts-museum.be/robots.txt');assert rc['status'] in [200,404]
 robot=RobotFileParser();robot.parse(gzip.decompress((ROOT/rc['body_path']).read_bytes()).decode().splitlines() if rc['status']==200 else []);assert robot.can_fetch('*','https://fine-arts-museum.be/fr/la-collection/artist/agneessens-edouard')
 for name,url in [('legal','https://fine-arts-museum.be/fr/declaration-juridique'),('photographic-service','https://fine-arts-museum.be/en/research/the-digital-museum/photographic-service'),('artist-agneessens','https://fine-arts-museum.be/fr/la-collection/artist/agneessens-edouard')]:
  rc,sp=capture(name,url);assert rc['status']==200
  save(name+'-text.json',dict(receipt=rc,text=sp.get_text(' ',strip=True)))
  if name.startswith('artist'):
   links=list(dict.fromkeys(urljoin(rc['final_url'],a['href']).split('?')[0] for a in sp.select('a[href]') if '/fr/la-collection/edouard-agneessens-' in a['href']))
   assert 0<len(links)<=50
   save('discovery.json',dict(at=h.now(),creator='Edouard Agneessens',artist_index=url,index_sha256=rc['sha256'],object_urls=links,directory_entries_not_artwork_counts=True))
   print('Distinct object URLs',len(links),flush=True)
 save('source-access-holds.json',dict(at=h.now(),provider='rmfab_belgium',native_metadata='HTTP200',native_image_hold='No explicit reusable image licence; photographic service closed indefinitely. No native image requests.',policy_reference='Original111-source registry rmfab_belgium + docs/ARTLINE_IMAGE_USE.md general policy',retry_held_providers=False))
def research():
 rows=[];holds=[]
 for pos,url in enumerate(h.load(E/'discovery.json')['object_urls']):
  rc,sp=capture('object-'+str(pos).zfill(3),url)
  if rc['status']!=200:holds.append(dict(url=url,reason='Access HTTP'+str(rc['status']),receipt=rc));break
  main=sp.select_one('h2');title=main.get_text(' ',strip=True) if main else ''
  text=sp.get_text(' ',strip=True);start=text.find('Edouard Agneessens',text.find('Collections'))
  # DOM-specific fields inspected before this parser is used for ingestion.
  save('parsed/object-'+str(pos).zfill(3)+'.json',dict(url=url,receipt=rc,heading=title,text=text,heading_html=str(main),lists=[u.get_text(' | ',strip=True) for u in sp.select('ul') if 'Dimensions' in u.get_text()]))
  print(pos,title,text[text.find('Inv.')-50:text.find('Inv.')+35],flush=True)
 save('research-access-results.json',dict(at=h.now(),reviewed=len(list((E/'parsed').glob('*.json'))),access_holds=holds,maximum=50))
def artist_collisions(db):
 labels=[dict(x) for x in db.execute("SELECT id::text,display_name label,birth_year,death_year,status FROM artists UNION SELECT a.id::text,al.alias,a.birth_year,a.death_year,a.status FROM artists a JOIN artist_aliases al ON al.artist_id=a.id")]
 return [x for x in labels if 'agneess' in h.norm(x['label']) or 'agnessens' in h.norm(x['label'])]
def object_collisions(db,rows):
 urls=[r['source_url'] for r in rows];titles=[h.norm(r['title']) for r in rows];acc=[r['accession_number'] for r in rows]
 native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (split_part(canonical_url,'?',1)=ANY(%s) OR (scheme ~* 'rmfab|fine-arts|belgium' AND external_id=ANY(%s)))",(urls,acc))]
 citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND split_part(source_url,'?',1)=ANY(%s)",(urls,))]
 artworks=[dict(x) for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE normalized_title=ANY(%s) OR (current_institution_id=%s AND accession_number=ANY(%s))',(titles,MID,acc))]
 creators=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.dimensions_text,a.current_institution_id::text,a.unlinked_creator_label FROM artworks a WHERE unlinked_creator_label ILIKE '%%agneess%%' OR unlinked_creator_label ILIKE '%%agnessens%%' ORDER BY a.id LIMIT 100")]
 excluded=[];ambiguous=[]
 for x in artworks:
  a=x['v']
  if a['id'] in ['2811ba39-7bcf-48a8-9334-7386ceba33d1','028a3ef5-d054-4732-87fe-1c2efc43cd5b']:
   assert a['title']=='Au théâtre' and a['work_type']=='print' and a['creation_year_start']==a['creation_year_end']==1895 and 'Henri-Patrice Dillon' in a['description_md']
   excluded.append(dict(artwork=a,reason='Separate1895 Dillon lithograph impression at NGA; source1879 Agneessens oil painting4650 is a different creator, medium, inventory and creation date.'))
  elif a['id']=='74af0b0a-eea6-426a-ae67-6a8e5748a8d1':
   assert a['unlinked_creator_label']=='LATOUCHE Gaston de' and a['creation_year_start']==1900 and a['creation_year_end']==1950 and a['dimensions_text']=='H. 77.5 ; L. 55'
   excluded.append(dict(artwork=a,reason='Separate Latouche oil-on-wood candidate1900–1950,77.5x55, Évreux; source1879 Agneessens canvas46x38 is not this object.'))
  elif a['id']=='32d08878-53d5-4c45-9bd3-41cca441fd5c':
   assert a['unlinked_creator_label']=='Jacques de Tonnancour' and a['creation_year_start']==1956
   excluded.append(dict(artwork=a,reason='Tonnancour1956 Montréal candidate differs from Agneessens undated6554; undated6554 remains held and is not imported.'))
  else:ambiguous.append(x)
 return dict(native=native,citations=citations,artworks=ambiguous,global_title_exclusions=excluded,existing_unlinked_creator_works=creators)
def collision(db,rows):
 c=object_collisions(db,rows)
 assert not c['native'] and not c['citations'] and not c['artworks'],'Concurrent/ambiguous existing object requires review'
 assert not artist_collisions(db),'Concurrent creator insertion requires new plan'
 assert not db.execute('SELECT id FROM artists WHERE id=%s',(h.uid('artist/agneessens-edouard'),)).fetchone()
 return c
h.collision=collision
original_dates=h.dates
def qualified_dates(r):
 first,last,precision=original_dates(r)
 if (r.get('date_display') or '').startswith('(') and first is not None:precision='circa'
 return first,last,precision
h.dates=qualified_dates
plan_code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch177: dated official RMFAB paintings, reconciled painter and documented holdings. Keep new catalogue records in review.')
plan_code=plan_code.replace('  usedartists=sorted',"  creator=load(RUN/'creator-identity-plan.json')\n  assert not artist_collisions(db)\n  for r in selected:\n   assert not r['before'] and not r['artist_id'] and norm(r['creator_label'])=='edouard agneessens'\n   r['artist_id']=creator['artist']['id'];r['creator_identity']=creator\n  usedartists=sorted")
plan_code=plan_code.replace('p=dict(at=now(),phase=phase,','p=dict(at=now(),phase=phase,new_artists=[creator[\'artist\']],creator_identity=creator,')
exec(compile(plan_code,__file__,'exec'),h.__dict__)
h.artist_collisions=artist_collisions
apply_code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 0<len(rows)<=50 and all(not r['before'] for r in rows) and len(p['new_artists'])==1")
apply_code=apply_code.replace('india_minimum_300_museum_coverage_20261011',FIELD)
apply_code=apply_code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
apply_code=apply_code.replace("  locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists)","  locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists,new_artist_preimages={})")
apply_code=apply_code.replace("  existing_keys=", "  batch_insert(db,'artists',p['new_artists'])\n  creator=p['creator_identity'];artist=creator['artist'];csid=next(iter(sources))\n  batch_insert(db,'external_identifiers',[dict(id=uid('artist-native/agneessens-edouard'),entity_type='artist',entity_id=artist['id'],scheme='museum-native-rmfab-artist',external_id='agneessens-edouard',canonical_url=creator['source_url'],source_id=csid,retrieved_at=creator['receipt']['retrieved_at'])])\n  batch_insert(db,'citations',[dict(id=uid('artist-citation/agneessens-edouard'),entity_type='artist',entity_id=artist['id'],field_name='continuous_rmfab_creator_identity_b000177',source_id=csid,source_record_id='agneessens-edouard',source_url=creator['source_url'],evidence_note=json.dumps(dict(creator_identity=creator,plan_sha256=digest),ensure_ascii=False),retrieved_at=creator['receipt']['retrieved_at'],created_by=ACTOR)])\n  existing_keys=")
apply_code=apply_code.replace("new_artworks=len(data['artworks']),", "new_painters=len(p['new_artists']),new_artworks=len(data['artworks']),")
exec(compile(apply_code,__file__,'exec'),h.__dict__)
def stage():
 rows=[];holds=[];decisions=[]
 for path in sorted((E/'parsed').glob('*.json')):
  parsed=h.load(path);rc=parsed['receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
  sp=BeautifulSoup(raw,'html.parser');heading=sp.select_one('h2');author=heading.select_one('.author');label=author.get_text(' ',strip=True);assert label=='Edouard Agneessens';author.extract();title=heading.get_text(' ',strip=True)
  inv=' '.join(sp.select_one('p.inv').get_text(' ',strip=True).split());m=re.fullmatch(r'(.*?)\s*(?:—\s*)?Inv\.\s*(\d+)',inv);assert m,inv
  dt=m[1].strip().strip('—').strip();acc=m[2];items=[li.get_text(' ',strip=True) for li in sp.select('.artwork-description li')];assert len(items)>=3
  medium=items[0];assert medium.startswith('Huile sur ');dimensions=next(x.removeprefix('Dimensions :').strip() for x in items if x.startswith('Dimensions :'));credit=next(x.removeprefix('Origine :').strip() for x in items if x.startswith('Origine :'))
  yr=re.fullmatch(r'\(?\s*(?:ca\.\s*)?(\d{4})\s*\)?',dt)
  if not yr:
   holds.append(dict(source_url=parsed['url'],inventory=acc,title=title,date_display=dt or None,reason='No creation date in museum object header. Authentication, acquisition and creator life dates are not creation dates.',receipt=rc,source_description=items));continue
  year=int(yr[1]);assert 1842<=year<=1885 and year<=1970
  copyright=sp.select_one('.copyright').get_text(' ',strip=True)
  life=next(a.get_text(' ',strip=True) for a in sp.select('a[href]') if '/artist/agneessens-edouard' in a['href'] and a.select_one('.muted'))
  assert life=='Edouard AGNEESSENS Bruxelles 1842 - Uccle / Bruxelles 1885'
  row=dict(provider='rmfab',source_id=acc,source_url=parsed['url'],museum='Royal Museums of Fine Arts of Belgium, Brussels, Belgium',title=title,creator_label=label,date_display=dt,year_start=year,year_end=year,date_decision='eligible',accession_number=acc,source_type='painting',medium=medium,dimensions=dimensions,credit=credit,evidence=rc,raw=dict(original_title=title,original_dates=dt,inventory_header=inv,description=items,creator_life_label=life,image_credit=copyright,image_rights='Unknown; museum photographic service closed, no explicit licence. Images not requested.',measurements=dimensions,dimension_unit='not explicitly stated on selected notice; not invented'),identity_review='Exact official native inventory, title, creator, source date, material, dimensions and acquisition evidence. Distinct study12531 and full painting4137 retained as separate objects. Parenthesized source years and ca. years remain circa; unknown fields retained. No current display assertion.')
  rows.append(row);decisions.append(dict(inventory=acc,title=title,date_display=dt,structured_year=year,precision=h.dates(row)[2],source_sha256=rc['sha256']))
 assert len(rows)==13 and len(holds)==4
 rc=h.load(E/'artist-agneessens-text.json')['receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
 sp=BeautifulSoup(raw,'html.parser');a=next(a for a in sp.select('a[href]') if '/artist/agneessens-edouard' in a['href'] and '1842' in a.get_text());assert ' '.join(a.get_text(' ',strip=True).split())=='Agneessens Edouard Bruxelles 1842 - Uccle / Bruxelles 1885'
 with h.connect() as db:
  creatorhits=artist_collisions(db);assert not creatorhits
  matches=object_collisions(db,rows);assert not matches['native'] and not matches['citations'] and not matches['artworks']
 save('global-identity-reconciliation.json',dict(at=h.now(),creator_matches=creatorhits,object_matches=matches,related_foreign_works_not_reassigned=True,confidence=.98,basis='Official inventory, dates, sizes and acquisition records; global native URLs/identifiers and titles, institution inventories, creator names and aliases reviewed. Related foreign-holding records have different titles/subjects and inventories.'))
 artist=dict(id=h.uid('artist/agneessens-edouard'),slug='edouard-agneessens-'+h.sha(OP.encode())[:8],display_name='Edouard Agneessens',sort_name='Agneessens, Edouard',normalized_name=h.norm('Edouard Agneessens'),birth_year=1842,death_year=1885,birth_display='1842',death_display='1885',birth_precision='exact',death_precision='exact',timeline_start_year=1842,timeline_end_year=1885,timeline_display='1842–1885',timeline_basis='life',status='review',created_by=h.ACTOR,updated_by=h.ACTOR)
 save('creator-identity-plan.json',dict(at=h.now(),artist=artist,source_url=rc['url'],receipt=rc,source_life_label='Bruxelles 1842 - Uccle / Bruxelles 1885',supported_by_object_inventories=[r['source_id'] for r in rows],global_reconciliation='global-identity-reconciliation.json',confidence=.98,unverified_biography_fields_not_inserted=True))
 save('research-holds.json',dict(at=h.now(),rows=holds,images='Native images lack explicit reusable rights; museum service closed. No source pictures downloaded or visual inspection claimed.',wikiart='No matching WikiArt profile/object found by bounded source-specific web discovery.',unknown_date_records_imported=0))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==13 and not p['held'] and not p['new_institutions'] and len(p['new_artists'])==1
 save('independent-source-validation.json',dict(at=h.now(),plan_sha256=pin,selected=13,held=4,decisions=decisions,creator_evidence_sha256=rc['sha256'],original_titles_preserved=True,all_selected_native_captures_sha256_verified=True,no_images_requested=True,new_artworks_in_review=True,through1970=True))
 print('Frozen13 paintings,1 sourced painter;4 undated holds.',flush=True)
def recovery():
 p,pin=h.pinned(PHASE);target('before-recovery')
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791897658924','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL'
 h.save(E/'cloud-sql-backup.json',backup);h.save(h.BACKUP/'cloud-sql-backup.json',backup)
 with h.connect() as db:
  collision(db,p['records']);assert h.snapshot(db,[r['artwork_id'] for r in p['records']])=={}
  h.save(h.BACKUP/'affected-row-preimages.json.gz',dict(at=h.now(),artworks={},new_artist_preimages={},institution=p['institutions'],existing_artworks=h.snapshot(db,list(h.load(E/'existing-institution-preimages.json.gz'))),related_creator_works=h.snapshot(db,[r['id'] for r in h.load(E/'global-identity-reconciliation.json')['object_matches']['existing_unlinked_creator_works']]),plan_sha256=pin))
 h.BACKUP.chmod(0o700)
 files=[h.BACKUP/'affected-row-preimages.json.gz',h.BACKUP/PHASE/'plan-preimages.json.gz',h.BACKUP/'cloud-sql-backup.json']
 save('local-recovery-verification.json',dict(at=h.now(),status='VERIFIED',plan_sha256=pin,existing_cloud_backup=backup['id'],cloud_backups_created=0,files=[dict(path=str(f),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size) for f in files],locked_transaction_preimages_required=True,local_catalogue_connections=0))
 print('Existing backup and exact scoped preimages verified.',flush=True)
def finish_stage():
 # Preserve frozen selections; adapt capture receipts to established helper naming.
 for path in sorted((E/'captures').glob('object-*.json')):h.save(path.with_suffix('.json.gz'),h.load(path))
 if not (E/PHASE/'plan.json.gz').exists():h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==13 and not p['held'] and not p['new_institutions'] and len(p['new_artists'])==1
 decisions=[]
 for row in p['records']:
  rc=row['evidence'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
  sp=BeautifulSoup(raw,'html.parser');hd=sp.select_one('h2');maker=hd.select_one('.author');assert maker.get_text(' ',strip=True)==row['creator_label'];maker.extract();assert hd.get_text(' ',strip=True)==row['title']
  assert sp.select_one('p.inv').get_text(' ',strip=True).split('Inv.')[1].strip()==row['accession_number'];assert 1842<=row['first']<=row['last']<=1885<1970
  assert row['dimensions']==next(x.get_text(' ',strip=True).removeprefix('Dimensions :').strip() for x in sp.select('.artwork-description li') if x.get_text().strip().startswith('Dimensions :'))
  decisions.append(dict(inventory=row['accession_number'],title=row['title'],date_display=row['date_display'],structured_year=row['first'],precision=row['precision'],source_sha256=rc['sha256'],title_creator_inventory_dimensions_checked=True))
 rc=h.load(E/'creator-identity-plan.json')['receipt'];assert h.sha(gzip.decompress((ROOT/rc['body_path']).read_bytes()))==rc['sha256']
 save('independent-source-validation.json',dict(at=h.now(),plan_sha256=pin,selected=13,held=4,decisions=decisions,creator_evidence_sha256=rc['sha256'],original_titles_preserved=True,all_selected_native_captures_sha256_verified=True,no_images_requested=True,new_artworks_in_review=True,through1970=True))
 print('Frozen13 paintings,1 sourced painter;4 undated holds.',flush=True)
def apply():
 p,pin=h.pinned(PHASE)
 with h.connect() as db:
  live=h.snapshot(db,[r['artwork_id'] for r in p['records']])
  if live:
   assert len(live)==len(p['records'])
   notes=db.execute('SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE field_name=%s',(FIELD,)).fetchall();assert len(notes)==len(live) and all(n['note']['plan_sha256']==pin for n in notes)
   pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['artworks']=={} and pre['new_artist_preimages']=={} and pre['plan_sha256']==pin
   print('Own committed plan reconciled; no replay.',flush=True);return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'independent-source-validation.json')['plan_sha256']==pin
 target('before-database-write');h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
