"""Offline research policy checks; no catalogue fixtures or database writes."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('planner', Path(__file__).with_name('plan-expanded-round2.py'))
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)


class ResearchPolicy(unittest.TestCase):
    def test_month_and_place_retain_explicit_year(self):
        value = planner.date_literal('Paris, June-July 1914')
        self.assertEqual((value['first'], value['last'], value['precision']), (1914, 1914, 'exact'))

    def test_shortened_range_is_not_a_single_year(self):
        value = planner.date_literal('c. 1914-18')
        self.assertEqual((value['first'], value['last'], value['precision']), (1914, 1918, 'circa_range'))

    def test_open_and_disputed_dates_stay_unknown(self):
        for text in ['before 1900', 'after 1950', '1927 or 1928', '1912-14?',
                     '1929 (original date obliterated; repainted 1925)']:
            self.assertEqual(planner.date_literal(text)['precision'], 'unknown', text)

    def test_namesakes_keep_distinct_full_name_keys(self):
        self.assertNotEqual(planner.namekey('Johann Heinrich Tischbein I'), planner.namekey('Johann Heinrich Tischbein II'))

    def test_word_order_and_accents_can_match_documented_name_variants(self):
        self.assertEqual(planner.namekey('Cézanne, Paul'), planner.namekey('Paul Cezanne'))


if __name__ == '__main__':
    unittest.main()
