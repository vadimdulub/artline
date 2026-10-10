"""Inspect source-observed public advanced-search controls and native collection homepage."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-war-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
CAP=RUN/'captures';BASE='https://www.searchculture.gr'
clean=c.module('q','museum-expansion-kazantzakis-selection-20261009.py').clean

def capture(key,url):
    CAP.mkdir(parents=True,exist_ok=True);rp,bp=CAP/(key+'.json'),CAP/(key+'.body.gz')
    if rp.exists():
        rc=m.load(rp);raw=gzip.decompress(bp.read_bytes());assert rc['url']==url and hashlib.sha256(raw).hexdigest()==rc['sha256'] and rc['status']==200
    else:
        response=requests.get(url,timeout=(15,45));raw=response.content;assert not bp.exists();bp.write_bytes(gzip.compress(raw));rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),content_type=response.headers.get('Content-Type'),body_path=str(bp.relative_to(m.ROOT)));m.save(rp,rc);response.raise_for_status()
    return BeautifulSoup(raw.decode('utf-8'),'html.parser'),rc

def main():
    assert not(RUN/'art-navigation-001.json.gz').exists();source=next(x for x in m.load(c.DISCOVERY)['rows'] if x['institution_id']==c.IID)
    raw=gzip.decompress((m.ROOT/source['receipt']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==source['receipt']['sha256'];doc=BeautifulSoup(raw,'html.parser')
    advanced=urljoin(BASE,doc.find('a',string=lambda x:x and 'More search options' in x)['href']);native='https://exhibition.warmuseumdigital.gr/';assert native in source['external_links'];rows=[]
    for key,url in [('advanced-001',advanced),('native-home-001',native)]:
        doc,rc=capture(key,url);controls=[]
        for label in doc.select('span.labels'):
            box=label.parent.parent;check=box.select_one('input[type=checkbox]')
            if check:
                name=check['name'];value=doc.find('input',attrs={'name':name.replace('.checked','.value')});field=name.split('.values')[0]+'.field';fv=doc.find('input',attrs={'name':field});controls.append(dict(label=clean(label.get_text(' ',strip=True)),text=clean(box.get_text(' ',strip=True)),control=name,value=value.get('value') if value else None,field_control=field,field_value=fv.get('value') if fv else None))
        forms=[dict(action=f.get('action'),method=f.get('method'),selects=[dict(name=x.get('name'),options=[dict(value=o.get('value'),label=clean(o.get_text(' ',strip=True))) for o in x.select('option')]) for x in f.select('select[name]')]) for f in doc.select('form')]
        links=[dict(title=clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href'])) for a in doc.select('a[href]') if a.get_text(' ',strip=True)]
        row=dict(key=key,receipt=rc,text=clean(doc.get_text(' ',strip=True)),controls=controls,forms=forms,links=links);rows.append(row);print(json.dumps(dict(key=key,status=rc['status'],controls=controls,text=row['text'][:4500]),ensure_ascii=False),flush=True)
    m.save(RUN/'art-navigation-001.json.gz',dict(at=m.now(),rows=rows,collection_reference=source['receipt'],source_total=1888,script_reference=c.ref(Path(__file__).resolve()),policy='Observed public advanced search and native homepage only. Art/type/date scope selection pending; no individual object/image downloads or writes. No retry of NHM facet or TIFF failures.'))

if __name__=='__main__':main()
