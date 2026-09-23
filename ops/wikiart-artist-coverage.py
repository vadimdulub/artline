#!/usr/bin/env python3
"""Artist-first WikiArt coverage: catalogue inventory, selected works, <=100 KB images."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import re
import string
import time
import html
import uuid
import hashlib
import base64
import threading
import difflib
from urllib.parse import urljoin,urlparse

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('wikiart',ROOT/'ops/wikiart-selected-images.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PREVIOUS=m.RUN
RUN=ROOT/'docs/research/wikiart-artist-coverage-20260920'
m.RUN=RUN
m.BACKUP=Path.home()/'Library/Application Support/Artline/backups/wikiart-artist-coverage-20260920'
m.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images/wikiart-artist-coverage-20260920'
m.FETCH_INTERVAL=0.4
m.PREPARE_WORKERS=8


class SharedFetcher(m.Fetcher):
    def get(self,url,limit=5_000_000,image=False):
        key=m.core.sha(url.encode())
        if not image and (PREVIOUS/'captures'/(key+'.body')).exists():
            raw=(PREVIOUS/'captures'/(key+'.body')).read_bytes()
            receipt=json.loads((PREVIOUS/'captures'/(key+'.json')).read_bytes())
            if m.core.sha(raw)!=receipt['sha256']:raise ValueError('Previous capture checksum mismatch')
            m.save_atomic(RUN/'captures'/(key+'.body'),raw);m.save_atomic(RUN/'captures'/(key+'.json'),receipt)
            return raw,receipt
        return super().get(url,limit,image)


def inventory():
    path=RUN/'catalogue-artists.json'
    if not path.exists():
        with m.read_only() as db:
            artists=db.execute("""SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year,p.entity_type,p.status,
              COALESCE((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=p.id),'[]') aliases,
              EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=p.id AND c.country_code IN ('RU','GR')) priority,
              EXISTS(SELECT 1 FROM artist_discovery_selection s WHERE s.artist_id=p.id AND s.is_popular) popular
              FROM artists p WHERE p.status<>'archived' ORDER BY p.id""").fetchall()
        m.save_atomic(path,{'at':m.core.now(),'artists':artists})
    else:artists=json.loads(path.read_bytes())['artists']
    def letter(c):
        target=RUN/'directory'/(c+'.json')
        if target.exists():return json.loads(target.read_bytes())['artists']
        raw,receipt=SharedFetcher().get('https://www.wikiart.org/en/Alphabet/'+c+'/text-list')
        soup=BeautifulSoup(raw,'html.parser');found=[]
        for li in soup.select('li'):
            a=li.find('a',recursive=False);spans=li.find_all('span',recursive=False)
            if not a or not re.fullmatch(r'/en/[^/]+',a.get('href','')) or not spans or not re.search(r'\d+ artworks',spans[-1].get_text()):continue
            lifespan=spans[0].get_text(' ',strip=True).strip(', ')
            dates=re.fullmatch(r'(\d{4})\s*-\s*(\d{4})',lifespan)
            found.append({'name':a.get_text(' ',strip=True),'url':urljoin(receipt['final_url'],a['href']),
                'life_display':lifespan,'birth_year':int(dates[1]) if dates else None,'death_year':int(dates[2]) if dates else None,
                'source_count':int(re.search(r'\d+',spans[-1].get_text())[0]),'directory_receipt':receipt})
        m.save_atomic(target,{'artists':found,'receipt':receipt});print('Directory',c,len(found),flush=True)
        return found
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:groups=list(pool.map(letter,string.ascii_lowercase))
    source={p['url']:p for group in groups for p in group};names=collections.defaultdict(dict)
    for p in artists:
        for name in [p['display_name']]+p['aliases']:names[m.norm(name)][p['id']]=p
    matches=[];ambiguous=[];unmatched=[]
    for p in source.values():
        candidates=list(names[m.norm(p['name'])].values())
        # Directory lifespan is corroboration, never the artwork date cutoff.
        candidates=[a for a in candidates if all(p.get(k) is None or a.get(k) is None or p[k]==a[k] for k in ('birth_year','death_year'))]
        if len(candidates)>1:
            exact=[a for a in candidates if m.norm(a['display_name'])==m.norm(p['name'])]
            if len(exact)==1:candidates=exact
        if len(candidates)==1:matches.append({'artist':candidates[0],'wikiart':p})
        elif candidates:ambiguous.append({'wikiart':p,'candidates':candidates})
        else:unmatched.append(p)
    matched_ids={r['artist']['id'] for r in matches}
    matches.sort(key=lambda r:(not r['artist']['priority'],not r['artist']['popular'],r['artist']['display_name']))
    m.save_atomic(RUN/'artist-matches.json',{'catalogue_count':len(artists),'wikiart_count':len(source),'matches':matches,
        'ambiguous':ambiguous,'unmatched_source_artists':unmatched,'catalogue_without_directory_match':[a for a in artists if a['id'] not in matched_ids]})
    print(json.dumps({'catalogue_artists':len(artists),'wikiart_artists':len(source),'matched_artists':len(matches),'ambiguous':len(ambiguous),'unmatched_source_artists':len(unmatched)}),flush=True)


def dated(value):
    result=m.creation_date(value)
    return result if result and result['creation_year_end']<=1955 else None


def profile_one(source):
    slug=urlparse(source['url']).path.rsplit('/',1)[-1]
    suffix='.ru.json' if '/ru/' in source['url'] else '.json'
    path=RUN/'profiles'/(slug+suffix)
    if path.exists():return json.loads(path.read_bytes())
    result={'source':source,'featured':[]}
    try:
        raw,receipt=SharedFetcher().get(source['url']);soup=BeautifulSoup(raw,'html.parser')
        for tag in soup.select('[ng-init]'):
            init=tag['ng-init']
            if not re.search(r"['\"]masonryId['\"]\s*:\s*['\"]famous-works['\"]",init):continue
            match=re.search(r"['\"]customSource['\"]\s*:\s*",init)
            if match:
                data,_=json.JSONDecoder().raw_decode(init[match.end():]);result['featured']=data.get('_v',[])
        result.update(receipt=receipt,outcome='inspected',wikidata_ids=sorted(set(re.findall(r'www.wikidata.org/(?:wiki/)?(Q\d+)',raw.decode()))),
            name=(soup.select_one('h1') or soup).get_text(' ',strip=True)[:250])
        for w in result['featured']:
            w['title']=html.unescape(w['title']);w['date']=dated(w.get('year'))
    except (ValueError,m.core.requests.RequestException) as error:
        if isinstance(error,m.core.requests.HTTPError) and error.response.status_code in (403,429):raise
        result.update(outcome='source_unavailable',error=str(error)[:300])
    m.save_atomic(path,result)
    return result


def profiles():
    inventory=json.loads((RUN/'artist-matches.json').read_bytes())
    ordered=[r['wikiart'] for r in inventory['matches']]+inventory['unmatched_source_artists']+[r['wikiart'] for r in inventory['ambiguous']]
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(profile_one,ordered):
            counts['artists']+=1;counts[result['outcome']]+=1
            counts['eligible_featured']+=sum(bool(w.get('date')) for w in result['featured'])
            if counts['artists']%25==0:print('Profile progress',dict(counts),flush=True)
    m.save_atomic(RUN/'profiles-finished.json',{'at':m.core.now(),'counts':dict(counts)})
    print('Profiles finished',dict(counts),flush=True)


def artist_works(db,artist_id):
    return db.execute("""SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,
        a.creation_year_start,a.creation_year_end,a.date_display,a.date_precision,a.work_type,a.status,
        a.primary_media_id::text,a.accession_number,a.current_institution_id::text,to_jsonb(a) before_record,
        (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'external_id',e.external_id,'url',e.canonical_url,'source_id',e.source_id))
          FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
        (SELECT jsonb_agg(jsonb_build_object('id',p.id,'slug',p.slug,'name',p.display_name,'role',x.attribution_role))
          FROM artwork_artists x JOIN artists p ON p.id=x.artist_id WHERE x.artwork_id=a.id) creators,
        (SELECT to_jsonb(i) FROM institutions i WHERE i.id=a.current_institution_id) institution
        FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s""",(artist_id,)).fetchall()


def select_one(pair,db,excluded_source_ids=()):
    artist=pair['artist'];source=pair['wikiart'];slug=urlparse(source['url']).path.rsplit('/',1)[-1]
    output=RUN/'discovery-v2'/(artist['id']+'.json');profile_path=RUN/'profiles'/(slug+'.json')
    if output.exists() or not profile_path.exists():return
    profile=json.loads(profile_path.read_bytes());result={'artist':artist,'matches':[],'held':[],'profile_outcome':profile['outcome']}
    rows=[] if artist.get('new_authority') or artist.get('object_level_creator') else artist_works(db,artist['id']);titles=collections.defaultdict(list)
    for w in rows:
        for title in {m.norm(w['title']),m.norm(w.get('alternate_title'))}-{''}:titles[title].append(w)
    featured=[dict(w,date=dated(w.get('year'))) for w in profile['featured']];translated={}
    if any(re.search('[А-Яа-я]',w['title']) for w in rows) and featured:
        translated_profile=profile_one({**source,'url':source['url'].replace('/en/','/ru/')})
        translated={w['_id']:w['title'] for w in translated_profile['featured']}
        if translated_profile['outcome']!='inspected':
            result['held'].append({'reason':'Russian title reconciliation unavailable'})
    def title_candidates(item):
        candidates={w['artwork_id']:w for title in (item['title'],translated.get(item['_id']))
            if title for w in titles[m.norm(title)]}
        return list(candidates.values())
    possible_sources=collections.defaultdict(set)
    for item in featured:
        if not item.get('date'):continue
        for work in title_candidates(item):
            if work['creation_year_start'] is not None and work['creation_year_end'] is not None and item['date']['creation_year_start']<=work['creation_year_end'] and item['date']['creation_year_end']>=work['creation_year_start']:
                possible_sources[work['artwork_id']].add(item['_id'])
    # Start with selected works already in the catalogue, then broaden coverage.
    featured=sorted(featured,key=lambda w:not bool(title_candidates(w)))
    seen=set()
    for item in featured:
        if len(result['matches'])>=artist.get('selection_limit',1 if artist.get('new_authority') else 3):break
        if item['_id'] in excluded_source_ids:continue
        date=item.get('date');url=urljoin(source['url'],item['paintingUrl'])
        if not date or url in seen:continue
        if 'reconstruction' in item['title'].casefold():
            result['held'].append({'url':url,'reason':'Modern reconstruction date is not the ancient original date'});continue
        seen.add(url)
        if item['artistUrl']!=urlparse(source['url']).path:
            result['held'].append({'url':url,'reason':'Featured artist identity differs'});continue
        # A whole lifespan presented as a date is not a reliable creation date.
        if date['creation_year_start']==source.get('birth_year') and date['creation_year_end']==source.get('death_year'):
            result['held'].append({'url':url,'reason':'Creation interval repeats artist lifespan'});continue
        candidates=title_candidates(item)
        if candidates:
            valid=[w for w in candidates if w['creation_year_start'] is not None and w['creation_year_end'] is not None
                and w['creation_year_start']<=date['creation_year_end'] and w['creation_year_end']>=date['creation_year_start']
                and w['creation_year_end']<=1955 and w['status']!='archived' and len(w['creators'])==1 and w['creators'][0]['role']=='primary']
            if len(valid)!=1:
                result['held'].append({'url':url,'reason':'Existing title has uncertain identity/date/attribution','ids':[w['artwork_id'] for w in candidates]});continue
            work=valid[0]
            if work['primary_media_id']:continue
            if len(possible_sources[work['artwork_id']])>1:
                result['held'].append({'url':url,'reason':'Multiple source objects match the existing title/date','artwork_id':work['artwork_id']});continue
            work['artist']=artist
            if m.norm(item['title']) not in {m.norm(work['title']),m.norm(work.get('alternate_title'))}:
                url=url.replace('/en/','/ru/')
        else:
            aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikiart.org/artwork/'+item['_id']))
            work={'artwork_id':aid,'slug':'wikiart-'+item['_id'],'title':item['title'],'alternate_title':None,
                **date,'work_type':'unknown','status':'review','research_candidate':True,'primary_media_id':None,
                'current_institution_id':None,'accession_number':None,'institution':None,'artist':artist,
                'creators':[{'id':artist['id'],'slug':artist['slug'],'name':artist['display_name'],'role':'primary'}],
                'identifiers':[{'scheme':'wikiart-artwork','external_id':item['_id'],'url':url}],
                'before_record':None,'new_record':True}
            if artist.get('object_level_creator'):
                labels=artist.get('source_creator_labels',{})
                work.update(creators=[],unlinked_creator_label=labels.get(item['_id'],artist.get('unlinked_creator_label','Creator not recorded')),cultural_context=artist.get('source_group'))
        match={'work':work,'wikiart':{'title':item['title'],'url':url,'year':date['creation_year_start'],'source_id':item['_id']},
            'selection_basis':'WikiArt artist profile explicitly lists this work in famous-works; artist-first breadth pass, up to three additional reproductions per artist.',
            'index_receipt':profile['receipt']}
        result['matches'].append(match)
    m.save_atomic(output,result)
    print('Selected',artist['display_name'],len(result['matches']),'new',sum(bool(x['work'].get('new_record')) for x in result['matches']),flush=True)


def select():
    inventory=json.loads((RUN/'artist-matches.json').read_bytes());pairs=inventory['matches']
    with m.read_only() as db:
        while True:
            extra_path=RUN/'extra-artist-matches.json';groups=RUN/'priority-group-matches.json'
            pairs=list(inventory['matches'])
            if extra_path.exists():
                extras=json.loads(extra_path.read_bytes())['matches'];holds=RUN/'artist-identity-holds.json'
                excluded={r['artist_id'] for r in json.loads(holds.read_bytes())['held']} if holds.exists() else set()
                pairs+=[p for p in extras if p['artist']['id'] not in excluded]
            if groups.exists():pairs+=json.loads(groups.read_bytes())['matches']
            pending=[pair for pair in pairs if not (RUN/'discovery-v2'/(pair['artist']['id']+'.json')).exists()]
            if not pending and (RUN/'extra-artists-finished.json').exists():break
            done=0
            for pair in pending:
                slug=urlparse(pair['wikiart']['url']).path.rsplit('/',1)[-1]
                if not (RUN/'profiles'/(slug+'.json')).exists():continue
                select_one(pair,db);done+=1
            if not done:time.sleep(5)
    matches=m.discovered_matches()
    m.save_atomic(RUN/'discovered-v2.json',{'matches':matches,'at':m.core.now(),'artist_count':len(pairs)})
    print('Selection finished',len(matches),flush=True)


def source_life(source):
    value=source['life_display'];match=re.fullmatch(r'(c\.)?\s*(\d{3,4})\s*-\s*(c\.)?\s*(\d{3,4})',value)
    if match:return {'birth_year':int(match[2]),'death_year':int(match[4]),
        'birth_display':('c.' if match[1] else '')+match[2],'death_display':('c.' if match[3] else '')+match[4],
        'birth_precision':'circa' if match[1] else 'exact','death_precision':'circa' if match[3] else 'exact'}
    match=re.fullmatch(r'born\s+(c\.)?\s*(\d{3,4})',value)
    if match:return {'birth_year':int(match[2]),'death_year':None,'birth_display':('c.' if match[1] else '')+match[2],
        'death_display':None,'birth_precision':'circa' if match[1] else 'exact','death_precision':None}
    return None


def extra_artists():
    inventory=json.loads((RUN/'artist-matches.json').read_bytes())
    catalogue=json.loads((RUN/'catalogue-artists.json').read_bytes())['artists']
    token_names=collections.defaultdict(dict);last_names=collections.defaultdict(dict)
    for artist in catalogue:
        for name in [artist['display_name']]+artist['aliases']:
            parts=m.norm(name).split()
            if not parts:continue
            token_names[' '.join(sorted(parts))][artist['id']]=artist
            last_names[parts[-1]][artist['id']]=artist
    sources=inventory['unmatched_source_artists'];outcomes=[];matches=[]
    for source in sources:
        slug=urlparse(source['url']).path.rsplit('/',1)[-1];output=RUN/'extra-artists'/(slug+'.json')
        while not (RUN/'profiles'/(slug+'.json')).exists():time.sleep(5)
        if output.exists():result=json.loads(output.read_bytes())
        else:
            profile=json.loads((RUN/'profiles'/(slug+'.json')).read_bytes());eligible=[w for w in profile['featured'] if w.get('date')]
            result={'wikiart':source,'outcome':'no_eligible_featured_work'}
            life=source_life(source)
            if re.search(r'\b(architecture|pottery|mosaics|icons|ancient|school|workshop|collective|anonymous|unknown)\b',source['name'],re.I):life=None
            if eligible and life:
                parts=m.norm(source['name']).split();candidates=list(token_names[' '.join(sorted(parts))].values())
                compatible=[a for a in candidates if all(life.get(k) is None or a.get(k) is None or life[k]==a[k] for k in ('birth_year','death_year'))]
                if len(compatible)==1:result.update(outcome='reconciled_existing',artist=compatible[0])
                elif candidates:result.update(outcome='identity_needs_reconciliation',candidate_ids=[a['id'] for a in candidates])
                else:
                    near=[a for a in last_names[parts[-1]].values()
                        if any(life.get(k) is not None and a.get(k)==life[k] for k in ('birth_year','death_year'))
                        or difflib.SequenceMatcher(None,m.norm(a['display_name']),m.norm(source['name'])).ratio()>=0.88]
                    if near:result.update(outcome='possible_existing_identity',candidate_ids=[a['id'] for a in near])
                    else:
                        years=[n for w in eligible for n in (w['date']['creation_year_start'],w['date']['creation_year_end'])]
                        start,end=min(years),max(years)
                        if life['birth_year'] and start<life['birth_year']:
                            result.update(outcome='work_date_predates_source_birth')
                        else:
                            artist={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,source['url'])),'slug':'wikiart-artist-'+slug,
                                'display_name':source['name'],'sort_name':source['name'],'normalized_name':m.norm(source['name']),
                                'entity_type':'person','status':'review','new_authority':True,**life,'priority':False,'popular':False,'aliases':[],
                                'timeline_start_year':life['birth_year'] if life['death_year'] else start,
                                'timeline_end_year':life['death_year'] or end,
                                'timeline_basis':'life' if life['death_year'] else 'activity',
                                'timeline_display':source['life_display'] if life['death_year'] else 'Documented featured works: '+str(start)+('–'+str(end) if end!=start else ''),
                                'source_url':source['url'],'directory_receipt':source['directory_receipt'],'profile_receipt':profile['receipt']}
                            result.update(outcome='new_named_artist',artist=artist)
            elif eligible:result.update(outcome='creator_kind_or_life_dates_need_reconciliation')
            m.save_atomic(output,result)
        outcomes.append(result)
        if result.get('artist'):matches.append({'artist':result['artist'],'wikiart':source})
        if len(outcomes)%25==0:print('Additional artists',len(outcomes),dict(collections.Counter(r['outcome'] for r in outcomes)),flush=True)
    # Source directory duplicates pointing to an already processed artist remain
    # one catalogue identity and must not replace its earlier selected metadata.
    existing={p['artist']['id'] for p in inventory['matches']};distinct={}
    for pair in matches:
        if pair['artist']['id'] not in existing:distinct.setdefault(pair['artist']['id'],pair)
    m.save_atomic(RUN/'extra-artist-matches.json',{'matches':list(distinct.values()),'counts':dict(collections.Counter(r['outcome'] for r in outcomes))})
    m.save_atomic(RUN/'extra-artists-finished.json',{'at':m.core.now(),'inspected':len(outcomes),'matched':len(distinct)})
    print('Additional artist selection finished',len(distinct),flush=True)


def configure_preparation():
    m.Fetcher=SharedFetcher
    original=m.page_record
    def record(match,raw,receipt):
        try:result=original(match,raw,receipt)
        except ValueError as error:
            if str(error)!='Artwork metadata missing' or '/ModalLogIn' not in receipt['final_url']:raise
            # The public profile itself supplies an explicitly featured object
            # and a public CDN image URL. Use only that public data; do not
            # authenticate, retry the gated page or infer its rights statement.
            slug=match['index_receipt']['final_url'].rstrip('/').rsplit('/',1)[-1]
            profile=json.loads((RUN/'profiles'/(slug+'.json')).read_bytes())
            entries=[w for w in profile['featured'] if urljoin(profile['receipt']['final_url'],w['paintingUrl'])==match['wikiart']['url']]
            if len(entries)!=1:raise ValueError('Public featured object identity is ambiguous')
            source=entries[0];work=match['work'];date=dated(source.get('year'))
            if not date or date['creation_year_start']>work['creation_year_end'] or date['creation_year_end']<work['creation_year_start']:
                raise ValueError('Public profile creation date differs')
            if m.norm(source['title']) not in {m.norm(work['title']),m.norm(work.get('alternate_title'))}:raise ValueError('Public profile title differs')
            if source['artistUrl']!=urlparse(profile['source']['url']).path:raise ValueError('Public profile creator differs')
            result={'artwork_id':work['artwork_id'],'title':work['title'],'artist':work['artist']['display_name'],
                'artist_slug':work['artist']['slug'],'work':work,'page':profile['receipt']['final_url'],
                'source_image_url':source['image'],'source_id':source['_id'],'source_year':date['creation_year_start'],
                'source_year_end':date['creation_year_end'],'rights_status':'unknown','license_label':'Rights not specified on public artist profile',
                'source_rights_label':None,'policy_url':'https://www.wikiart.org/en/terms-of-use','page_receipt':profile['receipt'],
                'source_metadata':source,'source_image_variants':[],'source_description':'Public artist profile famous-works metadata and its publicly linked image; artwork detail page redirects to sign-in.',
                'checked_at':profile['receipt']['checked_at'],'detail_page_receipt':receipt}
        result['selection_basis']=match['selection_basis'];result['selection_receipt']=match['index_receipt']
        if result['work']['artist'].get('object_level_creator'):
            result['artist']=result['work']['unlinked_creator_label']+(' — '+result['work']['cultural_context'] if result['work'].get('cultural_context') else '')
        if result['work'].get('new_record'):
            if result['source_id']!=result['work']['identifiers'][0]['external_id']:raise ValueError('Featured artwork identifier changed')
            date=dated(result['source_metadata'].get('year'))
            if not date:raise ValueError('New artwork date unresolved')
            result['work'].update(date)
        return result
    m.page_record=record


def prepare():
    configure_preparation()
    m.prepare()


def target_before(db,im):
    work=im['work'];unlinked=work['artist'].get('object_level_creator',False)
    artist={'record':None} if unlinked else db.execute('SELECT to_jsonb(p) record FROM artists p WHERE slug=%s',(im['artist_slug'],)).fetchone()
    if not artist:
        if not work['artist'].get('new_authority'):return {'outcome':'held','reason':'Artist authority absent in target'}
        known=db.execute('SELECT id FROM artists WHERE normalized_name=%s OR lower(display_name)=lower(%s)',(work['artist']['normalized_name'],im['artist'])).fetchall()
        aliases=db.execute('SELECT artist_id FROM artist_aliases WHERE normalized_alias=%s',(work['artist']['normalized_name'],)).fetchall()
        if known or aliases:return {'outcome':'held','reason':'New artist name already exists in target'}
        artist=work['artist']
    else:artist=artist['record']
    if not unlinked and m.norm(artist['display_name'])!=m.norm(work['artist']['display_name']):return {'outcome':'held','reason':'Target artist identity differs'}
    existing=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(im['artwork_id'],)).fetchone()
    identifiers=work.get('identifiers') or []
    if not existing and identifiers:
        alternatives=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) AS x(scheme text,external_id text))
            SELECT DISTINCT to_jsonb(a) record FROM input x JOIN external_identifiers e ON e.entity_type='artwork'
            AND e.scheme=x.scheme AND e.external_id=x.external_id JOIN artworks a ON a.id=e.entity_id""",(m.Jsonb(identifiers),)).fetchall()
        if len(alternatives)>1:return {'outcome':'held','reason':'Multiple identifier matches'}
        if alternatives:existing=alternatives[0]
    if existing:
        existing=existing['record']
        if work.get('new_record'):
            if existing['id']!=im['artwork_id'] or any(existing[k]!=work[k] for k in ('slug','title','creation_year_start','creation_year_end','date_precision','work_type','status','research_candidate')):
                return {'outcome':'held','reason':'New identity conflicts with existing target'}
        elif not m.same_artwork(existing,work['before_record']):return {'outcome':'held','reason':'Target record differs'}
        if existing['primary_media_id'] not in (None,im['media_id']):return {'outcome':'held','reason':'Existing primary image preserved'}
        creators=db.execute('SELECT artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=%s',(existing['id'],)).fetchall()
        if creators!=([] if unlinked else [{'artist_id':artist['id'],'attribution_role':'primary'}]):return {'outcome':'held','reason':'Attribution differs'}
        if not work.get('new_record'):
            institution=db.execute('SELECT slug FROM institutions WHERE id=%s',(existing['current_institution_id'],)).fetchone() if existing['current_institution_id'] else None
            if (institution or {}).get('slug')!=(work.get('institution') or {}).get('slug'):return {'outcome':'held','reason':'Holding differs'}
        return {'outcome':'attach','artist':artist,'record':existing}
    if not work.get('new_record'):return {'outcome':'held','reason':'Existing artwork absent in target'}
    if unlinked:return {'outcome':'create','artist':None,'record':None}
    # Do not create a second object under a coincident title while processing a
    # source whose catalogue mapping changed since metadata selection.
    current=db.execute('SELECT a.id::text artwork_id,a.title,a.alternate_title FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s',(artist['id'],)).fetchall()
    conflicts=[w['artwork_id'] for w in current if m.norm(im['title']) in {m.norm(w['title']),m.norm(w.get('alternate_title'))}]
    if conflicts:
        path=RUN/'title-identity-resolutions'/(im['artwork_id']+'.json')
        resolution=json.loads(path.read_bytes()) if path.exists() else {}
        if resolution.get('image_sha256')!=im['sha256'] or not set(conflicts).issubset(resolution.get('distinct_from',[])):
            return {'outcome':'held','reason':'Title already exists in target','ids':conflicts}
    return {'outcome':'create','artist':artist,'record':None}


def apply_image(db,im,state):
    if state['outcome']=='held':return {'outcome':'held','reason':state['reason']}
    with db.transaction():
        db.execute("SET LOCAL lock_timeout='3s'")
        current=target_before(db,im)
        if current!=state:raise ValueError('Target changed after recovery snapshot')
        if state['outcome']=='create':
            w=im['work']
            source=db.execute("SELECT id FROM sources WHERE slug='wikiart-artist-coverage-20260920'").fetchone()
            if source is None:
                source=db.execute("""INSERT INTO sources(slug,name,source_type,base_url) VALUES('wikiart-artist-coverage-20260920',
                    'WikiArt artist-first featured artwork selection','collection_page','https://www.wikiart.org/')
                    ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id""").fetchone()
            sid=source['id']
            if state['artist'] and state['artist'].get('new_authority'):
                a=state['artist']
                db.execute("""INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,entity_type,birth_year,death_year,
                    birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,timeline_display,
                    timeline_basis,status,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,'person',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',%s,%s)""",
                    tuple(a[k] for k in ('id','slug','display_name','sort_name','normalized_name','birth_year','death_year','birth_display','death_display',
                        'birth_precision','death_precision','timeline_start_year','timeline_end_year','timeline_display','timeline_basis'))+(m.ACTOR,m.ACTOR))
                db.execute("""INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                    VALUES('artist',%s,'wikiart-artist',%s,%s,%s,%s)""",(a['id'],urlparse(a['source_url']).path.rsplit('/',1)[-1],a['source_url'],sid,im['checked_at']))
                db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by)
                    VALUES('artist',%s,%s,'wikiart_named_artist',%s,%s,%s,%s)""",(a['id'],sid,a['source_url'],json.dumps({
                        'directory':a['directory_receipt'],'profile':a['profile_receipt'],'life_display':a['birth_display']+'–'+str(a['death_display']),
                        'timeline_basis':a['timeline_basis'],'biography_and_geography':'Not inferred'},ensure_ascii=False),im['checked_at'],m.ACTOR))
            db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,
                date_precision,work_type,status,research_candidate,created_by,updated_by)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'unknown','review',true,%s,%s)""",
                (im['artwork_id'],w['slug'],w['title'],m.norm(w['title']),w['date_display'],w['creation_year_start'],w['creation_year_end'],w['date_precision'],m.ACTOR,m.ACTOR))
            if state['artist']:
                db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                    (im['artwork_id'],state['artist']['id'],'WikiArt artwork page names this artist and is listed on the matching artist profile; source attribution retained for review.'))
            else:
                db.execute('UPDATE artworks SET unlinked_creator_label=%s,cultural_context=%s WHERE id=%s',
                    (w['unlinked_creator_label'],w['cultural_context'],im['artwork_id']))
            db.execute("""INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                VALUES('artwork',%s,'wikiart-artwork',%s,%s,%s,%s)""",(im['artwork_id'],im['source_id'],im['page'],sid,im['checked_at']))
            note=json.dumps({'selection_basis':im['selection_basis'],'selection_receipt':im['selection_receipt'],
                'artwork_receipt':im['page_receipt'],'source_metadata':im['source_metadata'],
                'identity_review':im.get('identity_review'),
                'unknown_fields':'Type, accepted holding, current display and biography not inferred.'},ensure_ascii=False)
            db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                VALUES('artwork',%s,%s,'wikiart_featured_identity',%s,%s,%s,%s,%s)""",(im['artwork_id'],sid,im['source_id'],im['page'],note,im['checked_at'],m.ACTOR))
            before=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(im['artwork_id'],)).fetchone()['record']
        else:before=state['record']
        attachment=m.attach(db,im,before)
        after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(before['id'],)).fetchone()['record']
        return {'outcome':attachment,'created':state['outcome']=='create','before_attachment':before,'after':after}


def deliver_one(path,dbs,bucket):
    im=json.loads(path.read_bytes());aid=im['artwork_id'];receipt_path=RUN/'delivery'/path.name
    if receipt_path.exists():return json.loads(receipt_path.read_bytes())
    plan_path=RUN/'delivery-plans'/path.name
    if plan_path.exists():plan=json.loads(plan_path.read_bytes())
    else:
        states={t:target_before(db,im) for t,db in dbs.items()}
        backup=m.BACKUP/'preimages'/path.name;m.save_atomic(backup,states)
        plan={'targets':states,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes())}
        m.save_atomic(plan_path,plan)
    if m.core.sha(Path(plan['backup']).read_bytes())!=plan['backup_sha256']:raise ValueError('Recovery checksum differs')
    data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
    if len(data)>100000 or len(data)!=im['bytes'] or m.core.sha(data)!=im['sha256']:raise ValueError('Image checksum/size differs')
    blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'artwork-id':aid,'provider':'WikiArt','source-record-id':im['source_id']}
    blob.cache_control='public,max-age=31536000,immutable'
    try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
    except m.PreconditionFailed:blob.reload(timeout=30)
    if blob.size!=len(data) or blob.md5_hash!=base64.b64encode(hashlib.md5(data).digest()).decode():raise ValueError('Uploaded bytes differ')
    receipts={}
    for target,db in dbs.items():
        applied_path=RUN/'applied'/target/path.name
        if applied_path.exists():receipts[target]=json.loads(applied_path.read_bytes());continue
        state=plan['targets'][target];actual=target_before(db,im)
        if state['outcome']!='held' and actual['outcome']=='attach' and actual['record']['primary_media_id']==im['media_id']:
            result={'outcome':'already_attached','created':state['outcome']=='create','after':actual['record'],
                'before_attachment':state['record'],'recovered_receipt':True}
        else:
            try:result=apply_image(db,im,state)
            except ValueError as error:
                if str(error)!='Target changed after recovery snapshot':raise
                fresh=target_before(db,im)
                m.save_atomic(RUN/'target-changes'/target/path.name,{'before':state,'after':fresh,'at':m.core.now()})
                result={'outcome':'held','reason':'Target changed after recovery snapshot; current record preserved','current_outcome':fresh['outcome']}
        m.save_atomic(applied_path,result);receipts[target]=result
    receipt={'artwork_id':aid,'at':m.core.now(),'path':im['path'],'sha256':im['sha256'],'generation':blob.generation,'targets':receipts}
    m.save_atomic(receipt_path,receipt)
    print('Delivered',im['artist'],im['title'][:65],{t:r['outcome'] for t,r in receipts.items()},flush=True)
    return receipt


def deliver_ready():
    bucket=m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    dsns={'local':'postgres://localhost/artline','cloud':m.core.cloud_dsn()}
    contexts=threading.local();connections=[];counts=collections.Counter();artist_locks={};lock_guard=threading.Lock()
    def worker(path):
        if not hasattr(contexts,'dbs'):
            contexts.dbs={t:m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) for t,dsn in dsns.items()}
            connections.extend(contexts.dbs.values())
        artist_slug=json.loads(path.read_bytes())['artist_slug']
        with lock_guard:artist_lock=artist_locks.setdefault(artist_slug,threading.Lock())
        with artist_lock:return deliver_one(path,contexts.dbs,bucket)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            while True:
                paths=[p for p in sorted((RUN/'images').glob('*.json')) if not (RUN/'delivery'/p.name).exists()]
                if paths:
                    for receipt in pool.map(worker,paths[:40]):
                        counts['uploaded']+=1
                        for target,result in receipt['targets'].items():counts[target+'_'+result['outcome']]+=1
                    print('Delivery progress',dict(counts),flush=True)
                elif (RUN/'preparation-finished.json').exists():break
                else:time.sleep(10)
    finally:
        for db in connections:db.close()
    m.save_atomic(RUN/'delivery-finished.json',{'at':m.core.now(),'total_receipts':len(list((RUN/'delivery').glob('*.json')))})
    print('Delivery finished',dict(counts),flush=True)


def verify():
    receipts=[json.loads(p.read_bytes()) for p in sorted((RUN/'delivery').glob('*.json'))]
    images={r['artwork_id']:json.loads((RUN/'images'/(r['artwork_id']+'.json')).read_bytes()) for r in receipts}
    errors=[];totals={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        new_artists={}
        attached=[r for r in receipts if r['targets'][target]['outcome'] in ('attached','already_attached')]
        ids=[r['targets'][target]['after']['id'] for r in attached]
        with m.read_only(dsn) as db:
            rows=db.execute('SELECT to_jsonb(a) artwork,to_jsonb(ma) media FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
            actual={r['artwork']['id']:r for r in rows}
            for receipt in attached:
                aid=receipt['artwork_id'];im=images[aid];expected=receipt['targets'][target]['after'];row=actual.get(expected['id'])
                if not row or row['artwork']!=expected:
                    errors.append({'target':target,'artwork_id':aid,'error':'Artwork changed after recorded attachment'});continue
                media=row['media']
                if media['id']!=im['media_id'] or media['checksum_sha256']!=im['sha256'] or media['byte_size']!=im['bytes'] or media['byte_size']>100000 or media['rights_status']!=im['rights_status'] or media['source_page_url']!=im['page']:
                    errors.append({'target':target,'artwork_id':aid,'error':'Media metadata differs'})
                if im['work'].get('new_record') and im['work']['identifiers'][0]['external_id']!=im['source_id']:
                    errors.append({'target':target,'artwork_id':aid,'error':'Featured identifier differs'})
                if im['work']['artist'].get('new_authority'):new_artists[im['work']['artist']['id']]=im['work']['artist']
            identities=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(list(new_artists),)).fetchall()
            byid={r['record']['id']:r['record'] for r in identities}
            for aid,a in new_artists.items():
                current=byid.get(aid)
                if not current or any(current[k]!=a[k] for k in ('slug','display_name','birth_year','death_year','birth_precision','death_precision','timeline_start_year','timeline_end_year','timeline_basis','timeline_display','status')):
                    errors.append({'target':target,'artist_id':aid,'error':'New artist metadata differs'})
            new_ids=[r['targets'][target]['after']['id'] for r in attached if images[r['artwork_id']]['work'].get('new_record')]
            selected=db.execute("""SELECT a.id::text FROM artworks a WHERE a.id=ANY(%s::uuid[])
                AND a.status='review' AND a.research_candidate AND a.current_institution_id IS NULL
                AND EXISTS(SELECT 1 FROM curated_collection_items i JOIN curated_collections c ON c.id=i.collection_id
                    WHERE i.artwork_id=a.id AND c.curator_kind='owner' AND c.institution_id IS NULL
                    AND c.status<>'archived')""",(new_ids,)).fetchall()
            if len(selected)!=len(new_ids):
                errors.append({'target':target,'error':'New artwork review state or personal collection membership differs',
                    'artwork_ids':sorted(set(new_ids)-{r['id'] for r in selected})})
            totals[target]={'attached':len(attached),'new_artworks':sum(r['targets'][target].get('created',False) for r in attached),
                'held':len(receipts)-len(attached),'new_artists':len(byid),'personal_collection_items':len(selected)}
    def check_file(receipt):
        im=images[receipt['artwork_id']];local=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        result={'artwork_id':receipt['artwork_id'],'local_verified':len(local)<=100000 and len(local)==im['bytes'] and m.core.sha(local)==im['sha256']}
        try:
            response=m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'],timeout=(15,45))
            result.update(http_status=response.status_code,public_verified=response.status_code==200 and m.core.sha(response.content)==im['sha256'])
        except m.requests.RequestException as error:result.update(public_verified=False,error=str(error)[:160])
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:files=list(pool.map(check_file,receipts))
    errors.extend(r for r in files if not r['local_verified'] or not r['public_verified'])
    samples={}
    for receipt in receipts:
        im=images[receipt['artwork_id']]
        if receipt['targets']['cloud']['outcome'] in ('attached','already_attached'):
            samples.setdefault((im['artist_slug'],im['rights_status']),receipt)
    sampled=sorted(samples.values(),key=lambda r:(images[r['artwork_id']]['rights_status']=='public_domain',not images[r['artwork_id']]['work']['artist'].get('new_authority',False)))[:40]
    sampled_ids={r['artwork_id'] for r in sampled}
    sampled.extend(r for r in receipts if r['artwork_id'] not in sampled_ids
        and images[r['artwork_id']]['work']['artist'].get('object_level_creator')
        and r['targets']['cloud']['outcome'] in ('attached','already_attached'))
    api=[]
    for receipt in sampled:
        im=images[receipt['artwork_id']];aid=receipt['targets']['cloud']['after']['id']
        endpoint='/atlas/artworks/'+aid if im['work']['artist'].get('object_level_creator') else '/artists/'+im['artist_slug']+'/works/'+aid
        response=m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1'+endpoint,timeout=(15,45))
        record=response.json() if response.status_code==200 else {}
        good=response.status_code==200 and record.get('title')==im['title'] and record.get('media_url')==im['path']
        api.append({'artwork_id':aid,'verified':good,'http_status':response.status_code})
        if not good:errors.append({'artwork_id':aid,'error':'Public artwork API differs'})
    result={'at':m.core.now(),'uploaded':len(receipts),'artists':len({im['artist_slug'] for im in images.values()}),
        'bytes':sum(im['bytes'] for im in images.values()),'max_bytes':max((im['bytes'] for im in images.values()),default=0),
        'rights_labels':dict(collections.Counter(im['rights_status'] for im in images.values())),
        'databases':totals,'file_checks':files,'api_checks':api,'errors':errors}
    path=RUN/('verification-'+str(len(receipts))+'-'+str(int(time.time()))+'.json');m.save_atomic(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('file_checks','api_checks')},ensure_ascii=False),flush=True)
    print('Verification receipt',path,flush=True)
    if errors:raise SystemExit(1)


def sync_selection(targets=('local','cloud'), receipt_directory='delivery', finished_marker='delivery-finished.json', output_marker='personal-selection-finished.json'):
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    dsns={target:('postgres://localhost/artline' if target=='local' else m.core.cloud_dsn()) for target in targets}
    dbs={t:m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) for t,dsn in dsns.items()}
    try:
        for target,db in dbs.items():
            before=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE institution_id IS NULL AND curator_kind=%s',('owner',)).fetchall()
            backup=m.BACKUP/'personal-collection-selection'/(target+'-before.json')
            if not backup.exists():m.save_atomic(backup,{'collections':before})
            db.execute("""INSERT INTO curated_collections(id,institution_id,curator_kind,title,status)
                VALUES(%s,NULL,'owner','Personal artwork collection','review') ON CONFLICT(id) DO NOTHING""",(collection_id,))
        while True:
            for target,db in dbs.items():
                entries=[]
                for path in sorted((RUN/receipt_directory).glob('*.json')):
                    if (RUN/'personal-selection'/target/path.name).exists():continue
                    receipt=json.loads(path.read_bytes());result=receipt['targets'][target]
                    if result['outcome'] not in ('attached','already_attached'):continue
                    im=json.loads((RUN/'images'/path.name).read_bytes())
                    if not im['work'].get('new_record'):continue
                    entries.append({'image_artwork_id':im['artwork_id'],'artwork_id':result['after']['id'],'source_url':im['page'],
                        'checked_at':im['checked_at'],'reason':'Owner collection selection requested 20 September 2026: artist-by-artist historical artwork coverage, drawn from WikiArt famous-works. Source creation date ends by 1955. This is a personal collection selection, not a museum designation or holding claim.'})
                    if len(entries)>=100:break
                if not entries:continue
                batch=m.core.sha(m.core.encode(entries))[:16]
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='3s'")
                    collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                    if collection['status']=='archived' or collection['curator_kind']!='owner' or collection['institution_id'] is not None:raise ValueError('Personal collection identity changed')
                    existing=db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',
                        (collection_id,[e['artwork_id'] for e in entries])).fetchall()
                    snapshot=m.BACKUP/'personal-collection-selection'/target/(batch+'.json')
                    m.save_atomic(snapshot,{'collection':collection,'items':existing,'selected':entries})
                    sid=db.execute("SELECT id FROM sources WHERE slug='wikiart-artist-coverage-20260920'").fetchone()['id']
                    db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) AS x(artwork_id uuid,source_url text,checked_at timestamptz,reason text)),
                        positions AS(SELECT coalesce(max(position),0) AS n FROM curated_collection_items WHERE collection_id=%s),
                        selected AS(SELECT x.*,row_number() OVER(ORDER BY x.artwork_id)::int ord FROM input x JOIN artworks a ON a.id=x.artwork_id
                            WHERE a.status<>'archived' AND a.creation_year_end<=1955 AND a.creation_year_start IS NOT NULL)
                        INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                        SELECT %s,s.artwork_id,p.n+s.ord,s.reason,%s,s.source_url,s.checked_at FROM selected s CROSS JOIN positions p
                        ON CONFLICT(collection_id,artwork_id) DO NOTHING""",(m.Jsonb(entries),collection_id,collection_id,sid))
                    db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
                    actual=db.execute('SELECT artwork_id::text,id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',
                        (collection_id,[e['artwork_id'] for e in entries])).fetchall()
                    if len(actual)!=len(entries):raise ValueError('Selected work changed creation eligibility')
                byid={r['artwork_id']:r['id'] for r in actual}
                for entry in entries:m.save_atomic(RUN/'personal-selection'/target/(entry['image_artwork_id']+'.json'),{
                    'artwork_id':entry['artwork_id'],'item_id':byid[entry['artwork_id']],'collection_id':collection_id,'at':m.core.now(),'backup':str(snapshot)})
                print('Personal collection',target,'added',len(entries),flush=True)
            if (RUN/finished_marker).exists():
                remaining=False
                for target in dbs:
                    for path in (RUN/receipt_directory).glob('*.json'):
                        r=json.loads(path.read_bytes())['targets'][target]
                        if r['outcome'] in ('attached','already_attached') and r.get('created') and not (RUN/'personal-selection'/target/path.name).exists():remaining=True
                if not remaining:break
            time.sleep(5)
    finally:
        for db in dbs.values():db.close()
    m.save_atomic(RUN/output_marker,{'at':m.core.now(),'collection_id':collection_id})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['inventory','profiles','select','extra_artists','prepare','deliver_ready','verify','sync_selection']);args=parser.parse_args();globals()[args.phase]()
