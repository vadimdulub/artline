#!/usr/bin/env python3
"""Reconstruct selected official web extracts and retain literal catalogue facts."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-nelson-web-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m;RUN=w.RUN;ref=w.ref;IID=w.d.IID
def checked_reference(r):
 p=m.ROOT/r['path'];assert ref(p)==r;return p
def page(number):
 path=RUN/'web-objects-001'/('object-%03d.json'%number);capture=m.load(path);queue=m.load(checked_reference(capture['queue_reference']));row=queue['selected'][number-1];assert row['number']==capture['number']==number
 req=dict(ref_id=row['index_web_ref'],id=row['link_id']);assert capture['request']==req
 original=w.pages(capture['result']);assert len(original)==1;original=original[0]
 assert original['source_call']==dict(method='click',args=req)
 for idx in row['index_references']:
  parsed=w.pages(m.load(checked_reference(idx['index_capture_reference']))['result']);ip=next(p for p in parsed if p['web_ref']==idx['index_web_ref'])
  assert {k:idx[k] for k in w.index_rows(ip)[0]} in w.index_rows(ip)
 lines=dict(original['lines']);references=[ref(path)];metas=[original['source_metadata']]
 for part in sorted((RUN/'web-object-parts-001').glob('object-%03d-part-*.json'%number)):
  rec=m.load(part);assert rec['request']['source_reference']==ref(path)
  pages=w.pages(rec['result']);assert len(pages)==1;p=pages[0]
  assert w.cleanurl(p['url'])==w.cleanurl(original['url']) and p['total_lines']==original['total_lines']
  assert p['source_call']==dict(method='open',args=dict(ref_id=original['web_ref'],lineno=rec['request']['lineno']))
  for num,text in p['lines']:
   if num in lines:assert lines[num]==text,('Changed overlap',number,num,lines[num],text)
   lines[num]=text
  references.append(ref(part));metas.append(p['source_metadata'])
 missing=sorted(set(range(original['total_lines']))-set(lines))
 return capture,row,dict(original,lines=sorted(lines.items()),complete=not missing,missing_lines=missing,source_metadata_parts=metas),references
def creator(raw):
 links=list(re.finditer(r'\ue200cite\ue202\d+†([^\ue201]+)\ue201',raw))
 if not links:return w.plain(raw) or None
 assert len(links)==1,'Multiple authorities in a single creator field'
 link=links[0];before=w.plain(raw[:link.start()]);after=w.plain(raw[link.end():])
 # Biographical dates/nationality remain in creator_source_fields. Only the
 # explicit authority label and attribution qualifiers become an object label.
 bio=after.startswith('(') and after.endswith(')') and bool(re.search(r'\b(?:\d{3,4}|century|active|born|died|American|Chinese|Dutch|English|Flemish|French|German|Greek|Italian|Japanese|Netherlandish|Russian|Scottish|Spanish)\b',after,re.I))
 return ' '.join(v for v in [before,link[1],'' if bio else after] if v)
def facts(p):
 assert p['complete'],'Incomplete object extraction'
 url=w.cleanurl(p['url']);match=re.fullmatch(re.escape(w.BASE)+r'/objects/(\d+)(?:/[^/]+)?/?',url);assert match,'Not a native artwork page'
 lines=[t for n,t in p['lines'] if t];heads=[(i,t) for i,t in enumerate(lines) if t.startswith('# ')];assert len(heads)==1
 start,heading=heads[0];title=heading[2:].strip()
 end=next(i for i in range(start+1,len(lines)) if lines[i].startswith('Information about a particular artwork or image'))
 core=lines[start+1:end];current_roles=['Artist','Maker','Attributed to','Workshop of','Circle of','School of','Follower of','After','Studio of','Manner of']
 title_roles=['Alternate Title','Former Title','Original Language Title','Primary Title']
 labels=title_roles+['Series Title','Portfolio','Formerly attributed to']+current_roles+['Culture','Date','Medium','Dimensions','Credit Line','Object number','Signed','Inscribed','Inscription','Copyright','Place of Origin','Classification']
 field_rows=[]
 for t in core:
  if t in ['On View','Collections','Terms','Gallery Location'] or t.startswith(('Description','Exhibition History','Gallery Label','Provenance','Published References')):break
  label=next((key for key in labels if t==key or t.startswith(key+' ') or t.startswith(key+'\ue200cite') or (key in ['Signed','Inscribed','Inscription'] and t.startswith((key+'(',key+'\"')))),None)
  if label:field_rows.append(dict(label=label,values=[t[len(label):].strip()]))
  elif field_rows:field_rows[-1]['values'].append(t)
  else:raise AssertionError(('Unknown object field',title,t))
 fields=collections.defaultdict(list)
 for r in field_rows:fields[r['label']].append(' '.join(w.plain(t) for t in r['values'] if t))
 def one(key):
  values=fields.get(key,[]);assert len(values)<=1,(title,key,values);return values[0] if values else None
 makers=[('' if r['label'] in ['Artist','Maker'] else r['label']+' ')+creator(' '.join(r['values'])) for r in field_rows if r['label'] in current_roles]
 historical=[creator(' '.join(r['values'])) for r in field_rows if r['label']=='Formerly attributed to']
 creator_label='; '.join(v for v in makers if v) or one('Culture')
 terms=[]
 if 'Terms' in core:
  for t in core[core.index('Terms')+1:]:
   if not t.startswith('* '):break
   terms.extend(re.findall(r'\ue200cite\ue202\d+†([^\ue201]+)\ue201',t))
 kind=next((v for term,v in [('Painting','painting'),('Drawing','drawing'),('Sculpture','sculpture'),('Prints','print')] if term in terms),'unknown')
 source_rights=[w.plain(t) for t in core if re.search(r'copyright|©|rights reserved|public domain|creative commons',t,re.I)]
 return dict(source_id=match[1],source_url=url,native_object_id=match[1],native_page_urls=list(dict.fromkeys([url,w.BASE+'/objects/'+match[1]+'/'])),native_metadata_urls=[],wikidata_ids=[],title=title,titles=list(dict.fromkeys([title]+[t for role in title_roles for t in fields.get(role,[])])),creator_label=creator_label,detail_creator_label=creator_label,identity_creator_labels=makers+historical,creator_source_fields=[r for r in field_rows if r['label'] in current_roles+['Culture','Formerly attributed to']],historical_creator_labels=historical,date_display=one('Date'),**w.creation(one('Date')),inventory=one('Object number'),inventory_fields=[one('Object number')] if one('Object number') else [],medium=one('Medium'),dimensions_text=one('Dimensions'),work_type=kind,object_form=None,credit_line=one('Credit Line'),source_terms=terms,source_fields=dict(fields),source_rights=source_rights or None,source_text=[w.plain(t) for t in core],source_metadata=p['source_metadata_parts'],source_note='Official object-page web extraction with crawl metadata and hashed source selection. Original object HTTP bytes unavailable. Literal creator qualifications, dates, inventory, materials, narrative, provenance and unknown rights preserved. Current and former attributions stay distinct; historical labels and titles assist identity discovery only. Alternative/reworked dates retain literal wording and source-endpoint envelope without claiming continuous creation. No legal title, custody or current-display assertion.')
def candidates(suffix):
 rows=[];errors=[];selected=m.load(RUN/'selected-official-queue-001.json')['selected']
 for row in selected:
  number=row['number']
  try:
   capture,index,p,refs=page(number);v=facts(p);holds=[]
   if v['date_issue']:holds.append(v['date_issue'])
   if not v['inventory'] or v['inventory']!=index['inventory']:holds.append('Missing or conflicting native inventory')
   if not v['credit_line']:holds.append('Missing collection credit')
   if re.search(r'\b(?:lent|loan|on deposit|private collection)\b',v['credit_line'] or '',re.I):holds.append('Loan or private-credit scope requires editorial review')
   if v['work_type']=='unknown':holds.append('Unmapped native artwork type')
   if not v['creator_label']:holds.append('Creator/cultural label absent')
   for key,indexkey in [('title','title'),('creator_label','creator_label')]:
    if m.norm(v[key])!=m.norm(index[indexkey]):holds.append('Index/detail '+key+' differs')
   if w.creation(v['date_display'])!=index['creation_screen']:holds.append('Index/detail creation dates differ')
   life=re.sub(r'\s+','',v['date_display'] or '')
   if re.fullmatch(r'\d{4}[-–]\d{4}',life) and any(life in re.sub(r'\s+','',t) for r in v['creator_source_fields'] for t in r['values']):holds.append('Creation field repeats artist lifespan')
   rows.append(dict(number=number,source_id=v['source_id'],facts=v,index=index,source_references=refs,state='source_hold' if holds else 'candidate',reasons=holds,retrieved_at=capture['at']))
  except (AssertionError,KeyError,ValueError,StopIteration) as ex:errors.append(dict(number=number,title=row['title'],error=type(ex).__name__+': '+str(ex)))
 assert len(rows)==len({r['source_id'] for r in rows})
 out=RUN/('native-candidates-'+suffix+'.json.gz');m.save(out,dict(at=m.now(),rows=rows,errors=errors,parser_references=[ref(Path(__file__).resolve()),ref(Path(w.__file__).resolve())],policy='Source triage only. All metadata, source discrepancies, unknown fields, attribution qualifiers and incomplete captures retained. Every candidate still requires physical-object, duplicate, date and holding review.'))
 print(json.dumps(dict(rows=len(rows),counts=dict(collections.Counter(r['state'] for r in rows)),errors=errors,holds=[dict(number=r['number'],title=r['facts']['title'],reasons=r['reasons']) for r in rows if r['state']!='candidate']),ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();candidates(a.suffix)
