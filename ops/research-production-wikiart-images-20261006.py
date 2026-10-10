#!/usr/bin/env python3
"""Research image identities for every production museum artwork except Louvre/Prado.

Snapshot/research are strictly read-only. Source metadata is captured without
image downloads. Production image application is a separate pinned operation.
"""
import argparse
import collections
import concurrent.futures
import gzip
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import time
import threading
import unicodedata
from urllib.parse import urlsplit, urljoin

from bs4 import BeautifulSoup
import requests

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/production-wikiart-images-20261006'
spec = importlib.util.spec_from_file_location('research', ROOT/'ops/research-artwork-locations-20261004.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
r.PORT = 55445
r.RUN = RUN
os.environ.setdefault('CLOUDSDK_CORE_ACCOUNT', 'vadim@alingva.com')


def norm(v):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', html.unescape(v or '')).casefold() if not unicodedata.combining(c))))


def title_keys(work):
    return {norm(work.get(k)) for k in ['title','alternate_title']} - {''}


def snapshot():
    if (RUN/'snapshot.json').exists():
        print('Preserving completed snapshot', flush=True)
        return
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'] == 'on'
        institutions = db.execute('SELECT to_jsonb(i) record FROM institutions i ORDER BY id').fetchall()
        institutions = [x['record'] for x in institutions]
        excluded = [x for x in institutions if re.search(r'louvre|prado', x['slug']+' '+x['name'], re.I) or x.get('wikidata_id') in ['Q19675','Q160112']]
        included = [x['id'] for x in institutions if x not in excluded]
        counts = db.execute("SELECT current_institution_id::text institution_id,count(*) works,count(primary_media_id) images FROM artworks WHERE status<>'archived' AND current_institution_id=ANY(%s::uuid[]) GROUP BY 1", (included,)).fetchall()
        artists = db.execute('''SELECT ar.id::text,ar.slug,ar.display_name,ar.birth_year,ar.death_year,ar.entity_type,
          COALESCE((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=ar.id),'[]') aliases,
          COALESCE((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'external_id',external_id,'url',canonical_url))
            FROM external_identifiers WHERE entity_type='artist' AND entity_id=ar.id),'[]') identifiers
          FROM artists ar ORDER BY ar.id''').fetchall()
        r.save_gz(RUN/'artists.json.gz', artists)
        r.save_gz(RUN/'institutions.json.gz', institutions)
        query = '''SELECT a.id::text,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,
          a.date_display,a.date_precision,a.work_type,a.status,a.accession_number,a.unlinked_creator_label,
          a.current_institution_id::text institution_id,a.primary_media_id::text,
          m.source_page_url existing_image_source,m.storage_path existing_image_path,
          m.delivery_url existing_delivery_url,m.rights_status existing_image_rights
          FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id
          WHERE a.status<>'archived' AND a.current_institution_id=ANY(%s::uuid[])
          AND (%s::uuid IS NULL OR a.id>%s::uuid) ORDER BY a.id LIMIT 2000'''
        r.save(RUN/'snapshot-query-plan.json', db.execute('EXPLAIN (FORMAT JSON) '+query, (included,None,None)).fetchone())
        cursor = None
        total = 0
        parts = []
        while True:
            rows = db.execute(query, (included,cursor,cursor)).fetchall()
            if not rows: break
            ids = [x['id'] for x in rows]
            creators = collections.defaultdict(list)
            identifiers = collections.defaultdict(list)
            citations = collections.defaultdict(list)
            for x in db.execute('SELECT artwork_id::text,artist_id::text,attribution_role role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id', (ids,)).fetchall():
                creators[x.pop('artwork_id')].append(x)
            for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (ids,)).fetchall():
                identifiers[x.pop('entity_id')].append(x)
            for x in db.execute("SELECT DISTINCT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND source_url LIKE 'https://www.wikiart.org/%%'", (ids,)).fetchall():
                citations[x.pop('entity_id')].append(x)
            for x in rows:
                x.update(creators=creators[x['id']], identifiers=identifiers[x['id']], wikiart_citations=citations[x['id']])
            path = RUN/'snapshot'/f'{len(parts):04d}.json.gz'
            r.save_gz(path,rows)
            parts.append({'path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes()),'rows':len(rows)})
            total += len(rows)
            cursor = rows[-1]['id']
            if total % 20000 == 0: print('Production snapshot',total,flush=True)
        assert total == sum(x['works'] for x in counts)
        summary = {'at':r.now(),'target':'production','read_only':True,'artworks':total,'museum_counts':counts,
            'excluded_institutions':excluded,'parts':parts,'scope':'All nonarchived artworks with a current institution, except Louvre and Prado aliases. No date or creator exclusions in research inventory.'}
        r.save(RUN/'snapshot.json', summary)
        print(json.dumps({'artworks':total,'institutions':len(counts),'images':sum(x['images'] for x in counts),'excluded':[x['name'] for x in excluded]}),flush=True)


def works():
    for part in r.load(RUN/'snapshot.json')['parts']:
        path=ROOT/part['path']
        assert r.sha(path.read_bytes())==part['sha256']
        yield from r.load(path)


def cache():
    """Index existing WikiArt image metadata, with original capture references."""
    by_url={}
    folders=[]
    for root in (ROOT/'docs/research').iterdir():
        if root.is_dir() and root != RUN and (root/'selected').is_dir(): folders.append(root)
    for root in folders:
        for path in (root/'selected').glob('*.json'):
            try:
                im=r.load(path)
                if not isinstance(im,dict):continue
                page=im.get('page') or im.get('source_page_url')
                image=im.get('source_image_url')
                if not page or urlsplit(page).hostname!='www.wikiart.org' or not image: continue
                metadata=im.get('source_metadata') or {}
                item={'url':page,'title':html.unescape(metadata.get('title') or im.get('title') or ''),
                    'artist':metadata.get('artistName') or im.get('artist'),
                    'artist_url':urljoin(page,metadata.get('artistUrl') or page.rsplit('/',1)[0]),
                    'source_id':im.get('source_id'),'image_url':image,
                    'year_start':im.get('source_year'),'year_end':im.get('source_year_end',im.get('source_year')),
                    'rights_status':im.get('rights_status'),'rights_label':im.get('source_rights_label'),
                    'receipt':im.get('page_receipt'),'evidence_path':str(path.relative_to(ROOT)),
                    'source_description':im.get('source_description','')}
                by_url.setdefault(page,item)
            except (ValueError,TypeError,KeyError):continue
        print('Cached image metadata',root.name,len(by_url),flush=True)
    r.save_gz(RUN/'cached-images.json.gz',list(by_url.values()))


FETCH_LOCK = threading.Lock()
FETCH_NEXT = 0.0
FETCH_STOP = threading.Event()


def capture(url, tag):
    global FETCH_NEXT
    if FETCH_STOP.is_set(): raise RuntimeError('Source paused after rate limit/access restriction')
    key=r.sha(url.encode())
    existing=RUN/tag/(key+'.receipt.json')
    if not existing.exists():
        with FETCH_LOCK:
            slot=max(FETCH_NEXT,time.monotonic())
            FETCH_NEXT=slot+0.45
        time.sleep(max(0,slot-time.monotonic()))
    raw,rc=r.capture(url,tag=tag,timeout=40)
    if rc['status'] in [403,429]:
        FETCH_STOP.set()
        raise RuntimeError('WikiArt returned HTTP '+str(rc['status']))
    return raw,rc


def artist_sources():
    directory=[]
    def letter(c):
        raw,rc=capture('https://www.wikiart.org/en/Alphabet/'+c+'/text-list','directory-captures')
        assert rc['status']==200
        soup=BeautifulSoup(raw,'html.parser')
        out=[]
        for li in soup.select('li'):
            a=li.find('a',recursive=False)
            spans=li.find_all('span',recursive=False)
            if not a or not re.fullmatch('/en/[^/]+',a.get('href','')) or not spans or not re.search(r'\d+ artworks',spans[-1].get_text()):continue
            lifespan=spans[0].get_text(' ',strip=True).strip(', ')
            dates=re.fullmatch(r'(\d{4})\s*-\s*(\d{4})',lifespan)
            out.append({'name':a.get_text(' ',strip=True),'url':urljoin(rc['final_url'],a['href']),
                'birth_year':int(dates[1]) if dates else None,'death_year':int(dates[2]) if dates else None,
                'count':int(re.search(r'\d+',spans[-1].get_text())[0]),'receipt':rc})
        return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for out in pool.map(letter,'abcdefghijklmnopqrstuvwxyz'):directory.extend(out)
    r.save_gz(RUN/'wikiart-directory.json.gz',directory)
    artists=r.load(RUN/'artists.json.gz')
    with r.connect('production') as db:
        linked=db.execute("""SELECT aa.artist_id::text,count(*) works,count(*) FILTER(WHERE a.primary_media_id IS NULL) gaps
          FROM institutions i JOIN artworks a ON a.current_institution_id=i.id JOIN artwork_artists aa ON aa.artwork_id=a.id
          WHERE a.status<>'archived' AND i.slug !~* 'louvre|prado' AND i.name !~* 'louvre|prado'
          AND COALESCE(i.wikidata_id,'') NOT IN ('Q19675','Q160112') GROUP BY aa.artist_id""").fetchall()
        unlinked=db.execute("""SELECT a.unlinked_creator_label,count(*) works,count(*) FILTER(WHERE a.primary_media_id IS NULL) gaps
          FROM institutions i JOIN artworks a ON a.current_institution_id=i.id
          WHERE a.status<>'archived' AND i.slug !~* 'louvre|prado' AND i.name !~* 'louvre|prado'
          AND COALESCE(i.wikidata_id,'') NOT IN ('Q19675','Q160112') AND a.unlinked_creator_label IS NOT NULL
          GROUP BY a.unlinked_creator_label""").fetchall()
    linked={x['artist_id']:x for x in linked}
    by_name=collections.defaultdict(dict)
    by_url={x['url']:x for x in directory}
    for s in directory:by_name[norm(s['name'])][s['url']]=s
    matches=[];unmatched=[];ambiguous=[]
    for a in artists:
        if a['id'] not in linked:continue
        sources={}
        for name in [a['display_name']]+a['aliases']:sources.update(by_name[norm(name)])
        for e in a['identifiers']:
            url=(e.get('url') or '').rstrip('/')
            if url in by_url:sources[url]=by_url[url]
        sources={u:s for u,s in sources.items() if all(a.get(k) is None or s.get(k) is None or a[k]==s[k] for k in ['birth_year','death_year'])}
        row={'artist':a,'scope':linked[a['id']]}
        if len(sources)==1:matches.append({**row,'source':next(iter(sources.values())),'basis':'exact artist name/alias or source identifier; no lifespan conflict'})
        elif sources:ambiguous.append({**row,'sources':list(sources)})
        else:unmatched.append(row)
    labels=[]
    for x in unlinked:
        candidates=by_name[norm(x['unlinked_creator_label'])]
        if len(candidates)==1:labels.append({**x,'source':next(iter(candidates.values())),'basis':'exact object-level creator label; requires attribution review'})
    r.save_gz(RUN/'artist-sources.json.gz',{'matches':matches,'unmatched':unmatched,'ambiguous':ambiguous,'object_labels':labels})
    print(json.dumps({'wikiart_artists':len(directory),'matched_catalogue_artists':len(matches),'unmatched_catalogue_artists':len(unmatched),'ambiguous':len(ambiguous),'object_labels':len(labels),'matched_artwork_links':sum(x['scope']['works'] for x in matches)}),flush=True)


def indexes():
    data=r.load(RUN/'artist-sources.json.gz')
    sources={x['source']['url']:x['source'] for x in data['matches']+data['object_labels']}
    def one(source):
        slug=urlsplit(source['url']).path.rsplit('/',1)[-1]
        dest=RUN/'artist-indexes'/(slug+'.json.gz')
        if dest.exists():return r.load(dest)
        url='https://www.wikiart.org/en/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
        result={'source':source,'api_url':url}
        try:
            raw,rc=capture(url,'artist-index-captures')
            result['receipt']=rc
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            items=json.loads(raw)
            if not isinstance(items,list):raise ValueError('Unexpected artist index shape')
            result.update(outcome='indexed',items=items)
        except Exception as exc:
            result.update(outcome='source_unavailable',error=str(exc)[:300],items=[])
        r.save_gz(dest,result)
        return result
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n,item in enumerate(pool.map(one,sources.values()),1):
            counts[item['outcome']]+=1
            counts['source_artworks']+=len(item['items'])
            if n%50==0:print('WikiArt artist indexes',n,'/',len(sources),dict(counts),flush=True)
    r.save(RUN/'indexes-summary.json',{'at':r.now(),'source_artists':len(sources),'counts':dict(counts)})


def translations():
    data=r.load(RUN/'artist-sources.json.gz')
    sources={x['source']['url']:x['source'] for x in data['matches']+data['object_labels']}
    artists={x['artist']['id']:x['source']['url'] for x in data['matches']}
    labels={norm(x['unlinked_creator_label']):x['source']['url'] for x in data['object_labels']}
    institutions={x['id']:x for x in r.load(RUN/'institutions.json.gz')}
    wanted=set()
    for w in works():
        urls={artists[c['artist_id']] for c in w['creators'] if c['artist_id'] in artists}
        if norm(w.get('unlinked_creator_label')) in labels:urls.add(labels[norm(w['unlinked_creator_label'])])
        langs=[]
        if re.search('[А-Яа-яЁё]',w['title']):langs.append('ru')
        if 'musée' in institutions[w['institution_id']]['name'].casefold():langs.append('fr')
        for url in urls:
            for lang in langs:wanted.add((url,lang))
    def one(pair):
        url,lang=pair;source=sources[url];slug=urlsplit(url).path.rsplit('/',1)[-1]
        dest=RUN/'translated-indexes'/(lang+'-'+slug+'.json.gz')
        if dest.exists():return r.load(dest)
        api='https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
        result={'source':source,'language':lang,'api_url':api}
        try:
            raw,rc=capture(api,'translated-index-captures');result['receipt']=rc
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            items=json.loads(raw)
            if not isinstance(items,list):raise ValueError('Unexpected response')
            result.update(outcome='indexed',items=items)
        except Exception as exc:result.update(outcome='source_unavailable',error=str(exc)[:300],items=[])
        r.save_gz(dest,result);return result
    print('Selected translated indexes',len(wanted),dict(collections.Counter(lang for _,lang in wanted)),flush=True)
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n,result in enumerate(pool.map(one,sorted(wanted)),1):
            counts[result['outcome']]+=1
            if n%50==0:print('Translated indexes',n,'/',len(wanted),dict(counts),flush=True)
    r.save(RUN/'translations-summary.json',{'at':r.now(),'selected':len(wanted),'counts':dict(counts)})


def image_key(url):
    return urlsplit(url or '').path.split('!',1)[0]


def parse_date(value):
    m=re.fullmatch(r'(?:c\.|ок\.)?\s*(\d{1,4})(?:\s*[-–]\s*(?:c\.|ок\.)?\s*(\d{1,4}))?',str(value or ''),re.I)
    if not m:return None
    start,end=int(m[1]),int(m[2] or m[1])
    return (start,end) if 0<start<=end else None


def date_compatible(work, date):
    start,end=work.get('creation_year_start'),work.get('creation_year_end')
    return bool(date and start is not None and end is not None and start<=end<=1970
        and work.get('date_precision') not in ['unknown','before','after','century']
        and date[1]<=1970 and max(start,date[0])<=min(end,date[1]))


def candidates():
    source_data=r.load(RUN/'artist-sources.json.gz')
    artist_sources={x['artist']['id']:x['source']['url'] for x in source_data['matches']}
    label_sources={norm(x['unlinked_creator_label']):x['source']['url'] for x in source_data['object_labels']}
    cached=r.load(RUN/'cached-images.json.gz')
    image_pages={image_key(x['image_url']):x for x in cached}
    title_index=collections.defaultdict(dict)
    url_index={x['url']:x for x in cached}
    for x in cached:
        item={**x,'date':(x['year_start'],x['year_end']) if x.get('year_start') and x.get('year_end') else None}
        title_index[(x['artist_url'],norm(x['title']))][image_key(x['image_url'])]=item
    indexed=set()
    paths=list((RUN/'artist-indexes').glob('*.json.gz'))+list((RUN/'translated-indexes').glob('*.json.gz'))
    english={}
    for path in paths:
        record=r.load(path)
        if record['outcome']!='indexed':continue
        indexed.add(record['source']['url'])
        for x in record['items']:
            key=image_key(x.get('image'))
            # Translation endpoints contain blank titles for untranslated works.
            # These must never match an absent catalogue alternate title.
            if not key or not norm(x.get('title')):continue
            old=image_pages.get(key,{})
            if not record.get('language'):english[(record['source']['url'],x['contentId'])]=x
            original=english.get((record['source']['url'],x['contentId']),{})
            # This URL is a discovery hint only; a page must verify it before use.
            filename=key.rsplit('/',1)[-1]
            page=old.get('url') or record['source']['url']+'/'+filename.rsplit('.',1)[0]
            item={'title':html.unescape(x.get('title') or ''),'artist':x.get('artistName'),
                'artist_url':record['source']['url'],'date':parse_date(x.get('yearAsString')),
                'image_url':x['image'],'url':page,'page_url_verified':bool(old),'content_id':x['contentId'],
                'api_receipt':record['receipt'],'source_id':old.get('source_id')}
            item.update(language=record.get('language','en'),english_title=html.unescape(original.get('title') or x.get('title') or ''))
            title_index[(item['artist_url'],norm(item['title']))][key]=item
    totals=collections.Counter();found=[];outcomes=[]
    parts=sorted((RUN/'snapshot').glob('*.json.gz'))
    for path in parts:
        for w in r.load(path):
            sources={artist_sources[c['artist_id']] for c in w['creators'] if c['artist_id'] in artist_sources}
            if norm(w.get('unlinked_creator_label')) in label_sources:sources.add(label_sources[norm(w['unlinked_creator_label'])])
            possible={}
            for source in sources:
                for title in title_keys(w):
                    possible.update(title_index[(source,title)])
            direct={}
            for e in w['identifiers']+w['wikiart_citations']:
                url=e.get('url') or e.get('source_url')
                if url in url_index:
                    x=url_index[url]
                    direct[image_key(x['image_url'])]={**x,'date':(x['year_start'],x['year_end']) if x.get('year_start') and x.get('year_end') else None,'direct_identity':True}
            possible.update(direct)
            compatible={k:x for k,x in possible.items() if date_compatible(w,x['date'])}
            outcome='no_exact_title_match' if sources else 'artist_identity_unresolved'
            if sources and not sources.issubset(indexed):outcome='artist_index_pending'
            if possible and not compatible:outcome='date_review_or_conflict'
            if len(compatible)>1:outcome='multiple_source_versions'
            if len(compatible)==1:
                outcome='candidate_found'
                found.append({'work':w,'candidate':next(iter(compatible.values())),'candidate_count':len(possible),
                    'creator_basis':'linked_primary' if len(w['creators'])==1 and w['creators'][0]['role']=='primary' else 'object_label_or_qualified_attribution'})
            totals[outcome]+=1
            totals['with_existing_image' if w['primary_media_id'] else 'missing_image']+=1
            outcomes.append({'artwork_id':w['id'],'institution_id':w['institution_id'],'title':w['title'],
                'has_image':bool(w['primary_media_id']),'outcome':outcome,'possible_candidates':len(possible),'date_compatible_candidates':len(compatible),
                'candidate_images':[{'title':x['title'],'date':x.get('date'),'image_url':x['image_url'],
                    'source_metadata_url':(x.get('api_receipt') or x.get('receipt') or {}).get('url'),
                    'page_hint':x['url'],'page_hint_requires_verification':not x.get('page_url_verified',False)}
                    for x in list((compatible or possible).values())[:12]],
                'additional_candidates_in_artist_index':max(0,len(compatible or possible)-12)})
    counts=collections.Counter(image_key(x['candidate']['image_url']) for x in found if not x['work']['primary_media_id'])
    for x in found:x['missing_target_count']=counts[image_key(x['candidate']['image_url'])]
    label=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    dest=RUN/'candidate-passes'/(label+'.json.gz')
    data={'at':r.now(),'snapshot_complete':(RUN/'snapshot.json').exists(),'indexes_complete':(RUN/'indexes-summary.json').exists(),
        'indexed_artists':len(indexed),'counts':dict(totals),'candidates':found,'outcomes':outcomes}
    r.save_gz(dest,data)
    (RUN/'latest-candidate-pass.json').write_text(json.dumps({'path':str(dest.relative_to(ROOT)),'sha256':r.sha(dest.read_bytes())}))
    print(json.dumps({'path':str(dest.relative_to(ROOT)),'counts':dict(totals),'candidate_images':len(found),
        'missing_candidates':sum(not x['work']['primary_media_id'] for x in found),
        'unique_missing_candidates':sum(not x['work']['primary_media_id'] and x['missing_target_count']==1 for x in found)}),flush=True)


def candidate_pass():
    pointer=r.load(RUN/'latest-candidate-pass.json');path=ROOT/pointer['path']
    assert r.sha(path.read_bytes())==pointer['sha256']
    return r.load(path)


def page_metadata(raw,rc):
    soup=BeautifulSoup(raw,'html.parser')
    tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
    if not tag:raise ValueError('Artwork metadata missing')
    record=json.loads(tag['ng-init'].split('=',1)[1].strip())
    image=soup.select_one('img[itemprop="image"]')
    if not image:raise ValueError('Artwork image missing')
    label=soup.select_one('.copyright-wrapper .copyright')
    info=soup.select_one('.wiki-layout-artwork-info')
    fields={}
    for li in info.select('article > ul > li') if info else []:
        key=li.find('s')
        if key:
            name=key.get_text(' ',strip=True).rstrip(':');key.extract()
            fields[name]=li.get_text(' ',strip=True)
    return {'url':rc['final_url'],'metadata':record,'image_url':image.get('src'),'date':parse_date(record.get('year')),
        'rights_status':'public_domain' if label and label.select_one('.copyright-icon-public-domain') else 'restricted_or_unknown',
        'rights_label':label.get_text(' ',strip=True) if label else None,'fields':fields,'receipt':rc}


def pages():
    selected=[x for x in candidate_pass()['candidates'] if not x['work']['primary_media_id'] and x['missing_target_count']==1]
    unique={x['candidate']['url']:x['candidate'] for x in selected}
    def one(x):
        dest=RUN/'pages'/(r.sha(x['url'].encode())+'.json.gz')
        if dest.exists():return r.load(dest)
        result={'candidate':x}
        try:
            raw,rc=capture(x['url'],'page-captures')
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            result.update(outcome='captured',page=page_metadata(raw,rc))
        except Exception as exc:result.update(outcome='source_error',error=str(exc)[:300])
        r.save_gz(dest,result)
        return result
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n,x in enumerate(pool.map(one,unique.values()),1):
            counts[x['outcome']]+=1
            if n%50==0:print('Selected WikiArt pages',n,'/',len(unique),dict(counts),flush=True)
    print('Page checks',dict(counts),flush=True)


def resolve_pages():
    """Resolve failed filename hints using actual links in the artist text index."""
    selected=[x['candidate'] for x in candidate_pass()['candidates'] if not x['work']['primary_media_id'] and x['missing_target_count']==1]
    wanted={}
    for c in selected:
        path=RUN/'pages'/(r.sha(c['url'].encode())+'.json.gz')
        if path.exists() and r.load(path)['outcome']=='captured':continue
        wanted[c['url']]=c
    sources=sorted({c['artist_url'] for c in wanted.values()})
    def links(url):
        path=RUN/'artist-links'/(r.sha(url.encode())+'.json.gz')
        if path.exists():return url,r.load(path)
        raw,rc=capture(url+'/all-works/text-list','artist-link-captures')
        items=[]
        if rc['status']==200:
            soup=BeautifulSoup(raw,'html.parser');prefix=urlsplit(url).path+'/'
            for a in soup.select('li a[href]'):
                if a['href'].startswith(prefix):
                    title=a.get_text(' ',strip=True)
                    date=a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,')
                    items.append({'title':title,'date':parse_date(date),'url':urljoin(url,a['href'])})
        result={'items':items,'receipt':rc};r.save_gz(path,result)
        return url,result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:index=dict(pool.map(links,sources))
    def one(c):
        dest=RUN/'resolved-pages'/(r.sha(c['url'].encode())+'.json.gz')
        if dest.exists():return r.load(dest)
        choices=[x for x in index[c['artist_url']]['items'] if norm(x['title']) in {norm(c['title']),norm(c.get('english_title'))} and x['date'] and c.get('date') and max(x['date'][0],c['date'][0])<=min(x['date'][1],c['date'][1])]
        result={'candidate':c,'choices':choices,'outcome':'ambiguous_or_absent_page_link'}
        if len(choices)==1:
            try:
                raw,rc=capture(choices[0]['url'],'page-captures')
                if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
                result.update(outcome='captured',page=page_metadata(raw,rc))
            except Exception as exc:result.update(outcome='source_error',error=str(exc)[:300])
        r.save_gz(dest,result);return result
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for x in pool.map(one,wanted.values()):counts[x['outcome']]+=1
    print('Resolved page hints',dict(counts),flush=True)


MUSEUM_ALIASES={
    'tate':['Tate Modern, London','Tate Britain, London','Tate Gallery, London'],
    'the-met':['Metropolitan Museum of Art, New York','Metropolitan Museum of Art (Met), New York City'],
    'national-gallery':['National Gallery, London'],
    'national-gallery-london':['National Gallery, London'],
    'state-russian-museum':['Russian Museum, Saint Petersburg','Russian Museum, St. Petersburg','State Russian Museum'],
    'state-tretyakov-gallery':['Tretyakov Gallery, Moscow','State Tretyakov Gallery'],
    'joconde-m5041':['Musée National Gustave Moreau, Paris','Gustave Moreau Museum, Paris'],
    'musee-d-orsay':['Musée d’Orsay, Paris'],
    'national-gallery-of-art':['National Gallery of Art, Washington'],
    'art-institute-of-chicago':['Art Institute of Chicago'],
    'kunsthistorisches-museum':['Kunsthistorisches Museum, Vienna'],
    'albertina':['Albertina, Vienna'],
    'wikimedia-museum-q188740':['Museum of Modern Art (MoMA), New York City'],
    'wikimedia-museum-q857276':["Musée d'Art Moderne de la Ville de Paris, Paris"],
    'joconde-m5077':['Château de Versailles, Versailles'],
    'joconde-m5051':['École nationale supérieure des Beaux-Arts (ENSBA), Paris'],
}


def museum_agrees(institution, location):
    loc=norm(location)
    if not loc:return None
    names=[institution['name']]+MUSEUM_ALIASES.get(institution['slug'],[])
    generic={'national gallery','national museum','museum of fine arts','museum of modern art','state museum'}
    for name in names:
        key=norm(name)
        if key.removeprefix('the ') in generic:continue
        if len(key)>=8 and key in loc:return True
    # French native museum labels carry their city after an em dash. Ignore
    # articles/prepositions only when all substantive words, including city,
    # are present. A generic museum name without a city cannot pass this rule.
    if institution['slug'].startswith('joconde-') and '—' in institution['name']:
        stop={'de','des','du','d','et','le','la','les','l','en','a'}
        tokens=set(norm(institution['name']).split())-stop
        if len(tokens)>=3 and tokens.issubset(set(loc.split())):return True
    return False


def assess_one(item,page,institution):
    w,c=item['work'],item['candidate'];metadata=page['metadata']
    if w['primary_media_id']:return 'existing_image_preserved'
    if item['missing_target_count']!=1:return 'multiple_catalogue_targets'
    title_matches=norm(metadata.get('title')) in title_keys(w)
    translated_title_matches=bool(c.get('language','en')!='en' and norm(c['title']) in title_keys(w)
        and norm(c.get('english_title'))==norm(metadata.get('title')))
    if not title_matches and not translated_title_matches:return 'page_title_conflict'
    if urljoin(page['url'],metadata.get('artistUrl','')).rstrip('/')!=c['artist_url'].rstrip('/'):return 'page_artist_conflict'
    if not date_compatible(w,page['date']):return 'page_date_conflict'
    if image_key(c['image_url']) not in {image_key(page['image_url']),image_key(metadata.get('image'))}:return 'page_image_conflict'
    if page['rights_status']!='public_domain' or norm(page['rights_label'])!='public domain':return 'rights_restricted_unknown_or_territorial'
    if w['creators'] and (len(w['creators'])!=1 or w['creators'][0]['role']!='primary'):return 'qualified_or_multiple_creators'
    if not w['creators'] and norm(w.get('unlinked_creator_label'))!=norm(metadata.get('artistName')):return 'object_creator_needs_review'
    source_medium=norm(page['fields'].get('Media'))
    print_terms=r'\b(etching|engraving|aquatint|drypoint|lithograph|lithography|woodcut|woodblock|linocut|mezzotint|screenprint)\b'
    paint_terms=r'\b(oil|acrylic|tempera|fresco)\b'
    work_type=w.get('work_type')
    if work_type=='print' and re.search(paint_terms,source_medium) and not re.search(print_terms,source_medium):return 'artwork_medium_conflict'
    if work_type in ['painting','fresco','icon'] and re.search(print_terms,source_medium) and not re.search(paint_terms,source_medium):return 'artwork_medium_conflict'
    if work_type=='drawing' and re.search(paint_terms,source_medium) and not re.search(r'\b(pencil|ink|charcoal)\b',source_medium):return 'artwork_medium_conflict'
    if re.search(r'\b(detail|fragment|copy|after|study|sketch|workshop)\b',norm(w['title'])):return 'partial_or_study_needs_visual_reconciliation'
    location=page['fields'].get('Location')
    agrees=museum_agrees(institution,location)
    if agrees is False:return 'museum_location_needs_reconciliation'
    if c.get('direct_identity'):return 'high_existing_source_identity'
    if agrees is True:return 'high_creator_title_date_museum'
    # A long distinctive title and narrow compatible date can identify a work
    # when the source omits its museum. Generic subjects cannot pass this rule.
    generic={'untitled','landscape','portrait','self portrait','still life','nude','composition','abstract composition','flowers','study'}
    title=norm(w['title']);date=page['date']
    if title in generic or len(title.split())<4 or item['candidate_count']!=1:return 'insufficient_object_corroboration'
    if w['creation_year_end']-w['creation_year_start']>5 or date[1]-date[0]>5:return 'broad_date_needs_review'
    return 'high_distinctive_title_creator_narrow_date'


def assess():
    data=candidate_pass();institutions={x['id']:x for x in r.load(RUN/'institutions.json.gz')}
    ready=[];held=[]
    for item in data['candidates']:
        if item['work']['primary_media_id']:continue
        key=r.sha(item['candidate']['url'].encode())+'.json.gz'
        paths=[RUN/'resolved-pages'/key,RUN/'pages'/key]
        results=[r.load(p) for p in paths if p.exists()]
        source=next((x for x in results if x['outcome']=='captured'),None)
        outcome='multiple_catalogue_targets' if item['missing_target_count']!=1 else (assess_one(item,source['page'],institutions[item['work']['institution_id']]) if source else 'page_verification_pending_or_failed')
        value={**item,'review_outcome':outcome,'institution':institutions[item['work']['institution_id']]}
        if source:value['page']=source['page']
        (ready if outcome.startswith('high_') else held).append(value)
    source_counts=collections.Counter(x['page']['metadata']['_id'] for x in ready+held if x.get('page'))
    for x in ready[:]:
        if source_counts[x['page']['metadata']['_id']]!=1:
            ready.remove(x);held.append({**x,'review_outcome':'multiple_catalogue_targets_after_page_resolution'})
    label=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());path=RUN/'review-passes'/(label+'.json.gz')
    result={'at':r.now(),'candidate_pass':r.load(RUN/'latest-candidate-pass.json'),'ready':ready,'held':held,
        'confidence_policy':'User requested matches at least 90% confident. High corroboration rules are conservative operational gates, not calibrated probabilities. No fuzzy-only matches or uncertain versions applied.'}
    r.save_gz(path,result)
    (RUN/'latest-review-pass.json').write_text(json.dumps({'path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes())}))
    print(json.dumps({'ready':len(ready),'held':len(held),'ready_reasons':dict(collections.Counter(x['review_outcome'] for x in ready)),
        'held_reasons':dict(collections.Counter(x['review_outcome'] for x in held))}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['snapshot','cache','artist_sources','indexes','translations','candidates','pages','resolve_pages','assess'])
    args=p.parse_args()
    globals()[args.command]()
