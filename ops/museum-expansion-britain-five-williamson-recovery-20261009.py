"""One same-URL retry for two isolated transport failures; preserve earlier results."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode
z=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-britain-five-williamson-v2-20261009.py'));w=importlib.util.module_from_spec(z);z.loader.exec_module(w);m=w.m;n=w.n;RUN=w.RUN;ref=w.ref
def main():
 dest=RUN/'williamson-recovery-001.json';assert not dest.exists();initial=m.load(RUN/'williamson-native-002.json.gz');assert not initial['requests_stopped'] and not initial['unprocessed_numbers'];errors=[m.load(m.ROOT/v['reference']['path']) for v in initial['rows'] if v['state']=='capture_error'];assert [v['number'] for v in errors]==[110,138];out=[]
 for old in errors:
  assert old['error'].startswith(('ConnectionError:','ReadTimeout:')) and not any(s in old['error'] for s in ['403','429','Forbidden']);row={k:old[k] for k in ['number','artwork_id','inventory']};row['prior_reference']=ref(RUN/'williamson-selected-002'/('%03d.json'%row['number']));url=n.SITES['williamson']+'/collections/?'+urlencode({'eHive_query':'"'+row['inventory']+'"'})
  try:
   raw,cap=n.capture('williamson',url);soup=n.BeautifulSoup(raw,'html.parser');links=sorted({a['href'] for a in soup.select('a[href]') if re.fullmatch(r'https://williamsonartgallery\.org/item/\d+/?',a['href'])});row.update(search_capture=cap,object_links=links)
   if len(links)==1:
    raw,cap=n.capture('williamson',links[0]);data=w.parsed(raw);assert len(data['fields']['Object number'])==1;row.update(object_capture=cap,parsed=data,object_url=links[0],state='captured_exact_inventory' if w.invkey(data['fields']['Object number'][0])==w.invkey(row['inventory']) else 'native_inventory_mismatch')
   else:row['state']='no_unique_exact_inventory_result'
  except Exception as error:row.update(state='capture_error',error=type(error).__name__+': '+str(error))
  out.append(row);print(json.dumps(dict(number=row['number'],state=row['state'])),flush=True)
  if row['state']=='capture_error':break
 m.save(dest,dict(at=m.now(),rows=out,initial_reference=ref(RUN/'williamson-native-002.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Original two nonconsecutive transport failures retained. One retry at the same observed public URL; cached HTTP200 search reused. No access rejection,authentication,bypass,image download or catalogue write. Stop on any further failure.'))
if __name__=='__main__':main()
