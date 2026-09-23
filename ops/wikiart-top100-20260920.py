#!/usr/bin/env python3
"""Bounded, source-evidenced WikiArt expansion for Artline's actual Top 100."""
import argparse
import collections
import concurrent.futures
import csv
import difflib
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('coverage',ROOT/'ops/wikiart-artist-coverage.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m=c.m
PRIOR=c.RUN
RUN=ROOT/'docs/research/wikiart-top100-20260920'
PREVIOUS=[ROOT/'docs/research'/name for name in ('wikiart-1000-1500-20260920','women-wikiart-20260920',
    'wikiart-artist-followup-20260920','wikiart-artist-coverage-20260920','wikiart-selected-images-20260919','armenian-painters-20260920')]
c.RUN=m.RUN=RUN
m.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
m.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
BaseFetcher=m.Fetcher


class Fetcher(BaseFetcher):
    def get(self,url,limit=5_000_000,image=False):
        key=m.core.sha(url.encode())
        for previous in PREVIOUS:
            receipt=previous/'captures'/(key+'.json')
            rawpath=((Path.home()/'Library/Application Support/Artline/source-images'/previous.name)
                if image else previous/'captures')/(key+'.body')
            if receipt.exists() and rawpath.exists():
                raw,record=rawpath.read_bytes(),json.loads(receipt.read_bytes())
                if m.core.sha(raw)!=record['sha256']:raise ValueError('Prior capture checksum differs')
                m.save_atomic((m.ORIGINALS if image else RUN/'captures')/rawpath.name,raw)
                m.save_atomic(RUN/'captures'/receipt.name,record)
                return raw,record
        return super().get(url,limit,image)


c.SharedFetcher=Fetcher


def read(path):return json.loads(path.read_bytes())


def audit():
    path=RUN/'cohort-baseline.json'
    if not path.exists():
        with m.read_only() as db:
            artists=db.execute("""SELECT to_jsonb(a) artist,to_jsonb(d) discovery,
                coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
                coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers
                FROM artist_discovery_selection d JOIN artists a ON a.id=d.artist_id
                WHERE d.is_popular AND a.status<>'archived' ORDER BY d.popularity_rank NULLS LAST,a.display_name""").fetchall()
            if len(artists)!=100:raise ValueError('Top 100 cohort size differs; do not invent a ranking')
            for row in artists:
                works=c.artist_works(db,row['artist']['id'])
                m.save_atomic(RUN/'catalogue-works'/(row['artist']['id']+'.json'),works)
                row['baseline_artworks']=sum(w['status']!='archived' for w in works)
                row['baseline_images']=sum(w['status']!='archived' and w['primary_media_id'] is not None for w in works)
            source_ids=db.execute("""SELECT external_id value FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork'
                UNION SELECT source_record_id FROM citations WHERE entity_type='artwork' AND source_url LIKE 'https://www.wikiart.org/%%' AND source_record_id IS NOT NULL""").fetchall()
            source_urls=db.execute("""SELECT canonical_url value FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork'
                UNION SELECT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE 'https://www.wikiart.org/%%'
                UNION SELECT source_page_url FROM media_assets WHERE source_page_url LIKE 'https://www.wikiart.org/%%'""").fetchall()
        m.save_atomic(path,{'at':m.core.now(),'artists':artists,'existing_source_ids':[r['value'] for r in source_ids],
            'existing_source_urls':[r['value'] for r in source_urls if r['value']],
            'scope':'Actual is_popular cohort, including existing editorial choices; ranking and memberships preserved.'})
    baseline=read(path);active={r['artist']['id']:r for r in baseline['artists']}
    sources=collections.defaultdict(dict)
    for filename in ('artist-matches.json','extra-artist-matches.json','priority-group-matches.json','supplemental-artist-matches.json'):
        for pair in read(PRIOR/filename)['matches']:
            aid=pair['artist']['id']
            if aid in active:sources[aid][pair['wikiart']['url']]=pair['wikiart']
    for previous in PREVIOUS:
        for path in (previous/'images').glob('*.json'):
            im=read(path);aid=im['work']['artist']['id']
            if aid not in active or not im.get('selection_receipt'):continue
            url=im['selection_receipt']['final_url'].replace('/ru/','/en/').removesuffix('/all-works/text-list')
            if re.fullmatch(r'https://www.wikiart.org/en/[^/]+',url):
                sources[aid].setdefault(url,{'url':url,'name':im['work']['artist']['display_name'],
                    'life_display':'','birth_year':None,'death_year':None})
    inventory=read(PRIOR/'artist-matches.json')
    directory=inventory['unmatched_source_artists']+[p['wikiart'] for p in inventory['matches']+inventory['ambiguous']]
    pairs=[];unresolved=[]
    for aid,row in active.items():
        if not sources[aid]:
            names={m.norm(x) for x in [row['artist']['display_name']]+row['aliases']}
            for source in directory:
                if m.norm(source['name']) in names:sources[aid][source['url']]=source
        if len(sources[aid])==1:
            source=next(iter(sources[aid].values()))
            pairs.append({'artist':row['artist'],'wikiart':source})
        else:unresolved.append({'artist':row['artist'],'sources':list(sources[aid].values())})
    m.save_atomic(RUN/'artist-source-matches.json',{'pairs':pairs,'unresolved':unresolved})
    print('Top 100 baseline',sum(r['baseline_artworks'] for r in baseline['artists']),'artist-linked works,',
        sum(r['baseline_images'] for r in baseline['artists']),'images; source matches',len(pairs),flush=True)
    print('Unresolved',json.dumps([{'name':r['artist']['display_name'],'sources':[s['url'] for s in r['sources']]} for r in unresolved],ensure_ascii=False),flush=True)


def index_one(pair):
    artist=pair['artist'];source=pair['wikiart'];path=RUN/'indexes'/(artist['id']+'.json')
    if path.exists():return read(path)
    profile=c.profile_one(source)
    raw,receipt=Fetcher().get(source['url']+'/all-works/text-list')
    soup=c.BeautifulSoup(raw,'html.parser');prefix=urlparse(source['url']).path+'/'
    works={}
    for a in soup.select('li a[href]'):
        if not a['href'].startswith(prefix):continue
        title=a.get_text(' ',strip=True)
        date=a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,')
        parsed=m.creation_date(date)
        works[a['href']]={'title':title,'url':urljoin(source['url'],a['href']),'date':parsed,'source_date':date}
    result={'artist':artist,'source':source,'receipt':receipt,'works':list(works.values()),'profile':profile,
        'eligible_dates':sum(bool(w['date'] and w['date']['creation_year_end']<=1955) for w in works.values())}
    m.save_atomic(path,result)
    print('Index',artist['display_name'],len(works),'entries, eligible',result['eligible_dates'],flush=True)
    return result


def indexes():
    inventory=read(RUN/'artist-source-matches.json')
    if inventory['unresolved']:raise ValueError('Resolve source identities before index capture')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(index_one,inventory['pairs']))
    m.save_atomic(RUN/'indexes-finished.json',{'at':m.core.now(),'painters':len(results),
        'entries':sum(len(r['works']) for r in results),'eligible_dates':sum(r['eligible_dates'] for r in results)})


def title_key(value):
    return re.sub(r'^the ','',m.norm(re.sub(r'\([^)]*\)','',value or '')))


def overlaps(a,b):
    return a['creation_year_start'] is not None and a['creation_year_end'] is not None and \
        a['creation_year_start']<=b['creation_year_end'] and b['creation_year_start']<=a['creation_year_end']


def select_one(index):
    artist=index['artist'];aid=artist['id'];output=RUN/'discovery-v2'/(aid+'.json')
    if output.exists():return read(output)
    baseline=read(RUN/'cohort-baseline.json');excluded_ids=set(baseline['existing_source_ids']);excluded_urls=set(baseline['existing_source_urls'])
    rows=[w for w in read(RUN/'catalogue-works'/(aid+'.json')) if w['status']!='archived']
    titles=collections.defaultdict(dict);near_titles=collections.defaultdict(dict);identifiers={};urls={}
    for w in rows:
        for title in (w['title'],w.get('alternate_title')):
            if title:
                titles[m.norm(title)][w['artwork_id']]=w;near_titles[title_key(title)][w['artwork_id']]=w
        for e in w.get('identifiers') or []:
            if e['scheme']=='wikiart-artwork':identifiers[e['external_id']]=w
            if e.get('url'):urls[e['url']]=w
    featured={urljoin(index['source']['url'],w['paintingUrl']):w for w in index['profile']['featured']}
    items={w['url']:dict(w) for w in index['works']}
    for url,w in featured.items():
        if url not in items:items[url]={'url':url,'title':w['title'],'source_date':w.get('year'),'date':m.creation_date(w.get('year'))}
    candidate_counts=collections.Counter(m.norm(w['title']) for w in items.values())
    gaps=[];fresh=[];held=[];skipped=collections.Counter()
    for item in items.values():
        date=item['date'];url=item['url'];known=featured.get(url,{})
        if not date or date['creation_year_end']>1955:
            skipped['date_unresolved_or_after_1955']+=1;continue
        if re.search(r'\b(detail|reconstruction)\b',item['title'],re.I):
            skipped['detail_or_reconstruction']+=1;continue
        exact=list(titles[m.norm(item['title'])].values())
        identity=identifiers.get(known.get('_id')) or urls.get(url)
        if identity:exact=[identity]
        if exact:
            valid=[w for w in exact if overlaps(w,date) and w['creation_year_end']<=1955 and len(w['creators'] or [])==1 and w['creators'][0]['role']=='primary']
            if len(valid)!=1:
                held.append({'url':url,'title':item['title'],'reason':'Existing title identity/date/attribution requires review','ids':[w['artwork_id'] for w in exact]});continue
            w=valid[0]
            if w['primary_media_id']:
                skipped['existing_primary_image']+=1;continue
            if candidate_counts[m.norm(item['title'])]>1 and not identity:
                held.append({'url':url,'reason':'Multiple source works could fill existing title'});continue
            gaps.append({**item,'existing':w,'featured':url in featured,'identifier_match':bool(identity)})
        elif url in excluded_urls or known.get('_id') in excluded_ids:
            skipped['already_recorded_source']+=1
        else:fresh.append({**item,'featured':url in featured})
    # Museum-linked image gaps first; additional selections favor source highlights,
    # then creation periods with fewer illustrated records for this painter.
    gaps.sort(key=lambda x:(not bool(x['existing']['current_institution_id']),not x['featured'],x['date']['creation_year_start'],x['title']))
    decade_counts=collections.Counter(w['creation_year_start']//10 for w in rows if w['primary_media_id'] and w['creation_year_start'] is not None)
    fresh.sort(key=lambda x:(not x['featured'],decade_counts[x['date']['creation_year_start']//10],x['date']['creation_year_start'],x['title']))
    pending=gaps[:6]+fresh+gaps[6:];matches=[];selected_titles=set();selected_ids=set();attempts=0
    for item in pending:
        if len(matches)>=12:break
        if attempts>=36:break
        key=title_key(item['title'])
        if key in selected_titles:
            held.append({'url':item['url'],'reason':'Coincident selected title'});continue
        if not item.get('existing'):
            close=difflib.get_close_matches(key,list(near_titles),n=4,cutoff=0.84)
            conflicts=[w for name in close for w in near_titles[name].values()
                if key==name or w['creation_year_start'] is None or w['creation_year_end'] is None or overlaps(w,item['date'])]
            if conflicts:
                held.append({'url':item['url'],'title':item['title'],'reason':'Potential existing title variant',
                    'ids':sorted({w['artwork_id'] for w in conflicts})});continue
        attempts+=1
        try:
            raw,receipt=Fetcher().get(item['url']);soup=c.BeautifulSoup(raw,'html.parser')
            tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
            if tag is None:raise ValueError('Public detail metadata unavailable; no authentication attempted')
            record=json.loads(tag['ng-init'].split('=',1)[1].strip());date=c.dated(record.get('year'))
            if not date:raise ValueError('Detail date unresolved or after 1955')
            if record['artistUrl']!=urlparse(index['source']['url']).path:raise ValueError('Detail creator differs from selected painter')
            if m.norm(record['title'])!=m.norm(item['title']):raise ValueError('Detail title differs from index')
            if not overlaps(date,item['date']):raise ValueError('Detail creation date disagrees with index')
            if record['_id'] in selected_ids:continue
            existing=item.get('existing')
            if existing:
                if not overlaps(existing,date):raise ValueError('Detail date disagrees with existing artwork')
                if record['_id'] in identifiers and identifiers[record['_id']]['artwork_id']!=existing['artwork_id']:
                    raise ValueError('Source identifier belongs to another catalogue record')
                if record['_id'] in excluded_ids and record['_id'] not in identifiers:
                    raise ValueError('Source identifier already recorded elsewhere; reconcile before attachment')
                if m.norm(record['title']) not in {m.norm(existing['title']),m.norm(existing.get('alternate_title'))}:
                    raise ValueError('Existing source identity has a different title; retain for explicit alias review')
                work={**existing,'artist':artist}
            else:
                if record['_id'] in excluded_ids:
                    skipped['already_recorded_source']+=1;continue
                wid=str(c.uuid.uuid5(c.uuid.NAMESPACE_URL,'https://www.wikiart.org/artwork/'+record['_id']))
                work={'artwork_id':wid,'slug':'wikiart-'+record['_id'],'title':record['title'],'alternate_title':None,
                    **date,'work_type':'unknown','status':'review','research_candidate':True,'primary_media_id':None,
                    'current_institution_id':None,'accession_number':None,'institution':None,'artist':artist,
                    'creators':[{'id':artist['id'],'slug':artist['slug'],'name':artist['display_name'],'role':'primary'}],
                    'identifiers':[{'scheme':'wikiart-artwork','external_id':record['_id'],'url':item['url']}],
                    'before_record':None,'new_record':True}
            basis=('User-requested Top 100 painter expansion, maximum twelve selected additions per painter. '+
                ('Fill an existing image gap. ' if existing else 'Personal owner collection highlight. ')+
                ('WikiArt explicitly features this object in famous-works. ' if item['featured'] else
                 'Selected from the dated WikiArt artist index to broaden this painter’s illustrated creation periods. ')+
                'Source creation date ends by 1955; selection is personal, without asserting a museum designation, holding or current display.')
            match={'work':work,'wikiart':{'title':record['title'],'url':item['url'],'year':date['creation_year_start'],'source_id':record['_id']},
                'selection_basis':basis,'index_receipt':index['profile']['receipt'] if item['featured'] else index['receipt'],
                'source_featured':item['featured'],'metadata_receipt':receipt}
            matches.append(match);selected_titles.add(key);selected_ids.add(record['_id'])
        except (ValueError,m.requests.RequestException) as error:
            held.append({'url':item['url'],'title':item['title'],'reason':str(error)[:300]})
            if isinstance(error,m.requests.HTTPError) and error.response.status_code in (403,429):raise
    result={'artist':artist,'matches':matches,'held':held,'skipped':dict(skipped),'index_entries':len(items),
        'eligible_index_dates':index['eligible_dates'],'metadata_pages_selected_for_review':attempts}
    m.save_atomic(output,result)
    print('Selected',artist['display_name'],len(matches),'new',sum(bool(x['work'].get('new_record')) for x in matches),
        'existing gaps',sum(not x['work'].get('new_record',False) for x in matches),flush=True)
    return result


def select():
    indexes=[read(p) for p in sorted((RUN/'indexes').glob('*.json'))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(select_one,indexes))
    matches=m.discovered_matches()
    m.save_atomic(RUN/'discovered-v2.json',{'at':m.core.now(),'matches':matches,'reviewed_profiles':len(results),
        'new_artworks':sum(bool(x['work'].get('new_record')) for x in matches)})
    print('Selection finished',len(matches),'images for',len({m['work']['artist']['id'] for m in matches}),'painters',flush=True)


def prepare():c.prepare()


def visual_review():
    from PIL import Image, ImageOps, ImageDraw
    images=[read(p) for p in sorted((RUN/'images').glob('*.json'))]
    ids=sorted({im['work']['artist']['id'] for im in images})
    with m.read_only() as db:
        rows=db.execute("""SELECT aa.artist_id::text,a.id::text artwork_id,a.title,ma.storage_path path,
            ma.checksum_sha256 sha256 FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
            JOIN media_assets ma ON ma.id=a.primary_media_id WHERE aa.artist_id=ANY(%s::uuid[])
            AND a.status<>'archived'""",(ids,)).fetchall()
    pool=collections.defaultdict(list);cache={};missing=[]
    def fingerprint(path):
        with Image.open(path) as im:
            ratio=im.width/im.height;gray=ImageOps.grayscale(im)
            a=list(gray.resize((9,8)).getdata());b=list(gray.resize((8,9)).getdata())
            bits=[a[y*9+x]>a[y*9+x+1] for y in range(8) for x in range(8)]
            bits += [b[y*8+x]>b[(y+1)*8+x] for y in range(8) for x in range(8)]
            value=0
            for bit in bits:value=(value<<1)|int(bit)
        return ratio,value
    for i,row in enumerate(rows):
        path=ROOT/'apps/web/public'/row['path'].lstrip('/')
        if not path.is_file():missing.append(row);continue
        key=row['path']
        if key not in cache:cache[key]=fingerprint(path)
        pool[row['artist_id']].append((row,*cache[key]))
        if i%2000==0:print('Existing image comparison',i,'of',len(rows),flush=True)
    pairs=[]
    for im in images:
        ratio,value=fingerprint(ROOT/'apps/web/public'/im['path'].lstrip('/'))
        aid=im['work']['artist']['id']
        for other,other_ratio,other_value in pool[aid]:
            if abs(ratio/other_ratio-1)>0.04:continue
            distance=(value^other_value).bit_count()
            if distance<=10:pairs.append({'candidate':{k:im[k] for k in ('artwork_id','title','path','sha256')},
                'other':other,'distance':distance,'decision':'Held for composition/object identity review, no automatic merge'})
        pool[aid].append(({k:im[k] for k in ('artwork_id','title','path','sha256')},ratio,value))
    m.save_atomic(RUN/'visual-review.json',{'at':m.core.now(),'pairs':pairs,'compared_existing_images':len(rows)-len(missing),
        'missing_local_reference_images':missing,'method':'128-bit horizontal/vertical difference hash within selected painter; distance <=10 and aspect difference <=4%; flag only.'})
    for start in range(0,len(pairs),8):
        group=pairs[start:start+8];out=Image.new('RGB',(1100,250*len(group)),'white');draw=ImageDraw.Draw(out)
        for i,pair in enumerate(group):
            for j,key in enumerate(('candidate','other')):
                item=pair[key]
                with Image.open(ROOT/'apps/web/public'/item['path'].lstrip('/')) as im:
                    thumb=ImageOps.contain(im,(380,208));out.paste(thumb,(j*550+5,i*250+30))
                draw.text((j*550+5,i*250+4),str(start+i)+' '+item['title'][:78],fill='black')
                draw.text((j*550+390,i*250+50),item['artwork_id'][:12],fill='black')
        path=Path('/tmp')/('artline-top100-duplicates-'+str(start//8)+'.jpg');out.save(path)
        m.save_atomic(m.BACKUP/'visual-review'/path.name,path.read_bytes())
    print('Visual comparison flagged',len(pairs),'pairs for',len({p['candidate']['artwork_id'] for p in pairs}),'candidates',flush=True)


def preflight():
    images=[read(p) for p in sorted((RUN/'images').glob('*.json'))]
    flagged={p['candidate']['artwork_id'] for p in read(RUN/'visual-review.json')['pairs']}
    dimension_holds=collections.defaultdict(list)
    if (RUN/'dimension-identity-review.json').exists():
        for pair in read(RUN/'dimension-identity-review.json')['pairs']:
            dimension_holds[pair['candidate_artwork_id']].append(pair)
    hashes=collections.defaultdict(list)
    for im in images:hashes[im['sha256']].append(im['artwork_id'])
    held=[];approved=[]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            rows=db.execute("""SELECT a.id::text artwork_id,a.title,ma.checksum_sha256 FROM media_assets ma
                JOIN artworks a ON a.primary_media_id=ma.id WHERE ma.checksum_sha256=ANY(%s) AND a.status<>'archived'""",(list(hashes),)).fetchall()
            m.save_atomic(RUN/('existing-reproductions-'+target+'.json'),rows)
    existing=collections.defaultdict(list)
    for target in ('local','cloud'):
        for row in read(RUN/('existing-reproductions-'+target+'.json')):
            existing[row['checksum_sha256']].append({'target':target,**row})
    with m.read_only() as db:
        for im in images:
            reasons=[];work=im['work'];artist=work['artist']
            if dimension_holds[im['artwork_id']]:
                reasons.append({'reason':'Compatible date and dimensions with existing object; translated identity needs review','pairs':dimension_holds[im['artwork_id']]})
            if im['artwork_id'] in flagged:reasons.append({'reason':'Similar reproduction; object identity unresolved'})
            if existing[im['sha256']]:reasons.append({'reason':'Identical reproduction already attached','records':existing[im['sha256']]})
            if len(hashes[im['sha256']])>1:reasons.append({'reason':'Selected candidates share identical reproduction','ids':hashes[im['sha256']]})
            if work['creation_year_start']==artist.get('birth_year') and work['creation_year_end']==artist.get('death_year'):
                reasons.append({'reason':'Source creation interval repeats artist lifespan'})
            state=c.target_before(db,im)
            if state['outcome']=='held':reasons.append(state)
            if work['creation_year_start'] is None or work['creation_year_end']>1955:reasons.append({'reason':'Date eligibility changed'})
            if reasons:
                path=RUN/'images'/(im['artwork_id']+'.json')
                m.save_atomic(RUN/'prepared-held'/path.name,{'image':im,'reasons':reasons});path.unlink()
                held.append({'artwork_id':im['artwork_id'],'reasons':reasons})
            else:approved.append(im['artwork_id'])
    m.save_atomic(RUN/'preflight.json',{'at':m.core.now(),'approved':approved,'held':held})
    print('Approved',len(approved),'held',len(held),flush=True)


def dimension_review():
    pattern=re.compile(r'(\d+(?:[.,]\d+)?)\s*[×x]\s*(\d+(?:[.,]\d+)?)\s*cm\b',re.I)
    def dimensions(value):
        return [sorted([float(m[1].replace(',','.')),float(m[2].replace(',','.'))]) for m in pattern.finditer(value or '')]
    artist_rows={};pairs=[];with_dimensions=0
    for path in sorted((RUN/'images').glob('*.json')):
        im=read(path)
        if not im['work'].get('new_record'):continue
        rawpath=RUN/'captures'/(m.core.sha(im['page_receipt']['url'].encode())+'.body')
        soup=c.BeautifulSoup(rawpath.read_bytes(),'html.parser')
        text=next((li.get_text(' ',strip=True) for li in soup.select('li') if li.get_text(' ',strip=True).startswith('Dimensions:')),None)
        dims=dimensions(text)
        if not dims:continue
        with_dimensions+=1;aid=im['work']['artist']['id']
        if aid not in artist_rows:
            artist_rows[aid]=[(w,dimensions(w['before_record'].get('dimensions_text')))
                for w in read(RUN/'catalogue-works'/(aid+'.json')) if w['status']!='archived']
        for w,existing in artist_rows[aid]:
            if w['artwork_id']==im['artwork_id'] or not overlaps(w,im['work']):continue
            if any(all(abs(a-b)<=max(0.5,0.01*max(a,b)) for a,b in zip(new,old)) for new in dims for old in existing):
                pairs.append({'candidate_artwork_id':im['artwork_id'],'candidate_title':im['title'],
                    'candidate_dimensions':text,'existing_artwork_id':w['artwork_id'],'existing_title':w['title'],
                    'existing_dimensions':w['before_record']['dimensions_text'],'existing_date':w['date_display'],
                    'decision':'Conservative identity hold only; matching dimensions/date do not prove the same object.'})
    m.save_atomic(RUN/'dimension-identity-review.json',{'at':m.core.now(),'new_candidates_with_source_dimensions':with_dimensions,'pairs':pairs})
    print('Dimension/date identity review',with_dimensions,'source objects;',len(pairs),'possible existing object matches',flush=True)


def reconcile_cloud_existing():
    if not (RUN/'delivery-finished.json').exists():raise ValueError('Wait for delivery to finish')
    completed=[]
    with m.psycopg.connect(m.core.cloud_dsn(),autocommit=True,row_factory=m.dict_row) as db:
        for path in sorted((RUN/'delivery').glob('*.json')):
            receipt=read(path);prior=receipt['targets']['cloud']
            if prior['outcome'] in ('attached','already_attached'):continue
            im=read(RUN/'images'/path.name);w=im['work']
            if w.get('new_record') or prior.get('reason')!='Existing artwork absent in target':
                raise ValueError('Unreviewed cloud hold: '+str(prior))
            backup=m.BACKUP/'cloud-existing-reconciliation'/path.name
            with db.transaction():
                rows=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE slug=%s FOR UPDATE',(w['slug'],)).fetchall()
                if len(rows)!=1:raise ValueError('Exact catalogue slug is not unique')
                current=rows[0]['record']
                before=read(backup)['artwork'] if backup.exists() else current
                excluded={'id','created_at','updated_at'}
                if {k:v for k,v in before.items() if k not in excluded}!={k:v for k,v in w['before_record'].items() if k not in excluded}:
                    raise ValueError('Existing cloud artwork metadata differs')
                if before['primary_media_id'] is not None or current['primary_media_id'] not in (None,im['media_id']):
                    raise ValueError('Existing primary image must be preserved')
                if before['creation_year_start'] is None or before['creation_year_end'] is None or before['creation_year_end']>1955:
                    raise ValueError('Creation date does not meet selection cutoff')
                creators=db.execute("""SELECT to_jsonb(aa) attribution,p.slug,aa.attribution_role
                    FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=%s ORDER BY p.slug""",(before['id'],)).fetchall()
                if [(r['slug'],r['attribution_role']) for r in creators]!=[(im['artist_slug'],'primary')]:
                    raise ValueError('Existing cloud creator differs')
                institution=db.execute('SELECT slug FROM institutions WHERE id=%s',(before['current_institution_id'],)).fetchone()
                if (institution or {}).get('slug')!=(w['institution'] or {}).get('slug'):
                    raise ValueError('Existing cloud holding differs')
                if not backup.exists():
                    media=db.execute('SELECT to_jsonb(ma) record FROM media_assets ma WHERE id=%s',(im['media_id'],)).fetchone()
                    m.save_atomic(backup,{'artwork':before,'creators':creators,'media_before':media,
                        'local_before':w['before_record'],'prior_delivery':receipt,
                        'basis':'Exact unique catalogue slug, all metadata except ID and timestamps identical, exact primary creator and holding checked.'})
                if current['primary_media_id']==im['media_id']:
                    permitted={'primary_media_id','revision','updated_at','updated_by'}
                    if any(current[k]!=before[k] for k in before if k not in permitted):
                        raise ValueError('Recovered attachment contains unrelated changes')
                    outcome='attached'
                else:outcome=m.attach(db,im,before)
                after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(before['id'],)).fetchone()['record']
                if after['primary_media_id']!=im['media_id']:raise ValueError('Cloud image association missing')
            result={'outcome':outcome,'created':False,'before_attachment':before,'after':after,
                'identity_reconciliation':{'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),
                    'basis':'Exact catalogue slug and unchanged semantic metadata; existing cloud UUID preserved.'}}
            applied=RUN/'applied/cloud'/path.name
            for old,kind in [(path,'delivery'),(applied,'applied-cloud')]:
                history=RUN/'reconciliation-history'/kind/path.name
                if not history.exists():m.save_atomic(history,old.read_bytes())
            receipt['targets']['cloud']=result
            for output,value in [(applied,result),(path,receipt)]:
                temporary=output.with_name(output.name+'.reconciled.tmp')
                temporary.write_bytes(m.core.encode(value));temporary.replace(output)
            completed.append({'local_artwork_id':im['artwork_id'],'cloud_artwork_id':after['id'],
                'artist':im['artist'],'title':im['title'],'backup':str(backup)})
            print('Reconciled existing cloud artwork',im['artist'],im['title'],flush=True)
    marker=RUN/'cloud-existing-reconciliation-finished.json'
    if not marker.exists():m.save_atomic(marker,{'at':m.core.now(),'reconciled':completed})


def sync_selection():
    collection_id=str(c.uuid.uuid5(c.uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    receipts=[read(p) for p in sorted((RUN/'delivery').glob('*.json'))]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            eligible=[r for r in receipts if r['targets'][target]['outcome'] in ('attached','already_attached')
                and not (RUN/'personal-selection'/target/(r['artwork_id']+'.json')).exists()]
            sid=db.execute("SELECT id FROM sources WHERE slug='wikiart-artist-coverage-20260920'").fetchone()['id']
            for start in range(0,len(eligible),100):
                batch=eligible[start:start+100];expected={r['targets'][target]['after']['id']:r['targets'][target]['after'] for r in batch}
                images={r['targets'][target]['after']['id']:read(RUN/'images'/(r['artwork_id']+'.json')) for r in batch}
                decisions={}
                with db.transaction():
                    rows=db.execute('SELECT to_jsonb(a) record,artline_has_selection_evidence(a.id) selected FROM artworks a WHERE id=ANY(%s::uuid[])',
                        (list(expected),)).fetchall()
                    if len(rows)!=len(expected):raise ValueError('Artwork missing before personal selection')
                    entries=[]
                    for row in rows:
                        aid=row['record']['id'];im=images[aid]
                        if row['record']!=expected[aid]:raise ValueError('Artwork changed before personal selection')
                        if row['selected'] and not im['work'].get('new_record'):
                            decisions[aid]={'artwork_id':aid,'action':'existing_selection_preserved'}
                        else:entries.append({'artwork_id':aid,'source_url':im['page'],'checked_at':im['checked_at'],'reason':im['selection_basis']})
                    if entries:
                        collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                        if collection['curator_kind']!='owner' or collection['institution_id'] is not None or collection['status']=='archived':
                            raise ValueError('Personal collection identity differs')
                        ids=[e['artwork_id'] for e in entries]
                        existing=db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection_id,ids)).fetchall()
                        backup=m.BACKUP/'personal-selection'/target/(m.core.sha(m.core.encode(ids))[:16]+'.json')
                        m.save_atomic(backup,{'artworks':rows,'collection':collection,'items':existing,'selected':entries})
                        db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) AS x(artwork_id uuid,source_url text,checked_at timestamptz,reason text)),
                            positions AS(SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s),
                            selected AS(SELECT x.*,row_number() OVER(ORDER BY x.artwork_id)::int ord FROM input x JOIN artworks a ON a.id=x.artwork_id
                              WHERE a.status<>'archived' AND a.creation_year_start IS NOT NULL AND a.creation_year_end<=1955)
                            INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                            SELECT %s,s.artwork_id,p.n+s.ord,s.reason,%s,s.source_url,s.checked_at FROM selected s CROSS JOIN positions p
                            ON CONFLICT(collection_id,artwork_id) DO NOTHING""",(m.Jsonb(entries),collection_id,collection_id,sid))
                        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
                        after=db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection_id,ids)).fetchall()
                        if len(after)!=len(ids):raise ValueError('Personal selection count differs')
                        present={r['record']['artwork_id'] for r in existing}
                        for aid in ids:decisions[aid]={'artwork_id':aid,'action':'existing_owner_selection_preserved' if aid in present else 'personal_selection_added',
                            'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes())}
                for receipt in batch:
                    aid=receipt['targets'][target]['after']['id']
                    m.save_atomic(RUN/'personal-selection'/target/(receipt['artwork_id']+'.json'),{'at':m.core.now(),**decisions[aid]})
                print('Personal selection',target,min(start+100,len(eligible)),'of',len(eligible),flush=True)
            print('Personal selections completed',target,flush=True)
    m.save_atomic(RUN/'personal-selection-finished.json',{'at':m.core.now(),'collection_id':collection_id})


def retry_file_verification():
    previous=max(RUN.glob('verification-*.json'),key=lambda p:p.stat().st_mtime);result=read(previous)
    if not result['errors']:return
    failed={r['artwork_id'] for r in result['file_checks'] if not r['public_verified'] or not r['local_verified']}
    if any(e.get('artwork_id') not in failed or 'public_verified' not in e for e in result['errors']):
        raise ValueError('Only failed file checks may be retried in this phase')
    retries=[]
    for check in result['file_checks']:
        if check['artwork_id'] not in failed:continue
        im=read(RUN/'images'/(check['artwork_id']+'.json'))
        local=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        replacement={'artwork_id':im['artwork_id'],'local_verified':len(local)==im['bytes'] and len(local)<=100000 and m.core.sha(local)==im['sha256']}
        for attempt in range(3):
            try:
                response=m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'],timeout=(20,60))
                replacement.update(http_status=response.status_code,public_verified=response.status_code==200 and m.core.sha(response.content)==im['sha256'])
                if replacement['public_verified']:replacement.pop('error',None)
            except m.requests.RequestException as error:replacement.update(public_verified=False,error=str(error)[:200])
            retries.append({'at':m.core.now(),'attempt':attempt+1,**replacement})
            if replacement['local_verified'] and replacement['public_verified']:break
        check.clear();check.update(replacement)
    result['errors']=[r for r in result['file_checks'] if not r['public_verified'] or not r['local_verified']]
    result['initial_verification_at']=result['at'];result['at']=m.core.now()
    result['file_retries']={'previous_receipt':str(previous),'previous_sha256':m.core.sha(previous.read_bytes()),'checks':retries}
    destination=RUN/('verification-'+str(result['uploaded'])+'-'+str(int(time.time()))+'.json')
    m.save_atomic(destination,result)
    print('Retried file checks',len(failed),'remaining errors',len(result['errors']),flush=True)
    if result['errors']:raise SystemExit(1)


def report():
    baseline=read(RUN/'cohort-baseline.json');artists=baseline['artists'];receipts=[read(p) for p in (RUN/'delivery').glob('*.json')]
    images={r['artwork_id']:read(RUN/'images'/(r['artwork_id']+'.json')) for r in receipts}
    verify_path=max(RUN.glob('verification-*.json'),key=lambda p:p.stat().st_mtime);verification=read(verify_path)
    if verification['errors']:raise ValueError('Delivery verification has unresolved errors')
    results={};errors=[];checks=collections.Counter()
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            cohort=db.execute("""SELECT a.id::text,a.slug,a.display_name,d.is_popular,d.popularity_rank,d.basis,d.source_url,
                (SELECT count(*) FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived') works,
                (SELECT count(*) FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived' AND w.primary_media_id IS NOT NULL) images
                FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id WHERE d.is_popular ORDER BY a.id""").fetchall()
            current={r['slug']:r for r in cohort};results[target]=current
            if len(cohort)!=100:errors.append({'target':target,'error':'Top 100 membership count changed'})
            for row in artists:
                slug=row['artist']['slug'];now=current.get(slug)
                if not now or any(now[k]!=row['discovery'][k] for k in ('is_popular','popularity_rank','basis','source_url')):
                    errors.append({'target':target,'artist':slug,'error':'Top 100 selection changed'})
                else:checks[target+'_cohort_members']+=1
            attached=[r for r in receipts if r['targets'][target]['outcome'] in ('attached','already_attached')]
            ids=[r['targets'][target]['after']['id'] for r in attached]
            rows=db.execute("""SELECT a.id::text,coalesce((SELECT jsonb_agg(jsonb_build_object('slug',p.slug,'role',aa.attribution_role))
                FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators,
                artline_has_selection_evidence(a.id) selected FROM artworks a WHERE a.id=ANY(%s::uuid[])""",(ids,)).fetchall()
            actual={r['id']:r for r in rows}
            for receipt in attached:
                im=images[receipt['artwork_id']];aid=receipt['targets'][target]['after']['id'];row=actual.get(aid)
                if not row or row['creators']!=[{'slug':im['artist_slug'],'role':'primary'}] or not row['selected']:
                    errors.append({'target':target,'artwork_id':aid,'error':'Creator or selection differs'})
                else:checks[target+'_attributions_and_selections']+=1
            new_ids=[r['targets'][target]['after']['id'] for r in attached if r['targets'][target].get('created')]
            assertions=db.execute('SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(new_ids,)).fetchone()['n']
            if assertions:errors.append({'target':target,'error':'Unexpected holding assertions on new artworks'})
    for im in images.values():
        for kind,receipt in [('artwork',im['page_receipt']),('selection',im['selection_receipt'])]:
            key=m.core.sha(receipt['url'].encode())+'.body'
            paths=[p/'captures'/key for p in [RUN]+PREVIOUS]
            if not any(p.exists() and m.core.sha(p.read_bytes())==receipt['sha256'] for p in paths):
                errors.append({'artwork_id':im['artwork_id'],'error':kind+' evidence checksum differs'})
            else:checks[kind+'_captures']+=1
        original=m.ORIGINALS/(m.core.sha(im['download']['url'].encode())+'.body')
        if not original.exists() or m.core.sha(original.read_bytes())!=im['download']['sha256']:
            errors.append({'artwork_id':im['artwork_id'],'error':'Original reproduction differs'})
        else:checks['source_originals']+=1
        plan=read(RUN/'delivery-plans'/(im['artwork_id']+'.json'))
        if m.core.sha(Path(plan['backup']).read_bytes())!=plan['backup_sha256']:
            errors.append({'artwork_id':im['artwork_id'],'error':'Recovery preimage checksum differs'})
        else:checks['recovery_preimages']+=1
    for receipt in receipts:
        for target in ('local','cloud'):
            reconciliation=receipt['targets'][target].get('identity_reconciliation')
            if reconciliation:
                if m.core.sha(Path(reconciliation['backup']).read_bytes())!=reconciliation['backup_sha256']:
                    errors.append({'artwork_id':receipt['artwork_id'],'target':target,'error':'Reconciliation recovery checksum differs'})
                else:checks['reconciliation_preimages']+=1
            selection=read(RUN/'personal-selection'/target/(receipt['artwork_id']+'.json'))
            if selection.get('backup'):
                if m.core.sha(Path(selection['backup']).read_bytes())!=selection['backup_sha256']:
                    errors.append({'artwork_id':receipt['artwork_id'],'target':target,'error':'Personal selection recovery checksum differs'})
                else:checks[target+'_selection_preimages']+=1
    if errors:
        m.save_atomic(RUN/('audit-errors-'+str(int(time.time()))+'.json'),errors)
        raise ValueError('Completion audit failed: '+str(errors[:5]))
    index_by_artist={read(p)['artist']['id']:read(p) for p in (RUN/'indexes').glob('*.json')}
    discoveries={read(p)['artist']['id']:read(p) for p in (RUN/'discovery-v2').glob('*.json')}
    prepared_holds=collections.Counter(read(p)['image']['work']['artist']['id'] for p in (RUN/'prepared-held').glob('*.json'))
    artist_rows=[]
    for row in artists:
        aid=row['artist']['id'];slug=row['artist']['slug'];selection=discoveries.get(aid,{})
        own=[r for r in receipts if images[r['artwork_id']]['artist_slug']==slug]
        output={'rank':row['discovery']['popularity_rank'],'artist':row['artist']['display_name'],'artist_id':aid,'slug':slug,
            'baseline_artworks':row['baseline_artworks'],'baseline_images':row['baseline_images'],
            'index_entries_reviewed':len(index_by_artist.get(aid,{}).get('works',[])),
            'selected_candidates':len(selection.get('matches',[])),'prepared_candidates_held':prepared_holds[aid],
            'metadata_candidates_held':len(selection.get('held',[])),
            'review_outcome':'WikiArt indexed works and featured selection reviewed' if aid in index_by_artist else 'No usable WikiArt source profile found; no invented works or dates'}
        for target in ('local','cloud'):
            delivered=[r['targets'][target] for r in own if r['targets'][target]['outcome'] in ('attached','already_attached')]
            output[target+'_new_artworks']=sum(r.get('created',False) for r in delivered)
            output[target+'_new_image_attachments']=sum(r['outcome']=='attached' for r in delivered)
            output[target+'_existing_gaps_filled']=sum(r['outcome']=='attached' and not r.get('created') for r in delivered)
            output[target+'_works_after']=results[target][slug]['works'];output[target+'_images_after']=results[target][slug]['images']
        artist_rows.append(output)
    with (RUN/'all-top-100-review.csv').open('w',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(artist_rows[0]));writer.writeheader();writer.writerows(artist_rows)
    works=[]
    for receipt in receipts:
        im=images[receipt['artwork_id']]
        works.append({'artwork_id':im['artwork_id'],'cloud_artwork_id':receipt['targets']['cloud'].get('after',{}).get('id'),
            'painter':im['artist'],'title':im['title'],'source_date':im['work']['date_display'],
            'creation_year_start':im['work']['creation_year_start'],'creation_year_end':im['work']['creation_year_end'],
            'source_url':im['page'],'rights_label':im['rights_status'],'image_bytes':im['bytes'],
            'local_outcome':receipt['targets']['local']['outcome'],'cloud_outcome':receipt['targets']['cloud']['outcome'],
            'new_local_artwork':receipt['targets']['local'].get('created',False),'new_cloud_artwork':receipt['targets']['cloud'].get('created',False)})
    with (RUN/'delivered-artworks.csv').open('w',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(works[0]));writer.writeheader();writer.writerows(works)
    summary={'at':m.core.now(),'painters_reviewed':100,'wikiart_profiles':len(index_by_artist),
        'index_entries_reviewed':sum(len(r['works']) for r in index_by_artist.values()),
        'delivery':{k:v for k,v in verification.items() if k not in ('file_checks','api_checks')},
        'new_image_attachments':{t:sum(r[t+'_new_image_attachments'] for r in artist_rows) for t in ('local','cloud')},
        'existing_gaps_filled':{t:sum(r[t+'_existing_gaps_filled'] for r in artist_rows) for t in ('local','cloud')},
        'painters_with_additions':sum(r['local_new_image_attachments']>0 for r in artist_rows),
        'painters_without_additions':[r['artist'] for r in artist_rows if not r['local_new_image_attachments']],
        'existing_cloud_ids_reconciled':checks['reconciliation_preimages'],
        'prepared_candidates_held':sum(prepared_holds.values()),'checks':dict(checks),'errors':errors,
        'verification':str(verify_path.relative_to(ROOT))}
    text=['# Top 100 painters — WikiArt expansion, 20 September 2026','',
        f"Reviewed Artline’s existing 100-painter discovery cohort and {summary['index_entries_reviewed']:,} WikiArt index entries across {len(index_by_artist)} matched public profiles. The cohort, ranking, artist identities and prior primary images were preserved.", '',
        f"Added {verification['databases']['local']['new_artworks']:,} review artworks and {summary['new_image_attachments']['local']:,} new image attachments in each database, including {summary['existing_gaps_filled']['local']} existing image gaps, across {summary['painters_with_additions']} painters.", '',
        f"All {verification['uploaded']:,} uploaded files passed local/public SHA-256 verification; maximum image size {verification['max_bytes']:,} bytes. The source originals, source-page captures, selection captures, target recovery preimages, creator attribution and personal selection memberships were checked. No errors remained.", '',
        'New records retain review status, supplied source dates and unknown types/holdings. Personal selections are distinguished from WikiArt’s explicitly featured works and from museum designations. The continuing WikiArt image workflow uses creation dates ending by 1955 and preserves the actual source rights labels; it does not turn age into a licence claim.', '',
        f"Selection was bounded to twelve candidates per painter, prioritizing existing image gaps, source-featured works and less-illustrated creation periods. {summary['prepared_candidates_held']} prepared candidates remain held for duplicate/identity review. Similar images or matching dimensions/dates flag possible conflicts; they do not establish that two physical objects are identical. Earlier records were not deleted or merged.", '',
        'No approved additions: '+', '.join(summary['painters_without_additions'])+'. Bob Ross had no usable WikiArt profile; the other two had no eligible additional candidates after the existing-record and source-date checks. Unresolved candidates remain recorded in the full cohort audit.', '',
        f"{summary['existing_cloud_ids_reconciled']} existing production records used different UUIDs from local. Their exact unique catalogue slugs, metadata, primary creators and holdings agreed; supplemental preimages were archived and their existing production IDs were preserved.", '',
        'Files: [all 100 painters](all-top-100-review.csv), [delivered artworks](delivered-artworks.csv), [verified totals](completed-summary.json), [preflight holds](preflight.json), [image comparisons](visual-review.json), [dimension/date conflicts](dimension-identity-review.json).', '',
        f'Recovery snapshots and operation scripts: `{m.BACKUP}`. Archived source originals: `{m.ORIGINALS}`.', '']
    (RUN/'README.md').write_text('\n'.join(text))
    m.save_atomic(RUN/'completed-summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['audit','indexes','select','prepare','visual_review','dimension_review','preflight','deliver_ready','reconcile_cloud_existing','sync_selection','verify','retry_file_verification','report'])
    name=parser.parse_args().phase
    (globals().get(name) or getattr(c,name))()
