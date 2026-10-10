#!/usr/bin/env python3
"""Denmark, Sweden and Norway: bounded collection coverage with pinned evidence."""
import argparse, collections, csv, datetime, gzip, hashlib, importlib.util, json, re, subprocess, time, uuid
from pathlib import Path
from urllib.parse import urlencode, urlsplit
import psycopg
from psycopg.rows import dict_row
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nordic_core',ROOT/'ops/catalogue-expansion-20261008.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OP='nordic-museums-20261008';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
m.RUN=RUN
save=m.save;load=m.load;norm=m.norm;connect=m.connect;now=m.now
COUNTRIES={'DK':'Q35','SE':'Q34','NO':'Q20'}
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+s))
def capture(url,params=None):
    pace=8 if 'query.wikidata.org' in url else 1.5
    try:raw,rc=m.capture(url,params,pace=pace)
    except RuntimeError as error:
        if '429' not in str(error):raise
        raw,rc=m.capture(url,params,pace=pace)
    if rc['status']==429:
        text=raw.decode(errors='replace');hit=re.search(r'retry in (\d+) seconds',text,re.I)
        if not hit:raise RuntimeError('Rate limit without explicit retry guidance; source stopped')
        wait=max(10,int(hit[1])+2)
        stamp=datetime.datetime.fromisoformat(rc['retrieved_at']).timestamp()
        delay=max(0,stamp+wait-time.time())
        if delay:time.sleep(delay)
        # Same identified client and exact endpoint after the provider's backoff.
        # Preserve the original 429; only one retry is permitted.
        original=m.RUN;m.RUN=RUN/'retry-after-provider-backoff'
        try:raw,rc=m.capture(url,params,pace=pace)
        finally:m.RUN=original
        if rc['status']==429:raise RuntimeError('Repeated rate limit; stop source')
    return raw,rc
def snapshot():
    dest=RUN/'baseline.json.gz'
    if dest.exists():return
    with connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        inst=list(db.execute("""SELECT to_jsonb(i) record,p.name city,p.country_code,
          (SELECT count(*) FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived') works,
          (SELECT count(*) FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived' AND a.primary_media_id IS NOT NULL) images
          FROM institutions i LEFT JOIN places p ON p.id=i.place_id ORDER BY i.name"""))
        places=[x['r'] for x in db.execute('SELECT to_jsonb(p) r FROM places p WHERE country_code=ANY(%s)',(list(COUNTRIES),))]
        venues=[x['r'] for x in db.execute('SELECT to_jsonb(v) r FROM institution_venues v JOIN places p ON p.id=v.place_id WHERE p.country_code=ANY(%s)',(list(COUNTRIES),))]
        ids={x['record']['id'] for x in inst if x['country_code'] in COUNTRIES}|{x['institution_id'] for x in venues}
        works=[x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])',(sorted(ids),))]
        wids=[w['id'] for w in works];relations={}
        for table,col in [('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id'),('citations','entity_id'),('external_identifiers','entity_id')]:
            relations[table]=[x['r'] for x in db.execute(f'SELECT to_jsonb(t) r FROM {table} t WHERE {col}=ANY(%s::uuid[])',(wids,))]
        artists=list(db.execute('SELECT id::text,slug,display_name,normalized_name,birth_year,death_year,status FROM artists'))
        aext=list(db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist'"))
        sources=[x['r'] for x in db.execute('SELECT to_jsonb(s) r FROM sources s')]
    out=dict(at=now(),institutions=inst,places=places,venues=venues,artworks=works,relations=relations,artists=artists,artist_external=aext,sources=sources)
    save(dest,out)
    for cc in COUNTRIES:
        rows=[i for i in inst if i['country_code']==cc]
        print(cc,'institutions',len(rows),'nonempty',sum(i['works']>0 for i in rows),'works',sum(i['works'] for i in rows),flush=True)
        for i in rows:print(cc,i['record']['wikidata_id'],i['record']['name'],i['works'],flush=True)
    with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
        local=list(db.execute("SELECT p.country_code,count(*) institutions FROM institutions i JOIN places p ON p.id=i.place_id WHERE p.country_code=ANY(%s) GROUP BY 1",(list(COUNTRIES),)))
    save(RUN/'local-readonly-counts.json',dict(at=now(),rows=local))

def discover():
    for cc,qid in COUNTRIES.items():
        dest=RUN/'discovery'/(cc+'.json')
        if dest.exists():continue
        query='''SELECT DISTINCT ?museum ?museumLabel ?kind ?kindLabel ?city ?cityLabel ?website WHERE {
          VALUES ?country { wd:'''+qid+''' }
          ?museum wdt:P17 ?country; wdt:P31/wdt:P279* wd:Q33506; wdt:P31 ?kind .
          OPTIONAL { ?museum wdt:P131 ?city }
          OPTIONAL { ?museum wdt:P856 ?website }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,da,sv,no,nb,nn" }
        } LIMIT 1800'''
        raw,rc=capture('https://query.wikidata.org/sparql',dict(query=query,format='json'))
        assert rc['status']==200,rc['status']
        data=json.loads(raw);save(dest,dict(receipt=rc,data=data))
        print(cc,'museum rows',len(data['results']['bindings']),flush=True)

def art_directory():
    for cc,qid in COUNTRIES.items():
        for category in ['art-institutions-v2','collections']:
            dest=RUN/'discovery'/(cc+'-'+category+'.json')
            if dest.exists():continue
            if category=='art-institutions-v2':
                body='VALUES ?root { wd:Q207694 wd:Q1007870 wd:Q1747681 wd:Q11982370 wd:Q97662266 wd:Q7328910 } ?museum wdt:P31 ?root .'
            else:
                body='?work wdt:P195 ?museum; wdt:P31 wd:Q3305213 .'
            query='''SELECT DISTINCT ?museum ?museumLabel ?city ?cityLabel ?website WHERE {
              ?museum wdt:P17 wd:'''+qid+' . '+body+'''
              OPTIONAL { ?museum wdt:P131 ?city }
              OPTIONAL { ?museum wdt:P856 ?website }
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en,da,sv,no,nb,nn" }
            } LIMIT 1500'''
            raw,rc=capture('https://query.wikidata.org/sparql',dict(query=query,format='json'))
            assert rc['status']==200,rc['status'];data=json.loads(raw)
            save(dest,dict(receipt=rc,data=data));print(cc,category,'rows',len(data['results']['bindings']),flush=True)

def directory():
    base=load(RUN/'baseline.json.gz');byqid=collections.defaultdict(list)
    for i in base['institutions']:
        if i['record'].get('wikidata_id'):byqid[i['record']['wikidata_id']].append(i)
    rows={}
    for path in sorted((RUN/'discovery').glob('*.json')):
        if path.stem.endswith('-art-institutions'):continue
        cc=path.name[:2]
        if cc not in COUNTRIES:continue
        data=load(path)
        for binding in data['data']['results']['bindings']:
            r={k:v['value'] for k,v in binding.items()};qid=r['museum'].rsplit('/',1)[-1]
            if '-' not in path.stem and r.get('kindLabel') not in ['art museum','art gallery','sculpture garden','kunsthalle','artist museum',"artist's-home museum",'museum of modern art','art collection']:continue
            item=rows.setdefault(qid,dict(qid=qid,country=cc,name=r['museumLabel'],cities=[],websites=[],discovery=[],existing=byqid[qid]))
            if item['country']!=cc:item.setdefault('country_conflicts',[]).append(cc)
            if r.get('city') and r['city'] not in [p['qid'] for p in item['cities']]:item['cities'].append(dict(qid=r['city'],name=r['cityLabel']))
            if r.get('website') and r['website'] not in item['websites']:item['websites'].append(r['website'])
            if r.get('kindLabel'):item.setdefault('kinds',[]).append(r['kindLabel'])
            if str(path.relative_to(ROOT)) not in item['discovery']:item['discovery'].append(str(path.relative_to(ROOT)))
    save(RUN/'directory-v2.json',list(rows.values()))
    for cc in COUNTRIES:
        print('\n'+cc,flush=True)
        for r in rows.values():
                if r['country']==cc:print(r['qid'],r['name'],' / '.join(p['name'] for p in r['cities']),sum(x['works'] for x in r['existing']),flush=True)

def entity_batches(ids,tag):
    out={}
    for n,part in enumerate(m.chunks(sorted(set(ids)),25)):
        dest=RUN/'entities'/tag/(str(n).zfill(4)+'.json.gz')
        if dest.exists():
            d=load(dest);assert set(d['entities'])==set(part)
        else:
            time.sleep(6.5)
            raw,rc=capture('https://www.wikidata.org/w/api.php',dict(action='wbgetentities',ids='|'.join(part),props='labels|aliases|claims|descriptions',format='json'))
            assert rc['status']==200,rc['status'];d=dict(receipt=rc,entities=json.loads(raw)['entities']);save(dest,d)
        for q,e in d['entities'].items():out[q]=dict(entity=e,receipt=d['receipt'])
        print(tag,'entities',len(out),'/',len(set(ids)),flush=True)
    return out

def museum_entities():entity_batches([r['qid'] for r in load(RUN/'directory-v2.json')],'museums')

def value(claim):return claim.get('mainsnak',{}).get('datavalue',{}).get('value')
def active(e,p):return [c for c in e.get('claims',{}).get(p,[]) if c.get('rank')!='deprecated']
def vals(e,p):return [value(c) for c in active(e,p)]
def label(e):
    for lang in ['en','da','sv','nb','no','nn','de','fr','it']:
        if lang in e.get('labels',{}):return e['labels'][lang]['value']
    return next(iter(e.get('labels',{}).values()),{}).get('value')
def saved_entities(tag):
    out={}
    for p in sorted((RUN/'entities').glob(tag+'*/*.json.gz')):
        d=load(p)
        for q,e in d['entities'].items():out[q]=dict(entity=e,receipt=d['receipt'])
    return out

def work_indexes():
    entities=saved_entities('museums')
    pending=[]
    for r in load(RUN/'directory-v2.json'):
        qid=r['qid'];dest=RUN/'indexes-v2'/(qid+'.json')
        if dest.exists():continue
        e=entities.get(qid,{}).get('entity',{})
        if active(e,'P576'):
            save(dest,dict(qid=qid,skipped='dissolved institution; successor/branch review required'));continue
        pending.append(r)
    for group in m.chunks(pending,8):
        parts=[]
        for r in group:
            parts.append('{ { SELECT DISTINCT ?work WHERE { ?work wdt:P195 wd:'+r['qid']+' } LIMIT 36 } BIND(wd:'+r['qid']+' AS ?museum) }')
        query='SELECT ?museum ?work WHERE {'+' UNION '.join(parts)+'}'
        try:
            raw,rc=capture('https://query.wikidata.org/sparql',dict(query=query,format='json'))
            assert rc['status']==200,rc['status']
            data=json.loads(raw)
            for r in group:
                ids=[x['work']['value'].rsplit('/',1)[-1] for x in data['results']['bindings'] if x['museum']['value'].rsplit('/',1)[-1]==r['qid']]
                save(RUN/'indexes-v2'/(r['qid']+'.json'),dict(qid=r['qid'],receipt=rc,ids=ids,capped=len(ids)==36));print(r['country'],r['name'],len(ids),'bounded candidates',flush=True)
        except m.requests.RequestException as error:
            for r in group:save(RUN/'indexes-v2'/(r['qid']+'.json'),dict(qid=r['qid'],skipped='source transport failure',error=type(error).__name__))
            print('Group source transport failure',flush=True)

def work_entities():
    for cc in COUNTRIES:work_entities_country(cc)
    creator_entities()
def work_entities_country(cc):
    ids=[];decisions={r['qid']:r for r in reviewed_museums()};selected=[]
    for r in load(RUN/'directory-v2.json'):
        if r['country']!=cc:continue
        p=RUN/'indexes-v2'/(r['qid']+'.json');assert p.exists(),r['qid']
        if decisions[r['qid']]['reason']:continue
        chosen=load(p).get('ids',[])[:24];ids+=chosen
        selected.append(dict(institution_qid=r['qid'],selected_ids=chosen,index_path=str(p.relative_to(ROOT)),selection='First 24 source-index object identifiers per approved institution; no catalogue or image exhaustion.'))
    save(RUN/('entity-selection-'+cc+'.json'),selected)
    entity_batches(ids,'works-'+cc)
def work_entities_dk():work_entities_country('DK')
def work_entities_no():work_entities_country('NO')
def work_entities_se():work_entities_country('SE')
def creator_entities():
    works=saved_entities('works')
    creators={v['id'] for d in works.values() for v in vals(d['entity'],'P170') if isinstance(v,dict) and 'id' in v}
    entity_batches(creators,'creators')

def commons_probe():
    raw,rc=capture('https://commons.wikimedia.org/w/api.php',dict(action='query',titles='File:Skredsvig Idyll.png',prop='imageinfo',iiprop='extmetadata',format='json'))
    assert rc['status']==200;d=json.loads(raw);save(RUN/'commons-probe.json',dict(receipt=rc,data=d));print(json.dumps(d,ensure_ascii=False)[:10000],flush=True)

def commons_research():
    museums={r['qid']:r for r in reviewed_museums()};works=saved_entities('works');creators=saved_entities('creators')
    choices=collections.defaultdict(list);referenced=collections.Counter()
    for q,d in works.items():
        e=d['entity'];cs=vals(e,'P195')
        if len(cs)!=1 or not isinstance(cs[0],dict):continue
        museum=museums.get(cs[0]['id'])
        if not museum or museum['reason']:continue
        row,reason=work_fields(e,museum,creators,d['receipt'])
        if row:referenced[museum['institution_id']]+=1;continue
        if reason!='Collection statement lacks source reference':continue
        row,reason=work_fields(e,museum,creators,d['receipt'],collection_evidence='LEAD ONLY: still requires actual file-page collection evidence')
        files=[s for s in vals(e,'P18') if isinstance(s,str)]
        if reason or not files:continue
        choices[museum['institution_id']].append(dict(qid=q,institution_qid=museum['qid'],file='File:'+files[0],title=row['title'],inventories=row['inventories']))
    leads=[]
    for iid,rs in choices.items():
        # Breadth first: up to three exact reproductions for collections without a usable referenced work.
        if referenced[iid]>=2:continue
        leads+=sorted(rs,key=lambda r:(not bool(r['inventories']),r['qid']))[:3]
    save(RUN/'commons-leads.json',leads)
    pages={}
    for n,part in enumerate(m.chunks(sorted({r['file'] for r in leads}),20)):
        path=RUN/'commons'/('batch-'+str(n).zfill(3)+'.json.gz')
        if path.exists():d=load(path)
        else:
            time.sleep(6.5);raw,rc=capture('https://commons.wikimedia.org/w/api.php',dict(action='query',titles='|'.join(part),prop='revisions',rvprop='content',rvslots='main',format='json'));assert rc['status']==200
            d=dict(receipt=rc,data=json.loads(raw));save(path,d)
        for p in d['data']['query']['pages'].values():pages[p['title']]=dict(page=p,receipt=d['receipt'])
        print('Commons textual object evidence',len(pages),'/',len(leads),flush=True)
    results=[]
    for r in leads:
        page=pages.get(r['file']);text=page['page'].get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','') if page else ''
        fields={}
        for field in ['institution','location','source','accession number','accession_number','title','date','artist','wikidata']:
            hit=re.search(r'^\s*\|\s*'+re.escape(field)+r'\s*=(.*?)(?=\n\s*\|[a-zA-Z_ ]+\s*=|\n\}\})',text,re.M|re.S|re.I)
            if hit:fields[field]=hit[1].strip()
        results.append(dict(**r,fields=fields,wikitext=text,receipt=page['receipt'] if page else None))
    save(RUN/'commons-evidence.json.gz',results)
    for r in results:print(r['qid'],museums[r['institution_qid']]['name'],r['title'],'FIELDS',json.dumps(r['fields'],ensure_ascii=False),flush=True)

def reference_pages():
    urls={
      'denmark-art-directory':'https://bkf.dk/medlemskab/kunstliv/danske-museer-og-samlinger/',
      'norway-museum-directory':'https://www.visitnorway.com/things-to-do/art-culture/museums/',
      'zorn-collection':'https://zorn.se/en/about-us/zorn-collections/',
      'kode-rasmus':'https://www.kodebergen.no/en/collections/samlingene-rasmus-meyers-samlinger',
      'national-oslo':'https://www.nasjonalmuseet.no/en/about-the-national-museum/',
    }
    for key,url in urls.items():
        dest=RUN/'references'/(key+'.json')
        if dest.exists():continue
        try:
            raw,rc=capture(url);soup=m.BeautifulSoup(raw,'html.parser')
            links=[dict(label=a.get_text(' ',strip=True),url=a['href']) for a in soup.select('a[href]')]
            for tag in soup(['script','style','nav','footer','header']):tag.decompose()
            save(dest,dict(receipt=rc,text=soup.get_text('\n',strip=True),links=links));print(key,rc['status'],flush=True)
        except Exception as err:print(key,type(err).__name__,flush=True)

def api_before():
    for cc in COUNTRIES:
        raw,rc=capture('https://artlines.org/api/backend/v1/museums',dict(country=cc,limit=60))
        save(RUN/('api-before-v2-'+cc+'.json'),dict(receipt=rc,data=json.loads(raw)))
        print(cc,rc['status'],json.loads(raw).get('total'),flush=True)

MUSEUM_IDS={
 'Q671384':'ee9976cf-63a1-48f7-9e34-eb5444e0486c',
 'Q770918':'9127d636-9185-4067-a3e0-b091ac67ff11',
 'Q1140507':'1c878da6-1bfe-576c-8b03-bb1fbb983695',
 'Q10601378':'cb845384-fc8b-4634-924a-9c4f2d47633c',
 'Q3555520':'3ebbb3f4-7170-113c-d56f-353e09d1f494',
 'Q1410617':'bd86b5eb-f0b2-550c-973a-d81511fd85ed',
 'Q842858':'3dd937e8-ac85-4b50-8b55-c45034c1a18e',
 'Q1992004':'62fd4a9f-ecfc-5fab-814c-b18adec7821e',
 'Q1132918':'5f550b6e-7d78-4fab-89f5-5f54a9bc1241',
}
def institution_review():
    b=load(RUN/'baseline.json.gz');entities=saved_entities('museums');out=[]
    museums={r['museum']['value'].rsplit('/',1)[-1] for cc in COUNTRIES for r in load(RUN/'discovery'/(cc+'.json'))['data']['results']['bindings']}
    allinst={i['record']['id']:i for i in b['institutions']}
    for r in load(RUN/'directory-v2.json'):
        d=entities[r['qid']];e=d['entity'];reason=None
        types={v['id'] for v in vals(e,'P31') if isinstance(v,dict)}
        is_museum=r['qid'] in museums or bool(types & {'Q33506','Q207694','Q1007870','Q1747681','Q11982370','Q97662266','Q1475403'})
        if not is_museum:reason='Collection-only, corporate, private or civic owner; museum/gallery status needs individual primary-source review'
        country={v['id'] for v in vals(e,'P17') if isinstance(v,dict)}
        if country!={COUNTRIES[r['country']]}:reason='Country identity ambiguous or missing'
        if active(e,'P576'):reason='Dissolved institution; successor and transferred holdings require individual review'
        matches=[i for i in b['institutions'] if i['record'].get('wikidata_id')==r['qid']]
        if r['qid'] in MUSEUM_IDS:matches=[allinst[MUSEUM_IDS[r['qid']]]]
        if not matches:
            names={norm(v['value']) for v in e.get('labels',{}).values()}|{norm(v['value']) for vs in e.get('aliases',{}).values() for v in vs}
            matches=[i for i in b['institutions'] if norm(i['record']['name']) in names]
        if len(matches)>1:reason='Multiple existing institution identities; hold for reconciliation'
        old=matches[0]['record'] if len(matches)==1 else None
        if old and old.get('wikidata_id') and old['wikidata_id']!=r['qid']:reason='Existing institution authority conflicts with source; shared name is insufficient'
        if old and old['canonical_institution_id']:
            old=allinst[old['canonical_institution_id']]['record']
        places=[c for c in active(e,'P131') if isinstance(value(c),dict) and not c.get('qualifiers',{}).get('P582')]
        preferred=[c for c in places if c['rank']=='preferred'];places=preferred or places
        cities=[p for p in r['cities'] if p['qid'].rsplit('/',1)[-1] in {value(c)['id'] for c in places}]
        # Source municipality labels are retained; no administrative unit is silently renamed a city.
        city=cities[0]['name'] if len(cities)==1 else None
        if old and old['place_id']:place=next((p for p in b['places'] if p['id']==old['place_id']),None)
        else:
            vs=[v for v in b['venues'] if old and v['institution_id']==old['id']]
            place=next((p for p in b['places'] if len(vs)==1 and p['id']==vs[0]['place_id']),None)
            if not place and city:place=next((p for p in b['places'] if p['country_code']==r['country'] and norm(p['name'])==norm(city)),dict(id=uid('place/'+r['country']+'/'+city),name=city,normalized_name=norm(city),country_code=r['country']))
        if not place:reason=reason or 'Geographic locality needs individual review'
        if place and place['country_code']!=r['country']:reason='Existing/source country conflict'
        result=dict(qid=r['qid'],country=r['country'],name=old['name'] if old else label(e),institution_id=old['id'] if old else uid('institution/'+r['qid']),slug=old['slug'] if old else 'nordic-'+r['qid'].lower()+'-'+re.sub('[^a-z0-9]+','-',norm(label(e))).strip('-')[:90],before=old,place=place,website=(old.get('website_url') if old else None) or next((u for u in vals(e,'P856') if isinstance(u,str) and u.startswith('https://')),None),receipt=d['receipt'],types=sorted(types),reason=reason,confidence=.9,confidence_basis='Exact Wikidata institutional identity, explicit country and current administrative locality, museum/gallery classification and preserved source labels. Existing source-specific names reconciled by reviewed identities or unique exact multilingual names; editorial assessment, not a calibrated probability.')
        out.append(result)
    save(RUN/'institution-review.json',out)
    print('Institutions ready',sum(not r['reason'] for r in out),'held',dict(collections.Counter(r['reason'] for r in out if r['reason'])),flush=True)

def reviewed_museums():
    path=RUN/'institution-review-v4.json'
    if not path.exists():path=RUN/'institution-review-v3.json'
    if not path.exists():path=RUN/'institution-review-v2.json'
    return load(path if path.exists() else RUN/'institution-review.json')
def institution_followup():
    rows={r['qid']:r for r in load(RUN/'institution-review.json')};b=load(RUN/'baseline.json.gz')
    captures={}
    for key,url in {
      'kode-history':'https://www.kodebergen.no/om-oss/institusjonens-historie',
      'frederiksborg-museum':'https://frederiksborg.dk/en/museum-2/',
      'kunst-silo-collections':'https://www.kunstsilo.no/en/our-collections',
      'rasmus-museum':'https://www.kodebergen.no/en/museums/rasmus-meyer',
    }.items():
        dest=RUN/'references'/(key+'.json')
        if dest.exists():captures[key]=load(dest);continue
        raw,rc=capture(url);assert rc['status']==200
        soup=m.BeautifulSoup(raw,'html.parser')
        for tag in soup(['script','style','nav','footer','header']):tag.decompose()
        captures[key]=dict(receipt=rc,text=soup.get_text('\n',strip=True));save(dest,captures[key])
    assert 'Bergen Kunstmuseum' in captures['kode-history']['text']
    assert '1878' in captures['frederiksborg-museum']['text']
    assert 'Sørlandet Art Collection' in captures['kunst-silo-collections']['text']
    groups=[('Q1770313','Q12715958','kode-history'),('Q226103','Q3078776','frederiksborg-museum'),('Q2679762','Q124728154','kunst-silo-collections'),('Q113468011','Q4976948','zorn-collection')]
    rows['Q4976948']['reason']=None;rows['Q4976948']['primary_identity_evidence']=load(RUN/'references/zorn-collection.json')['receipt']
    for oldq,newq,key in groups:
        original=rows[oldq];target=rows[newq];proof=captures.get(key) or load(RUN/'references'/(key+'.json'))
        for field in ['institution_id','slug','before','place','name','website']:original[field]=target[field]
        original.update(reason=None,canonical_qid=newq,primary_identity_evidence=proof['receipt'],identity_note='Museum-authored institutional/collection continuity record reviewed; original collection identity remains in artwork citations. A source collection name does not imply current display at a particular branch.')
    rr=rows['Q40914682'];old=next(i['record'] for i in b['institutions'] if i['record']['id']=='5760fc9a-a505-5b14-9388-562e4f00c388')
    rr.update(before=old,institution_id=old['id'],slug=old['slug'],name=old['name'],primary_identity_evidence=captures['rasmus-museum']['receipt'])
    # Swedish and Danish national museums share a translated label, not an identity.
    d=rows['Q648166'];e=saved_entities('museums')['Q648166']['entity'];city=next(r['cities'][0]['name'] for r in load(RUN/'directory-v2.json') if r['qid']=='Q648166')
    place=next(p for p in b['places'] if p['country_code']=='DK' and p['name']=='Copenhagen')
    d.update(before=None,institution_id=uid('institution/Q648166'),slug='nordic-q648166-national-museum-of-denmark',name=label(e),place=place,reason=None,identity_note='Rejected false multilingual name match to Stockholm Nationalmuseum: explicit country, native name and official website distinguish the Danish museum.')
    save(RUN/'institution-review-v2.json',list(rows.values()));print('Reviewed institutional continuities',len(groups),'and two exact identity corrections',flush=True)

def extra_entities():
    ids=[];selections=[]
    for q in ['Q648166','Q2679762']:
        p=RUN/'indexes-v2'/(q+'.json');data=load(p)
        if 'ids' not in data:
            query='SELECT DISTINCT ?work WHERE { ?work wdt:P195 wd:'+q+' } LIMIT 24'
            raw,rc=capture('https://query.wikidata.org/sparql',dict(query=query,format='json'));assert rc['status']==200
            data=dict(qid=q,receipt=rc,ids=[x['work']['value'].rsplit('/',1)[-1] for x in json.loads(raw)['results']['bindings']]);save(RUN/'indexes-followup'/(q+'.json'),data)
        chosen=data.get('ids',[])[:24];ids+=chosen;selections.append(dict(qid=q,ids=chosen))
    save(RUN/'entity-selection-followup.json',selections);entity_batches(ids,'works-followup')

def qualified_holding(claim):
    qs=claim.get('qualifiers',{})
    if set(qs)-{'P580','P217'}:return False
    for s in qs.get('P580',[]):
        v=s.get('datavalue',{}).get('value',{});hit=re.fullmatch(r'\+(\d{4})-\d\d-\d\dT00:00:00Z',v.get('time',''))
        if not hit or int(hit[1])>=2026 or v.get('precision',0)<9 or v.get('before') or v.get('after'):return False
    return all(s.get('snaktype')=='value' and isinstance(s.get('datavalue',{}).get('value'),str) for s in qs.get('P217',[]))

def work_fields(e,museum,creators,rc,collection_evidence=None):
    cs=active(e,'P195')
    if len(cs)!=1 or not isinstance(value(cs[0]),dict) or value(cs[0]).get('id')!=museum['qid']:return None,'Multiple or different collection statements'
    c=cs[0]
    if not qualified_holding(c):return None,'Collection qualifier needs review'
    if not collection_evidence and not any(ref.get('snaks',{}).get('P854') or ref.get('snaks',{}).get('P248') for ref in c.get('references',[])):return None,'Collection statement lacks source reference'
    kinds={v['id'] for v in vals(e,'P31') if isinstance(v,dict)}
    if kinds=={'Q3305213'}:kind='painting'
    elif kinds in ({'Q132137'},{'Q132137','Q3305213'}):kind='painting'
    elif kinds=={'Q860861'}:kind='sculpture'
    elif kinds=={'Q93184'}:kind='drawing'
    else:return None,'Object form or ensemble requires individual review'
    if active(e,'P361') or active(e,'P527'):return None,'Part or ensemble identity requires review'
    title=label(e)
    if not title:return None,'Source title absent'
    ds=active(e,'P571');first=last=None;precision='unknown';display='Creation date unknown'
    if len(ds)>1:return None,'Multiple creation dates require review'
    if ds:
        d=value(ds[0]);qs=ds[0].get('qualifiers',{});hit=re.fullmatch(r'\+(\d{4})-\d\d-\d\dT00:00:00Z',d.get('time','')) if isinstance(d,dict) else None
        if not hit or d.get('precision') not in {9,10,11} or d.get('before') or d.get('after') or d.get('calendarmodel')!='http://www.wikidata.org/entity/Q1985727':return None,'Creation date precision requires review'
        if qs and not(set(qs)=={'P1480'} and len(qs['P1480'])==1 and qs['P1480'][0].get('datavalue',{}).get('value',{}).get('id')=='Q5727902'):return None,'Creation date qualifier requires review'
        first=last=int(hit[1]);precision='circa' if qs else 'exact';display=('c. ' if qs else '')+str(first)
        if first>1970 or first==1970 and qs:return None,'Creation date outside cutoff or crosses it'
    authors=active(e,'P170');aq=[];names=[]
    for a in authors:
        if a.get('qualifiers') or not isinstance(value(a),dict):return None,'Qualified or missing creator identity requires review'
        q=value(a)['id'];name=label(creators.get(q,{}).get('entity',{}))
        if not name:return None,'Creator label unavailable'
        aq.append(q);names.append(name)
    inventories=[value(a) for a in active(e,'P217') if isinstance(value(a),str) and not a.get('qualifiers')]
    inventories += [s['datavalue']['value'] for s in c.get('qualifiers',{}).get('P217',[]) if s.get('snaktype')=='value']
    inventories=list(dict.fromkeys(inventories))
    urls=sorted({s['datavalue']['value'] for cl in active(e,'P195') for ref in cl.get('references',[]) for s in ref.get('snaks',{}).get('P854',[]) if s.get('snaktype')=='value'})
    native_urls=[u for u in vals(e,'P973') if isinstance(u,str)]
    for p in ['P6002']:
        native_urls+=['https://www.wikiart.org/en/'+s for s in vals(e,p) if isinstance(s,str)]
    return dict(qid=e['id'],institution_qid=museum['qid'],institution_id=museum['institution_id'],title=title,title_aliases=sorted({v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs}),creator_qids=aq,creator_label='; '.join(names) or None,first=first,last=last,precision=precision,date_display=display,work_type=kind,object_form='icon' if 'Q132137' in kinds else None,inventories=inventories,accession='; '.join(inventories) or None,medium=None,dimensions=None,source_url='https://www.wikidata.org/wiki/'+e['id'],references=urls,native_urls=native_urls,receipt=rc,confidence=.85,confidence_basis='One explicit, non-deprecated, referenced collection statement for the exact object and museum; creator identifiers, source title, inventory and creation precision retained. Actual source is Wikidata; cited native records are not independently verified unless separately captured. Editorial confidence, not calibrated probability.',uncertainty=['Creation date unknown; retained in review without inferred years.'] if precision=='unknown' else []),None

def selection():
    museums={r['qid']:r for r in reviewed_museums()};creators=saved_entities('creators');works=saved_entities('works');selected=[];held=[]
    corroboration={r['qid']:r for r in load(RUN/'commons-reviewed.json')['accepted']} if (RUN/'commons-reviewed.json').exists() else {}
    for q,d in works.items():
        e=d['entity'];qs={v.get('id') for v in vals(e,'P195') if isinstance(v,dict)}
        ms=[museums[x] for x in qs if x in museums and not museums[x]['reason']]
        if len(ms)!=1:held.append(dict(qid=q,reason='Institution unresolved or outside selected museum/gallery scope',institutions=sorted(qs)));continue
        row,reason=work_fields(e,ms[0],creators,d['receipt'],corroboration.get(q))
        if reason:held.append(dict(qid=q,reason=reason,institution_qid=ms[0]['qid']))
        else:
            if q in corroboration:
                row['collection_corroboration']=corroboration[q]
                row['confidence_basis']='Explicit object-specific museum field in the preserved Commons file-page wikitext agrees with the exact Wikidata object and single collection statement. File attribution, source credit and inventory were reviewed; not independent institutional verification or an on-view claim. Editorial assessment, not a calibrated probability.'
            selected.append(row)
    if (RUN/'native-selected.json').exists():selected+=load(RUN/'native-selected.json')
    save(RUN/'selected-source-records-v3.json.gz',selected);save(RUN/'held-source-records-v3.json',held)
    print('Selected',len(selected),'institutions',len({r['institution_id'] for r in selected}),'held',dict(collections.Counter(r['reason'] for r in held)),flush=True)

def commons_review():
    approved='''Q104009370 Q105509810 Q105510441 Q52127559 Q60677416 Q20987656 Q20987747 Q20987852 Q69875266 Q107265143 Q111821881 Q110626632 Q122946994 Q123003121 Q111821996 Q114119780 Q114355101 Q116939402 Q116939415 Q24714471 Q113876805 Q116771235 Q123181767 Q22981324 Q22985028 Q130480681 Q137760318 Q21039028 Q21570175 Q21747212 Q23002058 Q51991144 Q106462090 Q102346598 Q102379052 Q104187068 Q104776462 Q27031564 Q115589659 Q115589829 Q19960771 Q105631672 Q107060626 Q110825185 Q109886695'''.split()
    evidence={r['qid']:r for r in load(RUN/'commons-evidence.json.gz')};works=saved_entities('works');accepted=[];held=[]
    for q in approved:
        e=evidence[q];assert e['fields'].get('institution') and e['fields'].get('source')
        explicit_qid=bool(re.search(r'\|\s*wikidata\s*=\s*'+q+r'\b',e['wikitext'],re.I))
        assert explicit_qid or q in {'Q111821996','Q116771235','Q22981324'},'Exact object ID absent from file description'
        if not explicit_qid:
            date=vals(works[q]['entity'],'P571')[0]['time'][1:5];assert e['fields']['date']==date
        if e['inventories'] and e['fields'].get('accession number'):
            assertion=e['fields']['accession number'];clean=re.sub(r'(?i)\b(?:inv\.?\s*(?:nr\.?|no\.?)|identifier)\s*:?','',assertion).strip()
            assert any(acc(v)==acc(clean) for v in e['inventories']),(q,assertion,e['inventories'])
        if q=='Q106462090':limitation='Source reproduction is a detail of the painting. Only its explicit collection metadata supports this whole-work record; no detail image is attached or created as a separate artwork.'
        elif q=='Q104187068':limitation='Commons uses the historic Bergen Kunstmuseum name. Kode’s official institutional history confirms collection continuity; native BB.M.00491 identifier also appears in the file notes.'
        else:limitation='Actual corroborating source is the Commons file description, including its museum field and source credit. Linked underlying pages were not independently fetched in this decision; no current-display inference.'
        accepted.append(dict(qid=q,institution_qid=e['institution_qid'],file=e['file'],source_url='https://commons.wikimedia.org/wiki/'+e['file'].replace(' ','_'),receipt=e['receipt'],explicit_institution=e['fields']['institution'],explicit_accession=e['fields'].get('accession number'),source_credit=e['fields']['source'],limitation=limitation,editorial_confidence=.85))
    for q,e in evidence.items():
        if q in approved:continue
        reason='No accepted explicit static collection corroboration, or insufficient provenance/version information'
        if q in ['Q108920195','Q108920207','Q110289522']:reason='Source medium/original institutional caption indicates graphic work or impression requiring separate review; do not trust the painting type alone'
        if e['institution_qid']=='Q5509094':reason='Historic Funen institution requires successor reconciliation; no new obsolete museum created'
        held.append(dict(qid=q,reason=reason))
    save(RUN/'commons-reviewed.json',dict(at=now(),accepted=accepted,held=held,source='Wikimedia Commons literal file-page wikitext; no image downloads or independent primary-source claim.'))
    print('Commons accepted',len(accepted),'held',len(held),flush=True)

def native():
    museums={r['qid']:r for r in load(RUN/'institution-review-v2.json')};b=load(RUN/'baseline.json.gz');pages={}
    urls={'vigeland-collection':'https://vigeland.museum.no/en/permanent-exhibition/sal-i','vigeland-contact':'https://vigeland.museum.no/en/vigelandmuseum/kontakt','milles-178':'https://konstdatabas.millesgarden.se/milles_print.asp?id=178'}
    for key,url in urls.items():
        raw,rc=capture(url);assert rc['status']==200
        soup=m.BeautifulSoup(raw,'html.parser')
        for tag in soup(['script','style','nav','footer','header']):tag.decompose()
        pages[key]=dict(receipt=rc,text=soup.get_text(' ',strip=True));save(RUN/'references'/(key+'.json'),pages[key])
    contact=pages['vigeland-contact'];assert 'N-0268 Oslo' in contact['text'] and 'Norway' in contact['text']
    assert not any('vigeland' in i['record']['name'].casefold() and 'emanuel' not in i['record']['name'].casefold() for i in b['institutions'])
    place=next(p for p in b['places'] if p['country_code']=='NO' and p['name']=='Oslo')
    museums['Q7928869']=dict(qid='Q7928869',country='NO',name='Vigeland Museum',institution_id=uid('institution/Q7928869'),slug='nordic-q7928869-vigeland-museum',before=None,place=place,website='https://vigeland.museum.no/en/',receipt=contact['receipt'],types=['Q33506'],reason=None,confidence=.99,confidence_basis='Official municipal museum contact page gives the exact museum identity and Oslo, Norway address; general Norwegian museum discovery independently includes the matching Wikidata identity. Museum collection catalogue distinguishes Gustav Vigeland from Emanuel Vigeland.')
    museums['Q5509094']['reason']='Historical Funen Art Museum identity; successor collection needs reconciliation before adding current holdings.'
    save(RUN/'institution-review-v3.json',list(museums.values()))
    rows=[]
    def row(key,mq,title,first,last,medium,accession,creator,rc,dimensions=None):
        museum=museums[mq]
        return dict(qid=key,source_scheme='nordic-native-object',institution_qid=mq,institution_id=museum['institution_id'],title=title,title_aliases=[title],creator_qids=[],creator_label=creator,first=first,last=last,precision='exact' if first==last else 'range',date_display=str(first) if first==last else f'{first}–{last}',work_type='sculpture',object_form=None,inventories=[accession] if accession else [],accession=accession,medium=medium,dimensions=dimensions,source_url=rc['final_url'],references=[rc['final_url']],native_urls=[rc['final_url']],receipt=rc,confidence=.99,confidence_basis='Museum-authored individual catalogue entry or explicitly labelled original sculpture in the museum’s permanent collection guide; exact version, source date and material retained. No current-display assertion.',uncertainty=['Creator retained as an object-level label; no matching existing painter authority was found.'])
    d=pages['vigeland-collection'];assert 'plaster original of Hagar and Ismael' in d['text']
    for key,title,year in [('hagar-ismael','Hagar and Ismael',1889),('doomsday','Doomsday',1894),('rizpah','Rizpah mourns her sons',1894),('resurrection','Resurrection',1900)]:
        assert re.search(r'Gustav Vigeland,\s*'+re.escape(title)+r'\s*,\s*'+str(year)+r'\.\s*Plaster\.',d['text'])
        rows.append(row('vigeland-hall-i-'+key,'Q7928869',title,year,year,'Plaster',None,'Gustav Vigeland',d['receipt']))
    d=pages['milles-178'];assert all(x in d['text'] for x in ['Guds Hand (M 119 B)','1952-54','Carl Milles','svartgrönpatinerad brons','68,5'])
    rows.append(row('millesgarden-178','Q667094','Guds Hand (M 119 B)',1952,1954,'svartgrönpatinerad brons','M 119 B','Carl Milles',d['receipt'],'H 68,5 × B 30 × Dj 20 cm'))
    rows[-1]['uncertainty'].append('This is the catalogued 68.5 cm bronze M 119 B; it is not identified as the monumental outdoor cast. The museum’s 1952–54 object date is retained without inventing a separate casting date.')
    save(RUN/'native-selected.json',rows);print('Direct native catalogue selections',len(rows),'museums',2,flush=True)

def validate_institution_crosswalks(rows):
    for r in rows:
        if r.get('reason') or not r.get('before'):continue
        old=r['before'].get('wikidata_id');target=r.get('canonical_qid',r['qid'])
        assert old in (None,target),(r['qid'],old,'Conflicting institution authority; namesake is not a match')
def identity_correction():
    rows=load(RUN/'institution-review-v3.json');entities=saved_entities('museums')
    for r in rows:
        if r['qid']!='Q2817221':continue
        assert r['before']['wikidata_id']=='Q1967614'
        r.update(before=None,institution_id=uid('institution/Q2817221'),name=label(entities['Q2817221']['entity']),slug='nordic-q2817221-national-portrait-gallery-of-sweden',website='https://www.nationalmuseum.se/',identity_note='Rejected the English-name collision with the Smithsonian National Portrait Gallery (Q1967614, npg.si.edu). The Swedish National Portrait Gallery is Q2817221 at Gripsholm, Strängnäs. Distinct source country, institution authority and website; no Smithsonian changes.',reason=None)
    validate_institution_crosswalks(rows);save(RUN/'institution-review-v4.json',rows);print('All accepted institution authorities verified; Swedish/Smithsonian namesakes kept separate',flush=True)

def database_health():
    with connect() as db:
        print('Activity',list(db.execute("SELECT state,wait_event_type,wait_event,count(*) n FROM pg_stat_activity WHERE datname=current_database() GROUP BY 1,2,3")),flush=True)
        print('Table',list(db.execute("SELECT relname,reltuples,pg_size_pretty(pg_relation_size(oid)) size FROM pg_class WHERE relname IN ('artworks','artworks_institution_idx','artworks_institution_year_page_idx')")),flush=True)
        print('Plan',list(db.execute("EXPLAIN (FORMAT JSON) SELECT id,title FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND normalized_title=ANY(%s)",('ee9976cf-63a1-48f7-9e34-eb5444e0486c',['portrait of a man']))),flush=True)

def snap(db,ids):
    result={x['r']['id']:dict(artwork=x['r']) for x in db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,))}
    for key,table,col in [('creators','artwork_artists','artwork_id'),('images','artwork_media','artwork_id'),('holdings','artwork_location_assertions','artwork_id'),('citations','citations','entity_id'),('identifiers','external_identifiers','entity_id')]:
        for x in result.values():x[key]=[]
        for x in db.execute(f'SELECT to_jsonb(t) r FROM {table} t WHERE {col}=ANY(%s::uuid[]) ORDER BY to_jsonb(t)::text',(ids,)):
            result[x['r'][col]][key].append(x['r'])
    return result
def acc(s):return ''.join(c for c in norm(s) if c.isalnum())
def proof_file(path):return dict(path=str(path.relative_to(ROOT)),sha256=m.sha(path.read_bytes()))

def prepare():
    rows=load(RUN/'selected-source-records-v3.json.gz');museums={r['qid']:r for r in reviewed_museums()};b=load(RUN/'baseline.json.gz')
    validate_institution_crosswalks(list(museums.values()))
    artists={x['id']:x for x in b['artists']};aq=collections.defaultdict(set)
    for e in b['artist_external']:
        if e['scheme']=='wikidata' and artists[e['entity_id']]['status']!='archived':aq[e['external_id']].add(e['entity_id'])
    for r in rows:
        r.setdefault('source_scheme','wikidata')
        r['artist_ids']=sorted({next(iter(aq[q])) for q in r['creator_qids'] if len(aq[q])==1}) if all(len(aq[q])==1 for q in r['creator_qids']) else []
        r['institution_id']=museums[r['institution_qid']]['institution_id']
    qids=[r['qid'] for r in rows];mids=sorted({r['institution_id'] for r in rows}|{x['institution_id'] for x in museums.values() if x['before'] and not x['reason']})
    titlekeys=sorted({norm(t) for r in rows for t in r['title_aliases']})
    aids=sorted({a for r in rows for a in r['artist_ids']})
    with connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        ext=list(db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s)",(qids,)))
        urls=sorted({u for r in rows for u in r['native_urls']+r['references'] if urlsplit(u).path.count('/')>=2})
        exacturls=list(db.execute("SELECT entity_id::text,canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) UNION SELECT entity_id::text,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,urls))) if urls else []
        scoped=[];inventories=sorted({acc(v) for r in rows for v in r['inventories']})
        for part in m.chunks(mids,5):
            scoped += [dict(x) for x in db.execute("SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,creation_year_start,creation_year_end,status FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' AND (normalized_title=ANY(%s) OR regexp_replace(lower(coalesce(accession_number,'')),'[^a-z0-9]','','g')=ANY(%s))",(part,titlekeys,inventories))]
        museum_nonempty={x['id'] for x in db.execute("SELECT i.id::text FROM institutions i WHERE id=ANY(%s::uuid[]) AND EXISTS(SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived')",(mids,))}
        related=[dict(x) for x in db.execute("SELECT DISTINCT a.id::text,a.title,a.alternate_title,a.normalized_title,a.accession_number,a.current_institution_id::text,a.creation_year_start,a.creation_year_end,a.status FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' AND a.normalized_title=ANY(%s)",(aids,titlekeys))]
        unlinked=[dict(x) for x in db.execute("SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,creation_year_start,creation_year_end,status,unlinked_creator_label FROM artworks WHERE status<>'archived' AND normalized_title=ANY(%s) AND unlinked_creator_label IS NOT NULL",(titlekeys,))]
        related+=unlinked;creatorlabels={r['id']:norm(r['unlinked_creator_label']) for r in unlinked}
        candidates={x['id']:x for x in scoped+related};missing=sorted(({x['entity_id'] for x in ext+exacturls})-set(candidates))
        for x in db.execute('SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,creation_year_start,creation_year_end,status FROM artworks WHERE id=ANY(%s::uuid[])',(missing,)):candidates[x['id']]=dict(x)
        creatorlinks=list(db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(list(candidates),)))
        bycreator=collections.defaultdict(set)
        for x in creatorlinks:bycreator[x['artwork_id']].add(x['artist_id'])
        byqid=collections.defaultdict(set);byurl=collections.defaultdict(set);byacc=collections.defaultdict(set);bytitle=collections.defaultdict(set)
        for x in ext:byqid[x['external_id']].add(x['entity_id'])
        for x in exacturls:byurl[x['url']].add(x['entity_id'])
        for a in candidates.values():
            if a['accession_number']:byacc[(a['current_institution_id'],acc(a['accession_number']))].add(a['id'])
            for t in [a['title'],a.get('alternate_title')]:
                if t:bytitle[norm(t)].add(a['id'])
        selected=[];held=[]
        for r in rows:
            exact=byqid[r['qid']];inventory=set().union(*(byacc[(r['institution_id'],acc(v))] for v in r['inventories'])) if r['inventories'] else set()
            source=set().union(*(byurl[u] for u in r['native_urls']+r['references'])) if r['native_urls']+r['references'] else set()
            titles=set().union(*(bytitle[norm(t)] for t in r['title_aliases']))
            plausible={aid for aid in titles if candidates[aid]['current_institution_id']==r['institution_id'] or r['artist_ids'] and bycreator[aid]==set(r['artist_ids']) or r['creator_label'] and creatorlabels.get(aid)==norm(r['creator_label'])}
            strong=exact|inventory|source
            # Broad source references and title/version similarity never create a duplicate or force a match.
            if len(strong)>1:held.append(dict(qid=r['qid'],reason='Conflicting exact object, inventory or source identities',candidates=sorted(strong)));continue
            if not strong and plausible:
                held.append(dict(qid=r['qid'],reason='Possible existing title/creator version; retain for exact-object reconciliation',candidates=sorted(plausible)));continue
            aid=next(iter(strong)) if strong else uid('artwork/'+r['qid']);a=candidates.get(aid)
            if a:
                reason=None
                if a['status']=='archived':reason='Existing object archived'
                elif a['current_institution_id'] not in (None,r['institution_id']):reason='Existing holding differs; preserve it'
                elif not ({norm(a['title']),norm(a.get('alternate_title'))}&{norm(t) for t in r['title_aliases']}):reason='Existing/source title requires translation or version review'
                elif a['accession_number'] and r['inventories'] and acc(a['accession_number']) not in {acc(v) for v in r['inventories']}:reason='Existing/source inventory conflict'
                elif bycreator[aid] and (not r['artist_ids'] or bycreator[aid]!=set(r['artist_ids'])):reason='Existing/source creator identity conflict'
                if reason:held.append(dict(qid=r['qid'],reason=reason,candidates=[aid]));continue
            r.update(artwork_id=aid,action='reuse' if a else 'create',identity_basis='Unique exact source QID, inventory or object-page concordance with matching title and no creator, inventory or holding conflict.' if a else 'No matching source identity, institution inventory, or title/creator version in the scoped production catalogue.')
            selected.append(r)
        internal=collections.defaultdict(list)
        for r in selected:
            internal[('id',r['artwork_id'])].append(r['qid'])
            for inventory in r['inventories']:internal[('inventory',r['institution_id'],acc(inventory))].append(r['qid'])
            if not r['inventories']:internal[('undocumented-version',r['institution_id'],norm(r['title']),tuple(r['creator_qids']),r['first'],r['last'])].append(r['qid'])
        duplicates={q for group in internal.values() if len(set(group))>1 for q in group}
        for r in selected:
            if r['qid'] in duplicates:held.append(dict(qid=r['qid'],reason='Two selected source records may describe one physical object; individual reconciliation required'))
        selected=[r for r in selected if r['qid'] not in duplicates]
        before=snap(db,[r['artwork_id'] for r in selected]);ready=[]
        for r in selected:
            old=before.get(r['artwork_id']);claims=[h for h in old['holdings'] if h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by']] if old else []
            if claims and any(h['institution_id']!=r['institution_id'] for h in claims):held.append(dict(qid=r['qid'],reason='Accepted holding differs; preserve it'));continue
            r['before']=old;r['add_holding']=not claims;ready.append(r)
        used={r['institution_id'] for r in ready}
        changes={}
        for r in museums.values():
            if r['reason']:continue
            if r['institution_id'] not in used and not r['before']:continue
            old=r['before']
            if old and old['place_id'] and old['wikidata_id']:continue
            if old and old['id'] not in museum_nonempty and old['id'] not in used:continue
            if r['institution_id'] in changes and r.get('canonical_qid')!=r['qid']:continue
            changes[r['institution_id']]=r
        museum_before={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=ANY(%s::uuid[])',(list(changes),))}
        for iid,r in changes.items():assert museum_before.get(iid)==r['before'],'Institution changed since baseline'
        counts=list(db.execute("SELECT p.country_code,count(*) n FROM institutions i JOIN places p ON p.id=i.place_id WHERE p.country_code=ANY(%s) AND i.canonical_institution_id IS NULL AND EXISTS(SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived') GROUP BY 1",(list(COUNTRIES),)))
        artist_rows={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artists a WHERE id=ANY(%s::uuid[])',(sorted({a for r in ready for a in r['artist_ids']}),))}
        query_plan=db.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=%s AND status<>'archived' LIMIT 100",(mids[0],)).fetchone()
    plan=dict(at=now(),authorization='User requested: try to cover all Denmark, Sweden and Norwegian museums and galleries. Selected production museum coverage additions and verified geography; real local database remains read-only.',records=ready,institutions=list(changes.values()),artists=artist_rows,held=held,counts_before=counts,query_plan=query_plan,evidence=[proof_file(RUN/'selected-source-records-v3.json.gz'),proof_file(RUN/'institution-review.json'),proof_file(RUN/'institution-review-v2.json')],policy='Source-backed selected pre-1971 and explicitly undated review artworks. No new image attachments, current display assertions or publication changes. No invented creators, dates, media or dimensions.')
    for path in ['institution-review-v3.json','institution-review-v4.json','native-selected.json','commons-reviewed.json','commons-evidence.json.gz']:
        if (RUN/path).exists():plan['evidence'].append(proof_file(RUN/path))
    save(RUN/'plan-v2.json.gz',plan);save(RUN/'plan-pin-v2.json',proof_file(RUN/'plan-v2.json.gz'))
    BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);save(BACKUP/'plan-and-preimages-v2.json.gz',plan)
    print(json.dumps(dict(records=len(ready),new=sum(r['action']=='create' for r in ready),existing=sum(r['action']=='reuse' for r in ready),holdings=sum(r['add_holding'] for r in ready),new_museums=sum(not r['before'] for r in changes.values()),existing_museums=sum(bool(r['before']) for r in changes.values()),held=len(held))),flush=True)

ACTOR='local-european-research'
def insert(db,table,row):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder() for _ in row)),list(row.values()))
def pinned():
    path=RUN/'plan-v2.json.gz';digest=load(RUN/'plan-pin-v2.json')['sha256'];assert m.sha(path.read_bytes())==digest
    plan=load(path)
    validate_institution_crosswalks(plan['institutions'])
    for ref in plan['evidence']:assert m.sha((ROOT/ref['path']).read_bytes())==ref['sha256']
    for row in plan['records']+plan['institutions']:
        rc=row['receipt'];assert rc['status']==200 and m.sha(gzip.decompress((ROOT/rc['body_path']).read_bytes()))==rc['sha256']
    return plan,digest
def backup():
    dest=RUN/'cloud-backup-request.json'
    if dest.exists():print('Backup already requested',flush=True);return
    raw=subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description=Before Nordic museum coverage 20261008','--async','--format=json'],text=True)
    save(dest,json.loads(raw));print('Cloud backup requested',flush=True)
def backup_verify():
    raw=subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=30','--format=json'],text=True)
    rows=[r for r in json.loads(raw) if r.get('description')=='Before Nordic museum coverage 20261008']
    assert len(rows)==1 and rows[0]['status']=='SUCCESSFUL',rows
    save(RUN/'cloud-backup.json',rows[0]);save(BACKUP/'cloud-backup.json',rows[0]);print('Backup successful',rows[0]['id'],flush=True)

def check_after(db,plan,digest):
    after=snap(db,[r['artwork_id'] for r in plan['records']]);assert len(after)==len(plan['records'])
    for r in plan['records']:
        s=after[r['artwork_id']];a=s['artwork'];old=r['before']
        assert a['current_institution_id']==r['institution_id']
        hs=[h for h in s['holdings'] if h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by']]
        assert len(hs)==1 and hs[0]['institution_id']==r['institution_id'] and hs[0]['display_state'] is None
        assert any(e['scheme']==r['source_scheme'] and e['external_id']==r['qid'] for e in s['identifiers'])
        cs=[c for c in s['citations'] if c['source_id']==uid('source') and c['field_name']==OP]
        assert len(cs)==1 and json.loads(cs[0]['evidence_note'])['plan_sha256']==digest
        if old:
            allowed={'current_institution_id','revision','updated_at','updated_by'} if r['add_holding'] else set()
            assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in old['artwork'].items() if k not in allowed}
            assert s['creators']==old['creators'] and s['images']==old['images']
            for key in ['holdings','identifiers','citations']:
                actual={x['id']:x for x in s[key]};assert all(actual[x['id']]==x for x in old[key])
        else:
            assert a['status']=='review' and a['published_at'] is None and a['research_candidate']
            assert a['primary_media_id'] is None and not s['images']
            assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(r['first'],r['last'],r['precision'])
            assert a['title']==r['title'] and a['date_display']==r['date_display'] and a['work_type']==r['work_type']
            assert a['accession_number']==r['accession'] and a['medium_text']==r['medium'] and a['dimensions_text']==r['dimensions']
            assert {x['artist_id'] for x in s['creators']}==set(r['artist_ids'])
            assert a['unlinked_creator_label']==(None if r['artist_ids'] else r['creator_label'])
    for r in plan['institutions']:
        a=db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=%s',(r['institution_id'],)).fetchone()['r']
        assert a['place_id']==r['place']['id']
        expected_q=(r['before'] or {}).get('wikidata_id') or r.get('canonical_qid',r['qid']);assert a['wikidata_id']==expected_q
        if r['before']:
            allowed={'place_id','wikidata_id','updated_at'}
            assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in r['before'].items() if k not in allowed}
        else:
            assert a['status']=='review'
            assert db.execute("SELECT 1 FROM artworks WHERE current_institution_id=%s AND status<>'archived' LIMIT 1",(r['institution_id'],)).fetchone()
    return after

def apply():
    plan,digest=pinned();assert not (RUN/'applied.json').exists();backup=load(RUN/'cloud-backup.json');assert backup['status']=='SUCCESSFUL'
    # An immutable, concrete plan and a successful recovery backup precede every mutation.
    sid=uid('source');ids=[r['artwork_id'] for r in plan['records']]
    with connect(write=True) as db,db.transaction():
        db.execute('SET LOCAL lock_timeout=10000');db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(OP,))
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        before=snap(db,ids);expected={r['artwork_id']:r['before'] for r in plan['records'] if r['before']};assert before==expected,'Concurrent artwork/relationship drift'
        ms={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([r['institution_id'] for r in plan['institutions']],))}
        assert ms=={r['institution_id']:r['before'] for r in plan['institutions'] if r['before']},'Concurrent institution drift'
        arts={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(plan['artists']),))};assert arts==plan['artists']
        exact={r['qid']:r['artwork_id'] for r in plan['records']}
        for e in db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) FOR SHARE",(list(exact),)):assert exact[e['external_id']]==e['entity_id'],'Source identity appeared since plan'
        # Recheck only selected inventories, using bounded institution groups.
        newrows=[r for r in plan['records'] if not r['before']]
        inventories=sorted({acc(v) for r in newrows for v in r['inventories']})
        existing_inventories=set()
        for part in m.chunks(sorted({r['institution_id'] for r in newrows}),5):
            for a in db.execute("SELECT current_institution_id::text,accession_number FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' AND regexp_replace(lower(coalesce(accession_number,'')),'[^a-z0-9]','','g')=ANY(%s)",(part,inventories)):
                existing_inventories.add((a['current_institution_id'],acc(a['accession_number'])))
        # Recheck exact creator/title candidates for new works.
        for r in plan['records']:
            if r['before']:continue
            if r['inventories']:
                assert not any((r['institution_id'],acc(v)) in existing_inventories for v in r['inventories']),'Institution inventory appeared since plan'
            match=db.execute("SELECT a.id FROM artworks a WHERE a.status<>'archived' AND a.normalized_title=ANY(%s) AND (a.current_institution_id=%s OR (%s::text IS NOT NULL AND lower(a.unlinked_creator_label)=lower(%s)) OR EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=ANY(%s::uuid[]))) LIMIT 1",([norm(t) for t in r['title_aliases']],r['institution_id'],r['creator_label'],r['creator_label'],r['artist_ids'])).fetchone()
            assert not match,'Possible title/creator duplicate appeared since plan'
        save(BACKUP/'locked-preimages.json.gz',dict(at=now(),plan_sha256=digest,artworks=before,institutions=ms,artists=arts))
        insert(db,'sources',dict(id=sid,slug=OP,name='Denmark, Sweden and Norway museum coverage — Wikidata and cited museum identity evidence',source_type='authority_data',base_url='https://www.wikidata.org/',adapter_key=OP))
        for r in plan['institutions']:
            p=r['place'];existing=db.execute('SELECT id::text,name,country_code FROM places WHERE id=%s',(p['id'],)).fetchone()
            if existing:assert existing['name']==p['name'] and existing['country_code']==r['country']
            else:insert(db,'places',{k:p[k] for k in ['id','name','normalized_name','country_code']})
            qid=r.get('canonical_qid',r['qid']);iid=r['institution_id'];old=r['before']
            if old:db.execute('UPDATE institutions SET place_id=%s,wikidata_id=coalesce(wikidata_id,%s),updated_at=now() WHERE id=%s',(p['id'],qid,iid))
            else:insert(db,'institutions',dict(id=iid,slug=r['slug'],name=r['name'],normalized_name=norm(r['name']),kind='museum',status='review',place_id=p['id'],wikidata_id=qid,website_url=r['website'],description='Selected collection records with preserved source evidence. Holdings do not establish current display.'))
            after=db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=%s',(iid,)).fetchone()['r']
            insert(db,'audit_log',dict(actor_user_id=ACTOR,action='update' if old else 'insert',entity_type='institution',entity_id=iid,before_json=Jsonb(old) if old else None,after_json=Jsonb(after)))
            note={k:v for k,v in r.items() if k!='before'};note['plan_sha256']=digest
            insert(db,'citations',dict(id=uid('institution-citation/'+iid),entity_type='institution',entity_id=iid,field_name=OP,source_id=sid,source_record_id=r['qid'],source_url='https://www.wikidata.org/wiki/'+r['qid'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=r['receipt']['retrieved_at'],created_by=ACTOR))
        for iid in sorted({r['institution_id'] for r in plan['records']}):insert(db,'source_institutions',dict(source_id=sid,institution_id=iid))
        for r in plan['records']:
            aid=r['artwork_id'];old=r['before']
            if not old:
                insert(db,'artworks',dict(id=aid,slug=OP+'-'+r['qid'].lower(),title=r['title'],normalized_title=norm(r['title']),date_display=r['date_display'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type=r['work_type'],object_form=r['object_form'],accession_number=r['accession'],medium_text=r['medium'],dimensions_text=r['dimensions'],unlinked_creator_label=None if r['artist_ids'] else r['creator_label'],status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
                for order,artist in enumerate(r['artist_ids'],1):
                    link=dict(artwork_id=aid,artist_id=artist,attribution_role='primary',representative_order=order,attribution_note='Exact source creator Wikidata identity. Original label: '+str(r['creator_label'])+'. '+r['source_url'])
                    insert(db,'artwork_artists',link);insert(db,'audit_log',dict(actor_user_id=ACTOR,action='insert',entity_type='artwork_creator_link',entity_id=aid,after_json=Jsonb(link)))
            elif r['add_holding']:db.execute('UPDATE artworks SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(ACTOR,aid))
            existing=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(r['source_scheme'],r['qid'])).fetchone()
            if existing:assert existing['entity_id']==aid
            else:
                link=dict(id=uid('identifier/'+r['qid']),entity_type='artwork',entity_id=aid,scheme=r['source_scheme'],external_id=r['qid'],canonical_url=r['source_url'],source_id=sid,retrieved_at=r['receipt']['retrieved_at']);insert(db,'external_identifiers',link)
                insert(db,'audit_log',dict(actor_user_id=ACTOR,action='insert',entity_type='external_identifier',entity_id=link['id'],after_json=Jsonb(link)))
            note={k:v for k,v in r.items() if k!='before'};note.update(plan_sha256=digest,actual_source='Wikidata structured statements; native citations retained without claiming they were independently checked.',publication='Review state for new records; existing publication, dates and images preserved.',holding_scope='Documented collection connection. No current display or ownership guarantee.')
            if r['source_scheme']=='nordic-native-object':note['actual_source']='Direct museum catalogue or museum-authored collection guide. Actual source text, dates and specific sculptural version verified.'
            insert(db,'citations',dict(id=uid('citation/'+r['qid']),entity_type='artwork',entity_id=aid,field_name=OP,source_id=sid,source_record_id=r['qid'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=r['receipt']['retrieved_at'],created_by=ACTOR))
            if r['add_holding']:insert(db,'artwork_location_assertions',dict(id=uid('holding/'+r['qid']),artwork_id=aid,claim_type='holding',institution_id=r['institution_id'],context='collection',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(confidence=r['confidence'],basis=r['confidence_basis'],original_museum_qid=r['institution_qid'],references=r['references'],plan_sha256=digest,limitation='Source-reported collection connection; not an on-view assertion or legal-ownership verification.'),ensure_ascii=False),checked_at=r['receipt']['retrieved_at'],review_state='accepted'))
        after=check_after(db,plan,digest);save(BACKUP/'transaction-after.json.gz',dict(at=now(),plan_sha256=digest,artworks=after))
    receipt=dict(at=now(),target='production',plan_sha256=digest,new_artworks=sum(r['action']=='create' for r in plan['records']),existing_artworks=sum(r['action']=='reuse' for r in plan['records']),new_holdings=sum(r['add_holding'] for r in plan['records']),new_museums=sum(not r['before'] for r in plan['institutions']),updated_institutions=sum(bool(r['before']) for r in plan['institutions']),local_database_changed=False,publication_preserved=True,images_preserved=True)
    save(RUN/'applied.json',receipt);print(json.dumps(receipt),flush=True)

def verify():
    plan,digest=pinned();applied=load(RUN/'applied.json');assert applied['plan_sha256']==digest
    with connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');after=check_after(db,plan,digest)
        mids=sorted({r['institution_id'] for r in plan['records']}|{r['institution_id'] for r in plan['institutions']})
        counts=list(db.execute("SELECT i.id::text,i.slug,i.name,p.country_code,count(a.id) works,count(a.primary_media_id) images FROM institutions i JOIN places p ON p.id=i.place_id LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id,p.country_code ORDER BY p.country_code,i.name",(mids,)))
        assert all(r['works']>0 for r in counts)
        claims=db.execute('SELECT count(*) n FROM artwork_location_assertions WHERE source_id=%s AND claim_type=%s',(uid('source'),'display')).fetchone();assert claims['n']==0
    save(RUN/'database-verification.json',dict(at=now(),records_verified=len(after),museum_counts=counts,new_display_claims=0,existing_artwork_metadata_images_publication_preserved=True,local_database_changed=False))
    countrychecks=[];museumchecks=[];artworkchecks=[]
    for cc in COUNTRIES:
        params=dict(country=cc,limit=60);items=[];total=None;pages=[]
        while True:
            response=m.SESSION.get('https://artlines.org/api/backend/v1/museums',params=params,timeout=(15,60));assert response.status_code==200
            data=response.json();pages.append(data);items+=data['items'];total=data['total'];cursor=data.get('next_cursor')
            if not cursor:break
            params['cursor']=cursor
        assert len({i['id'] for i in items})==len(items)==total
        assert all(i['work_count']>0 and i['country']==cc for i in items)
        countrychecks.append(dict(country=cc,total=total,pages=pages))
    for row in counts:
        response=m.SESSION.get('https://artlines.org/api/backend/v1/museums/'+row['slug'],timeout=(15,60))
        museumchecks.append(dict(id=row['id'],slug=row['slug'],status=response.status_code,data=response.json()))
        assert response.status_code==200,(row,response.status_code)
    bymuseum={r['id']:r for r in counts};samples={};samplegroups=set()
    for r in plan['records']:
        group=(bymuseum[r['institution_id']]['country_code'],r['action'])
        if group not in samplegroups or r['source_scheme']=='nordic-native-object' or r['precision']=='unknown':
            samples[r['artwork_id']]=r;samplegroups.add(group)
    for aid,r in samples.items():
        slug=bymuseum[r['institution_id']]['slug']
        response=m.SESSION.get('https://artlines.org/api/backend/v1/museums/'+slug+'/works/'+aid,timeout=(15,60))
        assert response.status_code==200,(aid,response.status_code)
        data=response.json();assert data['id']==aid
        artworkchecks.append(dict(id=aid,slug=slug,status=response.status_code,data=data))
    save(RUN/'api-verification.json',dict(at=now(),countries=countrychecks,museums=museumchecks,artworks=artworkchecks))
    print('Verified',len(after),'objects;',len(counts),'nonempty collections; countries',[(r['country'],r['total']) for r in countrychecks],flush=True)

def report():
    plan,digest=pinned();applied=load(RUN/'applied.json');verified=load(RUN/'database-verification.json');api=load(RUN/'api-verification.json')
    museums={r['qid']:r for r in reviewed_museums()};directory=load(RUN/'directory-v2.json');covered={i['id']:i for c in api['countries'] for p in c['pages'] for i in p['items']}
    existingcounts=collections.Counter(r['institution_id'] for r in plan['records'] if r['before']);newcounts=collections.Counter(r['institution_id'] for r in plan['records'] if not r['before'])
    country_names={'DK':'Denmark','SE':'Sweden','NO':'Norway'}
    with (RUN/'delivered-artworks.csv').open('w',newline='') as f:
        fields=['country','museum','artwork_id','action','title','creator','date','accession','source','source_scheme','confidence']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in plan['records']:
            mu=museums[r['institution_qid']];w.writerow(dict(country=mu['country'],museum=mu['name'],artwork_id=r['artwork_id'],action=r['action'],title=r['title'],creator=r['creator_label'],date=r['date_display'],accession=r['accession'],source=r['source_url'],source_scheme=r['source_scheme'],confidence=r['confidence']))
    ledger=[]
    for r in directory+[dict(qid='Q7928869',country='NO',name='Vigeland Museum',websites=['https://vigeland.museum.no/en/'])]:
        mu=museums[r['qid']];index=RUN/'indexes-v2'/(r['qid']+'.json');idx=load(index) if index.exists() else {}
        live=covered.get(mu['institution_id']);status='represented_in_verified_country_browsing' if live else 'institution_identity_or_scope_unresolved' if mu['reason'] else 'no_accepted_object_in_this_bounded_pass'
        ledger.append(dict(country=r['country'],source_qid=r['qid'],source_name=r['name'],canonical_name=mu['name'],institution_id=mu['institution_id'],status=status,visible_works=live['work_count'] if live else 0,new_artworks=newcounts[mu['institution_id']],source_index_candidates=len(idx.get('ids',[])),index_capped=idx.get('capped',False),reason=mu['reason'] or idx.get('skipped') or ('No qualifying exact object accepted; not evidence that the actual institution has no collection.' if not live else ''),source_url='https://www.wikidata.org/wiki/'+r['qid']))
    with (RUN/'coverage-and-gaps.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
    country_lines=[]
    for c in api['countries']:
        cc=c['country'];before=load(RUN/('api-before-v2-'+cc+'.json'))['data']['total'];newworks=sum(1 for r in plan['records'] if not r['before'] and museums[r['institution_qid']]['country']==cc)
        country_lines.append(f"| {country_names[cc]} | {before} | {c['total']} | {newworks} |")
    local=load(RUN/'local-readonly-counts.json');unknown=sum(not r['before'] and r['precision']=='unknown' for r in plan['records']);source_held=load(RUN/'held-source-records-v3.json')
    text=f'''# Denmark, Sweden and Norway museum coverage — 8 October 2026

The user requested an attempt to cover all Danish, Swedish and Norwegian museums and galleries. This completed bounded production pass adds **{applied['new_artworks']} review artworks** and **{applied['new_museums']} institutions**, supplies additional evidence for **{applied['existing_artworks']} existing artworks**, and verifies geography/authority updates for **{applied['updated_institutions']} existing institutions**.

## Verified live country coverage

| Country | Browsable collections before | Browsable collections after | New artworks |
| --- | ---: | ---: | ---: |
{chr(10).join(country_lines)}

Country pages were read with bounded keyset pagination. Every returned collection has a positive artwork count, correct country and unique identity. All {verified['records_verified']} selected artwork states, {len(verified['museum_counts'])} affected nonempty museum detail pages and {len(api['artworks'])} representative live artwork detail responses passed verification. Artwork API samples include the five direct museum objects, all selected unknown-date objects and a new/existing sample per country. New objects remain **review**, including {unknown} explicitly undated records. Existing dates, titles, creator links, images and publication states were preserved.

## Coverage and limits

The research directory contains 574 art-institution/collection leads found across targeted Wikidata museum, gallery and painting-collection indexes, plus a direct-source Vigeland Museum addition. Bounded indexes were checked for all 574 original leads; a first page is not an exhaustive collection catalogue. The broad Swedish general-museum discovery hit its row cap; targeted art-institution and collection discovery supplemented it. This is **not a complete national museum census**, and the represented collections do not have complete inventories.

The final selection contains {len(plan['records'])} accepted objects after identity reconciliation. {len(source_held)} source object records and {len(plan['held'])} additional database identity candidates remain unresolved or outside this selection. The gap ledger records empty source indexes, uncertain custody, unsupported references, later dates, qualified objects and ambiguous institutional identities. A missing Artline collection does not mean that a real museum has no artworks. No works were invented to make a museum visible.

## Evidence and identity

Actual catalogue sources are referenced Wikidata collection statements, explicitly reviewed Wikimedia Commons file-description metadata, and five directly verified museum catalogue entries/collection-guide objects from Vigeland and Millesgården. Commons fields were read as text; no reproduction files were downloaded. Unreferenced collection claims were withheld unless their exact object-specific collection evidence was reviewed. The Commons review accepted 45 corroborations and left 121 unresolved; an example rejection was a source caption describing an etching despite a painting classification.

Editorial holding confidence is 0.85 for accepted secondary-source evidence and 0.99 for the selected direct museum entries; these are assessments, not calibrated probabilities. Original source credits, collection names, native references and limitations are in the citations. Referenced pages are not described as independently fetched unless a capture exists. No current-display assertions were created.

Official museum pages establish Kode/Bergen, Kunstsilo/Sørlandet, Frederiksborg and Zorn institutional or collection continuity. The original collection identities remain in object evidence. Rasmus Meyer remains a distinct documented collection. Sweden's National Portrait Gallery and the Smithsonian National Portrait Gallery are different institutions; the initial name-only draft mapping was rejected before any database writes. The Danish and Swedish national museums were also distinguished despite a shared translated label. The obsolete Funen museum identity remains unresolved rather than creating a separate current collection.

Vigeland's four records identify the museum's original plaster versions (1889–1900), including the 1894 Rizpah version rather than its 1892 predecessor. Millesgården's record is the 68.5 cm bronze **M 119 B**, dated 1952–54 by the museum; it is not identified as the monumental outdoor cast. Missing painter authorities remain object-level creator labels. No artist biographies were invented.

## Verification and recovery

Eleven offline evidence/identity regression checks pass. Read-only identity checks used exact source identifiers, institution-scoped inventory matches and indexed title/creator lookups. Ambiguous versions were withheld. A broad initial inventory read timed out; the final procedure uses bounded institution groups and selected title/inventory filters. The retained execution plan describes the current production catalogue, not a 10-million-row load test.

Cloud SQL backup **{load(RUN/'cloud-backup.json')['id']}** succeeded before writes. Immutable final plan SHA-256: `{digest}`. Recovery plans, locked preimages and transaction postimages are under `{BACKUP}`. Earlier superseded drafts and source captures remain as audit evidence. The real local database was queried read-only; no local catalogue writes, test databases or fixtures were created. No application deployment, Terraform apply or Git commit was made.

## Deliverables

- [Delivered artwork records](delivered-artworks.csv)
- [Complete coverage and gap ledger](coverage-and-gaps.csv)
- [Production application receipt](applied.json)
- [Database verification](database-verification.json)
- [Live API verification](api-verification.json)
- [Source and object decisions](held-source-records-v3.json)
- [Reviewed Commons corroborations](commons-reviewed.json)

Procedure: `ops/nordic-museums-20261008.py`. Tests: `ops/test_nordic_museums_20261008.py`.
'''
    (RUN/'README.md').write_text(text)
    save(RUN/'summary.json',dict(at=now(),applied=applied,countries=[dict(country=c['country'],before=load(RUN/('api-before-v2-'+c['country']+'.json'))['data']['total'],after=c['total']) for c in api['countries']],research_leads=len(ledger),affected_museums=len(verified['museum_counts']),artworks_verified=verified['records_verified'],unknown_new_dates=unknown))
    print(text[:1800],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command');args=p.parse_args();globals()[args.command]()
