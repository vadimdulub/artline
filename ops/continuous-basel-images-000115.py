#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base115','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000115'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000115'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000115'
B='commons-000';MID='fd4996c2-7514-56ff-9000-1d9b4d7bcf55'
i.OP='continuous-basel-images-20261011-b000115';i.RUN=E;i.CFG['commons']=dict(mid=MID,scheme='museum-native-swiss-basel',name='Wikimedia Commons',rights='public_domain',license='PD-Art / Public Domain Mark',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='upload.wikimedia.org',limit=100)
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
code=code.replace("p['provider']=='wikiart'", "p['provider']=='commons'").replace("source/wikiart", "source/commons").replace("OP+'-wikiart'", "OP+'-commons'").replace("WikiArt verified legacy image references", "Wikimedia Commons exact object reproductions").replace("https://www.wikiart.org", "https://commons.wikimedia.org")
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'")
code=code.replace("tables['media_assets'].append(dict(", "credit+=(' '+r['source_credit'] if r.get('source_credit') else '')\n    tables['media_assets'].append(dict(")
code=code.replace("assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'", "assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'\n    cite=r['image']['source']['identity_reconciliation']['source_citation']\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s\",(aid,cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone(),'Pinned citation changed'")
exec(compile(code,__file__,'exec'),i.__dict__)
def capture(url):
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','commons.wikimedia.org','sammlung.kunstmuseumbasel.ch'] and '/store/' not in url
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


# The selected museum-origin Commons original is 14.06 MB / 33.7 MP. Keep a
# bounded 20 MB / 40 MP allowance for this single full-resolution original.
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='prepare_one')
prep=ast.get_source_segment(raw,node).replace('12000000','40000000',1).replace('12000000','40000000',1)
prep=prep.replace('len(payload)<=40000000','len(payload)<=20000000')
exec(compile(prep,__file__,'exec'),i.__dict__)

def prepare():
 from bs4 import BeautifulSoup
 aid='02b69f34-6844-5c4f-a883-f7fff4b0e391'
 gap=load(E.parent/'000104/gap-input.json.gz')
 with connect() as db:gap['before']=h.snapshot(db,[r['id'] for r in gap['rows']])
 save('gap-input.json.gz',gap);a=gap['before'][aid]['artwork'];assert a['primary_media_id'] is None
 url='https://commons.wikimedia.org/wiki/File:Ulanen_jagen_Honved-Husaren_eine_Pferdeherde_ab,_1863.jpg'
 raw,rc=capture(url);sp=BeautifulSoup(raw,'html.parser');text=sp.select_one('.mw-parser-output').get_text(' ',strip=True)
 cite=next(c for c in gap['citations'] if c['entity_id']==aid and c['field_name']=='switzerland_southern_cone_museum_coverage_20261011');note=json.loads(cite['evidence_note'])
 raw2,rc2=capture(cite['source_url']);md=json.loads(BeautifulSoup(raw2,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item']
 save('native-adam.json',dict(receipt=rc2,metadata=md));print('NATIVE',json.dumps(md,ensure_ascii=False)[:14000])
 assert md['Id']=='3096' and md['ObjListInvTxt']['LabelTxt']=='2' and md['ObjDetailDateTxt']['LabelTxt']=='1863'
 assert all(x in text for x in ['Franz Adam','121.8','83.5','3096','Public Domain Mark','sammlungonline.kunstmuseumbasel.ch'])
 assert md['ObjDetailRightsTxt']['LabelTxt']=='Bilddaten gemeinfrei - Kunstmuseum Basel'
 with connect() as db:
  ids=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='museum-native-swiss-basel' AND external_id='3096'")];assert {r['entity_id'] for r in ids}=={aid}
  acc=[dict(r) for r in db.execute("SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number='2' AND status<>'archived'",(MID,))];assert [r['id'] for r in acc]==[aid]
 proof=dict(artwork_id=aid,native_id='3096',accession='2',source_citation=cite,source_citation_sha256=h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode()),official_source_sha256=rc2['sha256'],editorial_confidence=.98,external_identifiers=ids,accession_candidates=acc)
 basis='Exact native museum object3096, accession2, Franz Adam, matching title, oil canvas83.5x121.8cm and explicit Commons museum source3096. Commons structured1864 conflicts with its filename/descriptive1863; official museum and signed date1863 govern, existing date unchanged. Full frame must be visually reviewed.'
 source=dict(receipt=rc,metadata_text=text,official_metadata=dict(receipt=rc2,metadata=md),identity_reconciliation=proof,date_conflict='Commons structured1864 versus description1863; official museum1863 preserved',source_provenance='Explicit original museum object3096 source URL',licence='PD-Art / Public Domain Mark',attribution='Franz Adam; Kunstmuseum Basel; reproduction via Wikimedia Commons; museum-origin image',transformations='Full source frame, proportional resize and JPEG compression')
 image_url=sp.select_one('.fullImageLink > a')['href']
 row=dict(artwork_id=aid,native_id='3096',current_source_id=url.split('/wiki/')[1],title=a['title'],creator_label='Franz Adam',source_url=url,accession_number='2',first=1863,last=1863,precision=a['date_precision'],work_type=a['work_type'],provider='commons',expected_museum_id=MID,rights_status='public_domain',rights_label='PD-Art / Public Domain Mark',rights_basis='Commons PD-Art/PDM; museum image data public domain. Actual assertions preserved separately from user authorization.',source_credit=source['attribution'],image=dict(native_url=image_url,image_url=image_url,source=source,receipt=rc),plan_sha256=note['plan_sha256'],identity_confidence=.98,identity_basis=basis,manual_visual_required=True)
 save('global-identity-reconciliation.json',dict(at=h.now(),records=[proof]))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='Current bounded production enrichment instruction',policy_reference='Original111-source registry wikimedia_commons and docs/ARTLINE_IMAGE_USE.md',copyright_holder_licence=False,actual_source_licence='PD-Art / Public Domain Mark',local_catalogue_read_only=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='commons',batch=B,rows=[row],selection_basis='Exact museum-origin Commons reproduction selected before download'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 im=i.prepare_one(row,B);print('PREPARED',json.dumps(im,ensure_ascii=False));i.audit(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  globals()[sys.argv[1]]()
