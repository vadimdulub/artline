#!/usr/bin/env python3
"""Bounded regional WikiArt research; catalogue inspection is read-only."""
import argparse
import concurrent.futures
import hashlib
import html
import io
import json
import re
import threading
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import psycopg
from psycopg.rows import dict_row
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/africa-asia-cyprus-20261005'
OLD = ROOT / 'docs/research/wikiart-artist-coverage-20260920'
NATIONS = {
    'South African': ('ZA', 'South Africa', 'southern-africa'),
    'Egyptian': ('EG', 'Egypt', 'northern-africa'),
    'Ethiopian': ('ET', 'Ethiopia', 'eastern-africa'),
    'Moroccan': ('MA', 'Morocco', 'northern-africa'),
    'Nigerian': ('NG', 'Nigeria', 'western-africa'),
    'Sudanese': ('SD', 'Sudan', 'northern-africa'),
    'Chinese': ('CN', 'China', 'eastern-asia'),
    'Indian': ('IN', 'India', 'southern-asia'),
    'Indonesian': ('ID', 'Indonesia', 'south-eastern-asia'),
    'Iranian': ('IR', 'Iran', 'southern-asia'),
    'Iraqi': ('IQ', 'Iraq', 'western-asia'),
    'Lebanese': ('LB', 'Lebanon', 'western-asia'),
    'Syrian': ('SY', 'Syria', 'western-asia'),
    'Turkish': ('TR', 'Türkiye', 'western-asia'),
    'Filipino': ('PH', 'Philippines', 'south-eastern-asia'),
    'South Korean': ('KR', 'South Korea', 'eastern-asia'),
    'Vietnamese': ('VN', 'Vietnam', 'south-eastern-asia'),
    'Bangladeshi': ('BD', 'Bangladesh', 'southern-asia'),
    'Bangladeshi, Pakistani': ('BD', 'Bangladesh', 'southern-asia'),
    'Cypriot': ('CY', 'Cyprus', 'western-asia'),
}
SLUGS = '''mahmoud-saiid gebre-kristos-desta chaibia-talal olowe-of-ise
twins-seven-seven ibrahim-salahi george-pemba gerard-sekoto gregoire-boonzaier
irma-stern maggie-laubser pieter-wenning walter-battiss christo-coetzee
bada-shanren chang-dai-chien chen-hongshou fu-baoshi guan-zilan lin-fengmian
qi-baishi sanyu shen-zhou xu-beihong zao-wou-ki
abanindranath-tagore amrita-sher-gil m-f-husain nandalal-bose nasreen-mohamedi
raja-ravi-varma s-h-raza paritosh-sen
abdullah-suriosubroto basuki-abdullah raden-saleh
behjat-sadr hossein-behzad kamal-ol-molk manoucher-yektai reza-abbasi
rafa-nasiri paul-guiragossian louay-kayyali
botong-francisco vicente-manansala roberto-chabet
owon yoon-bok-shin park-seo-bo yun-hyong-keun ha-chong-hyun
bui-xuan-phai le-pho tran-van-can zainul-abedin sm-sultan
mihri-musfik huseyin-avni-lifij ibrahim-calli princess-fahrelnissa-zeid'''.split()
GATE = threading.Lock()
NEXT = 0.0


def now():
    return datetime.now(timezone.utc).isoformat()


def norm(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', html.unescape(str(value or '')).casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', value))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, indent=2, default=str).encode()
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Evidence already exists: ' + str(path))
    else:
        path.write_bytes(data)


def date(value):
    value = str(value or '')
    m = re.fullmatch(r'(c\.)?\s*(\d{1,4})\s*(BCE|BC|AD|CE)?(?:\s*[-–]\s*(c\.)?\s*(\d{1,4})\s*(BCE|BC|AD|CE)?)?', value, re.I)
    if not m:
        return None
    first, last = int(m[2]), int(m[5] or m[2])
    start = -first if (m[3] or m[6] or 'AD').upper() in ('BC', 'BCE') else first
    end = -last if (m[6] or m[3] or 'AD').upper() in ('BC', 'BCE') else last
    if not first or not last or start > end:
        return None
    circa = bool(m[1] or m[4])
    return dict(creation_year_start=start, creation_year_end=end, date_display=value,
                date_precision=('circa_range' if circa else 'range') if m[5] else ('circa' if circa else 'exact'))


def fetch(url, method='GET'):
    """Capture public metadata only, at <=1 request/second, without gate bypass."""
    global NEXT
    key = hashlib.sha256((url if method == 'GET' else method + ' ' + url).encode()).hexdigest()
    body, receipt = RUN / 'captures' / (key + '.body'), RUN / 'captures' / (key + '.json')
    if receipt.exists():
        r = json.loads(receipt.read_text())
        raw = body.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == r['sha256']
        return raw, r
    with GATE:
        slot = max(time.monotonic(), NEXT)
        NEXT = slot + 1.05
    time.sleep(max(0, slot-time.monotonic()))
    response = requests.request(method, url, timeout=(15, 40), headers={'User-Agent': 'Artline/1.0 (selected regional art research)'})
    response.raise_for_status()
    assert len(response.content) <= 5_000_000
    raw = response.content
    r = dict(url=url, method=method, final_url=response.url, retrieved_at=now(), sha256=hashlib.sha256(raw).hexdigest(),
             bytes=len(raw), content_type=response.headers.get('Content-Type'))
    save(body, raw)
    save(receipt, r)
    return raw, r


def profile(slug):
    path = RUN / 'profiles' / (slug + '.json')
    if path.exists():
        return json.loads(path.read_text())
    raw, receipt = fetch('https://www.wikiart.org/en/' + slug)
    soup = BeautifulSoup(raw, 'html.parser')
    featured = []
    for tag in soup.select('[ng-init]'):
        init = tag['ng-init']
        if not re.search(r"['\"]masonryId['\"]\s*:\s*['\"]famous-works['\"]", init):
            continue
        m = re.search(r"['\"]customSource['\"]\s*:\s*", init)
        if m:
            featured = json.JSONDecoder().raw_decode(init[m.end():])[0].get('_v', [])
    old_path = OLD / 'profiles' / (slug+'.json')
    old = json.loads(old_path.read_text()) if old_path.exists() else {}
    def field(prop):
        tag = soup.select_one('[itemprop="'+prop+'"]')
        return tag.get_text(' ', strip=True) if tag else None
    result = dict(slug=slug, name=soup.select_one('h1').get_text(' ', strip=True),
                  nationalities=[x.get_text(' ', strip=True) for x in soup.select('[itemprop="nationality"]')],
                  birth=field('birthDate'), death=field('deathDate'), receipt=receipt,
                  previous_directory=old.get('source'), featured=featured,
                  source_url=receipt['final_url'])
    save(path, result)
    print('Profile', slug, len(featured), flush=True)
    return result


def profiles():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(profile, SLUGS))


def readonly():
    return psycopg.connect('postgres://localhost/artline', row_factory=dict_row,
                           options='-c default_transaction_read_only=on -c statement_timeout=120000')


def select():
    out = RUN / 'selection.json'
    if out.exists():
        raise ValueError('Selection already pinned')
    selected, artists, holds, existing = [], [], [], []
    with readonly() as db:
        for slug in SLUGS:
            p = json.loads((RUN / 'profiles' / (slug+'.json')).read_text())
            names = list({norm(p['name']), norm((p.get('previous_directory') or {}).get('name')), norm(slug.replace('-', ' '))}-{''})
            matches = db.execute("""SELECT DISTINCT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status FROM artists a
              LEFT JOIN artist_aliases al ON al.artist_id=a.id
              LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikiart-artist'
              WHERE a.normalized_name=ANY(%s) OR al.normalized_alias=ANY(%s) OR e.external_id=%s OR e.canonical_url=%s""",
              (names, names, slug, p['source_url'])).fetchall()
            if len(matches)>1:
                holds.append(dict(artist=slug,reason='ambiguous_artist',matches=matches)); continue
            countries = sorted({NATIONS[n] for n in p['nationalities'] if n in NATIONS})
            a = dict(profile=p, existing=matches[0] if matches else None, countries=countries)
            if not countries:
                holds.append(dict(artist=slug,reason='country_needs_review',nationalities=p['nationalities'])); continue
            rows = db.execute("""SELECT a.id::text,a.title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,
                   a.primary_media_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s""",
                   (matches[0]['id'],)).fetchall() if matches else []
            a['existing_works']=rows
            artists.append(a)
            added=0
            for item in p['featured']:
                url=urljoin('https://www.wikiart.org',item['paintingUrl'])
                d=date(item.get('year'))
                w=dict(artist_slug=slug,artist_name=p['name'],source_id=item['_id'],title=html.unescape(item['title']),
                       source_url=url,source_image_url=item.get('image'),source_date=item.get('year'),date=d,
                       countries=countries,profile_receipt=p['receipt'],source_metadata=item,
                       selection_basis='Selected regional highlight from WikiArt famous-works; owner research selection, not museum designation.')
                if not d or d['creation_year_end']>1970:
                    holds.append(dict(**w,reason='unknown_date' if not d else 'after_cutoff'));continue
                identities=db.execute("""SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork'
                    AND ((scheme='wikiart-artwork' AND external_id=%s) OR canonical_url=%s)
                    UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s""",
                    (item['_id'],url,url)).fetchall()
                title_matches=[x for x in rows if norm(w['title']) in {norm(x['title']),norm(x['alternate_title'])}]
                if identities or title_matches:
                    existing.append(dict(**w,identities=identities,title_matches=title_matches));continue
                if added>=5:
                    continue
                selected.append(w);added+=1
    result=dict(at=now(),artists=artists,works=selected,existing=existing,holds=holds,
                scope='At most five new, explicitly dated pre-1971 WikiArt highlights per selected regional artist. No catalogue writes or image downloads in research phases.')
    save(out,result)
    print(json.dumps(dict(artists=len(artists),new_artist_candidates=sum(not a['existing'] for a in artists),
                         works=len(selected),existing=len(existing),holds=dict(Counter(x['reason'] for x in holds)),
                         countries=dict(Counter(c[1] for w in selected for c in w['countries'])))),flush=True)


def artwork(w):
    path=RUN/'objects'/(w['source_id']+'.json')
    if path.exists():return json.loads(path.read_text())
    result=dict(**w,rights_status='unknown',download_allowed=False)
    try:
        raw,receipt=fetch(w['source_url'])
        soup=BeautifulSoup(raw,'html.parser')
        tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
        if not tag:
            result.update(page_outcome='metadata_unavailable',page_receipt=receipt)
        else:
            record=json.loads(tag['ng-init'].split('=',1)[1].strip())
            assert record['_id']==w['source_id'] and norm(record['title'])==norm(w['title'])
            assert record['artistUrl']=='/en/'+w['artist_slug']
            assert date(record.get('year'))==w['date']
            label=soup.select_one('.copyright-wrapper .copyright')
            pd=bool(label and label.select_one('.copyright-icon-public-domain'))
            image=soup.select_one('img[itemprop="image"]')
            article=soup.select_one('.wiki-layout-artwork-info article')
            result.update(page_outcome='verified',page_receipt=receipt,object_metadata=record,
                          rights_status='public_domain' if pd else ('restricted' if label else 'unknown'),
                          rights_label=label.get_text(' ',strip=True) if label else None,
                          download_allowed=pd,source_image_url=image['src'] if image else w['source_image_url'],
                          object_text=article.get_text(' ',strip=True) if article else None)
    except requests.HTTPError as e:
        result.update(page_outcome='http_error',http_status=e.response.status_code,error=str(e))
    except (AssertionError,ValueError) as e:
        result.update(page_outcome='identity_or_date_conflict',error=str(e))
    save(path,result)
    print('Object',w['artist_slug'],w['title'],result['page_outcome'],result['rights_status'],flush=True)
    return result


def objects():
    works=json.loads((RUN/'selection.json').read_text())['works']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(artwork,works))
    save(RUN/'objects-summary.json',dict(at=now(),count=len(results),outcomes=dict(Counter(x['page_outcome'] for x in results)),
                                      rights=dict(Counter(x['rights_status'] for x in results))))


def cyprus():
    """Read the public gallery API used by its website, with no credentials."""
    if (RUN/'cyprus-selection.json').exists():
        raise ValueError('Cyprus selection already pinned')
    api='https://cypriotartists.leventisgallery.org/api/en/'
    raw,index_receipt=fetch(api+'fetch-artists', 'POST')
    index=json.loads(raw)
    save(RUN/'cyprus-artists-index.json',dict(data=index,receipt=index_receipt))
    results,held,existing,artists=[],[],[],[]
    with readonly() as db:
        for artist in index['artists'][:6]:
            slug=artist['slug']
            raw,receipt=fetch(api+'fetch-artist/'+slug, 'POST')
            p=json.loads(raw)
            names=list({norm(p['title']),norm(slug.replace('-',' '))})
            matches=db.execute("""SELECT DISTINCT a.id::text,a.display_name,a.slug FROM artists a LEFT JOIN artist_aliases al ON al.artist_id=a.id
               WHERE a.normalized_name=ANY(%s) OR al.normalized_alias=ANY(%s)""",(names,names)).fetchall()
            # An official biography page is evidence for identity, not an invented biography.
            info=dict(source_slug=slug,name=p['title'],birth=p.get('birthYear'),death=p.get('deathYear'),
                      profile_url='https://cypriotartists.leventisgallery.org/en/'+slug,receipt=receipt,existing_matches=matches)
            artists.append(info)
            save(RUN/'cyprus-profiles'/(slug+'.json'),dict(profile=p,receipt=receipt,identity=info))
            ids=[x['id'] for x in matches]
            rows=db.execute("""SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end FROM artwork_artists aa
                  JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])""",(ids,)).fetchall() if ids else []
            added=0
            for w in p.get('artworks',{}).get('all',[]):
                label=html.unescape(w['date'] or '')
                canonical=label.replace('ca.','c.').replace('circa ','c.')
                exact_day=re.fullmatch(r'\d{1,2} [A-Za-z]+ (\d{4})',canonical)
                if exact_day:canonical=exact_day[1]
                d=date(canonical)
                if d:d['date_display']=label
                url='https://cypriotartists.leventisgallery.org/en/'+slug+'/works/'+w['slug']
                item=dict(artist_name=p['title'],artist_slug=slug,title=html.unescape(w['title']),date=d,source_date=label,
                          source_id='leventis-'+str(w['id']),source_url=url,source_image_url=w.get('image'),
                          page_receipt=receipt,source_metadata=w,rights_status='unknown',download_allowed=False,
                          source_collection_label=w.get('collection'),country_code='CY',geography_basis='Cypriot creator; official Leventis artist collection',
                          selection_basis='Museum-curated artist research; supplied collection credit retained without asserting current display.')
                matches_by_title=[x for x in rows if norm(item['title']) in {norm(x['title']),norm(x['alternate_title'])}]
                identities=db.execute("""SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s
                    UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s""",(url,url)).fetchall()
                if matches_by_title or identities:
                    existing.append(dict(**item,title_matches=matches_by_title,identities=identities));continue
                if not d or d['creation_year_end']>1970:
                    held.append(dict(**item,reason='unknown_date' if not d else 'after_cutoff'));continue
                if added>=8:continue
                results.append(item);added+=1
            print('Cyprus',p['title'],added,'selected',flush=True)
        # Bounded museum supplement: Cyprus subjects do not make foreign artists Cypriot.
        paths=['st-george-xorinos-famagusta/1841','from-the-top-of-a-mountain-agia-irini-bay-morphou/4356',
               'carob-stores-in-kyrenia-harbour/4357','mountain-village-cyprus/4360','from-pedoulas/4363',
               'olive-trees-2/4396','famagusta-harbour-2/12858','platres-2/9169','tremetousia/7944','rooftops-at-nicosia/12769']
        for path in paths:
            url='https://cvar.severis.org/en/collections/item/'+path+'/'
            raw,receipt=fetch(url)
            soup=BeautifulSoup(raw,'html.parser')
            fields={}
            for row in soup.select('.info-table-row'):
                ps=row.find_all('p',recursive=False)
                if len(ps)>=2:fields[ps[0].get_text(' ',strip=True).rstrip(':')]=ps[1].get_text(' ',strip=True)
            label=fields.get('Date','')
            d=date(re.sub(r'^(\d{4})--\d{2}--\d{2}$',r'\1',label.replace('ca.','c.')))
            if d:d['date_display']=label
            image=soup.select_one('img[alt*="PNT-"]')
            item=dict(title=soup.select_one('h1').get_text(' ',strip=True),artist_name=fields.get('Creator'),date=d,source_date=label,
                      source_id='cvar-'+path.rsplit('/',1)[-1],source_url=url,source_metadata=fields,page_receipt=receipt,
                      source_image_url=image['src'] if image else None,rights_status='restricted',download_allowed=False,
                      country_code='CY',geography_basis='Cyprus subject documented by CVAR; no creator nationality inferred',
                      selection_basis='Selected named-creator museum catalogue record; holding and display remain separate.')
            ids=db.execute("""SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s
                UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s""",(url,url)).fetchall()
            if ids:existing.append(dict(**item,identities=ids))
            elif not d or d['creation_year_end']>1970:held.append(dict(**item,reason='unknown_date' if not d else 'after_cutoff'))
            else:results.append(item)
    result=dict(at=now(),artists=artists,works=results,existing=existing,holds=held)
    save(RUN/'cyprus-selection.json',result)
    print('Cyprus complete',len(results),'candidates;',len(existing),'existing;',len(held),'date holds',flush=True)


def image_plan():
    chosen=[]
    counts=Counter()
    for w in json.loads((RUN/'selection.json').read_text())['works']:
        obj=json.loads((RUN/'objects'/(w['source_id']+'.json')).read_text())
        if obj['page_outcome']=='verified' and obj['download_allowed'] and '(detail)' not in obj['title'].casefold() and counts[w['artist_slug']]<3:
            chosen.append(obj);counts[w['artist_slug']]+=1
    save(RUN/'image-plan-reviewed.json',dict(at=now(),works=chosen,policy='Maximum three selected images per artist; detail views excluded; WikiArt per-object public-domain labels only. Preserve source claim; no clearance inferred from artwork age.'))
    print('Image selection',len(chosen),'images across',len(counts),'artists',flush=True)


def images():
    from PIL import Image, ImageOps
    originals=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
    targets=json.loads((RUN/'image-plan-reviewed.json').read_text())['works']
    results=[]
    for w in targets:
        receipt_path=RUN/'images'/(w['source_id']+'.json')
        if receipt_path.exists():
            results.append(json.loads(receipt_path.read_text()));continue
        assert w['download_allowed'] and w['rights_status']=='public_domain'
        url=w['source_image_url']
        assert urlparse(url).scheme=='https' and re.fullmatch(r'uploads\d*\.wikiart\.org',urlparse(url).hostname or '')
        response=requests.get(url,timeout=(15,45),headers={'User-Agent':'Artline/1.0 (selected public-domain-labelled images)'},stream=True)
        response.raise_for_status()
        assert urlparse(response.url).hostname==urlparse(url).hostname
        buf=bytearray()
        for chunk in response.iter_content(65536):
            buf.extend(chunk)
            if len(buf)>20_000_000:raise ValueError('Selected image exceeds byte budget')
        raw=bytes(buf)
        with Image.open(io.BytesIO(raw)) as original:
            original.load()
            assert min(original.size)>80
            im=ImageOps.exif_transpose(original).convert('RGB')
            original_size=im.size
            im.thumbnail((1600,1600))
            while True:
                output=io.BytesIO();im.save(output,format='JPEG',quality=85,optimize=True)
                if len(output.getvalue())<=100000:break
                im.thumbnail((max(1,int(im.width*.9)),max(1,int(im.height*.9))))
        destination=RUN/'images'/(w['source_id']+'.jpg')
        original_path=originals/(w['source_id']+'.body')
        save(original_path,raw);save(destination,output.getvalue())
        result=dict(source_id=w['source_id'],artist=w['artist_name'],title=w['title'],source_url=w['source_url'],
                    source_image_url=url,rights_status='public_domain',rights_basis='WikiArt per-artwork public-domain label',
                    rights_label=w.get('rights_label'),page_receipt=w['page_receipt'],retrieved_at=now(),
                    original_path=str(original_path),original_sha256=hashlib.sha256(raw).hexdigest(),original_bytes=len(raw),
                    original_size=original_size,path=str(destination.relative_to(ROOT)),sha256=hashlib.sha256(output.getvalue()).hexdigest(),
                    bytes=len(output.getvalue()),width=im.width,height=im.height,visual_review='pending')
        save(receipt_path,result);results.append(result)
        print('Image',w['artist_name'],w['title'],len(output.getvalue()),flush=True)
        time.sleep(1.1)
    save(RUN/'images-summary.json',dict(at=now(),count=len(results),bytes=sum(x['bytes'] for x in results)))


def delivery():
    import importlib.util
    spec=importlib.util.spec_from_file_location('regional_delivery',ROOT/'ops/apply-africa-asia-cyprus-20261005.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(args.delivery_phase)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['profiles','select','objects','cyprus','image_plan','images','delivery'])
    parser.add_argument('delivery_phase',nargs='?',choices=['plan','backup','apply','verify','api_verify'])
    args=parser.parse_args()
    globals()[args.phase]()
