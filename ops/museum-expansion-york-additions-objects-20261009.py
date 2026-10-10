"""Select native York objects by dated museum metadata, then capture only selected object pages."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;PRIOR=n.RUN;RUN=m.RUN/'native/york-additions-20261009';n.RUN=RUN;ref=n.ref;IID='87750cb4-a118-5588-876c-999695cbe14b'
def invkey(v):return re.sub(r'[^a-z0-9]','',m.norm(v or ''))
def parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser');fields=collections.defaultdict(list);occurrences=[]
 for dl in soup.select('dl'):
  for dt in dl.find_all('dt',recursive=False):
   key=dt.get_text(' ',strip=True);values=[]
   for sib in dt.next_siblings:
    if getattr(sib,'name',None)=='dt':break
    if getattr(sib,'name',None)=='dd':values.append(sib.get_text(' ',strip=True))
   occurrences.append(dict(key=key,values=values))
   for value in values:
    if value not in fields[key]:fields[key].append(value)
 text=soup.get_text(' ',strip=True);start=text.find('Collection Item:');assert start>=0
 return dict(fields=dict(fields),field_occurrences=occurrences,headings=[v.get_text(' ',strip=True) for v in soup.select('h1,h2,h3')],object_text=text[start:],links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in soup.select('a[href]') if 'artuk' in a['href'] or 'wikidata' in a['href']],rights=[v.strip() for v in re.findall(r'Licence: ([^<]+)',str(soup))])
def select():
 rows={};sources=[RUN/'native-index-001.json.gz',RUN/'date-band-index-001.json.gz'];first=m.load(sources[0]);bands=m.load(sources[1])
 for v in first['rows']:rows.setdefault(v['native_id'],dict(v,discovery_references=[ref(sources[0])]))
 for group in bands['rows']:
  if not group.get('capture'):continue
  for v in group['hits']:
   if v['native_id'] not in rows:rows[v['native_id']]=dict(v,capture_reference=ref(m.ROOT/group['capture']['body_path']),discovery_references=[ref(sources[1])])
 initial=m.load(RUN/'initial-scope-001.json.gz');by=collections.defaultdict(list)
 for v in initial['snapshot']['artworks']:
  if v['accession_number']:by[invkey(v['accession_number'])].append(v)
 selected=[];known=[]
 for number,v in enumerate(rows.values(),1):
  old=by.get(invkey(v['fields']['object_number']),[]);row=dict(number=number,source_id='york-museums/'+v['native_id'],native_id=v['native_id'],index=v,institution_id=IID)
  if old and all(a['current_institution_id']==IID for a in old):known.append(dict(row,existing=old,state='already_catalogued_inventory_discovery_no_new_record'))
  else:selected.append(row)
 assert len(rows)==190 and len(selected)==177 and len(known)==13
 return dict(at=m.now(),rows=selected,already_catalogued_discovery=known,index_references=[ref(v) for v in sources],initial_reference=ref(RUN/'initial-scope-001.json.gz'),policy='190 unique dated index objects;13 already linked museum inventories retained as discovery,177selected for exact native object and full existing identity review. Two1933-08/1943-08 index values caused conservative band-parser stop: they are date-format questions,not observed access refusal or proof that filters were ignored. No further date-band requests; source date strings still require native object confirmation. No images or exhaustive catalogue download.')
def main():
 dest=RUN/'selected-objects-001.json.gz';assert not dest.exists();selection=select();m.save(RUN/'object-selection-001.json.gz',selection);rows=[];failed=0;stopped=False
 for v in selection['rows']:
  try:
   raw,c=n.capture('york',v['index']['url']);p=parsed(raw);assert p['fields']['ID']==[v['native_id']] and p['fields']['Object number']==[v['index']['fields']['object_number']];row=dict(v,capture=c,parsed=p);failed=0;print(json.dumps(dict(number=v['number'],id=v['native_id'],title=p['fields'].get('Title'),date_start=p['fields'].get('Production date start'),date_end=p['fields'].get('Production date end'),creators=p['fields'].get('Creators'),count=p['fields'].get('Number of objects')),ensure_ascii=False),flush=True)
  except Exception as e:
   failed+=1;row=dict(v,error=type(e).__name__+': '+str(e));print(json.dumps(row),flush=True)
  m.save(RUN/'selected-objects-001'/('%03d.json'%v['number']),row);rows.append(row)
  if failed>=3 or any(t in row.get('error','') for t in ['403','429']):stopped=True;break
 m.save(dest,dict(at=m.now(),rows=rows,provider_stopped=stopped,selection_reference=ref(RUN/'object-selection-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Only selected native object metadata. Preserve literal roles,qualifications,physical counts,date strings and raw bodies. No image downloads,artist links,publication or database writes.'))
if __name__=='__main__':main()
