#!/usr/bin/env python3
"""Parse preserved Toledo official-page web extracts. Read-only; no raw HTTP claim."""
import argparse,collections,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import unquote,urlsplit,urlunsplit
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-toledo-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
m=d.m;RUN=d.RUN;BASE=d.BASE;ref=base.ref;pages=base.pages
def cleanurl(url):
 p=urlsplit(unquote(url));return urlunsplit((p.scheme,p.netloc,p.path.split(';',1)[0],'',''))
def plain(t):return re.sub(r'\ue200cite\ue202\d+†([^\ue201]+)\ue201',r'\1',t).strip()
def index_rows(p):
 assert p['complete'];assert cleanurl(p['url']).startswith(BASE+'/collections/57691/paintings/objects')
 lines=[(n,t) for n,t in p['lines'] if t];start=next(i for i,(n,t) in enumerate(lines) if re.fullmatch(r'\d+ results',t));out=[]
 for pos,(num,text) in enumerate(lines[start+1:],start+1):
  if '†Next Page' in text:break
  matches=list(re.finditer(r'\ue200cite\ue202(\d+)†([^\ue201]+)\ue201',text))
  matches=[x for x in matches if not x[2].strip().startswith(('Image:','Image Not Available'))]
  if not matches:continue
  assert len(matches)==1
  match=matches[0];values=[]
  for n,t in lines[pos+1:]:
   if '\ue200cite' in t:break
   values.append(t)
  assert len(values) in [1,2],(text,values)
  out.append(dict(index_web_ref=p['web_ref'],index_url=p['url'],link_id=int(match[1]),title=match[2].strip(),creator_label=values[0] if len(values)==2 else None,date_display=values[-1]))
 assert len(out)==12;return out
def queue(suffix='002'):
 out=[];seen=set();errors=[]
 for path in sorted(RUN.glob('web-indexes-*/*.json.gz')):
  for p in pages(m.load(path)['result']):
   if not cleanurl(p['url']).startswith(BASE+'/collections/57691/paintings/objects'):continue
   try:rows=index_rows(p)
   except Exception as ex:errors.append(dict(reference=ref(path),web_ref=p['web_ref'],error=str(ex)));continue
   key=tuple((r['title'],r['creator_label'],r['date_display']) for r in rows)
   if key in seen:continue
   seen.add(key);out.extend(dict(r,index_capture_reference=ref(path)) for r in rows)
 assert len(out)<=240
 m.save(RUN/('web-object-queue-'+suffix+'.json'),dict(at=m.now(),rows=out,index_errors=errors,unique_index_pages=len(seen),policy='Bounded official painting collection metadata leads; duplicate index pages discarded. No image fetches or writes.'))
 print(json.dumps(dict(rows=len(out),pages=len(seen),errors=errors)))
def creation(value):
 t=re.sub(r'^(?:about|circa|ca\.?)\s+','c. ',value or '',flags=re.I)
 period=re.fullmatch(r'(Probably )?(?:(?:early|mid|late|mid-late)[ -])?(\d{1,2})(?:st|nd|rd|th) century',t,re.I)
 if period:
  first=(int(period[2])-1)*100+1;last=int(period[2])*100
  if 100<=first<=last<=1970:return dict(first=first,last=last,date_precision='circa_range' if period[1] else 'century',date_issue=None)
 era=re.fullmatch(r'Meiji Era \((\d{4})-(\d{4})\)',t)
 if era:return base.creation(era[1]+'-'+era[2])
 return base.creation(t)
def object_facts(p):
 assert p['complete'],'Incomplete web extract'
 url=cleanurl(p['url']);match=re.fullmatch(re.escape(BASE)+r'/objects/(\d+)/[^/]+',url);assert match,'Not a Toledo object URL'
 lines=[t for n,t in p['lines'] if t];heads=[(i,t) for i,t in enumerate(lines) if t.startswith('# ')];assert len(heads)==1
 start,heading=heads[0];title=heading[2:].strip();core=[]
 for text in lines[start+1:]:
  if re.match(r'^\ue200cite\ue202\d+†',text):break
  core.append(text)
 core=[re.sub(r'^(Artist|Maker|Culture)(?=\ue200cite)',r'\1 ',t) for t in core]
 labels=['Artist','Maker','Culture','Place of Origin','Date','Dimensions','Medium','Classification','Credit Line','Object number','Description','Provenance','Published References','Exhibition History','Inscribed','Inscription','Signed','Copyright','On View','Not on View','Location','Gallery','External Site Address']
 fields={};key=None
 for text in core:
  label=next((x for x in labels if text==x or text.startswith(x+' ')),None)
  if label:
   assert label not in fields,(title,label);fields[label]=[text[len(label):].strip()];key=label
  elif key:fields[key].append(text)
  else:raise AssertionError((title,text))
 fields={k:' '.join(plain(v) for v in vs if v).strip() for k,vs in fields.items()}
 # Artist authority lifespans remain evidence; never used as creation years.
 creator_raw=next((t for t in core if t.startswith(('Artist ','Maker ','Culture '))),None)
 creator=fields.get('Artist') or fields.get('Maker') or fields.get('Culture')
 if creator_raw:
  links=re.findall(r'\ue200cite\ue202\d+†([^\ue201]+)\ue201',creator_raw)
  if len(links)==1:
   marker=re.search(r'\ue200cite\ue202\d+†[^\ue201]+\ue201',creator_raw)
   prefix=re.sub(r'^(?:Artist|Maker|Culture)\s*','',creator_raw[:marker.start()]).strip()
   suffix=creator_raw[marker.end():].strip()
   # Preserve attribution outside the linked authority, remove only biography.
   bio=(suffix.startswith('(') and suffix.endswith(')') and suffix.count('(')==suffix.count(')') and (re.search(r'\b(?:\d{3,4}|century|active|born|died)\b',suffix,re.I) or suffix in ['(Chinese)','(Russian)','(Japanese)','(French)','(Italian)','(American)','(Dutch)','(British)','(German)']))
   creator=' '.join(x for x in [prefix,links[0],'' if bio else suffix] if x)
 classification=fields.get('Classification')
 return dict(source_id=match[1],source_url=url,title=title,titles=[title],creator_label=creator,detail_creator_label=creator,creator_source_text=fields.get('Artist') or fields.get('Maker') or fields.get('Culture'),date_display=fields.get('Date'),**creation(fields.get('Date')),inventory=fields.get('Object number'),medium=fields.get('Medium'),dimensions_text=fields.get('Dimensions'),work_type={'Paintings':'painting','Drawings':'drawing','Prints':'print'}.get(classification,'unknown'),object_form=None,acquisition=fields.get('Credit Line'),source_classification=classification,fields=fields,core_text=[plain(t) for t in core],source_metadata=p['source_metadata'],web_ref=p['web_ref'],capture_kind='Official-page web-tool text extraction; not original HTTP bytes')
def candidates(suffix='003'):
 rows=[];errors=[]
 for path in sorted(RUN.glob('web-objects-*/*.json.gz')):
  record=m.load(path);ps=pages(record['result']);request=record['requests'][0]
  if len(ps)!=1:errors.append(dict(reference=ref(path),index=request,error='No complete object response'));continue
  p=ps[0]
  try:
   f=object_facts(p);reference=request['index_capture_reference'];fp=m.ROOT/reference['path'];assert ref(fp)==reference
   ip=next(x for x in pages(m.load(fp)['result']) if x['web_ref']==request['index_web_ref']);assert {k:request[k] for k in index_rows(ip)[0]} in index_rows(ip)
   assert p['source_call']==dict(method='click',args=dict(ref_id=request['index_web_ref'],id=request['link_id']))
   holds=[]
   if f['date_issue']:holds.append(f['date_issue'])
   if not f['inventory']:holds.append('Missing inventory')
   if not f['acquisition']:holds.append('Missing acquisition credit')
   if m.norm(f['title'])!=m.norm(request['title']):holds.append('Index/title disagreement')
   if m.norm(f['creator_label'])!=m.norm(request['creator_label']):holds.append('Index/creator disagreement')
   if m.norm(f['date_display'])!=m.norm(request['date_display']):holds.append('Index/date disagreement')
   rows.append(dict(source_id=f['source_id'],facts=f,index=request,source_reference=ref(path),state='source_hold' if holds else 'candidate',reasons=holds))
  except Exception as ex:errors.append(dict(reference=ref(path),index=request,error=type(ex).__name__+': '+str(ex)))
 assert len(rows)==len({r['source_id'] for r in rows})
 m.save(RUN/('native-candidates-'+suffix+'.json.gz'),dict(at=m.now(),rows=rows,errors=errors,policy='Full preserved official object text and index chain; individual identity, narrative, grouping and ownership review still required.'))
 print(json.dumps(dict(rows=len(rows),counts=dict(collections.Counter(r['state'] for r in rows)),errors=errors),ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['queue','candidates']);globals()[p.parse_args().command]()
