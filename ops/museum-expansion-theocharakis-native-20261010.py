"""Reconcile selected SearchCulture records with their observed native object pages."""
import collections
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

spec = importlib.util.spec_from_file_location('t', Path(__file__).with_name('museum-expansion-theocharakis-source-20261010.py'))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
m, RUN, q = t.m, t.RUN, t.q


def native_fields(soup):
    main = soup.find('main')
    assert main is not None
    fields = {}
    for tr in main.select('table tr'):
        th, td = tr.find('th'), tr.find('td')
        assert th is not None and td is not None
        key = q.clean(th.get_text(' ', strip=True)).rstrip(':')
        assert key not in fields
        fields[key] = q.clean(td.get_text(' ', strip=True))
    creators = [q.clean(h.get_text(' ', strip=True)) for h in main.find_all('h3')]
    return main, fields, creators


def main():
    source = m.load(RUN / 'selected-source-records-001.json.gz')['rows']
    out = []
    for i, row in enumerate(source, 1):
        sid = row['source_id'].rsplit('-', 1)[1]
        soup, receipt = q.q.capture('native-' + sid + '-001', row['native_url'])
        main, fields, creators = native_fields(soup)
        assert fields.get('τίτλος') and fields.get('τεχνική') and fields.get('έτος')
        assets = sorted({urljoin(row['native_url'], a['href']) for a in main.select('a[href]')
                         if '/wp-content/uploads/' in a['href'] and not a['href'].endswith('.svg')})
        assert len(assets) == 1, (sid, assets)
        comparisons = {'title': fields['τίτλος'] in row['fields'].get('Τίτλος', []),
                       'medium': fields['τεχνική'] in row['fields'].get('Υλικό', []),
                       'date': fields['έτος'] in row['fields'].get('Ημερομηνία δημιουργίας', []),
                       'dimensions': fields.get('διαστάσεις') in row['fields'].get('Έκταση (μέγεθος ή διάρκεια)', []),
                       'creator': all(v in row['fields'].get('Δημιουργός', []) for v in creators)}
        out.append(dict(source_id=row['source_id'], number=row['number'], role=row['role'],
                        native_url=row['native_url'], fields=fields, creators=creators,
                        full_image_url=assets[0], receipt=receipt, source_comparison=comparisons,
                        text=q.clean(main.get_text(' ', strip=True))))
        if i % 20 == 0 or i == len(source):
            print(json.dumps(dict(native_captured=i, total=len(source), conflicts=sum(not all(v['source_comparison'].values()) for v in out))), flush=True)
        time.sleep(.08)
    m.save(RUN / 'native-object-records-001.json.gz', dict(at=m.now(), rows=out,
        source_reference=q.s.ref(RUN / 'selected-source-records-001.json.gz'), script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Observed native links only. Full-image URLs recorded but no full images downloaded. Source record IDs and asset filenames are not museum accession numbers. Native artwork dates are separate from creator life dates.'))


if __name__ == '__main__':
    main()
