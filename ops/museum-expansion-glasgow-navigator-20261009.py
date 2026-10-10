"""Bounded anonymous public Navigator metadata through its published session bootstrap."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-glasgow-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref;BASE='https://collections.glasgowmuseums.com'
def bounded(session,url):
 assert url.startswith(BASE+'/')
 with session.get(url,timeout=(12,45),stream=True) as response:
  raw=b''
  for chunk in response.iter_content(65536):raw+=chunk;assert len(raw)<4_000_000
  rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());root=RUN/'navigator-session/captures';key=hashlib.sha256((url+'\n'+rc['retrieved_at']).encode()).hexdigest();root.mkdir(parents=True,exist_ok=True);body=root/(key+'.body.gz');body.write_bytes(gzip.compress(raw,mtime=0));m.save(root/(key+'.json'),rc);response.raise_for_status();assert response.url.startswith(BASE+'/');return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))
def main():
 dest=RUN/'navigator-session-probe-001.json';assert not dest.exists();url=BASE+'/mwebcgi/mweb?request=advform';out=[];session=requests.Session();session.headers['User-Agent']='ArtlineMuseumResearch/1.0 (selected public metadata; no images)'
 try:
  raw,cap=bounded(session,url);p=n.parsed(raw);out.append(dict(state='anonymous_bootstrap',capture=cap,parsed=p));s=raw.decode();matches=re.findall(r"document\.cookie='([a-z]+)='\+escape\('([^']*)'\)\+';path=/;'",s);assert {k for k,v in matches}=={'user','realname','permissions'},'Unexpected public bootstrap';assert all(re.fullmatch(r'\d*',v) for k,v in matches)
  # These are literal anonymous defaults returned by this exact public request,
  # not credentials, invented role values, or values recovered from a user browser.
  for key,value in matches:session.cookies.set(key,value,domain='collections.glasgowmuseums.com',path='/')
  for key,value in [('screen','1280'),('imagedata',''),('lastdisp',''),('lastrequest',''),('query',''),('title','')]:session.cookies.set(key,value,domain='collections.glasgowmuseums.com',path='/')
  raw,cap=bounded(session,url);p=n.parsed(raw);out.append(dict(state='public_search_form',capture=cap,parsed=p));print(json.dumps(dict(text=p['text'],forms=p['forms'],links=p['links'])),flush=True)
 except Exception as err:out.append(dict(state='source_error',error=type(err).__name__+': '+str(err)));print(json.dumps(out[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),policy='Exactly supplied public anonymous JavaScript session defaults applied as cookies for ordinary HTTP metadata retrieval. No browser/private cookies,authentication,permission escalation,alternate host or denial bypass. Stop on access denial. No images,contact forms or catalogue mutation. Browser unavailable due environment metadata error; normal browser skill attempted twice.'))
if __name__=='__main__':main()
