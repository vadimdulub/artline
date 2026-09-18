#!/usr/bin/env python3
"""Bounded Russian Museum metadata capture; no images or database writes."""
import argparse, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/russian-painters-20260913'
BASE = 'https://rusmuseumvrm.ru'
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'ArtlineResearch/1.0 (owner-requested catalogue research; metadata only)'

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, indent=2).encode()
    if path.exists():
        if path.read_bytes() != data: raise ValueError(f'Evidence conflict: {path}')
    else: path.write_bytes(data)

def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    path = RUN / 'captures' / (key + '.html')
    if path.exists(): return BeautifulSoup(path.read_bytes(), 'html.parser'), key
    time.sleep(.35)
    r = SESSION.get(url, timeout=45)
    r.raise_for_status()
    if len(r.content) > 6_000_000: raise ValueError('Oversize response')
    save(path, r.content)
    save(path.with_suffix('.json'), {'url': url, 'final_url': r.url, 'retrieved_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'sha256': hashlib.sha256(r.content).hexdigest(), 'bytes': len(r.content)})
    return BeautifulSoup(r.content, 'html.parser'), key

def txt(node): return node.get_text(' ', strip=True) if node else ''

def norm(name):
    return ' '.join(sorted(re.findall(r'[а-яa-z]+',name.casefold().replace('ё','е'))))

def authors():
    soup, key = fetch(BASE+'/collections/references/authors/index.php?lang=ru')
    index = {}
    for a in soup.select('a[href*="/reference/classifier/author/"]'):
        index.setdefault(urljoin(BASE,a['href']),set()).add(txt(a))
    save(RUN/'museum-authors.json',{u:sorted(n) for u,n in index.items()})
    print('museum authors',len(index),flush=True)

def crosswalk():
    wd = json.loads(Path('/tmp/artline-russian-wikidata-v4.json').read_bytes())
    save(RUN/'wikidata-painter-authorities.json',wd)
    index = json.loads((RUN/'museum-authors.json').read_bytes())
    works = json.loads((RUN/'listings.json').read_bytes())['works']
    byname = {}
    for row in wd['results']['bindings']:
        if 'label' not in row: continue
        byname.setdefault(norm(row['label']['value']),[]).append(row)
    matches, deferred = {}, []
    for url in sorted({a['url'] for w in works for a in w['authors']}):
        names = index.get(url,[])
        found = {r['p']['value']:r for name in names for r in byname.get(norm(name),[])}
        if len(found)!=1:
            deferred.append({'url':url,'names':names,'reason':'no_unique_full_name_authority'})
            continue
        row = next(iter(found.values()))
        desc=row.get('description',{}).get('value','')
        if not re.search(r'\brussian\b',desc,re.I):
            deferred.append({'url':url,'names':names,'reason':'russian_affiliation_not_explicit','authority':row})
            continue
        matches[url]={'qid':row['p']['value'].rsplit('/',1)[1],'name':names[0],'native_name':row['label']['value'],'description':desc,'url':url,'match_basis':'unique exact full name, ignoring order; Wikidata painter occupation and explicit Russian description','wikidata':row}
    save(RUN/'creator-crosswalk.json',matches)
    save(RUN/'creator-deferred.json',deferred)
    selected=[w for w in works if len(w['authors'])==1 and w['authors'][0]['url'] in matches]
    print('matched authors',len(matches),'candidate works',len(selected),'deferred authors',len(deferred),flush=True)

def jsonfetch(url, params):
    request = requests.Request('GET',url,params=params).prepare().url
    key=hashlib.sha256(request.encode()).hexdigest()
    path=RUN/'authority-captures'/(key+'.json')
    if path.exists(): return json.loads(path.read_bytes())
    time.sleep(6)
    r=SESSION.get(request,timeout=60)
    if r.status_code == 429:
        save(RUN/'rate-limit-events'/(key+'.json'),{'url':request,'status':429,'retry_after':r.headers.get('Retry-After'),'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    r.raise_for_status(); data=r.json()
    if 'error' in data: raise ValueError(data['error'])
    save(path,r.content)
    save(path.with_suffix('.receipt.json'),{'url':request,'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    return data

def entities():
    cross=json.loads((RUN/'creator-crosswalk.json').read_bytes())
    deferred=json.loads((RUN/'creator-deferred.json').read_bytes())
    qids={r['qid'] for r in cross.values()}
    qids.update(r['authority']['p']['value'].rsplit('/',1)[1] for r in deferred if 'authority' in r)
    qids=sorted(qids); result={}
    for start in range(0,len(qids),40):
        data=jsonfetch('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(qids[start:start+40]),'props':'labels|descriptions|aliases|claims','languages':'en|ru','format':'json'})
        result.update(data['entities']); print('authorities',len(result),'/',len(qids),flush=True)
    save(RUN/'creator-entities.json',result)

def additional_entities():
    original=json.loads((RUN/'creator-entities.json').read_bytes())
    direct=json.loads(Path('/tmp/artline-russian-direct-authorities.json').read_bytes())
    save(RUN/'wikidata-direct-museum-authorities.json',direct)
    used={a['url'].split('/')[-2] for w in json.loads((RUN/'deferred-works.json').read_bytes()) for a in w.get('authors',[])}
    qids=sorted({row['p']['value'].rsplit('/',1)[1] for row in direct['results']['bindings'] if row['id']['value'] in used and row['p']['value'].rsplit('/',1)[1] not in original})
    result={}
    for start in range(0,len(qids),40):
        data=jsonfetch('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(qids[start:start+40]),'props':'labels|descriptions|aliases|claims','languages':'en|ru','format':'json'})
        result.update(data['entities']);print('additional exact-ID authorities',len(result),'/',len(qids),flush=True)
    save(RUN/'additional-creator-entities.json',result)

def values(entity, prop):
    claims=[c for c in entity.get('claims',{}).get(prop,[]) if c.get('rank')!='deprecated']
    preferred=[c for c in claims if c.get('rank')=='preferred']
    return preferred or claims

def year(entity,prop):
    result=set()
    for c in values(entity,prop):
        v=c['mainsnak'].get('datavalue',{}).get('value',{})
        if c.get('qualifiers') or v.get('precision',0)<9: return None
        m=re.match(r'^\+(\d{4})-',v.get('time',''))
        if m: result.add(int(m[1]))
    return next(iter(result)) if len(result)==1 else None

def date(display):
    text=display.strip().replace('–','-').replace('—','-')
    unknown={'first':None,'last':None,'precision':'unknown'}
    years=[int(x) for x in re.findall(r'(?<!\d)(1\d{3}|20\d{2})(?!\d)',text)]
    if years and min(years)>1970: return None
    if re.search(r'XXI|ХХI|ХХІ|XXІ|ХХИ',text,re.I): return None
    m=re.fullmatch(r'(?:Около |около |Ок\. |ок\. )?(1\d{3})(?:\s*-\s*(1\d{3}))?\s*(?:г\.?|гг\.?)?\s*(\(\?\)|\?)?\.?',text)
    if m:
        a=int(m[1]);b=int(m[2] or m[1]);p='range' if a!=b else 'exact'
        if 'ок' in text.lower() or m[3]: p='circa_range' if a!=b else 'circa'
        return {'first':a,'last':b,'precision':p} if 1100<=a<=b<=1970 else unknown
    m=re.fullmatch(r'(?:Начало |Середина |Конец |Первая половина |Вторая половина )?(1\d{2}0)-(?:е|х)(?:\s*гг?\.?)?\.?',text)
    if m:
        a=int(m[1]);return {'first':a,'last':a+9,'precision':'decade'} if a+9<=1970 else unknown
    return unknown

def plan(additional=False):
    authorities=json.loads((RUN/'creator-entities.json').read_bytes())
    if additional:authorities.update(json.loads((RUN/'additional-creator-entities.json').read_bytes()))
    museum=json.loads((RUN/'museum-authors.json').read_bytes())
    existing=json.loads(Path('/tmp/artline-russian-existing-works.json').read_bytes()) or []
    old={r['canonical_url'].split('?')[0] for r in existing}
    if additional:old.update(w['url'] for f in (RUN/'batch').glob('chunk-*.json') for w in json.loads(f.read_bytes())['works'])
    byname={}; eligible={}
    for q,e in authorities.items():
        descriptions={k:v['value'] for k,v in e.get('descriptions',{}).items()}
        desc=' | '.join(descriptions.values())
        country=[c['mainsnak'].get('datavalue',{}).get('value',{}).get('id') for c in values(e,'P27')]
        affiliation = bool(re.search(r'\brussian\b|\bрусск|\bроссийск',desc,re.I))
        if not affiliation and 'Q159' not in country: continue
        occupation=[c['mainsnak'].get('datavalue',{}).get('value',{}).get('id') for c in values(e,'P106')]
        if 'Q1028181' not in occupation: continue
        names=[v['value'] for v in e.get('labels',{}).values()]+[v['value'] for group in e.get('aliases',{}).values() for v in group]
        for name in names: byname.setdefault(norm(name),set()).add(q)
        native=e.get('labels',{}).get('ru',{}).get('value','')
        eligible[q]={'qid':q,'name':e.get('labels',{}).get('en',{}).get('value',native),'native_name':native,'description':desc,'birth':year(e,'P569'),'death':year(e,'P570'),'affiliation_evidence':('Explicit source Russian description: '+desc) if affiliation else 'Wikidata P27 explicitly records Russian Federation citizenship; other identities retained: '+desc}
    cross={}
    for url,names in museum.items():
        qs=set().union(*(byname.get(norm(n),set()) for n in names))
        if additional:
            direct={q for q in eligible if any(c['mainsnak'].get('datavalue',{}).get('value')==url.split('/')[-2] for c in values(authorities[q],'P12716'))}
            if len(direct)==1 and (not qs or qs==direct):qs=direct
        if len(qs)==1:
            q=next(iter(qs));cross[url]={**eligible[q],'url':url}
    selected=[];deferred=[];ranges={}
    for w in json.loads((RUN/'listings.json').read_bytes())['works']:
        reason=None
        if w['url'] in old: reason='existing_canonical_object'
        elif len(w['authors'])!=1 or w['authors'][0]['url'] not in cross: reason='creator_not_reconciled_as_russian_painter'
        elif w['creator_label']!=w['authors'][0]['label']: reason='qualified_or_ambiguous_creator_label'
        d=date(w['date_display'])
        if d is None:reason='post_1970'
        if reason: deferred.append({**w,'reason':reason});continue
        a=cross[w['authors'][0]['url']];q=a['qid']
        if d['first'] is not None:ranges.setdefault(q,[]).extend((d['first'],d['last']))
        selected.append({'painter':q,'title':w['title'],'institution':'russian-session-museum','source_object_id':w['url'].removeprefix(BASE),'url':w['url'],'attribution_role':'primary','date_display':w['date_display'] or 'Date unknown','creation_date':d,'work_type':{'painting':'painting','drawings':'drawing','engraving':'print'}[w['section']],'description_md':f"{w['title']} — {a['native_name']}. {w['date_display'] or 'Date unknown'}.\n\nState Russian Museum collection listing. Medium, dimensions and accession have not yet been checked against the detailed object notice.\n\n[Official catalogue entry]({w['url']}). [Collection listing]({w['listing_url']}), accessed 13 September 2026.",'notes':'Collection-scoped catalogue evidence; named-creator match uses full native name or exact authority alias. No current-display or masterpiece designation. Unparsed dates remain unknown and require review.','source_publisher':'State Russian Museum','source_raw':w})
    authors={a['qid']:a for a in cross.values()}
    for q,a in authors.items():
        if q in ranges:a.update(start=min(ranges[q]),end=max(ranges[q]))
    kept=[]
    for w in selected:
        if w['painter'] not in ranges:deferred.append({**w,'reason':'no_dated_work_for_authority_activity'})
        else:kept.append(w)
    kept.sort(key=lambda w:(w['painter'],w['url']))
    prefix='additional-' if additional else ''
    batchdir=RUN/('additional-batch' if additional else 'batch')
    save(RUN/(prefix+'selected-authors.json'),{q:authors[q] for q in {w['painter'] for w in kept}})
    save(RUN/(prefix+'deferred-works.json'),deferred)
    chunks=[]
    for start in range(0,len(kept),250):
        rows=kept[start:start+250];name=f'chunk-{start//250+1:03}.json'
        chunk={'source':'russian-painters-20260913','accessed_on':'2026-09-13','authors':{q:authors[q] for q in sorted({w['painter'] for w in rows})},'works':rows}
        save(batchdir/name,chunk)
        chunks.append({'file':name,'sha256':hashlib.sha256((batchdir/name).read_bytes()).hexdigest(),'works':len(rows)})
    manifest={'source':'russian-painters-20260913','chunks':chunks,'works':len(kept),'artists':len({w['painter'] for w in kept}),'unknown_dates':sum(w['creation_date']['precision']=='unknown' for w in kept)}
    save(batchdir/'manifest.json',manifest)
    print(manifest|{'chunks':len(chunks),'sha256':hashlib.sha256((batchdir/'manifest.json').read_bytes()).hexdigest()},flush=True)

def listing():
    rows, counts = {}, {}
    for section in ('painting', 'drawings', 'engraving'):
        for page in range(1, 21):
            url = f'{BASE}/collections/{section}/index.php?lang=ru&p=0&page={page}&ps=500&show=asc&t=0'
            soup, key = fetch(url)
            total = txt(soup.select_one('.collection-total'))
            items = soup.select('.works__item')
            print(section, page, total, len(items), flush=True)
            counts[section] = total
            if not items: break
            for node in items:
                a = node.select_one('.a_area a')
                authors = node.select('.item__author a')
                if not a: continue
                obj = urljoin(BASE, a['href'])
                rows.setdefault(obj, {'url':obj, 'title':txt(node.select_one('.item__title')), 'date_display':txt(node.select_one('.item__desc')), 'creator_label':txt(node.select_one('.item__author')), 'authors':[{'url':urljoin(BASE,x['href']), 'label':txt(x)} for x in authors], 'section':section, 'listing_url':url, 'capture':key})
            n = re.search(r'\d+', total)
            if not n or page * 500 >= int(n[0]): break
            if len(rows) >= 14000: break
    save(RUN/'listings.json', {'counts':counts,'works':list(rows.values())})
    print('unique works',len(rows),flush=True)

def combine():
    chunks=[];allworks=[];authors=set();out=RUN/'combined-batch'
    for directory in ('batch','additional-batch'):
        manifest=json.loads((RUN/directory/'manifest.json').read_bytes())
        for item in manifest['chunks']:
            data=(RUN/directory/item['file']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Source chunk changed')
            name=f'chunk-{len(chunks)+1:03}.json';save(out/name,data)
            c=json.loads(data);allworks.extend(c['works']);authors.update(c['authors'])
            chunks.append({**item,'file':name})
    if len({w['url'] for w in allworks})!=len(allworks):raise ValueError('Combined batches overlap')
    manifest={'source':'russian-painters-20260913','chunks':chunks,'works':len(allworks),'artists':len(authors),'unknown_dates':sum(w['creation_date']['precision']=='unknown' for w in allworks)}
    save(out/'manifest.json',manifest)
    print(manifest|{'chunks':len(chunks),'sha256':hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()},flush=True)

def retain_dates():
    es=json.loads((RUN/'creator-entities.json').read_bytes());es.update(json.loads((RUN/'additional-creator-entities.json').read_bytes()))
    works=[w for w in json.loads((RUN/'additional-deferred-works.json').read_bytes()) if w['reason']=='no_dated_work_for_authority_activity']
    authors={}
    for w in works:
        q=w['painter'];e=es[q];descriptions=' | '.join(x['value'] for x in e.get('descriptions',{}).values())
        authors[q]={'qid':q,'name':e['labels'].get('en',e['labels']['ru'])['value'],'native_name':e['labels']['ru']['value'],'url':w['source_raw']['authors'][0]['url'],'description':descriptions,'affiliation_evidence':'Source-described Russian painter: '+descriptions,'birth':year(e,'P569'),'death':year(e,'P570'),'start':0,'end':0}
        del w['reason']
    data={'source':'russian-painters-20260913','accessed_on':'2026-09-13','authors':authors,'works':works}
    directory=RUN/'date-review-batch';save(directory/'chunk-001.json',data)
    manifest={'source':'russian-painters-20260913','chunks':[{'file':'chunk-001.json','sha256':hashlib.sha256((directory/'chunk-001.json').read_bytes()).hexdigest(),'works':len(works)}],'works':len(works),'artists':len(authors),'unknown_dates':len(works),'unlinked_named_creators':True}
    save(directory/'manifest.json',manifest)
    print(manifest|{'sha256':hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()},flush=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('phase',choices=['list','authors','crosswalk','entities','plan','additional-entities','additional-plan','combine','retain-dates']); args=parser.parse_args()
    {'list':listing,'authors':authors,'crosswalk':crosswalk,'entities':entities,'plan':plan,'additional-entities':additional_entities,'additional-plan':lambda:plan(True),'combine':combine,'retain-dates':retain_dates}[args.phase]()
