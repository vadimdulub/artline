#!/usr/bin/env python3
"""One bounded SHUZO/Pola batch. Reuses production ingestion; no scheduler."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base81',ROOT/'ops/continuous-colbase-000076.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000081';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000081';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000081'
b.E=E;b.R=R;b.S=S;save=b.save;target=b.target;ref=b.ref
OP='continuous-pola-20261011-b000081';PHASE='pola-objects';FIELD='continuous_pola_object_evidence_b000081'
MUSEUM='Pola Museum of Art';SLUG='pola-museum-of-art';SCHEME='museum-native-pola';ARTIST='0c5cd80c-f544-5c39-b435-b0898a3ebae4'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.BACKUP.mkdir(parents=True,exist_ok=True)
h.SCHEMES={'pola':[SCHEME]};h.museums=lambda:{MUSEUM:(SLUG,'https://www.polamuseum.or.jp/')}
MID=h.uid('museum/'+SLUG);SID=h.uid('source/pola/'+MUSEUM)
def readsource(acc):
 rc=h.load(E/('pola-'+acc+'-capture.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
 sp=BeautifulSoup(raw,'html.parser');main=sp.select_one('main');assert main
 return raw,rc,main.get_text(' ',strip=True)
def identity(db,rows,existing=False):
 out=[]
 for r in rows:
  urls=[r['source_url'],r['shuzo_url']];titles=[h.norm(r['title']),h.norm(r['raw']['original_title'])]
  ex=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=ANY(%s)))",(urls,[SCHEME,'shuzo-work'],[r['source_id'],r['raw']['shuzo_id']]))]
  ac=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=%s',(r['accession_number'],))]
  ci=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
  tt=[dict(x) for x in db.execute('SELECT a.id::text,a.title,a.alternate_title,a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists FROM artworks a WHERE normalized_title=ANY(%s) OR title=%s OR alternate_title=%s',(titles,r['raw']['original_title'],r['raw']['original_title']))]
  own=r.get('artwork_id') if existing else None
  exact={x['entity_id'] for x in ex+ci}|{x['id'] for x in ac}
  if existing:assert exact=={own},(r['source_id'],exact)
  else:assert not exact,('Exact object collision',r['source_id'],ex,ac,ci)
  unresolved=[x for x in tt if x['id']!=own and (ARTIST in x['artists'] or not x['artists'] or x['current_institution_id']==MID)]
  separated=[]
  if r['source_id']=='006-0271':
   for x in unresolved[:]:
    if x['id']!='4990122f-27f1-5656-9ab0-238d1a9c4965':continue
    frozen=h.load(E/'same-title-existing-reiko.json')['artwork'][x['id']]
    assert h.snapshot(db,[x['id']])[x['id']]==frozen
    a=frozen['artwork'];assert a['accession_number']=='A-10568' and a['creation_year_start']==a['creation_year_end']==1921 and a['medium_text']=='Oil on Canvas' and a['dimensions_text']=='44.2x36.4'
    assert r['medium']=='Watercolor on paper' and r['dimensions']=='34.5 x 25.9 cm' and r['year_start']==1922
    separated.append(dict(id=x['id'],reason='Tokyo A-10568 is the 1921 oil on canvas, 44.2 x 36.4 cm; Pola 006-0271 is the 1922 watercolor on paper, 34.5 x 25.9 cm. Museum-contributed SHUZO W107155 independently corroborates Tokyo inventory/date/dimensions; no held provider re-request.'))
    unresolved.remove(x)
  if unresolved:raise RuntimeError('Title candidates need editorial review: '+json.dumps(dict(source_id=r['source_id'],candidates=unresolved),ensure_ascii=False))
  out.append(dict(source_id=r['source_id'],native_ids=ex,global_accession=ac,global_citations=ci,global_title_candidates=tt,explicit_version_separation=separated,decision='No same physical-object candidate after creator and exact material/date/dimension checks.'))
 return out
def collision(db,rows):
 identity(db,rows)
 assert not db.execute("SELECT id FROM institutions WHERE id=%s OR slug=%s OR website_url LIKE '%%polamuseum%%' OR name ILIKE 'Pola %%' OR name LIKE '%%ポーラ%%'",(MID,SLUG)).fetchall()
 assert not db.execute('SELECT id FROM sources WHERE id=%s OR adapter_key=%s',(SID,OP)).fetchall()
def add_ids(db,p,pin):
 h.batch_insert(db,'external_identifiers',[dict(id=h.uid('shuzo-id/'+r['raw']['shuzo_id']),entity_type='artwork',entity_id=r['artwork_id'],scheme='shuzo-work',external_id=r['raw']['shuzo_id'],canonical_url=r['shuzo_url'],source_id=SID,retrieved_at=r['shuzo_receipt']['retrieved_at']) for r in p['records']])
h.collision=collision;h.add_ids=add_ids
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch 81: nine source-backed Pola artworks and holdings with globally reconciled existing creator; new objects remain review.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==9 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace('locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists)','locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists,new_institution_preimages=[],new_source_preimages=[])')
code=code.replace('  after=snapshot(db,ids)','  add_ids(db,p,digest)\n  after=snapshot(db,ids)')
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save('production-target-before-plan.json',target());rows=[]
 old=E.parent/'000076';shuzo_rc=h.load(old/'shuzo-kishida-page1-capture.json');shuzo_raw=gzip.decompress(Path(shuzo_rc['body_path']).read_bytes());assert h.sha(shuzo_raw)==shuzo_rc['sha256'];xs=h.load(old/'shuzo-kishida-rows.json');assert json.loads(shuzo_raw)['data']['searchWorks']['items']==xs
 for x in xs[:10]:
  if x['id']=='W33645':continue
  raw,rc,text=readsource(x['accessionNumber']);assert all(t in text for t in [x['title']['ja'],x['medium'][0]['ja'],x['yearLabel']['ja'],x['dimension']['ja'],'岸田劉生','ポーラ美術館が収蔵する'])
  date=x['yearLabel']['en'];assert re.fullmatch(r'(ca\. )?\d{4}',date);year=int(re.search(r'\d{4}',date)[0]);assert year<=1970
  fp=S/('pola-'+x['accessionNumber']+'.html');fp.write_bytes(raw)
  facts={k:v for k,v in x.items() if k!='exhibition'};facts.update(original_title=x['title']['ja'],shuzo_id=x['id'],native_source_url=rc['url'],native_field_verification=dict(title=True,creator=True,date=True,medium=True,dimensions=True,collection=True),native_images_requested=False)
  medium=x['medium'][0]['en']
  if x['id']=='W33750':medium='Color on paper, framed' # Correct evident English typo against exact Japanese 額装, retaining raw label.
  rows.append(dict(provider='pola',source_id=x['accessionNumber'],source_url=rc['url'],shuzo_url='https://artplatform.go.jp/collections/'+x['id'],shuzo_receipt=shuzo_rc,museum=MUSEUM,title=x['title']['en'],creator_label='岸田劉生 / Kishida Ryusei',verified_artist_id=ARTIST,date_display=date,year_start=year,year_end=year,date_decision='eligible',accession_number=x['accessionNumber'],source_type='watercolor' if x['id']=='W33687' else 'painting',medium=medium,dimensions=x['dimension']['ja'],credit='Pola Museum of Art, Pola Art Foundation',raw=facts,evidence=rc,evidence_file=str(fp),identity_review='Exact Pola native accession URL, Japanese title, unqualified artist, date, dimensions and medium corroborate museum-contributed SHUZO record. Separate Reiko oil portrait and watercolor retained. No on-view claim.',source_attribution='Source: Art Platform Japan, National Center for Art Research; selected factual fields from museum-contributed SHUZO data, normalized by Artline. Native museum record separately verified; narrative description not reproduced.'))
 with h.connect() as db:
  checks=identity(db,rows);collision(db,rows)
  authorities=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist' AND external_id=ANY(%s)",(['A1293','60362067','500121267','Q3021493'],))];assert len(authorities)==4 and all(x['entity_id']==ARTIST for x in authorities)
  names=[dict(x) for x in db.execute("SELECT id::text,display_name name,birth_year,death_year FROM artists UNION SELECT a.id::text,al.alias name,a.birth_year,a.death_year FROM artist_aliases al JOIN artists a ON a.id=al.artist_id")]
  matches=[x for x in names if any(t in h.norm(x['name']) for t in ['kishida','ryusei','岸田','кисида','кишида'])];assert {x['id'] for x in matches}=={ARTIST}
  oeuvre=h.snapshot(db,[r['id'] for r in h.load(E/'creator-existing-works.json')]);assert len(oeuvre)==10
  institutions=[r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i')];instmatches=[x for x in institutions if re.search(r'\bpola\b|ポーラ|polamuseum',json.dumps(x,ensure_ascii=False),re.I)];assert not instmatches
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,creator_authorities=authorities,creator_matches=matches,global_names_checked=len(names),existing_creator_works=oeuvre,institutions_checked=len(institutions),institution_matches=instmatches,new_museum_id=MID))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE);p,pin=h.pinned(PHASE)
 assert len(p['records'])==9 and len(p['new_institutions'])==1 and not p['held'] and list(p['artists'])==[ARTIST] and p['existing_scope']==0
 save('source-selection-verification.json',dict(at=h.now(),selected=9,discovered_saved=10,metadata_plan_sha256=pin,new_painters=0,source_objects_captured=10,new_institutions=1,held_source_ids=['W33645'],held_reason='Grouped Kido original cover illustrations; multiple compositions and missing dimensions need exact catalogue-unit review before counting.',image_selection=0,image_hold='Pola terms reserve reproduction/use rights; no object-level open rights established; SHUZO image rights not inferred. No image downloads.'))
 save('authorization.json',dict(at=h.now(),batch=81,scope='User authorizes source-backed transactional production inserts and holdings without per-item approval. Local catalogue remains read-only. Images only with supported source policy.'))
 save('CHECKPOINT-prepared.json',dict(at=h.now(),stage='metadata_plan_prepared_recovery_and_prewrite_pending',batch=81,selected=9,plan_sha256=pin,verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  state=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
  if state:
   assert len(state)==len(notes)==9 and all(x['pin']==pin for x in notes)
   pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={} and pre['new_institution_preimages']==[] and pre['new_source_preimages']==[]
   identity(db,p['records'],True);print('Own committed metadata reconciled; zero replay writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'prewrite-verification.json')['passed'];save('production-target-before-metadata-write.json',checked);h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
