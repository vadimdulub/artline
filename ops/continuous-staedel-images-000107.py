#!/usr/bin/env python3
"""Bounded Städel primary-image continuation. No scheduler or local DB writes."""
import ast,csv,fcntl,gzip,importlib.util,json,os,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base107','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000107'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000107'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000107'
B='staedel-000';i.OP='continuous-staedel-images-20261012-b000107';i.RUN=E
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
def capture(url):
 host=urlsplit(url).hostname;assert host=='sammlung.staedelmuseum.de'
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=DATA/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds'/(host+'.json')).exists(),'Source host held'
 i.provider_slot(host);res=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=res.content
 bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=res.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=res.headers.get('Retry-After'),redirect=res.headers.get('Location'))
 h.save(rp,rc)
 if res.status_code in [401,403,429]:save('access-holds/'+host+'.json',dict(rc,retry_allowed=False))
 return raw,rc
def stage():
 if (E/'gap-input.json.gz').exists():print('Frozen discovery exists; reconcile before reselection.');return
 save('started.json',dict(at=h.now(),batch=107));save('production-target-before-research.json',target())
 files=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000106/CHECKPOINT.json',E.parent/'000106/source-access-holds.json',E.parent/'000091/source-access-holds.json']
 registry=list(csv.DictReader(files[1].open()));q=load(files[6]);assert len(registry)==len(q['sources'])==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in files],complete_original_registry=registry,source_registry_review_supplementary_only=True,local_catalogue_read_only=True,supervisor_unchanged=True))
 save('source-queue-before.json',q)
 save('source-access-holds.json',dict(at=h.now(),inherited=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in files[-2:]],staedel_historical_head_status=200,staedel_no_recorded_denial=True,held_endpoint_requests=0))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 with connect() as db:
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own,'Existing campaign writes must be reconciled first'
  prior=load(E.parent/'000106/independent-production-verification.json');live=h.snapshot(db,list(prior['after']));assert live==prior['after']
  save('prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=106,prior_ids=list(live),snapshot_equal=True,prior_increments_counted=0,own_existing_rows=own))
  museums=[dict(r) for r in db.execute("SELECT id::text,name,slug FROM institutions WHERE slug='staedel-museum'")];assert len(museums)==1;mid=museums[0]['id']
  rows=[dict(r) for r in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,(SELECT string_agg(ar.display_name,'; ' ORDER BY ar.display_name) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a WHERE current_institution_id=%s AND primary_media_id IS NULL AND status<>'archived' ORDER BY a.id LIMIT 25",(mid,))]
  ids=[r['id'] for r in rows];before=h.snapshot(db,ids)
  cites=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  exts=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 save('gap-input.json.gz',dict(at=h.now(),rows=rows,before=before,citations=cites,identifiers=exts,institution_id=mid,institution=museums[0]))
 print(json.dumps(dict(institution=museums[0],rows=rows,identifiers=exts),ensure_ascii=False))
def configure():
 global MID
 MID=load(E/'gap-input.json.gz')['institution_id']
 i.CFG['staedel']=dict(mid=MID,scheme='staedel-object',name='Städel Museum',rights='public_domain',license='Public Domain Mark 1.0',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='cdn.staedelmuseum.de',limit=25)
 # Preserve the established atomic image writer and strengthen pinned preimages/citations.
 raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text();node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply');code=ast.get_source_segment(raw,node)
 code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
 code=code.replace("assert native_ids.get(aid)==r['native_id'],'Native identity changed'", "assert native_ids.get(aid)==r['native_id'],'Native identity changed'\n    assert before[aid]==m.load(RUN/'gap-input.json.gz')['before'][aid],'Selected object state changed'\n    cite=r['image']['source']['identity_reconciliation']['source_citation']\n    assert db.execute(\"SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s AND source_url=%s AND evidence_note=%s\",(aid,cite['field_name'],cite['source_url'],cite['evidence_note'])).fetchone(),'Pinned identity citation changed'")
 code=code.replace("tables['media_assets'].append(dict(", "credit+=' '+r['source_credit']\n    tables['media_assets'].append(dict(")
 code=code.replace("p['provider']=='wikiart'", "p['provider']=='staedel'").replace('source/wikiart','source/staedel').replace("OP+'-wikiart'", "OP+'-staedel'").replace('WikiArt verified legacy image references','Städel Museum public-domain object reproductions').replace('https://www.wikiart.org','https://sammlung.staedelmuseum.de')
 exec(compile(code,__file__,'exec'),i.__dict__)
def prepare():
 from bs4 import BeautifulSoup
 configure()
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  for row in i.selected(B)['rows']:i.prepare_one(row,B)
  i.audit(B);return
 gap=load(E/'gap-input.json.gz');rows=[];proof=[];held=[]
 original=ROOT/'docs/research/museum-expansion-20261006/staedel-001-current-plan.json.gz';oldpin=h.sha(original.read_bytes());original_plan=load(original)
 parser=mod('stparser107','popular-staedel-images.py')
 with connect() as db:
  live=h.snapshot(db,list(gap['before']));assert live==gap['before']
  for r in gap['rows']:
   aid=r['id'];np=E/'native'/(aid+'.json')
   if not np.exists():held.append(dict(artwork_id=aid,title=r['title'],reason='Native museum inventory not yet reconciled for Wikidata-origin gap; no image selected.',category='identity_research_pending'));continue
   n=load(np);props=n['properties']
   if props.get('Picture Copyright')!=['Public Domain']:
    held.append(dict(artwork_id=aid,title=r['title'],reason='Exact museum reproduction is copyright-labelled; no provider-wide approval applies. Independent approved WikiArt matching remains a separate possible route.',category='museum_image_rights_hold',actual_rights=props.get('Picture Copyright'),source_receipt=n['receipt']));continue
   a=gap['before'][aid]['artwork'];ext=next(x for x in gap['identifiers'] if x['entity_id']==aid and x['scheme']=='staedel-object')
   cite=next(x for x in gap['citations'] if x['entity_id']==aid and x['field_name']=='museum_expansion_primary_metadata');note=json.loads(cite['evidence_note']);old=note['raw_source_record']['native_fields'];assert note['plan_sha256']==oldpin
   assert a['primary_media_id'] is None and a['status']!='archived' and a['creation_year_end']<=1970 and a['work_type']=='painting'
   for k in ['Title','Painter','Dimensions','Physical Description','Inventory Number','Institution','Creditline','Acquisition','Object Type']:
    assert {' '.join(v.split()) for v in props[k]}=={' '.join(old['fields'][k].split())},('Native field changed',aid,k)
   assert old['title']==a['title'] and old['creator']==a['unlinked_creator_label'] and old['date']==n['date'].lstrip(', ') and old['canonical']==n['canonical']==n['url']==ext['canonical_url']==cite['source_url']
   assert h.norm(props['Inventory Number'][0]).replace(' ','')==h.norm(a['accession_number']).replace(' ','')==ext['external_id']
   raw=gzip.decompress(Path(n['receipt']['body_path']).read_bytes());assert h.sha(raw)==n['receipt']['sha256'];sp=BeautifulSoup(raw,'html.parser')
   img=sp.select_one('meta[property="og:image"]')['content'];assert img==n['image'] and urlsplit(img).hostname=='cdn.staedelmuseum.de' and '/'+ext['external_id']+'/' in img
   pics=[x for x in sp.select('img[src]') if x['src']==img];assert pics and all(x.get('alt')==a['title']+', '+old['creator'] for x in pics)
   rights=load(E/'rights'/(aid+'.json'));rr=gzip.decompress(Path(rights['receipt']['body_path']).read_bytes());assert h.sha(rr)==rights['receipt']['sha256'] and parser.parse_download(json.loads(rr),n['url'])==rights['rights']
   global_matches=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=ANY(%s) AND lower(replace(external_id,' ',''))=%s) OR canonical_url=%s)",(['staedel-object','european-staedel-object'],ext['external_id'],n['url']))]
   acc=[dict(x) for x in db.execute("SELECT id::text,accession_number,title FROM artworks WHERE current_institution_id=%s AND lower(regexp_replace(accession_number,'[[:space:]]','','g'))=%s",(MID,ext['external_id']))]
   assert {x['entity_id'] for x in global_matches}=={aid} and {x['id'] for x in acc}=={aid}
   previous_raw=gzip.decompress((ROOT/note['body_path']).read_bytes());assert h.sha(previous_raw)==note['source_receipt']['sha256']
   basis='Exact native Städel inventory and canonical page, original checksum-pinned catalogue citation, creator label, title, date, dimensions, support, acquisition and credit agree. Primary page image alt and inventory path agree; same-image download statement explicitly PDM. Qualified and anonymous creators retained; no metadata, holding or current-display changes.'
   recon=dict(artwork_id=aid,identifier_matches=global_matches,accession_matches=acc,source_citation=cite,source_citation_sha256=h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode()),original_plan_sha256=oldpin,original_capture_sha256=note['source_receipt']['sha256'],compared_fields=['Title','Painter','Dimensions','Physical Description','Inventory Number','Institution','Creditline','Acquisition','Object Type','date','canonical'],editorial_confidence=.99,basis=basis)
   proof.append(recon)
   credit=props['Creditline'][0]+'. Image: Public Domain; Public Domain Mark 1.0, https://creativecommons.org/publicdomain/mark/1.0/. Full supplied frame proportionally resized and JPEG-compressed.'
   rows.append(dict(artwork_id=aid,native_id=ext['external_id'],current_source_id=ext['external_id'],title=a['title'],creator_label=old['creator'],source_url=n['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='staedel',expected_museum_id=MID,rights_status='public_domain',rights_label='Public Domain Mark 1.0',rights_basis='Exact native object Picture Copyright: Public Domain and per-image unrestricted PDM download statement, under original111-source registry per-record open-image policy. User authorization is separate from museum rights assertion.',source_credit=credit,image=dict(native_url=img,image_url=img,receipt=n['receipt'],source=dict(official_metadata=n,download_rights=rights,identity_reconciliation=recon,source_creator_label=old['creator'],source_date_label=old['date'],source_dimensions=props['Dimensions'][0])),plan_sha256=oldpin,identity_confidence=.99,identity_basis=basis,manual_visual_required=True))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=proof,original_plan_path=str(original),original_plan_sha256=oldpin,other_versions_preserved=True))
 save('research-holds.json',dict(at=h.now(),records=held,held_images_downloaded=0))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,policy_reference='Original111-source registry:staedel; docs/ARTLINE_IMAGE_USE.md general open-image policy',user_approval='Current bounded production image enrichment instruction',copyright_holder_licence=False,actual_museum_rights='Public Domain / Public Domain Mark1.0',actual_rights_labels_preserved=True,local_catalogue_read_only=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='staedel',batch=B,rows=rows,selection_basis='Exact existing gaps selected using native metadata and per-image PDM before downloading.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in rows:
  im=i.prepare_one(row,B);print(row['artwork_id'],im['state'],im.get('bytes'),im.get('flags'),im.get('reason'),flush=True)
 i.audit(B)
def deliver():
 configure();images,_,_=i.accepted(B);assert 0<len(images)<=100
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 recovery=load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
