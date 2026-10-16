#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base104','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000104'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000104'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000104'
B='commons-000';MID='fd4996c2-7514-56ff-9000-1d9b4d7bcf55'
i.OP='continuous-basel-images-20261011-b000104';i.RUN=E;i.CFG['commons']=dict(mid=MID,scheme='museum-native-swiss-basel',name='Wikimedia Commons',rights='cc_by_sa',license='CC BY-SA 4.0; PD-Art / Public Domain Mark',policy='https://creativecommons.org/licenses/by-sa/4.0/',host='upload.wikimedia.org',limit=100)
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

def preflight():
 save('started.json',dict(at=h.now(),batch=104))
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000103/CHECKPOINT.json',E.parent/'000103/khm/source-access-holds.json',ROOT/'docs/research/denmark-switzerland-museums-20260917/image-download-holds.json',ROOT/'docs/research/switzerland-southern-cone-1000-20261011/source-access-holds.json']
 registry=list(csv.DictReader(paths[1].open()));assert len(registry)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],complete_registry=registry,precedence='Latest production user authorization; external supervisor unchanged; no local catalogue connections.'))
 save('source-queue-before.json',load(paths[6]))
 save('source-access-holds.json',dict(at=h.now(),inherited=[dict(path=str(p),sha256=h.sha(p.read_bytes()),records=load(p)) for p in paths[-3:]],held_surfaces=['sammlung.kunstmuseumbasel.ch/multimedia/*','commons.wikimedia.org/w/api.php','www.wikiart.org store'],policy='No held-surface requests; independent ordinary public Commons file description and upload.wikimedia.org reproduction routes remain separate.',native_images_requested=0))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 save('production-target-before-research.json',target())
 with connect() as db:
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists()
  prior=load(E.parent/'000103/khm/independent-production-verification.json');previous=h.snapshot(db,[r['id'] for r in prior['rows']]);assert previous==prior['after']
  save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=103,verified_ids=list(previous),snapshot_equal=True,previous_increments_counted=0,own_rows=own))
  rows=[dict(r) for r in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,(SELECT string_agg(ar.display_name,'; ' ORDER BY ar.display_name) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a WHERE current_institution_id=%s AND primary_media_id IS NULL AND status<>'archived' ORDER BY a.id LIMIT 25",(MID,))]
  ids=[r['id'] for r in rows];before=h.snapshot(db,ids)
  cites=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  save('gap-input.json.gz',dict(at=h.now(),museum_id=MID,limit=25,rows=rows,before=before,citations=cites,identifiers=identifiers))
  bavaria=[]
  for mid in ['8bfd5cfe-59b4-4f9b-a621-6c995a804c42','33916550-59e8-4316-92d5-39c66ca12dfa']:
   bavaria.extend([dict(r) for r in db.execute("SELECT id::text,title,current_institution_id::text,accession_number,creation_year_start,creation_year_end FROM artworks WHERE current_institution_id=%s AND primary_media_id IS NULL AND status<>'archived' ORDER BY id LIMIT 25",(mid,))])
  save('bavarian-gap-discovery.json',dict(at=h.now(),rows=bavaria,native_requests=0,images_selected=0,scope='Two separately scoped canonical venues; not the entire museum network.'))
 print('Basel gaps',len(rows),'Bavarian gaps',len(bavaria))

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
 gap=load(E/'gap-input.json.gz');aid='02e8ba56-2a92-5559-b3b4-23a4e26b101e';a=gap['before'][aid]['artwork']
 page=load(E/'commons-courbet.json');rc=page['receipt'];sp=BeautifulSoup(gzip.decompress(Path(rc['body_path']).read_bytes()),'html.parser');text=sp.select_one('.mw-parser-output').get_text(' ',strip=True)
 native=load(E/'native-courbet.json');nr=native['receipt'];nsp=BeautifulSoup(gzip.decompress(Path(nr['body_path']).read_bytes()),'html.parser');md=json.loads(nsp.select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];native=dict(native,metadata=md)
 assert md['Id']=='1462' and md['ObjListInvTxt']['LabelTxt']=='1428' and md['ObjDetailDateTxt']['LabelTxt']=='1859'
 assert all(x in text for x in ['Gustave Courbet','Inv. 1428','46.6 x 61.5','1859','CC BY-SA 4.0','Public Domain Mark','Kunstmuseum Basel artwork ID : 1462','sammlungonline.kunstmuseumbasel.ch'])
 assert md['ObjDetailRightsTxt']['LabelTxt']=='Bilddaten gemeinfrei - Kunstmuseum Basel'
 cite=next(c for c in gap['citations'] if c['entity_id']==aid and c['field_name']=='switzerland_southern_cone_museum_coverage_20261011');note=json.loads(cite['evidence_note']);assert note['source_id']=='1462' and note['accession_number']=='1428'
 with connect() as db:
  live=h.snapshot(db,[aid]);assert live[aid]==gap['before'][aid] and live[aid]['artwork']['primary_media_id'] is None
  acc=[dict(r) for r in db.execute("SELECT id::text,title,primary_media_id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s AND status<>'archived'",(MID,'1428'))];assert [r['id'] for r in acc]==[aid]
  identities=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='museum-native-swiss-basel' AND external_id='1462') OR canonical_url=ANY(%s) OR (scheme='wikidata' AND external_id='Q94636917'))",([cite['source_url'],rc['url']],))];assert {r['entity_id'] for r in identities}=={aid}
  titles=[dict(r) for r in db.execute("SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived' AND (a.normalized_title=ANY(%s) OR a.title ILIKE '%%aster%%') LIMIT 30",(live[aid]['creators'][0]['artist_id'],['bouquet d asters','bouquet of asters','asternstrauss']))];assert {r['id'] for r in titles}=={aid}
  media=[dict(r) for r in db.execute('SELECT id::text FROM media_assets WHERE source_page_url=%s',(rc['url'],))];assert not media
 proof=dict(artwork_id=aid,native_id='1462',accession='1428',accession_candidates=acc,source_identifier_matches=identities,creator_title_matches=titles,existing_source_media=media,source_citation=cite,source_citation_sha256=h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode()),official_source_sha256=nr['sha256'],editorial_confidence=.98)
 basis='Exact Basel native object1462 and inventory1428, Gustave Courbet, title Bouquet d asters/Bouquet of Asters, 1859, oil on canvas, 46.6 x61.5cm, and museum-origin Commons source link all agree. Distinct other flower paintings excluded. Original museum composition and visible Baudelaire dedication require actual visual review; no catalogue metadata mutation.'
 source=dict(page,metadata_text=text,official_metadata=native,identity_reconciliation=proof,source_provenance='Commons explicitly cites former Kunstmuseum Basel online collection URL; current object1462 independently confirms inventory, dimensions, title, creator and public-domain museum image label.',licence='CC BY-SA 4.0 plus PD-Art/Public Domain Mark',attribution='Gustave Courbet; Kunstmuseum Basel, Geschenk der Amerbach-Stiftung; reproduction via Wikimedia Commons; original source Kunstmuseum Basel',transformations='Full source frame, proportional resize and JPEG compression; derivative supplied under CC BY-SA 4.0.')
 image_url=sp.select_one('.fullImageLink > a')['href']
 row=dict(artwork_id=aid,native_id='1462',current_source_id="File:Courbet - Bouquet d'asters, 1859.jpg",title=a['title'],creator_label='Gustave Courbet',source_url=rc['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='commons',expected_museum_id=MID,rights_status='cc_by_sa',rights_label='CC BY-SA 4.0; PD-Art / Public Domain Mark',rights_basis='Commons supplies CC BY-SA4.0 plus PD-Art/PDM. Source photograph is explicitly attributed to Kunstmuseum Basel collection portal; current museum object marks image data public domain. Preserve both assertions; derivative under CC BY-SA4.0. User authorization separate.',source_credit=source['attribution']+'. Derivative: CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/.',image=dict(native_url=image_url,image_url=image_url,source=source,receipt=rc),plan_sha256=note['plan_sha256'],identity_confidence=.98,identity_basis=basis,manual_visual_required=True)
 save('global-identity-reconciliation.json',dict(at=h.now(),records=[proof]))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='Current bounded production enrichment instruction',policy_reference='Original 111-source registry wikimedia_commons and docs/ARTLINE_IMAGE_USE.md general open image policy',copyright_holder_licence=False,actual_source_licence='CC BY-SA 4.0',actual_rights_labels_preserved=True,local_catalogue_read_only=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='commons',batch=B,rows=[row],selection_basis='One existing primary gap: exact museum identity and independently licensed museum-origin Commons reproduction; selected before download.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 im=i.prepare_one(row,B);print(im['state'],im.get('path'),im.get('reason'),flush=True);i.audit(B)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
