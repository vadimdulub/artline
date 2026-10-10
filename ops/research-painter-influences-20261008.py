#!/usr/bin/env python3
"""Resumable, read-only painter influence research. Never changes catalogue data.

Direction is always source (inspirer/teacher) -> target (library painter).
Source assertions, identity ambiguities and research gaps remain explicit.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urljoin, urlparse
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/painter-influences-20261008'
CACHE = Path.home() / 'Library/Application Support/Artline/research/painter-influences-20261008'
UA = 'ArtlineInfluenceResearch/1.0 (https://artlines.org/about; source-backed catalogue research)'
_bindings = None


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, default=str, sort_keys=True).encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(raw)
    temp.replace(path)


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def norm(value):
    return re.sub(r'[^a-z0-9]+', '', unidecode(value).lower())


def export(target):
    spec = importlib.util.spec_from_file_location('alignment', ROOT/'ops/align-catalogues-20261008.py')
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    with base.connect(target, readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists = db.execute("""SELECT id::text,slug,display_name,entity_type,birth_year,death_year,
            active_start_year,active_end_year,status,influence_review_state,biography_md
            FROM artists WHERE status<>'archived' ORDER BY id""").fetchall()
        ids = [a['id'] for a in artists]
        by_id = {a['id']:a for a in artists}
        for a in artists:
            a.update(identifiers=[], citations=[], aliases=[], countries=[], popular=False)
        for e in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])",(ids,)):
            by_id[e.pop('entity_id')]['identifiers'].append(e)
        for e in db.execute("SELECT entity_id::text,field_name,source_url,source_record_id,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])",(ids,)):
            by_id[e.pop('entity_id')]['citations'].append(e)
        for e in db.execute("SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])",(ids,)):
            by_id[e['artist_id']]['aliases'].append(e['alias'])
        for e in db.execute("SELECT artist_id::text,country_code FROM artist_countries WHERE artist_id=ANY(%s::uuid[])",(ids,)):
            by_id[e['artist_id']]['countries'].append(e['country_code'].strip())
        for e in db.execute("SELECT artist_id::text,is_popular FROM artist_discovery_selection WHERE artist_id=ANY(%s::uuid[])",(ids,)):
            by_id[e['artist_id']]['popular'] = e['is_popular']
        existing = db.execute('SELECT * FROM influence_claims').fetchall()
    path = RUN/(target+'-artists.json.gz')
    if path.exists():
        raise RuntimeError('Roster already pinned; preserve original snapshot')
    save(path,artists)
    save(RUN/(target+'-snapshot.json'),dict(at=now(),artists=len(artists),existing_influences=existing,
        read_only=True,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print(target,len(artists),'painters',flush=True)


def roster():
    # Keep local IDs canonical and retain all production bindings separately.
    local = load(RUN/'local-artists.json.gz')
    prod_path = RUN/'production-artists.json.gz'
    prod = load(prod_path) if prod_path.exists() else []
    by_slug = {a['slug']:a for a in local}
    for a in local:
        a['catalogue_bindings'] = [dict(catalogue='local',id=a['id'])]
    for p in prod:
        a = by_slug.get(p['slug'])
        if a and a['display_name'] == p['display_name']:
            a['catalogue_bindings'].append(dict(catalogue='production',id=p['id']))
            seen = {(v['scheme'],v['external_id']) for v in a['identifiers']}
            a['identifiers'].extend(v for v in p['identifiers'] if (v['scheme'],v['external_id']) not in seen)
        else:
            p['catalogue_bindings'] = [dict(catalogue='production',id=p['id'])]
            local.append(p)
    return local


def qids_for(a):
    global _bindings
    if _bindings is None:
        path=RUN/'research-identity-bindings.json'
        _bindings={r['artist_id']:r['qid'] for r in load(path) if r['decision']=='supported_research_identity'} if path.exists() else {}
    found={v['external_id'] for v in a['identifiers'] if v['scheme']=='wikidata' and re.fullmatch(r'Q[1-9][0-9]*',v['external_id'])}
    if a['id'] in _bindings: found.add(_bindings[a['id']])
    return found


def sparql(query, category, key):
    path = RUN/category/(key+'.json.gz')
    if path.exists():
        return load(path)
    for attempt in range(4):
        try:
            r=requests.get('https://query.wikidata.org/sparql',params={'query':query,'format':'json'},
                headers={'User-Agent':UA},timeout=80)
            if r.status_code==429:
                time.sleep(min(120,max(10,int(r.headers.get('Retry-After','60')))))
                continue
            r.raise_for_status()
            result=dict(at=now(),query=query,url=r.url,data=r.json())
            save(path,result)
            return result
        except Exception as e:
            if attempt==3:
                save(RUN/'errors'/(category+'-'+key+'.json'),dict(at=now(),query=query,error=str(e).split('?')[0]))
                return None
            time.sleep(3*(attempt+1))


def wikidata():
    qids=sorted({q for a in roster() for q in qids_for(a)})
    coverage=RUN/'wikidata-statement-coverage.json'
    prior=[r for r in load(coverage)['results'] if r['ok']] if coverage.exists() else []
    covered={q for r in prior for q in r['qids']}
    qids=[q for q in qids if q not in covered]
    batches=[qids[i:i+100] for i in range(0,len(qids),100)]
    def one(batch):
        values=' '.join('wd:'+q for q in batch)
        # P737=influenced by; P1066=student of. Teachers stay a separate relation.
        # Explicit statement/rank/reference records preserve unsupported claims.
        query='''SELECT ?artist ?property ?claim ?rank ?other ?ref ?refProperty ?refValue WHERE {
          VALUES ?artist { '''+values+''' }
          VALUES (?property ?statement ?value) { (wd:P737 p:P737 ps:P737) (wd:P1066 p:P1066 ps:P1066) }
          ?artist ?statement ?claim . ?claim ?value ?other; wikibase:rank ?rank .
          OPTIONAL { ?claim prov:wasDerivedFrom ?ref . ?ref ?refProperty ?refValue . }
        }'''
        key=hashlib.sha256(query.encode()).hexdigest()
        data=sparql(query,'wikidata-statements',key)
        return dict(batch=key,qids=batch,ok=data is not None,rows=len(data['data']['results']['bindings']) if data else 0)
    results=list(prior)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(one,b) for b in batches]):
            results.append(f.result())
            if len(results)%10==0:
                print('Wikidata statements',len(results),'/',len(batches),'rows',sum(r['rows'] for r in results),flush=True)
    save(RUN/'wikidata-statement-coverage.json',dict(at=now(),results=results))


def authorities():
    qids={q for a in roster() for q in qids_for(a)}
    for path in (RUN/'identity-search').glob('*.json'):
        for candidate in load(path).get('data',{}).get('search',[]):
            if candidate.get('id'): qids.add(candidate['id'])
    for path in (RUN/'wikidata-statements').glob('*.json.gz'):
        for b in load(path)['data']['results']['bindings']:
            value=b.get('other',{}).get('value','').rsplit('/',1)[-1]
            if re.fullmatch(r'Q[1-9][0-9]*',value): qids.add(value)
    coverage=RUN/'wikidata-authority-coverage.json'
    prior=[r for r in load(coverage)['results'] if r['ok']] if coverage.exists() else []
    covered={q for r in prior for q in r['qids']}
    qids=sorted(qids-covered)
    batches=[qids[i:i+150] for i in range(0,len(qids),150)]
    def one(batch):
        query='''SELECT ?artist ?artistLabel ?birth ?death ?occupation ?occupationLabel ?wikiart ?article WHERE {
          VALUES ?artist { '''+' '.join('wd:'+q for q in batch)+''' }
          OPTIONAL { ?artist wdt:P569 ?birth . } OPTIONAL { ?artist wdt:P570 ?death . }
          OPTIONAL { ?artist wdt:P106 ?occupation . }
          OPTIONAL { ?artist wdt:P6002 ?wikiart . }
          OPTIONAL { ?article schema:about ?artist; schema:isPartOf <https://en.wikipedia.org/> . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,mul,fr,de,ru,el" . }
        }'''
        key=hashlib.sha256(query.encode()).hexdigest()
        data=sparql(query,'wikidata-authorities',key)
        return dict(batch=key,qids=batch,ok=data is not None)
    results=list(prior)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(one,b) for b in batches]):
            results.append(f.result())
            if len(results)%10==0: print('Authorities',len(results),'/',len(batches),flush=True)
    save(RUN/'wikidata-authority-coverage.json',dict(at=now(),results=results))


def crosswalk():
    """Find missing authorities via explicit IDs; retain conflicts for review."""
    artists=roster()
    schemes={'nga-constituent':'P2252','fng-person':'P4177','moma-person':'P2174',
             'wikiart-artist':'P6002','tate-person':'P2741'}
    wanted=defaultdict(list)
    for a in artists:
        if qids_for(a): continue
        for e in a['identifiers']:
            if e['scheme'] in schemes:
                value=e['external_id']
                if e['scheme']=='tate-person' and e.get('canonical_url'):
                    value=e['canonical_url'].rstrip('/').rsplit('/',1)[-1]
                if e['scheme']=='fng-person': value=value.upper().split('E39.Actor_')[-1]
                wanted[(schemes[e['scheme']],value)].append(a['id'])
    pairs=sorted(wanted)
    batches=[pairs[i:i+80] for i in range(0,len(pairs),80)]
    def one(batch):
        values=' '.join('(wdt:'+prop+' '+json.dumps(value)+')' for prop,value in batch)
        query='''SELECT ?property ?value ?artist ?artistLabel ?birth ?death WHERE {
          VALUES (?property ?value) { '''+values+''' }
          ?artist ?property ?value . OPTIONAL {?artist wdt:P569 ?birth} OPTIONAL {?artist wdt:P570 ?death}
          SERVICE wikibase:label {bd:serviceParam wikibase:language "en,mul,fr,de,ru,el"}
        }'''
        return sparql(query,'identifier-crosswalk',hashlib.sha256(query.encode()).hexdigest())
    found=defaultdict(list)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i,result in enumerate(pool.map(one,batches)):
            if not result: continue
            for b in result['data']['results']['bindings']:
                key=(b['property']['value'].rsplit('/',1)[-1],b['value']['value'])
                for aid in wanted[key]:
                    found[aid].append(dict(qid=b['artist']['value'].rsplit('/',1)[-1],
                        label=b.get('artistLabel',{}).get('value'),birth=b.get('birth',{}).get('value'),
                        death=b.get('death',{}).get('value'),property=key[0],external_id=key[1],source_url=result['url']))
            if (i+1)%10==0: print('Identifier crosswalk',i+1,'/',len(batches),flush=True)
    by_id={a['id']:a for a in artists};results=[]
    for aid,candidates in found.items():
        qids={v['qid'] for v in candidates};a=by_id[aid]
        conflict=False
        for v in candidates:
            for ak,vk in [('birth_year','birth'),('death_year','death')]:
                if a.get(ak) is not None and re.match(r'^-?\d{4,}-\d\d-\d\dT',v.get(vk) or ''):
                    # Calendar conversion can move one day across New Year;
                    # any conflicting year remains an editorial hold here.
                    if int(v[vk].split('T')[0].rsplit('-',2)[0])!=a[ak]: conflict=True
        results.append(dict(artist_id=aid,name=a['display_name'],qid=next(iter(qids)) if len(qids)==1 else None,
            decision='supported_research_identity' if len(qids)==1 and not conflict else 'identity_conflict',
            basis='Exact museum/WikiArt identifier crosswalk; known life years checked',evidence=candidates))
    save(RUN/'research-identity-bindings.json',results)
    save(RUN/'identifier-crosswalk-coverage.json',dict(at=now(),attempted_artist_ids=sorted({a for ids in wanted.values() for a in ids}),
        matched=len(results),supported=sum(r['decision']=='supported_research_identity' for r in results)))
    print('Crosswalk',len(results),'candidates',Counter(r['decision'] for r in results),flush=True)


def identity_search():
    missing=[a for a in roster() if not qids_for(a)]
    def one(a):
        path=RUN/'identity-search'/(a['id']+'.json')
        if path.exists(): return load(path)
        name=a['display_name']
        for attempt in range(3):
            try:
                r=requests.get('https://www.wikidata.org/w/api.php',params=dict(action='wbsearchentities',
                    search=name,language='en',uselang='en',limit=5,format='json'),headers={'User-Agent':UA},timeout=40)
                if r.status_code==429:
                    time.sleep(min(120,max(10,int(r.headers.get('Retry-After','60')))));continue
                r.raise_for_status();data=r.json()
                if data.get('error'): raise ValueError(str(data['error']))
                result=dict(artist_id=a['id'],query=name,at=now(),url=r.url,data=data)
                save(path,result);time.sleep(0.3);return result
            except Exception as e:
                if attempt==2:
                    result=dict(artist_id=a['id'],query=name,at=now(),error=str(e).split('?')[0])
                    save(path,result);return result
                time.sleep(3*(attempt+1))
    counts=Counter()
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i,result in enumerate(pool.map(one,missing)):
            counts['attempted']+=1
            counts['error' if 'error' in result else 'results' if result['data'].get('search') else 'no_results']+=1
            if (i+1)%100==0:
                print('Identity searches',i+1,'/',len(missing),dict(counts),flush=True)
                save(RUN/'identity-search-progress.json',dict(at=now(),total=len(missing),counts=dict(counts)))
    save(RUN/'identity-search-progress.json',dict(at=now(),total=len(missing),counts=dict(counts),finished=True))


def resolve_names():
    auth=authority_index();artists=roster();by_id={a['id']:a for a in artists}
    path=RUN/'research-identity-bindings.json'
    previous=load(path) if path.exists() else []
    fixed={r['artist_id'] for r in previous}
    results=[];decisions=[]
    def tokens(name):
        return ' '.join(sorted(re.findall(r'[a-z0-9]+',unidecode(name).lower())))
    for source in (RUN/'identity-search').glob('*.json'):
        search=load(source);aid=search['artist_id']
        if aid in fixed: continue
        a=by_id[aid];supported=[];candidates=[]
        catalogue_names={tokens(n) for n in [a['display_name']]+a['aliases']}
        for r in search.get('data',{}).get('search',[]):
            q=r['id'];v=auth.get(q,{})
            source_names=[r.get('label',''),r.get('match',{}).get('text','')]+v.get('names',[])
            name_match=any(tokens(n) in catalogue_names for n in source_names if n)
            dates=[];conflict=False
            for ak,vk in [('birth_year','birth'),('death_year','death')]:
                years={int(d.split('T')[0].rsplit('-',2)[0]) for d in v.get(vk,[]) if re.match(r'^-?\d{4,}-\d\d-\d\dT',d)}
                if a.get(ak) is not None and years:
                    dates.append(a[ak] in years)
                    if a[ak] not in years: conflict=True
            occupations=v.get('occupations',[])
            art_practice=any(re.search(r'painter|artist|engraver|printmaker|sculptor|draughts|lithograph|illustrator|iconograph|miniatur',o,re.I) for o in occupations)
            item=dict(qid=q,label=r.get('label'),name_matches=name_match,date_matches=dates,
                conflicting_known_date=conflict,occupations=occupations,authority_checked=bool(v))
            candidates.append(item)
            if name_match and dates and all(dates) and not conflict and art_practice: supported.append(q)
        decision='supported_research_identity' if len(set(supported))==1 else 'identity_unresolved'
        decisions.append(dict(artist_id=aid,name=a['display_name'],decision=decision,candidates=candidates,search_url=search.get('url')))
        if decision=='supported_research_identity':
            results.append(dict(artist_id=aid,name=a['display_name'],qid=supported[0],decision=decision,
                basis='Unique exact full-name tokens/alias, compatible known life year(s), and documented visual-art occupation',
                evidence=dict(search_url=search['url'],candidates=candidates)))
    save(path,previous+results)
    save(RUN/'name-search-identity-decisions.json.gz',decisions)
    print('Name identities newly supported',len(results),'decisions',len(decisions),flush=True)


def qualifiers():
    statements=set()
    for p in (RUN/'wikidata-statements').glob('*.json.gz'):
        statements.update(b['claim']['value'] for b in load(p)['data']['results']['bindings'])
    statements=sorted(statements);batches=[statements[i:i+100] for i in range(0,len(statements),100)]
    def one(batch):
        query='''SELECT ?claim ?property ?propertyLabel ?value ?valueLabel WHERE { VALUES ?claim { '''+' '.join('<'+s+'>' for s in batch)+''' }
          ?claim ?predicate ?value . ?property wikibase:qualifier ?predicate .
          SERVICE wikibase:label {bd:serviceParam wikibase:language "en,mul"}
        }'''
        return sparql(query,'statement-qualifiers',hashlib.sha256(query.encode()).hexdigest())
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i,result in enumerate(pool.map(one,batches)):
            if (i+1)%10==0: print('Statement qualifiers',i+1,'/',len(batches),flush=True)


def wikipedia(language='en'):
    """Retrieve identity-checked full biographies in bounded API batches."""
    auth=authority_index()
    library_qids={q for a in roster() for q in qids_for(a)}
    if language=='en':
        title_q={unquote(url.rsplit('/wiki/',1)[-1]).replace('_',' '):qid
            for qid,a in auth.items() for url in a['articles'] if qid in library_qids and url.startswith('https://en.wikipedia.org/wiki/')}
    else:
        title_q={unquote(v['url'].rsplit('/wiki/',1)[-1]).replace('_',' '):v['qid'] for v in load(RUN/'native-article-index.json') if v['language']==language}
    manifest_path=RUN/('wikipedia-biography-manifest.json.gz' if language=='en' else 'wikipedia-'+language+'-manifest.json.gz')
    prior=load(manifest_path) if manifest_path.exists() else []
    done={p.get('qid') for p in prior if p.get('identity_match')}
    titles=sorted(t for t,q in title_q.items() if q not in done)
    batches=[titles[i:i+30] for i in range(0,len(titles),30)]
    def one(batch):
        key=hashlib.sha256(json.dumps(batch).encode()).hexdigest()
        path=CACHE/('wikipedia-'+language)/(key+'.json.gz')
        if path.exists(): return load(path)
        params=dict(action='query',format='json',formatversion=2,titles='|'.join(batch),
            prop='pageprops|info|revisions',inprop='url',rvprop='ids|timestamp|content',rvslots='main',redirects=1,maxlag=5)
        for attempt in range(4):
            try:
                r=requests.get('https://'+language+'.wikipedia.org/w/api.php',params=params,headers={'User-Agent':UA},timeout=80)
                if r.status_code==429:
                    time.sleep(min(120,max(10,int(r.headers.get('Retry-After','60')))));continue
                r.raise_for_status();data=r.json()
                if data.get('error'): raise ValueError(str(data['error']))
                result=dict(at=now(),requested={t:title_q[t] for t in batch},url=r.url,data=data)
                save(path,result);time.sleep(0.5);return result
            except Exception as e:
                if attempt==3: return dict(error=str(e).split('?')[0],requested={t:title_q[t] for t in batch})
                time.sleep(3*(attempt+1))
    manifest=list(prior)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i,data in enumerate(pool.map(one,batches)):
            allowed=set(data['requested'].values())
            if 'error' in data:
                manifest.append(data);continue
            for p in data['data'].get('query',{}).get('pages',[]):
                props=p.get('pageprops',{});qid=props.get('wikibase_item');revs=p.get('revisions',[])
                if not revs: continue
                raw=revs[0].get('slots',{}).get('main',{}).get('content','')
                match=qid in allowed and 'disambiguation' not in props
                record=dict(qid=qid,language=language,title=p['title'],source_url=p.get('fullurl'),revision_id=revs[0]['revid'],
                    revised_at=revs[0]['timestamp'],retrieved_at=data['at'],identity_match=match,
                    license_url='https://creativecommons.org/licenses/by-sa/4.0/',attribution='Wikipedia contributors',
                    revision_url='https://'+language+'.wikipedia.org/w/index.php?oldid='+str(revs[0]['revid']),
                    wikitext_sha256=hashlib.sha256(raw.encode()).hexdigest(),characters=len(raw))
                manifest.append(record)
                if match: save(CACHE/('biographies' if language=='en' else 'biographies-'+language)/(qid+'.json.gz'),dict(**record,wikitext=raw))
            if (i+1)%20==0: print('Wikipedia',language,'biographies',i+1,'/',len(batches),'pages',len(manifest),flush=True)
    save(manifest_path,manifest)
    print('Wikipedia',language,'pages',len(manifest),'matched',sum(m.get('identity_match',False) for m in manifest),flush=True)


def native_articles():
    auth=authority_index();artists=roster()
    languages=['ru','el','fr','de','it','es','nl','da','fi','sv','pl','pt','ja','zh','uk','hy','ka','ar']
    qids=sorted({q for a in artists for q in qids_for(a) if not auth.get(q,{}).get('articles')})
    covered=set();found=defaultdict(list)
    for path in (RUN/'native-sitelinks').glob('*.json.gz'):
        result=load(path);covered.update(re.findall(r'wd:(Q\d+)',result['query']))
        for b in result['data']['results']['bindings']:
            q=b['artist']['value'].rsplit('/',1)[-1];lang=urlparse(b['site']['value']).netloc.split('.')[0]
            if q in qids: found[q].append(dict(qid=q,language=lang,url=b['article']['value']))
    todo=[q for q in qids if q not in covered]
    batches=[todo[i:i+100] for i in range(0,len(todo),100)]
    def one(batch):
        query='SELECT ?artist ?article ?site WHERE { VALUES ?artist { '+' '.join('wd:'+q for q in batch)+' } VALUES ?site { '+' '.join('<https://'+l+'.wikipedia.org/>' for l in languages)+' } ?article schema:about ?artist; schema:isPartOf ?site . }'
        return sparql(query,'native-sitelinks',hashlib.sha256(query.encode()).hexdigest())
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i,result in enumerate(pool.map(one,batches)):
            if result:
                covered.update(re.findall(r'wd:(Q\d+)',result['query']))
                for b in result['data']['results']['bindings']:
                    q=b['artist']['value'].rsplit('/',1)[-1];lang=urlparse(b['site']['value']).netloc.split('.')[0]
                    found[q].append(dict(qid=q,language=lang,url=b['article']['value']))
            if (i+1)%10==0: print('Native-language article search',i+1,'/',len(batches),flush=True)
    # Use a fixed fallback language ordering; each selected
    # page must still match the authority ID returned by Wikipedia pageprops.
    selected=[min(v,key=lambda a:languages.index(a['language'])) for v in found.values()]
    save(RUN/'native-article-index.json',selected)
    save(RUN/'native-sitelink-coverage.json',dict(at=now(),qids_attempted=qids,selected=len(selected),qids_checked=sorted(set(qids)&covered),qids_failed=sorted(set(qids)-covered)))
    print('Native articles',len(selected),'/',len(qids),Counter(v['language'] for v in selected),flush=True)


def wikipedia_native():
    for language in sorted({v['language'] for v in load(RUN/'native-article-index.json')}):
        wikipedia(language)


def biography_leads():
    import mwparserfromhell
    auth=authority_index()
    library_qids={q for a in roster() for q in qids_for(a)}
    titles={('en',unquote(url.rsplit('/wiki/',1)[-1]).replace('_',' ')):qid for qid,a in auth.items() for url in a['articles']}
    native=RUN/'native-article-index.json'
    if native.exists():
        titles.update({(v['language'],unquote(v['url'].rsplit('/wiki/',1)[-1]).replace('_',' ')):v['qid'] for v in load(native)})
    pattern=re.compile(r'influen|inspir|pupil|studied under|teacher|admired|apprentice|влияни|вдохнов|ученик|учител|επιρρο|επηρεά|μαθητ|beeinfluss|schüler|lehrer|invloed|leerling|påvirk|elev|lärare|vaikut|oppilas|wpływ|ucze[nń]|élève|maître|formé|影響|影响|師事|ազդեց|ոգեշնչ|աշակերտ|ուսուցիչ|გავლენ|შთაგონ|მოსწავლ|მასწავლებ|تأثر|تأثير|تلميذ|أستاذ|ألهم')
    leads=[];checked=[]
    paths=sorted(p for folder in CACHE.glob('biographies*') for p in folder.glob('*.json.gz'))
    for i,path in enumerate(paths):
        page=load(path)
        if page['qid'] not in library_qids: continue
        raw=page['wikitext'];count=0
        for n,para in enumerate(re.split(r'\n\s*\n',raw)):
            if not pattern.search(para.lower()): continue
            code=mwparserfromhell.parse(para)
            for tag in list(code.filter_tags()):
                if str(tag.tag).lower() in ('ref','gallery','math'):
                    try: code.remove(tag)
                    except ValueError: pass
            for template in list(code.filter_templates(recursive=False)):
                try: code.remove(template)
                except ValueError: pass
            text=code.strip_code(normalize=True,collapse=True).strip()
            if not pattern.search(text.lower()) or len(text)<40: continue
            related=[];unresolved=[]
            for link in code.filter_wikilinks():
                title=str(link.title).split('#')[0].replace('_',' ').strip()
                q=titles.get((page.get('language','en'),title))
                if q and q!=page['qid']:
                    entry=dict(qid=q,title=title)
                    if entry not in related: related.append(entry)
                elif not q and title not in unresolved: unresolved.append(title)
            key=hashlib.sha256((page['revision_url']+'#'+str(n)).encode()).hexdigest()
            lead=dict(id=key,subject_qid=page['qid'],subject_title=page['title'],language=page.get('language','en'),
                source_url=page['source_url'],revision_url=page['revision_url'],paragraph_number=n,
                paragraph_sha256=hashlib.sha256(para.encode()).hexdigest(),related_painter_candidates=related,
                unresolved_link_titles=unresolved,
                status='context_and_direction_require_review',retrieved_at=page['retrieved_at'])
            leads.append(lead);count+=1
            save(CACHE/'lead-context'/(key+'.json.gz'),dict(**lead,text=text,wikitext=para))
        checked.append(dict(qid=page['qid'],language=page.get('language','en'),source_url=page['source_url'],
            revision_url=page['revision_url'],lead_paragraphs=count))
        if (i+1)%1000==0: print('Biography discovery',i+1,'/',len(paths),'leads',len(leads),flush=True)
    save(RUN/'biography-leads.json.gz',leads)
    save(RUN/'biography-discovery-coverage.json.gz',checked)
    print('Biographies checked',len(checked),'lead contexts',len(leads),flush=True)


def authority_index():
    result={}
    for path in (RUN/'wikidata-authorities').glob('*.json.gz'):
        for b in load(path)['data']['results']['bindings']:
            qid=b['artist']['value'].rsplit('/',1)[-1]
            a=result.setdefault(qid,dict(qid=qid,names=[],birth=[],death=[],occupations=[],wikiart=[],articles=[]))
            for key,target in [('artistLabel','names'),('birth','birth'),('death','death'),('occupationLabel','occupations'),('wikiart','wikiart'),('article','articles')]:
                if key in b and b[key]['value'] not in a[target]: a[target].append(b[key]['value'])
    return result


def wikiart():
    previous=ROOT/'docs/research/wikiart-artist-coverage-20260920'
    profiles=[]
    for path in (previous/'profiles').glob('*.json'):
        p=load(path)
        if p.get('outcome')=='inspected' and p.get('receipt'):
            p['profile_path']=str(path.relative_to(ROOT));profiles.append(p)
    def one(p):
        receipt=p['receipt'];url=receipt['url']
        path=previous/'captures'/(hashlib.sha256(url.encode()).hexdigest()+'.body')
        if not path.exists(): return dict(url=url,error='cached body missing')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=receipt['sha256']: return dict(url=url,error='checksum mismatch')
        soup=BeautifulSoup(raw,'lxml')
        facts=[]
        for li in soup.select('li.dictionary-values'):
            s=li.find('s')
            if not s: continue
            label=s.get_text(' ',strip=True).rstrip(':')
            if label not in ['Influenced by','Influenced on','Teachers','Pupils','Friends and Co-workers','Field']: continue
            for link in li.select('a[href]'):
                href=urljoin(receipt['final_url'],link['href'])
                facts.append(dict(field=label,name=link.get_text(' ',strip=True),url=href))
        # Biography text remains a discovery aid, never auto-accepted as an edge.
        paragraphs=[]
        for block in soup.select('.wiki-layout-artist-info p, .wiki-layout-artist-info article'):
            text=block.get_text(' ',strip=True)
            if re.search(r'influenc|inspir|pupil|teacher|studied under|admired',text,re.I):
                paragraphs.append(text)
        if paragraphs:
            save(CACHE/'wikiart-bio'/ (hashlib.sha256(url.encode()).hexdigest()+'.json.gz'),dict(url=url,paragraphs=paragraphs))
        return dict(url=url,name=p.get('name'),birth_year=p['source'].get('birth_year'),
            death_year=p['source'].get('death_year'),facts=facts,receipt=receipt,profile_path=p['profile_path'],
            biography_leads=bool(paragraphs))
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(one,p) for p in profiles]):
            results.append(f.result())
            if len(results)%500==0: print('WikiArt profiles',len(results),'/',len(profiles),flush=True)
    extra=RUN/'additional-wikiart-profile-receipts.json'
    if extra.exists():
        seen={p['url'] for p in results}
        results.extend(p for p in load(extra) if 'error' not in p and p['url'] not in seen)
    save(RUN/'wikiart-profiles.json.gz',results)
    print('WikiArt source profiles',len(results),'facts',sum(len(p.get('facts',[])) for p in results),flush=True)


def resolve_wikiart(artists, profiles, authorities):
    by_id={a['id']:a for a in artists}
    urls=defaultdict(set)
    reasons=defaultdict(set)
    def add(url,aid,why):
        url=url.rstrip('/')
        if aid in by_id:
            urls[url].add(aid);reasons[(url,aid)].add(why)
    for a in artists:
        for e in a['identifiers']:
            if e['scheme']=='wikiart-artist':
                add('https://www.wikiart.org/en/'+e['external_id'],a['id'],'catalogue WikiArt identifier')
        for q in qids_for(a):
            for slug in authorities.get(q,{}).get('wikiart',[]):
                if '/' not in slug: add('https://www.wikiart.org/en/'+slug,a['id'],'catalogue Wikidata identity + P6002')
    # Prior reviewed profile mappings are stable-ID bindings, not new fuzzy joins.
    old=load(ROOT/'docs/research/wikiart-artist-coverage-20260920/artist-matches.json')
    for row in old['matches']:
        a=by_id.get(row['artist']['id'])
        if a and a['slug']==row['artist']['slug']:
            add(row['wikiart']['url'],a['id'],'prior reviewed profile mapping, stable ID and slug')
    names=defaultdict(set)
    for a in artists:
        for name in [a['display_name']]+a['aliases']: names[norm(name)].add(a['id'])
    # Fallback requires one exact normalized full name and at least one matching
    # known life date. Conflicting dates and duplicate identities stay unresolved.
    for p in profiles:
        url=p['url'].rstrip('/')
        if urls[url] or not p.get('name'): continue
        matches=[]
        for aid in names[norm(p['name'])]:
            a=by_id[aid]
            known=[(a.get(k),p.get(k)) for k in ('birth_year','death_year') if a.get(k) is not None and p.get(k) is not None]
            if known and all(x==y for x,y in known): matches.append(aid)
        if len(matches)==1: add(url,matches[0],'unique exact normalized name and matching known life dates')
    return urls,reasons


def assemble():
    artists=roster();by_id={a['id']:a for a in artists}
    auth=authority_index();profiles=load(RUN/'wikiart-profiles.json.gz')
    by_q=defaultdict(set)
    for a in artists:
        for q in qids_for(a): by_q[q].add(a['id'])
    representatives={}
    for q,ids in by_q.items():
        native=[aid for aid in ids if any(e['scheme']=='wikidata' and e['external_id']==q for e in by_id[aid]['identifiers'])]
        representatives[q]=sorted(native or ids)[0]
    save(RUN/'shared-research-identities.json.gz',[dict(qid=q,artist_ids=sorted(ids),representative_id=representatives[q]) for q,ids in by_q.items() if len(ids)>1])
    urls,identity_reasons=resolve_wikiart(artists,profiles,auth)
    for url,ids in urls.items():
        common=set.intersection(*(qids_for(by_id[aid]) for aid in ids)) if len(ids)>1 else set()
        if len(common)==1:
            q=next(iter(common));rep=representatives[q]
            if rep in ids:
                urls[url]={rep}
                identity_reasons[(url,rep)].add('duplicate catalogue identities share an explicitly supported Wikidata identity')
    by_url={p['url'].rstrip('/'):p for p in profiles}
    evidence=[];holds=[]
    names=defaultdict(set)
    for a in artists:
        for name in [a['display_name']]+a['aliases']: names[norm(name)].add(a['id'])
    authority_names=defaultdict(set)
    authority_wikiart=defaultdict(set)
    for q,v in auth.items():
        for name in v['names']: authority_names[norm(name)].add(q)
        for slug in v['wikiart']: authority_wikiart['https://www.wikiart.org/en/'+slug].add(q)
    def named_qid(name):
        qs=authority_names[norm(name)]
        return next(iter(qs)) if len(qs)==1 else None
    def named(name):
        candidates=set(names[norm(name)])
        q=named_qid(name)
        if q in representatives: candidates.add(representatives[q])
        candidates=sorted(candidates)
        common=set.intersection(*(qids_for(by_id[aid]) for aid in candidates)) if candidates else set()
        if len(common)==1: return representatives[next(iter(common))]
        native=[aid for aid in candidates if any(e['scheme']=='wikidata' for e in by_id[aid]['identifiers'])]
        if len(native)==1: return native[0]
        return candidates[0] if len(candidates)==1 else None
    notes=RUN/'reviewed-source-notes.json'
    for document in load(notes) if notes.exists() else []:
        for c in document['claims']:
            target=named(c.get('target_name',document['target_name']))
            if not target:
                holds.append(dict(reason='reviewed source target requires identity reconciliation',document=document['source_url'],claim=c,target_name=c.get('target_name',document['target_name'])));continue
            source=named(c['source_name'])
            sq=named_qid(c['source_name'])
            provider=document.get('provider','Museum')
            evidence.append(dict(provider=provider,source_artist_id=source,source_label=c['source_name'],
                source_authority_url=c.get('source_authority_url','https://www.wikidata.org/wiki/'+sq if sq else document['source_url']),
                source_wikidata_id=sq,target_artist_id=target,
                relationship_type=c['relationship_type'],evidence_status='museum_source_read_and_reviewed' if provider=='Museum' else 'scholarly_source_read_and_reviewed',
                evidence_level=c.get('evidence_level','documented'),confidence='high',
                source_url=document['source_url'],publisher=document['publisher'],reviewed_at=document['reviewed_at'],
                identity_basis=['reviewed named painter in cited text; exact catalogue name/alias where uniquely resolved'],note=c['note']))
    decisions=RUN/'reviewed-biography-decisions.json'
    leads_path=RUN/'biography-leads.json.gz'
    lead_index={l['id']:l for l in load(leads_path)} if leads_path.exists() else {}
    for d in load(decisions) if decisions.exists() else []:
        if d['decision']!='explicit_secondary_source_statement': continue
        lead=lead_index[d['lead_id']];q=lead['subject_qid']
        target=named(d['target_name']) if d.get('target_name') else representatives.get(q)
        if not target:
            holds.append(dict(reason='reviewed biography subject outside resolved library',decision=d));continue
        for name in d['source_names']:
            qs={v['qid'] for v in lead['related_painter_candidates'] if norm(v['title'])==norm(name)}
            sq=next(iter(qs)) if len(qs)==1 else named_qid(name)
            source=representatives.get(sq) if sq else named(name)
            evidence.append(dict(provider='Wikipedia',source_artist_id=source,source_label=name,
                source_authority_url='https://www.wikidata.org/wiki/'+sq if sq else lead['source_url'],
                source_wikidata_id=sq,target_artist_id=target,relationship_type=d['relationship_type'],
                evidence_status='secondary_passage_direction_reviewed',evidence_level='secondary_source_assertion',confidence='medium',
                source_url=lead['revision_url'],page_url=lead['source_url'],lead_id=lead['id'],
                page_subject_qid=q,reviewed_target_override=d.get('target_name'),
                paragraph_sha256=lead['paragraph_sha256'],reviewed_at=d['reviewed_at'],note=d['note'],limitation=d['limitation'],
                identity_basis=['Wikipedia page identity checked against the catalogue authority; named influence direction read in source passage']))
    for p in profiles:
        for f in p.get('facts',[]):
            if f['field'] not in ('Influenced by','Influenced on'): continue
            source_url,target_url=(f['url'],p['url']) if f['field']=='Influenced by' else (p['url'],f['url'])
            source_url=source_url.rstrip('/');target_url=target_url.rstrip('/')
            sources=sorted(urls[source_url]);targets=sorted(urls[target_url])
            if len(targets)!=1:
                holds.append(dict(provider='WikiArt',source_url=source_url,target_url=target_url,
                    reason='target identity absent or ambiguous',target_candidates=targets,source_candidates=sources))
                continue
            if len(sources)>1:
                holds.append(dict(provider='WikiArt',source_url=source_url,target_id=targets[0],
                    reason='inspiring painter identity ambiguous',source_candidates=sources));continue
            source=by_id.get(sources[0]) if sources else None
            source_profile=by_url.get(source_url,{})
            source_label=(source['display_name'] if source else source_profile.get('name')) or (f['name'] if f['field']=='Influenced by' else p['name'])
            evidence.append(dict(provider='WikiArt',source_artist_id=source['id'] if source else None,
                source_label=source_label,source_authority_url=source_url,target_artist_id=targets[0],
                relationship_type='influenced',evidence_status='explicit_secondary_source_assertion',
                source_url=p['url'],source_field=f['field'],retrieved_at=p['receipt']['checked_at'],
                source_sha256=p['receipt']['sha256'],profile_path=p['profile_path'],
                identity_basis=sorted(identity_reasons[(target_url,targets[0])]),
                note='WikiArt explicitly lists this directed influence; underlying scholarship not supplied by this field.'))
    grouped={}
    claim_qualifiers=defaultdict(list)
    for path in (RUN/'statement-qualifiers').glob('*.json.gz'):
        for b in load(path)['data']['results']['bindings']:
            qualifier={k:v['value'] for k,v in b.items() if k!='claim'}
            if qualifier not in claim_qualifiers[b['claim']['value']]: claim_qualifiers[b['claim']['value']].append(qualifier)
    for path in (RUN/'wikidata-statements').glob('*.json.gz'):
        document=load(path)
        for b in document['data']['results']['bindings']:
            key=b['claim']['value']
            record=grouped.setdefault(key,dict(artist=b['artist']['value'].rsplit('/',1)[-1],
                other=b['other']['value'].rsplit('/',1)[-1],property=b['property']['value'].rsplit('/',1)[-1],
                claim=key,rank=b['rank']['value'].rsplit('#',1)[-1],references=[],retrieved_at=document['at']))
            if 'ref' in b:
                ref={k:b[k]['value'] for k in ('ref','refProperty','refValue') if k in b}
                if ref not in record['references']: record['references'].append(ref)
    for g in grouped.values():
        sources=[representatives[g['other']]] if g['other'] in representatives else []
        targets=[representatives[g['artist']]] if g['artist'] in representatives else []
        if g['rank']=='DeprecatedRank' or len(targets)!=1 or len(sources)>1:
            holds.append(dict(provider='Wikidata',statement=g,reason='deprecated claim or ambiguous identity'));continue
        source=by_id.get(sources[0]) if sources else None
        occupations=auth.get(g['other'],{}).get('occupations',[])
        painter=any(re.search(r'painter|miniaturist|iconographer|watercolorist|ukiyo-e artist',o,re.I) for o in occupations)
        if not source and not painter:
            holds.append(dict(provider='Wikidata',statement=g,reason='inspiring entity not established as a painter',occupations=occupations));continue
        source_names=auth.get(g['other'],{}).get('names',[])
        label=source['display_name'] if source else next((n for n in source_names if not re.fullmatch(r'Q\d+',n)),g['other'])
        refs=[r for r in g['references'] if r.get('refProperty','').rsplit('/',1)[-1] in ['P854','P248','P143']]
        evidence.append(dict(provider='Wikidata',source_artist_id=source['id'] if source else None,
            source_label=label,source_wikidata_id=g['other'],source_authority_url='https://www.wikidata.org/wiki/'+g['other'],
            target_artist_id=targets[0],relationship_type='influenced' if g['property']=='P737' else 'teacher_of',
            evidence_status='structured_source_assertion_with_references' if refs else 'structured_source_assertion_unreferenced',
            source_url='https://www.wikidata.org/wiki/'+g['artist']+'#'+g['property'],
            statement_url=g['claim'],rank=g['rank'],references=g['references'],qualifiers=claim_qualifiers[g['claim']],retrieved_at=g['retrieved_at'],
            identity_basis=['catalogue Wikidata identifier'],occupations=occupations,
            note='Wikidata source assertion; references retained but not independently verified. Student-of establishes teaching, not artistic inspiration.'))
    constraints_path=RUN/'reviewed-source-constraints.json'
    constraints=load(constraints_path) if constraints_path.exists() else []
    accepted=[]
    for e in evidence:
        a=by_id[e['target_artist_id']];s=by_id.get(e['source_artist_id'])
        if '/artists-by-' in e['source_authority_url'] or norm(e['source_label']) in {'orthodoxicons','ancientgreekpainting','ancientromanpainting','byzantinemosaics'}:
            holds.append(dict(reason='collective tradition or movement, not an individual painter',evidence=e));continue
        conflict=next((c for c in constraints if c['relationship_type']==e['relationship_type']
            and named(c['target_name'])==a['id'] and (named(c['source_name'])==e['source_artist_id']
                if named(c['source_name']) else norm(c['source_name'])==norm(e['source_label']))),None)
        if conflict:
            holds.append(dict(reason='relationship contested by reviewed scholarship',evidence=e,counterevidence=conflict));continue
        sq=qids_for(s) if s else ({e['source_wikidata_id']} if e.get('source_wikidata_id') else set())
        if not sq:
            sq=authority_wikiart.get(e['source_authority_url'],set())
            if len(sq)==1: e['source_wikidata_id']=next(iter(sq))
        occupations={o for q in sq for o in auth.get(q,{}).get('occupations',[])}
        if occupations and not any(re.search(r'painter|miniaturist|iconographer|watercolorist|ukiyo-e artist',o,re.I) for o in occupations):
            holds.append(dict(reason='source painter role not established by checked occupations',evidence=e,occupations=sorted(occupations)));continue
        e['source_painter_scope']='documented_painting_occupation' if occupations else 'source_names_visual_artist_painting_role_requires_review'
        if s and (s['id']==a['id'] or qids_for(s)&qids_for(a)):
            holds.append(dict(reason='self relation / identity conflict',evidence=e));continue
        source_birth={s['birth_year']} if s and s.get('birth_year') is not None else {
            int(d.split('T')[0].rsplit('-',2)[0]) for q in sq for d in auth.get(q,{}).get('birth',[]) if re.match(r'^-?\d{4,}-\d\d-\d\dT',d)}
        source_death={s['death_year']} if s and s.get('death_year') is not None else {
            int(d.split('T')[0].rsplit('-',2)[0]) for q in sq for d in auth.get(q,{}).get('death',[]) if re.match(r'^-?\d{4,}-\d\d-\d\dT',d)}
        # Posthumous artistic influence is possible; personal teaching is distinct.
        if source_birth and a.get('death_year') is not None and min(source_birth)>a['death_year']:
            holds.append(dict(reason='impossible known chronology',evidence=e));continue
        if e['relationship_type']=='teacher_of' and source_death and a.get('birth_year') is not None and max(source_death)<a['birth_year']:
            holds.append(dict(reason='impossible personal teaching chronology',evidence=e));continue
        accepted.append(e)
    edges={}
    for e in accepted:
        source=e['source_artist_id'] or (e['source_authority_url'],e['source_label'])
        key=(source,e['target_artist_id'],e['relationship_type'])
        edge=edges.setdefault(key,dict(source_artist_id=e['source_artist_id'],source_label=e['source_label'],
            source_authority_url=e['source_authority_url'],target_artist_id=e['target_artist_id'],
            target_label=by_id[e['target_artist_id']]['display_name'],relationship_type=e['relationship_type'],
            research_status='source_reported_not_independently_verified',publication_status='review',evidence=[]))
        edge['evidence'].append(e)
        if e['provider'] in ('Museum','Scholarly publication'): edge['research_status']='museum_or_scholarly_source_reviewed'
    # One painter may have multiple catalogue records. Carry an evidenced result
    # to those records only through explicit, nonconflicting authority bindings.
    for key,e in list(edges.items()):
        for q in qids_for(by_id[e['target_artist_id']]):
            for aid in by_q[q]:
                extra=(key[0],aid,key[2])
                if extra in edges: continue
                edges[extra]=dict(**{k:v for k,v in e.items() if k not in ('target_artist_id','target_label')},
                    target_artist_id=aid,target_label=by_id[aid]['display_name'],
                    shared_identity_basis=dict(qid=q,original_target_artist_id=e['target_artist_id']))
    covered_q=set()
    coverage=RUN/'wikidata-statement-coverage.json'
    if coverage.exists():
        for b in load(coverage)['results']:
            if b['ok']: covered_q.update(b['qids'])
    registers=[]
    incoming=defaultdict(list)
    for e in edges.values(): incoming[e['target_artist_id']].append(e)
    biography_coverage=RUN/'biography-discovery-coverage.json.gz'
    bios=defaultdict(list)
    for b in load(biography_coverage) if biography_coverage.exists() else []: bios[b['qid']].append(b)
    decisions=load(RUN/'reviewed-biography-decisions.json') if (RUN/'reviewed-biography-decisions.json').exists() else []
    reviewed={d['lead_id']:d for d in decisions}
    leads=defaultdict(list)
    for lead in lead_index.values(): leads[lead['subject_qid']].append(lead)
    searches={p.stem:load(p) for p in (RUN/'identity-search').glob('*.json')}
    matched_profiles=defaultdict(set)
    for u,ids in urls.items():
        if u not in by_url: continue
        for aid in ids:
            matched_profiles[aid].add(u)
            for q in qids_for(by_id[aid]):
                for other in by_q[q]: matched_profiles[other].add(u)
    for a in artists:
        matched=sorted(matched_profiles[a['id']])
        es=incoming[a['id']]
        qs=qids_for(a);bs=[b for q in qs for b in bios[q]];ls=[l for q in qs for l in leads[q]]
        checked=bool(qs&covered_q);search=searches.get(a['id']);pending=sum(l['id'] not in reviewed for l in ls)
        state=('source_assertions_found' if es else 'biography_passages_require_review' if pending else
            'no_relationship_in_checked_sources' if matched or checked or bs else
            'identity_unresolved_after_search' if search else 'identity_lookup_not_completed')
        registers.append(dict(artist_id=a['id'],slug=a['slug'],name=a['display_name'],catalogue_bindings=a['catalogue_bindings'],
            wikidata_ids=sorted(qs),wikidata_statement_check=checked,
            wikiart_profiles_checked=matched,explicit_influences=sum(e['relationship_type']=='influenced' for e in es),
            teacher_links=sum(e['relationship_type']=='teacher_of' for e in es),
            catalogue_biography_present=bool(a.get('biography_md')),catalogue_biography_characters=len(a.get('biography_md') or ''),
            identity_search=(dict(query=search['query'],source_url=search.get('url'),at=search['at'],
                status='error' if 'error' in search else 'candidates_found' if search.get('data',{}).get('search') else 'no_candidate_found') if search else None),
            research_attempted=bool(checked or matched or bs or search),
            biographies_checked=bs,biography_lead_paragraphs=len(ls),biography_leads_pending=pending,
            biography_leads_reviewed=sum(l['id'] in reviewed for l in ls),research_status=state,
            completeness_note='A bounded source pass, not proof of a complete influence list. No result does not mean no influences existed.'))
    save(RUN/'source-reported-relationships.json.gz',list(edges.values()))
    save(RUN/'identity-and-evidence-holds.json.gz',holds)
    save(RUN/'painter-research-register.json.gz',registers)
    save(RUN/'authority-index.json.gz',auth)
    def identity(aid,fallback):
        qs=qids_for(by_id[aid]) if aid else set()
        return ('wikidata',next(iter(qs))) if len(qs)==1 else ('catalogue',aid) if aid else ('external',fallback)
    unique={}
    for e in edges.values():
        key=(identity(e['source_artist_id'],e['source_authority_url']+'#'+e['source_label']),
            identity(e['target_artist_id'],''),e['relationship_type'])
        unique[key]=e
    summary=dict(at=now(),painters=len(artists),relationship_pairs=len(edges),evidence_assertions=len(accepted),
        relationship_types=dict(Counter(e['relationship_type'] for e in edges.values())),
        unique_identity_relationship_pairs=len(unique),unique_identity_relationship_types=dict(Counter(e['relationship_type'] for e in unique.values())),
        unique_identity_painters_with_influence=len({k[1] for k in unique if k[2]=='influenced'}),
        painters_with_influence=sum(r['explicit_influences']>0 for r in registers),
        painters_with_teachers=sum(r['teacher_links']>0 for r in registers),
        research_states=dict(Counter(r['research_status'] for r in registers)),
        wikidata_checked=sum(r['wikidata_statement_check'] for r in registers),wikiart_matched=sum(bool(r['wikiart_profiles_checked']) for r in registers),
        research_attempted=sum(r['research_attempted'] for r in registers),
        identity_searches=len(searches),biographies_checked=sum(len(r['biographies_checked']) for r in registers),
        unique_biography_pages_checked=sum(len(b) for b in bios.values()),
        biography_passages_discovered=len(lead_index),biography_passages_reviewed=len(reviewed),
        museum_scholarly_documents_reviewed=len(load(notes)) if notes.exists() else 0,
        museum_scholarly_unique_pairs=sum(e['research_status']=='museum_or_scholarly_source_reviewed' for e in unique.values()),
        holds=len(holds),database_writes=0)
    save(RUN/'summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
    # Plain JSONL is convenient for tools and preserves a row for every artist.
    with (RUN/'painters.jsonl').open('w') as out:
        for r in sorted(registers,key=lambda r:(norm(r['name']),r['artist_id'])):
            row=dict(**r,relationships=sorted(incoming[r['artist_id']],key=lambda e:(e['relationship_type'],norm(e['source_label']))))
            out.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    lines=['# Painter influences: research results','',
        'Direction below: **library painter ← painter who influenced them**. These are source-reported relationships, not a complete or uniformly verified history. Teaching and admiration remain separate in the structured files. All records remain in research review.','']
    for r in sorted(registers,key=lambda r:(norm(r['name']),r['artist_id'])):
        influences=[e for e in incoming[r['artist_id']] if e['relationship_type']=='influenced']
        if not influences: continue
        lines.extend(['## '+r['name'],'', 'Catalogue ID: `'+r['artist_id']+'`.',''])
        for e in sorted(influences,key=lambda e:norm(e['source_label'])):
            sources=list(dict.fromkeys((v['provider'],v['source_url']) for v in e['evidence']))
            citations='; '.join('['+provider+']('+url+')' for provider,url in sources)
            status='museum/scholarly text reviewed' if e['research_status']=='museum_or_scholarly_source_reviewed' else 'source assertion; independent verification pending'
            lines.append('- **'+e['source_label']+'** — '+citations+' — '+status+'.')
        lines.append('')
    (RUN/'influences-by-painter.md').write_text('\n'.join(lines)+'\n')


def validate():
    """Check the actual saved research, without fixtures or catalogue writes."""
    artists=roster();by_id={a['id']:a for a in artists}
    registers=load(RUN/'painter-research-register.json.gz')
    edges=load(RUN/'source-reported-relationships.json.gz')
    checks=[]
    def check(name,condition):
        checks.append(dict(check=name,passed=bool(condition)))
        if not condition: raise AssertionError(name)
    check('One register row per pinned library record',len(registers)==len(artists)==len({r['artist_id'] for r in registers}))
    check('Register has exactly the pinned library IDs',{r['artist_id'] for r in registers}==set(by_id))
    check('Every record has a documented source or identity lookup attempt',all(r['research_attempted'] for r in registers))
    for target in ('local','production'):
        receipt=load(RUN/(target+'-snapshot.json'))
        check(target+' pinned snapshot checksum unchanged',hashlib.sha256((RUN/(target+'-artists.json.gz')).read_bytes()).hexdigest()==receipt['sha256'])
    keys=set()
    for e in edges:
        a=by_id[e['target_artist_id']];s=by_id.get(e['source_artist_id'])
        assert not e['source_artist_id'] or s
        assert e['publication_status']=='review' and e['evidence']
        assert e['relationship_type'] in {'influenced','teacher_of','documented_admiration'}
        assert all(v['source_url'].startswith('https://') and v['provider'] for v in e['evidence'])
        assert '/artists-by-' not in e['source_authority_url']
        assert norm(e['source_label'])!='orthodoxicons'
        assert not s or (s['id']!=a['id'] and not qids_for(s)&qids_for(a))
        assert not (s and s.get('birth_year') is not None and a.get('death_year') is not None and s['birth_year']>a['death_year'])
        assert not (s and e['relationship_type']=='teacher_of' and s.get('death_year') is not None and a.get('birth_year') is not None and s['death_year']<a['birth_year'])
        key=(e['source_artist_id'] or (e['source_authority_url'],e['source_label']),e['target_artist_id'],e['relationship_type'])
        assert key not in keys;keys.add(key)
    checks.append(dict(check='All relationships have valid IDs, direction, citations, review status, and chronology; groups excluded',passed=True,rows=len(edges)))
    def has(source,target,kind):
        return any(norm(e['source_label'])==norm(source) and norm(e['target_label'])==norm(target) and e['relationship_type']==kind for e in edges)
    check('Rublev influence retained with direct-pupil dispute held',has('Theophanes the Greek','Andrei Rublev','influenced') and not has('Theophanes the Greek','Andrei Rublev','teacher_of'))
    check('Monet and Boudin influence and teaching stay distinct',has('Eugène Boudin','Claude Monet','influenced') and has('Eugène Boudin','Claude Monet','teacher_of'))
    check('Multiple cited Parthenis influences retained',sum(e['target_label']=='Konstantinos Parthenis' and e['relationship_type']=='influenced' for e in edges)>=4)
    with (RUN/'painters.jsonl').open() as f: rows=[json.loads(line) for line in f]
    check('Readable JSONL covers every register record',len(rows)==len(registers) and {r['artist_id'] for r in rows}==set(by_id))
    check('JSONL relationships agree with saved edge set',sum(len(r['relationships']) for r in rows)==len(edges))
    for filename in ('wikidata-statement-coverage.json','wikidata-authority-coverage.json'):
        check(filename+' has no failed final batches',all(r['ok'] for r in load(RUN/filename)['results']))
    summary=load(RUN/'summary.json')
    check('Summary counts agree with relationships',summary['relationship_types']==dict(Counter(e['relationship_type'] for e in edges)))
    save(RUN/'validation.json',dict(at=now(),checks=checks,catalogue_writes=0,validation_scope='Saved research consistency, not independent historical validation of every source assertion.'))
    print('Passed',len(checks),'checks across',len(registers),'library records and',len(edges),'relationships',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['export','wikidata','authorities','wikiart','assemble','crosswalk','wikipedia','identity_search','native_articles','wikipedia_native','biography_leads','resolve_names','qualifiers','validate'])
    parser.add_argument('--target',choices=['local','production'],default='local')
    args=parser.parse_args()
    if args.command=='export': export(args.target)
    else: globals()[args.command]()
