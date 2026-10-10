#!/usr/bin/env python3
"""Bounded Chinese pictorial-art research. No catalogue writes or image downloads."""
import argparse, collections, concurrent.futures, datetime, gzip, hashlib, json, re, time
from pathlib import Path
from urllib.parse import quote

import requests
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/chinese-art-20261008'
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(name, value):
    p = RUN / name
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, indent=2, default=str).encode()
    if p.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    p.write_bytes(raw)

def load(name):
    p = RUN / name
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())

class Source:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'ArtlineResearch/1.0 (bounded Chinese museum collection metadata research)'
        self.last = 0
        self.blocked = False

    def get(self, url, params=None, as_json=True):
        url = requests.Request('GET', url, params=params).prepare().url
        key = hashlib.sha256(url.encode()).hexdigest()
        p = RUN / 'captures' / (key + '.json')
        body = p.with_suffix('.body.gz')
        if p.exists():
            receipt = json.loads(p.read_text())
            raw = gzip.decompress(body.read_bytes())
            assert hashlib.sha256(raw).hexdigest() == receipt['sha256']
        else:
            if self.blocked:
                raise RuntimeError('Source stopped after access restriction')
            time.sleep(max(0, self.last + .45 - time.monotonic()))
            self.last = time.monotonic()
            r = self.session.get(url, timeout=(10, 35))
            raw = r.content
            assert len(raw) < 25_000_000
            receipt = dict(url=url, final_url=r.url, status=r.status_code,
                           retrieved_at=now(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            p.parent.mkdir(parents=True, exist_ok=True)
            body.write_bytes(gzip.compress(raw, mtime=0))
            p.write_text(json.dumps(receipt, indent=2))
        if receipt['status'] in (401, 403, 429):
            self.blocked = True
        if receipt['status'] != 200:
            raise RuntimeError('Source HTTP ' + str(receipt['status']) + ': ' + url)
        return (json.loads(raw) if as_json else raw.decode('utf-8', errors='replace')), receipt

    def search_post(self, url, payload):
        """Read-only public catalogue search, matching the site's own form."""
        request_key = json.dumps(dict(url=url, payload=payload), sort_keys=True, ensure_ascii=False)
        key = hashlib.sha256(request_key.encode()).hexdigest()
        p = RUN / 'captures' / (key + '.json'); body = p.with_suffix('.body.gz')
        if p.exists():
            receipt = json.loads(p.read_text()); raw = gzip.decompress(body.read_bytes())
            assert hashlib.sha256(raw).hexdigest() == receipt['sha256']
        else:
            if self.blocked: raise RuntimeError('Source stopped after access restriction')
            time.sleep(max(0, self.last + .6 - time.monotonic())); self.last = time.monotonic()
            response = self.session.post(url, json=payload, timeout=(10,35)); raw = response.content
            receipt = dict(url=url, method='POST search only', request=payload, final_url=response.url,
                status=response.status_code, retrieved_at=now(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            p.parent.mkdir(parents=True,exist_ok=True); body.write_bytes(gzip.compress(raw,mtime=0)); p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        if receipt['status'] in (401,403,429): self.blocked=True
        if receipt['status'] != 200: raise RuntimeError('Source HTTP '+str(receipt['status']))
        return raw.decode('utf-8'), receipt

def candidate(provider, raw, receipt, **kw):
    w = dict(provider=provider, raw=raw, evidence=receipt, current_display=None,
             decision='research_candidate', **kw)
    first, last = w.get('year_start'), w.get('year_end')
    w['date_decision'] = ('within_cutoff_source_bounds' if isinstance(first, int) and isinstance(last, int)
                          and -10000 <= first <= last <= 1970 else
                          'after_cutoff' if isinstance(first, int) and first > 1970 else 'date_review')
    # Permission availability is separate from final image/version review.
    w['image_decision'] = ('open_image_candidate_needs_visual_review' if w.get('image_url') and w.get('image_license_url')
                           else 'image_or_permission_research')
    return w

def cleveland():
    s = Source(); out = {}; totals = {}
    fields = 'id,accession_number,title,creation_date,creation_date_earliest,creation_date_latest,culture,technique,type,measurements,creators,legal_status,record_type,cover_accession_number,creditline,url,share_license_status,copyright,images,department,external_resources'
    for kind, cap in [('Painting', 700), ('Calligraphy', 150), ('Print', 300), ('Drawing', 100)]:
        for skip in range(0, cap, 100):
            data, rc = s.get('https://openaccess-api.clevelandart.org/api/artworks/', dict(department='Chinese Art', type=kind, limit=100, skip=skip, fields=fields))
            totals[kind] = data['info']['total']
            for w in data['data']:
                if w.get('legal_status') != 'accessioned':
                    continue
                image = (w.get('images') or {}).get('web', {}).get('url')
                row = candidate('cleveland', w, rc, source_id=str(w['id']), title=w['title'],
                    museum='The Cleveland Museum of Art', accession_number=w['accession_number'],
                    source_url=w['url'].replace('http:', 'https:'),
                    creator_label='; '.join(x.get('description') or x.get('name') or '' for x in w.get('creators', [])) or None,
                    date_display=w.get('creation_date'), year_start=w.get('creation_date_earliest'), year_end=w.get('creation_date_latest'),
                    medium=w.get('technique'), source_type=w.get('type'), culture=w.get('culture'),
                    image_url=image, image_rights_label=w.get('share_license_status'),
                    image_license_url=CC0 if w.get('share_license_status') == 'CC0' and not w.get('copyright') else None,
                    credit=w.get('creditline'), identity_note='Native inventory record; parts/ensemble relationships preserved, not automatically import-ready.')
                if w.get('cover_accession_number') or w.get('record_type') != 'object':
                    row['decision'] = 'part_or_ensemble_review'
                out[row['source_id']] = row
            print('Cleveland', kind, skip + len(data['data']), 'of', totals[kind], flush=True)
            if len(data['data']) < 100 or skip + 100 >= totals[kind]:
                break
    save('cleveland.json.gz', dict(records=list(out.values()), source_totals=totals, bounded=True))

def chicago():
    s = Source(); out = {}
    fields = 'id,title,main_reference_number,date_start,date_end,date_display,artist_display,artist_id,artist_ids,place_of_origin,dimensions,medium_display,credit_line,fiscal_year_deaccession,artwork_type_title,department_title,is_public_domain,copyright_notice,image_id'
    query = {'bool': {'filter': [{'term': {'place_of_origin.keyword': 'China'}}, {'terms': {'artwork_type_title.keyword': ['Painting','Drawing and Watercolor','Print','Miniature Painting']}}]}}
    for page in range(1, 8):
        data, rc = s.get('https://api.artic.edu/api/v1/artworks/search', {'params': json.dumps(dict(query=query, fields=fields.split(','), limit=100, page=page))})
        for w in data['data']:
            if w.get('fiscal_year_deaccession'):
                continue
            iid = w.get('image_id')
            row = candidate('chicago', w, rc, source_id=str(w['id']), title=w['title'], museum='Art Institute of Chicago',
                accession_number=w.get('main_reference_number'), source_url='https://www.artic.edu/artworks/' + str(w['id']),
                creator_label=w.get('artist_display'), date_display=w.get('date_display'), year_start=w.get('date_start'), year_end=w.get('date_end'),
                medium=w.get('medium_display'), source_type=w.get('artwork_type_title'), culture=w.get('place_of_origin'),
                image_url=f'https://www.artic.edu/iiif/2/{iid}/full/843,/0/default.jpg' if iid else None,
                image_rights_label='Public domain' if w.get('is_public_domain') else w.get('copyright_notice') or 'Not designated public domain',
                image_license_url=CC0 if w.get('is_public_domain') else None, credit=w.get('credit_line'))
            out[row['source_id']] = row
        print('Chicago', len(out), 'of', data['pagination']['total'], flush=True)
        if page >= data['pagination']['total_pages']:
            break
    save('chicago.json.gz', dict(records=list(out.values()), source_total=data['pagination']['total'], bounded=True))

def mia():
    s = Source(); out = {}
    query = 'country:"China" AND (classification:"Paintings" OR classification:"Drawings" OR classification:"Prints" OR classification:"Calligraphy")'
    for skip in range(0, 1000, 200):
        data, rc = s.get('https://search.artsmia.org/' + quote(query, safe=''), dict(size=200, **{'from': skip}))
        assert data.get('query') == query and not data.get('error') and not data.get('timed_out')
        for hit in data['hits']['hits']:
            w = hit['_source']
            if w.get('country') != 'China':
                continue
            loc = (w.get('Cache_Location') or '').replace('\\', '/')
            rendition = w.get('Primary_RenditionNumber') or ''
            image = ('https://img.artsmia.org/web_objects_cache/' + loc + '/' + rendition[:-4] + '_800.jpg') if loc and rendition.endswith('.jpg') else None
            pd = w.get('rights_type') == 'Public Domain' and w.get('restricted') in (None, 0) and not w.get('image_copyright') and w.get('Rights_Image_Display') == 'Full'
            row = candidate('mia', w, rc, source_id=str(w['id']), title=w['title'], museum='Minneapolis Institute of Art',
                accession_number=w.get('accession_number'), source_url='https://collections.artsmia.org/art/' + str(w['id']),
                creator_label=w.get('artist') or None, date_display=w.get('dated'), year_start=None, year_end=None,
                medium=w.get('medium'), source_type=w.get('classification'), culture=w.get('country'), image_url=image,
                image_rights_label=w.get('rights_type'), image_license_url='https://creativecommons.org/publicdomain/mark/1.0/' if pd else None,
                credit=w.get('creditline'), identity_note='Raw date and attribution retained; source index requires exact-object verification before attachment.')
            out[row['source_id']] = row
        print('Mia', len(out), 'of', data['hits']['total'], flush=True)
        if skip + 200 >= data['hits']['total']['value']:
            break
    save('mia.json.gz', dict(records=list(out.values()), source_total=data['hits']['total'], bounded=True))

def met():
    s = Source(); ids = []; searches = []
    for q, medium, cap in [('wall painting', None, 80), ('Dunhuang', None, 50), ('China', 'Paintings', 350), ('China', 'Prints', 80), ('China', 'Calligraphy', 80)]:
        params = dict(departmentId=6, q=q, dateBegin=-10000, dateEnd=1970, geoLocation='China', limit=cap, offset=0)
        if medium:
            params['medium'] = medium
        data, rc = s.get('https://collectionapi.metmuseum.org/public/collection/v1.1/search', params)
        searches.append(dict(query=params, result=data, evidence=rc))
        ids += [x for x in data.get('objectIDs', []) if x not in ids]
    out = []; errors = []
    for n, oid in enumerate(ids):
        try:
            w, rc = s.get('https://collectionapi.metmuseum.org/public/collection/v1/objects/' + str(oid))
            # Search results are leads; validate origin and pictorial object type again.
            origin = ' '.join(str(w.get(k) or '') for k in ('culture', 'country', 'artistNationality'))
            kind = ' '.join(str(w.get(k) or '') for k in ('classification', 'objectName', 'medium'))
            if not re.search(r'China|Chinese', origin, re.I) or not re.search(r'paint|print|calligraphy|drawing|rubbing', kind, re.I):
                continue
            out.append(candidate('met', w, rc, source_id=str(oid), title=w['title'], museum='The Metropolitan Museum of Art',
                accession_number=w.get('accessionNumber'), source_url=w.get('objectURL') or 'https://www.metmuseum.org/art/collection/search/' + str(oid),
                creator_label=w.get('artistDisplayName') or None, date_display=w.get('objectDate'), year_start=w.get('objectBeginDate'), year_end=w.get('objectEndDate'),
                medium=w.get('medium'), source_type=w.get('classification'), culture=origin.strip(), image_url=w.get('primaryImageSmall') or w.get('primaryImage') or None,
                image_rights_label='Public domain' if w.get('isPublicDomain') else w.get('rightsAndReproduction') or 'Not designated public domain',
                image_license_url=CC0 if w.get('isPublicDomain') else None, credit=w.get('creditLine')))
        except Exception as e:
            errors.append(dict(id=oid, error=str(e)))
            if s.blocked:
                break
        if (n + 1) % 50 == 0:
            save('met.json.gz', dict(records=out, searches=searches, errors=errors, bounded=True))
            print('Met', n + 1, '/', len(ids), 'accepted', len(out), flush=True)
    save('met.json.gz', dict(records=out, searches=searches, errors=errors, bounded=True))

def audit():
    rows = []
    for source in ('cleveland', 'chicago', 'mia', 'met'):
        if (RUN / (source + '.json.gz')).exists():
            rows += load(source + '.json.gz')['records']
    schemes = {'cleveland': ['cleveland-object', 'european-cleveland-cleveland-museum-of-art-object'],
               'chicago': ['aic-object','european-chicago-art-institute-of-chicago-object'], 'mia': ['mia-object'], 'met': ['met-object']}
    slugs = ['cleveland-museum-of-art','art-institute-of-chicago','minneapolis-institute-of-art','the-met']
    with psycopg.connect('postgresql://localhost/artline', row_factory=dict_row, options='-c default_transaction_read_only=on -c statement_timeout=60000') as db:
        inst = db.execute('SELECT id,slug,name FROM institutions WHERE slug=ANY(%s)', (slugs,)).fetchall()
        works = db.execute('SELECT a.id,a.title,a.accession_number,a.current_institution_id,a.primary_media_id,a.status FROM artworks a WHERE a.current_institution_id=ANY(%s::uuid[])', ([str(i['id']) for i in inst],)).fetchall()
        ext = db.execute("SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s)", (sum(schemes.values(), []),)).fetchall()
    byid = {str(w['id']): w for w in works}; native = collections.defaultdict(set); acc = collections.defaultdict(set)
    for e in ext:
        native[e['scheme'], e['external_id']].add(str(e['entity_id']))
    for w in works:
        if w['accession_number']:
            acc[str(w['current_institution_id']), w['accession_number'].strip().casefold()].add(str(w['id']))
    institution = {provider: str(next(i['id'] for i in inst if i['slug'] == slug)) for provider,slug in zip(('cleveland','chicago','mia','met'),slugs)}
    for r in rows:
        matches = set()
        for scheme in schemes[r['provider']]:
            matches |= native[scheme, r['source_id']]
        if r.get('accession_number'):
            matches |= acc[institution[r['provider']], r['accession_number'].strip().casefold()]
        r['local_matches'] = [dict(byid[x]) if x in byid else {'id':x,'outside_current_institution_scope':True} for x in sorted(matches)]
        r['local_match_decision'] = 'existing_exact_native_id_or_accession' if len(matches)==1 else 'conflicting_existing_matches' if matches else 'no_local_exact_match'
    save('candidates.json.gz', rows)
    save('local-audit.json', dict(at=now(), read_only=True, institutions=inst, scoped_artworks=len(works), records=len(rows),
        matches=dict(collections.Counter(r['local_match_decision'] for r in rows)),
        by_source=dict(collections.Counter(r['provider'] for r in rows)),
        open_image_candidates=sum(bool(r.get('image_url') and r.get('image_license_url')) for r in rows),
        source_date_decisions=dict(collections.Counter(r['date_decision'] for r in rows))))
    print(json.dumps(load('local-audit.json'),default=str,indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['cleveland','chicago','mia','met','audit','all'])
    a = p.parse_args()
    if a.action == 'all':
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {pool.submit(fn): fn.__name__ for fn in (cleveland,chicago,mia,met)}
            for job in concurrent.futures.as_completed(jobs):
                try: job.result()
                except Exception as exc:
                    save(jobs[job] + '-error.json', dict(at=now(),error=str(exc)))
                    print(jobs[job], str(exc), flush=True)
        audit()
    else:
        globals()[a.action]()
