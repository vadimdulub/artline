#!/usr/bin/env python3
"""One bounded Greek museum batch; no supervisor or local catalogue mutation."""
import csv,fcntl,gzip,importlib.util,inspect,json,os,re,subprocess,sys,time
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base127','continuous-image-batch-000002.py');h=mod('metadata127','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000127';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000127';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000127'
OP='continuous-greek-20261011-b000127';PHASE='greek-objects-v1';FIELD='continuous_greek_object_evidence_b000127';MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';MUSEUM='National Gallery - Alexandros Soutsos Museum';B='athens-000'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'athens':['continuous-athens-object','museum-native-nationalgallery-gr','nationalgallery-gr-artwork','museum-native-athens-object']}
for p in [E,R,S,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(url):
 key=url.rstrip('/').split('/')[-1];p=E/(key+'-capture.json')
 if p.exists():
  rc=h.load(p);bp=Path(rc['body_path']);raw=gzip.decompress(bp.read_bytes()) if bp.suffix=='.gz' else bp.read_bytes();assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds/www.nationalgallery.gr.json').exists()
 i.provider_slot('www.nationalgallery.gr');r=i.session().get(url,timeout=(15,40));bp=S/(key+'.html');bp.write_bytes(r.content);rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=h.now(),sha256=h.sha(r.content),body_path=str(bp),retry_after=r.headers.get('Retry-After'));save(key+'-capture.json',rc)
 if r.status_code in [401,403,429]:save('access-holds/www.nationalgallery.gr.json',rc)
 return r.content,rc
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch 127; Greek museum records through 1970; no invented creator or date.')
exec(compile(code,__file__,'exec'),h.__dict__)
def no_collision(db,rows):
 assert not db.execute('SELECT id FROM artworks WHERE accession_number=ANY(%s)',([r['accession_number'] for r in rows],)).fetchall(),'Concurrent global accession'
 assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",([r['source_url'] for r in rows],)).fetchall(),'Concurrent global source URL'
 for r in rows:
  if r['artist_id']:
   assert not db.execute('SELECT a.id FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.normalized_title=%s',(r['artist_id'],h.norm(r['title']))).fetchall(),'Concurrent creator/title'
h.no_collision=no_collision
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall(),'Concurrent inventory insertion'\n  assert not db.execute(\"SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)\",(SCHEMES['athens'],[r['source_id'] for r in rows])).fetchall(),'Concurrent native insertion'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save('production-target-before-plan.json',target())
 urls=h.load(E/'papaloukas-konstantinos-object-urls.json');assert len(urls)<=50
 records=[];checks=[];creator_checks=[]
 with h.connect() as db:
  inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(MID,)).fetchone();h.museums=lambda:{MUSEUM:(inst['slug'],inst['website_url'])}
  aliases=db.execute("SELECT id::text,display_name name FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias name FROM artist_aliases al JOIN artists a ON a.id=al.artist_id WHERE a.status<>'archived'").fetchall()
  for url in urls:
   raw,rc=capture(url)
   if rc['status']!=200:checks.append(dict(url=url,hold='HTTP '+str(rc['status'])));continue
   sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');dt=head.find('span');date=dt.get_text(' ',strip=True) if dt else '';dt.extract() if dt else None;title=head.get_text(' ',strip=True).rstrip(',').strip();acc=sp.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip();label=sp.select_one('p.artist').get_text(' ',strip=True);creator_url=sp.select_one('p.artist a')['href'];desc=sp.select_one('p.description').get_text(' ',strip=True);medium,dim=desc.split(', ',1) if ', ' in desc else (None,desc or None);credit=sp.select_one('p.obtainment');credit=credit.get_text(' ',strip=True) if credit else ''
   if desc=='Woodcut':medium,dim='Woodcut',None
   image=sp.select_one('.img-magnifier-container img');imageurl=image.get('data-zoom-image') or image.get('src');key=url.rstrip('/').split('/')[-1]
   years=[int(x) for x in re.findall(r'(?<!\d)[12]\d{3}(?!\d)',date)];reason=None
   if not years:reason='Undated object requires separate date review; not selected in this bounded dated batch'
   elif re.search(r'\b(before|after)\b',date,re.I):reason='Open date boundary requires separate review'
   elif max(years)>1970:reason='Creation extends beyond 1970'
   exact=db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s UNION SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND e.external_id=%s UNION SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_url=%s",(MID,acc,h.SCHEMES['athens'],key,url)).fetchall()
   if exact:reason='Existing object; excluded from new-artwork additions'
   simple=re.sub(r'\s*\([^)]*\).*','',label).strip();tokens=set(h.norm(simple).split());matches={x['id']:x['name'] for x in aliases if set(h.norm(x['name']).split())==tokens};artist_id=next(iter(matches)) if len(matches)==1 else None
   creator_checks.append(dict(label=label,url=creator_url,candidates=matches,decision='exact global name/alias token match' if artist_id else 'retain supplied object-level creator pending authority reconciliation'))
   checks.append(dict(url=url,source_id=key,title=title,accession_number=acc,date_display=date,creator_label=label,existing=exact,outcome=reason or 'selected'))
   print(key,reason or 'SELECTED',flush=True)
   if reason:continue
   assert years and min(years)<=max(years)<=1970 and len(years)<=2
   path=Path(rc['body_path']);assert path.suffix=='.html'
   records.append(dict(provider='athens',source_id=key,museum=MUSEUM,title=title,date_display=date,year_start=min(years),year_end=max(years),date_decision='eligible',source_type='painting' if (medium or '').startswith('Oil') else 'print' if 'woodcut' in (medium or '').lower() else 'watercolor' if (medium or '').startswith('Watercolour') else 'unknown',creator_label=label,verified_artist_id=artist_id,accession_number=acc,medium=medium,dimensions=dim,credit=credit,source_url=url,evidence=rc,evidence_file=str(path),raw=dict(image_url=imageurl,image_alt=image.get('alt'),creator_url=creator_url,credit=credit,original_title=None),identity_review='Exact official inventory, creator, date, support, dimensions and native object image; original copy/study wording retained. No current display claim.'))
 save('papaloukas-global-identity-reconciliation.json',dict(at=h.now(),records=checks));save('papaloukas-creator-global-reconciliation.json',dict(at=h.now(),records=creator_checks))
 h.save(E/PHASE/'source-records.json.gz',records);p={'records':records};pin=None
 save('source-register-v2.json',dict(at=h.now(),source_id='national_gallery_athens',policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',access_status='Official artist index and bounded object pages HTTP 200',discovered=len(urls),selected=len(p['records']),metadata_plan_sha256=pin,remaining_gaps='Museum-wide coverage incomplete; undated/post-1970 and existing objects separated; image cutoff 1955'))
def apply():
 assert h.load(E/'prewrite-verification.json')['passed']
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 with h.connect() as db:
  states=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
 if states:
  assert len(states)==len(notes)==len(ids) and all(x['pin']==pin for x in notes);assert h.load(h.BACKUP/PHASE/'locked-before.json.gz')['artworks']=={};print('Own committed plan reconciled; no new writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and Path(rc['path']).is_dir()
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-metadata-write.json',target(True));h.apply(PHASE)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=h.BACKUP
i.CFG['athens']=dict(mid=MID,scheme='continuous-athens-object',name=MUSEUM,rights='restricted',license='Museum site notice: © 2026 National Gallery - Alexandros Soutsos Museum; no per-image open licence stated',policy='https://www.nationalgallery.gr/en/terms-of-use/',host='www.nationalgallery.gr')
old_uid=i.m.uid;i.m.uid=lambda k:h.uid('source/athens/'+MUSEUM) if k=='source/athens' else old_uid(k)
def images():
 if not (i.folder(B)/'selection.json.gz').exists():
  p,pin=h.pinned(PHASE);rows=[]
  for r in p['records']:
   if r['last']>1955:continue
   rows.append(dict(artwork_id=r['artwork_id'],provider='athens',native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),expected_primary_artist_id=r['artist_id'],plan_sha256=pin,image=dict(image_url=r['raw']['image_url'],source=r,receipt=r['evidence']),rights_basis='Selected authentic Greek museum reproduction dated by 1955 under explicit Greek source extension. Museum rights retained as restricted; user authorization is not a copyright-holder licence.',manual_visual_required=True))
  h.save(i.folder(B)/'selection.json.gz',dict(provider='athens',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 (i.ORIG/B).mkdir(parents=True,exist_ok=True)
 for r in i.selected(B)['rows']:print(r['title'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B)
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("    if p['provider']=='wikiart':evidence.update","    evidence['user_approval']=m.load(RUN/'authorization.json')\n    if p['provider']=='wikiart':evidence.update")
exec(compile(code,__file__,'exec'),i.__dict__)
def deliver():
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B);save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
