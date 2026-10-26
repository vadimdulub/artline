"""Finite serial source research for the complete published Rouen catalogue.

Metadata discovery only; image downloads and catalogue writes are separate.
"""
import argparse
import collections
import gzip
import json
import shutil
import time
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
import exhibitions_common as c

E = c.ROOT / 'docs/research/catalogue-deduplication-20261026'
D = Path.home() / 'Library/Application Support/Artline/source-metadata/catalogue-deduplication-20261026'
UA = 'ArtlineResearch/1.0 (+https://artlines.org; finite exact Rouen museum object research)'
LIMIT = 1024**3
RESERVE = 15 * 1024**3


def field(soup, label):
    node = soup.find(string=label)
    return node.parent.find_next_sibling().get_text(' ', strip=True) if node and node.parent.find_next_sibling() else None


def discover():
    native = c.load(D / 'rouen-native-complete.json.gz')
    selected = [r for r in native['rows'] if r['Presence_image'] and
                any(x in (r.get('Domaine') or '') for x in ['peinture', 'dessin', 'estampe', 'enluminure'])]
    assert len(selected) == 1723 and len({r['Reference'] for r in selected}) == 1723
    robots = c.load(E / 'rouen-pop-image-route-preflight.json')[0]
    assert robots['status'] == 200
    import urllib.robotparser
    robot = urllib.robotparser.RobotFileParser()
    robot.parse(gzip.decompress(Path(robots['body_path']).read_bytes()).decode(errors='replace').splitlines())
    inherited = c.load(c.ROOT / 'docs/research/low-image-painters-100-wave2-20261026/source-holds-preflight.json')
    assert 'pop.culture.gouv.fr' not in inherited['denied_hosts']
    assert not (E / 'rouen-pop-access-hold.json').exists()
    assert shutil.disk_usage(D).free > RESERVE
    total_bytes = sum(f.stat().st_size for f in D.rglob('*') if f.is_file())
    session = requests.Session()
    session.headers['User-Agent'] = UA
    folder = D / 'rouen-notices'
    folder.mkdir(exist_ok=True)
    summaries = []
    consecutive_transport_failures = 0
    for number, raw_record in enumerate(selected, 1):
        ref = raw_record['Reference']
        path = folder / (ref + '.json.gz')
        if path.exists():
            summaries.append(c.load(path))
            continue
        assert shutil.disk_usage(D).free > RESERVE and total_bytes < LIMIT
        url = 'https://pop.culture.gouv.fr/notice/joconde/' + ref
        assert robot.can_fetch('ArtlineResearch', url)
        began = time.monotonic()
        response = None
        for attempt in range(2):
            try:
                response = session.get(url, timeout=(8, 20), allow_redirects=False)
                consecutive_transport_failures = 0
                break
            except requests.RequestException as error:
                failures = E / 'rouen-notice-transport-errors'
                failures.mkdir(exist_ok=True)
                stamp = str(time.time_ns())
                c.save(failures / (ref + '-' + stamp + '.json'),
                       dict(at=c.now(), native_id=ref, url=url, attempt=attempt + 1,
                            error=type(error).__name__ + ': ' + str(error)[:500]))
                session.close()
                session = requests.Session()
                session.headers['User-Agent'] = UA
                if attempt == 0:
                    time.sleep(2)
        if response is None:
            result = dict(native_id=ref, state='bounded_transport_gap', images=[],
                          url=url, checked_at=c.now())
            c.save(path, result)
            summaries.append(result)
            consecutive_transport_failures += 1
            if consecutive_transport_failures >= 3:
                raise RuntimeError('Three consecutive source transport gaps; checkpointed finite research stopped')
            continue
        content = response.content
        assert len(content) < 2_000_000
        body = folder / (ref + '.html.gz')
        packed = gzip.compress(content, mtime=0)
        body.write_bytes(packed)
        total_bytes += len(packed)
        receipt = dict(url=url, status=response.status_code, retrieved_at=c.now(),
                       bytes=len(content), sha256=c.sha(content), body_path=str(body),
                       content_type=response.headers.get('Content-Type'), location=response.headers.get('Location'))
        if response.status_code in [401, 402, 403, 429]:
            c.save(E / 'rouen-pop-access-hold.json', receipt)
            raise RuntimeError('POP access hold preserved; no alternate retrieval')
        result = dict(native_id=ref, receipt=receipt, state='source_http_' + str(response.status_code), images=[])
        if response.status_code == 200:
            soup = BeautifulSoup(content, 'html.parser')
            result['fields'] = {label: field(soup, label) for label in [
                "Numéro d'inventaire", 'Titre', 'Auteur', 'Crédits photographiques',
                'Date de création', 'Millésime de création', 'Période de création', 'Dénomination', 'Domaine',
                'Matériaux et techniques', 'Mesures', 'Localisation', 'Lieu de conservation',
                'Sujet représenté', 'Statut juridique', 'Historique', 'Genèse']}
            result['source_reference'] = field(soup, 'Référence de la notice')
            if not result['fields']["Numéro d'inventaire"] or result['source_reference'] != ref:
                result['state'] = 'notice_shell_or_reference_conflict'
            else:
                for node in soup.select('img[src]'):
                    rendered = urljoin(url, node['src'])
                    image = parse_qs(urlsplit(rendered).query).get('url', [rendered])[0]
                    if '/joconde/' + ref + '/' in image and image not in [x['url'] for x in result['images']]:
                        result['images'].append(dict(url=image, rendered_src=rendered, alt=node.get('alt')))
                result['state'] = 'published_images' if result['images'] else 'no_image_in_current_notice'
                result['metadata_licence_is_not_image_licence'] = True
        c.save(path, result)
        total_bytes += path.stat().st_size
        summaries.append(result)
        if number % 25 == 0:
            print('Rouen exact notices', number, '/', len(selected), dict(collections.Counter(x['state'] for x in summaries)), flush=True)
            checkpoint = dict(at=c.now(), selected_notices=len(selected), completed=len(summaries),
                              outcomes=dict(collections.Counter(x['state'] for x in summaries)),
                              scope='Metadata discovery only; no image downloads or catalogue writes.',
                              directory=str(folder), metadata_bytes=total_bytes)
            temp = E / 'rouen-notice-discovery-checkpoint.tmp'
            temp.write_text(json.dumps(checkpoint, indent=2) + '\n')
            temp.replace(E / 'rouen-notice-discovery-checkpoint.json')
        time.sleep(max(0, 1.1 - (time.monotonic() - began)))
    summary = dict(at=c.now(), complete=True, selected_notices=len(selected), completed=len(summaries),
                   outcomes=dict(collections.Counter(x['state'] for x in summaries)),
                   published_image_candidates=sum(len(x['images']) for x in summaries),
                   discovery_is_not_visual_review_or_delivery=True, metadata_bytes=total_bytes)
    c.save(E / 'rouen-notice-discovery-complete.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['discover'])
    args = parser.parse_args()
    globals()[args.phase]()
