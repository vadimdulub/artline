#!/usr/bin/env python3
"""Capture a bounded war-literature selection; audit the real catalogue read-only."""
import importlib.util
import json
from pathlib import Path
import sys

import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ops'))
spec = importlib.util.spec_from_file_location('war_book_sources', ROOT / 'ops/research-early-books-20260923.py')
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)
research.OUT = ROOT / 'docs/research/war-books-africa-20261004'
TITLES = [
    'Thebes at War', 'Palace Walk', 'Palace of Desire', 'Sugar Street',
    'The Man Died: Prison Notes of Wole Soyinka', 'Season of Anomy',
    'Madmen and Specialists', 'A Shuttle in the Crypt', 'Hosties noires',
    'The Old Man and the Medal', 'God\'s Bits of Wood', 'Tribal Scars',
    'A Grain of Wheat', 'Weep Not, Child', 'Remember Ruben',
    'The Dark Child', 'The Radiance of the King', 'The Last of the Empire',
    'The Poor Christ of Bomba', 'The Thief and the Dogs', 'Adrift on the Nile',
    'Once There Was a War', 'Bombs Away (book)', 'Men at War',
    'Dragon Seed', 'The Promise (Buck novel)', 'China Sky', 'China Flight',
    'A Fable', 'Soldiers\' Pay', 'Above the Battle', 'Clérambault', 'Pierre et Luce',
    'Where Were You, Adam?', 'The Silent Angel', 'The Flanders Road',
    'The Georgics', 'They Fought for Their Country', 'Tales from the Don',
    'The Thibaults', 'Summer 1914', 'The Red Wheel', 'August 1914',
    'One of Ours', 'Civilisation (book)', 'Wooden Crosses',
    'The Life of the Martyrs', 'Fear (Chevallier novel)', 'Company K',
    'The Case of Sergeant Grischa', 'Education Before Verdun',
    'The Seventh Cross', 'Transit (Seghers novel)', 'The Dead Stay Young',
    'The Human Species', 'The Silence of the Sea', 'The Kites (novel)',
    'The Roots of Heaven', 'The Tin Flute', 'The Bridge over the River Kwai',
    'Hiroshima (book)', 'A Bell for Adano', 'The Wall (Hersey novel)',
    'The Caine Mutiny', 'Guard of Honor', 'A Time to Love and a Time to Die',
    'Captain Corelli\'s Mandolin', 'The English Patient', 'The Ghost Road',
    'The Famished Road', 'Sozaboy', 'The Joys of Motherhood',
    'Sleepwalking Land', 'Allah Is Not Obliged', 'Monnè, outrages et défis',
    'Palace of Desire (novel)', 'Sugar Street (novel)', 'Dragon Seed (novel)',
    'Clérambault (novel)', 'The Angel Was Silent', 'August 1914 (novel)',
    'The Roots of Heaven (novel)', 'A Bell for Adano (novel)',
    'Allah Is Not Obliged (novel)', 'A Time to Love and a Time to Die (novel)',
    'Bombs Away: The Story of a Bomber Team', 'The Road to Flanders',
    'And Where Were You, Adam?', 'Men at War (anthology)',
    'Wooden Crosses (novel)', 'The Wall (novel)', 'Civilization (novel)',
    'Mr. Britling Sees It Through', 'The Return of the Soldier',
]


def main():
    assert not (research.OUT / 'apply-receipt.json').exists(), 'Preserve applied research.'
    candidates, unresolved = [], []
    for offset in range(0, len(TITLES), 12):
        data, proof = research.capture('en.wikipedia.org', {
            'action': 'query', 'titles': '|'.join(TITLES[offset:offset + 12]),
            'redirects': 1, 'prop': 'pageprops|extracts|revisions',
            'ppprop': 'wikibase_item', 'exintro': 1, 'explaintext': 1,
            'exlimit': 20, 'rvprop': 'ids|timestamp',
        })
        for page in data['query']['pages']:
            qid = page.get('pageprops', {}).get('wikibase_item')
            if not qid or page.get('missing'):
                unresolved.append(page['title'])
                continue
            candidates.append({'title': page['title'], 'qid': qid,
                               'extract': page.get('extract', ''),
                               'revision': page['revisions'][0]['revid'], 'source': proof})
        print('Captured', min(offset + 12, len(TITLES)), 'of', len(TITLES), flush=True)
    # Resolve original-language titles where English names point to adaptations
    # or disambiguation pages. Keep those rejected identities in the audit.
    for language, titles in [
        ('fr', ['Civilisation (roman)', 'Vie des martyrs', 'Les Croix de bois',
                'Hosties noires', "Allah n'est pas obligé", 'La Route des Flandres',
                "Le Dernier de l'Empire", 'Ô pays, mon beau peuple !',
                'En attendant le vote des bêtes sauvages']),
        ('de', ['Wo warst du, Adam?', 'Der Engel schwieg']),
    ]:
        data, proof = research.capture(language + '.wikipedia.org', {
            'action': 'query', 'titles': '|'.join(titles), 'redirects': 1,
            'prop': 'pageprops|extracts|revisions', 'ppprop': 'wikibase_item',
            'exintro': 1, 'explaintext': 1, 'exlimit': 20, 'rvprop': 'ids|timestamp',
        })
        for page in data['query']['pages']:
            qid = page.get('pageprops', {}).get('wikibase_item')
            if qid and not page.get('missing'):
                candidates.append({'title': page['title'], 'qid': qid,
                    'extract': page.get('extract', ''), 'language': language,
                    'revision': page['revisions'][0]['revid'], 'source': proof})
            else:
                unresolved.append(language + ':' + page['title'])
    candidates = list({item['qid']: item for item in candidates}.values())
    with psycopg.connect('postgres://localhost/artline', options='-c default_transaction_read_only=on') as db:
        existing = {q: {'id': i, 'title': t, 'year': y} for q, i, t, y in db.execute(
            'SELECT source_id,id,title,start_year FROM book_records WHERE source_id=ANY(%s)',
            ([item['qid'] for item in candidates],))}
    wanted = sorted(item['qid'] for item in candidates if item['qid'] not in existing)
    entities = {}
    for offset in range(0, len(wanted), 40):
        data, proof = research.capture('www.wikidata.org', {
            'action': 'wbgetentities', 'ids': '|'.join(wanted[offset:offset + 40]),
            'props': 'info|labels|descriptions|claims', 'languages': 'en|mul',
        })
        entities.update({qid: {'entity': entity, 'source': proof} for qid, entity in data['entities'].items()})
    for item in candidates:
        item['existing'] = existing.get(item['qid'])
        item['wikidata'] = entities.get(item['qid'])
    research.OUT.mkdir(parents=True, exist_ok=True)
    (research.OUT / 'candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + '\n')
    (research.OUT / 'unresolved-titles.json').write_text(json.dumps(unresolved, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'candidates': len(candidates), 'missing': [(i['title'], i['qid']) for i in candidates if not i['existing']], 'unresolved': unresolved}, indent=2))


if __name__ == '__main__':
    main()
