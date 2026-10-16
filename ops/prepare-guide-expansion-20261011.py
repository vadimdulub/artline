"""Prepare editorial candidates, selected image sheets and linked-source receipts.

This prepares research only. Publication requires individually written copy and
review. No catalogue writes; images are existing selected Artline reproductions.
"""
import collections
import concurrent.futures
import gzip
import hashlib
import io
import json
import re
import sys
import textwrap
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/museum-guides-80-20261011'
TEMP=Path('/tmp/artline-80-guides-20261011')
CACHE=Path('/tmp/artline-guides-20261010/images')
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def load(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def norm(value):return re.sub(r'\W+','',(value or '').casefold())
def image_url(w):
    m=w['media']
    return 'https://artlines.org'+m['storage_path'] if m['storage_kind']=='local' else m['delivery_url']
def prepare():
    selections=collections.defaultdict(list)
    for s in load(RUN/'prior-editorial-selections.json'):selections[s['id']].append(s)
    anchors=load(RUN/'anchors.json')
    for path in sorted((RUN/'catalogue').glob('*.json.gz')):
        slug=path.name.removesuffix('.json.gz');dest=RUN/'selections'/(slug+'.json')
        if dest.exists() and (load(dest).get('anchorsApplied') or load(dest).get('reviewed')):continue
        data=load(path);works=data['works']
        def score(w):
            rank=0
            if w['work_type']=='painting':rank+=40
            elif w['work_type']in ['drawing','fresco','sculpture']:rank+=15
            if w['creation_year_end']is not None:rank+=5
            if w['holdings']:rank+=15
            ss=selections[w['id']]
            if any(s['collection']['curator_kind']=='museum' for s in ss):rank+=80
            elif ss:rank+=35
            if w['artists']:rank+=5
            return rank
        eligible=[w for w in works if w['holdings'] and image_url(w) and (w['creation_year_end']is None or w['creation_year_end']<=1970) and (w['creation_year_start']is None or w['creation_year_start']<=1970)]
        ranked=sorted(eligible,key=lambda w:(-score(w),w['title'],w['id']))
        picked=[];seen=set();artists=collections.Counter()
        def add(w,cap=20):
            creator=';'.join(a['name']for a in w['artists']) or w['unlinked_creator_label'] or 'Anonymous'
            keys=[('id',w['id']),('image',w['media'].get('checksum_sha256')or image_url(w)),('title',norm(creator),norm(w['title']))]
            if w['accession_number']:keys.append(('accession',norm(w['accession_number'])))
            if any(k in seen for k in keys) or artists[creator]>=cap:return False
            picked.append(w);artists[creator]+=1;seen.update(keys);return True
        anchor_results=[]
        for pattern in anchors.get(slug,[]):
            matches=[w for w in ranked if re.search(pattern,w['title'],re.I)]
            selected=None
            for w in matches:
                if len(picked)<20 and add(w):selected=w['id'];break
            anchor_results.append({'pattern':pattern,'matches':len(matches),'selected':selected})
        for max_per_artist in [3,5,10,20]:
            if len(picked)==20:break
            for w in ranked:
                add(w,max_per_artist)
                if len(picked)==20:break
            if len(picked)==20:break
        save(dest,{**{k:v for k,v in data.items()if k!='works'},'selectionStage':'Candidate selection: requires visual and editorial review','anchorsApplied':True,'anchorResults':anchor_results,'works':picked})
        print(slug,len(picked),flush=True)

def images(slugs):
    CACHE.mkdir(parents=True,exist_ok=True)
    paths=[RUN/'selections'/(s+'.json')for s in slugs] if slugs else sorted((RUN/'selections').glob('*.json'))
    for path in paths:
        data=load(path);slug=data['candidate']['slug'];ws=data['works']
        def get(w):
            dest=CACHE/(w['id']+'.jpg')
            if not dest.exists():
                r=requests.get(image_url(w),timeout=60);r.raise_for_status()
                Image.open(io.BytesIO(r.content)).verify()
                dest.write_bytes(r.content)
            Image.open(dest).verify()
            return {'id':w['id'],'url':image_url(w),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:receipts=list(pool.map(get,ws))
        out=TEMP/'sheets';out.mkdir(exist_ok=True)
        sheet=Image.new('RGB',(1440,1900),'#f6f2e9');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype(FONT,16)
        for n,w in enumerate(ws):
            x=(n%4)*360;y=(n//4)*380
            im=Image.open(CACHE/(w['id']+'.jpg')).convert('RGB');im.thumbnail((342,280))
            sheet.paste(im,(x+(360-im.width)//2,y+5+(280-im.height)//2))
            label=f'{n+1}. {w["title"]} / '+('; '.join(a['name']for a in w['artists'])or w['unlinked_creator_label']or'Anonymous')
            draw.multiline_text((x+8,y+292),'\n'.join(textwrap.wrap(label,43)[:4]),font=font,fill='#171717',spacing=3)
        sheet.save(out/(slug+'.jpg'),quality=92)
        save(RUN/'image-receipts'/(slug+'.json'),receipts)
        print(slug,'20 images cached and sheet prepared',flush=True)

def sources(slugs):
    paths=[RUN/'selections'/(s+'.json')for s in slugs] if slugs else sorted((RUN/'selections').glob('*.json'))
    urls=set()
    for path in paths:
        d=load(path)
        if d['institution'].get('website_url'):urls.add(d['institution']['website_url'])
        urls.update(h['url']for w in d['works']for h in w['holdings']if h['url'])
        authored=RUN/'copy'/(path.stem+'.json')
        if authored.exists():
            prose=load(authored)
            urls.update(prose[k]for k in ['website','officialGuide']if prose.get(k))
            urls.update(b['url']for b in prose.get('extraBooks',[]))
        edition=TEMP/'editions'/path.stem/'en.json'
        if edition.exists():
            guide=load(edition)
            urls.update(guide[k]for k in ['website','officialGuide']if guide.get(k))
            urls.update(b['url']for b in guide['books'])
            urls.update(w['source']for w in guide['works']if w.get('source'))
    override_path=RUN/'field-overrides.json'
    if override_path.exists():
        for override in load(override_path).values():
            urls.update(re.findall(r'https?://[^\s\"<>]+',json.dumps(override.get('evidence',[]))))
    def fetch(url):
        key=hashlib.sha256(url.encode()).hexdigest();dest=RUN/'sources'/(key+'.json')
        if dest.exists():return load(dest)
        result={'url':url,'checkedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        try:
            r=requests.get(url,headers={'User-Agent':'Artline editorial source verification (https://artlines.org)'},timeout=35)
            result.update(status=r.status_code,finalUrl=r.url,contentType=r.headers.get('content-type'),sha256=hashlib.sha256(r.content).hexdigest())
            dest.parent.mkdir(parents=True,exist_ok=True);dest.with_suffix('.body.gz').write_bytes(gzip.compress(r.content,mtime=0))
            if r.ok and 'html'in r.headers.get('content-type',''):
                soup=BeautifulSoup(r.content,'html.parser')
                result['title']=soup.title.get_text(' ',strip=True)if soup.title else ''
                for e in soup(['script','style','nav','footer','header']):e.decompose()
                result['text']=re.sub(r'\n\s*\n+','\n',soup.get_text('\n',strip=True))[:55000]
        except Exception as e:result['error']=type(e).__name__+': '+str(e)[:300]
        save(dest,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i,result in enumerate(pool.map(fetch,sorted(urls)),1):
            if i%20==0:print(i,'/',len(urls),'sources checked',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='images':images(sys.argv[2:])
    elif sys.argv[1]=='sources':sources(sys.argv[2:])
