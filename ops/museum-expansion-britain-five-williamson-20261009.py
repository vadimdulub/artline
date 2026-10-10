"""Capture only 126 selected Williamson inventories via its published public form."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-five-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
def invkey(v):return re.sub(r'^BIKGM[:.]\s*','BIKGM:',v.strip().upper())
def parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser');fields={}
 for el in soup.select('p.ehive-field'):
  label=el.select_one('.ehive-field-label');value=el.select_one('.ehive-field-value');assert label and value;fields.setdefault(label.get_text(' ',strip=True),[]).append(value.get_text('\n',strip=True))
 assert fields;return dict(fields=fields,text=soup.get_text(' ',strip=True))
def main():
 dest=RUN/'williamson-native-001.json.gz';assert not dest.exists();rs=[v for v in m.load(RUN/'candidate-facts-001.json.gz')['rows'] if v['institution_id']=='97f7055a-ac1b-529d-b6b0-1d2865e74650'];assert len(rs)==126;selection=RUN/'williamson-native-selection-001.json';assert not selection.exists();m.save(selection,dict(at=m.now(),source_reference=ref(RUN/'candidate-facts-001.json.gz'),rows=[dict(number=v['number'],artwork_id=v['existing_artwork_id'],inventory=v['facts']['inventory']) for v in rs],policy='Selected existing identities only,including one source inventory missing in current catalogue. Exact form searches and observed object links only. No images,catalogue-wide crawl or writes.'))
 out=[];failures=0;stopped=False
 for r in rs:
  row=dict(number=r['number'],artwork_id=r['existing_artwork_id'],inventory=r['facts']['inventory']);item=RUN/'williamson-selected'/('%03d.json'%r['number']);assert not item.exists();url=n.SITES['williamson']+'/collections/?'+urlencode({'eHive_query':'"'+row['inventory']+'"'})
  try:
   raw,cap=n.capture('williamson',url);soup=n.BeautifulSoup(raw,'html.parser');links=sorted({a['href'] for a in soup.select('a[href]') if re.fullmatch(r'https://williamsonartgallery\.org/item/\d+/?',a['href'])});row.update(search_capture=cap,object_links=links)
   if len(links)==1:
    raw,cap=n.capture('williamson',links[0]);data=parsed(raw);assert len(data['fields']['Object number'])==1;row.update(object_capture=cap,parsed=data,object_url=links[0],state='captured_exact_inventory' if invkey(data['fields']['Object number'][0])==invkey(row['inventory']) else 'native_inventory_mismatch')
   else:row['state']='no_unique_exact_inventory_result'
   failures=0
  except Exception as error:
   failures+=1;row.update(state='capture_error',error=type(error).__name__+': '+str(error));stopped=failures>=3 or any(v in str(error) for v in ['403','429','Forbidden'])
  m.save(item,row);out.append(dict(number=row['number'],state=row['state'],reference=ref(item)));print(json.dumps(dict(number=row['number'],state=row['state'],complete=len(out),selected=len(rs))),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(selection),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,consecutive_failures=failures,unprocessed_numbers=[v['number'] for v in rs if v['number'] not in {r['number'] for r in out}],policy='BIKGM colon/period punctuation normalized only for identity comparison; original inventory text retained. Exact object metadata is corroboration,not automatic editorial approval. General catalogue warning distinguishes holdings from on-display status.'))
if __name__=='__main__':main()
