#!/usr/bin/env python3
"""Scoped Museofile names and Orsay's documented predecessor collections."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('dc', Path(__file__).with_name('refine-artwork-location-deposit-custody-20261005d.py'))
dc = importlib.util.module_from_spec(s)
s.loader.exec_module(dc)
r, p, m = dc.r, dc.p, dc.m

# Scoped to the exact official Museofile identifier AND named municipality.
# Palace museum abbreviations cannot match administrative buildings in a city.
ALIASES = {
 'M5013': ('Fontainebleau', ['musée national du château', 'musée du château']),
 'M5009': ('Compiègne', ['musée national du château', 'musée du château']),
 'M5077': ('Versailles', ['musée du château']),
 'M0607': ('Montauban', ['musée Ingres']),
 'M0638': ('Valenciennes', ['musée des beaux-arts', 'musée des beaux-arts de Valenciennes']),
 'M0941': ('Saint-Tropez', ["musée de l'Annonciade"]),
 'M0798': ('Beauvais', ["musée départemental de l'Oise", "musée de l'Oise"]),
 'M0028': ('Colmar', ["musée d'Unterlinden"]),
 'M0744': ('Nantes', ['musées du château des Ducs de Bretagne']),
 'M0655': ('Bayeux', ['musée Baron Gérard']),
}


def words(value):
    return re.sub(r'[^\w]+', ' ', r.norm(value)).strip()


def normalized_candidate(o, authority):
    city, name = authority['Ville'], authority['Nom_officiel']
    if words(o.get('Ville')) != words(city): return None
    names = {words(name)}
    alias = ALIASES.get(authority['Identifiant'])
    if alias:
        assert words(alias[0]) == words(city)
        names.update(words(v) for v in alias[1])
    if words(o.get('Nom_officiel_musee')) not in names: return None
    location = [v.strip() for v in (o.get('Localisation') or '').split(';') if v.strip()]
    if len(location) != 2 or words(location[0]) != words(city) or words(location[1]) not in names:
        return None
    parts = [v.strip() for v in (o.get('Lieu_de_depot') or '').split(';') if v.strip()]
    if len(parts) < 3 or words(parts[-2]) != words(city) or words(parts[-1]) not in names:
        return None
    legal_parts = [v.strip() for v in (o.get('Statut_juridique') or '').replace('’', "'").split(';')]
    owners = [v for v in legal_parts if r.norm(v) in {"propriete de l'etat", 'propriete de la commune', 'propriete du departement', 'propriete de la region'}]
    if len(owners) != 1: return None
    return {**o, 'Nom_officiel_musee': name, 'Ville': city,
            'Localisation': city + ';' + name,
            'Lieu_de_depot': ';'.join(parts[:-2] + [city, name]),
            'Statut_juridique': ';'.join(owners + [v for v in legal_parts if v not in owners])}


def orsay_predecessor(o, authority):
    if o.get('Code_Museofile') != 'M5060' or authority['Identifiant'] != 'M5060': return False
    if r.norm(o.get('Nom_officiel_musee')) != "musee d'orsay" or r.norm(o.get('Ville')) != 'paris': return False
    if [r.norm(v.strip()) for v in (o.get('Localisation') or '').split(';')] != ['paris', "musee d'orsay"]: return False
    parts = [r.norm(v.strip()) for v in (o.get('Lieu_de_depot') or '').split(';')]
    if parts != ['attribution', 'musee du louvre departement des peintures']: return False
    if o.get('MANQUANT') or o.get('MANQUANT_COM'): return False
    if re.search(r'\b(attribue|copie|atelier|ecole|suiveur|entourage|apres|anonyme)\b|\?', r.norm(o.get('Auteur'))): return False
    legal = r.norm(o.get('Statut_juridique'))
    if not legal.startswith("propriete de l'etat") or re.search(r'recuperation|restitution|restitue|depot|pret|privee|particulier|usufruit|\?', legal): return False
    assert 'collections du musée du Louvre' in authority['Histoire']
    return True


def main():
    done = {c['artwork_id'] for c in r.load(r.RUN / 'primary-plans/joconde-deposit-custody-20261005d.json.gz')['claims']}
    remaining = m.remaining() - done
    originals = {}
    for provider in ['joconde-deposit-review-20261005', 'joconde-alias-20261005b']:
        for c in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
            if c['artwork_id'] in remaining and c.get('review_state') == 'review': originals[c['artwork_id']] = c
    registry = r.load(r.RUN / 'museofile-current-20261005b.json.gz')
    authorities = {v['Identifiant']: v for v in registry['rows']}
    claims, holds = [], []
    for old in originals.values():
        o = old['object_evidence']
        authority = authorities.get(o.get('Code_Museofile'))
        if not authority: continue
        normal = normalized_candidate(o, authority)
        reason = dc.deposit_check(normal) if normal else 'recipient_and_authority_unresolved'
        mode = 'exact_registered_museum_and_city_with_scoped_name_alias'
        if reason and orsay_predecessor(o, authority):
            reason, mode = None, 'orsay_conservation_place_and_registered_predecessor_collection'
        if reason:
            holds.append({'artwork_id': old['artwork_id'], 'reason': reason})
            continue
        c = copy.deepcopy(old)
        c['review_state'] = 'accepted'
        c['source_class'] = 'primary_national_catalogue_and_museum_registry'
        c['identity_basis'] = old['identity_basis'].split('; collection/deposit')[0] + '; ' + mode
        c['limitation'] = 'Documented museum collection association with source conservation place and institutional identity reconciled. Legal ownership and any original attribution/deposit wording remain preserved. No public-display or present physical verification claim; no artwork publication or metadata change.'
        extra = []
        if o.get('Code_Museofile') in {'M0607', 'M0638'}:
            extra.append(r.load(r.RUN / ('french-identity-' + o['Code_Museofile'] + '-20261005d.json')))
        c['object_evidence'] = {'current_object_record': o, 'prior_review_candidate': old,
            'museum_identity_reconciliation': {'basis': mode, 'current_museum_authority': authority,
                'museum_authority_receipt': registry['receipt'], 'additional_primary_authorities': extra,
                'scoped_aliases': ALIASES.get(o.get('Code_Museofile')),
                'field_specification': r.load(r.RUN / 'joconde-deposit-specification-20261005d.json'),
                'interpretation': 'Orsay LOCA identifies its current collection, while DEPO attribution records its Louvre predecessor, expressly described in the current registry history.' if mode.startswith('orsay') else 'Same Museofile identifier and municipality; full and abbreviated names identify the same museum. Original source strings are retained.'}}
        claims.append(c)
    p.output('french-museum-identities-20261005d', claims, holds)
    print('Modes', collections.Counter(c['object_evidence']['museum_identity_reconciliation']['basis'] for c in claims))
    print('Museums', collections.Counter(c['institution']['name'] for c in claims), flush=True)


if __name__ == '__main__': main()
