#!/usr/bin/env python3
"""Selected Greek painter image expansion, with exact source and recovery evidence."""
import argparse, collections, concurrent.futures, csv, difflib, hashlib, html, importlib.util, io, json, os, re, threading, time, uuid
from pathlib import Path
from urllib.parse import urlencode,quote,urlsplit,urlunsplit,urljoin,urlparse
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('top100',ROOT/'ops/wikiart-top100-20260920.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
c=t.c;m=t.m
RUN=ROOT/'docs/research/greek-images-20260920'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
GATE=threading.Lock()
os.environ.setdefault('CLOUDSDK_CORE_ACCOUNT','vadim@alingva.com')
TARGET='both'


def target_dsns():
    if TARGET in ('local','both'):yield 'local','postgres://localhost/artline'
    if TARGET in ('cloud','both'):yield 'cloud',m.core.cloud_dsn()


def images_for_target(target):
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    if target=='local':return images
    mappings=read(RUN/'target-id-reconciliation.json') if (RUN/'target-id-reconciliation.json').exists() else {}
    for im in images:
        match=mappings.get(im['work']['id'])
        if match:
            w=im['work'];w['local_artwork_id']=w['id'];w['id']=match['cloud_artwork_id']
            w['slug']=match['cloud_before_record']['slug'];w['before_record']=match['cloud_before_record']
            w['target_identity_evidence']=match
    return images


def reconcile_target_ids():
    mappings={}
    for p in sorted((RUN/'prepared').glob('*.json')):
        w=read(p)['work']
        if w['new_record']:continue
        local=read(RUN/'catalogue/local'/(w['artist']['id']+'.json'));cloud=read(RUN/'catalogue/cloud'/(w['artist']['id']+'.json'))
        if any(x['artwork_id']==w['id'] for x in cloud):continue
        before=next(x for x in local if x['artwork_id']==w['id'])
        native={(e['scheme'],e['external_id']) for e in before['identifiers'] or []}
        matches=[x for x in cloud if native & {(e['scheme'],e['external_id']) for e in x['identifiers'] or []}]
        if len(matches)!=1 or not m.same_artwork(before['before_record'],matches[0]['before_record']):raise ValueError('Exact native target identity needs reconciliation: '+w['title'])
        candidate=matches[0]
        if candidate['primary_media_id'] or len(candidate['creators'] or [])!=1 or candidate['creators'][0]['role']!='primary':raise ValueError('Target already illustrated or attribution differs')
        mappings[w['id']]={'local_artwork_id':w['id'],'cloud_artwork_id':candidate['artwork_id'],'cloud_before_record':candidate['before_record'],
            'matching_native_identifiers':[list(x) for x in sorted(native & {(e['scheme'],e['external_id']) for e in candidate['identifiers'] or []})],
            'basis':'Same existing creator, exact native museum identifier and identical semantic artwork metadata; preserve each database UUID and holding institution ID.'}
    m.save_atomic(RUN/'target-id-reconciliation.json',mappings);m.save_atomic(BACKUP/'target-id-reconciliation.json',mappings)
    print('Existing target identities reconciled',len(mappings),flush=True)
FETCH_NEXT=0.0
PREVIOUS=[ROOT/'docs/research'/name for name in ('wikiart-top100-20260920','women-wikiart-20260920','wikiart-artist-followup-20260920','wikiart-artist-coverage-20260920','wikiart-selected-images-20260919')]


def read(path):return json.loads(path.read_bytes())


def fetch(url):
    key=m.core.sha(url.encode());path=RUN/'captures'/(key+'.body');receipt=path.with_suffix('.json')
    if path.exists():
        raw=path.read_bytes();evidence=read(receipt)
        if m.core.sha(raw)!=evidence['sha256']:raise ValueError('Capture checksum differs')
        if evidence['http_status']!=200:raise ValueError('Cached source was not accessible: '+url)
        return raw,evidence
    if urlparse(url).netloc=='www.wikiart.org':
        for prior in PREVIOUS:
            capture=prior/'captures'/(key+'.body');rp=capture.with_suffix('.json')
            if capture.exists() and rp.exists():
                raw=capture.read_bytes();ev=read(rp)
                if m.core.sha(raw)!=ev['sha256']:raise ValueError('Prior source checksum differs')
                ev={**ev,'path':str(path.relative_to(ROOT)),'http_status':200,'reused_from':str(capture.relative_to(ROOT))}
                m.save_atomic(path,raw);m.save_atomic(receipt,ev);return raw,ev
    global FETCH_NEXT
    with GATE:
        slot=max(time.monotonic(),FETCH_NEXT);FETCH_NEXT=slot+1.0
    time.sleep(max(0,slot-time.monotonic()))
    response=m.requests.get(url,headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected artwork research)'},timeout=(15,45))
    if len(response.content)>20_000_000:raise ValueError('Metadata response exceeds limit')
    evidence={'url':url,'final_url':response.url,'checked_at':m.core.now(),'http_status':response.status_code,
        'sha256':m.core.sha(response.content),'bytes':len(response.content),'path':str(path.relative_to(ROOT))}
    m.save_atomic(path,response.content);m.save_atomic(receipt,evidence)
    response.raise_for_status()
    return response.content,evidence


def audit():
    path=RUN/'baseline.json'
    if path.exists():return
    targets={}
    for target,dsn in target_dsns():
        with m.read_only(dsn) as db:
            artists=db.execute("""SELECT to_jsonb(a) artist,
                coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
                (SELECT jsonb_agg(to_jsonb(ac)) FROM artist_countries ac WHERE ac.artist_id=a.id) countries,
                coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers
                FROM artists a WHERE a.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND ac.country_code='GR')
                ORDER BY a.display_name""").fetchall()
            for row in artists:
                works=c.artist_works(db,row['artist']['id'])
                m.save_atomic(RUN/'catalogue'/target/(row['artist']['id']+'.json'),works)
                row['works']=sum(w['status']!='archived' for w in works)
                row['images']=sum(w['status']!='archived' and w['primary_media_id'] is not None for w in works)
            targets[target]=artists
    result={'at':m.core.now(),'targets':targets}
    m.save_atomic(path,result);m.save_atomic(BACKUP/'cohort-baseline.json',result)
    print({target:{'painters':len(rows),'works':sum(r['works'] for r in rows),'images':sum(r['images'] for r in rows)} for target,rows in targets.items()},flush=True)


def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/greek-images-20260920/'+value))


def source_work(artist,prior,title,date,scheme,source_id,url,image_url,receipt,metadata,rights,label,credit,basis,work_type='unknown'):
    return {'id':prior['artwork_id'] if prior else uid(scheme+'/'+source_id),
        'slug':prior['slug'] if prior else 'greek-images-'+uid(scheme+'/'+source_id),'artist':artist,
        'title':prior['title'] if prior else html.unescape(title),
        **{k:(prior[k] if prior else date[k]) for k in ('date_display','creation_year_start','creation_year_end','date_precision')},
        'work_type':prior['work_type'] if prior else work_type,'source_url':url,'scheme':scheme,'source_id':source_id,
        'image_url':image_url,'source_receipt':receipt,'source_metadata':metadata,'rights_status':rights,'license_label':label,
        'license_url':url,'creator_credit':credit,
        'rights_basis':'Continuation of the user-authorized Greek painter collection workflow, with creation end by 1955; actual source rights retained without asserting independent copyright-holder permission.',
        'selection_basis':'Fill an existing selected artwork image gap.' if prior else 'Personal owner highlight selected from the documented painter catalogue; not a museum designation or current display assertion.',
        'attribution_basis':basis,'new_record':prior is None,'before_record':prior['before_record'] if prior else None,'requires_source_policy':True}


def source_date(value):
    return m.creation_date(re.sub(r'^(?:ca\.?|circa)\s*','c.',value or '',flags=re.I))


def national_gallery():
    artists={r['artist']['id']:r for r in read(RUN/'baseline.json')['targets']['local']};tasks=[]
    for path in (RUN/'catalogue/local').glob('*.json'):
        row=artists[path.stem]
        for w in read(path):
            if w['primary_media_id'] or w['creation_year_end'] is None or w['creation_year_end']>1955:continue
            refs=[e for e in w['identifiers'] or [] if (e.get('url') or '').startswith('https://www.nationalgallery.gr/en/artwork/')]
            if refs:tasks.append((row,w,refs[0]))
    def one(task):
        row,w,ref=task;path=RUN/'museum-discovery'/(w['artwork_id']+'.json')
        if path.exists():return read(path)
        result={'artwork_id':w['artwork_id'],'artist':row['artist']['display_name'],'title':w['title']}
        try:
            raw,receipt=fetch(ref['url']);soup=BeautifulSoup(raw,'html.parser');main=soup.find('main') or soup
            heading=main.select_one('h1.artwork');span=heading.find('span') if heading else None
            source_date=span.get_text(' ',strip=True) if span else ''
            title=heading.get_text(' ',strip=True).removesuffix(source_date).strip(' ,') if heading else ''
            date=m.creation_date(re.sub(r'^(?:ca\.?|circa)\s*','c.',source_date,flags=re.I))
            author=main.select_one('p.artist');links=[a['href'] for a in author.select('a[href]')] if author else []
            known={e['canonical_url'] for e in row['identifiers'] if e['scheme']=='nationalgallery-gr-artist'}
            if row['artist']['display_name']=='El Greco':known.add('https://www.nationalgallery.gr/en/artist/theotokopoulos-domenicos/')
            if len(links)!=1 or links[0] not in known:raise ValueError('Exact museum painter identity requires reconciliation: '+str(links))
            if m.norm(title)!=m.norm(w['title']):raise ValueError('Museum object title differs: '+title)
            if not date or date['creation_year_end']>1955:raise ValueError('Museum creation date unresolved or after 1955: '+source_date)
            if not t.overlaps(w,date):raise ValueError('Museum date differs from existing record: '+source_date)
            if len(w['creators'] or [])!=1 or w['creators'][0]['role']!='primary':raise ValueError('Existing attribution requires review')
            pics=[x['src'] for x in main.select('img[src]') if '/uploads/' in x['src']]
            if len(pics)!=1:raise ValueError('Exact museum reproduction is ambiguous')
            fulltext=soup.get_text(' ',strip=True);copyright_text='; '.join(x.get_text(' ',strip=True) for x in soup.select('footer') if '©' in x.get_text())
            metadata={'title':title,'source_date':source_date,'artist_label':author.get_text(' ',strip=True),'artist_links':links,
                'inventory':(main.select_one('.artwork-no') or main).get_text(' ',strip=True)[:100],
                'medium_dimensions':(main.select_one('p.description') or main).get_text(' ',strip=True)[:300],
                'source_copyright':copyright_text,'source_page_text':main.get_text(' ',strip=True)}
            work=source_work(row['artist'],w,title,date,ref['scheme'],ref['external_id'],ref['url'],pics[0],receipt,metadata,
                'restricted' if copyright_text else 'unknown','Source copyright retained; no reuse licence verified' if copyright_text else 'No reuse licence verified',
                row['artist']['display_name']+'; National Gallery – Alexandros Soutsos Museum; '+metadata['inventory'],
                'Existing exact museum object URL, title, compatible creation date and primary maker page independently match.')
            result.update(work=work,outcome='selected')
        except (ValueError,m.requests.RequestException) as e:result.update(outcome='held',reason=str(e)[:450])
        m.save_atomic(path,result);print('Museum',result['outcome'],row['artist']['display_name'],w['title'],result.get('reason',''),flush=True)
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,tasks))
    m.save_atomic(RUN/'museum-selected.json',[r['work'] for r in results if r['outcome']=='selected'])
    print('Museum selection',sum(r['outcome']=='selected' for r in results),'of',len(results),flush=True)


def wikiart_sources():
    rows=read(RUN/'baseline.json')['targets']['local'];pairs=[];prior=ROOT/'docs/research/wikiart-artist-coverage-20260920';known=[]
    for fn in ('artist-matches.json','extra-artist-matches.json','supplemental-artist-matches.json'):
        if (prior/fn).exists():known+=read(prior/fn)['matches']
    manual={'greek-iakovidis-georgios':'georgios-jakobides','greek-flora-karavia-thaleia':'thalia-flora-karavia',
        'nicolas-ghika-research-ab841ccc7ea0':'nikos-hadjikyriakos-ghikas'}
    raw,receipt=fetch('https://www.wikiart.org/en/artists-by-nation/greek');m.save_atomic(RUN/'wikiart-directory-review.json',receipt)
    unmatched=[]
    for row in rows:
        a=row['artist'];names={m.norm(n) for n in [a['display_name']]+row['aliases']}
        found={p['wikiart']['url']:p['wikiart'] for p in known if p['artist']['id']==a['id'] or m.norm(p['wikiart']['name']) in names}
        if a['slug'] in manual:
            url='https://www.wikiart.org/en/'+manual[a['slug']];found={url:{'url':url,'name':a['display_name'],'identity_review':'Named transliteration/alias matched with source lifespan and museum authority; existing biography remains unchanged.'}}
        if len(found)==1:pairs.append({'artist':a,'source':next(iter(found.values()))})
        else:unmatched.append({'artist':a,'reason':'No unambiguous named profile in reviewed WikiArt mapping','sources':list(found)})
    m.save_atomic(RUN/'wikiart-source-matches.json',{'pairs':pairs,'unmatched':unmatched});print('WikiArt matched',len(pairs),'painters',flush=True)


def wikiart_indexes():
    def one(pair):
        artist=pair['artist'];source=pair['source'];path=RUN/'wikiart-indexes'/(artist['id']+'.json')
        if path.exists():return read(path)
        raw,receipt=fetch(source['url']);soup=BeautifulSoup(raw,'html.parser');featured=[]
        for tag in soup.select('[ng-init]'):
            init=tag['ng-init']
            if not re.search(r"['\"]masonryId['\"]\s*:\s*['\"]famous-works['\"]",init):continue
            match=re.search(r"['\"]customSource['\"]\s*:\s*",init)
            if match:featured=json.JSONDecoder().raw_decode(init[match.end():])[0].get('_v',[])
        profile={'receipt':receipt,'featured':featured,'title':(soup.select_one('h1') or soup).get_text(' ',strip=True),
            'wikidata_ids':sorted(set(re.findall(r'www.wikidata.org/(?:wiki/)?(Q\d+)',raw.decode())))}
        raw,receipt=fetch(source['url']+'/all-works/text-list');soup=BeautifulSoup(raw,'html.parser');prefix=urlparse(source['url']).path+'/'
        works={}
        for a in soup.select('li a[href]'):
            if not a['href'].startswith(prefix):continue
            title=a.get_text(' ',strip=True);date=a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,')
            url=urljoin(source['url'],a['href']);works[url]={'title':title,'source_date':date,'date':m.creation_date(date),'url':url}
        result={'artist':artist,'source':source,'profile':profile,'receipt':receipt,'works':list(works.values())}
        m.save_atomic(path,result);print('WikiArt index',artist['display_name'],len(works),'works',flush=True);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,read(RUN/'wikiart-source-matches.json')['pairs']))


def wikiart_select():
    with m.read_only() as db:
        present=db.execute("SELECT entity_id::text,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork'").fetchall()
    global_ids={r['external_id']:r['entity_id'] for r in present};global_urls={r['canonical_url']:r['entity_id'] for r in present}
    def one(index):
        artist=index['artist'];path=RUN/'wikiart-selections'/(artist['id']+'.json')
        if path.exists():return read(path)
        rows=[w for w in read(RUN/'catalogue/local'/(artist['id']+'.json')) if w['status']!='archived']
        names=collections.defaultdict(dict);ids={};urls={}
        for w in rows:
            for title in (w['title'],w.get('alternate_title')):
                if title:names[m.norm(title)][w['artwork_id']]=w
            for e in w['identifiers'] or []:
                if e['scheme']=='wikiart-artwork':ids[e['external_id']]=w
                if e.get('url'):urls[e['url']]=w
        featured={urljoin(index['source']['url'],w['paintingUrl']):w for w in index['profile']['featured']}
        choices=[];held=[];skipped=collections.Counter()
        counts=collections.Counter(m.norm(w['title']) for w in index['works'])
        for item in index['works']:
            date=item['date'];url=item['url']
            if not date or date['creation_year_end']>1955:skipped['undated_or_after_1955']+=1;continue
            if re.search(r'\b(detail|reconstruction)\b',item['title'],re.I):skipped['detail_or_reconstruction']+=1;continue
            known=urls.get(url) or ids.get(featured.get(url,{}).get('_id'))
            matches=[known] if known else list(names.get(m.norm(item['title']),{}).values())
            if matches:
                valid=[w for w in matches if w['creation_year_end'] is not None and w['creation_year_end']<=1955 and t.overlaps(w,date)
                    and len(w['creators'] or [])==1 and w['creators'][0]['role']=='primary']
                if len(valid)!=1 or (not known and counts[m.norm(item['title'])]!=1):
                    held.append({'item':item,'reason':'Existing title/date/attribution requires reconciliation'});continue
                prior=valid[0]
                if prior['primary_media_id']:skipped['already_illustrated']+=1;continue
            else:
                prior=None
                if url in global_urls:skipped['source_already_catalogued']+=1;continue
                close=difflib.get_close_matches(t.title_key(item['title']),[t.title_key(n) for n in names],n=1,cutoff=.87)
                if close:held.append({'item':item,'reason':'Potential title variant of existing work','near_title':close});continue
            choices.append({**item,'prior':prior,'featured':url in featured})
        choices.sort(key=lambda w:(w['prior'] is None,not w['featured'],w['date']['creation_year_start'],w['title']))
        selected=[];new_count=0;selected_titles=set();attempts=0
        for item in choices:
            if item['prior'] is None and new_count>=12:continue
            if attempts>=80:break
            if m.norm(item['title']) in selected_titles:continue
            attempts+=1
            try:
                raw,receipt=fetch(item['url']);soup=BeautifulSoup(raw,'html.parser');tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
                if tag is None:raise ValueError('Public detail unavailable; no sign-in attempted')
                record=json.loads(tag['ng-init'].split('=',1)[1].strip());date=source_date(record.get('year'))
                if not date or date['creation_year_end']>1955 or not t.overlaps(date,item['date']):raise ValueError('Detail creation date differs or is ineligible')
                if record['artistUrl']!=urlparse(index['source']['url']).path:raise ValueError('Source painter differs')
                if m.norm(record['title'])!=m.norm(item['title']):raise ValueError('Source title differs')
                prior=item['prior'];sid=record['_id']
                if sid in global_ids and (prior is None or global_ids[sid]!=prior['artwork_id']):raise ValueError('Source object already catalogued under another identity')
                image=soup.select_one('img[itemprop="image"]')
                if image is None:raise ValueError('Missing exact artwork image')
                label=soup.select_one('.copyright-wrapper .copyright');pd=bool(label and label.select_one('.copyright-icon-public-domain'))
                rights='public_domain' if pd else 'restricted' if label else 'unknown'
                rights_label='Public domain (WikiArt label)' if pd else 'Copyright protected (WikiArt label)' if label else 'Rights not specified'
                info=(soup.select_one('.wiki-layout-artwork-info article') or soup).get_text(' ',strip=True)
                medium=[]
                for li in soup.select('li'):
                    txt=li.get_text(' ',strip=True)
                    if txt.startswith('Media:'):medium=[a.get_text(' ',strip=True) for a in li.select('a')]
                medium_text=', '.join(medium);mt=medium_text.lower()
                typ='watercolor' if 'watercolor' in mt else 'painting' if any(x in mt for x in ('oil','tempera','acrylic','gouache')) else 'drawing' if any(x in mt for x in ('pencil','charcoal','ink','crayon')) else 'print' if any(x in mt for x in ('lithograph','etching','woodcut')) else 'unknown'
                work=source_work(artist,prior,record['title'],date,'wikiart-artwork',sid,item['url'],image['src'],receipt,
                    {'record':record,'rights_label':label.get_text(' ',strip=True) if label else None,'description':info[:6000],
                     'index_receipt':index['receipt'],'source_featured':item['featured'],'media':medium},rights,rights_label,
                    artist['display_name']+'; WikiArt; '+rights_label,
                    'Exact scoped WikiArt painter, object title, source object ID and compatible creation dates; existing records reconciled by exact source or unambiguous title.',typ)
                work['medium_text']=medium_text or None
                if not prior:work['selection_basis']='Personal owner highlight from the dated WikiArt painter catalogue, at most twelve new works per painter; '+('explicitly featured by WikiArt.' if item['featured'] else 'selected to broaden the illustrated creation periods.')
                selected.append(work);new_count+=prior is None;selected_titles.add(m.norm(work['title']))
            except (ValueError,m.requests.RequestException) as e:
                held.append({'item':item,'reason':str(e)[:400]})
                if isinstance(e,m.requests.HTTPError) and e.response.status_code in (403,429):break
        result={'artist':artist,'selected':selected,'held':held,'skipped':dict(skipped),'inspected_index_entries':len(index['works'])}
        m.save_atomic(path,result);print('WikiArt selected',artist['display_name'],len(selected),'new',new_count,flush=True);return result
    indexes=[read(p) for p in sorted((RUN/'wikiart-indexes').glob('*.json'))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,indexes))
    m.save_atomic(RUN/'wikiart-selected.json',[w for r in results for w in r['selected']])


def commons_discover():
    rows=read(RUN/'baseline.json')['targets']['local']
    def one(row):
        a=row['artist'];path=RUN/'commons-discovery'/(a['id']+'.json')
        if path.exists():return
        names=list(dict.fromkeys([a['display_name']]+row['aliases']))[:6]
        query=' OR '.join('"'+x.replace('"','')+'"' for x in names)
        url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','generator':'search','gsrsearch':query,
            'gsrnamespace':6,'gsrlimit':40,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','rvprop':'ids|content','rvslots':'main'})
        try:
            raw,receipt=fetch(url);data=json.loads(raw)
            result={'artist':a,'names':names,'receipt':receipt,'pages':list(data.get('query',{}).get('pages',{}).values()),'continuation':data.get('continue')}
        except (ValueError,m.requests.RequestException) as e:result={'artist':a,'names':names,'pages':[],'error':str(e)[:300]}
        m.save_atomic(path,result);print('Commons metadata',a['display_name'],len(result['pages']),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,rows))


def prepare_selected():
    selected={};alternatives=[]
    for name in ('museum-selected.json','wikiart-selected.json','commons-selected.json','native-selected.json','specific-selected.json'):
        if not (RUN/name).exists():continue
        for w in read(RUN/name):
            if w['id'] in selected:alternatives.append({'artwork_id':w['id'],'retained_source':selected[w['id']]['source_url'],'alternative_source':w['source_url']})
            else:selected[w['id']]=w
    stamp=str(len(selected))+'-'+m.core.sha(json.dumps(selected,sort_keys=True).encode())[:12]
    manifest='selected-'+stamp+'.json'
    m.save_atomic(RUN/manifest,list(selected.values()));m.save_atomic(RUN/('alternative-images-'+stamp+'.json'),alternatives)
    prepare(manifest)


def commons_select():
    rows={r['artist']['id']:r for r in read(RUN/'baseline.json')['targets']['local']}
    selected=[];held=[];review=[]
    licenses={'Public domain':'public_domain','CC0':'cc0','CC BY 4.0':'cc_by','CC BY 3.0':'cc_by','CC BY-SA 4.0':'cc_by_sa','CC BY-SA 3.0':'cc_by_sa'}
    def clean(value):
        soup=BeautifulSoup(value or '','html.parser')
        for node in soup.select('[style*="display: none"], [style*="display:none"], .noprint'):node.decompose()
        return soup.get_text(' ',strip=True)
    def title_value(value):
        soup=BeautifulSoup(value or '','html.parser');node=soup.select_one('[lang="en"]') or soup.select_one('[lang="en-us"]')
        return clean(str(node) if node else value)
    with m.read_only() as db:
        qids=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme IN ('wikidata','commons-artwork')").fetchall()
    existing_sources={x['external_id']:x['entity_id'] for x in qids}
    other=[w for name in ('museum-selected.json','wikiart-selected.json') for w in read(RUN/name)]
    selected_ids={w['id'] for w in other}
    for p in sorted((RUN/'commons-discovery').glob('*.json')):
        discovery=read(p);artist=discovery['artist'];row=rows[artist['id']]
        names={m.norm(n) for n in [artist['display_name']]+row['aliases']}
        old=read(RUN/'catalogue/local'/(artist['id']+'.json'))
        titles={m.norm(w['title']):w for w in old};more_titles={m.norm(w['title']) for w in other if w['artist']['id']==artist['id']}
        fresh=0;outcomes=collections.Counter();seen_qids=set();seen_titles=set()
        for page in discovery['pages']:
            info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});field=lambda k:clean(meta.get(k,{}).get('value',''))
            markup=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
            credit=field('Artist');name=m.norm(re.sub(r'\s*\(\d{3,4}\s*[-–]\s*\d{3,4}\).*','',credit))
            artist_field=' '.join(re.findall(r'\|\s*artist\s*=[^\n]*',markup,re.I))
            if name not in names or '{{Artwork' not in markup or re.search(r'\b(attributed|workshop|follower|after |circle of)\b',credit+' '+artist_field,re.I):
                outcomes['maker_or_object_metadata_not_exact']+=1;continue
            if info.get('mime') not in ('image/jpeg','image/png','image/tiff') or re.search(r'\b(detail|close[ -]up|cropped|collage|montage)\b',page['title'],re.I):
                outcomes['format_or_partial_image']+=1;continue
            if field('LicenseShortName') not in licenses or field('Restrictions'):outcomes['rights_needs_review']+=1;continue
            raw_date=field('DateTimeOriginal');normal=re.sub(r'^between (\d{3,4}) and (\d{3,4})$',r'\1–\2',raw_date)
            date=source_date(normal)
            if not date or date['creation_year_end']>1955:outcomes['date_unresolved_or_ineligible']+=1;continue
            if artist['death_year'] and date['creation_year_start']>artist['death_year']:outcomes['date_after_creator_life']+=1;continue
            if artist['birth_year'] and date['creation_year_end']<artist['birth_year']:outcomes['date_before_creator_life']+=1;continue
            title=title_value(meta.get('ObjectName',{}).get('value',''))
            if not title or len(title)>200:outcomes['title_needs_review']+=1;continue
            qid_match=re.search(r'\|\s*wikidata\s*=\s*(Q\d+)',markup,re.I);qid=qid_match[1] if qid_match else None
            prior=None
            source_prior=existing_sources.get(page['title']) or (existing_sources.get(qid) if qid else None)
            if source_prior:prior=next((w for w in old if w['artwork_id']==source_prior),None)
            if source_prior and prior is None:outcomes['source_already_elsewhere']+=1;continue
            title_prior=titles.get(m.norm(title))
            if not prior and title_prior:
                if not t.overlaps(title_prior,date):outcomes['existing_title_date_ambiguous']+=1;continue
                prior=title_prior
            if prior:
                if prior['primary_media_id'] or prior['artwork_id'] in selected_ids:outcomes['existing_image_or_selected']+=1;continue
                if not t.overlaps(prior,date) or len(prior['creators'] or [])!=1 or prior['creators'][0]['role']!='primary':outcomes['existing_attribution_date_ambiguous']+=1;continue
            else:
                key=t.title_key(title)
                if qid in seen_qids or m.norm(title) in seen_titles or m.norm(title) in more_titles:outcomes['duplicate_selected_source']+=1;continue
                if difflib.get_close_matches(key,[t.title_key(x) for x in titles],n=1,cutoff=.88):outcomes['possible_existing_title_variant']+=1;continue
                if fresh>=4:outcomes['bounded_four_new_highlights']+=1;continue
            medium=field('Medium');lower=(medium+' '+markup).lower()
            icon=bool(re.search(r'category:icons|\bicon\b',lower))
            typ='painting' if re.search(r'object[ _]type\s*=\s*painting|category:paintings|oil|tempera',lower) else 'unknown'
            rights=licenses[field('LicenseShortName')];license_url='https://creativecommons.org/publicdomain/mark/1.0/' if rights=='public_domain' else meta.get('LicenseUrl',{}).get('value','').replace('http://','https://')
            if not license_url.startswith('https://creativecommons.org/'):outcomes['licence_url_missing']+=1;continue
            url=info['descriptionurl'];work=source_work(artist,prior,title,date,'commons-artwork',page['title'],url,info['url'],discovery['receipt'],page,rights,
                field('LicenseShortName'),credit+'; Wikimedia Commons; '+field('Credit'),
                'Commons Artwork metadata explicitly names the scoped painter and supplies the creation date; exact source Wikidata object or unambiguous compatible title used for existing records.',typ)
            work.update(license_url=license_url,commons_sha1=info['sha1'],commons_size=info['size'],medium_text=medium or None,
                independently_verified_rights=True,source_artwork_wikidata=qid)
            if icon:work['object_form']='icon'
            work['rights_basis']='Retained per-file Commons licence and metadata for this exact reproduction. Underlying historical two-dimensional artwork and photographer/source credits preserved.'
            if not prior:work['selection_basis']='Personal owner selection of at most four additional dated highlights per painter from explicitly attributed Commons artwork metadata.'
            selected.append(work);selected_ids.add(work['id']);seen_titles.add(m.norm(title))
            if qid:seen_qids.add(qid)
            fresh+=prior is None
        review.append({'artist':artist['display_name'],'artist_id':artist['id'],'reviewed_files':len(discovery['pages']),'outcomes':dict(outcomes),
            'new_selected':fresh,'search_truncated':bool(discovery.get('continuation'))})
    m.save_atomic(RUN/'commons-selected.json',selected);m.save_atomic(RUN/'commons-selection-review.json',review)
    print('Commons selected',len(selected),'new',sum(w['new_record'] for w in selected),'painters',len({w['artist']['id'] for w in selected}),flush=True)


def record_cooldown():
    m.core.provider_rate_slot('upload.wikimedia.org',cooldown=900)
    m.save_atomic(RUN/'commons-download-pause.json',{'at':m.core.now(),'host':'upload.wikimedia.org','http_status':429,
        'observed_url':'https://upload.wikimedia.org/wikipedia/commons/c/c6/Nikolaos_Lytras_Portrait_of_man_oil-on-canvas-63x47cm-1915.jpg',
        'reason':'Server requested lower request rate; response headers were not retained by the initial downloader. Apply conservative 15-minute pause and slower future requests; no alternate download host used.'})


def native_select():
    selected=[];held=[];used={w['id'] for n in ('museum-selected.json','wikiart-selected.json','commons-selected.json') for w in read(RUN/n)}
    for row in read(RUN/'baseline.json')['targets']['local']:
        artist=row['artist']
        for w in read(RUN/'catalogue/local'/(artist['id']+'.json')):
            if w['artwork_id'] in used or w['primary_media_id'] or w['creation_year_end'] is None or w['creation_year_end']>1955:continue
            refs=[e for e in w['identifiers'] or [] if e['scheme'] in ('european-chicago-art-institute-of-chicago-object','aic-object','european-met-the-met-object','met-object')]
            if not refs:continue
            e=refs[0];kind='chicago' if e['scheme'] in ('european-chicago-art-institute-of-chicago-object','aic-object') else 'met'
            api=('https://api.artic.edu/api/v1/artworks/' if kind=='chicago' else 'https://collectionapi.metmuseum.org/public/collection/v1/objects/')+e['external_id']
            try:
                raw,receipt=fetch(api);payload=json.loads(raw);data=payload['data'] if kind=='chicago' else payload
                maker=data.get('artist_title') if kind=='chicago' else data.get('artistDisplayName')
                if m.norm(maker)!=m.norm(artist['display_name']):raise ValueError('Museum maker differs: '+str(maker))
                start=data.get('date_start') if kind=='chicago' else data.get('objectBeginDate');end=data.get('date_end') if kind=='chicago' else data.get('objectEndDate')
                if not start or not end or end>1955 or not t.overlaps(w,{'creation_year_start':start,'creation_year_end':end}):raise ValueError('Museum date differs or is ineligible')
                if kind=='chicago':
                    iid=data.get('image_id');image_url=payload['config']['iiif_url']+'/'+iid+'/full/843,/0/default.jpg' if iid else None
                    rights='public_domain' if data.get('is_public_domain') else 'restricted' if data.get('copyright_notice') else 'unknown'
                    label='Public domain (Art Institute of Chicago)' if rights=='public_domain' else data.get('copyright_notice') or 'No reuse licence verified'
                    credit=artist['display_name']+'; Art Institute of Chicago; '+(data.get('credit_line') or '')
                else:
                    image_url=data.get('primaryImage');rights='cc0' if data.get('isPublicDomain') else 'restricted' if data.get('rightsAndReproduction') else 'unknown'
                    label='CC0 (Met Open Access)' if rights=='cc0' else data.get('rightsAndReproduction') or 'No reuse licence verified'
                    credit=artist['display_name']+'; The Metropolitan Museum of Art; '+(data.get('creditLine') or '')
                if not image_url:raise ValueError('Museum API supplies no public exact-object image')
                work=source_work(artist,w,w['title'],None,e['scheme'],e['external_id'],e['url'],image_url,receipt,data,rights,label,credit,
                    'Existing native museum object ID, named creator and overlapping source creation range match; exact object API primary image.')
                if rights=='cc0':work['license_url']='https://creativecommons.org/publicdomain/zero/1.0/'
                if rights=='public_domain':work['license_url']='https://www.artic.edu/open-access/open-access-images'
                selected.append(work);print('Native selected',kind,w['title'],flush=True)
            except (ValueError,m.requests.RequestException) as error:
                held.append({'artwork_id':w['artwork_id'],'title':w['title'],'source_url':api,'reason':str(error)[:350]});print('Native held',w['title'],str(error)[:120],flush=True)
    m.save_atomic(RUN/'native-selected.json',selected);m.save_atomic(RUN/'native-source-holds.json',held)


def specific_gaps():
    results=[]
    for qid in ('Q128258459','Q112309161'):
        raw,receipt=fetch('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json');entity=json.loads(raw)['entities'][qid]
        files=[claim['mainsnak'].get('datavalue',{}).get('value') for claim in entity['claims'].get('P18',[]) if claim['rank']!='deprecated']
        row={'wikidata':qid,'receipt':receipt,'files':files,'pages':[]}
        for filename in files[:2]:
            url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'File:'+filename,
                'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','rvprop':'ids|content','rvslots':'main'})
            raw,creceipt=fetch(url);row['pages']+=list(json.loads(raw).get('query',{}).get('pages',{}).values());row['commons_receipt']=creceipt
        results.append(row)
        print(qid,files,flush=True)
        for page in row['pages']:
            print(json.dumps(page.get('imageinfo',[{}])[0].get('extmetadata',{}),ensure_ascii=False),flush=True)
    m.save_atomic(RUN/'specific-gap-source-review.json',results)


def specific_select():
    selected=[];artists=read(RUN/'baseline.json')['targets']['local']
    for row in read(RUN/'specific-gap-source-review.json'):
        matches=[]
        for artist in artists:
            for w in read(RUN/'catalogue/local'/(artist['artist']['id']+'.json')):
                if any(e['scheme']=='wikidata' and e['external_id']==row['wikidata'] for e in w['identifiers'] or []):matches.append((artist['artist'],w))
        if len(matches)!=1 or len(row['pages'])!=1:raise ValueError('Exact existing object and file must be unambiguous')
        artist,prior=matches[0];page=row['pages'][0];info=page['imageinfo'][0];metadata=info['extmetadata']
        def field(key):
            soup=BeautifulSoup(metadata.get(key,{}).get('value',''),'html.parser')
            for node in soup.select('[style*="display: none"]'):node.decompose()
            return soup.get_text(' ',strip=True)
        if m.norm(field('Artist'))!=m.norm(artist['display_name']):raise ValueError('Maker does not match')
        d=field('DateTimeOriginal');date=source_date(d if d!='1750s' else '1750–1759')
        if not date or date['creation_year_end']>1955 or not t.overlaps(prior,date):raise ValueError('Source creation range differs')
        rights={'Public domain':'public_domain','CC BY-SA 4.0':'cc_by_sa'}[field('LicenseShortName')]
        license_url=field('LicenseUrl') if rights=='cc_by_sa' else 'https://creativecommons.org/publicdomain/mark/1.0/'
        credit=artist['display_name']+'; Wikimedia Commons; '+field('Credit')
        if rights=='cc_by_sa':credit+='; photograph: Tzim78 (https://commons.wikimedia.org/wiki/User:Tzim78); '+field('LicenseShortName')+' ('+license_url+')'
        work=source_work(artist,prior,prior['title'],date,'commons-artwork',page['title'],info['descriptionurl'],info['url'],row['commons_receipt'],page,
            rights,field('LicenseShortName'),credit,'Existing artwork Wikidata P18 identifies this exact Commons file; explicit Commons maker, subject and compatible source creation date match the existing record.')
        work.update(license_url=license_url,commons_sha1=info['sha1'],commons_size=info['size'],independently_verified_rights=True,
            wikidata_identity_receipt=row['receipt'],rights_basis='Exact Commons per-file licence with preserved creator, photographer and source credits.')
        if row['wikidata']=='Q128258459':
            work['source_identifier_conflict']='Commons markup links unrelated Q128258342 (a Dyckmans still life); that identifier is not adopted. Existing Q128258459 explicitly identifies this file, whose visible title, creator and 1878 date independently match May Day on Corfu.'
        selected.append(work)
    m.save_atomic(RUN/'specific-selected.json',selected);print('Specific existing gaps selected',len(selected),flush=True)


def replace_evidence(path,value):
    if path.exists():
        if read(path)==value:return
        archive=RUN/'revision-history'/(path.parent.name+'-'+path.stem+'-'+m.core.sha(path.read_bytes())[:12]+'.json')
        m.save_atomic(archive,path.read_bytes());path.unlink()
    m.save_atomic(path,value)


def refine_review():
    decisions=read(RUN/'review-decisions.json');selected={}
    for name in ('museum-selected.json','wikiart-selected.json','commons-selected.json','native-selected.json'):
        for w in read(RUN/name):selected.setdefault(w['id'],w)
    for hold in decisions['holds']:
        wid=hold['artwork_id'];path=RUN/'prepared'/(wid+'.json');out=RUN/'prepared-held'/path.name
        if path.exists():
            m.save_atomic(out,path.read_bytes());path.unlink()
        elif not out.exists():m.save_atomic(out,{'work':selected[wid],'preparation_skipped':True})
    works=read(RUN/'commons-selected.json')
    for w in works:
        if w['rights_status'] not in ('cc_by','cc_by_sa'):continue
        markup=w['source_metadata']['revisions'][0]['slots']['main']['*']
        author=re.search(r'\|\s*author\s*=\s*(.*)',markup,re.I)
        if not author:continue
        user=re.search(r'\[\[User:([^|\]]+)(?:\|[^\]]+)?\]\]',author[1],re.I)
        if not user:raise ValueError('Photographer credit requires review: '+w['title'])
        w['creator_credit']=w['artist']['display_name']+'; photograph: '+user[1]+' (https://commons.wikimedia.org/wiki/User:'+quote(user[1])+'); Wikimedia Commons; '+w['license_label']+' ('+w['license_url']+')'
        path=RUN/'prepared'/(w['id']+'.json')
        if path.exists():
            im=read(path);im['work']['creator_credit']=w['creator_credit'];replace_evidence(path,im)
    replace_evidence(RUN/'commons-selected.json',works)
    _,receipt=fetch('https://api.artic.edu/docs/')
    works=read(RUN/'native-selected.json')
    for w in works:
        if 'www.artic.edu/iiif' not in w['image_url']:continue
        w['image_url']=w['image_url'].replace('/full/!1200,1200/','/full/843,/')
        w['image_variant_evidence']={'documentation':receipt,'reason':'Official IIIF Image API documentation publishes full/843,/0/default.jpg as the public website image variant; larger 1200-pixel request returned 403 and is not retried.'}
    replace_evidence(RUN/'native-selected.json',works)
    print('Review refinements saved; prepared',len(list((RUN/'prepared').glob('*.json'))),'cooldown',m.core.provider_cooldown_seconds('upload.wikimedia.org'),flush=True)


def schema_review():
    decisions=read(RUN/'review-decisions.json');changes=[]
    allowed={'painting','fresco','manuscript_illumination','drawing','watercolor','print','unknown'}
    for p in sorted((RUN/'prepared').glob('*.json')):
        im=read(p);w=im['work']
        if not w['new_record'] or w['scheme']!='commons-artwork':continue
        metadata=w['source_metadata'];markup=metadata['revisions'][0]['slots']['main']['*'];ext=metadata['imageinfo'][0]['extmetadata']
        categories=ext.get('Categories',{}).get('value','');maker=' '.join(re.findall(r'\|\s*artist\s*=[^\n]*',markup,re.I))
        if re.search(r'attributed|workshop|school|circle of|after |possibly|follower|anonymous|unknown|uncertain',maker,re.I):
            if (RUN/'applied/local'/p.name).exists() or (RUN/'applied/cloud'/p.name).exists():raise ValueError('Held attribution was already applied')
            hold={'artwork_id':w['id'],'reason':'Raw Commons artist wording is qualified: '+maker+'. Do not assign a held attribution as primary creator.'}
            decisions['holds'].append(hold);m.save_atomic(RUN/'prepared-held'/p.name,p.read_bytes());p.unlink();continue
        modified=False
        if w['work_type']=='icon':
            evidence=markup+' '+categories
            painted=bool(re.search(r'object[ _]type\s*=\s*painting|paintings|oil|tempera',evidence,re.I))
            # Tree of Jesse is explicitly a painted icon in its file description and image.
            if w['id']=='1178e957-b105-5980-8615-713e62e0d833':painted=True
            w['work_type']='painting' if painted else 'unknown';w['object_form']='icon';modified=True
            w['classification_review']='Use existing icon object_form independently of work_type; painted form supported by source object type, medium, painting category or inspected painted panel.'
        if re.search(r'\bicons\b',categories,re.I) and w.get('object_form')!='icon':w['object_form']='icon';modified=True
        licenses=re.findall(r'cc-by-sa-([1-4]\.0)',markup,re.I)
        if licenses and w['rights_status']=='public_domain':
            version=licenses[0];w['rights_status']='cc_by_sa';w['license_url']='https://creativecommons.org/licenses/by-sa/'+version+'/'
            w['license_label']='CC BY-SA '+version+' (reproduction); artwork labelled public domain'
            if w['id']=='1178e957-b105-5980-8615-713e62e0d833':
                w['creator_credit']='Theodore Poulakis; photograph: Tilemahos Efthimiadis (https://www.flickr.com/people/64379474@N00); source photograph https://www.flickr.com/photos/telemax/8384481474/; Wikimedia Commons; '+w['license_label']+' ('+w['license_url']+')'
            else:w['creator_credit']+='; reproduction source: Österreichische Galerie Belvedere; '+w['license_label']+' ('+w['license_url']+')'
            w['rights_basis']='Preserve both the Commons artwork public-domain label and the explicitly stated reproduction CC BY-SA licence in raw file markup; photographer/source credits and derivative changes retained.';modified=True
        if w['work_type'] not in allowed:raise ValueError('Unsupported artwork type remains')
        if modified:
            if (RUN/'applied/local'/p.name).exists() or (RUN/'applied/cloud'/p.name).exists():raise ValueError('Do not rewrite applied preparation evidence')
            replace_evidence(p,im);changes.append({'artwork_id':w['id'],'work_type':w['work_type'],'object_form':w.get('object_form'),'rights_status':w['rights_status']})
    replace_evidence(RUN/'review-decisions.json',decisions)
    m.save_atomic(RUN/'schema-and-credit-review.json',{'at':m.core.now(),'changes':changes,'basis':'Existing migrations 0012 and 0017; raw per-file attribution and licence metadata audited across all selected Commons files.'})
    print('Schema and credit review',len(changes),'corrections; prepared',len(list((RUN/'prepared').glob('*.json'))),flush=True)


def visual_assets():
    from PIL import Image,ImageOps,ImageDraw
    import textwrap
    changed=[];metadata_holds=[]
    for p in sorted((RUN/'prepared').glob('*.json')):
        im=read(p);w=im['work'];reason=None
        if w['scheme']=='commons-artwork' and w['creation_year_start']==w['artist']['birth_year'] and w['creation_year_end']==w['artist']['death_year']:
            reason='Source date equals the entire creator lifespan; artwork creation requires independent clarification.'
        if reason:
            (RUN/'prepared-held').mkdir(parents=True,exist_ok=True);p.rename(RUN/'prepared-held'/p.name)
            metadata_holds.append({'artwork_id':w['id'],'reason':reason});continue
        if w['new_record'] and html.unescape(w['title'])!=w['title']:
            before=w['title'];w['title']=html.unescape(w['title']);archive=RUN/'prepared-history'/(p.stem+'-'+m.core.sha(p.read_bytes())[:12]+'.json')
            archive.parent.mkdir(parents=True,exist_ok=True);p.rename(archive);m.save_atomic(p,im)
            changed.append({'artwork_id':w['id'],'before':before,'after':w['title'],'reason':'Decode source HTML entities in display title, retaining raw source metadata.'})
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))];aids=sorted({im['work']['artist']['id'] for im in images})
    def fingerprint(path):
        with Image.open(path) as image:
            image=ImageOps.exif_transpose(image);ratio=image.width/image.height;gray=ImageOps.grayscale(image)
            a=list(gray.resize((9,8)).getdata());b=list(gray.resize((8,9)).getdata())
            bits=[a[y*9+x]>a[y*9+x+1] for y in range(8) for x in range(8)]
            bits += [b[y*8+x]>b[(y+1)*8+x] for y in range(8) for x in range(8)]
            value=0
            for bit in bits:value=(value<<1)|int(bit)
        return ratio,value
    with m.read_only() as db:
        rows=db.execute('''SELECT aa.artist_id::text,a.id::text artwork_id,a.title,ma.storage_path path,ma.checksum_sha256 sha256
            FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN media_assets ma ON ma.id=a.primary_media_id
            WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ''',(aids,)).fetchall()
    pool=collections.defaultdict(list);missing=[]
    for row in rows:
        path=ROOT/'apps/web/public'/row['path'].lstrip('/')
        if not path.is_file():missing.append(row);continue
        pool[row['artist_id']].append((row,*fingerprint(path)))
    pairs=[]
    for im in images:
        row={'artwork_id':im['work']['id'],'title':im['work']['title'],'path':im['path'],'sha256':im['sha256']}
        ratio,fp=fingerprint(ROOT/'apps/web/public'/im['path'].lstrip('/'))
        for other,oratio,ofp in pool[im['work']['artist']['id']]:
            if abs(ratio/oratio-1)<=.08 and (fp^ofp).bit_count()<=17:
                pairs.append({'candidate':row,'other':other,'distance':(fp^ofp).bit_count(),'reason':'Composition comparison only; requires visual decision.'})
        pool[im['work']['artist']['id']].append((row,ratio,fp))
    total_images=len(images)
    if (RUN/'reviewed-visual-manifests.json').exists():
        inspected={wid for name in read(RUN/'reviewed-visual-manifests.json') for wid in read(RUN/name)['prepared_ids']}
        images=[im for im in images if im['work']['id'] not in inspected]
    stamp=str(len(images))+'-'+str(int(time.time()));sheets=[]
    for n in range(0,len(images),20):
        canvas=Image.new('RGB',(1500,1250),'#f4f4f4');draw=ImageDraw.Draw(canvas)
        for j,im in enumerate(images[n:n+20]):
            x=(j%5)*300;y=(j//5)*312
            with Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/')) as source:
                tile=ImageOps.contain(source.convert('RGB'),(290,232));canvas.paste(tile,(x+(300-tile.width)//2,y))
            label=f"{n+j}: {im['work']['title']}\n{im['work']['artist']['display_name']} | {im['work']['date_display']}"
            draw.text((x+5,y+235),'\n'.join(textwrap.wrap(label,42))[:220],fill='#111111')
        out=Path('/tmp')/('artline-greek-'+stamp+'-'+str(n//20)+'.jpg');canvas.save(out,quality=93)
        m.save_atomic(BACKUP/'visual-review'/out.name,out.read_bytes());sheets.append(str(out))
    duplicates=[]
    for n in range(0,len(pairs),6):
        group=pairs[n:n+6];canvas=Image.new('RGB',(1000,250*len(group)),'white');draw=ImageDraw.Draw(canvas)
        for j,pair in enumerate(group):
            for k,field in enumerate(('candidate','other')):
                item=pair[field]
                with Image.open(ROOT/'apps/web/public'/item['path'].lstrip('/')) as source:
                    tile=ImageOps.contain(source.convert('RGB'),(370,205));canvas.paste(tile,(k*500+5,j*250+35))
                draw.text((k*500+5,j*250+4),str(n+j)+' '+item['title'][:70],fill='black')
        out=Path('/tmp')/('artline-greek-duplicates-'+stamp+'-'+str(n//6)+'.jpg');canvas.save(out,quality=93)
        m.save_atomic(BACKUP/'visual-review'/out.name,out.read_bytes());duplicates.append(str(out))
    result={'at':m.core.now(),'total_images':total_images,'prepared_ids':[im['work']['id'] for im in images],'metadata_holds':metadata_holds,'title_normalizations':changed,
        'existing_images_compared':len(rows)-len(missing),'missing_local_reference_images':missing,'pairs':pairs,'sheets':sheets,'duplicate_sheets':duplicates}
    m.save_atomic(RUN/('visual-review-'+stamp+'.json'),result)
    print(json.dumps({'images':len(images),'pairs':len(pairs),'sheets':sheets,'duplicate_sheets':duplicates,'missing_references':len(missing)},ensure_ascii=False),flush=True)


def compress_selected(raw,work):
    info=work.get('source_metadata',{}).get('imageinfo',[{}])[0]
    if info.get('width',0)*info.get('height',0)<=40_000_000:return m.core.compress(raw)
    from PIL import Image,ImageOps
    import warnings
    if info['width']*info['height']>125_000_000:raise ValueError('Original exceeds bounded selected source dimensions')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as opened:
            if opened.format!='JPEG' or opened.size!=(info['width'],info['height']):raise ValueError('Large selected JPEG differs from exact source metadata')
            opened.draft('RGB',(2400,2400))
            if opened.width*opened.height>40_000_000:raise ValueError('JPEG decoder did not downsample safely')
            opened.load();image=ImageOps.exif_transpose(opened).convert('RGB')
            image.thumbnail((2400,2400),Image.Resampling.LANCZOS)
            intermediate=io.BytesIO();image.save(intermediate,'PNG')
    return m.core.compress(intermediate.getvalue())


def prepare(filename):
    unavailable_hosts=set()
    for work in read(RUN/filename):
        path=RUN/'prepared'/(work['id']+'.json')
        if path.exists() or (RUN/'prepared-held'/path.name).exists():continue
        original=ORIGINALS/(work['id']+'.original')
        if original.exists():raw=original.read_bytes()
        else:
            parsed=urlsplit(work['image_url'])
            download_url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,'','')) if parsed.netloc=='upload.wikimedia.org' else work['image_url']
            host=urlparse(download_url).hostname
            if host in unavailable_hosts:continue
            if m.core.provider_cooldown_seconds(host)>0:
                print('Source cooldown; deferred',work['title'],flush=True);continue
            m.core.provider_rate_slot(host)
            if host=='upload.wikimedia.org':time.sleep(5)
            response=m.requests.get(download_url,headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected catalogue research)'},timeout=(15,45))
            if response.status_code==429:
                pause=max(900,m.core.retry_delay(response.headers.get('Retry-After')))
                m.core.provider_rate_slot(host,cooldown=pause)
                m.save_atomic(RUN/'download-holds'/(work['id']+'-'+str(int(time.time()))+'.json'),
                    {'at':m.core.now(),'work':work,'status':429,'retry_after':response.headers.get('Retry-After'),'cooldown_seconds':pause})
                print('Source requested cooldown; deferred',work['title'],flush=True);continue
            if response.status_code in (401,403,404):
                m.save_atomic(RUN/'download-holds'/(work['id']+'-'+str(int(time.time()))+'.json'),
                    {'at':m.core.now(),'work':work,'status':response.status_code,'reason':'Public source image unavailable; no restricted access or alternate host attempted.'})
                if response.status_code in (401,403):unavailable_hosts.add(host)
                print('Public image unavailable; deferred',work['title'],response.status_code,flush=True);continue
            response.raise_for_status();raw=response.content
            if len(raw)>64_000_000:raise ValueError('Selected image exceeds bounded archival original limit')
            m.save_atomic(original,raw)
        if work.get('commons_sha1') and (hashlib.sha1(raw).hexdigest()!=work['commons_sha1'] or len(raw)!=work['commons_size']):
            raise ValueError('Selected Commons original differs')
        content,width,height,quality=compress_selected(raw,work);checksum=m.core.sha(content)
        image_path='/assets/artworks/imported/greek-images-20260920/'+work['id']+'-'+checksum[:16]+'.jpg'
        if len(content)>100000:raise ValueError('Derivative exceeds image size limit')
        m.save_atomic(ROOT/'apps/web/public'/image_path.lstrip('/'),content)
        prepared={'work':work,'id':uid('media/'+checksum),'path':image_path,'sha256':checksum,'bytes':len(content),
            'width':width,'height':height,'quality':quality,'original':str(original),'original_sha256':m.core.sha(raw),'checked_at':m.core.now()}
        m.save_atomic(path,prepared)
        print('Prepared',work['title'],len(content),'bytes',flush=True)


def target_state(db,im):
    w=im['work']
    artist=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE slug=%s',(w['artist']['slug'],)).fetchone()
    if not artist or not m.same_artwork(artist['record'],w['artist']):raise ValueError('Painter identity changed')
    exact=db.execute("""SELECT a.id::text FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
        WHERE e.scheme=%s AND e.external_id=%s""",(w['scheme'],w['source_id'])).fetchall()
    record=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(w['id'],)).fetchone()
    record=record['record'] if record else None
    if any(r['id']!=w['id'] for r in exact):raise ValueError('Source identifier belongs to another artwork')
    if w['new_record']:
        if record is not None and record['primary_media_id']!=im['id']:raise ValueError('New artwork ID is already occupied')
        duplicates=db.execute("""SELECT a.id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
            WHERE aa.artist_id=%s AND a.normalized_title=%s AND a.status<>'archived' AND a.id<>%s""",
            (artist['record']['id'],m.norm(w['title']),w['id'])).fetchall()
        if duplicates:raise ValueError('Existing painter/title needs reconciliation')
    elif (record is None or not m.same_artwork(record,w['before_record'])
        or record['current_institution_id']!=w['before_record']['current_institution_id']):raise ValueError('Existing artwork identity differs')
    creators=db.execute("""SELECT p.slug,aa.attribution_role FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id
        WHERE aa.artwork_id=%s ORDER BY p.slug""",(w['id'],)).fetchall() if record else []
    if record and creators!=[{'slug':w['artist']['slug'],'attribution_role':'primary'}]:raise ValueError('Artwork creator differs')
    if record and record['primary_media_id'] not in (None,im['id']):raise ValueError('Existing primary image preserved')
    return {'artist':artist['record'],'artwork':record,'creators':creators,'source_identifiers':exact}


def plan_delivery():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    if not (RUN/'visual-review-approved.json').exists():raise ValueError('Visual review is incomplete')
    approval=read(RUN/'visual-review-approved.json');approved=approval['approved']
    if {i['work']['id']:i['sha256'] for i in images}!=approved:raise ValueError('Visual review does not cover exact images')
    if m.core.sha((RUN/'target-id-reconciliation.json').read_bytes())!=approval['target_mapping_sha256']:raise ValueError('Reviewed target identities changed')
    if any(m.core.sha((RUN/'prepared'/(wid+'.json')).read_bytes())!=checksum for wid,checksum in approval['prepared_evidence'].items()):raise ValueError('Reviewed preparation evidence changed')
    if len({i['id'] for i in images})!=len(images):raise ValueError('Duplicate selected image')
    for im in images:
        if im['work']['creation_year_end'] is None or im['work']['creation_year_end']>1955:raise ValueError('Image date is ineligible')
        if m.core.sha(Path(im['original']).read_bytes())!=im['original_sha256']:raise ValueError('Original differs')
        source=im['work']['source_receipt']
        if m.core.sha((ROOT/source['path']).read_bytes())!=source['sha256']:raise ValueError('Source receipt differs')
        data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        if m.core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:raise ValueError('Selected local derivative differs')
    for target,dsn in target_dsns():
        with m.read_only(dsn) as db:
            for im in images_for_target(target):
                path=RUN/'delivery-plans'/target/(im['work']['id']+'.json')
                if path.exists():continue
                state=target_state(db,im);backup=BACKUP/'preimages'/target/path.name
                media=db.execute('SELECT to_jsonb(ma) record FROM media_assets ma WHERE id=%s',(im['id'],)).fetchone()
                if media:raise ValueError('Selected media ID already exists')
                duplicates=db.execute('SELECT id::text FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchall()
                if duplicates:raise ValueError('Exact image already exists and needs reconciliation: '+im['work']['title'])
                m.save_atomic(backup,{'target':state,'media_before':media})
                m.save_atomic(path,{'state':state,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes())})
            print('Recovery plans',target,len(images),flush=True)


def preflight():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))];problems=[]
    for target,dsn in target_dsns():
        with m.read_only(dsn) as db:
            for im in images_for_target(target):
                try:
                    target_state(db,im)
                    dup=db.execute('SELECT id::text FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchall()
                    if dup:raise ValueError('Exact image already exists: '+str(dup))
                except ValueError as error:problems.append({'target':target,'artwork_id':im['work']['id'],'title':im['work']['title'],'reason':str(error)})
    result={'at':m.core.now(),'images':len(images),'target':TARGET,'problems':problems}
    m.save_atomic(RUN/('preflight-'+TARGET+'-'+str(int(time.time()))+'.json'),result)
    print(json.dumps(result,ensure_ascii=False),flush=True)


def approve_visual():
    manifests=read(RUN/'reviewed-visual-manifests.json');reviewed=set();evidence=[]
    for name in manifests:
        path=RUN/name;manifest=read(path);reviewed.update(manifest['prepared_ids'])
        evidence.append({'manifest':name,'sha256':m.core.sha(path.read_bytes()),
            'sheets':[{'file':p,'sha256':m.core.sha(Path(p).read_bytes())} for p in manifest['sheets']+manifest['duplicate_sheets']]})
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    if any(im['work']['id'] not in reviewed for im in images):raise ValueError('Unreviewed image remains')
    held={h['artwork_id'] for h in read(RUN/'review-decisions.json')['holds']}
    if held & {im['work']['id'] for im in images}:raise ValueError('Held image remains in delivery')
    replace_evidence(RUN/'visual-review-approved.json',{'at':m.core.now(),'approved':{im['work']['id']:im['sha256'] for im in images},
        'review_evidence':evidence,'decisions_sha256':m.core.sha((RUN/'review-decisions.json').read_bytes()),
        'target_mapping_sha256':m.core.sha((RUN/'target-id-reconciliation.json').read_bytes()),
        'prepared_evidence':{im['work']['id']:m.core.sha((RUN/'prepared'/(im['work']['id']+'.json')).read_bytes()) for im in images},
        'review':'All listed contact sheets and duplicate pairs visually inspected; source identities, dates, source frame, image quality and attribution credits checked. Holds are excluded without deleting catalogue records.'})
    print('Approved images',len(images),flush=True)


def apply_one(db,im,target):
    w=im['work'];plan=read(RUN/'delivery-plans'/target/(w['id']+'.json'))
    if m.core.sha(Path(plan['backup']).read_bytes())!=plan['backup_sha256']:raise ValueError('Recovery preimage differs')
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    with db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(plan['state']['artist']['id'],))
        current=target_state(db,im)
        if current['artwork'] and current['artwork']['primary_media_id']==im['id']:
            return {'outcome':'already_attached','created':w['new_record'],'after':current['artwork']}
        if current!=plan['state']:raise ValueError('Target changed after recovery snapshot')
        sid=db.execute("""INSERT INTO sources(id,slug,name,source_type,base_url)
            VALUES(%s,'greek-images-20260920','Greek painters: selected museum, artist and heritage image evidence','collection_page','https://www.nationalgallery.gr/')
            ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id""",(uid('source'),)).fetchone()['id']
        if w['new_record']:
            db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
                work_type,medium_text,accession_number,object_form,status,research_candidate,created_by,updated_by)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",
                (w['id'],w['slug'],w['title'],m.norm(w['title']),w['date_display'],w['creation_year_start'],w['creation_year_end'],w['date_precision'],
                 w['work_type'],w.get('medium_text'),w.get('accession_number'),w.get('object_form'),m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                (w['id'],current['artist']['id'],w['attribution_basis']))
            db.execute("""INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                VALUES('artwork',%s,%s,%s,%s,%s,%s)""",(w['id'],w['scheme'],w['source_id'],w['source_url'],sid,im['checked_at']))
        credit=w['creator_credit']+'. Source frame preserved; proportionally resized and JPEG compressed.'
        db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
            checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
            VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (im['id'],im['path'],w['source_url'],'WikiArt' if w['scheme']=='wikiart-artwork' else 'Wikimedia Commons' if w['scheme']=='commons-artwork' else 'Greek museum/artist source',
             im['width'],im['height'],im['bytes'],im['sha256'],w['title']+' — '+w['artist']['display_name'],w['rights_status'],w['license_label'],
             w['license_url'],w['creator_credit'],credit,im['checked_at'],im['checked_at'] if w.get('independently_verified_rights') else None,m.ACTOR))
        db.execute("""INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,
            rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,'greek-selected-v1',%s,%s)""",
            (im['id'],sid,w['source_id'],w['source_receipt']['sha256'],w['image_url'],w['license_url'],w['rights_basis'],im['checked_at'],m.Jsonb(im)))
        db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
            VALUES('artwork',%s,%s,'greek_image_identity',%s,%s,%s,%s,%s)""",
            (w['id'],sid,w['source_id'],w['source_url'],json.dumps(w,ensure_ascii=False),im['checked_at'],m.ACTOR))
        db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',
            (im['id'],m.ACTOR,w['id']))
        already=db.execute('SELECT artline_has_selection_evidence(%s) selected',(w['id'],)).fetchone()['selected']
        if w['new_record'] or not already:
            collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
            if collection['curator_kind']!='owner' or collection['institution_id'] is not None:raise ValueError('Personal collection identity differs')
            before_items=db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE collection_id=%s AND artwork_id=%s',(collection_id,w['id'])).fetchall()
            m.save_atomic(BACKUP/'personal-selection'/target/(w['id']+'.json'),{'collection':collection,'items':before_items})
            db.execute("""INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                SELECT %s,%s,coalesce(max(position),0)+1,%s,%s,%s,%s FROM curated_collection_items WHERE collection_id=%s
                ON CONFLICT(collection_id,artwork_id) DO NOTHING""",(collection_id,w['id'],w['selection_basis'],sid,w['source_url'],im['checked_at'],collection_id))
            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
        after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(w['id'],)).fetchone()['record']
    return {'outcome':'attached','created':w['new_record'],'before':plan['state']['artwork'],'after':after}


def deliver():
    approval=read(RUN/'visual-review-approved.json')
    if m.core.sha((RUN/'target-id-reconciliation.json').read_bytes())!=approval['target_mapping_sha256']:raise ValueError('Reviewed target identities changed')
    if any(m.core.sha((RUN/'prepared'/(wid+'.json')).read_bytes())!=checksum for wid,checksum in approval['prepared_evidence'].items()):raise ValueError('Reviewed preparation evidence changed')
    bucket=m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET) if TARGET!='local' else None
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    if {im['work']['id']:im['sha256'] for im in images}!=approval['approved']:raise ValueError('Unapproved image in delivery')
    mappings=read(RUN/'target-id-reconciliation.json')
    for im in images if bucket else []:
        output=RUN/'uploads'/(im['work']['id']+'.json')
        if output.exists():continue
        data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        if m.core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:raise ValueError('Selected image differs')
        blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],
            'artwork-id':mappings.get(im['work']['id'],{}).get('cloud_artwork_id',im['work']['id']),'local-artwork-id':im['work']['id']};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except m.PreconditionFailed:blob.reload(timeout=30)
        if blob.size!=len(data) or blob.md5_hash!=m.base64.b64encode(hashlib.md5(data).digest()).decode():raise ValueError('Uploaded bytes differ')
        m.save_atomic(output,{'at':m.core.now(),'path':im['path'],'sha256':im['sha256'],'generation':blob.generation})
    for target,dsn in target_dsns():
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            for im in images_for_target(target):
                path=RUN/'applied'/target/(im['work']['id']+'.json')
                if path.exists():continue
                result=apply_one(db,im,target);m.save_atomic(path,result)
                print('Attached',target,im['work']['artist']['display_name'],im['work']['title'],flush=True)


def verify_public_files():
    images=images_for_target('cloud');base='https://artline-web-lpuqqlugnq-ew.a.run.app'
    def one(im):
        result={'artwork_id':im['work']['id'],'path':im['path'],'expected_sha256':im['sha256'],'at':m.core.now()}
        try:
            response=m.requests.get(base+im['path'],timeout=(15,45))
            result.update(http_status=response.status_code,bytes=len(response.content),sha256=m.core.sha(response.content),
                verified=response.status_code==200 and len(response.content)==im['bytes'] and m.core.sha(response.content)==im['sha256'])
        except m.requests.RequestException as error:result.update(verified=False,error=str(error)[:250])
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(one,images))
    result={'at':m.core.now(),'checks':checks,'verified':sum(c['verified'] for c in checks),'images':len(images)}
    replace_evidence(RUN/'public-file-verification.json',result)
    print({k:v for k,v in result.items() if k!='checks'},flush=True)
    if result['verified']!=len(images):raise SystemExit(1)


def verify():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    expected={im['work']['id']:im for im in images};errors=[];targets={};baseline=read(RUN/'baseline.json')
    for im in images:
        data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        if m.core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:
            errors.append({'artwork_id':im['work']['id'],'error':'Local image bytes differ'})
    ignored={'primary_media_id','revision','updated_at','updated_by'}
    for target,dsn in target_dsns():
        expected={im['work']['id']:im for im in images_for_target(target)}
        with m.read_only(dsn) as db:
            ids=list(expected)
            rows=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(ma) media,
                artline_has_selection_evidence(a.id) selected FROM artworks a
                JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])''',(ids,)).fetchall()
            byid={r['artwork']['id']:r for r in rows};checks=[]
            for aid,im in expected.items():
                w=im['work'];r=byid.get(aid);receipt_path=RUN/'applied'/target/(aid+'.json')
                problems=[]
                if not r or not receipt_path.exists():
                    errors.append({'target':target,'artwork_id':aid,'error':'Missing artwork/media or delivery receipt'});continue
                receipt=read(receipt_path);media=r['media']
                if r['artwork']!=receipt['after']:problems.append('Artwork differs from committed receipt')
                if not r['selected']:problems.append('Missing owner or museum selection evidence')
                for k,v in {'id':im['id'],'storage_path':im['path'],'checksum_sha256':im['sha256'],'byte_size':im['bytes'],
                    'width':im['width'],'height':im['height'],'rights_status':w['rights_status'],'source_page_url':w['source_url'],
                    'license_label':w['license_label'],'license_url':w['license_url'],'creator_credit':w['creator_credit']}.items():
                    if media[k]!=v:problems.append('Media field differs: '+k)
                if w['rights_status'] in ('unknown','restricted') and media['verified_at'] is not None:problems.append('Unresolved rights incorrectly verified')
                evidence=db.execute('SELECT evidence_json FROM media_rights_evidence WHERE media_id=%s',(im['id'],)).fetchall()
                if [e['evidence_json'] for e in evidence]!=[im]:problems.append('Source evidence differs')
                citations=db.execute("SELECT evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name='greek_image_identity'",(aid,)).fetchall()
                if len(citations)!=1 or json.loads(citations[0]['evidence_note'])!=w:problems.append('Identity citation differs')
                state=target_state(db,im)
                if w['new_record'] and (state['artwork']['status']!='review' or not state['artwork']['research_candidate'] or state['artwork']['current_institution_id'] is not None):
                    problems.append('New record review/holding state differs')
                if w['new_record']:
                    for key in ('title','creation_year_start','creation_year_end','date_display','date_precision','work_type','object_form','medium_text'):
                        if state['artwork'][key]!=w.get(key):problems.append('New artwork source field differs: '+key)
                checks.append({'artwork_id':aid,'verified':not problems,'new_record':w['new_record']})
                errors.extend({'target':target,'artwork_id':aid,'error':p} for p in problems)
            cohort=[]
            for before in baseline['targets'][target]:
                artist=before['artist'];current=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(artist['id'],)).fetchone()['record']
                if current!=artist:errors.append({'target':target,'artist_id':artist['id'],'error':'Painter profile changed'})
                countries=db.execute('SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=%s',(artist['id'],)).fetchall()
                if sorted([r['record'] for r in countries],key=lambda x:x['country_code'])!=sorted(before['countries'] or [],key=lambda x:x['country_code']):
                    errors.append({'target':target,'artist_id':artist['id'],'error':'Painter country association changed'})
                works=c.artist_works(db,artist['id']);now={w['artwork_id']:w for w in works}
                old=read(RUN/'catalogue'/target/(artist['id']+'.json'))
                for previous in old:
                    wid=previous['artwork_id'];latest=now.get(wid);excluded=ignored if wid in expected else set()
                    if not latest or {k:v for k,v in latest['before_record'].items() if k not in excluded}!={k:v for k,v in previous['before_record'].items() if k not in excluded}:
                        errors.append({'target':target,'artwork_id':wid,'error':'Existing artwork metadata changed'})
                cohort.append({'artist_id':artist['id'],'artist':artist['display_name'],'slug':artist['slug'],
                    'before_works':before['works'],'before_images':before['images'],
                    'after_works':sum(w['status']!='archived' for w in works),
                    'after_images':sum(w['status']!='archived' and w['primary_media_id'] is not None for w in works),
                    'remaining_gaps':[{'artwork_id':w['artwork_id'],'title':w['title'],'date_display':w['date_display'],
                        'creation_year_start':w['creation_year_start'],'creation_year_end':w['creation_year_end'],
                        'reason':'Creation date unresolved' if w['creation_year_end'] is None else ('After the 1955 image cutoff' if w['creation_year_end']>1955 else 'No selected, exact-object image identified in reviewed sources')}
                        for w in works if w['status']!='archived' and w['primary_media_id'] is None]})
            targets[target]={'verified':sum(x['verified'] for x in checks),'checks':checks,'cohort':cohort}
    base='https://artline-web-lpuqqlugnq-ew.a.run.app'
    cached_files={r['path']:r for r in read(RUN/'public-file-verification.json')['checks']} if (RUN/'public-file-verification.json').exists() else {}
    def check_public(im):
        w=im['work'];local=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        result={'artwork_id':w['id'],'local_file_verified':m.core.sha(local)==im['sha256'] and len(local)==im['bytes'] and len(local)<=100000}
        try:
            cached=cached_files.get(im['path'])
            if cached and cached.get('verified') and cached['sha256']==im['sha256']:
                result.update(file_http_status=cached['http_status'],public_file_verified=True,file_checked_at=cached['at'],file_receipt='public-file-verification.json')
            else:
                response=m.requests.get(base+im['path'],timeout=(15,45))
                result.update(file_http_status=response.status_code,public_file_verified=response.status_code==200 and m.core.sha(response.content)==im['sha256'])
            response=m.requests.get(base+'/api/backend/v1/artists/'+w['artist']['slug']+'/works/'+w['id'],timeout=(15,45))
            data=response.json() if response.status_code==200 else {}
            result.update(api_http_status=response.status_code,api_verified=response.status_code==200 and data.get('title')==w['title'] and data.get('media_url')==im['path'])
        except m.requests.RequestException as e:result.update(error=str(e)[:200])
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:public=list(pool.map(check_public,images_for_target('cloud'))) if TARGET!='local' else []
    errors.extend({'error':'Public delivery check failed',**r} for r in public if not all(r.get(k) for k in ('local_file_verified','public_file_verified','api_verified')))
    result={'at':m.core.now(),'images':len(images),'new_artworks':sum(im['work']['new_record'] for im in images),
        'existing_gaps_filled':sum(not im['work']['new_record'] for im in images),'painters_with_additions':len({im['work']['artist']['id'] for im in images}),
        'rights':dict(collections.Counter(im['work']['rights_status'] for im in images)),
        'maximum_bytes':max(im['bytes'] for im in images),'total_bytes':sum(im['bytes'] for im in images),
        'targets':targets,'public_checks':public,'errors':errors}
    path=RUN/('verification-'+str(int(time.time()))+'.json');m.save_atomic(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('targets','public_checks')},ensure_ascii=False),flush=True)
    print('Verification receipt',path,flush=True)
    if errors:raise SystemExit(1)

def report():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))];receipts=sorted(RUN.glob('verification-*.json'))
    verified={}
    for path in receipts:
        value=read(path)
        if value['errors'] or value['images']!=len(images):continue
        for target in value['targets']:verified[target]=(path,value)
    if 'local' not in verified:raise ValueError('Local final verification is incomplete')
    path,verification=verified['local'];cohort=verification['targets']['local']['cohort'];decisions=read(RUN/'review-decisions.json')
    gaps=[{'artist':row['artist'],'artist_id':row['artist_id'],**gap} for row in cohort for gap in row['remaining_gaps']]
    holdmap={h['artwork_id']:h['reason'] for h in decisions['holds']}
    for gap in gaps:
        if gap['artwork_id'] in holdmap:gap['reason']=holdmap[gap['artwork_id']]
    summary={k:verification[k] for k in ('at','images','new_artworks','existing_gaps_filled','painters_with_additions','rights','maximum_bytes','total_bytes')}
    summary['at']=m.core.now()
    summary.update(reviewed_painters=len(cohort),works=sum(r['after_works'] for r in cohort),images_after=sum(r['after_images'] for r in cohort),remaining_gaps=len(gaps),
        verified_targets={target:{'receipt':p.name,'at':v['at'],'verified':v['targets'][target]['verified']} for target,(p,v) in verified.items()},
        production_status='Verified' if 'cloud' in verified else 'Delivery or verification in progress; '+str(len(list((RUN/'applied/cloud').glob('*.json'))))+' production transaction receipts recorded. Public verification is not yet complete.',
        source_counts=dict(collections.Counter(im['work']['scheme'] for im in images)),held_candidates=len(decisions['holds']),
        staged_unattached_uploads=[p.stem for p in (RUN/'uploads').glob('*.json') if p.stem not in {im['work']['id'] for im in images}])
    replace_evidence(RUN/'completion-summary.json',summary);replace_evidence(RUN/'painter-coverage.json',cohort);replace_evidence(RUN/'remaining-image-gaps.json',gaps)
    mappings=read(RUN/'target-id-reconciliation.json')
    delivered=[{'artwork_id':im['work']['id'],'cloud_artwork_id':mappings.get(im['work']['id'],{}).get('cloud_artwork_id',im['work']['id']),'artist_id':im['work']['artist']['id'],'artist':im['work']['artist']['display_name'],
        'title':im['work']['title'],'new_record':im['work']['new_record'],'date':im['work']['date_display'],'source_url':im['work']['source_url'],
        'media_path':im['path'],'rights':im['work']['rights_status'],'credit':im['work']['creator_credit'],'bytes':im['bytes'],'sha256':im['sha256']} for im in images]
    replace_evidence(RUN/'delivered-artworks.json',delivered)
    categories=collections.Counter('Date unresolved' if g['creation_year_end'] is None else 'After 1955' if g['creation_year_end']>1955 else 'Dated by 1955, source or identity unresolved' for g in gaps)
    state='local and production' if 'cloud' in verified else 'the local catalogue'
    text=f'''# Greek painter images — 20–21 September 2026

Completed in **{state}**: **{summary['images']} image attachments**, including **{summary['existing_gaps_filled']} existing image gaps** and **{summary['new_artworks']} new review artworks**, across **{summary['painters_with_additions']} painters**.

All **{len(cohort)} existing Greek-linked painter profiles** were reviewed. Local coverage increased from **460 artworks / 202 images** to **{summary['works']} artworks / {summary['images_after']} images**. **{len(gaps)} recorded works remain without images**. This selected expansion does not claim a complete illustrated catalogue.

**Production: {summary['production_status']}**

## Painter coverage

| Painter | New works | Added images | Total works | Total images | Remaining image gaps |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
    for row in cohort:
        added=[im for im in images if im['work']['artist']['id']==row['artist_id']]
        text+=f"| {row['artist']} | {sum(im['work']['new_record'] for im in added)} | {len(added)} | {row['after_works']} | {row['after_images']} | {len(row['remaining_gaps'])} |\n"
    text+='''
## Sources and review

The [National Gallery of Greece](https://www.nationalgallery.gr/en/), [WikiArt Greek directory](https://www.wikiart.org/en/artists-by-nation/greek), and bounded Commons artwork metadata searches were reviewed against the existing painter authorities. Fifteen matched WikiArt profiles were indexed; at most twelve new dated works per painter were selected. Commons metadata searches covered all 43 painters, with at most four new dated highlights per painter. Existing image gaps were prioritized. These are selected additions, not exhaustive image downloads.

Museum object identity, named creator, source object identifier and compatible creation date were checked before images were selected. Greek-linked is an existing database association, not an inferred citizenship. Anonymous and held attributions were not reassigned to a named painter. Work dates were not inferred from creator lifespans.

Five existing Chirico works use different local and production UUIDs. Exact native museum identifiers and identical semantic metadata reconciled them; each target retained its artwork and institution IDs. Two additional Commons files matched existing Wikidata P18 references: Pachis’s May Day on Corfu and Nikolaos Doxaras’s Assumption of Mary. A conflicting Commons Wikidata link for Pachis points to an unrelated Dyckmans still life; it was documented and not adopted. Source title, maker, creation date and the correct existing Wikidata file reference independently match.

New artworks remain `review` / `research_candidate` and belong to the personal owner collection. Source museum references remain evidence rather than accepted new holdings or current display assertions. Existing artwork metadata, artist profiles, country relationships and prior primary images passed preservation checks.

The [established image workflow](../../ARTLINE_IMAGE_USE.md) retains the conservative artwork creation cutoff of 1955 and actual source rights labels. Commons photographer credits and licence URLs are retained. Restricted and unknown rights are not marked independently verified. User collection authorization is not represented as copyright-holder permission.

## Holds and limits

'''
    text+=f"Remaining image gaps include **{categories['Date unresolved']} unresolved creation dates**, **{categories['After 1955']} works after 1955**, and **{categories['Dated by 1955, source or identity unresolved']} dated works needing an accessible exact-object image or identity reconciliation**. Retained image rights: **{summary['rights'].get('public_domain',0)} public domain**, **{summary['rights'].get('restricted',0)} restricted**, **{summary['rights'].get('cc_by_sa',0)} CC BY-SA**, and **{summary['rights'].get('cc_by',0)} CC BY**.\n\n"
    text+='''The review excludes duplicate compositions found under translated or alternative titles, captioned video-style reproductions, sculpture photographs outside this painting selection, Saint Stephen/Saint Alexis and Ascension/Trinity source-title conflicts, and creation ranges that merely repeat the artist's lifespan. Candidate evidence and originals remain preserved. Existing records were not merged or deleted. Vasileios Chatzis and Vasileios Hatzis remain separate existing authorities pending reconciliation.

Six Metropolitan Museum object APIs supplied no public image. The Art Institute of Chicago's documented public image variant returned HTTP 403; this provider was stopped for the batch. Wikimedia's HTTP 429 response was followed by a provider cooldown and slower requests, without alternate hosts or proxies. All selected Commons downloads subsequently completed. Eleven Chicago candidates remain held, with no access restrictions bypassed.

## Delivery and verification

'''
    text+=f"All {len(images)} attached derivatives were visually inspected, preserve the full supplied frame, and are at most **{summary['maximum_bytes']:,} bytes**, below the 100,000-byte limit. Full originals are separately archived. No generated art or reconstruction was used.\n\n"
    text+=f"Read-only final verification checked every attachment, local file checksum and byte size, source/rights evidence, identity citation, selection evidence, and new-record review status. It checked preservation of existing cohort records and painter profiles, with **zero errors**. These are bounded content checks, not catalogue-scale performance evidence.\n\n"
    if 'cloud' in verified:text+='Production database associations, all public image checksums and artwork detail API responses also passed verification. [Production verification]('+verified['cloud'][0].name+') and [public file checksums](public-file-verification.json) contain the exact results.\n\n'
    else:text+='Production delivery and public file/API verification are not yet complete. Local completion does not imply public availability.\n\n'
    text+=f'''Each update used a transaction, identity rechecks and exact recovery preimages. One staged source image remains unattached after its raw creator wording was found to be qualified; the asset and evidence were preserved. Fifteen sourced icons use the existing object-form field independently of artwork type. Two raw Commons reproduction licences were retained separately from their underlying public-domain artwork labels. No fixture, test database, commit, deployment or infrastructure change was used.

Recovery snapshots, personal collection snapshots, visual review and operation script: `{BACKUP}/`. Original reproductions: `{ORIGINALS}/`. Application derivatives: `apps/web/public/assets/artworks/imported/{RUN.name}/`.

[Completion summary](completion-summary.json) · [Delivered artworks](delivered-artworks.json) · [All painter coverage](painter-coverage.json) · [Remaining gaps](remaining-image-gaps.json) · [Review decisions](review-decisions.json) · [Visual approval](visual-review-approved.json) · [Local verification]({path.name})
'''
    (RUN/'README.md').write_text(text)
    stamp=str(int(time.time()));m.save_atomic(BACKUP/'completion'/('summary-'+stamp+'.json'),summary)
    m.save_atomic(BACKUP/'completion'/('README-'+stamp+'.md'),text.encode())
    m.save_atomic(BACKUP/'operations'/('greek-images-'+m.core.sha(Path(__file__).read_bytes())[:12]+'.py'),Path(__file__).read_bytes())
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("phase");parser.add_argument('--target',choices=['local','cloud','both'],default='both')
    args=parser.parse_args();TARGET=args.target;globals()[args.phase]()
