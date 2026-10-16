#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base106bavaria','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000106'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000106'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000106'
B='pinakothek-000';MID='8bfd5cfe-59b4-4f9b-a621-6c995a804c42'
i.OP='continuous-bavarian-images-20261011-b000106';i.RUN=E;i.CFG['pinakothek']=dict(mid=MID,scheme='wikidata',name='Bayerische Staatsgemäldesammlungen',rights='cc_by_sa',license='CC BY-SA 4.0',policy='https://creativecommons.org/licenses/by-sa/4.0/',host='cdn.thenetexperts.info',limit=25)
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
code=code.replace("p['provider']=='wikiart'", "p['provider']=='pinakothek'").replace("source/wikiart", "source/pinakothek").replace("OP+'-wikiart'", "OP+'-pinakothek'").replace("WikiArt verified legacy image references", "Bayerische Staatsgemäldesammlungen licensed object reproductions").replace("https://www.wikiart.org", "https://www.sammlung.pinakothek.de")
code=code.replace("SELECT entity_id::text,external_id FROM external_identifiers", "SELECT entity_id::text,scheme,external_id FROM external_identifiers").replace("AND scheme=%s\",(ids,cfg['scheme']))}", "AND scheme=ANY(%s)\",(ids,['wikiart-artwork','wikidata'])) if r['scheme']==rows[r['entity_id']]['native_scheme']}")
exec(compile(code,__file__,'exec'),i.__dict__)
def capture(url):
 host=urlsplit(url).hostname;assert host in ['www.wikiart.org','commons.wikimedia.org','www.sammlung.pinakothek.de','www.pinakothek.de'] and '/store/' not in url
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
 if (i.folder(B)/'selection.json.gz').exists():
  print('Pinned selection already exists; resume preparation or independent verification, never reselect.');return
 save('started.json',dict(at=h.now(),batch=106))
 save('production-target-before-research.json',target())
 files=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000105/CHECKPOINT.json',E.parent/'000105/source-access-holds.json',E.parent/'000104/source-access-holds.json']
 registry=list(csv.DictReader(files[1].open()));q=load(files[6]);assert len(registry)==len(q['sources'])==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in files],complete_original_registry=registry,source_registry_review_supplementary_only=True,local_catalogue_read_only=True,supervisor_unchanged=True))
 save('source-queue-before.json',q)
 save('source-access-holds.json',dict(at=h.now(),inherited=[dict(path=str(p),sha256=h.sha(p.read_bytes()),records=load(p)) for p in files[-2:]],held_endpoints=['commons.wikimedia.org/w/api.php','www.wikiart.org/store/'],no_held_endpoint_requests=True))
 res=mod('reserve106','continuous-reserve-warsaw-000052-research.py');res.E=E;res.PREVIOUS=E.parent/'000103/khm';res.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with connect() as db:
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for r in p['rows']:
   a=live[r['artwork_id']]['artwork'];im=p['images'][r['artwork_id']];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived'
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists()
  prior=load(E.parent/'000105/warsaw/independent-production-verification.json');previous=h.snapshot(db,list(prior['rows']));assert previous==prior['rows']
  save('prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=105,verified_ids=list(previous),snapshot_equal=True,prior_increments_counted=0,own_rows=own))
  rows=[dict(r) for r in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,(SELECT string_agg(ar.display_name,'; ' ORDER BY ar.display_name) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a WHERE current_institution_id=%s AND primary_media_id IS NULL AND status<>'archived' ORDER BY a.id LIMIT 25",(MID,))]
  aids=[r['id'] for r in rows];before=h.snapshot(db,aids)
  cites=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(aids,))]
  exts=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(aids,))]
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,physical_date_holds_preserved=['80082','80437','81054']))
 save('gap-input.json.gz',dict(at=h.now(),rows=rows,before=before,citations=cites,identifiers=exts,institution_id=MID))
 print('188 reserve rows already delivered; staged gaps',len(rows))
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  for row in i.selected(B)['rows']:i.prepare_one(row,B)
  if not (i.folder(B)/'quality-audit.json').exists():i.audit(B)
  print('Pinned preparation resumed; no selection or prior receipt rewritten.');return
 from bs4 import BeautifulSoup
 gap=load(E/'gap-input.json.gz');rows=[];proof=[]
 choices=[('veronese','6683ffc4-9dd2-5579-893d-95e818641239','594','QKGBPPnxBb','random_200_source_identity'),('duck','84ba1814-09a7-5c56-8e9a-d9bb36297378','1280','Znxw9NvGXg','low-count-200-painters-round2-20261009')]
 basis={
 'veronese':'Existing exact WikiArt object57727607edc2cb3880d017a8, Paolo Veronese, Venetian woman portrait at Alte Pinakothek, canvas118x101cm. Official native QKGBPPnxBb inventory594 identifies same lady, canvas117.3x100.8cm, ca1570, red pleated dress and white kerchief. Small measurement rounding retained. Other creator portraits reviewed: Louvre La Belle Nani is a distinct 1560 blue-dress work; Portrait of a Lady1565 is106x87cm. Unknown catalogue/WikiArt dates remain unknown; official ca1570 evidence supports image eligibility only.',
 'duck':'Existing source Q30056880 explicitly cites exact official native Znxw9NvGXg with title aliases Liederliches Weib/Brothel scene with a sleeping couple, Jacob Duck and1640/1650. Current official page confirms inventory1280, wood37x31cm, acquired1799 Galerie Zweibruecken. Distinct sleeping-woman compositions and Graz inventoryGG-713 remain separate. No catalogue metadata or holding mutation.'}
 with connect() as db:
  live=h.snapshot(db,[x[1] for x in choices])
  for key,aid,inv,oid,field in choices:
   a=live[aid]['artwork'];assert live[aid]==gap['before'][aid] and a['primary_media_id'] is None
   native=load(E/'native'/(key+'.json'));rc=native['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
   sp=BeautifulSoup(raw,'html.parser');txt=sp.get_text(' ',strip=True);assert txt==native['text'] and 'CC BY-SA 4.0' in txt and 'Inventory number '+inv in txt and 'Bayerische Staatsgemäldesammlungen – Alte Pinakothek München' in txt
   license=sp.select_one('a[href="https://creativecommons.org/licenses/by-sa/4.0/"]');assert license
   img=sp.select_one('img');url=img['src'];assert urlsplit(url).hostname=='cdn.thenetexperts.info' and ('-'+inv+'_') in url and 'CC-BY-SA_BSTGS.jpg' in url
   ext=next(x for x in gap['identifiers'] if x['entity_id']==aid);cite=next(c for c in gap['citations'] if c['entity_id']==aid and c['field_name']==field);note=json.loads(cite['evidence_note'])
   ident=load(E/'identity'/(key+'.json'));assert not ident['accession_matches'] and {r['entity_id'] for r in ident['identifier_matches']}=={aid}
   if key=='veronese':
    page=load(E/'objects'/(aid+'.json'));assert page['source_id']==ext['external_id']==note['page']['metadata']['_id'] and page['date'] is None and 'um 1570' in txt and '117,3 x 100,8 cm' in txt
   else:assert rc['url'] in note['source_references'] and '1640/1650' in txt and '37 x 31 cm' in txt
   assert not db.execute('SELECT id FROM media_assets WHERE source_page_url=%s',(rc['url'],)).fetchall()
   recon=dict(ident,source_citation=cite,source_citation_sha256=h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode()),native_object_id=oid,source_accession=inv,official_source_sha256=rc['sha256'],basis=basis[key],editorial_confidence=.98)
   proof.append(recon)
   credit='Bayerische Staatsgemäldesammlungen – Alte Pinakothek München; inventory '+inv+'. Image: CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/; full supplied frame proportionally resized and JPEG-compressed, derivative under the same licence.'
   rows.append(dict(artwork_id=aid,native_id=ext['external_id'],native_scheme=ext['scheme'],current_source_id=oid,title=a['title'],creator_label=next(r['creator'] for r in gap['rows'] if r['id']==aid),source_url=rc['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='pinakothek',expected_museum_id=MID,rights_status='cc_by_sa',rights_label='CC BY-SA 4.0',rights_basis='The exact official object page explicitly links CC BY-SA4.0 beside its selected reproduction. Original111-source registry permits explicitly open per-record images. This is a museum licence assertion, separately preserved from user authorization. Supplied public signed CDN URL used unchanged.',source_credit=credit,image=dict(native_url=url,image_url=url,receipt=rc,source=dict(official_metadata=native,identity_reconciliation=recon,source_accession=inv,source_creator_label='Paolo Veronese (Paolo Caliari)' if key=='veronese' else 'Jacob Duck',source_date_label='um 1570' if key=='veronese' else '1640/1650',physical_dimensions_cm=[117.3,100.8] if key=='veronese' else [37,31],licence_url=license['href'],image_alt=img.get('alt'))),plan_sha256=note['plan_sha256'],identity_confidence=.98,identity_basis=basis[key],manual_visual_required=True))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=proof,creator_rows_reviewed=258,other_versions_preserved=True))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='Current bounded production enrichment instruction',policy_reference='Original111-source registry:bavarian_state_paintings; docs/ARTLINE_IMAGE_USE.md general open image policy',copyright_holder_licence=False,actual_museum_licence='CC BY-SA 4.0',actual_rights_labels_preserved=True,local_catalogue_read_only=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='pinakothek',batch=B,rows=rows,selection_basis='Two exact existing image gaps, native official object/creator/dimensions/creation evidence; selected before downloading.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in rows:
  im=i.prepare_one(row,B);print(row['artwork_id'],im['state'],im.get('path'),im.get('original_path'),im.get('reason'),flush=True)
 i.audit(B)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
