#!/usr/bin/env python3
"""Find independently licensed alternate photographs of selected painting gaps.

The Wikidata primary image is never rewritten. An alternate must have its own
exact Commons structured artwork link and pass the existing per-file policy.
"""
import argparse,collections,fcntl,importlib.util,json,re,time
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row
s=importlib.util.spec_from_file_location('common',Path(__file__).with_name('overnight-commons-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);core=m.core

def valid_alternate(c,page,sdc,primary):
 if page.get('ns')!=6 or not page.get('title','').startswith('File:'):raise ValueError('Not a Commons file')
 if page['title']=='File:'+primary:raise ValueError('Already evaluated primary file')
 if re.search(r'\b(detail|collage|montage|verso|reverse)\b',page['title'],re.I):raise ValueError('Partial or composite reproduction')
 if m.ids(sdc,'P6243')!={c['qid']}:raise ValueError('Alternate lacks an exact single structured artwork identity')

def select(run,reference=None,include_nonpopular=False):
 path=run/'candidates.json'
 if path.exists():return json.loads(path.read_text())['candidates']
 sources={};blocked={x['artwork_id'] for x in json.loads((run.parent/'withdrawn-images.json').read_text())['records']}
 reference=reference or run.parent
 attempted=set()
 for event_file in reference.glob('*alternate*/events.jsonl'):
  for line in event_file.read_text().splitlines():
   row=json.loads(line)
   if row.get('artwork_id') and row.get('outcome') in ('prepared','complete','manual_review','failed'):attempted.add(row['artwork_id'])
 for file in sorted(reference.glob('*/candidates.json')):
  if file==path:continue
  data=json.loads(file.read_text())
  if not isinstance(data,dict):continue
  for c in data.get('candidates',[]):
   if c.get('provider')=='night-commons' and (c.get('popular') or include_nonpopular) and c.get('work_type')=='painting' and c['artwork_id'] not in blocked|attempted and c.get('target_ids',{}).get('cloud'):sources[c['artwork_id']]=c
 missing=set()
 with psycopg.connect('postgres://localhost/artline',autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
  ids=list(sources)
  for start in range(0,len(ids),500):
   missing.update(x['id'] for x in db.execute("SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[]) AND primary_media_id IS NULL AND status='review' AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids[start:start+500],)).fetchall())
 rows=sorted((sources[aid] for aid in missing),key=lambda c:(not c.get('popular'),c['artist'],c['title'],c['artwork_id']))
 core.save_new(path,{'selected_at':core.now(),'candidates':rows,'policy':'Existing source-backed painting gaps, popular painters first; no new metadata or publication. Previously attempted alternates and inherited holds excluded. Alternate files require exact Commons P6243 plus all existing rights/identity safeguards.'});return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=100);p.add_argument('--deadline',type=float,required=True);p.add_argument('--reference',type=Path);p.add_argument('--include-nonpopular',action='store_true');a=p.parse_args();a.run.mkdir(exist_ok=True)
 lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert (a.run.parent/'backups.json').exists()
 rows=select(a.run,a.reference,a.include_nonpopular);done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('prepared','complete','manual_review','failed')};rows=[c for c in rows if c['artwork_id'] not in done][:a.limit];f=core.Fetcher(a.run/'metadata');totals=collections.Counter()
 for n,c in enumerate(rows,1):
  if time.time()>=a.deadline:break
  selected_path=a.run/'selected/night-commons'/(c['artwork_id']+'.json')
  try:
   if not selected_path.exists():
    entity_data=m.api(f,'www.wikidata.org',{'action':'wbgetentities','ids':c['qid'],'props':'claims|labels|aliases','languages':'en|mul|fr|it|nl|de|ru|el|sv|da|fi|es|pt|nb|pl'});e=entity_data['entities'][c['qid']];primary=m.entity_match(c,e)
    result=m.api(f,'commons.wikimedia.org',{'action':'query','list':'search','srsearch':'haswbstatement:P6243='+c['qid'],'srnamespace':6,'srlimit':20,'srprop':''});names=[x['title'].removeprefix('File:') for x in result.get('query',{}).get('search',[]) if x['title']!='File:'+primary];accepted=None;held=[]
    for start in range(0,len(names),10):
     if accepted:break
     part=names[start:start+10];data=m.api(f,'commons.wikimedia.org',{'action':'query','titles':'|'.join('File:'+name for name in part),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'});pages=[]
     for name in part:
      try:pages.append(m.page_for_filename(data,name))
      except ValueError as exc:held.append({'filename':name,'reason':str(exc)})
     mids=['M'+str(page['pageid']) for page in pages];sd=m.api(f,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join(mids),'props':'claims'})['entities'] if mids else {}
     for page in pages:
      try:
       sdc=sd['M'+str(page['pageid'])];valid_alternate(c,page,sdc,primary);rendered=m.rendered_rights_uri(f,page);info,credit,label,uri,status,url,original=m.rights_and_identity(c,e,page,sdc,rendered)
       accepted=dict(c,page=info['descriptionurl'],source_image_url=url,policy_url=uri,rights_status=status,license_label=label,checked_at=core.now(),raw={'wikidata':e,'commons':page,'structured_data':sdc,'alternate_discovery':{'method':'Exact Commons P6243 artwork link','wikidata_primary_filename':primary,'search':result}},creator_credit=credit,source_name='Wikimedia Commons',source_record_url=info['descriptionurl'],image_url=url,image_license=label,image_license_url=uri,rights_statement=label,creator=c['artist'],creation_date=c['date_display'],source_object_id=c['qid'],rights_verified_at=core.now())
       if rendered:accepted['rendered_licence_evidence']=rendered
       accepted['attribution_text']=f"{c['artist']}. {c['title']}. Image credit: {credit}. {info['descriptionurl']}. {label} ({uri}). Full-frame resize and JPEG compression; applicable ShareAlike terms retained."
       if original:accepted['commons_original_sha1']=info['sha1']
       break
      except (ValueError,KeyError) as exc:held.append({'filename':page['title'],'reason':str(exc)})
    core.save_new(a.run/'discovery'/(c['artwork_id']+'.json'),{'at':core.now(),'artwork_id':c['artwork_id'],'alternates_considered':len(names),'held':held,'selected':accepted['page'] if accepted else None})
    if not accepted:raise ValueError('No alternate with independently verified exact identity and approved image rights')
    core.save_new(selected_path,accepted)
   core.worker('night-commons',[c],SimpleNamespace(run=a.run,prepare_only=True),None);totals['prepared_or_attempted']+=1
  except (ValueError,KeyError) as exc:
   core.event(a.run,{'provider':'night-commons','artwork_id':c['artwork_id'],'external_id':c['qid'],'outcome':'manual_review','reason':str(exc)});totals['manual_review']+=1
  print(core.now(),'Popular alternate photographs',n,'of',len(rows),dict(totals),flush=True)
if __name__=='__main__':main()
