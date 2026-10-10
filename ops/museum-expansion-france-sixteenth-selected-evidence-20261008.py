"""Bounded captures of three selected identity references; no image attachments."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-sixteenth-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
SOURCES=[('ng2092',567,'https://www.nationalgallery.org.uk/paintings/moretto-da-brescia-saint-joseph','html'),('desiderio',542,'https://www.wikiart.org/en/desiderio-da-settignano/vierge-a-lenfant-1460','html'),('desiderio-image',542,'https://uploads3.wikiart.org/00287/images/desiderio-da-settignano/virgin-with-child-mba-lyon-d-612-img-0658.JPG','jpg'),('pompadour-image',439,'https://uploads1.wikiart.org/images/maurice-quentin-de-la-tour/portrait-of-madame-de-pompadour.jpg','jpg')]
def main():
    root=i.RUN/'selected-evidence-001';assert not root.exists();root.mkdir();out=[]
    for name,number,url,kind in SOURCES:
        try:
            with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0'},timeout=(15,45),stream=True) as response:
                raw=b''
                for b in response.iter_content(65536):
                    raw+=b
                    if len(raw)>8_000_000:raise ValueError('Bounded response exceeded')
                p=root/(name+('.html.gz' if kind=='html' else '.jpg'));p.write_bytes(gzip.compress(raw,mtime=0) if kind=='html' else raw)
                receipt=dict(number=number,name=name,url=url,final_url=response.url,status=response.status_code,retrieved_at=i.m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),body_reference=i.ref(p));i.m.save(root/(name+'.receipt.json'),receipt);response.raise_for_status()
            if kind=='html':
                soup=BeautifulSoup(raw,'html.parser')
                for tag in soup(['script','style','noscript']):tag.decompose()
                p=root/(name+'.txt');p.write_text(soup.get_text('\n',strip=True));receipt['text_reference']=i.ref(p)
            out.append(receipt);print(json.dumps(dict(name=name,status=response.status_code)),flush=True)
        except Exception as error:
            receipt=dict(name=name,number=number,url=url,error=repr(error),policy='No retry or access bypass.');i.m.save(root/(name+'.error.json'),receipt);out.append(receipt);print(json.dumps(receipt),flush=True)
    i.m.save(i.RUN/'selected-evidence-001.json',dict(at=i.m.now(),rows=out,extractor_reference=i.ref(Path(__file__).resolve()),policy='Selected WikiArt images used only for object-identity review under user approval. No database image attachment, publication or catalogue changes.',database_writes=0))
if __name__=='__main__':main()
