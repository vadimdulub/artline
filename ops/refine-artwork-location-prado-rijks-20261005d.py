#!/usr/bin/env python3
"""Selected exact Prado identities and explicitly located Rijksmuseum loans."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-major-museums-20261005d.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p = m.r, m.p


def rijks_loan_proof(e):
    if e.get('qualifications') != ['loan_or_custody_qualification'] or e.get('museum_provider_id') != 'https://id.rijksmuseum.nl/2109266': return None
    location = e.get('current_location') or {}
    labels = [v.get('content') for item in location.get('identified_by', []) for v in item.get('part', []) if v.get('type') == 'Name']
    if 'Main building' not in labels and 'Hoofdgebouw' not in labels: return None
    numbers = [v.get('content', '') for v in location.get('identified_by', []) if v.get('type') == 'Identifier']
    if not any(re.fullmatch(r'HG-[\d.]+', n) for n in numbers): return None
    credits = [v.get('content', '') for v in e.get('referred_to_by', []) if any(t.get('id') == 'http://vocab.getty.edu/aat/300026687' for t in v.get('classified_as', []))]
    if not any(v.startswith('On loan from ') for v in credits): return None
    if re.search(r'returned|deaccession|teruggegeven|afgestoten|restitu', ' '.join(credits), re.I): return None
    return {'current_source_location': location, 'incoming_loan_credits': credits, 'basis': 'Fresh primary record explicitly describes an incoming loan and locates the same exact object in the Rijksmuseum main building. Loan ownership remains with the credited lender. Undated gallery text is not converted into an on-view assertion.'}


def main():
    ids, index = m.remaining(), p.Index()
    claims = []
    for old in r.load(r.RUN / 'primary-plans/prado-dataset-20261005d.json.gz')['claims']:
        e = old['object_evidence']
        if old['artwork_id'] not in ids or e['qualifications'] != ['creation_date_requires_review']: continue
        row, ent = index.by_id[old['artwork_id']], e['wikidata_identity']['entity']
        if row['artwork']['status'] != 'review': continue
        local_qids = {v['external_id'] for v in row['identifiers'] if v['scheme'] == 'wikidata'}
        if e['wikidata_identity']['qid'] not in local_qids or old['external_id'] not in m.h.statements(ent, 'P8905'): continue
        number = e['catalogue_facts_from_2026_dataset']['Número de catálogo']
        if m.inventory(number) not in {m.inventory(v) for v in m.h.statements(ent, 'P217') if isinstance(v, str)}: continue
        c = copy.deepcopy(old)
        c['review_state'] = 'accepted'
        c['duplicate_native_ids'] = [number, m.inventory(number)]
        c['object_evidence']['holding_identity_with_date_review'] = {'local_wikidata_id': e['wikidata_identity']['qid'], 'exact_prado_native_id': c['external_id'], 'exact_inventory': number,
            'original_date_display': row['artwork'].get('date_display'), 'original_creation_year_start': row['artwork'].get('creation_year_start'), 'original_creation_year_end': row['artwork'].get('creation_year_end'),
            'current_source_date': e['catalogue_facts_from_2026_dataset']['Fecha'], 'creation_date_and_eligibility_require_editorial_review': True, 'artwork_publication_remains_review': True}
        c['identity_basis'] += '; exact original Wikidata identity, Prado native ID and inventory; date and eligibility remain in editorial review'
        c['limitation'] += ' Creation-date wording and eligibility are unresolved; all original artwork date fields and review publication state are preserved.'
        claims.append(c)
    for old in r.load(r.RUN / 'primary-plans/rijks-20261005b.json.gz')['claims']:
        if old['artwork_id'] not in ids: continue
        proof = rijks_loan_proof(old['object_evidence'])
        if not proof: continue
        c = copy.deepcopy(old)
        c['review_state'] = 'accepted'
        c['object_evidence']['qualifications'] = []
        c['object_evidence']['incoming_loan_reconciliation'] = proof
        c['identity_basis'] += '; incoming loan and Rijksmuseum main-building location explicitly recorded'
        c['limitation'] = 'Documented Rijksmuseum holding via an incoming loan, with the credited owner retained in evidence. The undated catalogue location is not a fresh dated display confirmation. No artwork publication, creator, date or legal ownership change.'
        claims.append(c)
    p.output('prado-rijks-refined-20261005d', claims, [])
    print(collections.Counter(c['scheme'] for c in claims), flush=True)


if __name__ == '__main__': main()
