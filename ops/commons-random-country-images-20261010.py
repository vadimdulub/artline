#!/usr/bin/env python3
"""Bounded Commons file metadata for already selected official objects; candidates require visual comparison."""
import importlib.util,collections,json,re,sys
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-random-country-collections-20261010.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
code=sys.argv[1];r.phase(code);rows=m.pinned(code)[0]['records'];src=r.b.Source();groups=collections.defaultdict(list)
with m.connect() as db:states=m.snapshot(db,[w['artwork_id'] for w in rows])
for w in rows:
 if w['source_type'] not in ['painting','drawing'] or not w.get('reference_image_url') or not w.get('year_end') or w['year_end']>1955 or w.get('creator_link_hold') or states[w['artwork_id']]['artwork']['primary_media_id']:continue
 if len((w.get('creator_label')or'').split())<2:continue
 groups[w['creator_label']].append(w)
selected=[w for name,works in sorted(groups.items(),key=lambda t:-len(t[1]))[:12] for w in works[:4]][:36]
out=[];held=[]
for n,w in enumerate(selected,1):
 name=w['creator_label'];query=name+' '+str(w['year_start']);filekey=w['key']
 try:
  d,rc=src.get('https://commons.wikimedia.org/w/api.php',dict(action='query',format='json',generator='search',gsrsearch=query,gsrnamespace=6,gsrlimit=8,prop='imageinfo',iiprop='url|extmetadata|size',iiurlwidth=1200))
  choices=[]
  for page in d.get('query',{}).get('pages',{}).values():
   infos=page.get('imageinfo',[])
   if not infos:continue
   im=infos[0];meta=im.get('extmetadata',{});plain=lambda k:BeautifulSoup(str(meta.get(k,{}).get('value','')),'html.parser').get_text(' ',strip=True)
   if plain('LicenseShortName') not in ['Public domain','CC0']:continue
   if im.get('size',0)>15_000_000:continue
   creator=plain('Artist');date=plain('DateTimeOriginal');text=plain('ObjectName')+' '+plain('ImageDescription')+' '+page['title'];categories=plain('Categories')
   surname=m.norm(name).split()[-1]
   if surname not in m.norm(creator+' '+page['title']):continue
   years=list(map(int,re.findall(r'(?<!\d)[12]\d{3}(?!\d)',date)))
   if not years or not w['year_start']<=years[0]<=w['year_end']:continue
   if re.search(r'gravure|engraving|photograph of|sculpture',plain('ObjectName'),re.I):continue
   words=set(m.norm(w['title']).split())-{'the','a','an','with','of','at','in','and','from','to','self','portrait'};found=set(m.norm(text).split());score=len(words&found)/max(1,len(words))
   choices.append(dict(page=page,metadata_text=dict(creator=creator,date=date,title=plain('ObjectName'),description=plain('ImageDescription'),categories=categories,credit=plain('Credit'),rights=plain('LicenseShortName')),score=score,evidence=rc))
  choices.sort(key=lambda x:-x['score']);out.append(dict(record=w,query=query,choices=choices[:3]));print(code,n,w['creator_label'],w['title'],'choices',len(choices),flush=True)
 except Exception as e:
  held.append(dict(key=filekey,error=str(e)))
  if src.blocked:break
m.save(m.RUN/code/'commons-image-candidates.json.gz',out);m.save(m.RUN/code/'commons-image-held.json.gz',held)
