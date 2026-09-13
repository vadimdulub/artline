"""Offline identity and attribution safeguards; never connects to a database."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('reconcile', Path(__file__).with_name('reconcile-artwork-creators.py'))
reconcile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconcile)


class CreatorPolicy(unittest.TestCase):
    def test_name_without_biography_is_not_an_identity(self):
        self.assertIsNone(reconcile.identity('joconde', {'name': 'John Smith', 'birth': 1800}))
        self.assertNotEqual(
            reconcile.identity('joconde', {'name': 'John Smith', 'birth': 1800, 'death': 1870}),
            reconcile.identity('joconde', {'name': 'John Smith', 'birth': 1810, 'death': 1870}))

    def test_authority_identifiers_are_scoped_to_museum(self):
        p = {'name': 'John Smith', 'source_id': '123'}
        self.assertNotEqual(reconcile.identity('smk', p), reconcile.identity('tate', p))

    def row(self):
        return {'state': 'needs_review', 'review': {}, 'context': {}, 'note': 'creation_date_review',
                'painter': {'name': 'John Smith', 'birth': 1800, 'death': 1870, 'role': 'artist'},
                'precision': 'unknown', 'first': None, 'last': None, 'type': 'painting'}

    def test_unknown_dates_do_not_prevent_creator_reconciliation(self):
        self.assertIsNone(reconcile.blocked(self.row()))

    def test_qualifier_in_separate_field_and_copy_notes_are_held(self):
        for context in [{'creator_qualifier': 'tilskrevet'}, {'creator_notes': 'Kopi efter et maleri'}]:
            row = self.row(); row['context'] = context
            self.assertEqual(reconcile.blocked(row), 'qualified_creator')

    def test_existing_hold_and_impossible_painting_date_are_preserved(self):
        row = self.row(); row['review'] = {'blocks_promotion': True}
        self.assertEqual(reconcile.blocked(row), 'attribution_or_state_hold')
        row = self.row(); row.update(precision='exact', first=1900, last=1900)
        self.assertEqual(reconcile.blocked(row), 'date_conflict')


if __name__ == '__main__':
    unittest.main()
