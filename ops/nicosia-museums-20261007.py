#!/usr/bin/env python3
"""Source-backed Nicosia museum and artwork expansion; production only."""
import argparse,collections,concurrent.futures,csv,gzip,importlib.util,json,re,uuid
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'docs/research/nicosia-museums-20261007'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/ROOT.name
def module(name,file):
    s=importlib.util.spec_from_file_location(name,REPO/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('nicosia_sources','research-havre-rouen-cyprus-20261006.py')
d=module('nicosia_delivery','museum-minimum-100-delivery-20261006.py')
h.RUN=ROOT;h.BACKUP=BACKUP
h.connect=lambda target='production',readonly=True:d.connect(readonly=readonly)if target=='production'else(_ for _ in ()).throw(AssertionError('Production only'))
save,load,now,norm=h.save,h.load,h.now,h.norm
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,ROOT.name+'/'+key))

DIRECTORIES={
    'municipality':'https://www.nicosia.org.cy/en-GB/discover/museums/',
    'tourism-city':'https://visitnicosia.com.cy/meet-nicosia-meet-culture/museums-art-institutions/',
    'tourism-district':'https://visitnicosia.com.cy/museums/',
    'near-east':'https://neu.edu.tr/campus-life/museums/?lang=en',
    'north-lapidary':'https://www.visitncy.com/discover/lapidary-museum/',
    'north-mevlevi':'https://www.visitncy.com/discover/mevlevi-tekke/',
    'gunsel':'https://sanat.gunsel.com.tr/en/our-museums/gunsel-art-museum/',
}

def capture_page(url,key=None):
    raw,rc=h.capture(url);soup=BeautifulSoup(raw,'html.parser')
    for tag in soup(['script','style','noscript']):tag.decompose()
    text=soup.get_text('\n',strip=True)
    value=dict(url=url,receipt=rc,text=text,headings=[dict(tag=t.name,text=t.get_text(' ',strip=True))for t in soup.select('h1,h2,h3,h4,h5')],
        links=[dict(url=urljoin(url,a['href']),text=a.get_text(' ',strip=True))for a in soup.select('a[href]')])
    dest=ROOT/'pages'/((key or h.sha(url.encode()))+'.json');save(dest,value)
    print('Captured',key or url,rc['status'],len(raw),'bytes',flush=True)
    return value

def directories():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        list(pool.map(lambda kv:capture_page(kv[1],kv[0]),DIRECTORIES.items()))

# Reconciled museum identities. Different departments of one State Gallery
# remain one institution; the two Bank of Cyprus museums remain distinct.
REGISTRY=[
('cyprus-museum-nicosia','Cyprus Museum','tourism-city','Cyprus Museum'),
('leventis-municipal-museum-nicosia','Leventis Municipal Museum of Nicosia','tourism-city','The Leventis Municipal Museum'),
('makarios-byzantine-museum-nicosia','Byzantine Museum and Art Galleries, Archbishop Makarios III Foundation','tourism-district','Byzantine Museum and Art Galleries'),
('hambis-municipal-printmaking-museum-nicosia','Hambis Municipal Printmaking Museum','tourism-city','Hambis Municipal Museum of Printmaking'),
('cypriot-coinage-museum-nicosia','Museum of the History of Cypriot Coinage','tourism-city','Museum of the History of Cypriot Coinage'),
('leventis-gallery','A. G. Leventis Gallery','tourism-city','A. G. Leventis Gallery'),
('fairy-tale-museum-nicosia','Fairy Tale Museum','tourism-city','Fairy Tale Museum'),
('cyprus-folk-art-museum-nicosia','Cyprus Folk Art Museum','tourism-city','Museum of Cyprus Folk Art'),
('hadjigeorgakis-kornesios-museum-nicosia','Ethnological Museum — House of Hadjigeorgakis Kornesios','tourism-city','House of Hadjigeorgakis Kornesios'),
('cyprus-classic-motorcycle-museum-nicosia','Cyprus Classic Motorcycle Museum','tourism-city','Cyprus Classic Motorcycle Museum'),
('cyprus-postal-museum-nicosia','Cyprus Postal Museum','tourism-city','Cyprus Post Museum'),
('national-struggle-museum-nicosia','National Struggle Museum, Nicosia','tourism-city','Struggle Museum'),
('state-gallery-cyprus','State Gallery of Contemporary Cypriot Art','tourism-city','State Gallery of Modern and Contemporary Cypriot Art'),
('cvar-nicosia','Centre of Visual Arts and Research (CVAR)','tourism-city','Centre Of Visual Arts and Research'),
('nimac-nicosia','Nicosia Municipal Arts Centre (NiMAC)','tourism-city','NiMac (Nicosia Municipal Arts Centre)'),
('pancyprian-gymnasium-museums-nicosia','Pancyprian Gymnasium Museums','tourism-city','Museum of the Pancyprian Gymnasium'),
('giabra-pierides-collection-museum-nicosia','Museum of the George and Nefeli Giabra Pierides Collection','tourism-city','Museum of George and Nefeli Giabra'),
('ledroi-archaeological-museum-nicosia','Local Archaeological Museum of Ledroi','tourism-city','Ledroi Museum'),
('apoel-history-museum-nicosia','APOEL History Museum','municipality','APOEL History Museum'),
('shacolas-tower-museum-nicosia','Shacolas Tower Museum and Observatory','municipality','Shacolas Tower Museum'),
('zampelas-art-museum-nicosia','Loukia and Michael Zampelas Art Museum','municipality','Zampelas Art Museum'),
('national-guard-commandos-museum-nicosia','National Guard Commandos Museum','tourism-district','National Guard Commandos Museum'),
('eldyk-museum-nicosia','Museum of the Hellenic Force in Cyprus (ELDYK)','tourism-district','Museum of the Hellenic Force in Cyprus'),
('cybc-broadcasting-museum-nicosia','CyBC Museum of Broadcasting','tourism-district','CYBC Museum Of Broadcasting'),
('historical-labour-museum-nicosia','Historical Labour Museum','tourism-district','Historical Labour Museum'),
('water-board-museum-nicosia','Nicosia Water Board Museum','tourism-district','Nicosia Water Board Museum'),
('heroes-museum-yeri','Heroes Museum, Yeri','tourism-district','Heroes Museum'),
('point-centre-contemporary-art-nicosia','Point Centre for Contemporary Art','tourism-district','Point Center of Contemporary Art'),
('cyprus-police-museum-nicosia','Cyprus Police Museum','tourism-district','Cyprus Police Museum'),
('tsirides-natural-history-museum-nicosia','International Natural History Museum of the Tsirides Foundation','tourism-district','International Natural History Museum of the Tsirides Foundation'),
('cyprus-natural-history-museum-latsia','Cyprus Museum of Natural History','tourism-district','Cyprus Museum of Natural History'),
('cyprus-food-nutrition-museum-nicosia','Cyprus Food and Nutrition Museum','tourism-district','Cyprus Food and Nutrition Museum'),
('press-museum-nicosia','Press Museum, Nicosia','tourism-district','Press Museum'),
('boccf','Bank of Cyprus Cultural Foundation','boccf-main','Bank of Cyprus'),
('barbarism-museum-nicosia','Museum of Barbarism','north-department','Barbarlık Müzesi'),
('dervish-pasha-museum-nicosia','Dervish Pasha Mansion — Ethnographic Museum','north-department','Derviş Paşa Konağı'),
('lusignan-house-museum-nicosia','Lusignan House Museum','north-department','Lüzinyan Evi'),
('mevlevi-tekke-museum-nicosia','Mevlevi Tekke Museum','north-department','Mevlevi Müzesi'),
('turkish-cypriot-history-museum-nicosia','Turkish Cypriot History, Culture and National Struggle Museum','north-department','Kıbrıs Türk Tarih, Kültür ve'),
('lapidary-museum-nicosia','Lapidary Museum, Nicosia','north-department','Taş Eserler Müzesi'),
('bedesten-medieval-tombstones-museum-nicosia','Bedesten Medieval Tombstones Museum','north-department','Bedesten Ortaçağ Mezar Taşları Müzesi'),
('cyprus-modern-art-museum-nicosia','Cyprus Museum of Modern Arts','cyprus-modern','Cyprus Museum of Modern Arts'),
('cyprus-car-museum-nicosia','Cyprus Car Museum','north-museums','Cyprus Car Museum'),
('cyprus-herbarium-natural-history-museum-nicosia','Cyprus Herbarium and Natural History Museum','north-museums','Cyprus Herbarium and Natural'),
('walled-city-museum-nicosia','Walled City Museum, Nicosia','north-museums','Walledcity Museum'),
('gunsel-art-museum-nicosia','Günsel Art Museum','gunsel','GÜNSEL Art Museum'),
('gunsel-office-museum-nicosia','Günsel Office Museum','north-museums','Günsel Office Museum'),
('fazil-kucuk-museum-nicosia','Dr. Fazıl Küçük Museum','fazil','Küçük Museum'),
('archbishop-kyprianos-museum-strovolos','Archbishop Kyprianos Ecclesiastical Museum','kyprianos','Church Museum'),
('aglantzia-natural-history-museum','Aglantzia Municipal Museum of Natural History','web-ucy','Aglantzia Municipal Museum of Natural History'),
('cyprus-jewellers-museum-nicosia','Cyprus Jewellers Museum','web-ucy','Cyprus Jewellers Museum'),
('pancyprian-geographical-museum-strovolos','Pancyprian Geographical Museum','web-ucy','Pancyprian Geographical Museum'),
('von-world-pens-hall-nicosia','Von World Pens Hall','web-ucy','The Von World Pens Hall'),
('alparslan-turkes-house-museum-nicosia','Alparslan Türkeş House Museum','alparslan-turkes','Alparslan Türkeş Müzesi'),
('turkish-cypriot-islamic-arts-museum-nicosia','Museum of Turkish Cypriot Islamic Arts','islamic-arts-museum','Kıbrıs Türk İslam Eserleri Müzesi'),
]

def source_proof(key,needle):
    if key=='web-ucy':
        path=ROOT/'web-evidence/ucy.json';value=load(path);text=value['result']
        assert needle in text and 'Museums – Living in Nicosia'in text
        return dict(url=value['source_url'],channel=value['channel'],body_path=str(path.relative_to(REPO)),sha256=h.sha(path.read_bytes()),
            source_last_updated=value['source_last_updated'],retrieved_at=now(),matched_label=needle,
            limitation='Indexed primary university directory, last updated 2024; direct HTTP capture was denied. Existence evidence does not verify present opening or object holdings.')
    page=load(ROOT/'pages'/(key+'.json'));rc=page['receipt']
    assert rc['status']==200 and h.sha(gzip.decompress((REPO/rc['body_path']).read_bytes()))==rc['sha256']
    assert norm(needle)in norm(page['text']),(key,needle)
    return dict(rc,matched_label=needle,channel='direct_public_source',limitation='Institution identity/directory evidence only; no current-opening, artwork holding or display inference.')

def institution_plan(use_saved=False):
    if use_saved:
        live=load(ROOT/'all-institution-identities.json.gz')['institutions']
        place=[x for x in load(ROOT/'production-baseline.json.gz')['places']if x['v']['name']=='Nicosia'and x['v']['country_code']=='CY']
    else:
        with d.connect()as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            live=[x['v']for x in db.execute('SELECT to_jsonb(i)v FROM institutions i ORDER BY id')]
            place=db.execute("SELECT to_jsonb(p)v FROM places p WHERE normalized_name='nicosia' AND country_code='CY'").fetchall()
    assert len(place)==1
    rows=[]
    for slug,name,key,needle in REGISTRY:
        proof=source_proof(key,needle)
        existing=[i for i in live if i['slug']==slug or(norm(i['name'])in {norm(name),norm(needle)}and i['place_id']==place[0]['v']['id'])]
        assert len(existing)<=1,(slug,existing)
        prior=existing[0]if existing else None
        kind='foundation'if slug in ['boccf','point-centre-contemporary-art-nicosia']else'museum'
        notes='Nicosia city or metropolitan area, Cyprus. Identity supported by the cited museum, municipality or institutional directory.'
        if slug=='state-gallery-cyprus':notes+=' SPEL and Majestic are documented venues of the existing State Gallery; no duplicate institution or venue-specific artwork holding is asserted.'
        if key=='web-ucy':notes+=' University directory dated 2024; current operation requires confirmation.'
        if key=='islamic-arts-museum':notes+=' Primary school visit report documents the Nicosia museum and museum director; current opening and object holdings need separate evidence.'
        if slug=='zampelas-art-museum-nicosia':notes+=' Former zampelasart.com address serves unrelated content and is excluded from museum/artwork evidence.'
        row=prior or dict(id=uid('institution/'+slug),slug=slug,name=name,normalized_name=norm(name),kind=kind,place_id=place[0]['v']['id'],website_url=proof['url'],status='review',description=notes)
        rows.append(dict(institution=row,before=prior,source=proof,editorial_confidence=.85 if key in ['web-ucy','islamic-arts-museum']else .95,
            confidence_basis='Exact named museum in authoritative Nicosia directory or its own website, reviewed geographical context and duplicate institution identities.',notes=notes))
    assert len({x['institution']['id']for x in rows})==len(rows)
    plan=dict(at=now(),target='production',records=rows,place=place[0]['v'],baseline_identity_rows=live,using_preserved_production_snapshot=use_saved,
        scope='Nicosia city, both sides, and immediate metropolitan municipalities. Rural district museums and non-museum monuments remain separately documented research leads.')
    save(ROOT/'institution-plan.json.gz',plan);save(BACKUP/'institution-plan-preimages.json.gz',plan)
    print('Institution plan:',len(rows),'identified;',sum(x['before']is None for x in rows),'new;',sum(x['before']is not None for x in rows),'existing',flush=True)

def institution_apply():
    from psycopg.types.json import Jsonb
    backup=load(ROOT/'production-backup.json')['production']
    assert backup['status']=='SUCCESSFUL'and backup['instance']=='artline-postgres'
    assert '/projects/artline-508319/'in backup['selfLink']
    p=load(ROOT/'institution-plan.json.gz');digest=h.sha((ROOT/'institution-plan.json.gz').read_bytes());assert not(ROOT/'institutions-applied.json').exists()
    for row in p['records']:
        rc=row['source'];raw=(REPO/rc['body_path']).read_bytes();raw=gzip.decompress(raw)if rc['channel']=='direct_public_source'else raw
        assert h.sha(raw)==rc['sha256']
    sid=uid('institution-source');ids=[x['institution']['id']for x in p['records']]
    with d.connect(readonly=False)as db,db.transaction():
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(ROOT.name,))
        actual={x['v']['id']:x['v']for x in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))}
        for row in p['records']:assert actual.get(row['institution']['id'])==row['before'],'Institution version changed'
        slugs=[x['institution']['slug']for x in p['records']if not x['before']]
        assert not db.execute('SELECT id FROM institutions WHERE slug=ANY(%s)',(slugs,)).fetchall(),'Concurrent museum slug'
        names=[x['institution']['normalized_name']for x in p['records']if not x['before']]
        assert not db.execute('SELECT id FROM institutions WHERE normalized_name=ANY(%s)AND place_id=%s',(names,p['place']['id'])).fetchall(),'Concurrent museum name and city'
        save(BACKUP/'institution-transaction-preimages.json.gz',dict(at=now(),plan_sha256=digest,institutions=actual,absent_ids=[i for i in ids if i not in actual]))
        h.insert(db,'sources',dict(id=sid,slug=ROOT.name+'-museum-identities',name='Nicosia museums: official municipal, museum and university identity evidence',source_type='authority_data'))
        for row in p['records']:
            i=row['institution'];rc=row['source']
            if row['before']is None:
                h.insert(db,'institutions',i);h.audit_entry(db,'institution',i['id'],None,i,'insert')
            h.insert(db,'citations',dict(id=uid('institution-citation/'+i['id']),entity_type='institution',entity_id=i['id'],field_name='verified_museum_identity_and_geography',source_id=sid,source_url=rc['url'],
                evidence_note=json.dumps(dict(source=rc,editorial_confidence=row['editorial_confidence'],confidence_basis=row['confidence_basis'],remaining_uncertainty=rc['limitation'],notes=row['notes'],plan_sha256=digest),ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=h.ACTOR))
        after={x['v']['id']:x['v']for x in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[])',(ids,))};assert len(after)==len(ids)
        for row in p['records']:
            i=row['institution'];assert after[i['id']]==row['before']if row['before']else all(after[i['id']][k]==v for k,v in i.items())
        save(BACKUP/'institution-transaction-after.json.gz',dict(at=now(),plan_sha256=digest,institutions=after))
    save(ROOT/'institutions-applied.json',dict(at=now(),target='production',plan_sha256=digest,new_institutions=len(slugs),existing_institutions=len(ids)-len(slugs),institution_ids=ids,new_publications=0,local_database_writes=0))
    print('COMMITTED',len(slugs),'new institutions and',len(ids),'institution evidence citations in production',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['directories','institution_plan','institution_prepare','institution_apply']);a=p.parse_args()
    institution_plan(use_saved=True)if a.phase=='institution_prepare'else globals()[a.phase]()
