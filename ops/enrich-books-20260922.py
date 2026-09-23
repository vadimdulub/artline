#!/usr/bin/env python3
"""Capture Wikipedia introductions for existing books and credited creators."""
import argparse,concurrent.futures,importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

spec=importlib.util.spec_from_file_location('review',Path(__file__).with_name('review-book-languages-20260922.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
RUN=r.ROOT/'docs/research/book-context-20260922'
LANG=r.RUN
r.RUN=RUN

def baseline():
    path=r.BACKUP.parent/'book-context-20260922'/'baseline-local.json'
    if path.exists():return r.read(path)
    with psycopg.connect(r.DSN,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
        creators=db.execute('SELECT to_jsonb(c) creator FROM book_creators c ORDER BY id').fetchall()
        links=db.execute('SELECT to_jsonb(l) link FROM book_creator_links l ORDER BY book_id,position').fetchall()
    value={'at':r.now(),'creators':creators,'links':links};r.save(path,value)
    r.save(RUN/'baseline-local-reference.json',{'path':str(path),'sha256':r.sha(path.read_bytes()),'creators':len(creators),'links':len(links)})
    return value

def capture_creators():
    base=baseline();qids=sorted(x['creator']['id'] for x in base['creators'] if x['creator']['id'].startswith('Q'))
    def batch(qs):
        if all((RUN/'creator-entities'/(q+'.json')).exists() for q in qs):return len(qs)
        data,receipt=r.source_request('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(qs),'props':'info|labels|descriptions|claims|sitelinks','languages':'en|mul','sitefilter':'enwiki'})
        for q in qs:r.save(RUN/'creator-entities'/(q+'.json'),{'entity':data['entities'].get(q,{'id':q,'missing':True}),'receipt':receipt})
        return len(qs)
    total=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n in pool.map(batch,[qids[i:i+50] for i in range(0,len(qids),50)]):
            total+=n
            if total%500==0 or total==len(qids):print('Creator source records',total,'of',len(qids),flush=True)

def capture():
    capture_creators();entries=[]
    for kind,folder in [('book',LANG/'entities'),('creator',RUN/'creator-entities')]:
        for path in sorted(folder.glob('*.json')):
            e=r.read(path)['entity'];link=e.get('sitelinks',{}).get('enwiki')
            if link:entries.append({'qid':path.stem,'kind':kind,'title':link['title']})
    def batch(items):
        if all((RUN/(v['kind']+'-introductions')/(v['qid']+'.json')).exists() for v in items):return len(items)
        params={'action':'query','titles':'|'.join(v['title'] for v in items),'redirects':1,'prop':'extracts|pageprops|revisions','exintro':1,'explaintext':1,'exlimit':20,'ppprop':'wikibase_item','rvprop':'ids|timestamp'}
        data,receipt=r.source_request('en.wikipedia.org',params)
        assert not data.get('continue'),data.get('continue')
        remap={v['from']:v['to'] for v in data.get('query',{}).get('normalized',[])+data.get('query',{}).get('redirects',[])}
        pages={p['title']:p for p in data.get('query',{}).get('pages',[])}
        for item in items:
            title=item['title'];seen=set()
            while title in remap and title not in seen:seen.add(title);title=remap[title]
            path=RUN/(item['kind']+'-introductions')/(item['qid']+'.json')
            if not path.exists():r.save(path,{'requested':item,'page':pages.get(title,{'title':title,'missing':True}),'receipt':receipt})
        return len(items)
    total=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n in pool.map(batch,[entries[i:i+20] for i in range(0,len(entries),20)]):
            total+=n
            if total%500==0 or total==len(entries):print('Wikipedia introductions',total,'of',len(entries),flush=True)
    r.save(RUN/'capture-finished.json',{'entries':entries})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['capture','baseline']);args=parser.parse_args();globals()[args.phase]()
