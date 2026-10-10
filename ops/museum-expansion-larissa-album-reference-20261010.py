"""Preserve the observed parliamentary catalogue and render only Kanas reference pages."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import requests

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-larissa-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF=v.m,v.RUN,v.PROOF
URL='https://www.hellenicparliament.gr/UserFiles/8c3e9046-78fb-48f4-bd82-bbba28ca1ef5/2019_%CE%A7%CE%91%CE%A1%CE%91%CE%93%CE%9C%CE%91%CE%A4%CE%91.pdf'

def main():
    folder=PROOF/'reference-pdf';folder.mkdir(parents=True,exist_ok=True);p=folder/'parliament-charagmata-2019.pdf'
    res=requests.get(URL,timeout=(15,90));res.raise_for_status();raw=res.content;assert raw.startswith(b'%PDF')and len(raw)<60000000 and not p.exists();p.write_bytes(raw)
    rc=dict(at=m.now(),url=URL,final_url=res.url,status=res.status_code,content_type=res.headers.get('Content-Type'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=str(p),purpose='Read the specific Kanas album catalogue entry. Web tool could not load55.7MBPDF because of its content-size limit, not a provider access denial.')
    m.save(RUN/'captures/album-reference-pdf-001.json',rc)
    txt=folder/'parliament-charagmata-2019.txt';subprocess.run(['pdftotext','-layout',str(p),str(txt)],check=True)
    pages=txt.read_text().split('\f');selected=[]
    for i,text in enumerate(pages,1):
        if '12' in text and ('ΚΑΝΑΣ'in text or 'Κανάς'in text):
            prefix=folder/('kanas-page-'+str(i));subprocess.run(['pdftoppm','-f',str(i),'-singlefile','-r','100','-png',str(p),str(prefix)],check=True)
            selected.append(dict(pdf_page=i,text=text,render=v.ref(str(prefix)+'.png')))
    assert selected
    m.save(RUN/'album-reference-001.json.gz',dict(at=m.now(),receipt=rc,text_reference=v.ref(txt),selected_pages=selected,script_reference=v.ref(Path(__file__).resolve()),
        policy='Publication supports album title/edition context; Larissa holdings require its own native source pages. Do not substitute this photographed institutional copy for the Larissa copy. Visual review of selected pages pending.'))
    print(json.dumps(dict(bytes=len(raw),pages=[dict(page=x['pdf_page'],text=x['text'])for x in selected]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
