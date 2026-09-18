"""Pure parsing checks; never connect to any database."""
import importlib.util
import unittest
from pathlib import Path

s = importlib.util.spec_from_file_location('france_campaign', Path(__file__).with_name('france-catalogue-campaign.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)


def row(**changes):
    value = {'Auteur':'Monet Claude (1840-1926)','Titre':'Fécamp, bord de mer','MANQUANT':'',
        'Millesime_de_creation':'1881','Periode_de_creation':'4e quart 19e siècle',
        'Denomination':'tableau','Materiaux_techniques':"peinture à l'huile, toile",'Mesures':'65.3 x 80.5 cm','Numero_inventaire':'994.01'}
    return dict(value, **changes)


class FactsTests(unittest.TestCase):
    def test_exact(self):
        f=m.facts(row());self.assertEqual((f['first'],f['last'],f['precision']),(1881,1881,'exact'))
    def test_after_cutoff(self):
        with self.assertRaises(AssertionError):m.facts(row(Millesime_de_creation='1971'))
    def test_multiple_dates_not_invented_range(self):
        f=m.facts(row(Millesime_de_creation='1881;1883'));self.assertIsNone(f['first']);self.assertEqual(f['precision'],'unknown')
    def test_conflicting_century(self):
        f=m.facts(row(Periode_de_creation='4e quart 20e siècle'));self.assertIsNone(f['first'])
    def test_creator_lifespan_conflict(self):
        f=m.facts(row(Auteur='Fricero Joseph (1807-1870)',Millesime_de_creation='1879'));self.assertIsNone(f['first'])
    def test_qualified_creator(self):
        with self.assertRaises(AssertionError):m.facts(row(Auteur='Monet Claude (attribué à)'))
    def test_anonymous_hold_is_explicit(self):
        with self.assertRaises(AssertionError):m.facts(row(Auteur='anonyme'))
    def test_missing_work(self):
        with self.assertRaises(AssertionError):m.facts(row(MANQUANT='manquant'))
    def test_relief_unknown(self):
        self.assertEqual(m.facts(row(Denomination='tableau-relief'))['work_type'],'unknown')
    def test_approximate_not_stripped(self):
        with self.assertRaises(AssertionError):m.facts(row(Millesime_de_creation='1881 vers'))
    def test_deposit_not_parsed_as_creation(self):
        f=m.facts(row(Date_de_depot='1981'));self.assertEqual(f['first'],1881)
    def test_alphanumeric_source_id(self):
        self.assertNotEqual(m.uid('joconde/M1111160007695'),m.uid('joconde/000PE000014'))


if __name__=='__main__':unittest.main()
