#!/usr/bin/env python3
"""Review cultural affiliations separately from 457 known birth-country links."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=m.x.BASE/'country-gap-followup/birth-only-context'
def research():
    path=RUN/'research.json'
    if path.exists():return
    artists=json.loads((RUN.parent/'birth-only-current-identities.json').read_text())['artists'];qids={a['slug']:next(e['id'] for e in a['authorities'] if e['scheme']=='wikidata') for a in artists}
    entities,receipts=m.x.r.entities(list(qids.values()));requests=[]
    for a in artists:
        q=qids[a['slug']];e=entities[q];title=e.get('sitelinks',{}).get('enwiki',{}).get('title')
        if title:requests.append(dict(qid=q,title=title))
    bios={}
    for start in range(0,len(requests),20):
        part=requests[start:start+20];dest=RUN/'biographies'/f'{start:04d}.json'
        if dest.exists():captured=json.loads(dest.read_text())
        else:
            d,rec=m.x.r.fetch('https://en.wikipedia.org/w/api.php?'+urlencode(dict(action='query',format='json',titles='|'.join(x['title'] for x in part),prop='extracts|info',exintro=1,explaintext=1,inprop='url',redirects=1,maxlag=5)))
            captured=dict(data=d,receipt=rec,requested=part);CORE.save_new(dest,captured)
        query=captured['data'].get('query',{});pages={p['title']:p for p in query.get('pages',{}).values()};redirects={x['from']:x['to'] for x in [*query.get('normalized',[]),*query.get('redirects',[])]}
        for item in part:
            title=item['title'];seen=set()
            while title in redirects and title not in seen:seen.add(title);title=redirects[title]
            p=pages.get(title)
            if p and p.get('extract'):bios[item['qid']]=dict(url=p.get('fullurl'),intro=p['extract'].split('\n\n')[0][:1800],receipt=captured['receipt'])
        print('Birth-only biography batch',start//20+1,len(part),flush=True)
    records=[]
    for a in artists:
        q=qids[a['slug']];e=entities[q];bio=bios.get(q);desc=e.get('descriptions',{}).get('en',{}).get('value','');left=g.labels(desc);right=g.biography_labels(bio['intro']) if bio else {};codes=sorted(set(left.values())&set(right.values()))
        records.append(dict(artist=a,qid=q,entity=e,entity_receipt=receipts[q],description=desc,biography=bio,description_affiliations=left,biography_affiliations=right,proposed_codes=codes,source_birth=m.m.r.year(e,'P569'),source_death=m.m.r.year(e,'P570')))
    CORE.save_new(path,dict(at=CORE.now(),records=records,policy='Known exact Wikidata person identities only. Keep all documented birth links separately. Explicit cultural role wording required; no automatic Flemish/Netherlandish/imperial-to-modern-country mapping. Life date disagreements require individual identity review before application.'))
    print('Birth-only researched',len(records),'proposals',sum(bool(r['proposed_codes']) for r in records),flush=True)
if __name__=='__main__':research()
