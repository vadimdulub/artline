"""Pure identifier and source-date checks; no real or fixture database access."""
import importlib.util
from pathlib import Path
import unittest

s = importlib.util.spec_from_file_location('ng', Path(__file__).with_name('research-artwork-location-national-gallery-20261005d.py'))
ng = importlib.util.module_from_spec(s)
s.loader.exec_module(ng)
m = ng.m
s = importlib.util.spec_from_file_location('dc', Path(__file__).with_name('refine-artwork-location-deposit-custody-20261005d.py'))
dc = importlib.util.module_from_spec(s)
s.loader.exec_module(dc)
def extra(filename):
    spec = importlib.util.spec_from_file_location(filename, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
loans = extra('refine-artwork-location-ng-loans-20261005d.py')
names = extra('refine-artwork-location-french-museum-names-20261005d.py')
date_review = extra('refine-artwork-location-date-review-holdings-20261005d.py')
prado_rijks = extra('refine-artwork-location-prado-rijks-20261005d.py')

class MajorMuseumChecks(unittest.TestCase):
    def test_prado_inventory_padding_keeps_series(self):
        self.assertEqual(m.inventory('P001204'), m.inventory('P1204'))
        self.assertNotEqual(m.inventory('P001204'), m.inventory('G001204'))
        self.assertNotEqual(m.inventory('P001204A'), m.inventory('P001204'))

    def test_spanish_circa_and_full_range_keep_uncertainty(self):
        self.assertTrue(m.dn.equivalent('c. 1635', m.prado_date('Hacia 1635.')))
        self.assertTrue(m.dn.equivalent('1635–1638', m.prado_date('Entre 1635 y 1638')))
        self.assertFalse(m.dn.equivalent('1635', m.prado_date('Hacia 1635')))
        self.assertFalse(m.dn.equivalent('1635', m.prado_date('Después de 1635')))

    def test_empty_creator_label_cannot_match_an_empty_source_creator(self):
        self.assertEqual(m.local_names({'artists': [], 'supplied': [['', '', '']], 'artwork': {'unlinked_creator_label': None}}), set())

    def test_title_normalization_preserves_words_numbers_and_version(self):
        self.assertEqual(m.key('Adolphe Moreau.'), m.key('ADOLPHE MOREAU'))
        self.assertNotEqual(m.key('Study for a Portrait'), m.key('Portrait'))
        self.assertNotEqual(m.key('Composition IV'), m.key('Composition VI'))

    def test_ng_abbreviated_range_requires_matching_explicit_endpoints(self):
        self.assertTrue(ng.date_matches('1520–1523', {'value':'1520-3','from':'1520','to':'1523'}))
        self.assertFalse(ng.date_matches('1520–1524', {'value':'1520-3','from':'1520','to':'1523'}))
        self.assertFalse(ng.date_matches('1520–1523', {'value':'after 1520','from':'1520','to':'1523'}))

    def test_ng_approximate_date_and_post_cutoff_stay_review(self):
        self.assertFalse(ng.date_matches('1830', {'value':'about 1830','from':'1830','to':'1830'}))
        self.assertTrue(ng.date_matches('c. 1830', {'value':'about 1830','from':'1830','to':'1830'}))
        self.assertFalse(ng.date_matches('1980', {'value':'1980','from':'1980','to':'1980'}))

    def test_documented_deposit_needs_same_city_and_receiving_museum(self):
        o = dict(Lieu_de_depot='dépôt;Rouen;musée des beaux-arts', Localisation='Rouen ; musée des beaux-arts', Ville='Rouen', Nom_officiel_musee='musée des beaux-arts', Statut_juridique="propriété de l'Etat;achat;musée du Louvre", Auteur='MONET Claude')
        self.assertIsNone(dc.deposit_check(o))
        self.assertIsNotNone(dc.deposit_check(dict(o, Lieu_de_depot='dépôt;Bordeaux;musée des beaux-arts')))
        self.assertIsNotNone(dc.deposit_check(dict(o, Localisation='Paris ; musée du Louvre')))

    def test_deposit_does_not_override_missing_qualified_or_uncertain_ownership(self):
        o = dict(Lieu_de_depot='dépôt;Rouen;musée des beaux-arts', Localisation='Rouen ; musée des beaux-arts', Ville='Rouen', Nom_officiel_musee='musée des beaux-arts', Statut_juridique="propriété de l'Etat;achat;musée du Louvre", Auteur='MONET Claude')
        for changes in [dict(MANQUANT='volé'), dict(Auteur='MONET Claude (attribué)'), dict(Statut_juridique='propriété privée'), dict(Statut_juridique="propriété de l'Etat;réserve d'usufruit"), dict(Lieu_de_depot='dépôt (?);Rouen;musée des beaux-arts')]:
            with self.subTest(changes=changes): self.assertIsNotNone(dc.deposit_check(dict(o, **changes)))

    def test_loan_custody_requires_current_named_recipient_and_effective_interval(self):
        import copy
        o = {'legal': {'status': 'Long Loan', 'credit': 'On loan from a private collection'}, '@datatype': {'virtual': False}, 'location': {'current': {'@link': {'date': [{'from': '2026-08-01T00:00'}], 'custodian': {'@admin': {'uid': '0P5X-0001-0000-0000'}, 'summary': {'title': 'The National Gallery (London)'}}}}}}
        self.assertIsNotNone(loans.custody_proof(o, '2026-10-05T00:00:00Z'))
        for changes in [{'from': '2027-01-01'}, {'from': '2025-01-01', 'to': '2026-09-01'}]:
            bad = copy.deepcopy(o); bad['location']['current']['@link']['date'] = [changes]
            self.assertIsNone(loans.custody_proof(bad, '2026-10-05T00:00:00Z'))
        bad = copy.deepcopy(o); bad['location']['current']['@link']['custodian']['@admin']['uid'] = 'other-museum'
        self.assertIsNone(loans.custody_proof(bad, '2026-10-05T00:00:00Z'))

    def test_palace_alias_is_scoped_and_cannot_resolve_a_government_office(self):
        authority = {'Identifiant': 'M5077', 'Ville': 'Versailles', 'Nom_officiel': 'musée national des châteaux de Versailles et de Trianon'}
        o = dict(Code_Museofile='M5077', Ville='Versailles', Nom_officiel_musee=authority['Nom_officiel'], Localisation='Versailles;' + authority['Nom_officiel'], Lieu_de_depot='dépôt;Versailles;musée du Château', Statut_juridique="musées nationaux;propriété de l'Etat")
        self.assertIsNotNone(names.normalized_candidate(o, authority))
        self.assertIsNone(names.normalized_candidate(dict(o, Lieu_de_depot='dépôt;Versailles;Questure du Sénat'), authority))
        self.assertIsNone(names.normalized_candidate(dict(o, Lieu_de_depot='dépôt;Compiègne;musée du Château'), authority))

    def test_date_review_holding_needs_exact_inventory_and_preserved_review_status(self):
        row = {'artwork': {'status': 'review', 'accession_number': '12.34', 'date_display': 'Creation date under review'}}
        c = {'scheme': 'met-object', 'external_id': '123', 'review_state': 'review', 'checked_at': '2026-10-05T00:00:00Z', 'source_receipt': {'status': 200}, 'object_evidence': {'qualifications': ['date_wording_differs'], 'current_museum_record': {'accessionNumber': '12.34', 'objectDate': 'after 1800'}}}
        self.assertIsNotNone(date_review.proof(row, c))
        self.assertIsNone(date_review.proof({'artwork': dict(row['artwork'], accession_number='12.35')}, c))
        self.assertIsNone(date_review.proof({'artwork': dict(row['artwork'], status='published')}, c))
        c['object_evidence']['qualifications'].append('qualified_creator')
        self.assertIsNone(date_review.proof(row, c))

    def test_rijks_incoming_loan_requires_explicit_main_building_location(self):
        e = {'qualifications': ['loan_or_custody_qualification'], 'museum_provider_id': 'https://id.rijksmuseum.nl/2109266', 'current_location': {'identified_by': [{'type': 'Name', 'part': [{'type': 'Name', 'content': 'Main building'}]}, {'type': 'Identifier', 'content': 'HG-2.25'}]}, 'referred_to_by': [{'content': 'On loan from the City of Amsterdam', 'classified_as': [{'id': 'http://vocab.getty.edu/aat/300026687'}]}]}
        self.assertIsNotNone(prado_rijks.rijks_loan_proof(e))
        self.assertIsNone(prado_rijks.rijks_loan_proof(dict(e, current_location=None)))
        self.assertIsNone(prado_rijks.rijks_loan_proof(dict(e, museum_provider_id='other-museum')))

    def test_orsay_predecessor_does_not_override_a_different_deposit_destination(self):
        authority = {'Identifiant': 'M5060', 'Histoire': 'Regroupement des collections du musée du Louvre'}
        o = dict(Code_Museofile='M5060', Nom_officiel_musee="musée d'Orsay", Ville='Paris', Localisation="Paris ; musée d'Orsay", Lieu_de_depot='Attribution;musée du Louvre département des Peintures', Auteur='MONET Claude', Statut_juridique="propriété de l'Etat;achat;musée du Louvre")
        self.assertTrue(names.orsay_predecessor(o, authority))
        self.assertFalse(names.orsay_predecessor(dict(o, Lieu_de_depot='dépôt;Paris;musée du Louvre'), authority))
        self.assertFalse(names.orsay_predecessor(dict(o, MANQUANT='disparu'), authority))

if __name__ == '__main__': unittest.main()
