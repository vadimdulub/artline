#!/usr/bin/env python3
"""One bounded worker; external supervisor and historical plans stay unchanged."""
import csv, fcntl, gzip, importlib.util, json, subprocess, sys
from urllib.parse import urlsplit
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base43','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000043'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000043'
B='wikiart-000'
i.CFG['wikiart']['scheme']='wikidata'
i.OP='continuous-primary-images-20261011-b000043';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,R,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return load(p)
 h.save(p,value);return value
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def capture(url):
 assert urlsplit(url).hostname=='www.wikiart.org','Only approved unheld alternate provider here'
 key=h.sha(url.encode());rp=E/'source-captures'/(key+'.json');bp=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000043'/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert h.sha(raw)==rc['sha256'];return raw,rc
 assert not (E/'access-holds/www.wikiart.org.json').exists()
 i.provider_slot('www.wikiart.org');resp=i.session().get(url,timeout=(15,45),allow_redirects=False);raw=resp.content
 bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0))
 rc=dict(url=url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),retry_after=resp.headers.get('Retry-After'))
 h.save(rp,rc)
 if resp.status_code in [401,403,429]:save('access-holds/www.wikiart.org.json',rc)
 assert resp.status_code==200,resp.status_code
 return raw,rc
i.m.m.capture=capture
def research():
 from bs4 import BeautifulSoup
 from urllib.parse import urljoin
 pages={}
 for profile in ['charles-conder','julian-ashton']:
  url='https://www.wikiart.org/en/'+profile+'/all-works/text-list';raw,rc=capture(url);sp=BeautifulSoup(raw,'html.parser');entries=[]
  for li in sp.select('li'):
   for a in li.select('a[href]'):
    link=urljoin(url,a['href'])
    if link.startswith('https://www.wikiart.org/en/'+profile+'/') and 'all-works' not in link:entries.append(dict(title=a.get_text(' ',strip=True),text=li.get_text(' ',strip=True),url=link))
  pages[profile]=dict(receipt=rc,entries=entries)
 save('wikiart-index-research.json',pages)
 for profile,title in [('charles-conder','The hot sands, Mustapha, Algiers'),('julian-ashton','The prospector')]:
  entries=[x for x in pages[profile]['entries'] if h.norm(x['title'])==h.norm(title)];assert len(entries)==1
  page=i.m.m.wiki_fields(entries[0]['url']);save('wikiart-'+profile+'-object.json',page)
  print(json.dumps(dict(profile=profile,title=page['title'],date=page['date'],fields=page['fields'],image_url=page['image_url'],metadata_image=page['metadata']['image'],rights_label=page['rights_label'],source_id=page['source_id'])))
def prepare():
 candidates=[('charles-conder','345b3633-fa29-5b97-a366-722ac93efdf0'),('julian-ashton','39f03d16-2162-5bc6-9381-0112538f1904')]
 prior=load(E/'nsw-live-gap-reconciliation.json');rows=[];checks=[]
 if not (i.folder(B)/'selection.json.gz').exists():
  with connect() as db:
   current=h.snapshot(db,[aid for _,aid in candidates])
   for profile,aid in candidates:
    assert current[aid]==prior['before'][aid],'Concurrent changes require review'
    a=current[aid]['artwork'];assert a['primary_media_id'] is None and a['status']!='archived'
    page=load(E/('wikiart-'+profile+'-object.json'));rc=page['receipt'];assert rc['status']==200 and h.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256']
    assert page['title']==a['title'] and page['date']['first']==a['creation_year_start'] and page['date']['last']==a['creation_year_end']<=1955
    assert page['fields']['Location']=='Art Gallery of New South Wales (AGNSW), Sydney, Australia'
    assert page['artist_url']=='https://www.wikiart.org/en/'+profile
    assert urlsplit(page['metadata']['image']).path==urlsplit(page['image_url']).path.split('!')[0]
    note=next(json.loads(c['evidence_note']) for c in prior['citations'] if c['entity_id']==aid)
    entity=note.get('source_entity') or note['raw_source_record']['entity'];qid=entity['id']
    values={k:[x.get('mainsnak',{}).get('datavalue',{}).get('value') for x in v if x.get('rank')!='deprecated'] for k,v in entity['claims'].items()}
    oldrc=note['source_receipt'];oldbody=ROOT/oldrc.get('body_path',note.get('body_path',''));raw=gzip.decompress(oldbody.read_bytes());assert h.sha(raw)==oldrc['sha256']
    assert json.loads(raw)['entities'][qid]==entity
    assert [x['external_id'] for x in prior['identifiers'] if x['entity_id']==aid and x['scheme']=='wikidata']==[qid]
    duplicate=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikiart-artwork' AND external_id=%s) OR canonical_url=%s OR (scheme='wikidata' AND external_id=%s))",(page['source_id'],page['source_url'],qid))]
    assert all(x['entity_id']==aid for x in duplicate),'Other catalogue record uses selected source identity'
    media=[dict(x) for x in db.execute('SELECT id::text,source_page_url FROM media_assets WHERE source_page_url=%s',(page['source_url'],))];assert not media,'Existing exact source image requires duplicate review'
    titles=[dict(x) for x in db.execute('SELECT id::text,title,unlinked_creator_label,current_institution_id::text FROM artworks WHERE normalized_title=%s',(a['normalized_title'],))]
    same=[x for x in titles if x['current_institution_id']==a['current_institution_id']];assert len(same)==1 and same[0]['id']==aid
    primary=current[aid]['creators']
    if primary:
     assert len(primary)==1 and primary[0]['attribution_role']=='primary'
     artist=db.execute('SELECT display_name FROM artists WHERE id=%s',(primary[0]['artist_id'],)).fetchone();assert artist['display_name']==page['creator']
    else:assert a['unlinked_creator_label']==page['creator']
    if profile=='charles-conder':
     assert values['P217']==['1.1982'] and '/1-1982-s.jpg' in page['metadata']['image']
     basis='Exact distinctive title, Charles Conder, 1891, NSW collection and museum accession 1.1982 encoded in the actual WikiArt source image filename. Saved accession/object source and current catalogue globally reconciled. Source dimensions differ (Wikidata 63 x 72 cm versus WikiArt 46 x 55.3 cm); no invented frame explanation and no metadata rewrite. Image filename explicitly ties to exact accession. WikiArt genre still life retained only as source evidence; no classification update.'
    else:
     assert values['P217']==['4554']
     basis='Exact title The prospector, Julian Ashton, 1889 and Art Gallery of New South Wales location agree with saved object Q20425894, native inventory 4554 and museum-referenced source. Explicit source artwork URL and one full primary reproduction; same-title objects scoped and native object crosswalk checked globally. Existing unlinked creator label stays unchanged.'
    checks.append(dict(artwork_id=aid,wikidata=qid,original_citation_sha256=h.sha(json.dumps(note,sort_keys=True).encode()),original_source_sha256=oldrc['sha256'],source_values=values,wikiart_id=page['source_id'],page_sha256=rc['sha256'],duplicate_identifiers=duplicate,same_title_rows=titles,source_image_rows=media,identity_basis=basis,editorial_confidence=.97))
    rows.append(dict(artwork_id=aid,native_id=qid,current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=page['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='wikiart',expected_museum_id=a['current_institution_id'],expected_primary_artist_id=primary[0]['artist_id'] if primary else None,rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis'],image=dict(native_url=page['metadata']['image'],image_url=page['image_url'],source=page,receipt=rc),plan_sha256=note['plan_sha256'],identity_confidence=.97,identity_basis=basis,manual_visual_required=True))
  save('global-identity-reconciliation.json',dict(at=h.now(),records=checks))
  save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,user_approval='WikiArt source approved 6 October 2026; current continuous production enrichment authorized',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',copyright_holder_licence=False,actual_rights_labels_preserved=True,local_catalogue_read_only=True))
  h.save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='wikiart',batch=B,rows=rows,selection_basis='Two NSW exact-object primary gaps from saved 35-record queue; WikiArt object evidence selected before download.'))
  h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in i.selected(B)['rows']:print(json.dumps(i.prepare_one(row,B)),flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
def deliver():
 images,_,_=i.accepted(B);assert 1<=len(images)<=2
 assert load(E/'independent-prewrite-verification.json')['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL'
 save('cloud-backup.json',backup)
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-database-write.json',target(True));i.apply(B)
def preflight():
 save('production-target-reconciliation.json',target())
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(regpath.open()));assert len(registry)==111
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(regpath),registry_sha256=h.sha(regpath.read_bytes()),registry_rows=111,complete_registry=registry,precedence='Current production authorization supersedes old local writes. External supervisor untouched.'))
 queue=load(E.parents[1]/'source-queue.json');save('source-queue-before.json',queue)
 ledgers=list(E.parent.glob('*/source-access-holds.json'))+list((ROOT/'docs/research/illustrated-300k-20261011/access-holds').glob('*.json'))
 save('source-access-holds.json',dict(at=h.now(),inherited=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),data=load(p)) for p in ledgers if p.parent!=E],queue_holds=[r for r in queue['sources'] if 'hold' in r['status'] or '403' in r['status']],policy='No NSW direct requests; WikiArt alternate provider approval is separate. No held routes retried.'))
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=load(pp);rows=p['rows'];assert len(rows)==188
 main=ROOT/'docs/research/french-printmaking-20261011';old=load(main/'delivery-plan.json.gz');top=load(main/'scope-topup/delivery-plan.json.gz')
 assert {r['artwork_id'] for r in rows}==set(old['eligible_reserve'])-{r['artwork_id'] for r in top['rows']}
 visual={}
 for path in (main/'visual-decisions').glob('*.json'):
  dec=load(path);sheet=load(main/'visual-sheets'/path.name)
  if not any(im['artwork_id'] in {r['artwork_id'] for r in rows} for im in sheet['images']):continue
  assert dec['sheet_sha256']==h.sha(Path(sheet['sheet']).read_bytes())
  for im in sheet['images']:
   if im['artwork_id'] in dec['approved']:visual[im['artwork_id']]=dict(decision=str(path.relative_to(ROOT)),decision_sha256=h.sha(path.read_bytes()),sheet=sheet['sheet'],sheet_sha256=dec['sheet_sha256'],image_sha256=im['sha256'])
 checks=[]
 for r in rows:
  op=ROOT/r['source_record_reference'];assert h.sha(op.read_bytes())==r['source_record_sha256'];o=load(op)
  for key,receiptkey in [('raw','receipt'),('manifest','manifest_receipt')]:
   rc=o[receiptkey];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'] and json.loads(raw)==o[key]
  im=p['images'][r['artwork_id']];assert visual[r['artwork_id']]['image_sha256']==im['sha256']
  checks.append(dict(artwork_id=r['artwork_id'],native_id=r['native_id'],source_sha256=r['source_record_sha256'],prior_actual_visual_review=visual[r['artwork_id']]))
 save('independent-french-reserve-evidence-verification.json',dict(at=h.now(),records=checks,source_capture_checks=376,prior_review_reused_without_new_view_claim=True,immutable_plans=[dict(path=str(x.relative_to(ROOT)),sha256=h.sha(x.read_bytes())) for x in [pp,main/'delivery-plan.json.gz',main/'scope-topup/delivery-plan.json.gz']]))
 oldE=E.parent/'000042';previous=load(oldE/'batch-verification-receipt.json');ids=previous['production_ids']
 with connect() as db:
  live=h.snapshot(db,[r['artwork_id'] for r in rows]);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(list(live),))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==h.sha(pp.read_bytes()) for x in cit)
  for r in rows:
   a=live[r['artwork_id']]['artwork'];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==p['images'][r['artwork_id']]['media_id'] and a['status']!='archived'
  prev=h.snapshot(db,ids);ev=[dict(x) for x in db.execute('SELECT a.id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(prev)==len(ev)==7
  for x in ev:
   note=x['evidence_json'];note=json.loads(note) if isinstance(note,str) else note;assert note['selection_sha256']==previous['image_selection_sha256']
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists()
  pool=load(E.parent/'000041/nsw-bounded-gap-input.json');states=h.snapshot(db,[r['id'] for r in pool['rows']]);conder='b4102d86-a457-5c15-8d8e-f607ce9f539a'
  artworks=[dict(x) for x in db.execute('SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text,a.current_institution_id::text,a.creation_year_start,a.creation_year_end FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s ORDER BY a.id LIMIT 300',(conder,))]
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(states),))]
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(states),))]
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,new_programme_increments=0,plan_sha256=h.sha(pp.read_bytes()),source_citations=cit,live_rows=live,selected=0,physical_date_holds_preserved=['80082','80437','81054'],next_action='Switch to NSW image gaps via approved WikiArt matching; do not replay French reserve.'))
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=42,rows=prev,rights_evidence=ev,previous_increments_counted=0,current_batch_existing_rights=own))
 save('nsw-live-gap-reconciliation.json',dict(at=h.now(),before=states,identifiers=identifiers,citations=citations,conder_catalogue=artworks))
 print(json.dumps(dict(french_reserve_already_delivered=188,prior_batch_verified=7,nsw_gaps=len(states),conder_catalogue=artworks)))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
