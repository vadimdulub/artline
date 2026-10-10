"""Capture exact selected Southampton object links; no accession inferred from URL."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
EXPECTED={13:'Air, Water, Stone',43:'Composition',45:'Good Shooting',97:'Untitled',135:'Time for Tea (Foliage Fantasy)',173:'The Hermit Discovered'}
def main():
 dest=RUN/'native-objects-001.json';assert not dest.exists();overview=RUN/'native-selected-001.json';x=m.load(overview);selected=[]
 for number,title in EXPECTED.items():
  matches={(v['url'],a['href']) for v in x['rows'] for a in v.get('parsed',{}).get('links',[]) if a['text']==title and '/object/' in a['href']};assert len(matches)==1;index,url=next(iter(matches));selected.append(dict(number=number,title=title,index_url=index,url=url))
 m.save(RUN/'native-object-selection-001.json',dict(at=m.now(),rows=selected,overview_reference=ref(overview),policy='Titles select public object pages for evidence review,not automatic identity approval. URL numeric components are not assumed to be accessions.'))
 out=[];failed=0;stopped=False
 for v in selected:
  if stopped:out.append(dict(v,state='unrequested_after_access_hold'));continue
  try:
   raw,cap=n.n.capture('southampton',v['url']);p=n.parsed(raw);s=n.n.BeautifulSoup(raw,'html.parser');p['headings']=[h.get_text(' ',strip=True) for h in s.select('h1,h2,h3')];p['tables']=[t.get_text(' ',strip=True) for t in s.select('table')];out.append(dict(v,state='captured_metadata',capture=cap,parsed=p));failed=0;print(json.dumps(dict(number=v['number'],text=p['text'])),flush=True)
  except Exception as e:
   failed+=1;out.append(dict(v,state='source_error',error=type(e).__name__+': '+str(e)));stopped=failed>=3 or any(t in str(e) for t in ['403','429']);print(json.dumps(out[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,requests_stopped=stopped,selection_reference=ref(RUN/'native-object-selection-001.json'),script_reference=ref(Path(__file__).resolve()),policy='Selected exact native object metadata. Museum scope,source inventory/date and physical versions need review; no images or metadata mutations.'))
if __name__=='__main__':main()
