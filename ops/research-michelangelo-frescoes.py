#!/usr/bin/env python3
"""Research a bounded selection of twelve Michelangelo frescoes and Commons files."""
import hashlib, json, time
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT=Path(__file__).resolve().parent.parent
RUN=ROOT/'docs/research/michelangelo-frescoes-20260913'
IDS=['Q3955636','Q3696827','Q3955632','Q500242','Q3696835','Q3898510','Q3944655','Q3707697','Q116621556','Q567861','Q2432043','Q1886263']
BASE='https://www.museivaticani.va/content/museivaticani/en/collezioni/musei/cappella-sistina/'
URLS=[BASE+'volta.html',BASE+'volta/storie-centrali.html',BASE+'giudizio-universale.html','https://www.vatican.va/news_services/liturgy/chapel/paolina_en.html']
SESSION=requests.Session()
SESSION.headers['User-Agent']='Artline/1.0 (selected art catalogue research; https://github.com/vadimdulub/artline)'

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    if path.exists():assert path.read_bytes()==raw,'Preserve existing evidence: '+str(path)
    else:path.write_bytes(raw)

def fetch(url,is_json=True):
    key=hashlib.sha256(url.encode()).hexdigest();path=RUN/'captures'/(key+('.json' if is_json else '.html'))
    if path.exists():
        raw=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
        return json.loads(raw) if is_json else raw,receipt
    for attempt in range(4):
        time.sleep(1)
        r=SESSION.get(url,timeout=(15,40));r.raise_for_status();raw=r.content
        assert len(raw)<8_000_000
        if is_json and r.json().get('error',{}).get('code')=='maxlag':time.sleep(10);continue
        if is_json:assert 'error' not in r.json(),str(r.json())[:200]
        receipt={'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        save(path,raw);save(path.with_suffix('.receipt.json'),receipt)
        return json.loads(raw) if is_json else raw,receipt
    raise RuntimeError('Wikimedia replication lag; evidence remains pending')

def values(entity,prop):
    return [s['mainsnak']['datavalue']['value'] for s in entity.get('claims',{}).get(prop,[]) if s.get('rank')!='deprecated' and s.get('mainsnak',{}).get('snaktype')=='value']

def main():
    official=[fetch(u,False)[1] for u in URLS]
    records=[]
    for i,qid in enumerate(IDS):
        data,receipt=fetch('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json');e=data['entities'][qid]
        assert 'Q5592' in {v.get('id') for v in values(e,'P170')},'Creator identity mismatch: '+qid
        images=values(e,'P18');assert images,'No documented image: '+qid
        record={'qid':qid,'title':e.get('labels',{}).get('en',{}).get('value',qid),'entity':e,'entity_receipt':receipt,'official_evidence':official[:2] if i<9 else [official[2 if i==9 else 3]],'location':'Sistine Chapel, Vatican City' if i<10 else 'Pauline Chapel, Apostolic Palace, Vatican City','institution_slug':'sistine-chapel' if i<10 else 'pauline-chapel','first':1508 if i<9 else 1536 if i==9 else 1542,'last':1512 if i<9 else 1541 if i==9 else 1550,'date_basis':'Documented ceiling campaign; individual scene dating remains in review' if i<9 else 'Documented Last Judgment campaign' if i==9 else 'Documented Pauline Chapel campaign; individual fresco dating remains in review','images':images}
        records.append(record);print(qid,record['title'],images,flush=True)
    titles=['File:'+r['images'][0] for r in records]
    url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'|'.join(titles),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size','rvprop':'ids|content','rvslots':'main','maxlag':5})
    data,receipt=fetch(url);pages={p['title'].replace('_',' '):p for p in data['query']['pages'].values()}
    for r in records:
        p=pages['File:'+r['images'][0].replace('_',' ')];info=p['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','')
        r['commons_page']=p;r['commons_receipt']=receipt;r['image_info']=info
        r['rights_cleared']=field('LicenseShortName')=='Public domain' and field('Copyrighted')=='False'
        r['license_label']=field('LicenseShortName');r['license_url']='https://creativecommons.org/publicdomain/mark/1.0/' if r['rights_cleared'] else field('LicenseUrl')
        r['commons_creator_credit']=field('Artist');r['commons_credit']=field('Credit')
        print('Rights',r['qid'],r['license_label'],r['rights_cleared'],info.get('size'),flush=True)
    save(RUN/'researched-records.json',records)

if __name__=='__main__':main()
