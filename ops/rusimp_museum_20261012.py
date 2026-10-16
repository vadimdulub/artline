#!/usr/bin/env python3
"""Museum of Russian Impressionism: source capture and reviewed production delivery."""
import collections, concurrent.futures, datetime, gzip, hashlib, importlib.util, io, json, re, sys, time
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
import exhibitions_common as c

OP='russian-impressionism-museum-20261012'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ROOT=c.ROOT
OLD='https://ftp.rusimp.su'
NEW='https://www.rusimp.su'
MID=c.uid(OP+'/museum');SID=c.uid(OP+'/source')
def uid(s): return c.uid(OP+'/'+s)
def save(name,data): c.save(DATA/name,data)
def load(name): return c.load(DATA/name)
def serial(x): return json.loads(json.dumps(x,default=str))
def selected_objects():
    rows=load('parsed-objects-v2.json')
    for r in rows:
        if r['hold']and r['hold'].startswith('Created after 1970'):
            r['hold']=None;r['date_scope_exception']='User explicitly requested including all dated artworks from this museum, 12 October 2026.'
    return [r for r in rows if not r['hold']]
def all_artists():return load('artist-decisions.json')+load('artist-exception-extension.json')
def capture(url):
    key=c.sha(url.encode());p=DATA/'captures'/(key+'.json');b=DATA/'captures'/(key+'.body.gz')
    if p.exists():
        rc=c.load(p);raw=gzip.decompress(b.read_bytes());assert c.sha(raw)==rc['sha256'];return raw,rc
    host=urlsplit(url).hostname;hold=DATA/'access-holds'/(host+'.json')
    assert not hold.exists(),'Recorded provider access hold'
    # Legacy official host has an expired/mismatched TLS deployment. Public GETs
    # carry no credentials; transport limitation is explicit in every receipt.
    verify=host!='ftp.rusimp.su'
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    r=requests.get(url,timeout=(12,45),verify=verify,headers={'User-Agent':'Artline catalogue source research; selected museum records'})
    rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=c.now(),sha256=c.sha(r.content),bytes=len(r.content),content_type=r.headers.get('content-type'),body_path=str(b),tls_verified=verify)
    b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(gzip.compress(r.content,mtime=0));c.save(p,rc)
    if r.status_code in (401,403,429):c.save(hold,rc)
    return r.content,rc
def soup(url):
    raw,rc=capture(url);assert rc['status']==200,(url,rc['status']);return BeautifulSoup(raw,'html.parser'),rc
def text(el):return el.get_text(' ',strip=True) if el else ''
def discover():
    indexes={};objects={};artists={}
    for lang in ['ru','en']:
        s,rc=soup(OLD+'/'+lang+'/collection');indexes[lang]=dict(receipt=rc,text=text(s))
        for kind,dest in [('object',objects),('artist',artists)]:
            for a in s.select('a[href]'):
                m=re.fullmatch('/'+lang+'/collection/'+kind+r'/(\d+)',a['href'])
                if m:dest.setdefault(m[1],{})[lang]=dict(url=urljoin(OLD,a['href']),label=text(a))
        indexes[lang]['pagination']=[a['href'] for a in s.select('a[href]') if 'page=' in a['href']]
    save('collection-index.json',dict(indexes=indexes,objects=objects,artists=artists))
    s,rc=soup(NEW+'/exhibitions');events=[]
    for card in s.select('.event-card'):
        title=text(card.select_one('h3'))
        if not title:continue
        links=[urljoin(NEW,a['href'])for a in card.select('a[href]') if text(a).startswith('Подробнее')]
        events.append(dict(title=title,description=text(card.select_one('p')),text=text(card),tags=[text(x)for x in card.select('.tag')],urls=links,receipt=rc))
    save('exhibition-index.json',events)
    print('Discovered',len(objects),'collection identities,',len(artists),'first-page artists,',len(events),'exhibition cards',flush=True)
def fetch_objects():
    d=load('collection-index.json');jobs=[(n,lang,r) for n,v in d['objects'].items()for lang,r in v.items()]
    def one(job):
        n,lang,r=job;s,rc=soup(r['url']);main=s.select_one('main')or s
        out=dict(id=n,lang=lang,index=r,receipt=rc,headings=[dict(tag=a.name,text=text(a),html=str(a))for a in main.select('h1,h2,h3,h4,h5')],text=text(main),images=[dict(a.attrs)for a in main.select('img')],links=[dict(url=urljoin(OLD,a['href']),label=text(a))for a in main.select('a[href]')])
        save('objects/'+n+'-'+lang+'.json',out);return n
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as p:
        for i,n in enumerate(p.map(one,jobs),1):
            if i%10==0:print('Captured objects',i,'/',len(jobs),flush=True)
def fetch_context():
    artists={}
    for p in (DATA/'objects').glob('*.json'):
        o=c.load(p)
        for a in o['links']:
            m=re.search(r'/(ru|en)/collection/artist/(\d+)$',a['url'])
            if m:artists[(m[2],m[1])]=a['url']
    def artist(job):
        (n,lang),url=job;s,rc=soup(url)
        out=dict(id=n,lang=lang,receipt=rc,headings=[text(a)for a in s.select('h1')],text=text(s),objects=[a['href']for a in s.select('a[href]')if '/collection/object/'in a['href']])
        save('artists/'+n+'-'+lang+'.json',out)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(artist,artists.items()))
    s,rc=soup(NEW+'/sitemap.xml');urls=[a.text for a in s.select('loc')if '/exhibitions/'in a.text]
    urls+=list({u for e in load('exhibition-index.json')for u in e['urls']if '.rusimp.su' in u and u not in urls and '/permanent-exhibition'not in u})
    def event(url):
        try:
            s,rc=soup(url)
            out=dict(url=url,receipt=rc,headings=[dict(tag=a.name,text=text(a))for a in s.select('h1,h2,h3')],text=text(s),links=[dict(url=urljoin(url,a['href']),label=text(a))for a in s.select('a[href]')],images=[dict(a.attrs)for a in s.select('img')])
            save('events/'+c.sha(url.encode())+'.json',out)
        except Exception as exc:save('event-errors/'+c.sha(url.encode())+'.json',dict(url=url,error=str(exc)[:500]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(event,urls))
    print('Context captured',len(artists),'artist languages',len(urls),'event pages',flush=True)

def baseline():
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        people=serial(db.execute("SELECT id,slug,display_name,normalized_name,birth_year,death_year,status FROM artists").fetchall())
        aliases=serial(db.execute('SELECT artist_id,alias FROM artist_aliases').fetchall())
        institutions=serial(db.execute("SELECT * FROM institutions WHERE name ILIKE '%impression%' OR name ILIKE '%импресс%' OR website_url ILIKE '%rusimp%'").fetchall())
        exhibitions=serial(db.execute("SELECT * FROM exhibitions WHERE start_year>=2014").fetchall())
        refs=serial(db.execute("SELECT * FROM exhibition_source_records WHERE source_url ILIKE '%rusimp%'").fetchall())
        ext=serial(db.execute("SELECT * FROM external_identifiers WHERE canonical_url ILIKE '%rusimp%' OR scheme ILIKE '%rusimp%'").fetchall())
    out=dict(at=c.now(),artists=people,aliases=aliases,institutions=institutions,exhibitions=exhibitions,exhibition_refs=refs,identifiers=ext)
    save('baseline.json.gz',out);c.save(BACKUP/'baseline.json.gz',out)
    print('Baseline',len(people),'artists',len(exhibitions),'recent events',len(refs),'source refs',len(ext),'native ids',flush=True)

def parse_objects():
    rows=[]
    for n,idx in load('collection-index.json')['objects'].items():
        versions={}
        for lang in ['ru','en']:
            d=load('objects/'+n+'-'+lang+'.json');s=BeautifulSoup(gzip.decompress(Path(d['receipt']['body_path']).read_bytes()),'html.parser');box=s.select_one('.object-title');a=box.select_one('h4 a');h=[text(x)for x in box.select('h5')];imgs=[urljoin(OLD,a.get('src'))for a in s.select('img[src]')if '/uploads/images/' in a['src']]
            versions[lang]=dict(heading=text(box.select_one('h1')),creator=text(a),creator_native=a['href'].rsplit('/',1)[1]if a else None,medium=next((v for v in h if v and not re.fullmatch(r'[\d.,\sXx×х]+',v)),None),dimensions=next((v for v in h if re.fullmatch(r'[\d.,\sXx×х]+',v)),None),images=imgs,receipt=d['receipt'])
        en=versions['en'];ru=versions['ru'];heading=en['heading'];rm=re.search(r'[.,]\s*((?:(?:Начало|Середина|Вторая треть)\s+)?(?:\d{4}|X|Х).*)$',ru['heading']);assert rm,(n,ru['heading'])
        rdate=rm[1];ru_title=ru['heading'][:rm.start()];em=re.search(r'[.,]\s*((?:\d{4}|Middle|Mid-|Beginning).*)$',heading);title=heading[:em.start()]if em else heading;date=em[1]if em else rdate
        if n=='78':date='Mid-20th century'
        years=[int(y)for y in re.findall(r'\d{4}',rdate)];lo=hi=None;precision='unknown'
        if years:
            lo=years[0];hi=years[-1];precision='exact'if lo==hi else'range'
            if re.search(r'\d0-е|\d0-х',rdate):hi+=9;precision='decade'if lo==hi-9 else'range'
            if re.search(r'\d{4}[–-]\d{4}-е',rdate):hi=years[-1]+9
            if rdate.startswith('Начало'):precision='circa_range'
        if n in ['7','24','30']:
            # Russian label bounds explicit years; English translation expands
            # them into decades. Keep the conservative union and both labels.
            hi={'7':1959,'24':1929,'30':1929}[n];precision='range'
        medium=en['medium']or ru['medium'];work_type='drawing'if n=='224'else'watercolor'if n=='62'else'sculpture'if n in ['152','283']else'painting'
        held='Sculpture excluded by collection scope'if work_type=='sculpture'else'Created after 1970; exception not yet authorized'if hi and hi>1970 else None
        creator=en['creator']or ru['creator'];native=ru['creator_native']
        if n=='62':creator='Oscar Rabin';native='index-rabin' # explicit collection index, object-page creator link absent
        rows.append(dict(native=n,title=title,ru_title=ru_title,date_display=date,year_start=lo,year_end=hi,precision=precision,medium=medium,dimensions=en['dimensions']or ru['dimensions'],work_type=work_type,creator=creator,creator_native=native,versions=versions,image_url=(ru['images']or en['images'])[0],source_url=en['receipt']['url'],hold=held))
    save('parsed-objects-v2.json',rows)
    print('Parsed',len(rows),'held',[(r['native'],r['hold'])for r in rows if r['hold']],flush=True)

def candidate_artists():
    import difflib
    base=load('baseline.json.gz');artists={a['id']:a for a in base['artists']};names=collections.defaultdict(set)
    for a in artists.values():names[c.norm(a['display_name'])].add(a['id'])
    for a in base['aliases']:names[c.norm(a['alias'])].add(a['artist_id'])
    report=[]
    for n in sorted({r['creator_native']for r in load('parsed-objects-v2.json')if not r['hold']}):
        en=load('artists/'+n+'-en.json')if (DATA/'artists'/f'{n}-en.json').exists()else None;ru=load('artists/'+n+'-ru.json')if n!='index-rabin'else dict(headings=['Оскар Яковлевич Рабин']);label=en['headings'][0]if en else ru['headings'][0]
        if n=='index-rabin':label='Oscar Rabin'
        exact=set(names[c.norm(label)])|names[c.norm(ru['headings'][0])];near=difflib.get_close_matches(c.norm(label),list(names),n=5,cutoff=.54);cands=set(exact)|set().union(*(names[k]for k in near));row=dict(native=n,name=label,ru_name=ru['headings'][0],lifespan=(en or ru)['headings'][1:],exact=list(exact),candidates=[artists[k]for k in cands]);report.append(row)
        print(n,label,row['lifespan'],'EXACT',list(exact),[(a['display_name'],a['id'],a['birth_year'],a['death_year'])for a in row['candidates']],flush=True)
    save('artist-candidates.json',report)

def stage_artists():
    reviewed={'15':'9c17e646-0fe9-56e5-85fb-28e16a48182e','2':'9d8fc095-3713-42aa-9729-1ee9dad1adc0','23':'2bbce882-8d94-4ee0-ac51-d56e0178647c','41':'95e18cbf-fea1-4619-a6a6-55086dadb117','49':'ae2baca7-c7ed-4f51-a8b7-b9c7e00e061f'}
    decisions=[]
    for a in load('artist-candidates.json'):
        assert len(a['exact'])<=1
        aid=reviewed.get(a['native'])or next(iter(a['exact']),None);life=re.findall(r'\d{4}',a['lifespan'][0]if a['lifespan']else'');birth=int(life[0])if len(life)==2 else None;death=int(life[1])if len(life)==2 else None
        decisions.append(dict(native=a['native'],id=aid or uid('artist/'+a['native']),action='existing'if aid else'create',name=a['name'],ru_name=a['ru_name'],birth=birth,death=death,basis='Source native identity; exact full name/alias or manually reviewed transliteration with concordant lifespan. Other nearby-name and differing-lifespan artists rejected.',source=load('artists/'+a['native']+'-ru.json')if a['native']!='index-rabin'else load('collection-index.json')['indexes']['ru']))
    save('artist-decisions.json',decisions)
    ids=[a['id']for a in decisions if a['action']=='existing']
    with c.connect()as db:
        works=serial(db.execute('''SELECT a.*,aa.artist_id,ma.storage_path,ma.checksum_sha256,ma.source_page_url,ma.width image_width,ma.height image_height
          FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE aa.artist_id=ANY(%s::uuid[])''',(ids,)).fetchall())
        ext=serial(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",([a['id']for a in works],)).fetchall())
    save('scoped-artworks.json.gz',dict(works=works,identifiers=ext));c.save(BACKUP/'scoped-artworks.json.gz',dict(works=works,identifiers=ext))
    import difflib
    for r in load('parsed-objects-v2.json'):
        if r['hold']:continue
        ap=next(a for a in decisions if a['native']==r['creator_native']);same=[w for w in works if w['artist_id']==ap['id']];candidates=[]
        for w in same:
            score=max(difflib.SequenceMatcher(None,c.norm(r[k]),c.norm(w['title'])).ratio()for k in ['title','ru_title'])
            if score>.54 or (r['year_start']and r['year_start']==w['creation_year_start']):candidates.append((round(score,2),w['id'],w['title'],w['date_display'],w['dimensions_text'],w['storage_path']))
        if candidates:print(r['native'],r['title'],r['date_display'],r['dimensions'],'CANDIDATES',sorted(candidates,reverse=True)[:18],flush=True)
    print('Artists',collections.Counter(a['action']for a in decisions),'scoped works',len(works),flush=True)

def prepare_images():
    from PIL import Image,ImageOps,ImageStat,ImageDraw,ImageFont
    rows=selected_objects()
    def one(r):
        dest=DATA/'images'/(r['native']+'.json')
        if dest.exists():return c.load(dest)
        raw,rc=capture(r['image_url']);assert rc['status']==200 and rc['content_type'].startswith('image/')
        original=Path.home()/'Library/Application Support/Artline/source-images'/OP/(r['native']+'-'+rc['sha256'][:16]+'.jpg');original.parent.mkdir(parents=True,exist_ok=True);original.write_bytes(raw)
        with Image.open(io.BytesIO(raw))as src:im=ImageOps.exif_transpose(src).convert('RGB');ow,oh=im.size
        assert min(ow,oh)>=100 and ImageStat.Stat(im.convert('L')).stddev[0]>2
        im.thumbnail((1600,1600));quality=90
        while True:
            out=io.BytesIO();im.save(out,'JPEG',quality=quality,optimize=True,progressive=True);data=out.getvalue()
            if len(data)<=100000:break
            if quality>45:quality-=5
            else:im.thumbnail((round(im.width*.85),round(im.height*.85)));quality=85
        digest=c.sha(data);path='/assets/artworks/imported/'+OP+'/'+r['native']+'-'+digest[:16]+'.jpg';local=ROOT/'apps/web/public'/path.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(data)
        out=dict(native=r['native'],path=path,local_path=str(local),sha256=digest,width=im.width,height=im.height,bytes=len(data),original_dimensions=[ow,oh],original_path=str(original),receipt=rc,quality=quality,media_id=uid('image/'+r['native']+'/'+digest))
        c.save(dest,out);return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:images=list(pool.map(one,rows))
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for start in range(0,len(images),24):
        canvas=Image.new('RGB',(1600,1800),'#eeeae4');draw=ImageDraw.Draw(canvas)
        for i,im in enumerate(images[start:start+24]):
            r=next(x for x in rows if x['native']==im['native']);x=i%4*400;y=i//4*300
            with Image.open(im['local_path'])as pic:pic.thumbnail((380,244));canvas.paste(pic,(x+(400-pic.width)//2,y+(244-pic.height)//2))
            draw.text((x+8,y+249),r['native']+' / '+r['title'][:39],font=font,fill='black');draw.text((x+8,y+272),r['creator'][:38],font=font,fill='black')
        p=DATA/'visual'/f'{start//24+1:02}.jpg';p.parent.mkdir(exist_ok=True);canvas.save(p,quality=90)
    print('Prepared',len(images),'full-frame images',flush=True)

def image_reconcile():
    from PIL import Image,ImageDraw,ImageFont
    def dh(path):
        with Image.open(path)as src:
            im=src.convert('L').resize((17,16));p=list(im.getdata());return int(''.join('1'if p[y*17+x]>p[y*17+x+1]else'0'for y in range(16)for x in range(16)),2)
    aps={a['native']:a for a in load('artist-decisions.json')};old=load('scoped-artworks.json.gz')['works'];cache={};missing=[]
    for w in old:
        if w['storage_path']:
            p=ROOT/'apps/web/public'/w['storage_path'].lstrip('/')
            if p.exists():cache[w['id']]=dh(p)
            else:missing.append(w['id'])
    matches=[]
    for r in load('parsed-objects-v2.json'):
        if r['hold']:continue
        im=load('images/'+r['native']+'.json');h=dh(im['local_path']);near=[]
        for w in old:
            if w['artist_id']==aps[r['creator_native']]['id'] and w['id']in cache:
                distance=(h^cache[w['id']]).bit_count()
                if distance<65:near.append(dict(distance=distance,work=w))
        if near:matches.append(dict(native=r['native'],title=r['title'],matches=sorted(near,key=lambda x:x['distance'])))
    save('image-reconciliation.json',dict(matches=matches,existing_images_checked=len(cache),missing_local_images=missing))
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17);pairs=[(r,x)for r in matches for x in r['matches']];canvas=Image.new('RGB',(1000,max(1,len(pairs))*320),'#eeeae4');draw=ImageDraw.Draw(canvas)
    for i,(r,x)in enumerate(pairs):
        paths=[load('images/'+r['native']+'.json')['local_path'],str(ROOT/'apps/web/public'/x['work']['storage_path'].lstrip('/'))]
        for j,p in enumerate(paths):
            with Image.open(p)as im:im.thumbnail((480,270));canvas.paste(im,(j*500+(500-im.width)//2,i*320))
        draw.text((8,i*320+274),r['native']+' '+r['title'],font=font,fill='black');draw.text((508,i*320+274),str(x['distance'])+' '+x['work']['title'][:48],font=font,fill='black');draw.text((508,i*320+298),x['work']['id'],font=font,fill='black')
    canvas.save(DATA/'visual/duplicate-pairs.jpg',quality=90)
    print('Image matches',[(r['native'],[(x['distance'],x['work']['id'],x['work']['title'])for x in r['matches']])for r in matches],'Missing',len(missing),flush=True)

def legacy_events():
    jobs=[];idx=[]
    for lang in ['ru','en']:
        s,rc=soup(OLD+'/'+lang+'/exhibitions')
        for a in s.select('a[href]'):
            match=re.fullmatch('/'+lang+r'/exhibitions\?id=(\d+)',a['href'])
            if match:
                url=urljoin(OLD,a['href']);idx.append(dict(id=match[1],lang=lang,url=url,label=text(a),receipt=rc));jobs.append((match[1],lang,url))
    save('legacy-event-index.json',idx)
    def one(job):
        n,lang,url=job;s,rc=soup(url);h=s.select_one('h1')
        out=dict(id=n,lang=lang,title=text(h),receipt=rc,text=text(s),objects=[dict(url=urljoin(OLD,a['href']),label=text(a))for a in s.select('a[href]')if '/collection/object/'in a['href']],links=[dict(url=urljoin(OLD,a['href']),label=text(a))for a in s.select('a[href]')if '/books/'in a['href']])
        save('legacy-events/'+n+'-'+lang+'.json',out)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(one,jobs))
    print('Captured',len(jobs),'legacy event languages',flush=True)

def extend_dates():
    base=load('baseline.json.gz');extra=[]
    for n in ['5','29']:
        en=load('artists/'+n+'-en.json');ru=load('artists/'+n+'-ru.json');name=en['headings'][0];life=re.findall(r'\d{4}',en['headings'][1]);near=[a for a in base['artists']if re.search('britov|radyuk|radiuk|радюк|бритов',a['display_name'],re.I)];assert not near,near
        extra.append(dict(native=n,id=uid('artist/'+n),action='create',name=name,ru_name=ru['headings'][0],birth=int(life[0]),death=int(life[1])if len(life)==2 else None,basis='Explicit museum artist identity and birth/death headings; full production name/alias reconciliation found no candidate.',source=ru))
    save('artist-exception-extension.json',extra)
    save('authorization.json',dict(date='2026-10-12',request='Add all artworks from Museum of Russian Impressionism to my site, plus exhibitions etc.',exhibitions_exception='Include this museum’s exhibitions',artworks_exception='Include all dated museum artworks',medium_scope='Paintings, drawings, prints and icons; existing photography/sculpture exclusions retained.',production_authorized=True,real_local_database='Read only; no local database writes',images='Selected authentic museum reproductions under current requested museum delivery and established direct image workflow; actual restricted/unknown rights retained separately. No independent rights-holder licence asserted.'))
    print('Date exception prepared',len(selected_objects()),'objects',len(all_artists()),'artists',flush=True)

def collection_plan():
    rows=selected_objects();aps={a['native']:a for a in all_artists()}
    for r in rows:
        r.update(artwork_id='229f0a87-dea8-53ff-b6c7-2cc0389f3db7'if r['native']=='50'else uid('artwork/'+r['native']),action='existing'if r['native']=='50'else'create',artist_id=aps[r['creator_native']]['id'],image=load('images/'+r['native']+'.json'))
    with c.connect()as db:
        before={r['id']:r for r in serial(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([r['artwork_id']for r in rows],)).fetchall())};assert list(before)==['229f0a87-dea8-53ff-b6c7-2cc0389f3db7']
        assert before[next(iter(before))]['current_institution_id']is None
        assert not db.execute('SELECT 1 FROM institutions WHERE id=%s OR slug=%s',(MID,'museum-of-russian-impressionism')).fetchone()
    plan=dict(at=c.now(),rows=rows,artists=list(aps.values()),before=before,museum_id=MID,authorization=load('authorization.json'),duplicate_review='1,714 existing artworks scoped to 18 exact matched artists; every available existing image compared by perceptual hash. One exact Yuon composition matched visually despite documented 61x79 vs63x80 cm dimension disagreement; prior metadata and primary image retained. Kuznetsov and Serov same-year/title candidates individually viewed and rejected as different works.',counts=dict(collection_objects=len(rows),new_artworks=sum(r['action']=='create'for r in rows),existing_artworks=1,new_artists=sum(a['action']=='create'for a in aps.values()),existing_artists=sum(a['action']=='existing'for a in aps.values()),new_primary_images=sum(r['action']=='create'for r in rows),new_alternate_images=1,sculptures_excluded=2,post1970_exception_objects=5))
    save('collection-plan.json.gz',plan);c.save(BACKUP/'collection-preimage.json.gz',plan);print(plan['counts'],flush=True)

def upload_images():
    import base64
    from google.cloud import storage
    from google.api_core.exceptions import PreconditionFailed
    spec=importlib.util.spec_from_file_location('rusimp_images',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cred=core.GcloudCredentials();cred.refresh(None);bucket=storage.Client(project='artline-508319',credentials=cred).bucket('artline-508319-images');p=load('collection-plan.json.gz');pin=c.sha((DATA/'collection-plan.json.gz').read_bytes())
    def one(r):
        im=r['image'];dest=DATA/'uploads'/(r['native']+'.json')
        if dest.exists():assert c.load(dest)['plan_sha256']==pin;return
        raw=Path(im['local_path']).read_bytes();assert c.sha(raw)==im['sha256'];blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':OP,'artwork-id':r['artwork_id']};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        resp=requests.get('https://artlines.org'+im['path'],timeout=(15,45));resp.raise_for_status();assert c.sha(resp.content)==im['sha256']
        c.save(dest,dict(at=c.now(),plan_sha256=pin,sha256=im['sha256'],generation=blob.generation,public_bytes_verified=True))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(one,p['rows']))
    print('Uploaded and public-checksum verified',len(p['rows']),'images',flush=True)

def slug(title,key):return (re.sub('[^a-z0-9]+','-',c.norm(title)).strip('-')or'rusimp')[:100]+'-'+key[:8]

def apply_collection():
    from psycopg.types.json import Jsonb
    p=load('collection-plan.json.gz');assert p==c.load(BACKUP/'collection-preimage.json.gz');pin=c.sha((DATA/'collection-plan.json.gz').read_bytes());actor='local-european-research'
    for r in p['rows']:assert load('uploads/'+r['native']+'.json')['plan_sha256']==pin
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(actor,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone(),'Already applied; verify rather than rerun'
        actual={r['id']:r for r in serial(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR UPDATE',(list(p['before']),)).fetchall())};assert actual==p['before']
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='rusimp-object' AND external_id=ANY(%s)",([r['native']for r in p['rows']],)).fetchone()
        db.execute("INSERT INTO institutions(id,slug,name,normalized_name,place_id,website_url,kind,status,description) VALUES(%s,'museum-of-russian-impressionism','Museum of Russian Impressionism','museum of russian impressionism','244cee18-cc19-43ef-851b-a7527faab171',%s,'museum','review',%s)",(MID,NEW,'Moscow museum devoted to Russian Impressionism, opened in 2016. Collection holdings and exhibition loans are recorded separately.'))
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key,priority) VALUES(%s,%s,'Museum of Russian Impressionism — official collection and exhibition catalogues','collection_page',%s,%s,10)",(SID,OP,NEW,OP))
        db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'institution',%s,%s,'museum_identity',%s,%s,now(),%s)",(uid('museum-citation'),MID,SID,NEW+'/about',json.dumps(dict(authorization=p['authorization'],plan_sha256=pin),ensure_ascii=False),actor))
        for a in p['artists']:
            if a['action']=='create':
                ws=[r for r in p['rows']if r['artist_id']==a['id']];years=[y for r in ws for y in [r['year_start'],r['year_end']]if y];birth=a['birth'];death=a['death'];lo=birth or min(years);hi=death or max(years);label=f'{birth}–{death}'if birth and death else('Born '+str(birth)+'; death unknown'if birth else'Documented works '+str(lo)+'–'+str(hi));basis='life'if birth and death else'mixed'if birth else'activity'
                db.execute('''INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',%s,%s)''',(a['id'],slug(a['name'],a['id']),a['name'],a['name'],c.norm(a['name']),birth,death,str(birth)if birth else None,str(death)if death else None,'exact'if birth else None,'exact'if death else None,lo,hi,label,basis,actor,actor))
            else:assert db.execute("SELECT 1 FROM artists WHERE id=%s AND status<>'archived'",(a['id'],)).fetchone()
            if a['native']!='index-rabin':db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artist',%s,'rusimp-artist',%s,%s,%s)",(uid('artist-native/'+a['native']),a['id'],a['native'],a['source']['receipt']['url'],SID))
            db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artist',%s,%s,'rusimp_creator_identity',%s,%s,%s,%s)",(uid('artist-citation/'+a['native']),a['id'],SID,a['source']['receipt']['url'],json.dumps(a,ensure_ascii=False),a['source']['receipt']['retrieved_at'],actor))
        for r in p['rows']:
            aid=r['artwork_id'];im=r['image'];rc=r['versions']['ru']['receipt'];note=dict(operation=OP,source=r,plan_sha256=pin,holdingClaim=True,currentDisplayClaim=False,identityBasis='Exact native collection object, official permanent collection index and bilingual object page; source images visually reviewed.',rights='No reuse licence stated; museum offers image use by enquiry. User collection preference is separate from licence evidence.')
            if r['action']=='create':
                title=r['title'].capitalize()if r['title'].isupper()else r['title']
                db.execute('''INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',(aid,slug(title,aid),title,r['ru_title'],c.norm(title),r['date_display'],r['year_start'],r['year_end'],r['precision'],r['work_type'],r['medium'],r['dimensions'],actor,actor))
                db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,r['artist_id'],'Explicit museum object attribution: '+r['creator']+'. Source: '+r['source_url']))
            db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artwork',%s,'rusimp-object',%s,%s,%s)",(uid('object-native/'+r['native']),aid,r['native'],r['source_url'],SID))
            db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'rusimp_collection_identity',%s,%s,%s,%s,%s)",(uid('object-citation/'+r['native']),aid,SID,r['native'],r['source_url'],json.dumps(note,ensure_ascii=False),rc['retrieved_at'],actor))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(uid('holding/'+r['native']),aid,MID,SID,r['source_url'],json.dumps(note,ensure_ascii=False),rc['retrieved_at']))
            credit=r['creator']+'; Museum of Russian Impressionism';label='No reuse licence stated; museum image-use enquiry policy'
            db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,'Museum of Russian Impressionism','image/jpeg',%s,%s,%s,%s,%s,'unknown',%s,%s,%s,%s,%s,now(),%s)""",(im['media_id'],im['path'],r['source_url'],im['width'],im['height'],im['bytes'],im['sha256'],r['title']+' — '+r['creator'],label,NEW+'/business#images',credit,credit+'. Complete museum source frame; proportional resizing and JPEG compression; no crop.',im['receipt']['retrieved_at'],actor))
            db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)''',(im['media_id'],SID,r['native'],rc['sha256'],r['image_url'],NEW+'/business#images',label+'; current user museum selection and explicit date exceptions are recorded separately.',OP,Jsonb(dict(image=im,authorization=p['authorization'],policy=load('image-policy.json'),plan_sha256=pin))))
            db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,%s,'Complete museum reproduction')",(aid,im['media_id'],0 if r['action']=='create'else 1))
            if r['action']=='create':db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['media_id'],aid))
        assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s',(MID,)).fetchone()['n']==len(p['rows'])
    save('collection-delivered.json',dict(at=c.now(),counts=p['counts'],plan_sha256=pin));print('Collection committed',p['counts'],flush=True)

def fetch_exhibited():
    jobs={}
    for p in (DATA/'legacy-events').glob('*.json'):
        e=c.load(p)
        for obj in e['objects']:
            n=obj['url'].rsplit('/',1)[1];jobs.setdefault(n,{})[e['lang']]=obj['url']
    def one(job):
        n,urls=job;url=urls.get('ru')or urls['en'];s,rc=soup(url);box=s.select_one('.object-title');assert box
        h=[text(a)for a in box.select('h5')];a=box.select_one('h4');holder=text(box.select_one('p'))
        # The collection title block is followed by the source holding line.
        out=dict(native=n,url=url,receipt=rc,title=text(box.select_one('h1')),creator=text(a),creator_url=urljoin(OLD,a.select_one('a')['href'])if a and a.select_one('a')else None,medium=next((v for v in h if v and not re.fullmatch(r'[\d.,\sXx×х]+',v)),None),dimensions=next((v for v in h if re.fullmatch(r'[\d.,\sXx×х]+',v)),None),holding_label=holder,object_title_html=str(box),images=[urljoin(OLD,a['src'])for a in s.select('img[src]')if '/uploads/images/'in a['src']],text=text(s))
        save('exhibited-objects/'+n+'.json',out)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(one,jobs.items()))
    print('Exhibited native objects captured',len(jobs),flush=True)

def event_plan():
    # Current official archive cards, manually reconciled to legacy native IDs.
    native={13:'49',14:'47',15:'45',16:'44',17:'46',18:'43',19:'42',20:'40',21:'41',22:'39',23:'38',24:'37',25:'35',26:'36',27:'33',28:'34',29:'32',30:'30',31:'28',32:'26',33:'20',34:'21',35:'16',36:'15',37:'14',38:'13',39:'12',40:'10',41:'9',42:'8',43:'7',44:'4',12:'48'}
    english={0:'A Fairy Tale Nearby',1:'The Age of Museum Poets: Vadim Znamenov and His Peterhof',2:'The Excellent: Exhibition in Tver',8:'The Zvantseva School: A Laboratory of Modernism',9:'Metropolitan Jam: Exhibition in Rostov Veliky',10:'Behind the Mask',11:'One of Us: Vladimir Gilyarovsky',12:'Les Fauves Russes',13:'Matisse Remix',14:'Depicting the Air: Russian Impressionism',15:'The New Society of Artists',16:'Beautiful Life Magazine',17:'Beautiful Life Magazine: The 21st Century',18:'Group of 13: Through the Alleys of Time',19:'The Artist Is Unknown: Touch upon the Essential',20:"Dobychina’s Choice",21:'Fragments of Russian Impressionism',22:'The Excellent',23:'Mirages: The Saratov School of Painting',24:'Alexander Savinov: Mirages',25:'Points of View',26:'Points of View: Feodor Chaliapin',27:'Avant-Garde: On a Cart to the 21st Century',28:'The Art of Transporting Art',29:'Other Shores: Russian Art in New York, 1924',30:'Seekers of Art',31:'Sergey Vinogradov: Painted Life',32:'Yuri Annenkov: Revolution Behind the Door',33:'Impressionism and Spanish Art',34:'A Place in the Sun: Benkov / Fechin',35:'Nikolay Meshcherin: Away from Vanity',36:'David Burliuk: I Speak Out!',37:'Impressionism in the Avant-Garde',38:'Wives',39:'Mikhail Shemyakin: An Entirely Different Artist',40:'Avocations: The Private Collection of Vladimir Spivakov',41:'Armenian Impressionism: From Moscow to Paris',42:'Elena Kiseleva: The Elegant Epoch',43:'Valeriy Koshlyakov: Elisions',44:'Arnold Lakhovsky: Enchanted Pilgrim',46:'Fragile Whims: From Confectionery to Museum'}
    cards=load('exhibition-index.json');events=[]
    def day(x):
        d,mo,y=map(int,x.split('.'));return datetime.date(y+2000 if y<100 else y,mo,d).isoformat()
    for i,title in english.items():
        e=cards[i];ds=re.findall(r'\d{1,2}\.\d{1,2}\.\d{2,4}',e['tags'][-1]);assert len(ds)==2,(i,ds)
        start,end=map(day,ds);note=[]
        if i==46:start='2026-06-25';note.append('Archive card incorrectly prints 25.06.25; dedicated detail explicitly starts 2026-06-25. Dedicated detail used; original card retained.')
        key='legacy/'+native[i]if i in native else'current/'+str(i);url=e['urls'][0];nid=native.get(i)
        sources=[dict(receipt=e['receipt'],data=e)]
        for lang in ['ru','en']:
            path=DATA/'legacy-events'/f'{nid}-{lang}.json'
            if nid and path.exists():sources.append(dict(receipt=c.load(path)['receipt'],data=c.load(path)))
        # Later official RU archive provides extensions and corrections to the
        # earlier English translation; retain every source date for auditing.
        if i in [14,31,37,39]:note.append('Legacy English date differs from the current Russian archive. Current Russian archive dates used; original values preserved in source records.')
        ev=dict(id=uid('event/'+key),key=key,native=nid,title=title,original_title=e['title'],start_date=start,end_date=end,start_year=int(start[:4]),end_year=int(end[:4]),date_display=start+' – '+end,date_precision='day',event_state='announced'if start>'2026-10-12'else'held',source_url=url,sources=sources,notes=note,city='Moscow',country='Russia',country_code='RU',venue='Museum of Russian Impressionism',institution_id=MID)
        if i==0:ev.update(city='Veliky Novgorod',venue="Exhibition Halls at Yaroslav’s Court, Novgorod Museum-Reserve",institution_id=None)
        if i==2:ev.update(city='Tver',venue='Tver Regional Picture Gallery',institution_id=None)
        if i==9:ev.update(city='Rostov Veliky',venue='Rostov Kremlin Museum-Reserve',institution_id=None)
        if i==21:ev.update(city='Zheleznogorsk',venue='Zheleznogorsk Museum of Local Lore',institution_id=None)
        for path in (DATA/'events').glob('*.json'):
            detail=c.load(path)
            if detail['url']==url:ev['sources'].append(dict(receipt=detail['receipt'],data=detail))
        events.append(ev)
    extras={'17':('Abram Arkhipov','2019-02-13','2019-05-19'),'18':('Semyon Nikiforov','2018-10-03','2019-01-27'),'19':('Igor Grabar','2018-05-30','2018-09-19'),'22':('Nicolai Fechin',None,None),'24':('Brodsky and Kostandi','2019-06-05','2019-09-24'),'25':('Konstantin Gorbatov','2019-10-10','2020-01-26'),'27':('Nikolai Dubovskoy','2020-02-13','2020-08-23'),'29':('Konstantin Korovin and Valentin Serov','2020-09-09','2021-03-31'),'31':('Fifth Anniversary Special Project','2021-04-21','2021-08-29')}
    for n,(title,start,end)in extras.items():
        d=load('legacy-events/'+n+'-ru.json');notes=[];sources=[dict(receipt=d['receipt'],data=d)];sy=int(start[:4])if start else None;ey=int(end[:4])if end else None
        if n in ['17','18']:
            notes.append('Conflicting opening days in official descriptions; day withheld. Original header/body dates retained.');start=None
        if n=='19':
            notes.append('The Arkhipov 2019 source explicitly identifies the Grabar display as the 2018 beginning of this series; exact month/day from dedicated Grabar page.');s=load('legacy-events/17-ru.json');sources.append(dict(receipt=s['receipt'],data=s))
        if n=='22':notes.append('Header says 4 October–27 January but omits years. Text precedes summer 2019 Fechin/Benkov show; likely 2018–2019 remains unasserted. Historical occurrence documented in official archive.')
        events.append(dict(id=uid('event/legacy/'+n),key='legacy/'+n,native=n,title=title,original_title=d['title'],start_date=start,end_date=end,start_year=sy,end_year=ey,date_display=(str(sy)+' – '+str(ey)if sy else'4 October – 27 January; years unresolved'),date_precision='day'if start and end else'mixed'if end else'unknown',event_state='held',source_url=d['receipt']['url'],sources=sources,notes=notes,city='Moscow',country='Russia',country_code='RU',venue='Museum of Russian Impressionism',institution_id=MID))
    own={r['native']:r for r in load('collection-plan.json.gz')['rows']};entries=[];publications=[];participants=[];aps=all_artists();by_native={a['native']:a for a in aps}
    for e in events:
        sources=[c.load(path)for lang in ['ru','en']if e['native']and(path:=DATA/'legacy-events'/f"{e['native']}-{lang}.json").exists()];objects={a['url'].rsplit('/',1)[1]:a for source in sources for a in source['objects']}
        for n,a in objects.items():
            r=load('exhibited-objects/'+n+'.json');assert not r['medium']or not re.search('бронз|скульп|фотограф|bronze|sculpt|photograph',r['medium'],re.I)
            date=re.search(r'(?:, |\. |\()((?:\d{4}|Вторая|середина|конец|Без даты).*)$',r['title']);entry=dict(id=uid('entry/'+e['key']+'/'+n),event_id=e['id'],native=n,artwork_id=own[n]['artwork_id']if n in own else None,title_label=r['title'][:date.start()]if date else r['title'],creator_label=r['creator']or'Anonymous',date_label=date[1].rstrip(')')if date else None,medium_label=r['medium'],dimensions_label=r['dimensions'],source=r,participation='exhibited',basis='Exact native object listed under Exhibits on official exhibition page; not a claim of museum ownership or of checklist completeness.');entries.append(entry)
            if r['creator_url']:
                an=r['creator_url'].rsplit('/',1)[1];ap=by_native.get(an)
                if ap and not any(x['event_id']==e['id']and x['artist_id']==ap['id']for x in participants):participants.append(dict(id=uid('participant/'+e['key']+'/'+ap['id']),event_id=e['id'],artist_id=ap['id'],name=r['creator'],source_native=n))
        for source in sources:
            for book in source['links']:
                if book['label']and not any(x['event_id']==e['id']and x['url']==book['url']for x in publications):publications.append(dict(id=uid('publication/'+e['key']+'/'+book['url']),event_id=e['id'],url=book['url'],title=book['label'],source_url=source['receipt']['url']))
    with c.connect()as db:
        existing=serial(db.execute('SELECT id,title,start_year FROM exhibitions WHERE id=ANY(%s::uuid[]) OR normalized_title=ANY(%s)',([e['id']for e in events],[c.norm(e['title'])for e in events]+[c.norm(e['original_title'])for e in events])).fetchall())
    # Historical same-title shows can exist; current museum title/date identities must not.
    conflicts=[x for x in existing if any(x['start_year']==e['start_year']and c.norm(x['title'])in [c.norm(e['title']),c.norm(e['original_title'])]for e in events)];assert not conflicts,conflicts
    plan=dict(at=c.now(),events=events,entries=entries,participants=participants,publications=publications,authorization=load('authorization.json'),same_title_prior=existing,counts=dict(events=len(events),held=sum(e['event_state']=='held'for e in events),announced=sum(e['event_state']=='announced'for e in events),undated=sum(e['start_year']is None for e in events),entries=len(entries),exact_artwork_links=sum(bool(e['artwork_id'])for e in entries),artist_connections=len(participants),publications=len(publications)),coverage='Current archive and all legacy linked exhibition pages inspected; artwork lists are partial. Permanent collection not counted as a dated exhibition. Borrowed works are not assigned museum holdings. Named concurrent special projects remain distinct; recurring archive cards deduplicated.')
    save('event-plan.json.gz',plan);c.save(BACKUP/'event-preimage.json.gz',plan);print(plan['counts'],flush=True)

def exhibition_images():
    from PIL import Image,ImageOps,ImageStat,ImageDraw,ImageFont
    p=load('event-plan.json.gz');own={r['native']:r for r in load('collection-plan.json.gz')['rows']}
    def one(e):
        n=e['native'];dest=DATA/'exhibition-images'/(n+'.json')
        if dest.exists():return c.load(dest)
        if n in own:
            im=own[n]['image']|dict(reused_collection_image=True);c.save(dest,im);return im
        assert len(e['source']['images'])==1,(n,e['source']['images'])
        url=e['source']['images'][0];raw,rc=capture(url);assert rc['status']==200 and rc['content_type'].startswith('image/')
        original=Path.home()/'Library/Application Support/Artline/source-images'/OP/('exhibition-'+n+'-'+rc['sha256'][:16]+'.jpg');original.write_bytes(raw)
        with Image.open(io.BytesIO(raw))as src:im=ImageOps.exif_transpose(src).convert('RGB');ow,oh=im.size
        assert min(ow,oh)>=100 and ImageStat.Stat(im.convert('L')).stddev[0]>2
        im.thumbnail((1600,1600));quality=90
        while True:
            out=io.BytesIO();im.save(out,'JPEG',quality=quality,optimize=True,progressive=True);data=out.getvalue()
            if len(data)<=100000:break
            if quality>45:quality-=5
            else:im.thumbnail((round(im.width*.85),round(im.height*.85)));quality=85
        digest=c.sha(data);path='/assets/artworks/imported/'+OP+'/exhibition-'+n+'-'+digest[:16]+'.jpg';local=ROOT/'apps/web/public'/path.lstrip('/');local.write_bytes(data)
        result=dict(native=n,path=path,local_path=str(local),sha256=digest,width=im.width,height=im.height,bytes=len(data),original_dimensions=[ow,oh],original_path=str(original),receipt=rc,quality=quality,reused_collection_image=False)
        c.save(dest,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:images=list(pool.map(one,p['entries']))
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for start in range(0,len(images),20):
        canvas=Image.new('RGB',(1600,1700),'#eeeae4');draw=ImageDraw.Draw(canvas)
        for i,im in enumerate(images[start:start+20]):
            e=next(x for x in p['entries']if x['native']==im['native']);x=i%4*400;y=i//4*340
            with Image.open(im['local_path'])as pic:pic.thumbnail((380,280));canvas.paste(pic,(x+(400-pic.width)//2,y+(280-pic.height)//2))
            draw.text((x+8,y+287),im['native']+' / '+e['title_label'][:37],font=font,fill='black');draw.text((x+8,y+310),e['creator_label'][:38],font=font,fill='black')
        canvas.save(DATA/'visual'/f'exhibition-{start//20+1:02}.jpg',quality=90)
    print('Prepared exhibition images',len(images),flush=True)

def upload_exhibition_images():
    import base64
    from google.cloud import storage
    from google.api_core.exceptions import PreconditionFailed
    review=load('exhibition-visual-review.json');assert len(review['reviewed_native_ids'])==74
    spec=importlib.util.spec_from_file_location('rusimp_images',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cred=core.GcloudCredentials();cred.refresh(None);bucket=storage.Client(project='artline-508319',credentials=cred).bucket('artline-508319-images');pin=c.sha((DATA/'event-plan.json.gz').read_bytes())
    def one(e):
        im=load('exhibition-images/'+e['native']+'.json');dest=DATA/'exhibition-uploads'/(e['native']+'.json')
        if dest.exists():assert c.load(dest)['plan_sha256']==pin;return
        raw=Path(im['local_path']).read_bytes();assert c.sha(raw)==im['sha256']
        if not im['reused_collection_image']:
            blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':OP,'source-object-id':e['native']};blob.cache_control='public,max-age=31536000,immutable'
            try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
            except PreconditionFailed:blob.reload(timeout=30)
            assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status();assert c.sha(response.content)==im['sha256']
        c.save(dest,dict(at=c.now(),plan_sha256=pin,sha256=im['sha256'],public_bytes_verified=True,reused=im['reused_collection_image']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(one,load('event-plan.json.gz')['entries']))
    print('All 74 exhibition image assets verified; 71 new, three reused',flush=True)

def apply_events():
    from psycopg.types.json import Jsonb
    p=load('event-plan.json.gz');assert p==c.load(BACKUP/'event-preimage.json.gz');pin=c.sha((DATA/'event-plan.json.gz').read_bytes());sourcekey='museum-of-russian-impressionism'
    for e in p['entries']:assert load('exhibition-uploads/'+e['native']+'.json')['plan_sha256']==pin
    base=dict(operation=OP,plan_sha256=pin,authorization=p['authorization'],checklistComplete=False,currentDisplayClaim=False,holdingClaim=False,scope='Museum-specific exception; historical campaign scope remains unchanged.')
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        assert not db.execute('SELECT 1 FROM exhibitions WHERE import_batch=%s',(OP,)).fetchone(),'Already applied; verify instead'
        before=db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held FROM exhibitions WHERE status<>'archived'").fetchone()
        artist_slugs={r['id']:r['slug']for r in db.execute('SELECT id::text,slug FROM artists WHERE id=ANY(%s::uuid[])',([a['id']for a in all_artists()],)).fetchall()}
        with db.pipeline():
            db.execute('INSERT INTO exhibition_research_batches(id,corpus_sha256,manifest) VALUES(%s,%s,%s)',(OP,pin,Jsonb(base|dict(counts=p['counts'],image_policy=load('image-policy.json'),visual_review=load('exhibition-visual-review.json')))))
            for ev in p['events']:
                es=[e for e in p['entries']if e['event_id']==ev['id']]
                basis='Official museum archive and dated exhibition detail; announced future project.'if ev['event_state']=='announced'else'Official museum exhibition archive and detail document the held exhibition; date conflicts are retained.'
                db.execute("""INSERT INTO exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,series_label,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'physical',%s,'Museum of Russian Impressionism','review',%s)""",(ev['id'],ev['title'],c.norm(ev['title']),Jsonb([ev['original_title']]),ev['start_date'],ev['end_date'],ev['start_year'],ev['end_year'],ev['date_display'],ev['date_precision'],ev['event_state'],basis,'partial'if es else'unknown',OP))
                for i,s in enumerate(ev['sources']):
                    rc=s['receipt'];key=ev['key']+'/'+str(i)
                    db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(uid('event-source/'+key),ev['id'],sourcekey,key,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(s['data']),Jsonb(base|dict(research_issues=ev['notes']))))
                source_id=uid('event-source/'+ev['key']+'/0')
                db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(uid('occurrence/'+ev['key']),ev['id'],source_id,ev['institution_id'],ev['venue'],ev['city'],ev['country'],ev['country_code'],ev['start_date'],ev['end_date'],ev['date_display'],Jsonb(base|dict(venue_basis='Explicit official host venue; organizing museum is not substituted for an offsite venue.'))))
                # Register organizer separately from physical venue for the four offsite projects.
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,institution_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,'Museum of Russian Impressionism','organizer',%s)",(uid('organizer/'+ev['key']),ev['id'],source_id,MID,Jsonb(base)))
                details=[]
                for e in es:
                    rc=e['source']['receipt'];sk=ev['key']+'/object/'+e['native'];sid=uid('object-source/'+sk);im=load('exhibition-images/'+e['native']+'.json');oid=uid('exhibition-object/'+e['native'])
                    proof=base|dict(basis=e['basis'],object_receipt=rc,image=im,image_rights='No reuse licence stated; museum image-use enquiry policy',source_list_urls=[s['receipt']['url']for s in ev['sources']if s['data'].get('objects')])
                    db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,ev['id'],sourcekey,sk,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['source']),Jsonb(proof)))
                    db.execute('INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['id'],ev['id'],sid,uid('occurrence/'+ev['key']),e['artwork_id'],e['native'],e['title_label'],e['creator_label'],e['date_label'],e['medium_label'],e['dimensions_label'],e['participation'],Jsonb(proof),'Exact permanent-collection native object identity'if e['artwork_id']else'Exact source exhibition object; main-catalogue match unresolved'))
                    evidence=dict(kind='museum_public_list',note=e['basis'],url=ev['source_url'],retrievedAt=rc['retrieved_at'])
                    detail=dict(id=e['id'],artworkId=e['artwork_id'],localArtworkId=oid,title=e['title_label'],creator=e['creator_label'],date=e['date_label'],medium=e['medium_label'],catalogueNumber=None,participation=e['participation'],participationEvidence=evidence,sourcePage=None,sourceURL=rc['url'],provider=sourcekey,sourceCaption=e['source']['title'],imageCredit=e['creator_label']+'; Museum of Russian Impressionism',imageLicense='No reuse licence stated',imageSource=im['receipt']['url'],image=im['path'],imageWidth=im['width'],imageHeight=im['height']);details.append(detail)
                    obj=detail|dict(id=oid,artists=[],dimensions=e['dimensions_label'],attribution=e['creator_label'],sourceArtworkID=e['native'],hasSourceExhibitionHistory=True,identityBasis=e['basis'],localStudy=False,imageEvidence=proof)
                    db.execute('INSERT INTO exhibition_objects(id,provider,source_object_id,artwork_id,batch_id,detail) VALUES(%s,%s,%s,%s,%s,%s)',(oid,sourcekey,e['native'],e['artwork_id'],OP,Jsonb(obj)))
                if es:
                    research=dict(overview='Selected artworks documented in the museum’s public exhibition list. The complete exhibition checklist has not been established.',excerpt='',excerptSource=ev['source_url'],concepts=[],conceptBasis='No inferred thematic classifications',publicListComplete=False,publicListTotal=len(es),scope='Published object-page links only; borrowed objects do not imply museum ownership.',presenter='Museum of Russian Impressionism',reviewedAt=c.now())
                    detail=dict(expandedStudy=True,entryCount=len(es),linkedArtworkCount=sum(bool(e['artwork_id'])for e in es),localArtworkCount=len(es),illustratedArtworkCount=len(es),previewWorks=details[:6],research=research)
                    db.execute('INSERT INTO exhibition_research(exhibition_id,batch_id,detail,summary,concepts,featured,entry_count,illustrated_count) VALUES(%s,%s,%s,%s,%s,false,%s,%s)',(ev['id'],OP,Jsonb(detail),Jsonb(detail),[],len(es),len(es)))
                    for e,d in zip(es,details):
                        sid=uid('object-source/'+ev['key']+'/object/'+e['native']);appearance=dict(id=e['id'],exhibitionId=ev['id'],title=ev['title'],startDate=ev['start_date'],endDate=ev['end_date'],dates=ev['date_display'],startYear=ev['start_year'],format='physical',venues=[dict(name=ev['venue'],start_date=ev['start_date'],end_date=ev['end_date'])],participation=e['participation'],evidence=d['participationEvidence'])
                        db.execute('INSERT INTO exhibition_object_entries(id,exhibition_id,object_id,source_record_id,participation,detail,appearance) VALUES(%s,%s,%s,%s,%s,%s,%s)',(e['id'],ev['id'],d['localArtworkId'],sid,e['participation'],Jsonb(d),Jsonb(appearance)))
                for a in [a for a in p['participants']if a['event_id']==ev['id']]:
                    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(a['id'],ev['id'],source_id,a['artist_id'],a['name'],Jsonb(base|dict(native_object=a['source_native']))))
                    if es:db.execute('INSERT INTO exhibition_research_people(exhibition_id,person_id,artist_id) VALUES(%s,%s,%s)',(ev['id'],a['artist_id'],a['artist_id']))
            db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,%s,2016,2027,'partial',%s)",(uid('coverage'),MID,sourcekey,NEW+'/exhibitions',Jsonb(base|dict(counts=p['counts'],coverage=p['coverage']))))
        assert db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(OP,)).fetchone()['n']==50
    save('events-delivered.json',dict(at=c.now(),counts=p['counts'],before=before,plan_sha256=pin,new_exhibition_images=71,reused_collection_images=3));print('Committed museum exhibitions',p['counts'],flush=True)

def projection_creators():
    # The existing UI labels attribution as object classification. A creator
    # label must stay in creator/artists, not be rendered as a classification.
    from psycopg.types.json import Jsonb
    p=load('event-plan.json.gz');aps={a['native']:a for a in all_artists()}
    with c.connect()as db:
        rows=serial(db.execute('SELECT * FROM exhibition_objects WHERE batch_id=%s ORDER BY id',(OP,)).fetchall());assert len(rows)==74
        slugs={a['id']:a['slug']for a in db.execute('SELECT id::text,slug FROM artists WHERE id=ANY(%s::uuid[])',([a['id']for a in aps.values()],)).fetchall()}
    changes=[]
    for r in rows:
        e=next(e for e in p['entries']if e['native']==r['source_object_id']);d=r['detail'];assert d['attribution']==e['creator_label']and d['artists']==[]
        after=dict(d);after['attribution']=None;url=e['source']['creator_url'];person=aps.get(url.rsplit('/',1)[1])if url else None
        if person:after['artists']=[dict(id=person['id'],artist_id=person['id'],artist_slug=slugs[person['id']],name=e['creator_label'],role='primary',sourceURL=url)]
        changes.append(dict(id=r['id'],before=d,after=after))
    plan=dict(at=c.now(),changes=changes,reason='Correct existing UI classification field and expose exact museum-native creator links. Main artwork data unchanged.')
    save('object-creators-plan.json.gz',plan);c.save(BACKUP/'object-creators-preimage.json.gz',plan)
    with c.connect(write=True)as db:
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        actual=serial(db.execute('SELECT id,detail FROM exhibition_objects WHERE batch_id=%s ORDER BY id FOR UPDATE',(OP,)).fetchall());assert {r['id']:r['detail']for r in actual}=={r['id']:r['before']for r in changes}
        with db.pipeline():
            for r in changes:db.execute('UPDATE exhibition_objects SET detail=%s WHERE id=%s',(Jsonb(r['after']),r['id']))
    save('object-creators-delivered.json',dict(at=c.now(),object_records=len(changes),objects_with_exact_artist_links=sum(bool(r['after']['artists'])for r in changes)));print('Object creator projection corrected',sum(bool(r['after']['artists'])for r in changes),'artist-linked objects',flush=True)

def verify_delivery():
    p=load('collection-plan.json.gz');ep=load('event-plan.json.gz');repo=load('collection-repository-verification.json')
    assert len(repo['works'])==68 and repo['museum']['work_count']==68
    assert {r['id']for r in repo['works']}=={r['artwork_id']for r in p['rows']}
    with c.connect()as db:
        works={r['id']:r for r in serial(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([r['artwork_id']for r in p['rows']],)).fetchall())}
        for r in p['rows']:
            w=works[r['artwork_id']];assert w['current_institution_id']==MID
            if r['action']=='create':
                assert w['status']=='review' and not w['published_at'] and w['primary_media_id']==r['image']['media_id']
                assert w['creation_year_start']==r['year_start']and w['creation_year_end']==r['year_end']
            else:
                before=p['before'][r['artwork_id']]
                assert all(w[k]==v for k,v in before.items()if k not in ['current_institution_id','revision','updated_at','updated_by'])
            im=r['image'];proof=load('uploads/'+r['native']+'.json');assert proof['public_bytes_verified']and proof['sha256']==im['sha256']
        media=serial(db.execute('SELECT * FROM media_assets WHERE id=ANY(%s::uuid[])',([r['image']['media_id']for r in p['rows']],)).fetchall());assert len(media)==68 and all(m['rights_status']=='unknown'and m['byte_size']<=100000 for m in media)
        events=serial(db.execute('SELECT * FROM exhibitions WHERE import_batch=%s',(OP,)).fetchall());assert len(events)==50
        for e in events:
            expected=next(x for x in ep['events']if x['id']==e['id'])
            for key in ['title','start_date','end_date','start_year','end_year','date_precision','event_state']:assert e[key]==expected[key],(key,e,expected)
        counts=db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated FROM exhibitions WHERE status<>'archived'").fetchone()
        assert db.execute('SELECT count(*) n FROM exhibition_objects WHERE batch_id=%s',(OP,)).fetchone()['n']==74
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1'
    def get(path,params=None):
        response=requests.get(api+path,params=params,timeout=(15,60));response.raise_for_status();return response.json()
    def event_check(e):
        d=get('/exhibitions/'+e['id']);expected=[x for x in ep['entries']if x['event_id']==e['id']]
        assert d['title']==e['title']and d['state']==e['event_state']and d['entryCount']==len(expected)
        assert d['startYear']==e['start_year']and d['endYear']==e['end_year']and d['startDate']==e['start_date']and d['endDate']==e['end_date']
        assert len(d['venues'])==1 and d['venues'][0]['name']==e['venue']
        items=[];after=''
        while True:
            page=get('/exhibitions/'+e['id']+'/entries',dict(limit=5,after=after));assert page['total']==len(expected);items+=page['items']
            if not page['hasMore']:break
            after=page['nextCursor']
        assert {x['id']for x in items}=={x['id']for x in expected}
        for x in items:
            want=next(y for y in expected if y['id']==x['id']);im=load('exhibition-images/'+want['native']+'.json')
            assert x['artworkId']==want['artwork_id']and x['image']==im['path']and x['localArtworkId']==uid('exhibition-object/'+want['native'])
            assert x['participation']=='exhibited'
        return dict(id=e['id'],state=d['state'],entries=len(items),illustrated=len(items),dates_checked=True,paging_checked=True,venue_checked=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:checks=list(pool.map(event_check,ep['events']))
    def object_check(e):
        oid=uid('exhibition-object/'+e['native']);d=get('/exhibitions/artworks/'+oid);appear=get('/exhibitions/artworks/'+oid+'/exhibitions',dict(limit=100));im=load('exhibition-images/'+e['native']+'.json')
        assert d['sourceArtworkID']==e['native']and d['image']==im['path']and d['appearanceCount']==1
        assert appear['total']==1 and appear['items'][0]['exhibitionId']==e['event_id']
        assert load('exhibition-uploads/'+e['native']+'.json')['public_bytes_verified']
        return dict(id=oid,native=e['native'],detail_checked=True,reverse_link_checked=True,image=im['path'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:objects=list(pool.map(object_check,ep['entries']))
    listing=get('/exhibitions',dict(source='museum-of-russian-impressionism',limit=100));assert listing['total']==50 and listing['heldTotal']==48 and {e['id']for e in listing['items']}=={e['id']for e in ep['events']}
    venues=get('/exhibitions',dict(institution=MID,limit=100));assert venues['total']==46 # Four correctly retained offsite hosts.
    for n in ['14','71','224']:
        r=next(x for x in p['rows']if x['native']==n);page=get('/exhibitions',dict(artwork=r['artwork_id'],limit=100));assert any(x['id']==next(e['event_id']for e in ep['entries']if e['native']==n)for x in page['items'])
    result=dict(at=c.now(),collection=p['counts'],exhibitions=ep['counts'],events=checks,objects=objects,all_images_public_sha256_verified=139,new_exhibition_images=71,production_exhibition_totals=counts,museum_repository_checks='Read-only production repository calls verified museum counts, all 68 details, all three gallery pages, images, artist links, and date-exception objects.',http_checks='All 50 exhibition details, 74 entries, 74 documentary artwork details, reverse histories, source list, museum venue filter and three canonical artwork filters verified. Museum HTTP routes require a member session; browser runtime unavailable. Global timeline cutoff remains separate.',real_local_database_writes=False)
    save('delivery-verification.json',result);print('Verified',result['collection'],result['exhibitions'],'production exhibitions',counts,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
