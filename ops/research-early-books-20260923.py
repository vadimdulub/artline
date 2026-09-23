#!/usr/bin/env python3
"""Capture bounded early-book candidates. Research only; no database writes."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/early-books-20260923'
TITLES = [
    'De Ceremoniis', 'Strategikon of Maurice', 'Tactica of Emperor Leo VI',
    'Strategikon of Kekaumenos', 'De velitatione bellica', 'Synopsis of Histories',
    'Chronographia', 'De Thematibus', 'Bibliotheca (Photius)', 'Pantheognosia',
    'Christian Topography', 'Alexiad', 'Hexabiblos', 'De Officiis (Pseudo-Kodinos)',
    'Almagest', 'Geography (Ptolemy)', 'Arithmetica', 'Collection (Pappus)',
    'De materia medica', 'Al-Tasrif', 'The Canon of Medicine', 'Book of Optics',
    'The Book of Healing', 'Book of Ingenious Devices',
    'The Compendious Book on Calculation by Completion and Balancing',
    'The Book of Knowledge of Ingenious Mechanical Devices', 'Tabula Rogeriana',
    'Compendium of Materia Medica', 'De revolutionibus orbium coelestium',
    'De humani corporis fabrica', 'De re metallica', 'De architectura',
    'Natural History (Pliny)', 'Dream Pool Essays', 'Shu Shu Jiu Zhang',
    'The Nine Chapters on the Mathematical Art', 'Aryabhatiya', 'Brahmasphutasiddhanta',
    'The Book of the City of Ladies', 'The Treasure of the City of Ladies',
    'The Book of Margery Kempe', 'Revelations of Divine Love', 'Scivias',
    'The Flowing Light of the Godhead', 'The Mirror of Simple Souls',
    'The Heptameron', 'The Book of the Courtier', 'Orlando Furioso',
    'Orlando Innamorato', 'The Lusiads', 'Jerusalem Delivered',
    'The Faerie Queene', 'The Tale of the Heike', 'Hōjōki', 'Tsurezuregusa',
    'The Sarashina Diary', 'The Diary of Lady Murasaki', 'Kagerō Nikki',
    'The Cloud of Unknowing', 'The Consolation of Philosophy', 'The City of God',
    'Ecclesiastical History of the English People', 'The Muqaddimah', 'Rihla',
    'The Ring of the Dove', 'The Guide for the Perplexed', 'The Incoherence of the Philosophers',
    'The Incoherence of the Incoherence', 'Hayy ibn Yaqdhan', 'Masnavi',
    'Gulistan (book)', 'Bustan (book)', 'The Knight in the Panther\'s Skin',
    'Digenes Akritas', 'The Primary Chronicle', 'The Tale of Bygone Years',
    'The Life of Saint Sava', 'A Journey Beyond the Three Seas', 'The Book of Dede Korkut',
    'Book of Lamentations (Gregory of Narek)', 'Dialogues of the Carmelites',
]


def capture(host, params):
    url = f'https://{host}/w/api.php?' + urllib.parse.urlencode({'format': 'json', 'formatversion': 2, **params})
    key = hashlib.sha256(url.encode()).hexdigest()
    path = OUT / 'sources' / (key + '.json.gz')
    receipt = path.with_suffix('.receipt.json')
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes())), json.loads(receipt.read_text())
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ArtlineEarlyBooksResearch/1.0 (selected historical works; metadata only)'})
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read()
            data = json.loads(raw)
            if 'error' in data:
                raise RuntimeError(data['error'])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(raw, mtime=0))
            proof = {'url': url, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            receipt.write_text(json.dumps(proof, indent=2) + '\n')
            time.sleep(.5)
            return data, proof
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    candidates = []
    for offset in range(0, len(TITLES), 15):
        data, proof = capture('en.wikipedia.org', {'action': 'query', 'titles': '|'.join(TITLES[offset:offset + 15]), 'redirects': 1, 'prop': 'pageprops|extracts|revisions', 'ppprop': 'wikibase_item', 'exintro': 1, 'explaintext': 1, 'exlimit': 20, 'rvprop': 'ids|timestamp'})
        for page in data['query']['pages']:
            if page.get('missing'):
                continue
            candidates.append({'title': page['title'], 'qid': page.get('pageprops', {}).get('wikibase_item'), 'extract': page.get('extract', ''), 'revision': page.get('revisions', [{}])[0].get('revid'), 'source': proof})
    entities = {}
    wanted = sorted({item['qid'] for item in candidates if item['qid']})
    for offset in range(0, len(wanted), 40):
        data, proof = capture('www.wikidata.org', {'action': 'wbgetentities', 'ids': '|'.join(wanted[offset:offset + 40]), 'props': 'info|labels|descriptions|claims|sitelinks', 'languages': 'en', 'sitefilter': 'enwiki'})
        for qid, entity in data['entities'].items():
            entities[qid] = {'entity': entity, 'source': proof}
    audit = json.loads(Path('/private/tmp/artline-early-books-audit.json').read_text())['books']
    existing = {book['qid']: book for book in audit}
    for item in candidates:
        item['existing'] = existing.get(item['qid'])
        item['wikidata'] = entities.get(item['qid'])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'candidates': len(candidates), 'new': [item['title'] for item in candidates if not item['existing']], 'existingUnhighlighted': sum(bool(item['existing']) and not item['existing']['highlight'] for item in candidates)}, indent=2))


if __name__ == '__main__':
    main()
