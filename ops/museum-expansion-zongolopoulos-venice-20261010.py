"""Inspect two observed public preservation previews for a possible repeated photograph."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN;PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/zongolopoulos-delivery-20261010'

def main():
    assert not(RUN/'venice-comparison-inputs-001.json').exists();out=[]
    for key in ['64302','64304']:
        body=c.RESEARCH/'captures'/('selected-'+key+'-001.body.gz');s=BeautifulSoup(gzip.decompress(body.read_bytes()),'html.parser');links={urljoin('https://www.searchculture.gr',a['href'])for a in s.select('a[href]')if '/ZoggopoulosF/000041-'+key+'/files/'in a['href']};assert len(links)==1
        url=links.pop();rc=RUN/'captures'/('venice-viewer-'+key+'-001.json');dest=RUN/'captures'/('venice-viewer-'+key+'-001.body.gz')
        if rc.exists():receipt=m.load(rc);raw=gzip.decompress(dest.read_bytes());assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
        else:
            response=requests.get(url,timeout=(15,40));response.raise_for_status();raw=response.content;dest.parent.mkdir(parents=True,exist_ok=True);dest.open('xb').write(gzip.compress(raw,mtime=0));receipt=dict(at=m.now(),url=url,final_url=response.url,status=response.status_code,sha256=hashlib.sha256(raw).hexdigest(),body_path=str(dest.relative_to(m.ROOT)));m.save(rc,receipt)
        soup=BeautifulSoup(raw,'html.parser');media=soup.select('img.files-thumbnail');assert len(media)==1;preview=urljoin(receipt['final_url'],media[0]['src']);assert '/digital-files-from-preservator/file/'in preview
        irc=RUN/'captures'/('venice-preview-'+key+'-001.json')
        if irc.exists():imrc=m.load(irc)
        else:
            response=requests.get(preview,timeout=(15,45));response.raise_for_status();data=response.content;image=Image.open(io.BytesIO(data));image.load();p=PROOF/'venice-comparison'/(key+'.jpg');p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(data);imrc=dict(at=m.now(),source_id='ZoggopoulosF/000041-'+key,url=preview,final_url=response.url,status=response.status_code,path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),width=image.width,height=image.height,viewer_receipt=receipt);m.save(irc,imrc)
        out.append(imrc)
    m.save(RUN/'venice-comparison-inputs-001.json',dict(at=m.now(),rows=out,purpose='Compare two selected source records that may be repeated/cropped photographs; do not infer physical duplication or distinctness from differing colours, export digits or file hashes alone.',web_tool_observation='Two source object opens returned inaccessible-tool errors; complete earlier source captures remained valid. Observed public viewer links are followed, not a restricted native host or guessed file route.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(previews=[dict(source_id=x['source_id'],width=x['width'],height=x['height'])for x in out])),flush=True)
if __name__=='__main__':main()
