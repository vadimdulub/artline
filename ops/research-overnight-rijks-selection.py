#!/usr/bin/env python3
"""Discover additional eligible Rijksmuseum paintings through its public API.

Metadata only: source rights and exact creator authorities precede any image
selection. Separate image download and catalogue import require a reviewed plan.
"""
import argparse,collections,concurrent.futures,importlib.util,json,re,time,uuid
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('rijks',ROOT/'ops/overnight-rijks-images.py');rijks=importlib.util.module_from_spec(s);s.loader.exec_module(rijks);core=rijks.core

def verify(oid,o,artists):
    parts=o.get('produced_by',{}).get('part',[])
    if len(parts)!=1:raise ValueError('Multipart or missing production requires review')
    makers=parts[0].get('carried_out_by',[])
    if len(makers)!=1 or makers[0].get('type')!='Person':raise ValueError('Single named creator authority unavailable')
    person=makers[0];pid=person.get('id','').removeprefix('https://id.rijksmuseum.nl/')
    if not re.fullmatch(r'\d+',pid):raise ValueError('Museum person identity missing')
    qids={x.get('id','').rstrip('/').rsplit('/',1)[-1] for x in person.get('equivalent',[]) if 'wikidata.org/' in x.get('id','')}
    people={x['id']:x for q in qids for x in artists.get(('wikidata',q),[])}
    people.update({x['id']:x for x in artists.get(('rijks-person',pid),[])})
    if len(people)!=1:raise ValueError('Existing creator authority absent or ambiguous')
    artist=next(iter(people.values()))
    if o.get('part_of') or o.get('part'):raise ValueError('Separate parts require object relationship review')
    names=[x for x in o.get('identified_by',[]) if x.get('type')=='Name' and x.get('content')]
    preferred=[x['content'] for x in names if any(l.get('id')=='http://vocab.getty.edu/aat/300388277' for l in x.get('language',[]))]
    titles=preferred or [x['content'] for x in names]
    if not titles:raise ValueError('Source title missing')
    accessions={x.get('content') for x in o.get('identified_by',[]) if x.get('type')=='Identifier' and any(t.get('id')=='http://vocab.getty.edu/aat/300312355' for t in x.get('classified_as',[]))}
    if len(accessions)!=1:raise ValueError('Museum accession missing or ambiguous')
    span=o.get('produced_by',{}).get('timespan',{})
    lo=span.get('begin_of_the_begin','');hi=span.get('end_of_the_end','')
    if not re.match(r'^\d{4}-',lo) or not re.match(r'^\d{4}-',hi):raise ValueError('Creation bounds absent')
    lo,hi=int(lo[:4]),int(hi[:4]);date_names=[x.get('content','') for x in span.get('identified_by',[]) if x.get('type')=='Name']
    texts=[d for d in date_names if re.fullmatch(r'(?:(?:c\.|ca\.|circa|about)\s*)?\d{4}(?:\s*[-–—/]\s*\d{4})?',d,re.I)]
    if not texts:raise ValueError('Unknown or open creation date wording')
    text=texts[0];approx=bool(re.match(r'(?:c\.|ca\.|circa|about)',text,re.I));precision=('circa' if lo==hi else 'circa_range') if approx else ('exact' if lo==hi else 'range')
    if artist.get('birth_year')==lo and artist.get('death_year')==hi and lo!=hi:raise ValueError('Source creation interval repeats creator lifespan')
    aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-rijks/'+oid))
    c={'artwork_id':aid,'slug':'night-rijks-'+oid,'external_id':oid,'scheme':'rijks-object','provider':'night-rijks','title':titles[0],
       'alternate_titles':sorted(set(x['content'] for x in names)-{titles[0]}),'accession_number':next(iter(accessions)),
       'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'date_display':text,'work_type':'painting',
       'artist':artist['display_name'],'artist_id':artist['id'],'artist_slug':artist['slug'],'artist_qids':sorted(qids),'rijks_people':[pid],'roles':['primary'],'popular':artist['popular'],
       'object':o,'target_ids':{'local':aid}}
    rijks.source_match(c,o)
    return c

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    with rijks.ro('postgres://localhost/artline') as db:
        people=db.execute("""SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year,e.scheme,e.external_id,
          EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=p.id AND d.is_popular) popular
          FROM artists p JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=p.id WHERE p.status<>'archived' AND e.scheme IN ('wikidata','rijks-person')""").fetchall()
        existing={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='rijks-object'").fetchall()}
    artists=collections.defaultdict(list)
    for row in people:artists[(row['scheme'],row['external_id'])].append(row)
    fetcher=core.Fetcher(a.run/'discovery');ids=[];url='https://data.rijksmuseum.nl/search/collection?type=painting&imageAvailable=true';seen=set();total=None
    while url:
        if time.time()>=a.deadline:return
        if url in seen or urlparse(url).hostname!='data.rijksmuseum.nl':raise ValueError('Unsafe or repeating source pagination')
        seen.add(url);page=fetcher.metadata(url);total=page.get('partOf',{}).get('totalItems');ids.extend(x['id'].removeprefix('https://id.rijksmuseum.nl/') for x in page.get('orderedItems',[]));url=page.get('next',{}).get('id')
    if len(ids)!=len(set(ids)) or len(ids)!=total:raise ValueError('Source pagination changed or incomplete')
    core.save_new(a.run/'painting-search-inventory.json',{'count':total,'object_ids':ids,'pages':len(seen),'query':'type=painting&imageAvailable=true'})
    pending=[oid for oid in ids if oid not in existing and not (a.run/'verified'/(oid+'.json')).exists() and not (a.run/'review-held'/(oid+'.json')).exists()];counts=collections.Counter()
    print(core.now(),'Rijksmuseum additional painting metadata to inspect',len(pending),'of',total,flush=True)
    def stripe(rows):
        f=core.Fetcher(a.run/'fresh-api')
        for oid in rows:
            if time.time()>=a.deadline:return
            try:
                if not re.fullmatch(r'\d+',oid):raise ValueError('Invalid source identifier')
                url='https://data.rijksmuseum.nl/'+oid+'?_profile=la-framed';o=f.metadata(url);c=verify(oid,o,artists);c['metadata_capture']=json.loads((f.cache/(core.sha(url.encode())+'.receipt.json')).read_text());core.save_new(a.run/'verified'/(oid+'.json'),c);outcome='verified_metadata'
            except ValueError as e:core.save_new(a.run/'review-held'/(oid+'.json'),{'at':core.now(),'object_id':oid,'reason':str(e)});outcome='needs_review'
            except Exception as e:
                with (a.run/'api-errors.jsonl').open('ab') as log:log.write(core.encode({'at':core.now(),'object_id':oid,'error':str(e)[:250]})+b'\n')
                outcome='api_error'
            with core.LOCK:
                counts[outcome]+=1
                if sum(counts.values())%100==0:print(core.now(),'Rijks source metadata reviewed',sum(counts.values()),'of',len(pending),dict(counts),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for task in [pool.submit(stripe,pending[n::3]) for n in range(3)]:task.result()
    print(core.now(),'Rijks source metadata pass complete',dict(counts),flush=True)
if __name__=='__main__':main()
