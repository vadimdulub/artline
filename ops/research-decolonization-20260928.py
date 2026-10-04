#!/usr/bin/env python3
"""Bounded WikiArt metadata discovery; never downloads images or writes the DB."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('add-islamic-world-images-20260925.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
c.RUN=c.ROOT/'docs/research/decolonization-deep-20260928'
ARTISTS=['gerard-sekoto','zainul-abedin','joaquin-torres-garcia','jose-clemente-orozco',
    'david-alfaro-siqueiros','diego-rivera','hector-hyppolite','mahmoud-saiid','wifredo-lam',
    'baya-mahieddine','oswaldo-guayasamin']

def index():
    for slug in ARTISTS:
        url='https://www.wikiart.org/en/'+slug+'/all-works/text-list'
        try:
            raw,receipt=c.fetch(url,c.RUN/'captures'/('wiki-index-'+slug+'.html'))
            soup=BeautifulSoup(raw,'html.parser')
            links=[]
            for a in soup.select('a[href]'):
                if a['href'].startswith('/en/'+slug+'/') and '/all-works' not in a['href']:
                    links.append(dict(title=a.get_text(' ',strip=True),context=a.parent.get_text(' ',strip=True),url=urljoin(url,a['href'])))
            c.save(c.RUN/'wiki-index'/(slug+'.json'),dict(url=url,receipt=receipt,works=links))
            print(slug,len(links),flush=True)
        except Exception as e:
            c.save(c.RUN/'wiki-index'/(slug+'-failed.json'),dict(url=url,error=str(e)))
            print(slug,str(e)[:180],flush=True)
        time.sleep(1.1)

def objects():
    selection=c.load('wiki-object-selection.json')
    for entry in selection:
        url=entry['url'];key=entry['key']
        raw,receipt=c.fetch(url,c.RUN/'captures'/('wiki-object-'+key+'.html'))
        soup=BeautifulSoup(raw,'html.parser')
        tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
        assert tag,'Missing painting object: '+url
        record=json.loads(tag['ng-init'].split('=',1)[1].strip())
        image=soup.select_one('img[itemprop="image"]')
        label=soup.select_one('.copyright-wrapper .copyright')
        pd=bool(label and label.select_one('.copyright-icon-public-domain'))
        article=soup.select_one('.wiki-layout-artwork-info') or soup
        result=dict(selection=entry,record=record,receipt=receipt,image_url=image['src'] if image else None,
            rights_status='public_domain' if pd else ('restricted' if label else 'unknown'),
            rights_label=label.get_text(' ',strip=True) if label else None,
            text=article.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in article.select('a[href]')])
        c.save(c.RUN/'wiki-objects'/(key+'.json'),result)
        print(key,record['title'],record.get('year'),result['rights_status'],flush=True)
        time.sleep(1.1)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['index','objects']);globals()[p.parse_args().phase]()
