#!/usr/bin/env python3
"""Retain visually checked historical museum-book evidence without current claims."""
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
# All entries checked on printed page 244, PDF page 248. Numbers below
# refer to the illustrated artwork pages printed in the museum book.
ENTRIES = [
    ('Q28845534', 'Vardges Sureniants', 'Выход армянских женщин из церкви', '1905', 32),
    ('Q30678575', 'Zakar Zakarian', 'Натюрморт со сливами', '1900', 36),
    ('Q59210030', 'Hovhannes Zardaryan', 'Ранняя весна', '1945', 93),
    ('Q77381476', 'Vahram Gayfejian', 'Сирень', '1917', 59),
    ('Q77461457', 'Sedrak Arakelyan', 'Сушат пшеницу', '1920', 60),
    ('Q77550494', 'Stepan Aghajanian', 'Автопортрет', '1926', 40),
    ('Q77862609', 'Hakob Nagashi Hovnatanyan', 'Портрет Н. Теумян', 'Начало 1840-х гг.', 25),
    ('Q77862649', 'Mariam Aslamazian', 'Возвращение героя', '1943', 94),
    ('Q77862761', 'Hovsep Karalian', 'В город', '1958', 67),
    ('Q78217211', 'Stepanos Nersisyan', 'Пикник на берегу Куры', '1850–1860-е гг.', 26),
    ('Q77301617', 'Yeghishe Tadevosyan', 'Комитас', '1935', 45),
]


def main():
    index = p.Index()
    selected = {v['qid']: v for v in r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')['Q2087788']}
    receipt = r.load(r.RUN / 'armenia-book-1982-receipt-20261005c.json')
    assert receipt['status'] == 200 and receipt['bytes'] == 19044004
    with r.connect('local') as db:
        museums = [v['i'] for v in db.execute("SELECT to_jsonb(i) i FROM institutions i WHERE wikidata_id='Q2087788'")]
    assert len(museums) == 1
    claims = []
    for qid, artist, source_title, source_date, page in ENTRIES:
        selection = selected[qid]
        row = index.by_id[selection['artwork_id']]
        assert any(v['name'] == artist for v in row['artists'])
        assert any(v['scheme'] == 'wikidata' and v['external_id'] == qid for v in row['identifiers'])
        evidence = {'bibliography': {'author': 'Р. Г. Дрампян / Ruben Drampian',
            'title': 'Государственная картинная галерея Армении', 'publisher': 'Искусство', 'publication_place': 'Москва',
            'year': 1982, 'printed_index_page': 244, 'pdf_index_page': 248, 'illustrated_work_printed_page': page,
            'library_catalogue_url': 'https://arar.sci.am/dlibra/publication/343744/edition/316592',
            'source_type': 'Museum collection history by its former director; historical evidence'},
            'source_title': source_title, 'source_creation_date': source_date, 'local_title': row['artwork']['title'],
            'local_creation_date': row['artwork'].get('date_display'), 'selected_secondary_object': selection,
            'visual_verification': 'PDF page 248 rendered and read; printed artwork page references transcribed. PDF page 49 also inspected for Komitas.',
            'qualifications': ['historical_publication_not_current_inventory', 'translated_title_identity_requires_editorial_review']}
        if p.datekey(source_date) != p.datekey(row['artwork'].get('date_display')):
            evidence['qualifications'].append('source_date_wording_or_year_differs')
        c = p.claim(row, 'armenia-book-1982', qid, museums[0], receipt, receipt['url'] + '#page=248', evidence,
            'Manual comparison of named artist, translated title, historical museum-book illustration index and exact existing Wikidata selection; retained for review')
        c['review_state'] = 'review'
        c['limitation'] = 'Historical museum-book evidence from 1982, retained in review. Current inventory and translated-title identity still need reconciliation; source date conflicts remain visible. No accepted current holding, location, display or artwork metadata change.'
        claims.append(c)
    p.output('armenia-book-20261005c', claims, [])


if __name__ == '__main__':
    main()
