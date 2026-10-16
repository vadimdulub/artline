#!/usr/bin/env python3
"""Selected, source-backed South American collection expansion; production only."""
import argparse,collections,concurrent.futures,gzip,importlib.util,json,re,threading,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup

def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=module('prior_campaign','switzerland-southern-cone-1000-20261011.py');d=c.d
PREVIOUS=c.RUN;OLD=c.OLD
OP='south-america-1000-20261011';RUN=d.ROOT/'docs/research'/OP
d.OP=OP;d.RUN=RUN;d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
d.DESCRIPTION='Before additional 1000 South America artworks 20261011'
d.AUTHORIZATION='User: try to cover all South America; add at least 1000 new distinct artworks, beyond earlier deliveries.'
d.CITATION_FIELD='south_america_museum_coverage_20261011'
c.r.RUN=c.r.b.RUN=RUN
for provider in ['brazil-masp','chile-surdoc','colombia-banrep','ecuador-national','peru-mali','suriname-stedelijk','guyana-national','bolivia-decree','french-guiana-pop']:
    d.SCHEMES[provider]=['museum-native-'+provider]
d.SCHEMES['venezuela-wikiart']=['wikiart-native-id']
d.SCHEMES['venezuela-mppc']=['venezuela-mppc-collection-caption']
COUNTRIES=dict(AR='Argentina',BO='Bolivia',BR='Brasil',CL='Chile',CO='Colombia',EC='Ecuador',GY='Guyana',PY='Paraguay',PE='Perú',SR='Suriname',UY='Uruguay',VE='Venezuela')
ORIGINS=[PREVIOUS,OLD,c.SWISS]
LOCKS=collections.defaultdict(threading.Lock);LAST={}

def capture(url,params=None):
    prepared=c.r.b.requests.Request('GET',url,params=params).prepare().url
    key=d.sha(prepared.encode());host=urlsplit(prepared).hostname;dest=RUN/'captures'/(key+'.json.gz')
    with LOCKS[host]:
        if not dest.exists():
            for origin in ORIGINS:
                prior=origin/'captures'/(key+'.json.gz')
                if prior.exists():
                    rc=d.load(prior);raw=gzip.decompress(prior.with_name(key+'.body.gz').read_bytes());assert d.sha(raw)==rc['sha256']
                    d.save(dest,rc);dest.with_name(key+'.body.gz').write_bytes(gzip.compress(raw,mtime=0));break
            if not dest.exists():
                for origin in ORIGINS:
                    assert not(origin/'access-holds'/(host+'.json')).exists(),'Earlier provider access hold: '+host
                if host=='upload.wikimedia.org':raise AssertionError('Earlier Commons media HTTP 429 hold')
                if host=='sammlung.kunstmuseumbasel.ch' and '/multimedia/' in prepared:raise AssertionError('Earlier Basel image HTTP 403 hold')
        if dest.exists():
            rc=d.load(dest);raw=gzip.decompress(dest.with_name(key+'.body.gz').read_bytes())
            assert d.sha(raw)==rc['sha256'] and rc['status']==200,(prepared,rc['status'])
            return raw,rc
        time.sleep(max(0,LAST.get(host,0)+.4-time.monotonic()))
        raw,rc=c.r.b.capture(url,params);LAST[host]=time.monotonic()
        assert rc['status']==200,(prepared,rc['status'])
        return raw,rc

def boot():
    d.save(RUN/'authorization.json',dict(at=d.now(),instruction=d.AUTHORIZATION,countries=COUNTRIES,additional_territory_research=['French Guiana'],minimum_new_artworks=1000,earlier_batches_excluded=True,target='production',metadata_cutoff=1970,image_cutoff=1955,new_status='review',local_database_connections=0))
    with d.connect() as db:
        inst=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i')]
        places=list(db.execute('SELECT id::text,name,normalized_name,country_code FROM places WHERE country_code=ANY(%s)',(list(COUNTRIES),)))
        countries=list(db.execute('SELECT * FROM countries WHERE code=ANY(%s)',(list(COUNTRIES),)))
        ids=[x['id'] for x in inst if x['place_id'] in {p['id'] for p in places}]
        counts=list(db.execute("SELECT current_institution_id::text id,count(*) n,count(primary_media_id) images FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id",(ids,)))
    d.save(RUN/'production-baseline.json.gz',dict(at=d.now(),institutions=inst,places=places,countries=countries,counts=counts))
    print('Baseline',len(inst),'institutions;',len(ids),'placed in South America',flush=True)

def probe(url):
    path=RUN/'discovery'/(d.sha(url.encode())+'.json.gz')
    if path.exists():return d.load(path)
    try:
        raw,rc=capture(url);p=BeautifulSoup(raw,'html.parser')
        result=dict(url=url,evidence=rc,title=p.title.get_text(' ',strip=True) if p.title else '',text=p.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in p.select('a[href]')],scripts=[urljoin(url,s['src']) for s in p.select('script[src]')],iframes=[urljoin(url,i['src']) for i in p.select('iframe[src]')])
    except Exception as e:result=dict(url=url,error=str(e))
    d.save(path,result);return result

def directory(country):
    name=COUNTRIES[country];raw,tr=capture('https://www.rmiberoamericanos.org/Busqueda/GetJsTree3Data');tree=json.loads(raw)
    match=[x for x in tree if d.norm(x['text'])==d.norm(name)]
    if not match:
        d.save(RUN/country/'directory-gap.json',dict(country=country,reason='Country absent from Ibermuseos country tree; native directory research required',evidence=tr));return
    cid=match[0]['id'];rows={};receipts=[tr];expected=None
    for number in range(1,501):
        url=f'https://www.rmiberoamericanos.org/Busqueda/IndexFilterTree?searchString=&searchStringTree={cid}&page={number}'
        raw,rc=capture(url);p=BeautifulSoup(raw,'html.parser');total=int(p.select_one('#hdNumRegistros')['value'])
        if expected is None:expected=total
        assert total==expected;receipts.append(rc)
        for card in p.select('.ficha'):
            key=card.select_one('.ficha__link[id]')['id'].split('_')[1];assert key not in rows
            fields={}
            for strong in card.select('strong'):
                value=strong.get_text(' ',strip=True);label=strong.parent.get_text(' ',strip=True).removesuffix(value).strip().rstrip(':');fields[label]=value
            assert d.norm(fields['País'])==d.norm(name)
            rows[key]=dict(directory_id=key,name=card.select_one('h2 a').get_text(' ',strip=True),country=country,locality=fields.get('Ciudad'),fields=fields,directory_url='https://www.rmiberoamericanos.org/Busqueda/DetalleByID?id='+key,native_websites=[],evidence=rc,object_coverage='Individual object evidence pending; directory entry is not artwork coverage')
        if number%10==0 or len(rows)==expected:print(country,'directory',len(rows),'/',expected,flush=True)
        if len(rows)==expected:break
    assert len(rows)==expected
    d.save(RUN/country/'directory.json.gz',dict(country=country,records=list(rows.values()),sources=receipts,scope='Exhausted this public registry country filter; entries may overlap other sources and completeness is not established.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['boot','backup','apply','probe','directory']);p.add_argument('value',nargs='?');a=p.parse_args()
    if a.action=='probe':print(json.dumps(probe(a.value),ensure_ascii=False)[:14000])
    elif a.action=='apply':d.apply(a.value)
    elif a.action=='backup':d.backup()
    elif a.action=='directory':directory(a.value)
    else:boot()
