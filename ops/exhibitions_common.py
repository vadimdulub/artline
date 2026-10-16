"""Evidence storage and bounded source retrieval for the exhibition campaign."""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import re
import time
import unicodedata
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parents[1]
OP = 'exhibitions-100k-20261011'
RUN = ROOT / 'docs/research' / OP
DATA = Path.home() / 'Library/Application Support/Artline/source-metadata' / OP
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
TODAY = dt.date(2026, 10, 11)
UA = 'Artline exhibition history research; bounded metadata retrieval'
_db_base = None


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.app/exhibitions/' + key))


def norm(value):
    value = unicodedata.normalize('NFKD', str(value or '')).casefold()
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in value if not unicodedata.combining(c))))


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def save(path, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2, default=str).encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Immutable evidence differs: ' + str(path))
        return
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(raw)
    temp.replace(path)


def connect(write=False, local=False):
    global _db_base
    if _db_base is None:
        spec = importlib.util.spec_from_file_location('exhibition_db_base', ROOT / 'ops/cesi-top100-20261010.py')
        _db_base = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_db_base)
    return _db_base.connect(write=write, local=local)


def capture(url, params=None):
    url = requests.Request('GET', url, params=params).prepare().url
    key = sha(url.encode())
    receipt_path = RUN / 'captures' / (key + '.json')
    body_path = DATA / 'captures' / (key + '.body.gz')
    if receipt_path.exists():
        rc = load(receipt_path)
        raw = gzip.decompress(body_path.read_bytes())
        assert sha(raw) == rc['sha256']
        if rc['status'] != 200:
            raise RuntimeError(f"Captured HTTP {rc['status']}: {url}")
        return raw, rc
    hold = RUN / 'access-holds' / (urlsplit(url).hostname + '.json')
    if hold.exists():
        raise RuntimeError('Source access held: ' + url)
    # Existing campaign holds remain authoritative; no alternate host/token routing.
    if urlsplit(url).hostname in {'www.metmuseum.org', 'www.nga.gov', 'artfacts.net', 'artlas.huma-num.fr'}:
        raise RuntimeError('Previously observed source access hold: ' + url)
    for attempt in range(3):
        try:
            r = requests.get(url, headers={'User-Agent': UA}, timeout=(15, 45))
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code >= 500 and attempt < 2:
            time.sleep(2 * (attempt + 1))
            continue
        break
    rc = dict(url=url, final_url=r.url, status=r.status_code, retrieved_at=now(),
              sha256=sha(r.content), bytes=len(r.content), content_type=r.headers.get('Content-Type'),
              body_path=str(body_path))
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_bytes(gzip.compress(r.content, mtime=0))
    save(receipt_path, rc)
    if r.status_code in (401, 403, 429):
        save(hold, rc)
    r.raise_for_status()
    return r.content, rc


def exact_date(value):
    """Only explicit ISO dates; never manufacture a day from a year/month."""
    if not value:
        return None
    value = str(value).strip()
    if not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|T| )', value):
        return None
    try:
        return dt.date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def event(provider, native_id, title, url, receipt, start=None, end=None, **extra):
    title = str(title or '').strip()
    if not title:
        raise ValueError('An exhibition needs a source title')
    start_date, end_date = exact_date(start), exact_date(end)
    conflict = bool(start_date and end_date and start_date > end_date)
    state = 'held' if not conflict and end_date and end_date <= TODAY.isoformat() else 'uncertain'
    if not conflict and start_date and start_date > TODAY.isoformat():
        state = 'announced'
    row = dict(id=uid(provider + '/' + str(native_id)), provider=provider, native_id=str(native_id),
               title=title, normalized_title=norm(title) or title.casefold(), source_url=url, receipt=receipt,
               source_start=start, source_end=end, start_date=start_date, end_date=end_date,
               event_state=state, state_basis='Source exhibition-history record with explicit historical closing date' if state == 'held' else 'Dates or occurrence require review',
               date_conflict=conflict, occurrences=[], participants=[], entries=[], publications=[],
               status='review', checklist_state='unknown', source_payload={})
    row.update(extra)
    return row
