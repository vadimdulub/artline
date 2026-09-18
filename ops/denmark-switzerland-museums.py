#!/usr/bin/env python3
"""Selected DK/CH museum campaign. Writes require explicit pinned review files."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin, unquote

spec = importlib.util.spec_from_file_location('base', Path(__file__).with_name('dutch-german-museum-campaign.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ROOT = b.ROOT
RUN = ROOT / 'docs/research/denmark-switzerland-museums-20260917'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/denmark-switzerland-museums-20260917')
b.RUN, b.BACKUP, b.SOURCE = RUN, BACKUP, 'denmark-switzerland-selected-museums-20260917'
core, save, load, uid, norm, connect, capture = b.core, b.save, b.load, b.uid, b.norm, b.connect, b.capture

SEEDS = {
 'hirschsprung': 'https://www.hirschsprung.dk/en/collection/art',
 'hirschsprung-rights': 'https://www.hirschsprung.dk/en/the-museum/photos',
 'basel': 'https://kunstmuseumbasel.ch/de/sammlung/schwerpunkte',
 'bern': 'https://www.kunstmuseumbern.ch/en/collection-research',
 'mcba': 'https://www.mcba.ch/en/collection/',
 'glyptotek': 'https://glyptoteket.com/exhibitions/permanent-exhibitions/french-art-1870',
 'roemerholz': 'https://www.roemerholz.ch/en/the-collection',
 'kunsten': 'https://collection.kunsten.dk/',
}

GEO = [
 ('wikimedia-museum-q2982867','Copenhagen','DK','index-hirschsprung','2100 København'),
 ('wikimedia-museum-q194626','Basel','CH','index-basel','CH-4010 Basel'),
 ('wikimedia-museum-q194622','Bern','CH','index-bern','3011 Bern'),
 ('wikimedia-museum-q3329523','Lausanne','CH','index-mcba','1003 Lausanne'),
 ('ny-carlsberg-glyptotek','Copenhagen','DK','glyptotek-visit','1556 København'),
 ('sammlung-oskar-reinhart-am-roemerholz','Winterthur','CH','index-roemerholz','8400 Winterthur'),
]
NEW_INSTITUTIONS = {
 'ny-carlsberg-glyptotek': ('Ny Carlsberg Glyptotek','https://glyptoteket.com/'),
 'sammlung-oskar-reinhart-am-roemerholz': ('Sammlung Oskar Reinhart “Am Römerholz”','https://www.roemerholz.ch/en'),
}

def ensure_source(db):
    sid=uid('source')
    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Denmark and Switzerland — selected museum review','collection_page','https://www.hirschsprung.dk/') ON CONFLICT(slug) DO NOTHING",(sid,b.SOURCE))
    assert str(db.execute('SELECT id FROM sources WHERE slug=%s',(b.SOURCE,)).fetchone()['id'])==sid
    return sid
b.ensure_source=ensure_source

def backup_verify():
    cloud=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1789675309278','--instance=artline-postgres','--project=artline-508319','--format=json'],text=True))
    assert cloud['status']=='SUCCESSFUL'
    save(RUN/'backups.json',dict(local=load(BACKUP/'local-verified.json'),cloud=cloud))

def geo_plan():
    facts=[]
    for slug,city,country,key,needle in GEO:
        raw=(RUN/'captures'/(key+'.html')).read_bytes()
        receipt=load(RUN/'captures'/(key+'.receipt.json'))
        assert core.sha(raw)==receipt['sha256']
        soup=b.BeautifulSoup(raw,'html.parser')
        for t in soup(['script','style']):t.decompose()
        text=soup.get_text(' ',strip=True)
        assert needle in text,(slug,needle)
        pos=text.index(needle)
        facts.append(dict(slug=slug,city=city,country=country,source=receipt,evidence_excerpt=text[max(0,pos-150):pos+200],
            name=NEW_INSTITUTIONS.get(slug,(None,None))[0],website=NEW_INSTITUTIONS.get(slug,(None,None))[1]))
    result=dict(at=core.now(),facts=facts,targets={})
    for target in ('local','cloud'):
        with connect(target) as db:
            planned=[]
            places=db.execute("SELECT id::text,name,country_code FROM places WHERE country_code IN ('DK','CH') ORDER BY id").fetchall()
            for f in facts:
                before=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE slug=%s',(f['slug'],)).fetchone()
                before=before['row'] if before else None
                if before:
                    assert before['place_id'] is None and before['status']!='archived'
                    assert not db.execute('SELECT 1 FROM institution_venues WHERE institution_id=%s',(before['id'],)).fetchone()
                else:
                    assert f['slug'] in NEW_INSTITUTIONS
                    needle='glyptotek' if 'glyptotek' in f['slug'] else 'römerholz'
                    assert not db.execute('SELECT id FROM institutions WHERE lower(name) LIKE %s OR website_url=%s',('%'+needle+'%',f['website'])).fetchone()
                matches=[p for p in places if p['country_code']==f['country'] and norm(p['name'])==norm(f['city'])]
                place=matches[0] if matches else dict(id=uid('place/'+f['country']+'/'+f['city']),name=f['city'],country_code=f['country'])
                planned.append(dict(fact=f,before=before,id=before['id'] if before else uid('institution/'+f['slug']),place=place,place_new=not bool(matches)))
            result['targets'][target]=planned
            save(BACKUP/(target+'-geography-preimages.json'),planned)
    save(RUN/'geography-plan.json',result)
    print('Geography plan',len(facts),'institutions')

def geo_apply(target):
    plan,review=b.reviewed_plan('geography')
    receipts=[]
    with connect(target,False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559320260918)')
        sid=ensure_source(db)
        for item in plan['targets'][target]:
            f=item['fact'];p=item['place'];iid=item['id'];before=item['before']
            if before:
                now=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s FOR UPDATE',(iid,)).fetchone()['row']
                assert now==before
            else:assert not db.execute('SELECT id FROM institutions WHERE id=%s OR slug=%s',(iid,f['slug'])).fetchone()
            if item['place_new']:
                db.execute('INSERT INTO places(id,name,normalized_name,country_code) VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',(p['id'],p['name'],norm(p['name']),p['country_code']))
            actual=db.execute('SELECT name,country_code FROM places WHERE id=%s',(p['id'],)).fetchone()
            assert actual and actual['country_code']==f['country'] and actual['name']==p['name']
            if before:db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s',(p['id'],iid))
            else:db.execute("INSERT INTO institutions(id,slug,name,normalized_name,place_id,website_url,status) VALUES(%s,%s,%s,%s,%s,%s,'review')",(iid,f['slug'],f['name'],norm(f['name']),p['id'],f['website']))
            name=before['name'] if before else f['name']
            db.execute("INSERT INTO institution_venues(id,institution_id,slug,name,place_id,visit_url,source_url,checked_at,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'review')",(uid('venue/'+f['slug']),iid,f['slug']+'-verified-location',name,p['id'],f['source']['url'],f['source']['url'],f['source']['at']))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES('institution',%s,'country_city_venue',%s,%s,%s,%s,%s)",(iid,sid,f['source']['url'],json.dumps(f,ensure_ascii=False),f['source']['at'],core.ACTOR))
            db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,iid))
            receipts.append(dict(id=iid,slug=f['slug'],new=before is None,country=f['country']))
    save(RUN/(target+'-geography-applied.json'),dict(at=core.now(),records=receipts,plan_sha256=review['plan_sha256']))
    print(target,'geography applied',len(receipts),flush=True)

def research():
    out = []
    for key, url in SEEDS.items():
        try:
            soup, receipt = capture(url, 'index-'+key)
            links = [{'label':a.get_text(' ',strip=True),'url':urljoin(receipt['url'],a['href'])} for a in soup.select('a[href]')]
            for tag in soup(['script','style','noscript']): tag.decompose()
            text = soup.get_text(' ',strip=True)
            out.append(dict(key=key,receipt=receipt,links=links,text=text))
            print(key,len(text),'characters',flush=True)
        except Exception as error:
            out.append(dict(key=key,error=str(error)));print(key,str(error),flush=True)
    save(RUN/'discovery.json',out)

def backup_start():
    BACKUP.mkdir(parents=True,exist_ok=True)
    receipt=BACKUP/'cloud-request.json'
    if not receipt.exists():
        raw=subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319',
          '--description=Before selected Denmark Switzerland museum import 20260917','--async','--format=json'],text=True)
        save(receipt,json.loads(raw))
    path=BACKUP/'local-before.dump'
    assert not path.exists(), 'Preserve existing backup; verify it instead of overwriting'
    subprocess.run(['pg_dump','--dbname=postgres://localhost/artline','--format=custom','--file='+str(path)],check=True)
    listing=subprocess.check_output(['pg_restore','--list',str(path)],text=True)
    assert 'TABLE DATA public artworks' in listing and 'TABLE DATA public media_assets' in listing
    with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
    save(BACKUP/'local-verified.json',dict(path=str(path),bytes=path.stat().st_size,sha256=digest,directory_verified=True,at=core.now()))
    print('Local backup verified; cloud backup requested',flush=True)

def selected_capture():
    rows=load(RUN/'selected-pages.json')
    assert len(rows)<=90
    def one(row):
        try:
            soup,receipt=capture(row['url'],row['key'])
            for t in soup(['script','style','noscript']):t.decompose()
            return dict(row,receipt=receipt,text=soup.get_text(' ',strip=True))
        except Exception as error:return dict(row,error=str(error))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:out=list(pool.map(one,rows))
    save(RUN/'selected-captures.json',out)
    for row in out:print(row['key'],row.get('error') or row['text'][:250],flush=True)

def select_pages():
    discovery={r['key']:r for r in load(RUN/'discovery.json')}
    selected=[]
    for row in discovery['hirschsprung']['links']:
        tail=row['url'].rstrip('/').split('/')[-1]
        if tail in ('women-artists','vilhelm-hammershoi','p-s-kroyer','the-golden-age-painters','the-funen-painters','bertha-wegmann','the-skagen-painters','the-modern-breakthrough-masterpieces-from-the-museum-s-collection'):
            selected.append(dict(key='hirschsprung-'+tail,url=row['url'],museum='hirschsprung'))
    needles=('open-air-portrait','griche-la-borgne','le-criquet','paravent-baigneuses','interieur-aux','le-colin','memoire-memory','les-tresseuses','paysage-aux','blackfriars','portrait-de-jean')
    seen=set()
    for row in discovery['mcba']['links']:
        tail=row['url'].rstrip('/').split('/')[-1]
        if any(tail.startswith(n) for n in needles) and row['url'] not in seen:
            seen.add(row['url']);selected.append(dict(key='mcba-'+tail[:70],url=row['url'],museum='mcba'))
    selected += [dict(key='roemerholz-online',url='https://www.bundessammlungen.ch/en/collection/?f=Sammlung%2COskar%2CReinhart&v=2',museum='roemerholz'),
      dict(key='glyptotek-danish',url='https://glyptoteket.com/exhibitions/permanent-exhibitions/danish-art-1780',museum='glyptotek')]
    save(RUN/'selected-pages.json',selected)
    print('Selected',len(selected),'bounded primary pages')

def basel_native():
    soup=b.BeautifulSoup((RUN/'captures/index-basel.html').read_bytes(),'html.parser')
    selected=[]
    for f in soup.select('figure.masterpieces__item'):
        title=f.select_one('.masterpieces__werk');year=f.select_one('.masterpieces__year')
        if not title or not year:continue
        date=b.parse_date(year.get_text(' ',strip=True))
        if date['last'] and date['last']>1970:continue
        match=re.search(r'(?:gw|ew)\d{2}-(\d{7})-',f.a['href'])
        if not match:continue
        ident=str(int(match[1]))
        if any(r['id']==ident for r in selected):continue
        selected.append(dict(key='basel-'+ident,id=ident,title=title.get_text(' ',strip=True),url='https://sammlung.kunstmuseumbasel.ch/en/collection/item/'+ident))
        if len(selected)==24:break
    assert len(selected)<=30
    out=[]
    for row in selected:
        try:
            soup,receipt=capture(row['url'],row['key'])
            item=json.loads(soup.select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item']
            out.append(dict(row,item=item,receipt=receipt))
            print(row['key'],item['ObjDetailCaption1Txt']['LabelTxt'],flush=True)
        except Exception as error:out.append(dict(row,error=str(error)))
    save(RUN/'basel-native.json',out)

def parse_date(raw):
    # Source intervals preserved, never collapsed to a made-up representative year.
    adjusted=re.sub(r'(?i)^circa\s+','c. ',raw.strip())
    adjusted=re.sub(r'(?i)^between (\d{4}) and (\d{4})$',r'\1–\2',adjusted)
    date=b.parse_date(adjusted);date['display']=raw
    return date

def parse_records():
    records=[]
    def add(key,museum,slug,title,creator,raw,kind,medium,dimensions,accession,capture_key,fields,**extra):
        receipt=load(RUN/'captures'/(capture_key+'.receipt.json'))
        records.append(dict(key=key,museum=museum,institution_slug=slug,title=title,creator_label=creator,
            date=parse_date(raw),work_type=kind,medium=medium,dimensions=dimensions,accession=accession,
            url=receipt['url'],source=receipt,capture_key=capture_key,fields=fields,**extra))
    for row in load(RUN/'selected-captures.json'):
        if row['museum']!='mcba' or row.get('error'):continue
        soup=b.BeautifulSoup((RUN/'captures'/(row['key']+'.html')).read_bytes(),'html.parser')
        h=soup.select_one('h1');creator=h.select_one('[itemprop=artist]').get_text(' ',strip=True)
        title_date=h.select_one('[itemprop=name]').get_text(' ',strip=True)
        title,raw=title_date.rsplit(', ',1)
        node=soup.find(string=lambda s:s and 'Inv.' in s)
        info=node.parent.parent
        medium=info.select_one('[itemprop=artMedium]').get_text(' ',strip=True)
        line=info.select_one('[itemprop=artMedium]').parent.get_text(' ',strip=True)
        dimensions=line[len(medium):].lstrip(' ,')
        accession=re.search(r'Inv\.\s*(.+)',node.parent.get_text(' ',strip=True))[1]
        kind='painting' if re.search(r'\b(oil|tempera|gouache|watercolour)\b',medium,re.I) else 'unknown'
        add(row['key'],'mcba','wikimedia-museum-q3329523',title,creator,raw,kind,medium,dimensions,accession,row['key'],
            dict(object_label=info.get_text(' ',strip=True)),native_id=row['url'].rstrip('/').split('/')[-1])
    for row in load(RUN/'basel-native.json'):
        if row.get('error'):continue
        item=row['item']
        def field(k):return item.get(k,{}).get('LabelTxt')
        title=field('ObjDetailCaption1Txt');creator=re.sub(r'\s*\([^)]*\)\s*$','',field('ObjDetailCaption2Txt')).strip()
        medium=field('ObjDetailMaterialTechniqueTxt') or ''
        kind='painting' if re.search(r'Öl|Acryl|Tempera|Mischtechnik auf (?:Linden|Tannen|Buchen|Eichen)holz',medium) else 'unknown'
        add(row['key'],'basel','wikimedia-museum-q194626',title,creator,field('ObjDetailDateTxt') or 'Not stated',kind,medium or None,
            field('ObjDetailDimensionTxt'),field('ObjDetailNumberTxt'),row['key'],item,native_id=row['id'])
    # Museum-authored captions support these distinct selected records. Do not
    # pretend the campaign key is an inventory number; absent inventories stay null.
    for item in load(RUN/'hirschsprung-selection.json'):
        key=item['capture_key'];soup=b.BeautifulSoup((RUN/'captures'/(key+'.html')).read_bytes(),'html.parser')
        text=soup.get_text(' ',strip=True)
        assert item['evidence_needle'] in text,(key,item['evidence_needle'])
        add(item['key'],'hirschsprung','wikimedia-museum-q2982867',item['title'],item['creator'],item['date'],item['work_type'],
            item.get('medium'),None,None,key,dict(evidence_needle=item['evidence_needle']),native_id=item['key'],
            title_is_descriptive=item.get('title_is_descriptive',False),commons_title=item.get('commons_title'))
    soup=b.BeautifulSoup((RUN/'captures/glyptotek-monet.html').read_bytes(),'html.parser')
    text=soup.get_text(' ',strip=True)
    assert all(v in text for v in ['M.IN. 1753','Claude Monet','1882','Olie på lærred','Ny Carlsberg Glyptotek'])
    add('glyptotek-min-1753','glyptotek','ny-carlsberg-glyptotek','Skygger på havet. Klipperne ved Pourville','Claude Monet','1882',
        'painting','Olie på lærred','57 x 80 cm','M.IN. 1753','glyptotek-monet',dict(evidence=text[-1300:]),native_id='min-1753')
    save(RUN/'parsed-records.json',records)
    for r in records:print(r['key'],r['creator_label'],r['title'],r['date']['display'],r['work_type'],flush=True)

def source_file_key(url):
    if not url:return ''
    return unquote(url).split('/wiki/')[-1].replace('_',' ').casefold() if '/wiki/File' in unquote(url) else ''

def metadata_plan():
    records=load(RUN/'parsed-records.json')
    assert 1<=len(records)<=80
    # Conservative clarification of year-bearing labels, preserving original text.
    for r in records:
        raw=r['date']['display']
        if r['date']['first'] is None:
            m=re.fullmatch(r'(?:March |Frühsommer )?(\d{4})(?: \(Sommer\)| \(Gósol\)|, \d+)?',raw)
            if m:r['date']=dict(first=int(m[1]),last=int(m[1]),precision='exact',display=raw)
    result=dict(at=core.now(),records=records,targets={})
    for target in ('local','cloud'):
        with connect(target) as db:
            institutions=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE slug=ANY(%s)',(list({r['institution_slug'] for r in records}),)).fetchall()
            imap={i['row']['slug']:i['row'] for i in institutions}
            keys=[norm(r['creator_label']) for r in records]
            artists=db.execute('''SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,
              ARRAY(SELECT x.alias FROM artist_aliases x WHERE x.artist_id=a.id) aliases
              FROM artists a WHERE a.status<>'archived' AND (a.normalized_name=ANY(%s)
              OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.normalized_alias=ANY(%s))) LIMIT 201''',(keys,keys)).fetchall()
            assert len(artists)<=200
            ii=[i['row']['id'] for i in institutions];aa=[a['id'] for a in artists]
            # First choose candidate IDs through institution/artist indexes; enrich only that set.
            works=db.execute('''WITH chosen AS MATERIALIZED (
              SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
              UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL
              UNION SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])
            ) SELECT to_jsonb(a) row,
              ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) urls,
              ARRAY(SELECT e.canonical_url FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) external_urls,
              ARRAY(SELECT x.artist_id::text FROM artwork_artists x WHERE x.artwork_id=a.id) artist_ids,
              ARRAY(SELECT l.institution_id::text FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.superseded_by IS NULL) institution_ids,
              m.source_page_url image_source
              FROM chosen s JOIN artworks a ON a.id=s.id LEFT JOIN media_assets m ON m.id=a.primary_media_id
              WHERE a.status<>'archived' ORDER BY a.id LIMIT 30001''',(ii,ii,aa)).fetchall()
            assert len(works)<=30000
            save(BACKUP/(target+'-metadata-scoped-preimages.json'),dict(institutions=institutions,artists=artists,works=works))
            planned=[]
            for r in records:
                matches=[a for a in artists if norm(r['creator_label']) in {norm(n) for n in [a['display_name']]+a['aliases']}]
                creator=matches[0] if len(matches)==1 else None
                q=dict(record=r,artist=creator,institution=imap[r['institution_slug']])
                # Explicit post-cutoff/multiphase labels are held even when numeric parsing stays unknown.
                if any(int(y)>1970 for y in re.findall(r'\b\d{4}\b',r['date']['display'])):
                    q.update(action='hold',reason='Source creation date includes a year after 1970');planned.append(q);continue
                exact=[]
                for w in works:
                    related={w['row']['current_institution_id']}|set(w['institution_ids'])
                    source_match=(r['museum']!='hirschsprung' and r['url'] in w['urls']+w['external_urls'])
                    accession_match=r['accession'] and q['institution']['id'] in related and b.accession_key(r['accession'])==b.accession_key(w['row']['accession_number'])
                    file_match=r.get('commons_title') and source_file_key(w['image_source'])==r['commons_title'].casefold()
                    if source_match or accession_match or file_match:exact.append(w)
                if len(exact)==1:q.update(action='existing',work=exact[0]['row'],reason='Exact source URL, museum inventory or selected reproduction identity')
                elif len(exact)>1:q.update(action='hold',reason='Multiple existing exact identities',leads=[w['row']['slug'] for w in exact])
                else:
                    titles={norm(r['title']),norm(r['title'].split(' (')[0])}
                    similar=[w for w in works if titles & {norm(w['row']['title']),norm(w['row']['alternate_title'] or '')} and (not creator or creator['id'] in w['artist_ids'])]
                    if similar:q.update(action='hold',reason='Possible existing title identity',leads=[w['row']['slug'] for w in similar])
                    else:q.update(action='new',artwork_id=uid('artwork/'+r['key']),slug='dk-ch-'+r['key'])
                # Saved for manual reconciliation, not used as automatic identity proof.
                q['same_creator_date_leads']=[dict(id=w['row']['id'],slug=w['row']['slug'],title=w['row']['title'],date=w['row']['date_display'],accession=w['row']['accession_number'],image=w['image_source']) for w in works
                  if creator and creator['id'] in w['artist_ids'] and r['date']['first'] is not None and w['row']['creation_year_start'] is not None
                  and w['row']['creation_year_start']<=r['date']['last'] and (w['row']['creation_year_end'] or w['row']['creation_year_start'])>=r['date']['first']][:60]
                planned.append(q)
            result['targets'][target]=planned
            print(target,'scoped',len(works),{a:sum(p['action']==a for p in planned) for a in ('new','existing','hold')},flush=True)
    save(RUN/'metadata-plan.json',result)

def metadata_apply(target):
    plan,review=b.reviewed_plan('metadata');allowed=set(review['selected_keys'])
    selected=[p for p in plan['targets'][target] if p['record']['key'] in allowed]
    assert len(selected)==len(allowed)
    receipts=[]
    with connect(target,False) as db:
        for item in selected:
            r=item['record'];key=r['key'];date=r['date'];aid=item.get('artwork_id') or item['work']['id']
            assert item['action'] in ('new','existing')
            assert core.sha((RUN/'captures'/(r['capture_key']+'.html')).read_bytes())==r['source']['sha256']
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559320260918)')
                sid=ensure_source(db)
                if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s",(aid,sid,key)).fetchone():
                    print(target,key,'already applied',flush=True);continue
                inst=db.execute('SELECT slug,status FROM institutions WHERE id=%s FOR SHARE',(item['institution']['id'],)).fetchone()
                assert inst and inst['slug']==r['institution_slug'] and inst['status']!='archived'
                if item['action']=='new':
                    assert not db.execute('SELECT 1 FROM artworks WHERE id=%s OR slug=%s',(aid,item['slug'])).fetchone()
                    if r['accession']:
                        assert not db.execute('''SELECT 1 FROM artworks a WHERE a.accession_number=%s AND
                          (a.current_institution_id=%s OR EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=%s AND l.superseded_by IS NULL))''',(r['accession'],item['institution']['id'],item['institution']['id'])).fetchone()
                    db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
                      work_type,medium_text,dimensions_text,accession_number,unlinked_creator_label,status,research_candidate,created_by,updated_by)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',
                      (aid,item['slug'],r['title'],norm(r['title']),date['display'],date['first'],date['last'],date['precision'],r['work_type'],r['medium'],r['dimensions'],r['accession'],r['creator_label'],core.ACTOR,core.ACTOR))
                    if item['artist']:
                        artist=item['artist'];current=db.execute('SELECT display_name,birth_year,death_year,status FROM artists WHERE id=%s FOR SHARE',(artist['id'],)).fetchone()
                        assert current and all(current[k]==artist[k] for k in current)
                        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,artist['id'],'Unqualified primary museum attribution; exact source name retained: '+r['creator_label']))
                    db.execute('''INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                      VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'review')''',(aid,item['institution']['id'],sid,r['url'],
                       'Selected museum collection association; ownership and deposit credits preserved in source citation. Review only, not accepted ownership/custody or current display.',r['source']['at']))
                else:
                    current=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']
                    assert current==item['work'],'Existing artwork changed after preflight'
                evidence=dict(record=r,plan_sha256=review['plan_sha256'],action=item['action'],policy='Review only; no accepted holding, display, invented biography or publication.')
                db.execute('''INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                  VALUES('artwork',%s,'selected_museum_object',%s,%s,%s,%s,%s,%s)''',(aid,sid,key,r['url'],json.dumps(evidence,ensure_ascii=False),r['source']['at'],core.ACTOR))
                db.execute('''INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                  VALUES('artwork',%s,%s,%s,%s,%s,%s)''',(aid,'dk-ch-selected-'+r['museum'],r['native_id'],r['url'],sid,r['source']['at']))
                after=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']
                if item['action']=='new':assert after['status']=='review' and after['published_at'] is None and after['current_institution_id'] is None
                else:assert after==item['work']
            receipt=dict(at=core.now(),target=target,key=key,action=item['action'],artwork_id=aid,slug=after['slug'],plan_sha256=review['plan_sha256'])
            save(RUN/'metadata-applied'/target/(key+'.json'),receipt);receipts.append(receipt)
            print(target,key,item['action'],flush=True)
    save(RUN/(target+'-metadata-applied.json'),receipts)

BASEL_IMAGE_KEYS = {'basel-'+x for x in ('1077','969','1207','1482','1569','40269','1516')}
BASEL_POLICY = 'https://download.kunstmuseumbasel.ch/app/snippets/infoClaim.html'

def commons_fields(soup):
    fields={}
    for tr in soup.select('tr'):
        cells=tr.find_all(['td','th'],recursive=False)
        if len(cells)==2:
            label=cells[0].get_text(' ',strip=True)
            if label in ('Date','Collection','Accession number','Source/Photographer','Title','Notes'):
                fields[label]=cells[1].get_text(' ',strip=True)
    # Only actual file licence templates, never site footer or structured-data licences.
    licenses=[t.get_text(' ',strip=True) for t in soup.select('.licensetpl')]
    return fields,licenses

def image_plan():
    plan,review=b.reviewed_plan('metadata')
    allowed=set(review['selected_keys']);selected=[];held=[]
    commons={r['key']:r for r in load(RUN/'commons-selected-evidence.json')}
    basel_terms=load(RUN/'captures/basel-image-use-terms.receipt.json')
    assert core.sha((RUN/'captures/basel-image-use-terms.html').read_bytes())==basel_terms['sha256']
    donated=b.BeautifulSoup((RUN/'captures/hirschsprung-donated.html').read_bytes(),'html.parser')
    donated_files={unquote(a['href']).split('/wiki/')[-1].replace('Fil:','File:').replace('_',' ') for a in donated.select('a[href]')}
    for item in plan['targets']['local']:
        r=item['record'];key=r['key']
        if key not in allowed:continue
        if key not in BASEL_IMAGE_KEYS and key not in commons:
            held.append(dict(key=key,reason='No selected, date-eligible, exact-object commercially reusable reproduction; existing images preserved.'));continue
        assert r['date']['last'] is not None and r['date']['last']<=1970
        museum='Kunstmuseum Basel' if r['museum']=='basel' else 'The Hirschsprung Collection'
        im=dict(key=key,title=r['title'],artist=r['creator_label'],external_id=r['native_id'],provider='denmark-switzerland-selected',
            source_record=dict(r,collection_label=museum),targets={})
        if r['museum']=='basel':
            fields=r['fields'];label='Bilddaten gemeinfrei - Kunstmuseum Basel'
            assert fields['ObjDetailRightsTxt']['LabelTxt']==label
            matching=[p for p in fields['ObjDetailMultimediaRef']['Items'] if any(m['full']==fields['DefaultImage'] for m in p['Multimedia'])]
            assert len(matching)==1 and matching[0]['ImageCopyrightTxt']['LabelTxt']==label
            im.update(source_image_url=urljoin('https://sammlung.kunstmuseumbasel.ch/',fields['DefaultImage']),page=r['url'],
                policy_url=BASEL_POLICY,rights_status='public_domain',license_label='Public domain — Kunstmuseum Basel',
                creator_credit=fields['ObjDetailCreditlineTxt']['LabelTxt'],checked_at=core.now(),source_evidence_sha256=r['source']['sha256'],
                identity_basis='Exact official collection object '+r['native_id']+', inventory '+r['accession']+'. DefaultImage matches the individually public-domain-labelled multimedia entry. Museum terms explicitly allow public and commercial use without further permission.',
                rights_evidence=dict(object=r['source'],terms=basel_terms,exact_image_label=label))
        else:
            evidence=commons[key];raw=(RUN/'captures'/(evidence['capture_key']+'.html')).read_bytes()
            assert core.sha(raw)==evidence['receipt']['sha256']
            soup=b.BeautifulSoup(raw,'html.parser');fields,licenses=commons_fields(soup)
            assert 'Hirschsprung Collection' in fields['Collection']
            assert any('Public domain' in t for t in licenses)
            assert r['commons_title'] in donated_files,key
            status='public_domain';uri='https://creativecommons.org/publicdomain/mark/1.0/';label='Public Domain Mark 1.0'
            if key=='hirschsprung-ancher-maid-kitchen':
                assert any('Attribution 3.0 Unported' in t for t in licenses)
                status='cc_by';uri='https://creativecommons.org/licenses/by/3.0/';label='CC BY 3.0'
            elif key=='hirschsprung-kroyer-summer-evening':
                assert any('CC0 1.0' in t for t in licenses)
                status='cc0';uri='https://creativecommons.org/publicdomain/zero/1.0/';label='CC0 1.0'
            previews=[p for p in evidence['previews'] if 500<=int(p['label'].split(' × ')[0].replace(',',''))<=1600]
            assert previews
            credit=museum
            if 'Google Cultural Institute' in fields['Source/Photographer']:credit+=' / Google Art Project'
            elif key=='hirschsprung-kroyer-summer-evening':credit+=' / Statens Museum for Kunst (Photo)'
            if key=='hirschsprung-ancher-maid-kitchen':credit+='; Commons upload by Villy Fink Isaksen'
            im.update(source_image_url=previews[0]['url'].split('?')[0],page=evidence['receipt']['url'],policy_url=uri,rights_status=status,
                license_label=label,creator_credit=credit,checked_at=core.now(),source_evidence_sha256=evidence['receipt']['sha256'],
                identity_basis='Museum-authored creator, title and date reconciled to the exact Commons file and Hirschsprung inventory '+fields['Accession number']+'. Museum photo page directs visitors to this public selection; the specific file licence and reproduction origin are retained separately from ordered-photo terms.',
                rights_evidence=dict(file=evidence['receipt'],fields=fields,file_license_templates=licenses,
                  museum_photo_policy=load(RUN/'captures/index-hirschsprung-rights.receipt.json'),
                  museum_linked_selection=load(RUN/'captures/hirschsprung-donated.receipt.json'),
                  interpretation='Selected existing public reproduction, not a photo order; independent explicit file licence/PD statement retained. No paid-photo contract or museum endorsement claimed.'))
        im['attribution_text']=r['creator_label']+'. '+r['title']+' ('+r['date']['display']+'). '+im['creator_credit']+'. '+im['license_label']+' ('+im['policy_url']+'). Source: '+im['page']+'. Accessed '+im['checked_at']+'. Full-frame proportional resize and JPEG compression; no crop or generated content.'
        for target in ('local','cloud'):
            receipt=load(RUN/'metadata-applied'/target/(key+'.json'))
            with connect(target) as db:
                row=db.execute('SELECT to_jsonb(a) row,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope FROM artworks a WHERE id=%s',(receipt['artwork_id'],)).fetchone()
                assert row['date_scope']=='eligible' and row['row']['primary_media_id'] is None and row['row']['status']=='review'
                im['targets'][target]=dict(id=receipt['artwork_id'],before=row['row'])
        im['artwork_id']=im['targets']['local']['id'];selected.append(im)
    assert len(selected)==16
    save(RUN/'image-selection.json',selected);save(RUN/'image-held.json',held);save(BACKUP/'image-target-preimages.json',selected)
    print('Selected',len(selected),'images; sha256',core.sha((RUN/'image-selection.json').read_bytes()),flush=True)

def image_upload():
    b.image_upload(adapter_version='denmark-switzerland-selected-v1',selection_name='image-download-selection.json')

def verify():
    plan,review=b.reviewed_plan('metadata');geo=load(RUN/'geography-plan.json');images=load(RUN/'image-upload-summary.json')
    result=dict(at=core.now(),targets={},limits='Selected first batch, not nationwide coverage. No publication, accepted holding, display claim or 10-million-row load-test assertion.')
    for target in ('local','cloud'):
        selected=[p for p in plan['targets'][target] if p['record']['key'] in review['selected_keys']]
        ids=[p.get('artwork_id') or p['work']['id'] for p in selected]
        with connect(target) as db:
            rows=db.execute('''SELECT a.id::text,a.slug,a.title,a.status,a.published_at,a.research_candidate,a.primary_media_id::text,a.unlinked_creator_label,
              a.creation_year_start,a.creation_year_end,a.date_precision,a.current_institution_id::text,
              (SELECT count(*) FROM artwork_artists x WHERE x.artwork_id=a.id) linked_creators,
              (SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_id=%s AND c.field_name='selected_museum_object') source_citations,
              (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='review') review_holdings,
              (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND (l.claim_type='display' OR l.review_state='accepted')) accepted_or_display_claims,
              m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,m.license_url,
              (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=m.id) rights_evidence
              FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.slug''',(uid('source'),ids)).fetchall()
            byid={r['id']:r for r in rows};assert len(rows)==47 and all(r['source_citations']==1 for r in rows)
            new=[byid[p['artwork_id']] for p in selected if p['action']=='new']
            assert len(new)==46 and all(r['status']=='review' and r['research_candidate'] and r['published_at'] is None and r['current_institution_id'] is None and r['review_holdings']==1 and r['accepted_or_display_claims']==0 for r in new)
            for p in selected:
                after=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(p.get('artwork_id') or p['work']['id'],)).fetchone()['row']
                if p['action']=='existing':assert after==p['work'],'Existing record changed'
                else:
                    date=p['record']['date']
                    assert (after['creation_year_start'],after['creation_year_end'],after['date_precision'],after['date_display'])==(date['first'],date['last'],date['precision'],date['display'])
                    assert after['unlinked_creator_label']==p['record']['creator_label']
            delivered=[r for r in rows if r['primary_media_id'] in {i['media_id'] for i in images}]
            assert len(delivered)==len(images)
            assert all(r['byte_size']<=100000 and r['rights_evidence']==1 and r['license_url'] for r in delivered)
            museums=db.execute('''SELECT i.id::text,i.slug,i.status,p.name city,p.country_code,
              ARRAY(SELECT vp.country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id) venue_countries
              FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[]) ORDER BY i.slug''',([g['id'] for g in geo['targets'][target]],)).fetchall()
            assert len(museums)==6
            for g in geo['targets'][target]:
                m=next(i for i in museums if i['slug']==g['fact']['slug'])
                assert m['country_code']==g['fact']['country'] and m['venue_countries']==[g['fact']['country']]
                assert m['status']==(g['before']['status'] if g['before'] else 'review')
                venue=db.execute('SELECT status FROM institution_venues WHERE id=%s',(uid('venue/'+g['fact']['slug']),)).fetchone()
                assert venue['status']=='review'
            result['targets'][target]=dict(new_artworks=46,existing_enriched=1,new_images=len(delivered),new_institutions=2,geography_repairs=4,new_venues=6,
                unresolved_creator_labels=sum(r['linked_creators']==0 for r in new),unknown_numeric_dates=sum(r['creation_year_start'] is None for r in new),museums=museums,artworks=rows)
            print(target,'verified',len(new),'new review works,',len(delivered),'images, 6 museum geographies',flush=True)
    def canonical(t):return [{k:v for k,v in r.items() if k not in ('id','primary_media_id')} for r in result['targets'][t]['artworks']]
    assert canonical('local')==canonical('cloud')
    save(RUN/'verification.json',result)

def public_verify():
    site='https://artline-web-lpuqqlugnq-ew.a.run.app';images=load(RUN/'image-upload-summary.json')
    def one(im):
        r=b.requests.get(site+im['path'],timeout=(10,45));r.raise_for_status()
        assert len(r.content)==im['bytes']<=100000 and core.sha(r.content)==im['sha256'] and r.headers.get('Content-Type','').startswith('image/jpeg')
        return dict(url=r.url,status=r.status_code,sha256=core.sha(r.content),bytes=len(r.content),verified=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,images))
    museums=[]
    for slug,city,country,_,_ in GEO:
        r=b.requests.get(site+'/api/backend/v1/museums/'+slug,timeout=(10,30))
        if slug in NEW_INSTITUTIONS and r.status_code==404:
            museums.append(dict(slug=slug,status=404,note='New review-only museum, with unaccepted holding assertions, not publicly listed.'));continue
        r.raise_for_status();body=r.json()
        assert body['slug']==slug and any(v['country']==country for v in body['venues'])
        museums.append(dict(slug=slug,status=r.status_code,venues=body['venues'],verified=True))
    save(RUN/'public-verification.json',dict(at=core.now(),images=results,museum_details=museums))
    print('Verified',len(results),'public image byte streams and existing museum geography; review-only records remain unpublished',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['research','backup-start','backup-verify','select-pages','selected-capture','geo-plan','geo-apply','basel-native','parse','metadata-plan','metadata-apply','image-plan','image-upload','verify','public-verify'])
    p.add_argument('--target',choices=['local','cloud'])
    args=p.parse_args()
    if args.phase in ('geo-apply','metadata-apply'):
        assert args.target;{'geo-apply':geo_apply,'metadata-apply':metadata_apply}[args.phase](args.target)
    else:{'research':research,'backup-start':backup_start,'backup-verify':backup_verify,'select-pages':select_pages,'selected-capture':selected_capture,'geo-plan':geo_plan,'basel-native':basel_native,'parse':parse_records,'metadata-plan':metadata_plan,'image-plan':image_plan,'image-upload':image_upload,'verify':verify,'public-verify':public_verify}[args.phase]()
