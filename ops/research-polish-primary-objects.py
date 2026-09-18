#!/usr/bin/env python3
"""Selected museum object checks with migration-safe inventory crosswalks."""
import argparse,collections,importlib.util,json,re,time,os
from pathlib import Path
from urllib.parse import urlencode,urlparse
import requests
s=importlib.util.spec_from_file_location('country',Path(__file__).with_name('research-country-rounds.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
ROOT=x.SESSION_BASE/'primary-museums'
VERSION=os.environ.get('ARTLINE_POLISH_PRIMARY_VERSION','');assert VERSION in ('','-v2')
HOSTS={'warsaw':('https://cyfrowe-api.mnw.art.pl','https://cyfrowe.mnw.art.pl/en/catalog/'),'krakow':('https://api-zbiory.mnk.pl','https://zbiory.mnk.pl/en/search-result/advance/catalog/')}

def get(url,museum,key):
    path=ROOT/museum/(key+'.json');receiptpath=ROOT/museum/(key+'.receipt.json')
    if path.exists():
        raw=path.read_bytes();receipt=json.loads(receiptpath.read_text());assert x.r.core.sha(raw)==receipt['sha256'];return json.loads(raw),receipt
    time.sleep(1);r=requests.get(url,timeout=(15,45),headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected object research)'})
    r.raise_for_status();assert len(r.content)<2_000_000;data=r.json();receipt={'url':r.url,'retrieved_at':x.r.core.now(),'sha256':x.r.core.sha(r.content),'status':r.status_code,'bytes':len(r.content)};x.save(path,r.content);x.save(receiptpath,receipt);return data,receipt

def capture(code,number):
    delivery=x.BASE/code/f'round-{number:02d}'/'delivery';dest=delivery/('polish-primary'+VERSION+'-review.json')
    if dest.exists():return
    out=[]
    for path in sorted((delivery/'ready').glob('*.json')):
        r=json.loads(path.read_text())['record'];urls=x.r.values(r['entity'],'P973');museum='warsaw' if x.r.values(r['entity'],'P9061') else 'krakow' if any(isinstance(u,str) and urlparse(u).hostname=='zbiory.mnk.pl' for u in urls) else None
        if not museum or not r['accession']:continue
        q=r['qid'];target=delivery/('polish-primary'+VERSION)/(q+'.json')
        if target.exists():out.append(json.loads(target.read_text()));continue
        e={'qid':q,'at':x.r.core.now(),'museum':museum,'review':'primary_review_required','ready_sha256':x.r.core.sha(path.read_bytes())}
        try:
            root,human=HOSTS[museum]
            # Public SPA code specifies filter[inventoryNumber]. The unscoped
            # phrase parameter is ignored by the API and must never be crawled.
            data,search_receipt=get(root+'/api/search/Object/page/1?'+urlencode({'filter[inventoryNumber]':r['accession'],'maxPerPage':10}),museum,q+'-inventory-crosswalk')
            total=data['data']['paginatorDetails']['totalItemsCount'];assert total<=10,'Inventory search is not sufficiently scoped'
            matches=[o for o in data['data']['items'] if x.r.norm(o.get('inventoryNumber',''))==x.r.norm(r['accession'])];assert len(matches)==1,'Exact unique museum inventory crosswalk required'
            oid=matches[0]['id'];data,receipt=get(root+'/api/object/'+str(oid),museum,q+'-primary-object');o=data['data'];assert o['id']==oid
            accession_match=x.r.norm(o.get('noEvidence',''))==x.r.norm(r['accession'])
            authors=o.get('authors',[]);names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])}
            def clean(n):
                n=re.sub(r'\s*\([^)]*\)\s*$','',n or '')
                return ' '.join(reversed([p.strip() for p in n.split(',')])) if ',' in n else n
            creator_match=len(authors)==1 and x.r.norm(clean(authors[0].get('name'))) in names
            qualifiers=[a for a in authors if a.get('comment') or a.get('additionalRoles') or a.get('role') not in ('autor','malarz','twórca','rysownik','wykonawca')]
            exact=creator_match and accession_match and not qualifiers
            e.update(object={'title':o.get('title'),'creator':'; '.join(a['name'] for a in authors),'makers':authors,'accession':o.get('noEvidence'),'date':'; '.join(d['name']+((' ('+d['comment']+')') if d.get('comment') else '') for d in o.get('createDates',[])),'fields':o,'rights':o.get('copyrights',[]),'credit':(o.get('owner') or {}).get('name')},receipt=receipt,search_receipt=search_receipt,primary_object_id=str(oid),human_url=human+str(oid),creator_match=creator_match,accession_match=accession_match,qualified_maker_roles=qualifiers,legacy_source_ids=x.r.values(r['entity'],'P9061') if museum=='warsaw' else urls,review='primary_object_and_creator_corroborated' if exact else 'primary_review_required')
        except Exception as error:e['reason']=str(error)[:350]
        x.save(target,e);out.append(e);print(code,number,museum,q,e['review'],e.get('primary_object_id'),flush=True)
    x.save(dest,{'at':x.r.core.now(),'records':out,'counts':dict(collections.Counter(e['review'] for e in out))})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--country',required=True,choices=x.COUNTRIES);p.add_argument('--round',type=int,required=True);a=p.parse_args();capture(a.country,a.round)
