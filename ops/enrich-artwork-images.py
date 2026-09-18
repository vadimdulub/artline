#!/usr/bin/env python3
"""Selected existing-work image enrichment. Separate selection and apply phases.

Only museum-confirmed CC0/public-domain images; <=100,000-byte full-frame JPEGs.
No painter edits, new artworks, publication, migrations or existing-image replacement.
One worker per provider; immutable evidence and resumable per-artwork receipts.
"""
import argparse
import base64
import collections
import concurrent.futures
import csv
import hashlib
import fcntl
import io
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urlparse

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests
from PIL import Image, ImageOps
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from google.auth.credentials import Credentials

ROOT = Path(__file__).resolve().parent.parent
BUCKET = 'artline-508319-images'
ACTOR = 'local-european-research'
VERSION = 'verified-museum-images-100kb-v2'
SCHEMES = {
    'nga': 'european-nga-object',
    'met': 'european-met-the-met-object',
    'chicago': 'european-chicago-art-institute-of-chicago-object',
    'cleveland': 'european-cleveland-cleveland-museum-of-art-object',
    'smk': 'european-smk-statens-museum-for-kunst-object',
    'rijks': 'european-rijks-rijksmuseum-object',
}
EXTRA_SCHEMES = {'rijks': ['european-rijks-object']}
PROVIDERS = {'nga': 'National Gallery of Art', 'met': 'The Metropolitan Museum of Art',
             'met-commons': 'The Metropolitan Museum of Art via Wikimedia Commons',
             'chicago': 'Art Institute of Chicago', 'cleveland': 'The Cleveland Museum of Art',
             'smk': 'Statens Museum for Kunst', 'rijks': 'Rijksmuseum'}
POLICIES = {
    'nga': 'https://www.nga.gov/artworks/free-images-and-open-access',
    'met': 'https://www.metmuseum.org/about-the-met/policies-and-documents/open-access',
    'chicago': 'https://www.artic.edu/open-access/open-access-images',
    'cleveland': 'https://www.clevelandart.org/open-access',
    'smk': 'https://creativecommons.org/publicdomain/mark/1.0/',
    'rijks': 'https://creativecommons.org/publicdomain/mark/1.0/',
}
HOSTS = {'raw.githubusercontent.com', 'api.github.com', 'api.nga.gov',
         'commons.wikimedia.org', 'upload.wikimedia.org',
         'collectionapi.metmuseum.org', 'images.metmuseum.org', 'api.artic.edu',
         'www.artic.edu', 'openaccess-api.clevelandart.org', 'openaccess-cdn.clevelandart.org',
         'api.smk.dk', 'iip.smk.dk', 'data.rijksmuseum.nl', 'iiif.micr.io'}
LOCK = threading.Lock()
COUNTS = collections.Counter()
# Visually reviewed source-data error: this resource is inscribed "Veduta di
# Campo Vaccino" and is also the primary image of Met 366647. It does not depict
# the Colosseum print catalogued as 409630. A different corrected museum image
# can be considered independently; the artwork itself is retained.
KNOWN_SOURCE_IMAGE_CONFLICTS = {
    ('night-joconde', '00000060300', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/63/Don_Pedro_de_Tol%C3%A8de_baisant_l%E2%80%99%C3%A9p%C3%A9e_d%E2%80%99Henri_IV-Jean_Auguste_Dominque_Ingres-MBA_Lyon_2014.jpeg/960px-Don_Pedro_de_Tol%C3%A8de_baisant_l%E2%80%99%C3%A9p%C3%A9e_d%E2%80%99Henri_IV-Jean_Auguste_Dominque_Ingres-MBA_Lyon_2014.jpeg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('night-joconde', '06380000626', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b0/Beuckelaer_-_La_pourvoyeuse_de_legumes.jpg/960px-Beuckelaer_-_La_pourvoyeuse_de_legumes.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('met', '702925', 'https://images.metmuseum.org/CRDImages/dp/web-large/DP853117.jpg'),
    ('met', '690970', 'https://images.metmuseum.org/CRDImages/dp/web-large/DP853117.jpg'),
    ('night-commons', 'Q20268024', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8d/After_Khorkom.jpg/960px-After_Khorkom.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('night-commons', 'Q112312795', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/13/Vienna_Kaiserliches_Hofmobiliendepot_Elisabeth_of_Austria_F_X_Winterhalter_24042013_10_B.jpg/960px-Vienna_Kaiserliches_Hofmobiliendepot_Elisabeth_of_Austria_F_X_Winterhalter_24042013_10_B.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('night-commons', 'Q110249833', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4a/Penry_Williams_%281802-1885%29_-_Sgwd_Gwladys%2C_Vale_of_Neath_-_NMW_A_526_-_National_Museum_Cardiff.jpg/960px-Penry_Williams_%281802-1885%29_-_Sgwd_Gwladys%2C_Vale_of_Neath_-_NMW_A_526_-_National_Museum_Cardiff.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('night-commons', 'Q105099615', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/07/Claude_Monet_-_Glycines_W1903_-_Mus%C3%A9e_Marmottan-Monet.jpg/960px-Claude_Monet_-_Glycines_W1903_-_Mus%C3%A9e_Marmottan-Monet.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('night-commons', 'Q63952039', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/07/Claude_Monet_-_Glycines_W1903_-_Mus%C3%A9e_Marmottan-Monet.jpg/960px-Claude_Monet_-_Glycines_W1903_-_Mus%C3%A9e_Marmottan-Monet.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail'),
    ('met','409630','https://images.metmuseum.org/CRDImages/dp/web-large/DP260583.jpg'),
    # The resource shows a frontal figure, while this accession is explicitly
    # catalogued as a figure seen from behind. Commons donation identifiers
    # conflict with the poses, so no automatic replacement is authorized.
    ('met','392795','https://images.metmuseum.org/CRDImages/dp/web-large/DP812688.jpg'),
}

def validate_source_image_identity(image):
    if (image.get('provider'),str(image.get('external_id')),image.get('source_image_url')) in KNOWN_SOURCE_IMAGE_CONFLICTS:
        raise ValueError('Current source image depicts a different artwork; independently reviewed image required')


class GcloudCredentials(Credentials):
    """Use the already authorized gcloud account, without exposing its token."""
    def refresh(self, request):
        from datetime import datetime, timedelta, timezone
        self.token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
        self.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=45)


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else encode(value)
    try:
        with path.open('xb') as f:
            f.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError('Existing evidence differs: ' + str(path))


def retry_delay(value, default=60):
    try:return max(1,float(value))
    except (TypeError,ValueError):
        try:return max(1,parsedate_to_datetime(value).timestamp()-time.time())
        except (TypeError,ValueError,OverflowError):return default

def provider_rate_slot(host,cooldown=None):
    folder=Path('/Users/vadimdulub/Library/Application Support/Artline/research-rate-limits')
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(hashlib.sha256(host.encode()).hexdigest()+'.lock')
    while True:
        with path.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
            try:next_at=float(f.read() or 0)
            except ValueError:next_at=0
            now_at=time.time()
            if cooldown is not None:
                f.seek(0);f.truncate();f.write(str(max(next_at,now_at+cooldown)));f.flush();return
            wait=next_at-now_at
            if wait<=0:
                # Met publishes an 80 requests/second API limit. Use at most
                # four/second for metadata, retaining any server cooldown.
                # Image servers and other providers retain their prior pace.
                interval=0.25 if host=='collectionapi.metmuseum.org' else 1.1
                f.seek(0);f.truncate();f.write(str(now_at+interval));f.flush();return
        time.sleep(min(wait,60))


def provider_cooldown_seconds(host):
    """Observe a server cooldown without consuming a request slot or shortening it."""
    folder = Path.home() / 'Library/Application Support/Artline/research-rate-limits'
    path = folder / (hashlib.sha256(host.encode()).hexdigest() + '.lock')
    if not path.exists():
        return 0
    with path.open('r') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            return max(0, float(f.read() or 0) - time.time())
        except ValueError:
            return 0

class SourceCooldown(RuntimeError):
    def __init__(self, seconds):
        self.seconds = max(1, int(seconds) + 1)
        super().__init__('Source requested a temporary download pause')


class Fetcher:
    def __init__(self, cache):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Artline/1.0 (+https://github.com/vadimdulub/artline; selected museum open-access study images)',
                                     'AIC-User-Agent': 'Artline selected public-domain reproductions'})
        self.last = 0

    def get(self, url, limit=8_000_000):
        parsed=urlparse(url)
        if parsed.hostname in ('commons.wikimedia.org','www.wikidata.org') and parsed.path=='/w/api.php':
            folder=Path.home()/'Library/Application Support/Artline/research-rate-limits';folder.mkdir(parents=True,exist_ok=True)
            # Serialize Action API requests across all local campaign workers.
            # The existing rate slots, maxlag checks and Retry-After still apply.
            with (folder/(sha(parsed.hostname.encode())+'.inflight.lock')).open('a') as gate:
                fcntl.flock(gate,fcntl.LOCK_EX)
                return self._get(url,limit)
        return self._get(url,limit)

    def _get(self, url, limit=8_000_000):
        if urlparse(url).scheme != 'https' or urlparse(url).hostname not in HOSTS:
            raise ValueError('Unapproved source host')
        for attempt in range(3):
            provider_rate_slot(urlparse(url).hostname)
            time.sleep(max(0, 1.05 - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            try:
                response = self.session.get(url, timeout=(15, 45), stream=True, allow_redirects=False)
                if response.status_code in (429, 502, 503, 504):
                    pause=retry_delay(response.headers.get('Retry-After')) if response.status_code==429 else min(30,3*2**attempt)
                    if response.status_code==429:provider_rate_slot(urlparse(url).hostname,cooldown=pause)
                    response.close()
                    if response.status_code==429 and pause>60 and getattr(self,'defer_long_cooldowns',False):
                        raise SourceCooldown(pause)
                    time.sleep(min(pause,60))
                    continue
                response.raise_for_status()
                if response.status_code != 200:
                    raise ValueError(f'Unexpected source response {response.status_code}')
                data = bytearray()
                for chunk in response.iter_content(65536):
                    data.extend(chunk)
                    if len(data) > limit:
                        raise ValueError('Source response exceeds byte budget')
                headers = {k: response.headers.get(k) for k in ('Content-Type', 'ETag', 'Last-Modified')}
                response.close()
                return bytes(data), headers
            except (requests.RequestException, ValueError):
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        raise RuntimeError('Source unavailable after bounded retries')

    def metadata(self, url):
        key = sha(url.encode())
        path = self.cache / (key + '.json')
        if path.exists():
            return json.loads(path.read_bytes())
        data, headers = self.get(url, 8_000_000)
        value = json.loads(data)
        save_new(path, data)
        save_new(self.cache / (key + '.receipt.json'), {'url': url, 'retrieved_at': now(),
                    'sha256': sha(data), 'bytes': len(data), 'headers': headers})
        return value

    def xml(self, url):
        key = sha(url.encode())
        path = self.cache / (key + '.xml')
        if path.exists():
            return path.read_text()
        data, headers = self.get(url)
        ET.fromstring(data)
        save_new(path, data)
        save_new(self.cache / (key + '.receipt.json'), {'url': url, 'retrieved_at': now(),
                    'sha256': sha(data), 'bytes': len(data), 'headers': headers})
        return data.decode('utf-8')


def compress(data):
    with Image.open(io.BytesIO(data)) as opened:
        if opened.width * opened.height > 40_000_000:
            raise ValueError('Unexpected source dimensions')
        opened.load()
        image = ImageOps.exif_transpose(opened).convert('RGB')
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        for edge in (1200, 1000, 843, 700, 600, 500, 400):
            image.thumbnail((edge, edge), Image.Resampling.LANCZOS)
            for quality in (90, 85, 80, 75, 70, 65, 60, 55):
                output = io.BytesIO()
                image.save(output, 'JPEG', quality=quality, optimize=True, progressive=True)
                if output.tell() <= 100000:
                    return output.getvalue(), image.width, image.height, quality
    raise ValueError('Cannot meet image byte limit')


def select(args):
    excluded = set()
    for previous in args.exclude_run:
        excluded.update(c['artwork_id'] for c in json.loads((previous / 'candidates.json').read_bytes())['candidates'])
    with psycopg.connect('postgres://localhost/artline', row_factory=dict_row) as db:
        db.execute('SET TRANSACTION READ ONLY')
        selected = []
        for provider in args.providers.split(','):
            rows = db.execute('''SELECT a.id::text AS artwork_id,a.title,a.date_display,a.work_type,
                e.scheme,e.external_id,e.canonical_url AS page,e.source_id::text,
                COALESCE((SELECT string_agg(p.display_name, '; ' ORDER BY p.display_name)
                  FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'Attributed creator') AS artist,
                EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_countries ac ON ac.artist_id=aa.artist_id
                  WHERE aa.artwork_id=a.id AND ac.country_code IN ('RU','GR')) AS priority_tradition,
                EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection ds ON ds.artist_id=aa.artist_id
                  WHERE aa.artwork_id=a.id AND ds.is_popular) AS popular
              FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
              WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND a.primary_media_id IS NULL
                AND a.status<>'archived' AND e.source_id IS NOT NULL
                AND (%s='' OR a.work_type=%s) AND NOT (a.id=ANY(%s::uuid[]))
                AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
                AND artline_has_selection_evidence(a.id)
              ORDER BY priority_tradition DESC,popular DESC,(a.work_type IN ('painting','fresco','manuscript_illumination')) DESC,
                a.creation_year_start,a.normalized_title,a.id LIMIT %s''',
                ([SCHEMES[provider]] + EXTRA_SCHEMES.get(provider, []), args.work_type, args.work_type,
                 sorted(excluded), args.per_source)).fetchall()
            for row in rows:
                row['provider'] = provider
            selected.extend(rows)
            print(provider, len(rows), 'existing eligible works selected', flush=True)
    save_new(args.run / 'candidates.json', {'created_at': now(), 'version': VERSION, 'candidates': selected,
             'work_type': args.work_type or None, 'excluded_runs': [str(p) for p in args.exclude_run]})


def nga_index(fetcher):
    commit = fetcher.metadata('https://api.github.com/repos/NationalGalleryOfArt/opendata/commits/main')['sha']
    if not re.fullmatch('[a-f0-9]{40}', commit):
        raise ValueError('Invalid source revision')
    path = fetcher.cache / 'nga-published-images.csv'
    url = f'https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/{commit}/data/published_images.csv'
    if not path.exists():
        data, headers = fetcher.get(url, 120_000_000)
        save_new(path, data)
        save_new(path.with_suffix('.receipt.json'), {'url': url, 'revision': commit, 'retrieved_at': now(),
                 'sha256': sha(data), 'bytes': len(data), 'headers': headers})
    result = {}
    with path.open(newline='') as f:
        for row in csv.DictReader(f):
            if row.get('openaccess') == '1' and row.get('viewtype') == 'primary':
                oid = row['depictstmsobjectid']
                if oid not in result or row.get('sequence', '') == '0':
                    result[oid] = row
    return result


def image_record(c, fetcher, nga, chicago):
    provider, oid = c['provider'], c['external_id']
    if provider == 'nga':
        raw = nga.get(oid)
        if not raw:
            return None
        if raw['iiifurl'] != 'https://api.nga.gov/iiif/' + raw['uuid']:
            raise ValueError('NGA image identity mismatch')
        url = raw['iiifurl'] + '/full/!1000,1000/0/default.jpg'
        rights, label = 'public_domain', 'NGA Open Access — public domain'
    elif provider == 'chicago':
        raw = chicago.get(oid)
        if not raw or raw.get('is_public_domain') is not True or raw.get('copyright_notice') or not raw.get('image_id'):
            return None
        url = 'https://www.artic.edu/iiif/2/' + raw['image_id'] + '/full/843,/0/default.jpg'
        rights, label = 'cc0', 'CC0 1.0'
    elif provider == 'met':
        raw = fetcher.metadata('https://collectionapi.metmuseum.org/public/collection/v1/objects/' + quote(oid, safe=''))
        if str(raw.get('objectID')) != oid:
            raise ValueError('Met object identity mismatch')
        if raw.get('isPublicDomain') is not True or raw.get('rightsAndReproduction') or not raw.get('primaryImageSmall'):
            return None
        url = raw['primaryImageSmall']
        rights, label = 'cc0', 'CC0 1.0'
    elif provider == 'cleveland':
        raw = fetcher.metadata('https://openaccess-api.clevelandart.org/api/artworks/' + quote(oid, safe=''))['data']
        if str(raw.get('id')) != oid:
            raise ValueError('Cleveland object identity mismatch')
        if raw.get('share_license_status') != 'CC0' or raw.get('copyright'):
            return None
        url = ((raw.get('images') or {}).get('web') or {}).get('url')
        if not url:
            return None
        rights, label = 'cc0', 'CC0 1.0'
    elif provider == 'smk':
        items = fetcher.metadata('https://api.smk.dk/api/v1/art?object_number=' + quote(oid, safe='')).get('items', [])
        raw = next((r for r in items if r.get('object_number') == oid), None)
        if not raw or raw.get('public_domain') is not True or raw.get('rights') != POLICIES['smk'] or not raw.get('has_image'):
            return None
        base = raw.get('image_iiif_id', '')
        if re.fullmatch(r'https://iip\.smk\.dk/iiif/jp2/[A-Za-z0-9_.-]+', base):
            url = base + '/full/!1000,1000/0/default.jpg'
        else:
            # Current SMK records can expose only the museum's primary JPEG.
            url = raw.get('image_native') or raw.get('image_thumbnail') or ''
            if not re.fullmatch(r'https://api\.smk\.dk/api/v1/thumbnail/[A-Za-z0-9_-]{1,100}\.(?:jpg|JPG)', url):
                return None
        rights, label = 'public_domain', 'Public Domain Mark 1.0'
    elif provider == 'rijks':
        ids = [oid]
        legacy = c['scheme'] == 'european-rijks-object'
        if legacy:
            matches = fetcher.metadata('https://data.rijksmuseum.nl/search/collection?objectNumber=' + quote(oid, safe=''))
            ids = [r['id'].removeprefix('https://id.rijksmuseum.nl/') for r in matches.get('orderedItems', [])]
            if len(ids) > 10:
                raise ValueError('Ambiguous Rijksmuseum object-number search')
        raw = None
        for resolved_id in ids:
            if not re.fullmatch(r'[0-9]+', resolved_id):
                raise ValueError('Invalid Rijksmuseum object identity')
            document = fetcher.xml(f'https://data.rijksmuseum.nl/{resolved_id}?_profile=edm')
            selected = rijks_edm(document, resolved_id, oid if legacy else None)
            if selected:
                if raw:
                    raise ValueError('Multiple Rijksmuseum exact matches')
                raw = selected
        if not raw:
            return None
        url = raw['source_image_url']
        rights, label = 'public_domain', 'Public Domain Mark 1.0'
    else:
        raise ValueError('Unknown museum provider')
    return {**c, 'source_image_url': url, 'raw': raw, 'rights_status': rights,
            'license_label': label, 'policy_url': POLICIES[provider], 'checked_at': now()}


def rijks_edm(document, object_id, object_number=None):
    ns = {'ore': 'http://www.openarchives.org/ore/terms/', 'edm': 'http://www.europeana.eu/schemas/edm/',
          'dc': 'http://purl.org/dc/elements/1.1/'}
    rdf = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
    root = ET.fromstring(document)
    uri = 'https://id.rijksmuseum.nl/' + object_id
    cho = root.find('edm:ProvidedCHO', ns)
    aggregation = root.find('ore:Aggregation', ns)
    if cho is None or cho.get(rdf + 'about') != uri or aggregation is None:
        raise ValueError('Rijksmuseum EDM identity mismatch')
    relation = aggregation.find('edm:aggregatedCHO', ns)
    if relation is None or relation.get(rdf + 'resource') != uri:
        raise ValueError('Rijksmuseum aggregation identity mismatch')
    if object_number and object_number not in [r.text for r in cho.findall('dc:identifier', ns)]:
        return None
    allowed = {'http://creativecommons.org/publicdomain/mark/1.0/', POLICIES['rijks']}
    rights = [r.get(rdf + 'resource') for r in aggregation.findall('edm:rights', ns)]
    if not rights or any(r not in allowed for r in rights):
        return None
    image = aggregation.find('edm:isShownBy', ns)
    url = image.get(rdf + 'resource', '') if image is not None else ''
    match = re.fullmatch(r'https://iiif\.micr\.io/([A-Za-z0-9_-]+)/full/max/0/default\.jpg', url)
    if not match:
        return None
    resources = [r for r in root.findall('edm:WebResource', ns) if r.get(rdf + 'about') == url]
    if len(resources) != 1:
        raise ValueError('Rijksmuseum image resource mismatch')
    image_rights = resources[0].findall('edm:rights', ns) + resources[0].findall('dc:rights', ns)
    if any(r.get(rdf + 'resource') not in allowed for r in image_rights):
        return None
    return {'object_id': object_id, 'object_number': object_number, 'edm_document': document,
            'source_image_url': f'https://iiif.micr.io/{match[1]}/full/1000,/0/default.jpg',
            'image_rights': rights, 'source_primary_image': url}


def cloud_dsn():
    secret = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest',
                     '--secret=artline-database-url', '--project=artline-508319'], text=True).strip()
    fields = psycopg.conninfo.conninfo_to_dict(secret)
    fields.update(host='127.0.0.1', port='55433', sslmode='disable', connect_timeout='15')
    return psycopg.conninfo.make_conninfo(**fields)


def attach(db, image, target):
    # Queue dependent statements in the same explicit transaction. Sync the
    # identity lookup before deciding whether to enqueue the three writes.
    with db.transaction(), db.pipeline() as pipeline:
        db.execute("SET LOCAL lock_timeout='2s'")
        lookup = db.execute('''SELECT a.id::text,a.primary_media_id::text,e.source_id::text
            FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
            WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s
              AND a.status<>'archived' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
              AND artline_has_selection_evidence(a.id)
            FOR UPDATE OF a''', (image['scheme'], image['external_id']))
        pipeline.sync()
        row = lookup.fetchone()
        if not row:
            return 'artwork_not_present_or_eligible'
        if row['primary_media_id']:
            return 'attached' if row['primary_media_id'] == image['media_id'] else 'existing_media_preserved'
        if target == 'local' and row['id'] != image['artwork_id']:
            raise ValueError('Local artwork identity changed')
        db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,
            mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,
            creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
            VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(id) DO NOTHING''', (image['media_id'], image['path'], image['page'], PROVIDERS[image['provider']],
            image['width'], image['height'], image['bytes'], image['sha256'], image['title']+' — '+image['artist'],
            image['rights_status'], image['license_label'], image['policy_url'], image['artist'],
            image['artist']+'. '+image['title']+'. '+PROVIDERS[image['provider']]+'. '+image['license_label']+'. Compressed full-frame reproduction.',
            image['downloaded_at'], image['checked_at'], ACTOR))
        evidence = {k:v for k,v in image.items() if k not in ('artist','title')}
        db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,
            source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(media_id) DO NOTHING''',
            (image['media_id'], row['source_id'], image['external_id'], sha(encode(image['raw'])),
             image['source_image_url'], image['policy_url'], 'Exact museum object identifier and explicit per-image open-access/public-domain evidence; no conflicting copyright notice',
             VERSION, image['checked_at'], Jsonb(evidence)))
        db.execute('''UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s
                      WHERE id=%s AND primary_media_id IS NULL''', (image['media_id'], ACTOR, row['id']))
    return 'attached'


def event(run, value):
    with LOCK:
        with (run / 'events.jsonl').open('ab') as f:
            f.write(encode({'at':now(), 'adapter_version':VERSION, **value}) + b'\n')
        COUNTS[value['provider'] + ':' + value['outcome']] += 1


def latest_events(run):
    """Read the current checkpoint, including explicit retry events after failures."""
    path = run / 'events.jsonl'
    latest = {}
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if value.get('artwork_id'):
                latest[value['artwork_id']] = value
    return latest


class AttachmentDB:
    """Reconnect lost sessions and safely repeat an idempotent attachment."""
    def __init__(self, dsn, target):
        self.dsn, self.target, self.db = dsn, target, None

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def apply(self, image):
        for attempt in range(3):
            try:
                if self.db is None or self.db.closed:
                    self.close()
                    self.db = psycopg.connect(self.dsn, autocommit=True, row_factory=dict_row)
                return attach(self.db, image, self.target)
            except (psycopg.OperationalError, psycopg.InterfaceError) as error:
                state = error.sqlstate or ''
                # Constraint, validation, deadlock, and row-lock errors retain
                # their normal handling; only broken connections are retried.
                if state and not (state.startswith('08') or state in ('57P01','57P02','57P03')):
                    raise
                self.close()
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)


def worker(provider, candidates, args, remote_dsn):
    prepare_only = getattr(args, 'prepare_only', False)
    upload_prepared_only = getattr(args, 'upload_prepared_only', False)
    fetcher = Fetcher(args.run / 'metadata' / provider)
    nga = nga_index(fetcher) if provider == 'nga' and not upload_prepared_only else {}
    chicago = {}
    if provider == 'chicago' and not upload_prepared_only:
        fields = 'id,title,image_id,is_public_domain,copyright_notice,date_start,date_end,main_reference_number'
        for i in range(0, len(candidates), 50):
            ids = ','.join(c['external_id'] for c in candidates[i:i+50])
            raw = fetcher.metadata('https://api.artic.edu/api/v1/artworks?ids=' + ids + '&fields=' + fields + '&limit=100')
            chicago.update({str(r['id']):r for r in raw.get('data', [])})
    bucket = None if prepare_only else storage.Client(project='artline-508319', credentials=GcloudCredentials()).bucket(BUCKET)
    local = AttachmentDB('postgres://localhost/artline', 'local')
    remote = AttachmentDB(remote_dsn, 'cloud')
    failures = 0
    try:
        for c in candidates:
            receipt_path = args.run / 'images' / provider / (c['artwork_id'] + '.json')
            try:
                if receipt_path.exists():
                    image = json.loads(receipt_path.read_bytes())
                    data = (ROOT / 'apps/web/public' / image['path'].lstrip('/')).read_bytes()
                    if sha(data) != image['sha256'] or len(data)>100000:
                        raise ValueError('Cached derivative mismatch')
                else:
                    if upload_prepared_only:
                        raise ValueError('Prepared receipt required; source download is disabled')
                    selected_path = args.run / 'selected' / provider / (c['artwork_id'] + '.json')
                    image = json.loads(selected_path.read_bytes()) if selected_path.exists() else image_record(c, fetcher, nga, chicago)
                    if image is None:
                        event(args.run, {**c, 'outcome':'no_explicit_open_image'})
                        continue
                    validate_source_image_identity(image)
                    # Pinned rights and identity evidence precede the image request.
                    save_new(selected_path, image)
                    if prepare_only:
                        cooldown = provider_cooldown_seconds(urlparse(image['source_image_url']).hostname)
                        if cooldown > 60:
                            event(args.run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                                  'outcome':'source_rate_limited','retry_after_seconds':int(cooldown) + 1,
                                  'reason':'Respecting the source Retry-After; image URL and rights evidence are preserved for resume'})
                            continue
                    fetcher.defer_long_cooldowns = prepare_only
                    original, headers = fetcher.get(image['source_image_url'])
                    if image.get('commons_original_sha1') and hashlib.sha1(original).hexdigest() != image['commons_original_sha1']:
                        raise ValueError('Commons original file checksum mismatch')
                    data, width, height, quality = compress(original)
                    digest = sha(data)
                    path = f'/assets/artworks/open-museums/{provider}/{c["artwork_id"]}-{digest[:16]}.jpg'
                    save_new(ROOT / 'apps/web/public' / path.lstrip('/'), data)
                    image.update(path=path, sha256=digest, bytes=len(data), width=width, height=height,
                                 jpeg_quality=quality, source_sha256=sha(original), source_bytes=len(original),
                                 downloaded_at=now(), response_headers=headers,
                                 transform='Full-frame proportional resize and JPEG compression; no crop or generated content',
                                 media_id=str(uuid.uuid5(uuid.NAMESPACE_URL, path)))
                    save_new(receipt_path, image)
                validate_source_image_identity(image)
                if prepare_only:
                    event(args.run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                          'outcome':'prepared','path':image['path'],'sha256':image['sha256'],'bytes':image['bytes']})
                    failures = 0
                    continue
                blob = bucket.blob(image['path'].lstrip('/'))
                blob.metadata = {'sha256':image['sha256'], 'artwork-id':c['artwork_id'], 'provider':provider,
                                 'source-record-id':c['external_id'], 'license':image['license_label']}
                blob.cache_control = 'public,max-age=31536000,immutable'
                try:
                    blob.upload_from_string(data, content_type='image/jpeg', if_generation_match=0, timeout=60)
                except PreconditionFailed:
                    blob.reload(timeout=30)
                expected_md5 = base64.b64encode(hashlib.md5(data).digest()).decode()
                if blob.size != len(data) or blob.md5_hash != expected_md5:
                    raise ValueError('Google Storage checksum mismatch')
                local_result = local.apply(image)
                cloud_result = remote.apply(image)
                event(args.run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                      'outcome':'complete','local':local_result,'cloud':cloud_result,'path':image['path'],
                      'sha256':image['sha256'],'bytes':image['bytes'],'generation':blob.generation})
                failures = 0
            except SourceCooldown as error:
                event(args.run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                                'outcome':'source_rate_limited','retry_after_seconds':error.seconds,
                                'reason':'Source Retry-After retained; resume this selected image after the cooldown'})
            except Exception as error:
                # Do not include DSNs, authorization headers or credentials in receipts.
                event(args.run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                                'outcome':'failed','error':str(error)[:500]})
                failures += 1
                if failures >= 8:
                    event(args.run, {'provider':provider,'outcome':'provider_paused_after_repeated_errors'})
                    break
    finally:
        local.close()
        remote.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['select','apply'])
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--providers', default=','.join(SCHEMES))
    parser.add_argument('--per-source', type=int, default=2000)
    parser.add_argument('--work-type', default='', choices=['', 'painting', 'print', 'drawing'], help='Optional SQL selection filter')
    parser.add_argument('--exclude-run', action='append', type=Path, default=[], help='Exclude previously selected artwork IDs')
    parser.add_argument('--limit', type=int, default=0, help='Optional per-provider canary limit')
    parser.add_argument('--prepare-only', action='store_true', help='Download/compress selected images locally; do not upload or write either database')
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=True)
    if args.phase == 'select':
        select(args)
        return
    document = json.loads((args.run / 'candidates.json').read_bytes())
    done = set()
    if (args.run / 'events.jsonl').exists():
        for line in (args.run / 'events.jsonl').read_text().splitlines():
            r = json.loads(line)
            if r['outcome'] == 'complete' or (args.prepare_only and r['outcome'] == 'prepared') or (r['outcome'] == 'no_explicit_open_image' and r.get('adapter_version') == VERSION):
                done.add(r['artwork_id'])
    grouped = collections.defaultdict(list)
    for candidate in document['candidates']:
        if candidate['artwork_id'] not in done and candidate['provider'] in args.providers.split(','):
            grouped[candidate['provider']].append(candidate)
    dsn = None if args.prepare_only else cloud_dsn()
    print('Starting', {p:min(len(c),args.limit) if args.limit else len(c) for p,c in grouped.items()}, flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        pending = {pool.submit(worker,p,c[:args.limit] if args.limit else c,args,dsn):p for p,c in grouped.items()}
        while pending:
            finished,_ = concurrent.futures.wait(pending,timeout=30,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in finished:
                provider = pending.pop(future)
                try: future.result()
                except Exception as error:
                    event(args.run, {'provider':provider,'outcome':'provider_failed','error':str(error)[:500]})
            print(now(), dict(COUNTS), flush=True)


if __name__ == '__main__':
    main()
