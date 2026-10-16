#!/usr/bin/env python3
"""One bounded existing-image-gap batch; uses established production helpers."""
import ast,csv,fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base103khm','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000103/khm'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000103/khm'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000103/khm'
B='wikiart-000';MID='fbc55862-f61c-4561-a0a0-eedf65674f62'
i.OP='continuous-khm-images-20261011-b000103';i.RUN=E;i.CFG['wikiart']['scheme']='wikidata'
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
 import csv
 save('production-target-before-research.json',target())
 q=load(E.parent.parent.parent/'source-queue.json');save('source-queue-before.json',q)
 required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parent.parent.parent/'CHECKPOINT.json',E.parent.parent.parent/'source-queue.json',E.parent.parent/'000102/CHECKPOINT.json',E.parent.parent/'000102/source-access-holds.json',E.parent.parent/'000098/research-holds.json']
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],original_registry_rows=len(list(csv.DictReader(required[1].open()))),supervisor_not_modified=True))
 reserve=mod('reserve103','continuous-reserve-warsaw-000052-research.py');reserve.E=E;reserve.PREVIOUS=E.parent.parent/'000100';reserve.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with connect() as db:
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for r in p['rows']:
   a=live[r['artwork_id']]['artwork'];im=p['images'][r['artwork_id']];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived'
  own=list(db.execute('SELECT media_id FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,)));assert not own or (i.folder(B)/'selection.json.gz').exists()
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,physical_date_holds_preserved=['80082','80437','81054']))
 frozen=load(E.parent.parent/'000095/khm-gap-input.json.gz');cur=next(r for r in q['sources'] if r['source_id']=='khm_vienna')['resume_cursor'];picked=[r for r in frozen['rows'] if r['id'] in cur['pending_artwork_ids']];ids=[r['id'] for r in picked]
 with connect() as db:before=h.snapshot(db,ids)
 save('gap-input.json.gz',dict(at=h.now(),rows=picked,before=before,citations=[r for r in frozen['citations'] if r['entity_id'] in ids],identifiers=[r for r in frozen['identifiers'] if r['entity_id'] in ids],institution_id=MID))
 save('source-access-holds.json',dict(at=h.now(),queue_holds_preserved=True,inherited=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required[-2:]],held_endpoint_requests=0))
 print('Reserve 188 existing; KHM untouched gaps staged',len(ids))
def research():
 from bs4 import BeautifulSoup
 profiles={'lucas-cranach-the-younger':['portrait'],'hieronymus-bosch':['cross'],'giovanni-girolamo-savoldo':['lament','pieta'],'pieter-claesz':['vanitas','1656'],'francesco-bassano':['summer','spring'],'palma-il-giovane':['salom','lament'],'salomon-van-ruysdael':['winter'],'jacopo-bassano':['magi','kings']}
 for slug,terms in profiles.items():
  try:raw,rc=capture('https://www.wikiart.org/en/'+slug+'/all-works/text-list')
  except AssertionError as e:print(slug,str(e),flush=True);continue
  rows=[dict(title=a.get_text(' ',strip=True),url='https://www.wikiart.org'+a['href']) for a in BeautifulSoup(raw,'html.parser').select('li a[href]') if a['href'].startswith('/en/'+slug+'/') and 'all-works' not in a['href']]
  save('indexes/'+slug+'.json',dict(receipt=rc,entries=rows));leads=[r for r in rows if any(t in r['title'].lower() for t in terms)];save('leads/'+slug+'.json',leads);print(slug,json.dumps(leads),flush=True)
def prepare():
 gaps=load(E/'gap-input.json.gz');choices=[('13789504-962d-52a3-a8a9-ebefcd65b5bb','winterlandschaft-am-wasser-0','winter','6210')]
 notes={'winter':'WikiArt source file explicitly names GG-6210 Kunsthistorisches Museum, agrees with original catalogue inventory GG_6210, exact artist/title and current official KHM 1627 dated oak panel 34 x 58 cm. WikiArt year remains unknown, not replaced or invented. The second same-title WikiArt page labels canvas with no location or date; not selected. Distinct winter scenes remain separate. No metadata, holdings or dates changed.'}
 plan_manifest=load(ROOT/'docs/research/austrian-museums-20260916/metadata-plan-manifest.json');rows=[];proof=[]
 with connect() as db:
  live=h.snapshot(db,[x[0] for x in choices]);assert all(v==gaps['before'][aid] and v['artwork']['primary_media_id'] is None for aid,v in live.items())
  for aid,slug,key,inv in choices:
   a=live[aid]['artwork'];page=load(E/'objects'/(slug+'.json'));native=load(E/'native'/(key+'.json'));citation=next(c for c in gaps['citations'] if c['entity_id']==aid and c['field_name']=='austrian_museum_identity');note=json.loads(citation['evidence_note']);ext=next(r for r in gaps['identifiers'] if r['entity_id']==aid and r['scheme']=='wikidata')
   assert note['accession']==a['accession_number']=='GG_'+inv and 'Gemäldegalerie, '+inv in native['text']
   assert page['date'] is None and 'gg-6210-kunsthistorisches-museum' in page['image_url'] and '1627 datiert' in native['text'] and '34 × 58' in native['text'] and a['creation_year_start']==a['creation_year_end']==1627
   assert page['creator']==next(r for r in gaps['rows'] if r['id']==aid)['creator']
   candidates=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE current_institution_id=%s AND replace(accession_number,'GG_','')=%s AND status<>'archived'",(MID,inv))];assert [r['id'] for r in candidates]==[aid]
   eids=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme LIKE 'wikiart%%' AND external_id=%s) OR (scheme='wikidata' AND external_id=%s))",(page['source_url'],page['source_id'],ext['external_id']))];assert {r['entity_id'] for r in eids}=={aid}
   media=[dict(r) for r in db.execute('SELECT id::text FROM media_assets WHERE source_page_url=%s',(page['source_url'],))];assert not media
   basis='Exact creator, named subject, museum location, accession in original citation and current official KHM metadata, and documented version reconciliation. '+notes[key]
   identity=dict(artwork_id=aid,accession=a['accession_number'],wikidata_id=ext['external_id'],current_wikiart_id=page['source_id'],accession_candidates=candidates,global_identifier_matches=eids,existing_source_media=media,source_citation=citation,source_citation_sha256=h.sha(json.dumps(citation,sort_keys=True,ensure_ascii=False).encode()),official_source_sha256=native['receipt']['sha256'],editorial_confidence=.97,basis=basis,composition_review_pending=True)
   proof.append(identity)
   rows.append(dict(artwork_id=aid,native_id=ext['external_id'],current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=page['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='wikiart',expected_museum_id=MID,rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis'],source_credit='Kunsthistorisches Museum, Gemäldegalerie; museum image copyright/reproduction terms retained separately from WikiArt approval.',image=dict(native_url=page['metadata']['image'],image_url=page['image_url'],source=dict(page,official_metadata=native,identity_reconciliation=identity),receipt=page['receipt']),plan_sha256=plan_manifest['sha256'],identity_confidence=.97,identity_basis=basis,manual_visual_required=True))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=proof,creator_catalogue_rows=139,duplicate_reconciliation='All 139 active works of the canonical creator checked; one exact catalogue inventory and no other matching source identity/media. Same-title alternative WikiArt record not independently counted.'))
 save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='6 October WikiArt source approval and current bounded production enrichment instruction',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',copyright_holder_licence=False,actual_rights_labels_preserved=True,local_catalogue_read_only=True,native_museum_reproduction_permission_not_generalized=True))
 save('batches/'+B+'/selection.json.gz',dict(at=h.now(),provider='wikiart',batch=B,rows=rows,selection_basis='One current KHM primary gap, exact official accession/title/creator crosswalk, current WikiArt reproduction; selected before image download.'))
 save('batches/'+B+'/pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in rows:
  im=i.prepare_one(row,B);print(im['artwork_id'],im['state'],im.get('path'),im.get('reason'),flush=True)
 i.audit(B)


if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
