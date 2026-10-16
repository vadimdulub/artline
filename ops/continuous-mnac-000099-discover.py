import importlib.util,json,re,fcntl,gzip
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-mnac-batch-000099.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
urls=[u for u in h.load(b.E/'medieval-object-urls.json') if u.startswith('https://www.museunacional.cat/en/colleccio/')];assert len(urls)==18
out=[]
for url in urls:
 raw,rc=b.capture(url)
 if rc['status']!=200:break
 sp=BeautifulSoup(raw,'html.parser')
 x=dict(url=url,receipt=rc,title=sp.title.get_text(' ',strip=True).split(' | ')[0],creators=[e.get_text(' ',strip=True) for e in sp.select('.field-name-field-piece-authors-author .field-item')],features=[e.get_text(' ',strip=True) for e in sp.select('.ds-feature')],tags=[e.get_text(' ',strip=True) for e in sp.select('.ds-detail-tags')])
 out.append(x);print(json.dumps({k:v for k,v in x.items() if k!='receipt'},ensure_ascii=False),flush=True)
b.save('parsed-native-objects.json',out)
