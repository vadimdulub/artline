"""Offline safety checks for selected Walker holdings; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('walker', Path(__file__).with_name('museum-expansion-walker-holdings-20261007.py'))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WalkerSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = w.records()
        cls.record = next(r for r in cls.records if r['facts']['qid'] == 'Q119141543')
        scope = w.m.load(w.RUN / 'initial-scope-001.json.gz')
        initial = w.m.load(Path(scope['backup_path']))
        cls.art = next(r for r in initial['artworks'] if r['id'] == cls.record['facts']['artwork_id'])
        cls.identity = next(r for r in w.m.load(w.RUN / 'identity-comparison-002.json.gz')['selected'] if r['artwork_id'] == cls.art['id'])

    def setUp(self):
        self.entity = copy.deepcopy(self.record['source']['entity'])
        self.artwork = copy.deepcopy(self.art)
        self.identity_row = copy.deepcopy(self.identity)

    def check(self):
        return w.facts(self.entity, self.artwork, self.identity_row)

    def test_selected_distinct_identities(self):
        self.assertEqual(185, len(self.records))
        self.assertEqual(185, len({r['facts']['inventory'] for r in self.records}))
        self.assertEqual(self.record['facts'], self.check())

    def test_foreign_collection_rejected(self):
        self.entity['claims']['P195'][0]['mainsnak']['datavalue']['value']['id'] = 'Q2087788'
        with self.assertRaises(AssertionError): self.check()

    def test_expired_collection_rejected(self):
        self.entity['claims']['P195'][0].setdefault('qualifiers', {})['P582'] = []
        with self.assertRaises(AssertionError): self.check()

    def test_preferred_claim_does_not_hide_conflict(self):
        claim = copy.deepcopy(self.entity['claims']['P195'][0])
        claim['rank'] = 'preferred'
        self.entity['claims']['P195'].append(claim)
        with self.assertRaises(AssertionError): self.check()

    def test_qualified_creator_rejected(self):
        self.entity['claims']['P170'][0]['qualifiers'] = {'P1480': []}
        with self.assertRaises(AssertionError): self.check()

    def test_inventory_collection_must_match(self):
        self.entity['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id'] = 'Q1'
        with self.assertRaises(AssertionError): self.check()

    def test_missing_inventory_not_invented(self):
        self.artwork['accession_number'] = None
        with self.assertRaises(AssertionError): self.check()

    def test_reference_must_name_same_artuk_object(self):
        self.entity['claims']['P195'][0]['references'] = []
        with self.assertRaises(AssertionError): self.check()

    def test_unknown_creator_kept_for_reconciliation(self):
        self.identity_row['creator_match'] = False
        with self.assertRaises(AssertionError): self.check()

    def test_duplicate_version_not_selected(self):
        self.identity_row['same_creator_title_collisions'] = [{'id': 'other'}]
        with self.assertRaises(AssertionError): self.check()

    def test_date_discrepancy_rejected_without_rewriting(self):
        self.artwork['creation_year_start'] = 1885
        with self.assertRaises(AssertionError): self.check()
        self.assertEqual(1885, self.artwork['creation_year_start'])

    def test_date_qualifications_preserved(self):
        self.assertEqual({'exact', 'circa', 'range', 'circa_range'}, {r['facts']['precision'] for r in self.records})
        for r in self.records:
            f = r['facts']
            self.assertEqual((f['first'], f['last'], f['precision']), w.creation(w.one(r['source']['entity'], 'P571')))

    def test_cross_cutoff_date_rejected(self):
        self.entity['claims']['P571'][0]['mainsnak']['datavalue']['value']['time'] = '+1971-01-01T00:00:00Z'
        with self.assertRaises(AssertionError): self.check()

    def test_published_record_rejected(self):
        self.artwork['published_at'] = '2026-10-07'
        with self.assertRaises(AssertionError): self.check()

    def test_component_title_held(self):
        self.artwork['title'] = 'My Sister (triptych, left wing)'
        self.entity['labels']['en']['value'] = self.artwork['title']
        with self.assertRaises(AssertionError): self.check()

    def test_other_location_rejected(self):
        self.entity['claims']['P276'][0]['mainsnak']['datavalue']['value']['id'] = 'Q2087788'
        with self.assertRaises(AssertionError): self.check()

    def test_review_retains_held_and_unselected_entries(self):
        rows = w.m.load(w.REVIEW)['decisions']
        self.assertEqual(220, len(rows))
        self.assertEqual(33, sum(r['decision'] == 'hold' for r in rows))
        self.assertEqual(2, sum(r['decision'] == 'not_selected' for r in rows))


if __name__ == '__main__':
    unittest.main()
