"""Inspect observed advanced-search controls and native art collection navigation."""
import gzip, importlib.util, json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-nhm-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def main():
    assert not (RUN/'art-navigation-001.json.gz').exists()
    found=m.load(RUN/'source-selection-discovery-001.json')
    page=BeautifulSoup(gzip.decompress((m.ROOT/found['first_date_page']['receipt']['body_path']).read_bytes()).decode(),'html.parser')
    advanced=urljoin(src.BASE,page.find('a',string=lambda x:x and 'More search options' in x)['href'])
    targets=[('advanced-001',advanced)]
    for label in ['Ζωγραφικά Έργα','Γλυπτά','Λαϊκές εικόνες & γελοιογραφίες']:
        link=next(x for x in found['native_links'] if x['title']==label)
        targets.append(('native-art-'+str(len(targets)).zfill(3),link['url']))
    targets.append(('native-browse-001','https://www.nhmuseum.gr/tmimata/mesa-stis-sylloges-tou-mouseiou'))
    rows=[]
    for key,url in targets:
        doc,rc=src.capture(key,url)
        rows.append(dict(key=key,receipt=rc,text=src.clean(doc.get_text(' ',strip=True)),links=[dict(title=src.clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href'])) for a in doc.select('a[href]') if a.get_text(' ',strip=True)],forms=[dict(action=f.get('action'),method=f.get('method'),inputs=[dict(name=x.get('name'),value=x.get('value')) for x in f.select('input[name]')],selects=[dict(name=x.get('name'),options=[dict(value=o.get('value'),label=src.clean(o.get_text(' ',strip=True))) for o in x.select('option')]) for x in f.select('select[name]')]) for f in doc.select('form')]))
        print(json.dumps(dict(key=key,status=rc['status'],text=rows[-1]['text'][:9000],forms=rows[-1]['forms']),ensure_ascii=False),flush=True)
    m.save(RUN/'art-navigation-001.json.gz',dict(at=m.now(),rows=rows,script_reference=c.ref(Path(__file__).resolve()),policy='Observed native art collection descriptions and advanced public search UI; no failed facet retry or guessed APIs. No images or database writes.'))

if __name__=='__main__':main()
