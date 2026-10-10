#!/usr/bin/env python3
"""Bounded, read-only follow-up for the 312 remaining Prado image gaps.

Reuse hashed source captures; never infer a match from a search score. Keep
artist collisions, truncated searches and missing source facts explicit.
"""
import collections, concurrent.futures, gzip, hashlib, importlib.util, json, re, sys
from pathlib import Path
from urllib.parse import quote, urljoin

ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / 'docs/research/prado-wikiart-20261006'
RUN = PREV / 'deep-research-20261006'
spec = importlib.util.spec_from_file_location('source', PREV / 'scripts/wikiart-research.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.RUN = RUN
network_fetch = m.fetch

def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    for folder in (RUN, PREV / 'delivery', PREV / 'round-2', PREV):
        p = folder / 'captures' / key
        if p.with_suffix('.json').exists():
            receipt = json.loads(p.with_suffix('.json').read_text())
            raw = gzip.decompress(p.with_suffix('.html.gz').read_bytes())
            assert hashlib.sha256(raw).hexdigest() == receipt['sha256']
            return raw, receipt
    return network_fetch(url)

m.fetch = fetch
snapshot = json.loads(gzip.decompress((RUN / 'production-snapshot.json.gz').read_bytes()))
baseline = json.loads((PREV / 'round-2/image-matches.json').read_text())['works']
cross = json.loads((PREV / 'round-2/museum-crosswalk.json').read_text())['objects']
aliases = json.loads((PREV / 'round-2/object-aliases.json').read_text())
artists = {a['id']: a for a in snapshot['artists']}
targets = [w for w in baseline if not snapshot['records'][w['artwork_id']]['artwork']['primary_media_id']]
ACCESS_HOLD = 'd09b5c58-de13-5a76-81b0-260af0599afd'

def short_title(title):
    stop = {'the','and','with','from','this','that','still','life','portrait','of','a','an','in','on',
            'de','del','la','las','el','los','un','una','y','con','en','retrato','bodegon','nature','morte'}
    words = [w for w in m.norm(title).split() if w not in stop]
    return ' '.join(words[:6]) if len(words) >= 2 else ''

def work(w):
    aid = w['artwork_id']; path = RUN / 'searches' / (aid + '.json')
    if path.exists(): return json.loads(path.read_text())
    result = {'artwork_id': aid, 'title': w['title'], 'queries': [], 'candidates': []}
    if aid == ACCESS_HOLD:
        result['outcome'] = 'prior_login_boundary_preserved'; m.save(path,result); return result
    names = {m.norm(a['name']) for a in w['artists']}
    profiles = set()
    for a in w['artists']:
        # Known collisions remain leads; they are never reconciled automatically.
        names.update(m.norm(n) for n in artists.get(a['id'],{}).get('aliases',[]))
        idx = json.loads((PREV / 'artists' / (a['id']+'.json')).read_text())
        profiles.update('/'.join(x['url'].split('/')[:5]) for x in idx['works'])
    titles = {w['title'], w.get('alternate_title'), cross.get(aid,{}).get('Título')} - {None,''}
    for lang in ('en','es','fr','de','it','ca'):
        if aliases.get(aid,{}).get('titles',{}).get(lang): titles.add(aliases[aid]['titles'][lang])
    queries = [('en', w['title'])]
    es = cross.get(aid,{}).get('Título') or w.get('alternate_title')
    if es and m.norm(es) != m.norm(w['title']): queries.append(('es',es))
    short = short_title(es or w['title'])
    if short and all(m.norm(t)!=short for _,t in queries): queries.append(('en',short))
    candidates = {}
    for lang, query in queries:
        url = 'https://www.wikiart.org/'+lang+'/Search/'+quote(query,safe='')+'/?json=2&layout=new'
        raw,receipt = fetch(url)
        evidence = {'query':query,'language':lang,'receipt':receipt}
        if '/login' in receipt['final_url'].lower() or receipt['status'] in (401,403,429):
            evidence['outcome']='access_boundary'; result['queries'].append(evidence);break
        try: data=json.loads(raw)
        except ValueError:
            evidence['outcome']='unexpected_response';result['queries'].append(evidence);continue
        rows=data.get('Paintings') or []
        evidence.update(total=data.get('AllPaintingsCount'), returned=len(rows), truncated=(data.get('AllPaintingsCount') or 0)>len(rows))
        evidence['artist_candidates']=[]
        for c in rows:
            u=urljoin('https://www.wikiart.org',c['paintingUrl']);profile='/'.join(u.split('/')[:5])
            if profile not in profiles and m.norm(c.get('artistName')) not in names:continue
            candidate={**c,'url':u,'title_score':round(m.score(c['title'],{m.norm(t) for t in titles}),4),
                       'artist_match_basis':'previously_checked_profile' if profile in profiles else 'catalogue_name_or_alias_requires_review'}
            candidates[u]=candidate;evidence['artist_candidates'].append(u)
        result['queries'].append(evidence)
    result['candidates']=list(candidates.values());result['outcome']='leads_for_manual_review' if candidates else 'no_artist_matched_result_in_bounded_queries'
    m.save(path,result);return result

def search():
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(work,targets):
            results.append(row)
            if len(results)%20==0:print('Objects checked',len(results),'/',len(targets),'with leads',sum(bool(x['candidates'])for x in results),flush=True)
    m.save(RUN/'search-summary.json',{'objects':len(results),'queries':sum(len(x['queries'])for x in results),
        'truncated_queries':sum(bool(q.get('truncated'))for x in results for q in x['queries']),
        'outcomes':dict(collections.Counter(x['outcome']for x in results)),
        'source_pages':sorted({c['url']for x in results for c in x['candidates']})})

def pages():
    # An explicit, reviewed list of leads; this does not download image files.
    rows=json.loads((RUN/'page-queue.json').read_text())
    for url in rows:
        path=RUN/'pages'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if not path.exists():m.save(path,{'url':url,**m.page(url)})
        p=json.loads(path.read_text());print(url,p.get('attributes'),flush=True)

if __name__=='__main__': {'search':search,'pages':pages}[sys.argv[1]]()
