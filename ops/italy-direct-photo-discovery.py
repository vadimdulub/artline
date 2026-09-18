#!/usr/bin/env python3
"""Bounded file-metadata leads for Italian holdings without authority crosswalks.

No image downloads and no image/metadata database writes. A lead is not an
identity match, licence approval, or attachment authorization.
"""
import argparse
import collections
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crosswalks', ROOT / 'ops/italy-image-crosswalks.py')
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
c, w = x.c, x.w
OUT = c.RUN / 'direct-photo-discovery'
MUSEUM_TERMS = {
    'pinacoteca-ambrosiana':'Ambrosiana',
    'accademia-carrara':'Carrara',
    'castello-sforzesco-art-collections':'Sforzesco',
    'galleria-arte-moderna-milano':'Milano',
    'musei-civici-arte-storia-brescia':'Brescia',
    'musei-civici-monza':'Monza',
    'musei-civici-pavia':'Pavia',
    'accademia-tadini':'Tadini',
    'museo-scienza-tecnologia-milano':'Milano',
    'museo-risorgimento-milano':'Risorgimento',
    'palazzo-morando-milano':'Morando',
    'accademia-brera-collections':'Brera',
    'museo-poldi-pezzoli':'Poldi',
    'museo-civico-ala-ponzone':'Cremona',
    'montichiari-musei':'Lechi',
    'villa-necchi-campiglio':'Necchi',
}


def main(limit,per_museum_limit=15,exclude_prior=False,targeted=False):
    OUT.mkdir(parents=True,exist_ok=True)
    selection = OUT/'selected-existing-gaps.json'
    if selection.exists():
        rows=c.load(selection)['records']
    else:
        used={r['artwork_id'] for f in c.RUN.glob('*/candidates.json') for r in c.load(f)['candidates']}
        if exclude_prior:
            for f in c.RUN.glob('direct-photo-discovery*/selected-existing-gaps.json'):
                used.update(r['artwork_id'] for r in c.load(f)['records'])
        per_museum=collections.Counter();per_artist=collections.Counter();rows=[]
        for record in c.load(c.RUN/'eligible-image-gaps.json'):
            museum=record['institution_slug']
            if museum not in MUSEUM_TERMS or record['work_type']!='painting' or record['artwork_id'] in used or c.institution_policy_reason(record):
                continue
            if len(record['creators'])!=1:
                continue
            artist=record['creators'][0]
            if not artist.get('death') or artist['death']>=1956 or artist['role']!='primary':
                continue
            if per_museum[museum]>=per_museum_limit or per_artist[(museum,artist['id'])]>=2:
                continue
            if not any('lombardiabeniculturali.it/opere-arte/' in (e.get('url') or '') for e in record['identifiers']):
                continue
            rows.append(record);per_museum[museum]+=1;per_artist[(museum,artist['id'])]+=1
            if len(rows)>=limit:break
        c.save(selection,{'selected_at':c.core.now(),'records':rows,'limit':limit,
            'selection':f'Existing eligible selected Italian museum painting gaps; max {per_museum_limit} per museum and two per creator; metadata leads only'})
    groups=collections.defaultdict(list)
    for row in rows:
        query='"'+MUSEUM_TERMS[row['institution_slug']]+'" "'+row['creators'][0]['name'].split()[-1]+'" filetype:bitmap'
        if targeted:
            import re
            stop={'ritratto','madonna','bambino','della','delle','dello','dalla','dallo','dell','degli','santa','santo','santi','sacre','sacra','con','del','dei','alla','nel','nella','tra','una','uno'}
            words=[t.lower() for t in re.findall(r'[A-Za-zÀ-ÿ]+',row['title']) if len(t)>3 and t.lower() not in stop]
            query+=' '+' '.join('"'+t+'"' for t in list(dict.fromkeys(words))[:2])
        groups[query].append(row)
    fetcher=w.core.Fetcher(OUT/'captures')
    for number,(query,targets) in enumerate(groups.items(),1):
        key=c.core.sha(query.encode())[:20];path=OUT/'queries'/(key+'.json')
        if path.exists():continue
        result=w.api(fetcher,'commons.wikimedia.org',{'action':'query','generator':'search',
            'gsrsearch':query,'gsrnamespace':6,'gsrlimit':8,'prop':'imageinfo|revisions',
            'iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
        pages=[p for p in result.get('query',{}).get('pages',{}).values() if p.get('ns')==6 and p.get('imageinfo')
               and p['imageinfo'][0].get('mime') in ('image/jpeg','image/png','image/tiff')]
        c.save(path,{'query':query,'targets':[r['artwork_id'] for r in targets],
            'search_capped':bool(result.get('continue')),'pages':pages,
            'status':'Unreviewed metadata leads; no physical-object match or image licence approval inferred'})
        print(number,'/',len(groups),query,'file leads',len(pages),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=60)
    p.add_argument('--per-museum',type=int,default=15);p.add_argument('--cohort',default='direct-photo-discovery')
    p.add_argument('--exclude-prior',action='store_true');p.add_argument('--targeted',action='store_true')
    a=p.parse_args();OUT=c.RUN/a.cohort
    main(a.limit,a.per_museum,a.exclude_prior,a.targeted)
