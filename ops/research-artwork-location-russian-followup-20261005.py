#!/usr/bin/env python3
"""Three manually reconciled Russian painting leads; conflicts remain review."""
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r

JOBS = [
    ('4dbb2c17-e4d3-5160-b603-d656324306f5', 'tretyakov-masterpiece', '8433', 'https://my.tretyakov.ru/app/masterpiece/8433', ['Врубель Михаил', 'Пан', '1899', '124 x 106,3', 'Инв.1461'], 'accepted', 'Pan/Пан, Mikhail Vrubel, 1899 and 124 x 106.3 cm agree exactly; official object inventory 1461 and museum acquisition in 1907 identify the collection object.'),
    ('1ae187a0-02be-5948-a0c2-6b70651f0b07', 'tretyakov-masterpiece', '11026', 'https://my.tretyakov.ru/app/masterpiece/11026', ['Кандинский Василий', 'Москва. Красная площадь', '1916', '51,5 x 49,5', 'Ж-1271'], 'review', 'Kandinsky, 1916 and dimensions agree with Moscow I, with axes reversed. The current museum title is Moscow. Red Square; title variant requires editorial reconciliation before accepting this holding.'),
    ('35dba5d3-4546-516c-9e33-1a937650ca10', 'tretyakov-inventory', '5600', 'https://rusmuseumvrm.ru/data/collections/museums/gtg/vrubel_m._a._demon_sidyaschiy._1890._inv._5600._gtg/index.php', ['Врубель М. А.', 'Демон (сидящий)', '1890', '116,5 х 213,8', 'инв. 5600', 'Государственная Третьяковская галерея'], 'review', 'Seated Demon title, Mikhail Vrubel and 1890 agree, and the Russian Museum portal explicitly credits the Tretyakov Gallery. Current dimensions 116.5 x 213.8 differ from the supplied 115 x 212.5; candidate remains review and source attribution is not treated as public display.'),
]


def main():
    index = p.Index()
    claims, holds = [], []
    for aid, scheme, oid, url, tokens, state, basis in JOBS:
        try:
            lead = r.load(r.RUN / 'wikiart-leads' / (aid + '.json'))
            assert lead['title'] == index.by_id[aid]['artwork']['title'] and lead['outcome'] == 'museum_lead_requires_corroboration'
            raw, receipt = r.capture(url, tag='curated-russian-followup-20261005', timeout=40)
            assert receipt['status'] == 200
            soup = BeautifulSoup(raw, 'html.parser')
            for node in soup.select('script,style,nav,footer'):
                node.decompose()
            text = ' '.join(soup.get_text(' ', strip=True).split())
            assert all(v in text for v in tokens), 'Source identity tokens incomplete'
            c = p.claim(index.by_id[aid], scheme, oid, index.institution('wikimedia-museum-q183334'), receipt, url, {'reviewed_tokens': tokens, 'secondary_identity_lead': lead, 'manual_identity_review': basis}, basis)
            c['review_state'] = state
            c['limitation'] += ' ' + basis
            claims.append(c)
        except Exception as exc:
            holds.append({'artwork_id': aid, 'source_url': url, 'reason': 'source_or_identity_requires_review', 'detail': str(exc)[:400]})
    p.output('russian-followup-20261005', claims, holds)


if __name__ == '__main__':
    main()
