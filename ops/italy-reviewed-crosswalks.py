#!/usr/bin/env python3
"""Resolve reviewed authority spelling differences without editing catalogue data."""
import argparse
import copy
import importlib.util
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crosswalks', ROOT / 'ops/italy-image-crosswalks.py')
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
c, w = x.c, x.w


def resolve(label):
    accepted, held = [], []
    for path in sorted(x.RUN.glob('*-matches.json')):
        discovery = c.load(path.with_name(path.name.replace('-matches.json', '.json')))
        for entry in c.load(path)['held']:
            record = copy.deepcopy(entry.get('candidate'))
            if not record:
                continue
            entity = discovery['entities'][record['qid']]
            basis = record['crosswalk_basis']
            resolution = None
            # Exact native catalogue identifiers independently establish the
            # physical object. A source-language title is an image-research
            # alias only; it never changes the artwork's stored title/aliases.
            if entry['reason'] == 'Title and inventory require manual match' and basis['exact_source_references']:
                labels = entity.get('labels', {})
                source_title = next((labels[lang]['value'] for lang in ('it', 'en', 'mul', 'fr', 'de') if lang in labels), None)
                if not source_title:
                    continue
                record['catalogue_alternate_title_before_research'] = record.get('alternate_title')
                record['alternate_title'] = source_title
                resolution = {'method': 'Exact native object URL/identifier in authority source references',
                    'source_references': basis['exact_source_references'],
                    'authority_title_for_image_matching_only': source_title,
                    'catalogue_metadata_write': False}
            # These two reviewed Venice records use an explicit "Cat." prefix
            # in Wikidata. The museum's own catalogue calls them 203 and 915.
            elif entry['reason'] == 'Accession conflict' and record['institution_slug'] == 'gallerie-accademia-venezia' and record['qid'] in ('Q951105', 'Q930137'):
                expected = {'Q951105': '203', 'Q930137': '915'}[record['qid']]
                if record['accession_number'] != expected:
                    continue
                equivalents = [v for v in w.values(entity, 'P217') if isinstance(v, str)
                    and re.fullmatch(r'Cat\.\s*' + re.escape(expected), v)]
                if len(equivalents) != 1:
                    continue
                record['catalogue_accession_before_research'] = record['accession_number']
                record['accession_number'] = equivalents[0]
                resolution = {'method': 'Manually reviewed museum catalogue-number prefix equivalence',
                    'museum_catalogue_number': expected, 'authority_spelling': equivalents[0],
                    'museum_source_url': record['page'], 'reviewed_at': c.core.now(),
                    'source_access': 'Official museum page indexed by web search; live open returned 403',
                    'museum_field': 'Catalogo: ' + expected,
                    'catalogue_metadata_write': False}
            if not resolution:
                continue
            record['crosswalk_resolution'] = resolution
            try:
                w.entity_match(record, entity)
                accepted.append(record)
            except ValueError as error:
                held.append({'artwork_id': record['artwork_id'], 'qid': record['qid'],
                             'reason': str(error), 'resolution_attempt': resolution})
    c.save(c.RUN / (label + '-resolutions.json'), {'reviewed_at': c.core.now(),
           'accepted': accepted, 'held': held, 'scope': 'Image research identity only; metadata and creators remain unchanged'})
    x.select_records(accepted, label)
    print('Reviewed identity resolutions', len(accepted), 'remaining holds', len(held), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--label', required=True)
    a = p.parse_args()
    resolve(a.label)
