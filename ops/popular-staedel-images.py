#!/usr/bin/env python3
"""Selected existing paintings, matched to Städel's current per-object image release."""
import argparse
import importlib.util
import json
import re
import time
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('staedel_core', ROOT / 'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
PROVIDER = 'popular-staedel'
HOST = 'https://sammlung.staedelmuseum.de'
PDM = 'https://creativecommons.org/publicdomain/mark/1.0/'
CREDIT = 'Städel Museum, Frankfurt am Main'
core.PROVIDERS[PROVIDER] = 'Städel Museum'
core.HOSTS.update({'sammlung.staedelmuseum.de', 'cdn.staedelmuseum.de'})
core.VERSION = 'staedel-exact-object-download-pdm-v1'


def norm(value):
    return ' '.join(unicodedata.normalize('NFKC', value).split()).casefold()


def parse_object(document, page):
    if not re.fullmatch(HOST + r'/(?:en/work|de/werk)/[a-z0-9-]+', page):
        raise ValueError('Unapproved object page')
    soup = BeautifulSoup(document, 'html.parser')
    canonical = soup.select_one('meta[property="og:url"]')
    if not canonical or canonical.get('content') != page:
        raise ValueError('Object canonical page differs')
    properties = {}
    for row in soup.select('dl.dsProperty'):
        key, value = row.find('dt'), row.find('dd')
        if key and value:
            properties.setdefault(key.get_text(' ', strip=True), set()).add(value.get_text(' ', strip=True))

    def one(*keys):
        values = set().union(*(properties.get(k, set()) for k in keys))
        if len(values) != 1:
            raise ValueError('Absent or conflicting source property: ' + keys[0])
        return values.pop()

    caption = soup.select_one('h1 .dsArtwork__titleCaption')
    date = soup.select_one('h1 .dsArtwork__titleYear')
    image = soup.select_one('meta[property="og:image"]')
    if not caption or not date or not image:
        raise ValueError('Primary artwork presentation unavailable')
    date_text = date.get_text(' ', strip=True).lstrip(', ').strip()
    match = re.fullmatch(r'(\d{4})(?:\s*[–—-]\s*(\d{4}))?', date_text)
    if not match:
        raise ValueError('Unresolved source creation date')
    image_url = image['content']
    accession = one('Inventory Number', 'Inventarnummer')
    compact = re.sub(r'\s', '', accession).lower()
    if not re.fullmatch(r'https://cdn\.staedelmuseum\.de/images/[a-f0-9]{2}/[a-f0-9]{2}/' + re.escape(compact) + r'/thumb-xl\.jpg', image_url):
        raise ValueError('Primary image accession or host differs')
    title, artist = one('Title', 'Titel'), one('Painter', 'Maler')
    if norm(caption.get_text(' ', strip=True)) != norm(title):
        raise ValueError('Primary title differs')
    primary = [i for i in soup.select('img[src]') if i['src'] == image_url]
    if not primary or any(i.get('alt') != title + ', ' + artist for i in primary):
        raise ValueError('Primary image is not the depicted artwork')
    button = soup.select_one('button[data-action="download"]')
    if not button or button.get('data-target') != page + '/download':
        raise ValueError('Object download statement unavailable')
    return dict(page=page, title=title, artist=artist, accession_number=accession,
                year_start=int(match[1]), year_end=int(match[2] or match[1]), date_text=date_text,
                object_type=one('Object Type', 'Objektart'), museum=one('Institution'),
                credit=one('Creditline'), image_rights=one('Picture Copyright', 'Bildrechte'),
                image_url=image_url, download_url=button['data-target'])


def parse_download(data, page):
    if len(data) != 1 or data[0].get('action') != 'layer':
        raise ValueError('Unexpected image download response')
    soup = BeautifulSoup(data[0]['content'], 'html.parser')
    form = soup.find('form')
    if not form or form.get('action') != page + '/download':
        raise ValueError('Download belongs to another object')
    links = [a['href'] for a in form.select('a[href]') if 'creativecommons.org' in a['href']]
    paragraphs = [p.get_text(' ', strip=True) for p in form.find_all('p')]
    text = ' '.join(paragraphs)
    if links != [PDM] or not ('without restrictions' in text or 'uneingeschränkt' in text):
        raise ValueError('Exact download lacks unrestricted Public Domain Mark')
    if re.search(r'non-commercial|nicht.kommerziell|permission required|rights reserved', text, re.I):
        raise ValueError('Conflicting download restriction')
    files = [f.get('value') for f in form.select('input[name="files[]"]')]
    if len(files) != 1 or not re.fullmatch(r'[a-f0-9]{8}', files[0] or '') or CREDIT not in text:
        raise ValueError('Ambiguous image download or absent attribution')
    # Session/CSRF tokens and authored artwork descriptions are never retained.
    return {'url': page + '/download', 'image_file_id': files[0], 'licence_uri': links[0],
            'rights_statement': paragraphs[0], 'credit': CREDIT}


def verify(im):
    obj, rights = im['raw']['object'], im['raw']['download_rights']
    if im['scheme'] != 'european-staedel-object' or im['external_id'] != im['accession_number']:
        raise ValueError('Native source identity differs')
    if norm(obj['accession_number']) != norm(im['accession_number']):
        raise ValueError('Accession differs')
    if obj['museum'] != 'Städel Museum' or im['museum'] != obj['museum'] or im['country_code'] != 'DE':
        raise ValueError('Holding institution differs')
    if obj['object_type'] not in ('painting (artwork)', 'Gemälde') or im['work_type'] != 'painting':
        raise ValueError('Source classification differs')
    if norm(obj['title']) != norm(im['title']) or norm(obj['artist']) != norm(im['artist']) or im['roles'] != ['primary']:
        raise ValueError('Title or primary creator differs')
    if (obj['year_start'], obj['year_end']) != (im['creation_year_start'], im['creation_year_end']) or not 1000 <= obj['year_start'] <= obj['year_end'] <= 1970:
        raise ValueError('Artwork creation bounds differ')
    if obj['image_rights'] != 'Public Domain' or rights['licence_uri'] != PDM or im['policy_url'] != PDM or im['rights_status'] != 'public_domain':
        raise ValueError('Exact image rights differ')
    if obj['page'] != im['page'] or im['source_record_url'] != im['page'] or rights['url'] != im['page'] + '/download':
        raise ValueError('Object and rights source differ')
    if im['source_image_url'] != obj['image_url'] or urlparse(im['source_image_url']).hostname != 'cdn.staedelmuseum.de':
        raise ValueError('Image resource differs')
    if CREDIT not in im['creator_credit'] or CREDIT not in im['attribution_text'] or PDM not in im['attribution_text']:
        raise ValueError('Required image provenance missing')
    for key in ('object_capture', 'rights_capture'):
        if not im['raw'][key].get('sha256') or not im['raw'][key].get('retrieved_at'):
            raise ValueError('Source retrieval evidence missing')


base_attach = core.attach


def attach(db, im, target):
    verify(im)
    with db.transaction():
        row = db.execute("""SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,
          a.work_type,a.status,a.current_institution_id::text,
          ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) artists
          FROM artworks a WHERE a.id=%s FOR UPDATE""", (im['target_ids'][target],)).fetchone()
        if not row or row['status'] != 'review' or row['current_institution_id'] != im['institution_ids'][target] or row['artists'] != im['artist_ids'][target]:
            raise ValueError('Current target creator or institution changed')
        if any(row[k] != im[k] for k in ('title', 'accession_number', 'creation_year_start', 'creation_year_end', 'work_type')):
            raise ValueError('Current target artwork facts changed')
        result = base_attach(db, im, target)
        if result == 'attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',
                       (im['creator_credit'], im['attribution_text'], im['media_id']))
        return result


core.attach = attach


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True, type=Path)
    args = parser.parse_args()
    assert (args.run.parent / 'backups.json').exists()
    fetch = core.Fetcher(args.run / 'source-evidence')
    robots, _ = fetch.get(HOST + '/robots.txt', 100000)
    policy = RobotFileParser(); policy.parse(robots.decode().splitlines())
    rows = json.loads((args.run / 'candidates.json').read_text())['candidates']
    done = {k for k, v in core.latest_events(args.run).items() if v['outcome'] in ('prepared', 'complete')}
    for c in rows:
        if c['artwork_id'] in done:
            continue
        try:
            captures = []
            payloads = []
            for url in (c['page'], c['page'] + '/download'):
                if not policy.can_fetch('Artline', url):
                    raise ValueError('Robots policy disallows this record')
                body, _ = fetch.get(url, 2000000)
                captures.append({'url': url, 'retrieved_at': core.now(), 'sha256': core.sha(body)})
                payloads.append(body)
                time.sleep(1)
            obj = parse_object(payloads[0], c['page'])
            rights = parse_download(json.loads(payloads[1]), c['page'])
            im = dict(c, provider=PROVIDER, source_name='Städel Museum', source_record_url=c['page'],
                      source_object_id=c['external_id'], source_image_url=obj['image_url'], policy_url=PDM,
                      rights_status='public_domain', license_label='Public Domain Mark 1.0',
                      creator_credit=c['artist'] + '; ' + CREDIT,
                      attribution_text=f"{c['artist']}. {c['title']}. {CREDIT}. Public Domain Mark ({PDM}). Full-frame proportional resize and JPEG compression.",
                      checked_at=core.now(), rights_verified_at=core.now(), creation_date=obj['date_text'],
                      raw={'object': obj, 'download_rights': rights, 'object_capture': captures[0], 'rights_capture': captures[1]})
            verify(im)
            core.save_new(args.run / 'selected' / PROVIDER / (c['artwork_id'] + '.json'), im)
            core.worker(PROVIDER, [im], SimpleNamespace(run=args.run, prepare_only=True), None)
        except ValueError as exc:
            core.event(args.run, {'provider': PROVIDER, 'artwork_id': c['artwork_id'], 'outcome': 'manual_review', 'reason': str(exc)})
    print(json.dumps(dict(core.COUNTS)))


if __name__ == '__main__':
    main()
