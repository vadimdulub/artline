#!/usr/bin/env python3
"""Bounded metadata-only Vatican icon capture; never connects to a database.

Resume uses immutable captures. No image requests, retries, or enumeration.
"""
import datetime
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'docs/research/continuous-production-20261011/batches/000051'
CAP = Path.home() / 'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000051'
OBJECTS = ['MV.40076.0.0', 'MV.40045.0.0', 'MV.64662.0.0', 'MV.61191.0.0']


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, f'Immutable evidence differs: {path}'
    else:
        path.write_bytes(data)


def capture(key, url):
    receipt = CAP / (key + '.json')
    body_path = CAP / (key + '.html')
    if receipt.exists():
        result = json.loads(receipt.read_text())
        assert result['url'] == url
        assert sha(body_path.read_bytes()) == result['sha256']
        return result
    req = urllib.request.Request(url, headers={'User-Agent': 'Artline bounded source research/1.0', 'Accept': 'text/html'})
    at = now()
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read(2_000_001)
            assert len(body) <= 2_000_000, 'Bounded metadata response exceeded'
            status = response.status
            final_url = response.url
            content_type = response.headers.get('Content-Type')
            retry_after = response.headers.get('Retry-After')
    except urllib.error.HTTPError as error:
        body = error.read(100_000)
        status = error.code
        final_url = error.url
        content_type = error.headers.get('Content-Type')
        retry_after = error.headers.get('Retry-After')
    except (urllib.error.URLError, TimeoutError) as error:
        body = b''
        status = None
        final_url = url
        content_type = None
        retry_after = None
    body_path.parent.mkdir(parents=True, exist_ok=True)
    assert not body_path.exists(), 'Unreceipted capture requires recovery review'
    body_path.write_bytes(body)
    result = dict(url=url, final_url=final_url, retrieved_at=at, status=status,
                  content_type=content_type, retry_after=retry_after, attempts=1,
                  body_path=str(body_path), sha256=sha(body), bytes=len(body),
                  image_download=False, database_connection=False)
    save(receipt, result)
    return result


def main():
    records = []
    for native_id in OBJECTS:
        result = capture(native_id, 'https://catalogo.museivaticani.va/index.php/Detail/objects/' + native_id)
        records.append(dict(native_id=native_id, **result))
        print(native_id, result['status'], result['bytes'], flush=True)
        if result['status'] in [401, 403, 429] or result['status'] is None:
            break  # Do not retry an access-held host or transient route.
    save(E / 'source-capture-manifest.json', dict(
        route='vatican_museums_native_inventory', maximum_objects=4,
        records=records, remaining_native_ids=OBJECTS[len(records):],
        images_requested=0, database_connections=0))


if __name__ == '__main__':
    main()
