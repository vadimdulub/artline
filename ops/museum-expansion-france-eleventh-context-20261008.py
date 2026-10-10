"""Bounded primary-source captures for museum identity reconciliation."""
import gzip, hashlib, importlib.util, json, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-france-eleventh-discovery-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;RUN=d.RUN
SOURCES=[('vendome-museofile','https://pop.culture.gouv.fr/notice/museo/M0277'),('beaune-museofile','https://pop.culture.gouv.fr/notice/museo/M0134'),('saint-denis-museofile','https://pop.culture.gouv.fr/notice/museo/M0422'),('belfort-museofile','https://pop.culture.gouv.fr/notice/museo/M0361'),('honfleur-museofile','https://pop.culture.gouv.fr/notice/museo/M0661')]
def main():
    root=RUN/'museum-context-001';assert not root.exists();root.mkdir()
    for name,url in SOURCES:
        try:
            time.sleep(1)
            with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected museum identity evidence)'},timeout=(15,45),stream=True) as response:
                raw=b''
                for chunk in response.iter_content(65536):
                    raw+=chunk
                    if len(raw)>4_000_000:raise ValueError('Bounded primary-source response exceeded')
                receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                (root/(name+'.html.gz')).write_bytes(gzip.compress(raw,mtime=0));m.save(root/(name+'.receipt.json'),receipt);response.raise_for_status()
            soup=BeautifulSoup(raw,'html.parser')
            for tag in soup(['script','style','noscript']):tag.decompose()
            (root/(name+'.txt')).write_text(soup.get_text(' ',strip=True))
            print(json.dumps(dict(name=name,status=receipt['status'],bytes=len(raw))),flush=True)
        except Exception as error:
            m.save(root/(name+'.error.json'),dict(at=m.now(),url=url,error=repr(error),policy='Stop first failure; no retry or access bypass.'));raise
    m.save(RUN/'museum-context-capture-complete-001.json',dict(at=m.now(),sources=SOURCES,read_only=True,images=0))
if __name__=='__main__':main()
