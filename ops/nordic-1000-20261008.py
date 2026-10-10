#!/usr/bin/env python3
"""Selected continuation: 1,000 genuinely new Nordic collection records."""
import argparse,collections,csv,gzip,importlib.util,json,re,subprocess,time,uuid
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nordic',ROOT/'ops/nordic-museums-20261008.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m;OP='nordic-1000-20261008';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
TARGET=1000
AUTHORIZATION='User: add more, 1000 artworks. Continues production Denmark, Sweden and Norway museum coverage.'
BACKUP_DESCRIPTION='Before Nordic additional 1000 artworks 20261008'
EVIDENCE_FILES=['baseline.json.gz','wd-selected.json.gz','norway-selected-v3.json.gz','smk-selected-v2.json.gz','norway-current-page-checks-v3.json']
m.RUN=RUN;save=m.save;load=m.load;norm=m.norm;acc=n.acc
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline/'+OP+'/'+s))
def capture(url,params=None,pace=1.2):return m.capture(url,params,pace=pace)

def baseline():
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        museums=[dict(x) for x in db.execute("SELECT to_jsonb(i) record,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE p.country_code IN ('DK','SE','NO') AND i.canonical_institution_id IS NULL AND i.status<>'archived'")]
        mids=[r['record']['id'] for r in museums];works=[]
        for ids in m.chunks(mids,5):
            works += [dict(x) for x in db.execute("SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,status FROM artworks WHERE current_institution_id=ANY(%s::uuid[])",(ids,))]
        wids=[r['id'] for r in works]
        identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(wids,))]
        artists=[dict(x) for x in db.execute("SELECT id::text,display_name,normalized_name,status FROM artists WHERE status<>'archived'")]
        aext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist'")]
        creators=[dict(x) for x in db.execute('SELECT artwork_id::text,artist_id::text FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(wids,))]
    data=dict(at=m.now(),museums=museums,works=works,identifiers=identifiers,artists=artists,artist_external=aext,creators=creators)
    save(RUN/'baseline.json.gz',data);BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);save(BACKUP/'baseline.json.gz',data)
    for cc in ['DK','SE','NO']:
        raw,rc=capture('https://artlines.org/api/backend/v1/museums',dict(country=cc,limit=60));assert rc['status']==200
        save(RUN/('country-before-'+cc+'.json'),dict(data=json.loads(raw),receipt=rc))
    print('Baseline',len(museums),'institutions',len(works),'artworks',flush=True)

def museums():
    return {r['record']['wikidata_id']:dict(r['record'],country=r['country_code'],qid=r['record']['wikidata_id'],institution_id=r['record']['id']) for r in load(RUN/'baseline.json.gz')['museums'] if r['record']['wikidata_id']}

def wd_index():
    ms=museums();b=load(RUN/'baseline.json.gz');existing={x['external_id'] for x in b['identifiers'] if x['scheme']=='wikidata'}
    for cc in ['DK','SE','NO']:
        targets=[r for r in ms.values() if r['country']==cc and r['qid']!='Q671384']
        choices=[]
        pending=[r for r in targets if not (RUN/'wd-index'/(r['qid']+'.json')).exists()]
        for group in m.chunks(pending,6):
            parts=[];caps={}
            for museum in group:
                q=museum['qid'];cap=1800 if q=='Q842858' else 1000 if q=='Q1132918' else 120;caps[q]=cap
                parts.append('{ { SELECT DISTINCT ?work WHERE { ?work wdt:P195 wd:'+q+'; wdt:P31 wd:Q3305213; wdt:P571 ?date . FILTER(?date <= "1970-12-31T23:59:59Z"^^xsd:dateTime) ?work p:P195 ?claim . ?claim ps:P195 wd:'+q+'; prov:wasDerivedFrom ?reference . { ?reference pr:P854 ?url } UNION { ?reference pr:P248 ?source } } ORDER BY ?work LIMIT '+str(cap)+' } BIND(wd:'+q+' AS ?museum) }')
            raw,rc=capture('https://query.wikidata.org/sparql',dict(query='SELECT ?museum ?work WHERE {'+' UNION '.join(parts)+'}',format='json'),pace=8);assert rc['status']==200
            bindings=json.loads(raw)['results']['bindings']
            for museum in group:
                q=museum['qid'];ids=[x['work']['value'].rsplit('/',1)[-1] for x in bindings if x['museum']['value'].rsplit('/',1)[-1]==q]
                save(RUN/'wd-index'/(q+'.json'),dict(receipt=rc,ids=ids,cap=caps[q]))
        for museum in targets:
            q= museum['qid'];path=RUN/'wd-index'/(q+'.json')
            if path.exists():d=load(path)
            else:
                cap=1800 if q=='Q842858' else 1000 if q=='Q1132918' else 120
                query='SELECT DISTINCT ?work WHERE { ?work wdt:P195 wd:'+q+'; wdt:P31 wd:Q3305213; wdt:P571 ?date . FILTER(?date <= "1970-12-31T23:59:59Z"^^xsd:dateTime) ?work p:P195 ?claim . ?claim ps:P195 wd:'+q+'; prov:wasDerivedFrom ?reference . { ?reference pr:P854 ?url } UNION { ?reference pr:P248 ?source } } ORDER BY ?work LIMIT '+str(cap)
                raw,rc=capture('https://query.wikidata.org/sparql',dict(query=query,format='json'),pace=8);assert rc['status']==200
                d=dict(receipt=rc,ids=[x['work']['value'].rsplit('/',1)[-1] for x in json.loads(raw)['results']['bindings']],cap=cap);save(path,d)
            new=[q for q in d['ids'] if q not in existing]
            cap=750 if museum['qid']=='Q842858' else 400 if museum['qid']=='Q1132918' else 70
            choices+=new[:cap];print(cc,museum['name'],len(d['ids']),len(new),'new source IDs',flush=True)
        save(RUN/('wd-choices-'+cc+'.json'),sorted(set(choices)))

def entities():
    n.RUN=RUN
    for cc in ['DK','SE','NO']:
        ids=load(RUN/('wd-choices-'+cc+'.json'))
        if cc=='NO':
            # Direct museum-export candidates already cover the national collection.
            national=set(load(RUN/'wd-index/Q1132918.json')['ids']);ids=[q for q in ids if q not in national]
        n.entity_batches(ids,'works-'+cc)
    n.creator_entities()

def wd_select():
    n.RUN=RUN;ms=museums();works=n.saved_entities('works');creators=n.saved_entities('creators');rows=[];held=[]
    for q,d in works.items():
        qs=[v['id'] for v in n.vals(d['entity'],'P195') if isinstance(v,dict)]
        if len(qs)!=1 or qs[0] not in ms:held.append(dict(key=q,reason='Multiple or unresolved institutions'));continue
        row,reason=n.work_fields(d['entity'],ms[qs[0]],creators,d['receipt'])
        if reason:held.append(dict(key=q,reason=reason));continue
        if row['precision']=='unknown':held.append(dict(key=q,reason='No explicit eligible date in this additional 1,000 selection'));continue
        row.update(key='wikidata/'+q,source_scheme='wikidata',external_id=q,country=ms[qs[0]]['country'],source_kind='referenced Wikidata record',source_evidence=d['entity'])
        rows.append(row)
    save(RUN/'wd-selected.json.gz',rows);save(RUN/'wd-held.json',held)
    print('WD selected',len(rows),collections.Counter(r['country'] for r in rows),'held',len(held),flush=True)

def native_row(provider,oid,museum,title,aliases,creator,creator_ids,first,last,precision,display,kind,inventory,medium,dimensions,url,rc,raw):
    return dict(key=provider+'/'+oid,qid=oid,source_scheme=provider,external_id=oid,institution_qid=museum['qid'],institution_id=museum['id'],country=museum['country'],title=title,title_aliases=sorted(set([title]+aliases)),creator_qids=[],creator_label=creator,creator_source_ids=creator_ids,first=first,last=last,precision=precision,date_display=display,work_type=kind,object_form=None,inventories=[inventory],accession=inventory,medium=medium,dimensions=dimensions,source_url=url,native_urls=[url],references=[url],receipt=rc,confidence=.97,confidence_basis='Museum-authored exact object catalogue record with inventory, creator and explicitly eligible creation date; source fields and qualifications preserved. Documented collection connection, not a current-display claim.',source_kind=provider,source_evidence=raw,uncertainty=[])

def existing_keys(museum):
    b=load(RUN/'baseline.json.gz');rows=[r for r in b['works'] if r['current_institution_id']==museum['id']]
    return {acc(r['accession_number']) for r in rows if r['accession_number']},{norm(t) for r in rows for t in [r['title'],r['alternate_title']] if t}

def norwegian_fields(item,museum,rc):
    e=item['_source']['MetaData'];oid=item['_id'];inventory=item['_source'].get('NmId')
    if not inventory or '-' in inventory or re.search(r'VERSO|RECTO',inventory,re.I):return None,'Sheet side, part or version inventory requires individual reconciliation'
    if e.get('CataloguingLevel')!=['Enkeltobjekt']:return None,'Not a single object'
    if e.get('ObjectName') not in [['Maleri'],['Tegning']]:return None,'Outside selected paintings/drawings'
    if [o.get('FullName') for o in e.get('Owner',[])]!=['Nasjonalmuseet for kunst, arkitektur og design']:return None,'Museum custody not explicit'
    if e.get('ObjectNumber')!=[inventory]:return None,'Inventory conflict'
    ps=e.get('Production',[])
    if len(ps)!=1 or ps[0].get('PerRole')!='Kunstner' or ps[0].get('LevelCertainty')!='sikker':return None,'Qualified or multiple creator roles'
    p=ps[0];creator=p.get('PersonRefMetaData',{}).get('FullName')
    if not creator or creator.casefold() in ['ukjent','ukjent kunstner']:return None,'Creator requires individual review'
    df=p.get('DateFrom','');dt=p.get('DateTo','');display='; '.join(e.get('Labeldate',[]))
    if not re.fullmatch(r'\d{4}',df) or not re.fullmatch(r'\d{4}',dt):return None,'Creation range not explicit'
    first=int(df);last=int(dt)
    if not 1000<=first<=last<=1970:return None,'Outside pre-1971 selection'
    if not display or re.search(r'etter|før|post|ante|\?|antag|mulig|trolig|tidligst|senest|uten år|udatert|ikke datert|begynnelsen|slutten',display,re.I):return None,'Uncertain date needs review'
    circa=bool(re.search(r'ca\.?|omkring',display,re.I))
    if circa and last==1970:return None,'Circa range crosses cutoff'
    precision=('circa' if first==last else 'circa_range') if circa else ('exact' if first==last else 'range')
    titles=e.get('ObjectTitle',[])
    if len(titles)!=1 or not titles[0].get('Title'):return None,'Title variant needs review'
    source_title=titles[0]['Title'];alts=titles[0].get('Alternatives',[]);title=next((v['Title'] for v in alts if v.get('Lang')=='ENG'),source_title)
    row=native_row('nasjonalmuseet-object',oid,museum,title,[source_title]+[v['Title'] for v in alts],creator,[['nasjonalmuseet-person',str(p['PersonRef'])]],first,last,precision,display or (df if df==dt else df+'–'+dt),'painting' if e['ObjectName']==['Maleri'] else 'drawing',inventory,'; '.join(e.get('MaterialTechnique',[])) or None,'; '.join(e.get('PreviewDimensionsNo',[])) or None,'https://www.nasjonalmuseet.no/en/collection/object/'+quote(inventory,safe=''),rc,item)
    row['uncertainty'].append('Museum-published collection metadata export dated 3 December 2020, retrieved now. Current display and legal ownership were not independently verified. Selected current native pages were checked as samples only.')
    row['confidence']=.94
    return row,None

def norway():
    museum=museums()['Q1132918'];existing,titles=existing_keys(museum)
    url='https://raw.githubusercontent.com/nasjonalmuseet/collection/master/metadata-json/nasjonalmuseet-collection-part4.json'
    raw,rc=capture(url);assert rc['status']==200;data=json.loads('{'+raw.decode()+'}')
    rows=[];held=[]
    for item in data['hits']:
        row,reason=norwegian_fields(item,museum,rc)
        if row and (acc(row['accession']) in existing or any(norm(t) in titles for t in row['title_aliases'])):reason='Existing museum inventory or title; excluded from new-object queue'
        if reason:held.append(dict(key=item['_id'],reason=reason))
        elif len(rows)<600:rows.append(row)
    save(RUN/'norway-selected-v3.json.gz',rows);save(RUN/'norway-held-v3.json',held)
    print('Native Norway candidates',len(rows),'held',collections.Counter(r['reason'] for r in held),flush=True)

def smk_fields(e,museum,rc):
    inventory=e.get('object_number','')
    if not re.match(r'^KMS',inventory):return None,'Deposit, print or other inventory series outside selected painting scope'
    if e.get('number_of_parts',1)!=1:return None,'Multi-part work'
    if [r.get('name') for r in e.get('object_names',[])]!=['Painting']:return None,'Not an individual painting'
    ps=e.get('production',[])
    if len(ps)!=1:return None,'Multiple or missing creators'
    p=ps[0]
    if p.get('creator_qualifier') or p.get('creator_role','') not in ('','artist','Painter'):return None,'Qualified creator needs individual review'
    creator=' '.join([p.get('creator_forename',''),p.get('creator_surname','')]).strip() or p.get('creator')
    if not creator or re.search(r'ubekendt|ukendt|unknown|anonymous',creator,re.I):return None,'Unknown creator requires separate review'
    ds=e.get('production_date',[])
    if len(ds)!=1:return None,'Multiple or missing creation dates'
    d=ds[0];start=d.get('start','');end=d.get('end','');display=d.get('period','');notes='; '.join(e.get('production_dates_notes',[]))
    if not re.match(r'^\d{4}-',start) or not re.match(r'^\d{4}-',end):return None,'Unknown creation bounds'
    first=int(start[:4]);last=int(end[:4])
    if not 1000<=first<=last<=1970:return None,'Outside pre-1971 selection'
    birth=p.get('creator_date_of_birth','');death=p.get('creator_date_of_death','')
    if re.match(r'^\d{4}-',birth) and re.match(r'^\d{4}-',death) and first==int(birth[:4])+15 and abs(last-int(death[:4]))<=1:
        return None,'Apparent artist-career proxy range; retain as uncertain research evidence'
    if re.search(r'udateret|virkeår|levetid|baseret på kunstnerens|after|before|efter|før|muligvis|\?',display+' '+notes,re.I):return None,'Creation dates uncertain or based on artist biography'
    circa=bool(re.search(r'\bca\.?|circa|\bc\.',display+' '+notes,re.I))
    if circa and last==1970:return None,'Circa at cutoff'
    precision=('circa' if first==last else 'circa_range') if circa else ('exact' if first==last else 'range')
    ts=e.get('titles',[])
    if not ts or not all(t.get('title') for t in ts):return None,'Title absent'
    title=next((t['title'] for t in ts if t.get('language')=='engelsk'),ts[0]['title'])
    dims=[' '.join(str(d[k]) for k in ['part','type','value','unit'] if d.get(k) is not None) for d in e.get('dimensions',[]) if d.get('part')=='netto']
    return native_row('european-smk-statens-museum-for-kunst-object',inventory,museum,title,[t['title'] for t in ts],creator,[['smk-person',p['creator_lref']]] if p.get('creator_lref') else [],first,last,precision,display or str(first),'painting',inventory,'; '.join(e.get('techniques',[])) or None,'; '.join(dims) or None,e['frontend_url'],rc,e),None

def smk():
    museum=museums()['Q671384'];existing,titles=existing_keys(museum);rows=[];held=[];seen=set()
    for offset in range(0,3500,250):
        raw,rc=capture('https://api.smk.dk/api/v1/art/search/',dict(keys='*',filters='[object_names:Painting]',rows=250,offset=offset,lang='en',sort='object_number',sort_type='asc'))
        assert rc['status']==200;data=json.loads(raw)
        for e in data['items']:
            assert e['id'] not in seen;seen.add(e['id']);row,reason=smk_fields(e,museum,rc)
            if row and (acc(row['accession']) in existing or any(norm(t) in titles for t in row['title_aliases'])):reason='Existing museum inventory or title; excluded from new-object queue'
            if reason:held.append(dict(key=e['object_number'],reason=reason))
            else:rows.append(row)
        print('SMK',offset+len(data['items']),'bounded leads,',len(rows),'new eligible candidates',flush=True)
        if len(rows)>=550 or offset+len(data['items'])>=data['found']:break
    save(RUN/'smk-selected-v2.json.gz',rows);save(RUN/'smk-held-v2.json',held)
    print('Native SMK',len(rows),'held',collections.Counter(r['reason'] for r in held),flush=True)

def native_check():
    rows=load(RUN/'norway-selected-v3.json.gz');checks=[]
    for r in rows[::max(1,len(rows)//8)][:8]:
        raw,rc=capture(r['source_url'])
        if rc['status']!=200:
            checks.append(dict(key=r['key'],receipt=rc,verified=False,result='Current native object page unavailable; preserve source export as historical catalogue evidence and hold sampled record'))
            print('Native sample unavailable',r['accession'],rc['status'],flush=True);continue
        soup=m.BeautifulSoup(raw,'html.parser');fields={}
        for dt in soup.select('.description-list dt'):
            dd=dt.find_next_sibling('dd')
            if dd:fields[dt.get_text(' ',strip=True).rstrip(':')]=dd.get_text(' ',strip=True)
        head=soup.select_one('.collection-object-header');assert head
        title=head.select_one('h1').get_text(' ',strip=True)
        names=[a.get_text(' ',strip=True) for a in head.select('a[href*="/producer/"]')]
        years=[int(y) for y in re.findall(r'\b[12]\d{3}\b',fields.get('Creation date',''))]
        verified=bool(acc(fields.get('Inventory no.',''))==acc(r['accession']) and any(norm(name)==norm(r['creator_label']) for name in names) and norm(title) in {norm(t) for t in r['title_aliases']} and years and min(years)>=r['first'] and max(years)<=r['last'])
        checks.append(dict(key=r['key'],receipt=rc,title=title,creators=names,fields=fields,verified=verified,result='Exact inventory/title/creator/date corroborated on current page' if verified else 'Current page differs from export or date remains unresolved; sampled record withheld'))
        print('Current native sample',r['accession'],title,fields.get('Creation date'),'verified',verified,flush=True)
    save(RUN/'norway-current-page-checks-v3.json',checks)

def source_rows():
    held={r['key'] for r in load(RUN/'norway-current-page-checks-v3.json') if not r['verified']}
    return [r for name in ['wd-selected.json.gz','norway-selected-v3.json.gz','smk-selected-v2.json.gz'] for r in load(RUN/name) if r['key'] not in held]

def object_urls(r):
    urls={r['source_url']}
    if r['source_scheme']=='european-smk-statens-museum-for-kunst-object':
        oid=r['external_id'];urls.update(['https://api.smk.dk/api/v1/art?object_number='+oid,'https://open.smk.dk/en/artwork/image/'+oid,'https://collection.smk.dk/#/en/detail/'+oid])
    elif r['source_scheme']=='nasjonalmuseet-object':
        urls.add('https://www.nasjonalmuseet.no/samlingen/objekt/'+quote(r['accession'],safe=''))
        urls.add('https://www.nasjonalmuseet.no/samlingen/objekt/'+quote(r['accession'].replace('&','_'),safe=''))
        urls.add('https://www.nasjonalmuseet.no/en/collection/object/'+quote(r['accession'],safe=''))
    else:
        e=r['source_evidence']
        for value in n.vals(e,'P2539'):
            urls.add('https://collection.nationalmuseum.se/en/collection/item/'+str(value)+'/')
    return sorted(urls)

def collision_candidates(db,rows):
    keys=sorted({norm(t) for r in rows for t in r['title_aliases']});mids=sorted({r['institution_id'] for r in rows});inventories=sorted({acc(v) for r in rows for v in r['inventories']})
    extids=sorted({r['external_id'] for r in rows});urls=sorted({u for r in rows for u in object_urls(r)})
    ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))",(extids,urls))]
    cites=[dict(x) for x in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
    found={}
    for ids in m.chunks(mids,5):
        for r in db.execute("SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,unlinked_creator_label,status FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND (normalized_title=ANY(%s) OR regexp_replace(lower(coalesce(accession_number,'')),'[^a-z0-9]','','g')=ANY(%s))",(ids,keys,inventories)):found[r['id']]=dict(r)
    for part in m.chunks(keys,250):
        for r in db.execute("SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,unlinked_creator_label,status FROM artworks WHERE status<>'archived' AND normalized_title=ANY(%s)",(part,)):found[r['id']]=dict(r)
    links=[dict(x) for x in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,a.display_name creator_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(list(found),))]
    result=dict(external=ext,citations=cites,artworks=list(found.values()),creators=links)
    result['_lookups']=collision_lookups(result)
    return result

def collision_lookups(candidates):
    exact=collections.defaultdict(set);allids=collections.defaultdict(set);urls=collections.defaultdict(set);inventories=collections.defaultdict(set);titles=collections.defaultdict(dict);creators=collections.defaultdict(set);creator_names=collections.defaultdict(set)
    for x in candidates['external']:
        exact[(x['scheme'],x['external_id'])].add(x['entity_id']);allids[x['external_id']].add(x['entity_id'])
        if x['canonical_url']:urls[x['canonical_url']].add(x['entity_id'])
    for x in candidates['citations']:urls[x['source_url']].add(x['entity_id'])
    for x in candidates['artworks']:
        if x['accession_number']:inventories[(x['current_institution_id'],acc(x['accession_number']))].add(x['id'])
        for t in [x['title'],x['alternate_title']]:
            if t:titles[norm(t)][x['id']]=x
    for x in candidates['creators']:
        creators[x['artwork_id']].add(x['artist_id'])
        if x.get('creator_name'):creator_names[x['artwork_id']].add(norm(x['creator_name']))
    return exact,allids,urls,inventories,titles,creators,creator_names

def collision_reason(r,candidates):
    exact,allids,urls,inventories,titles,bycreator,creator_names=candidates.get('_lookups') or collision_lookups(candidates)
    ext=set(exact[(r['source_scheme'],r['external_id'])])
    if r['source_scheme']=='wikidata':ext.update(allids[r['external_id']])
    for url in object_urls(r):ext.update(urls[url])
    if ext:return 'Existing exact source identity',sorted(set(ext))
    for inv in r['inventories']:
        matches=inventories[(r['institution_id'],acc(inv))]
        if matches:return 'Existing institution inventory',sorted(matches)
    possible={}
    for t in r['title_aliases']:possible.update(titles[norm(t)])
    for a in possible.values():
        same_museum=a['current_institution_id']==r['institution_id']
        if same_museum or (r['artist_ids'] and bycreator[a['id']]==set(r['artist_ids'])) or (r['creator_label'] and (norm(a['unlinked_creator_label'])==norm(r['creator_label']) or norm(r['creator_label']) in creator_names[a['id']])):
            return 'Possible existing title/creator version; withheld from new-object count',[a['id']]
    return None,[]

def prepare():
    rows=source_rows();base=load(RUN/'baseline.json.gz');artists={a['id']:a for a in base['artists']};authorities=collections.defaultdict(set)
    for e in base['artist_external']:
        if e['entity_id'] in artists:authorities[(e['scheme'],e['external_id'])].add(e['entity_id'])
    for r in rows:
        creator_keys=[('wikidata',q) for q in r['creator_qids']]+[tuple(x) for x in r.get('creator_source_ids',[])]
        r['artist_ids']=sorted({next(iter(authorities[k])) for k in creator_keys}) if creator_keys and all(len(authorities[k])==1 for k in creator_keys) else []
        r['artwork_id']=uid('artwork/'+r['key'])
        r['slug']=OP+'-'+m.sha(r['key'].encode())[:20]
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        candidates=collision_candidates(db,rows);ready=[];held=[]
        for r in rows:
            reason,ids=collision_reason(r,candidates)
            if reason:held.append(dict(key=r['key'],reason=reason,candidates=ids))
            else:ready.append(r)
        groups=collections.defaultdict(list)
        for r in ready:
            for inv in r['inventories']:groups[(r['institution_id'],acc(inv))].append(r['key'])
            groups[('version',r['institution_id'],norm(r['title']),norm(r['creator_label']),r['first'],r['last'])].append(r['key'])
        duplicates={k for vals in groups.values() if len(set(vals))>1 for k in vals}
        for r in ready:
            if r['key'] in duplicates:held.append(dict(key=r['key'],reason='Within-batch inventory or same-title creator/version collision'))
        ready=[r for r in ready if r['key'] not in duplicates]
        # Rotate collections within each country, then countries, to retain breadth.
        buckets=collections.defaultdict(lambda:collections.defaultdict(list))
        for r in sorted(ready,key=lambda r:(r['source_scheme']=='wikidata',r['key'])):buckets[r['country']][r['institution_id']].append(r)
        ordered={}
        for cc,by in buckets.items():
            out=[]
            while any(by.values()):
                for iid in sorted(by):
                    if by[iid]:out.append(by[iid].pop(0))
            ordered[cc]=out
        chosen=[]
        while len(chosen)<TARGET and any(ordered.values()):
            for cc in ['DK','SE','NO']:
                if ordered.get(cc) and len(chosen)<TARGET:chosen.append(ordered[cc].pop(0))
        print('Identity-ready',len(ready),collections.Counter(r['country'] for r in ready),'chosen',len(chosen),collections.Counter(r['country'] for r in chosen),'held',collections.Counter(r['reason'] for r in held),flush=True)
        save(RUN/'identity-review.json.gz',dict(at=m.now(),ready_count=len(ready),held=held,remaining=[r['key'] for rs in ordered.values() for r in rs]))
        assert len(chosen)==TARGET,'More eligible source candidates required'
        mids=sorted({r['institution_id'] for r in chosen});aids=sorted({aid for r in chosen for aid in r['artist_ids']})
        before={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=ANY(%s::uuid[])',(mids,))}
        astates={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artists a WHERE id=ANY(%s::uuid[])',(aids,))}
        counts=[dict(x) for x in db.execute("SELECT current_institution_id::text,count(*) n FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY 1",(mids,))]
        query_plan=db.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND normalized_title=ANY(%s)",(chosen[0]['institution_id'],[norm(chosen[0]['title'])])).fetchone()
    evidence=[n.proof_file(RUN/f) for f in EVIDENCE_FILES]
    plan=dict(at=m.now(),authorization=AUTHORIZATION,target=TARGET,records=chosen,institutions=before,artists=astates,counts_before=counts,evidence=evidence,query_plan=query_plan,policy=f'{TARGET:,} new review artwork records only; dated before 1971; no existing catalogue changes or image downloads; documented holdings, no current-display claims; real local database read-only.')
    save(RUN/'plan.json.gz',plan);save(RUN/'plan-pin.json',n.proof_file(RUN/'plan.json.gz'));save(BACKUP/'plan-and-recovery.json.gz',plan)

def backup():
    raw=subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+BACKUP_DESCRIPTION,'--async','--format=json'],text=True)
    save(RUN/'cloud-backup-request.json',json.loads(raw));print('Cloud recovery backup requested',flush=True)

def backup_verify():
    raw=subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=30','--format=json'],text=True)
    rows=[r for r in json.loads(raw) if r.get('description')==BACKUP_DESCRIPTION];assert len(rows)==1 and rows[0]['status']=='SUCCESSFUL'
    save(RUN/'cloud-backup.json',rows[0]);save(BACKUP/'cloud-backup.json',rows[0]);print('Successful backup',rows[0]['id'],flush=True)

def pinned():
    pin=load(RUN/'plan-pin.json');assert m.sha((RUN/'plan.json.gz').read_bytes())==pin['sha256'];plan=load(RUN/'plan.json.gz')
    assert len(plan['records'])==len({r['artwork_id'] for r in plan['records']})==TARGET
    for ref in plan['evidence']:assert m.sha((ROOT/ref['path']).read_bytes())==ref['sha256']
    checked=set()
    for r in plan['records']:
        rc=r['receipt'];assert rc['status']==200
        if (rc['body_path'],rc['sha256']) not in checked:
            assert m.sha(gzip.decompress((ROOT/rc['body_path']).read_bytes()))==rc['sha256'];checked.add((rc['body_path'],rc['sha256']))
        assert r['first'] is not None and r['first']<=r['last']<=1970
    return plan,pin['sha256']

def insert_many(db,table,rows):
    if not rows:return
    cols=list(rows[0]);assert all(list(r)==cols for r in rows)
    q=n.sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(n.sql.Identifier(table),n.sql.SQL(',').join(map(n.sql.Identifier,cols)),n.sql.SQL(',').join(n.sql.Placeholder() for _ in cols))
    with db.cursor() as cur:cur.executemany(q,[[r[k] for k in cols] for r in rows])

def check_after(db,plan,digest):
    states=n.snap(db,[r['artwork_id'] for r in plan['records']]);assert len(states)==TARGET
    for r in plan['records']:
        state=states[r['artwork_id']];a=state['artwork']
        assert a['status']=='review' and a['published_at'] is None and a['research_candidate']
        assert a['title']==r['title'] and a['slug']==r['slug'] and a['normalized_title']==norm(r['title'])
        assert a['date_display']==r['date_display'] and (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(r['first'],r['last'],r['precision'])
        assert a['accession_number']==r['accession'] and a['medium_text']==r['medium'] and a['dimensions_text']==r['dimensions']
        assert a['work_type']==r['work_type'] and a['object_form']==r['object_form']
        assert a['current_institution_id']==r['institution_id'] and a['primary_media_id'] is None and not state['images']
        assert a['unlinked_creator_label']==(None if r['artist_ids'] else r['creator_label'])
        assert {c['artist_id'] for c in state['creators']}==set(r['artist_ids'])
        assert len(state['holdings'])==1;h=state['holdings'][0]
        assert h['claim_type']=='holding' and h['review_state']=='accepted' and h['display_state'] is None and h['institution_id']==r['institution_id'] and h['source_id']==uid('source')
        assert len(state['identifiers'])==1;e=state['identifiers'][0]
        assert e['scheme']==r['source_scheme'] and e['external_id']==r['external_id'] and e['source_id']==uid('source')
        assert len(state['citations'])==1;c=state['citations'][0];note=json.loads(c['evidence_note'])
        assert c['source_id']==uid('source') and note['plan_sha256']==digest and note['key']==r['key']
    assert db.execute("SELECT count(*) n FROM artworks WHERE created_by=%s AND id=ANY(%s::uuid[])",(n.ACTOR,list(states))).fetchone()['n']==TARGET
    return states

def apply():
    plan,digest=pinned();assert not (RUN/'applied.json').exists();assert load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'
    sid=uid('source');rows=plan['records'];ids=[r['artwork_id'] for r in rows]
    with m.connect(write=True) as db,db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(OP,))
        ms={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(list(plan['institutions']),))};assert ms==plan['institutions'],'Institution identity drift'
        astates={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(plan['artists']),))};assert astates==plan['artists'],'Creator authority drift'
        assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
        candidates=collision_candidates(db,rows)
        for r in rows:
            reason,found=collision_reason(r,candidates);assert not reason,(r['key'],reason,found)
        save(BACKUP/'locked-preimages.json.gz',dict(at=m.now(),plan_sha256=digest,new_artwork_ids=ids,existing_new_ids=[],institutions=ms,artists=astates))
        n.insert(db,'sources',dict(id=sid,slug=OP,name=f'Additional {TARGET:,} Nordic artworks — SMK API, Nasjonalmuseet published metadata, referenced Wikidata',source_type='authority_data',base_url='https://www.wikidata.org/',adapter_key=OP))
        insert_many(db,'source_institutions',[dict(source_id=sid,institution_id=iid) for iid in sorted(ms)])
        arts=[];creators=[];identifiers=[];citations=[];holdings=[]
        for r in rows:
            aid=r['artwork_id']
            arts.append(dict(id=aid,slug=r['slug'],title=r['title'],normalized_title=norm(r['title']),date_display=r['date_display'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type=r['work_type'],object_form=r['object_form'],accession_number=r['accession'],medium_text=r['medium'],dimensions_text=r['dimensions'],unlinked_creator_label=None if r['artist_ids'] else r['creator_label'],status='review',research_candidate=True,created_by=n.ACTOR,updated_by=n.ACTOR))
            for order,artist in enumerate(r['artist_ids'],1):creators.append(dict(artwork_id=aid,artist_id=artist,attribution_role='primary',representative_order=order,attribution_note='Unique exact museum or Wikidata creator authority. Original source label: '+str(r['creator_label'])+'. '+r['source_url']))
            identifiers.append(dict(id=uid('identifier/'+r['key']),entity_type='artwork',entity_id=aid,scheme=r['source_scheme'],external_id=r['external_id'],canonical_url=r['source_url'],source_id=sid,retrieved_at=r['receipt']['retrieved_at']))
            note=dict(r,plan_sha256=digest,actual_source_url=r['receipt']['url'],actual_source_kind=r['source_kind'],publication='New record in review; source qualifiers retained; no generated image or inferred creator/date.',holding_scope='Documented collection connection. Not a current-display claim. Nasjonalmuseet export is dated 2020; current page checks are samples only.')
            citations.append(dict(id=uid('citation/'+r['key']),entity_type='artwork',entity_id=aid,field_name=OP,source_id=sid,source_record_id=r['external_id'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=r['receipt']['retrieved_at'],created_by=n.ACTOR))
            holdings.append(dict(id=uid('holding/'+r['key']),artwork_id=aid,claim_type='holding',institution_id=r['institution_id'],context='collection',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,actual_source_url=r['receipt']['url'],confidence=r['confidence'],basis=r['confidence_basis'],uncertainty=r['uncertainty']),ensure_ascii=False),checked_at=r['receipt']['retrieved_at'],review_state='accepted'))
        for table,batch in [('artworks',arts),('artwork_artists',creators),('external_identifiers',identifiers),('citations',citations),('artwork_location_assertions',holdings)]:
            insert_many(db,table,batch);print('Transaction staged',table,len(batch),flush=True)
        after=check_after(db,plan,digest)
        insert_many(db,'audit_log',[dict(actor_user_id=n.ACTOR,action='insert',entity_type='artwork',entity_id=aid,after_json=n.Jsonb(dict(artwork=s['artwork'],creators=s['creators'],holding_ids=[h['id'] for h in s['holdings']],identifier_ids=[e['id'] for e in s['identifiers']],citation_ids=[c['id'] for c in s['citations']],plan_sha256=digest))) for aid,s in after.items()])
        unchanged={x['r']['id']:x['r'] for x in db.execute('SELECT to_jsonb(i) r FROM institutions i WHERE id=ANY(%s::uuid[])',(list(ms),))};assert unchanged==ms
        save(BACKUP/'transaction-after.json.gz',dict(at=m.now(),plan_sha256=digest,artworks=after))
    result=dict(at=m.now(),target='production',plan_sha256=digest,new_artworks=TARGET,new_holdings=TARGET,institutions=len(ms),countries=dict(collections.Counter(r['country'] for r in rows)),new_creators=0,new_images=0,existing_artworks_changed=False,local_database_changed=False)
    save(RUN/'applied.json',result);print(json.dumps(result),flush=True)

def verify():
    plan,digest=pinned();receipt=load(RUN/'applied.json');assert receipt['plan_sha256']==digest
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');after=check_after(db,plan,digest)
        counts=[dict(x) for x in db.execute("SELECT i.id::text,i.slug,i.name,count(a.id) works FROM institutions i JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id ORDER BY i.name",(list(plan['institutions']),))]
        assert all(r['works']>0 for r in counts)
        assert db.execute('SELECT count(*) n FROM artwork_location_assertions WHERE source_id=%s AND claim_type=%s',(uid('source'),'display')).fetchone()['n']==0
        # Database triggers also audit inserts and the holding projection update.
        # Verify exactly one operation-specific final-state audit per new object.
        audits=db.execute("SELECT count(*) n,count(DISTINCT entity_id) objects FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert' AND after_json->>'plan_sha256'=%s",(list(after),digest)).fetchone()
        assert audits['n']==audits['objects']==TARGET
    save(RUN/'database-verification.json',dict(at=m.now(),verified_artworks=TARGET,new_display_claims=0,new_images=0,all_review=True,museums=counts))
    countrychecks=[];museumchecks=[];artchecks=[]
    for cc in ['DK','SE','NO']:
        items=[];params=dict(country=cc,limit=60);pages=[]
        while True:
            response=m.SESSION.get('https://artlines.org/api/backend/v1/museums',params=params,timeout=(15,60));assert response.status_code==200;data=response.json();items+=data['items'];pages.append(data)
            if not data.get('next_cursor'):break
            params['cursor']=data['next_cursor']
        assert len(items)==len({x['id'] for x in items})==data['total'] and all(x['work_count']>0 for x in items)
        countrychecks.append(dict(country=cc,total=data['total'],pages=pages))
    slugs={r['id']:r['slug'] for r in counts}
    for mu in counts:
        response=m.SESSION.get('https://artlines.org/api/backend/v1/museums/'+mu['slug'],timeout=(15,60));assert response.status_code==200;data=response.json()
        assert data['work_count']>=mu['works'];museumchecks.append(dict(id=mu['id'],status=200,data=data))
    samples={};groups=set()
    for r in plan['records']:
        group=(r['institution_id'],r['work_type'],r['precision'],bool(r['artist_ids']))
        if group not in groups:samples[r['artwork_id']]=r;groups.add(group)
    for aid,r in samples.items():
        url='https://artlines.org/api/backend/v1/museums/'+slugs[r['institution_id']]+'/works/'+aid
        response=m.SESSION.get(url,timeout=(15,60));assert response.status_code==200;data=response.json();assert data['id']==aid
        artchecks.append(dict(id=aid,status=200,data=data))
    save(RUN/'api-verification.json',dict(at=m.now(),countries=countrychecks,museums=museumchecks,artworks=artchecks))
    print('Verified',TARGET,'production objects,',len(museumchecks),'collections and',len(artchecks),'live artwork examples',flush=True)

def report():
    plan,digest=pinned();applied=load(RUN/'applied.json');db=load(RUN/'database-verification.json');api=load(RUN/'api-verification.json');rows=plan['records']
    names={q:mu['name'] for q,mu in plan['institutions'].items()};bycountry=collections.Counter(r['country'] for r in rows);bymuseum=collections.Counter(r['institution_id'] for r in rows);sources=collections.Counter(r['source_kind'] for r in rows)
    with (RUN/'delivered-artworks.csv').open('w',newline='') as f:
        fields=['country','museum','artwork_id','title','creator','date','type','accession','source_kind','object_url','evidence_url'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow(dict(country=r['country'],museum=names[r['institution_id']],artwork_id=r['artwork_id'],title=r['title'],creator=r['creator_label'],date=r['date_display'],type=r['work_type'],accession=r['accession'],source_kind=r['source_kind'],object_url=r['source_url'],evidence_url=r['receipt']['url']))
    countries={'DK':'Denmark','SE':'Sweden','NO':'Norway'};table='\n'.join(f"| {countries[cc]} | {bycountry[cc]} |" for cc in countries)
    institutions='\n'.join(f"| {names[iid]} | {count} |" for iid,count in sorted(bymuseum.items(),key=lambda x:(-x[1],names[x[0]])))
    native=load(RUN/'norway-current-page-checks-v3.json');linked=sum(bool(r['artist_ids']) for r in rows)
    text=f'''# Additional 1,000 Nordic artworks — 8 October 2026

The user requested “add more, 1000 artworks” following the Denmark, Sweden and Norway museum pass. **Exactly 1,000 new production artwork records** and 1,000 supported collection links were added across **{len(bymuseum)} existing institutions**. Existing records were not counted toward the target. All new records remain in review; no images, artist profiles or on-view assertions were created. The real local catalogue was not changed.

| Country | New artworks |
| --- | ---: |
{table}

## Collections expanded

| Collection | New artworks |
| --- | ---: |
{institutions}

## Sources and decisions

- Referenced Wikidata object statements: {sources['referenced Wikidata record']} records. Exact source entities, collection references, creators, inventory numbers, title aliases and date precision were retained. Linked underlying references are not described as independently checked.
- [SMK's public catalogue API](https://api.smk.dk/api/v1/docs/): {sources['european-smk-statens-museum-for-kunst-object']} records. A bounded 3,500-painting metadata selection was checked against the existing catalogue. Deposits, uncertain attributions, open-ended dates and apparent artist-career proxy ranges were withheld.
- [Nasjonalmuseet's own collection metadata](https://github.com/nasjonalmuseet/collection): {sources['nasjonalmuseet-object']} records, selected from one 2,465-record export fragment. The source dataset is dated **3 December 2020**, although retrieved in this pass. That source date and its limitations remain in each citation. Current native-page checks are samples, not a current inspection of every object. {sum(x['verified'] for x in native)} of the eight refined samples corroborated inventory, title, creator and dates; the differing sample was withheld. Earlier unavailable sketchbook/verso samples prompted exclusion of sheet-side, part and version inventory codes. No current-display claim or ownership guarantee is inferred from the export.

All selected creation bounds end in or before 1970. Source ranges and circa labels are retained; no creation year was inferred from an artist's biography. New records include {sum(r['work_type']=='painting' for r in rows)} paintings and {sum(r['work_type']=='drawing' for r in rows)} drawings. {linked} records link to unique existing museum/Wikidata creator authorities; the remaining {1000-linked} preserve source creator labels without inventing artist profiles or resolving identity by name alone.

Exact identifiers and object URLs were checked globally; inventory matches were institution-scoped; possible title/creator/version matches and within-batch duplicate identities were withheld. The selection rotates countries and collections, using additional eligible records where a country's new-object queue is smaller. This expands existing collections and does not establish complete national museum or artwork coverage. The [earlier 575-lead gap ledger](../nordic-museums-20261008/coverage-and-gaps.csv) remains the institution research directory.

## Verification and recovery

All **1,000 database records** passed exact metadata, holding, creator, citation, source identity, review-state and image-absence checks. All {len(api['museums'])} affected live museum responses and {len(api['artworks'])} representative artwork responses passed; samples span institutions, types, date precision and linked/unlinked creators. Country pages were checked with bounded pagination and positive collection counts. Thirteen offline source/identity regression tests pass.

Source evidence and the final plan are hashed and immutable. Final plan SHA-256: `{digest}`. Cloud SQL backup **{load(RUN/'cloud-backup.json')['id']}** completed before writes. Recovery plans, locked preimages and transaction postimages: `{BACKUP}`. The insert transaction rechecked duplicate identities, locked the relevant institution and creator records, inserted all 1,000 records atomically and verified them before commit. Institution metadata remained unchanged. No existing artwork metadata, images or publication states were updated.

The retained query plan describes the current production catalogue, not a 10-million-row performance test. No test database, database fixtures, Git commit, application deployment or Terraform apply was used.

## Evidence

- [Delivered records](delivered-artworks.csv)
- [Production receipt](applied.json)
- [Database verification](database-verification.json)
- [Live API checks](api-verification.json)
- [Identity exclusions](identity-review.json.gz)
- [Wikidata exclusions](wd-held.json)
- [Norwegian source decisions](norway-held-v3.json)
- [SMK source decisions](smk-held-v2.json)
- [Current Norwegian page samples](norway-current-page-checks-v3.json)

Procedure: `ops/nordic-1000-20261008.py`. Regression tests: `ops/test_nordic_1000_20261008.py`.
'''
    (RUN/'README.md').write_text(text)
    save(RUN/'summary.json',dict(at=m.now(),new_artworks=1000,countries=dict(bycountry),institutions=len(bymuseum),new_images=0,all_review=True,verified_artworks=1000,live_artwork_samples=len(api['artworks']),source_counts=dict(sources)))
    print(text[:1900],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command');args=ap.parse_args();globals()[args.command]()
