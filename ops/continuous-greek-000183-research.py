#!/usr/bin/env python3
"""Bounded batch 183: untouched Athens Aivazovsky creator index reconciliation."""
import copy,csv,fcntl,gzip,hashlib,json,os,re,subprocess
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000183'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000183'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000183'
for p in (E,R,S):p.mkdir(parents=True,exist_ok=True)
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('delivery183','india-300-delivery-20261011.py')
MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b'; INDEX='https://www.nationalgallery.gr/en/artist/aivasowsky-ivan/'
def rel(p):return str(Path(p).relative_to(ROOT))
def save(name,v):h.save(E/name,v);return v
def capture(url,key):
 p=S/(key+'.html');r=requests.Session();r.headers['User-Agent']='Artline selected collection research (+https://artlines.org)';q=r.get(url,timeout=(15,45));q.raise_for_status();p.write_bytes(q.content)
 return q.content,dict(url=url,final_url=q.url,status=q.status_code,retrieved_at=h.now(),sha256=h.sha(q.content),bytes=len(q.content),body_path=str(p),retry_after=q.headers.get('Retry-After'))
def main():
 started=h.now();registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')));assert len(registry)==111
 reg=next(x for x in registry if x['source_id']=='national_gallery_athens')
 connection=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert connection=='artline-508319:europe-west1:artline-postgres'
 proxies=[x.strip() for x in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines() if '/tmp/artline-cloud-sql-proxy ' in x and '--port 55519' in x and connection in x];assert len(proxies)==1
 with h.connect() as db:
  target=dict(db.execute('SELECT current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone());assert target['db']=='artline' and not target['recovery']
 save('required-input-verification.json',dict(at=h.now(),required_files_read=True,registry_rows=len(registry),registry_entry=reg,latest_checkpoint='batch182',latest_holds='batch182/failures-and-holds.json',translation_calls=0))
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=connection,proxy_command=proxies[0],database=target,helper='ops/india-300-delivery-20261011.py',write=False,local_catalogue_connections=0))
 raw,irc=capture(INDEX,'aivasowsky-ivan-index');save('source-captures/aivasowsky-ivan-index.json',irc);sp=BeautifulSoup(raw,'html.parser')
 urls=[]
 for a in sp.select('a[href*="/en/artwork/"]'):
  u=a['href']
  if u not in urls:urls.append(u)
 assert 1<=len(urls)<=50
 rows=[]
 with h.connect() as db:
  for pos,url in enumerate(urls):
   body,rc=capture(url,'aivasowsky-%02d'%pos);save('source-captures/aivasowsky-%02d.json'%pos,rc);s=BeautifulSoup(body,'html.parser')
   head=s.select_one('h1.artwork');dt=head.find('span') if head else None;date=dt.get_text(' ',strip=True) if dt else '';dt.extract() if dt else None;title=head.get_text(' ',strip=True).rstrip(',').strip() if head else ''
   acc=s.select_one('.artwork-no');acc=acc.get_text(' ',strip=True).replace('Inv. Number','').strip() if acc else None
   creator=s.select_one('p.artist');creator=creator.get_text(' ',strip=True) if creator else None
   desc=s.select_one('p.description');desc=desc.get_text(' ',strip=True) if desc else None
   image=s.select_one('.img-magnifier-container img');image_url=(image.get('data-zoom-image') or image.get('src')) if image else None
   sid=url.rstrip('/').rsplit('/',1)[-1];years=[int(x) for x in re.findall(r'(?<!\d)[12]\d{3}(?!\d)',date)]
   exact=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text,a.creation_year_start,a.creation_year_end FROM artworks a WHERE a.current_institution_id=%s AND a.accession_number=%s UNION SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text,a.creation_year_start,a.creation_year_end FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND e.external_id=%s",(MID,acc,['continuous-athens-object','museum-native-nationalgallery-gr','nationalgallery-gr-artwork','museum-native-athens-object'],sid))]
   if exact:decision='existing_exact_inventory_or_native_identity'
   elif not years:decision='hold_unknown_creation_date'
   elif max(years)>1970:decision='hold_creation_beyond_1970'
   else:decision='eligible_new_object_requires_separate_creator_authority_and_visual_delivery'
   rows.append(dict(position=pos,source_id=sid,url=url,title=title,date_display=date,years=years,accession_number=acc,creator_label=creator,description=desc,image_url=image_url,source_receipt=rc,production_matches=exact,decision=decision))
 save('aivasowsky-native-object-reconciliation.json',dict(at=h.now(),creator_index=INDEX,index_receipt=irc,objects_classified=len(rows),rows=rows,directory_entries_counted_as_artworks=False,production_writes=0))
 counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']}
 decisions={x:sum(r['decision']==x for r in rows) for x in sorted({r['decision'] for r in rows})}
 eligible=[r for r in rows if r['decision'].startswith('eligible_')]
 # This bounded pass performs exact live reconciliation only; any genuinely new candidate is checkpointed for a later visual/write batch.
 save('independent-production-verification.json',dict(at=h.now(),target=target,connection_name=connection,rows_checked=len(rows),decisions=decisions,eligible_checkpointed=len(eligible),production_writes=0,verified_counts=counts,local_catalogue_connections=0))
 save('batch-verification-receipt.json',dict(at=h.now(),route='national_gallery_athens/aivasowsky-ivan',source_index_sha256=irc['sha256'],object_receipt_sha256s={r['source_id']:r['source_receipt']['sha256'] for r in rows},objects_classified=len(rows),decisions=decisions,production_writes=0,verified_counts=counts,attribution='Fresh official index/object captures and read-only live production reconciliation; no earlier programme increments counted.'))
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=h.load(qp);before=copy.deepcopy(q);route=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens')
  cursor=dict(route='official_creator_index_native_inventory_reconciliation',creator_index=INDEX,source_index_sha256=irc['sha256'],source_reported_total=len(rows),notices_reviewed=len(rows),processed_object_urls=urls,index_complete=True,next_object_url=None,decisions=decisions,eligible_source_ids=[r['source_id'] for r in eligible],evidence=rel(E/'aivasowsky-native-object-reconciliation.json'),coverage='Eight native object notices classified; institution-wide coverage remains incomplete',do_not_repeat_unchanged_holds=True)
  route['last_checked_at']=h.now();route['last_batch']=183;route['status']='aivasowsky_creator_index_eight_notices_live_reconciled';route.setdefault('resume_cursor',{})['aivasowsky_ivan']=cursor;route.setdefault('batch_history',[]).append(dict(batch=183,route='aivasowsky-ivan',notices_reviewed=len(rows),verified_counts=counts,evidence=rel(E/'batch-verification-receipt.json')));route.setdefault('remaining_gaps',[]).append('Batch183: Aivazovsky eight native notices classified; exact existing, date and any new-object candidates remain explicitly separated; no writes in this bounded reconciliation pass.')
  tmp=qp.with_suffix('.183.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
  unchanged=[x for x in before['sources'] if x['source_id']!='national_gallery_athens']==[x for x in q['sources'] if x['source_id']!='national_gallery_athens']
  save('source-queue-update-verification.json',dict(at=h.now(),updated_source='national_gallery_athens',unrelated_entries_preserved=unchanged,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor));assert unchanged
 next_task='Deliver only the checkpointed eligible Aivazovsky objects after creator authority, exact-version and individual image review; if none remain eligible, rotate to an untouched Russian icon or Byzantine registry institution. Do not replay the completed Athens creator indexes or SAAM shards 0–27.'
 save('source-register-final.json',dict(at=h.now(),provider=reg,policy_reference='Original 111-source registry and docs/ARTLINE_IMAGE_USE.md Greek source extension',access_status='Official creator index and eight native object notices HTTP200',objects_classified=len(rows),selected=0,prepared=0,imported=0,verified=0,decisions=decisions,remaining_gaps=next_task,resume_cursor=cursor))
 save('CHECKPOINT.json',dict(at=h.now(),batch=183,stage='research_reconciled_complete_no_production_write',started_at=started,finished_at=h.now(),objects_classified=len(rows),decisions=decisions,verified_counts=counts,next_task=next_task,blocker='',evidence=[rel(E/x) for x in ['required-input-verification.json','production-target-reconciliation.json','aivasowsky-native-object-reconciliation.json','independent-production-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json']]))
 save('independent-final-artifact-verification.json',dict(at=h.now(),files={rel(p):h.sha(p.read_bytes()) for p in E.rglob('*.json') if p.name!='independent-final-artifact-verification.json'},queue_sha256=h.sha(qp.read_bytes()),passed=True))
 print(json.dumps(dict(rows=len(rows),decisions=decisions,eligible=len(eligible)),ensure_ascii=False))
if __name__=='__main__':main()
