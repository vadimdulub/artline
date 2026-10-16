#!/usr/bin/env python3
"""Batch 188: schema-anchored Tretyakov SSR extraction and bounded icon review."""
import copy,csv,datetime,fcntl,gzip,hashlib,json,os,re,subprocess,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000188'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000188'
Q=E.parents[1]/'source-queue.json'; REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
CAP=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000187/tretyakov-masterpiece-index.html.gz'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
registry=list(csv.DictReader(REG.open()));assert len(registry)==111
required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
save(E/'required-input-verification.json',dict(at=now(),files=[dict(path=p,sha256=sha((ROOT/p).read_bytes()),bytes=(ROOT/p).stat().st_size) for p in required],registry=dict(path=str(REG),sha256=sha(REG.read_bytes()),rows=111),latest_hold_ledgers=[str(p.relative_to(ROOT)) for p in sorted(E.parent.glob('*/source-access-holds.json'))[-10:]],rules='Local catalogue read-only; Translation prohibited; bounded worker only.'))
proxy=subprocess.check_output(['ps','aux'],text=True);pline=next(x for x in proxy.splitlines() if '/tmp/artline-cloud-sql-proxy' in x and '--port 55519' in x);assert 'artline-508319:europe-west1:artline-postgres' in pline
helper=ROOT/'ops/india-300-delivery-20261011.py'
b107=E.parent/'000107'; receipts=sorted(str(p.relative_to(ROOT)) for p in b107.glob('*.json') if any(x in p.name for x in ['verification','receipt','CHECKPOINT']))
save(E/'production-target-reconciliation.json',dict(at=now(),proxy=dict(port=55519,target='artline-508319:europe-west1:artline-postgres',verified=True),helper=dict(path=str(helper.relative_to(ROOT)),sha256=sha(helper.read_bytes()),shared_lock='artline-curated-ingestion'),batch107_receipts=receipts,batch107_reconciled_by='docs/research/continuous-production-20261011/batches/000128/README.md',write_mode='not_entered_no_selected_images',local_catalogue_connections=0))
q=load(Q);route=next(x for x in q['sources'] if x['source_id']=='tretyakov_gallery');completed=set(route['resume_cursor']['completed_source_ids'])
raw=gzip.decompress(CAP.read_bytes());assert sha(raw)==route['resume_cursor']['index_sha256'];text=raw.decode('utf-8')
# Exact Nuxt object schema prefix: object begins with numeric id, literal code and literal name.
pat=re.compile(r'\{id:(\d+),code:"((?:\\.|[^"\\])*)",name:"((?:\\.|[^"\\])*)",author:')
objects=[]
for m in pat.finditer(text):
 oid,code,name=m.groups(); name=json.loads('"'+name+'"');code=json.loads('"'+code+'"')
 if oid not in completed and re.search(r'икон|богомат|спас|апостол|архангел|свят|деисус|евангел',name,re.I): objects.append(dict(source_id=oid,code=code,name=name,offset=m.start()))
dedup={x['source_id']:x for x in objects}; shard=sorted(dedup.values(),key=lambda x:x['offset'])[:12]
captures=[];holds=[]
for row in shard:
 url='https://my.tretyakov.ru/app/masterpiece/'+row['source_id'];req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0'})
 try:
  with urllib.request.urlopen(req,timeout=30) as res: body=res.read();status=res.status;ctype=res.headers.get('Content-Type')
  p=R/(row['source_id']+'.html.gz');p.write_bytes(gzip.compress(body));captures.append(dict(**row,url=url,status=status,content_type=ctype,bytes=len(body),sha256=sha(body),capture_path=str(p)))
  holds.append(dict(source_id=row['source_id'],title=row['name'],reason='Official image remains rights-managed and registry forbids automated download; object metadata requires exact inventory/date/creator extraction before any catalogue action. No image requested.'))
 except Exception as ex: holds.append(dict(source_id=row['source_id'],title=row['name'],reason='Bounded object fetch failed; no retry in this batch',error=type(ex).__name__))
save(E/'tretyakov-schema-extraction.json',dict(at=now(),capture_path=str(CAP),raw_sha256=sha(raw),gzip_sha256=sha(CAP.read_bytes()),schema='Nuxt object literal prefix {id:<integer>,code:<json string>,name:<json string>,author:',explicit_object_tuples=len({m.group(1) for m in pat.finditer(text)}),icon_candidates_excluding_completed=len(dedup),selected_shard=shard,completed_ids_excluded=sorted(completed),unsafe_positional_alias_resolution=False))
save(E/'independent-source-verification.json',dict(at=now(),provider='tretyakov_gallery',registry_policy=dict(ingestion_mode='manual_review',automated_image_download='never',image_rights='rights-managed unless explicitly released'),captures=captures,holds=holds,images_requested=0,images_downloaded=0,visual_review=dict(files_viewed=0,reason='No eligible image was released or downloaded; file checks are not represented as visual review.'),production_writes=0))
before=copy.deepcopy(q)
with open(str(Q)+'.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=load(Q);route=next(x for x in q['sources'] if x['source_id']=='tretyakov_gallery');route['status']='official_ssr_schema_extracted_bounded_icon_shard_metadata_held_no_image_release';route['last_checked_at']=now();route['checkpoint']='docs/research/continuous-production-20261011/batches/000188/CHECKPOINT.json';route['resume_cursor']['schema_cursor_offset']=shard[-1]['offset'] if shard else route['resume_cursor'].get('schema_cursor_offset',0);route['resume_cursor']['reviewed_metadata_ids']=list(dict.fromkeys(route['resume_cursor'].get('reviewed_metadata_ids',[])+[x['source_id'] for x in shard]));route['resume_cursor']['next_step']='Rotate to an undercovered permitted source with explicit open image release; preserve Tretyakov rights hold and do not repeat these IDs.';route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+['docs/research/continuous-production-20261011/batches/000188/tretyakov-schema-extraction.json','docs/research/continuous-production-20261011/batches/000188/independent-source-verification.json']));tmp=Q.with_suffix('.188.tmp');save(tmp,q);os.replace(tmp,Q)
save(E/'source-queue-update-verification.json',dict(at=now(),source_id='tretyakov_gallery',unrelated_entries_preserved=all(next(y for y in q['sources'] if y['source_id']==x['source_id'])==x for x in before['sources'] if x['source_id']!='tretyakov_gallery'),reviewed_ids=[x['source_id'] for x in shard],resume_cursor=route['resume_cursor']))
counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']};nxt='Select a bounded existing primary-image-gap shard from an undercovered registry source with explicit open image release (prefer Cleveland CC0 or Rijksmuseum), excluding completed cursors and all provider holds.'
cp=dict(at=now(),batch=188,stage='complete_no_eligible_candidates',discovered=len(dedup),selected=0,prepared=0,imported=0,verified_counts=counts,holds=dict(tretyakov_rights_managed_metadata_rows=len(shard),images_not_requested=True),next_task=nxt,blocker='',evidence=[str((E/x).relative_to(ROOT)) for x in ['required-input-verification.json','production-target-reconciliation.json','tretyakov-schema-extraction.json','independent-source-verification.json','source-queue-update-verification.json']])
save(E/'CHECKPOINT.json',cp);save(E/'batch-verification-receipt.json',cp);save(R/'CHECKPOINT.json',cp)
files=[p for p in sorted(E.glob('*.json')) if p.name!='independent-final-artifact-verification.json'];save(E/'independent-final-artifact-verification.json',dict(at=now(),files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes())) for p in files],runtime_checkpoint_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),production_writes=0,verified_counts=counts))
result=dict(outcome='no_eligible_candidates',summary=f'Parsed the checksum-pinned Tretyakov Nuxt index with an explicit object-schema anchor and reviewed {len(shard)} fresh icon-related object routes. The registry marks Tretyakov images rights-managed and forbids automated image download; no image was explicitly released, so no visual claim or unsafe production write was made.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence']+[str((E/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'independent-final-artifact-verification.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]);save(R/'worker-result.json',result);print(json.dumps(result))
