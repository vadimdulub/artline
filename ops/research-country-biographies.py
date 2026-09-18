#!/usr/bin/env python3
"""Capture Wikipedia introductions for country cross-checks, not publication."""
import argparse,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-country-rounds.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
def main(code):
    roster=json.loads((x.BASE/code/'roster.json').read_text());work=[]
    for a in roster['artists']:
        e=json.loads((x.r.RUN/'entities'/(a['qid']+'.json')).read_text())['entity'];title=e.get('sitelinks',{}).get('enwiki',{}).get('title')
        if title:work.append({'qid':a['qid'],'title':title,'name':a['name']})
    for start in range(0,len(work),20):
        group=work[start:start+20];path=x.BASE/code/'biography-captures'/f'{start//20+1:03d}.json'
        if path.exists():continue
        data,receipt=x.r.fetch('https://en.wikipedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'|'.join(a['title'] for a in group),'prop':'extracts|info','exintro':1,'explaintext':1,'exlimit':20,'inprop':'url','redirects':1,'maxlag':5}))
        x.save(path,{'requested':group,'data':data,'receipt':receipt});print(code,'biography batch',start//20+1,len(group),flush=True)
    print(code,'biography source introductions captured',len(work),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('country',choices=x.COUNTRIES);a=p.parse_args();main(a.country)
