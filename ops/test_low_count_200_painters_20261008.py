"""Pure source/plan checks. No database connections or database fixtures."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('low_count_operation', Path(__file__).with_name('low-count-200-painters-20261008.py'))
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


class SourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.pair = {'artist': {'id': 'painter-id', 'display_name': 'Example Painter'},
                     'source': {'name': 'Example Painter', 'url': 'https://www.wikiart.org/en/example-painter'}, 'aliases': []}
        self.item = {'title': 'Specific composition', 'url': self.pair['source']['url']+'/specific-composition',
                     'source_date': '1960', 'date': op.m.dates.creation_date('1960')}
        self.meta = {'title': 'Specific composition', 'artistName': 'Example Painter', 'contentId': 123,
                     'yearAsString': '1960', 'image': 'https://uploads0.wikiart.org/images/example-painter/specific-composition.jpg!Large.jpg'}

    def run_source(self, items=None, metadata=None):
        idx = {'outcome': 'indexed', 'items': items or [self.item], 'metadata': metadata or [self.meta],
               'receipt': {'sha256': 'index-proof'}, 'metadata_receipt': {'sha256': 'metadata-proof'}}
        with patch.object(op.r, 'load', return_value=idx):
            return op.source_candidates(self.pair)

    def test_distinct_object_requires_both_source_lists(self):
        rows, held = self.run_source()
        self.assertEqual(len(rows), 1)
        self.assertFalse(held)
        self.assertEqual(rows[0]['source_id'], '123')
        self.assertEqual(rows[0]['work']['work_type'], 'unknown')

    def test_wrong_named_creator_is_held(self):
        self.meta['artistName'] = 'Different Painter'
        rows, held = self.run_source()
        self.assertFalse(rows)
        self.assertIn('creator', held[0]['reason'])

    def test_post_1970_creation_is_excluded(self):
        self.item.update(source_date='1971', date=op.m.dates.creation_date('1971'))
        self.meta['yearAsString'] = '1971'
        rows, held = self.run_source()
        self.assertFalse(rows)
        self.assertIn('After 1970', held[0]['reason'])

    def test_conflicting_source_dates_are_held(self):
        self.meta['yearAsString'] = '1961'
        rows, held = self.run_source()
        self.assertFalse(rows)
        self.assertEqual(held[0]['reason'], 'Source date conflict')

    def test_unknown_date_is_never_invented(self):
        self.item.update(source_date='?', date=None)
        self.meta['yearAsString'] = None
        rows, held = self.run_source()
        self.assertFalse(held)
        self.assertIsNone(rows[0]['work']['creation_year_start'])
        self.assertEqual(rows[0]['work']['date_precision'], 'unknown')

    def test_duplicate_source_image_does_not_create_two_objects(self):
        other = {**self.meta, 'contentId': 124}
        rows, held = self.run_source(metadata=[self.meta, other])
        self.assertFalse(rows)
        self.assertEqual(len(held), 2)


class PlanBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = {'pair': {'artist': {'id': 'example-painter'}, 'count_at_selection': 3,
                                 'source': {'url': 'https://www.wikiart.org/en/example-painter'}}, 'rows': []}
        for i in range(20):
            cls.original['rows'].append({'artist_id': 'example-painter', 'artwork_id': 'work-'+str(i),
                'source_id': str(i+1), 'source_scheme': 'wikiart-legacy-content-id',
                'source_url': 'https://www.wikiart.org/en/example-painter/work-'+str(i),
                'metadata': {'contentId': i+1}, 'work': {'id': 'work-'+str(i), 'title': 'Example work '+str(i),
                'creation_year_start': 1900, 'creation_year_end': 1900, 'date_precision': 'exact'}})

    def valid(self):
        data = copy.deepcopy(self.original)
        for row in data['rows']:
            if row['work']['creation_year_start'] is None:
                row['date_review'] = 'Creation date unknown; editorial review retained.'
        return data

    def test_valid_twenty_work_plan_passes(self):
        op.validate_plan(self.valid())

    def test_fewer_than_20_additions_rejected(self):
        plan = self.valid(); plan['rows'] = plan['rows'][:19]
        with self.assertRaises(AssertionError): op.validate_plan(plan)

    def test_duplicate_target_rejected(self):
        plan = self.valid(); plan['rows'][1]['artwork_id'] = plan['rows'][0]['artwork_id']
        with self.assertRaises(AssertionError): op.validate_plan(plan)

    def test_existing_count_above_ten_rejected(self):
        plan = self.valid(); plan['pair']['count_at_selection'] = 11
        with self.assertRaises(AssertionError): op.validate_plan(plan)

    def test_after_cutoff_rejected(self):
        plan = self.valid(); plan['rows'][0]['work'].update(creation_year_start=1971, creation_year_end=1971)
        with self.assertRaises(AssertionError): op.validate_plan(plan)


if __name__ == '__main__':
    unittest.main()
