#!/usr/bin/env python3
"""Reconcile a documented title alias against an exact current museum record."""
import copy
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    aid = '1ae187a0-02be-5948-a0c2-6b70651f0b07'
    old = next(c for c in r.load(r.RUN / 'primary-plans/russian-followup-20261005.json.gz')['claims'] if c['artwork_id'] == aid)
    assert old['review_state'] == 'review' and old['external_id'] == '11026'
    url = 'https://www.artothek.de/en/image-details/17167.html'
    raw, receipt = r.capture(url, tag='russian-title-concordance-20261005c', timeout=35)
    assert receipt['status'] == 200
    text = ' '.join(BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True).split())
    tokens = ['The Red Square, Moscow (Moscow I.). 1916', 'Kandinsky, Wassily, 1866-1944', '51,5 x 49,5 cm', 'Tretyakov Gallery']
    assert all(token in text for token in tokens)
    primary, primary_receipt = r.capture(old['source_url'], tag='russian-title-primary-recheck-20261005c', timeout=40)
    primary_text = ' '.join(BeautifulSoup(primary, 'html.parser').get_text(' ', strip=True).split())
    assert primary_receipt['status'] == 200
    assert all(token in primary_text for token in ['Кандинский Василий', 'Москва. Красная площадь', '1916', '51,5 x 49,5', 'Ж-1271'])
    c = copy.deepcopy(old)
    c['review_state'] = 'accepted'
    c['source_receipt'] = primary_receipt
    c['checked_at'] = primary_receipt['retrieved_at']
    c['object_evidence']['title_alias_reconciliation'] = {'secondary_source_receipt': receipt, 'source_tokens_checked': tokens, 'primary_title': 'Москва. Красная площадь', 'primary_inventory': 'Ж-1271', 'existing_title': 'Moscow I', 'manual_decision': 'ARTOTHEK explicitly records both English titles together with Kandinsky, 1916, Tretyakov and the same 51.5 by 49.5 cm dimensions. The current museum record independently confirms artist, date, measurements and inventory. This resolves title identity; dimensions in the old source are in the opposite axis order.'}
    c['identity_basis'] = 'Manually reconciled documented Moscow I / Moscow, Red Square title alias; exact named artist, 1916 date, 51.5 x 49.5 cm measurements and current Tretyakov inventory Ж-1271.'
    c['limitation'] = 'Documented Tretyakov collection holding only. Existing title, dates, creator, images and publication state retained; no present physical-location or display assertion.'
    p.output('russian-title-20261005c', [c], [])


if __name__ == '__main__':
    main()
