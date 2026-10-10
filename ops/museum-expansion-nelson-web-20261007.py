#!/usr/bin/env python3
"""Bounded public object leads and evidence-labelled Nelson-Atkins web facts."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import unquote,urlsplit,urlunsplit
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-nelson-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN;BASE=d.BASE;ref=d.ref
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('museum-expansion-toledo-web-20261007.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);pages=b.pages;plain=b.plain
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-birmingham-facts-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)
def cleanurl(url):
 p=urlsplit(unquote(url));return urlunsplit((p.scheme,p.netloc,re.sub(r';jsessionid=[^/]*','',p.path),'',''))
def index_rows(p):
 assert p['complete'] and re.match(re.escape(BASE)+r'/(?:collections/(?:27507/european-art|27500/american-art|27508/modern-art)|people/4526/domenikos-theotokopoulos-called-el-greco)/objects',cleanurl(p['url']))
 lines=[(n,t) for n,t in p['lines'] if t];start=next(i for i,(n,t) in enumerate(lines) if re.fullmatch(r'\d+ results',t));out=[]
 for pos,(num,t) in enumerate(lines[start+1:],start+1):
  if '†Next Page' in t:break
  match=re.fullmatch(r'\ue200cite\ue202(\d+)†([^\ue201]+)\ue201',t)
  if not match or match[2].startswith('Image'):continue
  values=[]
  for n,text in lines[pos+1:]:
   if '\ue200cite' in text:break
   values.append(text)
  assert len(values) in [2,3],(t,values)
  out.append(dict(index_web_ref=p['web_ref'],link_id=int(match[1]),index_url=p['url'],title=match[2].strip(),creator_label=values[0],date_display=values[1] if len(values)==3 else None,inventory=values[-1]))
 assert 1<=len(out)<=12;return out
def creation(raw):
 t=(raw or '').replace('\u2060','').strip()
 alternatives=re.fullmatch(r'(\d{3,4}) or (\d{3,4})',t)
 reworking=re.fullmatch(r'(\d{3,4}); reworked (\d{3,4})',t)
 pair=alternatives or reworking
 if pair:
  first,last=sorted([int(pair[1]),int(pair[2])])
  if 100<=first<=last<=1970:return dict(first=first,last=last,date_precision='range',date_issue=None)
 return dates.creation(t)
def selected():
 paths=list((RUN/'web-indexes-001').glob('*.json'))+list((RUN/'web-culture-indexes-001').glob('*.json'))+list((RUN/'web-additional-indexes-001').glob('*.json'))+list(RUN.glob('web-priority-*-001.json'))
 rows={};duplicate_pages=[];seen=set()
 for path in sorted(paths):
  ps=pages(m.load(path)['result']);assert len(ps)==1
  parsed=index_rows(ps[0]);key=tuple((r['title'],r['creator_label'],r['date_display'],r['inventory']) for r in parsed)
  if key in seen:duplicate_pages.append(ref(path));continue
  seen.add(key)
  for row in parsed:
   k=row['inventory'];assert k
   lead=dict(row,index_capture_reference=ref(path))
   if k not in rows:rows[k]=dict(row,index_references=[lead],creation_screen=creation(row['date_display']))
   else:rows[k]['index_references'].append(lead)
 selected=[];held=[]
 for row in rows.values():
  issue=row['creation_screen']['date_issue']
  if issue:held.append(dict(row,state='date_screen_hold',reason=issue))
  else:selected.append(dict(row,number=len(selected)+1,state='selected_metadata_only'))
 assert len(selected)<=240
 m.save(RUN/'selected-official-queue-001.json',dict(at=m.now(),selected=selected,held=held,index_references=[ref(p) for p in sorted(paths)],duplicate_indexes=duplicate_pages,policy='Bounded public painting indexes and explicit Greek/Russian priorities. Native inventory deduplicates leads while all source labels/qualifications remain evidence. Complete source creation dates screened before detail retrieval; alternative years and explicit reworking years remain literal with a search envelope only. All physical identity, credit, rights and date discrepancies still require review. No images or catalogue writes.'))
 print(json.dumps(dict(distinct_leads=len(rows),selected=len(selected),held=len(held),duplicate_pages=len(duplicate_pages),holds=[(r['title'],r['date_display']) for r in held]),ensure_ascii=False),flush=True)
def queue():
 indexed=[];seen=set();duplicates=[]
 for path in sorted((RUN/'web-indexes-001').glob('*.json')):
  ps=pages(m.load(path)['result']);assert len(ps)==1;rows=index_rows(ps[0]);key=tuple((r['title'],r['creator_label'],r['date_display'],r['inventory']) for r in rows)
  if key in seen:duplicates.append(ref(path));continue
  seen.add(key);indexed.extend(dict(r,index_capture_reference=ref(path),selection_kind='official_painting_index') for r in rows)
 selected=[];held=[];rawrefs=[]
 for path in sorted((RUN/'wikidata-objects-001').glob('*.json.gz')):
  batch=m.load(path);rawrefs.append(ref(path))
  for qid,entity in batch['entities'].items():
   urls=sorted(set(re.findall(r'https?://art\.nelson-atkins\.org/objects/[^"\\\s]*',json.dumps(entity))))
   urls=[u.replace('http:','https:') for u in urls];ids={re.match(r'.*/objects/(\d+)',u)[1] for u in urls if re.match(r'.*/objects/(\d+)',u)}
   title=next((entity.get('labels',{}).get(k,{}).get('value') for k in ['en','mul','fr','nl','de'] if entity.get('labels',{}).get(k,{}).get('value')),None)
   entry=dict(qid=qid,title=title,source_urls=urls,source_reference=ref(path),selection_kind='secondary_selected_native_url',source_index_reference=ref(RUN/'wikidata-index-002.json.gz'))
   if len(ids)!=1:held.append(dict(entry,reason='No unique referenced native object ID'));continue
   url=sorted(urls,key=lambda u:(-len(urlsplit(u).path),u))[0]
   selected.append(dict(entry,source_id=next(iter(ids)),source_url=url))
 assert len(selected)<=200 and len(indexed)==24
 m.save(RUN/'web-object-queue-001.json',dict(at=m.now(),official_index_rows=indexed,secondary_rows=selected,secondary_url_holds=held,duplicate_indexes=duplicates,secondary_capture_references=rawrefs,uncaptured_secondary_entities=61,policy='Only 24 distinct public index entries; repeated next-page responses are not additional objects. Selected Wikidata references identify public object URL leads, not approved facts. 200 of 261 selected secondary entities captured before HTTP 429 stopped collection; no further rate-limited requests. Native date, attribution, credit and version checks remain required. No images or database writes.'))
 print(json.dumps(dict(official=len(indexed),secondary=len(selected),secondary_url_holds=len(held),duplicate_indexes=len(duplicates)),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['queue','selected']);a=p.parse_args();globals()[a.command]()
