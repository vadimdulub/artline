#!/usr/bin/env python3
"""Use visually reviewed official catalogue inventory numbers for image identity."""
import argparse
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crosswalks', ROOT / 'ops/italy-image-crosswalks.py')
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
c, w = x.c, x.w
OUT = c.RUN / 'primary-catalogue-followup'

# Numbers transcribed from rendered official catalogue pages. The second value
# is the corresponding authority spelling; differences are explicit, reviewed
# inventory-label prefixes, never inferred missing numbers.
REVIEWED = {
    '2d050-00089': ('GAM 7543', 'GAM 7543', 5),
    '2d050-00092': ('GAM 5264', '5264', 5),
    '2d050-00111': ('GAM 3804', 'GAM 3804', 5),
    '2d050-00113': ('GAM 7597', 'GAM 7597', 4),
    '2d050-00115': ('GAM 1592', 'GAM 1592', 6),
    '3o210-01265': ('DEF 0545', 'DEF 0545', 4),
    'B0050-00104': ('GRASSI 113', 'GRASSI 113', 3),
    'B0050-00105': ('GRASSI 114', 'GRASSI 114', 3),
    'B0050-00110': ('GRASSI 119', 'GRASSI 119', 4),
    'C0050-00666': ('81LC00185', '81LC00185', 5),
    'C0050-01212': ('58AC00424', '58AC00424', 5),
    'RL480-00031': ('443', 'Inv. 443', 3),
    'RL480-00038': ('5240', '5240', 3),
    'ST070-00053': ('1862', '1862', 5),
    'SWCO1-00033': ('DEF 0033', 'DEF 0033', 3),
    'SWCO1-00035': ('DEF 0035', 'DEF 0035', 3),
}


def select(label):
    extractions = {r['candidate']['source_id']:r for r in c.load(OUT / 'inventory-extraction.json')}
    accepted, held = [], []
    for sid, (source_number, authority_number, page) in REVIEWED.items():
        extraction = extractions[sid]
        source = extraction['receipt']
        if c.core.sha((ROOT/source['path']).read_bytes()) != source['sha256']:
            raise ValueError('Official PDF checksum differs from reviewed source')
        if source_number not in extraction['source_inventories'] or authority_number not in extraction['authority_inventories']:
            raise ValueError('Reviewed inventory transcription differs from captured record')
        source_candidate = extraction['candidate']
        discovery = c.load(x.RUN / (source_candidate['institution_slug']+'.json'))
        matches = c.load(x.RUN / (source_candidate['institution_slug']+'-matches.json'))
        lead = next(r for r in matches['held'] if r.get('qid')==source_candidate['qid']
                    and r['artwork_id']==source_candidate['artwork_id'])
        record = copy.deepcopy(lead['candidate'])
        record['catalogue_accession_before_research'] = record['accession_number']
        record['accession_number'] = authority_number
        record['crosswalk_resolution'] = {'method':'Visually reviewed official SIRBeC PDF inventory',
            'source_id':sid, 'source_inventory':source_number, 'authority_spelling':authority_number,
            'source_pdf':source, 'reviewed_pdf_page':page, 'reviewed_at':c.core.now(),
            'catalogue_metadata_write':False,
            'display_status':'Historic catalogue location fields are not a current on-view claim'}
        try:
            w.entity_match(record, discovery['entities'][record['qid']])
            accepted.append(record)
        except ValueError as error:
            held.append({'artwork_id':record['artwork_id'],'reason':str(error)})
    c.save(OUT/(label+'-review.json'), {'reviewed_at':c.core.now(), 'accepted':accepted, 'held':held})
    x.select_records(accepted,label)
    print('Official PDF inventory matches',len(accepted),'held',len(held),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();select(a.label)
