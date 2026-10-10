#!/usr/bin/env python3
"""Resolve the Venetsianov candidate through the current official catalogue."""
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    index = p.Index()
    aid = '4cbe01ca-b930-5983-82dc-db5af4b0336f'
    row = index.by_id[aid]
    lead = r.load(r.RUN / 'wikiart-leads' / (aid + '.json'))
    assert lead['title'] == row['artwork']['title'] == 'Reapers'
    assert lead['outcome'] == 'museum_lead_requires_corroboration'
    url = 'https://rusmuseumvrm.ru/data/collections/painting/18_19/zh_5166/index.php'
    raw, receipt = r.capture(url, tag='curated-supplement-20261005', timeout=45)
    assert receipt['status'] == 200
    soup = BeautifulSoup(raw, 'html.parser')
    for node in soup.select('script,style,nav,footer'):
        node.decompose()
    text = ' '.join(soup.get_text(' ', strip=True).split())
    tokens = ['Венецианов', 'Жнецы', 'Конец 1820-х', '66,7 x 52', 'Ж-5166', '1909']
    assert all(v in text for v in tokens)
    basis = 'Reapers/Жнецы title translation, Alexey Venetsianov, late 1820s and exact 66.7 x 52 cm identify the object. Museum accession Ж-5166 documents receipt in 1909. Existing source dates 1825–1829 remain unchanged.'
    claim = p.claim(row, 'russian-museum-object', 'Ж-5166', index.institution('state-russian-museum'), receipt, url, {'reviewed_tokens': tokens, 'secondary_identity_lead': lead, 'manual_identity_review': basis}, basis)
    claim['limitation'] += ' Museum explicitly warns that actual gallery placement can differ from the virtual tour; no public-display claim is made.'
    p.output('curated-supplement-20261005', [claim], [])


if __name__ == '__main__':
    main()
