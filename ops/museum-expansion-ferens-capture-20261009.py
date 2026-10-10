"""Capture detail metadata only for the180 preselected Ferens object leads."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
p=module('p','museum-expansion-ferens-native-20261009.py');w=module('w','museum-expansion-britain-six-ferens-v2-20261009.py');m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
def main():
 dest=RUN/'native-captured-001.json.gz';assert not dest.exists();source=RUN/'native-selection-001.json.gz';selected=[v for v in m.load(source)['rows'] if v['state']=='selected_detail_review'];assert len(selected)==180;out=[];failures=0;stopped=False
 for v in selected:
  number=v['number'];row=dict(number=number,index=v['index'],selection_reference=ref(source));path=RUN/'objects-selected-001'/('%03d.json'%number);assert not path.exists();url=v['index']['url']
  try:
   raw,cap=n.capture('ferens',url);soup=n.BeautifulSoup(raw,'html.parser');detail=sorted({urljoin(url,a['href']) for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Detailed Record'})
   if detail:
    assert len(detail)==1;row.update(overview_capture=cap,overview_parsed=p.parsed(raw));url=detail[0];raw,cap=n.capture('ferens',url)
   data=w.parsed(raw);row.update(state='captured_metadata',url=url,capture=cap,parsed=data);failures=0
  except Exception as e:
   failures+=1;row.update(state='capture_error',error=type(e).__name__+': '+str(e));stopped=failures>=3 or any(v in str(e) for v in ['403','429','Forbidden'])
  m.save(path,row);out.append(dict(number=number,state=row['state'],reference=ref(path)));print(json.dumps(dict(number=number,state=row['state'],completed=len(out),selected=len(selected))),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(source),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,consecutive_failures=failures,unprocessed_numbers=[v['number'] for v in selected if v['number'] not in {r['number'] for r in out}],policy='Only preselected object metadata and observed detail links. No images,full collection download,authentication or catalogue writes. Native field conflicts and qualifiers remain explicit for editorial review.'))
if __name__=='__main__':main()
