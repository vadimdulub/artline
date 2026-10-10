import importlib.util,json,time,hashlib
from urllib.parse import urlencode
from pathlib import Path
s=importlib.util.spec_from_file_location('f','ops/museum-expansion-fitzwilliam-native-20261007.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;R=f.RUN
pages=[];seen={};old={r['source_id'] for r in m.load(R/'native-object-queue-001.json')['objects']};dest=R/'native-objects-002';dest.mkdir(exist_ok=True)
for page in range(13,16):
 url=f.BASE+'/search/results?'+urlencode(dict(query='painting',operator='AND',sort='desc',object_type='painting',page=page));raw,cap=f.n.capture(f.PROVIDER,url);parsed=f.parse_index(raw);pages.append(dict(page=page,url=url,capture=cap,parsed=parsed))
 for row in parsed['rows']:
  if row['source_id'] not in old:seen[row['source_id']]=row
 print('INDEX',page,len(parsed['rows']),flush=True)
m.save(R/'native-index-002.json.gz',dict(at=m.now(),pages=pages,unique_objects=list(seen.values()),policy='Three further selected public painting-index pages, bounded to72 leads toward remaining30 eligible works. No image assets or exhaustive archive.'))
m.save(R/'native-object-queue-002.json',dict(at=m.now(),objects=list(seen.values()),previous_capture_excluded=len(old),index_reference=f.reference(R/'native-index-002.json.gz')))
for idx,row in enumerate(seen.values(),1):
 out=dest/(row['source_id']+'.json.gz')
 if out.exists():continue
 try:
  raw,cap=f.n.capture(f.PROVIDER,row['url']);parsed=f.parse_page(raw);url=row['url']+'?format=json';assert url in parsed['json_links'];rawj,capj=f.n.capture(f.PROVIDER,url);j=json.loads(rawj);assert j['admin']['id']=='object-'+row['source_id'] and j['admin']['uri']==row['url']
  m.save(out,dict(index=row,url=row['url'],native=dict(capture=cap,parsed=parsed),json=dict(capture=capj,parsed=j)));print('OBJECT',idx,len(seen),row['source_id'],row['title'],flush=True)
 except Exception as error:m.save(dest/(row['source_id']+'-error.json'),dict(at=m.now(),index=row,error=str(error)));print('ERROR',row['source_id'],str(error),flush=True)
 time.sleep(.4)
