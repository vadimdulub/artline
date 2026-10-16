"""Inspect two observed museum collections and their public art/date search controls."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-momus-common-20261011.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
CAP=RUN/'captures';BASE='https://www.searchculture.gr'
clean=c.module('cleaner','museum-expansion-kazantzakis-selection-20261009.py').clean

def capture(key,url):
    CAP.mkdir(parents=True,exist_ok=True);rp,bp=CAP/(key+'.json'),CAP/(key+'.body.gz')
    if rp.exists():
        rc=m.load(rp);raw=gzip.decompress(bp.read_bytes());assert rc['url']==url and hashlib.sha256(raw).hexdigest()==rc['sha256'] and rc['status']==200
    else:
        response=requests.get(url,timeout=(15,45));raw=response.content;assert not bp.exists();bp.write_bytes(gzip.compress(raw));rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),content_type=response.headers.get('Content-Type'),body_path=str(bp.relative_to(m.ROOT)));m.save(rp,rc);response.raise_for_status()
    return BeautifulSoup(raw.decode('utf-8'),'html.parser'),rc

def extract(key,doc,rc):
    controls=[]
    for label in doc.select('span.labels'):
        box=label.parent.parent;check=box.select_one('input[type=checkbox]')
        if check:
            name=check['name'];value=doc.find('input',attrs={'name':name.replace('.checked','.value')});field=name.split('.values')[0]+'.field';fv=doc.find('input',attrs={'name':field});controls.append(dict(label=clean(label.get_text(' ',strip=True)),text=clean(box.get_text(' ',strip=True)),control=name,value=value.get('value') if value else None,field_control=field,field_value=fv.get('value') if fv else None))
    forms=[dict(action=f.get('action'),method=f.get('method'),inputs=[dict(name=x.get('name'),value=x.get('value'),type=x.get('type')) for x in f.select('input[name]') if 'token' not in x.get('name','').lower()],selects=[dict(name=x.get('name'),options=[dict(value=o.get('value'),label=clean(o.get_text(' ',strip=True))) for o in x.select('option')]) for x in f.select('select[name]')]) for f in doc.select('form')]
    links=[dict(title=clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href'])) for a in doc.select('a[href]')]
    return dict(key=key,receipt=rc,text=clean(doc.get_text(' ',strip=True)),controls=controls,forms=forms,links=links)
