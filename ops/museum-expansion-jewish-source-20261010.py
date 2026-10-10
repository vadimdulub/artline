"""Inspect two observed museum collections and their public art/date search controls."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-jewish-common-20261010.py'))
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

def main():
    dest=RUN/'source-navigation-001.json.gz';assert not dest.exists();source=next(x for x in m.load(c.DISCOVERY)['rows'] if x['institution_id']==c.IID)
    raw=gzip.decompress((m.ROOT/source['receipt']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==source['receipt']['sha256'];doc=BeautifulSoup(raw.decode('utf-8'),'html.parser')
    advanced=urljoin(BASE,doc.find('a',string=lambda x:x and 'More search options' in x)['href']);other=next(x['url'] for x in source['navigation'] if x['title'].startswith('Jewish Museum of Greece Collection'));native='https://artifacts.jewishmuseum.gr/';assert native in source['external_links']
    requests0=[('narratives-advanced-001',advanced),('collection-001',other),('native-home-001',native)];rows=[];held=[]
    for key,url in requests0:
        try:doc,rc=capture(key,url)
        except Exception as exc:
            rp=CAP/(key+'.json');held.append(dict(key=key,url=url,error=type(exc).__name__,receipt=m.load(rp) if rp.exists() else None));continue
        row=extract(key,doc,rc);rows.append(row);print(json.dumps(dict(key=key,status=rc['status'],text=row['text'][:1300],type_controls=[dict(label=x['label'],text=x['text']) for x in row['controls'] if 'dc_type_hierarchy' in x['control']]),ensure_ascii=False),flush=True)
        if key=='collection-001':
            links=[x for x in row['links'] if 'advancedSearch' in x['url'] and 'providerInstitytionShortNames' in x['url']];assert len(links)==1;requests0.append(('collection-advanced-001',links[0]['url']))
    m.save(dest,dict(at=m.now(),rows=rows,held=held,narratives_collection_reference=source['receipt'],discovery_reference=c.ref(c.DISCOVERY),script_reference=c.ref(Path(__file__).resolve()),policy='Two observed collection contexts:1044digitalnarrative records and13533generalcollectionrecords. Art/date facets inspected before bounded selection; overlap and page/view-level records require physicalobject reconciliation. No individualobject or image retrieval, no cataloguewrites.'))

if __name__=='__main__':main()
