"""Inspect the observed museum collection and digital-library entry points."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-source-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,q=c.m,c.RUN,c.q

def main():
    d=m.load(RUN/'native-discovery-001.json.gz');rows=[]
    for key,title in [('permanent-collection','G.I. Katsigras Permanent Collection'),('digital-library','Katsigras Collection Digital Library')]:
        url=next(x['url']for x in d['links']if x['title']==title)
        soup,rc=q.q.capture('native-'+key+'-001',url)
        row=dict(kind=key,receipt=rc,text=q.clean(soup.get_text(' ',strip=True)),links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href']))for a in soup.select('a[href]')])
        m.save(RUN/(key+'-discovery-001.json.gz'),row);rows.append(row)
        print(json.dumps(dict(kind=key,final_url=rc['final_url'],text=row['text'][:6000],links=row['links'][:30]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
