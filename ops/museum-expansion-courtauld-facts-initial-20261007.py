#!/usr/bin/env python3
"""Parse retained Courtauld catalogue evidence without approving additions."""
import collections,importlib.util,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-courtauld-capture-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d;m=c.m;RUN=c.RUN;ref=c.ref
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)

def creation(raw):
 text=re.sub(r'^\(circa\)\s*','c. ',raw or '',flags=re.I)
 # Preserve a redundant explicit decade qualifier in date_display; only parse
 # its equally explicit complete numeric interval, never an artist lifespan.
 text=re.sub(r'^\((\d{3})0\'s\) (\1\d\s*-\s*\1\d)$',r'\2',text)
 return dates.creation(text)

def content_lines(html):
 soup=BeautifulSoup(html,'html.parser')
 for form in soup.select('form.adv_maker_search'):
  button=form.select_one('input[type="submit"]');assert button and button.get('value');form.replace_with(button['value'])
 for br in soup.select('br'):br.replace_with('\n')
 return [re.sub(r'\s+',' ',x).strip() for x in soup.get_text().split('\n') if x.strip()]

def creator_parts(field):
 if field is None:return []
 soup=BeautifulSoup(field['html'],'html.parser');sets=soup.select('.field-set') or [soup];out=[]
 for node in sets:
  lines=content_lines(str(node));bio=[]
  # Remove only standalone birth/death ranges. Their source lines are retained.
  while lines and re.fullmatch(r'(?:ca\.\s*)?\d{3,4}\s*[-–]\s*\d{3,4}(?: \(Life dates\))?',lines[-1]):bio.insert(0,lines.pop())
  label=' '.join(lines)
  if label:out.append(dict(label=label,biographical_lines=bio,source_html=str(node)))
 return out

def checked_record(path):
 v=m.load(path);p=m.ROOT/v['index_reference']['path'];assert ref(p)==v['index_reference'];idx=m.load(p)
 assert c.parsed_index(c.saved_body(idx['capture']))==idx['parsed'] and v['index_row'] in idx['parsed']['rows']
 parsed=c.parsed_object(c.saved_body(v['capture']));assert parsed==v['parsed'];receipt=v['capture']['receipt'];assert receipt['status']==200 and receipt['url']==v['index_row']['url']==receipt['final_url']
 return v,parsed

def facts(v,parsed):
 fields={x['label']:x for x in parsed['fields']};assert len(fields)==len(parsed['fields'])
 text=lambda k:fields.get(k,{}).get('text') or None
 clean=lambda x:re.sub(r'\s+',' ',x).strip()
 titles=content_lines(fields['Title']['html']);assert titles and clean(parsed['headings'][0])==clean(' '.join(titles)) and titles[0]==clean(v['index_row']['title'])
 assert all(x=='PLEASE SHARE WITH US HOW YOU PLAN TO USE THIS IMAGE' for x in parsed['headings'][1:])
 parts=creator_parts(fields.get('Maker'));label='; '.join(p['label'] for p in parts) or None
 return dict(source_id=v['index_row']['source_path'].removeprefix('/object-'),source_url=v['index_row']['url'],title=' / '.join(titles),titles=titles,creator_label=label,detail_creator_label=label,creator_parts=parts,date_display=text('Date of Production'),**creation(text('Date of Production')),inventory=text('Object Number'),medium=text('Medium'),dimensions_text=text('Dimensions'),work_type='painting',object_form=None,credit=text('Credit'),acquisition=text('Mode of Acquisition'),provenance=text('Provenance'),description=text('Label Text'),inscriptions=text('Inscriptions'),exhibitions=text('Exhibition History'),copyright=text('Copyright'),location_label=text('Location'),native_fields=parsed['fields'],object_links=parsed['object_links'],date_basis='Literal Date of Production; creator lifespans and acquisition years excluded. Source circa/range/period wording retained. Painting type derives from official painting collection category, not an invented medium.',source_limitation='Official native metadata and original HTTP evidence. Collection and ownership credits retained separately from display labels. Images not downloaded; rights statements are evidence only.')

def main():
 capture=m.load(RUN/'selected-capture-001.json.gz');rows=[]
 for reference in capture['records']:
  path=m.ROOT/reference['path'];assert ref(path)==reference;v,p=checked_record(path);f=facts(v,p);reasons=[]
  if f['date_issue']:reasons.append(f['date_issue'])
  if not f['creator_label']:reasons.append('Maker field absent; do not infer creator from title or narrative')
  if not f['inventory']:reasons.append('Object number absent')
  if not f['credit'] or not f['credit'].startswith('Courtauld Gallery, London'):reasons.append('Credit requires separate holding/ownership review')
  if re.search(r'\bmissing\b',str([f['inventory'],f['provenance']]),re.I):reasons.append('Missing physical object; no current holding approval')
  if f['date_display']!=v['index_row']['date_display']:reasons.append('Index/detail dates differ')
  rows.append(dict(source_id=f['source_id'],source_reference=reference,index=v['index_row'],facts=f,state='source_hold' if reasons else 'candidate',reasons=reasons))
 # Numbered subobjects may describe components, faces or separately framed
 # panels. Keep them for explicit grouping review rather than counting both.
 inventories={r['facts']['inventory'] for r in rows}
 for r in rows:
  inv=r['facts']['inventory'] or '';parent=inv.rsplit('.',1)[0]
  r['grouping']=dict(parent_inventory=parent if parent in inventories else None,child_inventories=sorted(x for x in inventories if x and x.startswith(inv+'.')),component_number=bool(re.fullmatch(r'P\.\d{4}\.[A-Z]+\.\d+\.\d+',inv)))
 counts=dict(collections.Counter(r['state'] for r in rows));m.save(RUN/'native-candidates-001.json.gz',dict(at=m.now(),rows=rows,counts=counts,capture_reference=ref(RUN/'selected-capture-001.json.gz'),policy='Source candidates only, pending individual identity, creator, version and grouping review. All unknown and qualified labels preserved. No database writes.'));print(counts,flush=True)

if __name__=='__main__':main()
