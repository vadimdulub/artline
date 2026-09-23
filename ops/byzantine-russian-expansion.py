#!/usr/bin/env python3
"""Bounded source research for the owner's Byzantine/Russian icon expansion.

Captures are provenance. Database audits are read-only; mutations are separate.
"""
import argparse
import concurrent.futures
import hashlib
import io
import json
import os
import re
import subprocess
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlencode
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/byzantine-russian-icons-frescoes-20260920'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/byzantine-russian-icons-frescoes-20260920'
DSN = 'postgres://localhost/artline'
AGENT = 'ArtlineIconResearch/1.0'
HOSTS = {'www.ebyzantinemuseum.gr', 'collectiononline.kreml.ru',
         'art.thewalters.org', 'openaccess-api.clevelandart.org',
         'collectionapi.metmuseum.org', 'rusmuseumvrm.ru', 'www.mbp.gr', 'www.dionisy.com',
         'kirmuseum.org', 'www.kirmuseum.org', 'novgorodmuseum.ru'}
HOSTS.update({'images.metmuseum.org','openaccess-cdn.clevelandart.org'})


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, default=str)
        f.write('\n')


class Capture:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': AGENT})
        self.robots = {}
        self.last = {}

    def get(self, url, robot=False):
        p = urlparse(url)
        assert p.scheme == 'https' and p.hostname in HOSTS and not p.username
        assert not (p.hostname == 'collectiononline.kreml.ru' and p.path.startswith('/api/'))
        key = sha(url.encode())
        body = RUN / 'captures' / (key + '.body')
        receipt_path = RUN / 'captures' / (key + '.json')
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            assert receipt['url'] == url
            raw = body.read_bytes()
            assert sha(raw) == receipt['sha256'] and len(raw) == receipt['bytes']
            if receipt['status'] != 200:
                raise ValueError('Recorded HTTP failure: ' + str(receipt['status']) + ' ' + url)
            return raw, receipt
        if not robot:
            if p.hostname not in self.robots:
                robots_url = 'https://' + p.hostname + '/robots.txt'
                try:
                    raw, _ = self.get(robots_url, robot=True)
                    policy = RobotFileParser()
                    policy.parse(raw.decode('utf-8', errors='replace').splitlines())
                    self.robots[p.hostname] = policy
                except ValueError as exc:
                    # An explicit 404 means the host supplies no robots policy;
                    # every other failed policy request leaves this host held.
                    if '404' not in str(exc):
                        raise
                    self.robots[p.hostname] = None
            policy = self.robots[p.hostname]
            if policy and not policy.can_fetch(AGENT, url):
                raise ValueError('Robots disallows ' + url)
        delay = 10.5 if p.hostname in {'www.ebyzantinemuseum.gr', 'collectiononline.kreml.ru'} else 1.1
        policy = self.robots.get(p.hostname)
        if policy:
            delay = max(delay, policy.crawl_delay(AGENT) or policy.crawl_delay('*') or 0)
        time.sleep(max(0, delay - (time.monotonic() - self.last.get(p.hostname, 0))))
        response = self.session.get(url, timeout=40, allow_redirects=False)
        self.last[p.hostname] = time.monotonic()
        raw = response.content
        assert len(raw) <= 12 * 1024 * 1024
        body.parent.mkdir(parents=True, exist_ok=True)
        body.write_bytes(raw)
        receipt = {'url': url, 'status': response.status_code, 'retrieved_at': now(),
                   'sha256': sha(raw), 'bytes': len(raw), 'path': str(body.relative_to(ROOT)),
                   'content_type': response.headers.get('content-type'),
                   'redirect_location': response.headers.get('location')}
        save(receipt_path, receipt)
        if response.status_code != 200:
            raise ValueError('HTTP ' + str(response.status_code) + ' ' + url)
        return raw, receipt


def probe():
    c = Capture()
    urls = [
        'https://www.ebyzantinemuseum.gr/?i=bxm.en.collections',
        'https://collectiononline.kreml.ru/entity/OBJECT',
        'https://art.thewalters.org/search/?q=icon',
        'https://openaccess-api.clevelandart.org/api/artworks/?q=icon&limit=100',
        'https://collectionapi.metmuseum.org/public/collection/v1/search?title=true&q=icon',
        'https://rusmuseumvrm.ru/collections/old_russian_painting/index.php',
    ]
    for url in urls:
        try:
            raw, receipt = c.get(url)
            soup = BeautifulSoup(raw, 'html.parser')
            links = [{'url': urljoin(url, a['href']), 'text': a.get_text(' ', strip=True)} for a in soup.select('a[href]')]
            for node in soup.select('script,style,nav,footer,header'):
                node.decompose()
            result = {'url': url, 'receipt': receipt, 'links': links, 'text': soup.get_text(' ', strip=True)}
            path = RUN / 'probe' / (urlparse(url).hostname + '.json')
            if not path.exists():
                save(path, result)
            print(url, receipt['status'], receipt['bytes'], 'links', len(links), flush=True)
        except Exception as exc:
            print(type(exc).__name__, str(exc), flush=True)


def audit():
    with psycopg.connect(DSN, options='-c default_transaction_read_only=on', row_factory=dict_row) as db:
        rows = db.execute("""SELECT to_jsonb(a) artwork,
          coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
          coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
          coalesce((SELECT jsonb_agg(jsonb_build_object('name',p.display_name,'artist_id',p.id,'role',aa.attribution_role)) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
          FROM artworks a WHERE object_form='icon' OR work_type='fresco' OR cultural_context ~* 'Byzant|Russian icon'
            OR a.id IN (SELECT aa.artwork_id FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE p.display_name ~* 'Rublev|Rublyov|Theophanes|Ushakov')
          ORDER BY a.id""").fetchall()
        totals = db.execute("SELECT count(*) artworks,count(*) FILTER (WHERE object_form='icon') icons,count(*) FILTER (WHERE work_type='fresco') frescoes FROM artworks").fetchone()
    path = RUN / 'baseline.json'
    if not path.exists():
        save(path, {'at': now(), 'totals': totals, 'records': rows})
    print(json.dumps({'totals': totals, 'audited_records': len(rows)}), flush=True)


def fetch_pages(urls):
    assert 0 < len(urls) <= 20
    c = Capture()
    for url in urls:
        try:
            raw, receipt = c.get(url)
            print(json.dumps(receipt), flush=True)
        except Exception as exc:
            print(type(exc).__name__, str(exc), flush=True)


def collect_russian():
    c = Capture()
    leads = {}
    for page in range(1, 9):
        url = 'https://rusmuseumvrm.ru/collections/iconography/index.php?' + urlencode(
            {'lang': 'ru', 'show': 'asc', 'p': 0, 't': 0, 'page': page, 'ps': 100})
        raw, receipt = c.get(url)
        soup = BeautifulSoup(raw, 'html.parser')
        for node in soup.select('.item__inner'):
            link = node.select_one('a[href^="/data/collections/ikonopis/"]')
            if not link:
                continue
            detail = urljoin(url, link['href'])
            title = node.select_one('.item__title')
            date = node.select_one('.item__desc')
            leads.setdefault(detail, {'url': detail, 'title': title.get_text(' ', strip=True) if title else '',
                                     'index_date': date.get_text(' ', strip=True) if date else '',
                                     'index_capture': receipt})
        print('Russian Museum index', page, 'unique leads', len(leads), flush=True)
    path = RUN / 'russian-index.json'
    if not path.exists():
        save(path, list(leads.values()))
    assert len(leads) <= 800
    for i, lead in enumerate(leads.values(), 1):
        path = RUN / 'russian-objects' / (sha(lead['url'].encode()) + '.json')
        if path.exists():
            continue
        try:
            raw, receipt = c.get(lead['url'])
            soup = BeautifulSoup(raw, 'html.parser')
            for n in soup.select('script,style,nav,header,footer'):
                n.decompose()
            save(path, {**lead, 'capture': receipt, 'text': soup.get_text(' ', strip=True)})
        except Exception as exc:
            save(path, {**lead, 'error': type(exc).__name__ + ': ' + str(exc)})
        if i % 25 == 0:
            print('Russian Museum objects', i, '/', len(leads), flush=True)


def collect_athens():
    c = Capture()
    leads = {}
    indices = ['https://www.ebyzantinemuseum.gr/?i=bxm.en.collections&c=' + str(cat) for cat in (9, 11, 7)]
    for url in indices:
        raw, _ = c.get(url)
        soup = BeautifulSoup(raw, 'html.parser')
        for a in soup.select('a[href]'):
            dest = urljoin(url, a['href'])
            if 'bxm.en.collections' in dest and 'page=' in dest and dest not in indices:
                indices.append(dest)
            if 'bxm.en.exhibit' in dest:
                leads.setdefault(dest, {'url': dest, 'title': a.get_text(' ', strip=True), 'index_url': url})
        assert len(indices) <= 12
    path = RUN / 'athens-index.json'
    if not path.exists():
        save(path, list(leads.values()))
    print('Athens selected catalogue leads', len(leads), flush=True)
    assert len(leads) <= 150
    for i, lead in enumerate(leads.values(), 1):
        path = RUN / 'athens-objects' / (sha(lead['url'].encode()) + '.json')
        if path.exists():
            continue
        try:
            raw, receipt = c.get(lead['url'])
            soup = BeautifulSoup(raw, 'html.parser')
            descriptions = [n.get_text(' ', strip=True) for n in soup.select('.description')]
            facts = [n.get_text(' ', strip=True) for n in soup.select('li,p') if not n.select('li,p,ul,ol')]
            save(path, {**lead, 'capture': receipt, 'headings': [n.get_text(' ', strip=True) for n in soup.select('h1,h2')],
                        'description': descriptions, 'facts': facts})
        except Exception as exc:
            save(path, {**lead, 'error': type(exc).__name__ + ': ' + str(exc)})
        if i % 10 == 0:
            print('Athens objects', i, '/', len(leads), flush=True)


def collect_met():
    c = Capture()
    ids = set()
    for query in ('icon', 'fresco'):
        params = {'title': 'true', 'q': query}
        if query == 'fresco':
            params['departmentId'] = 17
        url = 'https://collectionapi.metmuseum.org/public/collection/v1/search?' + urlencode(params)
        raw, _ = c.get(url)
        ids.update(json.loads(raw).get('objectIDs') or [])
    assert len(ids) <= 200
    for i, oid in enumerate(sorted(ids), 1):
        path = RUN / 'met-objects' / (str(oid) + '.json')
        if path.exists():
            continue
        try:
            raw, receipt = c.get('https://collectionapi.metmuseum.org/public/collection/v1/objects/' + str(oid))
            save(path, {'object': json.loads(raw), 'capture': receipt})
        except Exception as exc:
            save(path, {'object_id': oid, 'error': type(exc).__name__ + ': ' + str(exc)})
        if i % 20 == 0:
            print('Met objects', i, '/', len(ids), flush=True)


def collect():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        jobs = {executor.submit(fn): fn.__name__ for fn in (collect_russian, collect_athens, collect_met)}
        for future in concurrent.futures.as_completed(jobs):
            try:
                future.result()
                print(jobs[future], 'complete', flush=True)
            except Exception as exc:
                print(jobs[future], 'stopped', repr(exc), flush=True)


def collect_thessaloniki():
    c = Capture()
    leads = {}
    for category in ('wall-paintings', 'wooden-icons'):
        url = 'https://www.mbp.gr/en/collections/' + category + '/'
        raw, _ = c.get(url)
        soup = BeautifulSoup(raw, 'html.parser')
        for a in soup.select('a[href]'):
            if a['href'].startswith('https://www.mbp.gr/en/exhibit/'):
                leads[a['href']] = {'title':a.get_text(' ',strip=True),'category':category}
    assert len(leads) <= 50
    for url, lead in leads.items():
        raw, receipt = c.get(url)
        soup = BeautifulSoup(raw, 'html.parser')
        for n in soup.select('script,style,header,footer,nav'):
            n.decompose()
        path = RUN/'thessaloniki-objects'/(sha(url.encode())+'.json')
        if not path.exists():
            save(path, {**lead,'url':url,'capture':receipt,'text':soup.get_text(' ',strip=True)})
    print('Thessaloniki selected objects',len(leads),flush=True)


def norm(value):
    return ' '.join(re.findall(r'[^\W_]+', unicodedata.normalize('NFKC', value or '').casefold().replace('ё', 'е')))


def russian_date(literal):
    """Only the museum's creation-date field, never essays or artist lifespans."""
    text = literal.replace('Х', 'X').replace('І', 'I').replace('–', '-').replace('—', '-')
    unknown = (None, None, 'unknown')
    if re.search(r'копи|понов|реставр|допис|передел|запис|сло[йя]|оборот|лицев|оклад\s*:|\?', text, re.I):
        # A question mark about location before the date does not alter dating.
        text = re.sub(r'^[^\dIVX]*\(\?\)\.\s*', '', text)
        if re.search(r'копи|понов|реставр|допис|передел|запис|сло[йя]|оборот|лицев|оклад\s*:|\?', text, re.I):
            return unknown
    romans = re.findall(r'(?<!\w)([IVX]{1,6})(?!\w)', text)
    roman_values = {'I': 1, 'V': 5, 'X': 10}
    def roman(s):
        return sum(-roman_values[c] if i+1 < len(s) and roman_values[c] < roman_values[s[i+1]] else roman_values[c] for i,c in enumerate(s))
    centuries = [roman(s) for s in romans]
    years = [int(s) for s in re.findall(r'(?<!\d)(\d{3,4})(?!\d)', text)]
    if centuries and years:
        return unknown
    if centuries:
        if not all(1 <= c <= 20 for c in centuries) or centuries != sorted(centuries):
            return unknown
        lo, hi = (centuries[0]-1)*100+1, centuries[-1]*100
        if len(centuries) == 1:
            base = lo-1
            # Multiple qualifiers are retained with a conservative whole century.
            if not re.search(r'середин|начал|конец|конца', text, re.I):
                for phrase, start, end in [('первая половина',1,50),('вторая половина',51,100),
                        ('первая треть',1,33),('вторая треть',34,66),('последняя треть',67,100),('третья треть',67,100),
                        ('первая четверть',1,25),('вторая четверть',26,50),('третья четверть',51,75),('четвертая четверть',76,100),('последняя четверть',76,100)]:
                    if phrase in text.casefold().replace('ё','е'):
                        return base+start, base+end, 'range'
        return lo, hi, 'century' if len(centuries) == 1 else 'range'
    if not years or len(years) > 2 or years != sorted(years):
        return unknown
    if re.search(r'после|не ранее', text, re.I):
        return years[0], None, 'after'
    if re.search(r'до\s+\d|ранее\s+\d', text, re.I):
        return None, years[-1], 'before'
    if len(years) == 1 and re.search(r'\d{3,4}\s*-?\s*[еы]([\s.]|$)|\d{3,4}-х', text):
        return years[0], years[0]+9, 'decade'
    approximate = bool(re.search(r'около|ок\.|начал|конец|середин', text, re.I))
    return years[0], years[-1], ('circa' if len(years)==1 else 'circa_range') if approximate else ('exact' if len(years)==1 else 'range')


def english_date(literal):
    text = literal.replace('–','-').replace('—','-')
    if re.search(r'\?|\band\b|\brepaint|\bcopy|\brestor', text, re.I):
        return None, None, 'unknown'
    centuries = [int(s) for s in re.findall(r'(\d{1,2})(?:st|nd|rd|th)(?!\s+(?:half|quarter|third))',text,re.I)]
    if centuries and re.search(r'centur|\bc\.',text,re.I):
        if not all(1<=n<=20 for n in centuries) or centuries!=sorted(centuries):
            return None,None,'unknown'
        lo,hi=(centuries[0]-1)*100+1,centuries[-1]*100
        if len(centuries)==1:
            if re.search(r'1st half|first half',text,re.I):
                hi=lo+49
            elif re.search(r'2nd half|second half',text,re.I):
                lo+=50
        return lo,hi,'century' if hi-lo==99 else 'range'
    matches = re.findall(r'(?<!\d)(\d{3,4})(?!\d)',text)
    if not matches or len(matches)>2:
        return None,None,'unknown'
    years=[int(y) for y in matches]
    short=re.search(r'(?<!\d)(\d{3,4})\s*-\s*(\d{2})(?!\d)',text)
    if short:
        years=[int(short[1]),(int(short[1])//100)*100+int(short[2])]
    if years!=sorted(years):
        return None,None,'unknown'
    approx=bool(re.search(r'\bc\.|\bca\.|circa|about',text,re.I))
    return years[0],years[-1],('circa' if len(years)==1 else 'circa_range') if approx else ('exact' if len(years)==1 else 'range')


def base_work(provider, source_id, url, title, accession, institution, capture):
    return {'provider': provider, 'source_object_id': str(source_id), 'source_url': url,
            'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/icons-frescoes-20260920/' + provider + '/' + str(source_id))),
            'slug': 'icons-frescoes-' + provider + '-' + sha(str(source_id).encode())[:14],
            'title': title, 'accession_number': accession or None, 'institution_slug': institution,
            'date_display': 'Date not stated', 'creation_year_start': None, 'creation_year_end': None,
            'date_precision': 'unknown', 'work_type': 'painting', 'object_form': 'icon',
            'creator_label': 'Unidentified artist (not named in the source catalogue)',
            'artist_qid': None, 'attribution_role': None, 'medium_text': None, 'dimensions_text': None,
            'cultural_context': None, 'source_capture': capture, 'source_fields': {},
            'image_candidate': None, 'notes': []}


def russian_candidates():
    selected, held = [], []
    for path in sorted((RUN / 'russian-objects').glob('*.json')):
        record = json.loads(path.read_text())
        if 'error' in record:
            held.append({'url': record['url'], 'reason': record['error']}); continue
        raw = (ROOT / record['capture']['path']).read_bytes()
        assert sha(raw) == record['capture']['sha256']
        soup = BeautifulSoup(raw, 'html.parser')
        card = soup.select_one('.work__card--right')
        if not card or not card.select_one('.work__title'):
            held.append({'url': record['url'], 'reason': 'Missing exact museum object fields'}); continue
        text = lambda selector: card.select_one(selector).get_text(' ', strip=True) if card.select_one(selector) else ''
        title, literal = text('.work__title'), text('.period')
        fields = {n.get('title'): n.get_text(' ', strip=True) for n in card.select('[title]') if n.get('title','').strip()}
        medium, accession = fields.get('Материал',''), fields.get('Инвентарный номер','')
        creator = text('.work__author')
        if not accession:
            held.append({'url': record['url'], 'reason': 'Missing museum accession'}); continue
        if len(re.findall(r'ДРЖ|Ж-',accession,re.I)) > 1:
            held.append({'url':record['url'],'reason':'Multiple object accessions require component review','accession':accession});continue
        if re.search(r'копия|копии|копийн|прорись|репродук|кальк|эскиз', title+' '+literal, re.I):
            held.append({'url': record['url'], 'title': title, 'reason': 'Copy, tracing or study; separate from original icon/fresco'}); continue
        fresco = bool(re.search(r'фреск', title, re.I))
        painted = bool(re.search(r'темпер|масл|энкауст|живопись', medium, re.I))
        if not painted and not fresco:
            held.append({'url': record['url'], 'title': title, 'reason': 'Source medium needs separate object-type review', 'medium': medium}); continue
        if re.search(r'хоругв|шитье|шитьё|пелен|резьба', title+' '+medium, re.I):
            held.append({'url': record['url'], 'title': title, 'reason': 'Textile, banner or carved object outside this painted-icon selection'}); continue
        w = base_work('russian-museum', urlparse(record['url']).path, record['url'], title, accession,
                      'state-russian-museum', record['capture'])
        w.update(date_display=literal or record['index_date'] or 'Date not stated', medium_text=medium or None,
                 dimensions_text=fields.get('Размер') or None,
                 cultural_context=('Byzantine icon painting; catalogue attribution: '+literal if re.search(r'Визант',literal,re.I)
                                   else 'Old Russian iconography collection; source context: '+literal)[:500])
        w['creation_year_start'], w['creation_year_end'], w['date_precision'] = russian_date(literal or record['index_date'])
        if w['creation_year_start'] and w['creation_year_start'] > 1970:
            held.append({'url': record['url'], 'title': title, 'reason': 'Creation after 1970'}); continue
        if fresco:
            w.update(work_type='fresco', object_form=None)
        if creator:
            w['creator_label'] = creator[:500]
            if creator == 'Рублев А.':
                w.update(artist_qid='Q838', attribution_role='primary')
            elif creator == 'Рублев А. и мастерская':
                w['notes'].append('Named artist and workshop retained together as a source-level attribution; no exclusive authorship assigned.')
        else:
            w['creator_label']='Creator not separately indexed; attribution and context retained from the museum record'
        # Nationality is not inferred from the museum, historical geography, or custody.
        w['source_fields'] = {'title': title, 'date': literal, 'creator': creator, 'fields': fields,
                              'index_title': record['title'], 'index_date': record['index_date'],
                              'creator_authorities': [{'label': a.get_text(' ',strip=True), 'url': urljoin(record['url'], a['href'])}
                                                     for a in card.select('.work__author a[href]')]}
        w['notes'].append('Current museum collection record and inventory establish museum connection. Source provenance is retained separately; no on-view claim. Museum image permission remains unreviewed.')
        if w['date_precision'] == 'unknown':
            w['notes'].append('Creation wording remains unresolved; no year inferred from biography, restoration, or acquisition.')
        selected.append(w)
    return selected, held


def met_candidates():
    selected, held = [], []
    for path in sorted((RUN / 'met-objects').glob('*.json')):
        record = json.loads(path.read_text())
        if 'object' not in record:
            held.append({'url': str(path), 'reason': record.get('error')}); continue
        o = record['object']
        culture = o.get('culture') or ''
        medium = o.get('medium') or ''
        if not re.search(r'Byzant|Russia|Greek|Crete|Cretan', culture+' '+(o.get('artistNationality') or ''), re.I):
            continue
        if not re.search(r'tempera|fresco|oil|encaustic', medium, re.I):
            continue
        w = base_work('met', o['objectID'], o['objectURL'], o['title'], o['accessionNumber'], 'the-met', record['capture'])
        w.update(date_display=o.get('objectDate') or 'Date not stated', medium_text=medium,
                 dimensions_text=o.get('dimensions') or None, cultural_context=culture or o.get('artistNationality'))
        if o.get('artistDisplayName'):
            w['creator_label'] = o['artistDisplayName']
        lo, hi = o.get('objectBeginDate'), o.get('objectEndDate')
        if w['date_display'] != 'Date not stated' and isinstance(lo,int) and isinstance(hi,int) and lo<=hi and hi<=1970:
            approx = bool(re.search(r'ca\.|circa|about', w['date_display'], re.I))
            w.update(creation_year_start=lo, creation_year_end=hi, date_precision=('circa' if lo==hi else 'circa_range') if approx else ('exact' if lo==hi else 'range'))
        if lo and lo>1970:
            continue
        if re.search(r'fresco', medium, re.I):
            w.update(work_type='fresco', object_form=None)
        if o.get('isPublicDomain') is True and not o.get('rightsAndReproduction') and o.get('primaryImage'):
            w['image_candidate'] = {'url': o['primaryImage'], 'rights_status': 'cc0', 'license_label': 'CC0 1.0',
                                    'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
                                    'credit': 'The Metropolitan Museum of Art; '+(o.get('creditLine') or '')}
        w['source_fields'] = {k:o.get(k) for k in ('objectID','title','accessionNumber','culture','objectDate','objectBeginDate','objectEndDate','medium','dimensions','artistDisplayName','artistWikidata_URL','objectWikidata_URL','repository','creditLine','isPublicDomain','rightsAndReproduction','primaryImage')}
        w['notes'].append('Official object metadata; museum holding and creation evidence remain separate from display status.')
        selected.append(w)
    return selected, held


def thessaloniki_candidates():
    selected,held=[],[]
    for path in sorted((RUN/'thessaloniki-objects').glob('*.json')):
        r=json.loads(path.read_text());raw=(ROOT/r['capture']['path']).read_bytes()
        assert sha(raw)==r['capture']['sha256']
        soup=BeautifulSoup(raw,'html.parser')
        fields={n.select_one('h3').get_text(' ',strip=True):n.select_one('.toggle-content').get_text(' ',strip=True)
                for n in soup.select('.text-aside-note') if n.select_one('h3') and n.select_one('.toggle-content')}
        assert fields.get('Code') and fields.get('Type')
        w=base_work('thessaloniki',urlparse(r['url']).path,r['url'],r['title'],fields['Code'],
                    'museum-of-byzantine-culture-thessaloniki',r['capture'])
        w.update(date_display=fields.get('Chronology') or 'Date not stated',medium_text=fields.get('Material of Construction'),
                 dimensions_text=fields.get('Dimensions'),cultural_context='Early Christian / Byzantine / post-Byzantine art (Museum of Byzantine Culture collection)')
        w['creation_year_start'],w['creation_year_end'],w['date_precision']=english_date(w['date_display'])
        if w['creation_year_end'] and w['creation_year_end']<330:
            held.append({'url':r['url'],'title':w['title'],'reason':'Late Roman wall painting predating this Byzantine-focused selection'});continue
        if r['category']=='wall-paintings':
            w.update(work_type='fresco',object_form=None)
        w['source_fields']=fields
        w['notes'].append('Exact museum object code and type retained. Dates of different sides remain unresolved rather than collapsed into one invented creation year. Dimensions may describe a whole tomb, as specified by the source.')
        selected.append(w)
    return selected,held


def walters_candidates():
    selected=[]
    for accession in ('37.557','37.568','37.2664','37.1183'):
        url='https://art.thewalters.org/object/'+accession+'/'
        key=sha(url.encode());body=RUN/'captures'/(key+'.body')
        if not body.exists():continue
        raw=body.read_bytes();receipt=json.loads((RUN/'captures'/(key+'.json')).read_text());assert sha(raw)==receipt['sha256']
        soup=BeautifulSoup(raw,'html.parser')
        text=lambda sel:soup.select_one(sel).get_text(' ',strip=True) if soup.select_one(sel) else ''
        title,literal,creator=text('h1.artwork--title'),text('.section__date'),text('.section__author')
        assert title and literal and creator
        fields={}
        for n in soup.select('.stat'):
            heading=n.select_one('h3');value=n.find('p',recursive=False)
            if not heading or not value:continue
            label=heading.contents[0].strip() if isinstance(heading.contents[0],str) else heading.get_text(' ',strip=True)
            fields[label]=value.get_text(' ',strip=True)
        assert fields.get('Accession Number')==accession
        category=soup.select_one('.section__category');medium=category.contents[0].strip()
        w=base_work('walters',accession,url,title,accession,'wikimedia-museum-q210081',receipt)
        w.update(date_display=literal,creator_label=creator,medium_text=medium,dimensions_text=fields.get('Measurements'),
                 cultural_context='Byzantium and Early Russia (Walters collection)')
        w['creation_year_start'],w['creation_year_end'],w['date_precision']=english_date(literal)
        # Primary museum photographs still require visual review: a multipart
        # object page can illustrate only one panel (for example 37.568).
        images=[im.get('src') for im in soup.select('img[src]') if im['src'].startswith('https://art.thewalters.org/images/art/') and '/thumbnails/' not in im['src']]
        cc=soup.select_one('a[href="https://creativecommons.org/publicdomain/zero/1.0/"]')
        if cc and images:
            w['image_candidate']={'url':images[0],'rights_status':'cc0','license_label':'CC0 1.0',
                                  'license_url':'https://creativecommons.org/publicdomain/zero/1.0/',
                                  'credit':'The Walters Art Museum; '+fields.get('Credit Line','')}
        w['source_fields']={'title':title,'date':literal,'creator':creator,'medium':medium,'fields':fields,
                            'primary_image':images[0] if images else None,'cc0_link':bool(cc)}
        w['notes'].append('One accession is one physical icon or complete multipart icon; separately photographed panels are not additional works.')
        selected.append(w)
    return selected,[]


def fresco_ensembles():
    center='https://novgorodmuseum.ru/muzei/centr-restavracii-monumentalnoj-zhivopisi'
    volotovo='https://novgorodmuseum.ru/muzei/cerkov-uspeniya-v-volotove'
    rows=[
        ('kirmuseum','ferapontov-1502','Фрески собора Рождества Богородицы Ферапонтова монастыря',
         'https://kirmuseum.org/ru/exhibitions/freski-dionisiya-v-sobore-rozhdestva-bogorodicy',
         'с 6 августа по 8 сентября (ст. ст.) 1502 г.',1502,1502,'exact','1502','Dionisy and his children (museum inscription attribution)',None),
        ('novgorod','volotovo-1363','Фресковый ансамбль церкви Успения Богородицы на Волотовом поле',volotovo,
         'храм был расписан в 1363 году',1363,1363,'exact','1363','Unidentified painters (Volotovo fresco ensemble)',None),
        ('novgorod','ilyina-1378','Фресковый ансамбль церкви Спаса Преображения на Ильине улице',volotovo,
         'с росписью Феофана Грека в церкви Спаса Преображения на Ильине улице (1378)',1378,1378,'exact','1378','Theophanes the Greek','Q319403'),
        ('novgorod','theodore-stratilates','Фресковый ансамбль церкви Феодора Стратилата на Ручью',volotovo,
         'живописью церкви Феодора Стратилата на Ручью (1370-е или 1380-е)',1370,1389,'range','1370-е или 1380-е','Unidentified painters (Theodore Stratilates fresco ensemble)',None),
        ('novgorod','kovalevo-1380','Фресковый ансамбль церкви Спаса на Ковалёве',center,
         'Спаса на Ковалево (1380 г.)',1380,1380,'exact','1380','Unidentified painters (Kovalevo fresco ensemble)',None),
        ('novgorod','skovorodka','Фресковый ансамбль церкви Архангела Михаила на Сковородке',center,
         'Архангела Михаила на Сковородке (начало XV в.)',1401,1500,'century','начало XV века','Unidentified painters (Skovorodka fresco ensemble)',None),
        ('novgorod','gorodishche','Фресковый ансамбль церкви Благовещения на Городище',center,
         'Благовещения на Городище (начало XII в.)',1101,1200,'century','начало XII века','Unidentified painters (Gorodishche fresco ensemble)',None),
    ]
    selected=[]
    for provider,oid,title,url,evidence,lo,hi,precision,literal,creator,qid in rows:
        key=sha(url.encode());body=RUN/'captures'/(key+'.body')
        if not body.exists():continue
        raw=body.read_bytes();receipt=json.loads((RUN/'captures'/(key+'.json')).read_text())
        assert sha(raw)==receipt['sha256'] and receipt['status']==200
        text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
        assert evidence in text,(oid,evidence)
        w=base_work(provider,oid,url,title,None,None,receipt)
        w.update(work_type='fresco',object_form=None,date_display=literal,creation_year_start=lo,creation_year_end=hi,date_precision=precision,
                 medium_text='Fresco ensemble',creator_label=creator,artist_qid=qid,attribution_role='primary' if qid else None,
                 cultural_context='Byzantine / Old Russian monumental painting',holding_verified=False,location_text=title)
        w['source_fields']={'cycle_identity':oid,'creation_evidence':evidence,'source_publisher':PROVIDERS[provider][0],
                            'unit':'Historic fresco ensemble, not individual scenes or restoration fragments'}
        w['notes'].append('One historic fresco ensemble is one research record. Original creation is separate from later conservation, losses and reconstruction. Museum documentation establishes the connection; no museum ownership or current-display assertion is inferred.')
        selected.append(w)
    return selected,[]


def cleveland_candidates():
    selected,held=[],[]
    url='https://openaccess-api.clevelandart.org/api/artworks/?q=icon&limit=100'
    key=sha(url.encode());raw=(RUN/'captures'/(key+'.body')).read_bytes();receipt=json.loads((RUN/'captures'/(key+'.json')).read_text())
    assert sha(raw)==receipt['sha256']
    for o in json.loads(raw)['data']:
        if o['type']!='Painting' or not re.search(r'Byzant|Russia|Cretan|Greek',' '.join(o.get('culture') or []),re.I):
            continue
        if o.get('record_type')=='part' or o.get('cover_accession_number'):
            held.append({'url':o['url'],'title':o['title'],'reason':'Component of the separately selected complete triptych; avoid duplicate whole/part records'});continue
        if o['legal_status']!='accessioned' or o['on_loan'] is not False:
            held.append({'url':o['url'],'reason':'Museum holding not established'});continue
        w=base_work('cleveland',o['id'],o['url'],o['title'],o['accession_number'],'cleveland-museum-of-art',receipt)
        w.update(date_display=o['creation_date'],creation_year_start=o['creation_date_earliest'],creation_year_end=o['creation_date_latest'],
                 date_precision='circa_range' if o['creation_date'].startswith('c.') else 'range',medium_text=o['technique'],
                 dimensions_text=o.get('measurements'),cultural_context='; '.join(o['culture'])[:500])
        if o['creators']:
            w['creator_label']='; '.join(((a.get('qualifier')+' ') if a.get('qualifier') else '')+a['description'] for a in o['creators'])[:500]
        if o['share_license_status']=='CC0' and not o.get('copyright') and not o.get('rights_and_reproductions') and (o.get('images') or {}).get('web'):
            w['image_candidate']={'url':o['images']['web']['url'],'rights_status':'cc0','license_label':'CC0 1.0',
                                  'license_url':'https://creativecommons.org/publicdomain/zero/1.0/',
                                  'credit':'The Cleveland Museum of Art; '+(o.get('creditline') or '')}
        w['source_fields']={k:o.get(k) for k in ('id','title','accession_number','record_type','cover_accession_number','culture','creators','creation_date','creation_date_earliest','creation_date_latest','technique','legal_status','on_loan','share_license_status','images','copyright','creditline')}
        if o['record_type']=='cover':
            w['notes'].append('One complete portable triptych retained as one object; three component image records are not counted as additional artworks.')
        selected.append(w)
    return selected,held


def athens_candidates():
    selected,held=[],[]
    for path in sorted((RUN/'athens-objects').glob('*.json')):
        r=json.loads(path.read_text())
        if 'capture' not in r:
            held.append({'url':r['url'],'reason':r.get('error')});continue
        fields={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in r['facts'] if ':' in s and s.split(':',1)[0] in ('Collection','Creator','Origin','Measurement','Exhibit Number')}
        if not fields.get('Exhibit Number') or not r['headings']:
            held.append({'url':r['url'],'reason':'Missing museum object identity'});continue
        title=r['headings'][-1].splitlines()[0].strip();description=' '.join(r['description'])
        if re.search(r'wood.carv|iconostasis|episcopal throne|relief',title,re.I):
            held.append({'url':r['url'],'title':title,'reason':'Carved object needs separate classification'});continue
        if re.search(r'antimension|embroider',title+' '+description,re.I) or re.search(r'engraving|print',title,re.I):
            held.append({'url':r['url'],'title':title,'reason':'Liturgical textile or print needs separate form review'});continue
        if fields.get('Collection') not in ('Icons and Wood-Carvings','Wall-paintings','Dionysios Loverdos Collection'):
            held.append({'url':r['url'],'title':title,'reason':'Different source collection'});continue
        # These two records explicitly describe separated paint layers; component
        # identities require reconciliation before representing them as one object.
        oid=re.search(r'\bid=(\d+)',r['url'])[1]
        if oid in {'23','245','237','242','243','244'}:
            held.append({'url':r['url'],'title':title,'reason':'Separated painting layers require component-identity review'});continue
        w=base_work('athens',oid,r['url'],title,fields['Exhibit Number'],'byzantine-christian-museum-athens',r['capture'])
        w.update(dimensions_text=fields.get('Measurement'),creator_label=fields.get('Creator') or w['creator_label'],
                 cultural_context='Byzantine / post-Byzantine art (Byzantine and Christian Museum collection)')
        if fields['Collection']=='Wall-paintings':
            w.update(work_type='fresco',object_form=None,medium_text='Wall painting (museum collection classification)')
        elif re.search(r'icon is made of mosaic|mosaic icon',description,re.I):
            w.update(work_type='unknown',medium_text='Mosaic icon')
            w['notes'].append('Mosaic medium preserved; general work type remains unresolved because the current taxonomy has no mosaic type.')
        elif re.search(r'combination of wood-carving and painting',description,re.I):
            w.update(work_type='unknown',medium_text='Wood carving and painting')
            w['notes'].append('Mixed carved and painted icon; current general work type remains unresolved.')
        w['source_fields']={'title':title,**fields}
        # Narrative dates are applied only through the separately reviewed map.
        reviews=RUN/'athens-date-review.json'
        review=json.loads(reviews.read_text()).get(oid) if reviews.exists() else None
        if review:
            assert review['evidence'] in description
            w.update(date_display=review['display'],creation_year_start=review['first'],creation_year_end=review['last'],date_precision=review['precision'])
            w['source_fields']['creation_date_evidence']=review['evidence']
        else:
            w['notes'].append('No separately reviewed creation date; narrative dates may describe artist activity, restoration, or other works. Kept as an undated research record.')
        w['notes'].append('Museum inventory and source provenance retained. Image permissions require a separate review.')
        selected.append(w)
    return selected,held


def assemble():
    selected, held = [], []
    for fn in (russian_candidates, met_candidates, thessaloniki_candidates, cleveland_candidates, athens_candidates, walters_candidates, fresco_ensembles):
        rows, deferred = fn(); selected.extend(rows); held.extend(deferred)
    identities={}
    for w in selected:
        if w['accession_number']:
            identities.setdefault((w['institution_slug'],accession_key(w['accession_number'])),[]).append(w)
    ambiguous={w['id'] for group in identities.values() if len(group)>1 for w in group}
    for w in selected:
        if w['id'] in ambiguous:
            held.append({'url':w['source_url'],'title':w['title'],'accession':w['accession_number'],
                         'reason':'Conflicting official records share one accession; both retained as research evidence pending identity reconciliation'})
    selected=[w for w in selected if w['id'] not in ambiguous]
    data = {'at': now(), 'records': selected, 'held': held, 'scope': 'Byzantine, post-Byzantine and Russian icons and frescoes; local review records only'}
    raw = (json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n').encode()
    pin = sha(raw)
    path = RUN / 'selections' / (pin+'.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    (RUN / 'latest-selection.json').write_text(json.dumps({'path':str(path.relative_to(ROOT)),'sha256':pin},indent=2)+'\n')
    from collections import Counter
    print(json.dumps({'selected':len(selected),'held':len(held),'providers':dict(Counter(w['provider'] for w in selected)),
                      'types':dict(Counter(w['work_type'] for w in selected)), 'dates':dict(Counter(w['date_precision'] for w in selected))}),flush=True)


def selection():
    pin=json.loads((RUN/'latest-selection.json').read_text())
    raw=(ROOT/pin['path']).read_bytes();assert sha(raw)==pin['sha256']
    plan=json.loads(raw)
    assert 0<len(plan['records'])<=1200
    for w in plan['records']:
        assert w['title'] and w['source_url'] and w['cultural_context']
        assert w['accession_number'] or w['source_fields'].get('cycle_identity')
        assert w['object_form']=='icon' or w['work_type']=='fresco'
        assert w['creation_year_start'] is None or w['creation_year_start']<=1970
        receipt=w['source_capture'];body=(ROOT/receipt['path']).read_bytes()
        assert receipt['status']==200 and sha(body)==receipt['sha256']
    return plan,pin


def accession_key(value):
    # Separators within inventory numbers carry identity: ДРЖ-1-24 != ДРЖ-124.
    return re.sub(r'\s','',unicodedata.normalize('NFKC',value or '').casefold())


def reconcile(db, plan):
    works=plan['records']
    slugs=sorted({w['institution_slug'] for w in works if w['institution_slug']})
    institutions=db.execute('SELECT * FROM institutions WHERE slug=ANY(%s)',(slugs,)).fetchall()
    byslug={i['slug']:i for i in institutions}
    urls=set()
    for w in works:
        urls.update((w['source_url'],w['source_url'].replace('https://','http://')))
    ext=db.execute("SELECT entity_id::text artwork_id,canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(list(urls),)).fetchall()
    cit=db.execute("SELECT DISTINCT entity_id::text artwork_id,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(list(urls),)).fetchall()
    byurl={}
    for row in ext+cit:
        byurl.setdefault(row['url'].replace('http://','https://'),set()).add(row['artwork_id'])
    # Scoped museum lookup; compare only bounded candidate accessions/titles.
    titles=sorted({w['title'] for w in works});keys=sorted({accession_key(w['accession_number']) for w in works})
    old=db.execute("""SELECT a.id::text,a.title,a.alternate_title,a.accession_number,a.current_institution_id::text,a.status
      FROM artworks a WHERE a.current_institution_id=ANY(%s::uuid[])
      AND (a.title=ANY(%s) OR regexp_replace(lower(coalesce(a.accession_number,'')),'[[:space:]]','','g')=ANY(%s))""",
      ([str(i['id']) for i in institutions],titles,keys)).fetchall()
    byacc={}
    for a in old:
        if a['accession_number']:
            byacc.setdefault((a['current_institution_id'],accession_key(a['accession_number'])),set()).add(a['id'])
    shared=[w for w in works if w['source_fields'].get('cycle_identity') or w['source_fields'].get('shared_source_page')]
    shared_ids={}
    if shared:
        rows=db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)",
                        (list({w['provider']+'-object' for w in shared}),list({w['source_object_id'] for w in shared}))).fetchall()
        for r in rows:shared_ids.setdefault((r['scheme'],r['external_id']),set()).add(r['entity_id'])
    new,existing,conflicts=[],[],[]
    seen={}
    for w in works:
        ids=set(byurl.get(w['source_url'],set()))
        if w['source_fields'].get('cycle_identity') or w['source_fields'].get('shared_source_page'):
            ids=set(shared_ids.get((w['provider']+'-object',w['source_object_id']),set()))
        iid=str(byslug[w['institution_slug']]['id']) if w['institution_slug'] in byslug else None
        ids.update(byacc.get((iid,accession_key(w['accession_number'])),set()))
        key=(w['institution_slug'],accession_key(w['accession_number'])) if w['accession_number'] else (w['provider'],w['source_object_id'])
        if key in seen:
            conflicts.append({'work':w,'reason':'Another selected URL has the same museum accession','other_source_url':seen[key]});continue
        seen[key]=w['source_url']
        if len(ids)>1:
            conflicts.append({'work':w,'reason':'Multiple existing records match this physical object','existing_ids':sorted(ids)})
        elif ids:
            existing.append({'work':w,'existing_id':next(iter(ids))})
        else:
            new.append(w)
    return {'new':new,'existing':existing,'conflicts':conflicts,'institutions':institutions}


def preflight():
    plan,pin=selection()
    with psycopg.connect(DSN,options='-c default_transaction_read_only=on',row_factory=dict_row) as db:
        result=reconcile(db,plan)
        result['counts']={'new':len(result['new']),'existing':len(result['existing']),'conflicts':len(result['conflicts'])}
        # Confirm the two globally scoped identity lookups use their URL indexes.
        example=[w['source_url'] for w in plan['records'][:20]]
        result['identity_query_plan']=db.execute("EXPLAIN (FORMAT JSON) SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(example,)).fetchone()['QUERY PLAN']
    path=RUN/'preflights'/(pin['sha256']+'.json')
    if not path.exists():save(path,{'at':now(),'selection':pin,**result})
    print(json.dumps(result['counts']),flush=True)


def backup():
    plan,pin=selection()
    with psycopg.connect(DSN,options='-c default_transaction_read_only=on',row_factory=dict_row) as db:
        result=reconcile(db,plan)
    assert result['new'],'No new records in the reviewed selection'
    BACKUP.mkdir(parents=True,exist_ok=True)
    receipt_path=RUN/'backup.json'
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text());p=Path(receipt['path'])
        assert p.is_relative_to(BACKUP) and p.stat().st_size==receipt['bytes']
        print('Existing verified recovery archive retained',flush=True);return
    target=BACKUP/'local-before.dump'
    assert not target.exists(),'Reconcile any unfinished backup before retrying'
    subprocess.run(['pg_dump','--format=custom','--file',str(target),DSN],check=True)
    listing=subprocess.run(['pg_restore','--list',str(target)],check=True,capture_output=True).stdout
    (BACKUP/'local-before.contents.txt').write_bytes(listing)
    assert listing and target.stat().st_size>0
    with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    receipt={'at':now(),'path':str(target),'bytes':target.stat().st_size,'sha256':digest,'contents_entries':len(listing.splitlines()),'selection':pin}
    save(receipt_path,receipt)
    print(json.dumps(receipt),flush=True)


PROVIDERS={
    'russian-museum':('State Russian Museum — iconography','https://rusmuseumvrm.ru/collections/iconography/index.php'),
    'athens':('Byzantine and Christian Museum','https://www.ebyzantinemuseum.gr/'),
    'thessaloniki':('Museum of Byzantine Culture, Thessaloniki','https://www.mbp.gr/'),
    'cleveland':('The Cleveland Museum of Art','https://www.clevelandart.org/'),
    'met':('The Metropolitan Museum of Art','https://www.metmuseum.org/'),
    'walters':('The Walters Art Museum','https://art.thewalters.org/'),
    'kirmuseum':('Kirillo-Belozersky Museum / Museum of Dionisy Frescoes','https://kirmuseum.org/'),
    'novgorod':('Novgorod Museum-Reserve','https://novgorodmuseum.ru/'),
}
SOURCE='byzantine-russian-research-20260920'
ACTOR='local-european-research'
INSTITUTION_DEFINITIONS={}
IMAGE_CAMPAIGN='byzantine-russian-icons-frescoes-20260920'
IMAGE_ASSET_FOLDER='byzantine-russian-20260920'
IMAGE_CONTACT_SHEET='/tmp/artline-icons-frescoes-20260920-contact.jpg'


def apply():
    plan,pin=selection()
    recovery=json.loads((RUN/'backup.json').read_text());dump=Path(recovery['path'])
    assert dump.is_relative_to(BACKUP) and dump.stat().st_size==recovery['bytes']
    with dump.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==recovery['sha256']
    preflight_path=RUN/'preflights'/(pin['sha256']+'.json')
    assert preflight_path.exists(),'Run read-only preflight for this exact selection first'
    with psycopg.connect(DSN,options='-c default_transaction_read_only=on',row_factory=dict_row) as db:
        initial=reconcile(db,plan)
    assert not initial['conflicts'],'Resolve candidate identity conflicts before import'
    pending=initial['new']
    batches=[]
    for start in range(0,len(pending),100):
        group=pending[start:start+100]
        batchkey=sha(('\n'.join(w['id'] for w in group)).encode())[:20]
        receipt_path=RUN/'applied'/(batchkey+'.json')
        if receipt_path.exists():
            raise ValueError('Existing receipt requires reconciliation rather than blind replay')
        with psycopg.connect(DSN,row_factory=dict_row) as db:
            db.execute('SELECT pg_advisory_xact_lock(559220260915)')
            current=reconcile(db,{'records':group})
            assert len(current['new'])==len(group) and not current['conflicts'] and not current['existing'],'Identity changed after preflight'
            owner=db.execute("SELECT * FROM curated_collections WHERE institution_id IS NULL AND curator_kind='owner' FOR UPDATE").fetchone()
            assert owner and owner['status']=='review'
            preimage_path=BACKUP/'batch-preimages'/(batchkey+'-'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json')
            save(preimage_path,{'at':now(),'selection':pin,'owner_collection':owner,'new_artwork_ids':[w['id'] for w in group], 'institutions':current['institutions']})
            institutions={i['slug']:i for i in current['institutions']}
            for slug in sorted({w['institution_slug'] for w in group if w['institution_slug']} - set(institutions)):
                if slug not in INSTITUTION_DEFINITIONS:continue
                definition=INSTITUTION_DEFINITIONS[slug]
                row=db.execute("""INSERT INTO institutions(id,slug,name,normalized_name,website_url,kind,status,description)
                  VALUES(%s,%s,%s,%s,%s,'museum','review',%s) RETURNING *""",
                  (str(uuid.uuid5(uuid.NAMESPACE_URL,definition['url'])),slug,definition['name'],norm(definition['name']),definition['url'],definition['description'])).fetchone()
                institutions[slug]=row
            if any(w['institution_slug']=='museum-of-byzantine-culture-thessaloniki' for w in group) and 'museum-of-byzantine-culture-thessaloniki' not in institutions:
                row=db.execute("""INSERT INTO institutions(id,slug,name,normalized_name,website_url,kind,status,description)
                  VALUES(%s,'museum-of-byzantine-culture-thessaloniki','Museum of Byzantine Culture, Thessaloniki',%s,'https://www.mbp.gr/','museum','review',%s) RETURNING *""",
                  (str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.mbp.gr/')),norm('Museum of Byzantine Culture, Thessaloniki'),'Official collection records document early Christian, Byzantine and post-Byzantine icons and wall paintings.')).fetchone()
                institutions[row['slug']]=row
            sources={}
            for provider in {w['provider'] for w in group}:
                name,url=PROVIDERS[provider];slug=SOURCE+'-'+provider
                db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,%s,'collection_page',%s) ON CONFLICT(slug) DO NOTHING",(slug,name,url))
                sources[provider]=db.execute('SELECT id FROM sources WHERE slug=%s',(slug,)).fetchone()['id']
            position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(owner['id'],)).fetchone()['n']
            for w in group:
                sid=sources[w['provider']];iid=institutions[w['institution_slug']]['id'] if w['institution_slug'] else None
                checked=w['source_capture']['retrieved_at']
                artist=None
                if w.get('artist_qid'):
                    artist=db.execute("SELECT a.id FROM artists a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(w['artist_qid'],)).fetchone()
                    assert artist,'Explicit creator authority is missing'
                description=w['title']+'. '+w['date_display']+'.\n\n'+w['creator_label']+'.'
                if w['medium_text']:description+='\n\nMedium: '+w['medium_text']+'.'
                if w['dimensions_text']:description+=' Dimensions: '+w['dimensions_text']+'.'
                if w['accession_number']:description+='\n\nCollection number: '+w['accession_number']+'.'
                description+='\n\n['+PROVIDERS[w['provider']][0]+' — source record]('+w['source_url']+').'
                if w['notes']:description+='\n\n'+' '.join(w['notes'])
                db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
                  work_type,object_form,medium_text,dimensions_text,unlinked_creator_label,cultural_context,accession_number,current_institution_id,
                  current_location_text,description_md,status,research_candidate,created_by,updated_by)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",
                  (w['id'],w['slug'],w['title'],norm(w['title']),w['date_display'],w['creation_year_start'],w['creation_year_end'],w['date_precision'],
                   w['work_type'],w['object_form'],w['medium_text'],w['dimensions_text'],None if artist else w['creator_label'],w['cultural_context'],w['accession_number'],
                   iid if w.get('holding_verified',True) else None,w.get('location_text'),description,ACTOR,ACTOR))
                if artist:
                    db.execute('INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,%s,%s)',
                               (w['id'],artist['id'],w['attribution_role'],w['creator_label']+'; exact museum attribution retained.'))
                scheme={'athens':'european-icons-athens-object','met':'met-object','cleveland':'cleveland-object'}.get(w['provider'],w['provider']+'-object')
                db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",
                           (w['id'],scheme,w['source_object_id'],w['source_url'],sid,checked))
                for alias in w['source_fields'].get('additional_source_records',[]):
                    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'alternate_object_identity',%s,%s,%s,%s,%s)",
                               (w['id'],sid,alias['source_object_id'],alias['source_url'],json.dumps(alias,ensure_ascii=False),alias['source_capture']['retrieved_at'],ACTOR))
                evidence=json.dumps({'source_fields':w['source_fields'],'source_capture':w['source_capture'],'notes':w['notes'],'selection_sha256':pin['sha256']},ensure_ascii=False)
                db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",
                           (w['id'],sid,w['source_object_id'],w['source_url'],evidence,checked,ACTOR))
                if iid and w.get('holding_verified',True):
                    db.execute("""INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                      VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')""",
                      (w['id'],iid,sid,w['source_url'],'Official museum object record and exact accession '+w['accession_number']+' document collection holding. No current-display claim.',checked))
                position+=1
                db.execute("INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                           (owner['id'],w['id'],position,'Owner-requested expansion of Byzantine, post-Byzantine and Russian icons and frescoes; documented source identity. Personal research selection, not a museum masterpiece designation.',sid,w['source_url'],checked))
            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(owner['id'],))
            rows=db.execute("""SELECT id::text,title,work_type,object_form,status,published_at,research_candidate,
              artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) selected
              FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id""",([w['id'] for w in group],)).fetchall()
            assert len(rows)==len(group) and all(w['status']=='review' and w['published_at'] is None and w['research_candidate'] and w['selected'] for w in rows)
            assert not db.execute("SELECT id FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND claim_type='display'",([w['id'] for w in group],)).fetchone()
        receipt={'at':now(),'selection':pin,'new_records':rows,'preimages':str(preimage_path),'local_only':True}
        save(receipt_path,receipt);batches.append(receipt_path.name)
        print('Imported and verified',start+len(group),'/',len(pending),'new review records',flush=True)
    save(RUN/'applied'/('selection-'+pin['sha256']+'.json'),{'at':now(),'selection':pin,'batches':batches,'new_records':len(pending),'existing_preserved':len(initial['existing'])})


def prepare_images():
    from PIL import Image, ImageOps, ImageDraw
    plan,pin=selection()
    c=Capture()
    source_root=Path.home()/'Library/Application Support/Artline/source-images'/IMAGE_CAMPAIGN
    originals=source_root/'originals';originals.mkdir(parents=True,exist_ok=True)
    images=[]
    for w in plan['records']:
        candidate=w['image_candidate']
        if not candidate:continue
        with psycopg.connect(DSN,options='-c default_transaction_read_only=on',row_factory=dict_row) as db:
            target=db.execute('SELECT id,primary_media_id,title FROM artworks WHERE id=%s',(w['id'],)).fetchone()
        if not target:continue
        path=RUN/'prepared-images'/(w['id']+'.json')
        if path.exists():
            images.append(json.loads(path.read_text()));continue
        if target['primary_media_id']:
            continue
        url=candidate['url'];host=urlparse(url).hostname
        assert host in {'images.metmuseum.org','openaccess-cdn.clevelandart.org','art.thewalters.org'}
        assert candidate['rights_status']=='cc0'
        try:
            try:
                raw,_=c.get('https://'+host+'/robots.txt',robot=True)
                policy=RobotFileParser();policy.parse(raw.decode(errors='replace').splitlines())
                if not policy.can_fetch(AGENT,url):raise ValueError('Image URL disallowed by robots')
            except ValueError as exc:
                if '404' not in str(exc):raise
            original=originals/(w['id']+'.source')
            if original.exists():
                raw=original.read_bytes()
            else:
                r=c.session.get(url,timeout=60,allow_redirects=False)
                assert r.status_code==200,('Image HTTP',r.status_code,url)
                raw=r.content;assert len(raw)<=12*1024*1024
                original.write_bytes(raw)
            with Image.open(io.BytesIO(raw)) as source:
                source.load();im=ImageOps.exif_transpose(source).convert('RGB')
            original_size=im.size;im.thumbnail((1280,1280))
            encoded=None
            while encoded is None:
                for quality in (88,82,76,70,64,58,50,42):
                    out=io.BytesIO();im.save(out,format='JPEG',quality=quality,optimize=True,progressive=True)
                    if len(out.getvalue())<=100000:
                        encoded=out.getvalue();break
                if encoded is None:
                    assert min(im.size)>160
                    im.thumbnail((int(im.width*.8),int(im.height*.8)))
            relative='/assets/artworks/imported/'+IMAGE_ASSET_FOLDER+'/'+w['id']+'.jpg'
            asset=ROOT/'apps/web/public'/relative.lstrip('/');asset.parent.mkdir(parents=True,exist_ok=True)
            if asset.exists():assert asset.read_bytes()==encoded
            else:asset.write_bytes(encoded)
            entry={'artwork_id':w['id'],'title':w['title'],'provider':w['provider'],'source_url':w['source_url'],
                   'source_image_url':url,'original_path':str(original),'original_sha256':sha(raw),'original_bytes':len(raw),
                   'original_dimensions':original_size,'path':relative,'sha256':sha(encoded),'bytes':len(encoded),'width':im.width,'height':im.height,
                   'checked_at':now(),'rights':candidate,'source_capture':w['source_capture'],'selection':pin,
                   'transformation':'Full composition; proportional resize, EXIF orientation and JPEG compression; no cropping'}
            save(path,entry);images.append(entry)
            print('Prepared selected image',w['title'],len(encoded),'bytes',flush=True)
        except Exception as exc:
            held=RUN/'image-held'/(w['id']+'.json')
            if not held.exists():save(held,{'artwork_id':w['id'],'url':url,'error':str(exc),'at':now()})
            print('Image held',w['title'],str(exc),flush=True)
    if images:
        sheet=Image.new('RGB',(1000,360*((len(images)+2)//3)), '#eeeeea');draw=ImageDraw.Draw(sheet)
        for i,entry in enumerate(images):
            with Image.open(ROOT/'apps/web/public'/entry['path'].lstrip('/')) as im:
                im=im.copy();im.thumbnail((320,300))
                x=(i%3)*333;y=(i//3)*360
                sheet.paste(im,(x+(330-im.width)//2,y+(300-im.height)//2))
                draw.text((x+5,y+305),str(i+1)+'. '+entry['provider'],fill='black')
                draw.text((x+5,y+325),entry['title'][:45],fill='black')
        sheet.save(IMAGE_CONTACT_SHEET)
        save(RUN/'image-contact-order.json',{'images':images,'contact_sheet':IMAGE_CONTACT_SHEET})
    print('Selected images prepared',len(images),flush=True)


def attach_images():
    review=json.loads((RUN/'image-visual-review.json').read_text())
    approved=set(review['approved_artwork_ids'])
    attached=[]
    for path in sorted((RUN/'prepared-images').glob('*.json')):
        im=json.loads(path.read_text())
        if im['artwork_id'] not in approved:continue
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert len(raw)==im['bytes']<=100000 and sha(raw)==im['sha256']
        media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/icons-media/'+im['artwork_id']+'/'+im['sha256']))
        with psycopg.connect(DSN,row_factory=dict_row) as db:
            db.execute('SELECT pg_advisory_xact_lock(559220260915)')
            before=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(im['artwork_id'],)).fetchone()['record']
            if before['primary_media_id']:
                assert before['primary_media_id']==media_id;continue
            assert before['status']=='review' and before['published_at'] is None and before['title']==im['title']
            save(BACKUP/'image-preimages'/(im['artwork_id']+'.json'),before)
            rights=im['rights'];credit=rights['credit']
            db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
              checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
              VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,'cc0',%s,%s,%s,%s,%s,%s,%s)""",
              (media_id,im['path'],im['source_url'],PROVIDERS[im['provider']][0],im['width'],im['height'],im['bytes'],im['sha256'],im['title'],
               rights['license_label'],rights['license_url'],credit,credit+'. CC0 1.0. '+im['transformation']+'.',im['checked_at'],now(),ACTOR))
            db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(media_id,ACTOR,im['artwork_id']))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE+'-'+im['provider'],)).fetchone()['id']
            db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'image_rights_and_identity',%s,%s,%s,%s,%s)",
                       (im['artwork_id'],sid,media_id,im['source_url'],json.dumps(im,ensure_ascii=False),im['checked_at'],ACTOR))
        attached.append({'artwork_id':im['artwork_id'],'media_id':media_id,'path':im['path'],'sha256':im['sha256']})
    save(RUN/'images-attached.json',{'at':now(),'records':attached,'local_only':True})
    print('Images attached and verified',len(attached),flush=True)


def correct_dates():
    plan,pin=selection()
    path=RUN/'date-corrections-reviewed.json';raw=path.read_bytes();review=json.loads(raw)
    assert review['selection']==pin
    selected={w['id'] for w in json.loads((RUN/'preflights'/(pin['sha256']+'.json')).read_text())['new']}
    receipt=RUN/'date-corrections-applied.json'
    assert not receipt.exists()
    with psycopg.connect(DSN,row_factory=dict_row) as db:
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        for change in review['records']:
            key=change['artwork_id'];assert key in selected
            before=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(key,)).fetchone()['record']
            assert before['status']=='review' and before['published_at'] is None and before['date_display']==change['date_display']
            assert all(before[k]==v for k,v in change['before'].items())
            save(BACKUP/'date-correction-preimages'/(key+'.json'),before)
            after=change['after']
            db.execute('UPDATE artworks SET creation_year_start=%s,creation_year_end=%s,date_precision=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',
                       (after['creation_year_start'],after['creation_year_end'],after['date_precision'],ACTOR,key))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE+'-russian-museum',)).fetchone()['id']
            db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'creation_date_correction',%s,%s,%s,%s)",
                       (key,sid,change['source_url'],json.dumps({'reason':review['reason'],'change':change,'review_sha256':sha(raw)},ensure_ascii=False),now(),ACTOR))
    save(receipt,{'at':now(),'review_sha256':sha(raw),'artwork_ids':[c['artwork_id'] for c in review['records']],'local_only':True})
    print('Corrected source-date interpretation for',len(review['records']),'new review records',flush=True)


def verify():
    """Read-only audit of exact receipt IDs, bounded HTTP checks and local assets."""
    from collections import Counter
    from PIL import Image
    plan,pin=selection()
    pre=json.loads((RUN/'preflights'/(pin['sha256']+'.json')).read_text())
    manifest=json.loads((RUN/'applied'/('selection-'+pin['sha256']+'.json')).read_text())
    receipt_ids=[r['id'] for name in manifest['batches'] for r in json.loads((RUN/'applied'/name).read_text())['new_records']]
    new={w['id']:w for w in pre['new']}
    corrections=json.loads((RUN/'date-corrections-reviewed.json').read_text())
    correction_receipt=json.loads((RUN/'date-corrections-applied.json').read_text())
    assert correction_receipt['review_sha256']==sha((RUN/'date-corrections-reviewed.json').read_bytes())
    for correction in corrections['records']:
        new[correction['artwork_id']].update(correction['after'])
    ids=sorted(new)
    assert len(receipt_ids)==len(set(receipt_ids))==len(ids) and set(receipt_ids)==set(ids)
    with psycopg.connect(DSN,options='-c default_transaction_read_only=on',row_factory=dict_row) as db:
        rows=db.execute("""SELECT to_jsonb(a) artwork,
          artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,
          artline_has_selection_evidence(id) selected FROM artworks a WHERE id=ANY(%s::uuid[])""",(ids,)).fetchall()
        holdings=db.execute('SELECT to_jsonb(h) record FROM artwork_location_assertions h WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
        citations=db.execute("SELECT entity_id::text artwork_id,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
        media=db.execute('SELECT a.id::text artwork_id,to_jsonb(m) record FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
        current=reconcile(db,plan)
        baseline=json.loads((RUN/'baseline.json').read_text())['records']
        old={r['artwork']['id']:r['artwork'] for r in baseline}
        old_rows=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(list(old),)).fetchall()
        baseline_changed=[r['record']['id'] for r in old_rows if r['record']!=old[r['record']['id']]]
        scoped_plan=db.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT id,title FROM artworks WHERE id=ANY(%s::uuid[])",(ids[:20],)).fetchone()['QUERY PLAN']
    assert len(rows)==len(ids) and not current['new'] and not current['conflicts']
    assert not ({w['existing_id'] for w in pre['existing']} & set(baseline_changed)),'An existing matched record changed during the campaign'
    byid={r['artwork']['id']:r for r in rows}
    for key,r in byid.items():
        w=new[key];a=r['artwork']
        for field in ('title','date_display','creation_year_start','creation_year_end','date_precision','work_type','object_form','medium_text','dimensions_text','cultural_context','accession_number'):
            assert a[field]==w[field],(key,field)
        assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and r['selected']
        assert a['unlinked_creator_label']==(None if w['artist_qid'] else w['creator_label'])
        assert any(c['artwork_id']==key and c['source_url']==w['source_url'] and c['field_name']=='official_object_identity' and pin['sha256'] in c['evidence_note'] for c in citations)
        h=[h['record'] for h in holdings if h['record']['artwork_id']==key]
        if w.get('holding_verified',True):
            assert len(h)==1 and h[0]['claim_type']=='holding' and h[0]['review_state']=='accepted' and h[0]['institution_id']==a['current_institution_id'] and h[0]['source_url']==w['source_url']
        else:
            assert not h and a['current_institution_id'] is None
    attached=json.loads((RUN/'images-attached.json').read_text())['records']
    assert {r['artwork_id'] for r in attached}=={r['artwork_id'] for r in media}
    image_checks=[]
    for row in media:
        m=row['record'];raw=(ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes()
        assert sha(raw)==m['checksum_sha256'].strip() and len(raw)==m['byte_size']<=100000 and m['rights_status']=='cc0'
        with Image.open(io.BytesIO(raw)) as im:
            im.load();assert im.size==(m['width'],m['height'])
        image_checks.append({'artwork_id':row['artwork_id'],'path':m['storage_path'],'bytes':len(raw),'sha256':sha(raw)})
    report={'at':now(),'selection':pin,'new_records':len(ids),'existing_preserved':len(pre['existing']),
            'providers':dict(Counter(w['provider'] for w in new.values())),
            'types':dict(Counter((w['work_type']+'/'+str(w['object_form'])) for w in new.values())),
            'date_precision':dict(Counter(w['date_precision'] for w in new.values())),
            'creation_scope':dict(Counter(r['scope'] for r in rows)),
            'holding_assertions':len(holdings),'display_assertions':0,'baseline_records':len(old),'baseline_artwork_changes':baseline_changed,
            'unrelated_baseline_changes':[{'id':r['record']['id'],'title':r['record']['title'],'changed_fields':[k for k,v in r['record'].items() if v!=old[r['record']['id']].get(k)],'updated_by':r['record']['updated_by']} for r in old_rows if r['record']['id'] in baseline_changed],
            'date_corrections':correction_receipt,
            'held_metadata':len(plan['held']),'held_reasons':dict(Counter(h['reason'] for h in plan['held'])),
            'images':image_checks,'id_query_plan':scoped_plan,'checks':[],
            'limitation':'Real local catalogue read-only verification; no fixture database and no production-scale benchmark. Unknown/open-ended dates remain off the dated atlas.'}
    token=re.search(r'^ARTLINE_EDITOR_TOKEN=(.*)$',(ROOT/'apps/server/.env').read_text(),re.M)[1].strip().strip('\"\'')
    session=requests.Session();session.headers['Authorization']='Bearer '+token
    api_url=os.environ.get('ARTLINE_VERIFY_API_URL','http://localhost:8081')
    web_url=os.environ.get('ARTLINE_VERIFY_WEB_URL','http://localhost:3100')
    assert urlparse(api_url).hostname in ('localhost','127.0.0.1') and urlparse(web_url).hostname in ('localhost','127.0.0.1')
    report['local_api_url']=api_url;report['local_web_url']=web_url
    report['public_research_preview']=True  # Existing local server startup configuration; unchanged by this campaign.
    def get(path,status=200,auth=True):
        started=time.monotonic()
        r=(session if auth else requests).get(api_url+'/api/v1/'+path,timeout=25)
        report['checks'].append({'path':path,'status':r.status_code,'ms':round((time.monotonic()-started)*1000)})
        assert r.status_code==status,(path,r.status_code,r.text[:300])
        return r.json()
    # Cover every source and date precision, named/anonymous creators, early
    # Byzantine works, ensembles, unusual media and every attached image.
    sample={}
    for field in ('provider','date_precision','work_type'):
        for w in new.values():sample.setdefault((field,w[field]),w)
    sample_ids={w['id'] for w in sample.values()}|{r['artwork_id'] for r in media}
    sample_ids.update(w['id'] for w in new.values() if w['artist_qid'] or w['work_type']=='unknown' or w['source_fields'].get('cycle_identity'))
    sample_ids.update(w['id'] for w in sorted(new.values(),key=lambda w:w['creation_year_start'] or 9999)[:5])
    sample_ids.update(c['artwork_id'] for c in corrections['records'])
    for key in sorted(sample_ids):
        w=new[key];eligible=byid[key]['scope']=='eligible' and w['date_precision'] not in ('after','before','unknown')
        d=get('atlas/artworks/'+key+'?preview=1',200 if eligible else 404)
        if eligible:
            for field in ('id','title','date_precision','creation_year_start','creation_year_end','work_type','object_form'):
                assert d[field]==w[field],(key,field)
            assert d['status']=='review' and d['media_url']==next((m['record']['storage_path'] for m in media if m['artwork_id']==key),None)
        if w['institution_slug']:
            d=get('museums/'+w['institution_slug']+'/works/'+key+'?preview=1')
            assert d['id']==key and d['title']==w['title'] and d['display'] is None and d['holding']['slug']==w['institution_slug']
            assert any(c['source_url']==w['source_url'] for c in d['citations'])
    slug='museum-of-byzantine-culture-thessaloniki';seen=set();cursor=''
    while True:
        page=get('museums/'+slug+'/works?preview=1&limit=5'+('&cursor='+requests.utils.quote(cursor,safe='') if cursor else ''))
        assert page['total']==20 and len(page['items'])<=5
        for item in page['items']:
            assert item['id'] not in seen and item['display'] is None
            seen.add(item['id'])
        cursor=page['next_cursor']
        if not cursor:break
    assert seen=={w['id'] for w in new.values() if w['institution_slug']==slug}
    assert get('museums/'+slug+'/works?preview=1&display=on_view')['total']==0
    key=next(key for key in sample_ids if byid[key]['scope']=='eligible')
    get('atlas/artworks/'+key,200,False);get('atlas/artworks/'+key+'?preview=1',200,False)
    # Next production servers cache their public-file inventory at startup.
    # Check a fresh instance of the existing local build without interrupting
    # the owner's running preview or rebuilding unrelated frontend work.
    preview=Path('/tmp/artline-all-zoom-web')
    assert (preview/'public').resolve()==ROOT/'apps/web/public'
    log=Path('/tmp/artline-byzantine-web-verify.log')
    with log.open('w') as out:
        proc=subprocess.Popen(['node',str(ROOT/'apps/web/node_modules/next/dist/bin/next'),'start','--port','3111','--hostname','127.0.0.1'],cwd=preview,stdout=out,stderr=subprocess.STDOUT)
        try:
            web_url='http://127.0.0.1:3111';report['local_web_url']=web_url
            for attempt in range(30):
                assert proc.poll() is None,'Temporary preview failed; inspect '+str(log)
                try:
                    response=requests.get(web_url+image_checks[0]['path'],timeout=2)
                    if response.status_code==200:break
                except requests.ConnectionError:pass
                time.sleep(.5)
            for item in image_checks:
                r=requests.get(web_url+item['path'],timeout=15)
                assert r.status_code==200 and sha(r.content)==item['sha256'],(item['path'],r.status_code)
                item['local_http_verified']=True
        finally:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
    report['preview_note']='Eight assets verified through a fresh temporary Next instance of the existing local build; it was stopped afterward. Already-running production-mode previews need a restart to discover newly added public files.'
    report['passed']=True
    save(RUN/('verification-'+datetime.now(timezone.utc).strftime('%H%M%S')+'.json'),report)
    print(json.dumps({k:report[k] for k in ('new_records','providers','types','creation_scope','baseline_artwork_changes','holding_assertions','held_metadata','passed')}),flush=True)
    print('HTTP checks',len(report['checks']),'image file checks',len(image_checks),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['probe', 'audit', 'fetch', 'collect', 'collect_met', 'collect_thessaloniki', 'assemble', 'preflight', 'backup', 'apply', 'prepare_images', 'attach_images', 'correct_dates', 'verify'])
    parser.add_argument('urls', nargs='*')
    args = parser.parse_args()
    fetch_pages(args.urls) if args.stage == 'fetch' else globals()[args.stage]()
