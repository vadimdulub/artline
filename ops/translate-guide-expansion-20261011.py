"""Translate staged, authored guides with the existing Cloud Translation service.

The translated editions remain in staging for editorial review and PDF checks.
Object evidence is copied intact. Each artwork's title is translated alongside
its artist and paragraphs, rather than as an isolated ambiguous word.
"""

raise SystemExit("Disabled by user instruction on 12 October 2026: do not use Google services, including Cloud Translation.")

import concurrent.futures
import copy
import hashlib
import html
import json
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/museum-guides-80-20261011'
STAGE=Path('/tmp/artline-80-guides-20261011/editions')
PUBLIC=ROOT/'apps/web/content/articles/museum-guides'
CACHE=RUN/'translations';CACHE.mkdir(exist_ok=True)
LOCALES=['ru','it','de','zh','fr','es','pt','ja','ar']
MODEL='projects/artline-508319/locations/us-central1/models/general/translation-llm'
LOCK=threading.Lock();TOKEN=None;TOKEN_TIME=0
def load(p):return json.loads(p.read_text())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.partial');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def headers():
    global TOKEN,TOKEN_TIME
    with LOCK:
        if time.time()-TOKEN_TIME>1800:
            TOKEN=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip();TOKEN_TIME=time.time()
    return {'Authorization':'Bearer '+TOKEN,'x-goog-user-project':'artline-508319'}
def translate(texts,locale,mime='text/plain'):
    digest=hashlib.sha256(json.dumps([MODEL,locale,mime,texts],ensure_ascii=False).encode()).hexdigest();p=CACHE/(digest+'.json')
    if p.exists():result=load(p)
    else:
        for attempt in range(6):
            r=requests.post('https://translation.googleapis.com/v3/projects/artline-508319/locations/us-central1:translateText',headers=headers(),json={'model':MODEL,'contents':texts,'mimeType':mime,'sourceLanguageCode':'en','targetLanguageCode':locale},timeout=240)
            if r.ok or r.status_code not in [429,500,502,503,504]:break
            time.sleep(2**attempt+1)
        r.raise_for_status();result=r.json();save(p,result)
    assert len(result['translations'])==len(texts)
    return [html.unescape(x['translatedText'])for x in result['translations']]
def plain(s):return re.sub(r'\*([^*]+)\*',r'\1',s).strip()
def one(pair):
    slug,locale=pair;src=STAGE/slug/'en.json';original=load(src);digest=hashlib.sha256(src.read_bytes()).hexdigest()
    receipt=RUN/'translation-receipts'/f'{slug}-{locale}.json'
    if receipt.exists() and load(receipt)['englishSha256']==digest:return {'slug':slug,'locale':locale,'cached':True}
    edition=copy.deepcopy(original);edition['locale']=locale;edition['labels']=load(PUBLIC/'louvre'/f'{locale}.json')['labels']
    fields=[([k],original[k])for k in ['title','subtitle','introduction','visitNote','selectionNote','city','country'] if original[k]]
    for i,w in enumerate(original['works']):
        for key in ['date','medium']+(['artist'] if re.search(r'Attributed|Workshop|Follower|Unknown|Anonymous|attributed|workshop|follower',w['artist']) else []):
            if w[key] and (key=='medium' or re.search('[A-Za-zÀ-ž]',w[key])):fields.append((['works',i,key],w[key]))
    for i,b in enumerate(original['books']):
        for key in ['note','access']:fields.append((['books',i,key],b[key]))
    for (keys,_),value in zip(fields,translate([v for _,v in fields],locale)):
        target=edition
        for key in keys[:-1]:target=target[key]
        target[keys[-1]]=plain(value)
    chunks=[];batch=[];size=0
    for i,w in enumerate(original['works']):
        text='<div><h3>'+html.escape(w['title'])+'</h3><p>'+html.escape(w['artist'])+'</p><p>'+html.escape(w['description'])+'</p><p>'+html.escape(w['importance'])+'</p></div>'
        if batch and size+len(text)>20000:chunks.append(batch);batch=[];size=0
        batch.append((i,text));size+=len(text)
    if batch:chunks.append(batch)
    for batch in chunks:
        translated=translate([text for _,text in batch],locale,'text/html')
        for (i,_),value in zip(batch,translated):
            soup=BeautifulSoup(value,'html.parser');h=soup.find('h3');ps=soup.find_all('p')
            assert h is not None and len(ps)==3,(slug,locale,i,value)
            edition['works'][i]['title']=plain(h.get_text(' ',strip=True)).rstrip('.。')
            if original['works'][i]['id']=='e0d77fff-6b6b-5221-820d-e4e4aed13f33':
                # Flores is the sitter's name, not the Spanish noun for flowers.
                edition['works'][i]['title']='Flores'
            edition['works'][i]['description']=plain(ps[1].get_text(' ',strip=True))
            edition['works'][i]['importance']=plain(ps[2].get_text(' ',strip=True))
    edition['title']=edition['title'].rstrip('.。')
    save(STAGE/slug/f'{locale}.json',edition)
    save(receipt,{'slug':slug,'locale':locale,'englishSha256':digest,'model':MODEL,'artworks':len(edition['works']),'editorialReview':'Pending; automatic translation is not native-speaker verification.'})
    return {'slug':slug,'locale':locale,'cached':False}
if __name__=='__main__':
    slugs=sys.argv[1:]or sorted(p.name for p in STAGE.iterdir()if p.is_dir())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for row in pool.map(one,[(slug,locale)for slug in slugs for locale in LOCALES]):print(json.dumps(row),flush=True)
