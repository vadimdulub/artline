#!/usr/bin/env python3
"""UK painter source census and selected historical artwork delivery."""
import argparse, collections, concurrent.futures, importlib.util, json, re, time, uuid
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('coverage',ROOT/'ops/wikiart-artist-coverage.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m
PRIOR=c.RUN
RUN=ROOT/'docs/research/uk-painters-20260920'
c.RUN=m.RUN=RUN
m.BACKUP=Path.home()/'Library/Application Support/Artline/backups/uk-painters-20260920'
m.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images/uk-painters-20260920'
SOURCE='uk-painters-20260920'
ACTOR=m.ACTOR
s=importlib.util.spec_from_file_location('wikimedia',ROOT/'ops/research-wikimedia-catalogues.py')
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
w.RUN=RUN;w.BACKUPS=m.BACKUP
COUNTRIES={'Q145':'United Kingdom','Q174193':'United Kingdom of Great Britain and Ireland','Q161885':'Kingdom of Great Britain','Q179876':'Kingdom of England','Q230791':'Kingdom of Scotland','Q21':'England','Q22':'Scotland','Q25':'Wales','Q26':'Northern Ireland'}


def save(path, value):
    m.save_atomic(path, value)

def captured(url):
    # Wikimedia documents this as the equivalent main-graph service. The
    # default host returned HTTP 502 even for a five-row diagnostic query.
    # https://www.mediawiki.org/wiki/Wikidata_query_service
    if url.startswith('https://query.wikidata.org/'):
        url=url.replace('https://query.wikidata.org/','https://query-main.wikidata.org/',1)
    return w.fetch(url)

def claims(entity, prop):
    rows = [v for v in entity.get('claims', {}).get(prop, []) if v.get('rank') != 'deprecated' and v.get('mainsnak', {}).get('snaktype') == 'value']
    return [v for v in rows if v.get('rank') == 'preferred'] or rows

def values(entity, prop):
    return [v['mainsnak']['datavalue']['value'] for v in claims(entity, prop)]

def label(entity):
    return next((entity['labels'][lang]['value'] for lang in ('en', 'mul', 'cy', 'gd', 'ga', 'fr') if lang in entity.get('labels', {})), entity['id'])

def names(entity):
    return list(dict.fromkeys([v['value'] for v in entity.get('labels', {}).values()] + [v['value'] for group in entity.get('aliases', {}).values() for v in group]))

def year(entity, prop):
    return w.year(entity, prop)

def entities(ids):
    missing = [q for q in ids if not (RUN / 'entities' / (q + '.json')).exists()]
    for start in range(0, len(missing), 50):
        part = missing[start:start + 50]
        # This bounded metadata phase is answering the waiting user's request.
        # MediaWiki explicitly permits interactive queries without maxlag:
        # https://www.mediawiki.org/wiki/Manual:Maxlag_parameter
        # Keep the shared pacing, HTTP retry/backoff and rate-limit handling.
        data, receipt = captured('https://www.wikidata.org/w/api.php?' + urlencode({'action': 'wbgetentities', 'ids': '|'.join(part), 'props': 'labels|descriptions|aliases|claims|sitelinks', 'languages': 'en|cy|gd|ga|fr|mul', 'format': 'json'}))
        for q in part:
            with w.evidence_lock('entity/'+q):
                path=RUN / 'entities' / (q + '.json')
                if not path.exists():save(path, {'entity': data['entities'][q], 'receipt': receipt})
        print('Captured authorities', start + len(part), 'of', len(missing), flush=True)
    return {q: json.loads((RUN / 'entities' / (q + '.json')).read_bytes()) for q in ids}


def source(db):
    db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,'UK painters — source authorities and selected artwork research','collection_page','https://www.wikidata.org/') ON CONFLICT(slug) DO NOTHING",(SOURCE,))
    return db.execute('SELECT id FROM sources WHERE slug=%s AND is_active',(SOURCE,)).fetchone()['id']


def discover():
    if not (RUN/'artist-baseline.json').exists():
        with m.read_only() as db:
            rows=db.execute("""SELECT to_jsonb(a) record,
                coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
                coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
                coalesce((SELECT jsonb_agg(to_jsonb(ac)) FROM artist_countries ac WHERE ac.artist_id=a.id),'[]') countries
                FROM artists a WHERE a.status<>'archived' ORDER BY a.id""").fetchall()
        save(RUN/'artist-baseline.json',{'at':m.core.now(),'artists':rows})
        print('Catalogue baseline',len(rows),'artists;',sum(any(v['country_code']=='GB' for v in r['countries']) for r in rows),'UK-linked',flush=True)
    rows=[]
    for country,title in COUNTRIES.items():
        path=RUN/'roster-discovery'/(country+'.json')
        if path.exists():data=json.loads(path.read_bytes())
        else:
            query='SELECT DISTINCT ?artist WHERE { ?artist wdt:P27 wd:'+country+'; wdt:P106/wdt:P279* wd:Q1028181 . } ORDER BY ?artist'
            response,receipt=captured('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
            data={'country':country,'country_name':title,'rows':response['results']['bindings'],'receipt':receipt,'query':query};save(path,data)
        rows.extend({'artist':v['artist'],'country':{'type':'uri','value':'http://www.wikidata.org/entity/'+country}} for v in data['rows'])
        print('Source census',title,len(data['rows']),flush=True)
    save(RUN/'roster-discovery.json',{'rows':rows,'country_scope':COUNTRIES,'limit':None})
    print('Distinct UK painter source identities',len({v['artist']['value'] for v in rows}),flush=True)


def wikiart_directory():
    raw,index_receipt=m.Fetcher().get('https://www.wikiart.org/en/artists-by-nation')
    soup=c.BeautifulSoup(raw,'html.parser')
    choices=[]
    for link in soup.select('a[href]'):
        href=link['href']
        if href.rsplit('/',1)[-1] in ('british','english','scottish','welsh','northern-irish'):
            choices.append(urljoin(index_receipt['final_url'],href).rstrip('/')+'/text-list')
    assert choices
    groups=[]
    for url in sorted(set(choices)):
        raw,receipt=m.Fetcher().get(url);soup=c.BeautifulSoup(raw,'html.parser');artists=[]
        for li in soup.select('li'):
            link=li.find('a',recursive=False);spans=li.find_all('span',recursive=False)
            if not link or not re.fullmatch(r'/en/[^/]+',link.get('href','')) or not re.search(r'\d+ artwork',li.get_text()):continue
            lifespan=spans[0].get_text(' ',strip=True).strip(', ') if spans else ''
            dates=re.fullmatch(r'(\d{4})\s*-\s*(\d{4})',lifespan)
            artists.append({'name':link.get_text(' ',strip=True),'url':urljoin(receipt['final_url'],link['href']),'life_display':lifespan,'birth_year':int(dates[1]) if dates else None,'death_year':int(dates[2]) if dates else None,'directory_receipt':receipt,'source_count':int(re.search(r'(\d+) artwork',li.get_text())[1])})
        save(RUN/'national-directories'/(url.split('/')[-2]+'.json'),{'artists':artists,'receipt':receipt})
        groups.extend(artists);print('WikiArt nationality',url.split('/')[-2],len(artists),flush=True)
    merged={}
    for artist in groups:
        entry=merged.setdefault(artist['url'],dict(artist,affiliation_sources=[]));entry['affiliation_sources'].append(artist['directory_receipt'])
    save(RUN/'wikiart-uk-directory.json',{'artists':list(merged.values()),'index_receipt':index_receipt})
    for artist in merged.values():
        slug=urlparse(artist['url']).path.rsplit('/',1)[-1];old=PRIOR/'profiles'/(slug+'.json');new=RUN/'profiles'/(slug+'.json')
        if old.exists() and not new.exists():save(new,old.read_bytes())
    print('Distinct WikiArt UK directory profiles',len(merged),flush=True)


def capture_authorities():
    roster=json.loads((RUN/'roster-discovery.json').read_bytes())
    entities(sorted({v['artist']['value'].rsplit('/',1)[-1] for v in roster['rows']}))


def discover_capture():
    discover();capture_authorities()


def capture_selected():
    qids=sorted({v['qid'] for v in json.loads((RUN/'work-candidate-selection.json').read_bytes())['selected']})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for captured_records in pool.map(entities,[qids[0::2],qids[1::2]]):print('Selected artwork authority shard complete',len(captured_records),flush=True)
    save(RUN/'selected-captures-finished.json',{'artworks':len(qids),'at':m.core.now()})


def roster_probe():
    query='SELECT DISTINCT ?artist ?country WHERE { VALUES ?country { '+' '.join('wd:'+q for q in COUNTRIES)+' } ?artist wdt:P106 wd:Q1028181; wdt:P27 ?country . } ORDER BY ?artist ?country'
    response=w.SESSION.get('https://query.wikidata.org/sparql',params={'query':query,'format':'json'},timeout=(15,65))
    print('Direct painter census response',response.status_code,len(response.content),flush=True)
    response.raise_for_status();data=response.json();receipt={'url':response.url,'retrieved_at':m.core.now(),'sha256':m.core.sha(response.content),'bytes':len(response.content)}
    save(RUN/'direct-painter-roster.json',{'query':query,'rows':data['results']['bindings'],'receipt':receipt})
    print('Direct painter authorities',len({v['artist']['value'] for v in data['results']['bindings']}),flush=True)


def life(entity,prop):
    result=w.date({'claims':{'P571':claims(entity,prop)}})
    return result if result['first'] is not None and result['first']==result['last'] else None


def name_keys(name):
    keys={m.norm(name)}
    if ',' in name:
        parts=[v.strip() for v in name.split(',')]
        if len(parts)==2:keys.add(m.norm(parts[1]+' '+parts[0]))
    return keys-{''}


def source_activity(entity):
    start=life(entity,'P2031');end=life(entity,'P2032')
    if start and end and start['first']<=end['first']<=2026:
        first,last=start['first'],end['first'];display=f'Documented active {first}–{last}; life dates unknown'
        return {'active_start_year':first,'active_end_year':last,'activity_display':display,'timeline_start_year':first,'timeline_end_year':last,'timeline_display':display,'timeline_basis':'activity'}
    period=claims(entity,'P1317')
    if len(period)!=1 or period[0].get('qualifiers'):return None
    value=period[0]['mainsnak']['datavalue']['value']
    if value.get('before') or value.get('after') or value.get('precision') not in (7,8,9,10,11):return None
    match=re.match(r'\+(\d+)-',value.get('time',''))
    if not match:return None
    yr=int(match[1])
    if yr>2026:return None
    if value['precision']==7:
        century=(yr+99)//100;first=(century-1)*100+1;last=century*100;display='Active in century '+str(century)+'; life dates unknown'
    elif value['precision']==8:first=(yr//10)*10;last=first+9;display='Active in the '+str(first)+'s; life dates unknown'
    else:first=last=yr;display='Documented active in '+str(yr)+'; life dates unknown'
    return {'active_start_year':first,'active_end_year':last,'activity_display':display,'timeline_start_year':first,'timeline_end_year':last,'timeline_display':display,'timeline_basis':'activity'}


def compatible_name_identity(existing,entity,birth,death):
    """A shared name and missing dates alone do not establish identity."""
    artist=existing['record']
    for prop,scheme in [('P6002','wikiart-artist'),('P2252','nga-constituent'),('P2741','tate-person'),('P2174','moma-person')]:
        supplied={v.rsplit('-',1)[-1] if prop=='P2741' else v for v in values(entity,prop) if isinstance(v,str)}
        known={v['external_id'] for v in existing['identifiers'] if v['scheme']==scheme}
        if supplied and known and not supplied.intersection(known):return False
    for key,value in [('birth_year',birth),('death_year',death)]:
        if value is not None and artist.get(key) is not None and value!=artist[key]:return False
    activity=[artist.get('active_start_year'),artist.get('active_end_year')]
    if artist.get('timeline_basis')=='activity':activity.extend([artist.get('timeline_start_year'),artist.get('timeline_end_year')])
    if any(v is not None and ((birth is not None and v<birth) or (death is not None and v>death)) for v in activity):return False
    return any(v is not None and artist.get(k)==v for k,v in [('birth_year',birth),('death_year',death)])


def authority_plan():
    roster=json.loads((RUN/'roster-discovery.json').read_bytes());qids=sorted({v['artist']['value'].rsplit('/',1)[-1] for v in roster['rows']})
    baseline=json.loads((RUN/'artist-baseline.json').read_bytes())['artists'];bykey=collections.defaultdict(dict);byid=collections.defaultdict(dict)
    for row in baseline:
        aid=row['record']['id']
        for ident in row['identifiers']:byid[(ident['scheme'],ident['external_id'])][aid]=row
        for name in [row['record']['display_name']]+row['aliases']:
            for key in name_keys(name):bykey[key][aid]=row
    selected=[];held=[];claimed={}
    for q in qids:
        path=RUN/'entities'/(q+'.json');capture=json.loads(path.read_bytes());e=capture['entity'];row={'qid':q,'name':label(e),'capture':str(path)}
        if e.get('id')!=q or not any(v.get('id')=='Q5' for v in values(e,'P31') if isinstance(v,dict)):
            held.append(dict(row,reason='Source entity is not an unreconciled human painter'));continue
        affiliations=sorted({v.get('id') for v in values(e,'P27') if isinstance(v,dict)}&set(COUNTRIES))
        if not affiliations:held.append(dict(row,reason='Current authority lacks the discovered UK affiliation'));continue
        description=e.get('descriptions',{}).get('en',{}).get('value','')
        cultural=bool(re.search(r'\b(?:British|English|Scottish|Welsh|Northern Irish)\b',description,re.I))
        if not cultural and not (set(affiliations)&{'Q145','Q21','Q22','Q25','Q26'}):
            held.append(dict(row,reason='Historical polity alone does not establish a UK cultural affiliation',source_description=description,country_authorities=affiliations));continue
        birth=life(e,'P569');death=life(e,'P570');b=birth['first'] if birth else None;d=death['first'] if death else None
        matches=dict(byid[('wikidata',q)]);proof=[]
        for prop,scheme in [('P6002','wikiart-artist'),('P2174','moma-person'),('P2252','nga-constituent'),('P2741','tate-person')]:
            for value in values(e,prop):
                if not isinstance(value,str):continue
                ident=value.rsplit('-',1)[-1] if prop=='P2741' else value
                if byid[(scheme,ident)]:matches.update(byid[(scheme,ident)]);proof.append({'property':prop,'scheme':scheme,'id':ident})
        basis='explicit_authority_id'
        if not matches:
            named={a:p for name in names(e) for key in name_keys(name) for a,p in bykey[key].items()}
            matches={a:p for a,p in named.items() if compatible_name_identity(p,e,b,d)}
            if named and len(matches)!=1:held.append(dict(row,reason='Existing name/date identity requires reconciliation',candidate_ids=list(named)));continue
            basis='exact_name_and_compatible_source_dates'
        if len(matches)>1:held.append(dict(row,reason='Multiple existing authority matches',candidate_ids=list(matches)));continue
        if matches:
            existing=next(iter(matches.values()));artist=existing['record'];other={v['external_id'] for v in existing['identifiers'] if v['scheme']=='wikidata'}-{q}
            if other:held.append(dict(row,reason='Existing name match has another Wikidata authority',other_qids=sorted(other),candidate_ids=[artist['id']]));continue
            if artist['entity_type']!='person':held.append(dict(row,reason='Existing authority is not a person'));continue
            action='existing'
        else:
            if any(v is not None and v>2026 for v in (b,d)) or (b is not None and d is not None and (b>d or d-b>125)):held.append(dict(row,reason='Source life dates need review'));continue
            activity=source_activity(e) if b is None and d is None else None
            if b is None and d is None and not activity:held.append(dict(row,reason='No supported source life or activity years'));continue
            first=b if b is not None else d;last=d if d is not None else b
            display=(birth['display'] if birth else '?')+'–'+(death['display'] if death else '?')
            artist={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artist/'+q)),'slug':'wikimedia-painter-'+q.lower(),'display_name':label(e),'sort_name':label(e),'normalized_name':m.norm(label(e)),'entity_type':'person','birth_year':b,'death_year':d,'birth_display':birth['display'] if birth else None,'death_display':death['display'] if death else None,'birth_precision':birth['precision'] if birth else None,'death_precision':death['precision'] if death else None,'timeline_start_year':first,'timeline_end_year':last,'timeline_display':display,'timeline_basis':'life','status':'review','created_by':ACTOR,'updated_by':ACTOR}
            if activity:artist.update(activity)
            action='new';basis='new_source_authority_with_no_existing_identity_or_name_collision'
        if artist['id'] in claimed:held.append(dict(row,reason='Another source authority already resolves to the same artist',other_qid=claimed[artist['id']]));continue
        claimed[artist['id']]=q
        selected.append(dict(row,artist=artist,action=action,country_relationships=['cultural_affiliation' if cultural or 'Q145' not in affiliations else 'citizenship'],country_authorities=affiliations,identity_basis=basis,native_identity_proof=proof,source_description=description,source_dates={'birth':birth,'death':death}))
    save(RUN/'authority-plan.json',{'selected':selected,'held':held,'roster_count':len(qids)})
    print('Authority plan',dict(collections.Counter(v['action'] for v in selected)),'held',len(held),flush=True)


def wikiart_match():
    directory=json.loads((RUN/'wikiart-uk-directory.json').read_bytes())['artists']
    baseline=json.loads((RUN/'artist-baseline.json').read_bytes())['artists'];byid={v['record']['id']:v for v in baseline};byname=collections.defaultdict(dict)
    known={}
    for row in baseline:
        for ident in row['identifiers']:
            if ident['scheme']=='wikiart-artist':known['https://www.wikiart.org/en/'+ident['external_id']]=row['record']['id']
        for name in [row['record']['display_name']]+row['aliases']:
            for key in name_keys(name):byname[key][row['record']['id']]=row
    for filename in ('artist-matches.json','extra-artist-matches.json','supplemental-artist-matches.json'):
        data=json.loads((PRIOR/filename).read_bytes())
        for pair in data['matches']:
            if pair['artist']['id'] in byid:known.setdefault(pair['wikiart']['url'],pair['artist']['id'])
    matches=[];held=[]
    for src in directory:
        profile=c.profile_one(src)
        candidate=byid.get(known.get(src['url']))
        if not candidate:
            options={aid:v for key in name_keys(src['name']) for aid,v in byname[key].items()}
            options={aid:v for aid,v in options.items() if all(src.get(k) is None or v['record'][k] is None or src[k]==v['record'][k] for k in ('birth_year','death_year'))}
            if len(options)==1:candidate=next(iter(options.values()))
        if not candidate:held.append({'source':src,'reason':'Artist identity needs reconciliation'});continue
        if candidate['record']['entity_type']!='person':held.append({'source':src,'reason':'Directory group or nonperson profile'});continue
        matches.append({'artist':dict(candidate['record'],selection_limit=8),'wikiart':src,'identity_basis':'Existing WikiArt source identity or exact name with compatible dates'})
    save(RUN/'wikiart-artist-matches.json',{'matches':matches,'held':held,'directory_profiles':len(directory)})
    print('WikiArt existing matches',len(matches),'unresolved',len(held),flush=True)


def wikiart_directory_finish():
    import difflib
    national=json.loads((RUN/'wikiart-uk-directory.json').read_bytes())['artists']
    initial=json.loads((RUN/'wikiart-artist-matches.json').read_bytes())['matches']
    initial_map={v['wikiart']['url']:v['artist']['id'] for v in initial}
    source_ids=collections.defaultdict(set)
    for path in (RUN/'entities').glob('*.json'):
        entity=json.loads(path.read_bytes())['entity']
        for value in values(entity,'P6002'):
            if isinstance(value,str):source_ids[value].add(entity['id'])
    with m.read_only() as db:
        rows=db.execute("""SELECT to_jsonb(a) record,
            coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
            coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases
            FROM artists a WHERE a.status<>'archived'""").fetchall()
    byid={v['record']['id']:v for v in rows};byname=collections.defaultdict(dict);bykey=collections.defaultdict(dict)
    for row in rows:
        for name in [row['record']['display_name']]+row['aliases']:
            for key in name_keys(name):byname[key][row['record']['id']]=row
        for ident in row['identifiers']:bykey[(ident['scheme'],ident['external_id'])][row['record']['id']]=row
    resolution_path=RUN/'directory-identity-resolutions.json'
    resolutions=json.loads(resolution_path.read_bytes()) if resolution_path.exists() else {}
    matched=[];held=[]
    for src in national:
        slug=src['url'].rsplit('/',1)[-1];profile=json.loads((RUN/'profiles'/(slug+'.json')).read_bytes())
        if re.search(r'\b(architecture|pottery|mosaics|icons|ancient|school|workshop|collective|anonymous|unknown|viking art)\b',src['name'],re.I):
            held.append({'source':src,'reason':'Directory group is not a named painter'});continue
        candidates=dict(bykey[('wikiart-artist',slug)])
        if src['url'] in initial_map:candidates[initial_map[src['url']]]=byid[initial_map[src['url']]]
        for q in source_ids[slug]:candidates.update(bykey[('wikidata',q)])
        if src['url'] in resolutions:candidates={resolutions[src['url']]['artist_id']:byid[resolutions[src['url']]['artist_id']]}
        dates=c.source_life(src)
        if not candidates:
            named={aid:row for key in name_keys(src['name']) for aid,row in byname[key].items()}
            candidates={aid:row for aid,row in named.items() if not dates or all(dates[k] is None or row['record'][k] is None or dates[k]==row['record'][k] for k in ('birth_year','death_year'))}
            if named and len(candidates)!=1:held.append({'source':src,'reason':'Name or source life dates require identity reconciliation','candidate_ids':list(named)});continue
        if len(candidates)>1:held.append({'source':src,'reason':'Multiple source identity matches','candidate_ids':list(candidates)});continue
        if candidates:
            artist=next(iter(candidates.values()))['record']
            if artist['entity_type']!='person':held.append({'source':src,'reason':'Existing authority is not a person'});continue
            created=False
        else:
            if not dates or dates['birth_year']>2026 or (dates['death_year'] and (dates['death_year']>2026 or not 0<=dates['death_year']-dates['birth_year']<=125)):
                held.append({'source':src,'reason':'No supported personal life dates'});continue
            norm=m.norm(src['name']);last=norm.split()[-1]
            near=[r['record']['id'] for r in rows if m.norm(r['record']['display_name']).split()[-1:]==[last] and (any(dates[k] is not None and dates[k]==r['record'][k] for k in ('birth_year','death_year')) or difflib.SequenceMatcher(None,norm,m.norm(r['record']['display_name'])).ratio()>=.88)]
            if near:held.append({'source':src,'reason':'Possible existing artist identity','candidate_ids':near});continue
            artist=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,src['url'])),slug='wikiart-artist-'+slug,display_name=src['name'],sort_name=src['name'],normalized_name=norm,entity_type='person',status='review',timeline_start_year=dates['birth_year'],timeline_end_year=dates['death_year'] or dates['birth_year'],timeline_display=src['life_display'],timeline_basis='life',created_by=ACTOR,updated_by=ACTOR,**dates);created=True
        matched.append({'artist':artist,'wikiart':src,'created':created,'profile_receipt':profile['receipt'],'qid_candidates':sorted(source_ids[slug])})
    plan_path=RUN/('wikiart-directory-resolved-plan.json' if resolutions else 'wikiart-directory-final-plan.json')
    if plan_path.exists():
        prior=json.loads(plan_path.read_bytes());matched=prior['matched'];held=prior['held']
    else:save(plan_path,{'matched':matched,'held':held})
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            for item in matched:
                src=item['wikiart'];artist=item['artist'];slug=src['url'].rsplit('/',1)[-1];path=RUN/'directory-final-applied'/target/(slug+'.json')
                if path.exists():continue
                with db.transaction():
                    old=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s FOR UPDATE',(artist['id'],)).fetchone()
                    if not old:
                        qids=sorted(source_ids[slug]|{v['external_id'] for v in byid.get(artist['id'],{}).get('identifiers',[]) if v['scheme']=='wikidata'})
                        alternatives=db.execute("SELECT DISTINCT to_jsonb(a) record FROM artists a WHERE a.slug=%s OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND ((e.scheme='wikidata' AND e.external_id=ANY(%s)) OR (e.scheme='wikiart-artist' AND e.external_id=%s)))",(artist['slug'],qids,slug)).fetchall()
                        assert len(alternatives)<=1,('Directory target identity is ambiguous',src['name'],target)
                        if alternatives:old=alternatives[0];artist=old['record']
                    if not old:assert item['created'],'Existing directory authority absent in target'
                    if old:assert old['record']['status']!='archived' and old['record']['entity_type']=='person'
                    identities=db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND scheme='wikiart-artist' AND external_id=%s",(slug,)).fetchall()
                    assert all(v['record']['entity_id']==artist['id'] for v in identities),'Conflicting WikiArt identity'
                    countries=db.execute('SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=%s',(artist['id'],)).fetchall()
                    backup=m.BACKUP/'directory-final'/target/(slug+'.json');save(backup,{'artist':old,'countries':countries,'identifiers':identities,'planned':item})
                    if not old:w.base.insert(db,'artists',artist)
                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'wikiart-artist',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(artist['id'],slug,src['url'],sid,item['profile_receipt']['checked_at']))
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'GB','cultural_affiliation',false,%s) ON CONFLICT DO NOTHING",(artist['id'],'WikiArt British nationality directory affiliation retained as source grouping, preserving all other affiliations.'))
                    w.base.insert(db,'citations',dict(entity_type='artist',entity_id=artist['id'],source_id=sid,field_name='wikiart_uk_directory_identity',source_url=src['url'],evidence_note=json.dumps(item),retrieved_at=item['profile_receipt']['checked_at'],created_by=ACTOR))
                    after=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(artist['id'],)).fetchone()['record']
                    if old:assert after==old['record']
                save(path,{'artist_id':artist['id'],'source_url':src['url'],'created':not bool(old),'after':after,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes())})
        print('UK directory reconciled',target,len(matched),'held',len(held),flush=True)
    supplement=RUN/'wikiart-supplement';pairs=[]
    for item in matched:
        if item['wikiart']['url'] in initial_map:continue
        artist=dict(item['artist'],selection_limit=8);pairs.append({'artist':artist,'wikiart':item['wikiart']})
        slug=item['wikiart']['url'].rsplit('/',1)[-1];save(supplement/'profiles'/(slug+'.json'),(RUN/'profiles'/(slug+'.json')).read_bytes())
    match_path=supplement/'wikiart-artist-matches.json'
    result={'matches':pairs,'held':held,'directory_profiles':len(national)}
    if match_path.exists() and json.loads(match_path.read_bytes())!=result:
        archive=supplement/'selection-versions'/('artist-matches-'+m.core.sha(match_path.read_bytes())[:16]+'.json');save(archive,match_path.read_bytes());match_path.unlink()
    save(match_path,result)
    print('Supplemental WikiArt painter profiles',len(pairs),flush=True)


def supplement(phase):
    global RUN
    RUN=RUN/'wikiart-supplement';c.RUN=m.RUN=w.RUN=RUN
    m.BACKUP=m.BACKUP/'wikiart-supplement';m.ORIGINALS=m.ORIGINALS/'wikiart-supplement'
    globals()[phase]()


def directory_identity_supplement():
    mapping={'william-williams':'Q3569029','john-russell':'Q6255995','george-harvey':'Q1507528','henry-moore-ra':'Q466588','frances-macdonald-macnair':'Q458827','winston-churchill':'Q43198','tim-scott':'Q820821','kit-williams':'Q6417490'}
    entities(sorted(set(mapping.values())))
    directory={v['url'].rsplit('/',1)[-1]:v for v in json.loads((RUN/'wikiart-uk-directory.json').read_bytes())['artists']}
    path=RUN/'authority-directory-supplement.json'
    if not path.exists():
        selected=[]
        with m.read_only() as db:
            for slug,q in mapping.items():
                src=directory[slug];capture=json.loads((RUN/'entities'/(q+'.json')).read_bytes());e=capture['entity'];dates=c.source_life(src)
                assert slug in values(e,'P6002') and any(v.get('id')=='Q5' for v in values(e,'P31')) and dates
                for prop,key in [('P569','birth_year'),('P570','death_year')]:
                    y=year(e,prop)
                    assert y is None or dates[key] is None or y==dates[key],('Source date conflict',slug)
                proof=[]
                for prop,scheme in [('P2174','moma-person'),('P2252','nga-constituent'),('P2741','tate-person')]:
                    for v in values(e,prop):
                        if isinstance(v,str):proof.append({'property':prop,'scheme':scheme,'id':v.rsplit('-',1)[-1] if prop=='P2741' else v})
                identities=[{'scheme':'wikidata','id':q},{'scheme':'wikiart-artist','id':slug}]+proof
                candidates=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) x(scheme text,id text))
                    SELECT DISTINCT to_jsonb(a) record FROM input i JOIN external_identifiers e ON e.entity_type='artist' AND e.scheme=i.scheme AND e.external_id=i.id JOIN artists a ON a.id=e.entity_id WHERE a.status<>'archived'""",(m.Jsonb(identities),)).fetchall()
                assert len(candidates)<=1,('Conflicting native identities',slug)
                if candidates:artist=candidates[0]['record'];action='existing'
                else:
                    artist=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artist/'+q)),slug='wikimedia-painter-'+q.lower(),display_name=label(e),sort_name=label(e),normalized_name=m.norm(label(e)),entity_type='person',status='review',timeline_start_year=dates['birth_year'],timeline_end_year=dates['death_year'] or dates['birth_year'],timeline_display=src['life_display'],timeline_basis='life',created_by=ACTOR,updated_by=ACTOR,**dates);action='new'
                selected.append(dict(qid=q,name=label(e),capture=str(RUN/'entities'/(q+'.json')),artist=artist,action=action,country_relationships=['cultural_affiliation'],country_authorities=sorted({v.get('id') for v in values(e,'P27')} & set(COUNTRIES)),identity_basis='Exact Wikidata P6002 WikiArt profile plus consistent directory life dates; differing homonym identities preserved.',native_identity_proof=proof,source_description=e.get('descriptions',{}).get('en',{}).get('value',''),source_dates={'wikiart':dates,'wikidata_birth':life(e,'P569'),'wikidata_death':life(e,'P570')},directory_source=src))
        save(path,{'selected':selected,'held':[],'basis':'Explicit source identifier crosslinks distinguish historical namesakes and reconcile titled variants. Existing profiles and dates are preserved.'})
    authority_apply(path.name)
    resolutions={}
    for slug,q in mapping.items():
        receipt=json.loads((RUN/'authorities-applied/local'/(q+'.json')).read_bytes())
        resolutions[directory[slug]['url']]={'artist_id':receipt['artist_id'],'qid':q,'evidence':str(path),'reason':'Exact source profile identity and supplied life dates'}
    with m.read_only() as db:
        row=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikiart-artist' AND external_id='jacob-epstein'").fetchone();assert row
    resolutions[directory['jacob-epstein']['url']]={'artist_id':row['entity_id'],'qid':'Q354779','reason':'Existing explicit WikiArt identity retained. The separate NGA/Wikidata catalogue identity remains a documented duplicate-review case; neither profile nor its artworks are removed.'}
    save(RUN/'directory-identity-resolutions.json',resolutions)
    wikiart_directory_finish()


def wikiart_select():
    data=json.loads((RUN/'wikiart-artist-matches.json').read_bytes());excluded=set()
    for folder in ('wikiart-selected-images-20260919','wikiart-artist-coverage-20260920','wikiart-artist-followup-20260920','armenian-painters-20260920','women-wikiart-20260920','uk-painters-20260920'):
        for path in (ROOT/'docs/research'/folder/'images').glob('*.json'):excluded.add(json.loads(path.read_bytes())['source_id'])
    with m.read_only() as db:
        for pair in data['matches']:c.select_one(pair,db,excluded)
    matches=m.discovered_matches();save(RUN/'discovered-v2.json',{'matches':matches,'artist_count':len(data['matches']),'at':m.core.now()})
    print('WikiArt selected',len(matches),'works',flush=True)


def wikiart_prepare():
    c.configure_preparation();m.prepare()


def authority_apply(plan_filename='authority-plan.json'):
    plan=json.loads((RUN/plan_filename).read_bytes())
    def target_apply(target,dsn):
        pending=[v for v in plan['selected'] if not (RUN/'authorities-applied'/target/(v['qid']+'.json')).exists()]
        counts=collections.Counter()
        if not pending:return target,dict(counts)
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            inventory=db.execute("""SELECT to_jsonb(a) record,
                coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
                coalesce((SELECT jsonb_agg(to_jsonb(ac)) FROM artist_countries ac WHERE ac.artist_id=a.id),'[]') countries
                FROM artists a""").fetchall()
            byid={v['record']['id']:v for v in inventory};byslug={v['record']['slug']:v for v in inventory};bykey=collections.defaultdict(dict)
            for row in inventory:
                for ident in row['identifiers']:bykey[(ident['scheme'],ident['external_id'])][row['record']['id']]=row
            prepared=[]
            for item in pending:
                q=item['qid'];artist=item['artist'];matches={}
                if artist['id'] in byid:matches[artist['id']]=byid[artist['id']]
                if artist['slug'] in byslug:
                    row=byslug[artist['slug']];matches[row['record']['id']]=row
                matches.update(bykey[('wikidata',q)])
                for proof in item['native_identity_proof']:matches.update(bykey[(proof['scheme'],proof['id'])])
                reason=None
                if len(matches)>1:reason='Multiple target artist authorities'
                old=next(iter(matches.values())) if len(matches)==1 else None
                if old and (old['record']['status']=='archived' or old['record']['entity_type']!='person'):reason='Target is archived or not a person'
                if old and {v['external_id'] for v in old['identifiers'] if v['scheme']=='wikidata'}-{q}:reason='Target has another Wikidata identity'
                if not old and item['action']=='existing':reason='Existing local identity requires explicit production reconciliation'
                if reason:
                    save(RUN/'authority-target-held'/target/(q+'.json'),{'qid':q,'reason':reason,'matches':matches,'planned':item});counts['held']+=1;continue
                capture=json.loads(Path(item['capture']).read_bytes())
                prepared.append({'item':item,'capture':capture,'before':old,'artist_id':old['record']['id'] if old else artist['id']})
            for start in range(0,len(prepared),80):
                chunk=prepared[start:start+80];ids=[v['artist_id'] for v in chunk]
                assert len(ids)==len(set(ids))
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL statement_timeout='60s'")
                    current=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) FOR UPDATE',(ids,)).fetchall();current={v['record']['id']:v['record'] for v in current}
                    assert all(current.get(v['artist_id'])==(v['before']['record'] if v['before'] else None) for v in chunk),'Target artist changed after planning'
                    key=m.core.sha(m.core.encode([v['item']['qid'] for v in chunk]))[:20]
                    backup=m.BACKUP/'authorities'/target/(key+'.json');save(backup,{'kind':'bounded_artist_batch','selected':chunk,'at_plan':'Source receipts carry exact retrieval time; target preimages taken before this transaction.'})
                    with db.pipeline():
                        for entry in chunk:
                            item=entry['item'];q=item['qid'];aid=entry['artist_id'];capture=entry['capture'];e=capture['entity']
                            if not entry['before']:w.base.insert(db,'artists',item['artist'])
                            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'wikidata',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(aid,q,'https://www.wikidata.org/wiki/'+q,sid,capture['receipt']['retrieved_at']))
                            for lang,value in e.get('labels',{}).items():
                                db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(aid,value['value'],m.norm(value['value']),lang))
                            note='Source description: '+item['source_description']+'. Explicit source country statements: '+', '.join(COUNTRIES[q] for q in item['country_authorities'])+'. Historic polity alone does not establish modern cultural affiliation; other country relationships preserved.'
                            db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'GB',%s,false,%s) ON CONFLICT DO NOTHING",(aid,item['country_relationships'][0],note))
                            cid=str(uuid.uuid5(uuid.NAMESPACE_URL,SOURCE+'/authority/'+q))
                            w.base.insert(db,'citations',dict(id=cid,entity_type='artist',entity_id=aid,source_id=sid,field_name='uk_identity_and_affiliation',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note=json.dumps({'source_receipt':capture['receipt'],'source_country_claims':claims(e,'P27'),'identity_basis':item['identity_basis'],'native_identity_proof':item['native_identity_proof'],'source_dates':item['source_dates'],'directory_source':item.get('directory_source'),'date_policy':'Existing biography preserved, including source conflicts. New source circa precision and unknown fields retained. Cultural grouping does not replace other national affiliations.'}),retrieved_at=capture['receipt']['retrieved_at'],created_by=ACTOR))
                    after=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall();by_after={v['record']['id']:v['record'] for v in after}
                    assert len(by_after)==len(chunk)
                    identity_rows=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s)",([v['item']['qid'] for v in chunk],)).fetchall();identities={v['external_id']:v['entity_id'] for v in identity_rows}
                    assert all(identities.get(v['item']['qid'])==v['artist_id'] for v in chunk)
                    assert all(not v['before'] or by_after[v['artist_id']]==v['before']['record'] for v in chunk)
                digest=m.core.sha(backup.read_bytes())
                for entry in chunk:
                    q=entry['item']['qid'];aid=entry['artist_id'];created=entry['before'] is None
                    save(RUN/'authorities-applied'/target/(q+'.json'),{'qid':q,'artist_id':aid,'created':created,'after':by_after[aid],'backup':str(backup),'backup_sha256':digest,'at':m.core.now()})
                    counts['created' if created else 'existing']+=1
                print('Artist delivery',target,dict(counts),flush=True)
        return target,dict(counts)
    dsns={'local':'postgres://localhost/artline','cloud':m.core.cloud_dsn()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(target_apply,target,dsn) for target,dsn in dsns.items()]
        for f in futures:print('Artist delivery complete',f.result(),flush=True)


def sparql_post(query):
    # Official endpoint supports POST. Keep one sequential query at a time,
    # response bounds, immutable receipts and the service's Retry-After.
    endpoint='https://query-main.wikidata.org/sparql'
    for attempt in range(4):
        time.sleep(1.2)
        try:response=w.SESSION.post(endpoint,data={'query':query,'format':'json'},timeout=(15,65))
        except m.requests.RequestException:
            if attempt==3:raise
            time.sleep(5*(attempt+1));continue
        if response.status_code==429:
            delay=int(response.headers.get('Retry-After','60'));print('Source query pause',delay,'seconds',flush=True);time.sleep(delay);continue
        if response.status_code in (502,503,504):time.sleep(5*(attempt+1));continue
        response.raise_for_status();assert len(response.content)<20_000_000
        receipt={'url':endpoint,'method':'POST','query_sha256':m.core.sha(query.encode()),'retrieved_at':m.core.now(),'sha256':m.core.sha(response.content),'bytes':len(response.content)}
        return response.json(),receipt
    raise RuntimeError('Source query unavailable after respectful bounded retries')


def artwork_discover():
    roster=json.loads((RUN/'roster-discovery.json').read_bytes());qids=sorted({v['artist']['value'].rsplit('/',1)[-1] for v in roster['rows']})
    groups=collections.defaultdict(dict);total=0
    cached=[json.loads(p.read_bytes()) for p in sorted((RUN/'work-discovery').glob('*.json'))]
    covered={q for data in cached for q in data['artist_qids']}
    remaining=[q for q in qids if q not in covered]
    for start in range(0,len(remaining),400):
        part=remaining[start:start+400]
        query='SELECT DISTINCT ?work ?artist ?collection ?date ?image WHERE { hint:Query hint:optimizer "None" . VALUES ?artist { '+' '.join('wd:'+q for q in part)+' } ?work wdt:P170 ?artist; wdt:P195 ?collection . OPTIONAL { ?work wdt:P571 ?date } OPTIONAL { ?work wdt:P18 ?image } }'
        response,receipt=captured('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
        data={'artist_qids':part,'rows':response['results']['bindings'],'query':query,'receipt':receipt}
        save(RUN/'work-discovery'/('batch-'+m.core.sha(m.core.encode(part))[:16]+'.json'),data);cached.append(data);covered.update(part)
        print('Museum source census',len(covered),'of',len(qids),'source rows',sum(len(v['rows']) for v in cached),flush=True)
    assert covered==set(qids)
    with m.read_only() as db:
        for data in cached:
            rows=data['rows'];total+=len(rows)
            known=db.execute("SELECT e.external_id,a.id::text,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s)",(list({v['work']['value'].rsplit('/',1)[-1] for v in rows}),)).fetchall();known={v['external_id']:v for v in known}
            for row in rows:
                q=row['work']['value'].rsplit('/',1)[-1];aq=row['artist']['value'].rsplit('/',1)[-1]
                yr=int(row['date']['value'][:4]) if re.match(r'\d{4}-',row.get('date',{}).get('value','')) else None
                if yr is not None and yr>1955:continue
                if q in known and known[q]['primary_media_id']:continue
                groups[aq][q]={'qid':q,'artist_qid':aq,'year':yr,'image':row.get('image'),'existing':known.get(q)}
    selected=[]
    for aq,items in groups.items():
        selected.extend(sorted(items.values(),key=lambda v:(v['year'] is None,not bool(v['image']),bool(v['existing']),v['qid']))[:4])
    save(RUN/'work-candidate-selection.json',{'selected':selected,'source_rows':total,'artist_groups':len(groups),'artists_surveyed':len(qids),'policy':'Up to four further museum-source records per painter, dated through 1955 and source-linked images first. Unknown dates retained for metadata review only. Already illustrated source objects skipped.'})
    entities(sorted({v['qid'] for v in selected}))
    print('Museum candidates',len(selected),'for',len(groups),'artists',flush=True)


def image_duplicate_audit():
    from PIL import Image,ImageOps,ImageDraw
    images=[json.loads(p.read_bytes()) for p in (RUN/'images').glob('*.json')];ids=[im['work']['artist']['id'] for im in images]
    with m.read_only() as db:
        rows=db.execute("""SELECT aa.artist_id::text,a.id::text,a.title,a.creation_year_start,a.creation_year_end,ma.storage_path,ma.checksum_sha256
            FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN media_assets ma ON ma.id=a.primary_media_id
            WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'""",(list(set(ids)),)).fetchall()
    def fingerprint(path):
        im=Image.open(ROOT/'apps/web/public'/path.lstrip('/')).convert('L').resize((17,16));pixels=list(im.getdata());number=0
        for y in range(16):
            for x in range(16):number=(number<<1)|int(pixels[y*17+x]>pixels[y*17+x+1])
        return number
    byartist=collections.defaultdict(list)
    for row in rows:
        try:row=dict(row,fingerprint=fingerprint(row['storage_path']))
        except (FileNotFoundError,OSError):continue
        byartist[row['artist_id']].append(row)
    near=[]
    for im in images:
        h=fingerprint(im['path'])
        for row in byartist[im['work']['artist']['id']]:
            if row['id']==im['artwork_id']:continue
            distance=(h^row['fingerprint']).bit_count()
            if distance<=10 or row['checksum_sha256']==im['sha256']:
                entry={'selected':{k:im[k] for k in ('artwork_id','artist','title','source_year','path','sha256','page')},'existing':{k:v for k,v in row.items() if k!='fingerprint'},'distance':distance};near.append(entry)
                save(RUN/'image-identity-held'/(im['artwork_id']+'.json'),entry)
    report={'images_reviewed':len(images),'existing_images':len(rows),'near_matches':near,'method':'256-bit horizontal difference hash, distance at most 10; candidate detection only. Held object identities preserve public alternate images.'}
    save(RUN/'image-duplicate-audit.json',report)
    for start in range(0,len(near),8):
        part=near[start:start+8];canvas=Image.new('RGB',(800,275*len(part)),'white');draw=ImageDraw.Draw(canvas)
        for n,match in enumerate(part):
            for col,row in enumerate([match['selected'],match['existing']]):
                im=Image.open(ROOT/'apps/web/public'/row.get('path',row.get('storage_path')).lstrip('/')).convert('RGB');thumb=ImageOps.contain(im,(390,230));canvas.paste(thumb,(400*col+(400-thumb.width)//2,275*n));draw.text((400*col+5,275*n+235),str(start+n+1)+' '+row['title'][:45],fill='black')
        canvas.save('/tmp/artline-uk-image-review-'+str(start//8)+'.jpg',quality=90)
    print('Image identity candidates',len(near),'across',len(images),'prepared files',flush=True)


def wikiart_deliver():
    original=c.target_before
    def guarded(db,im):
        path=RUN/'image-identity-held'/(im['artwork_id']+'.json')
        if path.exists():return {'outcome':'held','reason':'Possible duplicate image; public alternate retained pending object identity reconciliation'}
        return original(db,im)
    c.target_before=guarded;c.deliver_ready();c.sync_selection();c.verify()


def correct_directory_categories():
    def replace(path,value,kind):
        old=path.read_bytes();save(RUN/'category-corrections/previous'/kind/path.name,old)
        path.unlink();save(path,value)
    images=[(p,json.loads(p.read_bytes())) for p in (RUN/'images').glob('*.json')]
    images=[(p,im) for p,im in images if im['artist']=='Viking art']
    assert len(images)==8 and all(im['work']['new_record'] for _,im in images)
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            for path,im in images:
                marker=RUN/'category-corrections'/target/path.name
                if marker.exists():continue
                aid=im['artwork_id'];delivery=json.loads((RUN/'delivery'/path.name).read_bytes());expected=delivery['targets'][target]['after']
                with db.transaction():
                    actual=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['record'];assert actual==expected
                    links=db.execute('SELECT to_jsonb(aa) record FROM artwork_artists aa WHERE artwork_id=%s',(aid,)).fetchall()
                    assert len(links)==1 and links[0]['record']['artist_id']==im['work']['artist']['id'] and links[0]['record']['attribution_role']=='primary'
                    backup=m.BACKUP/'category-corrections'/target/path.name;save(backup,{'artwork':actual,'creator_links':links,'delivery':delivery,'source_image_evidence':im})
                    db.execute('DELETE FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role=%s',(aid,im['work']['artist']['id'],'primary'))
                    db.execute("UPDATE artworks SET unlinked_creator_label=NULL,cultural_context='Viking art',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(ACTOR,aid))
                    w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='source_category_context_corrected',source_url=im['page'],evidence_note='The WikiArt nationality directory entry Viking art is a broad cultural category, not a named person. Removed only this newly introduced creator link; retained the source category as cultural context. Creator remains unknown. Artwork, date, image, source attribution, personal selection and review state are preserved. The older artist profile and its other records were not changed.',retrieved_at=m.core.now(),created_by=ACTOR))
                    after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(aid,)).fetchone()['record']
                save(marker,{'artwork_id':aid,'after':after,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now()})
    for path,im in images:
        im['work']['artist']['object_level_creator']=True;im['work']['unlinked_creator_label']=None;im['work']['cultural_context']='Viking art'
        if json.loads(path.read_bytes())!=im:replace(path,im,'images')
        delivery_path=RUN/'delivery'/path.name;delivery=json.loads(delivery_path.read_bytes())
        for target in ('local','cloud'):
            correction=json.loads((RUN/'category-corrections'/target/path.name).read_bytes())
            delivery['targets'][target]['after']=correction['after'];delivery['targets'][target]['category_correction']=str(RUN/'category-corrections'/target/path.name)
        if json.loads(delivery_path.read_bytes())!=delivery:replace(delivery_path,delivery,'delivery')
    c.verify()



def artwork_select(allow_unknown_types=False, only_qids=None, output_name='catalogue.json',candidate_path=None):
    candidates = list({v['qid']:v for v in json.loads((candidate_path or RUN / 'work-candidate-selection.json').read_bytes())['selected']}.values())
    if only_qids is not None:
        candidates=[v for v in candidates if v['qid'] in only_qids]
    selected, held = [], []
    with m.read_only() as db:
        artist_rows = db.execute("SELECT e.external_id,to_jsonb(a) record FROM external_identifiers e JOIN artists a ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s) AND a.status<>'archived'", (list({v['artist_qid'] for v in candidates}),)).fetchall()
        artist_byqid = {v['external_id']:v['record'] for v in artist_rows}
        cached_works = {}
        for item in candidates:
            q,aq = item['qid'],item['artist_qid']
            capture = json.loads((RUN/'entities'/(q+'.json')).read_bytes())
            e = capture['entity']
            creator_capture = json.loads((RUN/'entities'/(aq+'.json')).read_bytes())
            creator = creator_capture['entity']
            cs = claims(e,'P170')
            types = {v.get('id') for v in values(e,'P31') if isinstance(v,dict)}
            date = w.date(e)
            date['eligible'] = bool(date['first'] is not None and date['last'] <= 1955)
            reason = None
            if e.get('id') != q or label(e) == q:
                reason = 'Missing independent artwork identity or title'
            elif types.intersection({'Q5','Q4167410','Q4167836'}):
                reason = 'Source entity is a person, disambiguation or category rather than an artwork'
            elif len(cs) != 1 or cs[0].get('qualifiers') or cs[0]['mainsnak']['datavalue']['value'].get('id') != aq:
                reason = 'Qualified or multiple creators remain unresolved'
            elif not allow_unknown_types and not types.intersection({'Q3305213','Q93184','Q1278452','Q22669139','Q132137','Q429785'}):
                reason = 'Artwork type needs separate mapping'
            elif date['first'] is not None and not date['eligible']:
                reason = 'Source creation date exceeds 1955'
            elif not claims(e,'P195'):
                reason = 'No retained collection source statement'
            artist = artist_byqid.get(aq)
            if reason:
                held.append(dict(item,reason=reason,title=label(e)));continue
            existing = db.execute("SELECT to_jsonb(a) record FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s", (q,)).fetchall()
            if len(existing)>1:
                held.append(dict(item,reason='Multiple existing authority matches'));continue
            if not existing and artist:
                if aq not in cached_works:
                    cached_works[aq] = c.artist_works(db,artist['id'])
                titles = {m.norm(n) for n in names(e)}
                possible = [v for v in cached_works[aq] if {m.norm(v['title']),m.norm(v.get('alternate_title'))} & titles]
                source_accessions={v for v in values(e,'P217') if isinstance(v,str)}
                compatible = [v for v in possible if date['eligible'] and v['creation_year_start'] is not None and v['creation_year_end'] is not None and date['first']<=v['creation_year_end'] and date['last']>=v['creation_year_start'] and len(v['creators'])==1 and v['creators'][0]['role']=='primary'
                    and (not source_accessions or not v['accession_number'] or v['accession_number'] in source_accessions)]
                if possible and len(compatible)!=1:
                    held.append(dict(item,reason='Existing title requires object identity review',artwork_ids=[v['artwork_id'] for v in possible]));continue
                if compatible:
                    existing = [{'record':compatible[0]['before_record']}]
            existing = existing[0]['record'] if existing else None
            if existing and (existing['status']=='archived' or existing['primary_media_id']):
                held.append(dict(item,reason='Existing record or primary image preserved',artwork_id=existing['id']));continue
            images = [v for v in values(e,'P18') if isinstance(v,str)]
            accession = [v for v in values(e,'P217') if isinstance(v,str)]
            collection_ids = sorted({v.get('id') for v in values(e,'P195') if isinstance(v,dict) and v.get('id')})
            record = {'qid':q,'title':label(e),'titles':names(e),'date':date,'entity':e,'entity_receipt':capture['receipt'],
                'creator_qid':aq,'creator_label':label(creator),'creator_entity':creator,'creator_receipt':creator_capture['receipt'],
                'artist':artist,'collection':{'qid':','.join(collection_ids),'institution':{'slug':'source-collection-unvalidated'}},
                'collection_qids':collection_ids,'accession':accession[0] if len(accession)==1 else None,'images':images,
                'existing_local':existing,'selection_note':'Owner-selected UK painter research. Collection statements retained as supplied source metadata; no accepted holding or current display asserted.',
                'work_type':'painting' if 'Q3305213' in types else ('fresco' if 'Q22669139' in types else 'unknown')}
            selected.append(record)
    assert len({v['qid'] for v in selected})==len(selected)
    save(RUN/'selected-museum'/output_name,{'selected':selected,'held':held})
    save(RUN/'selected-museum'/(Path(output_name).stem+'-index.json'),{'selected':[{'qid':v['qid'],'creator_qid':v['creator_qid'],'eligible_image_date':v['date']['eligible'],'has_source_image':bool(v['images'])} for v in selected],'held':held})
    print('Museum artwork selection',len(selected),'records, existing',sum(bool(v['existing_local']) for v in selected),'eligible dated',sum(v['date']['eligible'] for v in selected),'with images',sum(bool(v['images']) and v['date']['eligible'] for v in selected),'held',len(held),flush=True)

def museum_target_chunk(db,items):
    records=[v['record'] for v in items];artist_qids=list({v['creator_qid'] for v in records})
    artists=db.execute("SELECT e.external_id,to_jsonb(a) record FROM external_identifiers e JOIN artists a ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s) AND a.status<>'archived'",(artist_qids,)).fetchall();amap={v['external_id']:v['record'] for v in artists}
    existing=db.execute("SELECT e.external_id,to_jsonb(a) record FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s)",([v['qid'] for v in records],)).fetchall();qmap={v['external_id']:v['record'] for v in existing}
    assert len(qmap)==len(existing)
    artist_ids=[v['id'] for v in amap.values()]
    peers=db.execute("SELECT aa.artist_id::text,to_jsonb(a) record FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'",(artist_ids,)).fetchall()
    byartist=collections.defaultdict(list)
    for row in peers:byartist[row['artist_id']].append(row['record'])
    existing_ids=[v['id'] for v in qmap.values()]
    links=db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(existing_ids,)).fetchall();bywork=collections.defaultdict(list)
    for row in links:bywork[row['artwork_id']].append(row)
    planned=[];held=[]
    for item in items:
        rec=item['record'];q=rec['qid'];artist=amap.get(rec['creator_qid']);old=qmap.get(q);reason=None
        if old:
            if old['status']=='archived':reason='Existing source object is archived'
            elif bywork[old['id']] and (not artist or [(v['artist_id'],v['attribution_role']) for v in bywork[old['id']]]!=[(artist['id'],'primary')]):reason='Existing creator identity differs'
            elif not bywork[old['id']] and old['unlinked_creator_label'] and m.norm(old['unlinked_creator_label']) not in {m.norm(v) for v in names(rec['creator_entity'])}:reason='Existing named creator requires reconciliation'
            elif rec['accession'] and old['accession_number'] and rec['accession']!=old['accession_number']:reason='Source accession conflicts with existing object'
        else:
            peers=[v for v in byartist[artist['id']] if {m.norm(v['title']),m.norm(v.get('alternate_title'))}&{m.norm(v) for v in rec['titles']}] if artist else []
            if rec.get('existing_local'):reason='Provisional title match needs exact source-object identity'
            elif peers and any(not rec['accession'] or not v['accession_number'] or rec['accession']==v['accession_number'] for v in peers):reason='Existing title requires object identity review'
        if reason:held.append({'qid':q,'reason':reason,'existing':old,'peer_ids':[v['id'] for v in peers] if not old and artist else []});continue
        aid=old['id'] if old else str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artwork/'+q))
        image=item['image'] if rec['date']['eligible'] and (not old or (not old['primary_media_id'] and old['creation_year_start'] is not None and old['creation_year_end'] is not None and old['creation_year_end']<=1955)) else None
        mid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/image/'+q+'/'+image['sha256'])) if image else None
        planned.append({'item':item,'artwork_id':aid,'artist':artist,'before':old,'creator_links_before':bywork[aid],'image':image,'media_id':mid})
        if artist and not old:byartist[artist['id']].append({'id':aid,'title':rec['title'],'alternate_title':None,'accession_number':rec['accession']})
    return planned,held


def museum_write_chunk(db,chunk,sid,collection_id):
    # All dependent identity/backup checks finish before independent inserts
    # are pipelined. The caller holds the collection row lock for positions.
    with db.pipeline():
        for entry in chunk:
            rec=entry['item']['record'];q=rec['qid'];aid=entry['artwork_id'];artist=entry['artist'];old=entry['before'];im=entry['image'];mid=entry['media_id']
            if im:
                w.base.insert(db,'media_assets',dict(id=mid,storage_kind='local',storage_path=im['path'],source_page_url=im['source_page_url'],provider_name='Wikimedia Commons',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=rec['title']+' — '+rec['creator_label'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['download']['retrieved_at'],verified_at=im['checked_at'],verified_by=ACTOR))
                w.base.insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=im['commons_page']['title'],source_checksum=im['commons_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis='Source-linked Commons file with per-file rights, identity and credit evidence retained.',adapter_version='uk-selected-20260920',checked_at=im['checked_at'],evidence_json=m.Jsonb(im)))
            if not old:
                d=rec['date']
                w.base.insert(db,'artworks',dict(id=aid,slug='wikimedia-artwork-'+q.lower(),title=rec['title'],normalized_title=m.norm(rec['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=rec['work_type'],accession_number=rec['accession'],primary_media_id=mid,status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR,unlinked_creator_label=None if artist else rec['creator_label']))
            elif mid:db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(mid,ACTOR,aid))
            if artist and not entry['creator_links_before']:
                w.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist['id'],attribution_role='primary',attribution_note='Unqualified source creator identity retained in review; supplied object-level labels preserved.'))
            if mid:w.base.insert(db,'artwork_media',dict(artwork_id=aid,media_id=mid,sort_order=0,view_label='Selected reproduction'))
            if not old:
                w.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=q,canonical_url='https://www.wikidata.org/wiki/'+q,source_id=sid,retrieved_at=rec['entity_receipt']['retrieved_at']))
            w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='uk_selected_source_metadata',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note=json.dumps({'entity_receipt':rec['entity_receipt'],'creator_qid':rec['creator_qid'],'collection_qids':rec['collection_qids'],'collection_statements':claims(rec['entity'],'P195'),'selection':rec['selection_note'],'holding_status':'Source collection statements retained; no accepted holding or current display claim created.'}),retrieved_at=rec['entity_receipt']['retrieved_at'],created_by=ACTOR))
    members=[{'artwork_id':v['artwork_id'],'source_url':'https://www.wikidata.org/wiki/'+v['item']['record']['qid'],'checked_at':v['item']['record']['entity_receipt']['retrieved_at'],'reason':v['item']['record']['selection_note']} for v in chunk]
    db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) x(artwork_id uuid,source_url text,checked_at timestamptz,reason text)), positions AS(SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s)
        INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
        SELECT %s,i.artwork_id,p.n+row_number() OVER(ORDER BY i.artwork_id)::int,i.reason,%s,i.source_url,i.checked_at FROM input i CROSS JOIN positions p ON CONFLICT(collection_id,artwork_id) DO NOTHING""",(m.Jsonb(members),collection_id,collection_id,sid))
    db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))


def museum_apply(incremental=False,upload_only=False):
    import base64,hashlib
    selected_qids={v['qid'] for v in json.loads((RUN/'selected-museum/catalogue-index.json').read_bytes())['selected']}
    all_inputs=sorted((RUN/'museum-images/ready').glob('*.json'))
    inputs=[p for p in all_inputs if p.stem in selected_qids]
    if not incremental:assert len(inputs)==len(selected_qids)
    bucket=m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    def upload(path):
        if (RUN/'museum-uploads'/path.name).exists():return
        item=json.loads(path.read_bytes())
        im=item['image'];q=item['record']['qid'];receipt=RUN/'museum-uploads'/(q+'.json')
        if not im or receipt.exists():return
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert len(raw)==im['bytes'] and len(raw)<=100000 and m.core.sha(raw)==im['sha256']
        blob=bucket.blob(im['path'].lstrip('/'));blob.cache_control='public,max-age=31536000,immutable';blob.metadata={'sha256':im['sha256'],'wikidata':q}
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except m.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        save(receipt,{'qid':q,'path':im['path'],'sha256':im['sha256'],'bytes':len(raw),'generation':blob.generation})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(upload,all_inputs))
    if upload_only:return
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    def apply_target(target,dsn):
        pending=[p for p in inputs if not (RUN/'museum-applied'/target/p.name).exists() and not (RUN/'museum-held'/target/p.name).exists()];counts=collections.Counter()
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            for start in range(0,len(pending),60):
                items=[json.loads(p.read_bytes()) for p in pending[start:start+60]]
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='15s'");db.execute("SET LOCAL statement_timeout='90s'")
                    collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                    chunk,held=museum_target_chunk(db,items)
                    for hold in held:save(RUN/'museum-held'/target/(hold['qid']+'.json'),hold);counts['held']+=1
                    if not chunk:continue
                    ids=[v['artwork_id'] for v in chunk];assert len(ids)==len(set(ids))
                    actual=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) FOR UPDATE',(ids,)).fetchall();actual={v['record']['id']:v['record'] for v in actual}
                    assert all(actual.get(v['artwork_id'])==v['before'] for v in chunk),'Artwork changed after object identity resolution'
                    mids=[v['media_id'] for v in chunk if v['media_id']]
                    assert not db.execute('SELECT id FROM media_assets WHERE id=ANY(%s::uuid[])',(mids,)).fetchall(),'Existing media identity requires reconciliation'
                    links=db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
                    key=m.core.sha(m.core.encode([v['item']['record']['qid'] for v in chunk]))[:20]
                    backup=m.BACKUP/'museum-artworks'/target/(key+'.json');save(backup,{'kind':'bounded_museum_artwork_batch','selected':chunk,'collection':collection,'collection_items':links})
                    museum_write_chunk(db,chunk,sid,collection_id)
                    after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall();after={v['record']['id']:v['record'] for v in after}
                    assert len(after)==len(chunk)
                    for entry in chunk:
                        old=entry['before'];new=after[entry['artwork_id']]
                        if old:assert all(new[k]==v for k,v in old.items() if k not in ('primary_media_id','revision','updated_at','updated_by'))
                        else:assert new['status']=='review' and new['current_institution_id'] is None and new['research_candidate']
                    qids=[v['item']['record']['qid'] for v in chunk]
                    identities=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(qids,)).fetchall();identities={v['external_id']:v['entity_id'] for v in identities}
                    assert all(identities.get(v['item']['record']['qid'])==v['artwork_id'] for v in chunk)
                digest=m.core.sha(backup.read_bytes())
                for entry in chunk:
                    q=entry['item']['record']['qid'];aid=entry['artwork_id'];created=entry['before'] is None
                    save(RUN/'museum-applied'/target/(q+'.json'),{'qid':q,'artwork_id':aid,'artist_id':entry['artist']['id'] if entry['artist'] else None,'created':created,'image_attached':bool(entry['media_id']),'media_id':entry['media_id'],'after':after[aid],'backup':str(backup),'backup_sha256':digest,'at':m.core.now()})
                    counts['created' if created else 'existing']+=1;counts['images']+=bool(entry['media_id'])
                print('Museum delivery',target,dict(counts),flush=True)
        return target,dict(counts)
    dsns={'local':'postgres://localhost/artline','cloud':m.core.cloud_dsn()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(apply_target,target,dsn) for target,dsn in dsns.items()]
        for f in futures:print('Museum delivery complete',f.result(),flush=True)


def museum_stream():
    selected={v['qid'] for v in json.loads((RUN/'selected-museum/catalogue-index.json').read_bytes())['selected']}
    while True:
        copied=0
        for path in sorted((RUN/'museum-images/shards').glob('*/[0-5]/ready/*.json')):
            destination=RUN/'museum-images/ready'/path.name
            if not destination.exists():save(destination,path.read_bytes());copied+=1
        ready={p.stem for p in (RUN/'museum-images/ready').glob('*.json')}
        print('Available museum records',len(ready&selected),'of',len(selected),'newly ready',copied,flush=True)
        if copied or selected<=ready:museum_apply(incremental=True)
        if selected<=ready:
            save(RUN/'museum-delivery-finished.json',{'at':m.core.now(),'selected':len(selected),'ready_files':len(ready)})
            print('Museum streaming delivery finished',flush=True);return
        time.sleep(30)


def museum_select():
    artwork_select(True)


def museum_prepare_child(shard,catalogue='catalogue.json',batch='final'):
    s=importlib.util.spec_from_file_location('imageprep',ROOT/'ops/prepare-wikimedia-catalogue-images.py');prep=importlib.util.module_from_spec(s);s.loader.exec_module(prep)
    s=importlib.util.spec_from_file_location('uk_downloads',ROOT/'ops/uk-source-downloads-20260920.py');downloads=importlib.util.module_from_spec(s);s.loader.exec_module(downloads);downloads.install(w)
    w.RUN=RUN/'museum-images/shards'/batch/str(shard);w.BACKUPS=m.BACKUP/'museum-images'/batch/str(shard);prep.r=w
    records=json.loads((w.RUN/'selected/records.json').read_bytes())['selected']
    for record in records:
        if not record['date']['eligible'] or not record['images']:
            save(w.RUN/'ready'/(record['qid']+'.json'),{'record':record,'image':None,'image_outcome':'metadata_retained','image_reason':'Unknown creation date or no source-linked image'})
    original=w.date
    def date(e):
        result=original(e);result['eligible']=result['first'] is not None and result['last']<=1955;return result
    # At the requested 100 KB display budget, Commons' supplied 1280px version
    # is adequate for large originals. The download receipt identifies it as
    # a source thumbnail and retains the original's Commons SHA-1 separately.
    w.date=date;prep.main(original_byte_limit=1_000_000,original_pixel_limit=4_000_000)


def museum_prepare(catalogue='catalogue.json',batch='final'):
    import subprocess,sys
    shard_count=3 if batch.startswith('prefetch-') else 6
    if not all((RUN/'museum-images/shards'/batch/str(shard)/'selected/records.json').exists() for shard in range(shard_count)):
        assigned=set()
        if batch=='final':
            for path in (RUN/'museum-images/shards').glob('prefetch-*/[0-2]/selected/records.json'):
                assigned.update(v['qid'] for v in json.loads(path.read_bytes())['selected'])
        records=[v for v in json.loads((RUN/'selected-museum'/catalogue).read_bytes())['selected'] if v['qid'] not in assigned and not (RUN/'museum-images/ready'/(v['qid']+'.json')).exists()]
        for shard in range(shard_count):save(RUN/'museum-images/shards'/batch/str(shard)/'selected/records.json',{'selected':records[shard::shard_count]})
        print('Prepared bounded image worklists',len(records),'records across',shard_count,'workers',flush=True)
        del records
    def worker(shard):
        log=Path('/tmp/artline-uk-museum-prepare-'+batch+'-'+str(shard)+'.log')
        with log.open('a') as stream:
            result=subprocess.run([sys.executable,'-B','-u',str(Path(__file__)),'museum_prepare_child','--shard',str(shard),'--catalogue',catalogue,'--batch',batch],stdout=stream,stderr=subprocess.STDOUT)
        assert result.returncode==0,('Image preparation shard failed',shard,str(log))
        return shard
    with concurrent.futures.ThreadPoolExecutor(max_workers=shard_count) as pool:
        for shard in pool.map(worker,range(shard_count)):print('Museum preparation completed shard',shard,flush=True)
    outcomes=collections.Counter()
    for shard in range(shard_count):
        for path in (RUN/'museum-images/shards'/batch/str(shard)/'ready').glob('*.json'):
            data=json.loads(path.read_bytes());save(RUN/'museum-images/ready'/path.name,data);outcomes['image' if data['image'] else 'metadata']+=1
    print('Museum preparation complete',dict(outcomes),flush=True)


def museum_prefetch():
    paths=sorted((RUN/'work-discovery').glob('*.json'));groups=collections.defaultdict(dict)
    key=m.core.sha(m.core.encode([p.name for p in paths]))[:12];candidate_path=RUN/'prefetch'/('candidates-'+key+'.json')
    if not candidate_path.exists():
        with m.read_only() as db:
            for path in paths:
                data=json.loads(path.read_bytes());rows=data['rows']
                known=db.execute("SELECT e.external_id,a.id::text,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s)",(list({v['work']['value'].rsplit('/',1)[-1] for v in rows}),)).fetchall();known={v['external_id']:v for v in known}
                for row in rows:
                    q=row['work']['value'].rsplit('/',1)[-1];aq=row['artist']['value'].rsplit('/',1)[-1]
                    yr=int(row['date']['value'][:4]) if re.match(r'\d{4}-',row.get('date',{}).get('value','')) else None
                    if yr is not None and yr>1955:continue
                    if q in known and known[q]['primary_media_id']:continue
                    groups[aq][q]={'qid':q,'artist_qid':aq,'year':yr,'image':row.get('image'),'existing':known.get(q)}
        selected={}
        for aq,items in sorted(groups.items()):
            for item in sorted(items.values(),key=lambda v:(v['year'] is None,not bool(v['image']),bool(v['existing']),v['qid']))[:4]:selected.setdefault(item['qid'],item)
        save(candidate_path,{'selected':list(selected.values()),'source_chunks':[p.name for p in paths]})
    candidates=json.loads(candidate_path.read_bytes())['selected'];print('Prefetch selected metadata',len(candidates),'from completed source batches',flush=True)
    entities(sorted({v['qid'] for v in candidates}))
    catalogue='prefetch-'+key+'.json'
    if not (RUN/'selected-museum'/catalogue).exists():artwork_select(True,output_name=catalogue,candidate_path=candidate_path)
    museum_prepare(catalogue,'prefetch-'+key)


def commons_prefetch(batch_filter=None):
    # A batched response still retains complete file-specific rights, revision,
    # identity and photographer metadata. The ordinary image preparer consumes
    # each member with its normal checks. Derived receipts explicitly identify
    # the preserved parent HTTP response; they are never labelled raw captures.
    s=importlib.util.spec_from_file_location('uk_downloads',ROOT/'ops/uk-source-downloads-20260920.py');downloads=importlib.util.module_from_spec(s);s.loader.exec_module(downloads);downloads.install(w)
    folders=[]
    for path in sorted((RUN/'museum-images/shards').glob('*/[0-5]/selected/records.json')):
        folder=path.parent.parent
        if batch_filter and folder.parent.name!=batch_filter:continue
        pending=[r for r in json.loads(path.read_bytes())['selected'] if r['date']['eligible'] and r['images'] and not (folder/'ready'/(r['qid']+'.json')).exists()]
        folders.append((folder,pending))
    while any(pending for _,pending in folders):
        for folder,pending in folders:
            if not pending:continue
            part=pending[:20];del pending[:20];w.RUN=folder
            urls={}
            for rec in part:
                filename=rec['images'][0]
                if (folder/'ready'/(rec['qid']+'.json')).exists():continue
                url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'File:'+filename,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5})
                if not (folder/'captures'/(m.core.sha(url.encode())+'.json')).exists():urls['File:'+filename]=url
            if not urls:continue
            batch_url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'|'.join(urls),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5})
            data,receipt=w.fetch(batch_url)
            normalized={v['from']:v['to'] for v in data.get('query',{}).get('normalized',[])}
            pages={v['title']:(key,v) for key,v in data.get('query',{}).get('pages',{}).items()}
            for title,url in urls.items():
                normalized_title=normalized.get(title,title)
                if normalized_title not in pages:continue
                page_id,page=pages[normalized_title]
                # A content-bearing revision is mandatory for this shortcut;
                # normal individual retrieval remains available otherwise.
                if not page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*'):continue
                raw=m.core.encode({'query':{'pages':{page_id:page}}});key=m.core.sha(url.encode());path=folder/'captures'/(key+'.json')
                with w.evidence_lock(url):
                    if path.exists():continue
                    derived=dict(receipt,bytes=len(raw),sha256=m.core.sha(raw),capture_kind='selected_page_from_batch',requested_page=title,parent_receipt=receipt,parent_capture=str(folder/'captures'/(m.core.sha(batch_url.encode())+'.json')))
                    save(path,raw);save(path.with_suffix('.receipt.json'),derived)
            print('Commons selected-file metadata batch',folder.name,len(urls),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['discover','discover_capture','roster_probe','wikiart_directory','wikiart_directory_finish','directory_identity_supplement','capture_authorities','capture_selected','authority_plan','authority_apply','artwork_discover','museum_prefetch','commons_prefetch','museum_select','museum_prepare','museum_prepare_child','museum_apply','museum_stream','wikiart_match','wikiart_select','wikiart_prepare','image_duplicate_audit','wikiart_deliver','correct_directory_categories'])
    p.add_argument('--shard',type=int,choices=range(6));p.add_argument('--supplement',action='store_true');p.add_argument('--catalogue',default='catalogue.json');p.add_argument('--batch',default='final');args=p.parse_args()
    if args.phase=='museum_prepare_child':museum_prepare_child(args.shard,args.catalogue,args.batch)
    elif args.phase=='museum_prepare':museum_prepare(args.catalogue,args.batch)
    elif args.phase=='commons_prefetch':commons_prefetch(args.batch)
    elif args.supplement:supplement(args.phase)
    else:globals()[args.phase]()
