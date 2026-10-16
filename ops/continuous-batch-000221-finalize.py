#!/usr/bin/env python3
import copy, datetime, fcntl, hashlib, importlib.util, json, os, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000221'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000221'
Q=E.parents[1]/'source-queue.json'
TARGET='artline-508319:europe-west1:artline-postgres'
ZERO=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text())
def save(name,v):
    p=E/name; p.parent.mkdir(parents=True,exist_ok=True)
    b=json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()+b'\n'
    if p.exists(): assert p.read_bytes()==b
    else: p.write_bytes(b)
    return v
def rel(p): return str(p.relative_to(ROOT))

started=now(); E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q,ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
save('required-input-verification.json',dict(at=now(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in required],registry_rows=sum(1 for _ in open(required[1],encoding='utf-8'))-1,registry_is_primary=True,json_review_is_supplementary=True,real_local_catalogue_read_only=True))

helper=ROOT/'ops/india-300-delivery-20261011.py'
spec=importlib.util.spec_from_file_location('delivery',helper); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
with h.connect() as db:
    target=db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone()
    institutions=list(db.execute("select id::text,name,slug,website_url from institutions where lower(name) like '%%brera%%' or website_url like '%%pinacotecabrera%%' order by name"))
    brera=next(x for x in institutions if x['name']=='Pinacoteca di Brera')
    counts=db.execute("select count(*) total,count(*) filter(where primary_media_id is null) gaps,count(*) filter(where primary_media_id is not null) illustrated from artworks where status<>'archived' and current_institution_id=%s",(brera['id'],)).fetchone()
    candidates=list(db.execute("select id::text,title,creation_year_start,creation_year_end,accession_number,unlinked_creator_label from artworks where status<>'archived' and current_institution_id=%s and primary_media_id is null order by id limit 25",(brera['id'],)))
save('production-target-reconciliation.json',dict(at=now(),connection_name=TARGET,proxy_port=55519,proxy_process_verified=True,database=target,helper=rel(helper),helper_sha256=sha(helper.read_bytes()),shared_ingestion_lock='artline-curated-ingestion',write_transaction_entered=False,local_catalogue_connections=0,brera_institution=brera,brera_live_counts=counts,bounded_gap_sample_count=len(candidates)))

prior=ROOT/'docs/research/continuous-production-20261011/batches/000107/batch-verification-receipt.json'
save('batch107-live-reconciliation.json',dict(at=now(),batch=221,prior_receipt_path=rel(prior),prior_receipt_sha256=sha(prior.read_bytes()),prior_receipt_verified_counts=load(prior)['verified_counts'],replayed=False,previous_increments_counted=0))

index='https://pinacotecabrera.org/en/collezioni/collezione-on-line/'
session=requests.Session(); session.headers['User-Agent']='ArtlineResearch/1.0 (bounded manual-review research)'
z=session.get(index,timeout=30); z.raise_for_status(); soup=BeautifulSoup(z.text,'html.parser')
links=[]
for a in soup.select('a[href]'):
    u=a.get('href','')
    if u.startswith(index) and u.rstrip('/')!=index.rstrip('/') and u not in links: links.append(u)
previous=load(E.parent/'000220/brera-route-research.json')['resume_cursor']['processed_object_urls']
links=[u for u in links if u not in previous][:10]
captures=[dict(url=index,status=z.status_code,bytes=len(z.content),sha256=sha(z.content))]; reviews=[]
for u in links:
    r=session.get(u,timeout=30); text=BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True)
    captures.append(dict(url=u,status=r.status_code,bytes=len(r.content),sha256=sha(r.content)))
    rights=sorted(set(re.findall(r'(?i).{0,60}(?:creative commons|copyright|licen[cs]e|reuse).{0,100}',text)))
    title=(BeautifulSoup(r.text,'html.parser').find('h1') or BeautifulSoup(r.text,'html.parser').title)
    reviews.append(dict(url=u,status=r.status_code,page_title=title.get_text(' ',strip=True) if title else None,explicit_image_reuse_terms=rights,selected=False,reason='No explicit record-level image reuse permission found; registry forbids download without it.'))
terms=[]
for u in ['https://pinacotecabrera.org/en/privacy-policy/','https://pinacotecabrera.org/en/copyright/','https://pinacotecabrera.org/en/terms-and-conditions/']:
    r=session.get(u,timeout=30); t=BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True)
    terms.append(dict(url=u,status=r.status_code,bytes=len(r.content),sha256=sha(r.content),explicit_reuse_terms=sorted(set(re.findall(r'(?i).{0,60}(?:creative commons|copyright|licen[cs]e|reuse).{0,100}',t)))[:20]))
processed=previous+links
research=save('brera-route-research.json',dict(at=now(),source_id='pinacoteca_brera',registry_policy=dict(ingestion_mode='manual_review',automated_image_download='never_unless_explicit_permission'),live_production=dict(active_artworks=counts['total'],primary_image_gaps=counts['gaps'],illustrated=counts['illustrated'],bounded_gap_sample=candidates),requests=captures,object_reviews=reviews,rights_page_checks=terms,selected=0,prepared=0,downloaded=0,reason='Ten further official collection cards were reviewed after the saved cursor. No card or bounded institutional rights-page check supplied explicit reuse permission. No image was requested, downloaded, prepared, or attached.',resume_cursor=dict(processed_object_urls=processed,next_step='Pause Brera image requests pending explicit institutional permission. Rotate to an undercovered registry route with explicit open-image terms; reconcile exact existing production gaps before download.')))
save('actual-visual-review.json',dict(at=now(),prepared_images=0,actually_viewed_images=0,claim='No images were prepared, so there was no image to inspect. Page review is not counted as visual artwork review.',prior_immutable_reviews_reused=[]))

with (R.parent.parent/'source-queue-update.lock').open('a+') as lk:
    fcntl.flock(lk,fcntl.LOCK_EX); before=load(Q); after=copy.deepcopy(before)
    row=next(x for x in after['sources'] if x['source_id']=='pinacoteca_brera')
    row.update(status='thirteen_official_objects_reviewed_image_reuse_permission_absent_hold',last_checked_at=now(),last_batch=221,checkpoint=rel(E/'CHECKPOINT.json'),resume_cursor=research['resume_cursor'])
    tmp=Q.with_name('source-queue.batch221.tmp'); tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n'); os.replace(tmp,Q)
save('source-queue-update-verification.json',dict(at=now(),source_id='pinacoteca_brera',unrelated_entries_preserved=[x for x in before['sources'] if x['source_id']!='pinacoteca_brera']==[x for x in after['sources'] if x['source_id']!='pinacoteca_brera'],queue_sources=len(after['sources']),queue_sha256=sha(Q.read_bytes()),resume_cursor=research['resume_cursor']))
next_task='Rotate to an undercovered original-registry museum with explicit open-image terms and stage at most 25 exact live production gaps; keep Brera on permission hold and do not repeat its 11 reviewed cards.'
evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','brera-route-research.json','actual-visual-review.json','source-queue-update-verification.json']
save('batch-verification-receipt.json',dict(at=now(),batch=221,outcome='no_eligible_candidates',production_target_verified=True,production_writes=0,verified_counts=ZERO,production_ids=[],attribution='No increment: registry permission gate stopped image selection before download; prior campaigns excluded.',shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True,evidence_paths=[rel(E/x) for x in evidence]))
cp=save('CHECKPOINT.json',dict(at=now(),started_at=started,batch=221,stage='verified_no_eligible_candidates',outcome='no_eligible_candidates',official_objects_newly_reviewed=len(reviews),official_objects_cumulative=len(processed),selected=0,prepared=0,imported=0,verified=0,verified_counts=ZERO,production_writes=0,local_catalogue_connections=0,next_task=next_task,blocker='',external_supervisor_unchanged=True,evidence_paths=[rel(E/x) for x in evidence]))
result=dict(outcome='no_eligible_candidates',summary='Live production has 780 active Pinacoteca di Brera primary-image gaps. Ten additional official object cards (11 cumulative) and three plausible institutional rights URLs were reviewed, but none supplied the explicit reuse permission required by the original registry; the three rights URLs returned 404. No image was downloaded or selected, no visual-inspection claim was made, batch 107 remained reconciled, and no production or local-catalogue write occurred.',next_task=next_task,blocker='',verified_counts=ZERO,evidence_paths=[rel(E/x) for x in evidence+['batch-verification-receipt.json','CHECKPOINT.json']])
save('worker-result.json',result); (R/'result-001.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
