#!/usr/bin/env python3
"""Read-only production Louvre inventory and WikiArt image discovery.

Preserves evidence only. Never downloads image binaries or writes to a database.
"""
import argparse
import collections
import concurrent.futures
import difflib
import gzip
import html
import importlib.util
import json
import re
import time
import threading
import unicodedata
from urllib.parse import quote, urljoin, urlparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('location_research', ROOT / 'ops/research-artwork-locations-20261004.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
r.PORT = 55445
r.RUN = ROOT / 'docs/research/louvre-wikiart-20261006'
FETCH_LOCK = threading.Lock()
FETCH_NEXT = 0.0
FETCH_STOP = threading.Event()


def norm(text):
    text = unicodedata.normalize('NFKD', html.unescape(str(text or '')).casefold())
    return ' '.join(re.findall(r'[^\W_]+', ''.join(x for x in text if not unicodedata.combining(x))))


def capture(url, tag='wikiart'):
    global FETCH_NEXT
    if FETCH_STOP.is_set():raise RuntimeError('Source paused after HTTP 403/429')
    if not (r.RUN/tag/(r.sha(url.encode())+'.receipt.json')).exists():
        with FETCH_LOCK:
            slot=max(time.monotonic(),FETCH_NEXT)
            FETCH_NEXT=slot+.4
        time.sleep(max(0,slot-time.monotonic()))
    raw,rc=r.capture(url,tag=tag,timeout=35)
    if rc['status'] in (403,429):
        FETCH_STOP.set()
        raise RuntimeError('Source paused after HTTP '+str(rc['status']))
    return raw,rc


def search():
    rows=r.load(r.RUN/'production-artworks.json.gz')
    titles={norm(x['artwork']['title']):x['artwork']['title'] for x in rows}
    def one(pair):
        key,title=pair
        dest=r.RUN/'search-results'/(r.sha(key.encode())+'.json')
        if dest.exists():
            previous=r.load(dest)
            if previous['outcome']=='searched':return previous
            dest=r.RUN/'search-retries'/(r.sha(key.encode())+'.json')
            if dest.exists():return r.load(dest)
        search_title=' '.join(re.sub(r"[^\w\s'’-]",' ',title).split())
        url='https://www.wikiart.org/fr/search/'+quote(search_title,safe='')+'?json=2'
        try:
            raw,rc=capture(url,'wikiart-search')
            d=json.loads(raw) if rc['status']==200 else {}
            assert isinstance(d,dict), 'Unexpected search response'
            result={'query':title,'search_title':search_title,'normalized_query':key,'receipt':rc,
              'paintings':d.get('Paintings',[]),'pagination':{k:v for k,v in d.items() if k not in ('Paintings','ArtistsHtml')},
              'outcome':'searched' if rc['status']==200 else 'http_error'}
        except (r.requests.RequestException,ValueError,AssertionError) as e:
            result={'query':title,'normalized_query':key,'outcome':'request_error','error':str(e)[:250],'paintings':[]}
        r.save(dest,result)
        return result
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for value in pool.map(one, sorted(titles.items())):
            counts['queries']+=1
            counts[value['outcome']]+=1
            counts['queries_with_results']+=bool(value['paintings'])
            if counts['queries']%50==0:print('WikiArt title search',dict(counts),'of',len(titles),flush=True)
    r.save(r.RUN/'search-summary.json',dict(counts))
    print('Search complete',dict(counts),flush=True)


def namekey(value):
    value=re.sub(r'\([^)]*\)', '', value or '')
    return ' '.join(sorted(x for x in norm(value).split() if x not in {'dit','baron','comte','sir'}))


def object_labels():
    labels=collections.defaultdict(list)
    for path in (r.RUN/'object-labels').glob('*.json'):
        data=r.load(path)
        for x in data['rows']:labels[x['joconde']].append({**x,'receipt':data['receipt']})
    return labels


def row_labels(row,labels):
    return [x for c in row['citations'] if 'pop.culture.gouv.fr/notice/joconde/' in (c.get('source_url')or'') for x in labels[c['source_record_id']]]


def load_artist_plan():
    path=r.RUN/'artist-search-plan-v2.json'
    return r.load(path if path.exists() else r.RUN/'artist-search-plan.json')


def artist_plan():
    rows=r.load(r.RUN/'production-artworks.json.gz')
    prev=ROOT/'docs/research/wikiart-artist-coverage-20260920'
    source=r.load(prev/'artist-matches.json')
    pairs=source['matches']+source['ambiguous']
    extra=prev/'extra-artist-matches.json'
    if extra.exists():pairs+=r.load(extra)['matches']
    wiki={x['wikiart']['url']:x['wikiart'] for x in pairs}
    wiki.update({x['url']:x for x in source['unmatched_source_artists']})
    names=collections.defaultdict(set)
    ids=collections.defaultdict(set)
    for url,x in wiki.items():names[namekey(x['name'])].add(url)
    for pair in pairs:
        if not pair.get('artist'):continue
        a=pair['artist'];url=pair['wikiart']['url'];ids[a['id']].add(url)
        for name in [a.get('display_name')]+(a.get('aliases')or[]):
            if name:names[namekey(name)].add(url)
    tokens={url:set(namekey(x['name']).split())-{'de','van','der','le','la','von','di','da','du','d'} for url,x in wiki.items()}
    labels_by_object=object_labels()
    plan=[]
    for row in rows:
        labels=[a['name'] for a in row['artists']]
        for a in row['artists']:labels+=a.get('aliases')or[]
        if row['artwork']['unlinked_creator_label']:labels.append(row['artwork']['unlinked_creator_label'])
        supplied_labels=list(labels)
        labels+=sorted({x['creatorName'] for x in row_labels(row,labels_by_object) if x.get('creatorName')})
        matches=set()
        for a in row['artists']:matches.update(ids[a['id']])
        for label in labels:matches.update(names[namekey(label)])
        basis='established_artist_or_exact_name'
        if not matches:
            for label in labels:
                ts=set(namekey(label).split())-{'de','van','der','le','la','von','di','da','du','d'}
                if len(ts)<2:continue
                possible={url for url,tt in tokens.items() if len(tt)>=2 and (ts<=tt or tt<=ts) and len(ts&tt)/max(len(ts),len(tt))>=.5}
                if len(possible)==1:matches.update(possible)
            basis='name_variant_candidate'
        plan.append({'artwork_id':row['artwork']['id'],'labels':labels,'supplied_labels':supplied_labels,'artist_urls':sorted(matches),'basis':basis})
    path=r.RUN/('artist-search-plan-v2.json' if labels_by_object else 'artist-search-plan.json')
    r.save(path,{'records':plan,'artists':wiki})
    print('Artist scope',len({u for p in plan for u in p['artist_urls']}),'artists for',sum(bool(p['artist_urls']) for p in plan),'records',flush=True)


def indexes():
    from bs4 import BeautifulSoup
    plan=load_artist_plan()
    urls=sorted({u for x in plan['records'] for u in x['artist_urls']})
    def one(url):
        dest=r.RUN/'artist-indexes'/(r.sha(url.encode())+'.json')
        if dest.exists():return r.load(dest)
        target=url.replace('/en/','/fr/')+'/all-works/text-list'
        raw,rc=capture(target,'wikiart-indexes');soup=BeautifulSoup(raw,'html.parser')
        prefix=urlparse(target).path.removesuffix('/all-works/text-list')+'/'
        works=[]
        for a in soup.select('li a[href]'):
            if not a['href'].startswith(prefix):continue
            title=a.get_text(' ',strip=True)
            works.append({'title':title,'year':a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,'),
              'paintingUrl':a['href'],'artistUrl':prefix.rstrip('/'),'artistName':plan['artists'][url]['name']})
        value={'artist_url':url,'receipt':rc,'works':works}
        r.save(dest,value);return value
    total=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,value in enumerate(pool.map(one,urls),1):
            total+=len(value['works'])
            if i%20==0:print('Artist indexes',i,'of',len(urls),'metadata entries',total,flush=True)
    print('Artist indexes complete',len(urls),total,flush=True)


def similarity(a,b):
    a,b=norm(a),norm(b)
    if not a or not b:return 0
    if a==b:return 1
    stop={'le','la','les','de','des','du','d','l','et','un','une','the','of','a','and','dit','aussi','ou'}
    aa=set(a.split())-stop;bb=set(b.split())-stop
    if not aa or not bb:return 0
    return max(difflib.SequenceMatcher(None,a,b).ratio(), len(aa&bb)/len(aa|bb))


def candidates():
    rows=r.load(r.RUN/'production-artworks.json.gz')
    plan={p['artwork_id']:p for p in load_artist_plan()['records']}
    labels_by_object=object_labels()
    indexes={d['artist_url']:d for p in (r.RUN/'artist-indexes').glob('*.json') for d in [r.load(p)]}
    cross=collections.defaultdict(list)
    for folder in ['identifier-crosswalk','ark-crosswalk']:
        for path in (r.RUN/folder).glob('*.json'):
            data=r.load(path)
            for x in data['rows']:
                for key in ['joconde','ark']:
                    if x.get(key):cross[(key,x[key])].append({**x,'receipt':data['receipt']})
    records=[]
    for row in rows:
        w=row['artwork'];p=plan[w['id']];found={}
        def add(source,basis,score,rc=None,extra=None):
            path=source.get('paintingUrl') or ''
            if not path:return
            path=re.sub(r'^/(fr|ru|de|es|pt|uk|zh)/','/en/',path)
            # Prefer the observed French page where the title was found; English
            # normalization is only a duplicate key, never an invented source URL.
            key=path
            url=urljoin('https://www.wikiart.org',source['paintingUrl'])
            candidate={'url':url,'source':source,'basis':basis,'title_score':round(score,4),'receipt':rc,**(extra or {})}
            strength={'identifier_crosswalk':5,'exact_artist_title':4,'search_same_artist':3,'similar_artist_title':2}
            if key not in found or (strength[basis],score)>(strength[found[key]['basis']],found[key]['title_score']):found[key]=candidate
        for c in row['citations']:
            keys=[]
            if 'pop.culture.gouv.fr/notice/joconde/' in (c.get('source_url')or''):keys.append(('joconde',c['source_record_id']))
            m=re.search(r'/ark:/53355/cl(\d+)',c.get('source_url')or'')
            if m:keys.append(('ark',m[1]))
            for key in keys:
                for x in cross[key]:
                    add({'paintingUrl':'/en/'+x['wikiart'],'title':x.get('en'),'artistName':None},'identifier_crosswalk',1,x['receipt'],{'crosswalk':{k:v for k,v in x.items() if k!='receipt'}})
        titles=[w['title'],w.get('alternate_title')]
        titles += [x.strip() for x in re.split(r';|,?\s+(?:dit aussi|dit|dite|dite aussi)\s+',w['title'],flags=re.I) if len(x.strip())>8]
        labels=row_labels(row,labels_by_object)
        titles+=sorted({x[k] for x in labels for k in ('en','fr') if x.get(k)})
        searches=[]
        key=r.sha(norm(w['title']).encode())
        for folder in ['search-short-retries','search-final-retries','search-retries','search-results']:
            path=r.RUN/folder/(key+'.json')
            if path.exists():searches.append(r.load(path));break
        extra_path=r.RUN/'supplemental-searches'/(w['id']+'.json')
        if extra_path.exists():searches+=r.load(extra_path)['searches']
        expected={urlparse(u).path.rsplit('/',1)[-1] for u in p['artist_urls']}
        for search in searches:
            for s in search['paintings'] or []:
                slug=(s.get('artistUrl')or'').rsplit('/',1)[-1]
                artist_ok=slug in expected or any(namekey(s.get('artistName'))==namekey(label) for label in p['labels'])
                if not artist_ok:continue
                score=max(similarity(t,s.get('title')) for t in titles if t)
                basis='exact_artist_title' if score>=.97 else 'search_same_artist'
                add(s,basis,score,search.get('receipt'))
        for url in p['artist_urls']:
            index=indexes.get(url)
            if not index:continue
            options=[]
            for s in index['works']:
                score=max(similarity(t,s.get('title')) for t in titles if t)
                if score>=.68:options.append((score,s))
            for score,s in sorted(options,key=lambda z:-z[0])[:3]:
                add(s,'exact_artist_title' if score>=.97 else 'similar_artist_title',score,index['receipt'])
        strength={'identifier_crosswalk':5,'exact_artist_title':4,'search_same_artist':3,'similar_artist_title':2}
        options=sorted(found.values(),key=lambda x:(-strength[x['basis']],-x['title_score'],x['url']))
        records.append({'artwork_id':w['id'],'title':w['title'],'creator_labels':p.get('supplied_labels',p['labels']),
          'sourced_title_variants':sorted({t for t in titles if t}),'label_evidence':labels,
          'artist_match_basis':p['basis'],'candidates':options[:6], 'candidate_count_before_limit':len(options),
          'searches':[{'query':s['query'],'outcome':s['outcome'],'receipt':s.get('receipt'),'pagination':s.get('pagination')} for s in searches]})
    return records


def page(url):
    from bs4 import BeautifulSoup
    dest=r.RUN/'artwork-pages'/(r.sha(url.encode())+'.json')
    if dest.exists():return r.load(dest)
    raw,rc=capture(url,'wikiart-pages')
    result={'url':url,'receipt':rc,'outcome':'page_unavailable'}
    if rc['status']==200:
        soup=BeautifulSoup(raw,'html.parser')
        tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
        if tag:
            metadata=json.loads(tag['ng-init'].split('=',1)[1].strip())
            copyright=soup.select_one('.copyright-wrapper .copyright')
            image=soup.select_one('img[itemprop="image"]')
            article=soup.select_one('.wiki-layout-artwork-info article')
            info=[]
            if article:
                for li in article.select('li'):
                    text=li.get_text(' ',strip=True)
                    if len(text)<1000:info.append(text)
            result.update(outcome='image_found' if image else 'no_image',metadata=metadata,
              image_url=metadata.get('image') or (image.get('src') if image else None),
              displayed_image_url=image.get('src') if image else None,
              rights_label=copyright.get_text(' ',strip=True) if copyright else None,
              public_domain_label=bool(copyright and copyright.select_one('.copyright-icon-public-domain')),
              object_info=info)
    r.save(dest,result)
    return result


def pages():
    records=candidates()
    urls=sorted({x['url'] for p in records for x in p['candidates']})
    digest=r.sha(json.dumps(records,sort_keys=True,ensure_ascii=False).encode())[:12]
    r.save(r.RUN/'candidate-plans'/('plan-'+digest+'.json'),records)
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i,result in enumerate(pool.map(page,urls),1):
            counts[result['outcome']]+=1
            if i%25==0:print('Candidate image pages',i,'of',len(urls),dict(counts),flush=True)
    print('Candidate pages complete',len(urls),dict(counts),flush=True)


def supplement():
    records=candidates();plan={x['artwork_id']:x for x in load_artist_plan()['records']}
    todo=[x for x in records if not x['candidates'] and plan[x['artwork_id']]['artist_urls']]
    def one(record):
        dest=r.RUN/'supplemental-searches'/(record['artwork_id']+'.json')
        if dest.exists():return r.load(dest)
        variants=sorted({x['en'] for x in record['label_evidence'] if x.get('en') and norm(x['en'])!=norm(record['title'])},key=len)
        short=re.split(r';|,?\s+(?:dit aussi|dit|dite|dite aussi)\s+',record['title'],flags=re.I)[0].strip()
        if len(short)>8 and norm(short)!=norm(record['title']):variants.append(short)
        searches=[]
        for title in variants[:2]:
            title=' '.join(re.sub(r"[^\w\s'’-]",' ',title).split())
            url='https://www.wikiart.org/en/search/'+quote(title,safe='')+'?json=2'
            raw,rc=capture(url,'wikiart-supplemental-search')
            data=json.loads(raw) if rc['status']==200 else {}
            searches.append({'query':title,'receipt':rc,'outcome':'searched' if rc['status']==200 else 'http_error',
              'paintings':data.get('Paintings')or[],'pagination':{k:v for k,v in data.items() if k not in ('Paintings','ArtistsHtml')}})
        value={'artwork_id':record['artwork_id'],'searches':searches}
        r.save(dest,value);return value
    total=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i,value in enumerate(pool.map(one,todo),1):
            total+=len(value['searches'])
            if i%50==0:print('Alternate-title search',i,'of',len(todo),'queries',total,flush=True)
    print('Supplement complete',len(todo),total,flush=True)


def date_range(value):
    match=re.fullmatch(r'(?:c\.|ca\.|vers)?\s*(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?',str(value or ''),re.I)
    return (int(match[1]),int(match[2]or match[1])) if match else None


def results():
    inventory={x['artwork']['id']:x for x in r.load(r.RUN/'production-artworks.json.gz')}
    records=candidates()
    quality={'identifier_match':6,'title_artist_location_match':5,'title_artist_match':4,
      'possible_match':3,'conflicting_source_metadata':2,'source_unavailable':1}
    for record in records:
        row=inventory[record['artwork_id']];work=row['artwork']
        record.update(existing_image=bool(work['primary_media_id']),catalogue_status=work['status'],
          catalogue_date_start=work['creation_year_start'],catalogue_date_end=work['creation_year_end'],
          slug=work['slug'],catalogue_image_path=(row['media']or{}).get('storage_path'))
        for candidate in record['candidates']:
            path=r.RUN/'artwork-pages'/(r.sha(candidate['url'].encode())+'.json')
            candidate.update(classification='source_unavailable',review_flags=[])
            if not path.exists():candidate['review_flags'].append('Candidate page not yet checked');continue
            detail=r.load(path)
            candidate.update(page_evidence=str(path.relative_to(ROOT)),page_status=detail['receipt']['status'])
            if detail['outcome']!='image_found':candidate['review_flags'].append('Source page did not expose an artwork image');continue
            metadata=detail['metadata'];location=next((x.split(':',1)[1].strip() for x in detail['object_info'] if x.startswith(('Location:','Lieu:'))),None)
            candidate.update(source_title=html.unescape(metadata['title']),source_artist=html.unescape(metadata.get('artistName')or''),
              source_date=metadata.get('year'),source_id=metadata.get('_id'),image_url=detail['image_url'],
              image_width=metadata.get('width'),image_height=metadata.get('height'),source_location=location,
              source_rights_label=detail['rights_label'],source_public_domain_label=detail['public_domain_label'],
              checked_at=detail['receipt']['retrieved_at'])
            flags=candidate['review_flags'];conflicts=[]
            source=candidate.get('source')or{}
            source_id=source.get('id')or source.get('_id')
            if source_id and source_id!=metadata.get('_id'):conflicts.append('WikiArt object identifier changed between discovery and page')
            requested_artist=urlparse(candidate['url']).path.split('/')[-2]
            actual_artist=(metadata.get('artistUrl')or'').rstrip('/').rsplit('/',1)[-1]
            if actual_artist and requested_artist!=actual_artist:conflicts.append('WikiArt page creator differs from the requested artist')
            qualified=any(a.get('role')not in ('primary',None) for a in row['artists']) or any(re.search(r"\b(?:atelier|attribu|suiveur|copie|après|after|workshop|follower)\w*\b",name,re.I) for name in record['creator_labels'])
            if qualified:flags.append('Qualified catalogue creator attribution needs review')
            years=date_range(metadata.get('year'))
            if work['creation_year_start'] is None or work['creation_year_end'] is None:flags.append('Catalogue creation date incomplete')
            if not years:flags.append('WikiArt creation date incomplete')
            elif work['creation_year_start'] is not None and work['creation_year_end'] is not None and (years[0]>work['creation_year_end'] or years[1]<work['creation_year_start']):conflicts.append('Catalogue and WikiArt creation dates differ')
            if years and years[1]>1970:conflicts.append('WikiArt date exceeds the 1970 catalogue cutoff')
            louvre=bool(location and 'louvre' in location.lower())
            if location and not louvre:conflicts.append('WikiArt names another location; requires object/version review')
            if not location:flags.append('WikiArt does not state the Louvre location')
            partial=r'\b(?:detail|détail|study|étude|sketch|esquisse|copy|copie)\b'
            if re.search(partial,candidate['source_title'],re.I) and not any(re.search(partial,t,re.I) for t in record['sourced_title_variants']):conflicts.append('Source may be a detail, study or copy')
            if record['artist_match_basis']=='name_variant_candidate' and candidate['basis']!='identifier_crosswalk':flags.append('Creator name variant needs review')
            if not detail['public_domain_label']:flags.append('Source reproduction rights require review')
            score=max(similarity(t,candidate['source_title']) for t in record['sourced_title_variants'])
            for info in detail['object_info']:
                if info.startswith(('Titre original:','Original Title:')):
                    score=max(score,max(similarity(t,info.split(':',1)[1]) for t in record['sourced_title_variants']))
            candidate['page_title_score']=round(score,4)
            if conflicts:
                candidate['classification']='conflicting_source_metadata';flags.extend(conflicts)
            elif candidate['basis']=='identifier_crosswalk':candidate['classification']='identifier_match'
            elif score>=.97 and louvre and record['artist_match_basis']!='name_variant_candidate':candidate['classification']='title_artist_location_match'
            elif score>=.97 and years and work['creation_year_start'] is not None and record['artist_match_basis']!='name_variant_candidate':candidate['classification']='title_artist_match'
            else:candidate['classification']='possible_match'
            if ';' in record['title'] and similarity(record['title'],candidate['source_title'])<.9 and candidate['basis']!='identifier_crosswalk':
                flags.append('Compound catalogue title: source may show only one component')
                if candidate['classification'] in ('title_artist_location_match','title_artist_match'):candidate['classification']='possible_match'
            if qualified and candidate['basis']!='identifier_crosswalk' and candidate['classification']in ('title_artist_location_match','title_artist_match'):candidate['classification']='possible_match'
            if candidate['classification']!='identifier_match':flags.append('Visual object identity review required before attachment')
        record['candidates'].sort(key=lambda x:(-quality[x['classification']],-x.get('page_title_score',x['title_score']),x['url']))
        best=record['candidates'][0] if record['candidates'] else None
        record['outcome']=best['classification'] if best else 'no_verified_match_found'
        if best:
            top=[x for x in record['candidates'] if quality[x['classification']]>=4]
            ids={x.get('source_id') for x in top}
            if len(ids)>1:
                record['outcome']='ambiguous_candidates'
                for x in top:x['review_flags'].append('Several WikiArt works fit this catalogue record')
        record['search_complete']=bool(record['searches']) and all(s['outcome']=='searched' for s in record['searches'])
    duplicates=collections.defaultdict(set)
    for record in records:
        if record['outcome'] in ('identifier_match','title_artist_location_match','title_artist_match'):
            duplicates[record['candidates'][0]['source_id']].add(record['artwork_id'])
    for record in records:
        if record['candidates']:
            ids=duplicates.get(record['candidates'][0].get('source_id'),set())
            if len(ids)>1:
                record['duplicate_catalogue_candidates']=sorted(ids-{record['artwork_id']})
                record['candidates'][0]['review_flags'].append('Same source image matches several catalogue records; duplicate review required')
    return records


def progress():
    records=results()
    summary={'records':len(records),'outcomes':dict(collections.Counter(x['outcome'] for x in records)),
      'with_source_image_candidates':sum(any(c.get('image_url') for c in x['candidates']) for x in records),
      'title_searches_complete':sum(x['search_complete']for x in records)}
    Path('/tmp/artline-louvre-wikiart-progress.json').write_text(json.dumps({'summary':summary,'records':records},ensure_ascii=False,default=str))
    print(json.dumps(summary),flush=True)


def retry_search():
    allrows={path.name:r.load(path) for path in (r.RUN/'search-results').glob('*.json')}
    allrows.update({path.name:r.load(path) for path in (r.RUN/'search-retries').glob('*.json')})
    for filename,previous in allrows.items():
        if previous['outcome']=='searched':continue
        dest=r.RUN/'search-final-retries'/filename
        shorten=False
        if dest.exists():
            if r.load(dest)['outcome']=='searched':continue
            dest=r.RUN/'search-short-retries'/filename;shorten=True
            if dest.exists():continue
        title=previous['query']
        query=title.split(';',1)[0] if len(title)>200 else title
        if shorten:query=' '.join(re.split(r'[;:.]',title,1)[0].split()[:9])[:90]
        query=' '.join(re.sub(r"[^\w\s'’-]",' ',query).split())
        url='https://www.wikiart.org/fr/search/'+quote(query,safe='')+'?json=2&layout=new'
        raw,rc=capture(url,'wikiart-final-retry')
        try:data=json.loads(raw) if rc['status']==200 else {}
        except ValueError:data={}
        value={'query':title,'search_title':query,'receipt':rc,'outcome':'searched' if rc['status']==200 and 'Paintings' in data else 'http_error',
          'paintings':data.get('Paintings')or[],'pagination':{k:v for k,v in data.items()if k not in ('Paintings','ArtistsHtml')}}
        r.save(dest,value);print('Search retry',value['outcome'],title[:80],flush=True)


def check_images():
    records=results()
    statuses={'identifier_match','title_artist_location_match','title_artist_match'}
    urls=sorted({x['candidates'][0]['image_url'] for x in records if x['outcome']in statuses})
    def one(url):
        dest=r.RUN/'image-url-checks'/(r.sha(url.encode())+'.json')
        if dest.exists():return r.load(dest)
        assert urlparse(url).scheme=='https' and re.fullmatch(r'uploads\d*\.wikiart\.org',urlparse(url).hostname or '')
        try:
            response=r.requests.head(url,headers={'User-Agent':r.UA},allow_redirects=True,timeout=(10,25))
            value={'url':url,'method':'HEAD','checked_at':r.now(),'status':response.status_code,
              'final_url':response.url,'content_type':response.headers.get('Content-Type'),
              'content_length':response.headers.get('Content-Length'),'binary_downloaded':False}
        except r.requests.RequestException as error:value={'url':url,'method':'HEAD','checked_at':r.now(),'error':str(error)[:250],'binary_downloaded':False}
        r.save(dest,value);return value
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        checks=list(pool.map(one,urls))
    print('Image URL checks',len(checks),dict(collections.Counter(x.get('status','error')for x in checks)),flush=True)


def report():
    records=results()
    assert len(records)==3286 and len({x['artwork_id']for x in records})==len(records)
    snapshot=r.load(r.RUN/'production-snapshot-summary.json')
    outcomes=dict(collections.Counter(x['outcome'] for x in records))
    matched={'identifier_match','title_artist_location_match','title_artist_match'}
    summary={'snapshot':snapshot,'completed_at':r.now(),'records':len(records),'outcomes':outcomes,
      'supported_image_matches':sum(x['outcome'] in matched for x in records),
      'supported_matches_without_existing_image':sum(x['outcome']in matched and not x['existing_image']for x in records),
      'records_with_any_image_candidate':sum(any(c.get('image_url')for c in x['candidates'])for x in records),
      'completed_title_searches_records':sum(x['search_complete']for x in records),
      'catalogue_duplicate_review_records':sum(bool(x.get('duplicate_catalogue_candidates'))for x in records),
      'database_mutations':0,'image_binary_downloads':0,'publication_changes':0,
      'limitations':['No verified match found means no match in this research, not proof that WikiArt has no image.',
        'WikiArt rights labels are source assertions, not independent reproduction clearance.',
        'Image candidates do not validate unknown dates, attributions, publication eligibility, museum holdings or current display.',
        'Title/artist matches need visual identity review before attachment. Existing images were preserved.']}
    checks={d['url']:d for path in (r.RUN/'image-url-checks').glob('*.json') for d in [r.load(path)]}
    summary['image_url_head_checks']=dict(collections.Counter(x.get('status','error')for x in checks.values()))
    for record in records:
        for candidate in record['candidates']:
            check=checks.get(candidate.get('image_url'))
            if check:candidate['image_url_check']=check
    r.save(r.RUN/'summary.json',summary)
    # A compact review export refers back to the immutable source evidence.
    for record in records:
        record['label_evidence']=[{k:v for k,v in x.items() if k!='receipt'} for x in record['label_evidence']]
        for candidate in record['candidates']:
            if candidate.get('receipt'):
                candidate['discovery_evidence']=candidate['receipt']['body_path']
                del candidate['receipt']
            candidate.pop('source',None)
        for search in record['searches']:
            if search.get('receipt'):
                search['url']=search['receipt']['url'];search['evidence']=search['receipt']['body_path'];del search['receipt']
    r.save(r.RUN/'artwork-image-results.json',records)
    r.save(r.RUN/'supported-image-matches.json',[x for x in records if x['outcome'] in matched])
    labels={'identifier_match':'Identifier cross-reference','title_artist_location_match':'Title, artist and Louvre match',
      'title_artist_match':'Title, artist and date match','possible_match':'Possible match — review',
      'ambiguous_candidates':'Several candidates — review','conflicting_source_metadata':'Conflicting metadata — review',
      'source_unavailable':'Source page unavailable','no_verified_match_found':'No verified match found'}
    ordering={k:i for i,k in enumerate(labels)}
    records.sort(key=lambda x:(ordering[x['outcome']],x['title'].casefold(),x['artwork_id']))
    esc=lambda x:html.escape(str(x or ''),quote=True)
    style='''body{font:16px/1.55 system-ui,sans-serif;margin:32px auto;max-width:1120px;padding:0 24px;color:#202830;background:#f7f7f4}h1{font-size:32px;margin-bottom:8px}h2{font-size:22px}a{color:#07558b}article{background:white;border:1px solid #d9dedc;border-radius:8px;padding:20px;margin:18px 0}small,.muted{color:#5d676b}.badge{font-weight:650;color:#215e56}ul{padding-left:22px}li{margin:5px 0}code{font-size:12px;overflow-wrap:anywhere}nav{display:flex;gap:20px;margin:24px 0}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px 14px;border-bottom:1px solid #ddd;text-align:left}summary{cursor:pointer;font-weight:600}.note{background:#edf2f0;padding:18px;border-left:4px solid #487b70}'''
    def document(title,body):return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+style+'</style><body>'+body+'</body></html>'
    pages_count=(len(records)+99)//100
    for number in range(pages_count):
        nav='<nav><a href="../report.html">Summary</a>'
        if number:nav+='<a href="page-'+str(number).zfill(2)+'.html">Previous 100</a>'
        if number+1<pages_count:nav+='<a href="page-'+str(number+2).zfill(2)+'.html">Next 100</a>'
        nav+='</nav>'
        body='<h1>Louvre · WikiArt image research</h1><p>Records '+str(number*100+1)+'–'+str(min((number+1)*100,len(records)))+' of '+str(len(records))+'. Sorted by match strength.</p>'+nav
        for x in records[number*100:(number+1)*100]:
            names=[]
            for name in x['creator_labels']:
                if norm(name) not in {norm(z)for z in names}:names.append(name)
            body+='<article id="'+x['artwork_id']+'"><div class="badge">'+esc(labels[x['outcome']])+'</div><h2>'+esc(x['title'])+'</h2><p>'+esc(' · '.join(names[:3]))+'</p><p class="muted">Production status: review · Existing image: '+('yes'if x['existing_image']else'no')+' · Catalogue date: '+esc(x['catalogue_date_start'])+'–'+esc(x['catalogue_date_end'])+'</p><code>'+esc(x['artwork_id'])+'</code>'
            if x['candidates']:
                body+='<ul>'
                for c in x['candidates']:
                    body+='<li><a href="'+esc(c['url'])+'">'+esc(c.get('source_title')or'WikiArt candidate')+'</a>'
                    if c.get('image_url'):body+=' · <a href="'+esc(c['image_url'])+'">Image URL</a>'
                    body+='<br><small>'+esc(' · '.join(str(y)for y in [c.get('source_artist'),c.get('source_date'),c.get('source_location'),c.get('source_rights_label')]if y))+'</small>'
                    if c['review_flags']:body+='<br><small>'+esc('; '.join(c['review_flags']))+'</small>'
                    body+='</li>'
                body+='</ul>'
            else:body+='<p>No verified candidate found in this search.</p>'
            body+='<details><summary>Search evidence</summary><ul>'
            for s in x['searches']:
                url=s.get('url')
                body+='<li>'+('<a href="'+esc(url)+'">'+esc(s['query'])+'</a>' if url else esc(s['query']))+' — '+esc(s['outcome'])+'</li>'
            body+='</ul></details></article>'
        r.save(r.RUN/'review'/('page-'+str(number+1).zfill(2)+'.html'),document('Louvre image research · '+str(number+1),body+nav).encode())
    body='<h1>Louvre · WikiArt image research</h1><p>Production catalogue snapshot: '+esc(snapshot['at'])+'. Research completed: '+esc(summary['completed_at'])+'.</p>'
    body+='<div class="note"><strong>'+str(len(records))+' artworks queried in production. '+str(summary['supported_image_matches'])+' supported image matches; '+str(summary['supported_matches_without_existing_image'])+' currently lack an attached image.</strong><br>All records remain in review. No database writes, image downloads, uploads or publication changes.</div>'
    body+='<h2>Results</h2><table><tr><th>Outcome</th><th>Artworks</th></tr>'
    for key in labels:body+='<tr><td>'+esc(labels[key])+'</td><td>'+str(outcomes.get(key,0))+'</td></tr>'
    body+='</table><p><a href="review/page-01.html">Browse the artwork results, 100 per page</a> · <a href="artwork-image-results.json">All results (JSON)</a> · <a href="supported-image-matches.json">Supported matches (JSON)</a></p>'
    body+='<h2>Method and limits</h2><p>Read-only, institution-scoped production query; title searches for all distinct catalogue titles; selected artist artwork lists; exact Joconde/Louvre identifiers for alternate titles and WikiArt cross-references; candidate page inspection for actual image URLs. Source responses and checksums are retained beside this report.</p><ul>'
    for limit in summary['limitations']:body+='<li>'+esc(limit)+'</li>'
    body+='</ul><p>'+str(summary['catalogue_duplicate_review_records'])+' matched records share a WikiArt object with another catalogue record and need duplicate review. '+str(len(records)-summary['completed_title_searches_records'])+' records have an incomplete or failed title-search request; their other evidence remains available.</p>'
    r.save(r.RUN/'report.html',document('Louvre · WikiArt image research',body).encode())
    print(json.dumps(summary,ensure_ascii=False),flush=True)


def verify():
    from bs4 import BeautifulSoup
    inventory={x['artwork']['id']:x['artwork'] for x in r.load(r.RUN/'production-artworks.json.gz')}
    records=r.load(r.RUN/'artwork-image-results.json');summary=r.load(r.RUN/'summary.json')
    assert set(inventory)=={x['artwork_id']for x in records}
    assert len(records)==len(inventory)==sum(summary['outcomes'].values())
    assert sum(x['existing_image']for x in records)==33
    for x in records:
        w=inventory[x['artwork_id']]
        assert x['catalogue_status']==w['status']=='review'
        assert (x['catalogue_date_start'],x['catalogue_date_end'])==(w['creation_year_start'],w['creation_year_end'])
        assert x['searches'],x['artwork_id']
        for c in x['candidates']:
            if c.get('image_url'):
                assert re.fullmatch(r'uploads\d*\.wikiart\.org',urlparse(c['image_url']).hostname or '')
                page=r.load(ROOT/c['page_evidence'])
                assert c['source_id']==page['metadata']['_id']
                assert c['image_url']==page['image_url']
    checked=0
    for path in r.RUN.glob('*/*.receipt.json'):
        rc=r.load(path);raw=gzip.decompress((ROOT/rc['body_path']).read_bytes())
        assert r.sha(raw)==rc['sha256'],path
        checked+=1
    seen=[];pages=[r.RUN/'report.html']+sorted((r.RUN/'review').glob('*.html'))
    for path in pages:
        soup=BeautifulSoup(path.read_text(),'html.parser')
        assert not soup.select('img,script,iframe')
        assert soup.select_one('h1')
        seen.extend(x['id']for x in soup.select('article[id]'))
        assert len(soup.select('article'))<=100
        for a in soup.select('a[href]'):
            href=a['href']
            if not urlparse(href).scheme:assert (path.parent/href).exists(),href
    assert len(seen)==len(set(seen))==len(records) and set(seen)==set(inventory)
    result={'at':r.now(),'catalogue_records_accounted_for':len(records),'source_checksums_verified':checked,
      'html_pages_checked':len(pages),'broken_local_links':0,'automatic_image_downloads':0,
      'preserved_catalogue_statuses_and_dates':True,'database_writes':0}
    r.save(r.RUN/'verification.json',result)
    print(json.dumps(result),flush=True)


def snapshot():
    dest = r.RUN / 'production-artworks.json.gz'
    if dest.exists():
        print('Preserving existing production snapshot', flush=True)
        return
    rows = []
    with r.connect('production') as db:
        assert db.execute('SHOW default_transaction_read_only').fetchone()['default_transaction_read_only'] == 'on'
        institutions = db.execute("SELECT to_jsonb(i) institution FROM institutions i WHERE slug='musee-du-louvre' OR name ILIKE '%louvre%' ORDER BY slug").fetchall()
        r.save(r.RUN / 'production-institutions.json', institutions)
        main = [x['institution'] for x in institutions if x['institution']['slug'] == 'musee-du-louvre']
        assert len(main) == 1
        institution_id = main[0]['id']
        query = '''SELECT to_jsonb(a) artwork,
          COALESCE((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
          COALESCE((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
          COALESCE((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role,
            'aliases',(SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=ar.id),
            'identifiers',(SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=ar.id)))
            FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists,
          (SELECT to_jsonb(m) FROM media_assets m WHERE m.id=a.primary_media_id) media
          FROM artworks a WHERE a.current_institution_id=%s::uuid AND (%s::uuid IS NULL OR a.id>%s::uuid)
          ORDER BY a.id LIMIT 250'''
        r.save(r.RUN / 'production-query-plan.json', db.execute('EXPLAIN (FORMAT JSON) '+query, (institution_id, None, None)).fetchone())
        cursor = None
        while True:
            batch = db.execute(query, (institution_id, cursor, cursor)).fetchall()
            if not batch:
                break
            rows.extend(batch)
            cursor = batch[-1]['artwork']['id']
            print('Production Louvre records', len(rows), flush=True)
    r.save_gz(dest, rows)
    summary = {'at':r.now(), 'target':'production', 'read_only':True,
      'institution':main[0]['name'], 'records':len(rows),
      'with_image':sum(bool(x['artwork']['primary_media_id']) for x in rows),
      'status_counts':dict(collections.Counter(x['artwork']['status'] for x in rows)),
      'work_types':dict(collections.Counter(x['artwork']['work_type'] for x in rows))}
    r.save(r.RUN / 'production-snapshot-summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def crosswalk():
    query = '''SELECT ?item ?wikiart ?joconde ?ark ?creator ?en ?fr WHERE {
      ?item wdt:P195 wd:Q19675; wdt:P6002 ?wikiart .
      OPTIONAL {?item wdt:P347 ?joconde}
      OPTIONAL {?item wdt:P9394 ?ark}
      OPTIONAL {?item wdt:P170 ?creator}
      OPTIONAL {?item rdfs:label ?en FILTER(LANG(?en)="en")}
      OPTIONAL {?item rdfs:label ?fr FILTER(LANG(?fr)="fr")}
    }'''
    raw, receipt = r.capture('https://query.wikidata.org/sparql', {'query':query,'format':'json'},tag='wikidata-crosswalk',timeout=60)
    assert receipt['status'] == 200, receipt
    data = [{k:v['value'] for k,v in x.items()} for x in json.loads(raw)['results']['bindings']]
    r.save(r.RUN/'wikidata-louvre-wikiart.json', {'receipt':receipt, 'rows':data})
    print('WikiArt Louvre crosswalk rows',len(data), flush=True)


def crosswalk_ids():
    rows = r.load(r.RUN/'production-artworks.json.gz')
    ids=sorted({c['source_record_id'] for x in rows for c in x['citations'] if 'pop.culture.gouv.fr/notice/joconde/' in (c.get('source_url') or '')})
    for offset in range(0,len(ids),100):
        dest=r.RUN/'identifier-crosswalk'/f'{offset:04d}.json'
        if dest.exists():continue
        query = 'SELECT ?item ?wikiart ?joconde ?ark ?creator ?en ?fr WHERE { VALUES ?joconde { '+ ' '.join(json.dumps(x) for x in ids[offset:offset+100])+''' }
          ?item wdt:P347 ?joconde; wdt:P6002 ?wikiart .
          OPTIONAL {?item wdt:P9394 ?ark} OPTIONAL {?item wdt:P170 ?creator}
          OPTIONAL {?item rdfs:label ?en FILTER(LANG(?en)="en")}
          OPTIONAL {?item rdfs:label ?fr FILTER(LANG(?fr)="fr")} }'''
        raw,rc=r.capture('https://query.wikidata.org/sparql',{'query':query,'format':'json'},tag='wikidata-crosswalk',timeout=45)
        if rc['status'] != 200: print('Crosswalk HTTP',rc['status'],flush=True);break
        found=[{k:v['value'] for k,v in x.items()} for x in json.loads(raw)['results']['bindings']]
        r.save(dest,{'receipt':rc,'rows':found})
        print('Joconde crosswalk',offset,len(found),flush=True)
        time.sleep(.5)


def crosswalk_arks():
    rows=r.load(r.RUN/'production-artworks.json.gz')
    arks=sorted({m[1] for x in rows for c in x['citations'] for m in [re.search(r'/ark:/53355/cl(\d+)',c.get('source_url') or '')] if m})
    for offset in range(0,len(arks),100):
        dest=r.RUN/'ark-crosswalk'/f'{offset:04d}.json'
        if dest.exists():continue
        query='SELECT ?item ?wikiart ?joconde ?ark ?creator ?en ?fr WHERE { VALUES ?ark { '+ ' '.join(json.dumps(x) for x in arks[offset:offset+100])+''' }
          ?item wdt:P9394 ?ark; wdt:P6002 ?wikiart .
          OPTIONAL {?item wdt:P347 ?joconde} OPTIONAL {?item wdt:P170 ?creator}
          OPTIONAL {?item rdfs:label ?en FILTER(LANG(?en)="en")}
          OPTIONAL {?item rdfs:label ?fr FILTER(LANG(?fr)="fr")} }'''
        raw,rc=r.capture('https://query.wikidata.org/sparql',{'query':query,'format':'json'},tag='wikidata-crosswalk',timeout=45)
        if rc['status']!=200:print('Crosswalk HTTP',rc['status'],flush=True);break
        found=[{k:v['value'] for k,v in x.items()} for x in json.loads(raw)['results']['bindings']]
        r.save(dest,{'receipt':rc,'rows':found})
        print('Louvre ARK crosswalk',offset,len(found),'of',len(arks),flush=True)
        time.sleep(.5)


def labels():
    rows=r.load(r.RUN/'production-artworks.json.gz')
    ids=sorted({c['source_record_id'] for x in rows for c in x['citations'] if 'pop.culture.gouv.fr/notice/joconde/' in (c.get('source_url') or '')})
    for offset in range(0,len(ids),100):
        dest=r.RUN/'object-labels'/f'{offset:04d}.json'
        if dest.exists():continue
        query='SELECT ?item ?joconde ?creator ?en ?fr ?creatorName WHERE { VALUES ?joconde { '+ ' '.join(json.dumps(x) for x in ids[offset:offset+100])+''' }
          ?item wdt:P347 ?joconde . OPTIONAL {?item wdt:P170 ?creator. OPTIONAL {?creator rdfs:label ?creatorName FILTER(LANG(?creatorName)="en")}}
          OPTIONAL {?item rdfs:label ?en FILTER(LANG(?en)="en")}
          OPTIONAL {?item rdfs:label ?fr FILTER(LANG(?fr)="fr")} }'''
        raw,rc=r.capture('https://query.wikidata.org/sparql',{'query':query,'format':'json'},tag='wikidata-labels',timeout=45)
        if rc['status']!=200:print('Label crosswalk HTTP',rc['status'],flush=True);break
        found=[{k:v['value'] for k,v in x.items()} for x in json.loads(raw)['results']['bindings']]
        r.save(dest,{'receipt':rc,'rows':found})
        print('Object labels',offset,len(found),'of',len(ids),flush=True)
        time.sleep(.5)


def probe():
    from bs4 import BeautifulSoup
    urls = ['https://www.wikiart.org/fr/app/search/autocomplete/?term=Le%20printemps',
      'https://www.wikiart.org/fr/search/Le%20printemps/1?json=2',
      'https://www.wikiart.org/fr/search/Le%20printemps?json=2',
      'https://www.wikiart.org/en/search/Mona%20Lisa?json=2']
    for url in urls:
        raw, receipt = r.capture(url,tag='probe',timeout=40)
        print(url,receipt['status'],len(raw),flush=True)
        if raw.startswith(b'{') or raw.startswith(b'['):
            print(raw[:1500].decode(),flush=True)
        else:
            soup=BeautifulSoup(raw,'html.parser')
            print([(x.get('ng-init')or '')[:1000] for x in soup.select('[ng-init]') if any(s in x.get('ng-init','').lower() for s in ['search','filter'])][:5],flush=True)
            print([(x.get('href'),x.get_text(' ',strip=True)) for x in soup.select('li a[href]')][-8:],flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['snapshot','crosswalk','crosswalk_ids','crosswalk_arks','labels','probe','search','artist_plan','indexes','pages','supplement','progress','retry_search','check_images','report','verify'])
    args = p.parse_args()
    globals()[args.command]()
