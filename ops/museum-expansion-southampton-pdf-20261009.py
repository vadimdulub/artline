"""Retain one collection exhibition catalogue and render selected pages for identity review."""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-southampton-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
URL='https://jcfa.co.uk/usr/library/documents/main/southampton-city-gallery-catalogue.pdf'
def main():
 dest=RUN/'exhibition-catalogue-001.json';path=RUN/'source-catalogue-001.pdf';assert not dest.exists() and not path.exists()
 response=requests.get(URL,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected source catalogue)'},timeout=(12,60),stream=True);raw=bytearray()
 for part in response.iter_content(65536):
  raw.extend(part);assert len(raw)<=32_000_000,'Selected catalogue exceeds32MB bound'
 raw=bytes(raw);receipt=dict(at=m.now(),url=URL,final_url=response.url,status=response.status_code,content_type=response.headers.get('Content-Type'),bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest());m.save(RUN/'source-catalogue-receipt-001.json',receipt);response.raise_for_status();assert response.url==URL and raw.startswith(b'%PDF-');path.write_bytes(raw)
 temp=Path('/tmp/artline-southampton-20261009');temp.mkdir(exist_ok=True);textpath=temp/'catalogue.txt';subprocess.run(['pdftotext','-layout',str(path),str(textpath)],check=True);pages=textpath.read_text().split('\f');assert len(pages) in [50,51];render=temp/'gosse-page';subprocess.run(['pdftoppm','-f','14','-l','14','-singlefile','-scale-to','1800','-png',str(path),str(render)],check=True)
 m.save(dest,dict(at=m.now(),source_url=URL,receipt_reference=ref(RUN/'source-catalogue-receipt-001.json'),pdf_reference=ref(path),text_pages=pages,rendered_selected_pages=[dict(zero_based_pdf_page=13,path=str(render)+'.png',sha256=hashlib.sha256(Path(str(render)+'.png').read_bytes()).hexdigest())],script_reference=ref(Path(__file__).resolve()),policy='One published Southampton collection exhibition catalogue retained as research evidence. Selected page14 rendered outside Documents for visual version review; no catalogue image attachment or exhaustive artwork-image download. Acquisition/exhibition dates do not supply creation. Source date/dimension disagreements remain explicit.'))
 print(json.dumps(dict(bytes=len(raw),pages=len(pages),rendered=str(render)+'.png')),flush=True)
if __name__=='__main__':main()
