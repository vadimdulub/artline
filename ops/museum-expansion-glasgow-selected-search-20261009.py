"""Four observed-field searches for exact selected Glasgow object identities."""
import gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
import requests
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-glasgow-navigator-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref;BASE=n.BASE
def main():
 dest=RUN/'native-selected-searches-001.json';assert not dest.exists();probe=m.load(RUN/'navigator-session-probe-001.json');bootstrap=probe['rows'][0];raw=gzip.decompress((m.ROOT/bootstrap['capture']['body_path']).read_bytes()).decode();matches=re.findall(r"document\.cookie='([a-z]+)='\+escape\('([^']*)'\)\+';path=/;'",raw);assert {k for k,v in matches}=={'user','realname','permissions'};s=requests.Session();s.headers['User-Agent']='ArtlineMuseumResearch/1.0 (selected public object metadata; no images)'
 for key,value in matches:s.cookies.set(key,value,domain='collections.glasgowmuseums.com',path='/')
 s.cookies.set('screen','1280',domain='collections.glasgowmuseums.com',path='/');source=m.load(RUN/'source-context-001.json.gz');rs=[];failed=0;stopped=False
 for number in [2,3,1,11]:
  row=next(v for v in source['rows'] if v['number']==number);art=row['artwork'];params=dict(request='advanced',subset='101',_t1108=art['accession_number']);url=BASE+'/mwebcgi/mweb?'+urlencode(params)
  if stopped:rs.append(dict(number=number,state='unrequested_after_access_hold'));continue
  try:
   raw,cap=n.bounded(s,url);parsed=n.n.parsed(raw);rs.append(dict(number=number,artwork_id=art['id'],title=art['title'],inventory=art['accession_number'],search_parameters=params,state='captured_metadata',capture=cap,parsed=parsed));failed=0;print(json.dumps(dict(number=number,text=parsed['text'][:6500],links=[v for v in parsed['links'] if 'record' in v['href'] or 'next' in v['href'].lower()])),flush=True)
  except Exception as err:
   failed+=1;rs.append(dict(number=number,state='source_error',error=type(err).__name__+': '+str(err)));stopped=failed>=3 or any(x in str(err) for x in ['403','429']);print(json.dumps(rs[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rs,requests_stopped=stopped,source_reference=ref(RUN/'source-context-001.json.gz'),form_reference=ref(RUN/'navigator-session-probe-001.json'),script_reference=ref(Path(__file__).resolve()),policy='Four exact selected inventory searches through public documented fields; no invented endpoint or full collection search. Public HTML metadata only; no images or holdings inferred from footer/contact address.'))
if __name__=='__main__':main()
