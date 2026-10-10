#!/usr/bin/env python3
"""Research Commons file metadata for exact existing Wikidata artwork IDs."""
import argparse
import collections
import importlib.util
import json
import time
from pathlib import Path
from urllib.parse import quote
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('research-artwork-location-secondary-20261004.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);r=s.r
ROOT=r.ROOT/'docs/research/museum-guides-20261005'


def select():
    selected={}
    for entry in r.load(ROOT/'snapshots/before/manifest.json')['museums']:
        data=r.load(ROOT/entry['path'])
        for w in data['artworks']:
            qids={e['external_id'] for e in w['identifiers']if e['scheme']=='wikidata'}
            if w['media'] or len(qids)!=1:continue
            selected[w['id']]={'artwork_id':w['id'],'qid':next(iter(qids)),'title':w['title'],'institution':data['institution']['name'],'source_holding_url':w['source_url']}
    wanted={v['qid']for v in selected.values()};entities={}
    for folder in ['wikidata-batches','major-museum-authorities-20261005d']:
        for path in (r.RUN/folder).glob('*.json'):
            data=r.load(path)
            if not isinstance(data,dict) or 'entities' not in data:continue
            for qid,obj in data['entities'].items():
                if qid in wanted:entities[qid]={'entity':obj,'receipt':data['receipt']}
    rows=[];held=[]
    for work in selected.values():
        match=entities.get(work['qid'])
        if not match:held.append({**work,'reason':'no_archived_wikidata_entity'});continue
        # No inference from labels or creators: preserve the exact existing QID.
        images=s.current_statements(match['entity'],'P18')
        names={s.value(x)for x in images if isinstance(s.value(x),str)and not x.get('qualifiers')}
        if len(names)!=1:held.append({**work,'reason':'no_unique_unqualified_depiction'});continue
        rows.append({**work,'filename':next(iter(names)),'wikidata_receipt':match['receipt'],'depiction_statements':images})
    r.save_gz(ROOT/'commons-selected.json.gz',{'at':r.now(),'selected':rows,'held':held})
    print('Commons selected',len(rows),'held',len(held),collections.Counter(v['reason']for v in held),flush=True)


def capture():
    rows=r.load(ROOT/'commons-selected.json.gz')['selected'];filenames=sorted({v['filename']for v in rows})
    for offset in range(0,len(filenames),40):
        dest=ROOT/'commons-metadata'/f'{offset//40:04d}.json.gz'
        if dest.exists():continue
        titles=['File:'+v for v in filenames[offset:offset+40]]
        raw,rc=r.capture('https://commons.wikimedia.org/w/api.php',{'action':'query','format':'json','prop':'imageinfo','iiprop':'url|size|mime|extmetadata','titles':'|'.join(titles)},tag='museum-guides-commons-file-metadata-20261005e',timeout=60)
        if rc['status'] in [403,429]:raise RuntimeError('Commons request denied or rate limited; stop')
        assert rc['status']==200
        data=json.loads(raw);assert 'query'in data,data.get('error')
        r.save_gz(dest,{'receipt':rc,'titles':titles,'data':data})
        print('Commons file metadata',min(offset+40,len(filenames)),'/',len(filenames),flush=True);time.sleep(2)
    r.save(ROOT/'commons-capture-complete.json',{'at':r.now(),'files':len(filenames)})


def build():
    assert (ROOT/'commons-capture-complete.json').exists()
    files={};redirects={}
    for path in sorted((ROOT/'commons-metadata').glob('*.json.gz')):
        batch=r.load(path);query=batch['data']['query']
        redirects.update({v['from']:v['to']for v in query.get('normalized',[])})
        redirects.update({v['from']:v['to']for v in query.get('redirects',[])})
        for obj in query['pages'].values():files[obj['title']]={'page':obj,'receipt':batch['receipt']}
    result={};held=[]
    for row in r.load(ROOT/'commons-selected.json.gz')['selected']:
        title='File:'+row['filename'];title=redirects.get(title,title);record=files.get(title)
        if not record or len(record['page'].get('imageinfo',[]))!=1:
            held.append({**row,'reason':'file_not_available_or_not_unique'});continue
        info=record['page']['imageinfo'][0]
        if not info.get('mime','').startswith('image/'):
            held.append({**row,'reason':'file_not_an_image'});continue
        meta=info.get('extmetadata',{})
        def plain(k):return BeautifulSoup(meta.get(k,{}).get('value',''),'html.parser').get_text(' ',strip=True)
        result[row['artwork_id']]={**row,'source_page_url':info['descriptionurl'],'image_url':info['url'],
            'credit':plain('Artist'),'attribution':plain('Credit'),'license':plain('LicenseShortName'),'license_url':plain('LicenseUrl'),
            'copyrighted':plain('Copyrighted'),'restrictions':plain('Restrictions'),'width':info.get('width'),'height':info.get('height'),
            'source_receipt':record['receipt'],'kind':'secondary_depiction_candidate','review_state':'review',
            'limitation':'Exact existing Artline Wikidata ID links to this Commons depiction. File identity, visual composition and reuse rights still require review before attachment or download. No change to accepted museum holding or current-display claims.',
            'no_image_downloaded':True}
    r.save_gz(ROOT/'commons-image-candidates.json.gz',{'at':r.now(),'by_artwork_id':result,'held':held})
    print('Commons image candidates',len(result),'held',len(held),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['select','capture','build']);globals()[parser.parse_args().command]()
