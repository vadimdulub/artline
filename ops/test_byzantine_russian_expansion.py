import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('icons', Path(__file__).with_name('byzantine-russian-expansion.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SourceDatingTests(unittest.TestCase):
    def test_explicit_century_parts(self):
        self.assertEqual(m.russian_date('Первая половина XIII века'), (1201, 1250, 'range'))
        self.assertEqual(m.russian_date('Вторая четверть XV века'), (1426, 1450, 'range'))
        self.assertEqual(m.russian_date('Первая треть XIII века'), (1201, 1233, 'range'))

    def test_broad_qualifier_keeps_conservative_envelope(self):
        self.assertEqual(m.russian_date('Новгород. Конец XIV — начало XV века'), (1301, 1500, 'range'))
        self.assertEqual(m.russian_date('Средняя Русь. Середина – вторая половина XIV века'), (1301, 1400, 'century'))

    def test_creation_and_later_phases_not_collapsed(self):
        self.assertEqual(m.russian_date('1199 (копия фрески - 1918)'), (None, None, 'unknown'))
        self.assertEqual(m.russian_date('XV век, поновление 1800'), (None, None, 'unknown'))
        self.assertEqual(m.russian_date('XVI век. Оклад: начало ХХ века'), (None, None, 'unknown'))
        self.assertEqual(m.russian_date('В окладе. 1704'), (1704, 1704, 'exact'))
        self.assertEqual(m.english_date('Virgin (early 14th c.) and Crucifixion (18th c.)'), (None, None, 'unknown'))

    def test_date_uncertainty_and_location_uncertainty_differ(self):
        self.assertEqual(m.russian_date('Византия (?). Конец XIV – начало XV века'), (1301, 1500, 'range'))
        self.assertEqual(m.russian_date('1400 (?)'), (None, None, 'unknown'))

    def test_years_and_decades(self):
        self.assertEqual(m.russian_date('Москва. Около 1408'), (1408, 1408, 'circa'))
        self.assertEqual(m.russian_date('1850-е'), (1850, 1859, 'decade'))
        self.assertEqual(m.russian_date('после 1650'), (1650, None, 'after'))

    def test_cyrillic_place_names_are_not_roman_centuries(self):
        self.assertEqual(m.russian_date('Холуй. Конец XIX — начало XX века'), (1801, 2000, 'range'))
        self.assertEqual(m.russian_date('Холуй, мастерская М. М. Блинничева. Начало XX века'), (1901, 2000, 'century'))

    def test_english_half_is_not_a_second_century(self):
        self.assertEqual(m.english_date('1st half of 18th c.'), (1701, 1750, 'range'))
        self.assertEqual(m.english_date('late 14th – early 15th century'), (1301, 1500, 'range'))
        self.assertEqual(m.english_date('360-370'), (360, 370, 'range'))
        self.assertEqual(m.english_date('End of 5th c.'), (401, 500, 'century'))

    def test_accession_punctuation_is_identity(self):
        self.assertNotEqual(m.accession_key('ДРЖ-1-24'), m.accession_key('ДРЖ-124'))
        self.assertNotEqual(m.accession_key('1961.35.a'), m.accession_key('1961.35'))
        self.assertEqual(m.accession_key('ΒΧΜ 01354'), m.accession_key('ΒΧΜ01354'))


if __name__ == '__main__':
    unittest.main()
