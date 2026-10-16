#!/usr/bin/env python3
"""Resolve a selected Getty accession through the museum's public UI search API.

Search results may be fuzzy even for accession-looking text; require an exact
accession match before returning a linked-data object URL. No bulk image fetch.
"""
import json
import exhibitions_common as c

def resolve(accession):
    raw, receipt = c.capture('https://www.getty.edu/art/collection/api/search', params={'q': '"' + accession + '"', 'size': 5})
    data = json.loads(raw)
    matches = [row for row in data.get('data', []) if row.get('accession_number') == accession]
    if len(matches) != 1:
        raise ValueError(f'Expected one exact accession match for {accession}; got {len(matches)}')
    row = matches[0]
    if not row['id'].startswith('object/'):
        raise ValueError('Search match is not an artwork object')
    return {'accession': accession, 'objectURL': 'https://data.getty.edu/museum/collection/' + row['id'], 'searchRecord': row, 'receipt': receipt}
