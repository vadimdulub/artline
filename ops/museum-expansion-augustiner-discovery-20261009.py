"""Selected public Freiburg museum pages and annual reports; blocked portal excluded."""
import gzip,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-augustiner-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
SOURCES=[
('permanent','https://museen.freiburg.de/museums/am-en/permanent-exhibition-am'),
('exhibitions','https://museen.freiburg.de/museen/am/sonderausstellungen-am'),
('press','https://museen.freiburg.de/presse'),
('opening','https://museen.freiburg.de/museen2024/presse/pressekits-aktuelle-projekte/gesamteroeffnung-augustinermuseum'),
('report2023','https://museen.freiburg.de/site/freiburg_museen2024/get/documents_E834460675/freiburg/daten_museen/Jahresberichte/STM_Jahresbericht_2023_final_barrierefrei.pdf'),
('report2022','https://www.freiburg.de/pb/site/freiburg_museen/get/params_E1446501350/2052292/STM_Jahresbericht_2022_barrierefrei.pdf'),
('report2021','https://museen.freiburg.de/site/freiburg_museen2024/get/documents_E-1399915181/freiburg/daten_museen/Jahresberichte/STM_Jahresbericht_2021_final_barrierefrei_V2.pdf')]
HOSTS={'museen.freiburg.de','www.freiburg.de'}
TEMP=Path('/tmp/artline-augustiner-20261009')
def capture(key,url):
 assert urlparse(url).hostname in HOSTS
 folder=RUN/'captures';folder.mkdir(parents=True,exist_ok=True);body=folder/(key+'.body.gz');rp=folder/(key+'.json')
 if rp.exists():rc=m.load(rp);raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256']
 else:
  time.sleep(.5)
  with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected public collection evidence)'},timeout=(12,45),stream=True) as r:
   raw=b''
   for chunk in r.iter_content(65536):raw+=chunk;assert len(raw)<20_000_000
   assert urlparse(r.url).hostname in HOSTS
   rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(rp,rc)
 assert rc['status']==200,str(rc['status'])
 assert b'Access Denied' not in raw[:10000] and b'BotStopper' not in raw[:10000],'access_denied'
 cap=dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))
 if raw.startswith(b'%PDF'):
  TEMP.mkdir(exist_ok=True);pdf=TEMP/(key+'.pdf');txt=TEMP/(key+'.txt');pdf.write_bytes(raw);subprocess.run(['/opt/homebrew/bin/pdftotext','-layout',str(pdf),str(txt)],check=True);return dict(key=key,url=url,capture=cap,text=txt.read_text(),local_pdf=str(pdf))
 soup=BeautifulSoup(raw,'html.parser');return dict(key=key,url=url,capture=cap,parsed=dict(text=soup.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in soup.select('a[href]')],images=[dict(alt=a.get('alt',''),src=a.get('src',''),title=a.get('title','')) for a in soup.select('img')]))
def main():
 dest=RUN/'native-discovery-001.json.gz';assert not dest.exists();rows=[];stopped=set();fails={}
 m.save(RUN/'portal-access-hold-001.json',dict(at=m.now(),provider='onlinesammlung.freiburg.de',url='https://onlinesammlung.freiburg.de/de/search',observation='Web tool returned explicit Access Denied: error code 9e4edb5b6b850c41; Protected by BotStopper (Anubis/Techaro). Numeric HTTP status not supplied.',second_independent_batched_url='https://onlinesammlung.freiburg.de/de/object/2ECB9740477D7FC27516ACA5BD3CA52B',second_observation='Web tool cache-miss internal error; no fresh object evidence.',action='Stop portal requests. No alternate path,proxy,browser or private endpoint attempts. Independent public museum publications remain research sources. Search snippets are leads only.'))
 for key,url in SOURCES:
  host=urlparse(url).hostname
  if host in stopped:rows.append(dict(key=key,url=url,state='unrequested_after_access_hold'));continue
  try:row=capture(key,url);rows.append(row);fails[host]=0;print(json.dumps(dict(key=key,bytes=row['capture']['receipt']['bytes'])),flush=True)
  except Exception as e:
   rows.append(dict(key=key,url=url,error=type(e).__name__+': '+str(e)));fails[host]=fails.get(host,0)+1;print(json.dumps(rows[-1]),flush=True)
   if fails[host]>=3 or any(v in str(e) for v in ['403','429','access_denied']):stopped.add(host)
 m.save(dest,dict(at=m.now(),rows=rows,stopped_providers=sorted(stopped),script_reference=s.ref(Path(__file__).resolve()),policy='Seven selected museum-owned public publications only. PDFs require rendered-page review before artwork acceptance. Exhibition loans,unnamed groups,post1970works and other municipal museum collections do not become Augustiner holdings. No portal retry,image attachments or database writes.'))
if __name__=='__main__':main()
