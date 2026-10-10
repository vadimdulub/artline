"""Selected curator-authored newsletters and a host museum's exact lender list."""
import gzip,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
from urllib.parse import urlparse
import requests
z=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-city-art-additions-discovery-20261009.py'));d=importlib.util.module_from_spec(z);z.loader.exec_module(d);s=d.s;m=s.m;RUN=s.RUN
DOCS=[('winter2014','https://ssahistory.wordpress.com/wp-content/uploads/2015/08/2014-15-winter-newsletter.pdf'),('summer2022','https://ssahistory.wordpress.com/wp-content/uploads/2023/03/ssah-spring-summer2022-newsletter.pdf'),('summer2014','https://ssahistory.wordpress.com/wp-content/uploads/2015/07/ssah_newsletter_08-14.pdf')]
def main():
 dest=RUN/'selected-documents-001.json.gz';assert not dest.exists();rows=[];stopped=False;fails=0;folder=RUN/'documents';folder.mkdir(parents=True,exist_ok=True);temp=Path('/tmp/artline-city-art-additions-20261009');temp.mkdir(exist_ok=True)
 for key,url in DOCS:
  if stopped:rows.append(dict(key=key,url=url,state='unrequested_after_access_hold'));continue
  try:
   time.sleep(.5)
   with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected curator-authored public documents)'},timeout=(12,45),stream=True) as r:
    raw=b''
    for c in r.iter_content(65536):raw+=c;assert len(raw)<20_000_000
    cap=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());body=folder/(key+'.body.gz');assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(folder/(key+'.json'),cap);r.raise_for_status();assert urlparse(r.url).hostname=='ssahistory.wordpress.com' and raw.startswith(b'%PDF')
   pdf=temp/(key+'.pdf');pdf.write_bytes(raw);txt=temp/(key+'.txt');subprocess.run(['/opt/homebrew/bin/pdftotext','-layout',str(pdf),str(txt)],check=True);rows.append(dict(key=key,capture=dict(receipt=cap,body_path=str(body.relative_to(m.ROOT))),text=txt.read_text(),local_pdf=str(pdf)));fails=0;print(json.dumps(dict(key=key,bytes=len(raw))),flush=True)
  except Exception as e:
   rows.append(dict(key=key,url=url,error=type(e).__name__+': '+str(e)));fails+=1;print(json.dumps(rows[-1]),flush=True)
   if fails>=3 or any(t in str(e) for t in ['403','429','robots']):stopped=True
 d.n.HOSTS['talbot']={'www.trg.ed.ac.uk','trg.ed.ac.uk'};url='https://www.trg.ed.ac.uk/exhibition/wide-new-kingdom-celtic-revival-scotland'
 try:
  raw,cap=d.n.capture('talbot',url);rows.append(dict(key='talbot',url=url,capture=cap,parsed=d.n.parsed(raw)))
 except Exception as e:rows.append(dict(key='talbot',url=url,error=type(e).__name__+': '+str(e)))
 m.save(dest,dict(at=m.now(),rows=rows,newsletter_requests_stopped=stopped,script_reference=s.ref(Path(__file__).resolve()),policy='Three selected art-history newsletters:only exact curator-authored collection articles accepted after visual review. Host gallery lender list distinguishes CityArtCentre loans from other collections. No catalogue image attachment,librarybookdownload,heldproviderretry or database writes.'))
if __name__=='__main__':main()
