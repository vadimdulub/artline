"""Selected exact inventory searches in the public NMNI catalogue."""
import gzip,hashlib,importlib.util,json,time
from pathlib import Path
from urllib.parse import urlparse
import requests
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-four-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;RUN=p.RUN;ref=p.ref;n=p.n

def search(inventory):
 home=m.load(RUN/'native-probes-001.json')['rows'][1];soup=n.BeautifulSoup(home['forms'][0],'html.parser');form=soup.form;url=form['action'];assert url==n.SITES['ulster']+'/results';data={v['name']:v.get('value','') for v in form.select('input[name]')};data['simple_search']=inventory
 key=hashlib.sha256(json.dumps(dict(url=url,method='POST',data=data),sort_keys=True).encode()).hexdigest();root=RUN/'ulster-search-captures';root.mkdir(parents=True,exist_ok=True);dest=root/(key+'.json');body=root/(key+'.body.gz')
 if dest.exists():
  cap=m.load(dest);raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['sha256'];assert cap['status']==200
 else:
  time.sleep(.4)
  with requests.post(url,data=data,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected inventory metadata; no images)'},timeout=(12,45),stream=True) as response:
   raw=b''
   for chunk in response.iter_content(65536):
    raw+=chunk;assert len(raw)<4_000_000
   cap=dict(url=url,method='POST',data=data,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),read_only_search=True);body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest,cap);response.raise_for_status();assert urlparse(response.url).hostname=='collections.nationalmuseumsni.org'
 return raw,dict(receipt=cap,receipt_reference=ref(dest),body_reference=ref(body))

def main():
 dest=RUN/'ulster-sample-001.json';assert not dest.exists();out=[]
 for inventory in ['BELUM.U238','BELUM.U2273']:
  raw,c=search(inventory);soup=n.BeautifulSoup(raw,'html.parser');out.append(dict(inventory=inventory,capture=c,text=soup.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in soup.select('a[href]')],forms=[str(f) for f in soup.select('form')]));print(inventory,soup.get_text(' ',strip=True)[-7000:]);print([(a['text'],a['href']) for a in out[-1]['links']][-30:],flush=True)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),policy='Two selected exact inventory searches via the existing anonymous public form. No images, pagination or write action. The public search session is only a catalogue query identifier.'))
if __name__=='__main__':main()
