#!/usr/bin/env python3
"""Reproducible production sample and evidence-preserving museum research."""
import argparse, collections, gzip, hashlib, importlib.util, json, secrets, re, time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
d=module('location_delivery','ops/apply-artwork-locations-20261004.py');r=d.r
RUN=ROOT/'docs/research/random-5000-museums-20261006'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/random-5000-museums-20261006'
r.PORT=55482

def sample():
    assert not(RUN/'sample.json').exists(),'Preserve frozen sample'
    seed=secrets.token_hex(32)
    query="""SELECT a.id::text FROM artworks a WHERE a.status<>'archived'
      AND a.current_institution_id IS NULL AND NOT EXISTS (
        SELECT 1 FROM artwork_location_assertions h WHERE h.artwork_id=a.id
        AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL)
      ORDER BY a.id"""
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        plan=db.execute('EXPLAIN (FORMAT JSON) '+query).fetchone()
        frame=[x['id']for x in db.execute(query)]
        assert len(frame)>=5000
        ranked=sorted(frame,key=lambda aid:(hashlib.sha256((seed+'/'+aid).encode()).digest(),aid));ids=ranked[:5000]
        r.save_gz(RUN/'sampling-frame.json.gz',frame)
        records={};citations={};artist_ids=set()
        for offset in range(0,len(ids),500):
            batch=ids[offset:offset+500];records.update(d.snapshots(db,batch))
            for row in db.execute("SELECT entity_id::text,array_agg(DISTINCT source_url) urls FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) GROUP BY entity_id",(batch,)):citations[row['entity_id']]=row['urls']
            print('Frozen sample details',offset+len(batch),'/ 5000',flush=True)
        for x in records.values():artist_ids.update(y['artist_id']for y in x['creators'])
        artists={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artists a WHERE id=ANY(%s::uuid[])',(list(artist_ids),))}
        artist_identifiers=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])",(list(artist_ids),)).fetchall()
        institutions=[x['data']for x in db.execute("SELECT to_jsonb(i) data FROM institutions i WHERE status<>'archived'")]
    r.save_gz(RUN/'baseline.json.gz',records);r.save_gz(RUN/'citation-urls.json.gz',citations)
    r.save_gz(RUN/'artists.json.gz',{'artists':artists,'identifiers':artist_identifiers});r.save_gz(RUN/'institutions.json.gz',institutions)
    receipt={'at':r.now(),'target':'production','eligible_population':len(frame),'selected':5000,'seed':seed,'algorithm':'Smallest 5,000 SHA-256(seed + slash + artwork UUID) values over the complete eligible UUID frame; uniform unweighted pseudorandom selection without replacement.','eligibility':'Non-archived records with no current institution and no active accepted holding assertion. Unknown dates, creator labels and non-museum provenance do not exclude a row from research.','artwork_ids':ids,'sampling_frame_sha256':r.sha((RUN/'sampling-frame.json.gz').read_bytes()),'baseline_sha256':r.sha((RUN/'baseline.json.gz').read_bytes()),'local_database_writes':0,'publication_authorized':False}
    r.save(RUN/'sample.json',receipt);r.save(RUN/'sampling-query-plan.json',plan)
    sample_report()

def sample_report():
    receipt=r.load(RUN/'sample.json');ids=receipt['artwork_ids'];records=r.load(RUN/'baseline.json.gz');population=receipt['eligible_population']
    stats={'at':receipt['at'],'population':population,'sample':5000,'with_images':sum(bool(x['artwork']['primary_media_id'])for x in records.values()),'external_identifier_schemes':dict(collections.Counter(e['scheme']for x in records.values()for e in x['identifiers'])),'statuses':dict(collections.Counter(x['artwork']['status']for x in records.values())),'location_labels':dict(collections.Counter(x['artwork']['current_location_text']or '[not supplied]'for x in records.values()).most_common(25))}
    r.save(RUN/'sample-summary.json',stats)
    md='# Random 5,000 artworks: museum research\n\nFrozen production sample: '+str(population)+ ' eligible artworks; 5,000 chosen without replacement. The seed, complete eligible UUID frame and baseline are preserved. No weighting by artist, country, existing images or likelihood of a museum match.\n\nResearch will distinguish museum holdings, historical collections, deposits, private collections, copies and ambiguous versions. Existing metadata, dates, images and publication states are preserved. Holding evidence does not establish current display.\n\n| Sample | Artwork | Creator | Existing location text |\n|---|---|---|---|\n'
    def cell(x):return str(x or 'Unknown').replace('|','\\|').replace('\n',' ')
    for n,aid in enumerate(ids,1):
        x=records[aid];a=x['artwork'];md+=f"| {n} | {cell(a['title'])} ({aid}) | {cell('; '.join(y['name']for y in x['creator_keys'])or a.get('unlinked_creator_label'))} | {cell(a['current_location_text'])} |\n"
    (RUN/'selected-5000.md').write_text(md)
    print(json.dumps(stats,ensure_ascii=False),flush=True)

def cached(version=''):
    records=r.load(RUN/'baseline.json.gz');ids=set(records);urls=r.load(RUN/'citation-urls.json.gz');cache={}
    for p in (ROOT/'docs/research').glob('*/capture-cache.json'):
        for url,x in r.load(p).items():
            if url not in cache or x['retrieved_at']>cache[url]['retrieved_at']:cache[url]=x
    old=ROOT/'docs/research/artwork-locations-20261004'
    for p in (old/'wikiart').glob('*.receipt.json'):
        x=r.load(p)
        if x.get('status')==200 and x.get('url')not in cache:cache[x['url']]={'receipt_path':str(p.relative_to(ROOT)),'body_path':x['body_path'],'sha256':x['sha256'],'retrieved_at':x['retrieved_at']}
    selected_urls={}
    for aid,row in records.items():
        values={e['canonical_url']for e in row['identifiers']if e.get('canonical_url')}|set(urls.get(aid,[]))
        selected_urls[aid]=sorted(u for u in values if u and urlsplit(u).hostname=='www.wikiart.org'and len(urlsplit(u).path.strip('/').split('/'))==3)
    # Captures created after an earlier campaign built its cache also count.
    wanted={u for values in selected_urls.values()for u in values}
    folders=[p/name for p in (ROOT/'docs/research').iterdir()if p.is_dir()for name in ['captures','page-captures','artist-link-captures']if(p/name).is_dir()]
    for url in wanted:
        key=r.sha(url.encode())
        for folder in folders:
            path=folder/(key+'.receipt.json')
            if not path.exists():continue
            x=r.load(path);when=x.get('retrieved_at')or x.get('at')or ''
            if x.get('status',x.get('status_code'))==200 and x.get('body_path')and x.get('sha256')and(url not in cache or when>cache[url]['retrieved_at']):cache[url]={'receipt_path':str(path.relative_to(ROOT)),'body_path':x['body_path'],'sha256':x['sha256'],'retrieved_at':when}
    wiki={};counts=collections.Counter()
    for aid,values in selected_urls.items():
        results=[]
        for url in values:
            if url not in cache:continue
            c=cache[url];raw=(ROOT/c['body_path']).read_bytes();raw=gzip.decompress(raw)if c['body_path'].endswith('.gz')else raw
            assert r.sha(raw)==c['sha256']
            soup=BeautifulSoup(raw,'html.parser');info=soup.select_one('.wiki-layout-artwork-info')
            if not info:continue
            fields={}
            for li in info.select('article > ul > li'):
                label=li.find('s')
                if label:key=label.get_text(' ',strip=True).rstrip(':');label.extract();fields[key]=li.get_text(' ',strip=True)
            canonical=soup.find('link',rel='canonical');source_ids=re.findall(r'(?:paintingId|paintingID|ArtworkId)[^a-f0-9]+([a-f0-9]{24})',str(info),re.I)
            results.append({'url':url,'canonical':canonical.get('href')if canonical else None,'title':info.select_one('h1').get_text(' ',strip=True)if info.select_one('h1')else None,'artist':info.select_one('h2').get_text(' ',strip=True)if info.select_one('h2')else None,'fields':fields,'source_ids':list(set(source_ids)),'capture':c})
        wiki[aid]={'artwork_id':aid,'known_wikiart_urls':values,'pages':results}
        counts['with_cached_wikiart_page'if results else 'without_cached_wikiart_page']+=1
        if any(x['fields'].get('Location')for x in results):counts['wikiart_location']+=1
    r.save_gz(RUN/('cached-wikiart-results'+version+'.json.gz'),wiki)
    if version:
        r.save(RUN/('cached-research-summary'+version+'.json'),{'at':r.now(),**dict(counts),'location_labels':dict(collections.Counter(p['fields']['Location']for x in wiki.values()for p in x['pages']if p['fields'].get('Location')))})
        print(json.dumps(dict(counts)),flush=True);return
    inherited=collections.defaultdict(list)
    for path in sorted((old/'primary-plans').glob('*.json.gz')):
        data=r.load(path)
        for name in ['claims','holds']:
            for x in data.get(name,[]):
                if x.get('artwork_id')in ids:inherited[x['artwork_id']].append({'kind':name,'plan_path':str(path.relative_to(ROOT)),'record':x})
    r.save_gz(RUN/'prior-primary-research.json.gz',inherited)
    original=r.load(old/'missing-locations.json.gz');selected={x['artwork']['id']:x for x in original if x['artwork']['id']in ids}
    r.save_gz(RUN/'prior-supplied-records.json.gz',selected)
    r.save(RUN/'cached-research-summary.json',{'at':r.now(),**dict(counts),'prior_primary_research_objects':len(inherited),'prior_supplied_records':len(selected),'location_labels':dict(collections.Counter(p['fields']['Location']for x in wiki.values()for p in x['pages']if p['fields'].get('Location')))})
    print(json.dumps({'wikiart':counts,'prior_primary_research_objects':len(inherited),'prior_supplied_records':len(selected)},ensure_ascii=False),flush=True)

def cached_supplement():cached('-supplement')

def wikidata():
    records=r.load(RUN/'baseline.json.gz');qids=sorted({e['external_id']for x in records.values()for e in x['identifiers']if e['scheme']=='wikidata'and re.fullmatch(r'Q[1-9][0-9]*',e['external_id'])})
    for start in range(0,len(qids),40):
        path=RUN/'wikidata-batches'/f'{start:05}.json'
        if path.exists():continue
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(qids[start:start+40]),'props':'labels|aliases|claims|sitelinks','format':'json'}).prepare().url
        response=requests.get(url,headers={'User-Agent':r.UA},timeout=(15,60));raw=response.content;body=RUN/'wikidata-captures'/f'{start:05}.body.gz'
        rc={'url':url,'status':response.status_code,'retrieved_at':r.now(),'sha256':r.sha(raw),'body_path':str(body.relative_to(ROOT)),'retry_after':response.headers.get('Retry-After')}
        r.save(body,gzip.compress(raw,mtime=0));r.save(body.with_name(body.name.replace('.body.gz','.receipt.json')),rc)
        if response.status_code!=200:
            print('Wikidata capture paused after HTTP',response.status_code,flush=True);return
        data=response.json();assert 'entities'in data;r.save(path,{'receipt':rc,'entities':data['entities']})
        print('Current Wikidata objects',min(start+40,len(qids)),'/',len(qids),flush=True);time.sleep(1.1)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['sample','sample_report','cached','cached_supplement','wikidata']);args=parser.parse_args();globals()[args.command]()
