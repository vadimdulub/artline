#!/usr/bin/env python3
"""Additional, selected museum objects and authentic images; production only.

Public collection records are captured before selection. Image requests follow
selection, per-file rights checks and reconciliation against the live catalogue.
"""
import argparse, collections, concurrent.futures, gzip, importlib.util, json, re, threading, time
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

def module(name, file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

d=module('delivery1000','switzerland-southern-cone-delivery-20261011.py')
r=module('research1000','switzerland-southern-cone-research-20261011.py')
OLD=d.RUN
SWISS=d.ROOT/'docs/research/switzerland-india-museums-20261011'
OP='switzerland-southern-cone-1000-20261011'
RUN=d.ROOT/'docs/research'/OP
d.OP=OP;d.RUN=RUN;d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
d.DESCRIPTION='Before additional 1000 Switzerland southern-cone artworks 20261011'
r.RUN=r.b.RUN=RUN
d.SCHEMES['swiss-basel']=['museum-native-swiss-basel']
d.SCHEMES['swiss-rietberg']=['museum-native-swiss-rietberg']
d.SCHEMES['paraguay-mnba-portal']=['paraguay-mnba-portalguarani-object']
LOCKS=collections.defaultdict(threading.Lock)
LAST={}
BASEL='https://sammlung.kunstmuseumbasel.ch'

def capture(url,params=None):
    prepared=r.b.requests.Request('GET',url,params=params).prepare().url
    key=d.sha(prepared.encode());host=urlsplit(prepared).hostname
    # Reuse exact captured bytes; do not bypass previous provider restrictions.
    dest=RUN/'captures'/(key+'.json.gz')
    if not dest.exists():
        for origin in [OLD,SWISS]:
            prior=origin/'captures'/(key+'.json.gz')
            if prior.exists():
                receipt=d.load(prior);body=gzip.decompress(prior.with_name(key+'.body.gz').read_bytes())
                assert d.sha(body)==receipt['sha256']
                d.save(dest,receipt);dest.with_name(key+'.body.gz').write_bytes(gzip.compress(body,mtime=0));break
        if not dest.exists():
            for origin in [OLD,SWISS]:
                held=origin/'access-holds'/(host+'.json')
                assert not held.exists(), 'Earlier source access hold: '+host
    with LOCKS[host]:
        time.sleep(max(0,LAST.get(host,0)+.35-time.monotonic()))
        result=r.b.capture(url,params);LAST[host]=time.monotonic()
    assert result[1]['status']==200,(url,result[1]['status'])
    return result

def boot():
    d.save(RUN/'authorization.json',dict(user_instruction='add 1000 artworks for this counteis and images',
        countries=['CH','AR','UY','PY'],new_artwork_target=1000,target='production',
        interpretation='One thousand additional distinct museum-connected artworks in total, across the four requested countries; authentic selected images. Earlier 176 additions do not count toward this batch.',
        local_database='No connection or mutations',new_status='review',metadata_cutoff=1970,image_cutoff=1955,
        safeguards=['Exact object/version reconciliation','Actual source rights and creator qualifiers retained','No current-display inference','No placeholder objects','Source selection before image downloading']))
    registry={}
    for p in [OLD/'institution-registry.json',*sorted(OLD.glob('institution-registry-wave*.json'))]:registry.update(d.load(p))
    registry.update(d.load(OLD/'institution-identity-crosswalk.json')) if False else None
    with d.connect() as db:
        institutions=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i')]
    d.save(RUN/'institution-baseline.json.gz',institutions)
    basel=[x for x in institutions if d.norm(x['name'])=='kunstmuseum basel' and not x['canonical_institution_id']]
    assert len(basel)==1,[(x['name'],x['id']) for x in basel]
    registry['Kunstmuseum Basel']=dict(slug=basel[0]['slug'],website=basel[0]['website_url'] or BASEL,country='CH',city='Basel')
    d.save(RUN/'institution-registry.json',registry)
    print('Bootstrapped',len(institutions),'production institutions; Basel',basel[0]['id'],flush=True)

def basel_index():
    records=[];receipts=[]
    for start in range(0,6000,200):
        raw,receipt=capture(BASEL+'/solr/published/select',dict(q='type:Object',fq='ObjSearchDateFromNum_de_ss:[1000 TO 1955]',rows=200,start=start,sort='id asc',wt='json'))
        data=json.loads(raw)['response'];records.extend(data['docs']);receipts.append(receipt)
        print('Basel metadata',len(records),'/',data['numFound'],flush=True)
        if len(data['docs'])<200:break
    assert len({x['oid'] for x in records})==len(records)
    d.save(RUN/'CH/index-v2.json.gz',dict(records=records,receipts=receipts,available=data['numFound'],
        scope='Bounded first 6000 dated native object identifiers. Metadata only, before image selection.'))

def label(item,key):
    value=item.get(key,{})
    return value.get('LabelTxt') or value.get('LabelTxt_en') or '' if isinstance(value,dict) else ''

def date_bounds(text):
    text=text.strip()
    # Conservative explicit years and ranges; no source sort-number or lifespan fallback.
    if not re.fullmatch(r'(?:(?:um|ca\.?|circa|vor|nach)\s+)?\d{4}(?:\s*[-–/]\s*\d{2,4})?(?:\s*\?)?',text,re.I):return None
    if re.match(r'(vor|nach)\b',text,re.I):return None
    years=re.findall(r'\d{2,4}',text);lo=int(years[0]);hi=int(years[-1])
    if len(years)>1 and len(years[-1])==2:hi=lo//100*100+hi
    return (lo,hi) if 1000<=lo<=hi<=1955 else None

def basel_objects(limit):
    idx=d.load(RUN/'CH/index-v2.json.gz');registry=d.load(RUN/'institution-registry.json');slug=registry['Kunstmuseum Basel']['slug']
    with d.connect() as db:
        institution=db.execute('SELECT id::text FROM institutions WHERE slug=%s',(slug,)).fetchone()['id']
        existing=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=%s',(institution,))]
        ext=[x for x in db.execute("SELECT scheme,external_id,entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (scheme='museum-native-swiss-basel' OR entity_id=ANY(%s::uuid[]))",([x['id'] for x in existing],))]
    d.save(RUN/'CH/catalogue-baseline.json.gz',dict(institution_id=institution,artworks=existing,identifiers=ext))
    inventories={d.norm(x['accession_number']) for x in existing if x['accession_number']}
    bycreator=collections.defaultdict(list)
    leads=[];held=[]
    for x in idx['records']:
        acc=x.get('ObjListInvTxt_de_s','');title=x.get('ObjListTitleTxt_de_s','');date=x.get('ObjListDateTxt_de_s','')
        reason=None
        if d.norm(acc) in inventories:reason='Existing museum inventory'
        elif not acc or not title or not x.get('img_s'):reason='Missing inventory, title or native image'
        elif not date_bounds(date):reason='Date not in explicit image-eligible range'
        elif re.search(r'\b(verso|rückseite|rueckseite)\b',title,re.I):reason='Reverse or related physical-object view requires separate reconciliation'
        if reason:held.append(dict(id=x['oid'],reason=reason));continue
        bycreator[x.get('ObjListArtistTxt_de_s','')].append(x)
    # Broad creator selection avoids letting a single large portfolio dominate.
    for n in range(max(map(len,bycreator.values()),default=0)):
        for creator,items in sorted(bycreator.items()):
            if n<len(items):leads.append(items[n])
    d.save(RUN/'CH/metadata-selection.json.gz',dict(records=leads[:limit],held=held,policy='Explicit native creation dates <=1955, inventory deduplication and round-robin creator breadth. Details and rights checked next.'))
    def one(x):
        path=RUN/'CH/objects'/(x['oid']+'.json.gz')
        if path.exists():return d.load(path)
        url=BASEL+'/de/collection/item/'+x['oid']+'/'
        try:
            raw,rc=capture(url);soup=BeautifulSoup(raw,'html.parser');item=json.loads(soup.select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item']
            assert str(item['Id'])==x['oid']
            result=dict(index=x,item=item,evidence=rc)
        except Exception as error:result=dict(index=x,error=str(error)[:300])
        d.save(path,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n,out in enumerate(pool.map(one,leads[:limit]),1):
            if n%100==0:print('Basel objects',n,'/',min(limit,len(leads)),flush=True)

def neuquen_objects():
    rows=d.load(RUN/'AR/neuquen-index.json.gz')['records']
    def one(x):
        path=RUN/'AR/objects'/(d.sha(x['url'].encode())+'.json.gz')
        if path.exists():return
        try:
            raw,rc=capture(x['url']);p=BeautifulSoup(raw,'html.parser')
            value=dict(index=x,evidence=rc,html=str(p))
        except Exception as e:value=dict(index=x,error=str(e)[:300])
        d.save(path,value)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n,_ in enumerate(pool.map(one,rows),1):
            if n%25==0:print('Neuquén objects',n,'/',len(rows),flush=True)

def paraguay_objects():
    rows=d.load(RUN/'PY/object-links-v2.json.gz')
    for n,x in enumerate(rows,1):
        path=RUN/'PY/objects'/(d.sha(x['url'].encode())+'.json.gz')
        if path.exists():continue
        try:
            raw,rc=capture(x['url']);p=BeautifulSoup(raw,'html.parser')
            value=dict(index=x,evidence=rc,html=str(p),text=p.get_text(' ',strip=True))
        except Exception as e:value=dict(index=x,error=str(e)[:300])
        d.save(path,value)
        if n%10==0:print('Paraguay objects',n,'/',len(rows),flush=True)

def source_plan(country,tag,phase,limit):
    records=d.load(RUN/country/(tag+'-facts.json.gz'))['records']
    artist_ids=sorted({x.get('verified_artist_id') for x in records if x.get('verified_artist_id')})
    with d.connect() as db:
        existing=list(db.execute("SELECT aa.artist_id::text,to_jsonb(a) artwork FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'",(artist_ids,))) if artist_ids else []
    byartist=collections.defaultdict(list)
    for x in existing:byartist[x['artist_id']].append(x['artwork'])
    for row in records:
        titles={d.norm(row['title'])}
        if country=='CH':
            for v in row['raw']['native'].get('ObjSearchTitleTxt',[]):
                titles.update(d.norm(v[k]) for k in v if k.startswith('LabelTxt'))
        possible=[]
        for a in byartist[row.get('verified_artist_id')]:
            if d.norm(a['title']) not in titles and d.norm(a.get('alternate_title')) not in titles:continue
            if row.get('accession_number') and a.get('accession_number') and d.norm(row['accession_number'])==d.norm(a['accession_number']):
                possible.append(a);continue
            if a['creation_year_start'] is not None and (a['creation_year_start']>row['year_end'] or a['creation_year_end']<row['year_start']):continue
            # Same-title paintings without an independent inventory and generic
            # unplaced records are unresolved versions, not automatically new objects.
            if not a.get('accession_number') and (a['current_institution_id'] is None or row['source_type']=='painting'):possible.append(a)
        if possible:row['editorial_hold']='Creator-scoped same-title/date or exact-inventory candidates require physical-object reconciliation';row['local_matches']=possible
    d.save(RUN/(phase+'-candidates')/'source-records.json.gz',records)
    d.plan(phase+'-candidates')
    pool,_=d.pinned(phase+'-candidates')
    new=[r for r in pool['records'] if not r['before']]
    assert len(new)>=limit,('Not enough distinct new records',len(new),limit)
    selected=[]
    for row in new[:limit]:
        # Return only source facts; final plan rechecks current production state.
        selected.append(next(x for x in records if x['provider']==row['provider'] and x['source_id']==row['source_id']))
    d.save(RUN/phase/'source-records.json.gz',selected);d.plan(phase)
    final,_=d.pinned(phase);assert len(final['records'])==limit and all(not x['before'] for x in final['records'])
    d.save(RUN/phase/'selection-audit.json.gz',dict(country=country,target_new=limit,candidate_count=len(records),
        candidate_plan_sha256=d.load(RUN/(phase+'-candidates')/'plan-pin.json')['sha256'],
        creator_scoped_existing=existing,policy='Excluded existing objects and unresolved same-work/version candidates; final plan freshly reconciled before production delivery.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['boot','basel_index','basel_objects','neuquen_objects','paraguay_objects','source_plan','apply']);p.add_argument('--limit',type=int,default=1600);p.add_argument('--country');p.add_argument('--tag');p.add_argument('--phase');a=p.parse_args()
    if a.action=='basel_objects':basel_objects(a.limit)
    elif a.action=='source_plan':source_plan(a.country,a.tag,a.phase,a.limit)
    elif a.action=='apply':d.apply(a.phase)
    else:globals()[a.action]()
