"""Read one selected museum educational PDF from its public media catalogue."""
import importlib.util,json,hashlib,gzip,subprocess
from pathlib import Path
from urllib.parse import urlparse
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-box-continuation-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m
def main():
 dest=s.RUN/'reynolds-guide-001.json';assert not dest.exists();src=m.load(s.RUN/'supplements-001.json.gz');row=next(r for r in src['rows'] if '/media?' in r['url']);v=row['data'][0];assert v['id']==7080;url=v['source_url'];assert urlparse(url).hostname=='theboxplymouth.com'
 with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected public museum educational document)'},timeout=(12,45),stream=True) as r:
  data=b''
  for chunk in r.iter_content(65536):data+=chunk;assert len(data)<20_000_000
  cap=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest());assert urlparse(r.url).hostname=='theboxplymouth.com'
 body=s.RUN/'box/reynolds-guide-001.pdf.gz';body.parent.mkdir(parents=True,exist_ok=True);assert not body.exists();body.write_bytes(gzip.compress(data,mtime=0))
 out=dict(at=m.now(),capture=cap,body_reference=s.ref(body),media_record=v,metadata_reference=s.ref(s.RUN/'supplements-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='One selected museum source PDF,not catalogue image attachments. Raw document retained;rendered proofs outside Documents. PDF evidence requires visual QA before acceptance.')
 if cap['status']==200 and data.startswith(b'%PDF'):
  temp=Path('/tmp/artline-box-continuation-20261009');temp.mkdir(exist_ok=True);pdf=temp/'reynolds.pdf';pdf.write_bytes(data);txt=temp/'reynolds.txt';subprocess.run(['/opt/homebrew/bin/pdftotext','-layout',str(pdf),str(txt)],check=True);out['text']=txt.read_text();out['local_pdf']=str(pdf)
 else:out['error']='Source document unavailable; no alternate/private route attempted.'
 m.save(dest,out);print(json.dumps(cap),flush=True)
if __name__=='__main__':main()
