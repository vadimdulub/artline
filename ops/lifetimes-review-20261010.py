#!/usr/bin/env python3
"""Full-catalogue life, timeline and artwork chronology audit. Local DB is read-only."""
import argparse,collections,concurrent.futures,gzip,hashlib,importlib.util,json,re,threading,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('cesi-top100-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OP='lifetimes-review-20261010';ROOT=m.ROOT;RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
UA='ArtlineChronologyReview/1.0 (https://artlines.org/about; evidence-based catalogue review)'
save,load,sha,now,chunks=m.save,m.load,m.sha,m.now,m.chunks
def snapshot(target):
    assert target in ['local','production'];dest=RUN/(target+'-snapshot.json.gz')
    if dest.exists():print('Pinned snapshot exists:',target);return
    with m.connect(local=target=='local') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists=[dict(record=r['v'],identifiers=[],citations=[],aliases=[]) for r in db.execute('SELECT to_jsonb(a) v FROM artists a ORDER BY id')]
        by={r['record']['id']:r for r in artists};ids=list(by);works=[]
        for batch in chunks(ids,500):
            for r in db.execute("SELECT entity_id::text,to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme",(batch,)):by[r['entity_id']]['identifiers'].append(r['v'])
            for r in db.execute("SELECT entity_id::text,to_jsonb(c) v FROM citations c WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(batch,)):by[r['entity_id']]['citations'].append(r['v'])
            for r in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,alias',(batch,)):by[r['artist_id']]['aliases'].append(r['alias'])
            works+=db.execute("""SELECT aa.artist_id::text,aa.attribution_role,aa.attribution_note,
                a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,
                a.work_type,a.medium_text,a.status,a.current_institution_id::text,a.primary_media_id::text,a.revision
                FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
                WHERE aa.artist_id=ANY(%s::uuid[]) ORDER BY aa.artist_id,a.id""",(batch,)).fetchall()
        plans=db.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id,a.creation_year_start,a.creation_year_end FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s",('c90a7468-e048-4a36-b497-bfe638973be0',)).fetchall()
        counts={table:db.execute('SELECT count(*) n FROM '+table).fetchone()['n'] for table in ['artists','artworks','artwork_artists','media_assets']}
    data=dict(at=now(),target=target,read_only=True,artists=artists,artwork_links=works,counts=counts,uccello_query_plan=plans)
    save(dest,data);print(target,'artists',len(artists),'artwork links',len(works),flush=True)
def qids(a):return sorted({e['external_id'] for e in a['identifiers'] if e['scheme']=='wikidata' and re.fullmatch(r'Q[1-9]\d*',e['external_id'])})
def identity_bindings():
    result=collections.defaultdict(list)
    for folder in ['painter-influences-20261008','painter-influences-round4-20261009','painter-influences-round4-20261009/catalogue-catchup']:
        for name in ['research-identity-bindings.json','supplemental-identity-bindings.json']:
            p=ROOT/'docs/research'/folder/name
            if not p.exists():continue
            digest=sha(p.read_bytes())
            for r in load(p):
                if r.get('decision')=='supported_research_identity':result[r['artist_id']].append(dict(qid=r['qid'],basis=r['basis'],path=str(p.relative_to(ROOT)),sha256=digest,evidence=r))
    save(RUN/'research-identity-bindings.json.gz',dict(result));print('Retained prior identity evidence:',len(result),flush=True)
def effective_qids(a,bindings):return sorted(set(qids(a))|{r['qid'] for r in bindings.get(a['record']['id'],[])})
def fresh_dates():
    bindings=load(RUN/'research-identity-bindings.json.gz');roster=[]
    for target in ['production','local']:roster+=load(RUN/(target+'-snapshot.json.gz'))['artists']
    ids=sorted({q for a in roster if a['record']['status']!='archived' for q in effective_qids(a,bindings)})
    stop=threading.Event();hold=RUN/'wikidata-access-hold.json'
    if hold.exists():stop.set()
    def one(batch):
        key=sha('|'.join(batch).encode());path=RUN/'fresh-date-statements'/(key+'.json.gz')
        if path.exists():return dict(key=key,qids=batch,state='captured',rows=len(load(path)['data']['results']['bindings']))
        if stop.is_set():return dict(key=key,qids=batch,state='access_held')
        query='''SELECT ?artist ?property ?claim ?rank ?value ?precision ?calendar ?before ?after ?qualifierProperty ?qualifierValue ?reference WHERE {
          VALUES ?artist { '''+' '.join('wd:'+q for q in batch)+''' }
          VALUES (?property ?p ?psv) {(wd:P569 p:P569 psv:P569) (wd:P570 p:P570 psv:P570) (wd:P2031 p:P2031 psv:P2031) (wd:P2032 p:P2032 psv:P2032)}
          ?artist ?p ?claim . ?claim wikibase:rank ?rank .
          OPTIONAL {?claim ?psv ?node . ?node wikibase:timeValue ?value; wikibase:timePrecision ?precision; wikibase:timeCalendarModel ?calendar . OPTIONAL {?node wikibase:timeBefore ?before} OPTIONAL {?node wikibase:timeAfter ?after}}
          OPTIONAL {?claim ?qualifierProperty ?qualifierValue . FILTER(STRSTARTS(STR(?qualifierProperty),"http://www.wikidata.org/prop/qualifier/"))}
          OPTIONAL {?claim prov:wasDerivedFrom ?reference}
        }'''
        try:
            r=requests.get('https://query.wikidata.org/sparql',params={'query':query,'format':'json'},headers={'User-Agent':UA},timeout=(15,50))
            receipt=dict(at=now(),url=r.url,status=r.status_code,sha256=sha(r.content),qids=batch,query=query)
            if r.status_code in [401,403,429]:
                stop.set()
                if not hold.exists():save(hold,receipt)
            r.raise_for_status();data=r.json();assert 'results' in data
            save(path,dict(**receipt,data=data));time.sleep(.15)
            return dict(key=key,qids=batch,state='captured',rows=len(data['results']['bindings']))
        except Exception as e:
            result=dict(key=key,qids=batch,state='failed',error=type(e).__name__+': '+str(e).split('?')[0]);save(RUN/'fresh-date-errors'/(key+'.json'),result);return result
    results=[];batches=list(chunks(ids,100))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(one,batches):
            results.append(result)
            if len(results)%10==0:print('Current life/activity statements',len(results),'/',len(batches),dict(collections.Counter(r['state'] for r in results)),flush=True)
    save(RUN/'fresh-date-coverage.json',dict(at=now(),qids=len(ids),batches=results));print('Current date coverage',len(ids),dict(collections.Counter(r['state'] for r in results)),flush=True)
def cached_authorities():
    result=collections.defaultdict(lambda:dict(birth=set(),death=set(),labels=set(),receipts=[]))
    folders=['painter-influences-20261008','painter-influences-round4-20261009','painter-influences-round4-20261009/catalogue-catchup']
    for folder in folders:
        for p in sorted((ROOT/'docs/research'/folder/'wikidata-authorities').glob('*.json.gz')):
            data=load(p);seen=set()
            for row in data['data']['results']['bindings']:
                q=row['artist']['value'].rsplit('/',1)[-1];d=result[q]
                for key in ['birth','death']:
                    value=row.get(key,{}).get('value')
                    if value:d[key].add(value)
                if row.get('artistLabel'):d['labels'].add(row['artistLabel']['value'])
                if q not in seen:d['receipts'].append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),at=data['at']));seen.add(q)
    out={q:{k:sorted(v) if isinstance(v,set) else v for k,v in r.items()} for q,r in result.items()}
    save(RUN/'cached-authority-index.json.gz',out);print('Cached authorities:',len(out),flush=True)
def year(value):
    match=re.match(r'^([+-]?\d+)-',value or '')
    return int(match[1]) if match else None
def artist_flags(a,source):
    r=a['record'];b,d=r['birth_year'],r['death_year'];flags=[]
    if r['entity_type']!='person':
        if b is not None or d is not None:flags.append('nonperson_life_fields_need_review')
        return flags
    if b is None:flags.append('birth_unknown')
    if d is None:flags.append('death_unknown_or_living')
    if b is not None and d is not None:
        if d-b<15:flags.append('implausibly_short_artist_life')
        if d-b>125:flags.append('implausibly_long_life')
    if r['timeline_basis']=='life' and (b is None or d is None):flags.append('life_timeline_missing_endpoint')
    if r['timeline_basis']=='life' and b is not None and d is not None and (r['timeline_start_year'],r['timeline_end_year'])!=(b,d):flags.append('life_timeline_disagrees_with_life_fields')
    for key,endpoint in [('active_start_year','birth_year'),('active_end_year','death_year')]:
        if r[key] is not None and r[endpoint] is not None and ((key=='active_start_year' and r[key]<r[endpoint]) or (key=='active_end_year' and r[key]>r[endpoint])):flags.append('activity_outside_recorded_life')
    qs=qids(a)
    if len(qs)>1:flags.append('multiple_artist_authorities')
    if len(qs)==1 and qs[0] in source:
        s=source[qs[0]]
        for field,key in [('birth_year','birth'),('death_year','death')]:
            years={year(v) for v in s[key]};years.discard(None)
            if len(years)>1:flags.append('authority_'+key+'_alternatives')
            if r[field] is not None and years and r[field] not in years:flags.append('authority_'+key+'_disagrees')
            if r[field] is None and years:flags.append('authority_'+key+'_available')
    else:flags.append('no_single_cached_authority')
    bio=r.get('biography_md') or ''
    for match in re.finditer(r'\((?:c(?:irca)?\.?\s*)?(\d{3,4})\s*[-–]\s*(\d{3,4})\)',bio[:450]):
        if (b is not None and b!=int(match[1])) or (d is not None and d!=int(match[2])):flags.append('biography_life_disagrees');break
    return sorted(set(flags))
def artwork_flags(w,a):
    if w['status']=='archived' or a['status']=='archived':return []
    lo,hi=w['creation_year_start'],w['creation_year_end'];b,d=a['birth_year'],a['death_year'];flags=[]
    if lo is None or hi is None:return ['creation_date_unassessable']
    if a['entity_type']!='person':return ['nonperson_use_activity_not_lifespan']
    if b is None and d is None:return ['creator_life_unassessable']
    qualified=w['attribution_role']!='primary'
    if b is not None and hi<b:flags.append('entirely_before_recorded_birth')
    if d is not None and lo>d:flags.append('entirely_after_recorded_death')
    if b is not None and b<=hi<b+5:flags.append('creation_before_age_five')
    if b is not None and d is not None and b==lo and d==hi and d-b>20:flags.append('creation_range_equals_artist_life')
    if not flags and ((b is not None and lo<b<=hi) or (d is not None and lo<=d<hi)):flags.append('broad_date_overlaps_life_boundary')
    if flags and qualified:flags.append('qualified_attribution_preserve_distinction')
    if 'entirely_after_recorded_death' in flags and (w['work_type'] in ['print','sculpture','photograph'] or re.search(r'cast|print|edition|bronze|etching|engraving|lithograph',w.get('medium_text') or '',re.I)):flags.append('posthumous_physical_production_possible')
    return flags
def audit(target):
    data=load(RUN/(target+'-snapshot.json.gz'));source=load(RUN/'cached-authority-index.json.gz');by={r['record']['id']:r for r in data['artists']};register=[];works=[];wc=collections.defaultdict(collections.Counter)
    for w in data['artwork_links']:
        flags=artwork_flags(w,by[w['artist_id']]['record'])
        if flags:works.append(dict(**w,flags=flags));wc[w['artist_id']].update(flags)
    for a in data['artists']:
        r=a['record'];register.append(dict(artist_id=r['id'],name=r['display_name'],slug=r['slug'],status=r['status'],entity_type=r['entity_type'],qids=qids(a),birth_year=r['birth_year'],death_year=r['death_year'],timeline_basis=r['timeline_basis'],timeline_start=r['timeline_start_year'],timeline_end=r['timeline_end_year'],flags=artist_flags(a,source) if r['status']!='archived' else ['archived_excluded'],artwork_flags=dict(wc[r['id']])))
    save(RUN/(target+'-initial-review.json.gz'),dict(at=now(),artists=register,artwork_flags=works))
    summary=dict(at=now(),target=target,artists=len(register),active=sum(r['status']!='archived' for r in register),artist_flags=dict(collections.Counter(f for r in register for f in r['flags'])),artwork_flags=dict(collections.Counter(f for r in works for f in r['flags'])))
    save(RUN/(target+'-initial-summary.json'),summary);print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['snapshot','cached_authorities','identity_bindings','fresh_dates','audit']);p.add_argument('target',nargs='?',choices=['local','production']);a=p.parse_args()
    globals()[a.command](a.target) if a.target else globals()[a.command]()
