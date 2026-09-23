"""Date and artist identity boundaries; no database, fixtures or network."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('coverage',Path(__file__).with_name('wikiart-artist-coverage.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class CoverageTests(unittest.TestCase):
    def test_early_byzantine_dates_are_supported(self):
        self.assertEqual(module.dated('547')['creation_year_start'],547)

    def test_bce_dates_keep_historical_order(self):
        date=module.dated('1981-1802 BC')
        self.assertEqual((date['creation_year_start'],date['creation_year_end']),(-1981,-1802))
        self.assertEqual(date['date_display'],'1981-1802 BC')
        self.assertEqual(module.dated('c.550 BCE')['date_precision'],'circa')

    def test_zero_and_reversed_bce_ranges_are_not_dates(self):
        self.assertIsNone(module.dated('0'))
        self.assertIsNone(module.dated('1802-1981 BC'))

    def test_cross_cutoff_range_is_not_eligible(self):
        self.assertIsNone(module.dated('1954–1956'))

    def test_unknown_and_open_dates_are_not_invented(self):
        for date in ('',None,'unknown','before 1900','19th century'):
            self.assertIsNone(module.dated(date))

    def test_approximation_and_interval_survive(self):
        d=module.dated('c.1900–1903')
        self.assertEqual((d['date_precision'],d['creation_year_start'],d['creation_year_end']),('circa_range',1900,1903))

    def test_reversed_dates_are_not_eligible(self):
        self.assertIsNone(module.dated('1903-1900'))

    def test_artist_death_does_not_set_artwork_cutoff(self):
        life=module.source_life({'life_display':'1900 - 1990'})
        self.assertEqual(life['death_year'],1990)
        self.assertIsNotNone(module.dated('1955'))
        self.assertIsNone(module.dated('1956'))

    def test_circa_lifespan_is_preserved(self):
        life=module.source_life({'life_display':'c.1430 - c.1510'})
        self.assertEqual((life['birth_precision'],life['death_precision']),('circa','circa'))
        self.assertEqual(life['birth_display'],'c.1430')

    def test_living_artist_does_not_receive_invented_death(self):
        life=module.source_life({'life_display':'born 1920'})
        self.assertIsNone(life['death_year'])
        self.assertIsNone(life['death_display'])


if __name__=='__main__':unittest.main()
