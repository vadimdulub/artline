#!/usr/bin/env python3
"""Immutable official museum metadata captures. No catalogue writes or images."""
import argparse,collections,concurrent.futures,csv,gzip,hashlib,importlib.util,json,os,time,threading,xml.etree.ElementTree as ET
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('million',Path(__file__).with_name('million-catalogue-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
UA='Artline museum catalogue research; metadata selection'
_sessions=threading.local()
def session():
    if not hasattr(_sessions,'value'):_sessions.value=requests.Session()
    return _sessions.value
def capture(key,url):
    dest=m.DATA/key;receipt=m.RUN/'sources'/(key+'.receipt.json')
    if receipt.exists():
        rc=m.load(receipt);assert dest.exists() and m.sha(dest.read_bytes())==rc['sha256'];return dest
    hold=m.RUN/'access-holds'/(requests.utils.urlparse(url).hostname+'.json')
    assert not hold.exists(),'Access hold: '+str(hold)
    dest.parent.mkdir(parents=True,exist_ok=True);temp=dest.with_suffix(dest.suffix+'.part')
    with session().get(url,headers={'User-Agent':UA},stream=True,timeout=(20,90)) as r:
        rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),content_type=r.headers.get('Content-Type'),etag=r.headers.get('ETag'))
        if r.status_code in (401,403,429):m.save(hold,rc)
        r.raise_for_status();h=hashlib.sha256();size=0
        with temp.open('wb') as out:
            for b in r.iter_content(1024*1024):out.write(b);h.update(b);size+=len(b)
    rc.update(sha256=h.hexdigest(),bytes=size,path=str(dest));os.replace(temp,dest);m.save(receipt,rc)
    print(key,size,flush=True);return dest
def nga():
    base='https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/'
    names=['objects.csv','constituents.csv','objects_constituents.csv','published_images.csv','object_associations.csv']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(lambda n:capture('nga/'+n,base+'data/'+n),names))
    capture('nga/data-dictionary.txt',base+'documentation/Data%20Dictionary.txt')
def met():capture('met/MetObjects.csv','https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv')
def rijks_probe():
    for verb in ['Identify','ListSets','ListMetadataFormats','ListRecords&metadataPrefix=edm']:
        capture('rijks/'+verb.split('&')[0]+'.xml','https://data.rijksmuseum.nl/oai?verb='+verb)
def rijks_harvest():
    """One sequential metadata stream; immutable pages and server-issued tokens."""
    ns={'o':'http://www.openarchives.org/OAI/2.0/'};url='https://data.rijksmuseum.nl/oai?verb=ListRecords&metadataPrefix=edm'
    for page in range(20000):
        if (m.RUN/'target-reached.json').exists():print('Catalogue target reached; metadata harvest checkpointed.',flush=True);return
        key='rijks/pages/'+str(page).zfill(5)+'.xml'
        fresh=page>0 and not (m.RUN/'sources'/(key+'.receipt.json')).exists()
        if page==0:
            path=m.DATA/'rijks/ListRecords.xml'
        else:
            for attempt in range(4):
                try:path=capture(key,url);break
                except (requests.exceptions.Timeout,requests.exceptions.ConnectionError,requests.exceptions.ChunkedEncodingError):
                    if attempt==3:raise
                    print('Transient metadata transport failure at page',page,'attempt',attempt+1,flush=True);time.sleep(5*(attempt+1))
        root=ET.parse(path);errors=root.findall('o:error',ns);assert not errors,[e.text for e in errors]
        token=root.find('.//o:resumptionToken',ns)
        if token is None or not token.text:print('Rijks metadata complete',page+1,flush=True);return
        url=requests.Request('GET','https://data.rijksmuseum.nl/oai',params={'verb':'ListRecords','resumptionToken':token.text}).prepare().url
        if fresh:time.sleep(.15)
def inspect():
    for p in m.DATA.glob('nga/*.csv'):
        with p.open(newline='',encoding='utf-8-sig') as f:
            rd=csv.DictReader(f);rows=[];counts=collections.Counter();n=0
            for r in rd:
                n+=1
                if len(rows)<2:rows.append(r)
                if p.name=='objects.csv':counts[(r.get('classification'),r.get('accessioned'))]+=1
        print(json.dumps(dict(file=p.name,count=n,samples=rows,types=counts.most_common(40)),ensure_ascii=False),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['nga','met','rijks_probe','rijks_harvest','inspect']);a=ap.parse_args();globals()[a.action]()
