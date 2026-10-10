"""Inspect one observed digital-file link for an explicitly seventeenth-century work."""
import hashlib, importlib.util, json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-nhm-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def main():
    dest=RUN/'digital-file-discovery-001.json';assert not dest.exists()
    row=next(x for x in m.load(RUN/'selected-source-records-001.json.gz')['rows'] if x['number']==7)
    assert '17ος αιώνας' in ' '.join(row['fields']['Περιγραφή']) and len(row['file_links'])==1
    url=row['file_links'][0];folder=c.PROOF/'digital-file-discovery';folder.mkdir(parents=True,exist_ok=True);path=folder/'007-response.body';assert not path.exists()
    with requests.get(url,timeout=(15,45),stream=True) as response:
        size=0
        with path.open('xb') as out:
            for chunk in response.iter_content(65536):
                size+=len(chunk);assert size<=50000000,'Selected source file exceeds inspection limit';out.write(chunk)
        value=dict(at=m.now(),number=7,source_id=row['source_id'],url=url,final_url=response.url,status=response.status_code,content_type=response.headers.get('Content-Type'),bytes=size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path),redirects=[dict(status=x.status_code,url=x.url,location=x.headers.get('Location')) for x in response.history])
    if response.status_code==200 and 'html' in (value['content_type'] or ''):
        doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser');value.update(text=src.clean(doc.get_text(' ',strip=True)),links=[dict(label=src.clean(x.get_text(' ',strip=True)),url=urljoin(response.url,x['href'])) for x in doc.select('a[href]')],images=[urljoin(response.url,x['src']) for x in doc.select('img[src]')])
    elif response.status_code==200:
        with Image.open(path) as im:value.update(format=im.format,width=im.width,height=im.height)
    m.save(dest,dict(at=m.now(),result=value,source_reference=c.ref(RUN/'selected-source-records-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),policy='One source-observed digital-file link inspected for a selected seventeenth-century painting; no image delivery or database writes. Original bytes remain in Library.'))
    print(json.dumps(value,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
