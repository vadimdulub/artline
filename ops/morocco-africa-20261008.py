#!/usr/bin/env python3
"""Source-pinned Morocco/Africa directory and selected catalogue additions."""
import argparse, collections, concurrent.futures, gzip, hashlib, json, re, time, unicodedata, uuid
from pathlib import Path
from urllib.parse import urljoin
import psycopg, requests
from psycopg.rows import dict_row
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/morocco-africa-20261008'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/morocco-africa-20261008'
ACTOR='local-european-research'
AFRICA='DZ AO BJ BW BF BI CV CM CF TD KM CG CD CI DJ EG GQ ER SZ ET GA GM GH GN GW KE LS LR LY MG MW ML MR MU MA MZ NA NE NG RW ST SN SC SL SO ZA SS SD TZ TG TN UG ZM ZW'.split()
def now(): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def norm(v): return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',v or '').casefold() if not unicodedata.combining(c))))
def uid(v): return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline/morocco-africa-20261008/'+v))
def save(path,v):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()
    if path.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
    if path.exists():assert path.read_bytes()==raw,'Preserve evidence '+str(path)
    else:path.write_bytes(raw)
def load(path):return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
def connect(write=False):return psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=dict_row,options='-c timezone=UTC -c statement_timeout=120000'+('' if write else ' -c default_transaction_read_only=on'))
def capture(url):
    key=hashlib.sha256(url.encode()).hexdigest();folder=RUN/'captures';receipt=folder/(key+'.json');body=folder/(key+'.body.gz')
    if receipt.exists():
        r=load(receipt)
        if r.get('error'):return r,None
        raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==r['sha256'];return r,raw
    folder.mkdir(parents=True,exist_ok=True)
    try:
        response=requests.get(url,timeout=(15,45),headers={'User-Agent':'Artline catalogue research/1.0 (selected museum metadata; no images)'})
        raw=response.content;assert len(raw)<25000000
        r=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),body_path=str(body.relative_to(ROOT)))
        body.write_bytes(gzip.compress(raw,mtime=0))
        if response.status_code!=200:r['error']='HTTP '+str(response.status_code)
    except Exception as e:r=dict(url=url,retrieved_at=now(),error=str(e));raw=None
    save(receipt,r);return r,raw if not r.get('error') else None
def page(url):
    r,raw=capture(url)
    if raw is None:return r,None,None
    soup=BeautifulSoup(raw,'html.parser')
    for tag in soup(['script','style','nav','footer','header']):tag.decompose()
    return r,soup,soup.get_text('\n',strip=True)
def audit():
    with connect() as db:
        institutions=db.execute('SELECT to_jsonb(i) row FROM institutions i ORDER BY id').fetchall()
        places=db.execute('SELECT to_jsonb(p) row FROM places p ORDER BY id').fetchall()
        countries=db.execute('SELECT * FROM countries WHERE code=ANY(%s) ORDER BY code',(AFRICA,)).fetchall()
    save(RUN/'initial-directory.json.gz',dict(at=now(),institutions=[x['row'] for x in institutions],places=[x['row'] for x in places],countries=countries))
    print('Saved directory',len(institutions),'institutions;',len(places),'places')
def initial():
    for key,url in [('fnm','https://www.fnm.ma/museums/'),('villa','https://www.villadesarts.ma/composition-70'),('morocco-list','https://en.wikipedia.org/wiki/List_of_museums_in_Morocco'),('macaal','https://macaal.org/en/collection')]:
        r,s,t=page(url)
        if s:
            save(RUN/(key+'-page.json'),dict(receipt=r,text=t,links=[dict(text=a.get_text(' ',strip=True),url=urljoin(r['final_url'],a['href'])) for a in s.select('a[href]')]))
            print(key,len(t))
        else:print(key,r.get('error'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','initial']);args=p.parse_args();globals()[args.command]()
