#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base98khm','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000098/khm'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000098/khm'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000098/khm'
B='wikiart-000';MID='fbc55862-f61c-4561-a0a0-eedf65674f62'
i.OP='continuous-khm-images-20261011-b000098';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
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
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'")
code=code.replace("tables['media_assets'].append(dict(", "credit+=(' '+r['source_credit'] if r.get('source_credit') else '')\n    tables['media_assets'].append(dict(")
code=code.replace("assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'", "assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'\n    cite=r['image']['source']['identity_reconciliation']['source_citation']\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s\",(aid,cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone(),'Pinned identity citation changed'")
exec(compile(code,__file__,'exec'),i.__dict__)
def capture(url):
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','commons.wikimedia.org','www.khm.at'] and '/store/' not in url
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
def deliver():
 images,_,_=i.accepted(B);assert 0<len(images)<=100
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)

def stage():
 save('production-target-before-research.json',target())
 frozen=load(E.parent.parent/'000095/khm-gap-input.json.gz')
 picked=[r for r in frozen['rows'] if r['creator'] in ['Anthony van Dyck','Lucas Cranach the Elder','Palma Vecchio','Paolo Veronese','Titian','Giorgione']]
 ids=[r['id'] for r in picked]
 with connect() as db:
  before=h.snapshot(db,ids)
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists()
 save('gap-input.json.gz',dict(at=h.now(),rows=picked,before=before,citations=[r for r in frozen['citations'] if r['entity_id'] in ids],identifiers=[r for r in frozen['identifiers'] if r['entity_id'] in ids],institution_id=MID))
 print('KHM staged',len(ids))
def research():
 profiles={'Anthony van Dyck':'anthony-van-dyck','Lucas Cranach the Elder':'lucas-cranach-the-elder','Palma Vecchio':'palma-vecchio','Paolo Veronese':'paolo-veronese','Titian':'titian','Giorgione':'giorgione'}
 for creator,slug in profiles.items():
  raw,rc=capture('https://www.wikiart.org/en/'+slug+'/all-works/text-list')
  from bs4 import BeautifulSoup
  rows=[dict(title=a.get_text(' ',strip=True),url='https://www.wikiart.org'+a['href']) for a in BeautifulSoup(raw,'html.parser').select('li a[href]') if a['href'].startswith('/en/'+slug+'/') and 'all-works' not in a['href']]
  save('indexes/'+slug+'.json',dict(receipt=rc,entries=rows))
  terms={'anthony-van-dyck':['lanier','montfort','hermann','wildens','isabella'],'lucas-cranach-the-elder':['jerome'],'palma-vecchio':['blue','feather'],'paolo-veronese':['sebastian'],'titian':['filetto','stephen','maurice'],'giorgione':['laura']}[slug]
  leads=[r for r in rows if any(t in r['title'].lower() for t in terms)]
  save('leads/'+slug+'.json',leads);print(slug,json.dumps(leads),flush=True)
def prepare():
 gaps=load(E/'gap-input.json.gz');choices=[('0b8b6cc0-60d4-5e3e-9236-5c035d2a661e','nicholas-lanier-1630','lanier','501'),('0bcdcf2f-93a1-5e29-90dc-6fcb61ffe0f2','the-penitence-of-st-jerome-1502','jerome','6739'),('3217035e-4a8e-5729-93b9-ea723de4dbb8','blessed-joseph-hermann-1629','hermann','488')]
 notes={'lanier':'Portrait sitter, KHM inventory 501 and museum location identify the Vienna canvas. Catalogue 1628, WikiArt 1630, current KHM around 1632 are documented scholarly date differences within scope. No dates changed. The undated second WikiArt page is not independently counted or downloaded.','jerome':'Same Vienna 1502 limewood panel, inventory 6739. WikiArt 55.5 x 41.5 cm versus current KHM overall 56 x 41.5 cm is a 0.5 cm height measurement discrepancy, not another version. The 1509 prints of Jerome and 1515 painting are separate works.','hermann':'Same large Vienna canvas of the vision of Hermann Joseph, inventory 488. WikiArt 160 x 128 cm and KHM 159.5 x 129 cm differ by under one percent; museum around 1629/1630 and WikiArt 1629-1630 encompass catalogue 1629. Not the different Blessed Aloysius Gonzaga painting.'}
 plan_manifest=load(ROOT/'docs/research/austrian-museums-20260916/metadata-plan-manifest.json');rows=[];proof=[]
 with connect() as db:
  live=h.snapshot(db,[x[0] for x in choices]);assert all(v==gaps['before'][aid] and v['artwork']['primary_media_id'] is None for aid,v in live.items())
  for aid,slug,key,inv in choices:
   a=live[aid]['artwork'];page=load(E/'objects'/(slug+'.json'));native=load(E/'native'/(key+'.json'));citation=next(c for c in gaps['citations'] if c['entity_id']==aid and c['field_name']=='austrian_museum_identity');note=json.loads(citation['evidence_note']);ext=next(r for r in gaps['identifiers'] if r['entity_id']==aid and r['scheme']=='wikidata')
   assert note['accession']==a['accession_number']=='GG_'+inv and 'Gemäldegalerie, '+inv in native['text']
   assert page['date']['last']<=1970 and page['fields']['Location']=='Kunsthistorisches Museum, Vienna, Austria'
   assert page['creator']==next(r for r in gaps['rows'] if r['id']==aid)['creator']
   candidates=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE current_institution_id=%s AND replace(accession_number,'GG_','')=%s AND status<>'archived'",(MID,inv))];assert [r['id'] for r in candidates]==[aid]
   eids=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme LIKE 'wikiart%%' AND external_id=%s) OR (scheme='wikidata' AND external_id=%s))",(page['source_url'],page['source_id'],ext['external_id']))];assert {r['entity_id'] for r in eids}=={aid}
   media=[dict(r) for r in db.execute('SELECT id::text FROM media_assets WHERE source_page_url=%s',(page['source_url'],))];assert not media
   basis='Exact creator, named subject, museum location, accession in original citation and current official KHM metadata, and documented version reconciliation. '+notes[key]
   identity=dict(artwork_id=aid,accession=a['accession_number'],wikidata_id=ext['external_id'],current_wikiart_id=page['source_id'],accession_candidates=candidates,global_identifier_matches=eids,existing_source_media=media,source_citation=citation,source_citation_sha256=h.sha(json.dumps(citation,sort_keys=True,ensure_ascii=False).encode()),official_source_sha256=native['receipt']['sha256'],editorial_confidence=.97,basis=basis,composition_review_pending=True)
   proof.append(identity)
   rows.append(dict(artwork_id=aid,native_id=ext['external_id'],current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=page['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='wikiart',expected_museum_id=MID,rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis'],source_credit='Kunsthistorisches Museum, Gemäldegalerie; museum image copyright/reproduction terms retained separately from WikiArt approval.',image=dict(native_url=page['metadata']['image'],image_url=page['image_url'],source=dict(page,official_metadata=native,identity_reconciliation=identity),receipt=page['receipt']),plan_sha256=plan_manifest['sha256'],identity_confidence=.97,identity_basis=basis,manual_visual_required=True))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=proof,creator_catalogue_rows=1525,duplicate_reconciliation='Palma blue dress and Giorgione Laura each have illustrated other records; excluded. Veronese 1558 fresco is not Vienna 1565 painting. All source and metadata differences retained.'))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='6 October WikiArt source approval and current bounded production enrichment instruction',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',copyright_holder_licence=False,actual_rights_labels_preserved=True,local_catalogue_read_only=True,native_museum_reproduction_permission_not_generalized=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='wikiart',batch=B,rows=rows,selection_basis='Three current KHM primary gaps, exact official accession/title/creator crosswalk, current WikiArt reproductions; selected before image download.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in rows:
  im=i.prepare_one(row,B);print(im['artwork_id'],im['state'],im.get('path'),im.get('reason'),flush=True)
 i.audit(B)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
