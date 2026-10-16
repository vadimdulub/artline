#!/usr/bin/env python3
"""Six selected native Aichi works discovered in registry-backed SHUZO."""
import fcntl,gzip,importlib.util,inspect,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('research76',Path(__file__).with_name('continuous-colbase-000076.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;E=b.E;R=b.R;S=b.S;ROOT=b.ROOT;save=b.save;target=b.target
OP='continuous-shuzo-20261011-b000076';PHASE='aichi-objects';FIELD='continuous_shuzo_object_evidence_b000076';AFIELD='continuous_shuzo_creator_evidence_b000076'
MUSEUM='Aichi Prefectural Museum of Art';SLUG='aichi-prefectural-museum-of-art';SCHEME='museum-native-aichi-jmapps';B='aichi-001'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.BACKUP.mkdir(parents=True,exist_ok=True)
h.SCHEMES={'aichi':[SCHEME,'shuzo-work']};h.museums=lambda:{MUSEUM:(SLUG,'https://apmoa.museum/')}
MID=h.uid('museum/'+SLUG);NEW_ARTIST=h.uid('artist/apj-A1293');KEYS=['W294469','W296667','W296669','W296670','W296671','W296672']
def new_artist():
 return dict(id=NEW_ARTIST,slug='kishida-ryusei-apj-a1293',display_name='Kishida Ryūsei',sort_name='Kishida, Ryūsei',normalized_name=h.norm('Kishida Ryūsei'),birth_year=1891,death_year=1929,birth_display='1891-06-23',death_display='1929-12-20',birth_precision='exact',death_precision='exact',active_start_year=1918,active_end_year=1929,timeline_start_year=1918,timeline_end_year=1929,timeline_display='Selected documented works: 1918–1929',timeline_basis='activity',status='review',created_by=h.ACTOR,updated_by=h.ACTOR)
def creator_matches(db):
 names=[dict(x) for x in db.execute("SELECT id::text,display_name name,birth_year,death_year FROM artists UNION SELECT a.id::text,al.alias name,a.birth_year,a.death_year FROM artist_aliases al JOIN artists a ON a.id=al.artist_id")]
 matches=[r for r in names if any(k in h.norm(r['name']) for k in ['kishida','ryusei','岸田','кисида','кишида','塘雅堂']) or (r['birth_year']==1891 and r['death_year']==1929)]
 auth=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist' AND external_id=ANY(%s)",(['A1293','500121267','60362067','Q3021493'],))]
 return dict(names_aliases_checked=len(names),matches=matches,authority_matches=auth)
def identities(db,rows):
 out=[]
 for r in rows:
  urls=[r['source_url'],r['shuzo_url']];acc=r['accession_number'];titles=[h.norm(r['title']),h.norm(r['raw']['original_title'])]
  ex=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=ANY(%s)))",(urls,h.SCHEMES['aichi'],[r['source_id'],r['raw']['shuzo_id']]))]
  ac=[dict(x) for x in db.execute('SELECT id::text,title,accession_number FROM artworks WHERE accession_number=ANY(%s)',([acc,'M'+r['source_id']],))]
  ci=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
  tt=[dict(x) for x in db.execute('SELECT id::text,title,alternate_title,accession_number,unlinked_creator_label FROM artworks WHERE normalized_title=ANY(%s) OR title=%s OR alternate_title=%s',(titles,r['raw']['original_title'],r['raw']['original_title']))]
  assert not(ex or ac or ci or tt),('Object candidates require review',r['source_id'],ex,ac,ci,tt)
  out.append(dict(source_id=r['source_id'],accession=acc,native=ex,global_accessions=ac,global_citations=ci,global_title_candidates=tt,decision='No global exact or same-title object candidate'))
 return out
def no_collision(db,rows):
 identities(db,rows);cr=creator_matches(db);assert not cr['matches'] and not cr['authority_matches']
 assert not db.execute("SELECT id FROM institutions WHERE id=%s OR slug=%s OR name ILIKE '%%aichi%%' OR name LIKE '%%愛知県美術館%%' OR website_url LIKE '%%apmoa%%'",(MID,SLUG)).fetchall()
h.no_collision=no_collision;h.NEW_ARTISTS=[new_artist()]
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch 76: selected Aichi artworks via SHUZO and a globally reconciled source-authorized creator, all new records remain review.')
code=code.replace('artists=artists,existing_scope','artists=artists,new_artists=NEW_ARTISTS,existing_scope');exec(compile(code,__file__,'exec'),h.__dict__)
def add_creator_evidence(db,p,pin):
 sid=h.uid('source/aichi/'+MUSEUM);rc=h.load(E/'shuzo-artist-A1293-capture.json');ev=dict(plan_sha256=pin,source_sha256=rc['sha256'],source_capture=rc,source_label='岸田劉生 / KISHIDA Ryūsei',birth='1891-06-23',death='1929-12-20',authority_ids=dict(apj='A1293',viaf='60362067',ulan='500121267',wikidata='Q3021493'),reconciliation=h.load(E/'global-creator-institution-reconciliation.json'),timeline_basis='Only selected documented artwork years, not inferred career',new_artist_plan=new_artist())
 h.batch_insert(db,'citations',[dict(id=h.uid('artist-citation/A1293'),entity_type='artist',entity_id=NEW_ARTIST,field_name=AFIELD,source_id=sid,source_record_id='A1293',source_url=rc['url'],evidence_note=json.dumps(ev,ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=h.ACTOR)])
 h.batch_insert(db,'external_identifiers',[dict(id=h.uid('artist-id/'+scheme+'/'+key),entity_type='artist',entity_id=NEW_ARTIST,scheme=scheme,external_id=key,canonical_url=url,source_id=sid,retrieved_at=rc['retrieved_at']) for scheme,key,url in [('apj-artist','A1293',rc['url']),('viaf','60362067','http://viaf.org/viaf/60362067'),('ulan','500121267','http://vocab.getty.edu/page/ulan/500121267'),('wikidata','Q3021493','https://www.wikidata.org/wiki/Q3021493')]])
 # SHUZO's museum-contributed identities remain explicit alongside native museum IDs.
 h.batch_insert(db,'external_identifiers',[dict(id=h.uid('shuzo-id/'+r['raw']['shuzo_id']),entity_type='artwork',entity_id=r['artwork_id'],scheme='shuzo-work',external_id=r['raw']['shuzo_id'],canonical_url=r['shuzo_url'],source_id=sid,retrieved_at=r['shuzo_receipt']['retrieved_at']) for r in p['records']])
h.add_creator_evidence=add_creator_evidence
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==6 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace('locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists)','locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists,new_artist_preimages=[],new_institution_preimages=[])')
code=code.replace("  batch_insert(db,'institutions',p['new_institutions'])","  batch_insert(db,'artists',p['new_artists'])\n  batch_insert(db,'institutions',p['new_institutions'])")
# Add creator evidence after artworks, because artwork external IDs are included.
code=code.replace('  after=snapshot(db,ids)','  add_creator_evidence(db,p,digest)\n  after=snapshot(db,ids)')
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save('production-target-before-plan.json',target());rows=[]
 for x in h.load(E/'shuzo-kishida-rows.json'):
  if x['id'] not in KEYS:continue
  key=x['url'].split('=')[-1];rc=h.load(E/('aichi-'+key+'-capture.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
  sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True);section=text.split('検索トップ')[-1].split('1．コレクション')[0]
  assert x['accessionNumber'] in section and x['title']['ja'] in section and '岸田劉生' in section and 'Public Domain' in section
  date=x['yearLabel']['en'];assert re.fullmatch(r'(ca\.)?\d{4}',date);year=int(re.search(r'\d{4}',date)[0]);assert year<=1970 and str(year) in section
  dim=x['dimension']['ja'];assert dim in section;medium=x['medium'][0];assert medium['ja'] in section
  img=next(im for im in sp.select('img') if 'pict_size=l' in im.get('src',''));url=urljoin(x['url'],img['src']);credit='Aichi Prefectural Museum of Art'+(' (Kimura Teizo Collection)' if '木村定三コレクション' in section else '')
  filepath=S/('aichi-'+key+'.html');filepath.write_bytes(raw)
  factual={k:v for k,v in x.items() if k not in ['exhibition']};factual.update(original_title=x['title']['ja'],shuzo_id=x['id'],image_url=url,image_alt=img.get('alt'),image_rights='Public Domain',image_credit=credit,native_object_fields=section)
  rows.append(dict(provider='aichi',source_id=key,source_url=x['url'],shuzo_url='https://artplatform.go.jp/collections/'+x['id'],shuzo_receipt=h.load(E/'shuzo-kishida-page1-capture.json'),museum=MUSEUM,title=x['title']['en'],creator_label='岸田劉生 / KISHIDA Ryusei',verified_artist_id=NEW_ARTIST,date_display=date,year_start=year,year_end=year,date_decision='eligible',accession_number=x['accessionNumber'],source_type='drawing' if key=='6261' else 'painting',medium=medium['en'],dimensions=dim,credit=credit,raw=factual,evidence=rc,evidence_file=str(filepath),identity_review='Exact museum inventory, native page, Japanese title, unqualified maker, date, dimensions and material corroborate museum-contributed SHUZO record. Different scrolls/versions remain distinct. No on-view claim.',source_attribution='Source: Art Platform Japan, National Center for Art Research; factual fields selected and normalized by Artline from museum-contributed records. Native Aichi records independently corroborated.'))
 with h.connect() as db:
  checks=identities(db,rows);no_collision(db,rows);creator=creator_matches(db)
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,creator=creator));h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==6 and len(p['new_artists'])==len(p['new_institutions'])==1 and not p['artists'] and not p['held']
 save('source-selection-verification.json',dict(at=h.now(),plan_sha256=pin,selected=6,discovered=25,rows=[dict(id=r['artwork_id'],source_id=r['source_id'],shuzo_id=r['raw']['shuzo_id'],date=r['date_display'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256']) for r in p['records']],image_policy='SHUZO used for metadata discovery only. Image selection resolves to native Aichi museum images individually labelled Public Domain under its express commercial-use policy. No aggregator image permission is inferred.'))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
  if present:
   assert len(present)==len(notes)==6 and all(x['pin']==pin for x in notes)
   pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={} and pre['new_artist_preimages']==[]
   assert db.execute("SELECT evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_id=%s AND field_name=%s",(NEW_ARTIST,AFIELD)).fetchone()['pin']==pin
   print('Own committed metadata reconciled; no replay writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'prewrite-verification.json')['passed'];save('production-target-before-metadata-write.json',checked);h.apply(PHASE)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=h.BACKUP
i.CFG['aichi']=dict(mid=MID,scheme=SCHEME,name=MUSEUM,rights='public_domain',license='Public Domain',policy='https://jmapps.ne.jp/apmoa/',host='jmapps.ne.jp')
old_uid=i.m.uid;i.m.uid=lambda k:h.uid('source/aichi/'+MUSEUM) if k=='source/aichi' else old_uid(k)
def images():
 if not (i.folder(B)/'selection.json.gz').exists():
  p,pin=h.pinned(PHASE);rows=[]
  for r in p['records']:
   rows.append(dict(artwork_id=r['artwork_id'],provider='aichi',native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),expected_primary_artist_id=NEW_ARTIST,plan_sha256=pin,image=dict(image_url=r['raw']['image_url'],source=r['raw'],receipt=r['evidence']),image_credit=r['raw']['image_credit'],rights_basis='Exact native museum image is individually labelled Public Domain. Museum collection terms permit download, reproduction and redistribution including commercial use, retaining custodian and Kimura Teizo Collection credit. User production authorization is separate, not a licence.',manual_visual_required=True))
  h.save(i.folder(B)/'selection.json.gz',dict(provider='aichi',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in i.selected(B)['rows']:
  if not (i.folder(B)/'prepared'/(row['artwork_id']+'.json')).exists():
   session=i.session();page=session.get(row['source_url'],timeout=(15,40));assert page.status_code==200 and row['accession_number'] in page.text
   save('image-session-'+row['native_id']+'.json',dict(at=h.now(),source_url=row['source_url'],status=page.status_code,page_sha256=h.sha(page.content),cookie_names=list(session.cookies.keys()),reason='Native public page establishes normal anonymous session; send its actual same-page Referer to its linked Public Domain image.'))
   session.headers['Referer']=row['source_url']
  result=i.prepare_one(row,B)
  i.session().headers.pop('Referer',None)
  print(row['native_id'],result['state'],flush=True)
 i.audit(B)
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("credits={}","credits={r['artwork_id']:r.get('image_credit','')+' / 愛知県美術館'+('（木村定三コレクション）' if 'Kimura' in r.get('image_credit','') else '') for r in p['rows']}")
code=code.replace("    if p['provider']=='wikiart':evidence.update","    evidence['user_approval']=m.load(RUN/'authorization.json')\n    if p['provider']=='wikiart':evidence.update")
exec(compile(code,__file__,'exec'),i.__dict__)
def deliver():
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
