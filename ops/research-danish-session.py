#!/usr/bin/env python3
"""Bounded official SMK catalogue research; no generated enrichment or images."""
import argparse, collections, hashlib, importlib.util, json, re, time
from pathlib import Path
from urllib.parse import urlencode
import requests, psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-painters-20260913'
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
SCHEME='european-smk-statens-museum-for-kunst-object'

def save(path,data):core.save_new(path,data)
def fetch(path,url):
    if path.exists():return json.loads(path.read_bytes())
    r=requests.get(url,timeout=(15,60));r.raise_for_status()
    if len(r.content)>20_000_000:raise ValueError('Bounded metadata response exceeded')
    data=r.json();save(path,r.content)
    save(path.with_suffix('.snapshot.json'),{'url':url,'retrieved_at':core.now(),'sha256':core.sha(r.content),'bytes':len(r.content)})
    time.sleep(1)
    return data

def capture():
    fetch(RUN/'api-schema.json','https://api.smk.dk/api/v1/swagger.json')
    fetch(RUN/'field-info.json','https://api.smk.dk/api/v1/art/field_info')
    for typ,cap in [('Painting',5000),('Drawing',15000),('Print',5000)]:
        total=None;seen=set();pages=[];captured=0
        for offset in range(0,cap,500):
            query=dict(keys='*',filters=f'[creator_nationality:Danish],[object_names:{typ}]',rows=500,offset=offset,lang='en',sort='object_number',sort_type='asc')
            p=RUN/'captures'/typ.lower()/f'{offset:06d}.json'
            d=fetch(p,'https://api.smk.dk/api/v1/art/search/?'+urlencode(query))
            if total is None:total=d['found']
            assert d['found']==total and d['offset']==offset and d['rows']==500
            ids=[r['id'] for r in d['items']]
            assert len(set(ids))==len(ids) and not seen.intersection(ids),'Pagination source-ID drift'
            seen.update(ids);captured+=len(ids);pages.append(str(p.relative_to(RUN)))
            print(typ,captured,'of',total,'bounded cap',cap,flush=True)
            if offset+len(ids)>=total:break
            assert len(ids)==500
        save(RUN/(typ.lower()+'-capture.json'),{'found':total,'captured':captured,'cap':cap,'pages':pages,'complete':captured==total})

def records(typ):
    m=json.loads((RUN/(typ+'-capture.json')).read_bytes())
    return [r for p in m['pages'] for r in json.loads((RUN/p).read_bytes())['items']]

def audit():
    for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            totals=db.execute('SELECT (SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artists) artists,(SELECT count(*) FROM media_assets) images').fetchone()
            works=db.execute("SELECT e.scheme,e.external_id,e.canonical_url,a.id::text,a.slug,a.title,a.status,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND (e.scheme LIKE '%smk%' OR e.canonical_url LIKE 'https://open.smk.dk/%')").fetchall()
            urls=db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE 'https://open.smk.dk/%'").fetchall()
            accession=db.execute("SELECT a.accession_number FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='statens-museum-for-kunst' AND a.accession_number IS NOT NULL").fetchall()
            artists=db.execute("SELECT a.id::text,a.slug,a.display_name,a.normalized_name,a.birth_year,a.death_year,a.status,e.scheme,e.external_id FROM artists a LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id").fetchall()
            save(RUN/(target+'-before.json'),{'totals':totals,'works':works,'urls':urls,'accessions':accession,'artists':artists})
            print(target,totals,'SMK identities',len(works),flush=True)

def creator(r):
    p=r.get('production',[])
    if len(p)!=1:return None
    c=p[0]
    if not re.fullmatch(r'\d+_person',c.get('creator_lref','')):return None
    if 'Danish' not in [n.strip() for n in c.get('creator_nationality','').split(',')]:return None
    if c.get('creator_role','') not in ('','artist','Painter') or c.get('creator_qualifier'):return None
    if not c.get('creator_surname') or re.search(r'unknown|anonymous|ubekendt|ukendt|unidentified',c.get('creator',''),re.I):return None
    return c

def persons():
    registry={}
    for r in records('painting'):
        c=creator(r)
        if c:registry.setdefault(c['creator_lref'],{'creator':c,'painting_evidence':r['object_url'],'painting_object':r['object_number']})
    save(RUN/'painter-registry.json',registry)
    print('Named Danish-associated painters with actual painting evidence',len(registry),flush=True)
    # Person authority metadata is bounded to creators found in the scoped
    # painting catalogue, not all museum people or every Danish artist.
    existing=[]
    for target in ('local','production'):
        existing.append({r['external_id'] for r in json.loads((RUN/(target+'-before.json')).read_bytes())['artists'] if r['scheme']=='smk-person'})
    needed=set(registry)-(existing[0]&existing[1])
    for i,pid in enumerate(sorted(needed)):
        fetch(RUN/'persons'/(pid+'.json'),'https://api.smk.dk/api/v1/person/?'+urlencode(dict(id=pid,lang='en')))
        if i%50==0:print('additional person authorities',i+1,'/',len(needed),flush=True)

UNCERTAIN=re.compile(r'udateret|virkeår|levetid|baseret på kunstnerens årstal|tilgået museet|unknown|undated|after|before|efter|før|muligvis|tilskrevet',re.I)
def date(r):
    ds=r.get('production_date',[]);notes='; '.join(r.get('production_dates_notes',[]))
    display='; '.join(d.get('period','') for d in ds).strip() or notes or 'Date not established by museum record'
    unknown={'first':None,'last':None,'precision':'unknown'}
    if len(ds)!=1:return unknown,display,'unknown'
    d=ds[0];first=int(d['start'][:4]) if re.match(r'^\d{4}-',d.get('start','')) else None;last=int(d['end'][:4]) if re.match(r'^\d{4}-',d.get('end','')) else None
    if first and first>1970:return None,display,'post_1970'
    if not first or not last or first<1100 or first>last or last>1970 or UNCERTAIN.search(notes+' '+display):return unknown,display,'unknown'
    circa=bool(re.search(r'\bca\.?|circa|\bc\.',notes+' '+display,re.I))
    return {'first':first,'last':last,'precision':('circa' if circa else 'exact') if first==last else ('circa_range' if circa else 'range')},display,'eligible'

def life(person,kind):
    a=person.get(kind+'_date_start',[]);b=person.get(kind+'_date_end',[]);p=person.get(kind+'_date_prec',[])
    if len(a)!=1 or len(b)!=1 or len(p)!=1 or not re.fullmatch(r'(?:\d{1,2}-\d{1,2}-)?\d{4}',p[0]):return None
    if a[0][:4]!=b[0][:4] or not re.match(r'^\d{4}-',a[0]):return None
    return int(a[0][:4])

def plan():
    registry=json.loads((RUN/'painter-registry.json').read_bytes())
    painting={r['object_number']:r for r in records('painting')}
    allrows={r['id']:r for typ in ('painting','drawing','print') for r in records(typ)}
    duplicates={oid for oid,n in collections.Counter(r['object_number'] for r in allrows.values()).items() if n>1}
    existing=set();existing_urls=set()
    for target in ('local','production'):
        audit=json.loads((RUN/(target+'-before.json')).read_bytes())
        existing.update(r['external_id'] for r in audit['works']);existing.update(r['accession_number'] for r in audit['accessions'])
        existing_urls.update(r['source_url'] for r in audit['urls'])
    decisions=[];groups=collections.defaultdict(list)
    for r in allrows.values():
        oid=r['object_number'];c=creator(r);reason=None
        types={x['name'] for x in r.get('object_names',[])}
        typ=next((t.lower() for t in ('Painting','Drawing','Print') if t in types),None)
        d,display,scope=date(r)
        if oid in duplicates:reason='ambiguous_source_accession'
        elif oid in existing or r.get('frontend_url') in existing_urls:reason='already_in_catalogue'
        elif not c:reason='unresolved_nationality_or_attribution'
        elif c['creator_lref'] not in registry:reason='no_painting_evidence_for_creator'
        elif not typ:reason='unsupported_type'
        elif scope=='post_1970':reason='post_1970'
        elif not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9./_-]{0,100}',oid) or '..' in oid:reason='source_identity_review'
        elif r.get('frontend_url')!='https://open.smk.dk/artwork/image/'+oid:reason='source_url_review'
        titles=[t['title'] for t in r.get('titles',[]) if t.get('title')]
        if not titles:reason=reason or 'missing_title'
        if reason:decisions.append({'object_number':oid,'source_id':r['id'],'reason':reason});continue
        title=next((t['title'] for t in r['titles'] if t.get('language')=='engelsk' and t.get('title')),titles[0])
        # Preserve source parts and page identity; do not count a list of many
        # distinct works as one individual artwork merely to inflate the batch.
        if r.get('parts'):decisions.append({'object_number':oid,'reason':'compound_object_review'});continue
        dims='; '.join(' '.join(str(v.get(k,'')) for k in ('part','type','value','unit')).strip() for v in r.get('dimensions',[]))
        medium='; '.join(dict.fromkeys(r.get('techniques',[])+r.get('materials',[])))
        w={'painter':c['creator_lref'],'title':title,'institution':'smk-statens-museum-for-kunst','url':r['frontend_url'],'accession':oid,'source_object_id':oid,'date_display':display,'creation_date':d,'attribution_role':'primary','work_type':typ,'medium':medium,'dimensions':dims,'aliases':list(dict.fromkeys(t for t in titles if t!=title)),
           'notes':'Official SMK object record. Creation-date notes: '+'; '.join(r.get('production_dates_notes',[]))+'. The museum holding is separate from current display.','raw':r}
        groups[c['creator_lref']].append(w)
    # Prefer paintings, then works with usable dates/images. Round-robin across
    # painters makes the bounded pass broad instead of filling it with one artist.
    for works in groups.values():works.sort(key=lambda w:(w['work_type']!='painting',w['creation_date']['precision']=='unknown',not(w['raw'].get('has_image') and w['raw'].get('public_domain')),w['source_object_id']))
    selected=[];keys=sorted(groups);roundno=0
    while len(selected)<10000:
        added=0
        for pid in keys:
            if roundno<len(groups[pid]):selected.append(groups[pid][roundno]);added+=1
            if len(selected)==10000:break
        if not added:break
        roundno+=1
    selected_ids={w['source_object_id'] for w in selected}
    selected.sort(key=lambda w:(w['painter'],w['source_object_id']))
    for g in groups.values():
        decisions.extend({'object_number':w['source_object_id'],'reason':'outside_bounded_10000_selection'} for w in g if w['source_object_id'] not in selected_ids)
    authors={}
    for pid in sorted({w['painter'] for w in selected}):
        a=registry[pid];c=a['creator'];name=' '.join(x for x in (c.get('creator_forename'),c.get('creator_surname')) if x)
        path=RUN/'persons'/(pid+'.json');items=json.loads(path.read_bytes()).get('items',[]) if path.exists() else [];person=items[0] if len(items)==1 else {}
        if person:assert person['id']==pid
        dated=[w['creation_date'] for w in selected if w['painter']==pid and w['creation_date']['first'] is not None]
        authors[pid]={'id':pid,'name':name,'sort_name':c['creator'],'nationality':c['creator_nationality'],'source_url':'https://api.smk.dk/api/v1/person/?id='+pid+'&lang=en','birth':life(person,'birth'),'death':life(person,'death'),
          'start':min((d['first'] for d in dated),default=0),'end':max((d['last'] for d in dated),default=0),'painting_raw':painting[a['painting_object']],'person_raw':person}
    chunks=[]
    for i in range(0,len(selected),250):
        works=selected[i:i+250];data={'source':'danish-painters-20260913','accessed_on':'2026-09-13','authors':{pid:authors[pid] for pid in sorted({w['painter'] for w in works})},'works':works}
        path=RUN/'batch'/f'chunk-{i//250+1:03d}.json';save(path,data)
        chunks.append({'file':path.name,'sha256':core.sha(path.read_bytes()),'works':len(works)})
    manifest={'source':'danish-painters-20260913','works':len(selected),'artists':len(authors),'unknown_dates':sum(w['creation_date']['precision']=='unknown' for w in selected),'types':dict(collections.Counter(w['work_type'] for w in selected)),'chunks':chunks}
    save(RUN/'batch/manifest.json',manifest);save(RUN/'selection-decisions.json',decisions)
    save(RUN/'selected-authors.json',authors)
    print({k:v for k,v in manifest.items() if k!='chunks'},'manifest sha',core.sha((RUN/'batch/manifest.json').read_bytes()),flush=True)
    print('Decision counts',dict(collections.Counter(d['reason'] for d in decisions)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['capture','audit','persons','plan']);a=p.parse_args();globals()[a.phase]()
