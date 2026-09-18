#!/usr/bin/env python3
"""Capture exact Web umenia identifiers already selected for a country round."""
import argparse, collections, importlib.util, json, re
from pathlib import Path
from urllib.parse import quote

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-german-primary-objects.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
x = p.x


def capture(code, number):
    delivery = x.BASE / code / f'round-{number:02d}' / 'delivery'
    destination = delivery / 'webumenia-primary-review.json'
    if destination.exists():
        return
    out = []
    for path in sorted((delivery / 'ready').glob('*.json')):
        r = json.loads(path.read_text())['record']
        identifiers = list(dict.fromkeys(x.r.values(r['entity'], 'P5269')))
        if not identifiers:
            continue
        target = delivery / 'webumenia-primary' / (r['qid'] + '.json')
        if target.exists():
            out.append(json.loads(target.read_text()))
            continue
        e = dict(qid=r['qid'], at=x.r.core.now(), museum='webumenia',
                 ready_sha256=x.r.core.sha(path.read_bytes()), review='primary_review_required')
        try:
            assert len(identifiers) == 1 and re.fullmatch(r'[A-Z]+:[A-Z]+\.[A-Za-z0-9_.-]+', identifiers[0]), 'Single safe museum object identifier required'
            soup, receipt = p.page('https://www.webumenia.sk/en/dielo/' + quote(identifiers[0], safe=':._-'), p.ROOT / 'webumenia', r['qid'])
            fields = {}
            for tr in soup.select('tr'):
                cells = tr.find_all(['td', 'th'], recursive=False)
                if len(cells) == 2:
                    fields[cells[0].get_text(' ', strip=True).rstrip(':')] = cells[1].get_text(' ', strip=True)
            title = soup.select_one('h1[itemprop=name]')
            assert title, 'Museum object heading required'
            makers = [node.get_text(' ', strip=True) for node in soup.select('[itemprop=creator] [itemprop=name]')]
            names = {x.r.norm(name) for name in x.r.labels(r['creator_entity'])}
            creator_match = len(makers) == 1 and x.r.norm(makers[0]) in names
            key = lambda value: re.sub(r'[^a-z0-9]', '', str(value).lower())
            accession = fields.get('inventory number')
            accession_match = bool(accession and r.get('accession')) and key(accession) == key(r['accession'])
            e.update(receipt=receipt, human_url=receipt['url'],
                     object=dict(title=title.get_text(' ', strip=True), creator=makers[0] if len(makers) == 1 else None,
                                 makers=makers, accession=accession, date=fields.get('date'), type=fields.get('work type'), fields=fields),
                     creator_match=creator_match, accession_match=accession_match,
                     review='primary_object_and_creator_corroborated' if creator_match and accession_match else 'primary_review_required',
                     basis='Selected P5269 object identifier, exact inventory and single unqualified primary maker alias. Holding and technique retained as catalogue evidence; no country, display or blanket reproduction permission inferred.')
        except Exception as error:
            e['reason'] = str(error)[:350]
        x.save(target, e)
        out.append(e)
        print(code, number, r['qid'], e['review'], e.get('object', {}).get('date'), flush=True)
    x.save(destination, dict(at=x.r.core.now(), records=out, counts=dict(collections.Counter(e['review'] for e in out))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', required=True, choices=x.COUNTRIES)
    parser.add_argument('--round', required=True, type=int)
    args = parser.parse_args()
    assert 1 <= args.round <= 20
    capture(args.country, args.round)
