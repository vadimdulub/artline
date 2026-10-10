#!/usr/bin/env python3
"""Select bounded Princeton metadata for date, attribution and object review."""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-princeton-native-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=n.RUN;IID=n.IID;ref=n.ref;checked=n.checked;QUEUE=RUN/'selected-metadata-queue-001.json'
def prefilter(row):
 date=row.get('displaydate') or '';credit=row.get('creditline') or '';holds=[]
 if re.search(r'\b(?:loan|lent|borrowed|promised gift)\b',credit,re.I):holds.append('Explicit loan or promised gift is not an accepted museum holding')
 if 'Princeton University' in credit:holds.append('University/campus credit: separate collection identity requires review; do not promote from shared catalogue')
 if re.search(r'printed later|printed\s+\d+\s+or later',date,re.I):holds.append('Physical print date has an unbounded later production statement')
 years=[int(v) for v in re.findall(r'(?<!\d)\d{3,4}(?!\d)',date)]
 if not re.search(r'\bB\.?C\.?E?\.?\b',date,re.I) and any(v>1970 for v in years):holds.append('Explicit source creation statement reaches after1970')
 if re.fullmatch(r'(?:ca\.\s*)?(?:late\s+)?(?:20th|21st) century',date,re.I):holds.append('Century reaches after1970')
 return holds
def queue():
 assert not QUEUE.exists();paths=list((RUN/'indexes-001').glob('*.json.gz'))+list((RUN/'extra-indexes-001').glob('*.json.gz'))+list(RUN.glob('priority-*-001.json.gz'))+[RUN/'painting-index-001.json.gz'];rows={}
 for path in sorted(paths,key=lambda p:(not p.name.startswith('priority-'),str(p))):
  for hit in n.search_hits(m.load(path)):
   data=hit['_source'];sid=hit['_id'];lead=dict(kind='search',reference=ref(path),source_record=hit)
   if sid not in rows:rows[sid]=dict(source_id=sid,data=data,index_references=[lead],priority=path.name.startswith('priority-'))
   else:
    assert rows[sid]['data']==data,(sid,'Changed source index facts');rows[sid]['index_references'].append(lead);rows[sid]['priority']|=path.name.startswith('priority-')
 for path in sorted((RUN/'tombstones-001').glob('*.json.gz')):
  x=m.load(path);data=x['data'];sid=str(data['objectid']);lead=dict(kind='tombstone',reference=ref(path),source_record=data,selection=x['selection'])
  if sid not in rows:rows[sid]=dict(source_id=sid,data=data,index_references=[lead],priority=x['selection']['kind']=='world_highlight')
  else:
   assert all(rows[sid]['data'].get(k)==data.get(k) for k in ['objectid','objectnumber','displaytitle','displaymaker','displaydate','creditline','medium','dimensions']),(sid,'Index/tombstone facts changed');rows[sid]['index_references'].append(lead)
 pending={v['source_id']:v for v in n.pending()};selected=[];held=[]
 for sid,row in rows.items():
  reasons=prefilter(row['data']);row.update(url=n.BASE+'/objects/'+sid,existing_pending=pending.get(sid),date_screen='Literal display date present; full numeric creation fields, qualifiers and physical version require review' if row['data'].get('displaydate') and row['data']['displaydate']!='undated' else 'Creation unknown in index; selected only for bounded metadata research, no inferred eligibility from creator lifespan')
  if reasons:held.append(dict(row,state='index_hold',reasons=reasons));continue
  selected.append(dict(row,state='selected_metadata_research_only',number=len(selected)+1))
 assert len(rows)<=400 and len(selected)<=280
 m.save(QUEUE,dict(at=m.now(),parser_reference=ref(Path(__file__).resolve()),capture_code_reference=ref(Path(n.__file__).resolve()),selected=selected,held=held,policy='Bounded metadata research only, no images or catalogue writes. Exact native IDs deduplicate overlap. Known post1970 works, unbounded later prints, explicit loans/promises and University/campus credits are held. Unknown creation dates remain unknown pending actual full-object fields and editorial review; no date inferred from artist life. Named, anonymous, cultural and school creators remain in scope. Count target never supplies evidence.'))
 print(json.dumps(dict(distinct=len(rows),selected=len(selected),held=len(held),selected_unknown_dates=sum(not v['data'].get('displaydate') or v['data'].get('displaydate')=='undated' for v in selected),selected_existing_pending=sum(bool(v['existing_pending']) for v in selected))),flush=True)
def objects():
 x=m.load(QUEUE);checked(x['parser_reference']);checked(x['capture_code_reference']);assert not list((RUN/'object-errors-001').glob('*.json')),'Retained failure requires assessment'
 for row in x['selected']:
  path=RUN/'objects-001'/('object-%03d.json.gz'%row['number'])
  try:
   v=n.save_capture(path,row['url'],number=row['number'],index=row,queue_reference=ref(QUEUE));assert str(v['data']['objectid'])==row['source_id'] and v['data']['type']=='artobject';print(json.dumps(dict(number=row['number'],source_id=row['source_id'],date=v['data'].get('displaydate'),bytes=v['capture']['receipt']['bytes'])),flush=True)
  except Exception as e:m.save(RUN/'object-errors-001'/('object-%03d.json'%row['number']),dict(at=m.now(),url=row['url'],number=row['number'],error=repr(e),queue_reference=ref(QUEUE),policy='Stopped first failure. No automatic retry, bypass or transport change.'));raise
 m.save(RUN/'selected-capture-001.json.gz',dict(at=m.now(),queue_reference=ref(QUEUE),records=[ref(p) for p in sorted((RUN/'objects-001').glob('*.json.gz'))],images=0,policy='Capture completion is not approval. Complete creation/creator/object/holding and database identity review still required.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['queue','objects']);globals()[p.parse_args().command]()
