"""Bounded public museum context; no image requests or held-provider access."""
import gzip,hashlib,importlib.util,json,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-britain-nine-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
HOSTS={'box':{'www.theboxplymouth.com','theboxplymouth.com'},'york':{'www.yorkmuseumstrust.org.uk','yorkmuseumstrust.org.uk','www.yorkartgallery.org.uk','yorkartgallery.org.uk'},'harris':{'www.theharris.org.uk','theharris.org.uk'}}
def capture(provider,url):
 assert urlparse(url).hostname in HOSTS[provider];key=hashlib.sha256(url.encode()).hexdigest();folder=RUN/provider/'captures';receipt=folder/(key+'.json');body=folder/(key+'.body.gz')
 if receipt.exists():
  rc=m.load(receipt);raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256'];assert rc['status']==200;return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))
 time.sleep(.4)
 with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata; no images)'},timeout=(12,45),stream=True) as resp:
  raw=b''
  for chunk in resp.iter_content(65536):raw+=chunk;assert len(raw)<4_000_000
  rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());folder.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));m.save(receipt,rc);resp.raise_for_status();assert urlparse(resp.url).hostname in HOSTS[provider];return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))
def parsed(raw):
 soup=BeautifulSoup(raw,'html.parser');return dict(text=soup.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in soup.select('a[href]')],scripts=[v['src'] for v in soup.select('script[src]')],forms=[str(v) for v in soup.select('form')])
SOURCES=[('box','https://www.theboxplymouth.com/collections'),('box','https://theboxplymouth.com/collections/art/'),('york','https://www.yorkmuseumstrust.org.uk/collections/'),('york','https://www.yorkmuseumstrust.org.uk/about-us/our-venues/york-art-gallery/'),('harris','https://www.theharris.org.uk/collections/fine-art-collections/')]
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();rows=[];stopped=set();fails={}
 for provider,url in SOURCES:
  if provider in stopped:rows.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   raw,cap=capture(provider,url);p=parsed(raw);rows.append(dict(provider=provider,url=url,capture=cap,parsed=p));fails[provider]=0;print(json.dumps(dict(provider=provider,url=url,bytes=cap['receipt']['bytes'],links=[v for v in p['links'] if any(t in v['href'].lower() for t in ['collection','cottonian','watercolour','fine-art','artgallery'])][:35])),flush=True)
  except Exception as e:
   fails[provider]=fails.get(provider,0)+1;rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
   if fails[provider]>=3 or any(t in str(e) for t in ['403','429']):stopped.add(provider)
 m.save(dest,dict(at=m.now(),rows=rows,stopped_providers=sorted(stopped),script_reference=ref(Path(__file__).resolve()),discovery_reference=ref(m.RUN/'native/britain-next-discovery-20261009.json'),policy='Five selected official museum context pages only; no images,contact submissions,ArtUK requests or held-provider retries. Context does not itself validate every object or current display.'))
if __name__=='__main__':main()
