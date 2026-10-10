#!/usr/bin/env python3
"""Reconcile documented deposits; preserve ownership and display distinctions."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('major', Path(__file__).with_name('research-artwork-location-major-museums-20261005d.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p = m.r, m.p


def deposit_check(o):
    parts = [r.norm(v) for v in (o.get('Lieu_de_depot') or '').split(';') if v.strip()]
    if len(parts) < 3 or parts[-3] not in {'depot', 'depot reglementaire'}:
        return 'no_explicit_final_deposit_destination'
    if re.search(r'\?|\b(pret|prets|pretee?|restitu\w*|recuperation|manquant|disparu|vole|termine|retour\w*)\b', ' '.join(parts)):
        return 'uncertain_or_ended_deposit'
    if o.get('MANQUANT') or o.get('MANQUANT_COM'):
        return 'missing_flag'
    if re.search(r'\b(attribue|copie|atelier|ecole|suiveur|entourage|apres|anonyme)\b|\?', r.norm(o.get('Auteur'))):
        return 'qualified_creator'
    legal = r.norm(o.get('Statut_juridique'))
    if not legal.startswith(("propriete de l'etat", 'propriete de la commune', 'propriete du departement', 'propriete de la region')):
        return 'public_owner_not_established'
    if re.search(r'recuperation|restitution|restitue|pret|privee|particulier|usufruit|\?', legal):
        return 'legal_qualification_requires_review'
    city, name = r.norm(o.get('Ville')), r.norm(o.get('Nom_officiel_musee'))
    location = [r.norm(v) for v in (o.get('Localisation') or '').split(';') if v.strip()]
    if location != [city, name]:
        return 'conservation_place_differs_from_registry'
    if parts[-2:] != [city, name]:
        return 'deposit_recipient_differs_from_conservation_place'
    if o.get('Code_Museofile') == 'M5031' or 'louvre' in name:
        return 'prefer_current_louvre_object_record'
    return None


def main():
    ids = m.remaining()
    originals = {}
    for provider in ['joconde-deposit-review-20261005', 'joconde-alias-20261005b']:
        for c in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
            if c['artwork_id'] in ids and c.get('review_state') == 'review':
                originals[c['artwork_id']] = c
    registry = r.load(r.RUN / 'museofile-current-20261005b.json.gz')
    authorities = {v['Identifiant']: v for v in registry['rows']}
    manual = r.load(r.RUN / 'joconde-deposit-specification-20261005d.json')
    claims, holds = [], []
    for old in originals.values():
        o = old['object_evidence']
        reason = deposit_check(o)
        authority = authorities.get(o.get('Code_Museofile'))
        if not reason and (not authority or (r.norm(authority['Nom_officiel']), r.norm(authority['Ville'])) != (r.norm(o['Nom_officiel_musee']), r.norm(o['Ville']))):
            reason = 'current_museum_authority_conflict'
        if reason:
            holds.append({'artwork_id': old['artwork_id'], 'reason': reason})
            continue
        c = copy.deepcopy(old)
        c['review_state'] = 'accepted'
        c['source_class'] = 'primary_national_collection_catalogue_documented_deposit'
        c['identity_basis'] = old['identity_basis'].split('; collection/deposit')[0] + '; explicit DEPO receiving museum, LOCA conservation place and current Museofile museum/city agree exactly'
        c['limitation'] = 'Documented museum holding through deposit. Legal owner is preserved in source evidence and may differ from the receiving museum. No ownership transfer, present physical verification or current-display assertion. Artwork publication and date review are unchanged.'
        c['object_evidence'] = {'current_object_record': o, 'prior_review_candidate': old,
            'deposit_reconciliation': {'manual': manual, 'manual_pages': [23, 33],
                'basis': 'The Ministry specifies DEPO as deposit, municipality and receiving institution; LOCA for an object received on deposit names that receiving institution. STAT records the owner separately.',
                'source_deposit': o['Lieu_de_depot'], 'source_conservation_place': o['Localisation'],
                'source_legal_owner': o['Statut_juridique'], 'current_museum_authority': authority,
                'museum_authority_receipt': registry['receipt']}}
        claims.append(c)
    p.output('joconde-deposit-custody-20261005d', claims, holds)
    print('Museums', collections.Counter(c['institution']['name'] for c in claims), flush=True)


if __name__ == '__main__':
    main()
