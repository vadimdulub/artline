"""Capture selected Southampton period collection indexes, metadata only."""
import hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;PRIOR=n.RUN;RUN=m.RUN/'native/southampton-additions-20261009';n.n.RUN=RUN;ref=n.ref;BASE='https://southamptoncityartgallery.com'
INDEXES=['renaissance-painting','18th-century-british-painting','french-19th-century','19th-century-british-painting','camden-town-group']
def parsed(raw):
 p=n.parsed(raw);s=n.n.BeautifulSoup(raw,'html.parser');p['headings']=[v.get_text(' ',strip=True) for v in s.select('h1,h2,h3')];return p
def main():
 dest=RUN/'additional-indexes-001.json';assert not dest.exists();overview=m.load(PRIOR/'native-probes-001.json');parent=next(v for v in overview['rows'] if v['url']==BASE+'/collection/');observed={urljoin(BASE,v['href'].strip()) for v in parent['parsed']['links']};rows=[];stopped=False;failures=0
 for name in INDEXES:
  url=BASE+'/collection/'+name+'/';assert url in observed
  if stopped:rows.append(dict(url=url,state='unrequested_after_access_hold'));continue
  try:
   raw,cap=n.n.capture('southampton',url);p=parsed(raw);rows.append(dict(url=url,state='captured_metadata',capture=cap,parsed=p));failures=0;print(json.dumps(dict(url=url,cards=[v for v in p['links'] if '/object/' in v['href'] and v['text']])),flush=True)
  except Exception as e:
   failures+=1;rows.append(dict(url=url,state='source_error',error=type(e).__name__+': '+str(e)));stopped=failures>=3 or any(t in str(e) for t in ['403','429']);print(json.dumps(rows[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,requests_stopped=stopped,discovery_reference=ref(PRIOR/'native-probes-001.json'),prior_indexes_reference=ref(PRIOR/'native-selected-001.json'),script_reference=ref(Path(__file__).resolve()),policy='Five observed historical collection sections selected for discovery,not exhaustive museum downloading. Category and artist life dates do not establish object creation. Exact object evidence,existing-record scope and physical versions still require review. No images or database mutations.'))
if __name__=='__main__':main()
