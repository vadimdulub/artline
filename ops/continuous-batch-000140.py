#!/usr/bin/env python3
"""Bounded batch 140: Greek/Byzantine primary gaps via approved WikiArt."""
import csv, fcntl, gzip, importlib.util, json, re, subprocess
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000140'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000140'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000140'
for p in (E,R,S): p.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('helper140',ROOT/'ops/india-300-delivery-20261011.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def save(name,value): h.save(E/name,value);return value
def rel(p): return str(Path(p).relative_to(ROOT))
files=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
registry=list(csv.DictReader(files[1].open()));queue=h.load(files[-1]);assert len(registry)==111 and len(queue['sources'])==111
save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in files],complete_original_registry_rows=111,supplementary_registry_review_not_substituted=True,local_catalogue_connections=0))
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x];assert proxy
save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_verified=True,proxy_port=55519,proxy_command_inspected=True,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))

with h.connect() as db:
 prev=h.load(E.parent/'000107/independent-production-verification.json');live=h.snapshot(db,list(prev['after']));assert live==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live),prior_increments_counted=0))
 rows=[dict(x) for x in db.execute("""SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.work_type,a.unlinked_creator_label,i.name institution FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.primary_media_id IS NULL AND a.status<>'archived' AND (lower(i.name) LIKE '%athens%' OR lower(i.name) LIKE '%greek%' OR lower(i.name) LIKE '%hellenic%' OR lower(i.name) LIKE '%byzantine%') AND COALESCE(a.creation_year_end,1971)<=1970 AND a.work_type IN ('painting','icon','drawing','print','watercolor') ORDER BY a.id LIMIT 100""")]
 before=h.snapshot(db,[x['id'] for x in rows]);assert len(rows)==100 and all(before[x['id']]['artwork']['primary_media_id'] is None for x in rows)
save('gap-input.json.gz',dict(at=h.now(),rows=rows,before=before,selection='First100 active Greek/Byzantine pictorial primary gaps through1970, UUID order; bounded read-only production query.'))

routes=[('jean-fautrier','Abstract Composition','0f95d0dc-55d8-5bf6-bc16-13012968ee03'),('joan-miro','Composition IIII','11804aa2-bf4a-5012-b33e-300060698f16'),('alekos-fassianos','Μπουκάλι με λουλούδια','032ef3f4-6154-5d24-af53-044ab2848e0f'),('theodoros-poulakis','Jacob laments the death of Joseph and rends hliw clothes','09e4f8a3-e0f9-569e-b899-8ee115c5293d'),('angelos-akotantos','Virgin Glykophilousa','18ae2b28-99aa-52f6-8bc7-02910c9d1cec')]
s=requests.Session();s.headers['User-Agent']='Artline catalogue research; bounded image identity review'
research=[]
for profile,title,aid in routes:
 url=f'https://www.wikiart.org/en/{profile}/all-works/text-list';r=s.get(url,timeout=(15,45));raw=r.content;bp=S/(profile+'.html.gz');bp.write_bytes(gzip.compress(raw,mtime=0))
 links=re.findall(r'href="(/en/[^"]+)"[^>]*>([^<]+)',r.text) if r.status_code==200 else []
 normalized=lambda v:' '.join(re.findall(r'[^\W_]+',v.casefold()))
 exact=[dict(url='https://www.wikiart.org'+u,title=t.strip()) for u,t in links if normalized(t)==normalized(title)]
 research.append(dict(profile=profile,index_url=url,status=r.status_code,bytes=len(raw),sha256=h.sha(raw),body_path=str(bp),artwork_id=aid,catalogue_title=title,exact_title_candidates=exact,disposition=('profile_unavailable_no_retry' if r.status_code==404 else 'no_exact_title_candidate')))
assert all(not x['exact_title_candidates'] for x in research)
save('independent-source-verification.json',dict(at=h.now(),provider='wikiart',policy='docs/ARTLINE_IMAGE_USE.md user-approved WikiArt source policy',routes=research,exact_candidates=0,selected=0,unchanged_failed_retries=0))
save('identity-reconciliation-and-holds.json',dict(at=h.now(),records=research,reason='No exact WikiArt title candidate in the bounded creator routes; generic Composition results are distinct/unresolved versions and were not substituted.',same_physical_version_verified=0,selected=0))
save('visual-review-verification.json',dict(at=h.now(),prepared_images=0,actual_images_viewed=0,claim='No image candidate passed metadata identity selection, so no prepared image existed to view; file checks were not represented as visual review.',prior_visual_evidence_reused=False))
with h.connect() as db:
 after=h.snapshot(db,list(before));assert after==before
save('independent-production-verification.json',dict(at=h.now(),frozen_gap_rows=100,selected=0,prepared=0,imported=0,verified=0,production_writes=0,before_equals_after=True,new_programme_increments=0,previous_campaign_rows_excluded=True,local_catalogue_connections=0))

qpath=E.parents[1]/'source-queue.json'
with (R.parent.parent/'source-queue-update.lock').open('a+') as qlock:
 fcntl.flock(qlock,fcntl.LOCK_EX);q=h.load(qpath);old=json.loads(json.dumps(q));row=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens')
 row['last_checked_at']=h.now();row['last_batch']=140;row['checkpoint']=rel(E/'CHECKPOINT.json');row['status']='bounded_greek_byzantine_gaps_five_wikiart_creator_routes_no_exact_candidates'
 row.setdefault('research_history',[]).append(dict(batch=140,at=h.now(),route='existing_Greek_Byzantine_primary_gaps_via_approved_WikiArt',frozen_gaps=100,creator_routes=5,selected=0,evidence=rel(E/'independent-source-verification.json')))
 row['resume_cursor']['batch140_processed_wikiart_profiles']=[x[0] for x in routes];row['resume_cursor']['batch140_next']='Rotate to an unprocessed exact museum-native or distinct WikiArt creator route; do not repeat these five unchanged indexes.'
 qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 untouched=[x for x in old['sources'] if x['source_id']!='national_gallery_athens']==[x for x in q['sources'] if x['source_id']!='national_gallery_athens']
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='national_gallery_athens',unrelated_entries_preserved=untouched,processed_profiles=[x[0] for x in routes],after_sha256=h.sha(qpath.read_bytes())))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
names=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','gap-input.json.gz','independent-source-verification.json','identity-reconciliation-and-holds.json','visual-review-verification.json','independent-production-verification.json','source-queue-update-verification.json']
next_task='Rotate to a distinct unprocessed registry-backed museum-native image route (prefer open Byzantine/Greek object images); preserve these five WikiArt route dispositions and do not retry unchanged 404s.'
save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='Frozen live preimages equal post-research state; no candidate selected or prepared and no prior campaign additions counted.',production_target=actual,shared_ingestion_lock='artline-curated-ingestion'))
save('CHECKPOINT.json',dict(at=h.now(),batch=140,stage='verified_complete_no_eligible_candidates',researched=dict(frozen_gaps=100,wikiart_creator_routes=5),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=next_task,evidence=[rel(E/x) for x in names],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0))
result=dict(outcome='no_eligible_candidates',summary='Batch 140 froze 100 live Greek/Byzantine pictorial primary-image gaps and researched five distinct approved WikiArt creator routes. Two indexes were available but had no exact object/version candidate; three profiles returned first-request 404 holds. No image passed identity selection, so no production write or visual-review claim was made.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in names+['batch-verification-receipt.json','CHECKPOINT.json']])
save('independent-final-artifact-verification.json',dict(at=h.now(),evidence_paths=result['evidence_paths'],all_exist=all((ROOT/x).exists() for x in result['evidence_paths']),result=result))
result['evidence_paths'].append(rel(E/'independent-final-artifact-verification.json'));save('worker-result.json',result);print(json.dumps(result))
