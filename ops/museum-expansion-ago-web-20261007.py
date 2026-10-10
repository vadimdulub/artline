#!/usr/bin/env python3
"""Bounded AGO public-index selection; preserve date and access holds."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import unquote,urlsplit,urlunsplit
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-ago-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN;IID=d.IID;ref=d.ref;BASE='https://art.ago.ca'
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-nelson-web-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w);pages=w.pages;plain=w.plain
def cleanurl(url):
 p=urlsplit(unquote(url));return urlunsplit((p.scheme,p.netloc,re.sub(r';jsessionid=[^/]*','',p.path),'',''))
def creation(raw):
 t=(raw or '').strip()
 seasonal=re.fullmatch(r'(?:Winter|Spring|Summer|Autumn|Fall) (\d{4}(?:[-–]\d{4})?)',t)
 months='January|February|March|April|May|June|July|August|September|October|November|December'
 calendar=re.fullmatch(r'(?:'+months+r')(?:[-–](?:'+months+r'))?(?: \d{1,2},)? (\d{4})',t)
 if seasonal or calendar:return w.creation((seasonal or calendar)[1])
 t=re.sub(r'^(c\. \d{3,4})-c\. (\d{3,4})$',r'\1-\2',t)
 return w.creation(t)
def index_rows(p):
 assert p['complete'],'Incomplete index extract'
 assert cleanurl(p['url']).startswith(BASE+'/collections/')
 lines=[(n,t) for n,t in p['lines'] if t];start=next(i for i,(n,t) in enumerate(lines) if re.fullmatch(r'[\d,]+ results',t));out=[]
 for pos,(num,t) in enumerate(lines[start+1:],start+1):
  if '†Next Page' in t or '†Image: AGO logo' in t:break
  match=re.fullmatch(r'\ue200cite\ue202(\d+)†([^\ue201]+)\ue201',t)
  if not match or match[2].strip().startswith(('Image','Compare')):continue
  values=[]
  for n,text in lines[pos+1:]:
   if '\ue200cite' in text or text=='Compare':break
   values.append(text)
  assert len(values) in [2,3],(t,values)
  out.append(dict(index_web_ref=p['web_ref'],link_id=int(match[1]),index_url=p['url'],title=match[2].strip(),creator_label=values[0] if len(values)==3 else None,date_display=values[-2],source_type=values[-1]))
 assert 1<=len(out)<=50;return out
def queue():
 paths=sorted((RUN/'web-indexes-001').glob('*.json'))+[RUN/'web-initial-modern-part-001.json'];rows={};dupes=[];errors=[];seen=set();outside=[]
 for path in paths:
  ps=pages(m.load(path)['result'])
  if not ps:errors.append(dict(reference=ref(path),reason='Web source returned no catalogue page'));continue
  for p in ps:
   try:rs=index_rows(p)
   except (AssertionError,StopIteration) as ex:errors.append(dict(reference=ref(path),reason=str(ex) or 'No catalogue results'));continue
   key=tuple((r['title'],r['creator_label'],r['date_display'],r['source_type']) for r in rs)
   if key in seen:dupes.append(ref(path));continue
   seen.add(key)
   for r in rs:
    lead=dict(r,index_capture_reference=ref(path));k=(r['title'],r['creator_label'],r['date_display'],r['source_type'])
    if k not in rows:rows[k]=dict(r,index_references=[lead],creation_screen=creation(r['date_display']))
    else:rows[k]['index_references'].append(lead)
 selected=[];held=[]
 for r in rows.values():
  if r['source_type'] not in ['Painting','Drawing','Watercolour']:outside.append(dict(r,state='outside_selected_work_types'));continue
  if r['creation_screen']['date_issue']:held.append(dict(r,state='source_date_hold'));continue
  selected.append(dict(r,number=len(selected)+1,state='selected_metadata_only'))
 assert len(selected)<=240
 m.save(RUN/'selected-official-queue-001.json',dict(at=m.now(),selected=selected,held=held,outside_selected_work_types=outside,duplicate_indexes=dupes,index_errors=errors,index_references=[ref(p) for p in paths],policy='Bounded published Canadian, Modern, Indigenous and Thomson collection indexes. Eligible explicit creation dates selected before object retrieval. Source-period words and unknowns preserved. Identical index labels are discovery deduplication only, not a physical-object decision. Sculptures and decorative objects remain outside this painting/drawing pass, not globally excluded. No original HTTP object claim, images or database writes.'))
 print(json.dumps(dict(distinct_index_leads=len(rows),selected=len(selected),date_holds=len(held),outside=len(outside),duplicates=len(dupes),errors=errors,by_collection=dict(collections.Counter(re.search(r'/collections/(\d+)',r['index_url'])[1] for r in selected))),ensure_ascii=False),flush=True)
if __name__=='__main__':queue()
