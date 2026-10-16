#!/usr/bin/env python3
"""Bounded continuation of four saved SHUZO/Aichi identities; no scheduler."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=mod('base79','continuous-colbase-000076.py');h=b.h;i=b.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000079';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000079';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000079';OLD=E.parent/'000076'
b.E=E;b.R=R;b.S=S;save=b.save;target=b.target
OP='continuous-shuzo-20261011-b000079';PHASE='aichi-objects';FIELD='continuous_shuzo_object_evidence_b000079';B='aichi-001'
MUSEUM='Aichi Prefectural Museum of Art';SLUG='aichi-prefectural-museum-of-art';SCHEME='museum-native-aichi-jmapps'
MID='95aba05e-2d80-52d8-be99-504d90104872';ARTIST='0c5cd80c-f544-5c39-b435-b0898a3ebae4';SID=''
KEYS=['W296668','W296834','W296835','W296836']
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.BACKUP.mkdir(parents=True,exist_ok=True)
h.SCHEMES={'aichi':[SCHEME,'shuzo-work']};h.museums=lambda:{MUSEUM:(SLUG,'https://apmoa.museum/')}
# Keep the established native provider source identity, not a second source row.
import uuid
SID=str(uuid.uuid5(uuid.NAMESPACE_URL,'continuous-shuzo-20261011-b000076/source/aichi/'+MUSEUM))
uid=h.uid
h.uid=lambda key:SID if key=='source/aichi/'+MUSEUM else uid(key)
def identities(db,rows):
 out=[]
 for r in rows:
  urls=[r['source_url'],r['shuzo_url']];titles=[h.norm(r['title']),h.norm(r['raw']['original_title'])]
  ex=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=ANY(%s)))",(urls,h.SCHEMES['aichi'],[r['source_id'],r['raw']['shuzo_id']]))]
  ac=[dict(x) for x in db.execute('SELECT id::text,title,accession_number FROM artworks WHERE accession_number=ANY(%s)',([r['accession_number'],r['raw']['native_collection_number']],))]
  ci=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
  tt=[dict(x) for x in db.execute('SELECT id::text,title,alternate_title,accession_number FROM artworks WHERE normalized_title=ANY(%s) OR title=%s OR alternate_title=%s',(titles,r['raw']['original_title'],r['raw']['original_title']))]
  assert not(ex or ac or ci or tt),('Identity candidates require review',r['source_id'],ex,ac,ci,tt)
  out.append(dict(source_id=r['source_id'],accession=r['accession_number'],native=ex,global_accessions=ac,global_citations=ci,title_candidates=tt,decision='no existing physical object candidate'))
 # An ensemble already present would overlap its separately numbered constituents.
 parents=[dict(x) for x in db.execute("SELECT id::text,title,accession_number FROM artworks WHERE accession_number='JJ201000001000' OR (current_institution_id=%s AND (title IN ('Landscape of Kugenuma','鵠沼小景') OR alternate_title='鵠沼小景'))",(MID,))]
 assert not parents,('Parent ensemble already in catalogue',parents)
 return out
def add_ids(db,p,pin):
 h.batch_insert(db,'external_identifiers',[dict(id=h.uid('shuzo-id/'+r['raw']['shuzo_id']),entity_type='artwork',entity_id=r['artwork_id'],scheme='shuzo-work',external_id=r['raw']['shuzo_id'],canonical_url=r['shuzo_url'],source_id=SID,retrieved_at=r['shuzo_receipt']['retrieved_at']) for r in p['records']])
h.identities=identities;h.add_ids=add_ids
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch 79: four exact Aichi works from the saved SHUZO queue, with existing creator and museum, all new artworks remain review.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert len(rows)==4 and all(not r['before'] for r in rows)").replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  identities(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace('  after=snapshot(db,ids)','  add_ids(db,p,digest)\n  after=snapshot(db,ids)')
exec(compile(code,__file__,'exec'),h.__dict__)
def init():
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(reg.open()));assert len(registry)==111
 files=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000078/CHECKPOINT.json',E.parent/'000078/source-access-holds.json',OLD/'source-register-final.json',OLD/'research-holds-and-pending.json',ROOT/'ops/india-300-delivery-20261011.py']
 save('required-input-verification.json',dict(at=h.now(),files=[b.ref(p) for p in files],complete_original_registry=registry,registry_count=111,precedence='One bounded worker; production authorized, real local catalogue read-only; newer image approvals prevail. No supervisor changes.'))
 save('authorization.json',dict(at=h.now(),batch=79,scope='Source-backed new production painters/artworks, images and museum links authorized without per-item approval. Exact selected native images retain actual rights. No publication/status changes or local catalogue writes.'))
 old=E.parent/'000078';rc=h.load(old/'batch-verification-receipt.json');ids=rc['production_ids']
 with h.connect() as db:
  state=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name='continuous_warsaw_object_evidence_b000078' AND entity_id=ANY(%s::uuid[])",(ids,))]
  assert len(state)==5
  # Source citation field is retrieved from its independently verified prior receipt.
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  assert len([x for x in notes if x['pin']==rc.get('metadata_plan_sha256',rc.get('plan_sha256'))])==5
  rights=[dict(x) for x in db.execute('SELECT a.id::text,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(rights)==5
  for x in rights:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert ev['selection_sha256']==rc['image_selection_sha256']
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_receipt=b.ref(old/'batch-verification-receipt.json'),states=state,citations=notes,rights=rights,prior_programme_increments=0))
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save('production-target-before-plan.json',target());rows=[]
 shuzo_rc=h.load(OLD/'shuzo-kishida-page1-capture.json');body=gzip.decompress(Path(shuzo_rc['body_path']).read_bytes());assert h.sha(body)==shuzo_rc['sha256']
 source_rows=h.load(OLD/'shuzo-kishida-rows.json');assert json.loads(body)['data']['searchWorks']['items']==source_rows
 for x in source_rows:
  if x['id'] not in KEYS:continue
  key=x['url'].split('=')[-1];raw,rc=b.capture('aichi-'+key,x['url']);assert rc['status']==200
  sp=BeautifulSoup(raw,'html.parser');section=sp.get_text(' ',strip=True).split('検索トップ')[-1].split('1．コレクション')[0]
  assert all(v in section for v in [x['accessionNumber'],x['title']['ja'],'岸田劉生','Public Domain',x['dimension']['ja'],x['medium'][0]['ja']])
  date=x['yearLabel']['en'];match=re.fullmatch(r'(\d{4})(?:-(\d{2}))?',date);assert match
  first=int(match[1]);last=(first//100)*100+int(match[2]) if match[2] else first;assert first<=last<=1970 and date in section
  tag=next(im for im in sp.select('img') if 'pict_size=l' in im.get('src',''));url=urljoin(x['url'],tag['src']);credit=MUSEUM+(' (Kimura Teizo Collection)' if key=='16860' else '')
  native_number='M1759' if key=='16860' else x['accessionNumber'];assert native_number in section
  fp=S/('aichi-'+key+'.html');fp.write_bytes(raw)
  factual={k:v for k,v in x.items() if k!='exhibition'};factual.update(original_title=x['title']['ja'],shuzo_id=x['id'],image_url=url,image_alt=tag.get('alt'),image_rights='Public Domain',image_credit=credit,native_object_fields=section,native_collection_number=native_number)
  if key!='16860':factual['component_identity']=dict(parent_shuzo_id='W296833',parent_native_id='11582',parent_accession='JJ201000001000',parent_source_capture=b.ref(E/'aichi-11582-capture.json'),decision='Import only separately accessioned, separately titled and separately imaged constituent. Parent ensemble excluded from new artwork count. Dimensions and date retained per component.')
  rows.append(dict(provider='aichi',source_id=key,source_url=x['url'],shuzo_url='https://artplatform.go.jp/collections/'+x['id'],shuzo_receipt=shuzo_rc,museum=MUSEUM,title=x['title']['en'],creator_label='岸田劉生 / KISHIDA Ryusei',verified_artist_id=ARTIST,date_display=date,year_start=first,year_end=last,date_decision='eligible',accession_number=x['accessionNumber'],source_type='painting',medium=x['medium'][0]['en'],dimensions=x['dimension']['ja'],credit=credit,raw=factual,evidence=rc,evidence_file=str(fp),identity_review='Exact native inventory, title, unqualified creator, explicit date, dimensions and technique corroborate museum-contributed SHUZO record. No current-display assertion.',source_attribution='Source: Art Platform Japan, National Center for Art Research; selected factual fields normalized by Artline from museum-contributed records. Native museum corroboration preserved.'))
 with h.connect() as db:
  checks=identities(db,rows)
  creator=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist' AND external_id=ANY(%s)",(['A1293','60362067','500121267','Q3021493'],))];assert len(creator)==4 and all(x['entity_id']==ARTIST for x in creator)
  related=[dict(x) for x in db.execute('SELECT id::text,title,alternate_title,accession_number,dimensions_text FROM artworks WHERE id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=%s)',(ARTIST,))]
  assert len(related)==6
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,creator_authorities=creator,existing_creator_works=related,decision='Four native museum inventories and compositions differ from six existing works; no parent ensemble present. Existing artist identity reused; no new painter.'))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==4 and not p['new_institutions'] and not p['held'] and list(p['artists'])==[ARTIST]
 save('source-selection-verification.json',dict(at=h.now(),plan_sha256=pin,selected=4,source_objects_captured=5,parent_excluded='11582',date_range_normalization='Literal 1923-25 retained, normalized to 1923–1925.',image_policy='SHUZO metadata only; exact native Aichi images labelled Public Domain with museum commercial-use terms.'))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']];checked=target(True)
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
  if present:
   assert len(present)==len(notes)==4 and all(x['pin']==pin for x in notes)
   pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={}
   print('Own committed metadata reconciled; no replay writes');return
 rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 assert h.load(E/'prewrite-verification.json')['passed'];save('production-target-before-metadata-write.json',checked);h.apply(PHASE)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=h.BACKUP;i.ORIG.mkdir(parents=True,exist_ok=True)
i.CFG['aichi']=dict(mid=MID,scheme=SCHEME,name=MUSEUM,rights='public_domain',license='Public Domain',policy='https://jmapps.ne.jp/apmoa/',host='jmapps.ne.jp')
old_uid=i.m.uid;i.m.uid=lambda k:SID if k=='source/aichi' else old_uid(k)
# Reuse the already reviewed image workflow without importing its patched metadata writer.
prior=(ROOT/'ops/continuous-shuzo-000076.py').read_text();src=prior[prior.index('def images():'):prior.index('code=inspect.getsource(i.apply)')].replace('NEW_ARTIST','ARTIST');exec(compile(src,__file__,'exec'))
code=inspect.getsource(i.apply).replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace('credits={}',"credits={r['artwork_id']:r.get('image_credit','')+' / 愛知県美術館'+('（木村定三コレクション）' if 'Kimura' in r.get('image_credit','') else '') for r in p['rows']}")
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
